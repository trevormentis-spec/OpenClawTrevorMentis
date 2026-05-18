"""For significant incidents, runs relevant framework. If framework can't
accommodate cleanly, logs capability gap."""

from __future__ import annotations
import json, pathlib
from typing import Any

FRAMEWORKS = {
    "cartel_factional": "analyst/knowledge/mexico/frameworks/cartel-factional-dynamics.md",
    "huachicoleo": "analyst/knowledge/mexico/frameworks/huachicoleo.md",
}

def plan(state: dict) -> dict | None:
    incidents = state.get("recent_incidents", [])
    # Use category as severity proxy: security/crime incidents are test-worthy
    testable_categories = ("security", "crime", "political", "energy")
    testable = [i for i in incidents if i.get("category", "").lower() in testable_categories]
    if testable:
        inc = testable[0]
        return {
            "target": {"id": inc.get("id", ""), "headline": inc.get("headline", ""), "category": inc.get("category", "")},
            "priority": "low",
            "estimated_cost": 0.001,
            "estimated_duration_mins": 2,
            "estimated_cost": 0.001,
        }
    return None

def execute(task: dict) -> dict:
    return {
        "task_type": "framework_stress_test",
        "incident": task["target"].get("title", "unknown"),
        "action": "test_pending",
        "cost": 0.0,
        "status": "queued",
    }
