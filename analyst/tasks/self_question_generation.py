"""Once per day, uses LLM to generate 3-5 subscriber-grade questions the agent
currently can't answer well. Builds queue for capability growth.
Replaces previously hardcoded Mexico-specific questions with dynamic generation.
"""
from __future__ import annotations

import datetime
import json
import pathlib
import sys
from typing import Any

_parent = pathlib.Path(__file__).resolve().parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

from tasks.llm_helper import call_llm

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
GAP_FILE = REPO_ROOT / "analyst" / "meta" / "capability_gaps.json"

QUESTION_SYSTEM = """You are an intelligence analyst identifying capability gaps — questions a
geopolitical intelligence service should be able to answer but currently cannot.

Review the existing gap list and the current analytical context. Generate 3-5
NEW questions that:
1. Cannot be answered from publicly available data feeds alone
2. Would materially improve the analytical product if answered
3. Are specific enough to be actionable ("What is X's position on Y?" not "What is happening in region Z?")
4. Cover a variety of regions and domains

Output valid JSON:
{
  "questions": [
    {
      "question": "<specific, actionable question>",
      "domain": "<geopolitical|security|economic|energy|technology|military>",
      "region": "<global region or 'global'>",
      "why_important": "<one sentence on why this question matters>",
      "collectability": "<high|medium|low — how feasible is it to answer this?>"
    }
  ],
  "most_urgent": "<index of the single most important question in the list>",
  "gap_theme": "<one-sentence theme describing the pattern across these questions>"
}"""


def plan(state: dict) -> dict | None:
    today = datetime.date.today().isoformat()
    last_gen = state.get("last_self_question_date", "")
    if last_gen == today:
        return None
    return {
        "target": str(GAP_FILE),
        "priority": "medium",
        "estimated_cost": 0.002,
        "estimated_duration_mins": 3,
    }


def execute(task: dict) -> dict:
    """Generate new capability questions using an LLM."""
    # Load existing questions for context
    existing = []
    if GAP_FILE.exists():
        try:
            existing = json.loads(GAP_FILE.read_text())
        except (json.JSONDecodeError, Exception):
            existing = []

    existing_qs = [q.get("question", "") for q in existing[-20:]]
    existing_text = "\n".join(f"- {q}" for q in existing_qs) if existing_qs else "(no existing questions)"

    # Get brief context if available — today's BLUF
    today = datetime.date.today().isoformat()
    brief_dir = pathlib.Path.home() / "trevor-briefings" / today.isoformat() / "analysis"
    brief_context = "No brief available for context."
    exec_summary = brief_dir / "exec_summary.json"
    if exec_summary.exists():
        try:
            data = json.loads(exec_summary.read_text())
            brief_context = f"Today's BLUF: {data.get('bluf', 'No BLUF')}"
            kjs = data.get("five_judgments", [])
            if kjs:
                brief_context += "\n\nKey Judgments:"
                for kj in kjs[:3]:
                    brief_context += f"\n- [{kj.get('drawn_from_region', '?')}] {kj.get('statement', '')}"
        except Exception:
            pass

    user_prompt = f"""EXISTING GAP QUESTIONS:
{existing_text}

CURRENT ANALYTICAL CONTEXT:
{brief_context}

TASK: Generate 3-5 NEW capability gap questions that this intelligence service
should work toward answering. These should be questions that are NOT already in
the existing list and NOT answered by today's brief."""

    result = call_llm(
        system=QUESTION_SYSTEM,
        user=user_prompt,
        model="deepseek/deepseek-v4-pro",
        provider="deepseek",
        max_tokens=2048,
    )

    if result.get("error"):
        return {"task_type": "self_question_generation", "error": result["error"], "status": "failed"}

    parsed = result.get("parsed", {})
    questions = parsed.get("questions", [])

    if not questions:
        return {"task_type": "self_question_generation", "questions_added": 0,
                "status": "no_questions_generated"}

    # Add to gap file
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for q in questions:
        existing.append({
            "question": q.get("question", ""),
            "domain": q.get("domain", "geopolitical"),
            "region": q.get("region", "global"),
            "why_important": q.get("why_important", ""),
            "collectability": q.get("collectability", "medium"),
            "added": now,
            "resolved": False,
        })

    GAP_FILE.parent.mkdir(parents=True, exist_ok=True)
    GAP_FILE.write_text(json.dumps(existing, indent=2, ensure_ascii=False))

    return {
        "task_type": "self_question_generation",
        "questions_added": len(questions),
        "total_open": sum(1 for q in existing if not q.get("resolved")),
        "most_urgent": questions[parsed.get("most_urgent", 0)].get("question", "") if questions else "",
        "gap_theme": parsed.get("gap_theme", ""),
        "cost": 0.002,
        "status": "completed",
    }
