#!/usr/bin/env python3
"""
Social Monitor — polls public social channels for Mexico-relevant discussions.

Uses openweb specs for:
- Reddit: r/mexico, r/NarcoFootage, r/Narco
- Bluesky: AT Protocol search for Mexico keywords
- Telegram: public channel monitoring

Runs on a polling cadence (recommended: every 2-4 hours via cron).
Stores results in the collection records pipeline.

Usage:
    python3 scripts/social_monitor.py                     # Full run
    python3 scripts/social_monitor.py --platform reddit   # Reddit only
    python3 scripts/social_monitor.py --keywords "CJNG CDMX Sheinbaum USMCA"
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Mexico-relevant keywords for social monitoring
DEFAULT_KEYWORDS = [
    "Mexico", "CJNG", "Sinaloa", "Sheinbaum", "USMCA",
    "cartel", "fentanyl", "Mexico security", "Mexico economy",
]

# Public subreddits for Mexico monitoring
SUBREDDITS = {
    "mexico": "r/mexico — general Mexico discussion",
    "NarcoFootage": "r/NarcoFootage — cartel-related media",
    "Narcos": "r/Narcos — drug war discussion",
    "MexicoFinance": "r/MexicoFinance — economic/financial",
    "MexicoNews": "r/MexicoNews — news-focused",
}

# Bluesky feeds/keywords for Mexico
BLUESKY_KEYWORDS = ["Mexico", "Sheinbaum", "USMCA", "CJNG"]

STATE_FILE = REPO_ROOT / "tasks" / "social_monitor_state.json"


def log(msg: str) -> None:
    print(f"[social] {msg}", file=sys.stderr, flush=True)


def call_openweb(site: str, op: str, params: str) -> dict | None:
    """Call openweb CLI and return parsed result."""
    cmd = ["openweb", site, op]
    if params:
        cmd.append(params)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        stdout = result.stdout.strip()
        if stdout:
            data = json.loads(stdout)
            if isinstance(data, dict) and data.get("output"):
                with open(data["output"]) as f:
                    return json.loads(data["output"])
            return data
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        log(f"openweb call failed: {e}")
    return None


def scan_reddit(subreddits: list[str], keywords: list[str]) -> list[dict]:
    """Scan Reddit posts from specified subreddits for keyword matches."""
    found = []
    for sub in subreddits:
        log(f"Scanning r/{sub}...")
        data = call_openweb("reddit", "getSubredditPosts", json.dumps({"subreddit": sub, "limit": 15}))
        if not data:
            log(f"  → no data (Reddit may require login)")
            continue

        posts = data if isinstance(data, list) else data.get("data", {}).get("children", []) if isinstance(data, dict) else []
        for post in posts[:15]:
            if isinstance(post, dict):
                title = post.get("title", post.get("data", {}).get("title", ""))
                # Check for keyword matches
                matched_kw = [kw for kw in keywords if kw.lower() in title.lower()]
                if matched_kw:
                    found.append({
                        "platform": "reddit",
                        "subreddit": sub,
                        "title": title,
                        "matched_keywords": matched_kw,
                        "url": post.get("url", post.get("data", {}).get("url", "")),
                        "score": post.get("score", post.get("data", {}).get("score", 0)),
                        "detected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                    })
                    log(f"  → [{sub}] {title[:80]} (matches: {matched_kw})")

    return found


def scan_bluesky(keywords: list[str]) -> list[dict]:
    """Search Bluesky for Mexico keywords via direct API (no auth)."""
    import urllib.request, urllib.parse
    found = []
    for kw in keywords[:3]:
        log(f"Searching Bluesky for '{kw}'...")
        try:
            url = f"https://api.bsky.app/xrpc/app.bsky.feed.searchPosts?q={urllib.parse.quote(kw)}&limit=5"
            req = urllib.request.Request(url, headers={"User-Agent": "TREVOR/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                for post in data.get("posts", [])[:5]:
                    text = post.get("record", {}).get("text", "")[:200]
                    author = post.get("author", {}).get("handle", "?")
                    found.append({
                        "platform": "bluesky",
                        "author": author,
                        "text": text[:200],
                        "matched_keyword": kw,
                        "detected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                    })
                log(f"  → {len(data.get('posts',[]))} posts for '{kw}'")
        except Exception as e:
            log(f"  Bluesky '{kw}' failed: {e}")
    return found


def write_record(source: str, payload: dict) -> None:
    """Write a collection record."""
    record = {
        "source": source,
        "site_spec_version": "social-monitor-v1",
        "method": "openweb",
        "nato_admiralty_source_rating": "C",
        "nato_admiralty_info_rating": "3",
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "payload": {**payload, "qc_status": "PENDING_HUMAN_ANALYST_QC_REVIEW"},
    }
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "append_collection_record.py"),
         "--record", json.dumps(record)],
        capture_output=True, timeout=10,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Social Monitor for Mexico topics")
    parser.add_argument("--platform", choices=["reddit", "bluesky", "all"], default="all")
    parser.add_argument("--keywords", default=",".join(DEFAULT_KEYWORDS))
    args = parser.parse_args()

    keywords = [k.strip() for k in args.keywords.split(",")]

    all_found = []
    log(f"Monitoring for keywords: {keywords}")

    if args.platform in ("reddit", "all"):
        log("\n=== Reddit ===")
        items = scan_reddit(list(SUBREDDITS.keys()), keywords)
        write_record("reddit", {"subreddits": len(SUBREDDITS), "matches": len(items), "keywords": keywords[:5]})
        all_found.extend(items)

    if args.platform in ("bluesky", "all"):
        log("\n=== Bluesky ===")
        items = scan_bluesky(keywords)
        write_record("bluesky", {"searches": min(len(keywords), 3), "matches": len(items)})
        all_found.extend(items)

    log(f"\nTotal matches: {len(all_found)}")
    for f in all_found:
        print(json.dumps(f, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    main()
