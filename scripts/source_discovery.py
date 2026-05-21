#!/usr/bin/env python3
"""
Weekly Source Discovery — find new high-quality sources across all regions.

Uses web search to discover new OSINT sources, newsletters, think tank reports,
and independent analysts for each coverage region. Adds promising finds to the
source registry and produces a report.

Usage:
    python3 scripts/source_discovery.py --week 2026-W21

Output:
    - Updates analyst/meta/sources.json with new entries
    - Saves discovery report to exports/source-discovery/
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES_FILE = REPO_ROOT / "analyst" / "meta" / "sources.json"
DISCOVERY_DIR = REPO_ROOT / "exports" / "source-discovery"

# Coverage areas to search for new sources
COVERAGE_AREAS = [
    {
        "region": "middle_east",
        "queries": [
            "best Iran conflict OSINT sources 2026",
            "Middle East intelligence analysis newsletter substack",
            "Strait of Hormuz maritime monitoring blog",
            "Israel Iran military analysis independent journalist",
        ],
        "existing": [],
    },
    {
        "region": "ukraine_russia",
        "queries": [
            "Ukraine war OSINT analysis substack 2026",
            "Russia Ukraine frontline tracking blog",
            "Russian military analysis independent source",
        ],
        "existing": [],
    },
    {
        "region": "europe",
        "queries": [
            "NATO defense analysis newsletter",
            "European security policy blog substack",
            "EU foreign policy independent analysis",
        ],
        "existing": [],
    },
    {
        "region": "asia_pacific",
        "queries": [
            "China Taiwan military analysis blog",
            "South China Sea maritime monitoring",
            "Asia security intelligence newsletter",
        ],
        "existing": [],
    },
    {
        "region": "mexico_americas",
        "queries": [
            "Mexico cartel analysis independent source",
            "Latin America security intelligence blog",
            "US Mexico border security analysis",
        ],
        "existing": [],
    },
    {
        "region": "energy_markets",
        "queries": [
            "oil market analysis substack independent",
            "energy geopolitics newsletter 2026",
            "shipping maritime intelligence blog",
        ],
        "existing": [],
    },
    {
        "region": "general_intel",
        "queries": [
            "open source intelligence newsletter best 2026",
            "geopolitical risk analysis independent",
            "intelligence community analysis public source",
        ],
        "existing": [],
    },
]


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[discovery {ts}] {msg}", file=sys.stderr, flush=True)


def load_sources() -> dict:
    """Load the existing source registry."""
    if SOURCES_FILE.exists():
        return json.loads(SOURCES_FILE.read_text())
    return {"durable_sources": [], "moltbook_sources": [], "local_language_sources": []}


def save_sources(sources: dict) -> None:
    """Save the updated source registry."""
    SOURCES_FILE.write_text(json.dumps(sources, indent=2))
    log(f"Source registry updated: {SOURCES_FILE}")


def web_search(query: str, count: int = 5) -> list[dict]:
    """Search the web for sources using Brave Search API."""
    api_key = os.environ.get("BRAVE_API_KEY", "")
    if not api_key:
        log("WARNING: BRAVE_API_KEY not set — skipping web search")
        return []

    encoded = urllib.parse.quote(query)
    url = f"https://api.search.brave.com/res/v1/web/search?q={encoded}&count={count}"

    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            results = []
            for r in data.get("web", {}).get("results", []):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "description": r.get("description", ""),
                    "source_type": _infer_type(r.get("url", "")),
                })
            return results
    except Exception as e:
        log(f"Search failed for '{query[:50]}': {e}")
        return []


def _infer_type(url: str) -> str:
    """Infer source type from URL."""
    if "substack.com" in url:
        return "Substack"
    if "medium.com" in url:
        return "Medium/Blog"
    if "youtube.com" in url or "youtu.be" in url:
        return "YouTube"
    if any(t in url for t in ["twitter.com", "x.com"]):
        return "X/Twitter"
    if "telegram" in url:
        return "Telegram"
    if any(t in url for t in ["org", ".edu"]) and "/blog" in url:
        return "Blog/Think Tank"
    return "Blog/Website"


def _is_duplicate(url: str, existing: list[dict]) -> bool:
    """Check if a URL already exists in the source registry."""
    url_lower = url.lower().rstrip("/")
    for src in existing:
        existing_url = ""
        if isinstance(src, dict):
            existing_url = src.get("url", "").lower().rstrip("/")
        elif isinstance(src, str):
            existing_url = src.lower().rstrip("/")
        if existing_url and url_lower in existing_url:
            return True
        if existing_url and existing_url in url_lower:
            return True
    return False


def quality_score(result: dict) -> int:
    """Score a discovered source for potential quality."""
    score = 2  # baseline
    url = result.get("url", "")
    title = result.get("title", "")
    desc = result.get("description", "")

    # Prefer longer titles/descriptions (more likely substantive)
    if len(desc) > 150:
        score += 1
    if len(title) > 30:
        score += 1

    # Prefer known high-quality domains
    if "substack.com" in url:
        score += 1  # High chance of sustained content
    if any(t in url for t in ["understandingwar", "csis", "cfr", "acled", "eia.gov"]):
        score += 1  # Already known good types

    # Penalize likely low-quality
    if any(t in url for t in ["medium.com", "wordpress.com"]):
        score -= 1  # Could be good, but high variance

    return max(0, min(10, score))


def run_discovery() -> list[dict]:
    """Run the full discovery sweep across all coverage areas."""
    sources = load_sources()
    existing_sources = sources.get("durable_sources", [])
    all_discovered: list[dict] = []

    for area in COVERAGE_AREAS:
        region = area["region"]
        log(f"Searching: {region}")

        for query in area["queries"]:
            results = web_search(query)
            for result in results:
                url = result.get("url", "")
                if not url:
                    continue
                if _is_duplicate(url, existing_sources):
                    continue
                if _is_duplicate(url, all_discovered):
                    continue

                result["region"] = region
                result["score"] = quality_score(result)
                all_discovered.append(result)

    # Deduplicate and sort by quality score
    seen_urls = set()
    unique: list[dict] = []
    for r in sorted(all_discovered, key=lambda x: x.get("score", 0), reverse=True):
        if r["url"] not in seen_urls:
            seen_urls.add(r["url"])
            unique.append(r)

    log(f"Total unique new discoveries: {len(unique)}")
    return unique


def add_to_registry(discoveries: list[dict], max_add: int = 10) -> list[dict]:
    """Add top discoveries to the source registry."""
    sources = load_sources()
    durable = sources.get("durable_sources", [])
    added: list[dict] = []

    for d in discoveries[:max_add]:
        if d.get("score", 0) < 3:
            continue  # Skip low-quality

        entry = {
            "name": d.get("title", "Unknown Source"),
            "type": d.get("source_type", "Blog/Website"),
            "focus": d.get("description", "")[:150],
            "url": d.get("url", ""),
            "discovered": dt.date.today().isoformat(),
            "signal_level": "Medium",
            "region": d.get("region", "general"),
        }
        durable.append(entry)
        added.append(entry)
        log(f"Added: {d.get('title', '?')[:60]} ({d.get('region', '?')})")

    sources["durable_sources"] = durable
    save_sources(sources)
    return added


def save_report(discoveries: list[dict], added: list[dict], week_str: str) -> None:
    """Save a discovery report."""
    DISCOVERY_DIR.mkdir(parents=True, exist_ok=True)
    path = DISCOVERY_DIR / f"discovery-{week_str}.md"

    lines = [
        f"# Source Discovery Report — {week_str}",
        f"Generated: {dt.datetime.now(dt.timezone.utc).isoformat()}",
        "",
        f"**New sources found:** {len(discoveries)}",
        f"**Added to registry:** {len(added)}",
        "",
        "---",
        "## Discovered Sources (by quality score)",
        "",
    ]

    for d in discoveries:
        lines.append(f"### [{d.get('title', '?')}]({d.get('url', '#')})")
        lines.append(f"- **Region:** {d.get('region', '?')}")
        lines.append(f"- **Type:** {d.get('source_type', '?')}")
        lines.append(f"- **Quality Score:** {d.get('score', 0)}/10")
        lines.append(f"- **Description:** {d.get('description', '')[:200]}")
        added_mark = "✅ ADDED" if d in added else "⏭️  Skipped (low quality or duplicate)"
        lines.append(f"- **Status:** {added_mark}")
        lines.append("")

    path.write_text("\n".join(lines))
    log(f"Report saved: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Weekly source discovery")
    parser.add_argument("--week", help="Week string (auto-detected if omitted)")
    args = parser.parse_args()

    week_str = args.week or f"{dt.date.today().year}-W{dt.date.today().isocalendar()[1]:02d}"

    log(f"Starting source discovery for {week_str}")

    discoveries = run_discovery()
    if not discoveries:
        log("No new sources discovered (Brave API may be unavailable)")
        print("No new sources discovered this week.")
        return

    added = add_to_registry(discoveries)
    save_report(discoveries, added, week_str)

    print(f"Discovery complete: {len(discoveries)} found, {len(added)} added to registry")


if __name__ == "__main__":
    main()
