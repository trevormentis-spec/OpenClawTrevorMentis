#!/usr/bin/env python3
"""
RSS Feed Discovery — auto-discover RSS/Atom feeds from web page URLs.

Given a URL, tries these discovery methods in order:
1. Common RSS feed paths (/feed/, /rss/, /rss.xml, /feed.xml, /atom.xml, /feeds/, /rss/feed/)
2. Link tags in HTML <link rel="alternate" type="application/rss+xml" href="...">
3. Link tags in HTML <link rel="alternate" type="application/atom+xml" href="...">

Usage:
  python3 scripts/rss_discovery.py https://example.com
  python3 scripts/rss_discovery.py --batch unmatched_sources.txt
  python3 scripts/rss_discovery.py --all  # Scan all unmatched from feed-inventory.md
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
INVENTORY_PATH = REPO_ROOT / "analyst" / "meta" / "feed-inventory.md"
CATALOG_PATH = REPO_ROOT / "analyst" / "meta" / "sources_tested.json"

USER_AGENT = "TrevorRSSDiscovery/1.0 (+https://github.com/trevormentis-spec)"
FETCH_TIMEOUT = 10  # seconds

# Common RSS/Atom feed paths to try as a first pass
COMMON_FEED_PATHS = [
    "/feed/",
    "/rss/",
    "/rss.xml",
    "/feed.xml",
    "/atom.xml",
    "/feeds/",
    "/rss/feed/",
    "/news/rss.xml",
    "/en/feed/",
    "/feed/rss/",
    "/rss/feed.xml",
    "/feeds/posts/default",  # Blogger
    "/rss/news.xml",
    "/rss.xml?format=rss",
    "/rss/all.xml",
    "/feed/rss.xml",
]

# Map from region name in inventory to region tag in catalog
REGION_MAP: dict[str, str] = {
    "central_america_caribbean": "central_america_caribbean",
    "central_asia_india": "central_asia_india",
    "china_asia": "china_asia",
    "cyber_threat": "cyber_threat",
    "dashboards": "dashboards",
    "energy": "energy",
    "europe": "europe",
    "iran": "iran",
    "israel_lebanon": "israel_lebanon",
    "maritime": "maritime",
    "middle_east": "middle_east",
    "military_osint": "military_osint",
    "north_america": "north_america",
    "oceania_pacific": "oceania_pacific",
    "prediction_markets": "prediction_markets",
    "russia_ukraine": "russia_ukraine",
    "south_america": "south_america",
    "southeast_asia": "southeast_asia",
    "sub_saharan_africa": "sub_saharan_africa",
    "think_tanks": "think_tanks",
}


def log(msg: str) -> None:
    print(f"[rss_discovery] {msg}", file=sys.stderr, flush=True)


def fetch(url: str, timeout: int = FETCH_TIMEOUT) -> str | None:
    """Fetch a URL. Returns text or None on failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            try:
                return data.decode("utf-8", errors="replace")
            except Exception:
                return None
    except Exception as exc:
        log(f"fetch failed for {url}: {exc}")
        return None


def try_common_paths(base_url: str) -> list[str]:
    """Try common RSS feed paths on the domain. Returns list of working feed URLs."""
    parsed = urllib.parse.urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    found: list[str] = []

    for path in COMMON_FEED_PATHS:
        url = base + path
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=5) as resp:
                content_type = resp.headers.get("Content-Type", "")
                body = resp.read()
                # Check if it looks like RSS/XML
                if "xml" in content_type.lower() or "rss" in content_type.lower() or "atom" in content_type.lower():
                    found.append(url)
                    continue
                # Check body for RSS signature
                body_str = body[:2000].decode("utf-8", errors="replace").lower()
                if "<rss" in body_str or "<feed" in body_str or "<rdf:rdf" in body_str:
                    found.append(url)
                    continue
                # Check if it redirects to an RSS URL
                if resp.url != url and ("rss" in resp.url.lower() or "feed" in resp.url.lower()):
                    found.append(resp.url)
        except Exception:
            continue

    return found


def parse_link_tags(html: str) -> list[str]:
    """Parse HTML link tags to find RSS/Atom feed URLs.

    Handles both:
        <link rel="alternate" type="application/rss+xml" href="...">
        <link rel="alternate" type="application/atom+xml" href="...">
        <link href="..." type="application/rss+xml" rel="alternate">
    """
    found: list[str] = []

    # Pattern 1: <link ... type="application/rss+xml" ... href="..." >
    # Pattern 2: <link ... href="..." ... type="application/rss+xml" ... >
    pattern = re.compile(
        r'<link\s[^>]*'
        r'(?:type=["\'](application/(?:rss|atom)\+xml|application/atom\+xml)["\'].*?href=["\']([^"\']+)["\']'
        r'|href=["\']([^"\']+)["\'].*?type=["\'](application/(?:rss|atom)\+xml)["\'])'
        r'[^>]*>',
        re.IGNORECASE,
    )

    for match in pattern.finditer(html):
        href = match.group(2) or match.group(3)
        if href:
            found.append(href)

    # Pattern 3: <link ... rel="alternate" ... type="application/rss+xml" ... (order-agnostic)
    variation = re.compile(
        r'<link\s[^>]*rel=["\']alternate["\'][^>]*>',
        re.IGNORECASE,
    )

    for link_tag in variation.finditer(html):
        tag = link_tag.group(0)
        if 'application/rss+xml' in tag.lower() or 'application/atom+xml' in tag.lower():
            # Extract href
            href_match = re.search(r'href=["\']([^"\']+)["\']', tag, re.IGNORECASE)
            if href_match:
                href = href_match.group(1)
                if href not in found:
                    found.append(href)

    return found


def resolve_url(href: str, base_url: str) -> str:
    """Resolve a potentially relative URL against the base URL."""
    if href.startswith("http://") or href.startswith("https://"):
        return href

    parsed = urllib.parse.urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    if href.startswith("/"):
        return base + href
    if href.startswith("./"):
        # Relative to current path
        current_dir = urllib.parse.urljoin(base_url, ".")
        return urllib.parse.urljoin(current_dir, href[2:])
    if href.startswith("//"):
        return parsed.scheme + ":" + href

    return urllib.parse.urljoin(base_url, href)


def discover(url: str) -> str:
    """Discover RSS/Atom feed URL for a given web page URL.

    Returns the first working feed URL found, or empty string.
    """
    # Validate URL
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    # Remove trailing slash for normalization
    url = url.rstrip("/")

    # Method 1: Try common RSS feed paths
    log(f"trying common paths for {url}")
    common = try_common_paths(url)
    if common:
        log(f"  found via common paths: {common[0]}")
        return common[0]

    # Method 2: Fetch the page and parse link tags
    log(f"fetching page to parse link tags: {url}")
    html = fetch(url)
    if html:
        feeds = parse_link_tags(html)
        if feeds:
            resolved = resolve_url(feeds[0], url)
            log(f"  found via link tags: {resolved}")
            return resolved

    # Method 3: Try common paths on alternative subdomains
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc

    # Try news subdomain
    if not domain.startswith("news."):
        news_url = f"{parsed.scheme}://news.{domain}"
        log(f"trying news subdomain: {news_url}")
        news_feeds = try_common_paths(news_url)
        if news_feeds:
            log(f"  found via news subdomain: {news_feeds[0]}")
            return news_feeds[0]

    log(f"  no feed found for {url}")
    return ""


def discover_source(source_name: str, source_url: str, region: str) -> dict[str, Any]:
    """Discover RSS feed for a source and return result dict."""
    result: dict[str, Any] = {
        "source_name": source_name,
        "source_url": source_url,
        "region": region,
        "found_rss": "",
        "status": "failed",
    }

    if not source_url:
        result["status"] = "no_url"
        return result

    rss_url = discover(source_url)
    if rss_url:
        result["found_rss"] = rss_url
        result["status"] = "found"
    else:
        result["status"] = "not_found"

    return result


def process_batch(filepath: str) -> list[dict[str, Any]]:
    """Process a batch file with source info.

    Format: one entry per line:
        source_name|website_url|region
    or just:
        url
    """
    results: list[dict[str, Any]] = []
    path = pathlib.Path(filepath)

    if not path.exists():
        log(f"batch file not found: {filepath}")
        return results

    lines = path.read_text(encoding="utf-8").strip().split("\n")
    log(f"processing {len(lines)} entries from {filepath}")

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        parts = [p.strip() for p in line.split("|")]

        if len(parts) >= 2:
            source_name, source_url = parts[0], parts[1]
            region = parts[2] if len(parts) >= 3 else "unknown"
        else:
            source_name = line
            source_url = line
            region = "unknown"

        log(f"  [{region}] {source_name}: {source_url}")
        result = discover_source(source_name, source_url, region)
        results.append(result)

        status_icon = "✓" if result["status"] == "found" else "✗"
        print(f"{status_icon} {source_name:40s} → {result['found_rss'] or '(not found)'}")

    # CSV summary
    csv_path = path.parent / "rss_discovery_results.csv"
    with open(csv_path, "w") as f:
        f.write("source_name,source_url,region,found_rss,status\n")
        for r in results:
            f.write(f"{r['source_name']},{r['source_url']},{r['region']},{r['found_rss']},{r['status']}\n")
    log(f"results written to {csv_path}")

    # Summary
    found_count = sum(1 for r in results if r["status"] == "found")
    log(f"batch complete: {found_count}/{len(results)} RSS feeds discovered")
    print(f"\n📊 Summary: {found_count}/{len(results)} RSS feeds discovered", file=sys.stderr)

    return results


def extract_unmatched_sources() -> list[tuple[str, str, str]]:
    """Parse feed-inventory.md for unmatched sources and try to extract URLs.

    Returns list of (source_name, url_or_empty, region) tuples.
    The registry markdown files only have names, not URLs.
    The sourc names are extracted via heuristics.

    We use the existing feed catalog (sources_tested.json) and try to find
    potential source URLs by looking for matching names.
    """
    if not INVENTORY_PATH.exists():
        log(f"inventory not found: {INVENTORY_PATH}")
        return []

    text = INVENTORY_PATH.read_text(encoding="utf-8")
    lines = text.split("\n")

    # Parse the unmatched sources table
    sources: list[tuple[str, str, str]] = []
    in_table = False

    for line in lines:
        # Detect table start
        if line.strip().startswith("| Region | Source Name |"):
            in_table = True
            continue
        if in_table and line.strip().startswith("|---|---|"):
            continue
        if in_table:
            # Empty line or new section ends the table
            if not line.strip() or line.strip().startswith("##") or line.strip().startswith("---"):
                in_table = False
                continue

            # Parse table row: | region | name |
            if line.strip().startswith("|") and line.strip().endswith("|"):
                parts = [p.strip() for p in line.strip().split("|")]
                if len(parts) >= 3:
                    region = parts[1]
                    name = parts[2]
                    if region and name:
                        sources.append((name, "", region))

    log(f"extracted {len(sources)} unmatched sources from inventory")
    return sources


def find_source_url(name: str, catalog: list[dict[str, Any]]) -> str:
    """Try to find a website URL for a source name from the catalog."""
    name_lower = name.lower().strip()

    for entry in catalog:
        entry_name = entry.get("name", "").lower().strip()
        entry_url = entry.get("url", "")

        # Direct match
        if name_lower == entry_name:
            return entry_url

        # Substring match
        if name_lower in entry_name or entry_name in name_lower:
            # Only return if it looks like a real website (not feedspot)
            if entry_url and "feedspot" not in entry_url.lower():
                return entry_url

    return ""


def process_all() -> list[dict[str, Any]]:
    """Process all unmatched sources from feed-inventory.md.

    For each unmatched source, uses the catalog to find a source URL,
    then runs RSS discovery.
    """
    # Load catalog
    if not CATALOG_PATH.exists():
        log(f"catalog not found: {CATALOG_PATH}")
        return []

    try:
        catalog = json.loads(CATALOG_PATH.read_text())
    except Exception as exc:
        log(f"catalog load failed: {exc}")
        return []

    # Get unmatched sources
    sources = extract_unmatched_sources()
    if not sources:
        return []

    # Try to find URLs for each source
    named_sources: list[tuple[str, str, str]] = []
    for name, url, region in sources:
        if url:
            named_sources.append((name, url, region))
        else:
            catalog_url = find_source_url(name, catalog)
            named_sources.append((name, catalog_url, region))

    # Write to batch file for processing
    batch_path = REPO_ROOT / "tasks" / "unmatched_for_discovery.txt"
    batch_path.parent.mkdir(parents=True, exist_ok=True)

    with open(batch_path, "w") as f:
        for name, url, region in named_sources:
            f.write(f"{name}|{url}|{region}\n")

    log(f"wrote {len(named_sources)} sources to {batch_path}")
    print(f"\n📝 Wrote {len(named_sources)} unmatched sources to {batch_path}", file=sys.stderr)

    # Now process the batch
    return process_batch(str(batch_path))


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 0

    mode = sys.argv[1]

    if mode == "--batch":
        if len(sys.argv) < 3:
            print("Usage: rss_discovery.py --batch <filepath>")
            return 1
        process_batch(sys.argv[2])
        return 0

    if mode == "--all":
        process_all()
        return 0

    # Single URL mode
    url = sys.argv[1]
    if url.startswith("http://") or url.startswith("https://"):
        result = discover(url)
        if result:
            print(result)
        else:
            print("")
            print("NO FEED FOUND", file=sys.stderr)
            return 1
        return 0
    else:
        print(f"Unknown mode: {mode}")
        print(__doc__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
