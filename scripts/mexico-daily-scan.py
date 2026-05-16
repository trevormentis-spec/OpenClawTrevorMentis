#!/usr/bin/env python3
"""
Mexico Daily News Scan — Spanish-Language Sources

Fetches and extracts headlines/summaries from key Mexican news sources
that don't have accessible RSS feeds. Outputs a structured JSON file
with articles organized by theme.

Sources (when accessible):
- El Universal (universal.com.mx) — free
- Milenio (milenio.com) — free  
- Animal Politico (animalpolitico.com) — free
- Aristegui Noticias (aristeguinoticias.com) — free
- Proceso (proceso.com.mx) — free
- La Jornada (jornada.com.mx) — free
- El Financiero (elfinanciero.com.mx) — partial paywall
- Reforma (reforma.com) — paywall (log and skip)
- El Economista (eleconomista.com.mx) — free
- El País México (elpais.com/mexico) — partial

Usage:
    python3 scripts/mexico-daily-scan.py
    python3 scripts/mexico-daily-scan.py --save

Output:
    exports/mexico-news-scan-YYYY-MM-DD.json
    (printed summary to stdout)
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
EXPORT_DIR = REPO_ROOT / "exports"

# Sources with free access and simple HTML parsing
SOURCES = [
    {
        "name": "Animal Politico",
        "url": "https://www.animalpolitico.com",
        "themes": ["political_risk", "cartel_security"],
        "type": "news",
        "selectors": {  # Simple keyword matching for headline extraction
            "security": ["seguridad", "violencia", "cártel", "narco", "crimen", "asesinato", "desaparición"],
            "politics": ["presidente", "sheinbaum", "morena", "gobierno", "congreso", "reforma"],
            "us_mexico": ["trump", "eeuu", "frontera", "arancel", "usmca", "migración"],
        }
    },
    {
        "name": "Milenio",
        "url": "https://www.milenio.com",
        "themes": ["cartel_security", "political_risk"],
        "type": "news",
    },
    {
        "name": "Aristegui Noticias",
        "url": "https://aristeguinoticias.com",
        "themes": ["political_risk", "cartel_security"],
        "type": "news",
    },
    {
        "name": "Proceso",
        "url": "https://www.proceso.com.mx",
        "themes": ["political_risk", "cartel_security"],
        "type": "news",
    },
    {
        "name": "La Jornada",
        "url": "https://www.jornada.com.mx",
        "themes": ["political_risk"],
        "type": "news",
        "note": "Strong Morena/government editorial line. Cross-reference with Animal Politico and Reforma.",
    },
    {
        "name": "El Financiero",
        "url": "https://www.elfinanciero.com.mx",
        "themes": ["economy_markets", "energy_infra"],
        "type": "financial",
    },
    {
        "name": "El Economista",
        "url": "https://www.eleconomista.com.mx",
        "themes": ["economy_markets", "energy_infra"],
        "type": "financial",
    },
    {
        "name": "El País México",
        "url": "https://elpais.com/mexico/",
        "themes": ["political_risk", "cartel_security", "us_mexico"],
        "type": "news",
        "note": "International coverage of Mexico — useful for cross-border framing",
    },
    {
        "name": "Reforma",
        "url": "https://www.reforma.com",
        "themes": ["political_risk", "cartel_security", "economy_markets"],
        "type": "paywall",
        "note": "PAYWALL — log as blocked, principal to resolve access",
    },
]

# Blocked sources (paywall or known inaccessibility)
BLOCKED = {
    "Reforma": "Paywall — principal to resolve access",
}


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[scan {ts}] {msg}", file=sys.stderr, flush=True)


def fetch_page(url: str, timeout: int = 15) -> str | None:
    """Fetch a page and return raw HTML text."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code == 403:
            return None  # Blocked
        log(f"HTTP {exc.code} for {url}")
        return None
    except Exception as exc:
        log(f"Failed to fetch {url}: {type(exc).__name__}")
        return None


def extract_links_from_html(html: str, base_url: str) -> list[dict]:
    """Basic extraction of headlines and links from HTML.
    
    This is intentionally simple — finds <a> tags and attempts to extract
    meaningful headlines. A proper solution would use newspaper3k or
    readability-lxml, but this avoids external dependencies.
    """
    articles = []
    
    # Extract title from <title> tag
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
    page_title = title_match.group(1).strip() if title_match else ""
    
    # Extract text content (simple strip)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Try to extract article links from common patterns
    # This is basic — checks for h2/h3 headings with links
    heading_patterns = re.findall(
        r'<(?:h[1-4])[^>]*>.*?<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>.*?</(?:h[1-4])>',
        html, re.IGNORECASE | re.DOTALL
    )
    
    for href, title in heading_patterns[:15]:
        # Clean title
        clean_title = re.sub(r'\s+', ' ', title).strip()
        # Make absolute URL
        if href.startswith("/"):
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            href = f"{parsed.scheme}://{parsed.netloc}{href}"
        elif not href.startswith("http"):
            href = base_url.rstrip("/") + "/" + href.lstrip("/")
        
        if clean_title and len(clean_title) > 15:
            articles.append({
                "title": clean_title,
                "url": href,
            })
    
    return articles, page_title, text[:2000]


def scan_source(source: dict) -> dict:
    """Scan a single source and return results."""
    name = source["name"]
    url = source["url"]
    source_type = source.get("type", "news")
    
    if source_type == "paywall" or name in BLOCKED:
        return {
            "name": name,
            "url": url,
            "status": "blocked",
            "reason": BLOCKED.get(name, "Paywall or inaccessible"),
            "articles": [],
        }
    
    log(f"Fetching {name}...")
    html = fetch_page(url)
    if html is None:
        return {
            "name": name,
            "url": url,
            "status": "error",
            "reason": "Failed to fetch or blocked (403)",
            "articles": [],
        }
    
    articles, page_title, preview = extract_links_from_html(html, url)
    
    # Filter for relevant themes using keyword matching
    themed_keywords = source.get("selectors", {})
    tagged_articles = []
    for art in articles[:20]:
        title_lower = art["title"].lower()
        matched_themes = []
        for theme, keywords in themed_keywords.items():
            if any(kw in title_lower for kw in keywords):
                matched_themes.append(theme)
        tagged_articles.append({
            **art,
            "matched_themes": matched_themes if matched_themes else ["unclassified"],
        })
    
    return {
        "name": name,
        "url": url,
        "status": "ok",
        "page_title": page_title,
        "article_count": len(articles),
        "articles": tagged_articles[:15],  # Top 15
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save", action="store_true", help="Save results to exports/")
    args = parser.parse_args()
    
    results = []
    
    for source in SOURCES:
        result = scan_source(source)
        results.append(result)
        
        # Print summary
        status = result["status"]
        count = result.get("article_count", 0)
        if status == "ok":
            print(f"  ✅ {result['name']}: {count} articles found")
        elif status == "blocked":
            print(f"  🔒 {result['name']}: BLOCKED — {result.get('reason','')}")
        else:
            print(f"  ❌ {result['name']}: FAILED — {result.get('reason','')}")
    
    # Summary
    ok = sum(1 for r in results if r["status"] == "ok")
    blocked = sum(1 for r in results if r["status"] == "blocked")
    failed = sum(1 for r in results if r["status"] == "error")
    total_articles = sum(r.get("article_count", 0) for r in results)
    
    print(f"\n{'='*50}")
    print(f"SCAN SUMMARY")
    print(f"{'='*50}")
    print(f"Sources: {ok} ok, {blocked} blocked, {failed} failed")
    print(f"Total articles: {total_articles}")
    
    if args.save:
        date_str = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = EXPORT_DIR / f"mexico-news-scan-{date_str}.json"
        out_path.write_text(json.dumps({
            "date": date_str,
            "sources_scanned": len(SOURCES),
            "sources_ok": ok,
            "sources_blocked": blocked,
            "sources_failed": failed,
            "total_articles": total_articles,
            "results": results,
        }, indent=2, ensure_ascii=False))
        print(f"Saved to {out_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
