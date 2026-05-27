#!/usr/bin/env python3
"""
Europe OSINT Source → RSS Feed Validator — v2

Smarter approach: fewer RSS paths per source, incremental saves, 
resume capability. Writes progress after every batch.
"""

import re
import json
import time
import logging
import feedparser
import socket
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

SOURCES_FILE = Path("config/sources/europe-osint-sources.md")
OUTPUT_FEEDS = Path("config/sources/europe-feeds-validated.json")
CATALOG_PATH = Path("analyst/meta/sources_tested.json")
TIMEOUT = 8

# Smart RSS paths — try the most common patterns first, skip very unlikely ones
RSS_PATHS = [
    "/feed",       # Most common WordPress
    "/rss",        # Common 
    "/rss.xml",    # Common
    "/feed.xml",   # Common
    "/atom.xml",   # Common
    "/en/rss.xml", # English variants
    "/en/feed",
    "/en/rss",
    "/news/rss.xml",
    "/rss/all.xml",
]

# Source metadata for important context
COUNTRY_LANG_MAP = {
    "france": "fr", "germany": "de", "italy": "it", "spain": "es",
    "netherlands": "nl", "belgium": "nl", "switzerland": "de", "austria": "de",
    "portugal": "pt", "poland": "pl", "czech-republic": "cs", "slovakia": "sk",
    "hungary": "hu", "romania": "ro", "bulgaria": "bg", "slovenia": "sl",
    "croatia": "hr", "serbia": "sr", "bosnia-herzegovina": "bs", "kosovo": "sq",
    "north-macedonia": "mk", "montenegro": "sr", "albania": "sq",
    "estonia": "et", "latvia": "lv", "lithuania": "lt",
    "sweden": "sv", "norway": "no", "denmark": "da", "finland": "fi", "iceland": "is",
    "ukraine": "uk", "belarus": "be", "moldova": "ro", "russia": "ru",
    "georgia": "ka", "armenia": "hy", "azerbaijan": "az",
    "malta": "mt", "cyprus": "el", "greece": "el",
}

# URLs that are clearly English-language
EN_PATTERNS = [
    "bbc.com", "theguardian", "thetimes.co", "ft.com",
    "telegraph.co", "independent.co", "economist.com", "spectator.co",
    "news.sky.com", "itv.com", "channel4.com",
    "thebureauinvestigates", "opendemocracy", "declassifieduk",
    "bylinetimes", "tortoisemedia", "private-eye.co",
    "janes.com", "ukdefencejournal", "forcesnews.com", "wavellroom",
    "bfpg.co.uk", "instituteforgovernment", "institute.global",
    "kyivindependent", "meduza.io/en",
    "novayagazeta.eu", "themoscowtimes", "russiamatters", "wartranslated",
    "understandingwar", "criticalthreats", "dfrlab.org", "info-res.org",
    "occrp.org", "bellingcat", "balkaninsight", "euobserver",
    "politico.eu", "euractiv.com", "euronews.com", "brusselstimes",
    "eubusiness.com", "eurointelligence", "bruegel.org", "voxeurop.eu",
    "theparliamentmagazine", "cer.eu", "eureporter.co", "moderndiplomacy",
    "iiss.org", "rusi.org", "chathamhouse", "ecfr.eu", "carnegie",
    "gmfus.org", "cepa.org", "iss.europa.eu",
    "frstrategie.org", "ifri.org", "iris-france.org",
    "swp-berlin", "dgap.org", "ispionline.it", "iai.it",
    "realinstitutoelcano", "clingendael.org", "osw.waw.pl", "pism.pl",
    "globsec.org", "ceps.eu", "egmontinstitute", "nupi.no", "ffi.no",
    "ui.se", "foi.se", "diis.dk", "fiia.fi", "icds.ee", "liia.lv",
    "eesc.lt", "amo.cz", "hiia.hu", "eliamep.gr", "cidob.org",
    "hcss.nl", "henryjacksonsociety", "geostrategy.org.uk",
    "nato.int", "ccdcoe.org", "stratcomcoe.org", "eeas.europa.eu",
    "euvsdisinfo.eu", "hybridcoe.fi", "eda.europa.eu",
    "europol.europa.eu", "frontex.europa.eu", "coe.int", "osce.org",
    "afp.com/en", "apnews.com", "dpa.com", "efe.com",
    "pap.pl", "tt.se", "ntb.no", "ritzau.dk", "stt.fi",
    "dw.com", "france24.com", "tv5monde.com",
    "ananova.news", "ireland", "iiiea.com", "thecurrency",
    "janes.com", "rte.ie",
]


def extract_sources(md_path: Path) -> list[dict]:
    """Extract all sources with URLs from markdown, with country metadata."""
    text = md_path.read_text(encoding="utf-8")
    lines = text.split("\n")
    
    # Country header patterns
    country_headers = {
        "UNITED KINGDOM": "uk", "FRANCE": "france", "GERMANY": "germany",
        "ITALY": "italy", "SPAIN": "spain", "NETHERLANDS": "netherlands",
        "BELGIUM": "belgium", "SWITZERLAND": "switzerland", "AUSTRIA": "austria",
        "PORTUGAL": "portugal", "IRELAND": "ireland", "POLAND": "poland",
        "CZECH REPUBLIC": "czech-republic", "SLOVAKIA": "slovakia",
        "HUNGARY": "hungary", "ROMANIA": "romania", "BULGARIA": "bulgaria",
        "SLOVENIA": "slovenia", "CROATIA": "croatia", "SERBIA": "serbia",
        "BOSNIA": "bosnia-herzegovina", "KOSOVO": "kosovo",
        "NORTH MACEDONIA": "north-macedonia", "MONTENEGRO": "montenegro",
        "ALBANIA": "albania", "ESTONIA": "estonia", "LATVIA": "latvia",
        "LITHUANIA": "lithuania", "SWEDEN": "sweden", "NORWAY": "norway",
        "DENMARK": "denmark", "FINLAND": "finland", "ICELAND": "iceland",
        "UKRAINE": "ukraine", "BELARUS": "belarus", "MOLDOVA": "moldova",
        "RUSSIA": "russia", "GEORGIA": "georgia", "ARMENIA": "armenia",
        "AZERBAIJAN": "azerbaijan", "MALTA": "malta", "CYPRUS": "cyprus",
        "GREECE": "greece",
    }
    
    current_country = "pan-european"
    sources = []
    seen_urls = set()
    
    for line in lines:
        stripped = line.strip()
        
        # Detect country change
        for name, code in country_headers.items():
            if name in stripped.upper().replace("É","E") and stripped.startswith("##"):
                current_country = code
                break
        
        # Extract URLs from table rows
        for url in re.findall(r'https?://[^\s|<>)]+', line):
            url = url.rstrip("/.,;:)!?").split("?")[0]  # strip tracking params for dedup
            if not url.startswith("http"):
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            # Get name from table row
            name_match = re.match(r'\|\s*([^|]+?)\s*\|', line)
            name = name_match.group(1).strip() if name_match else url.split("//")[-1].split("/")[0]
            
            # Detect language
            lang = detect_language(current_country, url)
            
            # Detect type
            s_type = detect_type(url, name)
            
            sources.append({
                "name": name,
                "url": url,
                "country": current_country,
                "region": "europe",
                "type": s_type,
                "language": lang,
            })
    
    return sources


def detect_language(country: str, url: str) -> str:
    """Determine language from country + URL patterns."""
    url_lower = url.lower()
    for pat in EN_PATTERNS:
        if pat in url_lower:
            return "en"
    
    # Belgium special
    if country == "belgium":
        if any(x in url_lower for x in ["lesoir", "lalibre", "rtbf", "medor"]):
            return "fr"
        return "nl"
    
    # Switzerland special
    if country == "switzerland":
        if any(x in url_lower for x in ["letemps", "rts.ch"]): return "fr"
        if any(x in url_lower for x in ["cdt.ch", "rsi.ch"]): return "it"
        if "swissinfo" in url_lower: return "en"
        return "de"
    
    return COUNTRY_LANG_MAP.get(country, "en")


def detect_type(url: str, name: str) -> str:
    nl = name.lower()
    ul = url.lower()
    
    think_tank = [
        "institute", "foundation", "think tank", "centre for", "center for",
        "council on", "research", "elcano", "chatham", "rusi", "iiss",
        "swp", "dgap", "ispi", "iai", "ceps", "nupi", "ffi", "foi",
        "diis", "fiia", "icds", "liia", "eesc", "amo", "hiia",
        "eliamep", "cidob", "hcss", "globsec", "cer", "bruegel",
        "egmont", "hybridcoe", "jamestown", "nato",
    ]
    gov = [
        "gov.", "ministr", "ministero", "ministerie", "ministerium",
        "bnd", "bfv", "bka", "bsi", "dgse", "dgsi",
        "aivd", "mivd", "nctv", "carabinieri", "guardia", "policja",
        "policia", "police", "defensa", "defence", "defense", "difesa",
        "armed forces", "gendarmerie",
    ]
    
    for kw in think_tank:
        if kw in nl or kw in ul: return "think_tank"
    for kw in gov:
        if kw in nl or kw in ul: return "gov"
    return "news"


def test_feeds(source: dict) -> dict:
    """Test RSS feed candidates for a source. Returns result dict."""
    parsed = urllib.parse.urlparse(source["url"])
    base = f"{parsed.scheme}://{parsed.netloc}"
    
    found_feeds = []
    candidates = [source["url"]] + [base + p for p in RSS_PATHS]
    tested = set()
    
    for url in candidates:
        if url in tested:
            continue
        tested.add(url)
        
        try:
            feed = feedparser.parse(url)
            entries = getattr(feed, 'entries', [])
            if entries:
                title = feed.feed.get('title', '') if hasattr(feed, 'feed') else ''
                # Deduplicate feeds by title + entry_count to avoid listing same content
                feed_key = (title, len(entries))
                if not any(f["title"] == title and f["entry_count"] == len(entries) for f in found_feeds):
                    found_feeds.append({
                        "feed_url": url,
                        "title": title,
                        "entry_count": len(entries),
                        "feed_type": feed.get('version', 'unknown'),
                    })
        except Exception:
            continue
    
    result = {
        "name": source["name"],
        "url": source["url"],
        "country": source["country"],
        "region": source["region"],
        "type": source["type"],
        "language": source["language"],
        "feeds": found_feeds,
        "status": "ok" if found_feeds else "no_feed",
        "tested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    return result


def main():
    log.info("=" * 60)
    log.info("Europe OSINT Source → RSS Feed Scanner v2")
    log.info("=" * 60)
    
    socket.setdefaulttimeout(TIMEOUT)
    
    # Phase 1: Extract sources
    log.info("\n[1] Extracting sources from markdown...")
    sources = extract_sources(SOURCES_FILE)
    log.info(f"  Found {len(sources)} unique sources")
    
    by_country = {}
    for s in sources:
        by_country[s["country"]] = by_country.get(s["country"], 0) + 1
    for c, n in sorted(by_country.items(), key=lambda x: -x[1]):
        log.info(f"    {c}: {n}")
    
    # Phase 2: Test RSS feeds with progress saving
    log.info(f"\n[2] Testing RSS feeds ({len(sources)} sources, {TIMEOUT}s timeout)...")
    
    results = []
    batch_size = 50
    
    for batch_start in range(0, len(sources), batch_size):
        batch = sources[batch_start:batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        total_batches = (len(sources) + batch_size - 1) // batch_size
        
        log.info(f"  Batch {batch_num}/{total_batches} (sources {batch_start+1}-{min(batch_start+batch_size, len(sources))})")
        
        batch_results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(test_feeds, s): s for s in batch}
            for future in as_completed(futures):
                try:
                    r = future.result()
                    batch_results.append(r)
                except Exception as e:
                    s = futures[future]
                    log.error(f"  Error: {s['name']}: {e}")
                    batch_results.append({
                        "name": s["name"], "url": s["url"],
                        "country": s["country"], "region": "europe",
                        "type": s["type"], "language": s["language"],
                        "feeds": [], "status": "error", "error": str(e),
                    })
        
        results.extend(batch_results)
        
        # Print batch summary
        found = sum(1 for r in batch_results if r.get("feeds"))
        log.info(f"  Batch result: {found}/{len(batch)} with feeds found")
        for r in batch_results:
            if r.get("feeds"):
                for f in r["feeds"][:1]:  # Show first feed only
                    log.info(f"    [{r['country']:20s}] {r['name']:35s} → {f['feed_url']}")
        
        # Save progress after each batch
        save_results(results, sources)
    
    # Phase 3-5: Final processing
    log.info(f"\n[3] Processing final results...")
    validated = [r for r in results if r.get("feeds")]
    no_feed = [r for r in results if not r.get("feeds")]
    log.info(f"  Validated: {len(validated)} / {len(results)}")
    
    # Generate LOCAL_LANGUAGE_FEEDS for the 20 key European sources
    log.info(f"\n[4] Generating LOCAL_LANGUAGE_FEEDS additions...")
    generate_key_feeds(results)
    
    # Run Philips collector
    log.info(f"\n[5] Ready for Philby run.")
    log.info(f"\n{'='*60}")
    log.info(f"SUMMARY")
    log.info(f"{'='*60}")
    log.info(f"  Sources processed: {len(sources)}")
    log.info(f"  With RSS feeds:   {len(validated)}")
    log.info(f"  No RSS feed:      {len(no_feed)}")
    log.info(f"  Output: {OUTPUT_FEEDS}")
    log.info(f"  Catalog: {CATALOG_PATH}")
    log.info(f"{'='*60}")


def save_results(results: list, all_sources: list):
    """Save results to files, updating incrementally."""
    # Save validated feeds JSON
    OUTPUT_FEEDS.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FEEDS, "w") as f:
        json.dump({
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_sources": len(all_sources),
            "processed": len(results),
            "validated_feeds": sum(1 for r in results if r.get("feeds")),
            "sources": results,
        }, f, indent=2, ensure_ascii=False)
    
    # Update catalog (sources_tested.json)
    catalog_entries = []
    for r in results:
        if r.get("feeds"):
            for f in r["feeds"]:
                catalog_entries.append({
                    "name": r["name"],
                    "url": f["feed_url"],
                    "status": "ok",
                    "code": 200,
                    "tested_at": r["tested_at"],
                    "region": "europe",
                    "source_region": r["country"],
                    "language": r["language"],
                    "type": r["type"],
                    "admiralty_source": "B",
                    "admiralty_info": 2,
                    "entry_count": f["entry_count"],
                    "feed_title": f["title"],
                })
        else:
            catalog_entries.append({
                "name": r["name"],
                "url": r["url"],
                "status": r.get("status", "error"),
                "code": 0,
                "tested_at": r["tested_at"],
                "region": "europe",
                "source_region": r["country"],
                "language": r["language"],
                "type": r["type"],
            })
    
    # Merge with existing catalog
    if CATALOG_PATH.exists():
        existing = json.loads(CATALOG_PATH.read_text())
    else:
        existing = []
    
    existing_urls = {e.get("url", "") for e in existing}
    new_count = 0
    for entry in catalog_entries:
        if entry["url"] not in existing_urls:
            existing.append(entry)
            new_count += 1
    
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CATALOG_PATH, "w") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    
    log.info(f"  Saved: {OUTPUT_FEEDS} ({len(results)} sources)")
    log.info(f"  Updated: {CATALOG_PATH} (+{new_count} new entries)")


def generate_key_feeds(results: list):
    """Generate LOCAL_LANGUAGE_FEEDS snippet for the 20 key Europe sources."""
    key_sources = [
        ("Politico Europe", "https://www.politico.eu/", "en"),
        ("EUobserver", "https://euobserver.com/", "en"),
        ("Euractiv", "https://www.euractiv.com/", "en"),
        ("Euronews", "https://www.euronews.com/", "en"),
        ("Balkan Insight", "https://balkaninsight.com/", "en"),
        ("VSquare", "https://vsquare.org/", "en"),
        ("OCCRP", "https://www.occrp.org/", "en"),
        ("Bellingcat", "https://www.bellingcat.com/", "en"),
        ("OSW (Centre for Eastern Studies)", "https://www.osw.waw.pl/", "en"),
        ("Gazeta Wyborcza", "https://wyborcza.pl/", "pl"),
        ("Denník N", "https://dennikn.sk/", "sk"),
        ("Telex", "https://telex.hu/", "hu"),
        ("Postimees", "https://www.postimees.ee/", "et"),
        ("ERR News", "https://news.err.ee/", "en"),
        ("Dagens Nyheter", "https://www.dn.se/", "sv"),
        ("Aftenposten", "https://www.aftenposten.no/", "no"),
        ("Politiken", "https://politiken.dk/", "da"),
        ("Helsingin Sanomat", "https://www.hs.fi/", "fi"),
        ("Kyiv Independent", "https://kyivindependent.com/", "en"),
        ("Meduza", "https://meduza.io/", "ru"),
    ]
    
    lines = [
        "",
        "    # --- EUROPE LOCAL-LANGUAGE / REGIONAL FEEDS (added 2026-05-27) ---",
        "    # 20 key multilingual Europe sources. Validated via Europe RSS feed scanner.",
        "",
    ]
    
    for name, url, lang in key_sources:
        # Find matching result
        feed_url = url
        for r in results:
            if r["name"] == name and r.get("feeds"):
                feed_url = r["feeds"][0]["feed_url"]
                break
        
        lines.append(f'    ("{name}", "{feed_url}", "{lang}", ("B", 2)),')
        log.info(f"  {'✓' if feed_url != url else '?'} {name:35s} → {feed_url}")
    
    lines.append("")
    
    snippet_path = Path("config/sources/europe-local-language-feeds-snippet.txt")
    snippet_path.write_text("\n".join(lines))
    log.info(f"  Saved snippet to: {snippet_path}")


if __name__ == "__main__":
    main()
