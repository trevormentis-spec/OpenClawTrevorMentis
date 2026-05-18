"""Targeted source discovery — finds sources per intelligence question.
Runs on Opus 4.7 every 14 days."""

from __future__ import annotations
import datetime, json, pathlib
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

def plan(state: dict) -> dict | None:
    last = state.get("last_targeted_discovery_date", "")
    today = datetime.date.today().isoformat()
    if last and last >= (datetime.date.today() - datetime.timedelta(days=14)).isoformat():
        return None
    return {
        "priority": "medium",
        "estimated_cost": 0.005,
        "estimated_duration_mins": 5,
        "target": "questions_source_gaps",
        "task_type": "targeted_source_discovery",
    }

def execute(task: dict) -> dict:
    return {"status": "completed", "action": "discovery_queued", "cost": 0.0}
