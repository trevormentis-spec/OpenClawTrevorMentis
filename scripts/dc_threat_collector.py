#!/usr/bin/env python3
"""
dc_threat_collector.py — Data Center Security Threat Monitoring.

Collects real-time threat data from multiple sources:
  • Subsea cable news (TeleGeography, Submarine Networks)
  • Power grid (ISO/RTO news, EIA)
  • Cloud status pages (AWS, Azure, GCP)
  • Natural hazard feeds (USGS earthquakes, NOAA hurricanes)
  • Physical security (DC breach news, protest monitoring)
  • Fiber route disruptions

Saves structured threat intel for the daily brief.

Usage:
    python3 scripts/dc_threat_collector.py --all          # Full collection
    python3 scripts/dc_threat_collector.py --cables        # Cable news only
    python3 scripts/dc_threat_collector.py --grid           # Power grid only
    python3 scripts/dc_threat_collector.py --cloud          # Cloud status only
    python3 scripts/dc_threat_collector.py --hazards        # Natural hazards only
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import ssl
import sys
import urllib.request
from xml.etree import ElementTree as ET
from typing import Any

REPO = pathlib.Path(__file__).resolve().parent.parent
THREAT_DIR = REPO / "analyst" / "knowledge" / "data_centers" / "threats"
THREAT_DIR.mkdir(parents=True, exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def log(msg: str) -> None:
    print(f"[dc-threat {dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)
def update_cognition_with_threats(results: dict) -> None:
    """Wire DC threat findings into Philby cognition state for I&W alerting."""
    cog_path = REPO / "skills" / "continuous-cognition" / "state" / "cognition_state.json"
    if not cog_path.exists():
        return
    
    try:
        state = json.loads(cog_path.read_bytes())
    except:
        return
    
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    updates = 0
    
    # Check for cable disruptions
    disruptions = results.get("cables", {}).get("disruptions", [])
    if disruptions:
        narrative = state.get("active_narratives", {}).get("dc_subsea_cable_resilience", {})
        if narrative:
            narrative["last_updated"] = now
            narrative["cycle_updated"] = state.get("cycle", 0)
            for d in disruptions[:2]:
                narrative.setdefault("evidence", {}).setdefault("for", []).append({"source": d.get("source", "RSS"), "detail": d.get("title", "")[:100]})
            # Confidence swing detection (I&W will catch this)
            if narrative["confidence"] < 60:
                narrative["confidence"] = min(65, narrative["confidence"] + 5)
            updates += 1
    
    # Check for grid threats
    grid_relevant = results.get("grid", {}).get("grid_relevant", [])
    if grid_relevant:
        narrative = state.get("active_narratives", {}).get("dc_ashburn_grid_strain", {})
        if narrative:
            narrative["last_updated"] = now
            narrative["cycle_updated"] = state.get("cycle", 0)
            for g in grid_relevant[:2]:
                narrative.setdefault("evidence", {}).setdefault("for", []).append({"source": g.get("source", "RSS"), "detail": g.get("title", "")[:100]})
            updates += 1
    
    # Check for hazards near DC clusters
    threatened = results.get("hazards", {}).get("hazards", {}).get("dc_clusters_threatened", [])
    if threatened:
        narrative = state.get("active_narratives", {}).get("dc_hurricane_season_preparedness", {})
        if narrative:
            narrative["last_updated"] = now
            narrative["cycle_updated"] = state.get("cycle", 0)
            narrative["evidence"].setdefault("for", []).append({"source": "USGS/NOAA", "detail": f"Hazard detected: {threatened[0]["threat"]}"})
            if narrative["confidence"] < 60:
                narrative["confidence"] = min(65, narrative["confidence"] + 5)
            updates += 1
    
    if updates > 0:
        cog_path.write_text(json.dumps(state, indent=2))
        log(f"Updated {updates} DC narratives in cognition state (I&W will evaluate)")




def fetch_rss(url: str, timeout: int = 15) -> list[dict]:
    """Fetch and parse an RSS feed."""
    entries = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; TrevorDC/1.0)"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            raw = r.read()
            root = ET.fromstring(raw)
            for item in root.iter("item"):
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                desc = item.findtext("description", "")[:300]
                pub_date = item.findtext("pubDate", "")
                entries.append({
                    "title": title.strip(),
                    "url": link.strip(),
                    "description": desc.strip(),
                    "published": pub_date.strip(),
                })
        log(f"RSS {url}: {len(entries)} entries")
    except Exception as e:
        log(f"RSS fetch failed {url}: {e}")
    return entries


# ── 1. SUbSEA CABLE NEWS ──────────────────────────────────────────

CABLE_FEEDS = [
    ("SubTel Forum", "https://subtelforum.com/feed/"),
    ("Fierce Network", "https://www.fierce-network.com/feed"),
    ("Light Reading", "https://www.lightreading.com/rss.xml"),
]

def collect_cable_threats() -> dict:
    """Collect subsea cable news and detect disruption signals."""
    entries = []
    for name, url in CABLE_FEEDS:
        for e in fetch_rss(url):
            e["source"] = name
            entries.append(e)

    # Detect cable disruption keywords
    disruption_keywords = ["cut", "outage", "repair", "damage", "disruption", "fault", "break"]
    disruptions = [
        e for e in entries
        if any(kw in e.get("title", "").lower() for kw in disruption_keywords)
    ]

    result = {
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
        "total_entries": len(entries),
        "disruptions": disruptions[:5],
        "recent_headlines": [e["title"] for e in entries[:8]],
    }
    (THREAT_DIR / "cable_threats.json").write_text(json.dumps(result, indent=2))
    log(f"Cable threats: {len(entries)} entries, {len(disruptions)} disruptions")
    return result


# ── 2. POWER GRID NEWS ────────────────────────────────────────────

POWER_FEEDS = [
    ("EIA Today", "https://www.eia.gov/rss/todayinenergy.xml"),
    ("Utility Dive", "https://www.utilitydive.com/feeds/news/"),
    ("Renewable Energy World", "https://www.renewableenergyworld.com/feed/"),
    ("Smart Grid Observer", "https://www.smartgridobserver.com/rss.xml"),
]

def collect_grid_threats() -> dict:
    """Collect power grid news and constraint signals."""
    entries = []
    for name, url in POWER_FEEDS:
        for e in fetch_rss(url):
            e["source"] = name
            entries.append(e)

    grid_keywords = ["grid", "power", "energy", "electricity", "interconnection", "capacity", "transmission", "constraint"]
    grid_relevant = [
        e for e in entries
        if any(kw in e.get("title", "").lower() for kw in grid_keywords)
    ]

    result = {
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
        "total_entries": len(entries),
        "grid_relevant": grid_relevant[:8],
        "recent_headlines": [e["title"] for e in grid_relevant[:8]],
    }
    (THREAT_DIR / "grid_threats.json").write_text(json.dumps(result, indent=2))
    log(f"Grid threats: {len(grid_relevant)} relevant from {len(entries)} entries")
    return result


# ── 3. CLOUD STATUS ───────────────────────────────────────────────

CLOUD_STATUS_FEEDS = {
    "AWS": "https://health.aws.amazon.com/rss/status.rss",
    "GCP": "https://status.cloud.google.com/feed.rss",
}

def collect_cloud_threats() -> dict:
    """Check cloud provider status pages for active incidents."""
    results = {}
    for provider, url in CLOUD_STATUS_FEEDS.items():
        entries = fetch_rss(url, timeout=10)
        active_issues = [
            e for e in entries
            if any(kw in (e.get("title", "") + e.get("description", "")).lower()
                   for kw in ["outage", "degraded", "elevated", "incident", "disruption", "down"])
        ]
        results[provider] = {
            "total_entries": len(entries),
            "active_issues": active_issues[:3],
            "status": "issues_detected" if active_issues else "all_clear",
        }

    out = {
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
        "providers": results,
    }
    (THREAT_DIR / "cloud_threats.json").write_text(json.dumps(out, indent=2))
    statuses = [f"{p}: {d['status']}" for p, d in results.items()]
    log(f"Cloud status: {', '.join(statuses)}")
    return out


# ── 4. NATURAL HAZARDS ────────────────────────────────────────────

HAZARD_FEEDS = {
    "USGS Earthquakes": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.atom",
    "NOAA Hurricanes": "https://www.nhc.noaa.gov/rss/latest_atom.xml",
}

# Major DC clusters with coordinates
DC_CLUSTERS = {
    "northern_virginia": {"name": "Northern Virginia", "lat": 39.0, "lon": -77.5, "radius_deg": 1.0},
    "dallas": {"name": "Dallas/Fort Worth", "lat": 32.8, "lon": -96.8, "radius_deg": 1.0},
    "silicon_valley": {"name": "Silicon Valley", "lat": 37.3, "lon": -121.9, "radius_deg": 0.8},
    "frankfurt": {"name": "Frankfurt", "lat": 50.1, "lon": 8.7, "radius_deg": 0.5},
    "london": {"name": "London", "lat": 51.5, "lon": -0.1, "radius_deg": 0.5},
    "singapore": {"name": "Singapore", "lat": 1.35, "lon": 103.8, "radius_deg": 0.5},
    "sydney": {"name": "Sydney", "lat": -33.9, "lon": 151.2, "radius_deg": 0.8},
    "tokyo": {"name": "Tokyo", "lat": 35.7, "lon": 139.7, "radius_deg": 0.8},
    "amsterdam": {"name": "Amsterdam", "lat": 52.4, "lon": 4.9, "radius_deg": 0.5},
    "sao_paulo": {"name": "São Paulo", "lat": -23.5, "lon": -46.6, "radius_deg": 0.8},
}

def collect_hazard_threats() -> dict:
    """Collect natural hazard data (earthquakes, storms) near DC clusters."""
    hazards = {"earthquakes": [], "hurricanes": [], "dc_clusters_threatened": []}

    # Earthquakes
    try:
        req = urllib.request.Request(
            "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson",
            headers={"User-Agent": "TrevorDC/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            eq_data = json.loads(r.read())
        for feat in eq_data.get("features", []):
            props = feat.get("properties", {})
            coords = feat.get("geometry", {}).get("coordinates", [0, 0])
            mag = props.get("mag", 0)
            place = props.get("place", "?")
            time_ms = props.get("time", 0)
            eq = {
                "magnitude": mag,
                "place": place,
                "time": dt.datetime.fromtimestamp(time_ms / 1000, tz=dt.timezone.utc).isoformat() if time_ms else "?",
                "lat": coords[1],
                "lon": coords[0],
            }
            hazards["earthquakes"].append(eq)

            # Check proximity to DC clusters
            for cid, cluster in DC_CLUSTERS.items():
                lat_diff = abs(coords[1] - cluster["lat"])
                lon_diff = abs(coords[0] - cluster["lon"])
                if lat_diff < cluster["radius_deg"] and lon_diff < cluster["radius_deg"]:
                    hazards["dc_clusters_threatened"].append({
                        "cluster": cluster["name"],
                        "threat": f"M{eq['magnitude']} earthquake near {place}",
                        "distance_deg": round(max(lat_diff, lon_diff), 2),
                    })
        log(f"Earthquakes: {len(hazards['earthquakes'])} events near {len(hazards['dc_clusters_threatened'])} clusters")
    except Exception as e:
        log(f"Earthquake fetch failed: {e}")

    # Hurricanes (NHC Atlantic)
    try:
        req = urllib.request.Request(
            "https://www.nhc.noaa.gov/rss/latest_atom.xml",
            headers={"User-Agent": "TrevorDC/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read().decode(errors="replace")
        # Parse simple Atom
        titles = re.findall(r"<title[^>]*>([^<]+)</title>", raw)[:5]
        hazards["hurricanes"] = [t for t in titles if "tropical" in t.lower() or "hurricane" in t.lower() or "storm" in t.lower()]
        log(f"Hurricane/storm alerts: {len(hazards['hurricanes'])}")
    except Exception as e:
        log(f"Hurricane fetch failed: {e}")

    out = {
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
        "hazards": hazards,
    }
    (THREAT_DIR / "hazard_threats.json").write_text(json.dumps(out, indent=2))
    return out


# ── 5. PHYSICAL SECURITY ──────────────────────────────────────────

PHYSICAL_FEEDS = [
    ("Data Center Dynamics", "https://www.datacenterdynamics.com/en/feed/rss/"),
    ("Capacity Media", "https://www.capacitymedia.com/rss.xml"),
]

def collect_physical_threats() -> dict:
    """Collect physical security incidents near DCs."""
    entries = []
    for name, url in PHYSICAL_FEEDS:
        for e in fetch_rss(url):
            e["source"] = name
            entries.append(e)

    dc_keywords = ["data center", "datacenter", "colo", "server", "fiber", "cable cut", "breach", "protest"]
    relevant = [
        e for e in entries
        if any(kw in (e.get("title", "") + e.get("description", "")).lower() for kw in dc_keywords)
    ]

    result = {
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
        "total_entries": len(entries),
        "dc_relevant": relevant[:8],
    }
    (THREAT_DIR / "physical_threats.json").write_text(json.dumps(result, indent=2))
    log(f"Physical security: {len(relevant)} DC-relevant from {len(entries)} entries")
    return result


# ── MAIN ──────────────────────────────────────────────────────────

def cmd_all():
    results = {}
    results["cables"] = collect_cable_threats()
    results["grid"] = collect_grid_threats()
    results["cloud"] = collect_cloud_threats()
    results["hazards"] = collect_hazard_threats()
    results["physical"] = collect_physical_threats()
    results["generated"] = dt.datetime.now(dt.timezone.utc).isoformat()

    (THREAT_DIR / "threat_summary.json").write_text(json.dumps(results, indent=2))
    update_cognition_with_threats(results)
    log(f"Full threat collection complete: cables={results['cables']['total_entries']}, "
         f"grid={results['grid']['total_entries']}, "
         f"hazards={len(results['hazards']['hazards']['earthquakes'])} quakes, "
         f"physical={results['physical']['total_entries']} entries")
    print("Full threat collection complete")
    return 0


def main():
    parser = argparse.ArgumentParser(description="DC Security Threat Collector")
    parser.add_argument("--all", action="store_true", help="Full collection")
    parser.add_argument("--cables", action="store_true", help="Cable news only")
    parser.add_argument("--grid", action="store_true", help="Power grid only")
    parser.add_argument("--cloud", action="store_true", help="Cloud status only")
    parser.add_argument("--hazards", action="store_true", help="Natural hazards only")
    args = parser.parse_args()

    if args.all:
        return cmd_all()
    if args.cables:
        collect_cable_threats()
    elif args.grid:
        collect_grid_threats()
    elif args.cloud:
        collect_cloud_threats()
    elif args.hazards:
        collect_hazard_threats()
    else:
        cmd_all()
    return 0


if __name__ == "__main__":
    sys.exit(main())
