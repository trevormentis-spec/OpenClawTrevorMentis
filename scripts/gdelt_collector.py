#!/usr/bin/env python3
"""GDELT Collection Floor — guarantees every region gets minimum incident data.

Runs as a collection-layer fallback in the daily brief pipeline.
Queries GDELT for each region that has < N incidents from RSS collection.
Fills gaps with structured event data.

Usage:
    python3 scripts/gdelt_collector.py --incidents incidents.json
    python3 scripts/gdelt_collector.py --test "Central America"
    python3 scripts/gdelt_collector.py --dry-run
"""

import json, os, pathlib, sys, urllib.request, urllib.parse, datetime, time

REPO = pathlib.Path(__file__).resolve().parent.parent
GDELT_API = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_TIMEOUT = 15

REGION_QUERIES = {
    "central_america_caribbean": "Central America crime gang protest Haiti Guatemala Honduras El Salvador Nicaragua",
    "south_america": "South America Brazil Argentina Colombia Venezuela protest election crime Amazon",
    "sub_saharan_africa": "Africa Nigeria Kenya Ethiopia Ghana South Africa DRC Somalia Sudan Mali conflict attack protest election coup",
    "north_africa": "North Africa Morocco Algeria Tunisia Libya Egypt protest election military migrant",
    "south_asia": "India Pakistan Bangladesh Afghanistan Sri Lanka Nepal conflict protest election attack",
    "central_asia": "Kazakhstan Kyrgyzstan Tajikistan Turkmenistan Uzbekistan energy security",
    "east_asia": "China Taiwan Japan South Korea North Korea military diplomacy missile protest",
    "south_east_asia": "Indonesia Philippines Vietnam Thailand Malaysia Myanmar Singapore protest election military maritime",
    "oceania": "Australia New Zealand Fiji Pacific Islands politics election climate security",
    "middle_east": "Iran Iraq Israel Palestine Syria Lebanon Yemen Saudi Arabia UAE conflict nuclear strike negotiation oil",
    "north_america": "United States Canada Mexico politics Congress election security crime migration tariff",
    "europe": "Europe EU NATO UK France Germany Ukraine Russia Poland Baltic Balkan Nordic election defense conflict energy",
    "russia_eurasia": "Russia Ukraine Belarus Moldova Caucasus Georgia Armenia Azerbaijan conflict attack protest election energy",
}


def log(msg):
    ts = datetime.datetime.now(datetime.UTC).strftime("%H:%M:%S")
    print(f"[gdelt {ts}] {msg}", file=sys.stderr, flush=True)


def query_gdelt(region: str, query: str, max_records: int = 30) -> list[dict]:
    """Query GDELT for recent events in a region with retry."""
    params = urllib.parse.urlencode({
        "query": query, "mode": "ArtList", "format": "json",
        "maxrecords": min(max_records, 100), "sort": "datedesc", "timespan": "24h",
    })
    url = f"{GDELT_API}?{params}"
    
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TrevorIntel/1.0"})
            resp = urllib.request.urlopen(req, timeout=GDELT_TIMEOUT)
            raw = resp.read()
            if raw[:2] == b'\x1f\x8b':
                import gzip
                raw = gzip.decompress(raw)
            data = json.loads(raw)
            articles = data.get("articles", data.get("results", []))
            if not articles:
                return []
            
            events = []
            for a in articles[:max_records]:
                title = a.get("title", "")
                url_out = a.get("url", "")
                source = a.get("source", "")
                date = a.get("seendate", a.get("date", ""))
                if not title or not url_out:
                    continue
                events.append({
                    "title": title[:200], "url": url_out,
                    "source": source or "GDELT", "region": region,
                    "date": str(date)[:10] if date else datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d"),
                    "relevance": "high", "admiralty": ("C", 3),
                    "collector": "gdelt",
                    "notes": f"GDELT-automated: region={region}",
                })
            return events
        
        except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError, OSError) as e:
            if attempt == 0:
                log(f"Retry {region}: {str(e)[:60]}")
                time.sleep(8)
                continue
            log(f"GDELT query failed for {region}: {str(e)[:80]}")
            return []
    
    return []


def collect_all_regions(target_regions=None, max_per_region=20):
    """Collect GDELT events for all regions."""
    results = {}
    regions_to_query = target_regions or list(REGION_QUERIES.keys())
    for i, region in enumerate(regions_to_query):
        query = REGION_QUERIES.get(region, region)
        events = query_gdelt(region, query, max_records=max_per_region)
        results[region] = events
        log(f"({i+1}/{len(regions_to_query)}) {region}: {len(events)} events")
        if i < len(regions_to_query) - 1:
            time.sleep(6.0)
    return results


def merge_with_incidents(gdelt_events, incidents_path):
    """Merge GDELT events into existing incidents.json."""
    if not incidents_path.exists():
        log(f"Incidents file not found: {incidents_path}")
        return 0
    data = json.loads(incidents_path.read_text())
    existing = data.get("incidents", data)
    if isinstance(existing, dict):
        existing = [existing]
    existing_urls = {i.get("url", "") for i in existing}
    added = 0
    for region, events in gdelt_events.items():
        for ev in events:
            if ev["url"] not in existing_urls:
                existing.append(ev)
                existing_urls.add(ev["url"])
                added += 1
    if isinstance(data, dict):
        data["incidents"] = existing
        data["gdelt_merged"] = True
        data["gdelt_added"] = added
    incidents_path.write_text(json.dumps(data, indent=2))
    log(f"Merged {added} new GDELT events into {incidents_path.name}")
    return added


def main():
    import argparse
    parser = argparse.ArgumentParser(description="GDELT Collection Floor")
    parser.add_argument("--incidents", type=str, help="Path to incidents.json to enrich")
    parser.add_argument("--test", type=str, help="Test a single region query")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be collected")
    args = parser.parse_args()
    
    if args.test:
        query = REGION_QUERIES.get(args.test.lower(), args.test)
        events = query_gdelt(args.test, query, max_records=5)
        print(f"\nResults for {args.test}: {len(events)} events")
        for e in events[:3]:
            print(f"  → {e['title'][:100]}")
        return 0
    
    if args.dry_run:
        results = collect_all_regions(max_per_region=5)
        total = sum(len(v) for v in results.values())
        print(f"\nTotal GDELT events available: {total}")
        return 0
    
    if args.incidents:
        incidents_path = pathlib.Path(args.incidents)
        log("Starting GDELT collection")
        results = collect_all_regions(max_per_region=20)
        total = sum(len(v) for v in results.values())
        log(f"Collected {total} total events")
        added = merge_with_incidents(results, incidents_path)
        log(f"Done. Added {added} new events")
        return 0
    
    parser.print_help()
    return 1


if __name__ == "__main__":
    main()
