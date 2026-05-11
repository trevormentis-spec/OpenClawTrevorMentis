# Memory Freeze Pattern

Adopted from Hermes Agent: memory is loaded once at session start and never modified
mid-session. Changes are persisted to disk immediately but only appear in the next
session's snapshot. This preserves the prefix cache and prevents context thrashing.

## Implementation

At session start (before any tool calls), run:
```
python3 brain/scripts/brain.py snapshot
```

This produces `brain/snapshot.json` with:
- Current date/time
- Top 3 memory entries from semantic store
- Today's daily log summary (if exists)
- Memory usage percentage

## The snapshot is injected at the top of every conversation as:

═══ MEMORY SNAPSHOT ═══
[Loaded: 2026-05-11T22:00:00Z] [72% capacity]
- Key fact about user/project
- Durable decision from MEMORY.md
- Today's context

## File Format
```json
{
  "snapshot_time": "2026-05-11T22:00:00Z",
  "memory_capacity_pct": 72,
  "entries": [
    {"source": "semantic", "content": "...", "key": "..."},
    {"source": "daily_log", "content": "...", "date": "2026-05-11"}
  ]
}
```
