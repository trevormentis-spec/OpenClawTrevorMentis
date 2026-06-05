#!/usr/bin/env python3
"""
Reverse-Engineered API Auto-Discovery — finds and generates specs for news APIs.

Scans our source registry for sites that expose well-known API patterns
under the hood (Arc XP, WordPress REST, GraphQL, headless CMS), then
auto-generates spec files that let us collect structured JSON data
instead of scraping HTML.

Usage:
    python3 scripts/discover_reverse_api.py --scan-all          # Scan all sources
    python3 scripts/discover_reverse_api.py --site reuters.com   # Single site test
    python3 scripts/discover_reverse_api.py --report            # Show what's available
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES_FILE = REPO_ROOT / "analyst" / "meta" / "sources.json"
SPECS_DIR = REPO_ROOT / "skills" / "collection" / "_specs"
STATE_FILE = REPO_ROOT / "tasks" / "reverse_api_discovery.json"

# Well-known API patterns to check
API_PROBES = [
    {
        "name": "Arc XP Platform",
        "platform": "arcxp",
        "probe_path": "/pf/api/v3/content/fetch/",
        "check": lambda resp: "content_elements" in resp or "content_alias" in resp,
        "spec_template": "arcxp",
    },
    {
        "name": "WordPress REST API",
        "platform": "wordpress",
        "probe_path": "/wp-json/wp/v2/posts?per_page=3",
        "check": lambda resp: isinstance(resp, list) and any("title" in p for p in resp),
        "spec_template": "wordpress",
    },
    {
        "name": "GraphQL Endpoint",
        "platform": "graphql",
        "probe_path": "/graphql",
        "check": lambda resp: "errors" in resp or "data" in resp,
        "spec_template": "graphql",
    },
    {
        "name": "News API Pattern",
        "platform": "newsapi",
        "probe_path": "/api/v1/news?limit=5",
        "check": lambda resp: isinstance(resp, dict) and ("articles" in resp or "news" in resp or "data" in resp or "items" in resp),
        "spec_template": "newsapi",
    },
    {
        "name": "Arc XP Search",
        "platform": "arcxp",
        "probe_path": "/pf/api/v3/content/fetch/content-api-search?q=iran&size=3&site=arc-anglerfish",
        "check": lambda resp: isinstance(resp, dict) and "content_elements" in resp,
        "spec_template": "arcxp",
    },
    {
        "name": "Headless CMS API",
        "platform": "headless",
        "probe_path": "/api/content/v1/posts?limit=3",
        "check": lambda resp: isinstance(resp, dict) and ("posts" in resp or "results" in resp or "data" in resp),
        "spec_template": "headless",
    },
]


def log(msg: str) -> None:
    print(f"[rev-api] {msg}", file=sys.stderr, flush=True)


def load_sources() -> dict:
    if SOURCES_FILE.exists():
        return json.loads(SOURCES_FILE.read_text())
    return {}


def save_sources(sources: dict) -> None:
    SOURCES_FILE.write_text(json.dumps(sources, indent=2))


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"discovered_apis": {}, "last_scan": None}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def probe_api(base_url: str, probe_path: str, timeout: int = 10) -> tuple[bool, str]:
    """Probe a potential API endpoint. Returns (success, response_preview)."""
    url = base_url.rstrip("/") + probe_path
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            if not body.strip():
                return False, ""
            # Try JSON
            try:
                data = json.loads(body)
                return True, json.dumps(data)[:300]
            except json.JSONDecodeError:
                # Check if it looks like JSON even if partially malformed
                if body.strip().startswith("{") or body.strip().startswith("["):
                    return True, body[:300]
                return False, ""
    except urllib.error.HTTPError as e:
        if e.code == 404 or e.code == 403 or e.code == 401:
            return False, f"HTTP {e.code}"
        if e.code == 200:
            body = e.read().decode("utf-8", errors="replace")[:300]
            return True, body
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)[:100]


def extract_base_url(source_url: str) -> str:
    """Extract the base URL (scheme + hostname) from a source URL."""
    match = re.match(r"(https?://[^/]+)", source_url)
    return match.group(1) if match else source_url


def generate_spec(site_name: str, base_url: str, platform: str, probe_info: dict) -> dict | None:
    """Generate a spec.json for a discovered API."""
    if platform == "arcxp":
        return {
            "site": site_name,
            "version": "1.0.0",
            "transport": "http",
            "base_url": base_url,
            "auth_type": "none",
            "platform": "arc_xp",
            "operations": [
                {
                    "name": "search",
                    "description": f"Search {site_name} articles",
                    "method": "GET",
                    "endpoint": "/pf/api/v3/content/fetch/content-api-search",
                    "params": [
                        {"name": "q", "type": "string", "required": True, "description": "Search query"},
                        {"name": "size", "type": "int", "required": False, "description": "Results count"},
                        {"name": "site", "type": "string", "required": True, "description": "Site identifier"},
                    ],
                    "response_selector": "$.content_elements",
                },
                {
                    "name": "get_collection",
                    "description": f"Fetch a content collection from {site_name}",
                    "method": "GET",
                    "endpoint": "/pf/api/v3/content/fetch/alert-bar-collections",
                    "params": [
                        {"name": "size", "type": "int", "required": False, "description": "Number of items"},
                        {"name": "site", "type": "string", "required": True, "description": "Site identifier"},
                    ],
                    "response_selector": "$.content_elements",
                },
            ],
            "discovered_by": "rev_api_discovery",
            "discovered_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
    elif platform == "wordpress":
        return {
            "site": site_name,
            "version": "1.0.0",
            "transport": "http",
            "base_url": base_url,
            "auth_type": "none",
            "platform": "wordpress",
            "operations": [
                {
                    "name": "get_posts",
                    "description": f"Get recent posts from {site_name}",
                    "method": "GET",
                    "endpoint": "/wp-json/wp/v2/posts",
                    "params": [
                        {"name": "per_page", "type": "int", "required": False, "description": "Posts per page"},
                        {"name": "search", "type": "string", "required": False, "description": "Search term"},
                        {"name": "categories", "type": "int", "required": False, "description": "Category ID"},
                    ],
                    "response_selector": "$",
                },
            ],
            "discovered_by": "rev_api_discovery",
            "discovered_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
    elif platform == "graphql":
        return {
            "site": site_name,
            "version": "1.0.0",
            "transport": "http",
            "base_url": base_url,
            "auth_type": "none",
            "platform": "graphql",
            "operations": [
                {
                    "name": "graphql_query",
                    "description": f"Execute a GraphQL query against {site_name}",
                    "method": "POST",
                    "endpoint": "/graphql",
                    "body_template": '{"query":"{ posts { edges { node { title } } } }"}',
                    "content_type": "application/json",
                    "response_selector": "$.data",
                },
            ],
            "discovered_by": "rev_api_discovery",
            "discovered_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
    return None


def save_spec(site_name: str, spec: dict) -> pathlib.Path | None:
    """Save a generated spec to disk."""
    spec_dir = SPECS_DIR / site_name
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec_path = spec_dir / "spec.json"
    spec_path.write_text(json.dumps(spec, indent=2))
    log(f"Saved spec: {spec_path}")
    return spec_path


def scan_source(source_name: str, source_url: str) -> list[dict]:
    """Scan a single source for reverse-engineerable APIs."""
    base = extract_base_url(source_url)
    discoveries = []

    for probe in API_PROBES:
        found, preview = probe_api(base, probe["probe_path"])
        if found:
            try:
                data = json.loads(preview) if preview.startswith("{") or preview.startswith("[") else {}
                if probe["check"](data if isinstance(data, (dict, list)) else {"raw": preview}):
                    discoveries.append({
                        "source": source_name,
                        "url": base,
                        "platform": probe["platform"],
                        "probe_path": probe["probe_path"],
                        "preview": preview[:200],
                        "status": "api_found",
                    })
                    log(f"  ✅ {source_name} → {probe['name']} at {probe['probe_path']}")
            except Exception:
                pass

    return discoveries


def scan_registry() -> list[dict]:
    """Scan all sources in the registry for discoverable APIs."""
    sources = load_sources()
    durable = sources.get("durable_sources", [])
    state = load_state()
    discoveries = []

    all_urls = set()
    for src in durable:
        url = src.get("url", "")
        if url:
            all_urls.add(url)
        rss = src.get("rss", "")
        if rss:
            all_urls.add(rss)

    log(f"Scanning {len(all_urls)} unique URLs for API endpoints...")

    for url in sorted(all_urls):
        base = extract_base_url(url)
        if base in state.get("discovered_apis", {}):
            log(f"  SKIP (cached): {base}")
            continue

        result = scan_source(base, base)
        discoveries.extend(result)

        # Cache even negatives to avoid re-scanning
        if "discovered_apis" not in state:
            state["discovered_apis"] = {}
        state["discovered_apis"][base] = {
            "last_scan": dt.datetime.now(dt.timezone.utc).isoformat(),
            "apis_found": len(result),
        }

    state["last_scan"] = dt.datetime.now(dt.timezone.utc).isoformat()
    save_state(state)
    return discoveries


def generate_and_save_specs(discoveries: list[dict]) -> list[dict]:
    """Generate spec files from discoveries and add to pipeline."""
    specs_created = []
    for d in discoveries:
        site_name = d["source"].lower().replace(" ", "-").replace("'", "")[:40]
        spec = generate_spec(site_name, d["url"], d["platform"], d)
        if spec:
            path = save_spec(site_name, spec)
            if path:
                specs_created.append({
                    "site": site_name,
                    "url": d["url"],
                    "platform": d["platform"],
                    "spec_path": str(path),
                })
    return specs_created


def print_report() -> None:
    """Print a report of all discovered APIs and existing specs."""
    state = load_state()
    apis = state.get("discovered_apis", {})

    print("\n=== Discovered APIs (from previous scans) ===\n")
    found = {k: v for k, v in apis.items() if v.get("apis_found", 0) > 0}
    if not found:
        print("  No APIs discovered yet. Run --scan-all to probe sources.")
    else:
        for url, info in sorted(found.items(), key=lambda x: x[1]["apis_found"], reverse=True):
            print(f"  {url}")
            print(f"    APIs found: {info['apis_found']} | Last scan: {info['last_scan'][:10]}")
        print()

    print(f"\n=== Existing Specs ({len(list(SPECS_DIR.iterdir())) if SPECS_DIR.exists() else 0}) ===\n")
    if SPECS_DIR.exists():
        for site_dir in sorted(SPECS_DIR.iterdir()):
            if site_dir.is_dir() and (site_dir / "spec.json").exists():
                spec = json.loads((site_dir / "spec.json").read_text())
                platform = spec.get("platform", "unknown")
                ops = len(spec.get("operations", []))
                print(f"  {site_dir.name:30s} platform={platform:15s} operations={ops}")
        print()


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Reverse-engineered API auto-discovery")
    parser.add_argument("--scan-all", action="store_true", help="Scan all sources in registry")
    parser.add_argument("--site", help="Scan a single site by URL")
    parser.add_argument("--report", action="store_true", help="Show discovery report")
    parser.add_argument("--generate-specs", action="store_true", help="Generate spec files from discoveries")
    args = parser.parse_args()

    if args.report:
        print_report()
        return

    if args.scan_all:
        discoveries = scan_registry()
        log(f"Total new API discoveries: {len(discoveries)}")
        for d in discoveries:
            print(f"  {d['source']:30s} → {d['platform']:15s} ({d['probe_path']})")

        if args.generate_specs:
            specs = generate_and_save_specs(discoveries)
            log(f"Generated {len(specs)} spec files")
            for s in specs:
                print(f"  Created: {s['spec_path']}")
        return

    if args.site:
        discoveries = scan_source(args.site, args.site)
        for d in discoveries:
            print(json.dumps(d, indent=2))
        return

    print("Specify --scan-all, --site <url>, or --report")
    sys.exit(1)


if __name__ == "__main__":
    main()
