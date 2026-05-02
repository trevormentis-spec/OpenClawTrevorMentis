#!/usr/bin/env python3
"""Global news gatherer for Trevor's Daily Intelligence Briefing.

Fetches from high-signal RSS/Atom feeds and writes structured raw data
to tasks/news_raw.md for ingestion by the 5AM PT briefing pipeline.

Usage:
    python3 tasks/global_news_gather.py
    python3 tasks/global_news_gather.py --out tasks/news_raw.md

Output format: Markdown with ## section headers per source category.
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

# ── Sources (auto-generated from analyst/meta/sources.json + core feeds) ──

SOURCES_JSON = Path(__file__).resolve().parent.parent / "analyst" / "meta" / "sources.json"

# Always-included feeds that work reliably (even if not in sources.json)
CORE_FEEDS: list[dict[str, str]] = [
    # Global News
    {"name": "BBC World", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "category": "Global News"},
    {"name": "BBC Middle East", "url": "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml", "category": "Middle East"},
    {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml", "category": "Global News"},
    {"name": "Guardian International", "url": "https://www.theguardian.com/world/rss", "category": "Global News"},
    {"name": "Guardian Middle East", "url": "https://www.theguardian.com/world/middle-east/rss", "category": "Middle East"},
    # Think Tanks & Intel
    {"name": "Stimson Center", "url": "https://www.stimson.org/feed/", "category": "Think Tank"},
    {"name": "SpecialEurasia", "url": "https://www.specialeurasia.com/feed/", "category": "Intel Analysis"},
    # Defense
    {"name": "Breaking Defense", "url": "https://breakingdefense.com/feed/", "category": "Defense"},
    # Energy
    {"name": "OilPrice.com", "url": "https://oilprice.com/rss/main", "category": "Energy Markets"},
]


def _guess_substack_feed(url: str) -> str | None:
    """If a URL is a Substack publication, return its /feed path."""
    if "substack.com" in url:
        base = url.rstrip("/")
        return f"{base}/feed"
    return None


def _guess_rss_feed(url: str) -> str | None:
    """Guess RSS feed URL from a source's homepage."""
    # Common RSS paths to try
    candidates = [
        url.rstrip("/") + "/feed",
        url.rstrip("/") + "/feed/",
        url.rstrip("/") + "/rss",
        url.rstrip("/") + "/rss/",
        url.rstrip("/") + "/rss.xml",
        url.rstrip("/") + "/index.xml",
        url.rstrip("/") + "/atom.xml",
        url.rstrip("/") + "/news/rss.xml",
    ]
    substack = _guess_substack_feed(url)
    if substack:
        candidates.insert(0, substack)
    return candidates[0]


def get_dynamic_feeds() -> list[dict[str, str]]:
    """Read sources.json and derive feeds from durable sources.
    
    This is the auto-update mechanism: when the OSINT Deep Search cron
    discovers new sources and writes them to analyst/meta/sources.json,
    this function picks them up automatically on the next gather run.
    """
    feeds: list[dict[str, str]] = []
    seen_names: set[str] = {f["name"] for f in CORE_FEEDS}

    if not SOURCES_JSON.exists():
        print("  ℹ️  sources.json not found — using core feeds only", file=sys.stderr)
        return feeds

    try:
        with open(SOURCES_JSON) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"  ⚠️  Failed to read sources.json: {e}", file=sys.stderr)
        return feeds

    # Collect from all source categories in sources.json
    source_lists: list[list[dict]] = []
    for key in data:
        val = data[key]
        if isinstance(val, list):
            source_lists.append(val)
        elif isinstance(val, dict):
            for sub in val.values():
                if isinstance(sub, list):
                    source_lists.append(sub)

    for entry in source_lists:
        for s in entry:
            if not isinstance(s, dict):
                continue
            name = s.get("name") or s.get("agent") or ""
            url = s.get("url") or ""
            category = s.get("type") or s.get("focus") or s.get("category", "OSINT") or "Uncategorized"

            if not name or not url:
                continue
            if name in seen_names:
                continue

            seen_names.add(name)
            feed_url = _guess_substack_feed(url)
            if not feed_url:
                feed_url = url  # Use raw URL; feed lookup will fail gracefully

            feeds.append({
                "name": name,
                "url": feed_url,
                "category": category[:40],
            })

    return feeds


def build_feeds() -> list[dict[str, str]]:
    """Merge core feeds with dynamically discovered feeds from sources.json."""
    all_feeds = list(CORE_FEEDS)
    dynamic = get_dynamic_feeds()
    all_feeds.extend(dynamic)
    return all_feeds

USER_AGENT = "Trevor-Intel-Gatherer/1.0 (intelligence briefing pipeline)"


def fetch_feed(url: str, timeout: int = 20) -> str | None:
    """Fetch an RSS/Atom feed and return the raw XML text."""
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
        return None


def parse_entries(xml_text: str, max_per_feed: int = 10) -> list[dict[str, str]]:
    """Parse RSS 2.0 or Atom entries from XML text."""
    entries: list[dict[str, str]] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return entries

    # RSS 2.0: <rss><channel><item>...</item></channel></rss>
    for item in root.iter("item"):
        entry = {}
        for child in item:
            tag = child.tag.lower()
            text = "".join(child.itertext()).strip()
            if tag in ("title", "link", "description", "pubdate", "category", "guid"):
                entry[tag] = html.unescape(text) if text else ""
        if entry.get("title"):
            entries.append(entry)
        if len(entries) >= max_per_feed:
            break

    # If RSS didn't match, try Atom: <feed><entry>...</entry></feed>
    if not entries:
        for entry_elem in root.iter("{http://www.w3.org/2005/Atom}entry"):
            entry = {}
            for child in entry_elem:
                tag = child.tag.split("}")[-1].lower()
                text = "".join(child.itertext()).strip()
                if tag in ("title", "link", "published", "updated", "summary", "category"):
                    if tag == "link":
                        href = child.attrib.get("href", "")
                        if href:
                            entry["link"] = href
                    else:
                        entry[tag] = html.unescape(text) if text else ""
            if entry.get("title"):
                # Map Atom fields to RSS-like keys
                entry.setdefault("link", "")
                entry.setdefault("pubdate", entry.get("published", ""))
                entry.setdefault("description", entry.get("summary", ""))
                entries.append(entry)
            if len(entries) >= max_per_feed:
                break

    return entries


def clean_text(text: str, max_len: int = 300) -> str:
    """Strip HTML tags and truncate."""
    cleaned = re.sub(r"<[^>]+>", "", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rsplit(" ", 1)[0] + "..."
    return cleaned


def gather_news(max_per_feed: int = 8) -> dict[str, list]:
    """Gather news from all feeds and return structured results.
    
    Feeds are auto-built from CORE_FEEDS + analyst/meta/sources.json,
    so new sources discovered by the OSINT Deep Search cron are
    automatically included on the next run.
    """
    feeds = build_feeds()
    n_core = len(CORE_FEEDS)
    n_dynamic = max(0, len(feeds) - n_core)
    print(f"📡 Fetching {len(feeds)} sources ({n_core} core + {n_dynamic} dynamic)...", file=sys.stderr)
    results: dict[str, list] = {}
    total_items = 0
    errors = []

    for feed_conf in feeds:
        name = feed_conf["name"]
        category = feed_conf.get("category", "Uncategorized")
        xml_text = fetch_feed(feed_conf["url"])
        if xml_text is None:
            errors.append(f"  ⚠️  {name} — Failed to fetch")
            continue

        entries = parse_entries(xml_text, max_per_feed)
        if not entries:
            errors.append(f"  ⚠️  {name} — No entries parsed")
            continue

        category_key = category
        if category_key not in results:
            results[category_key] = []
        for e in entries:
            results[category_key].append({
                "source": name,
                "title": e.get("title", "(no title)"),
                "link": e.get("link", ""),
                "description": clean_text(e.get("description", "")),
                "pubdate": e.get("pubdate", "")[:25],
            })
        total_items += len(entries)

    return {
        "results": results,
        "total_items": total_items,
        "errors": errors,
        "sources_fetched": len(feeds) - len(errors),
        "sources_total": len(feeds),
    }


def format_markdown(result: dict) -> str:
    """Format gathered news into markdown for news_raw.md."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Global News Gather — {now}",
        "",
        f"**Sources:** {result['sources_fetched']}/{result['sources_total']} fetched | "
        f"**Items:** {result['total_items']}",
        "",
    ]

    if result["errors"]:
        lines.append("### Errors")
        lines.extend(result["errors"])
        lines.append("")

    for category, items in result["results"].items():
        lines.append(f"## {category}")
        lines.append("")
        for item in items:
            title = item["title"]
            source = item["source"]
            desc = item["description"]
            link = item["link"]
            pub = item["pubdate"]
            lines.append(f"### {title}")
            lines.append(f"- **Source:** {source} | **Published:** {pub}")
            if desc:
                lines.append(f"- **Summary:** {desc}")
            if link:
                lines.append(f"- **Link:** <{link}>")
            lines.append("")

    # Summary metadata
    lines.append("---")
    lines.append(f"_Gathered at {now} by Trevor Global News Gatherer_")
    lines.append(f"_Feeds: {result['sources_fetched']}/{result['sources_total']} | {result['total_items']} items_")
    lines.append("")

    return "\n".join(lines)


def main(argv: list[str]) -> int:
    out_path = Path("/home/ubuntu/.openclaw/workspace/tasks/news_raw.md")

    # Allow override
    if len(argv) > 1 and "--out" in argv:
        idx = argv.index("--out")
        if idx + 1 < len(argv):
            out_path = Path(argv[idx + 1])

    print(f"🌐 Global News Gatherer — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    pass  # source count printed in gather_news
    print()

    result = gather_news(max_per_feed=8)

    print(f"✅ {result['sources_fetched']}/{result['sources_total']} sources fetched")
    print(f"📰 {result['total_items']} items gathered")
    print()

    if result["errors"]:
        for err in result["errors"][:5]:
            print(err)
        if len(result["errors"]) > 5:
            print(f"  ... and {len(result['errors']) - 5} more errors")

    markdown = format_markdown(result)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    # Print category summary
    print()
    print("📊 Category Breakdown:")
    for cat, items in result["results"].items():
        print(f"  {cat}: {len(items)} items")
    print()
    print(f"💾 Written to {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
