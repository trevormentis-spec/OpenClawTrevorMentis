#!/usr/bin/env python3
"""
trevor_freeze.py — Memory freeze pattern for Trevor.

Snapshots memory at pipeline start into a frozen block.
Writes during the run go to disk but don't modify the snapshot
until the next run. Preserves context stability.

Usage:
    from trevor_freeze import MemoryFreeze
    freeze = MemoryFreeze()
    freeze.snapshot()
    freeze.status()
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent
FREEZE_FILE = SKILL_ROOT / "memory" / "memory_freeze.json"


class MemoryFreeze:
    """Frozen memory snapshot — captured once at pipeline start."""

    def __init__(self):
        self.path = FREEZE_FILE
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def snapshot(self, entries: list[dict] | None = None) -> dict:
        """Create a frozen memory snapshot."""
        if entries is None:
            # Default: read from trevor_memory if available
            try:
                from trevor_memory import MemoryStore
                mem = MemoryStore()
                narrative_count = mem.count("narrative")
                recent = mem.get_recent("narrative", 5)
                entries = [{"key": r.get("key", ""), "region": r.get("region", ""),
                           "content": r.get("content", "")[:200],
                           "created_at": r.get("created_at", "")}
                          for r in recent]
                mem.close()
            except Exception:
                entries = []

        snapshot = {
            "snapshot_time": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "pipeline_date": datetime.date.today().isoformat(),
            "entry_count": len(entries),
            "entries": entries,
        }

        self.path.write_text(json.dumps(snapshot, indent=2))
        return snapshot

    def status(self) -> dict:
        """Return current freeze status."""
        if not self.path.exists():
            return {"frozen": False, "entries": 0, "age_seconds": 0}
        data = json.loads(self.path.read_text())
        age = (datetime.datetime.utcnow() - datetime.datetime.strptime(
            data["snapshot_time"], "%Y-%m-%dT%H:%M:%SZ")).total_seconds()
        return {
            "frozen": True,
            "entries": data.get("entry_count", 0),
            "age_seconds": int(age),
            "pipeline_date": data.get("pipeline_date", ""),
        }
