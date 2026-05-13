#!/usr/bin/env python3
"""
Source Discovery Engine — Autonomous Source Discovery.

Searches the web for new intelligence sources to fill collection gaps.
Discovers RSS feeds, news sites, and OSINT channels for under-covered
regions, topics, and languages.

Design:
- Takes a region, topic, or language gap as input
- Searches the web for candidate sources (RSS feeds, news aggregators)
- Verifies each candidate (fetch RSS, check parseability)
- Scores for relevance, quality, and strategic value
- Adds qualifying sources to sources.json and collect.py LOCAL_LANGUAGE_FEEDS
- Tracks all discoveries in autonomy metrics

Usage:
    python3 scripts/source_discovery.py --region south_central_america
    python3 scripts/source_discovery.py --topic "Iran oil sanctions"
    python3 scripts/source_discovery.py --language ar --region middle_east
    python3 scripts/source_discovery.py --gap-report       # Scan all gaps
    python3 scripts/source_discovery.py --region africa --save   # Save discovered
    python3 scripts/source_discovery.py --discovered       # List previously discovered
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES_FILE = REPO_ROOT / "analyst" / "meta" / "sources.json"
COLLECT_SCRIPT = REPO_ROOT / "skills" / "daily-intel-brief" / "scripts" / "collect.py"
AUTONOMY_TRACKER_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "autonomy-tracker.json"
COLLECTION_STATE_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "collection-state.json"

# Discovered sources are stored here for review before pipeline integration
DISCOVERY_DIR = REPO_ROOT / "analysis" / "source-discoveries"

# Minimum signal score to auto-add a source (0-100)
AUTO_ADD_THRESHOLD = 60

# Web search config — uses Brave Search API
USER_AGENT = "TrevorSourceDiscovery/1.0 (+https://github.com/trevormentis-spec)"


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[discovery {ts}] {msg}", file=sys.stderr, flush=True)


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
    """Fetch a URL with timeout and user-agent."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            return data.decode("utf-8", errors="replace")
    except Exception as exc:
        log(f"  fetch failed: {exc}")
        return None


def parse_rss(xml_text: str, source_name: str) -> list[dict]:
    """Check if an RSS feed parses and return its recent items."""
    items = []
    if not xml_text:
        return items
    try:
        cleaned = re.sub(r"&(?![a-zA-Z]+;|#\d+;)", "&amp;", xml_text)
        root = ET.fromstring(cleaned)
    except ET.ParseError:
        return items
    # RSS 2.0
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        if not title:
            continue
        items.append({"title": title, "link": link, "summary": desc[:200]})
    # Atom
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
        title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
        link_el = entry.find("a:link", ns)
        link = (link_el.get("href") if link_el is not None else "").strip()
        if not title:
            continue
        items.append({"title": title, "link": link, "summary": ""})
    return items


def search_for_sources(region: str = "", topic: str = "", language: str = "") -> list[dict]:
    """Search the web for RSS feeds covering a region/topic/language gap.

    Uses Brave Search API via web_search or direct HTTP.
    Returns candidate sources with name, url, estimated RSS url.
    """
    candidates = []

    # Build search query
    parts = []
    if region:
        parts.append(region.replace("_", " "))
    if topic:
        parts.append(topic)
    if language:
        lang_name = {"ar": "Arabic", "fa": "Persian/Farsi", "ru": "Russian",
                      "zh": "Chinese", "he": "Hebrew", "es": "Spanish",
                      "fr": "French", "ja": "Japanese", "pt": "Portuguese",
                      "tr": "Turkish", "ur": "Urdu"}.get(language, language)
        parts.append(lang_name)

    # Generic search for RSS feeds
    query = " ".join(parts + ["news RSS feed"])
    if not parts:
        query = "international news RSS feed"

    log(f"Searching: '{query}'")

    # Attempt Brave Search API first
    api_key = os.environ.get("BRAVE_API_KEY", "")
    if api_key:
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://api.search.brave.com/res/v1/web/search?q={encoded}&count=10"
            req = urllib.request.Request(url, headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": api_key,
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
            results = data.get("web", {}).get("results", [])
            for r in results:
                candidates.append({
                    "name": r.get("title", "Unknown"),
                    "url": r.get("url", ""),
                    "description": (r.get("description") or "")[:300],
                    "source": "brave_search",
                })
        except Exception as exc:
            log(f"Brave search failed: {exc}")

    # Also try known source directories if search returned nothing
    if not candidates:
        # Fallback: check known aggregators
        known_feeds = {
            "africa": [
                {"name": "African Arguments", "url": "https://africanarguments.org", "rss": "https://africanarguments.org/feed/"},
                {"name": "The Africa Report", "url": "https://www.theafricareport.com", "rss": "https://www.theafricareport.com/feed/"},
                {"name": "ISS Africa", "url": "https://issafrica.org", "rss": "https://issafrica.org/rss.xml"},
            ],
            "south_central_america": [
                {"name": "MercoPress", "url": "https://en.mercopress.com", "rss": "https://en.mercopress.com/rss/news"},
                {"name": "Buenos Aires Times", "url": "https://www.batimes.com.ar", "rss": "https://www.batimes.com.ar/feed"},
                {"name": "EL PAÍS América", "url": "https://english.elpais.com/america/", "rss": "https://feeds.elpais.com/mrss-s/pages/ep-english/site/elpais.com/portada"},
            ],
            "middle_east": [
                {"name": "Al-Monitor", "url": "https://www.al-monitor.com", "rss": "https://www.al-monitor.com/rss/all"},
                {"name": "Amwaj.media", "url": "https://amwaj.media", "rss": "https://amwaj.media/feed"},
                {"name": "L'Orient Today", "url": "https://today.lorientlejour.com", "rss": "https://today.lorientlejour.com/rss"},
            ],
            "asia": [
                {"name": "The Diplomat", "url": "https://thediplomat.com", "rss": "https://thediplomat.com/feed/"},
                {"name": "South China Morning Post", "url": "https://www.scmp.com", "rss": "https://www.scmp.com/rss/"},
                {"name": "China Briefing", "url": "https://www.china-briefing.com", "rss": "https://www.china-briefing.com/feed/"},
            ],
            "europe": [
                {"name": "EUobserver", "url": "https://euobserver.com", "rss": "https://euobserver.com/rss.xml"},
                {"name": "European Defence Review", "url": "https://europeandefence.co.uk", "rss": "https://europeandefence.co.uk/feed/"},
                {"name": "Kyiv Independent", "url": "https://kyivindependent.com", "rss": "https://kyivindependent.com/feed/"},
            ],
        }
        for candidate in known_feeds.get(region, []):
            candidates.append({
                "name": candidate["name"],
                "url": candidate["url"],
                "description": f"Known {region} source from directory",
                "source": "known_directory",
                "rss_candidate": candidate["rss"],
            })

    return candidates


def verify_source(name: str, rss_url: str) -> dict:
    """Verify a source by fetching and parsing its RSS feed.

    Returns a verification result with score, item count, and last item.
    """
    result = {
        "name": name,
        "rss_url": rss_url,
        "verified": False,
        "items_count": 0,
        "last_item_title": "",
        "last_item_date": "",
        "score": 0,
        "error": "",
    }

    if not rss_url:
        result["error"] = "No RSS URL"
        return result

    body = fetch(rss_url)
    if not body:
        result["error"] = "Feed unreachable"
        return result

    items = parse_rss(body, name)
    result["items_count"] = len(items)
    result["verified"] = len(items) > 0

    if items:
        result["last_item_title"] = items[0]["title"][:100]
        last_item = items[min(len(items) - 1, 0)]
        result["last_item_date"] = last_item.get("pub", "")

    # Score: 0-100 based on verification quality
    score = 0
    if result["verified"]:
        score += 40  # Feed works
        if result["items_count"] >= 5:
            score += 20  # Has recent content
        if result["items_count"] >= 20:
            score += 15  # Substantial feed
        if len(name) > 5:
            score += 10  # Real-sounding name
        score += 15  # Baseline -- fetched successfully
    result["score"] = min(score, 100)

    return result


def score_relevance(candidate: dict, region: str, topic: str, language: str) -> int:
    """Score how relevant a candidate source is to the target gap."""
    score = 0
    text = (candidate.get("name", "") + " " +
            candidate.get("description", "") + " " +
            candidate.get("url", "")).lower()

    target_text = region.replace("_", " ")
    if topic:
        target_text += " " + topic
    if language:
        lang_name = {"ar": "arab", "fa": "iran|persian|farsi", "ru": "russia",
                      "zh": "china|chinese", "he": "israel|hebrew"}.get(language, language)
        target_text += " " + lang_name

    for term in target_text.lower().split():
        if term in text and len(term) > 2:
            score += 15

    # Bonus for news-related keywords
    for kw in ["news", "intelligence", "security", "analysis", "report",
                "times", "post", "herald", "tribune", "observer"]:
        if kw in text:
            score += 5

    return min(score, 50)


def get_existing_source_names() -> set[str]:
    """Get names of all sources already in the registry."""
    existing = set()
    data = load_json(SOURCES_FILE)
    for s in data.get("durable_sources", []):
        existing.add(s.get("name", "").lower())
    for s in data.get("local_language_sources", []):
        existing.add(s.get("name", "").lower())
    return existing


def add_to_sources(new_source: dict) -> bool:
    """Add a verified source to sources.json."""
    data = load_json(SOURCES_FILE)
    name_lower = new_source.get("name", "").lower()

    # Check duplicates
    existing = get_existing_source_names()
    if name_lower in existing:
        log(f"  ← already exists: {new_source['name']}")
        return False

    # Determine which list to add to
    languages = new_source.get("languages", ["en"])
    if languages != ["en"]:
        target_list = data.setdefault("local_language_sources", [])
    else:
        target_list = data.setdefault("durable_sources", [])

    target_list.append({
        "name": new_source["name"],
        "type": new_source.get("type", "News/Journalism"),
        "focus": new_source.get("focus", new_source.get("description", "")[:200]),
        "url": new_source["url"],
        "rss": new_source.get("rss_url", ""),
        "languages": languages,
        "signal_level": "Medium",
        "discovered": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
        "discovery_method": "autonomous_source_discovery",
        "source": "discovered",
    })

    save_json(SOURCES_FILE, data)
    log(f"  ✅ Added to sources.json: {new_source['name']}")
    return True


def discover_for_gap(region: str, topic: str = "", language: str = "",
                     auto_save: bool = False) -> list[dict]:
    """Discover sources for a specific gap and optionally add them."""
    DISCOVERY_DIR.mkdir(parents=True, exist_ok=True)
    existing_names = get_existing_source_names()
    discoveries = []

    # Step 1: Search for candidates
    candidates = search_for_sources(region, topic, language)
    log(f"Found {len(candidates)} candidates")

    if not candidates:
        log("  No candidates found — nothing to verify")
        return discoveries

    # Step 2: Verify candidates — try to find and check RSS feeds
    for candidate in candidates:
        name = candidate.get("name", "Unknown")

        # Try the candidate's RSS URL if known
        rss_url = candidate.get("rss_candidate", "")

        # Try common RSS paths if no explicit URL
        if not rss_url:
            base_url = candidate.get("url", "")
            for path in ["/rss", "/rss.xml", "/feed", "/feed/",
                          "/feed/rss.xml", "/news/rss.xml",
                          "/rss/news", "/xml/rss/all.xml",
                          "/tools/feeds/entries"]:
                test_url = base_url.rstrip("/") + path
                body = fetch(test_url, timeout=10)
                if body and len(body) > 200:
                    items = parse_rss(body, name)
                    if items:
                        rss_url = test_url
                        break

        if not rss_url:
            log(f"  ⏭ {name}: no RSS feed found")
            continue

        # Step 3: Verify
        result = verify_source(name, rss_url)
        if not result["verified"]:
            log(f"  ⏭ {name}: feed verification failed — {result.get('error', 'no items')}")
            continue

        # Step 4: Score relevance
        relevance = score_relevance(candidate, region, topic, language)
        final_score = (result["score"] + relevance) // 2

        discovery = {
            "name": name,
            "url": candidate.get("url", ""),
            "rss_url": rss_url,
            "description": candidate.get("description", "")[:200],
            "items_count": result["items_count"],
            "last_item": result["last_item_title"],
            "score": final_score,
            "region": region,
            "topic": topic,
            "language": language,
            "discovered_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        log(f"  ✓ {name}: fed_check={result['items_count']} items, relevance={relevance}, score={final_score}")
        discoveries.append(discovery)

        # Auto-add if score meets threshold and not already in registry
        if auto_save and final_score >= AUTO_ADD_THRESHOLD:
            if name.lower() not in existing_names:
                languages = [language] if language else ["en"]
                source_entry = {
                    "name": name,
                    "url": candidate.get("url", ""),
                    "rss_url": rss_url,
                    "description": candidate.get("description", "")[:200],
                    "focus": f"{region.replace('_', ' ').title()} news coverage. {candidate.get('description', '')[:150]}",
                    "languages": languages,
                    "type": "Discovered/News",
                }
                added = add_to_sources(source_entry)
                if added:
                    existing_names.add(name.lower())
            else:
                log(f"  Already in registry: {name}")

    # Save discovery report
    if discoveries:
        report_path = DISCOVERY_DIR / f"{region}-{dt.datetime.now(dt.timezone.utc).strftime('%H%M%S')}.json"
        save_json(report_path, {
            "search_query": f"{region} {topic} {language}",
            "discovered": len(discoveries),
            "discoveries": discoveries,
            "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
        log(f"Discovery report saved: {report_path}")

    return discoveries


def scan_all_gaps(auto_save: bool = False) -> dict:
    """Scan collection state for gaps and discover sources for each."""
    state = load_json(COLLECTION_STATE_FILE)
    bs = load_json(REPO_ROOT / "brain" / "memory" / "semantic" / "behavioral-state.json")

    # Determine gap regions from collection state + behavioral state
    gap_regions = set()

    # From collection state
    coll = bs.get("collection_directives", {}) if bs else {}
    for region, info in coll.get("by_region", {}).items():
        tier = info.get("collection_quality_tier", "")
        if tier in ("CRITICAL GAP", "LOW"):
            gap_regions.add(region)
        if info.get("linguistic_gaps"):
            gap_regions.add(region)

    # From expansion needed
    expansion = coll.get("expansion_needed", [])
    for r in expansion:
        gap_regions.add(r)

    # Add known under-covered regions
    gap_regions.add("south_central_america")  # Only 1 source
    gap_regions.add("africa")  # 0 sources

    if not gap_regions:
        log("No gaps identified — system may have full coverage")
        return {"discovered": 0, "gaps": []}

    results = []
    for region in sorted(gap_regions):
        log(f"\n=== Discovering sources for: {region} ===")
        # Determine language for region
        lang_map = {
            "middle_east": "ar",
            "asia": "zh",
            "europe": "ru",
            "south_central_america": "es",
            "africa": "fr",
        }
        language = lang_map.get(region, "")
        discoveries = discover_for_gap(region, language=language, auto_save=auto_save)
        results.append({"region": region, "discovered": len(discoveries), "language": language})

    # Track in autonomy metrics
    tracker = load_json(AUTONOMY_TRACKER_FILE) or {
        "version": 1, "created": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
        "unscheduled_cognition_events": [], "source_trust_changes": [],
        "procedural_learnings": [], "autonomous_prioritizations": [],
        "source_discoveries": [],
    }
    tracker.setdefault("source_discoveries", [])
    for r in results:
        if r["discovered"] > 0:
            tracker["source_discoveries"].append({
                "timestamp": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
                "region": r["region"],
                "sources_found": r["discovered"],
                "language": r["language"],
            })
    save_json(AUTONOMY_TRACKER_FILE, tracker)

    return {"discovered": sum(r["discovered"] for r in results), "gaps": results}


def list_discovered() -> None:
    """List all previously discovered sources."""
    if DISCOVERY_DIR.exists():
        for f in sorted(DISCOVERY_DIR.glob("*.json")):
            data = load_json(f)
            print(f"\n## Discovery: {f.stem}")
            print(f"Search: {data.get('search_query', '?')}")
            for d in data.get("discoveries", []):
                print(f"  {d['name']}: score={d['score']}, items={d['items_count']}, region={d['region']}")

    # Show from autonomy tracker
    tracker = load_json(AUTONOMY_TRACKER_FILE)
    discoveries = tracker.get("source_discoveries", [])
    if discoveries:
        print(f"\n## From Autonomy Tracker ({len(discoveries)} discovery sessions)")
        for d in discoveries:
            print(f"  {d['timestamp'][:19]}: {d['region']} — {d['sources_found']} sources found")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", default="", help="Region to find sources for")
    parser.add_argument("--topic", default="", help="Topic to search for")
    parser.add_argument("--language", default="", help="Language code (ar, fa, ru, zh, etc.)")
    parser.add_argument("--save", action="store_true", help="Auto-add discovered sources to pipeline")
    parser.add_argument("--gap-report", action="store_true", help="Scan all gaps and discover sources")
    parser.add_argument("--discovered", action="store_true", help="List previously discovered sources")
    args = parser.parse_args()

    if args.discovered:
        list_discovered()
        return 0

    if args.gap_report:
        result = scan_all_gaps(auto_save=args.save)
        print(f"\n=== Summary ===")
        print(f"Total discovered: {result['discovered']}")
        for r in result.get("gaps", []):
            status = "✅" if r["discovered"] > 0 else "❌"
            print(f"  {status} {r['region']}: {r['discovered']} sources (lang={r['language']})")
        return 0

    if args.region or args.topic or args.language:
        region = args.region or "global"
        discoveries = discover_for_gap(region, args.topic, args.language, auto_save=args.save)
        print(f"\n=== Results for {region.upper()} ===")
        print(f"Sources discovered: {len(discoveries)}")
        for d in discoveries:
            print(f"  ✓ {d['name']}: score={d['score']}, {d['items_count']} RSS items")
        return 0

    # Default: scan gaps
    result = scan_all_gaps(auto_save=False)
    print(f"Discovered {result['discovered']} new sources across gaps")
    return 0


if __name__ == "__main__":
    sys.exit(main())
