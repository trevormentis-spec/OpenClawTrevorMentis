#!/usr/bin/env python3
"""
GDELT Collector — queries GDELT 2.0 DOC API for targeted geopolitical themes.
Outputs structured JSON to exports/gdelt/YYYY-MM-DD.json.

Usage:
    python3 gdelt_collector.py                        # save to exports/gdelt/
    python3 gdelt_collector.py --stdout               # print to stdout
    python3 gdelt_collector.py --stdout --date 2026-06-01   # specific date

Rate limit: GDELT requires >= 5s between requests. This script uses 6s.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

# ── 10 targeted queries covering major regions/themes ──
QUERIES = {
    "iran_israel_hormuz": (
        'Iran OR Hormuz OR IRGC OR "Strait of Hormuz" OR Hezbollah OR "Iran war"'
    ),
    "ukraine_russia": (
        'Ukraine OR Russia OR Donbas OR Crimea OR "Zaporizhzhia" OR "shadow fleet" OR NATO'
    ),
    "taiwan_china_scs": (
        'Taiwan OR "South China Sea" OR Spratly OR "Nine-Dash Line" OR "PLA" OR "Chinese military"'
    ),
    "africa_sahel": (
        'Africa OR Sahel OR Mali OR Burkina OR Niger OR Mozambique OR Sudan OR Ethiopia'
    ),
    "latin_america": (
        'Mexico OR "Latin America" OR Brazil OR Colombia OR Venezuela OR Ecuador OR Argentina'
    ),
    "cyber_intel": (
        'cyberattack OR ransomware OR "state-backed" OR hacking OR data breach OR CVE OR APT'
    ),
    "energy_commodities": (
        'oil OR brent OR crude OR energy OR commodity OR supply OR LNG OR gas OR shipping'
    ),
    "great_power": (
        '"great power" OR "US-China" OR "US-Russia" OR NATO OR alliance OR "defense pact"'
    ),
    "india_pakistan": (
        'India OR Pakistan OR Kashmir OR "Indian Ocean" OR "China-India" OR Modi'
    ),
    "korea": (
        'Korea OR North Korea OR Kim OR "South Korea" OR missiles OR "DMZ" OR Yoon OR Seoul'
    ),
}


def query_gdelt(query_str: str, maxrecords: int = 50, timespan: str = "24h", max_retries: int = 3) -> dict:
    """Execute a single GDELT DOC API query with retry on 429.
    Observed rate limit: ~90-120s cooldown per IP.
    """
    for attempt in range(max_retries):
        try:
            return _do_query(query_str, maxrecords, timespan)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_retries - 1:
                wait = (attempt + 1) * 90
                print(f"  ⏳ Rate limited. Waiting {wait}s (attempt {attempt+2}/{max_retries})...", file=sys.stderr)
                time.sleep(wait)
                continue
            body = e.read().decode("utf-8", errors="replace")
            return {"error": f"HTTP {e.code}: {body}", "articles": []}
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            return {"error": str(e), "articles": []}
    return {"error": "Max retries exceeded", "articles": []}


def _do_query(query_str: str, maxrecords: int = 50, timespan: str = "24h") -> dict:
    """Execute a single GDELT DOC API query (no retry)."""
    params = {
        "query": query_str,
        "mode": "artlist",
        "format": "json",
        "maxrecords": str(maxrecords),
        "timespan": timespan,
    }
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    
    req = urllib.request.Request(url, headers={"User-Agent": "GDELT-Collector/1.0"})
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError:
        raise
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        return {"error": str(e), "articles": []}
    
    articles = data.get("articles", [])
    return {"articles": articles, "total": len(articles)}


def analyze_query_results(result: dict) -> dict:
    """Extract key stats from a query result."""
    articles = result.get("articles", [])
    
    # Count articles
    count = len(articles)
    
    # Extract domains (sources)
    domains = Counter()
    languages = Counter()
    countries = Counter()
    
    for art in articles:
        domain = art.get("domain", "")
        if domain:
            domains[domain] += 1
        lang = art.get("language", "")
        if lang:
            languages[lang] += 1
        country = art.get("sourcecountry", "")
        if country:
            countries[country] += 1
    
    # Extract keywords from titles
    title_words = []
    stop_words = {"the", "a", "an", "in", "on", "at", "to", "for", "of", "and", 
                  "or", "is", "are", "was", "were", "be", "been", "has", "have",
                  "had", "do", "does", "did", "will", "would", "could", "should",
                  "may", "might", "can", "shall", "not", "no", "but", "if", "as",
                  "by", "with", "from", "its", "it", "this", "that", "these",
                  "those", "he", "she", "they", "we", "you", "i"}
    
    for art in articles:
        title = art.get("title", "")
        words = title.lower().split()
        title_words.extend([w.strip(".,;:!?\"'()[]-") for w in words 
                          if w.strip(".,;:!?\"'()[]-") not in stop_words 
                          and len(w.strip(".,;:!?\"'()[]-")) > 3])
    
    keyword_counts = Counter(title_words)
    
    # Volume classification
    if count >= 50:
        volume = "very_high"
    elif count >= 25:
        volume = "high"
    elif count >= 10:
        volume = "medium"
    elif count >= 1:
        volume = "low"
    else:
        volume = "none"
    
    return {
        "article_count": count,
        "volume": volume,
        "top_sources": domains.most_common(3),
        "top_languages": languages.most_common(3),
        "top_countries": countries.most_common(3),
        "top_keywords": keyword_counts.most_common(10),
    }


def collect(timespan: str = "24h", maxrecords: int = 50) -> dict:
    """Run all queries with rate-limit compliance."""
    results = {}
    query_index = 0
    total_queries = len(QUERIES)
    
    for theme, query_str in QUERIES.items():
        query_index += 1
        print(f"[{query_index}/{total_queries}] Querying: {theme}...", file=sys.stderr)
        
        result = query_gdelt(query_str, maxrecords=maxrecords, timespan=timespan)
        analysis = analyze_query_results(result)
        
        results[theme] = {
            "query": query_str,
            "raw_count": result.get("total", len(result.get("articles", []))),
            "articles_returned": len(result.get("articles", [])),
            "analysis": analysis,
            "error": result.get("error"),
        }
        
        if result.get("error"):
            print(f"  ⚠️  Error: {result['error']}", file=sys.stderr)
        else:
            print(f"  → {analysis['article_count']} articles, "
                  f"volume={analysis['volume']}, "
                  f"top={analysis['top_sources'][0][0] if analysis['top_sources'] else '-'}", file=sys.stderr)
        
        # Rate limit: observed ~90-120s per IP
        if query_index < total_queries:
            time.sleep(8)
    
    return results


def collect_verbose(timespan: str = "24h", maxrecords: int = 50) -> dict:
    """Run all queries and include raw article data."""
    results = {}
    query_index = 0
    total_queries = len(QUERIES)
    
    for theme, query_str in QUERIES.items():
        query_index += 1
        print(f"[{query_index}/{total_queries}] Querying: {theme}...", file=sys.stderr)
        
        result = query_gdelt(query_str, maxrecords=maxrecords, timespan=timespan)
        analysis = analyze_query_results(result)
        
        articles = result.get("articles", [])
        # Limit stored articles to avoid huge files (keep top 20)
        article_summaries = []
        for art in articles[:20]:
            article_summaries.append({
                "title": art.get("title", ""),
                "domain": art.get("domain", ""),
                "language": art.get("language", ""),
                "country": art.get("sourcecountry", ""),
                "timestamp": art.get("seendate", ""),
                "url": art.get("url", ""),
            })
        
        results[theme] = {
            "query": query_str,
            "article_count": len(articles),
            "analysis": analysis,
            "articles": article_summaries,
            "error": result.get("error"),
        }
        
        if result.get("error"):
            print(f"  ⚠️  Error: {result['error']}", file=sys.stderr)
        else:
            print(f"  → {analysis['article_count']} articles, "
                  f"volume={analysis['volume']}", file=sys.stderr)
        
        if query_index < total_queries:
            time.sleep(8)
    
    return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="GDELT Collector")
    parser.add_argument("--stdout", action="store_true", help="Print JSON to stdout")
    parser.add_argument("--date", type=str, default=None, help="Override date (YYYY-MM-DD)")
    parser.add_argument("--verbose", action="store_true", help="Include article summaries")
    parser.add_argument("--timespan", type=str, default="24h", help="GDELT timespan filter")
    parser.add_argument("--maxrecords", type=int, default=50, help="Max records per query")
    args = parser.parse_args()
    
    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    print(f"GDELT Collector — {date_str} (timespan={args.timespan})", file=sys.stderr)
    print(f"Running {len(QUERIES)} queries with 6s intervals...", file=sys.stderr)
    
    if args.verbose:
        results = collect_verbose(timespan=args.timespan, maxrecords=args.maxrecords)
    else:
        results = collect(timespan=args.timespan, maxrecords=args.maxrecords)
    
    output = {
        "date": date_str,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "timespan": args.timespan,
        "queries_run": len(QUERIES),
        "total_articles": sum(r.get("raw_count", r.get("article_count", 0)) for r in results.values()),
        "themes": results,
    }
    
    if args.stdout:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        export_dir = Path(__file__).resolve().parent.parent / "exports" / "gdelt"
        export_dir.mkdir(parents=True, exist_ok=True)
        out_path = export_dir / f"{date_str}.json"
        out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
        print(f"\nSaved to {out_path}", file=sys.stderr)
    
    # Summary table
    print(file=sys.stderr)
    print(f"{'Theme':<30} {'Articles':<10} {'Volume':<12} {'Top Source':<30}", file=sys.stderr)
    print("-" * 82, file=sys.stderr)
    for theme_key, data in results.items():
        ana = data.get("analysis", {})
        vol = ana.get("volume", "?")
        count = ana.get("article_count", data.get("article_count", "?"))
        top_src = ana.get("top_sources", [])
        src_name = top_src[0][0] if top_src else "-"
        err = data.get("error", "")
        if err:
            print(f"{theme_key:<30} {'ERR':<10} {'error':<12} {err[:40]:<30}", file=sys.stderr)
        else:
            print(f"{theme_key:<30} {str(count):<10} {vol:<12} {src_name:<30}", file=sys.stderr)
    print(file=sys.stderr)
    print(f"Total articles across all queries: {output['total_articles']}", file=sys.stderr)


if __name__ == "__main__":
    main()
