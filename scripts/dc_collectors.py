#!/usr/bin/env python3
"""
Data Center Security Daily — Collector & Registry.

Reads the global data center census and produces a structured registry
for the daily brief. Also collects external threat data.

Usage:
    python3 scripts/dc_collectors.py --registry              # Rebuild registry from census
    python3 scripts/dc_collectors.py --cable-news            # Check subsea cable news
    python3 scripts/dc_collectors.py --power-news            # Check power grid news
    python3 scripts/dc_collectors.py --status-pages          # Check cloud status pages
    python3 scripts/dc_collectors.py --all                   # Full collection cycle
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
import ssl
from typing import Any

REPO = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = REPO / "analyst" / "knowledge" / "data_centers"
FEEDS_DIR = DATA_DIR / "feeds"
ANALYSIS_DIR = DATA_DIR / "analysis"
REGISTRY_FILE = DATA_DIR / "registry.json"

# Power grid monitoring — key ISOs with heavy DC concentration
POWER_ISOS = {
    "PJM": "https://www.pjm.com/rss/",         # Northern Virginia
    "ERCOT": "https://www.ercot.com/rss/",      # Texas
    "CAISO": "https://www.caiso.com/rss/",      # California
    "NYISO": "https://www.nyiso.com/rss/",      # New York
    "ISO-NE": "https://www.iso-ne.com/rss/",    # New England
}

# Cloud status page URLs
CLOUD_STATUS = {
    "AWS": "https://health.aws.amazon.com/",
    "Azure": "https://azure.status.microsoft/",
    "GCP": "https://status.cloud.google.com/",
}

# Subsea cable news RSS
CABLE_NEWS_FEEDS = [
    ("TeleGeography", "https://blog.telegeography.com/feed"),
    ("Submarine Cable Networks", "https://www.submarinenetworks.com/feed"),
]


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[dc-collect {ts}] {msg}", file=sys.stderr, flush=True)


def load_feed(name: str) -> list[dict]:
    p = FEEDS_DIR / f"{name}.json"
    if p.exists():
        return json.loads(p.read_bytes()).get("records", [])
    return []


def build_registry() -> dict:
    """Build the master DC registry from all census tiers."""
    t1 = load_feed("tier1_hyperscale")
    t2 = load_feed("tier2_colocation")
    t3 = load_feed("tier3_census")
    cables = load_feed("subsea_cables")
    landings = load_feed("subsea_landings")
    fiber = load_feed("terrestrial_fiber")
    ixs = load_feed("internet_exchanges")

    # Build geo-indexed clusters for threat analysis
    by_country = {}
    for dc in t1 + t2 + t3:
        country = dc.get("country", dc.get("country", "?")).upper()
        by_country.setdefault(country, []).append(dc)

    # Power capacity analysis (Tier 1 only — has power_mw field)
    total_power = 0
    power_by_country = {}
    for dc in t1:
        p = dc.get("power_mw", "0")
        try:
            mw = float(str(p).replace("N/A", "0").replace(",", ""))
        except:
            mw = 0
        total_power += mw
        c = dc.get("country", "?").upper()
        power_by_country[c] = power_by_country.get(c, 0) + mw

    # Subsea cable landing analysis
    cables_by_dc_region = {}
    for landing in landings:
        nearby = landing.get("nearby_datacenters", "")
        if nearby and nearby != "N/A":
            region = landing.get("country", "?")
            cables_by_dc_region.setdefault(region, []).append({
                "station": landing.get("landing_station_name", "?"),
                "city": landing.get("city", "?"),
                "cables": landing.get("cables_terminating", ""),
            })

    # IX density
    ixs_by_country = {}
    for ix in ixs:
        c = ix.get("country", "?").upper()
        ixs_by_country[c] = ixs_by_country.get(c, 0) + 1

    registry = {
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
        "totals": {
            "hyperscale_hubs": len(t1),
            "colocation_facilities": len(t2),
            "global_census_total": len(t3),
            "subsea_cables": len(cables),
            "subsea_landing_stations": len(landings),
            "terrestrial_fiber_routes": len(fiber),
            "internet_exchanges": len(ixs),
        },
        "geography": {
            "dc_by_country": {k: len(v) for k, v in sorted(by_country.items(), key=lambda x: -len(x[1]))[:30]},
            "total_power_mw": total_power,
            "power_by_country": {k: int(v) for k, v in sorted(power_by_country.items(), key=lambda x: -x[1])[:15]},
        },
        "connectivity": {
            "ix_by_country": {k: v for k, v in sorted(ixs_by_country.items(), key=lambda x: -x[1])[:15]},
        },
        "top_operators": {},
    }

    # Top operators
    op_count = {}
    for dc in t1:
        op = dc.get("operator", dc.get("parent_company", "?"))
        op_count[op] = op_count.get(op, 0) + 1
    registry["top_operators"] = {k: v for k, v in sorted(op_count.items(), key=lambda x: -x[1])[:10]}

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(registry, indent=2))
    log(f"Registry built: {len(t1)+len(t2)+len(t3)} DCs, {len(cables)} cables, {len(ixs)} IXes")
    return registry


def collect_cable_news() -> list[dict]:
    """Fetch recent subsea cable news."""
    results = []
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    for name, url in CABLE_NEWS_FEEDS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
                content = r.read().decode(errors="replace")
                log(f"Fetched {name}: {len(content)} bytes")
                results.append({"source": name, "content_preview": content[:500]})
        except Exception as e:
            log(f"Cable news fetch failed for {name}: {e}")
    return results


def analyze_registry() -> dict:
    """Produce analytical output about DC security posture."""
    registry = json.loads(REGISTRY_FILE.read_bytes()) if REGISTRY_FILE.exists() else build_registry()
    
    # Identify high-risk clusters
    # Northern Virginia (PJM grid strain, fiber concentration)
    # Singapore (power constraints, political risk)
    # Silicon Valley (earthquake, power)
    # Frankfurt (power, geo-risk)
    
    analysis = {
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
        "registry": registry,
    }
    return analysis


def cmd_registry(args):
    registry = build_registry()
    print(f"Built registry: {registry['totals']['global_census_total']:,} total facilities")
    print(f"  Hyperscale: {registry['totals']['hyperscale_hubs']}")
    print(f"  Colocation: {registry['totals']['colocation_facilities']}")
    print(f"  Subsea cables: {registry['totals']['subsea_cables']}")
    print(f"  Internet exchanges: {registry['totals']['internet_exchanges']}")
    print(f"\nTop 5 countries (total DCs):")
    for c, n in list(registry.get("geography", {}).get("dc_by_country", {}).items())[:5]:
        print(f"  {c}: {n}")
    return 0


def cmd_all(args):
    build_registry()
    cable_news = collect_cable_news()
    log(f"Cable news: {len(cable_news)} sources fetched")
    # Save collection output
    collection = {
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
        "cable_news": cable_news,
    }
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    (ANALYSIS_DIR / "collection.json").write_text(json.dumps(collection, indent=2))
    print("Full collection cycle complete")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Data Center Security Collectors")
    parser.add_argument("--registry", action="store_true", help="Rebuild DC registry from census")
    parser.add_argument("--cable-news", action="store_true", help="Check subsea cable news")
    parser.add_argument("--all", action="store_true", help="Full collection cycle")
    args = parser.parse_args()

    if args.registry:
        return cmd_registry(args)
    elif args.all:
        return cmd_all(args)
    else:
        return cmd_registry(args)


if __name__ == "__main__":
    sys.exit(main())
