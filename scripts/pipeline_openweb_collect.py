#!/usr/bin/env python3
"""
OpenWeb Pipeline Collector — integrates openweb API specs into the daily collection cycle.

Replaces RSS/DOM for sites that have openweb specs or custom _specs/ definitions.
Runs as an additional collection phase before RSS fallback in the daily brief pipeline.

Handles:
- Mexico custom specs (El Financiero, Animal Politico, La Jornada)
- openweb built-in news sites (Reuters, BBC, CNN, Bloomberg)
- Wikipedia page-change monitoring for intel tracking
- All outputs formatted as pipeline incidents

Usage:
    python3 scripts/pipeline_openweb_collect.py          # Full run (all active)
    python3 scripts/pipeline_openweb_collect.py --mexico  # Mexico sources only
    python3 scripts/pipeline_openweb_collect.py --wiki-monitor  # Wikipedia changes only
    python3 scripts/pipeline_openweb_collect.py --list    # List available spec-backed sources
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# ============================================================
# Active source definitions
# ============================================================

# Mexico custom specs — these are our own reverse-engineered specs
MEXICO_SPECS = {
    "elfinanciero": {
        "label": "El Financiero",
        "operation": "get_collection",
        "query_params": '{"content_alias":"economia","size":5,"site":"elfinanciero"}',
        "response_path": ["content_elements"],
        "admiralty": ("C", 3),
    },
    "animalpolitico": {
        "label": "Animal Politico",
        "operation": "get_homepage_articles",
        "query_params": "",  # GraphQL — uses embedded query
        "response_path": [],
        "admiralty": ("C", 3),
    },
    "jornada": {
        "label": "La Jornada",
        "operation": "get_suplementos",
        "query_params": "",
        "response_path": [],
        "admiralty": ("C", 3),
    },
}

# openweb built-in news sites — filtered to Mexico-relevant outlets
NEWS_SITES = {
    "reuters": {"label": "Reuters", "op": "search", "admiralty": ("B", 2)},
    "bbc-news": {"label": "BBC News", "op": "search", "admiralty": ("B", 2)},
    "cnn": {"label": "CNN", "op": "search", "admiralty": ("B", 2)},
    "bloomberg": {"label": "Bloomberg", "op": "search", "admiralty": ("B", 2)},
}

# Wikipedia pages to monitor for intel-relevant changes
WIKI_MONITOR_PAGES = [
    "CJNG",
    "Sinaloa_Cartel",
    "Gulf_Cartel",
    "Claudia_Sheinbaum",
    "United_States–Mexico–Canada_Agreement",
    "2026_FIFA_World_Cup",
    "List_of_drug_cartels_in_Mexico",
    "Mexican_drug_war",
]

WIKI_STATE_FILE = REPO_ROOT / "tasks" / "wiki_monitor_state.json"


def log(msg: str) -> None:
    print(f"[ow-pipeline] {msg}", file=sys.stderr, flush=True)


def call_openweb(site: str, op: str, params: str = "") -> dict | None:
    """Call openweb CLI and return parsed result."""
    cmd = ["openweb", site, op]
    if params:
        cmd.append(params)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            return data
        # Check for output file pattern
        if result.stdout.strip():
            try:
                data = json.loads(result.stdout)
                if isinstance(data, dict) and data.get("output"):
                    with open(data["output"]) as f:
                        return json.loads(data["output"])
            except json.JSONDecodeError:
                pass
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        log(f"openweb call failed for {site}/{op}: {e}")
    return None


def call_custom_spec(site: str, label: str) -> list[dict]:
    """Call a custom spec by hitting its API endpoints directly."""
    spec_path = REPO_ROOT / "skills" / "collection" / "_specs" / site / "spec.json"
    if not spec_path.exists():
        log(f"  SKIP: no spec file at {spec_path}")
        return []

    try:
        spec = json.loads(spec_path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        log(f"  ERROR loading spec: {e}")
        return []

    base = spec.get("base_url", "")
    items = []

    for op in spec.get("operations", [])[:2]:  # Try first 2 ops
        endpoint = op.get("endpoint", "")
        method = op.get("method", "GET")
        params = {p["name"]: p.get("description", "") for p in op.get("params", []) if p.get("required")}

        # Handle path params
        url_path = endpoint
        if "{" in endpoint:
            # Skip operations with unresolved path params
            log(f"  SKIP {op['name']}: requires path params")
            continue

        url = base.rstrip("/") + url_path
        log(f"  GET {url}")

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                items.append({
                    "source": label,
                    "operation": op["name"],
                    "method": "reverse_engineered",
                    "data_preview": str(data)[:500],
                    "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                })
                log(f"  → {op['name']}: {len(str(data))} bytes")
        except Exception as e:
            log(f"  ERROR {op['name']}: {e}")

    return items


def collect_news_sites(query: str = "Mexico") -> list[dict]:
    """Collect from openweb built-in news sites."""
    items = []
    for site, cfg in NEWS_SITES.items():
        log(f"Fetching {cfg['label']} for '{query}'...")
        data = call_openweb(site, cfg["op"], json.dumps({"q": query, "size": 5}))
        if data:
            items.append({
                "source": cfg["label"],
                "method": "openweb",
                "data_preview": str(data)[:500],
                "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            })
            log(f"  → {cfg['label']}: data received")
        else:
            log(f"  → {cfg['label']}: no data")
    return items


def check_wiki_changes() -> list[dict]:
    """Check monitored Wikipedia pages for content changes. Returns alerts."""
    changes = []
    state = {}
    if WIKI_STATE_FILE.exists():
        try:
            state = json.loads(WIKI_STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            state = {}

    for page in WIKI_MONITOR_PAGES:
        data = call_openweb("wikipedia", "getPageSummary", json.dumps({"title": page.replace("_", " ")}))
        if not data:
            continue

        revision = data.get("revision", "")
        extract = data.get("extract", "")[:500]
        old_revision = state.get(page, {}).get("revision")

        if old_revision and old_revision != revision:
            changes.append({
                "page": page,
                "old_revision": old_revision,
                "new_revision": revision,
                "extract_preview": extract[:200],
                "detected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            })
            log(f"  ⚠️ CHANGE DETECTED: {page} ({old_revision} → {revision})")
        elif not old_revision:
            log(f"  ✅ Tracking new page: {page} (rev {revision})")

        state[page] = {"revision": revision, "last_checked": dt.datetime.now(dt.timezone.utc).isoformat()}

    WIKI_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    WIKI_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))
    return changes


def write_pipeline_record(source: str, method: str, payload: dict) -> None:
    """Write a collection record to the SQLite+JSONL pipeline."""
    record = {
        "source": source,
        "site_spec_version": "pipeline-v1",
        "method": method,
        "nato_admiralty_source_rating": "B" if method == "openweb" else "C",
        "nato_admiralty_info_rating": "2" if method == "openweb" else "3",
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "payload": {**payload, "qc_status": "PENDING_HUMAN_ANALYST_QC_REVIEW"},
    }
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "append_collection_record.py"),
         "--record", json.dumps(record)],
        capture_output=True, timeout=10,
    )


def list_sources() -> None:
    """List all spec-backed sources available for collection."""
    print("=== Mexico custom specs ===")
    for site, cfg in MEXICO_SPECS.items():
        print(f"  {site:20s} - {cfg['label']} (admiralty: {cfg['admiralty'][0]}-{cfg['admiralty'][1]})")
    print("\n=== openweb built-in news sites ===")
    for site, cfg in NEWS_SITES.items():
        print(f"  {site:20s} - {cfg['label']} (admiralty: {cfg['admiralty'][0]}-{cfg['admiralty'][1]})")
    print(f"\n=== Wikipedia monitored pages ({len(WIKI_MONITOR_PAGES)}) ===")
    for p in WIKI_MONITOR_PAGES:
        print(f"  {p}")


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenWeb Pipeline Collector")
    parser.add_argument("--mexico", action="store_true", help="Mexico custom specs only")
    parser.add_argument("--news", action="store_true", help="openweb news sites only")
    parser.add_argument("--wiki-monitor", action="store_true", help="Wikipedia change monitor only")
    parser.add_argument("--list", action="store_true", help="List available spec-backed sources")
    parser.add_argument("--query", default="Mexico", help="Search query for news sites")
    args = parser.parse_args()

    if args.list:
        list_sources()
        return 0

    run_all = not (args.mexico or args.news or args.wiki_monitor)

    total_items = 0

    # Mexico custom specs
    if run_all or args.mexico:
        log("=== Mexico custom specs ===")
        for site in MEXICO_SPECS:
            log(f"Collecting {MEXICO_SPECS[site]['label']}...")
            items = call_custom_spec(site, MEXICO_SPECS[site]["label"])
            write_pipeline_record(
                site, "reverse_engineered",
                {"items_count": len(items), "source_type": "custom_spec"}
            )
            total_items += len(items)
            log(f"  → {len(items)} items")
        log(f"Mexico specs total: {total_items} items\n")

    # openweb built-in news sites
    if run_all or args.news:
        log("=== openweb news sites ===")
        items = collect_news_sites(args.query)
        for item in items:
            write_pipeline_record(
                item["source"].lower().replace(" ", "-"),
                "openweb",
                {"query": args.query, "data_length": len(item.get("data_preview", ""))}
            )
        total_items += len(items)
        log(f"News sites total: {len(items)} items\n")

    # Wikipedia change monitor
    if run_all or args.wiki_monitor:
        log("=== Wikipedia change monitor ===")
        changes = check_wiki_changes()
        write_pipeline_record(
            "wikipedia", "openweb",
            {"pages_monitored": len(WIKI_MONITOR_PAGES), "changes_detected": len(changes)}
        )
        if changes:
            log(f"⚠️ {len(changes)} page change(s) detected!")
            for c in changes:
                log(f"  {c['page']}: {c['extract_preview'][:100]}")
        else:
            log("No changes detected (first run or page revisions stable)")
        total_items += len(changes)

    print(json.dumps({
        "status": "ok",
        "total_items": total_items,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
    }))
    return 0


if __name__ == "__main__":
    main()
