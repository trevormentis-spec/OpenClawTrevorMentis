#!/usr/bin/env python3
"""
Exploration Scanner — Autonomous Background Exploration.

Periodically scans collection state for weak coverage regions and
independently initiates source discovery WITHOUT needing a critical
event trigger. This is "curiosity" — exploring because coverage is
thin, not because something went wrong.

Design:
- Runs on schedule (cron) or as background check
- No escalation needed — self-initiated exploration
- Checks: regions with <3 sources, persistent LOW quality, linguistic gaps
- Runs source discovery for each weak region
- Tracks exploration history to avoid re-exploring same regions daily
- Produces exploration report with discoveries

Usage:
    python3 scripts/exploration_scanner.py                    # Scan and explore
    python3 scripts/exploration_scanner.py --check-only       # Report gaps only
    python3 scripts/exploration_scanner.py --force region     # Force explore a region
    python3 scripts/exploration_scanner.py --report           # Past explorations
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import subprocess
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BEHAVIORAL_STATE_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "behavioral-state.json"
COLLECTION_STATE_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "collection-state.json"
SOURCES_FILE = REPO_ROOT / "analyst" / "meta" / "sources.json"
AUTONOMY_TRACKER_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "autonomy-tracker.json"
DISCOVERY_SCRIPT = REPO_ROOT / "scripts" / "source_discovery.py"
EXPLORATION_DIR = REPO_ROOT / "analysis" / "explorations"

# Don't re-explore a region more than once per N days
EXPLORATION_COOLDOWN_DAYS = 3

# Minimum sources needed before a region is considered "covered"
MIN_SOURCES_PER_REGION = 5


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[explore {ts}] {msg}", file=sys.stderr, flush=True)


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


def count_sources_per_region() -> dict[str, int]:
    """Count how many sources cover each region."""
    sources = load_json(SOURCES_FILE)
    counts = {
        "middle_east": 0, "europe": 0, "asia": 0,
        "north_america": 0, "south_central_america": 0,
        "global_finance": 0, "africa": 0,
    }
    
    # Keyword matching for region detection
    region_kw = {
        "middle_east": ["iran", "hormuz", "gulf", "iraq", "yemen", "israel", "lebanon",
                         "syria", "middle east", "arab", "persian", "hezbollah", "irgc"],
        "europe": ["ukraine", "russia", "eu", "nato", "europe", "britain", "germany",
                    "france", "uk ", "european", "moscow", "kyiv", "kremlin"],
        "asia": ["china", "taiwan", "japan", "korea", "india", "asia", "pacific",
                  "xinhua", "beijing", "tokyo", "delhi"],
        "africa": ["africa", "nigeria", "south africa", "kenya", "ethiopia",
                    "egypt", "libya", "sudan", "somali", "sahara"],
        "south_central_america": ["brazil", "venezuela", "argentina", "colombia",
                                   "latin", "south america", "mexico", "chile"],
    }
    
    for s in sources.get("durable_sources", []) + sources.get("local_language_sources", []):
        text = (s.get("name", "") + " " + s.get("focus", "") + " " +
                s.get("url", "")).lower()
        for region, kws in region_kw.items():
            if any(kw in text for kw in kws):
                counts[region] = counts.get(region, 0) + 1
                break
    
    return counts


def check_exploration_history(region: str) -> dict | None:
    """Check when this region was last explored. Returns None if never explored."""
    tracker = load_json(AUTONOMY_TRACKER_FILE)
    explorations = tracker.get("explorations", [])
    for e in reversed(explorations):
        if e.get("region") == region:
            return e
    return None


def identify_exploration_targets() -> list[dict]:
    """Identify regions that need exploration based on coverage gaps.

    No critical event needed — purely coverage-driven.
    """
    targets = []
    
    # 1. Source coverage per region
    source_counts = count_sources_per_region()
    log("Source coverage by region:")
    for region, count in sorted(source_counts.items(), key=lambda x: x[1]):
        status = "✅" if count >= MIN_SOURCES_PER_REGION else "⚠"
        log(f"  {status} {region}: {count} sources")
        if count < MIN_SOURCES_PER_REGION:
            # Check cooldown
            last = check_exploration_history(region)
            if last:
                try:
                    ts = dt.datetime.fromisoformat(last["timestamp"].replace("Z", "+00:00"))
                    days_since = (dt.datetime.now(dt.timezone.utc) - ts).days
                    if days_since < EXPLORATION_COOLDOWN_DAYS:
                        log(f"    → in cooldown ({EXPLORATION_COOLDOWN_DAYS - days_since}d remaining)")
                        continue
                except (ValueError, TypeError):
                    pass
            targets.append({
                "region": region,
                "current_sources": count,
                "gap": MIN_SOURCES_PER_REGION - count,
                "reason": f"only {count} sources (need {MIN_SOURCES_PER_REGION})",
            })

    # 2. Check behavioral state for quality gaps
    bs = load_json(BEHAVIORAL_STATE_FILE)
    if bs:
        coll = bs.get("collection_directives", {})
        for region_setting in coll.get("by_region", {}).items():
            region, info = region_setting
            quality = info.get("collection_quality_tier", "")
            if quality in ("CRITICAL GAP", "LOW"):
                # Only add if not already targeted from source count
                if not any(t["region"] == region for t in targets):
                    targets.append({
                        "region": region,
                        "current_sources": source_counts.get(region, 0),
                        "gap": "quality",
                        "reason": f"collection quality: {quality}",
                    })
        
        # 3. Check linguistic gaps from behavioral state
        for gap in coll.get("linguistic_gaps", []):
            region = gap.get("region", "")
            if region and not any(t["region"] == region for t in targets):
                targets.append({
                    "region": region,
                    "current_sources": source_counts.get(region, 0),
                    "gap": "linguistic",
                    "reason": f"linguistic gap: {', '.join(gap.get('gaps', []))}",
                })

    return targets


def explore_region(region: str, reason: str) -> dict:
    """Run source discovery for a region and track the exploration."""
    EXPLORATION_DIR.mkdir(parents=True, exist_ok=True)
    exploration_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    log(f"EXPLORING {region}: {reason}")

    # Run source discovery (no escalation trigger needed)
    discoveries = []
    if DISCOVERY_SCRIPT.exists():
        try:
            subprocess.check_call([
                "python3", str(DISCOVERY_SCRIPT),
                "--region", region,
                "--save",
            ], cwd=str(REPO_ROOT), timeout=90)
            log(f"  Discovery completed for {region}")
        except Exception as exc:
            log(f"  Discovery failed: {exc}")

    # Check what was discovered
    disc_dir = pathlib.Path(REPO_ROOT / "analysis" / "source-discoveries")
    if disc_dir.exists():
        for f in sorted(disc_dir.glob("*.json"), reverse=True):
            data = load_json(f)
            # Check if this discovery file covers our region
            disc_region = data.get("discoveries", [{}])[0].get("region", "") if data.get("discoveries") else ""
            if disc_region == region:
                discoveries = data.get("discoveries", [])
                break

    # Save exploration report
    report = {
        "exploration_id": exploration_id,
        "region": region,
        "reason": reason,
        "timestamp": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "discoveries": discoveries,
        "sources_found": len(discoveries),
    }
    report_path = EXPLORATION_DIR / f"{exploration_id}-{region}.json"
    save_json(report_path, report)

    # Track in autonomy metrics
    tracker = load_json(AUTONOMY_TRACKER_FILE) or {"version": 1, "explorations": []}
    tracker.setdefault("explorations", []).append({
        "exploration_id": exploration_id,
        "region": region,
        "reason": reason,
        "timestamp": report["timestamp"],
        "sources_found": len(discoveries),
    })
    save_json(AUTONOMY_TRACKER_FILE, tracker)

    log(f"  → {len(discoveries)} sources discovered, report: {report_path}")
    return report


def scan_and_explore() -> int:
    """Main scan — identify gaps and explore them (no escalation needed)."""
    targets = identify_exploration_targets()
    explored = 0

    if not targets:
        log("No regions need exploration — coverage adequate")
        return 0

    log(f"\nIdentified {len(targets)} regions needing exploration:\n")
    for t in targets:
        log(f"  ⚠ {t['region']}: {t['reason']}")

    for target in targets:
        explore_region(target["region"], target["reason"])
        explored += 1

    log(f"\nExploration complete: {explored} regions explored")
    return explored


def check_only() -> None:
    """Report gaps without exploring."""
    targets = identify_exploration_targets()
    source_counts = count_sources_per_region()

    print("# Exploration Scanner — Coverage Report")
    print(f"**Generated:** {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC")
    print()
    print("| Region | Sources | Min Needed | Status |")
    print("|--------|---------|------------|--------|")
    for region, count in sorted(source_counts.items(), key=lambda x: x[1]):
        status = "✅" if count >= MIN_SOURCES_PER_REGION else "⚠ GAP"
        icon = {"critical": "🔴", "significant": "🟡", "notable": "🟢"}
        print(f"| {region} | {count} | {MIN_SOURCES_PER_REGION} | {status} |")

    if targets:
        print()
        print("## Exploration Targets")
        for t in targets:
            print(f"- **{t['region']}**: {t['reason']}")
    else:
        print()
        print("No exploration targets — coverage adequate across all regions.")


def show_report() -> None:
    """Show past explorations."""
    tracker = load_json(AUTONOMY_TRACKER_FILE)
    explorations = tracker.get("explorations", [])
    if not explorations:
        print("No autonomous explorations have been run yet.")
        return
    print(f"# Autonomous Explorations ({len(explorations)} total)")
    print()
    for e in reversed(explorations):
        print(f"- {e['timestamp'][:19]}: **{e['region']}** — {e['sources_found']} sources found")
        print(f"  Reason: {e['reason']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="Report gaps only")
    parser.add_argument("--force", default="", help="Force explore a specific region")
    parser.add_argument("--report", action="store_true", help="Show past explorations")
    args = parser.parse_args()

    if args.report:
        show_report()
        return 0

    if args.check_only:
        check_only()
        return 0

    if args.force:
        explore_region(args.force, f"Manual exploration")
        return 0

    count = scan_and_explore()
    print(f"\nExplored {count} region(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
