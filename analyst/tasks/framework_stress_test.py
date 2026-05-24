"""For significant incidents, runs relevant analytical framework through LLM.
If framework can't accommodate cleanly, logs capability gap for methodology refinement.
"""
from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

_parent = pathlib.Path(__file__).resolve().parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

from tasks.llm_helper import call_llm

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

FRAMEWORKS = {
    "concentric_physical": "analyst/knowledge/leo_ground_stations/frameworks/concentric-physical-security-methodology.md",
    "lloyds_insurance": "analyst/knowledge/leo_ground_stations/frameworks/lloyds-insurance-market.md",
}

STRESS_SYSTEM = """You are an analytical methodologist stress-testing an intelligence framework.
You receive a framework document and an incident. Your task:

1. Apply the framework to the incident — can it accommodate the case cleanly?
2. If yes: produce a structured analysis using the framework's categories.
3. If no: identify EXACTLY where the framework breaks — what concept, assumption,
   or category is missing. This is a capability gap.

Output valid JSON:
{
  "framework_accommodates": true/false,
  "analysis": "<framework-structured analysis of the incident, or explanation of breakage>",
  "gap_found": "<if framework breaks, describe the specific missing concept>",
  "framework_score": <1-10, how well the framework handled this case>,
  "methodology_recommendation": "<one-sentence recommendation for improving the framework>"
}"""


def plan(state: dict) -> dict | None:
    incidents = state.get("recent_incidents", [])
    testable_categories = ("security", "crime", "political", "energy")
    testable = [i for i in incidents if i.get("category", "").lower() in testable_categories]
    if testable:
        inc = testable[0]
        return {
            "target": {
                "id": inc.get("id", ""),
                "headline": inc.get("headline", ""),
                "category": inc.get("category", ""),
            },
            "priority": "low",
            "estimated_cost": 0.002,
            "estimated_duration_mins": 2,
        }
    return None


def execute(task: dict) -> dict:
    """Stress-test a framework against an incident using an LLM."""
    incident = task["target"]
    headline = incident.get("headline", "unknown")
    category = incident.get("category", "security")

    # Pick the most relevant framework based on category
    framework_key = "concentric_physical"
    if category == "energy":
        framework_key = "lloyds_insurance"

    framework_path = REPO_ROOT / FRAMEWORKS.get(framework_key, list(FRAMEWORKS.values())[0])

    framework_text = ""
    if framework_path.exists():
        framework_text = framework_path.read_text()[:4000]
    else:
        return {
            "task_type": "framework_stress_test",
            "incident": headline,
            "error": f"Framework not found: {framework_path}",
            "status": "failed",
        }

    user_prompt = f"""FRAMEWORK: {framework_key}
CATEGORY: {category}
INCIDENT: {headline}

FRAMEWORK CONTENT:
{framework_text}

TASK: Apply this framework to the incident. Can it accommodate this case cleanly?"""

    result = call_llm(
        system=STRESS_SYSTEM,
        user=user_prompt,
        model="deepseek/deepseek-v4-pro",
        provider="deepseek",
        max_tokens=2048,
    )

    if result.get("error"):
        return {"task_type": "framework_stress_test", "incident": headline,
                "error": result["error"], "status": "failed"}

    parsed = result.get("parsed", {})
    return {
        "task_type": "framework_stress_test",
        "incident": headline,
        "framework": framework_key,
        "accommodates": parsed.get("framework_accommodates"),
        "score": parsed.get("framework_score"),
        "gap_found": parsed.get("gap_found", ""),
        "recommendation": parsed.get("methodology_recommendation", ""),
        "cost": 0.002,
        "status": "completed",
    }
