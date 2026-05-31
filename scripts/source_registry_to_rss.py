#!/usr/bin/env python3
"""
Source Registry → RSS Converter

Reads all source registry markdown files (brain/memory/semantic/sources-*.md),
parses source names, cross-references them against the RSS feed catalog
(analyst/meta/sources_tested.json), and writes updated catalog with proper
region tags filled in.

Also produces analyst/meta/feed-inventory.md — a human-readable inventory.

Usage:
    python3 scripts/source_registry_to_rss.py
    python3 scripts/source_registry_to_rss.py --dry-run
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
from collections import defaultdict
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES_DIR = REPO_ROOT / "brain" / "memory" / "semantic"
CATALOG_PATH = REPO_ROOT / "analyst" / "meta" / "sources_tested.json"
INVENTORY_PATH = REPO_ROOT / "analyst" / "meta" / "feed-inventory.md"

# Map from registry filename pattern to unified region tag
FILENAME_REGION_MAP: dict[str, str] = {
    # Geographic regions — filename suffix after "sources-" (minus .md)
    "europe": "europe",
    "north_america": "north_america",
    "central_america_caribbean": "central_america_caribbean",
    "south_america": "south_america",
    "middle_east": "middle_east",
    "africa": "sub_saharan_africa",
    "russia_ukraine": "russia_ukraine",
    "south_east_asia": "southeast_asia",
    "east_asia": "east_asia",
    "south_asia": "south_asia",
    "oceania_pacific": "oceania_pacific",
    "central_asia_india": "central_asia_india",
    "china_asia": "china_asia",
    # Durable/theme sources
    "newly_added": None,  # mixed — skip auto-tagging
    "collection_methods": None,  # not sources
    "wire_feeds": None,  # mixed/general
    "prediction_markets_finance": "prediction_markets",
    "social_media_collection": None,  # not feeds
    "social_x_twitter": None,  # twitter handles, not RSS
    "telegram_channels": None,  # telegram, not RSS
    # Durable files mapped to their regions
    "durable_cyber_threat": "cyber_threat",
    "durable_maritime": "maritime",
    "durable_military_osint": "military_osint",
    "durable_israel_lebanon": "israel_lebanon",
    "durable_iran_specialist": "iran",
    "durable_substack_energy": "energy",
    "durable_thinktanks": "think_tanks",
    "durable_dashboards_realtime": "dashboards",
}


def extract_region_from_filename(filename: str) -> str | None:
    """Extract region from a sources-*.md filename."""
    stem = filename.replace(".md", "")
    if not stem.startswith("sources-"):
        return None
    key = stem[len("sources-"):]
    return FILENAME_REGION_MAP.get(key)


def parse_source_names(text: str) -> list[str]:
    """Extract source names from a source-registry markdown file.
    
    Format (actual):
        ## 2026-05-22
        Region sources (N feeds): Name1, Name2, Name3, ...
    
    Also handles:
        - (N+): instead of (N feeds):
        - Names with parenthetical descriptions
    """
    sources: list[str] = []

    for line in text.split("\n"):
        line = line.strip()
        # Skip headers, blank lines
        if not line or line.startswith("#"):
            continue
        # Look for lines containing source lists after a colon
        # Pattern: "description (N feeds): Name1, Name2, ..."
        if "):" in line or ":" in line:
            # Try to find the colon that separates description from source list
            colon_idx = line.find(":")
            if colon_idx > 0:
                after_colon = line[colon_idx + 1:].strip()
                # Split by comma and clean each name
                parts = [p.strip() for p in after_colon.split(",")]
                for part in parts:
                    # Skip empty parts, numbers, and parenthetical asides
                    part = part.strip()
                    if not part:
                        continue
                    # Remove leading/trailing parentheses and other noise
                    part = re.sub(r'^["\'(]|["\')]$', '', part)
                    part = part.strip()
                    if part and not part.startswith("(") and not part.startswith("["):
                        sources.append(part)
    
    # Deduplicate while preserving order
    seen = set()
    unique: list[str] = []
    for s in sources:
        s_lower = s.lower().strip()
        if s_lower not in seen:
            seen.add(s_lower)
            unique.append(s)
    return unique


def normalize_name(name: str) -> str:
    """Normalize a source name for fuzzy matching."""
    name = name.lower().strip()
    # Remove common organizational suffixes
    name = re.sub(r'\b(ltd|inc|corp|llc|gmbh|ag|sa|plc)\b\.?', '', name)
    # Remove parenthetical notes
    name = re.sub(r'\([^)]*\)', '', name)
    # Remove RSS / feeds markers
    name = re.sub(r'\b(rss|feeds?)\b', '', name)
    # Collapse whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def name_matches(catalog_name: str, source_name: str) -> bool:
    """Check if a catalog entry name matches a registry source name.
    
    Uses substring matching rather than exact equality since registry
    names are short ("Crisis Group") and catalog names are long
    ("RSS | International Crisis Group").
    """
    cat_lower = catalog_name.lower()
    src_lower = source_name.lower().strip()
    
    # Direct substring matches
    if src_lower in cat_lower or cat_lower in src_lower:
        return True
    
    # Token-based: check if all significant tokens from source_name appear in catalog_name
    src_tokens = set(re.findall(r'[a-z0-9]+', normalize_name(src_lower)))
    cat_tokens = set(re.findall(r'[a-z0-9]+', normalize_name(cat_lower)))
    
    if len(src_tokens) >= 2:
        # Source name tokens should mostly be in catalog tokens
        overlap = src_tokens & cat_tokens
        if len(overlap) >= min(2, len(src_tokens)):
            # Check overlap ratio
            if len(overlap) / len(src_tokens) >= 0.5:
                return True
    
    return False


def load_catalog() -> list[dict[str, Any]]:
    """Load the existing feed catalog."""
    if CATALOG_PATH.exists():
        try:
            data = json.loads(CATALOG_PATH.read_text())
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, Exception):
            pass
    return []


def save_catalog(catalog: list[dict[str, Any]]) -> None:
    """Save updated catalog."""
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False))
    print(f"✅ Catalog saved: {CATALOG_PATH} ({len(catalog)} entries)")


def write_inventory(source_regions: dict[str, list[str]],
                    region_stats: dict[str, int],
                    unmatched_sources: list[tuple[str, str]]) -> None:
    """Write human-readable inventory markdown."""
    lines = []
    lines.append("# Feed Inventory — Sources Registry Cross-Reference")
    lines.append(f"")
    lines.append(f"**Generated:** $(date -u)")
    lines.append(f"")
    lines.append(f"## Summary")
    lines.append(f"")
    total_names = sum(len(names) for names in source_regions.values())
    total_matched = sum(region_stats.get(r, 0) for r in region_stats)
    lines.append(f"- Source names parsed from registry: {total_names}")
    lines.append(f"- Catalog entries tagged with region: {total_matched}")
    lines.append(f"- Unmatched source names: {len(unmatched_sources)}")
    lines.append(f"")
    lines.append(f"## Region-by-Region")
    lines.append(f"")
    
    for region in sorted(source_regions.keys()):
        names = source_regions[region]
        matched = region_stats.get(region, "-")
        lines.append(f"### {region}")
        lines.append(f"")
        lines.append(f"Sources listed: {len(names)} | Catalog entries tagged: {matched}")
        lines.append(f"")
    
    if unmatched_sources:
        lines.append(f"")
        lines.append(f"## Unmatched Sources")
        lines.append(f"")
        lines.append(f"These source names from the registry could not be matched to any catalog entry:")
        lines.append(f"")
        lines.append(f"| Region | Source Name |")
        lines.append(f"|---|---|")
        for region, name in sorted(unmatched_sources):
            lines.append(f"| {region} | {name} |")
    
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"*Auto-generated by source_registry_to_rss.py*")
    
    INVENTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY_PATH.write_text("\n".join(lines))
    print(f"✅ Inventory written: {INVENTORY_PATH}")


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    
    print("=" * 60)
    print("  Source Registry → RSS Converter")
    print("=" * 60)
    
    # Step 1: Discover all source registry files
    registry_files = sorted(SOURCES_DIR.glob("sources-*.md"))
    print(f"\n📂 Found {len(registry_files)} source registry files")
    
    # Step 2: Parse each file
    source_regions: dict[str, list[str]] = {}  # region -> list of source names
    region_file_map: dict[str, str] = {}  # region -> filename
    
    for f in registry_files:
        region = extract_region_from_filename(f.name)
        if region is None:
            print(f"  ⏭️  Skipping {f.name} (no region mapping)")
            continue
        
        text = f.read_text(encoding="utf-8", errors="replace")
        names = parse_source_names(text)
        if names:
            source_regions[region] = source_regions.get(region, []) + names
            region_file_map[region] = f.name
            print(f"  📄 {f.name}: {len(names)} names → region '{region}'")
        else:
            print(f"  ⚠️  {f.name}: parsed 0 source names")
    
    # Step 3: Load existing catalog
    catalog = load_catalog()
    print(f"\n📋 Existing catalog: {len(catalog)} entries (all region='')")
    
    # Step 4: Cross-reference and tag
    tagged_count = 0
    unmatched_sources: list[tuple[str, str]] = []
    region_stats: dict[str, int] = defaultdict(int)
    
    for region, names in source_regions.items():
        for source_name in names:
            matched = False
            for entry in catalog:
                # Skip if already has a region tag
                if entry.get("region"):
                    continue
                if name_matches(entry.get("name", ""), source_name):
                    entry["region"] = region
                    tagged_count += 1
                    region_stats[region] += 1
                    matched = True
                    break
            
            if not matched:
                unmatched_sources.append((region, source_name))
    
    print(f"\n📊 Tagging results:")
    print(f"   Tagged {tagged_count} catalog entries with region info")
    print(f"   Unmatched source names: {len(unmatched_sources)}")
    
    # Step 5: Also run a URL-based pass — check if catalog URL contains region keywords
    url_region_keywords: dict[str, str] = {
        "europe": "europe",
        "european": "europe",
        "north america": "north_america", 
        "central america": "central_america_caribbean",
        "caribbean": "central_america_caribbean",
        "south america": "south_america",
        "middle east": "middle_east",
        "africa": "sub_saharan_africa",
        "russia": "russia_ukraine",
        "ukraine": "russia_ukraine",
        "southeast asia": "southeast_asia",
        "east asia": "east_asia",
        "south asia": "south_asia",
        "oceania": "oceania_pacific",
        "pacific": "oceania_pacific",
        "central asia": "central_asia_india",
        "india": "central_asia_india",
        "china": "china_asia",
    }
    
    url_tagged = 0
    for entry in catalog:
        if entry.get("region"):
            continue  # already tagged
        url = entry.get("url", "").lower()
        for keyword, region in url_region_keywords.items():
            if keyword in url:
                entry["region"] = region
                url_tagged += 1
                break
    
    print(f"   URL-based tags: {url_tagged} catalog entries")
    
    # Step 6: Save if not dry run
    if dry_run:
        print("\n🔍 DRY RUN — no files modified")
        return 0
    
    save_catalog(catalog)
    write_inventory(source_regions, dict(region_stats), unmatched_sources)
    
    # Summary
    total_tagged = sum(1 for e in catalog if e.get("region"))
    total_untagged = sum(1 for e in catalog if not e.get("region"))
    print(f"\n✅ Done! Catalog: {total_tagged} tagged, {total_untagged} untagged of {len(catalog)} total")
    print(f"   Inventory: {INVENTORY_PATH}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
