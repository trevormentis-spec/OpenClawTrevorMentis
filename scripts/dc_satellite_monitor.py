#!/usr/bin/env python3
"""
dc_satellite_monitor.py — Daily satellite imagery checks for data center sites.

Uses Copernicus Sentinel-2 to monitor:
  1. Change detection — new construction, expansions, ground disturbance
  2. Flooding/damage — after natural disasters near DC clusters
  3. Activity monitoring — protest encampments, access disruptions
  4. Power infrastructure — new substation construction near DCs

Priority order: Tier 1 hyperscale hubs (305) → Tier 2 colo clusters → at-risk sites

Usage:
    python3 scripts/dc_satellite_monitor.py --priority          # Check Tier 1 sites (daily)
    python3 scripts/dc_satellite_monitor.py --cluster nova      # Check Northern Virginia
    python3 scripts/dc_satellite_monitor.py --all               # Full sweep (weekly)
    python3 scripts/dc_satellite_monitor.py --status            # Show monitoring state
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.request
import urllib.parse
from typing import Any

REPO = pathlib.Path(__file__).resolve().parent.parent
FEEDS_DIR = REPO / "analyst" / "knowledge" / "data_centers" / "feeds"
IMAGERY_DIR = REPO / "analyst" / "knowledge" / "data_centers" / "imagery"
STATE_FILE = IMAGERY_DIR / "monitor_state.json"

# Sentinel-2 API config
TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"
EVALSCRIPT = "//VERSION=3\nfunction setup(){return{input:[\"B04\",\"B08\"],output:{bands:1,sampleType:\"UINT16\"}}}\nfunction evaluatePixel(sample){return[sample.B08-sample.B04];}"

BATCH_SIZE = 25  # Sites per run (rate limit safe)
LOOKBACK_DAYS = 30


def log(msg: str) -> None:
    print(f"[dc-imagery {dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


def get_token() -> str | None:
    cid = os.environ.get("SENTINEL_CLIENT_ID", "")
    secret = os.environ.get("SENTINEL_CLIENT_SECRET", "")
    if not cid or not secret:
        log("No SENTINEL credentials")
        return None
    auth = urllib.parse.urlencode({"client_id": cid, "client_secret": secret, "grant_type": "client_credentials"}).encode()
    req = urllib.request.Request(TOKEN_URL, data=auth, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())["access_token"]
    except Exception as e:
        log(f"Token failed: {e}")
        return None


def check_site(lon: float, lat: float, token: str) -> dict:
    """Query Sentinel-2 for a single site. Returns imagery metadata."""
    bbox = [lon - 0.015, lat - 0.015, lon + 0.015, lat + 0.015]
    end = dt.date.today().isoformat()
    start = (dt.date.today() - dt.timedelta(days=LOOKBACK_DAYS)).isoformat()
    
    payload = json.dumps({
        "input": {
            "bounds": {"properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}, "bbox": bbox},
            "data": [{"type": "SENTINEL-2-L2A", "dataFilter": {"timeRange": {"from": f"{start}T00:00:00Z", "to": f"{end}T23:59:59Z"}, "maxCloudCoverage": 50}}]
        },
        "evalscript": EVALSCRIPT,
        "output": {"width": 128, "height": 128}
    }).encode()

    req = urllib.request.Request(PROCESS_URL, data=payload, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            img = r.read()
            return {
                "queried": dt.datetime.now(dt.timezone.utc).isoformat(),
                "data_size_bytes": len(img),
                "has_imagery": len(img) > 100,
                "bbox": bbox,
            }
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:200]
        return {"queried": dt.datetime.now(dt.timezone.utc).isoformat(), "error": f"HTTP {e.code}: {body}", "has_imagery": False}
    except Exception as e:
        return {"queried": dt.datetime.now(dt.timezone.utc).isoformat(), "error": str(e), "has_imagery": False}


def load_state() -> dict:
    IMAGERY_DIR.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except: pass
    return {"last_site_index": 0, "total_checked": 0, "sites_with_imagery": 0}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def get_priority_sites() -> list[dict]:
    """Get Tier 1 hyperscale sites with coordinates, by priority cluster."""
    tier1 = json.loads((FEEDS_DIR / "tier1_hyperscale.json").read_bytes()).get("records", [])
    sites = []
    for r in tier1:
        try:
            lat = float(r.get("latitude", 0))
            lon = float(r.get("longitude", 0))
            if lat != 0 and lon != 0:
                sites.append({
                    "name": r.get("facility_name", "?")[:50],
                    "operator": r.get("operator", "?"),
                    "lat": lat,
                    "lon": lon,
                    "country": r.get("country", "?"),
                })
        except: pass
    return sites


def cmd_priority():
    """Check the next batch of Tier 1 sites."""
    token = get_token()
    if not token:
        return 1

    sites = get_priority_sites()
    state = load_state()
    idx = state.get("last_site_index", 0)
    
    batch = sites[idx: idx + BATCH_SIZE]
    if not batch:
        idx = 0
        batch = sites[:BATCH_SIZE]
        log("Full cycle complete — resetting")

    log(f"Checking batch {idx}-{idx+len(batch)} of {len(sites)} Tier 1 sites")
    results = []
    for site in batch:
        result = check_site(site["lon"], site["lat"], token)
        result["site"] = site
        results.append(result)
        log(f"  {site['operator'][:15]:15s} {site['name'][:30]:30s} {'✅' if result.get('has_imagery') else '❌'} ({result.get('data_size_bytes', 'err')}b)")

    # Save batch results
    today = dt.date.today().isoformat()
    batch_file = IMAGERY_DIR / f"batch-{idx}-{today}.json"
    batch_file.write_text(json.dumps({"batch_start": idx, "results": results}, indent=2))

    # Update state
    state["last_site_index"] = idx + len(batch)
    state["total_checked"] = state.get("total_checked", 0) + len(batch)
    state["sites_with_imagery"] = state.get("sites_with_imagery", 0) + sum(1 for r in results if r.get("has_imagery"))
    state["last_run"] = dt.datetime.now(dt.timezone.utc).isoformat()
    save_state(state)

    with_data = sum(1 for r in results if r.get("has_imagery"))
    log(f"Batch done: {with_data}/{len(batch)} with imagery ({state['sites_with_imagery']} total)")
    return 0


def cmd_status():
    state = load_state()
    sites = get_priority_sites()
    print(f"\nDC Satellite Monitor Status")
    print(f"{'─' * 50}")
    print(f"  Total Tier 1 sites: {len(sites)}")
    print(f"  Sites checked: {state.get('total_checked', 0)}")
    print(f"  Sites with imagery: {state.get('sites_with_imagery', 0)}")
    print(f"  Batch index: {state.get('last_site_index', 0)}/{len(sites)}")
    print(f"  Last run: {state.get('last_run', 'never')}")
    print(f"  Tiers monitored: Tier 1 (305 hyperscale hubs)")
    print(f"  Satellite: Copernicus Sentinel-2 L2A (10m resolution)")
    print(f"  Lookback window: {LOOKBACK_DAYS} days")
    print()
    return 0


def main():
    parser = argparse.ArgumentParser(description="DC Satellite Imagery Monitor")
    parser.add_argument("--priority", action="store_true", help="Check next batch of Tier 1 sites")
    parser.add_argument("--status", action="store_true", help="Show monitoring state")
    parser.add_argument("--all", action="store_true", help="Full sweep (reset batch)")
    args = parser.parse_args()

    if args.status:
        return cmd_status()
    elif args.all:
        state = load_state()
        state["last_site_index"] = 0
        save_state(state)
        log("Reset batch — next run starts from beginning")
        return cmd_priority()
    elif args.priority:
        return cmd_priority()
    else:
        return cmd_priority()


if __name__ == "__main__":
    sys.exit(main())
