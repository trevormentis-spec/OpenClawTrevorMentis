#!/usr/bin/env python3
"""
lessons_learned.py — Memory-Driven Behavior Loop.

When the system encounters a failure (trade not filled, QC block, source dead),
this writes a structured lesson to procedural memory. The cognition daemon
checks for relevant lessons before executing similar operations.

This closes the feedback loop: memory doesn't just store — it changes behavior.

Schema:
  {
    "id": "uuid",
    "timestamp": "ISO-8601",
    "category": "trade|brief|collection|cognition|source",
    "severity": "high|medium|low",
    "situation": "What happened",
    "root_cause": "Why it happened",
    "action_taken": "What was done to fix it",
    "prevention": "What should be done to prevent recurrence",
    "applied_count": 0,
    "last_applied": null,
    "expires": "ISO-8601 or null for permanent"
  }

Usage:
    python3 scripts/lessons_learned.py --record          # Interactive record
    python3 scripts/lessons_learned.py --check brief      # Check lessons for category
    python3 scripts/lessons_learned.py --list             # List all lessons
    python3 scripts/lessons_learned.py --apply <id>       # Mark lesson as applied
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
import uuid

REPO = pathlib.Path(__file__).resolve().parent.parent
LESSONS_FILE = REPO / "brain" / "memory" / "procedural" / "lessons-learned.json"

# Seed lessons from known system failures
SEEDED_LESSONS = [
    {
        "id": "less-001",
        "timestamp": "2026-05-26T23:00:00Z",
        "category": "brief",
        "severity": "high",
        "situation": "Daily brief QC gate blocked delivery on May 26. One of 7 gates failed.",
        "root_cause": "Model downgrade risk: if session default is Flash, the brief pipeline produces Flash-quality output that fails calibration gates.",
        "action_taken": "Created brief-auto-recovery.sh that retries with forced Pro model selection.",
        "prevention": "Before running brief pipeline, verify model selection is V4 Pro minimum. Add auto-recovery cron at 07:15 PT.",
        "applied": True,
        "applied_count": 1,
        "last_applied": "2026-05-27T00:00:00Z",
        "expires": None,
    },
    {
        "id": "less-002",
        "timestamp": "2026-05-26T23:00:00Z",
        "category": "trade",
        "severity": "high",
        "situation": "88% of trade attempts failed. Resting orders placed but never filled. Pricing logic produced maker prices that didn't execute.",
        "root_cause": "Orders placed at conservative maker prices without fill monitoring or price escalation. 80 of 90 orders sat unfilled.",
        "action_taken": "Added fill monitoring loop with price escalation: check fill at 20s intervals, bump price by 2 cents if unfilled.",
        "prevention": "All trades must include fill monitoring with price escalation. Orders should not rest unfilled for more than 60s.",
        "applied": True,
        "applied_count": 1,
        "last_applied": "2026-05-27T00:00:00Z",
        "expires": None,
    },
    {
        "id": "less-003",
        "timestamp": "2026-05-26T23:00:00Z",
        "category": "cognition",
        "severity": "medium",
        "situation": "Zero weak signals, anomalies, or narrative drift detected across 77 cognition cycles on Flash model.",
        "root_cause": "Flash model (Tier-3) is not capable of reliable pattern detection. Pro model (Tier-2) detected 28 weak signals in first cycle.",
        "action_taken": "Switched primary cognition model from Flash to Pro. Flash is now reserved for triage/ingestion only.",
        "prevention": "Cognition must run on Pro minimum. Flash is excluded from narrative-level analysis. Verify model tier in cognition daemon config.",
        "applied": True,
        "applied_count": 1,
        "last_applied": "2026-05-27T00:00:00Z",
        "expires": None,
    },
    {
        "id": "less-004",
        "timestamp": "2026-05-27T00:00:00Z",
        "category": "collection",
        "severity": "medium",
        "situation": "Only 30 of 996 durable sources tested. Cloud status and physical security RSS feeds returning 403/404 errors silently.",
        "root_cause": "Source health sweep was never completed after the SA source integration. Defunct feeds degrade collection silently.",
        "action_taken": "Implemented batch health testing at 50 sources per cycle via Philby Collector. Auto-disable 3x failed sources.",
        "prevention": "Source health must be tested continuously. Dead feeds must be quarantined and replaced within one cycle.",
        "applied": False,
        "applied_count": 0,
        "last_applied": None,
        "expires": None,
    },
    {
        "id": "less-005",
        "timestamp": "2026-05-27T00:00:00Z",
        "category": "trade",
        "severity": "low",
        "situation": "Ticker resolution failed for KXUSAIRANAGREEMENT because event ticker != series ticker.",
        "root_cause": "Scanner outputs event tickers (KXUSAIRANAGREEMENT) but Kalshi API requires series tickers (KXUSAIRANAGREEMENT-27-26JUN).",
        "action_taken": "Added scanner-style API resolution to convert event → series tickers using get_active_markets().",
        "prevention": "Always resolve event tickers to series tickers via the Kalshi API before placing orders.",
        "applied": True,
        "applied_count": 1,
        "last_applied": "2026-05-27T00:00:00Z",
        "expires": None,
    },
]


def load_lessons() -> list[dict]:
    if LESSONS_FILE.exists():
        try:
            return json.loads(LESSONS_FILE.read_text())
        except (json.JSONDecodeError,):
            pass
    return []


def save_lessons(lessons: list[dict]) -> None:
    LESSONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LESSONS_FILE.write_text(json.dumps(lessons, indent=2))


def cmd_list(args):
    lessons = load_lessons()
    if not lessons:
        print("No lessons recorded.")
        return 0

    print(f"\n=== Lessons Learned ({len(lessons)} total) ===")
    print(f"{'ID':<12} {'Category':<12} {'Severity':<8} {'Applied':<8} {'Count':<6} Situation")
    print("-" * 80)
    for l in sorted(lessons, key=lambda x: x.get("timestamp", ""), reverse=True):
        applied = "✅" if l.get("applied") else "❌"
        count = l.get("applied_count", 0)
        sit = l.get("situation", "")[:50]
        print(f"{l['id']:<12} {l['category']:<12} {l['severity']:<8} {applied:<8} {count:<6} {sit}")
    print()

    # Show prevention tips
    print("\nActive prevention rules (unapplied lessons):")
    for l in lessons:
        if not l.get("applied"):
            print(f"  🔴 {l['id']}: {l['prevention'][:100]}")
    print()
    return 0


def cmd_check(args):
    """Check lessons relevant to a category before an operation."""
    category = args.check or args.category
    if not category:
        print("Specify a category: --check <category>")
        return 1

    lessons = load_lessons()
    relevant = [l for l in lessons if l["category"] == category]
    if not relevant:
        print(f"No lessons for category '{category}'")
        return 0

    print(f"\n=== Lessons: {category} ({len(relevant)}) ===")
    for l in relevant:
        status = "✅ Applied" if l.get("applied") else "❌ Unapplied"
        print(f"\n  [{l['id']}] {status}")
        print(f"  Situation: {l['situation'][:100]}")
        print(f"  Prevention: {l['prevention'][:120]}")
        print(f"  Applied {l.get('applied_count', 0)} times"
              + (f" (last: {l['last_applied'][:19]})" if l.get('last_applied') else ""))
    print()
    return 0


def cmd_record(args):
    """Record a new lesson."""
    lesson = {
        "id": f"less-{str(uuid.uuid4())[:8]}",
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "category": args.category or "general",
        "severity": args.severity or "medium",
        "situation": args.situation or "Manual record",
        "root_cause": args.root_cause or "Unknown",
        "action_taken": args.action or "None",
        "prevention": args.prevention or "Monitor and verify",
        "applied": False,
        "applied_count": 0,
        "last_applied": None,
        "expires": None,
    }
    lessons = load_lessons()
    lessons.append(lesson)
    save_lessons(lessons)
    print(f"Recorded lesson: {lesson['id']}")
    return 0


def cmd_apply(args):
    """Mark a lesson as applied."""
    lessons = load_lessons()
    for l in lessons:
        if l["id"] == args.apply:
            l["applied"] = True
            l["applied_count"] = l.get("applied_count", 0) + 1
            l["last_applied"] = dt.datetime.now(dt.timezone.utc).isoformat()
            save_lessons(lessons)
            print(f"Applied: {l['id']} — {l['situation'][:80]}")
            return 0
    print(f"Lesson not found: {args.apply}")
    return 1


def main():
    # Seed lessons on first run
    if not LESSONS_FILE.exists():
        save_lessons(SEEDED_LESSONS)
        print(f"Seeded {len(SEEDED_LESSONS)} initial lessons")

    parser = argparse.ArgumentParser(description="Lessons Learned Memory Loop")
    parser.add_argument("--list", action="store_true", help="List all lessons")
    parser.add_argument("--check", default="", help="Check lessons for a category (brief, trade, cognition, collection)")
    parser.add_argument("--record", action="store_true", help="Record a new lesson")
    parser.add_argument("--category", default="", help="Lesson category")
    parser.add_argument("--severity", default="medium", help="Lesson severity")
    parser.add_argument("--situation", default="", help="What happened")
    parser.add_argument("--root-cause", default="", help="Why it happened")
    parser.add_argument("--action", default="", help="Action taken")
    parser.add_argument("--prevention", default="", help="Prevention rule")
    parser.add_argument("--apply", default="", help="Mark lesson ID as applied")
    args = parser.parse_args()

    if args.list:
        return cmd_list(args)
    elif args.check:
        return cmd_check(args)
    elif args.apply:
        return cmd_apply(args)
    elif args.record:
        return cmd_record(args)
    else:
        return cmd_list(args)


if __name__ == "__main__":
    sys.exit(main())
