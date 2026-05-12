#!/usr/bin/env python3
"""prioritize.py — Dynamic theatre prioritization based on narrative volatility.

Replaces static theatre ordering with adaptive prioritization based on:
- Narrative regime shifts (narrative_engine)
- Source density (enrichment report)
- Prediction-market repricing frequency
- Unresolved estimative question count (memory store)
- Intelligence significance score

Output: priority_ordered list consumed by improvement_daemon and dashboard

Usage:
    python3 prioritize.py                   # Print priority order
    python3 prioritize.py --json            # JSON output
    python3 prioritize.py --weights         # Show current weight configuration
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from trevor_config import THEATRE_KEYS as THEATRES
from trevor_log import get_logger
from trevor_memory import MemoryStore

log = get_logger("prioritize")

CRON_DIR = SKILL_ROOT / 'cron_tracking'
NARRATIVE_FILE = CRON_DIR / 'narrative_landscape.json'
ENRICHMENT_FILE = CRON_DIR / 'enrichment_report.json'

# Default weights — can be overridden by calibration history
DEFAULT_WEIGHTS = {
    "narrative_volatility": 0.30,
    "unresolved_questions": 0.25,
    "source_density": 0.20,
    "strategic_significance": 0.15,
    "prediction_market_activity": 0.10,
}

BASELINE_SIGNIFICANCE = {
    "middle_east": 0.95,
    "europe": 0.85,
    "asia": 0.75,
    "north_america": 0.60,
    "global_finance": 0.55,
    "africa": 0.40,
    "south_america": 0.35,
}


def score_theatre(region: str) -> dict:
    """Score a theatre on multiple axes. Returns normalized scores."""
    mem = MemoryStore()
    try:
        # 1. Narrative volatility
        volatility = 0.1
        if NARRATIVE_FILE.exists():
            try:
                landscape = json.loads(NARRATIVE_FILE.read_text())
                for drift in landscape.get("drifts", []):
                    if drift.get("region") == region:
                        if drift["status"] == "regime_shift":
                            volatility = 0.9
                        elif drift["status"] == "identical":
                            volatility = 0.2
                        elif drift["status"] == "minor_shift":
                            volatility = 0.5
            except:
                pass

        # 2. Unresolved questions
        unresolved = 0.1
        try:
            results = mem.search("unresolved", collection="narrative", region=region, top_k=5)
            unresolved = min(1.0, len(results) * 0.2)
        except:
            pass

        # 3. Source density
        source_density = 0.1
        if ENRICHMENT_FILE.exists():
            try:
                enrich = json.loads(ENRICHMENT_FILE.read_text())
                articles = enrich.get("articles_fetched", 0)
                source_density = min(1.0, articles / 20)
            except:
                pass

        # 4. Strategic significance
        significance = BASELINE_SIGNIFICANCE.get(region, 0.5)

        # 5. Prediction market activity
        pm_activity = 0.1
        try:
            pm_results = mem.search("trade thesis", collection="narrative", region=region, top_k=3)
            pm_activity = min(1.0, len(pm_results) * 0.3)
        except:
            pass

        return {
            "region": region,
            "volatility": round(volatility, 2),
            "unresolved": round(unresolved, 2),
            "source_density": round(source_density, 2),
            "significance": round(significance, 2),
            "pm_activity": round(pm_activity, 2),
        }

    finally:
        mem.close()


def compute_priority(scores: dict) -> float:
    """Compute weighted priority score."""
    w = DEFAULT_WEIGHTS
    return (
        scores.get("volatility", 0) * w["narrative_volatility"] +
        scores.get("unresolved", 0) * w["unresolved_questions"] +
        scores.get("source_density", 0) * w["source_density"] +
        scores.get("significance", 0) * w["strategic_significance"] +
        scores.get("pm_activity", 0) * w["prediction_market_activity"]
    )


def prioritize() -> list[dict]:
    """Return priority-ordered list of theatres with scores."""
    scored = []
    for region in THEATRES:
        s = score_theatre(region)
        s["priority"] = round(compute_priority(s), 3)
        scored.append(s)
    scored.sort(key=lambda x: x["priority"], reverse=True)
    return scored


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--weights", action="store_true", help="Show weight config")
    args = parser.parse_args()

    if args.weights:
        print("Current prioritization weights:")
        for k, v in DEFAULT_WEIGHTS.items():
            print(f"  {k}: {v}")
        return 0

    ordered = prioritize()
    if args.json:
        print(json.dumps(ordered, indent=2))
    else:
        print(f"\n📊 Theatre Priority (based on narrative volatility, density, significance)")
        print(f"{'='*60}")
        for i, t in enumerate(ordered, 1):
            print(f"  {i}. {t['region']:<25s} priority={t['priority']:.3f}  "
                  f"(vol={t['volatility']} unres={t['unresolved']} "
                  f"src={t['source_density']} sig={t['significance']})")
        print(f"\nHighest priority: {ordered[0]['region']}")
        print(f"Lowest priority: {ordered[-1]['region']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
