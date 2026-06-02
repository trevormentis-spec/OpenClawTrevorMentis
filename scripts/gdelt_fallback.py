#!/usr/bin/env python3
"""
GDELT Fallback Collector — uses Brave Web Search API when GDELT is rate-limited.

Makes one broad query for geopolitics news, categorizes results client-side.

Usage:
    python3 scripts/gdelt_fallback.py --stdout          # print
    python3 scripts/gdelt_fallback.py                   # save to exports/gdelt/
"""

import json
import os
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

CATEGORY_KEYWORDS = {
    "iran_israel_hormuz": ["iran", "hormuz", "irgc", "hezbollah", "ayatollah", "tehran",
                           "qods", "israel", "netanyahu", "gaza", "west bank", "lebanon"],
    "ukraine_russia": ["ukraine", "russia", "donbas", "crimea", "zaporizhzhia",
                       "putin", "zelensky", "kyiv", "kharkiv", "nato", "shadow fleet"],
    "taiwan_china_scs": ["taiwan", "south china sea", "spratly", "paracel", "pla",
                         "beijing", "nine-dash", "senkaku", "diaoyu"],
    "africa_sahel": ["sahel", "mali", "burkina", "niger", "sudan", "ethiopia",
                     "rwanda", "congo", "somalia", "amison"],
    "latin_america": ["mexico", "brazil", "colombia", "venezuela", "ecuador",
                      "argentina", "chile", "peru", "latin america", "sheinbaum"],
    "cyber_intel": ["cyberattack", "ransomware", "state-backed", "hacking",
                    "data breach", "cve-", "apt", "malware", "phishing"],
    "energy_commodities": ["oil", "brent", "crude", "lng", "energy", "commodity",
                           "shipping", "tanker"],
    "great_power": ["great power", "us-china", "us-russia", "nato", "defense pact",
                    "alliance", "superpower", "aukus"],
    "india_pakistan": ["india", "pakistan", "kashmir", "modi", "new delhi",
                       "islamabad", "indian ocean"],
    "korea": ["north korea", "south korea", "kim jong", "seoul", "pyongyang", "dmz"],
}


def _categorize(text: str) -> str:
    text_lower = text.lower()
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[cat] = score
    return max(scores, key=scores.get) if scores else "uncategorized"


def collect() -> dict:
    """Fetch geopolitical news via Brave Search, categorize."""
    query = (
        "geopolitics (Iran OR Israel OR Russia OR Ukraine OR China OR Taiwan "
        "OR NATO OR oil OR cyberattack OR Africa OR Mexico OR North Korea) latest news"
    )

    api_key = os.environ.get("BRAVE_API_KEY", "")
    if not api_key:
        # Try from .env
        env_path = Path(__file__).resolve().parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("BRAVE_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break

    if not api_key:
        return {"error": "No BRAVE_API_KEY", "themes": {}, "total_articles": 0}

    params = urllib.parse.urlencode({"q": query, "count": 20, "freshness": "24h"})
    url = f"https://api.search.brave.com/res/v1/web/search?{params}"

    req = urllib.request.Request(url, headers={
        "Accept": "application/json",
        
        "X-Subscription-Token": api_key,
    })

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return {"error": str(e), "themes": {}, "total_articles": 0}

    results = data.get("web", {}).get("results", [])
    sources = Counter()
    theme_map = {cat: [] for cat in CATEGORY_KEYWORDS}
    theme_map["uncategorized"] = []

    for item in results:
        title = item.get("title", "")
        desc = item.get("description", "")
        text = f"{title} {desc}"
        cat = _categorize(text)
        theme_map[cat].append(item)
        source = item.get("source", "") or item.get("url", "")
        if source:
            sources[source] += 1

    themes = {}
    for cat, items in theme_map.items():
        count = len(items)
        vol = "none"
        if count >= 10: vol = "very_high"
        elif count >= 5: vol = "high"
        elif count >= 3: vol = "medium"
        elif count >= 1: vol = "low"
        themes[cat] = {
            "article_count": count,
            "volume": vol,
            "top_sources": sources.most_common(5),
        }

    return {
        "total_articles": len(results),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "themes": themes,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--stdout", action="store_true")
    parser.add_argument("--date", type=str, default=None)
    args = parser.parse_args()

    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"GDELT Fallback — {date_str} (Brave Search)", file=sys.stderr)

    result = collect()

    if result.get("error"):
        print(f"  ⚠️  {result['error']}", file=sys.stderr)

    output = {
        "date": date_str,
        "timestamp": result.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "total_articles": result.get("total_articles", 0),
        "themes": result.get("themes", {}),
        "error": result.get("error"),
    }

    if args.stdout:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        export_dir = Path(__file__).resolve().parent.parent / "exports" / "gdelt"
        export_dir.mkdir(parents=True, exist_ok=True)
        out_path = export_dir / f"{date_str}.json"
        out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
        print(f"  Saved to {out_path}", file=sys.stderr)

    # Print summary
    themes = result.get("themes", {})
    sorted_t = sorted(themes.items(), key=lambda x: x[1].get("article_count", 0), reverse=True)
    print(f"{'Category':<30} {'Articles':<10} {'Volume':<12}", file=sys.stderr)
    print("-" * 52, file=sys.stderr)
    for cat, t in sorted_t:
        print(f"{cat:<30} {t['article_count']:<10} {t['volume']:<12}", file=sys.stderr)
    print(file=sys.stderr)
    print(f"Total: {result.get('total_articles', 0)} articles", file=sys.stderr)


if __name__ == "__main__":
    main()
