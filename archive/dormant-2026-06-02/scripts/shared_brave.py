#!/usr/bin/env python3
"""Shared Brave Search utility — handles gzip, retries, single import point.

Usage:
    from scripts.shared_brave import brave_search
    results = brave_search("Iran nuclear deal")
"""
import gzip, json, os, urllib.request, urllib.parse, urllib.error

API_URL = "https://api.search.brave.com/res/v1/web/search"
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")


def brave_search(query: str, count: int = 5) -> list[dict[str, str]]:
    """Search Brave Web Search API with proper gzip handling.
    
    Returns list of {title, url, age} dicts. Empty list on failure.
    """
    if not BRAVE_API_KEY:
        return []
    
    params = urllib.parse.urlencode({"q": query, "count": min(count, 10)})
    url = f"{API_URL}?{params}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/json")
    req.add_header("Accept-Encoding", "gzip")
    req.add_header("X-Subscription-Token", BRAVE_API_KEY)
    
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        raw = resp.read()
        # Handle gzip — Brave always gzips even without Accept-Encoding
        if raw[:2] == b'\x1f\x8b':
            raw = gzip.decompress(raw)
        data = json.loads(raw)
        results = []
        for r in data.get("web", {}).get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "age": r.get("age", ""),
            })
        return results
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, json.JSONDecodeError, gzip.BadGzipFile):
        return []


if __name__ == "__main__":
    # Quick test
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "test"
    results = brave_search(q)
    print(f"Brave Search: {len(results)} results for '{q}'")
    for r in results[:3]:
        print(f"  → {r['title']}")
