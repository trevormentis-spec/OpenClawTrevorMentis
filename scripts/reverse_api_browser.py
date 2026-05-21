#!/usr/bin/env python3
"""
Reverse-Engineer API Specs via Playwright Browser Automation.

Opens target sites in a headless Chromium, intercepts all network requests,
identifies JSON API endpoints, and generates spec.json files compatible with
pipeline_openweb_collect.py.

Usage:
    python3 scripts/reverse_api_browser.py --site https://www.timesofisrael.com
    python3 scripts/reverse_api_browser.py --tier1     # Top priority targets
    python3 scripts/reverse_api_browser.py --list      # List all targets
"""
from __future__ import annotations

import asyncio
import datetime as dt
import json
import os
import pathlib
import re
import sys
from urllib.parse import urlparse, urljoin

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SPECS_DIR = REPO_ROOT / "skills" / "collection" / "_specs"
STATE_FILE = REPO_ROOT / "tasks" / "reverse_api_browser.json"

TARGETS = [
    {"url": "https://www.timesofisrael.com", "label": "Times of Israel", "p": 1},
    {"url": "https://www.haaretz.com", "label": "Haaretz", "p": 1},
    {"url": "https://www.al-monitor.com", "label": "Al Monitor", "p": 1},
    {"url": "https://www.csis.org", "label": "CSIS", "p": 1},
    {"url": "https://www.cfr.org", "label": "CFR", "p": 1},
    {"url": "https://www.understandingwar.org", "label": "ISW", "p": 1},
    {"url": "https://www.lemonde.fr/en/", "label": "Le Monde EN", "p": 1},
    {"url": "https://www.ynet.co.il", "label": "Ynet", "p": 1},
    {"url": "https://www.nikkei.com", "label": "Nikkei", "p": 2},
    {"url": "https://www.reforma.com", "label": "Reforma", "p": 2},
    {"url": "https://www.milenio.com", "label": "Milenio", "p": 2},
    {"url": "https://www.eluniversal.com.mx", "label": "El Universal MX", "p": 2},
    {"url": "https://www.moscowtimes.ru", "label": "Moscow Times", "p": 2},
    {"url": "https://tass.com", "label": "TASS", "p": 2},
    {"url": "https://www.scmp.com", "label": "SCMP", "p": 2},
    {"url": "https://www.iranwarlive.com", "label": "Iran War Live", "p": 3},
    {"url": "https://www.iranmonitor.org", "label": "Iran Monitor", "p": 3},
    {"url": "https://warintelhub.com", "label": "War Intel Hub", "p": 3},
    {"url": "https://www.acleddata.com", "label": "ACLED", "p": 3},
]


def log(msg):
    print(f"[rev-browser] {msg}", file=sys.stderr, flush=True)


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"completed": {}, "discovered_apis": {}}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def is_json_api(url, content_type, response_data):
    if "json" not in content_type.lower():
        return False
    exclude = [
        "analytics", "google-analytics", "facebook", "doubleclick",
        "cdn-cgi", "recaptcha", "clarity", "hotjar", "bugsnag",
        "sentry", "datadog", "newrelic", "amplitude", "segment",
        "optimizely", "launchdarkly", "stripe", "paypal",
        "auth0", "okta", "logrocket", "fullstory",
        ".js", ".css", ".png", ".jpg", ".svg", ".ico", ".woff",
        "amp_", "gtm.", "googletag",
    ]
    url_lower = url.lower()
    for pat in exclude:
        if pat in url_lower:
            return False
    if not response_data or len(response_data) < 50:
        return False
    try:
        data = json.loads(response_data)
        if isinstance(data, dict):
            if len(data) == 0:
                return False
            if set(data.keys()) <= {"status", "message", "error", "success"}:
                return False
        if isinstance(data, list) and len(data) == 0:
            return False
    except json.JSONDecodeError:
        return False
    return True


def extract_operations(discovered):
    operations = []
    endpoint = discovered.get("endpoint", "")
    method = discovered.get("method", "GET")
    parsed = urlparse(endpoint)
    label = discovered.get("label", "")

    if "/pf/api/" in endpoint:
        operations.append({
            "name": "search",
            "description": f"Search {label} via Arc XP API",
            "method": method,
            "endpoint": parsed.path,
            "params": [
                {"name": "q", "type": "string", "required": True, "description": "Search query"},
                {"name": "size", "type": "int", "required": False, "description": "Results count"},
            ],
            "response_selector": "$",
        })
    elif "/wp-json/" in endpoint or "/wp/v2/" in endpoint:
        operations.append({
            "name": "get_posts",
            "description": f"WordPress posts from {label}",
            "method": method,
            "endpoint": parsed.path,
            "params": [
                {"name": "per_page", "type": "int", "required": False, "description": "Posts per page"},
            ],
            "response_selector": "$",
        })
    elif "/graphql" in endpoint.lower():
        operations.append({
            "name": "graphql_query",
            "description": f"GraphQL query on {label}",
            "method": "POST",
            "endpoint": parsed.path,
            "body_template": '{"query":"{ __schema { types { name } } }"}',
            "content_type": "application/json",
            "response_selector": "$.data",
        })
    else:
        op_name = re.sub(r'[^a-z0-9]', '_', parsed.path.strip("/").split("/")[0] or "api")
        operations.append({
            "name": op_name,
            "description": f"Fetch from {label} API",
            "method": method,
            "endpoint": parsed.path,
            "params": [],
            "response_selector": "$",
        })

    return operations


def generate_spec(site_label, base_url, discovered_apis):
    if not discovered_apis:
        return None
    site_slug = site_label.lower().replace(" ", "-").replace("'", "")[:40]
    all_ops = []
    for api in discovered_apis:
        all_ops.extend(extract_operations(api))
    seen = set()
    unique = []
    for op in all_ops:
        if op["endpoint"] not in seen:
            seen.add(op["endpoint"])
            unique.append(op)
    if not unique:
        return None
    return {
        "site": site_slug,
        "version": "1.0.0",
        "transport": "http",
        "base_url": base_url.rstrip("/"),
        "auth_type": "none",
        "platform": "auto_discovered",
        "operations": unique,
        "discovered_by": "reverse_api_browser.py",
        "discovered_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }


async def capture_api_calls(site_url, label):
    from playwright.async_api import async_playwright

    discovered = []
    seen = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )

        api_responses = []

        async def on_response(response):
            url = response.url
            if url in seen:
                return
            seen.add(url)
            ct = response.headers.get("content-type", "")
            if "json" not in ct.lower():
                return
            try:
                body = await response.text()
            except Exception:
                return
            if not is_json_api(url, ct, body):
                return
            api_responses.append({
                "url": url,
                "method": response.request.method,
                "status": response.status,
                "sample_response": body[:2000],
            })
            log(f"  CAPTURED: {response.request.method} {url}")

        page = await ctx.new_page()
        page.on("response", on_response)

        log("  Phase 1: Loading homepage...")
        try:
            await page.goto(site_url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(5)
        except Exception as e:
            log(f"  Homepage: {e}")
            await asyncio.sleep(3)

        log("  Phase 2: Scrolling...")
        try:
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(2)
        except Exception:
            pass

        log("  Phase 3: Searching...")
        for term in ["iran", "ukraine", "oil"]:
            try:
                sel = "input[type='search'], input[name='q'], input[name='s'], [placeholder*='earch' i]"
                si = await page.query_selector(sel)
                if si:
                    await si.click()
                    await asyncio.sleep(1)
                    await si.fill(term)
                    await si.press("Enter")
                    await asyncio.sleep(5)
                    break
            except Exception:
                pass

        log("  Phase 4: Articles...")
        try:
            links = await page.query_selector_all("a[href*='/20']")
            for link in links[:3]:
                try:
                    href = await link.get_attribute("href")
                    if href and len(href) > 20 and not href.startswith("#"):
                        await page.goto(urljoin(site_url, href), wait_until="domcontentloaded", timeout=10000)
                        await asyncio.sleep(3)
                except Exception:
                    pass
        except Exception:
            pass

        await browser.close()

    base_host = urlparse(site_url).hostname or ""
    for api in api_responses:
        parsed = urlparse(api["url"])
        if base_host in (parsed.hostname or ""):
            discovered.append({
                "base_url": f"{parsed.scheme}://{parsed.hostname}",
                "endpoint": api["url"],
                "method": api["method"],
                "status": api["status"],
                "sample_response": api["sample_response"][:500],
                "label": label,
            })
    return discovered


async def process_site(target):
    url, label = target["url"], target["label"]
    log(f"\n{'='*60}")
    log(f"Processing: {label} ({url})")
    log(f"{'='*60}")

    apis = await capture_api_calls(url, label)
    log(f"  Found {len(apis)} API endpoints")

    result = {"site": label, "url": url, "apis_found": len(apis), "apis": apis, "spec_generated": None}

    if apis:
        spec = generate_spec(label, url, apis)
        if spec:
            slug = spec["site"]
            d = SPECS_DIR / slug
            d.mkdir(parents=True, exist_ok=True)
            p = d / "spec.json"
            p.write_text(json.dumps(spec, indent=2))
            result["spec_generated"] = str(p)
            log(f"  ✅ Spec: {p}")

    return result


async def process_all(priorities=None):
    state = load_state()
    results = []
    for t in TARGETS:
        if priorities and t.get("p") not in priorities:
            continue
        if t["url"] in state.get("completed", {}):
            log(f"  SKIP (done): {t['label']}")
            continue
        r = await process_site(t)
        state.setdefault("completed", {})[t["url"]] = {
            "date": dt.datetime.now(dt.timezone.utc).isoformat(),
            "apis_found": r["apis_found"],
            "spec_generated": r.get("spec_generated"),
        }
        save_state(state)
        results.append(r)
        await asyncio.sleep(2)
    return results


async def main_async():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", help="Single site URL")
    ap.add_argument("--label", help="Label for single site")
    ap.add_argument("--tier1", action="store_true", help="Tier 1 only")
    ap.add_argument("--tier2", action="store_true", help="Tier 2 only")
    ap.add_argument("--list", action="store_true", help="List targets")
    ap.add_argument("--reset", action="store_true", help="Reset state")
    args = ap.parse_args()

    if args.list:
        print(f"{'P':4s} {'Label':30s} {'URL'}")
        print("-" * 80)
        for t in TARGETS:
            print(f"{t['p']:<4d} {t['label']:30s} {t['url']}")
        return

    if args.reset:
        save_state({"completed": {}, "discovered_apis": {}})
        log("State reset")
        return

    if args.site:
        r = await process_site({"url": args.site, "label": args.label or urlparse(args.site).hostname or args.site})
        print(json.dumps({k: v for k, v in r.items() if k != "apis"}, indent=2))
        return

    if args.tier1 or args.tier2:
        ps = []
        if args.tier1: ps.append(1)
        if args.tier2: ps.append(2)
        results = await process_all(priorities=ps)
        print(f"\n{'='*60}")
        print(f"Done: {len(results)} sites")
        for r in results:
            s = "✅" if r["spec_generated"] else "⚠️"
            print(f"  {s} {r['site']}: {r['apis_found']} APIs → {r.get('spec_generated', 'no spec')}")
        return

    ap.print_help()


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
