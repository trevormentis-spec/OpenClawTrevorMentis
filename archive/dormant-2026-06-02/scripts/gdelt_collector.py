#!/usr/bin/env python3
"""
GDELT Collector — single broad query then client-side categorization.

Avoids GDELT rate limits (~90-120s per IP) by making ONE API call
instead of 10, then categorizing articles locally by keyword matching.

Outputs structured JSON to exports/gdelt/YYYY-MM-DD.json.

Usage:
    python3 gdelt_collector.py                        # save to exports/gdelt/
    python3 gdelt_collector.py --stdout               # print to stdout
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

# ── Keyword maps for client-side categorization ──
CATEGORY_KEYWORDS = {
    "iran_israel_hormuz": ["iran", "hormuz", "irgc", "hezbollah", "ayatollah", "tehran",
                           "qods", "israel", "netanyahu", "gaza", "west bank", "lebanon"],
    "ukraine_russia": ["ukraine", "russia", "donbas", "crimea", "zaporizhzhia",
                       "putin", "zelensky", "kyiv", "kharkiv", "odesa", "nato",
                       "shadow fleet"],
    "taiwan_china_scs": ["taiwan", "south china sea", "spratly", "paracel", "pla",
                         "beijing", "lai ching-te", "nine-dash", "senkaku", "diaoyu"],
    "africa_sahel": ["sahel", "mali", "burkina", "niger", "sudan", "ethiopia",
                     "rwanda", "congo", "somalia", "amison", "africa"],
    "latin_america": ["mexico", "brazil", "colombia", "venezuela", "ecuador",
                      "argentina", "chile", "peru", "latin america", "sheinbaum",
                      "el tigre", "petro", "lula"],
    "cyber_intel": ["cyberattack", "ransomware", "state-backed", "hacking",
                    "data breach", "cve-", "apt", "malware", "phishing"],
    "energy_commodities": ["oil", "brent", "crude", "lng", "energy", "commodity",
                           "shipping", "supply chain", "freight", "tanker"],
    "great_power": ["great power", "us-china", "us-russia", "nato", "defense pact",
                    "alliance", "superpower", "hegemony", "aukus"],
    "india_pakistan": ["india", "pakistan", "kashmir", "modi", "new delhi",
                       "islamabad", "indian ocean"],
    "korea": ["north korea", "south korea", "kim jong", "seoul", "pyongyang",
              "dmz", "yoon", "kia", "hyundai"],
}


def _categorize_article(text: str) -> str:
    """Assign an article to its best-fit category based on keyword matching."""
    text_lower = text.lower()
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[cat] = score
    if not scores:
        return "uncategorized"
    return max(scores, key=scores.get)


def collect(maxrecords: int = 250, timespan: str = "24h") -> dict:
    """Execute a single broad GDELT query, categorize results client-side."""
    broad_query = (
        "(Iran OR Hormuz OR IRGC OR Israel OR Hezbollah)"
        " OR (Ukraine OR Russia OR Donbas OR NATO)"
        " OR (Taiwan OR South China Sea OR China)"
        " OR (oil OR brent OR LNG OR energy OR shipping)"
        " OR (cyberattack OR ransomware OR hacking)"
        " OR (India OR Pakistan OR North Korea)"
        " OR (Sahel OR Sudan OR Ethiopia OR Africa)"
        " OR (Mexico OR Brazil OR Colombia OR Venezuela)"
        " OR (great power OR US-China OR US-Russia)"
    )

    params = {
        "query": broad_query,
        "mode": "ArtList",
        "format": "JSON",
        "maxrecords": str(maxrecords),
        "timespan": timespan,
    }
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    })

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                raw = json.loads(resp.read().decode("utf-8", errors="ignore"))
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                wait = (attempt + 1) * 90
                print(f"  ⏳ Rate limited. Waiting {wait}s (attempt {attempt+2}/3)...", file=sys.stderr)
                time.sleep(wait)
                continue
            return {"error": f"HTTP {e.code}: {e.reason}", "themes": {}, "total_articles": 0}
        except Exception as e:
            return {"error": str(e), "themes": {}, "total_articles": 0}
    else:
        return {"error": "Max retries (429)", "themes": {}, "total_articles": 0}

    articles = raw.get("articles", [])
    sources = Counter()
    languages = Counter()
    keywords_all = Counter()

    # Categorize
    theme_articles = {cat: [] for cat in CATEGORY_KEYWORDS}
    theme_articles["uncategorized"] = []

    for art in articles:
        title = art.get("title", "")
        summary = art.get("summary", "")
        text = f"{title} {summary}"
        cat = _categorize_article(text)
        theme_articles[cat].append(art)

        source = art.get("source", "") or art.get("domain", "")
        if source:
            sources[source] += 1
        lang = art.get("language", "")
        if lang:
            languages[lang] += 1
        for word in title.split():
            w = word.strip(".,;:!?\"'()[]-")
            if len(w) > 5 and w[0].isupper():
                keywords_all[w] += 1

    # Build theme analysis
    themes = {}
    for cat, cat_arts in theme_articles.items():
        count = len(cat_arts)
        vol = "none"
        if count >= 50: vol = "very_high"
        elif count >= 30: vol = "high"
        elif count >= 15: vol = "medium"
        elif count >= 1: vol = "low"

        themes[cat] = {
            "article_count": count,
            "volume": vol,
            "top_sources": sources.most_common(5),
            "top_keywords": keywords_all.most_common(10),
            "top_languages": languages.most_common(5),
        }

    return {
        "total_articles": len(articles),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "themes": themes,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="GDELT Collector")
    parser.add_argument("--stdout", action="store_true", help="Print JSON to stdout")
    parser.add_argument("--date", type=str, default=None, help="Override date (YYYY-MM-DD)")
    parser.add_argument("--timespan", type=str, default="24h", help="GDELT timespan filter")
    parser.add_argument("--maxrecords", type=int, default=250, help="Max records")
    args = parser.parse_args()

    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print(f"GDELT Collector — {date_str} (1 broad query, {args.maxrecords} max)", file=sys.stderr)

    result = collect(maxrecords=args.maxrecords, timespan=args.timespan)

    output = {
        "date": date_str,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "timespan": args.timespan,
        "queries_run": 1,
        "total_articles": result.get("total_articles", 0),
        "themes": result.get("themes", {}),
        "error": result.get("error"),
    }

    if result.get("error"):
        print(f"  ⚠️  Error: {result['error']}", file=sys.stderr)

    if args.stdout:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        export_dir = Path(__file__).resolve().parent.parent / "exports" / "gdelt"
        export_dir.mkdir(parents=True, exist_ok=True)
        out_path = export_dir / f"{date_str}.json"
        out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
        print(f"  Saved to {out_path}", file=sys.stderr)

    # Summary
    print(file=sys.stderr)
    themes = result.get("themes", {})
    sorted_themes = sorted(themes.items(), key=lambda x: x[1].get("article_count", 0), reverse=True)
    print(f"{'Category':<30} {'Articles':<10} {'Volume':<12} {'Top Source':<30}", file=sys.stderr)
    print("-" * 82, file=sys.stderr)
    for cat, data in sorted_themes:
        count = data.get("article_count", 0)
        vol = data.get("volume", "?")
        srcs = data.get("top_sources", [])
        top = srcs[0][0] if srcs else "-"
        print(f"{cat:<30} {count:<10} {vol:<12} {top:<30}", file=sys.stderr)
    print(file=sys.stderr)
    print(f"Total: {result.get('total_articles', 0)} articles", file=sys.stderr)


if __name__ == "__main__":
    main()
