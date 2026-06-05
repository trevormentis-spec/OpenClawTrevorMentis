#!/usr/bin/env python3
"""
frozen_snapshot.py — Memory freeze pattern for Trevor.

Snapshots memory at session start into a frozen block that doesn't change
mid-session. Memory writes during the session go to disk immediately but
only appear in the NEXT session's snapshot. This preserves the LLM's prefix
cache and prevents context thrashing.

Usage:
    python3 scripts/frozen_snapshot.py              # Generate snapshot, print to stdout
    python3 scripts/frozen_snapshot.py --save       # Generate and save to brain/snapshot.json
    python3 scripts/frozen_snapshot.py --status     # Show current snapshot info
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import datetime

REPO = pathlib.Path(__file__).resolve().parent.parent
MEMORY_DIR = REPO / "memory"
BRAIN_DIR = REPO / "brain"
SNAPSHOT_PATH = BRAIN_DIR / "snapshot.json"
SEMANTIC_DIR = BRAIN_DIR / "memory" / "semantic"
PROCEDURAL_DIR = BRAIN_DIR / "memory" / "procedural"


# ── Config (matches Hermes-inspired char limits) ──
MEMORY_CHAR_LIMIT = 2200


def get_memory_entries() -> list[dict]:
    """Collect memory entries from semantic store and daily logs."""
    entries = []
    
    # 1. Semantic memory (durable facts)
    if SEMANTIC_DIR.exists():
        for f in sorted(SEMANTIC_DIR.glob("*.md")):
            content = f.read_text(encoding="utf-8").strip()
            if content and len(content) > 20:  # skip empty or stub files
                entries.append({
                    "source": "semantic",
                    "key": f.stem,
                    "content": content[:500],  # truncate to keep snapshot focused
                    "path": str(f.relative_to(REPO)),
                })
    
    # 2. Today's daily log (if exists)
    today = datetime.date.today()
    today_log = MEMORY_DIR / f"{today.isoformat()}.md"
    if today_log.exists():
        content = today_log.read_text(encoding="utf-8").strip()
        if content:
            entries.append({
                "source": "daily_log",
                "key": today.isoformat(),
                "content": content[:1000],
                "path": str(today_log.relative_to(REPO)),
            })
    
    # 3. Procedural memory (skills, methods)
    if PROCEDURAL_DIR.exists():
        for f in sorted(PROCEDURAL_DIR.glob("*.md")):
            content = f.read_text(encoding="utf-8").strip()
            if content and len(content) > 50:
                entries.append({
                    "source": "procedural",
                    "key": f.stem,
                    "content": content[:400],
                    "path": str(f.relative_to(REPO)),
                })
    
    return entries


def estimate_capacity(entries: list[dict]) -> int:
    """Estimate memory capacity percentage."""
    total = sum(len(e["content"]) for e in entries)
    pct = min(100, int(total / MEMORY_CHAR_LIMIT * 100))
    return pct


def build_snapshot() -> dict:
    """Build a frozen memory snapshot."""
    entries = get_memory_entries()
    capacity_pct = estimate_capacity(entries)
    
    snapshot = {
        "snapshot_time": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session_date": datetime.date.today().isoformat(),
        "memory_capacity_pct": capacity_pct,
        "entry_count": len(entries),
        "schema": "https://trevormentis.spec/memory-freeze/v1",
        "entries": entries[:8],  # cap at 8 entries to keep snapshot focused
    }
    
    return snapshot


def format_snapshot_for_context(snapshot: dict) -> str:
    """Format the snapshot into a frozen block suitable for injection."""
    lines = []
    lines.append("═══ MEMORY SNAPSHOT (frozen at session start) ═══")
    lines.append(f"Loaded: {snapshot['snapshot_time']}")
    lines.append(f"Capacity: {snapshot['memory_capacity_pct']}% | Entries: {snapshot['entry_count']}")
    lines.append("")
    
    for i, entry in enumerate(snapshot.get("entries", [])):
        source_icon = {"semantic": "🧠", "daily_log": "📋", "procedural": "📚"}
        icon = source_icon.get(entry["source"], "📄")
        lines.append(f"{icon} [{entry['source']}] {entry['key']}")
        lines.append(f"   {entry['content'][:200]}")
        if len(entry['content']) > 200:
            lines.append(f"   ... ({len(entry['content'])} chars total)")
        lines.append("")
    
    lines.append("═══════════════════════════════════════════")
    lines.append("")
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Memory freeze snapshot")
    parser.add_argument("--save", action="store_true", help="Save snapshot to brain/snapshot.json")
    parser.add_argument("--status", action="store_true", help="Show current snapshot info")
    args = parser.parse_args()
    
    if args.status:
        if SNAPSHOT_PATH.exists():
            snap = json.loads(SNAPSHOT_PATH.read_text())
            age = (datetime.datetime.utcnow() - datetime.datetime.strptime(
                snap["snapshot_time"], "%Y-%m-%dT%H:%M:%SZ")).total_seconds()
            print(f"Snapshot: {snap['snapshot_time']} ({int(age)}s old)")
            print(f"Capacity: {snap['memory_capacity_pct']}%")
            print(f"Entries: {snap['entry_count']}")
        else:
            print("No snapshot exists.")
        return 0
    
    snapshot = build_snapshot()
    
    if args.save:
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2))
        print(f"[freeze] Snapshot saved to {SNAPSHOT_PATH}")
        print(f"[freeze] {snapshot['entry_count']} entries, {snapshot['memory_capacity_pct']}% capacity")
    else:
        print(format_snapshot_for_context(snapshot))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
