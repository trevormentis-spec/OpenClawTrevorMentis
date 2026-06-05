#!/usr/bin/env python3
"""Feed health audit — test all RSS feeds, flag dead/slow ones.

Reads feeds from collect.py (hardcoded) AND sources_tested.json (catalog).
Outputs: working, dead (4xx/5xx), slow (>5s), parse_error feeds.

Usage:
    python3 scripts/feed_health_audit.py                  # audit collect.py only
    python3 scripts/feed_health_audit.py --catalog         # audit catalog feeds only
    python3 scripts/feed_health_audit.py --catalog --all   # audit both
    python3 scripts/feed_health_audit.py --prune           # remove dead from collect.py
    python3 scripts/feed_health_audit.py --quick           # test only feeds flagged slow
"""
import re, time, urllib.request, urllib.error, xml.etree.ElementTree as ET, ssl, json, sys, pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
COLLECT_PY = REPO / "skills" / "daily-intel-brief" / "scripts" / "collect.py"
CATALOG_JSON = REPO / "analyst" / "meta" / "sources_tested.json"
ctx = ssl.create_default_context()

def test_feed(name: str, url: str) -> dict:
    t0 = time.monotonic()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.5"})
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        raw = resp.read()
        elapsed = time.monotonic() - t0
        root = ET.fromstring(raw)
        if root.tag == "{http://www.w3.org/2005/Atom}feed":
            items = len(root.findall("{http://www.w3.org/2005/Atom}entry"))
        else:
            items = len(root.findall(".//item"))
        status = "✅" if items > 0 else "⚠️"
        return {"name": name, "url": url, "status": status, "items": items, "ms": int(elapsed*1000), "error": None}
    except urllib.error.HTTPError as e:
        return {"name": name, "url": url, "status": "❌", "items": 0, "ms": int((time.monotonic()-t0)*1000), "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"name": name, "url": url, "status": "❌", "items": 0, "ms": int((time.monotonic()-t0)*1000), "error": str(e)[:60]}

def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prune", action="store_true", help="Remove dead feeds from collect.py")
    parser.add_argument("--quick", action="store_true", help="Quick mode — fewer tests")
    parser.add_argument("--catalog", action="store_true", help="Audit catalog feeds (sources_tested.json)")
    parser.add_argument("--all", action="store_true", help="Audit both collect.py AND catalog feeds")
    args = parser.parse_args()

    feeds = []

    # Collect feeds from sources_tested.json catalog
    if args.catalog or args.all:
        if CATALOG_JSON.exists():
            catalog = json.loads(CATALOG_JSON.read_text())
            for s in catalog.get("sources", []):
                rss = (s.get("rss") or "").strip()
                if rss and rss.startswith("http"):
                    feeds.append((s["name"], rss))
            print(f"Catalog feeds: {len(feeds)}")

    # Parse feeds from collect.py
    if not args.catalog or args.all:
        content = COLLECT_PY.read_text()
        py_feeds = re.findall(r'^\s*\("([^"]+)",\s*"([^"]+)"', content, re.MULTILINE)
        # Dedup against catalog feeds
        existing = {url for _, url in feeds}
        for name, url in py_feeds:
            if url not in existing:
                feeds.append((name, url))
        print(f"Hardcoded feeds: {len(py_feeds)} (added {len(feeds) - len(existing)} new)")

    if not feeds:
        print("No feeds found. Use --catalog and/or check collect.py.")
        return

    print(f"Testing {len(feeds)} total feeds...")
    results = []
    for i, (name, url) in enumerate(feeds):
        result = test_feed(name, url)
        results.append(result)
        if i % 20 == 0:
            print(f"  [{i+1}/{len(feeds)}]")
        time.sleep(0.3)  # be polite

    # Summary
    working = [r for r in results if r["status"] == "✅"]
    empty = [r for r in results if r["status"] == "⚠️"]
    dead = [r for r in results if r["status"] == "❌"]

    print(f"\n{'='*60}")
    print(f"FEED HEALTH AUDIT — {len(results)} feeds")
    print(f"{'='*60}")
    print(f"  ✅ Working: {len(working)}")
    print(f"  ⚠️ Empty (0 items): {len(empty)}")
    print(f"  ❌ Dead/Error: {len(dead)}")
    print(f"  Health rate: {len(working)/max(len(results),1)*100:.0f}%")

    if dead:
        print(f"\n  ❌ Dead feeds:")
        for d in sorted(dead, key=lambda x: x["error"]):
            print(f"    {d['name']}: {d['error']}")

    if args.prune and dead:
        print(f"\n  Pruning {len(dead)} dead feeds from collect.py...")
        for d in dead:
            # Remove the feed entry
            pattern = re.escape(f'("{d["name"]}", "{d["url"]}"')
            content = re.sub(rf'^\s*{pattern}[^)]*\),\s*\n', '', content, flags=re.MULTILINE)
        COLLECT_PY.write_text(content)
        print(f"  Removed {len(dead)} feeds. Re-run collect.py to verify.")

    # Save to brain memory for reference
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total": len(results),
        "working": len(working),
        "dead": len(dead),
        "health_pct": round(len(working)/max(len(results),1)*100, 1),
        "dead_list": [{"name": d["name"], "error": d["error"]} for d in dead[:50]],
    }
    report_path = pathlib.Path(__file__).resolve().parent.parent / "brain" / "memory" / "semantic" / "feed-health-latest.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\n  Report saved to brain/memory/semantic/feed-health-latest.json")

if __name__ == "__main__":
    main()
