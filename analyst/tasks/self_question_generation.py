"""Once per day, generates 3-5 subscriber-grade questions the agent
currently can't answer well. Builds queue for capability growth."""

from __future__ import annotations
import json, pathlib, datetime
from typing import Any

GAP_FILE = pathlib.Path(__file__).resolve().parent.parent.parent / "analyst" / "meta" / "capability_gaps.json"

def plan(state: dict) -> dict | None:
    today = datetime.date.today().isoformat()
    last_gen = state.get("last_self_question_date", "")
    if last_gen == today:
        return None  # Already generated today
    return {
        "target": str(GAP_FILE),
        "priority": "medium",
        "estimated_cost": 0.002,
        "estimated_duration_mins": 3,
    }

def execute(task: dict) -> dict:
    # Read existing gap file
    questions = []
    if GAP_FILE.exists():
        with open(GAP_FILE) as f:
            try:
                questions = json.load(f)
            except json.JSONDecodeError:
                questions = []
    
    # For now, generate from known gaps
    new_questions = [
        "What is the municipality-level cartel control map for Guanajuato's industrial corridors?",
        "What is the CFE substation capacity utilization rate for Querétaro's Bernardo Quintana industrial park?",
        "What are the current insurance premium ranges for Bajío industrial properties with cartel-violence coverage?",
        "What is the Cenagas pipeline capacity utilization rate for Querétaro's manufacturing corridor?",
    ]
    
    questions.extend({"question": q, "added": datetime.datetime.utcnow().isoformat() + "Z", "resolved": False} for q in new_questions)
    
    GAP_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(GAP_FILE, "w") as f:
        json.dump(questions, f, indent=2)
    
    return {
        "task_type": "self_question_generation",
        "questions_added": len(new_questions),
        "total_open": sum(1 for q in questions if not q.get("resolved")),
        "cost": 0.0,
        "status": "completed",
    }
