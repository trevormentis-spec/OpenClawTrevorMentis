#!/usr/bin/env python3
"""Postdiction → Calibration → Prompt Loop.

Closes the postdiction→calibration feedback loop. Reads historical
calibration tracking and postdiction results, computes per-band accuracy,
writes calibration directives, and enforces auto-adjustment when accuracy
is critically low.

Environment: No special vars required (reads from filesystem).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Paths
CALIBRATION_TRACKING = REPO_ROOT / "brain" / "memory" / "semantic" / "calibration-tracking.json"
CALIBRATION_DIRECTIVES = REPO_ROOT / "config" / "calibration-directives.json"
POSTDICTION_RESULTS = REPO_ROOT / "analyst" / "calibration" / "postdiction-results.json"
BEHAVIORAL_STATE = REPO_ROOT / "brain" / "memory" / "semantic" / "behavioral-state.json"
EPISODIC_DIR = REPO_ROOT / "brain" / "memory" / "episodic"

# Bands in order from lowest to highest confidence
BANDS = [
    "almost no chance",
    "unlikely",
    "roughly even chance",
    "likely",
    "highly likely",
    "almost certain",
]

ACCURACY_CRITICAL = 0.10  # Below 10% — trigger auto-adjustment
MIN_SAMPLES = 3          # Minimum samples needed for per-band calculation


def load_json(path: Path) -> dict | None:
    """Load a JSON file, returning None if missing or invalid."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"WARNING: Could not load {path}: {e}", file=sys.stderr)
        return None


def write_json(path: Path, data: dict) -> None:
    """Write JSON, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {path}")


def compute_per_band_accuracy(cal_data: dict) -> dict[str, dict]:
    """Compute accuracy per confidence band from calibration-tracking.json.

    Returns dict mapping band names to {total, correct, incorrect, unresolved, accuracy_pct}.
    """
    by_band = cal_data.get("by_confidence_band", {})

    # If we only have "likely" (common case), derive from overall
    results = {}
    for band in BANDS:
        stats = by_band.get(band, {})
        total = stats.get("total", 0)
        correct = stats.get("correct", 0)
        incorrect = stats.get("incorrect", 0)
        unresolved = stats.get("unresolved", 0)

        if total < MIN_SAMPLES:
            continue

        resolved = correct + incorrect
        accuracy_pct = round(correct / max(resolved, 1) * 100, 1) if resolved > 0 else 0.0

        results[band] = {
            "total": total,
            "correct": correct,
            "incorrect": incorrect,
            "unresolved": unresolved,
            "accuracy_pct": accuracy_pct,
        }

    return results


def generate_directives(cal_data: dict, band_accuracy: dict[str, dict]) -> dict:
    """Generate calibration directives from accuracy data."""
    total = cal_data.get("total_judgments", 0)
    correct = cal_data.get("correct", 0)
    unresolved = cal_data.get("unresolved", 0)
    resolved = correct + (total - correct - unresolved)
    overall_accuracy = round(correct / max(resolved, 1) * 100, 1) if resolved > 0 else 0.0

    directives = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_judgments": total,
        "correct": correct,
        "unresolved": unresolved,
        "overall_accuracy_pct": overall_accuracy,
        "posture": "hold_bands",
        "band_directives": [],
        "per_region_directives": [],
        "warnings": [],
        "auto_adjustments": [],
    }

    # Determine overall posture
    if overall_accuracy < ACCURACY_CRITICAL * 100:
        directives["posture"] = "tighten_all"
        directives["warnings"].append(
            f"CRITICAL: Overall accuracy {overall_accuracy}% is below {ACCURACY_CRITICAL*100:.0f}%. "
            "Auto-adjustment triggered."
        )
    elif overall_accuracy < 30:
        directives["posture"] = "widen_two_notches"
        directives["warnings"].append(
            f"Low accuracy ({overall_accuracy}%): recommend widening confidence bands."
        )
    elif overall_accuracy < 50:
        directives["posture"] = "widen_one_notch"
        directives["warnings"].append(
            f"Moderate accuracy ({overall_accuracy}%): consider widening bands."
        )

    # Per-band directives
    for band, stats in band_accuracy.items():
        if stats["accuracy_pct"] < 30 and stats["total"] >= MIN_SAMPLES:
            # Find the band to use instead (one notch down)
            band_idx = BANDS.index(band) if band in BANDS else -1
            use_instead = BANDS[band_idx - 1] if band_idx > 0 else band
            directives["band_directives"].append({
                "band": band,
                "accuracy": round(stats["accuracy_pct"] / 100, 3),
                "samples": stats["total"],
                "use_instead": use_instead,
                "reason": f"Only {stats['accuracy_pct']}% accurate over {stats['total']} samples — use '{use_instead}' instead.",
            })

    # Auto-adjustment for critically low accuracy
    if overall_accuracy < ACCURACY_CRITICAL * 100:
        directives["auto_adjustments"].append({
            "setting": "max_kjs_per_region",
            "old_value": 5,
            "new_value": 3,
            "reason": "Accuracy critically low (<10%); reducing KJs forces selectivity and improves calibration.",
        })
        directives["auto_adjustments"].append({
            "setting": "min_bands_per_brief",
            "old_value": 0,
            "new_value": 2,
            "reason": "Enforcing minimum 2 different confidence bands per brief to increase diversity.",
        })

        # Log to health engine
        _log_to_health_engine(
            "WARNING",
            f"Calibration auto-adjustment triggered: accuracy {overall_accuracy}%. "
            f"Reduced max KJs/region to 3, enforced min 2 bands/brief."
        )

    return directives


def _log_to_health_engine(severity: str, message: str) -> None:
    """Write a warning entry to the health engine (brain/memory/semantic/...)."""
    log_entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "source": "calibration_loop",
        "severity": severity,
        "message": message,
    }
    log_path = REPO_ROOT / "brain" / "memory" / "episodic" / f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    print(f"Health log: [{severity}] {message}")


def check(cal_data: dict, directives: dict) -> dict:
    """Run the check subcommand — report calibration status."""
    band_accuracy = compute_per_band_accuracy(cal_data)

    print(f"\n{'='*55}")
    print(f"CALIBRATION ACCURACY REPORT — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
    print(f"{'='*55}")

    total = cal_data.get("total_judgments", 0)
    correct = cal_data.get("correct", 0)
    incorrect = cal_data.get("incorrect", 0)
    unresolved = cal_data.get("unresolved", 0)
    resolved = correct + incorrect
    acc_pct = round(correct / max(resolved, 1) * 100, 1) if resolved > 0 else 0.0

    print(f"Total judgments:  {total}")
    print(f"Correct:          {correct}")
    print(f"Incorrect:        {incorrect}")
    print(f"Unresolved:       {unresolved}")
    print(f"Resolved:         {resolved}")
    print(f"Accuracy:         {acc_pct}%")

    if band_accuracy:
        print(f"\nPer-band accuracy:")
        for band, stats in sorted(band_accuracy.items()):
            pct = stats["accuracy_pct"]
            icon = "✅" if pct >= 50 else "⚠️" if pct >= 20 else "❌"
            print(f"  {icon} {band:25s}: {pct:5.1f}% ({stats['correct']}/{stats['correct']+stats['incorrect']})")

    # Recommendations
    print(f"\nRecommendations:")
    posture = directives.get("posture", "hold_bands")
    print(f"  Posture: {posture}")

    if directives.get("band_directives"):
        print(f"  Band adjustments needed:")
        for bd in directives["band_directives"]:
            print(f"    → '{bd['band']}' → use '{bd['use_instead']}' ({bd['reason']})")

    if directives.get("auto_adjustments"):
        print(f"\n  Auto-adjustments applied:")
        for adj in directives["auto_adjustments"]:
            print(f"    → {adj['setting']}: {adj['old_value']} → {adj['new_value']} ({adj['reason']})")

    print(f"\n  {'='*45}")
    if acc_pct < ACCURACY_CRITICAL * 100:
        print(f"  ⚠ CRITICAL: Accuracy at {acc_pct}%. Auto-adjustments triggered.")
        tone = "WIDEN"
        message = (
            f"Calibration accuracy is critically low ({acc_pct}%). "
            "Recommended: widen/narrow bands and reduce KJs per region."
        )
    elif acc_pct < 30:
        message = (
            f"Calibration accuracy is low ({acc_pct}%). "
            "Recommended: widen confidence bands by one notch globally."
        )
        tone = "WIDEN"
    else:
        message = (
            f"Calibration accuracy at {acc_pct}%. "
            "Standing bands are appropriate."
        )
        tone = "HOLD"
    print(f"  Tone: {tone}")
    print(f"  {message}")
    print(f"{'='*55}\n")

    return {
        "total": total,
        "correct": correct,
        "incorrect": incorrect,
        "unresolved": unresolved,
        "accuracy_pct": acc_pct,
        "posture": posture,
        "message": message,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Calibration accuracy check — postdiction→calibration feedback loop."
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Run calibration accuracy check and report."
    )
    parser.add_argument(
        "--update", action="store_true",
        help="Update calibration directives and behavioral state."
    )
    args = parser.parse_args()

    if not args.check and not args.update:
        args.check = True
        args.update = True

    # Load calibration tracking data
    cal_data = load_json(CALIBRATION_TRACKING)
    if cal_data is None:
        print("ERROR: calibration-tracking.json not found or invalid.", file=sys.stderr)
        print(f"Expected at: {CALIBRATION_TRACKING}", file=sys.stderr)
        return 1

    # Compute per-band accuracy
    band_accuracy = compute_per_band_accuracy(cal_data)

    # Generate directives
    directives = generate_directives(cal_data, band_accuracy)

    # Write directives
    if args.update:
        write_json(CALIBRATION_DIRECTIVES, directives)

    # Check/report
    if args.check:
        check(cal_data, directives)

    return 0


if __name__ == "__main__":
    sys.exit(main())
