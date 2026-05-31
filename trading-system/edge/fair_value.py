#!/usr/bin/env python3
"""
Fair Value Engine — Probability Estimation from Intelligence

Takes KJs (Key Judgments) from the intel store and produces
ProbabilityEstimates with decay, uncertainty propagation, and
market-relative edge calculations.

This is the core analytical component. Phase 1 only produces estimates
(logged but not traded). Phase 2 adds edge calculation against market prices.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from intel.models import (
    KeyJudgment, ProbabilityEstimate, MarketSnapshot, Candidate,
    now_iso, parse_iso
)
from intel.intel_store import IntelStore

REPO = Path(__file__).resolve().parent.parent.parent
ESTIMATE_LOG = REPO / "trading-system" / "edge" / "estimates.jsonl"
AUDIT_LOG = REPO / "trading-system" / "audit" / "decisions.jsonl"


class FairValueEngine:
    """Computes fair-value probability estimates from KJs."""

    def __init__(self, intel_store: Optional[IntelStore] = None):
        self.store = intel_store or IntelStore()
        self._ensure_logs()

    def _ensure_logs(self):
        ESTIMATE_LOG.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        for f in [ESTIMATE_LOG, AUDIT_LOG]:
            if not f.exists():
                f.touch()

    def estimate_from_kj(
        self,
        kj_id: str,
        as_of: Optional[str] = None,
    ) -> Optional[ProbabilityEstimate]:
        """Generate a ProbabilityEstimate from a stored KJ.

        Returns None if KJ not found or too decayed (< 0.5% probability).
        """
        kj = self.store.get(kj_id)
        if kj is None:
            return None

        if as_of is None:
            as_of = now_iso()

        est = ProbabilityEstimate.from_kj(kj, as_of=as_of)

        # Don't generate estimates for effectively zero-probability events
        if est.p < 0.005:
            return None

        # Log the estimate
        self._log_estimate(est)
        self._audit("estimate_computed", {
            "kj_id": kj_id,
            "p": est.p,
            "sigma": est.sigma,
            "effective_at": est.effective_at,
            "ttl_seconds": est.ttl_seconds,
        })

        return est

    def compute_edge(self, est: ProbabilityEstimate, market: MarketSnapshot) -> Optional[Candidate]:
        """
        Compute edge between our estimate and the market price.

        Edge = our_probability - market_implied_probability (for YES).
        Edge = (1 - our_probability) - market_implied_probability (for NO).

        Only returns a Candidate if edge exceeds uncertainty bounds.

        Phase 1: This is called but NOT acted upon (paper-only logging).
        """
        # Shrink estimate toward market by uncertainty
        p_market_yes = market.yes_price_as_probability()
        p_market_no = market.no_price_as_probability()

        # Conservative shrinkage: blend estimate and market proportional to σ
        shrinkage = 1 / (1 + est.sigma * 5)  # σ=0.04 → 0.83, σ=0.10 → 0.67
        p_blended = est.p * shrinkage + p_market_yes * (1 - shrinkage)

        # Compute edge on both sides
        edge_yes = (p_blended - p_market_yes) * 100  # In percentage points
        edge_no = ((1 - p_blended) - p_market_no) * 100

        # Uncertainty-scaled min edge (from spec §4.3)
        min_edge = 3.0 + est.sigma * 100 * 0.5  # Base 3pp + σ scaling

        # Determine direction
        side = None
        edge_pct = 0.0
        confidence = "low"

        if edge_yes > min_edge and edge_yes > edge_no:
            side = "YES"
            edge_pct = edge_yes
            confidence = "high" if edge_yes > min_edge * 2 else "medium"
        elif edge_no > min_edge:
            side = "NO"
            edge_pct = edge_no
            confidence = "high" if edge_no > min_edge * 2 else "medium"

        if side is None:
            # Log but don't return a candidate
            self._audit("edge_insufficient", {
                "kj_id": est.kj_id,
                "edge_yes_pp": round(edge_yes, 2),
                "edge_no_pp": round(edge_no, 2),
                "min_edge_pp": round(min_edge, 2),
            })
            return None

        candidate = Candidate(
            ticker=market.ticker,
            side=side,
            edge_pct=round(edge_pct, 2),
            p_effective=round(p_blended, 4),
            p_market=p_market_yes if side == "YES" else p_market_no,
            sigma=round(est.sigma, 4),
            confidence=confidence,
            kj_id=est.kj_id,
            risk_factors=est.risk_factors,
            region=est.region,
            expiry=market.expiry,
        )

        self._audit("edge_computed", {
            "kj_id": est.kj_id,
            "ticker": market.ticker,
            "side": side,
            "edge_pct": candidate.edge_pct,
            "p_effective": candidate.p_effective,
            "p_market": candidate.p_market,
            "sigma": candidate.sigma,
            "confidence": confidence,
        })

        return candidate

    def _log_estimate(self, est: ProbabilityEstimate):
        """Append estimate to the estimate log."""
        entry = json.dumps({
            "event": "estimate",
            "timestamp": now_iso(),
            "data": est.to_dict(),
        })
        with open(ESTIMATE_LOG, "a") as f:
            f.write(entry + "\n")

    def _audit(self, event_type: str, data: dict):
        """Append to the immutable audit log."""
        entry = json.dumps({
            "event": event_type,
            "timestamp": now_iso(),
            "component": "fair_value",
            "data": data,
        })
        with open(AUDIT_LOG, "a") as f:
            f.write(entry + "\n")

    def get_recent_estimates(self, limit: int = 20) -> list[dict]:
        """Get the most recent estimates from the log."""
        if not ESTIMATE_LOG.exists():
            return []
        estimates = []
        with open(ESTIMATE_LOG) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    estimates.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return estimates[-limit:]
