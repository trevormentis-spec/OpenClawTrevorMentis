#!/usr/bin/env python3
"""Feed health audit: test all feed URLs from sources.json for HTTP status.

Optimized: 3s timeout, HEAD-only, periodic saves every 100 URLs."""
import json
import sys
import time
import urllib.request
import urllib.error
import socket

REPORT_PATH = "/home/ubuntu/.openclaw/workspace/brain/memory/semantic/feed-health-latest.json"
SOURCES_PATH = "/home/ubuntu/.openclaw/workspace/analyst/meta/sources.json"

# Wire feeds from collect.py
WIRE_FEEDS = [
    ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("FT World", "https://www.ft.com/world?format=rss"),
    ("The Guardian World", "https://www.theguardian.com/world/rss"),
    ("NPR World", "https://feeds.npr.org/1004/rss.xml"),
    ("France 24 EN", "https://www.france24.com/en/rss"),
    ("DW News EN", "https://rss.dw.com/rdf/rss-en-world"),
    ("CNBC World", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100727362"),
]

TIMEOUT = 3  # seconds per URL
SAVE_EVERY = 100  # save progress every N URLs

def test_url(name, url):
    """Test a URL and return status info. Tries HEAD first, GET fallback."""
    result = {"name": name, "url": url[:200]}
    start = time.time()
    try:
        req = urllib.request.Request(url, method="HEAD")
        resp = urllib.request.urlopen(req, timeout=TIMEOUT)
        elapsed = time.time() - start
        result["status"] = resp.status
        result["elapsed_s"] = round(elapsed, 2)
        result["healthy"] = 200 <= resp.status < 400
        result["slow"] = elapsed > 5
    except urllib.error.HTTPError as e:
        if e.code in (405, 501):
            # HEAD not supported, retry with GET
            try:
                start = time.time()
                req = urllib.request.Request(url, method="GET")
                resp = urllib.request.urlopen(req, timeout=TIMEOUT)
                elapsed = time.time() - start
                result["status"] = resp.status
                result["elapsed_s"] = round(elapsed, 2)
                result["healthy"] = 200 <= resp.status < 400
                result["slow"] = elapsed > 5
                result["note"] = "HEAD unsupported, used GET"
            except urllib.error.HTTPError as e2:
                elapsed = time.time() - start
                result["status"] = e2.code
                result["elapsed_s"] = round(elapsed, 2)
                result["healthy"] = False
            except urllib.error.URLError as e2:
                elapsed = time.time() - start
                result["status"] = f"URLError: {e2.reason}"
                result["elapsed_s"] = round(elapsed, 2)
                result["healthy"] = False
            except socket.timeout:
                elapsed = time.time() - start
                result["status"] = "timeout"
                result["elapsed_s"] = round(elapsed, 2)
                result["healthy"] = False
            except Exception as e2:
                elapsed = time.time() - start
                result["status"] = f"error: {type(e2).__name__}: {e2}"
                result["elapsed_s"] = round(elapsed, 2)
                result["healthy"] = False
        else:
            elapsed = time.time() - start
            result["status"] = e.code
            result["elapsed_s"] = round(elapsed, 2)
            result["healthy"] = False
    except urllib.error.URLError as e:
        elapsed = time.time() - start
        result["status"] = f"URLError: {e.reason}"
        result["elapsed_s"] = round(elapsed, 2)
        result["healthy"] = False
    except socket.timeout:
        elapsed = time.time() - start
        result["status"] = "timeout"
        result["elapsed_s"] = round(elapsed, 2)
        result["healthy"] = False
        result["slow"] = True
    except Exception as e:
        elapsed = time.time() - start
        result["status"] = f"error: {type(e).__name__}: {e}"
        result["elapsed_s"] = round(elapsed, 2)
        result["healthy"] = False
    return result

def save_interim(results, total, working, dead, done_count):
    """Save current progress to report file."""
    report = {
        "timestamp": time.time(),
        "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "feedsTested": total,
        "testedSoFar": done_count,
        "working": working,
        "dead": dead,
        "healthPct": round(working / max(done_count, 1) * 100, 1),
        "complete": done_count >= total,
    }
    if done_count >= total:
        slow = sum(1 for r in results if r.get("slow"))
        timeouts = sum(1 for r in results if r.get("status") == "timeout")
        dead_examples = [f"{r['name']} ({r['status']})" for r in results if not r["healthy"]][:15]
        parse_errors = [f"{r['name']}: {r['status']}" for r in results if "unknown url type" in str(r.get("status", ""))]
        report.update({
            "slow": slow,
            "timeouts": timeouts,
            "deadExamples": dead_examples,
            "parseErrors": parse_errors,
            "results": results
        })
    with open(REPORT_PATH, "w") as f:
        json.dump(report, f, indent=2)

def main():
    # Load sources
    with open(SOURCES_PATH) as f:
        sources = json.load(f)
    
    durable = sources.get("durable_sources", [])
    local_lang = sources.get("local_language_sources", [])
    
    # Collect all URLs
    all_sources = []
    seen_urls = set()
    for ds in durable:
        if ds.get("url"):
            key = ds["url"][:200]
            if key not in seen_urls:
                seen_urls.add(key)
                all_sources.append((ds["name"], ds["url"]))
    for ls in local_lang:
        if ls.get("url"):
            key = ls["url"][:200]
            if key not in seen_urls:
                seen_urls.add(key)
                all_sources.append((ls["name"], ls["url"]))
    for name, url in WIRE_FEEDS:
        if url not in seen_urls:
            seen_urls.add(url)
            all_sources.append((name, url))
    
    total = len(all_sources)
    print(f"Testing {total} URLs with {TIMEOUT}s timeout...", flush=True)
    
    results = []
    working = 0
    dead = 0
    
    for i, (name, url) in enumerate(all_sources):
        result = test_url(name, url)
        results.append(result)
        
        if result["healthy"]:
            working += 1
        else:
            dead += 1
        
        if (i + 1) % SAVE_EVERY == 0:
            pct = round((i + 1) / total * 100, 1)
            print(f"  {i+1}/{total} ({pct}%) — working={working} dead={dead}", flush=True)
            save_interim(results, total, working, dead, i + 1)
    
    # Final save
    health_pct = round(working / total * 100, 1) if total > 0 else 0
    save_interim(results, total, working, dead, total)
    
    slow = sum(1 for r in results if r.get("slow"))
    timeouts = sum(1 for r in results if r.get("status") == "timeout")
    dead_examples = [f"{r['name']} ({r['status']})" for r in results if not r["healthy"]][:15]
    
    print(f"\n=== Feed Health Audit Complete ===", flush=True)
    print(f"Total tested: {total}", flush=True)
    print(f"Working: {working} ({health_pct}%)", flush=True)
    print(f"Dead: {dead} ({round(100 - health_pct, 1)}%)", flush=True)
    print(f"  Slow (>5s): {slow}", flush=True)
    print(f"  Timeouts: {timeouts}", flush=True)
    print(f"\nNotable dead feeds:", flush=True)
    for ex in dead_examples:
        print(f"  - {ex}", flush=True)
    print(f"\nReport saved to {REPORT_PATH}", flush=True)

if __name__ == "__main__":
    main()
