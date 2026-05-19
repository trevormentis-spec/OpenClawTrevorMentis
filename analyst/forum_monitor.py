#!/usr/bin/env python3
"""Forum Monitor — Autonomous forum learning (read-only).

Monitors: r/openclaw, r/myclaw, OpenClaw Discord, Moltbook AI agent posts,
HN posts tagged ai-agents.

Extracts technique improvements, skill recommendations, security warnings,
configuration patterns. Filters via Opus 4.7 weekly synthesis.

Rate limit: maximum 1 forum synthesis per week.
Safety: read-only — no autonomous posting, no DM responses.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


WORKSPACE = Path(__file__).resolve().parent.parent
FORUM_LOG = WORKSPACE / "memory" / "forum-monitoring.jsonl"
SYNTHESIS_LOG = WORKSPACE / "memory" / "forum-synthesis.jsonl"
WEEKLY_SYNTHESIS_LIMIT = 1


@dataclass
class ForumEntry:
    """A monitored forum post or comment."""
    timestamp: str
    source: str  # "reddit_openclaw", "reddit_myclaw", "discord_openclaw", "moltbook", "hn"
    title: str
    url: str
    content_summary: str
    relevance: str  # "high", "medium", "low"
    category: str  # "technique", "skill_recommendation", "security_warning", "config_pattern"


@dataclass
class ForumSynthesis:
    """Weekly synthesis of forum monitoring."""
    timestamp: str
    period_start: str
    period_end: str
    entries_reviewed: int
    actionable_findings: list[dict]
    skill_recommendations: list[str]
    security_warnings: list[str]
    technique_improvements: list[str]


MONITOR_TARGETS = [
    {
        "source": "reddit_openclaw",
        "url": "https://www.reddit.com/r/openclaw/",
        "description": "OpenClaw community discussions",
        "check_frequency": "daily",
    },
    {
        "source": "reddit_myclaw",
        "url": "https://www.reddit.com/r/myclaw/",
        "description": "MyClaw user discussions",
        "check_frequency": "daily",
    },
    {
        "source": "hn_ai_agents",
        "url": "https://news.ycombinator.com/",
        "search_terms": ["ai agent", "autonomous agent", "llm agent"],
        "description": "HN posts about AI agents",
        "check_frequency": "daily",
    },
    {
        "source": "moltbook",
        "url": "https://www.moltbook.com/",
        "search_terms": ["agent", "technique", "intelligence"],
        "description": "Moltbook AI agent discussions",
        "check_frequency": "weekly",
    },
]


def log_entry(entry: ForumEntry) -> None:
    """Log a forum entry to monitoring log."""
    FORUM_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(FORUM_LOG, "a") as f:
        f.write(json.dumps(asdict(entry)) + "\n")


def _count_syntheses_this_week() -> int:
    """Count syntheses in current ISO week."""
    if not SYNTHESIS_LOG.exists():
        return 0
    current_week = time.strftime("%Y-W%W", time.gmtime())
    count = 0
    with open(SYNTHESIS_LOG) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                ts = entry.get("timestamp", "")
                if ts[:10]:
                    t = time.strptime(ts[:10], "%Y-%m-%d")
                    week = time.strftime("%Y-W%W", t)
                    if week == current_week:
                        count += 1
            except (json.JSONDecodeError, ValueError):
                continue
    return count


def record_synthesis(synthesis: ForumSynthesis) -> bool:
    """Record a forum synthesis. Returns False if rate-limited."""
    if _count_syntheses_this_week() >= WEEKLY_SYNTHESIS_LIMIT:
        return False

    SYNTHESIS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(SYNTHESIS_LOG, "a") as f:
        f.write(json.dumps(asdict(synthesis)) + "\n")
    return True


def get_recent_entries(days: int = 7) -> list[dict]:
    """Get forum entries from the last N days."""
    if not FORUM_LOG.exists():
        return []
    cutoff = time.strftime(
        "%Y-%m-%dT00:00:00Z",
        time.gmtime(time.time() - days * 86400)
    )
    entries = []
    with open(FORUM_LOG) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("timestamp", "") >= cutoff:
                    entries.append(entry)
            except json.JSONDecodeError:
                continue
    return entries


def get_monitor_targets() -> list[dict]:
    """Return configured monitoring targets."""
    return list(MONITOR_TARGETS)
