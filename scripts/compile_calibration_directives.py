#!/usr/bin/env python3
"""
Compile calibration-tracking.json into concrete behavioral directives.

Closes the postdiction → behavioral-state loop. Reads:
  brain/memory/semantic/calibration-tracking.json

Writes:
  brain/memory/semantic/calibration-directives.json — compiled directives
  brain/memory/semantic/behavioral-state.json — merged into existing state
    (creates/updates the `calibration_directives.overall` block that
     skills/daily-intel-brief/scripts/analyze.py already reads.)

Concrete rules:
  - Any confidence band with >= MIN_SAMPLES judgments and accuracy below
    threshold gets a downshift directive (e.g. "almost certain" at 40% →
    "downshift to highly likely until accuracy ≥ 70%").
  - Any region/theme with >= MIN_SAMPLES judgments and accuracy below
    threshold is flagged as overconfidence_region; analyze.py already
    consumes this list.
  - Running accuracy drives an overall posture stance ("hold bands",
    "widen one notch", "widen two notches").

This is run from daily-brief-cron.sh after postdict.py, before the next
day's brief.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CAL_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "calibration-tracking.json"
DIRECTIVES_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "calibration-directives.json"
BEHAVIORAL_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "behavioral-state.json"

# Band ordering, from widest (least committal) to narrowest
BAND_LADDER = ["even chance", "likely", "highly likely", "almost certain"]

MIN_SAMPLES = 5
ACCURACY_FLOOR = 0.60          # Below this, downshift the band
REGION_ACC_FLOOR = 0.55        # Below this, flag region for overconfidence


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[cal-compile {ts}] {msg}", file=sys.stderr, flush=True)


def downshift(band: str) -> str:
    """Move one rung wider on the band ladder. 'even chance' is the floor."""
    try:
        i = BAND_LADDER.index(band)
    except ValueError:
        return band
    return BAND_LADDER[max(0, i - 1)]


def band_accuracy(stats: dict) -> tuple[int, float | None]:
    total = stats.get("total", 0)
    correct = stats.get("correct", 0)
    incorrect = stats.get("incorrect", 0)
    resolved = correct + incorrect
    if resolved == 0:
        return total, None
    return total, round(correct / resolved, 3)


def compile_directives(cal: dict) -> dict:
    band_directives = []
    for band_name in BAND_LADDER:
        stats = cal.get("by_confidence_band", {}).get(band_name, {})
        total, acc = band_accuracy(stats)
        if total < MIN_SAMPLES or acc is None:
            continue
        if acc < ACCURACY_FLOOR:
            band_directives.append({
                "band": band_name,
                "accuracy": acc,
                "samples": total,
                "action": "downshift",
                "use_instead": downshift(band_name),
                "rationale": (
                    f"'{band_name}' is {int(acc*100)}% accurate over {total} judgments — "
                    f"below {int(ACCURACY_FLOOR*100)}% floor. Use '{downshift(band_name)}' instead "
                    f"until band-level accuracy recovers."
                ),
            })

    overconfidence_regions = []
    region_table = []
    for region, stats in cal.get("by_region", {}).items():
        total, acc = band_accuracy(stats)
        if total < MIN_SAMPLES or acc is None:
            continue
        region_table.append({"region": region, "accuracy": acc, "samples": total})
        if acc < REGION_ACC_FLOOR:
            overconfidence_regions.append(region)

    total_judgments = cal.get("total_judgments", 0)
    correct = cal.get("correct", 0)
    incorrect = cal.get("incorrect", 0)
    unresolved = cal.get("unresolved", 0)
    resolved = correct + incorrect
    overall_acc = round(correct / resolved, 3) if resolved else None

    if overall_acc is None:
        posture = "insufficient_data"
    elif overall_acc < 0.50:
        posture = "widen_two_notches"
    elif overall_acc < 0.65:
        posture = "widen_one_notch"
    else:
        posture = "hold_bands"

    directives = {
        "compiled_at": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
        "overall": {
            "total_judgments": total_judgments,
            "correct": correct,
            "incorrect": incorrect,
            "unresolved": unresolved,
            "accuracy_pct": round((overall_acc or 0) * 100, 1),
            "posture": posture,
            "overconfidence_regions": overconfidence_regions,
        },
        "band_directives": band_directives,
        "region_table": sorted(region_table, key=lambda r: r["accuracy"]),
    }
    return directives


def merge_into_behavioral_state(directives: dict) -> None:
    if BEHAVIORAL_FILE.exists():
        try:
            state = json.loads(BEHAVIORAL_FILE.read_text())
        except json.JSONDecodeError:
            state = {}
    else:
        state = {}

    cal_block = state.setdefault("calibration_directives", {})
    cal_block["overall"] = directives["overall"]
    cal_block["band_directives"] = directives["band_directives"]
    cal_block["region_table"] = directives["region_table"]
    cal_block["compiled_at"] = directives["compiled_at"]
    state["updated_at"] = directives["compiled_at"]

    BEHAVIORAL_FILE.write_text(json.dumps(state, indent=2))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true",
                   help="print directives without writing")
    args = p.parse_args()

    if not CAL_FILE.exists():
        log(f"no calibration history at {CAL_FILE} — nothing to compile")
        return 0

    cal = json.loads(CAL_FILE.read_text())
    directives = compile_directives(cal)

    if args.dry_run:
        print(json.dumps(directives, indent=2))
        return 0

    DIRECTIVES_FILE.parent.mkdir(parents=True, exist_ok=True)
    DIRECTIVES_FILE.write_text(json.dumps(directives, indent=2))
    merge_into_behavioral_state(directives)

    overall = directives["overall"]
    log(
        f"compiled: posture={overall['posture']} "
        f"overall={overall['accuracy_pct']}% "
        f"band_directives={len(directives['band_directives'])} "
        f"overconfidence_regions={len(overall['overconfidence_regions'])}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
