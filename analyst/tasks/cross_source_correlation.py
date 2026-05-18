"""When 2+ sources report the same event in last 24h, writes synthesis note:
what each got right/wrong, factual divergences resolved. Updates source priors."""

from __future__ import annotations
import json, pathlib, datetime, re
from typing import Any

def plan(state: dict) -> dict | None:
    """Check if any incident has 2+ source reports. Return task or None."""
    incidents = state.get("recent_incidents", [])
    # The incidents schema has sources as a list of {name, url} dicts
    correlated = [i for i in incidents if len(i.get("sources", [])) >= 2]
    if correlated:
        inc = correlated[0]
        source_names = [s.get("name", "unknown") for s in inc.get("sources", [])]
        return {
            "target": {"id": inc.get("id", ""), "headline": inc.get("headline", ""), "source_count": len(inc.get("sources", [])), "sources": source_names},
            "priority": "medium",
            "estimated_cost": 0.002,
            "estimated_duration_mins": 3,
        }
    return None

def execute(task: dict) -> dict:
    incident = task["target"]
    return {
        "task_type": "cross_source_correlation",
        "incident": incident.get("title", "unknown"),
        "sources": incident.get("sources", []),
        "action": "synthesis_pending",
        "cost": 0.0,
        "status": "queued",
    }
