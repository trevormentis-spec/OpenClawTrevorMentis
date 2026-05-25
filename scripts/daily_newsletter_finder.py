#!/usr/bin/env python3
"""
Daily Newsletter Discovery — find new substacks/newsletters to recommend.

Performs lightweight web searches for new intelligence/geopolitics newsletters,
checks against a running log of past recommendations, and outputs the top 2-3
new finds each day.

Usage:
    python3 scripts/daily_newsletter_finder.py

Output:
    - Writes recommended newsletters to stdout (YAML-like format)
    - Saves recommendation log to exports/newsletter-recs/log.json
"""
from __future__ import annotations

import datetime as dt
import gzip
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
REC_LOG_DIR = REPO_ROOT / "exports" / "newsletter-recs"
REC_LOG_FILE = REC_LOG_DIR / "recommendation-log.json"

# Search queries rotated daily — avoids stale results
QUERIES_POOL = [
    # Security & Intel
    "best intelligence analysis newsletter substack 2026",
    "national security daily briefing newsletter",
    "geopolitical risk analysis newsletter independent",
    "open source intelligence newsletter daily",
    "defense and security newsletter substack",
    # Regional
    "Middle East analysis newsletter substack",
    "Iran conflict newsletter daily update",
    "China Taiwan security newsletter substack",
    "Ukraine war analysis newsletter daily",
    "Latin America security newsletter",
    # Energy & Economics
    "oil energy markets newsletter substack",
    "global macro geopolitical newsletter",
    "shipping maritime security newsletter",
    # OSINT & Tradecraft
    "OSINT newsletter daily threat intelligence",
    "intelligence community analysis public newsletter",
]


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[newsletter_finder {ts}] {msg}", file=sys.stderr, flush=True)


def load_rec_log() -> dict:
    """Load the recommendation history log."""
    if REC_LOG_FILE.exists():
        try:
            return json.loads(REC_LOG_FILE.read_text())
        except Exception:
            pass
    return {"recommended_urls": [], "recommendations": []}


def save_rec_log(log_data: dict) -> None:
    """Save the recommendation history log."""
    REC_LOG_DIR.mkdir(parents=True, exist_ok=True)
    REC_LOG_FILE.write_text(json.dumps(log_data, indent=2))


def web_search(query: str, count: int = 5) -> list[dict]:
    """Search the web for newsletters."""
    api_key = os.environ.get("BRAVE_API_KEY", "")
    if not api_key:
        log("WARNING: BRAVE_API_KEY not set")
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
            raw = resp.read()
            if raw[:2] == b'\x1f\x8b':
                raw = gzip.decompress(raw)
            data = json.loads(raw)
            results = []
            for r in data.get("web", {}).get("results", []):
                url_lower = r.get("url", "").lower()
                # Only include newsletters/substacks
                if any(t in url_lower for t in ["substack.com", "buttondown", "newsletter", "mailchi.mp", "beehiiv"]):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "description": r.get("description", ""),
                        "query": query,
                    })
            return results
    except Exception as e:
        log(f"Search failed for '{query[:40]}': {e}")
        return []


def find_newsletters() -> list[dict]:
    """Run daily newsletter discovery."""
    rec_log = load_rec_log()
    previously_recommended = set(rec_log.get("recommended_urls", []))
    all_results: list[dict] = []

    # Rotate queries — pick 3 per day based on date
    day_of_year = dt.date.today().timetuple().tm_yday
    today_queries = [QUERIES_POOL[(day_of_year + i) % len(QUERIES_POOL)] for i in range(3)]

    log(f"Searching {len(today_queries)} queries...")
    for query in today_queries:
        results = web_search(query)
        for r in results:
            url = r.get("url", "").lower().rstrip("/")
            if url not in previously_recommended:
                all_results.append(r)

    # Deduplicate
    seen = set()
    unique_results = []
    for r in all_results:
        url = r["url"].lower().rstrip("/")
        if url not in seen:
            seen.add(url)
            unique_results.append(r)

    log(f"Found {len(unique_results)} new newsletters")
    return unique_results


def score_newsletter(result: dict) -> float:
    """Score a newsletter for recommendation quality."""
    score = 0.5
    url = result.get("url", "").lower()
    title = result.get("title", "")
    desc = result.get("description", "")

    # Prefer substack (highest quality sustained content)
    if "substack.com" in url:
        score += 2.0

    # Prefer newsletters with clear topical focus
    if any(t in (title + desc).lower() for t in ["intel", "security", "geopolit", "defense", "threat", "osint", "intelligence"]):
        score += 1.5

    # Length signals substance
    if len(desc) > 100:
        score += 0.5
    if len(title) > 20:
        score += 0.5

    return score


def recommend(discoveries: list[dict], max_recs: int = 3) -> list[dict]:
    """Select the top recommendations to include today."""
    scored = sorted(discoveries, key=score_newsletter, reverse=True)
    return scored[:max_recs]


def print_recommendations(recs: list[dict]) -> None:
    """Print recommendations in a parseable format."""
    for r in recs:
        print(f"NEWSLETTER: {r['title']}")
        print(f"  URL: {r['url']}")
        print(f"  About: {r['description'][:200]}")
        print()


def main() -> None:
    discoveries = find_newsletters()
    recs = recommend(discoveries)

    if not recs:
        log("No new newsletter recommendations today")
        print("NO_RECOMMENDATIONS")
        return

    # Log recommendations
    rec_log = load_rec_log()
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    for r in recs:
        url = r["url"].lower().rstrip("/")
        if url not in set(rec_log.get("recommended_urls", [])):
            rec_log.setdefault("recommended_urls", []).append(url)
            rec_log.setdefault("recommendations", []).append({
                "date": now,
                "title": r["title"],
                "url": r["url"],
                "description": r["description"][:200],
            })
    save_rec_log(rec_log)

    # Output for pipeline
    print_recommendations(recs)
    log(f"Recommended {len(recs)} newsletters")


if __name__ == "__main__":
    main()
