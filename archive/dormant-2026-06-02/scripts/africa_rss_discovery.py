#!/usr/bin/env python3
"""
Africa OSINT Source RSS Discovery & Validation.

Parses the Africa OSINT source directory markdown file, discovers RSS feeds
for each source, validates them with feedparser, and saves working feeds
to the Philby source registry.

Usage:
    python3 scripts/africa_rss_discovery.py [--limit N] [--quick]
"""

import argparse
import json
import pathlib
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Optional

import feedparser

REPO = pathlib.Path(__file__).resolve().parent.parent
SOURCES_MD = REPO / "config" / "sources" / "africa-osint-sources.md"
OUTPUT_JSON = REPO / "config" / "sources" / "africa-feeds-validated.json"
TESTED_JSON = REPO / "analyst" / "meta" / "sources_tested.json"
SOURCES_JSON = REPO / "analyst" / "meta" / "sources.json"

TIMEOUT = 10  # seconds for feed fetch

# Common RSS feed paths to try
RSS_PATHS = [
    "/feed/",
    "/rss/",
    "/feed.xml",
    "/rss.xml",
    "/feeds/posts/default",
    "/feeds/posts/default?alt=rss",
    "/index.xml",
    "/atom.xml",
    "/news/rss/",
    "/?feed=rss2",
    "/?format=feed",
    "/en/feed/",
    "/fr/feed/",
    "/ar/feed/",
    "/pt/feed/",
    "/news/feed/",
    "/latest/feed/",
    "/articles/feed/",
    "/blog/feed/",
    "/blog/rss/",
    "/rss/news",
    "/rss/top",
    "/rss/latest",
    "/api/rss",
    "/content/feed",
    "/en/rss/",
    "/ar/rss/",
]

# Known feed URLs for major sources (pre-validated)
KNOWN_RSS = {
    "bbc.com": "https://feeds.bbci.co.uk/news/world/africa/rss.xml",
    "dw.com": "https://rss.dw.com/rdf/rss-en-africa",
    "voanews.com": "https://www.voanews.com/api/zicqmrqevqvtcicy?format=rss",
    "aljazeera.com": "https://www.aljazeera.com/xml/rss/all.xml",
    "france24.com": "https://www.france24.com/en/africa/rss",
    "theafricareport.com": "https://www.theafricareport.com/feed/",
    "issafrica.org": "https://issafrica.org/rss.xml",
    "acleddata.com": "https://acleddata.com/feed/",
    "humanglemedia.com": "https://humanglemedia.com/feed/",
    "premiumtimesng.com": "https://www.premiumtimesng.com/feed",
    "dailymaverick.co.za": "https://www.dailymaverick.co.za/feed/",
    "mg.co.za": "https://mg.co.za/feed/",
    "news24.com": "https://www.news24.com/feeds/rss",
    "amabhungane.org": "https://amabhungane.org/feed/",
    "africacenter.org": "https://africacenter.org/feed/",
    "semafor.com": "https://www.semafor.com/feed",
    "chinaglobalsouth.com": "https://chinaglobalsouth.com/feed/",
    "african.business": "https://african.business/feed/",
    "africanarguments.org": "https://africanarguments.org/feed/",
    "africauncensored.online": "https://africauncensored.online/feed/",
    "thecontinent.org": "https://thecontinent.org/feed.xml",
    "newafricanmagazine.com": "https://newafricanmagazine.com/feed/",
    "zammagazine.com": "https://www.zammagazine.com/feed/",
    "reliefweb.int": "https://reliefweb.int/rss",
    "punchng.com": "https://punchng.com/feed/",
    "dailytrust.com": "https://dailytrust.com/feed/",
    "thisdaylive.com": "https://www.thisdaylive.com/feed/",
    "vanguardngr.com": "https://www.vanguardngr.com/feed/",
    "guardian.ng": "https://guardian.ng/feed/",
    "nation.africa": "https://nation.africa/kenya/-/widgets/rss",
    "standardmedia.co.ke": "https://www.standardmedia.co.ke/rss/",
    "the-star.co.ke": "https://www.the-star.co.ke/feed/",
    "businessdailyafrica.com": "https://www.businessdailyafrica.com/feed/",
    "citizen.digital": "https://www.citizen.digital/feed/",
    "addisstandard.com": "https://addisstandard.com/feed/",
    "thereporterethiopia.com": "https://www.thereporterethiopia.com/feed/",
    "hiiraan.com": "https://www.hiiraan.com/feed/",
    "garoweonline.com": "https://www.garoweonline.com/feed/",
    "goobjoog.com": "https://goobjoog.com/feed/",
    "radiookapi.net": "https://www.radiookapi.net/rss.xml",
    "actualite.cd": "https://actualite.cd/feed/",
    "kivusecurity.org": "https://kivusecurity.org/feed/",
    "caboligado.com": "https://caboligado.com/feed/",
    "zitamar.com": "https://zitamar.com/feed/",
    "cartamz.com": "https://cartamz.com/feed/",
    "legraph.com.ng": "https://www.legraph.com.ng/feed/",
    "iwacu-burundi.org": "https://www.iwacu-burundi.org/feed/",
    "radiotamazuj.org": "https://www.radiotamazuj.org/feed/",
    "eyeradio.org": "https://eyeradio.org/feed/",
    "dabangasudan.org": "https://www.dabangasudan.org/feed/",
    "sudantribune.com": "https://sudantribune.com/feed/",
    "libyaherald.com": "https://libyaherald.com/feed/",
    "madamasr.com": "https://www.madamasr.com/en/feed/",
    "thesentry.org": "https://thesentry.org/feed/",
    "occrp.org": "https://www.occrp.org/en/feed",
    "africanews.com": "https://www.africanews.com/rss/",
    "jeuneafrique.com": "https://www.jeuneafrique.com/feed/",
    "rfi.fr": "https://www.rfi.fr/fr/afrique/rss",
    "lefaso.net": "https://lefaso.net/rss.xml",
    "burkina24.com": "https://burkina24.com/feed/",
    "fij.ng": "https://fij.ng/feed/",
    "thecable.ng": "https://www.thecable.ng/feed/",
    "tesfanews.net": "https://tesfanews.net/feed/",
    "adf-magazine.com": "https://adf-magazine.com/feed/",
    "guardianpostcameroon.com": "https://www.theguardianpostcameroon.com/feed/",
    "journalducameroun.com": "https://www.journalducameroun.com/feed/",
    "myjoyonline.com": "https://www.myjoyonline.com/feed/",
    "3news.com": "https://3news.com/feed/",
    "citinewsroom.com": "https://citinewsroom.com/feed/",
    "monitor.co.ug": "https://www.monitor.co.ug/feed/",
    "observer.ug": "https://observer.ug/feed/",
    "newvision.co.ug": "https://www.newvision.co.ug/feed/",
    "newtimes.co.rw": "https://www.newtimes.co.rw/feed/",
    "igihe.com": "https://en.igihe.com/feed/",
}


def parse_sources_from_md() -> list[dict]:
    """Parse the Africa OSINT source directory markdown file."""
    text = SOURCES_MD.read_text()
    sources = []
    
    current_section = "Pan-African"
    current_region = "pan_african"
    current_country = ""
    
    lines = text.split("\n")
    for line in lines:
        # Detect country headers with flag emoji
        country_match = re.match(r'^##\s+\W{2}\s+([A-Z\s-]+?)(?:\s+|$)', line)
        if country_match and not re.match(r'^##\s+COUNTRY|SECTION|PAN', line, re.I):
            current_country = country_match.group(1).strip()
            current_section = f"Country: {current_country}"
            continue
        
        # Section headers (non-country)
        section_match = re.match(r'^##\s+([A-Z\s/&-]+)', line)
        if section_match and line.count('|') < 2:
            section_name = section_match.group(1).strip()
            current_section = section_name
            if "PAN" in section_name.upper():
                current_region = "pan_african"
            elif "MARITIME" in section_name.upper() or "GULF" in section_name.upper():
                current_region = "maritime"
            elif "MIGRATION" in section_name.upper() or "HUMANITARIAN" in section_name.upper():
                current_region = "humanitarian"
            elif "INVESTIGATIVE" in section_name.upper() or "SECURITY" in section_name.upper() or "THINK" in section_name.upper():
                current_region = "pan_african"
        
        # Inline country entries like: ## 🇹🇩 CHAD: Source1 (url), Source2 (url)
        if ':' in line and re.match(r'^##\s*\W{2}\s+[A-Z]', line):
            inline_parts = line.split(':', 1)[1] if ':' in line else ''
            if inline_parts:
                parts = re.findall(r'([^(]+)\(([^)]+)\)', inline_parts)
                for name, url in parts:
                    name = name.strip().rstrip(',').strip()
                    url = url.strip()
                    if url.startswith('http'):
                        sources.append({
                            "name": name,
                            "url": url.rstrip('/'),
                            "language": _detect_language(url, name),
                            "country": current_country,
                            "region": _get_region_from_country(current_country),
                            "section": current_section,
                            "type": "news",
                            "admirality": "B2"
                        })
            continue
        
        # Regular table row (| Source | Notes | URL |)
        cells = [c.strip() for c in line.split('|')[1:-1]]
        if line.startswith('|') and len(cells) >= 2 and not any(h in cells[0] for h in ['Source', '---', 'Notes', 'Coverage']):
            name = cells[0]
            url = ''
            # URL is typically in the last cell
            if len(cells) >= 3:
                last_cell = cells[-1]
                if last_cell.startswith('http'):
                    url = last_cell
                elif len(cells) >= 4 and cells[-2].startswith('http'):
                    url = cells[-2]
            
            # Parse multi-language URLs like: AR: https://... | FR: https://...
            multi_urls = re.findall(r'(?:EN|FR|PT|AR|SW|AM|HA|Mult)?\s*:?\s*(https?://[^\s|]+)', line)
            if not url and multi_urls:
                url = multi_urls[0]
            
            context_cell = cells[1] if len(cells) > 2 else ''
            
            if url and url.startswith('http'):
                url = url.rstrip('/')
                sources.append({
                    "name": name.strip(),
                    "url": url,
                    "language": _detect_language(url, context_cell),
                    "country": current_country,
                    "region": _get_region_from_country(current_country) if current_country else ("pan_african" if current_region == "pan_african" else current_region),
                    "section": current_section,
                    "type": _detect_type(name, current_section),
                    "admirality": "B2"
                })
    
    return sources


def _detect_language(url: str, context: str = "") -> str:
    """Detect language from URL or context."""
    url_lower = url.lower()
    if any(d in url_lower for d in ['.fr/', '/fr/', 'france', 'jeuneafrique', 'lemonde']):
        return "FR"
    if any(d in url_lower for d in ['.pt/', 'jornal', 'angop', 'noticias']):
        return "PT"
    if any(d in url_lower for d in ['.ar/', '/ar/', 'al-', 'akhbar']):
        return "AR"
    ctx_lower = context.lower()
    if '[fr]' in ctx_lower or 'french' in ctx_lower:
        return "FR"
    if '[pt]' in ctx_lower or 'portuguese' in ctx_lower:
        return "PT"
    if '[ar]' in ctx_lower or 'arabic' in ctx_lower:
        return "AR"
    return "EN"


def _detect_type(name: str, section: str) -> str:
    """Detect source type."""
    name_lower = name.lower()
    section_lower = section.lower()
    if 'think tank' in section_lower or 'think' in name_lower:
        return "thinktank"
    if 'government' in section_lower or 'military' in section_lower or 'police' in section_lower:
        return "gov"
    if 'investigative' in section_lower:
        return "investigative"
    if 'tv' in section_lower or 'radio' in section_lower:
        return "media"
    if 'wire' in name_lower or 'agency' in name_lower or 'agence' in name_lower:
        return "wire"
    return "news"


def _get_region_from_country(country: str) -> str:
    """Map country to region."""
    north_africa = ["Egypt", "Morocco", "Algeria", "Tunisia", "Libya", "Sudan", "Mauritania"]
    for c in north_africa:
        if c in country:
            return "north_africa"
    return "sub_saharan_africa"


def discover_rss_urls(base_url: str) -> list[str]:
    """Try to discover RSS feeds for a given URL."""
    parsed = urllib.parse.urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    
    # 1. Check known RSS feeds by domain
    for domain, rss_url in KNOWN_RSS.items():
        if domain in parsed.netloc:
            return [rss_url]
    
    # 2. Try common paths
    candidates = [f"{base}{path}" for path in RSS_PATHS]
    candidates.append(base_url)  # Also try the page itself
    
    return candidates


def fetch_rss(url: str, timeout: int = TIMEOUT) -> tuple[bool, str, Optional[int], str]:
    """Fetch and parse a URL as RSS. Returns (success, feed_url, entry_count, error_msg)."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; PhilbyCollector/1.0)"},
        )
        resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        content = resp.read()
        
        feed = feedparser.parse(content)
        if feed.bozo and feed.bozo_exception:
            return False, url, None, f"Feed parse error: {feed.bozo_exception}"
        
        if feed.entries:
            return True, url, len(feed.entries), ""
        elif feed.feed and hasattr(feed.feed, 'title') and feed.feed.title:
            return True, url, 0, ""
        else:
            return False, url, None, "No feed data"
            
    except urllib.error.HTTPError as e:
        return False, url, None, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return False, url, None, f"URLError: {e.reason}"
    except Exception as e:
        return False, url, None, f"Error: {str(e)[:80]}"


def test_source_rss(source: dict) -> Optional[dict]:
    """Test a source for working RSS feeds."""
    url = source["url"]
    if not url.startswith("http"):
        return None
    
    candidates = discover_rss_urls(url)
    
    for feed_url in candidates:
        success, final_url, count, err = fetch_rss(feed_url)
        if success:
            return {
                "name": source["name"],
                "url": url,
                "feed_url": final_url,
                "language": source["language"],
                "country": source.get("country", ""),
                "region": source.get("region", "sub_saharan_africa"),
                "type": source.get("type", "news"),
                "admirality": source.get("admirality", "B2"),
                "entry_count": count,
                "status": "ok",
                "tested_at": datetime.now(timezone.utc).isoformat()
            }
    
    return None


def save_to_philby_registry(feeds: list[dict]):
    """Save validated feeds to Philby's source registry."""
    # 1. Save to africa-feeds-validated.json
    region_coverage = {}
    for f in feeds:
        r = f.get("region", "unknown")
        region_coverage[r] = region_coverage.get(r, 0) + 1
    
    with open(OUTPUT_JSON, 'w') as f:
        json.dump({
            "generated": datetime.now(timezone.utc).isoformat(),
            "source_count": len(feeds),
            "region_coverage": region_coverage,
            "feeds": feeds
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(feeds)} validated feeds to {OUTPUT_JSON}")
    
    # 2. Append to sources_tested.json
    timestamp = datetime.now(timezone.utc).isoformat()
    tested_entries = []
    for f in feeds:
        tested_entries.append({
            "name": f["name"],
            "url": f["url"],
            "feed_url": f.get("feed_url", f["url"]),
            "status": "ok",
            "code": 200,
            "tested_at": timestamp,
            "region": f.get("region", "sub_saharan_africa"),
            "country": f.get("country", ""),
            "language": f.get("language", "EN"),
            "type": f.get("type", "news")
        })
    
    # Load existing or create new
    existing = []
    if TESTED_JSON.exists():
        try:
            existing = json.loads(TESTED_JSON.read_text())
        except (json.JSONDecodeError,):
            pass
    
    # Deduplicate by URL
    existing_urls = {e["url"] for e in existing}
    new_entries = [e for e in tested_entries if e["url"] not in existing_urls]
    existing.extend(new_entries)
    
    TESTED_JSON.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
    print(f"✅ Appended {len(new_entries)} new entries to {TESTED_JSON} (total: {len(existing)})")
    
    # 3. Add to sources.json durable_sources if they're new
    if SOURCES_JSON.exists():
        try:
            sources_data = json.loads(SOURCES_JSON.read_text())
            durable = sources_data.get("durable_sources", [])
            durable_urls = {s["url"] for s in durable}
            
            new_sources = []
            for f in feeds:
                if f["url"] not in durable_urls:
                    new_sources.append({
                        "name": f["name"],
                        "type": f.get("type", "news").title(),
                        "focus": f"Africa OSINT: {f['name']} ({f.get('country', 'Pan-African')})",
                        "url": f["url"],
                        "feed_url": f.get("feed_url", ""),
                        "signal_level": "High",
                        "region": f.get("region", "sub_saharan_africa"),
                        "country": f.get("country", ""),
                        "language": f.get("language", "EN"),
                        "discovered": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    })
            
            if new_sources:
                sources_data["durable_sources"].extend(new_sources)
                SOURCES_JSON.write_text(json.dumps(sources_data, indent=2, ensure_ascii=False))
                print(f"✅ Added {len(new_sources)} new sources to {SOURCES_JSON}")
            else:
                print(f"ℹ️  0 new sources to add to {SOURCES_JSON} (all already in registry)")
        except (json.JSONDecodeError,) as e:
            print(f"⚠️  Warning: Could not parse {SOURCES_JSON}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Africa OSINT RSS Discovery & Validation")
    parser.add_argument("--limit", type=int, default=100, help="Max sources to test")
    parser.add_argument("--quick", action="store_true", help="Test only from known RSS list")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Africa OSINT RSS Discovery & Validation")
    print("=" * 60)
    
    # Step 1: Parse sources
    print(f"\n[1/4] Parsing sources from {SOURCES_MD}...")
    sources = parse_sources_from_md()
    print(f"  Found {len(sources)} source entries")
    
    # Step 2: Filter for priority sources
    if args.quick:
        print(f"\n[2/4] Quick mode: filtering to known-RSS sources...")
        filtered = []
        for s in sources:
            parsed = urllib.parse.urlparse(s["url"])
            if any(d in parsed.netloc for d in KNOWN_RSS):
                filtered.append(s)
        print(f"  {len(filtered)} sources with known RSS feeds")
    else:
        print(f"\n[2/4] Ranking top {min(len(sources), args.limit)} priority sources...")
        
        def priority(source):
            score = 0
            url = source["url"]
            region = source.get("region", "")
            country = source.get("country", "")
            
            if region == "pan_african":
                score += 100
            if region == "north_africa":
                score += 80
            conflict_countries = ["Nigeria", "DRC", "Sudan", "Somalia", "Mali",
                                  "Burkina Faso", "Niger", "Ethiopia", "Libya", "Mozambique"]
            for cc in conflict_countries:
                if cc in country:
                    score += 90
            major = ["South Africa", "Kenya", "Egypt", "Morocco", "Ghana", "Angola"]
            for m in major:
                if m in country:
                    score += 50
            if "investigative" in source.get("type", ""):
                score += 40
            for domain in KNOWN_RSS:
                if domain in url:
                    score += 30
            return -score
        
        sources.sort(key=priority)
        filtered = sources[:args.limit]
    
    print(f"  Testing {len(filtered)} sources...")
    
    # Step 3: Test RSS feeds
    print(f"\n[3/4] Testing RSS feeds (timeout: {TIMEOUT}s each)...")
    print(f"  {'='*50}")
    
    working_feeds = []
    failed = 0
    for i, source in enumerate(filtered):
        result = test_source_rss(source)
        if result:
            working_feeds.append(result)
            print(f"  ✅ [{i+1}/{len(filtered)}] {source['name'][:40]:40s} → {result['feed_url'][:55]}")
        else:
            failed += 1
            if failed <= 5 or (i+1) % 10 == 0:
                print(f"  ❌ [{i+1}/{len(filtered)}] {source['name'][:40]:40s} no RSS")
            elif failed == 6:
                print(f"  ... (hiding further failures, showing every 10th)")
    
    print(f"\n  Results: {len(working_feeds)}/{len(filtered)} sources have working RSS feeds")
    
    # Step 4: Save results
    print(f"\n[4/4] Saving results...")
    save_to_philby_registry(working_feeds)
    
    # Summary
    regions = {}
    types = {}
    langs = {}
    for f in working_feeds:
        r = f.get("region", "unknown")
        regions[r] = regions.get(r, 0) + 1
        t = f.get("type", "unknown")
        types[t] = types.get(t, 0) + 1
        l = f.get("language", "unknown")
        langs[l] = langs.get(l, 0) + 1
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"  Total sources parsed:   {len(sources)}")
    print(f"  Sources tested:         {len(filtered)}")
    print(f"  Working RSS feeds:      {len(working_feeds)}")
    print(f"  Region coverage:")
    for r, c in sorted(regions.items(), key=lambda x: -x[1]):
        print(f"    {r:25s}: {c}")
    print(f"  Type breakdown:")
    for t, c in sorted(types.items(), key=lambda x: -x[1]):
        print(f"    {t:25s}: {c}")
    print(f"  Language breakdown:")
    for l, c in sorted(langs.items(), key=lambda x: -x[1]):
        print(f"    {l:25s}: {c}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
