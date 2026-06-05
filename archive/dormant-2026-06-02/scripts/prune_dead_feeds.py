#!/usr/bin/env python3
"""
Prune Dead Feeds — removes stale 403/forbidden entries from the feed catalog.

Removes catalog entries with status="forbidden" or code=403 that were tested
>7 days ago. Moves pruned entries to analyst/meta/dead-feeds-graveyard.json
(append-only, timestamped).

Usage:
    python3 scripts/prune_dead_feeds.py
    python3 scripts/prune_dead_feeds.py --days 14
    python3 scripts/prune_dead_feeds.py --dry-run
    python3 scripts/prune_dead_feeds.py --force  # Skip safety confirmation
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "analyst" / "meta" / "sources_tested.json"
GRAVEYARD_PATH = REPO_ROOT / "analyst" / "meta" / "dead-feeds-graveyard.json"

# Cutoff: anything tested more than this many days ago is eligible for removal
DEFAULT_CUTOFF_DAYS = 7


def load_json(path: pathlib.Path) -> list[dict[str, Any]]:
    """Load a JSON file, returning empty list on failure."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, Exception):
        return []


def save_json(path: pathlib.Path, data: list[dict[str, Any]]) -> None:
    """Save a JSON file, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def should_prune(entry: dict[str, Any], cutoff_days: int) -> bool:
    """Check if a catalog entry should be pruned.
    
    Prune if:
    - status is "forbidden" OR code is 403
    - tested_at is set and more than cutoff_days old
    """
    status = entry.get("status", "")
    code = entry.get("code", 0)
    
    # Must be a 403/forbidden feed
    if status != "forbidden" and code != 403:
        return False
    
    # Check tested_at date
    tested_str = entry.get("tested_at", "")
    if not tested_str:
        return False  # Can't determine age — keep it
    
    try:
        tested_dt = dt.datetime.fromisoformat(tested_str)
        # Strip timezone info for comparison (use UTC)
        now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
        if tested_dt.tzinfo is not None:
            tested_dt = tested_dt.replace(tzinfo=None)
        delta = now - tested_dt
        return delta.days >= cutoff_days
    except (ValueError, TypeError):
        return False  # Can't parse date — keep it


def main() -> int:
    # Parse args
    cutoff_days = DEFAULT_CUTOFF_DAYS
    dry_run = False
    force = False
    
    for arg in sys.argv[1:]:
        if arg == "--dry-run":
            dry_run = True
        elif arg == "--force":
            force = True
        elif arg.startswith("--days="):
            try:
                cutoff_days = int(arg.split("=", 1)[1])
            except ValueError:
                print(f"ERROR: Invalid --days value: {arg}")
                return 1
        elif arg == "--days" and len(sys.argv) > sys.argv.index(arg) + 1:
            idx = sys.argv.index(arg)
            try:
                cutoff_days = int(sys.argv[idx + 1])
            except ValueError:
                print(f"ERROR: Invalid --days value: {sys.argv[idx + 1]}")
                return 1
    
    print("=" * 60)
    print(f"  Prune Dead Feeds — cutoff: {cutoff_days} days")
    print("=" * 60)
    
    if dry_run:
        print("  DRY RUN — no files will be modified\n")
    
    # Load catalog
    catalog = load_json(CATALOG_PATH)
    if not catalog:
        print("ERROR: Empty or unreadable catalog")
        return 1
    
    print(f"\n📋 Catalog: {len(catalog)} entries")
    
    # Find prunable entries
    prunable: list[dict[str, Any]] = []
    remaining: list[dict[str, Any]] = []
    
    for entry in catalog:
        if should_prune(entry, cutoff_days):
            prunable.append(entry)
        else:
            remaining.append(entry)
    
    print(f"   Prunable (403/forbidden, >{cutoff_days}d old): {len(prunable)}")
    
    if not prunable:
        print("\n✅ No dead feeds to prune — catalog is clean")
        return 0
    
    # Show summary
    print(f"\n📊 Summary:")
    print(f"   Removed:    {len(prunable)} dead feeds")
    print(f"   Remaining:  {len(remaining)} feeds")
    
    # Show sample of pruned entries
    print(f"\n🔍 Pruned entries (first 5):")
    for entry in prunable[:5]:
        name = entry.get("name", "?")
        url = entry.get("url", "?")
        tested = entry.get("tested_at", "?")
        print(f"   - {name}")
        print(f"     {url}")
        print(f"     tested: {tested}")
    
    if dry_run:
        print("\n🔍 DRY RUN — no files modified")
        return 0
    
    # Confirm unless force
    if not force:
        print(f"\n⚠️  This will REMOVE {len(prunable)} entries from the catalog.")
        print(f"   Pruned entries will be MOVED to {GRAVEYARD_PATH.name}")
        try:
            confirm = input("   Proceed? (y/N): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            confirm = "n"
        if confirm != "y":
            print("   Aborted.")
            return 1
    
    # Add timestamp to each pruned entry and move to graveyard
    now_iso = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for entry in prunable:
        entry["_pruned_at"] = now_iso
        entry["_prune_reason"] = f"403_forbidden_gt{cutoff_days}d"
    
    graveyard = load_json(GRAVEYARD_PATH)
    graveyard.extend(prunable)
    save_json(GRAVEYARD_PATH, graveyard)
    print(f"\n📦 Graveyard: {len(graveyard)} total entries ({GRAVEYARD_PATH})")
    
    # Save updated catalog
    save_json(CATALOG_PATH, remaining)
    
    print(f"\n✅ Complete!")
    print(f"   Removed {len(prunable)} dead feeds, {len(remaining)} remaining")
    print(f"   Graveyard: {GRAVEYARD_PATH}")
    print(f"   Catalog:   {CATALOG_PATH}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
