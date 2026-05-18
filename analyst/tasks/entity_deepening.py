"""Selects least-recently-deepened entity, weighted by recent-incident relevance.
Pulls fresh source content, adds incidents with citations, updates last_source_date.
Quality bar: 1500w target. Must pass fabrication_check.py."""

from __future__ import annotations
import json, pathlib, datetime, re, os
from typing import Any

ACTORS_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "brain" / "memory" / "semantic" / "mexico" / "actors"
MIN_WORDS = 800
TARGET_WORDS = 1200

def plan(state: dict) -> dict[str, Any] | None:
    """Select the entity most in need of deepening. Returns task spec or None."""
    best = None
    best_score = float('-inf')
    
    if not ACTORS_DIR.exists():
        return None
    
    for f in sorted(ACTORS_DIR.glob("*.md")):
        text = f.read_text()
        words = len(text.split())
        
        # Extract last_source_date
        lsd_match = re.search(r"last[_ ]source[_ ]date.*?(\d{4}-\d{2}-\d{2})", text, re.IGNORECASE)
        last_date = datetime.date.fromisoformat(lsd_match.group(1)) if lsd_match else datetime.date(2026, 1, 1)
        days_since = (datetime.date.today() - last_date).days
        
        # Score: higher = more needed (below target words, older)
        word_shortfall = max(0, TARGET_WORDS - words)
        staleness = max(0, days_since - 14) * 2  # 14-day grace period
        score = word_shortfall + staleness
        
        if score > best_score:
            best_score = score
            best = {
                "file": str(f),
                "name": f.stem,
                "words": words,
                "last_source_date": str(last_date),
                "days_since_update": days_since,
                "priority": "high" if score > 500 else ("medium" if score > 200 else "low"),
                "estimated_cost": 0.006,
                "estimated_duration_mins": 5,
            }
    
    return best

def execute(task: dict[str, Any]) -> dict[str, Any]:
    """Execute a deepening task. Returns result dict."""
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    
    filepath = task["file"]
    with open(filepath) as f:
        original = f.read()
    
    # For MVP: flag that this entity needs deepening
    # Full implementation would call DeepSeek with fresh per-source data
    result = {
        "task_type": "entity_deepening",
        "entity": task["name"],
        "action": "needs_deepening",
        "current_words": task["words"],
        "target_words": TARGET_WORDS,
        "days_since_update": task["days_since_update"],
        "note": "Deepening requires fresh source fetch + LLM pass. Generated task for worker.",
        "cost": 0.0,
        "status": "queued",
    }
    return result
