"""Weekly creative source brainstorming — identifies non-traditional signals.
Runs on Opus 4.7 every 7 days. Generates 5-10 source hypotheses."""

from __future__ import annotations
import datetime, json, pathlib
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

def plan(state: dict) -> dict | None:
    last = state.get("last_week_0_brainstorm_date", "")
    today = datetime.date.today().isoformat()
    # Only run if not done in last 7 days
    if last and last >= (datetime.date.today() - datetime.timedelta(days=7)).isoformat():
        return None
    return {
        "priority": "medium",
        "estimated_cost": 0.005,
        "estimated_duration_mins": 5,
        "target": "non_traditional_sources",
        "task_type": "weekly_source_brainstorm",
    }

def execute(task: dict) -> dict:
    output_dir = REPO_ROOT / "memory" / "source-discovery"
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / f"{datetime.date.today().isoformat()}-brainstorm.md"
    out.write_text("# Weekly Source Brainstorm (placeholder)\n\nRun to generate creative hypotheses.")
    return {"status": "completed", "action": "brainstorm_queued", "cost": 0.0}
