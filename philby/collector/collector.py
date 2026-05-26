#!/usr/bin/env python3
"""
Philby Collector Sub-Agent — Continuous Source Health & Discovery.

Runs every ~30 minutes as a lightweight sub-agent that:
  1. Tests a batch of sources from the registry (staggered to avoid rate limits)
  2. Logs dead/403/timeout feeds for pruning
  3. Discovers new sources via Brave web search (gap regions)
  4. Updates the tested-sources registry
  5. Reports health metrics

Designed to be called from runtime-health.sh or heartbeat system Phase A/B/C.

Usage:
    python3 philby/collector/collector.py --quick           # Quick batch test (50 sources)
    python3 philby/collector/collector.py --discover        # Discovery for gap regions
    python3 philby/collector/collector.py --full            # Full cycle (test + discover)
    python3 philby/collector/collector.py --status          # Show collector state
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import random
import ssl
import sys
import time
import urllib.parse
import urllib.request
from typing import Any

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
STATE_FILE = REPO / "skills" / "philby-collector" / "state" / "collector_state.json"
SOURCES_FILE = REPO / "analyst" / "meta" / "sources.json"
TESTED_FILE = REPO / "analyst" / "meta" / "sources_tested.json"
HEALTH_FILE = REPO / "brain" / "memory" / "semantic" / "feed-health-latest.json"

BATCH_SIZE = 50  # Number of sources to test per cycle
TIMEOUT_SECONDS = 8
GAP_REGIONS = ["southeast_asia", "caribbean", "central_america", "africa", "north_africa"]


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[philby-collector {ts}] {msg}", file=sys.stderr, flush=True)


def load_state() -> dict:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError,):
            pass
    return {
        "version": 1,
        "last_batch_index": 0,
        "total_tested": 0,
        "total_ok": 0,
        "total_failed": 0,
        "discovery_cycles": 0,
        "last_full_cycle": None,
    }


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def load_sources() -> list[dict]:
    if SOURCES_FILE.exists():
        try:
            data = json.loads(SOURCES_FILE.read_text())
            return data.get("durable_sources", [])
        except (json.JSONDecodeError,):
            pass
    return []


def test_source(url: str, timeout: int = TIMEOUT_SECONDS) -> tuple[str, int | None]:
    """Test a single source URL. Returns (status, http_code)."""
    if not url or not url.startswith("http"):
        return "invalid_url", None

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; PhilbyCollector/1.0)"},
        )
        resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        return ("ok", resp.status)
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return ("forbidden", 403)
        elif e.code == 404:
            return ("not_found", 404)
        return (f"http_{e.code}", e.code)
    except urllib.error.URLError as e:
        return ("dns_fail" if "Name or service not known" in str(e) else "timeout", None)
    except Exception as e:
        return ("error", None)


def batch_test_sources(state: dict) -> dict:
    """Test the next batch of sources from the registry."""
    sources = load_sources()
    if not sources:
        log("No sources to test")
        return state

    batch_index = state.get("last_batch_index", 0)
    total = len(sources)

    # Wrap around
    if batch_index >= total:
        batch_index = 0

    batch = sources[batch_index : batch_index + BATCH_SIZE]
    if len(batch) < BATCH_SIZE:
        # Grab from the beginning to fill up
        batch += sources[: BATCH_SIZE - len(batch)]

    log(f"Testing batch {batch_index}-{batch_index+len(batch)} of {total}")

    results = []
    ok_count = 0
    fail_count = 0
    for i, source in enumerate(batch):
        url = source.get("url", "")
        name = source.get("name", "?")
        status, code = test_source(url)
        if status == "ok":
            ok_count += 1
        else:
            fail_count += 1
        results.append({
            "name": name,
            "url": url,
            "status": status,
            "code": code,
            "tested_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
        if (i + 1) % 10 == 0:
            log(f"  {i+1}/{len(batch)}: {ok_count} ok, {fail_count} failed")

    # Save tested results (append to existing)
    tested = []
    if TESTED_FILE.exists():
        try:
            existing = json.loads(TESTED_FILE.read_text())
            if isinstance(existing, list):
                tested = existing
            elif isinstance(existing, dict) and 'results' in existing:
                tested = existing['results']
        except (json.JSONDecodeError,):
            pass
    tested.extend(results)
    # Keep only last 1000 entries to avoid unbounded growth
    if len(tested) > 1000:
        tested = tested[-1000:]
    TESTED_FILE.write_text(json.dumps(tested, indent=2))

    # Update state
    state["last_batch_index"] = batch_index + len(batch)
    if state["last_batch_index"] >= total:
        state["last_batch_index"] = 0  # Full pass completed
        state["last_full_cycle"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    state["total_tested"] = state.get("total_tested", 0) + len(batch)
    state["total_ok"] = state.get("total_ok", 0) + ok_count
    state["total_failed"] = state.get("total_failed", 0) + fail_count

    # Save health report
    health_pct = (ok_count / len(batch) * 100) if batch else 0
    health_report = {
        "timestamp": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "batch_size": len(batch),
        "ok": ok_count,
        "failed": fail_count,
        "health_pct": round(health_pct, 1),
        "total_sources": total,
        "test_completed_pct": round(
            (state["last_batch_index"] / total * 100) if total else 0, 1
        ),
    }
    HEALTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    HEALTH_FILE.write_text(json.dumps(health_report, indent=2))

    log(f"Batch results: {ok_count}/{len(batch)} OK ({health_pct:.0f}%) — saved to {TESTED_FILE.name}")
    save_state(state)
    return state


def discover_sources(state: dict, region: str = "") -> list[dict]:
    """Discover new sources for gap regions via web search."""
    api_key = os.environ.get("BRAVE_API_KEY", "")
    if not api_key:
        log("No BRAVE_API_KEY — skipping discovery")
        return []

    regions_to_search = [region] if region else GAP_REGIONS
    candidates = []

    for r in regions_to_search:
        search_queries = [
            f"{r.replace('_', ' ')} news RSS feed intelligence",
            f"{r.replace('_', ' ')} current events analysis feed",
        ]
        for query in search_queries:
            try:
                req = urllib.request.Request(
                    f"https://api.search.brave.com/res/v1/web/search?q={urllib.parse.quote(query)}&count=5",
                    headers={
                        "Accept": "application/json",
                        "Accept-Encoding": "gzip",
                        "X-Subscription-Token": api_key,
                    },
                )
                resp = urllib.request.urlopen(req, timeout=10)
                data = json.loads(resp.read())
                for result in data.get("web", {}).get("results", []):
                    candidates.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "description": result.get("description", "")[:200],
                        "region": r,
                        "found_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    })
                time.sleep(1)  # Rate limit
            except Exception:
                continue

    state["discovery_cycles"] = state.get("discovery_cycles", 0) + 1

    # Save candidates
    discovery_file = REPO / "brain" / "memory" / "semantic" / "feed-discovery-latest.json"
    discovery_file.parent.mkdir(parents=True, exist_ok=True)
    discovery_file.write_text(json.dumps({
        "timestamp": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "regions_searched": regions_to_search,
        "candidates": candidates,
    }, indent=2))

    log(f"Discovery: {len(candidates)} candidates from {len(regions_to_search)} regions")
    save_state(state)
    return candidates


def cmd_quick(state: dict) -> None:
    """Quick batch test — test 50 sources."""
    state = batch_test_sources(state)
    print(f"Tested {BATCH_SIZE} sources. Total tracked: {state['total_tested']}")


def cmd_discover(state: dict, region: str = "") -> None:
    """Run discovery for gap regions."""
    candidates = discover_sources(state, region)
    print(f"Found {len(candidates)} candidates across {len(GAP_REGIONS)} regions")


def cmd_full(state: dict) -> None:
    """Full cycle: test + discover."""
    state = batch_test_sources(state)
    if random.random() < 0.2:  # ~20% chance of running discovery each full cycle
        discover_sources(state)
    print(f"Full cycle: tested {BATCH_SIZE}, discovered pending")


def cmd_status(state: dict) -> None:
    """Show collector state."""
    sources = load_sources()
    print(f"\nPhilby Collector Status")
    print(f"{'─' * 50}")
    print(f"  State version: {state.get('version', 1)}")
    print(f"  Total sources: {len(sources)}")
    print(f"  Sources tested: {state.get('total_tested', 0)}")
    print(f"  OK: {state.get('total_ok', 0)}")
    print(f"  Failed: {state.get('total_failed', 0)}")
    print(f"  Batch index: {state.get('last_batch_index', 0)}/{len(sources)}")
    print(f"  Discovery cycles: {state.get('discovery_cycles', 0)}")
    print(f"  Last full cycle: {state.get('last_full_cycle', 'never')}")
    if TESTED_FILE.exists():
        raw = json.loads(TESTED_FILE.read_text())
        tested = raw if isinstance(raw, list) else raw.get('results', [])
        ok = sum(1 for t in tested if isinstance(t, dict) and t.get("status") == "ok")
        print(f"  Tested registry: {len(tested)} entries ({ok} OK)")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Philby Collector Sub-Agent")
    parser.add_argument("--quick", action="store_true", help="Quick batch test (50 sources)")
    parser.add_argument("--discover", nargs="?", const="", default=None, help="Discover sources for gap regions")
    parser.add_argument("--full", action="store_true", help="Full cycle: test + discover")
    parser.add_argument("--status", action="store_true", help="Show collector state")
    args = parser.parse_args()

    state = load_state()

    if args.status:
        cmd_status(state)
    elif args.full:
        cmd_full(state)
    elif args.discover is not None:
        cmd_discover(state, args.discover if args.discover else "")
    elif args.quick:
        cmd_quick(state)
    else:
        # Default: quick test
        cmd_quick(state)

    return 0


if __name__ == "__main__":
    sys.exit(main())
