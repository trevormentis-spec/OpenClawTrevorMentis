#!/usr/bin/env python3
"""Source Scoring System — score every feed in sources_tested.json (1-10 scale).

Scoring dimensions:
  - Reliability (0-3): HTTP status history (working=3, intermittent=1-2, dead=0)
  - Freshness   (0-3): How recent the content appeared (daily=3, weekly=2, monthly=1, stale=0)
  - Relevance   (0-2): Keyword match for intelligence-adjacent language (defense, security, intel, geo-politics, etc.)
  - Diversity   (0-2): Specialist sources get 2, major wires get 1 (too much echo), commercial/ecommerce get 0

Output:
  - Updates analyst/meta/sources_tested.json with a "score" field per entry
  - Writes analyst/meta/source-scores.csv for external analysis
  - Auto-demotion flag: entries scoring <3 get "demoted": true added

Environment: No special vars required (reads from filesystem only).
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = REPO_ROOT / "analyst" / "meta" / "sources_tested.json"
SCORES_CSV = REPO_ROOT / "analyst" / "meta" / "source-scores.csv"
DEMOTION_THRESHOLD = 3  # Feeds scoring below this get flagged
STALE_DAYS = 30  # Days of low score before marking for demotion

# Keywords that signal intelligence relevance (built from domain vocabulary)
INTEL_RELEVANT = re.compile(
    r"\b(?:defen[cs]e|securit|intelligence|geopolit|military|conflict|"
    r"sanctions|terroris|cyber|hack|breach|espionage|trade\s*war|"
    r"nuclear|missile|navy|army|fleet|border|insurgent|rebel|"
    r"diplomac|foreign\s*affair|strategic|weapon|arms|warfare|"
    r"disinfo|misinfo|propaganda|influence|election\s*security|"
    r"supply\s*chain|crisis|escalat|de-escalat|treaty|alliance)\b",
    re.IGNORECASE,
)

# Keywords that signal general news (lower relevance)
GENERAL_NEWS = re.compile(
    r"\b(?:sport|entertain|fashion|lifestyle|cooking|recipe|"
    r"travel|tourism|movie|music|celebrity|gaming)\b",
    re.IGNORECASE,
)

# Domains/names considered major wires (high echo, lower diversity score)
MAJOR_WIRES = [
    "reuters", "ap.org", "apnews", "bbc", "bloomberg", "cnn", "npr",
    "associated press", "france24", "dw.com", "al jazeera",
]


def _score_reliability(entry: dict) -> int:
    """Score 0-3 based on HTTP status history."""
    status = entry.get("status", "")
    code = entry.get("code")
    # Handle None code (field not present in some entries)
    if code is None:
        code = 0

    if status == "ok" and code in (200, 0):
        return 3
    if status in ("ok", "redirect") or (200 <= code < 400):
        return 2
    if status in ("forbidden", "http_401", "http_403", "timeout", "error"):
        return 1 if code and code < 500 else 0
    return 1  # Unknown status — give benefit of doubt once


def _score_freshness(entry: dict) -> int:
    """Score 0-3 based on content recency.

    Uses 'tested_at' timestamp as a proxy for when we last checked.
    For a more precise freshness, we'd need to parse RSS feed dates,
    but this is a reasonable proxy.
    """
    tested_raw = entry.get("tested_at", "")
    if not tested_raw:
        return 1  # No timestamp — assume moderately stale

    try:
        tested = datetime.fromisoformat(tested_raw.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return 1

    days_since = (datetime.now(timezone.utc) - tested).days
    if days_since <= 1:
        return 3
    if days_since <= 7:
        return 2
    if days_since <= 30:
        return 1
    return 0  # >30 days since test


def _score_relevance(name: str, url: str) -> int:
    """Score 0-2: intelligence-relevant keywords in title/URL."""
    text = f"{name} {url}".lower()

    if INTEL_RELEVANT.search(text):
        return 2
    if GENERAL_NEWS.search(text):
        return 1
    # Catch-all: feed aggregators and generic sources get 1
    if any(w in text for w in ("news", "world", "global", "rss")):
        return 1
    return 0


def _score_diversity(name: str, url: str) -> int:
    """Score 0-2: specialist sources get 2, major wires get 1, others get 1 by default."""
    text = f"{name} {url}".lower()

    # Major wire detection
    for wire in MAJOR_WIRES:
        if wire.lower() in text:
            return 1  # Too much echo — don't over-weight

    # Specialist indicators — higher value for targeted collection
    specialist_indicators = [
        "institute", "center for", "foundation", "think tank",
        "analysis", "research", "intel", "defense", "security",
        "acled", "csis", "crisis group", "janes", "iiss", "rusi",
        "carnegie", "chatham", "brookings", "rand", "sipri",
    ]
    for indicator in specialist_indicators:
        if indicator in text:
            return 2

    return 1  # Default — reasonable source


def score_entry(entry: dict) -> dict:
    """Score a single source entry and return it with score fields added."""
    name = entry.get("name", "")
    url = entry.get("url", "")

    reliability = _score_reliability(entry)
    freshness = _score_freshness(entry)
    relevance = _score_relevance(name, url)
    diversity = _score_diversity(name, url)
    total = reliability + freshness + relevance + diversity

    entry["score"] = total
    entry["score_reliability"] = reliability
    entry["score_freshness"] = freshness
    entry["score_relevance"] = relevance
    entry["score_diversity"] = diversity

    if total < DEMOTION_THRESHOLD:
        entry["demoted"] = True
        entry.get("__demotion_risk", None)
    elif "demoted" in entry:
        # Clear previous demotion flag if score has improved
        del entry["demoted"]

    return entry


def load_sources() -> list[dict]:
    """Load sources_tested.json. Returns empty list if file missing."""
    if not SOURCES_PATH.exists():
        print(f"ERROR: sources file not found: {SOURCES_PATH}", file=sys.stderr)
        return []
    with open(SOURCES_PATH, "r") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print(f"ERROR: expected JSON array, got {type(data).__name__}", file=sys.stderr)
        return []
    return data


def write_sources(sources: list[dict]) -> None:
    """Write updated sources back to sources_tested.json."""
    with open(SOURCES_PATH, "w") as f:
        json.dump(sources, f, indent=2, ensure_ascii=False)
    print(f"Updated {SOURCES_PATH} with scores ({len(sources)} entries)")


def write_csv(sources: list[dict]) -> None:
    """Write source-scores.csv for external analysis."""
    fieldnames = [
        "name", "url", "region", "status", "code",
        "score", "score_reliability", "score_freshness",
        "score_relevance", "score_diversity", "demoted",
    ]
    with open(SCORES_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for entry in sources:
            row = {k: entry.get(k, "") for k in fieldnames}
            row["demoted"] = "yes" if entry.get("demoted") else ""
            writer.writerow(row)
    print(f"Wrote {SCORES_CSV} ({len(sources)} rows)")


def report_summary(sources: list[dict]) -> dict:
    """Generate a summary report of scoring results."""
    total = len(sources)
    scored = [s for s in sources if "score" in s]
    demoted = [s for s in sources if s.get("demoted")]
    by_health = {"ok": 0, "degraded": 0, "dead": 0}
    for s in sources:
        status = s.get("status", "")
        if status == "ok":
            by_health["ok"] += 1
        elif status in ("forbidden", "http_401", "http_403", "timeout", "error"):
            by_health["dead"] += 1
        else:
            by_health["degraded"] += 1

    avg_score = sum(s.get("score", 0) for s in scored) / max(len(scored), 1)

    print(f"\n{'='*50}")
    print(f"SOURCE SCORING SUMMARY")
    print(f"{'='*50}")
    print(f"Total sources:      {total}")
    print(f"Average score:      {avg_score:.2f}/10")
    print(f"Demoted (<3):       {len(demoted)}")
    print(f"  Working (ok):     {by_health['ok']}")
    print(f"  Degraded:         {by_health['degraded']}")
    print(f"  Dead (403/error): {by_health['dead']}")

    # Top 10 by score
    top = sorted(scored, key=lambda s: s.get("score", 0), reverse=True)[:10]
    print(f"\nTop 10 sources by score:")
    for s in top:
        print(f"  {s.get('score',0):2d} {s.get('name','?'):50s} [{s.get('status','?')}]")

    # Demoted list
    if demoted:
        print(f"\nDemoted sources (score < {DEMOTION_THRESHOLD}):")
        for s in sorted(demoted, key=lambda x: x.get("score", 0)):
            print(f"  {s.get('score',0)} {s.get('name','?'):50s} [{s.get('status','?')}]")

    return {
        "total": total,
        "avg_score": round(avg_score, 2),
        "demoted": len(demoted),
        "healthy": by_health["ok"],
        "degraded": by_health["degraded"],
        "dead": by_health["dead"],
    }


def main() -> int:
    sources = load_sources()
    if not sources:
        return 1

    for i, entry in enumerate(sources):
        sources[i] = score_entry(entry)

    write_sources(sources)
    write_csv(sources)
    report_summary(sources)
    return 0


if __name__ == "__main__":
    sys.exit(main())
