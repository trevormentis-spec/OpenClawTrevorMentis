#!/usr/bin/env python3
"""
Europe OSINT Source → RSS Feed Validator

Extracts all URLs from europe-osint-sources.md, tries common RSS feed paths,
validates them with feedparser, and produces:
  1. europe-feeds-validated.json (complete validated feed list)
  2. sources_tested.json updates (catalog entries)
  3. LOCAL_LANGUAGE_FEEDS snippet for collect.py
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

# --- Configuration ---
SOURCES_FILE = Path("config/sources/europe-osint-sources.md")
OUTPUT_FEEDS = Path("config/sources/europe-feeds-validated.json")
CATALOG_PATH = Path("analyst/meta/sources_tested.json")
TIMEOUT = 8  # seconds per feed attempt

# Common RSS feed paths to try
RSS_PATHS = [
    "/feed",
    "/feed/",
    "/rss",
    "/rss/",
    "/rss.xml",
    "/feed.xml",
    "/atom.xml",
    "/feeds",
    "/feeds/",
    "/feeds/posts/default",
    "/en/rss",
    "/en/rss.xml",
    "/en/feed",
    "/en/feed/",
    "/news/rss.xml",
    "/news/feed",
    "/news/feed/",
    "/rss/news",
    "/rss/all.xml",
    "/rss/feed",
    "/rss/feeds",
    "/xml/rss/all.xml",
    "/main/feed",
]


def extract_sources(md_path: Path) -> list[dict]:
    """Parse the markdown source file into structured source entries."""
    text = md_path.read_text(encoding="utf-8")
    sources = []

    # Split by country/section headers to assign region tags
    lines = text.split("\n")
    
    current_region = "europe"
    current_country = "pan-european"
    current_section = ""
    
    country_map = {
        "UNITED KINGDOM": "uk",
        "FRANCE": "france",
        "GERMANY": "germany",
        "ITALY": "italy",
        "SPAIN": "spain",
        "NETHERLANDS": "netherlands",
        "BELGIUM": "belgium",
        "SWITZERLAND": "switzerland",
        "AUSTRIA": "austria",
        "PORTUGAL": "portugal",
        "IRELAND": "ireland",
        "POLAND": "poland",
        "CZECH REPUBLIC": "czech-republic",
        "SLOVAKIA": "slovakia",
        "HUNGARY": "hungary",
        "ROMANIA": "romania",
        "BULGARIA": "bulgaria",
        "SLOVENIA": "slovenia",
        "CROATIA": "croatia",
        "SERBIA": "serbia",
        "BOSNIA": "bosnia-herzegovina",
        "KOSOVO": "kosovo",
        "NORTH MACEDONIA": "north-macedonia",
        "MONTENEGRO": "montenegro",
        "ALBANIA": "albania",
        "ESTONIA": "estonia",
        "LATVIA": "latvia",
        "LITHUANIA": "lithuania",
        "SWEDEN": "sweden",
        "NORWAY": "norway",
        "DENMARK": "denmark",
        "FINLAND": "finland",
        "ICELAND": "iceland",
        "UKRAINE": "ukraine",
        "BELARUS": "belarus",
        "MOLDOVA": "moldova",
        "RUSSIA": "russia",
        "GEORGIA": "georgia",
        "ARMENIA": "armenia",
        "AZERBAIJAN": "azerbaijan",
        "MALTA": "malta",
        "CYPRUS": "cyprus",
        "GREECE": "greece",
    }

    for line in lines:
        stripped = line.strip()

        # Track sections
        if stripped.startswith("## SECTION"):
            current_section = stripped
            continue

        # Detect country headers
        for country_name, code in country_map.items():
            if stripped.startswith(f"## 🇦") or stripped.startswith(f"## 🇧") or stripped.startswith(f"## 🇨") or \
               stripped.startswith(f"## 🇩") or stripped.startswith(f"## 🇪") or stripped.startswith(f"## 🇫") or \
               stripped.startswith(f"## 🇬") or stripped.startswith(f"## 🇭") or stripped.startswith(f"## 🇮") or \
               stripped.startswith(f"## 🇱") or stripped.startswith(f"## 🇲") or stripped.startswith(f"## 🇳") or \
               stripped.startswith(f"## 🇵") or stripped.startswith(f"## 🇷") or stripped.startswith(f"## 🇸") or \
               stripped.startswith(f"## 🇹") or stripped.startswith(f"## 🇺") or stripped.startswith(f"## 🇽"):
                if country_name in stripped:
                    current_country = code
                    break
        else:
            if stripped.startswith("## ") and "UNITED KINGDOM" in stripped.upper():
                current_country = "uk"
            elif stripped.startswith("## ") and "RUSSIA" in stripped.upper() and "UKRAINE" not in stripped.upper():
                current_country = "russia"
            elif stripped.startswith("## ") and "BELARUS" in stripped.upper().replace("É","E"):
                current_country = "belarus"

        # Detect table rows with URLs
        # Match | Name | ... | URL |  or just | URL |
        url_match = re.findall(r'https?://[^\s|]+', line)
        name_match = re.match(r'\|\s*([^|]+?)\s*\|', line)

        if url_match:
            url = url_match[0]
            # Clean trailing punctuation
            url = url.rstrip("/.,;:)!?")
            # Keep only http/https URLs
            if url.startswith("http"):
                name = name_match.group(1).strip() if name_match else url.split("//")[-1].split("/")[0]
                # Determine source type
                s_type = detect_source_type(url, name)
                # Determine language
                lang = detect_language(current_country, url, name)
                
                sources.append({
                    "name": name,
                    "url": url,
                    "country": current_country,
                    "region": "europe",
                    "type": s_type,
                    "language": lang,
                    "section": current_section,
                })

    return sources


def detect_source_type(url: str, name: str) -> str:
    """Detect source type from URL and name context."""
    name_lower = name.lower()
    url_lower = url.lower()
    
    think_tank_keywords = [
        "think tank", "institute", "foundation", "center", "centre",
        "council", "research", "elcano", "chatham", "rusi", "iiss",
        "swp", "dgap", "ispi", "iai", "ceps", "nupi", "ffi", "ui",
        "foi", "diis", "fiia", "icds", "liia", "eesc", "amo", "hiia",
        "eliamep", "cidob", "hcss", "globsec", "cer", "bruegel",
        "nato", "egmont", "hybridcoe", "jamestown"
    ]
    
    gov_keywords = [
        "gov.", "government", "ministry", "ministero", "ministerie",
        "ministerium", "bnd", "bfv", "bka", "bsi", "dgse", "dgsi",
        "aivd", "mivd", "nctv", "carabinieri", "guardia", "policja",
        "police", "defensa", "defence", "defense", "difesa",
    ]
    
    for kw in think_tank_keywords:
        if kw in name_lower or kw in url_lower:
            return "think_tank"
    
    for kw in gov_keywords:
        if kw in name_lower or kw in url_lower:
            return "gov"
    
    return "news"


def detect_language(country: str, url: str, name: str) -> str:
    """Detect source language based on country and URL patterns."""
    lang_map = {
        "france": "fr",
        "germany": "de",
        "italy": "it",
        "spain": "es",
        "netherlands": "nl",
        "belgium": "nl",
        "switzerland": "de",
        "austria": "de",
        "portugal": "pt",
        "poland": "pl",
        "czech-republic": "cs",
        "slovakia": "sk",
        "hungary": "hu",
        "romania": "ro",
        "bulgaria": "bg",
        "slovenia": "sl",
        "croatia": "hr",
        "serbia": "sr",
        "bosnia-herzegovina": "bs",
        "kosovo": "sq",
        "north-macedonia": "mk",
        "montenegro": "sr",
        "albania": "sq",
        "estonia": "et",
        "latvia": "lv",
        "lithuania": "lt",
        "sweden": "sv",
        "norway": "no",
        "denmark": "da",
        "finland": "fi",
        "iceland": "is",
        "ukraine": "uk",
        "belarus": "be",
        "moldova": "ro",
        "russia": "ru",
        "georgia": "ka",
        "armenia": "hy",
        "azerbaijan": "az",
        "malta": "mt",
        "cyprus": "el",
        "greece": "el",
    }
    
    # English-language sources get "en"
    en_indicators = [
        "english", "en/", "bbc.com", "theguardian", "thetimes", "ft.com",
        "telegraph", "independent", "economist", "spectator", "sky.com",
        "itv.com", "channel4.com", "bureauinvestigates", "opendemocracy",
        "declassifieduk", "bylinetimes", "tortoisemedia", "private-eye",
        "janes.com", "ukdefencejournal", "forcesnews.com", "wavellroom",
        "bfpg.co.uk", "instituteforgovernment", "institute.global",
        "kyivindependent", "meduza.io/en", "theins." if "theins." in url else "",
        "novayagazeta.eu", "themoscowtimes", "russiamatters", "wartranslated",
        "understandingwar", "criticalthreats", "dfrlab.org", "info-res.org",
        "occrp.org", "bellingcat", "balkaninsight", "euobserver",
        "politico.eu", "euractiv.com", "euronews.com", "brusselstimes",
        "eubusiness.com", "eurointelligence", "bruegel.org", "voxeurop.eu",
        "theparliamentmagazine", "cer.eu", "eureporter.co", "moderndiplomacy",
        "iiss.org", "rusi.org", "chathamhouse", "ecfr.eu", "carnegie",
        "gmfus.org", "cepa.org", "iss.europa.eu", "ndc.nato.int",
        "frstrategie.org", "ifri.org", "iris-france.org",
        "swp-berlin", "dgap.org", "ispionline.it", "iai.it",
        "realinstitutoelcano", "clingendael.org", "osw.waw.pl", "pism.pl",
        "globsec.org", "ceps.eu", "egmontinstitute", "nupi.no", "ffi.no",
        "ui.se", "foi.se", "diis.dk", "fiia.fi", "icds.ee", "liia.lv",
        "eesc.lt", "amo.cz", "hiia.hu", "eliamep.gr", "cidob.org",
        "hcss.nl", "henryjacksonsociety", "geostrategy.org.uk", "jamestown.org",
        "icij.org", "eic.network", "journalismfund.eu", "vsquare.org",
        "forensic-architecture", "thereckoningproject", "disclose.ngo",
        "lighthousereports.com", "investigate-europe.eu",
        "nato.int", "shape.nato.int", "ccdcoe.org", "stratcomcoe.org",
        "eeas.europa.eu", "euvsdisinfo.eu", "hybridcoe.fi", "eda.europa.eu",
        "europol.europa.eu", "frontex.europa.eu", "coe.int", "osce.org",
        "afp.com/en", "apnews.com", "dpa.com", "ansa.it", "efe.com",
        "pap.pl", "tt.se", "ntb.no", "ritzau.dk", "stt.fi",
        "bbc.com", "dw.com", "france24.com", "tv5monde.com",
    ]
    for indicator in en_indicators:
        if indicator and indicator in url.lower():
            return "en"
    
    # Belgium has both FR and NL
    if country == "belgium":
        if "/fr/" in url.lower() or "lesoir" in url or "lalibre" in url or "rtbf" in url or "medor" in url:
            return "fr"
        return "nl"
    
    # Switzerland has DE, FR, IT
    if country == "switzerland":
        if "letemps" in url or "rts.ch" in url:
            return "fr"
        if "cdt.ch" in url or "rsi.ch" in url:
            return "it"
        if "swissinfo" in url:
            return "en"
        return "de"
    
    return lang_map.get(country, "en")


def try_rss_feeds(base_url: str, source_name: str) -> list[dict]:
    """Try to discover RSS feeds for a given base URL."""
    results = []
    attempted = set()
    
    parsed = urllib.parse.urlparse(base_url)
    base_scheme = parsed.scheme or "https"
    base_netloc = parsed.netloc or parsed.path.split("/")[0]
    base = f"{base_scheme}://{base_netloc}"
    
    # Try the URL itself first (some sites serve RSS at their main URL)
    candidates = [base_url] + [base + path for path in RSS_PATHS]
    
    for url in candidates:
        if url in attempted:
            continue
        attempted.add(url)
        
        try:
            log.debug(f"  Testing: {url}")
            feed = feedparser.parse(url)
            if feed.bozo and feed.bozo_exception:
                err = str(feed.bozo_exception)
                if "timeout" in err.lower() or "Connection" in err:
                    continue  # Skip on connection error
                if "not well-formed" in err or "XML" in err:
                    continue  # Not a valid feed
            
            entries = getattr(feed, 'entries', [])
            if entries:
                feed_title = feed.feed.get('title', '') if hasattr(feed, 'feed') else ''
                log.info(f"  ✓ VALID FEED: {url} ({len(entries)} entries) - {feed_title}")
                results.append({
                    "feed_url": url,
                    "source_name": source_name,
                    "title": feed_title,
                    "entry_count": len(entries),
                    "feed_type": feed.get('version', 'unknown'),
                })
        except Exception as e:
            log.debug(f"  ✗ Error testing {url}: {e}")
            continue
    
    return results


def validate_single_source(source: dict) -> dict | None:
    """Validate a single source for RSS feeds."""
    try:
        feeds = try_rss_feeds(source["url"], source["name"])
        if feeds:
            return {
                "name": source["name"],
                "url": source["url"],
                "country": source["country"],
                "region": source["region"],
                "type": source["type"],
                "language": source["language"],
                "feeds": feeds,
                "status": "ok",
                "tested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        else:
            return {
                "name": source["name"],
                "url": source["url"],
                "country": source["country"],
                "region": source["region"],
                "type": source["type"],
                "language": source["language"],
                "feeds": [],
                "status": "no_feed",
                "tested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
    except Exception as e:
        return {
            "name": source["name"],
            "url": source["url"],
            "country": source["country"],
            "region": source["region"],
            "type": source["type"],
            "language": source["language"],
            "feeds": [],
            "status": "error",
            "error": str(e),
            "tested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }


def main():
    log.info("=" * 60)
    log.info("Europe OSINT Source → RSS Feed Scanner")
    log.info("=" * 60)
    
    # Step 1: Extract all sources from markdown
    log.info("\n[1/5] Extracting sources from markdown...")
    sources = extract_sources(SOURCES_FILE)
    log.info(f"  Found {len(sources)} unique sources with URLs")
    
    # Deduplicate by URL
    seen_urls = set()
    unique_sources = []
    for s in sources:
        if s["url"] not in seen_urls:
            seen_urls.add(s["url"])
            unique_sources.append(s)
    log.info(f"  {len(unique_sources)} unique URLs after dedup")
    
    # Print summary by country
    by_country = {}
    for s in unique_sources:
        c = s["country"]
        by_country[c] = by_country.get(c, 0) + 1
    for c, n in sorted(by_country.items(), key=lambda x: -x[1]):
        log.info(f"    {c}: {n} sources")
    
    # Step 2: Validate RSS feeds for each source
    log.info(f"\n[2/5] Testing RSS feeds for {len(unique_sources)} sources...")
    log.info(f"  (timeout: {TIMEOUT}s per feed, up to {len(RSS_PATHS)} paths per source)")
    
    socket.setdefaulttimeout(TIMEOUT)
    
    results = []
    tested_count = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(validate_single_source, s): s for s in unique_sources}
        for future in as_completed(futures):
            tested_count += 1
            s = futures[future]
            try:
                result = future.result()
                results.append(result)
                feed_count = len(result.get("feeds", []))
                status_icon = "✓" if feed_count > 0 else "✗"
                if tested_count % 20 == 0:
                    log.info(f"  [{tested_count}/{len(unique_sources)}] {s['country']}: {feed_count} feeds found for {s['name']}")
            except Exception as e:
                log.error(f"  Error testing {s['name']} ({s['url']}): {e}")
                results.append({
                    "name": s["name"],
                    "url": s["url"],
                    "country": s["country"],
                    "region": s["region"],
                    "type": s["type"],
                    "language": s["language"],
                    "feeds": [],
                    "status": "exception",
                    "error": str(e),
                })
    
    # Step 3: Separate validated vs non-validated
    log.info(f"\n[3/5] Processing results...")
    validated = [r for r in results if r.get("feeds")]
    no_feed = [r for r in results if not r.get("feeds")]
    
    log.info(f"  Validated feeds found: {len(validated)}")
    log.info(f"  No feed found: {len(no_feed)}")
    
    # Print validated feeds
    log.info(f"\n  --- Validated Feeds ({len(validated)}) ---")
    for r in sorted(validated, key=lambda x: (x["country"], x["name"])):
        for f in r["feeds"]:
            log.info(f"  [{r['country']:20s}] {r['name']:35s} → {f['feed_url']}")
    
    # Step 4: Save validated feeds
    log.info(f"\n[4/5] Saving outputs...")
    OUTPUT_FEEDS.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FEEDS, "w") as f:
        json.dump({
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_sources": len(unique_sources),
            "validated_feeds": len(validated),
            "no_feed": len(no_feed),
            "sources": results,
        }, f, indent=2, ensure_ascii=False)
    log.info(f"  Saved: {OUTPUT_FEEDS}")
    
    # Generate sources_tested.json compatible catalog entries
    catalog_entries = []
    for r in results:
        if r.get("feeds"):
            for f in r["feeds"]:
                entry = {
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
                }
                catalog_entries.append(entry)
        else:
            entry = {
                "name": r["name"],
                "url": r["url"],
                "status": r.get("status", "error"),
                "code": 0,
                "tested_at": r["tested_at"],
                "region": "europe",
                "source_region": r["country"],
                "language": r["language"],
                "type": r["type"],
            }
            catalog_entries.append(entry)
    
    # Load existing catalog and merge
    if CATALOG_PATH.exists():
        existing = json.loads(CATALOG_PATH.read_text())
    else:
        existing = []
    
    # Update/add entries
    existing_urls = {e.get("url", "") for e in existing}
    new_count = 0
    update_count = 0
    for entry in catalog_entries:
        if entry["url"] not in existing_urls:
            existing.append(entry)
            new_count += 1
        else:
            # Update existing entry
            for i, e in enumerate(existing):
                if e["url"] == entry["url"]:
                    existing[i] = entry
                    update_count += 1
                    break
    
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CATALOG_PATH, "w") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    log.info(f"  Updated: {CATALOG_PATH} ({new_count} new, {update_count} updated)")
    
    # Step 5: Generate LOCAL_LANGUAGE_FEEDS snippet for collect.py
    log.info(f"\n[5/5] Generating LOCAL_LANGUAGE_FEEDS additions...")
    
    # The key ~20 multilingual Europe sources to add
    key_europe_feeds = [
        ("Politico Europe", "https://www.politico.eu/", "en", ("B", 2)),
        ("EUobserver", "https://euobserver.com/", "en", ("B", 2)),
        ("Euractiv", "https://www.euractiv.com/", "en", ("B", 2)),
        ("Euronews", "https://www.euronews.com/", "en", ("B", 2)),
        ("Balkan Insight", "https://balkaninsight.com/", "en", ("B", 2)),
        ("VSquare", "https://vsquare.org/", "en", ("B", 2)),
        ("OCCRP", "https://www.occrp.org/", "en", ("B", 2)),
        ("Bellingcat", "https://www.bellingcat.com/", "en", ("B", 2)),
        ("OSW (Centre for Eastern Studies)", "https://www.osw.waw.pl/", "en", ("A", 2)),
        ("Gazeta Wyborcza", "https://wyborcza.pl/", "pl", ("B", 2)),
        ("Denník N", "https://dennikn.sk/", "sk", ("B", 2)),
        ("Telex", "https://telex.hu/", "hu", ("B", 2)),
        ("Postimees", "https://www.postimees.ee/", "et", ("B", 2)),
        ("ERR News", "https://news.err.ee/", "en", ("B", 2)),
        ("Dagens Nyheter", "https://www.dn.se/", "sv", ("B", 2)),
        ("Aftenposten", "https://www.aftenposten.no/", "no", ("B", 2)),
        ("Politiken", "https://politiken.dk/", "da", ("B", 2)),
        ("Helsingin Sanomat", "https://www.hs.fi/", "fi", ("B", 2)),
        ("Kyiv Independent", "https://kyivindependent.com/", "en", ("B", 2)),
        ("Meduza", "https://meduza.io/", "ru", ("B", 2)),
    ]
    
    # Try to find actual RSS feeds for these key sources
    key_feed_snippet = []
    source_names_seen = set()
    
    for name, url, lang, adm in key_europe_feeds:
        # Find matching validated feeds
        matching = [r for r in results if r["name"] == name]
        if matching and matching[0].get("feeds"):
            feed = matching[0]["feeds"][0]  # First feed
            feed_url = feed["feed_url"]
            key_feed_snippet.append(f'    ("{name}", "{feed_url}", "{lang}", {adm}),')
            source_names_seen.add(name)
            log.info(f"  ✓ {name:35s} → {feed_url}")
        else:
            # Use the base URL as fallback - collect.py will filter non-feed URLs
            key_feed_snippet.append(f'    ("{name}", "{url}", "{lang}", {adm}),')
            log.info(f"  ? {name:35s} → {url} (no feed found, using base URL)")
    
    # Generate the Python code snippet
    snippet = """    # --- EUROPE LOCAL-LANGUAGE / REGIONAL FEEDS (added 2026-05-27) ---
    # 20 key multilingual Europe sources for multi-language collection.
    # Added via Europe OSINT feed scanner.
""" + "\n".join(key_feed_snippet) + "\n"

    # Save snippet for manual insertion
    snippet_path = Path("config/sources/europe-local-language-feeds-snippet.txt")
    snippet_path.write_text(snippet)
    log.info(f"  Saved LOCAL_LANGUAGE_FEEDS snippet to: {snippet_path}")
    
    # Summary
    log.info("\n" + "=" * 60)
    log.info("SUMMARY")
    log.info("=" * 60)
    log.info(f"  Total sources processed: {len(unique_sources)}")
    log.info(f"  Validated RSS feeds found: {len(validated)}")
    log.info(f"  No RSS feed: {len(no_feed)}")
    log.info(f"  Catalog entries (sources_tested.json): {len(catalog_entries)}")
    log.info(f"  Key Europe feeds for LOCAL_LANGUAGE_FEEDS: {len(key_feed_snippet)}")
    log.info(f"\nOutputs:")
    log.info(f"  {OUTPUT_FEEDS}")
    log.info(f"  {CATALOG_PATH} (updated)")
    log.info(f"  {snippet_path}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
