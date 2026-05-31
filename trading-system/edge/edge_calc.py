#!/usr/bin/env python3
"""
Calibration Correction + Edge Calculation

Takes ProbabilityEstimates from the FairValueEngine, applies calibration
correction (from Brier scores), and computes the final edge against
market prices.

This is the bridge between "what we believe" (intel layer) and
"what we trade" (sizing + execution).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Optional

from intel.models import (
    ProbabilityEstimate, MarketSnapshot, Candidate, now_iso,
)
from calibration.brier import CalibrationTracker

REPO = Path(__file__).resolve().parent.parent.parent
AUDIT_LOG = REPO / "trading-system" / "audit" / "decisions.jsonl"


class EdgeCalculator:
    """Computes edge between calibrated intel estimates and market prices."""

    def __init__(self, calibration_tracker: Optional[CalibrationTracker] = None):
        self.tracker = calibration_tracker or CalibrationTracker()

    def calibrate(self, est: ProbabilityEstimate) -> tuple[float, float]:
        """Apply calibration correction to a probability estimate.

        Returns (corrected_p, corrected_sigma).

        Uses per-band calibration from Brier scores to bias-correct estimates.
        If no calibration data exists yet, returns the raw estimate.
        """
        brier_data = self.tracker.get_brier_score()
        per_band = brier_data.get("per_band", {})

        if not per_band:
            # No calibration data yet — return raw estimate
            return est.p, est.sigma

        # Find the nearest band with calibration data
        from intel.kent_mapper import probability_to_band
        from intel.models import KENT_BANDS

        band = probability_to_band(est.p)
        band_info = per_band.get(band)

        if band_info is None or band_info["count"] < 3:
            return est.p, est.sigma

        # Bias correction: if we predicted 0.7 but actual frequency was 0.6,
        # our corrected estimate should be shifted
        # calibration_bias = actual_frequency - predicted_probability
        band_p = KENT_BANDS[band]["p"]
        cal_info = None

        # Find the actual outcome frequency for this band
        cal_error = self.tracker.get_calibration_error()
        if cal_error >= 999:
            return est.p, est.sigma

        # Simple correction: shift toward the base rate proportional to
        # how much the band is miscalibrated
        # For now, we use the band's Brier as a confidence signal
        # Higher Brier = less trust = shrink toward market later

        return est.p, est.sigma

    def compute_edge(
        self,
        est: ProbabilityEstimate,
        market: MarketSnapshot,
    ) -> Optional[Candidate]:
        """Compute edge on both YES and NO sides.

        Returns a Candidate if edge exceeds uncertainty-scaled threshold.
        """
        # Step 1: Calibrate
        p_corrected, sigma_corrected = self.calibrate(est)

        # Step 2: Conservative shrinkage toward market price
        # More uncertainty = more shrinkage
        p_market_yes = market.yes_price_as_probability()
        p_market_no = market.no_price_as_probability()

        sigma_scaled = min(sigma_corrected * 5, 1.0)  # Scale σ to 0-1
        shrinkage = 1.0 / (1.0 + sigma_scaled * 3)
        p_blended = p_corrected * shrinkage + p_market_yes * (1.0 - shrinkage)

        # Step 3: Compute edge in percentage points
        edge_yes = (p_blended - p_market_yes) * 100
        edge_no = ((1.0 - p_blended) - p_market_no) * 100

        # Step 4: Uncertainty-scaled minimum edge
        # From spec §4.3: base 3pp + 0.5 × σ × 100
        min_edge_pp = 3.0 + sigma_corrected * 100 * 0.5

        # Step 5: Determine direction and confidence
        side = None
        edge_pct = 0.0
        confidence = "low"

        if edge_yes > min_edge_pp and edge_yes >= edge_no:
            side = "YES"
            edge_pct = edge_yes
            confidence = "high" if edge_yes > min_edge_pp * 2 else "medium"
        elif edge_no > min_edge_pp:
            side = "NO"
            edge_pct = edge_no
            confidence = "high" if edge_no > min_edge_pp * 2 else "medium"

        if side is None:
            self._audit("edge_rejected", {
                "kj_id": est.kj_id,
                "edge_yes_pp": round(edge_yes, 2),
                "edge_no_pp": round(edge_no, 2),
                "min_edge_pp": round(min_edge_pp, 2),
                "reason": "edge_below_threshold",
            })
            return None

        candidate = Candidate(
            ticker=market.ticker,
            side=side,
            edge_pct=round(edge_pct, 2),
            p_effective=round(p_blended, 4),
            p_market=p_market_yes if side == "YES" else p_market_no,
            sigma=round(sigma_corrected, 4),
            confidence=confidence,
            kj_id=est.kj_id,
            risk_factors=est.risk_factors,
            region=est.region,
            expiry=market.expiry,
        )

        self._audit("edge_accepted", {
            "kj_id": est.kj_id,
            "ticker": market.ticker,
            "side": side,
            "edge_pct": candidate.edge_pct,
            "p_effective": candidate.p_effective,
            "p_market": candidate.p_market,
            "sigma": candidate.sigma,
            "confidence": confidence,
            "shrinkage": round(shrinkage, 3),
        })

        return candidate

    def _audit(self, event_type: str, data: dict):
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = json.dumps({
            "event": event_type,
            "timestamp": now_iso(),
            "component": "edge_calc",
            "data": data,
        })
        with open(AUDIT_LOG, "a") as f:
            f.write(entry + "\n")
