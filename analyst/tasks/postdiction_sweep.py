"""Resolves expired-horizon judgments using 5-category system.
Updates per-region calibration."""

from __future__ import annotations
import json, pathlib, sys
from typing import Any

CAL_FILE = pathlib.Path(__file__).resolve().parent.parent.parent / "brain" / "memory" / "semantic" / "calibration-tracking.json"

def plan(state: dict) -> dict | None:
    if not CAL_FILE.exists():
        return None
    with open(CAL_FILE) as f:
        cal = json.load(f)
    
    # Count expired un-resolved judgments
    unresolved = cal.get("unresolved", 0)
    if unresolved > 0:
        return {
            "target": str(CAL_FILE),
            "unresolved_count": unresolved,
            "priority": "high",
            "estimated_cost": 0.003,
            "estimated_duration_mins": 5,
        }
    return None

def execute(task: dict) -> dict:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from scripts.postdict import load_calibration_history, recheck_expired
    cal = load_calibration_history()
    result = recheck_expired(cal)
    with open(CAL_FILE, "w") as f:
        json.dump(result, f, indent=2)
    remaining = result.get("unresolved", 0)
    return {
        "task_type": "postdiction_sweep",
        "previous_unresolved": task["unresolved_count"],
        "remaining_unresolved": remaining,
        "resolved": task["unresolved_count"] - remaining,
        "cost": 0.001,
        "status": "completed",
    }
