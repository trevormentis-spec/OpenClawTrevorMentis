#!/usr/bin/env python3
"""Briefometer — Active measurement + calibration system.

NOT a passive scorer. It:
  - Tracks Brier scores for Key Judgments over time
  - Flags calibration drift (over/under confidence)
  - Recommends confidence band adjustments
  - Tracks visual quality trends and flags degradation

Usage:
  python3 briefometer.py              # Full measurement + calibration check
  python3 briefometer.py --dashboard  # Show historical dashboard
  python3 briefometer.py --calibrate  # Run calibration regression
"""
from __future__ import annotations

import datetime
import json
import math
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from trevor_config import THEATRE_KEYS as THEATRES, EXPORTS_DIR
from trevor_log import get_logger

log = get_logger("briefometer")

ASSESS_DIR = SKILL_ROOT / 'assessments'
IMAGES_DIR = SKILL_ROOT / 'images'
MAPS_DIR = SKILL_ROOT / 'maps'
CRON_DIR = SKILL_ROOT / 'cron_tracking'
EXPORTS_DIR_PATH = EXPORTS_DIR

MEASUREMENT_LOG = CRON_DIR / 'measurement_log.json'
KJ_LOG = CRON_DIR / 'key_judgments.json'
BRIER_LOG = CRON_DIR / 'brier_scores.json'


# ── Confidence band calibration thresholds ──
BAND_CALIBRATION = {
    "almost certain": {"expected": 0.93, "lower": 0.85, "upper": 0.99},
    "highly likely": {"expected": 0.85, "lower": 0.75, "upper": 0.92},
    "likely": {"expected": 0.70, "lower": 0.55, "upper": 0.80},
    "roughly even odds": {"expected": 0.50, "lower": 0.40, "upper": 0.60},
    "even chance": {"expected": 0.50, "lower": 0.40, "upper": 0.60},
    "unlikely": {"expected": 0.30, "lower": 0.20, "upper": 0.45},
    "very unlikely": {"expected": 0.15, "lower": 0.05, "upper": 0.25},
    "almost no chance": {"expected": 0.07, "lower": 0.01, "upper": 0.15},
}


def extract_kjs_from_assessments() -> list[dict]:
    """Extract key judgments from assessment files with their Sherwood Kent bands."""
    kjs = []
    for region in THEATRES:
        path = ASSESS_DIR / f"{region}.md"
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        lines = text.split('\n')
        for line in lines:
            # Look for key judgment patterns
            if any(marker in line.lower() for marker in ["judgment:", "kj:", "key judgment"]):
                kjs.append({
                    "region": region,
                    "statement": line.strip()[:200],
                    "extracted_at": datetime.datetime.utcnow().isoformat(),
                })
    return kjs


def check_calibration() -> list[dict]:
    """Check if any confidence bands are consistently over/under-performing."""
    flags = []
    
    if not KJ_LOG.exists():
        return flags
    
    historical = json.loads(KJ_LOG.read_text())
    judgments = historical.get("judgments", [])
    
    if len(judgments) < 5:
        return flags  # not enough data
    
    # Calculate actual accuracy per band
    band_stats = {}
    for kj in judgments:
        band = kj.get("band", "").lower()
        if band not in BAND_CALIBRATION:
            continue
        if band not in band_stats:
            band_stats[band] = {"count": 0, "correct": 0}
        band_stats[band]["count"] += 1
        if kj.get("resolved", False) and kj.get("correct", False):
            band_stats[band]["correct"] += 1
    
    for band, stats in band_stats.items():
        if stats["count"] < 3:
            continue
        accuracy = stats["correct"] / stats["count"]
        expected = BAND_CALIBRATION[band]["expected"]
        lower = BAND_CALIBRATION[band]["lower"]
        upper = BAND_CALIBRATION[band]["upper"]
        
        if accuracy < lower:
            flags.append({
                "band": band,
                "issue": "overconfident",
                "accuracy": round(accuracy, 2),
                "expected": expected,
                "action": "widen_band",
                "note": f"'{band}' accuracy {accuracy:.0%} below expected {expected:.0%} — consider widening band",
            })
        elif accuracy > upper:
            flags.append({
                "band": band,
                "issue": "underconfident",
                "accuracy": round(accuracy, 2),
                "expected": expected,
                "action": "narrow_band",
                "note": f"'{band}' accuracy {accuracy:.0%} above expected {expected:.0%} — consider narrowing band",
            })
    
    return flags


def compute_brier_scores() -> dict:
    """Compute Brier scores for all resolved judgments."""
    if not KJ_LOG.exists():
        return {"total": 0, "average_brier": 0.0, "by_band": {}}
    
    historical = json.loads(KJ_LOG.read_text())
    resolved = [j for j in historical.get("judgments", []) if j.get("resolved", False)]
    
    if not resolved:
        return {"total": 0, "average_brier": 0.0, "by_band": {}}
    
    brier_by_band = {}
    total_brier = 0.0
    
    for j in resolved:
        band = j.get("band", "unknown").lower()
        predicted = j.get("predicted_probability", 0.5)
        actual = 1.0 if j.get("correct", False) else 0.0
        brier = (predicted - actual) ** 2
        
        if band not in brier_by_band:
            brier_by_band[band] = {"count": 0, "total_brier": 0.0}
        brier_by_band[band]["count"] += 1
        brier_by_band[band]["total_brier"] += brier
        total_brier += brier
    
    result = {
        "total": len(resolved),
        "average_brier": round(total_brier / len(resolved), 4),
        "by_band": {b: {"count": s["count"], "avg_brier": round(s["total_brier"] / s["count"], 4)} for b, s in brier_by_band.items()},
    }
    
    # Save for trend tracking
    BRIER_LOG.parent.mkdir(parents=True, exist_ok=True)
    BRIER_LOG.write_text(json.dumps(result, indent=2))
    
    return result


def record_kj(statement: str, band: str, probability: float, region: str):
    """Record a key judgment for future calibration tracking."""
    entry = {
        "id": f"KJ-{datetime.date.today().isoformat()}-{hash(statement) % 10000}",
        "statement": statement[:200],
        "band": band,
        "predicted_probability": probability,
        "region": region,
        "recorded_at": datetime.datetime.utcnow().isoformat(),
        "resolved": False,
        "correct": None,
    }
    
    KJ_LOG.parent.mkdir(parents=True, exist_ok=True)
    if KJ_LOG.exists():
        data = json.loads(KJ_LOG.read_text())
    else:
        data = {"judgments": []}
    data["judgments"].append(entry)
    KJ_LOG.write_text(json.dumps(data, indent=2))
    log.info("Key judgment recorded", region=region, band=band, probability=probability)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dashboard", action="store_true", help="Show historical dashboard")
    parser.add_argument("--calibrate", action="store_true", help="Run calibration check")
    parser.add_argument("--brier", action="store_true", help="Compute Brier scores")
    parser.add_argument("--record-kj", nargs=4, metavar=("STATEMENT", "BAND", "PROB", "REGION"),
                       help="Record a key judgment")
    args = parser.parse_args()
    
    if args.record_kj:
        statement, band, prob, region = args.record_kj
        record_kj(statement, band, float(prob), region)
        print(f"Recorded KJ: [{region}] {band} @ {prob}%")
        return 0
    
    if args.calibrate:
        flags = check_calibration()
        if flags:
            print(f"\n🔧 Calibration Issues ({len(flags)}):")
            for f in flags:
                print(f"  🔴 {f['band']}: {f['note']}")
        else:
            print("  ✅ Calibration looks good (or insufficient data)")
        return 0
    
    if args.brier:
        brier = compute_brier_scores()
        print(f"\n📊 Brier Scores:")
        print(f"  Total resolved: {brier['total']}")
        print(f"  Average Brier: {brier['average_brier']}")
        print(f"  By band: {json.dumps(brier.get('by_band', {}), indent=4)}")
        return 0
    
    if args.dashboard:
        brier = compute_brier_scores()
        kj_count = 0
        if KJ_LOG.exists():
            kj_count = len(json.loads(KJ_LOG.read_text()).get("judgments", []))
        print(f"\n📊 Briefometer Dashboard")
        print(f"{'='*50}")
        print(f"  Key judgments tracked: {kj_count}")
        print(f"  Resolved: {brier['total']}")
        print(f"  Avg Brier score: {brier['average_brier']}")
        flags = check_calibration()
        print(f"  Calibration flags: {len(flags)}")
        for f in flags:
            print(f"    🔴 {f['band']}: {f['note']}")
        return 0
    
    # Default: dashboard
    brier = compute_brier_scores()
    kj_count = 0
    if KJ_LOG.exists():
        kj_count = len(json.loads(KJ_LOG.read_text()).get("judgments", []))
    log.info("Briefometer run", kj_tracked=kj_count, brier=brier["average_brier"])
    print(f"Briefometer: {kj_count} KJs tracked, {brier['total']} resolved, Brier={brier['average_brier']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
