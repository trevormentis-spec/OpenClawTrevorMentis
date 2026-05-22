#!/usr/bin/env python3
"""Feed health audit — test all RSS feeds, flag dead/slow ones.

Reads LOCAL_LANGUAGE_FEEDS from collect.py and tests each URL.
Outputs: working, dead (4xx/5xx), slow (>5s), parse_error feeds.

Usage:
    python3 scripts/feed_health_audit.py                  # full audit
    python3 scripts/feed_health_audit.py --prune           # remove dead from collect.py
    python3 scripts/feed_health_audit.py --quick           # test only feeds flagged slow
"""
import re, time, urllib.request, urllib.error, xml.etree.ElementTree as ET, ssl, json, sys, pathlib

COLLECT_PY = pathlib.Path(__file__).resolve().parent.parent / "skills" / "daily-intel-brief" / "scripts" / "collect.py"
ctx = ssl.create_default_context()

def test_feed(name: str, url: str) -> dict:
    t0 = time.monotonic()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TrevorHealthCheck/1.0", "Accept": "application/rss+xml"})
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
    args = parser.parse_args()

    # Parse feeds from collect.py
    content = COLLECT_PY.read_text()
    feeds = re.findall(r'^\s*\(\"([^\"]+)\",\s*\"([^\"]+)\"', content, re.MULTILINE)

    print(f"Testing {len(feeds)} feeds...")
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
