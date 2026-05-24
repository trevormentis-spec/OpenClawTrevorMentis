"""When 2+ sources report the same event, uses LLM to write a synthesis note:
what each source got right/wrong, factual divergences resolved. Updates source priors.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from typing import Any

_parent = pathlib.Path(__file__).resolve().parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

from tasks.llm_helper import call_llm

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CORRELATION_DIR = REPO_ROOT / "analysis" / "source_correlations"

CORRELATION_SYSTEM = """You are an intelligence analyst performing cross-source correlation.
You receive one incident reported by multiple sources. Your task:

1. Identify factual DIVERGENCES between sources — what did Source A report that
   Source B didn't? What numbers differ?
2. Assess which source appears MORE RELIABLE for this specific incident and why.
3. Write a synthesis note: the likely ground truth based on cross-referencing.
4. Update source reliability priors — flag any source that was clearly wrong.

Output valid JSON:
{
  "ground_truth_assessment": "<most likely version of events based on cross-referencing>",
  "divergences": [
    {"source": "Source A", "claim": "what they reported", "assessment": "likely correct|likely incorrect|unverifiable"}
  ],
  "most_reliable_source": "<source name>",
  "reliability_notes": "<why the most reliable source is preferred>",
  "source_prior_update": [
    {"source": "<name>", "adjustment": "<upgrade|downgrade|hold>", "reason": "<why>"}
  ],
  "confidence": "<high|moderate|low> — how confident is the synthesis"
}"""


def plan(state: dict) -> dict | None:
    """Check if any incident has 2+ source reports."""
    incidents = state.get("recent_incidents", [])
    correlated = [i for i in incidents if len(i.get("sources", [])) >= 2]
    if correlated:
        inc = correlated[0]
        source_names = [s.get("name", "unknown") for s in inc.get("sources", [])]
        return {
            "target": {
                "id": inc.get("id", ""),
                "headline": inc.get("headline", ""),
                "summary": inc.get("summary", "")[:500],
                "source_count": len(inc.get("sources", [])),
                "sources": source_names,
            },
            "priority": "medium",
            "estimated_cost": 0.002,
            "estimated_duration_mins": 3,
        }
    return None


def execute(task: dict) -> dict:
    """Correlate multiple sources on the same event using an LLM."""
    incident = task["target"]
    headline = incident.get("headline", "unknown")
    summary = incident.get("summary", "")
    sources = incident.get("sources", [])

    if len(sources) < 2:
        return {"task_type": "cross_source_correlation", "incident": headline,
                "error": "Need 2+ sources for correlation", "status": "skipped"}

    # Build source list
    source_lines = "\n".join(f"- {s}" for s in sources)

    user_prompt = f"""INCIDENT: {headline}

SUMMARY: {summary}

SOURCES REPORTING THIS INCIDENT:
{source_lines}

TASK: Cross-reference these sources. What are the factual divergences?
Which source is most reliable? What is the likely ground truth?"""

    result = call_llm(
        system=CORRELATION_SYSTEM,
        user=user_prompt,
        model="deepseek/deepseek-v4-pro",
        provider="deepseek",
        max_tokens=2048,
    )

    if result.get("error"):
        return {"task_type": "cross_source_correlation", "incident": headline,
                "error": result["error"], "status": "failed"}

    parsed = result.get("parsed", {})

    # Save correlation report
    CORRELATION_DIR.mkdir(parents=True, exist_ok=True)
    inc_id = incident.get("id", "unknown")
    report_path = CORRELATION_DIR / f"correlation-{inc_id}.json"
    report_path.write_text(json.dumps(parsed, indent=2, ensure_ascii=False))

    return {
        "task_type": "cross_source_correlation",
        "incident": headline,
        "sources_count": len(sources),
        "divergences_found": len(parsed.get("divergences", [])),
        "most_reliable": parsed.get("most_reliable_source", ""),
        "confidence": parsed.get("confidence", "moderate"),
        "report_saved": str(report_path),
        "cost": 0.002,
        "status": "completed",
    }
