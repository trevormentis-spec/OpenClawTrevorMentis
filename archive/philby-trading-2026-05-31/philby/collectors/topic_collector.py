#!/usr/bin/env python3
"""
Topic Collector — fetches content from topic source YAML files for downstream analysis.

Reads topic source inventories from config/topics/<topic>/sources.yaml and:
  - Parses RSS/Atom feeds
  - Scrapes HTML pages (text extraction, 50KB limit)
  - Detects RSS feeds from HTML link tags
  - Skips corporate/government homepages unless RSS-identified
  - Rate-limits, retries, and tracks errors per source

Output: exports/topic-collections/topic-collection-<topic>-<YYYY-MM-DD>.json

Usage:
    python3 philby/collectors/topic_collector.py --topic leo_ground_stations
    python3 philby/collectors/topic_collector.py --all
    python3 philby/collectors/topic_collector.py --dry-run
    python3 philby/collectors/topic_collector.py --dry-run --all
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
TOPICS_DIR = REPO / "config" / "topics"
EXPORT_DIR = REPO / "exports" / "topic-collections"

# Active topics per task spec
ACTIVE_TOPICS = [
    "leo_ground_stations",
    "rdx_c4_supply",
    "semiconductor-supply-chain",
]

# Source types that should ONLY be fetched if RSS-identified
SKIP_UNLESS_RSS = {"corporate", "government"}

# Types that we attempt to RSS-detect from HTML
RSS_DETECT_TYPES = {
    "trade", "think_tank", "market_research", "industry_body", "academic",
    "conference", "commentary", "defense", "intelligence", "reference",
    "consulting", "financial", "insurance", "regulator", "regulatory",
    "market_intel", "market_report", "trade_data", "news_monitoring",
    "news", "analysis", "osint", "satellite", "equity_research",
}

# RSS URL indicators (used for skip/homepage-likely checks)
RSS_URL_PATTERNS = ("/feed", "/rss", "/xml", "rss.xml", "atom.xml", "feed.xml", "?feed=")

# Update frequencies that suggest content fetching is worthwhile
HIGH_FREQ = {"continuous", "real-time", "daily", "weekly", "every 5 days"}

USER_AGENT = "Mozilla/5.0 (compatible; PhilbyTopicCollector/1.0)"
TIMEOUT = 30  # seconds
DELAY = 1.0   # seconds between requests
RETRY_DELAY = 5  # seconds on 429/503
CONTENT_LIMIT = 50_000  # max chars for HTML extracted text
SUMMARY_LIMIT = 500     # max chars for item summary
CONTENT_CHUNK = 5000    # max chars stored per item's content field


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[topic-collector {ts}] {msg}", file=sys.stderr, flush=True)


# ── YAML loading ───────────────────────────────────────────────────

def load_sources(topic: str) -> list[dict]:
    """Load source list from a topic's sources.yaml. Handles both flat-list
    and sources:-key formats."""
    yaml_path = TOPICS_DIR / topic / "sources.yaml"
    if not yaml_path.exists():
        log(f"  No sources.yaml found for topic '{topic}'")
        return []

    with open(yaml_path) as f:
        raw = yaml.safe_load(f)

    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and "sources" in raw:
        return raw["sources"] or []  # handle None / empty list
    return []


def looks_like_rss_url(url: str) -> bool:
    """Heuristic: does this URL look like an RSS/Atom feed?"""
    if not url:
        return False
    lower = url.lower()
    return any(p in lower for p in RSS_URL_PATTERNS)


# ── Fetcher helpers ─────────────────────────────────────────────────

def _fetch(url: str, timeout: int = TIMEOUT) -> requests.Response | None:
    """Fetch a URL with retry on 429/503."""
    headers = {"User-Agent": USER_AGENT}
    for attempt in range(2):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            if resp.status_code in (429, 503):
                if attempt == 0:
                    log(f"    rate-limited ({resp.status_code}), retrying after {RETRY_DELAY}s…")
                    time.sleep(RETRY_DELAY)
                    continue
                return None
            return resp
        except requests.RequestException as e:
            if attempt == 0:
                time.sleep(RETRY_DELAY)
                continue
            return None
    return None


def _find_rss_in_html(html: str, base_url: str) -> str | None:
    """Find RSS feed URLs from <link> tags in HTML head."""
    soup = BeautifulSoup(html, "html.parser")
    for link in soup.find_all("link"):
        if link.get("type") in ("application/rss+xml", "application/atom+xml"):
            href = link.get("href", "")
            if href:
                return urljoin(base_url, href)
    # Also try common paths
    parsed = urlparse(base_url)
    common = [
        f"{parsed.scheme}://{parsed.netloc}/feed",
        f"{parsed.scheme}://{parsed.netloc}/rss",
        f"{parsed.scheme}://{parsed.netloc}/feed.xml",
        f"{parsed.scheme}://{parsed.netloc}/rss.xml",
        f"{parsed.scheme}://{parsed.netloc}/atom.xml",
    ]
    for candidate in common:
        try:
            r = requests.head(candidate, headers={"User-Agent": USER_AGENT}, timeout=10)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith(("application/rss", "application/atom", "text/xml")):
                return candidate
        except Exception:
            continue
    return None


# ── Content extraction ──────────────────────────────────────────────

def parse_rss(url: str) -> list[dict]:
    """Parse an RSS/Atom feed and return extracted items."""
    resp = _fetch(url)
    if resp is None:
        return []

    feed = feedparser.parse(resp.text)
    if feed.bozo and not feed.entries:
        return []

    items = []
    for entry in feed.entries[:20]:  # max 20 items per feed
        published = ""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = time.strftime("%Y-%m-%d", entry.published_parsed)
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            published = time.strftime("%Y-%m-%d", entry.updated_parsed)

        # Get summary text
        summary = entry.get("summary", "") or entry.get("description", "") or ""
        summary = _strip_html(summary)[:SUMMARY_LIMIT]

        # Get content text (longer extract)
        content = ""
        if hasattr(entry, "content") and entry.content:
            content = entry.content[0].get("value", "")
        elif hasattr(entry, "summary_detail") and entry.summary_detail.get("value"):
            content = entry.summary_detail.get("value", "")
        content = _strip_html(content)[:CONTENT_CHUNK]

        items.append({
            "title": entry.get("title", "Untitled"),
            "url": entry.get("link", ""),
            "published": published,
            "summary": summary,
            "content": content,
        })
    return items


def scrape_html(url: str) -> list[dict]:
    """Scrape a web page, extract text content, return as a single-item list."""
    resp = _fetch(url)
    if resp is None:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Strip scripts, styles, navigation
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    # Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text[:CONTENT_LIMIT]

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    return [{
        "title": title or urlparse(url).netloc,
        "url": url,
        "published": "",
        "summary": text[:SUMMARY_LIMIT],
        "content": text[:CONTENT_CHUNK],
    }]


def _strip_html(text: str) -> str:
    """Strip HTML tags and return plain text."""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ", strip=True)


# ── Source classification ──────────────────────────────────────────

def classify_source(source: dict) -> str:
    """Determine how to handle a source: rss, html, skip, or try_rss."""
    src_type = source.get("type", "").lower()
    url = source.get("url", "")
    frequency = source.get("update_frequency", "").lower()

    # RSS-identified URL → always treat as RSS
    if looks_like_rss_url(url):
        return "rss"

    # Corporate and government → skip unless RSS URL (already handled above)
    if src_type in SKIP_UNLESS_RSS:
        return "skip"

    # Explicit html source type → scrape
    if src_type == "html":
        return "html"

    # High-frequency types → try RSS first, fall back to scrape
    if frequency in HIGH_FREQ or src_type in RSS_DETECT_TYPES:
        return "try_rss"

    # Low-frequency, one-shot publications → scrape once
    if frequency in {"monthly", "quarterly", "annual", "one-time publication (mar 2026)"}:
        # For these, do a one-time scrape if the URL is a real page
        return "html"

    # Default: try to detect RSS, otherwise skip (watch item)
    return "watch"


# ── Main collection logic ──────────────────────────────────────────

def collect_topic(topic: str, dry_run: bool = False) -> dict:
    """Collect all source content for a single topic."""
    sources = load_sources(topic)
    result = {
        "topic": topic,
        "collected_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_count": len(sources),
        "sources_fetched": 0,
        "sources_skipped": 0,
        "sources_watch": 0,
        "sources_error": 0,
        "items": [],
        "errors": [],
    }

    if not sources:
        result["errors"].append("no_sources: No sources found for this topic")
        return result

    log(f"  Topic '{topic}': {len(sources)} sources")

    for i, source in enumerate(sources):
        name = source.get("name", f"source-{i}")
        url = source.get("url", "")
        src_type = source.get("type", "").lower()
        classification = classify_source(source)

        if not url:
            result["errors"].append(f"{name}: no URL")
            continue

        if dry_run:
            result["items"].append({
                "title": name,
                "url": url,
                "source_name": name,
                "source_type": src_type,
                "classification": classification,
                "published": "",
                "summary": "",
                "content": "",
                "fetch_status": "dry_run",
            })
            if classification == "skip":
                result["sources_skipped"] += 1
            elif classification == "watch":
                result["sources_watch"] += 1
            else:
                result["sources_fetched"] += 1
            continue

        # ── Actual fetch ──
        fetch_status = "ok"
        items = []

        try:
            if classification == "skip":
                fetch_status = "skipped"
                result["sources_skipped"] += 1
            elif classification == "watch":
                fetch_status = "watch"
                result["sources_watch"] += 1
                # Still record as a watch item
                items = [{
                    "title": name,
                    "url": url,
                    "published": "",
                    "summary": f"Watch item: {src_type} source with update_frequency={source.get('update_frequency', '')}",
                    "content": url,
                }]
            elif classification == "rss":
                items = parse_rss(url)
                result["sources_fetched"] += 1
                if not items:
                    fetch_status = "error"
                    result["errors"].append(f"{name}: RSS feed returned no entries")
            elif classification == "try_rss":
                # Try RSS first, fall back to HTML scrape
                resp = _fetch(url)
                if resp is None:
                    fetch_status = "error"
                    result["errors"].append(f"{name}: HTTP fetch failed")
                else:
                    # First, try parsing the response as RSS directly
                    feed = feedparser.parse(resp.text)
                    if feed.entries and not feed.bozo:
                        items = parse_rss(url)
                        result["sources_fetched"] += 1
                    else:
                        # Look for RSS link in HTML
                        rss_url = _find_rss_in_html(resp.text, url)
                        if rss_url:
                            log(f"    found RSS: {rss_url}")
                            items = parse_rss(rss_url)
                            result["sources_fetched"] += 1
                        else:
                            # No RSS found — scrape HTML
                            items = scrape_html(url)
                            result["sources_fetched"] += 1
                    if not items:
                        fetch_status = "error"
                        result["errors"].append(f"{name}: no content extracted")
            elif classification == "html":
                items = scrape_html(url)
                result["sources_fetched"] += 1
                if not items:
                    fetch_status = "error"
                    result["errors"].append(f"{name}: HTML scrape returned no content")
        except Exception as e:
            fetch_status = "error"
            result["errors"].append(f"{name}: {e}")
            result["sources_error"] += 1

        # Tag items with source metadata
        for item in items:
            item["source_name"] = name
            item["source_type"] = src_type
            item["fetch_status"] = fetch_status
        result["items"].extend(items)

        # Rate limit
        if not dry_run and classification not in ("skip", "watch"):
            time.sleep(DELAY)

        if (i + 1) % 20 == 0:
            log(f"    {i+1}/{len(sources)} processed ({result['sources_fetched']} fetched)")

    log(f"  Topic '{topic}': {result['sources_fetched']} fetched, "
        f"{result['sources_skipped']} skipped, {len(result['items'])} items, "
        f"{len(result['errors'])} errors")

    return result


def save_results(topic: str, result: dict) -> str:
    """Save collection results to JSON file."""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = EXPORT_DIR / f"topic-collection-{topic}-{today}.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    log(f"  Saved: {out_path}")
    return str(out_path)


# ── Active topics discovery ─────────────────────────────────────────

def get_active_topics() -> list[str]:
    """Return the list of active topics that have sources.yaml files."""
    if not TOPICS_DIR.exists():
        return []
    topics = []
    for d in sorted(TOPICS_DIR.iterdir()):
        if d.is_dir() and (d / "sources.yaml").exists():
            topics.append(d.name)
    return topics


# ── CLI ─────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Topic Collector — fetch content from topic source inventories"
    )
    parser.add_argument(
        "--topic", type=str, default=None,
        help="Topic name to collect (e.g. leo_ground_stations)"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Collect all topics with sources.yaml files"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be fetched without making HTTP requests"
    )
    parser.add_argument(
        "--save", action="store_true", default=True,
        help="Save results to JSON (default: yes)"
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="Don't save results — print JSON to stdout instead"
    )
    args = parser.parse_args()

    # Determine topics
    if args.all:
        topics = get_active_topics()
        if not topics:
            log("No topics found with sources.yaml")
            return 1
    elif args.topic:
        topics = [args.topic]
    else:
        log("Error: specify --topic <name> or --all")
        parser.print_usage()
        return 1

    log(f"{'DRY RUN' if args.dry_run else 'Collecting'} for {len(topics)} topic(s): {', '.join(topics)}")
    log("")

    exit_code = 0
    for topic in topics:
        result = collect_topic(topic, dry_run=args.dry_run)

        if args.no_save:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.save:
            save_path = save_results(topic, result)
            # Summary line
            if args.dry_run:
                print(f"  {topic}: {result['sources_fetched']} would fetch "
                      f"(of {result['source_count']} sources)")
            else:
                print(f"  {topic}: {result['sources_fetched']} fetched, "
                      f"{len(result['items'])} items → {save_path}")

        if result.get("errors") and not args.dry_run:
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
