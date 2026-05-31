#!/usr/bin/env python3
"""
Calibration → Brier Scoring + Reliability Curves

Tracks forecast accuracy across all KJs. Computes Brier scores,
reliability curves per Kent band, and calibration error.

This is the ONLY component that can:
- Raise the autonomy level
- Adjust the min-edge threshold
- Change position sizing confidence

Autonomy is earned by demonstrated calibration, never assumed.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from collections import Counter
from typing import Optional

from intel.models import (
    ResolutionRecord, now_iso, parse_iso, AutonomyLevel, KENT_BANDS
)

REPO = Path(__file__).resolve().parent.parent.parent
RESOLUTION_LOG = REPO / "trading-system" / "calibration" / "resolution_log.jsonl"
SOURCE_WEIGHTS_FILE = REPO / "trading-system" / "calibration" / "source_weights.json"


class CalibrationTracker:
    """Records forecast outcomes and computes calibration metrics."""

    def __init__(self):
        self._ensure_log()

    def _ensure_log(self):
        RESOLUTION_LOG.parent.mkdir(parents=True, exist_ok=True)
        if not RESOLUTION_LOG.exists():
            RESOLUTION_LOG.touch()

    def record_forecast(self, kj_id: str, claim: str, predicted_p: float,
                        predicted_sigma: float, region: str = "",
                        risk_factors: Optional[list[str]] = None):
        """Record a forecast that will be resolved later."""
        record = ResolutionRecord(
            kj_id=kj_id,
            claim=claim,
            predicted_p=predicted_p,
            predicted_sigma=predicted_sigma,
            forecast_timestamp=now_iso(),
            resolution_timestamp="",
            outcome=False,
            region=region,
            risk_factors=risk_factors or [],
        )
        entry = json.dumps({
            "event": "forecast_recorded",
            "timestamp": now_iso(),
            "data": {
                "kj_id": kj_id,
                "claim": claim,
                "predicted_p": predicted_p,
                "predicted_sigma": predicted_sigma,
                "forecast_timestamp": record.forecast_timestamp,
                "region": region,
                "risk_factors": risk_factors or [],
                "resolved": False,
            }
        })
        with open(RESOLUTION_LOG, "a") as f:
            f.write(entry + "\n")

    def resolve(self, kj_id: str, outcome: bool) -> bool:
        """Resolve a previously recorded forecast with actual outcome.

        Returns True if resolution was recorded, False if kj_id not found.
        """
        records = self._load_all()
        found = False
        for r in records:
            if r.get("data", {}).get("kj_id") == kj_id and not r.get("data", {}).get("resolved", True):
                r["data"]["outcome"] = outcome
                r["data"]["resolved"] = True
                r["data"]["resolution_timestamp"] = now_iso()
                found = True
                break

        if found:
            self._rewrite_all(records)

        return found

    def get_brier_score(self) -> dict:
        """Compute overall and per-band Brier scores.

        Returns:
            {
                "overall_brier": float,
                "brier_skill": float (positive = better than market base rate),
                "per_band": {band_name: {"count": N, "brier": float}},
                "total_forecasts": int,
                "total_resolved": int,
            }
        """
        records = self._load_all()
        resolved = [r for r in records if r.get("data", {}).get("resolved", False)]

        if not resolved:
            return {
                "overall_brier": None,
                "brier_skill": None,
                "per_band": {},
                "total_forecasts": len(records),
                "total_resolved": 0,
            }

        # Per-band Brier
        per_band: dict[str, dict] = {}
        total_brier = 0.0

        for r in resolved:
            d = r["data"]
            p = d["predicted_p"]
            outcome = 1.0 if d.get("outcome") else 0.0
            brier = (p - outcome) ** 2

            # Determine band
            band = min(KENT_BANDS.keys(),
                       key=lambda b: abs(KENT_BANDS[b]["p"] - p))

            if band not in per_band:
                per_band[band] = {"count": 0, "brier_sum": 0.0}
            per_band[band]["count"] += 1
            per_band[band]["brier_sum"] += brier
            total_brier += brier

        n = len(resolved)
        overall_brier = total_brier / n

        # Brier skill score relative to always-predicting-base-rate
        # (climatology baseline: predict the outcome base rate for every event)
        outcomes = [1.0 if r["data"].get("outcome") else 0.0 for r in resolved]
        base_rate = sum(outcomes) / len(outcomes) if outcomes else 0.5
        baseline_brier = sum((base_rate - o) ** 2 for o in outcomes) / len(outcomes)
        brier_skill = 1.0 - (overall_brier / baseline_brier) if baseline_brier > 0 else 0.0

        result = {
            "overall_brier": round(overall_brier, 4),
            "brier_skill": round(brier_skill, 4),
            "per_band": {
                band: {
                    "count": v["count"],
                    "brier": round(v["brier_sum"] / v["count"], 4),
                }
                for band, v in per_band.items()
            },
            "total_forecasts": len(records),
            "total_resolved": n,
        }

        return result

    def get_calibration_error(self) -> float:
        """Compute mean calibration error.

        Measures: for each band, |actual_frequency - predicted_probability|.
        Returns a value 0-1 where 0 = perfectly calibrated.
        """
        records = self._load_all()
        resolved = [r for r in records if r.get("data", {}).get("resolved", False)]

        if len(resolved) < 5:
            return 999.0  # Not enough data

        # Group by band
        band_outcomes: dict[str, list[bool]] = {}
        for r in resolved:
            d = r["data"]
            p = d["predicted_p"]
            band = min(KENT_BANDS.keys(),
                       key=lambda b: abs(KENT_BANDS[b]["p"] - p))
            if band not in band_outcomes:
                band_outcomes[band] = []
            band_outcomes[band].append(d.get("outcome", False))

        errors = []
        for band, outcomes in band_outcomes.items():
            if len(outcomes) < 3:
                continue
            actual_freq = sum(outcomes) / len(outcomes)
            predicted = KENT_BANDS[band]["p"]
            errors.append(abs(actual_freq - predicted))

        if not errors:
            return 999.0

        return round(sum(errors) / len(errors), 4)

    def evaluate_autonomy_promotion(self, current_level: AutonomyLevel) -> dict:
        """Check if autonomy level should be promoted.

        Returns dict with promotion status and gate progress.
        """
        brier_data = self.get_brier_score()
        cal_error = self.get_calibration_error()
        total_resolved = brier_data["total_resolved"]
        brier_skill = brier_data.get("brier_skill", 0)

        gates = {}

        if current_level == AutonomyLevel.PAPER:
            # Level 0 → 1: 50 resolved forecasts, positive skill, cal error < 0.10
            gates = {
                "min_forecasts": total_resolved >= 50,
                "positive_skill": (brier_skill is not None and brier_skill > 0),
                "calibration_error_ok": (cal_error < 0.10),
            }

        elif current_level == AutonomyLevel.TINY_CONFIRMED:
            # Level 1 → 2: 50 paper trades resolved, maintained skill
            gates = {
                "min_resolved": total_resolved >= 50,
                "positive_skill": (brier_skill is not None and brier_skill > 0),
                "calibration_error_ok": (cal_error < 0.08),
            }

        elif current_level == AutonomyLevel.LIVE_BATCHED:
            # Level 2 → 3: sustained calibration for 30 days
            gates = {
                "sustained_calibration": (cal_error < 0.06),
                "total_resolved_sufficient": total_resolved >= 100,
            }

        eligible = all(gates.values()) if gates else False

        return {
            "current_level": current_level.name,
            "eligible_for_promotion": eligible,
            "gates": gates,
            "brier_skill": brier_skill,
            "calibration_error": cal_error,
            "total_resolved": total_resolved,
        }

    def _load_all(self) -> list[dict]:
        if not RESOLUTION_LOG.exists():
            return []
        records = []
        with open(RESOLUTION_LOG) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return records

    def _rewrite_all(self, records: list[dict]):
        with open(RESOLUTION_LOG, "w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")


# ── CLI ─────────────────────────────────────────────────────────────

def cli_report():
    """Print calibration report."""
    tracker = CalibrationTracker()
    brier = tracker.get_brier_score()
    cal_err = tracker.get_calibration_error()

    print("=" * 60)
    print("  Calibration Report")
    print(f"  {now_iso()}")
    print("=" * 60)
    print(f"  Total forecasts:  {brier['total_forecasts']}")
    print(f"  Total resolved:   {brier['total_resolved']}")
    print(f"  Overall Brier:    {brier['overall_brier'] or 'N/A'}")
    print(f"  Brier Skill:      {brier['brier_skill'] or 'N/A'}")
    print(f"  Cal. Error:       {cal_err if cal_err < 999 else 'N/A'}")
    print()

    if brier["per_band"]:
        print("  Per-Band Brier:")
        for band, info in sorted(brier["per_band"].items()):
            print(f"    {band:<25} n={info['count']:>4}  brier={info['brier']:.4f}")
    print("=" * 60)

    # Autonomy check
    for level in [AutonomyLevel.PAPER, AutonomyLevel.TINY_CONFIRMED]:
        result = tracker.evaluate_autonomy_promotion(level)
        badge = "✅" if result["eligible_for_promotion"] else "⏳"
        print(f"\n  {badge} Promote from {result['current_level']}?")
        for gate, status in result["gates"].items():
            print(f"    {'✅' if status else '❌'} {gate}")


if __name__ == "__main__":
    cli_report()
