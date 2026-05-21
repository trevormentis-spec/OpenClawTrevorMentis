#!/usr/bin/env python3
"""
Browser-based API discovery — lightweight Playwright probe.

Instead of full page navigation, injects JS to extract the page's
API configuration and captures the first page load's network calls.

Usage:
    python3 scripts/browser_api_probe.py --list
    python3 scripts/browser_api_probe.py https://www.timesofisrael.com
    python3 scripts/browser_api_probe.py --batch       # Run all targets
"""
from __future__ import annotations

import asyncio
import json
import pathlib
import re
import sys
from urllib.parse import urlparse

import subprocess

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SPECS_DIR = REPO_ROOT / "skills" / "collection" / "_specs"

FILTER_DOMAINS = [
    "google", "facebook", "doubleclick", "youtube", "imasdk",
    "cdn-cgi", "recaptcha", "gstatic", "googlesyndication",
    "hotjar", "sentry", "datadog", "fullstory",
]


def log(msg):
    print(f"[probe] {msg}", file=sys.stderr, flush=True)


async def probe_site(url: str) -> dict:
    """Open a site, capture network responses, extract API config."""
    from playwright.async_api import async_playwright

    hostname = urlparse(url).hostname or "unknown"
    api_calls = []
    js_config = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox", "--disable-setuid-sandbox",
                "--disable-dev-shm-usage", "--disable-gpu",
                "--js-flags=--max_old_space_size=128",
            ],
        )
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            viewport={"width": 1280, "height": 720},
            java_script_enabled=True,
        )
        page = await ctx.new_page()

        # Intercept JSON responses
        async def on_response(response):
            if any(d in response.url for d in FILTER_DOMAINS):
                return
            ct = response.headers.get("content-type", "")
            if "json" not in ct.lower():
                return
            if len(response.url) < 20 or response.url.startswith("data:"):
                return
            try:
                body = await response.text()
                json.loads(body)  # validate
                api_calls.append({
                    "url": response.url,
                    "method": response.request.method,
                    "status": response.status,
                    "size": len(body),
                })
            except Exception:
                pass

        page.on("response", on_response)

        # Load page
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(3)
        except Exception as e:
            log(f"  load: {e}")
            await asyncio.sleep(2)

        # Extract API config from window/JS
        try:
            js_config = await page.evaluate("""() => {
                const config = {};
                // Arc XP
                if (window.arcSite) config.arcSite = window.arcSite;
                if (window.arcgen) config.arcgen = true;
                // WordPress
                if (window.wpApiSettings) config.wpApiSettings = window.wpApiSettings;
                // Next.js data
                try {
                    const el = document.getElementById('__NEXT_DATA__');
                    if (el) config.nextData = JSON.parse(el.textContent);
                } catch(e) {}
                // Page metadata
                const metas = document.querySelectorAll('meta[name], meta[property]');
                const metaObj = {};
                metas.forEach(m => {
                    const name = m.getAttribute('name') || m.getAttribute('property') || '';
                    const content = m.getAttribute('content') || '';
                    if (content) metaObj[name] = content;
                });
                config.meta = metaObj;
                // Detect CMS/API URLs in the page
                const scripts = Array.from(document.scripts).map(s => s.src).filter(s => s);
                config.script_srcs = scripts.slice(0, 10);
                // Any JSON-LD
                try {
                    const jld = document.querySelectorAll('script[type="application/ld+json"]');
                    config.jsonld = Array.from(jld).map(j => JSON.parse(j.textContent));
                } catch(e) {}
                return config;
            }""")
        except Exception as e:
            log(f"  evaluate: {e}")

        await browser.close()

    # Filter to same-origin API calls
    same_origin = []
    for api in api_calls:
        api_host = urlparse(api["url"]).hostname or ""
        if hostname in api_host:
            same_origin.append(api)

    return {
        "hostname": hostname,
        "url": url,
        "same_origin_apis": same_origin,
        "third_party_apis": [a for a in api_calls if a not in same_origin],
        "js_config": js_config,
    }


def analyze_arcxp(result: dict) -> dict | None:
    """Check if the site uses Arc XP and extract site identifier."""
    cfg = result.get("js_config", {})
    meta = cfg.get("meta", {})
    next_data = cfg.get("nextData", {})

    # Arc XP site identifiers
    arc_site = cfg.get("arcSite", "")
    if not arc_site:
        # Check JSON-LD
        for j in cfg.get("jsonld", []):
            if isinstance(j, dict):
                arc_site = j.get("arc-site", "") or j.get("site", "")
                if arc_site:
                    break

    if arc_site:
        return {
            "platform": "arcxp",
            "site_id": arc_site,
            "base_url": result["url"].rstrip("/"),
        }

    return None


def detect_platform(result: dict) -> str:
    """Detect CMS/platform from JS config."""
    cfg = result.get("js_config", {})
    meta = cfg.get("meta", {})
    scripts = cfg.get("script_srcs", [])

    all_text = str(cfg).lower()
    script_text = " ".join(scripts)

    if cfg.get("arcSite"):
        return "arcxp"
    if cfg.get("wpApiSettings"):
        return "wordpress"
    if "drupal" in all_text or "/jsonapi/" in script_text:
        return "drupal"
    if "next.js" in all_text or "_next/" in script_text:
        return "nextjs"
    if "gatsby" in all_text:
        return "gatsby"
    if "graphql" in all_text:
        return "graphql"
    if "ghost" in all_text:
        return "ghost"

    generator = meta.get("generator", "")
    if "wordpress" in generator.lower():
        return "wordpress"
    if "drupal" in generator.lower():
        return "drupal"

    return "unknown"


async def main_async():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("url", nargs="?", help="Site URL to probe")
    ap.add_argument("--batch", action="store_true", help="Run against known targets")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    targets = [
        "https://www.timesofisrael.com",
        "https://www.haaretz.com",
        "https://www.al-monitor.com",
        "https://www.csis.org",
        "https://www.cfr.org",
        "https://www.understandingwar.org",
        "https://www.lemonde.fr/en/",
        "https://www.ynet.co.il",
        "https://www.scmp.com",
        "https://www.nikkei.com",
        "https://asia.nikkei.com",
        "https://english.elpais.com",
        "https://www.elmundo.es",
        "https://www.kommersant.ru/english",
        "https://www.reforma.com",
        "https://www.milenio.com",
        "https://www.eluniversal.com.mx",
    ]

    if args.list:
        for t in targets:
            print(t)
        return

    if args.batch:
        for url in targets:
            log(f"Probing {url}")
            result = await probe_site(url)
            platform = detect_platform(result)
            arc = analyze_arcxp(result)

            originals = len(result.get("same_origin_apis", []))
            third = len(result.get("third_party_apis", []))

            status = "✅" if arc or platform != "unknown" else "⚠️"
            plat = f" ({arc['platform']}:{arc['site_id']})" if arc else f" ({platform})"
            print(f"{status} {urlparse(url).hostname:30s} platform={plat:25s} apis={originals}+{third}")
            if arc:
                print(f"   → spec candidate: arc site_id={arc['site_id']}")

            await asyncio.sleep(1)
        return

    if args.url:
        result = await probe_site(args.url)
        print(json.dumps({
            "hostname": result["hostname"],
            "platform": detect_platform(result),
            "arcxp": analyze_arcxp(result),
            "same_origin_api_count": len(result["same_origin_apis"]),
            "api_endpoints": [a["url"] for a in result["same_origin_apis"][:10]],
            "js_config_keys": list(result["js_config"].keys()),
        }, indent=2))
        return

    ap.print_help()


def main():
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
