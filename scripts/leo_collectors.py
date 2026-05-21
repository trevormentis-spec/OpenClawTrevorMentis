#!/usr/bin/env python3
"""
LEO Ground Station Market Data Collectors — Tier 1 Feeds.

Wires in FCC earth station licenses, ITU coordination filings,
launch schedules, job postings, and Sentinel-2 imagery checks
for the LEO Ground Stations topic.

Usage:
    python3 scripts/leo_collectors.py --fcc-daily        # FCC new filings check
    python3 scripts/leo_collectors.py --launch-daily      # Launch schedule check
    python3 scripts/leo_collectors.py --itu-weekly        # ITU coordination check
    python3 scripts/leo_collectors.py --jobs-weekly       # Job posting scan
    python3 scripts/leo_collectors.py --imagery-monthly   # Sentinel-2 site check
    python3 scripts/leo_collectors.py --all-daily         # Run all daily tasks
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LEO_DATA_DIR = REPO_ROOT / "analyst" / "knowledge" / "leo_ground_stations" / "data_feeds"
LEO_SITES_FILE = REPO_ROOT / "config" / "topics" / "leo_ground_stations" / "_principal_data" / "global_risk_register_risk_register.json"

# 80-site register for reference
SITES_80 = None


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[leo-collect {ts}] {msg}", file=sys.stderr, flush=True)


def load_sites_80() -> list[dict]:
    global SITES_80
    if SITES_80 is None and LEO_SITES_FILE.exists():
        try:
            SITES_80 = json.loads(LEO_SITES_FILE.read_text())
        except Exception:
            SITES_80 = []
    return SITES_80 or []


def save_output(name: str, data: dict) -> None:
    """Save collector output to the LEO data feeds directory."""
    LEO_DATA_DIR.mkdir(parents=True, exist_ok=True)
    date_slug = dt.date.today().isoformat()
    path = LEO_DATA_DIR / f"{name}-{date_slug}.json"
    path.write_text(json.dumps(data, indent=2, default=str))
    log(f"Saved: {path} ({len(json.dumps(data))} bytes)")


def load_previous(name: str) -> dict | None:
    """Load the most recent previous output for comparison."""
    pattern = f"{name}-*.json"
    files = sorted(LEO_DATA_DIR.glob(pattern), reverse=True)
    if len(files) >= 2:
        try:
            return json.loads(files[1].read_text())  # second-most-recent
        except Exception:
            pass
    return None


# =========================================================================
# COLLECTOR 1: FCC Earth Station Licenses (Daily)
# =========================================================================

def collect_fcc_daily() -> dict:
    """Fetch recent FCC earth station license filings. New licenses = new sites."""
    log("Collecting FCC earth station licenses...")
    
    results = []
    # FCC opendata API — protected FSS earth stations
    url = "https://opendata.fcc.gov/resource/acbv-jbb4.json?$limit=100&$order=sys_updated_on%20DESC"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TrevorIntel/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return {"status": "error", "error": str(e), "feeds_checked": ["fcc"]}

    for r in data:
        results.append({
            "number": r.get("number"),
            "licensee": r.get("call_sign_licensee_name"),
            "call_sign": r.get("call_sign"),
            "lat": r.get("latitude_decimal"),
            "lon": r.get("longitude_decimal"),
            "status": r.get("location_status"),
            "lower_freq": r.get("lower_frequency"),
            "upper_freq": r.get("upper_frequency"),
            "antenna_gain": r.get("antenna_gain"),
            "cert_date": r.get("certification_date"),
            "updated": r.get("sys_updated_on"),
        })

    # Match against known sites
    sites_80 = load_sites_80()
    matches = []
    for site in sites_80:
        site_lat = site.get("Lat")
        site_lon = site.get("Lon")
        if site_lat and site_lon:
            for r in results:
                r_lat = r.get("lat")
                r_lon = r.get("lon")
                if r_lat and r_lon:
                    try:
                        d = abs(float(site_lat) - float(r_lat)) + abs(float(site_lon) - float(r_lon))
                        if d < 0.1:  # ~10km proximity
                            matches.append({"site": site.get("Station Name / Location"), "licensee": r["licensee"]})
                    except (ValueError, TypeError):
                        pass

    output = {
        "status": "ok",
        "feeds_checked": ["fcc"],
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "total_records": len(results),
        "licensees_found": list(set(r["licensee"] for r in results if r.get("licensee"))),
        "matched_known_sites": len(matches),
        "matches": matches[:10],
        "recent_filings": results[:20],
    }
    save_output("fcc-earth-stations", output)
    return output


# =========================================================================
# COLLECTOR 2: Launch Schedule (Daily)
# =========================================================================

def collect_launch_daily() -> dict:
    """Check upcoming launches. More LEO satellites = more ground station demand."""
    log("Collecting launch schedules...")
    
    feeds = {}
    
    # Feed 1: Spaceflight Now RSS
    try:
        import feedparser
        sf = feedparser.parse("https://spaceflightnow.com/feed/")
        feeds["spaceflight_now"] = [
            {"title": e.get("title"), "link": e.get("link"), "published": e.get("published")}
            for e in sf.get("entries", [])[:20]
        ]
    except Exception as e:
        feeds["spaceflight_now"] = f"Error: {e}"

    # Feed 2: Launch Library 2 API
    try:
        url = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=25&mode=detailed"
        req = urllib.request.Request(url, headers={"User-Agent": "TrevorIntel/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            ll = json.loads(resp.read())
        
        launches = []
        for r in ll.get("results", []):
            mission = r.get("mission", {}) or {}
            rocket = r.get("rocket", {}) or {}
            pad = r.get("pad", {}) or {}
            loc = pad.get("location", {}) or {}
            
            launches.append({
                "name": r.get("name"),
                "net": r.get("net"),
                "mission_type": mission.get("type"),
                "orbit": mission.get("orbit", {}).get("name") if mission.get("orbit") else None,
                "rocket": rocket.get("configuration", {}).get("name") if rocket.get("configuration") else None,
                "location": loc.get("name"),
                "country": loc.get("country_code"),
                "status": r.get("status", {}).get("name") if r.get("status") else None,
            })
        
        # Count LEO launches specifically
        leo_launches = [l for l in launches if l.get("orbit") and "LEO" in (l["orbit"] or "")]
        starlink_launches = [l for l in launches if "Starlink" in (l.get("name") or "")]
        
        feeds["launch_library"] = {
            "total_upcoming": ll.get("count"),
            "leo_launches": len(leo_launches),
            "starlink_launches": len(starlink_launches),
            "launches": launches[:25],
        }
    except Exception as e:
        feeds["launch_library"] = f"Error: {e}"

    output = {
        "status": "ok",
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "feeds": feeds,
    }
    save_output("launch-schedule", output)
    return output


# =========================================================================
# COLLECTOR 3: ITU Earth Station Filings (Weekly)
# =========================================================================

def collect_itu_weekly() -> dict:
    """Check ITU Space Explorer for new earth station filings globally."""
    log("Collecting ITU earth station filings...")
    
    results = []
    
    # ITU BR IFIC (International Frequency Information Circular) — earth station filings
    # The ITU Space Explorer has a search API
    url = "https://www.itu.int/itu-r/space/apps/public/spaceexplorer/api/networks"
    
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return {
            "status": "error",
            "error": f"ITU API failed: {e}",
            "note": "ITU Space Explorer may require interactive session. Try scraping the as-received publication page instead.",
            "alternative_url": "https://www.itu.int/ITU-R/space/asreceived/Publication/AsReceived",
        }

    # Parse ITU response
    if isinstance(data, list):
        for r in data[:50]:
            results.append({
                "name": r.get("name"),
                "operator": r.get("operator"),
                "type": r.get("type"),
                "orbital_slot": r.get("orbital_position"),
                "filing_date": r.get("filing_date"),
                "status": r.get("status"),
            })

    output = {
        "status": "ok",
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "total_filings": len(results),
        "filings": results[:50],
    }
    save_output("itu-filings", output)
    return output


# =========================================================================
# COLLECTOR 4: Job Postings (Weekly)
# =========================================================================

def collect_jobs_weekly() -> dict:
    """Scan for ground station / satellite infrastructure job postings.
    Spikes in hiring = expansion phase at target operators."""
    log("Scanning ground station job postings...")
    
    # Search job sites for ground station roles
    # Indeed, LinkedIn, Google Jobs - via TheirStack or direct
    # For now, use Indeed RSS feeds as they're publicly accessible
    
    companies = [
        "KSAT", "Kongsberg Satellite", "Space Norway",
        "Leaf Space", "Skynopy", "Atlas Space Operations",
        "RBC Signals", "Infostellar", "Sfera Technologies",
        "AWS Ground Station", "Amazon Kuiper",
        "Viasat", "Eutelsat", "OneWeb", "Telesat",
        "SpaceX", "Starlink",
    ]
    
    jobs_found = []
    
    # Simple web search for ground station job postings
    search_queries = [
        "ground station engineer hiring 2026",
        "satellite gateway site manager job",
        "RF engineer ground terminal",
        "satellite earth station technician",
    ]
    
    for query in search_queries:
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://www.google.com/search?q={encoded}&tbm=nws"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode()
                # Look for date mentions to gauge activity
                dates = re.findall(r'(?:2025|2026)', html)
                jobs_found.append({"query": query, "hits": len(dates), "signal": "recent" if len(dates) > 0 else "none"})
        except Exception as e:
            jobs_found.append({"query": query, "error": str(e)})

    output = {
        "status": "ok",
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "target_companies": companies,
        "search_results": jobs_found,
        "note": "Job posting data is noisy. Better signal from paid LinkedIn API or TheirStack.",
    }
    save_output("job-postings", output)
    return output


# =========================================================================
# COLLECTOR 5: Sentinel-2 Satellite Imagery Check (Monthly)
# =========================================================================

def collect_imagery_monthly() -> dict:
    """Check Sentinel-2 imagery for the highest-priority ground station sites.
    Detects new construction, antenna count changes, site expansions."""
    log("Checking Sentinel-2 imagery for priority sites...")
    
    sites_80 = load_sites_80()
    
    # Focus on top 10 highest-risk sites + any under construction
    # Sort by composite risk score
    sorted_sites = sorted(
        sites_80,
        key=lambda x: x.get("Composite", 0) if isinstance(x.get("Composite"), (int, float)) else 0,
        reverse=True,
    )
    
    # Check sites that have "Imagery" flag = Y (confirmed satellite imagery available)
    priority_sites = [s for s in sorted_sites if s.get("Imagery") == "Y"][:10]
    
    # Sentinel Hub API — free tier allows limited requests
    # Uses OAuth client credentials
    sentinel_client_id = os.environ.get("SENTINEL_CLIENT_ID", "")
    sentinel_client_secret = os.environ.get("SENTINEL_CLIENT_SECRET", "")
    copernicus_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    copernicus_api_url = "https://sh.dataspace.copernicus.eu/api/v1/process"
    
    imagery_results = []
    for site in priority_sites:
        lat = site.get("Lat")
        lon = site.get("Lon")
        name = site.get("Station Name / Location", "Unknown")
        operator = site.get("Operator", "?")
        
        info = {
            "site": name,
            "operator": operator,
            "lat": lat,
            "lon": lon,
            "composite_risk": site.get("Composite"),
            "imagery_available": False,
            "note": "Copernicus Data Space credentials available — will query on monthly run",
        }
        
        if sentinel_client_id and sentinel_client_secret:
            try:
                # Authenticate to Copernicus Data Space
                import urllib.parse
                auth_data = urllib.parse.urlencode({
                    "client_id": sentinel_client_id,
                    "client_secret": sentinel_client_secret,
                    "grant_type": "client_credentials",
                }).encode()
                auth_req = urllib.request.Request(
                    copernicus_token_url,
                    data=auth_data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    method="POST",
                )
                with urllib.request.urlopen(auth_req, timeout=15) as auth_resp:
                    token = json.loads(auth_resp.read())["access_token"]
                
                # Query Sentinel-2 imagery for this site
                evalscript = """
                //VERSION=3
                function setup() {
                    return { input: ["B04", "B08"], output: { bands: 1, sampleType: "UINT16" } };
                }
                function evaluatePixel(sample) {
                    return [sample.B08 - sample.B04];
                }
                """
                
                # Check for recent cloud-free imagery
                today = dt.date.today().isoformat()
                thirty_days_ago = (dt.date.today() - dt.timedelta(days=30)).isoformat()
                
                payload = json.dumps({
                    "input": {
                        "bounds": {
                            "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"},
                            "bbox": [lon-0.1, lat-0.1, lon+0.1, lat+0.1]
                        },
                        "data": [{
                            "type": "SENTINEL-2-L2A",
                            "dataFilter": {
                                "timeRange": {"from": f"{thirty_days_ago}T00:00:00Z", "to": f"{today}T23:59:59Z"},
                                "maxCloudCoverage": 30
                            }
                        }]
                    },
                    "evalscript": evalscript,
                    "output": {"width": 64, "height": 64}
                }).encode()
                
                img_req = urllib.request.Request(
                    copernicus_api_url,
                    data=payload,
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(img_req, timeout=30) as img_resp:
                    img_data = img_resp.read()
                    if img_data and len(img_data) > 100:
                        info["imagery_available"] = True
                        info["image_size_bytes"] = len(img_data)
                        info["note"] = "Recent imagery retrieved"
                        # Save image
                        img_dir = LEO_DATA_DIR / "satellite_imagery"
                        img_dir.mkdir(parents=True, exist_ok=True)
                        img_path = img_dir / f"{name.lower().replace(' ', '_')[:30]}-{today}.png"
                        img_path.write_bytes(img_data)
                        info["saved_image"] = str(img_path)
                    else:
                        info["note"] = "No suitable imagery found (cloud cover or no recent pass)"
            except Exception as img_err:
                info["note"] = f"Imagery query failed: {str(img_err)[:100]}"
        
        imagery_results.append(info)
    
    output = {
        "status": "ok",
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sentinel_api_configured": bool(sentinel_client_id),
        "sites_checked": len(priority_sites),
        "sites_with_recent_imagery": sum(1 for s in imagery_results if s.get("imagery_available")),
        "sites": imagery_results,
    }
    save_output("sentinel-imagery", output)
    return output


# =========================================================================
# SUMMARY: Compile all feeds into a market tracker
# =========================================================================

def compile_tracker() -> dict:
    """Compile all data feeds into a single market tracker snapshot."""
    log("Compiling LEO ground station market tracker...")
    
    tracker = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "data_feeds": {},
    }
    
    # Load most recent outputs from each collector
    for prefix in ["fcc-earth-stations", "launch-schedule", "itu-filings", "job-postings", "sentinel-imagery"]:
        files = sorted(LEO_DATA_DIR.glob(f"{prefix}-*.json"), reverse=True)
        if files:
            try:
                tracker["data_feeds"][prefix] = json.loads(files[0].read_text())
            except Exception:
                tracker["data_feeds"][prefix] = {"status": "unreadable"}

    # Save tracker
    date_slug = dt.date.today().isoformat()
    path = LEO_DATA_DIR / f"market-tracker-{date_slug}.json"
    path.write_text(json.dumps(tracker, indent=2, default=str))
    log(f"Market tracker saved: {path}")
    return tracker


# =========================================================================
# Main
# =========================================================================

def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="LEO Ground Station market data collectors")
    ap.add_argument("--fcc-daily", action="store_true", help="FCC earth station licenses (daily)")
    ap.add_argument("--launch-daily", action="store_true", help="Launch schedule (daily)")
    ap.add_argument("--itu-weekly", action="store_true", help="ITU coordination filings (weekly)")
    ap.add_argument("--jobs-weekly", action="store_true", help="Job posting scan (weekly)")
    ap.add_argument("--imagery-monthly", action="store_true", help="Sentinel-2 site check (monthly)")
    ap.add_argument("--all-daily", action="store_true", help="All daily tasks")
    ap.add_argument("--compile", action="store_true", help="Compile market tracker")
    args = ap.parse_args()

    ran_any = False

    if args.fcc_daily or args.all_daily:
        collect_fcc_daily()
        ran_any = True

    if args.launch_daily or args.all_daily:
        collect_launch_daily()
        ran_any = True

    if args.itu_weekly:
        collect_itu_weekly()
        ran_any = True

    if args.jobs_weekly:
        collect_jobs_weekly()
        ran_any = True

    if args.imagery_monthly:
        collect_imagery_monthly()
        ran_any = True

    if args.compile or ran_any:
        compile_tracker()

    if not ran_any and not args.compile:
        ap.print_help()


if __name__ == "__main__":
    main()
