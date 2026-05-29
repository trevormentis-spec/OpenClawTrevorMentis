#!/usr/bin/env python3
"""GDELT 2.0 Event Collector — CSV export based.

Downloads the latest 15-min GDELT event export, parses CAMEO-coded events,
filters by region/actor/event type, and outputs structured incidents.

No API keys needed. Data is public domain.

Usage:
    python3 scripts/gdelt_collector_v2.py                     # Collect all regions
    python3 scripts/gdelt_collector_v2.py --region middle_east # Single region
    python3 scripts/gdelt_collector_v2.py --incidents incidents.json  # Merge into pipeline
    python3 scripts/gdelt_collector_v2.py --test "Israel"     # Test query
"""

import csv, gzip, io, json, os, pathlib, sys, urllib.request, zipfile
import datetime, time, re

REPO = pathlib.Path(__file__).resolve().parent.parent
CACHE_DIR = REPO / "exports" / "gdelt-cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

LASTUPDATE_URL = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
EXPORT_BASE = "http://data.gdeltproject.org/gdeltv2/"

# GDELT columns (tab-separated, 58 fields)
# Key columns: 0=GLOBALEVENTID, 1=SQLDATE, 2=MonthYear, 3=Year, 4=FractionDate
#   5=Actor1Code, 6=Actor1Name, 7=Actor1CountryCode, 8=Actor1KnownGroupCode
#   9=Actor1EthnicCode, 10=Actor1Religion1Code, 11=Actor1Religion2Code
#   12=Actor1Type1Code, 13=Actor1Type2Code, 14=Actor1Type3Code
#   15=Actor2Code, 16=Actor2Name, 17=Actor2CountryCode, 18=Actor2KnownGroupCode
#   19=Actor2EthnicCode, 20=Actor2Religion1Code, 21=Actor2Religion2Code
#   22=Actor2Type1Code, 23=Actor2Type2Code, 24=Actor2Type3Code
#   25=IsRootEvent, 26=EventCode, 27=EventBaseCode, 28=EventRootCode
#   29=QuadClass, 30=GoldsteinScale, 31=NumMentions, 32=NumSources
#   33=NumArticles, 34=AvgTone, 35=Actor1Geo_Type, 36=Actor1Geo_FullName
#   37=Actor1Geo_CountryCode, 38=Actor1Geo_ADM1Code, 39=Actor1Geo_Lat
#   40=Actor1Geo_Lon, 41=Actor1Geo_FeatureID
#   42=Actor2Geo_Type, 43=Actor2Geo_FullName, 44=Actor2Geo_CountryCode
#   45=Actor2Geo_ADM1Code, 46=Actor2Geo_Lat, 47=Actor2Geo_Lon
#   48=Actor2Geo_FeatureID, 49=ActionGeo_Type, 50=ActionGeo_FullName
#   51=ActionGeo_CountryCode, 52=ActionGeo_ADM1Code, 53=ActionGeo_Lat
#   54=ActionGeo_Lon, 55=ActionGeo_FeatureID, 56=DATEADDED, 57=SOURCEURL

COL = {
    "id": 0, "date": 1, "actor1": 6, "actor1_country": 7,
    "actor2": 16, "actor2_country": 17,
    "event_code": 26, "event_root": 28, "quad_class": 29,
    "goldstein": 30, "mentions": 31, "sources": 32, "articles": 33,
    "tone": 34, "lat": 53, "lon": 54, "location": 50,
    "country": 51, "source_url": 57,
}

# CAMEO root event codes we care about (conflict/cooperation)
EVENT_ROOTS_OF_INTEREST = {
    "14": "protest", "15": "exhibit_force",
    "16": "reduce_relations", "17": "coerce",
    "18": "assault", "19": "fight", "20": "mass_violence",
}

# Regional actor/country filters
REGION_FILTERS = {
    "middle_east": ["ISR", "IRN", "IRQ", "SAU", "SYR", "YEM", "LBN",
                     "PSE", "JOR", "ARE", "OMN", "QAT", "BHR", "KUW"],
    "europe": ["GBR", "FRA", "DEU", "ITA", "ESP", "POL", "UKR", "RUS",
                "NLD", "BEL", "GRC", "PRT", "SWE", "NOR", "FIN",
                "ROM", "BGR", "HUN", "CZE", "SVK", "HRV", "SRB"],
    "north_america": ["USA", "CAN", "MEX"],
    "central_america_caribbean": ["GTM", "HND", "SLV", "NIC", "CRI", "PAN",
                                   "CUB", "HTI", "DOM", "JAM", "TTO"],
    "south_america": ["COL", "VEN", "BRA", "ARG", "CHL", "PER", "ECU",
                       "BOL", "PRY", "URY", "GUY", "SUR"],
    "sub_saharan_africa": ["NGA", "ZAF", "KEN", "ETH", "COD", "SOM", "SDN",
                            "SSD", "MLI", "NER", "TCD", "CAF", "GHA"],
    "north_africa": ["DZA", "EGY", "LBY", "MAR", "TUN", "SDN"],
    "central_asia": ["KAZ", "KGZ", "TJK", "TKM", "UZB"],
    "south_asia": ["AFG", "PAK", "IND", "BGD", "LKA", "NPL", "MMR"],
    "east_asia": ["CHN", "TWN", "JPN", "KOR", "PRK", "MNG"],
    "south_east_asia": ["IDN", "PHL", "VNM", "THA", "MYS", "SGP",
                         "MMR", "KHM", "LAO"],
    "oceania": ["AUS", "NZL", "FJI", "PNG"],
    "russia_eurasia": ["RUS", "UKR", "BLR", "MDA", "GEO", "ARM", "AZE"],
}


def log(msg):
    ts = datetime.datetime.now(datetime.UTC).strftime("%H:%M:%S")
    print(f"[gdelt2 {ts}] {msg}", file=sys.stderr, flush=True)


def get_latest_export_url() -> tuple[str, str, str]:
    """Get the latest export CSV URL from the lastupdate file."""
    resp = urllib.request.urlopen(LASTUPDATE_URL, timeout=15)
    lastupdate = resp.read().decode("utf-8").strip()
    lines = lastupdate.split("\n")
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 3 and parts[2].endswith("export.CSV.zip"):
            url = parts[2]
            filename = url.rstrip("/").split("/")[-1].replace(".export.CSV.zip", "")
            return url, filename, "events"
        if len(parts) >= 3 and parts[2].endswith(".gkg.csv.zip"):
            url = parts[2]
            filename = url.rstrip("/").split("/")[-1].replace(".gkg.csv.zip", "")
            return url, filename, "gkg"
    return "", "", ""


def download_export(url: str) -> str:
    """Download and extract GDELT CSV export, return path to extracted file."""
    cache_name = url.rstrip("/").split("/")[-1].replace(".zip", "")
    csv_path = CACHE_DIR / f"{cache_name}"

    if csv_path.exists():
        log(f"Using cached: {csv_path}")
        return str(csv_path)

    log(f"Downloading: {url}")
    try:
        resp = urllib.request.urlopen(url, timeout=30)
        data = resp.read()
        z = zipfile.ZipFile(io.BytesIO(data))
        csv_filename = z.namelist()[0]
        csv_path.write_bytes(z.read(csv_filename))
        log(f"Extracted: {csv_path} ({csv_path.stat().st_size:,} bytes)")
        return str(csv_path)
    except Exception as e:
        log(f"Download failed: {e}")
        return ""


def parse_events(csv_path: str, region_filter: str | None = None,
                 query: str | None = None, max_events: int = 50) -> list[dict]:
    """Parse GDELT CSV and filter events."""
    if not os.path.exists(csv_path):
        return []

    country_codes = set()
    if region_filter and region_filter in REGION_FILTERS:
        country_codes = set(REGION_FILTERS[region_filter])

    events = []
    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if len(row) < 58:
                continue

            event_code = row[COL["event_code"]]
            event_root = row[COL["event_root"]]
            quad_class = row[COL["quad_class"]]
            goldstein = float(row[COL["goldstein"]]) if row[COL["goldstein"]] else 0

            # Filter: only conflict events (quad 3=material conflict, 4=verbal conflict)
            if quad_class not in ("3", "4"):
                continue

            # Get actor info
            actor1 = row[COL["actor1"]].strip()
            actor2 = row[COL["actor2"]].strip()
            actor1_country = row[COL["actor1_country"]].strip()
            actor2_country = row[COL["actor2_country"]].strip()
            location = row[COL["location"]].strip()
            loc_country = row[COL["country"]].strip()

            # Filter by region if specified
            if region_filter and country_codes:
                matches = False
                for code in [actor1_country, actor2_country, loc_country]:
                    if code in country_codes:
                        matches = True
                        break
                if not matches:
                    continue

            # Filter by query text if specified
            if query:
                query_lower = query.lower()
                if (query_lower not in actor1.lower() and
                    query_lower not in actor2.lower() and
                    query_lower not in location.lower()):
                    continue

            date_str = row[COL["date"]]
            if len(date_str) == 8:
                date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

            try:
                lat = float(row[COL["lat"]]) if row[COL["lat"]] else None
                lon = float(row[COL["lon"]]) if row[COL["lon"]] else None
            except (ValueError, TypeError):
                lat, lon = None, None
            try:
                tone = float(row[COL["tone"]]) if row[COL["tone"]] else 0
            except (ValueError, TypeError):
                tone = 0
            try:
                mentions = int(row[COL["mentions"]]) if row[COL["mentions"]] else 0
                articles = int(row[COL["articles"]]) if row[COL["articles"]] else 0
            except (ValueError, TypeError):
                mentions, articles = 0, 0

            title = f"{actor1} → {actor2}: {EVENT_ROOTS_OF_INTEREST.get(event_root, f'event_{event_root}')}"
            if location:
                title += f" [{location}]"

            events.append({
                "title": title[:200],
                "actor1": actor1,
                "actor2": actor2,
                "actor1_country": actor1_country,
                "actor2_country": actor2_country,
                "location": location,
                "country": loc_country,
                "lat": lat,
                "lon": lon,
                "date": date_str,
                "event_code": event_code,
                "event_root": event_root,
                "quad_class": quad_class,
                "goldstein_scale": goldstein,
                "tone": tone,
                "mentions": mentions,
                "articles": articles,
                "goldstein_label": "conflict" if goldstein < -5 else "tension" if goldstein < 0 else "cooperation",
            })

    # Sort by mentions (relevance proxy), deduplicate, limit
    events.sort(key=lambda e: e["mentions"], reverse=True)
    seen = set()
    unique = []
    for e in events:
        key = (e["actor1"], e["actor2"], e["event_root"])
        if key not in seen:
            seen.add(key)
            unique.append(e)

    return unique[:max_events]


def format_incidents(events: list[dict], region: str) -> list[dict]:
    """Convert GDELT events to pipeline incident format."""
    incidents = []
    for e in events:
        narrative = f"{e['title']}."
        if e["location"]:
            narrative += f" Location: {e['location']} ({e['country'] or 'unknown'})."
        if e["goldstein_scale"]:
            narrative += f" Goldstein scale: {e['goldstein_scale']:+.1f} ({e['goldstein_label']})."
        if e["articles"]:
            narrative += f" Coverage: {e['articles']} articles."

        incidents.append({
            "title": e["title"],
            "narrative": narrative,
            "region": region,
            "date": e["date"],
            "source": "GDELT 2.0",
            "collector": "gdelt_v2",
            "admiralty": ("C", 3),
            "metadata": {
                "actor1": e["actor1"],
                "actor2": e["actor2"],
                "country": e["country"],
                "lat": e["lat"],
                "lon": e["lon"],
                "goldstein": e["goldstein_scale"],
                "articles": e["articles"],
            },
        })
    return incidents


def collect_region(region: str, max_events: int = 15) -> list[dict]:
    """Collect GDELT events for a single region."""
    url, ts, _ = get_latest_export_url()
    if not url:
        log("No export URL found")
        return []

    csv_path = download_export(url)
    if not csv_path:
        return []

    query = " ".join(REGION_FILTERS.get(region, []))
    events = parse_events(csv_path, region_filter=region, max_events=max_events)
    log(f"{region}: {len(events)} events")
    return format_incidents(events, region)


def collect_all_regions(max_per_region: int = 10) -> dict[str, list[dict]]:
    """Collect GDELT events for all pipeline regions."""
    url, ts, _ = get_latest_export_url()
    if not url:
        log("No export URL found")
        return {}

    csv_path = download_export(url)
    if not csv_path:
        return {}

    results = {}
    for region in REGION_FILTERS:
        events = parse_events(csv_path, region_filter=region, max_events=max_per_region)
        results[region] = format_incidents(events, region)
        log(f"{region}: {len(events)} events")
    return results


def merge_with_incidents(gdelt_results: dict[str, list[dict]],
                         incidents_path: str) -> int:
    """Merge GDELT events into pipeline incidents.json."""
    ipath = pathlib.Path(incidents_path)
    if not ipath.exists():
        log(f"Incidents file not found: {incidents_path}")
        return 0

    data = json.loads(ipath.read_text())
    existing = data if isinstance(data, list) else data.get("incidents", [])

    # Deduplicate by title+region
    existing_keys = {(i.get("title", ""), i.get("region", "")) for i in existing}
    added = 0
    for region, events in gdelt_results.items():
        for ev in events:
            key = (ev["title"], region)
            if key not in existing_keys:
                existing.append(ev)
                existing_keys.add(key)
                added += 1

    if isinstance(data, dict):
        data["incidents"] = existing
        data["gdelt_v2_added"] = added
    ipath.write_text(json.dumps(data, indent=2))
    log(f"Merged {added} new GDELT events into {incidents_path}")
    return added


def main():
    import argparse
    parser = argparse.ArgumentParser(description="GDELT 2.0 Event Collector")
    parser.add_argument("--region", type=str, help="Collect single region")
    parser.add_argument("--incidents", type=str, help="Merge into incidents.json")
    parser.add_argument("--test", type=str, help="Test a keyword query")
    parser.add_argument("--max", type=int, default=10, help="Max events per region")
    args = parser.parse_args()

    if args.test:
        url, ts, _ = get_latest_export_url()
        csv_path = download_export(url)
        events = parse_events(csv_path, query=args.test, max_events=5)
        print(f"\nGDELT results for '{args.test}': {len(events)} events")
        for e in events:
            print(f"  {e['actor1']:30s} → {e['actor2']:30s} | "
                  f"GS={e['goldstein_scale']:+.1f} | {e['location']}")
        return 0

    if args.region:
        incidents = collect_region(args.region, max_events=args.max)
        print(f"\n{args.region}: {len(incidents)} incidents")
        for inc in incidents[:5]:
            print(f"  → {inc['title'][:80]}")
        return 0

    if args.incidents:
        log("Starting GDELT 2.0 collection")
        results = collect_all_regions(max_per_region=args.max)
        total = sum(len(v) for v in results.values())
        log(f"Collected {total} total events")
        added = merge_with_incidents(results, args.incidents)
        log(f"Done. Added {added} new events")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    main()
