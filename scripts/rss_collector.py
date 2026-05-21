#!/usr/bin/env python3
"""
RSS Collector — Reads sources_tested.json, fetches working RSS feeds, 
groups by region, and saves structured incidents.

Intended to run as Step 1 in the daily brief pipeline, after 
pipeline_openweb_collect.py and before collect.py.

Usage:
    python3 scripts/rss_collector.py --working-dir <wd> [--regions regions.json]
    python3 scripts/rss_collector.py --working-dir <wd> --max-feeds 30
    python3 scripts/rss_collector.py --working-dir <wd> --rotate

Daily rotation:
  --rotate enables round-robin: instead of fetching all feeds each day,
  it fetches a subset (default 25) rotating through the full catalog.
  This keeps the pipeline fast while cycling through all sources.

Output:
  WORKING_DIR/raw/rss_incidents.json — structured incidents list
  WORKING_DIR/raw/rss_meta.json — metadata about which feeds were fetched
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import sys
import time
from typing import Any

import feedparser

REPO = pathlib.Path("/home/ubuntu/.openclaw/workspace")
DEFAULT_CATALOG = REPO / "analyst/meta/sources_tested.json"
DEFAULT_REGIONS = REPO / "skills/daily-intel-brief/references/regions.json"
CACHE_DIR = REPO / "tasks" / "rss_cache"

USER_AGENT = "TrevorRSSCollector/1.0 (+https://github.com/trevormentis-spec)"
SECURITY_KEYWORDS = re.compile(
    r"\b(strike|attack|killed|wounded|missile|drone|sanction|coup|protest|"
    r"clashes|operation|raid|airstrike|shelling|siege|treaty|election|"
    r"summit|withdrawal|sovereign|default|downgrade|hijack|hostage|cyber|"
    r"ransomware|phishing|breach|cartel|trafficking|seize|blockade|ceasefire|"
    r"war|invasion|nuclear|sanktion|explosion|attack)\b",
    re.IGNORECASE,
)


def log(msg: str) -> None:
    ts = dt.datetime.utcnow().strftime("%H:%M:%S")
    print(f"[rss_collect {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> Any:
    if not path.exists():
        log(f"ERROR: {path} not found")
        return None
    return json.loads(path.read_text())


def make_id(source: str, title: str) -> str:
    h = hashlib.md5(f"{source}|{title}".encode()).hexdigest()[:6]
    return f"rss-{h}"


def is_security_relevant(title: str, summary: str) -> bool:
    text = f"{title} {summary}"
    return bool(SECURITY_KEYWORDS.search(text))


def fetch_feed(url: str, timeout: int = 15) -> feedparser.FeedParserDict:
    """Fetch and parse an RSS/Atom feed. Returns feedparser object."""
    try:
        feedparser.USER_AGENT = USER_AGENT
        parsed = feedparser.parse(url)
        return parsed
    except Exception as exc:
        log(f"Exception fetching {url}: {exc}")
        return feedparser.FeedParserDict({"entries": [], "bozo": True})


def rss_entry_to_incident(entry: dict, source_name: str, region: str,
                          admiralty_rel: str, admiralty_cred: str,
                          now: str) -> dict | None:
    """Convert an RSS feed entry to a collector-compatible incident."""
    title = entry.get("title", "").strip()
    link = entry.get("link", "").strip()
    summary = entry.get("summary", entry.get("description", "")).strip() or ""
    # Handle HTML in summary
    summary = re.sub(r"<[^>]+>", " ", summary)[:600]
    
    if not title:
        return None
    
    # Only include security-relevant items
    if not is_security_relevant(title, summary):
        return None
    
    # Parse date
    published = entry.get("published_parsed") or entry.get("updated_parsed")
    if published:
        occurred = dt.datetime(*published[:6], tzinfo=dt.timezone.utc).isoformat()
    else:
        occurred = now
    
    # Categorise
    text = f"{title} {summary}".lower()
    if any(k in text for k in ("strike", "missile", "shelling", "airstrike", "raid", "clashes", "casualt", "explosion")):
        category = "kinetic"
    elif any(k in text for k in ("cyber", "ransomware", "phishing", "breach", "hack")):
        category = "cyber"
    elif any(k in text for k in ("vessel", "tanker", "ais", "ukmto", "maritime", "hijack", "blockade")):
        category = "maritime"
    elif any(k in text for k in ("flight", "aircraft", "airspace", "ads-b", "no-fly")):
        category = "aviation"
    elif any(k in text for k in ("aid", "famine", "refugee", "humanitarian", "displaced")):
        category = "humanitarian"
    elif any(k in text for k in ("inflation", "rate", "fx", "yield", "default", "downgrade", "central bank", "imf", "oil", "brent")):
        category = "economic"
    else:
        category = "political"
    
    return {
        "id": make_id(source_name, title),
        "region": region,
        "country": None,
        "lat": None, "lon": None,
        "occurred_at_utc": occurred,
        "actors": [],
        "category": category,
        "headline": title[:200],
        "summary": summary[:600],
        "sources": [{
            "name": source_name,
            "url": link,
            "admiralty_reliability": admiralty_rel,
            "admiralty_credibility": admiralty_cred,
            "retrieved_at_utc": now,
        }],
        "single_source": True,
        "confidence_collector": "rss_direct",
    }


def deduplicate(items: list[dict]) -> list[dict]:
    by_key: dict[tuple, dict] = {}
    for it in items:
        key = (it["region"], it["headline"][:80].lower())
        if key not in by_key:
            by_key[key] = it
        else:
            existing = by_key[key]
            # Merge sources
            for s in it.get("sources", []):
                if s not in existing.get("sources", []):
                    existing["sources"].append(s)
                    existing["single_source"] = False
    return list(by_key.values())


def cap_per_region(items: list[dict], cap: int = 10) -> list[dict]:
    items.sort(key=lambda x: x["occurred_at_utc"], reverse=True)
    out: list[dict] = []
    counts: dict[str, int] = {}
    for it in items:
        c = counts.get(it["region"], 0)
        if c >= cap:
            continue
        counts[it["region"]] = c + 1
        out.append(it)
    return out


def get_rotation(catalog_path: pathlib.Path, day_to_fetch: int = 5) -> list[dict]:
    """Get a daily rotation of feeds from the catalog.
    
    Returns `day_to_fetch` feeds per region for the current day.
    Uses modulo-based rotation so all feeds get cycled over time.
    """
    catalog = load_json(catalog_path)
    if not catalog:
        return []
    
    sources = catalog.get("sources", [])
    working = [s for s in sources if s.get("status") == "working" and s.get("rss")]
    
    # Group by region
    by_region: dict[str, list[dict]] = {}
    for s in working:
        r = s.get("region", "global")
        by_region.setdefault(r, []).append(s)
    
    # Calculate day offset (use date hash for deterministic rotation)
    today = dt.date.today()
    day_num = today.toordinal()
    
    selected = []
    for region, feeds in sorted(by_region.items()):
        n = min(len(feeds), day_to_fetch)
        # Modulo rotation: different slice each day
        offset = day_num % max(1, len(feeds))
        indices = [(offset + i) % len(feeds) for i in range(n)]
        for idx in indices:
            selected.append(feeds[idx])
        
        if len(feeds) > day_to_fetch:
            log(f"  {region}: selected {n}/{len(feeds)} (daily rotation)")
        else:
            log(f"  {region}: selected all {n}")
    
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(description="RSS Collector for daily brief pipeline")
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--regions", default=str(DEFAULT_REGIONS))
    parser.add_argument("--rotate", action="store_true",
                        help="Rotate feeds across days instead of fetching all")
    parser.add_argument("--max-feeds", type=int, default=25,
                        help="Max feeds per region when rotating (default: 25)")
    parser.add_argument("--cap-per-region", type=int, default=10,
                        help="Max incidents per region in output (default: 10)")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Delay between fetches in seconds (default: 1.0)")
    args = parser.parse_args()
    
    wd = pathlib.Path(args.working_dir).expanduser().resolve()
    raw_dir = wd / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    catalog_path = pathlib.Path(args.catalog)
    regions_path = pathlib.Path(args.regions) if args.regions else None
    
    now = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    
    log(f"RSS Collector starting — catalog: {catalog_path}")
    
    # Load catalog
    catalog = load_json(catalog_path)
    if not catalog:
        log("ERROR: No catalog loaded. Exiting.")
        return 1
    
    sources = catalog.get("sources", [])
    
    # Select which feeds to fetch
    if args.rotate:
        selected = get_rotation(catalog_path, args.max_feeds)
        log(f"Daily rotation mode: {len(selected)} feeds selected")
    else:
        selected = [s for s in sources if s.get("status") == "working" and s.get("rss")]
        log(f"Full fetch mode: {len(selected)} working feeds available")
    
    if not selected:
        log("ERROR: No working feeds to fetch. Exiting.")
        return 1
    
    # Fetch all selected feeds
    all_incidents: list[dict] = []
    feed_meta: dict[str, Any] = {
        "started_at": now,
        "feeds_fetched": 0,
        "feeds_failed": 0,
        "total_raw_entries": 0,
        "total_incidents": 0,
        "feeds": {},
    }
    
    for source in selected:
        name = source.get("name", "Unknown")
        feed_url = source.get("rss", "")
        region = source.get("region", "global")
        rel = source.get("admiralty_source", "B")
        cred = source.get("admiralty_info", "2")
        
        if not feed_url:
            continue
        
        log(f"Fetching: {name} ({feed_url[:60]}...)")
        parsed = fetch_feed(feed_url)
        
        entries = parsed.entries
        n_raw = len(entries)
        incident_count = 0
        
        feed_meta["feeds"][name] = {
            "url": feed_url,
            "raw_entries": n_raw,
            "status": "ok" if n_raw > 0 else "empty",
            "feed_title": parsed.feed.get("title", ""),
        }
        feed_meta["feeds_fetched"] += 1
        feed_meta["total_raw_entries"] += n_raw
        
        if n_raw == 0:
            feed_meta["feeds_failed"] += 1
            time.sleep(args.delay)
            continue
        
        for entry in entries:
            incident = rss_entry_to_incident(entry, name, region, rel, cred, now)
            if incident:
                all_incidents.append(incident)
                incident_count += 1
        
        feed_meta["feeds"][name]["incidents"] = incident_count
        log(f"  → {n_raw} entries, {incident_count} security-relevant incidents")
        time.sleep(args.delay)
    
    # Deduplicate and cap
    all_incidents = deduplicate(all_incidents)
    all_incidents = cap_per_region(all_incidents, args.cap_per_region)
    
    feed_meta["total_incidents"] = len(all_incidents)
    feed_meta["completed_at"] = now
    
    # Write output
    incidents_path = raw_dir / "rss_incidents.json"
    meta_path = raw_dir / "rss_meta.json"
    
    incidents_path.write_text(json.dumps(all_incidents, indent=2))
    meta_path.write_text(json.dumps(feed_meta, indent=2))
    
    log(f"\n{'='*50}")
    log(f"RSS COLLECTION COMPLETE")
    log(f"{'='*50}")
    log(f"  Feeds fetched:  {feed_meta['feeds_fetched']}")
    log(f"  Feeds failed:   {feed_meta['feeds_failed']}")
    log(f"  Raw entries:    {feed_meta['total_raw_entries']}")
    log(f"  Incidents:      {feed_meta['total_incidents']}")
    log(f"  Written to:     {incidents_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
