#!/usr/bin/env python3
"""
nudge_check.py — Self-improvement nudge system.

Checks recent session activity for complex task completion and prompts
skill creation / memory updates. Designed to be called from heartbeat.

Usage:
    python3 scripts/nudge_check.py           # Check and print nudges
    python3 scripts/nudge_check.py --status   # Show nudge history
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import datetime

REPO = pathlib.Path(__file__).resolve().parent.parent
BRAIN_DIR = REPO / "brain"
NUDGE_LOG = BRAIN_DIR / "meta" / "nudge-log.jsonl"
SEMANTIC_DIR = BRAIN_DIR / "memory" / "semantic"
EPISODIC_DIR = BRAIN_DIR / "memory" / "episodic"
SKILLS_DIR = REPO / "skills" / "trevor"


def log_nudge(nudge: dict):
    """Append a nudge to the log."""
    NUDGE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(NUDGE_LOG, "a") as f:
        f.write(json.dumps(nudge) + "\n")


def get_recent_sessions(count: int = 3) -> list[dict]:
    """Read recent episodic logs for session complexity hints."""
    sessions = []
    if EPISODIC_DIR.exists():
        files = sorted(EPISODIC_DIR.glob("*.jsonl"), reverse=True)[:count]
        for f in files:
            try:
                for line in f.read_text().strip().split("\n")[-20:]:  # last 20 lines per file
                    if line:
                        sessions.append(json.loads(line))
            except:
                pass
    return sessions


def estimate_session_complexity(sessions: list[dict]) -> dict:
    """Estimate complexity from recent session data."""
    tool_call_count = 0
    error_count = 0
    correction_count = 0
    outcomes = []
    
    for s in sessions:
        action = s.get("action", s.get("type", ""))
        if "tool" in action.lower() or "function" in action.lower() or "exec" in action.lower():
            tool_call_count += 1
        if "error" in action.lower() or "fail" in str(s.get("content", "")).lower():
            error_count += 1
        if "correction" in str(s.get("content", "")).lower() or "mistake" in str(s.get("content", "")).lower():
            correction_count += 1
        outcomes.append(s.get("content", "")[:100])
    
    return {
        "tool_calls": tool_call_count,
        "errors": error_count,
        "corrections": correction_count,
        "session_count": len(sessions),
        "is_complex": tool_call_count >= 5,
        "has_corrections": correction_count > 0,
        "has_errors": error_count > 0,
    }


def check() -> list[str]:
    """Run the nudge check and return actionable nudges."""
    nudges = []
    sessions = get_recent_sessions(5)
    complexity = estimate_session_complexity(sessions)
    
    # Nudge 1: Complex task completed
    if complexity["is_complex"]:
        existing_skills = list(SKILLS_DIR.rglob("*.md"))
        nudges.append(
            f"📝 NUDGE: You completed {complexity['tool_calls']} tool calls recently. "
            f"Consider saving this workflow as a skill in skills/trevor/ if it's repeatable. "
            f"Skills exist: {len(existing_skills)}"
        )
    
    # Nudge 2: User correction received
    if complexity["has_corrections"]:
        nudges.append(
            f"🔧 NUDGE: User correction detected. Update MEMORY.md or brain semantic "
            f"memory so the correction is durable."
        )
    
    # Nudge 3: Error recovery
    if complexity["has_errors"]:
        nudges.append(
            f"⚠️ NUDGE: {complexity['errors']} error(s) detected. If you found a working "
            f"workaround, save it as a skill pitfall or reference note."
        )
    
    # Nudge 4: Skill registry needs rebuild
    registry_path = REPO / "skills" / "registry.json"
    if registry_path.exists():
        registry_age = datetime.datetime.now() - datetime.datetime.fromtimestamp(
            registry_path.stat().st_mtime
        )
        if registry_age.total_seconds() > 3600:  # 1 hour
            nudges.append(
                f"🔄 NUDGE: Skill registry is {int(registry_age.total_seconds() // 60)}m old. "
                f"Run: python3 scripts/skill_registry.py --rebuild"
            )
    else:
        nudges.append(
            f"🆕 NUDGE: No skill registry found. Run: python3 scripts/skill_registry.py --rebuild"
        )
    
    return nudges


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Self-improvement nudge system")
    parser.add_argument("--status", action="store_true", help="Show nudge history")
    args = parser.parse_args()
    
    if args.status:
        if NUDGE_LOG.exists():
            for line in NUDGE_LOG.read_text().strip().split("\n"):
                if line:
                    print(json.dumps(json.loads(line), indent=2))
        else:
            print("No nudge history yet.")
        return 0
    
    nudges = check()
    
    if nudges:
        print("🧠 Self-Improvement Nudges:")
        for n in nudges:
            print(f"\n  {n}")
    else:
        print("✅ No nudges — everything looks clean.")
    
    log_nudge({
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "nudges": nudges,
        "count": len(nudges),
    })
    
    return 0 if not nudges else 1


if __name__ == "__main__":
    sys.exit(main())
