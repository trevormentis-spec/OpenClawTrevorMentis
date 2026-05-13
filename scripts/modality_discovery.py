#!/usr/bin/env python3
"""
Modality Discovery Engine — Autonomous Collection Modality Selection.

Trevor independently decides what KIND of intelligence source to pursue,
not just which RSS feed to add. This is the "I should monitor Telegram
channels for this region" decision.

Maintains a registry of collection modalities and their characteristics:
- What kind of data they provide (real-time, analytical, official)
- Which regions/topics they're best suited for
- How to discover sources in this modality
- How to fetch/parse data from this modality

When a region has a coverage gap, Trevor selects the best modality,
discovers sources, verifies them, and integrates them into the pipeline.

Usage:
    python3 scripts/modality_discovery.py --scan-gaps              # Scan all gaps for modality fit
    python3 scripts/modality_discovery.py --region africa          # What modality fits this region?
    python3 scripts/modality_discovery.py --discover telegram      # Discover Telegram sources
    python3 scripts/modality_discovery.py --report                 # Modality coverage report
    python3 scripts/modality_discovery.py --list-modalities        # List known modalities
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES_FILE = REPO_ROOT / "analyst" / "meta" / "sources.json"
COLLECT_SCRIPT = REPO_ROOT / "skills" / "daily-intel-brief" / "scripts" / "collect.py"
AUTONOMY_TRACKER_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "autonomy-tracker.json"
MODALITY_DIR = REPO_ROOT / "analysis" / "modality-discoveries"

USER_AGENT = "TrevorModalityDiscovery/1.0"

# ── Modality Registry ─────────────────────────────────────────────

MODALITIES = {
    "telegram": {
        "name": "Telegram Channels",
        "description": "Real-time OSINT channels, often breaking developments before news wires",
        "data_type": "real-time",
        "best_for": ["middle_east", "europe", "asia"],
        "strengths": ["Unmediated source", "real-time updates", "often primary source for Iran/Middle East"],
        "weaknesses": ["Propaganda risk", "unverified claims", "no editorial control"],
        "discovery_method": "web_search_telegram",
        "fetch_method": "scrape_telegram",
        "status": "ready",
    },
    "substack": {
        "name": "Substack Newsletters",
        "description": "Long-form analytical newsletters from domain experts",
        "data_type": "analytical",
        "best_for": ["global_finance", "middle_east", "europe"],
        "strengths": ["Deep analysis", "expert authors", "RSS-compatible"],
        "weaknesses": ["Long-form only", "publication cadence varies"],
        "discovery_method": "web_search_substack",
        "fetch_method": "rss_feed",
        "status": "ready",
    },
    "government_rss": {
        "name": "Government & IGO Press Releases",
        "description": "Official statements from governments and international organizations",
        "data_type": "official",
        "best_for": ["north_america", "europe", "global_finance"],
        "strengths": ["Authoritative", "structured", "predictable"],
        "weaknesses": ["Official narratives only", "may lag events"],
        "discovery_method": "known_feeds",
        "fetch_method": "rss_feed",
        "status": "ready",
    },
    "youtube_transcript": {
        "name": "YouTube Analysis Transcripts",
        "description": "Transcripts from OSINT and geopolitical analysis channels",
        "data_type": "analytical",
        "best_for": ["middle_east", "europe", "global_finance"],
        "strengths": ["Deep analysis", "multi-hour content", "expert hosts"],
        "weaknesses": ["Transcript fetch unreliable", "long-form only"],
        "discovery_method": "web_search_youtube",
        "fetch_method": "youtube_transcript_api",
        "status": "experimental",
    },
    "reddit_communities": {
        "name": "Reddit OSINT Communities",
        "description": "Crowd-sourced intelligence analysis and discussion",
        "data_type": "crowd-sourced",
        "best_for": ["middle_east", "europe", "global_finance"],
        "strengths": ["Fast-breaking", "crowd verification", "diverse sources"],
        "weaknesses": ["Noise", "unverified", "variable quality"],
        "discovery_method": "web_search_reddit",
        "fetch_method": "reddit_rss",
        "status": "experimental",
    },
}

REGION_MODALITY_FIT = {
    "middle_east": ["telegram", "substack", "youtube_transcript"],
    "europe": ["telegram", "substack", "government_rss"],
    "asia": ["telegram", "substack", "government_rss"],
    "north_america": ["government_rss", "substack"],
    "south_central_america": ["reddit_communities", "government_rss"],
    "africa": ["reddit_communities", "government_rss", "telegram"],
    "global_finance": ["substack", "government_rss"],
}

# Known modality-specific sources that can be immediately integrated
KNOWN_MODALITY_SOURCES = {
    "telegram": [
        {
            "name": "Judean OSINT",
            "channel": "judean_osint",
            "url": "https://t.me/judean_osint",
            "description": "Dedicated Iran-Israel real-time OSINT",
            "region": "middle_east",
            "signal_level": "High",
            "discovered": "2026-05-12",
        },
        {
            "name": "Straits of Hormuz Monitor",
            "channel": "HormuzMonitor",
            "url": "https://t.me/HormuzMonitor",
            "description": "Real-time Strait of Hormuz tanker traffic bot",
            "region": "middle_east",
            "signal_level": "High",
            "discovered": "2026-05-12",
        },
    ],
    "substack": [
        # Already covered by existing sources.json — just need to ensure RSS fetch
    ],
    "government_rss": [
        {
            "name": "UK FCDO Press Releases",
            "url": "https://www.gov.uk/government/organisations/foreign-commonwealth-development-office.atom",
            "description": "UK Foreign Office official statements",
            "region": "europe",
            "signal_level": "High",
        },
        {
            "name": "US State Department Briefings",
            "url": "https://www.state.gov/feed/",
            "description": "US State Department official releases",
            "region": "north_america",
            "signal_level": "High",
        },
        {
            "name": "UN News RSS",
            "url": "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
            "description": "United Nations news and press releases",
            "region": "global_finance",
            "signal_level": "High",
        },
        {
            "name": "EU Press Releases",
            "url": "https://ec.europa.eu/commission/presscorner/api/iprss",
            "description": "European Commission official press releases",
            "region": "europe",
            "signal_level": "High",
        },
        {
            "name": "IAEA Press Releases",
            "url": "https://www.iaea.org/news/rss",
            "description": "IAEA official statements and nuclear monitoring",
            "region": "middle_east",
            "signal_level": "High",
        },
    ],
    "youtube_transcript": [
        {
            "name": "Perun (YouTube)",
            "channel_id": "UCC3ehuUksTyQ7bbjGntmx3Q",
            "url": "https://www.youtube.com/@PerunAU",
            "description": "Military-industrial complex analysis",
            "region": "europe",
            "signal_level": "High",
        },
        {
            "name": "Bilawal Sidhu (YouTube)",
            "channel_id": "UCBilawalSidhu",
            "url": "https://www.youtube.com/@bilawalsidhu",
            "description": "4D geospatial OSINT reconstruction",
            "region": "middle_east",
            "signal_level": "High",
        },
    ],
}


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[modality {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, Exception):
            return {}
    return {}


def save_json(path: pathlib.Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def fetch(url: str, timeout: int = 15) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return None


# ── Telecom Discovery ─────────────────────────────────────────────

def discover_telegram_sources(region: str) -> list[dict]:
    """Discover Telegram channels for a region.

    Uses the known list first, then searches web for more.
    """
    sources = []
    region_keywords = {
        "middle_east": ["iran", "hormuz", "middle east", "israel", "gaza", "hezbollah"],
        "europe": ["ukraine", "russia", "nato", "eu"],
        "asia": ["china", "taiwan", "korea", "pacific"],
        "africa": ["africa", "sahel", "horn of africa"],
    }
    keywords = region_keywords.get(region, [region])

    # Start with known sources
    for src in KNOWN_MODALITY_SOURCES.get("telegram", []):
        if src.get("region") == region or not region:
            sources.append(src)

    # Search for more Telegram channels via web
    for keyword in keywords[:3]:
        query = f"telegram channel {keyword} news osint"
        log(f"  Searching: '{query}'")
        try:
            brave_key = os.environ.get("BRAVE_API_KEY", "")
            if brave_key:
                encoded = urllib.parse.quote(query)
                url = f"https://api.search.brave.com/res/v1/web/search?q={encoded}&count=5"
                req = urllib.request.Request(url, headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": brave_key,
                })
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read())
                for r in data.get("web", {}).get("results", []):
                    link = r.get("url", "")
                    title = r.get("title", "")
                    desc = r.get("description", "")
                    # Look for Telegram links
                    tg_match = re.search(r't\.me/([a-zA-Z0-9_]+)', link)
                    if tg_match:
                        channel = tg_match.group(1)
                        # Avoid duplicates
                        if not any(s.get("channel") == channel for s in sources):
                            sources.append({
                                "name": title.split("–")[0].split(" — ")[0].strip()[:50],
                                "channel": channel,
                                "url": f"https://t.me/{channel}",
                                "description": desc[:300],
                                "region": region,
                                "signal_level": "Medium",
                                "source": "brave_search",
                            })
                            log(f"    Found Telegram: {channel}")
        except Exception as exc:
            log(f"  Search failed: {exc}")
            continue

    # Verify each source
    verified = []
    for src in sources:
        channel = src.get("channel", "")
        if not channel:
            continue
        # Verify by attempting to fetch the public channel
        tg_url = f"https://t.me/s/{channel}"
        body = fetch(tg_url, timeout=15)
        if body and len(body) > 1000:
            # Parse channel name from page
            name_match = re.search(r'<div class="tgme_channel_info_header_title"><span>(.*?)</span>', body)
            channel_name = name_match.group(1) if name_match else channel
            # Count recent messages
            msg_count = len(re.findall(r'<div class="tgme_widget_message_wrap', body))
            src["verified"] = True
            src["channel_name"] = channel_name
            src["recent_messages"] = msg_count
            src["fetch_url"] = tg_url
            verified.append(src)
            log(f"  ✅ Telegram @{channel}: '{channel_name}', {msg_count} recent messages")
        else:
            log(f"  ⏭ Telegram @{channel}: unreachable or empty")

    return verified


# ── Government RSS Discovery ──────────────────────────────────────

def discover_government_sources(region: str) -> list[dict]:
    """Return known government/IGO RSS feeds for a region."""
    sources = []
    for src in KNOWN_MODALITY_SOURCES.get("government_rss", []):
        if src.get("region") == region or not region:
            # Verify the RSS feed works
            body = fetch(src["url"], timeout=10)
            if body and len(body) > 500:
                sources.append({**src, "verified": True})
                log(f"  ✅ {src['name']}: RSS verified")
            else:
                log(f"  ⏭ {src['name']}: RSS unreachable")
    return sources


# ── YouTube Discovery ─────────────────────────────────────────────

def discover_youtube_sources(region: str) -> list[dict]:
    """Return known YouTube channels for a region."""
    sources = []
    for src in KNOWN_MODALITY_SOURCES.get("youtube_transcript", []):
        if src.get("region") == region or not region:
            sources.append({**src, "verified": True})
    return sources


# ── Modality Selection ────────────────────────────────────────────

def get_best_modality(region: str, available: list[str]) -> str | None:
    """Select the best modality for a given region based on fit and availability."""
    preferred = REGION_MODALITY_FIT.get(region, ["substack"])
    for modality in preferred:
        if modality in available:
            return modality
    return None


def discover_for_region(region: str, modality: str = "") -> list[dict]:
    """Discover new sources for a region using the best modality or specified one."""
    MODALITY_DIR.mkdir(parents=True, exist_ok=True)
    
    available = [m for m, info in MODALITIES.items() if info["status"] == "ready"]
    
    if not modality:
        modality = get_best_modality(region, available) or "substack"
    
    log(f"Discovering {modality} sources for {region}")
    MODALITY_DIR.mkdir(parents=True, exist_ok=True)

    discoverers = {
        "telegram": discover_telegram_sources,
        "government_rss": discover_government_sources,
        "substack": lambda r: [],  # Handled by source_discovery.py
        "youtube_transcript": discover_youtube_sources,
    }

    discover_func = discoverers.get(modality)
    if not discover_func:
        log(f"No discoverer for modality: {modality}")
        return []

    sources = discover_func(region)
    
    if sources:
        report = {
            "region": region,
            "modality": modality,
            "timestamp": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sources_found": len(sources),
            "sources": sources,
        }
        report_path = MODALITY_DIR / f"{region}-{modality}-{dt.datetime.now(dt.timezone.utc).strftime('%H%M%S')}.json"
        save_json(report_path, report)
        log(f"Report saved: {report_path}")

    return sources


def integrate_telegram_sources(sources: list[dict]) -> int:
    """Add telegram sources to the collection pipeline."""
    integrated = 0
    
    for src in sources:
        if not src.get("verified"):
            continue
        channel = src["channel"]
        fetch_url = f"https://t.me/s/{channel}"
        
        # Add to sources.json
        data = load_json(SOURCES_FILE)
        existing_names = {s.get("name", "").lower(): s for s in data.get("durable_sources", [])}
        
        name = src.get("channel_name", src["name"])
        if name.lower() in existing_names:
            log(f"  Already in sources.json: {name}")
            continue
        
        entry = {
            "name": name,
            "type": "Telegram/OSINT",
            "focus": f"Telegram channel: {src.get('description', '')[:200]}",
            "url": fetch_url,
            "rss": fetch_url,
            "modality": "telegram",
            "channel": channel,
            "signal_level": src.get("signal_level", "Medium"),
            "discovered": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
            "discovery_method": "modality_discovery",
        }
        data.setdefault("durable_sources", []).append(entry)
        save_json(SOURCES_FILE, data)
        
        # Add to collect.py's collection
        _add_to_collect_py(name, fetch_url, "telegram", src.get("region", "global"))
        
        log(f"  ✅ Integrated Telegram @{channel} into pipeline")
        integrated += 1
    
    return integrated


def _add_to_collect_py(name: str, url: str, modality: str, region: str) -> None:
    """Add a modality-specific source to collect.py's feed lists."""
    if not COLLECT_SCRIPT.exists():
        log(f"  collect.py not found at {COLLECT_SCRIPT}")
        return

    content = COLLECT_SCRIPT.read_text()
    
    if f'"{name}"' in content:
        log(f"  Already in collect.py: {name}")
        return
    
    # Find the LOCAL_LANGUAGE_FEEDS or the // Gmail intel digest line to add before
    insertion_points = [
        ("# Gmail intel digest", 
         f"    #{ modality.upper() } — discovered by modality discovery\n"
         f"    (\"{name}\", \"{url}\", \"en\", (\"C\", 3)),\n\n"
         f"# Gmail intel digest"),
    ]
    
    for marker, replacement in insertion_points:
        if marker in content:
            content = content.replace(marker, replacement)
            COLLECT_SCRIPT.write_text(content)
            log(f"  Added to collect.py: {name}")
            return

    log(f"  Could not find insertion point in collect.py for {name}")


# ── Scan Gaps ──────────────────────────────────────────────────────

def scan_and_discover() -> dict:
    """Scan all regions for coverage gaps and discover modality-specific sources."""
    bs = load_json(REPO_ROOT / "brain" / "memory" / "semantic" / "behavioral-state.json")
    coll = bs.get("collection_directives", {}) if bs else {}
    
    # Find regions needing new collection modalities
    gap_regions = set()
    for region, info in coll.get("by_region", {}).items():
        q = info.get("collection_quality_tier", "")
        if q in ("CRITICAL GAP", "LOW"):
            gap_regions.add(region)
        if info.get("linguistic_gaps"):
            gap_regions.add(region)
    
    # Always check under-covered regions
    gap_regions.add("africa")
    gap_regions.add("south_central_america")
    
    results = []
    for region in sorted(gap_regions):
        log(f"\n{'='*50}")
        log(f"Discovering for {region}")
        log(f"{'='*50}")
        
        # Try Telegram first (most valuable for new modalities)
        tg_sources = discover_for_region(region, "telegram")
        if tg_sources:
            integrated = integrate_telegram_sources(tg_sources)
            results.append({"region": region, "modality": "telegram", "found": len(tg_sources), "integrated": integrated})
        
        # Then government RSS
        gov_sources = discover_for_region(region, "government_rss")
        if gov_sources:
            results.append({"region": region, "modality": "government_rss", "found": len(gov_sources), "integrated": 0})
    
    # Track in autonomy metrics
    tracker = load_json(AUTONOMY_TRACKER_FILE) or {}
    tracker.setdefault("modality_discoveries", [])
    for r in results:
        tracker["modality_discoveries"].append({
            "timestamp": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "region": r["region"],
            "modality": r["modality"],
            "sources_found": r["found"],
            "integrated": r["integrated"],
        })
    save_json(AUTONOMY_TRACKER_FILE, tracker)
    
    return {"scanned": len(gap_regions), "results": results}


# ── Report ─────────────────────────────────────────────────────────

def modality_report() -> None:
    """Report modality coverage and recent discoveries."""
    tracker = load_json(AUTONOMY_TRACKER_FILE)
    discoveries = tracker.get("modality_discoveries", [])

    print("# Collection Modality Coverage")
    print()
    print("| Modality | Status | Best For | Data Type |")
    print("|----------|--------|----------|-----------|")
    for m, info in sorted(MODALITIES.items()):
        best = ", ".join(info["best_for"][:3])
        print(f"| {info['name']} | {info['status']} | {best} | {info['data_type']} |")
    
    print()
    print("## Discoveries")
    print()
    if discoveries:
        for d in discoveries:
            print(f"- {d['timestamp'][:19]}: {d['modality']} → {d['region']} ({d['sources_found']} found, {d['integrated']} integrated)")
    else:
        print("(No modality discoveries yet)")
    
    print()
    print("## Telegram Sources Currently Available for Integration")
    tg_available = KNOWN_MODALITY_SOURCES.get("telegram", [])
    for s in tg_available:
        print(f"- @{s['channel']} ({s['region']}): {s['description'][:80]}")
    
    print()
    print("## Government RSS Sources Available for Integration")
    gov_available = KNOWN_MODALITY_SOURCES.get("government_rss", [])
    for s in gov_available:
        status = "✅" if fetch(s["url"], timeout=5) else "⏭"
        print(f"- {status} {s['name']} ({s['region']})")


def list_modalities() -> None:
    """List all known collection modalities."""
    print("# Collection Modalities")
    print()
    for m, info in sorted(MODALITIES.items()):
        print(f"## {info['name']}")
        print(f"*{info['description']}*")
        print(f"- Data type: {info['data_type']}")
        print(f"- Best for: {', '.join(info['best_for'])}")
        print(f"- Strengths: {', '.join(info['strengths'])}")
        print(f"- Weaknesses: {', '.join(info['weaknesses'])}")
        print(f"- Discovery: {info['discovery_method']}")
        print(f"- Fetch: {info['fetch_method']}")
        print(f"- Status: {info['status']}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan-gaps", action="store_true", help="Scan gaps and discover modality sources")
    parser.add_argument("--region", default="", help="Target region")
    parser.add_argument("--discover", default="", help="Modality to discover (telegram, substack, etc.)")
    parser.add_argument("--integrate", action="store_true", help="Integrate discovered sources into pipeline")
    parser.add_argument("--report", action="store_true", help="Modality coverage report")
    parser.add_argument("--list-modalities", action="store_true", help="List known modalities")
    args = parser.parse_args()

    if args.list_modalities:
        list_modalities()
        return 0

    if args.report:
        modality_report()
        return 0

    if args.scan_gaps:
        result = scan_and_discover()
        print(f"\nScanned {result['scanned']} regions across all modalities")
        for r in result.get("results", []):
            print(f"  {r['region']}: {r['modality']} → {r['found']} found, {r['integrated']} integrated")
        return 0

    if args.region:
        sources = discover_for_region(args.region, args.discover)
        if args.integrate and sources:
            modal = args.discover or "telegram"
            if modal == "telegram":
                integrated = integrate_telegram_sources(sources)
                print(f"Integrated {integrated}/{len(sources)} sources into pipeline")
        print(f"\nDiscovered {len(sources)} {args.discover or 'new modality'} sources for {args.region}")
        for s in sources:
            print(f"  ✅ {s.get('channel_name', s.get('name', '?'))}: {s.get('description', '')[:100]}")
        return 0

    # Default: scan gaps
    result = scan_and_discover()
    print(f"\nScanned {result['scanned']} regions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
