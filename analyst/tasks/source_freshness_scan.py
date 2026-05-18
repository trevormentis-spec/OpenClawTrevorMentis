"""Runs freshness checker. Generates deepening tasks for stale entities."""

from __future__ import annotations
import json, pathlib, sys, subprocess
from typing import Any

def plan(state: dict) -> dict | None:
    return {
        "target": "all_entity_files",
        "priority": "high",
        "estimated_cost": 0.0,
        "estimated_duration_mins": 1,
    }

def execute(task: dict) -> dict:
    script = pathlib.Path(__file__).resolve().parent.parent.parent / "scripts" / "check_source_freshness.py"
    if not script.exists():
        return {"status": "failed", "error": "check_source_freshness.py not found"}
    
    result = subprocess.run(
        [sys.executable, str(script), "--stale-only", "--json"],
        capture_output=True, text=True, timeout=30
    )
    
    stale = []
    if result.stdout.strip():
        try:
            stale = json.loads(result.stdout)
        except json.JSONDecodeError:
            pass
    
    return {
        "task_type": "source_freshness_scan",
        "stale_entities": stale,
        "stale_count": len(stale),
        "cost": 0.0,
        "status": "completed",
    }
