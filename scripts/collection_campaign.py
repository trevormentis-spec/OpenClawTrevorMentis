#!/usr/bin/env python3
"""
Collection Campaign Launcher — Autonomous Collection Campaigns.

Launches supplementary collection runs outside the scheduled daily cycle.
When behavioral state identifies a region needing expansion, this script:
1. Runs source discovery for the target region
2. Performs supplementary RSS/feed collection from discovered + existing sources
3. Summarizes findings as a "campaign report"
4. Stores results for pipeline pickup by next analysis run
5. Adds newly discovered sources to the permanent collection pipeline

Triggered by:
  - behavioral_state.py autonomous_prioritization (high-priority regions)
  - continuous_monitor.py escalation (critical events need deeper collection)
  - Manual invocation for gap regions

Usage:
    python3 scripts/collection_campaign.py                            # Check and launch
    python3 scripts/collection_campaign.py --region middle_east       # Target specific region
    python3 scripts/collection_campaign.py --region africa --discover # Discover + collect
    python3 scripts/collection_campaign.py --campaigns                # Show past campaigns
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import subprocess
import sys
import urllib.request
import re
from typing import Any
from xml.etree import ElementTree as ET

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BEHAVIORAL_STATE_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "behavioral-state.json"
AUTONOMY_TRACKER_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "autonomy-tracker.json"
COLLECT_SCRIPT = REPO_ROOT / "skills" / "daily-intel-brief" / "scripts" / "collect.py"
DISCOVERY_SCRIPT = REPO_ROOT / "scripts" / "source_discovery.py"
CAMPAIGN_DIR = REPO_ROOT / "analysis" / "campaigns"

# Minimum region priority to auto-launch a campaign
AUTO_LAUNCH_THRESHOLD = 80  # 0-100 priority score

USER_AGENT = "TrevorCampaign/1.0"


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[campaign {ts}] {msg}", file=sys.stderr, flush=True)


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
    except Exception:
        return None


def parse_rss(xml_text: str, source_name: str) -> list[dict]:
    items = []
    if not xml_text:
        return items
    try:
        cleaned = re.sub(r"&(?![a-zA-Z]+;|#\d+;)", "&amp;", xml_text)
        root = ET.fromstring(cleaned)
    except ET.ParseError:
        return items
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        if not title:
            continue
        items.append({"title": title, "link": link, "summary": desc[:300],
                       "source": source_name})
    for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
        title = (entry.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
        link_el = entry.find("{http://www.w3.org/2005/Atom}link")
        link = (link_el.get("href") if link_el is not None else "").strip()
        if not title:
            continue
        items.append({"title": title, "link": link, "summary": "",
                       "source": source_name})
    return items


def get_target_regions() -> list[dict]:
    """Determine which regions need collection campaigns."""
    bs = load_json(BEHAVIORAL_STATE_FILE)
    if not bs:
        log("No behavioral state — checking collection gaps directly")
        coll = load_json(REPO_ROOT / "brain" / "memory" / "semantic" / "collection-state.json")
        if not coll:
            return []
        # Fall back to regions with lowest coverage
        targets = []
        for region in ["south_central_america", "africa", "asia", "europe"]:
            activity = coll.get("region_activity", {}).get(region, {})
            score = activity.get("smoothed_score", 0)
            if score < 5:
                targets.append({"region": region, "priority": 50, "reason": "low collection activity"})
        return targets

    # Use autonomous prioritization
    prio = bs.get("autonomous_prioritization", {})
    coll = bs.get("collection_directives", {})
    targets = []

    for region, p in sorted(prio.items()):
        score = p.get("priority_score", 0)
        reasons = p.get("reasons", [])

        # Trigger on high priority or critical gaps
        if score >= AUTO_LAUNCH_THRESHOLD:
            targets.append({
                "region": region,
                "priority": score,
                "reason": "; ".join(reasons) if reasons else "high priority score",
            })
            continue

        # Also trigger for collection quality gaps
        coll_region = coll.get("by_region", {}).get(region, {})
        quality = coll_region.get("collection_quality_tier", "")
        if quality in ("CRITICAL GAP",):
            targets.append({
                "region": region,
                "priority": score,
                "reason": f"critical collection quality gap",
            })

    return targets


def collect_feeds(feeds: list[tuple[str, str, str]]) -> list[dict]:
    """Fetch and parse multiple RSS feeds. Returns all items."""
    all_items = []
    for name, rss_url, region in feeds:
        log(f"  Fetching: {name}")
        body = fetch(rss_url)
        if not body:
            log(f"    ✗ unreachable")
            continue
        items = parse_rss(body, name)
        # Tag each item with its region
        for item in items:
            item["target_region"] = region
        all_items.extend(items)
        log(f"    ✓ {len(items)} items")
    return all_items


def launch_campaign(region: str, priority: int, reason: str,
                    discover_sources: bool = False,
                    feeds_to_try: list[tuple[str, str, str]] | None = None) -> dict:
    """Launch a collection campaign for a specific region.

    Steps:
    1. Optionally discover new sources
    2. Fetch RSS from campaign-specific feeds
    3. Compile campaign report
    4. Save for pipeline pickup
    """
    CAMPAIGN_DIR.mkdir(parents=True, exist_ok=True)
    campaign_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    log(f"LAUNCHING campaign [{campaign_id}] for {region} (priority={priority})")

    discovered_sources = []

    # Step 1: Source discovery (if requested or if region has gaps)
    if discover_sources:
        log("  Running source discovery...")
        try:
            result = subprocess.check_call([
                "python3", str(DISCOVERY_SCRIPT),
                "--region", region,
                "--save",
            ], cwd=str(REPO_ROOT), timeout=60)
            log(f"  Source discovery completed (exit={result})")
        except Exception as exc:
            log(f"  Source discovery failed: {exc}")

    # Step 2: Fetch feeds (either provided or from sources.json)
    campaign_feeds = feeds_to_try or []
    if not campaign_feeds:
        # Search sources.json for this region
        sources_data = load_json(REPO_ROOT / "analyst" / "meta" / "sources.json")
        for s in sources_data.get("durable_sources", []):
            rss = s.get("rss", "") or s.get("url", "")
            if rss and ("Iran" in s.get("name", "") or "Hormuz" in s.get("name", "")):
                if region in ("middle_east",):
                    campaign_feeds.append((s["name"], rss, region))
        for s in sources_data.get("local_language_sources", []):
            rss = s.get("rss", "")
            lang = s.get("primary_language", "en")
            if rss:
                # Add local-language sources for this region
                if region == "middle_east" and lang in ("ar", "fa"):
                    campaign_feeds.append((s["name"], rss, region))
                elif region == "asia" and lang in ("zh", "ja", "ko"):
                    campaign_feeds.append((s["name"], rss, region))
                elif region == "europe" and lang in ("ru",):
                    campaign_feeds.append((s["name"], rss, region))

    # If still no feeds, add some default campaign-specific feeds
    if not campaign_feeds:
        default_feeds = {
            "middle_east": [
                ("Al-Monitor", "https://www.al-monitor.com/rss/all", "middle_east"),
                ("Iran International", "https://www.iranintl.com/en/rss", "middle_east"),
            ],
            "asia": [
                ("The Diplomat", "https://thediplomat.com/feed/", "asia"),
                ("Nikkei Asia", "https://asia.nikkei.com/rss/feed", "asia"),
            ],
            "europe": [
                ("EUobserver", "https://euobserver.com/rss.xml", "europe"),
                ("Kyiv Independent", "https://kyivindependent.com/feed/", "europe"),
            ],
            "south_central_america": [
                ("MercoPress", "https://en.mercopress.com/rss/news", "south_central_america"),
            ],
            "africa": [
                ("AllAfrica", "https://allafrica.com/tools/headlines/rss/latest/headlines.xml", "africa"),
            ],
        }
        campaign_feeds = default_feeds.get(region, [])

    # Step 3: Fetch all feeds
    items = collect_feeds(campaign_feeds)

    # Step 4: Build campaign report
    report = {
        "campaign_id": campaign_id,
        "region": region,
        "launched_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "priority": priority,
        "reason": reason,
        "feeds_fetched": len(campaign_feeds),
        "total_items": len(items),
        "items": items[:50],  # Cap at 50 items
        "source_discovery_run": discover_sources,
    }

    # Save campaign report
    report_path = CAMPAIGN_DIR / f"{campaign_id}-{region}.json"
    save_json(report_path, report)
    log(f"Campaign report: {report_path} ({len(items)} items from {len(campaign_feeds)} feeds)")

    # Step 5: Track in autonomy metrics
    tracker = load_json(AUTONOMY_TRACKER_FILE) or {
        "version": 1, "created": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
        "unscheduled_cognition_events": [], "source_trust_changes": [],
        "procedural_learnings": [], "autonomous_prioritizations": [],
        "source_discoveries": [], "collection_campaigns": [],
    }
    tracker.setdefault("collection_campaigns", []).append({
        "campaign_id": campaign_id,
        "timestamp": report["launched_at"],
        "region": region,
        "priority": priority,
        "reason": reason,
        "feeds_fetched": len(campaign_feeds),
        "items_collected": len(items),
        "report_path": str(report_path),
    })
    save_json(AUTONOMY_TRACKER_FILE, tracker)

    # Print summary
    print(f"\nCampaign {campaign_id} for {region.upper()}:")
    print(f"  Feeds fetched: {len(campaign_feeds)}")
    print(f"  Items collected: {len(items)}")
    print(f"  Report: {report_path}")

    return report


def check_and_launch() -> int:
    """Check behavioral state and launch campaigns for priority regions."""
    targets = get_target_regions()
    launched = 0

    if not targets:
        log("No regions need campaigns")
        return 0

    log(f"Targets identified: {len(targets)}")
    for target in targets:
        region = target["region"]
        priority = target["priority"]
        reason = target["reason"]
        log(f"  {region}: priority={priority} — {reason}")

        # Check cooldown: don't campaign same region more than once per 12h
        tracker = load_json(AUTONOMY_TRACKER_FILE) or {}
        campaigns = tracker.get("collection_campaigns", [])
        now = dt.datetime.now(dt.timezone.utc)
        in_cooldown = False
        for c in campaigns:
            if c.get("region") == region:
                try:
                    ts = dt.datetime.fromisoformat(c["timestamp"].replace("Z", "+00:00"))
                    if (now - ts).total_seconds() < 43200:  # 12h
                        in_cooldown = True
                        break
                except (ValueError, TypeError):
                    continue
        if in_cooldown:
            log(f"  {region}: in cooldown (12h) — skipping")
            continue

        # Launch campaign
        discover = priority >= 90  # Auto-discover for highest priority
        launch_campaign(region, priority, reason, discover_sources=discover)
        launched += 1

    return launched


def show_campaigns() -> None:
    """Show past collection campaigns."""
    tracker = load_json(AUTONOMY_TRACKER_FILE)
    campaigns = tracker.get("collection_campaigns", [])
    if not campaigns:
        print("No collection campaigns have been run yet.")
        return

    print(f"# Collection Campaigns ({len(campaigns)} total)")
    print()
    for c in campaigns:
        print(f"## {c['campaign_id']} — {c['region'].upper()}")
        print(f"**Time:** {c['timestamp'][:19]} UTC")
        print(f"**Priority:** {c['priority']}")
        print(f"**Reason:** {c['reason']}")
        print(f"**Feeds:** {c['feeds_fetched']} | **Items:** {c['items_collected']}")
        print()

    # Show on-disk reports
    if CAMPAIGN_DIR.exists():
        print("**Campaign reports on disk:**")
        for f in sorted(CAMPAIGN_DIR.glob("*.json")):
            data = load_json(f)
            print(f"  {f.name}: {data.get('total_items', 0)} items from {data.get('feeds_fetched', 0)} feeds")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", default="", help="Target specific region for campaign")
    parser.add_argument("--discover", action="store_true", help="Also run source discovery")
    parser.add_argument("--campaigns", action="store_true", help="Show past campaigns")
    args = parser.parse_args()

    if args.campaigns:
        show_campaigns()
        return 0

    if args.region:
        launch_campaign(args.region, 90, f"Manual campaign for {args.region}",
                        discover_sources=args.discover)
        return 0

    # Default: check and auto-launch
    launched = check_and_launch()
    print(f"\nLaunched {launched} collection campaign(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
