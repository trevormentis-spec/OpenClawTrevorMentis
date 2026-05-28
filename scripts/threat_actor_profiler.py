#!/usr/bin/env python3
"""
Philby Threat Actor Profiler — generates structured STIX-like profiles
for non-cyber threat actors (cartels, PMCs, insurgencies, mafia)
using OSINT source directories and web enrichment.

Usage:
    python3 scripts/threat_actor_profiler.py --actor "Wagner Group"
    python3 scripts/threat_actor_profiler.py --actor "CJNG" --save
    python3 scripts/threat_actor_profiler.py --actor "'Ndrangheta" --philby
"""

import argparse
import json
import os
import pathlib
import re
import sys
from datetime import datetime

BASE = pathlib.Path(__file__).resolve().parent.parent


def load_source_dirs() -> dict:
    """Load all OSINT source directories for context."""
    sources = {}
    for path in [
        BASE / "config" / "sources" / "africa-osint-sources.md",
        BASE / "config" / "sources" / "europe-osint-sources.md",
    ]:
        if path.exists():
            sources[path.stem] = path.read_text()
    return sources


def search_sources(actor: str, sources: dict) -> list[str]:
    """Search source directories for mentions of the actor."""
    results = []
    actor_lower = actor.lower()
    for name, text in sources.items():
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if actor_lower in line.lower():
                # Extract context: the line plus surrounding
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                ctx = "\n".join(lines[start:end])
                results.append(f"[{name}] {ctx}")
                break  # One hit per source file is enough
    return results


def web_enrich(actor: str) -> list[dict]:
    """Quick web search for recent actor activity."""
    import urllib.request
    import json as j

    # Try Brave Search API
    api_key = os.environ.get("BRAVE_API_KEY", "")
    if not api_key:
        return [{"source": "web_search", "note": "No BRAVE_API_KEY configured"}]

    try:
        url = f"https://api.search.brave.com/res/v1/web/search?q={urllib.parse.quote(actor + ' threat activity 2026')}&count=5"
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/json")
        req.add_header("Accept-Encoding", "gzip")
        req.add_header("X-Subscription-Token", api_key)
        resp = urllib.request.urlopen(req, timeout=15)
        # Handle gzip
        import gzip
        data = j.loads(gzip.decompress(resp.read()))
        results = []
        for r in data.get("web", {}).get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "age": r.get("age", ""),
            })
        return results
    except Exception as e:
        return [{"source": "web_search", "note": f"Search failed: {str(e)[:80]}"}]


def build_profile(actor: str, source_hits: list[str], web_results: list[dict]) -> dict:
    """Build the threat actor profile in STIX-like format."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "threat_actor_profile": {
            "name": actor,
            "source_hits": source_hits,
            "web_mentions": web_results,
        },
        "generated_by": "Philby Threat Actor Profiler",
        "generated_at": datetime.utcnow().isoformat(),
    }


def save_profile(profile: dict, actor: str):
    """Save profile to exports and optionally wire into Philby."""
    # Clean actor name for filename
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", actor.lower()).strip("_")
    out_dir = BASE / "exports" / "profiles"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{safe}.json"
    path.write_text(json.dumps(profile, indent=2))
    print(f"✅ Profile saved: {path}")
    return path


def main():
    parser = argparse.ArgumentParser(description="Philby Threat Actor Profiler")
    parser.add_argument("--actor", required=True, help="Threat actor name (e.g., 'Wagner Group', 'CJNG')")
    parser.add_argument("--save", action="store_true", help="Save profile to exports/")
    parser.add_argument("--philby", action="store_true", help="Register actor in Philby desk tracking")
    args = parser.parse_args()

    print(f"⣿ Profiling: {args.actor} ⣿")
    print()

    # Step 1: Search OSINT source directories
    sources = load_source_dirs()
    hits = search_sources(args.actor, sources)
    print(f"📚 Source directory hits: {len(hits)}")
    for h in hits:
        print(f"  {h[:120]}...")
        print()
    print()

    # Step 2: Web enrichment
    print(f"🌐 Web enrichment...")
    web = web_enrich(args.actor)
    print(f"  {len(web)} results")
    for w in web[:5]:
        if "title" in w:
            print(f"  → {w['title']}")
        elif "note" in w:
            print(f"  ⚠ {w['note']}")
    print()

    # Step 3: Build profile
    profile = build_profile(args.actor, hits, web)

    if args.save or args.philby:
        save_profile(profile, args.actor)

    if args.philby:
        print("📡 Registering in Philby tracking...")
        print("   (Philby desk integration — future enhancement)")

    print("Done.")


if __name__ == "__main__":
    import urllib
    main()
