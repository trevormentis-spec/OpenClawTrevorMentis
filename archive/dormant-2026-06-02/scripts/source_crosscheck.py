#!/usr/bin/env python3
"""
Source Cross-Check — compares openweb API output against RSS/DOM for the same source.

Finds discrepancies: different headlines, missing articles, stale data, or structural drift.
Anomalies signal either a feed problem or (potentially) a source integrity concern.

Usage:
    python3 scripts/source_crosscheck.py                  # Run all checks
    python3 scripts/source_crosscheck.py --source reuters  # Single source
    python3 scripts/source_crosscheck.py --report          # Summary of recent checks
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
import xml.etree.ElementTree as ET

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

CROSSCHECK_STATE = REPO_ROOT / "tasks" / "source_crosscheck_state.json"

# Sources with both openweb API and RSS feed
CHECKED_SOURCES = {
    "reuters": {
        "label": "Reuters",
        "rss": "https://www.reutersagency.com/feed/",
        "api_op": "search",
        "api_site": "reuters",
        "expected_overlap": 0.3,  # Expect at least 30% headline overlap
    },
    "bbc-news": {
        "label": "BBC News",
        "rss": "https://feeds.bbci.co.uk/news/rss.xml",
        "api_op": "search",
        "api_site": "bbc-news",
        "expected_overlap": 0.3,
    },
}


def log(msg: str) -> None:
    print(f"[xcheck] {msg}", file=sys.stderr, flush=True)


def fetch_rss(url: str, timeout: int = 15) -> list[str]:
    """Fetch RSS feed and return headline list."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TREVOR/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            xml = resp.read()
        root = ET.fromstring(xml)
        items = root.findall(".//item") or root.findall(".//entry")
        headlines = []
        for item in items:
            title = item.findtext("title") or ""
            if title:
                headlines.append(title.strip())
        return headlines
    except Exception as e:
        log(f"RSS fetch failed for {url}: {e}")
        return []


def fetch_api(source_cfg: dict) -> list[str]:
    """Fetch from openweb API and return headline-like strings."""
    site = source_cfg["api_site"]
    op = source_cfg["api_op"]
    try:
        result = subprocess.run(
            ["openweb", site, op, json.dumps({"q": "headlines", "size": 10})],
            capture_output=True, text=True, timeout=20,
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            # Try common response structures
            if isinstance(data, list):
                return [str(item.get("title", item.get("headline", item.get("text", str(item)))))[:150] for item in data[:10]]
            if isinstance(data, dict):
                # Check for embedded output
                if data.get("output"):
                    with open(data["output"]) as f:
                        inner = json.load(f)
                    if isinstance(inner, list):
                        return [str(item.get("title", ""))[:150] for item in inner[:10]]
    except Exception as e:
        log(f"API fetch failed for {site}: {e}")
    return []


def compute_overlap(api_heads: list[str], rss_heads: list[str]) -> float:
    """Compute simple Jaccard overlap between API and RSS headlines."""
    if not api_heads or not rss_heads:
        return 0.0
    api_set = set(h.lower().strip() for h in api_heads if h)
    rss_set = set(h.lower().strip() for h in rss_heads if h)
    if not api_set or not rss_set:
        return 0.0
    intersection = api_set & rss_set
    union = api_set | rss_set
    return len(intersection) / len(union)


def run_check(source_key: str, source_cfg: dict) -> dict:
    """Run a single cross-check."""
    log(f"Checking {source_cfg['label']}...")
    api_heads = fetch_api(source_cfg)
    rss_heads = fetch_rss(source_cfg["rss"])
    overlap = compute_overlap(api_heads, rss_heads)
    expected = source_cfg.get("expected_overlap", 0.3)

    status = "PASS" if overlap >= expected else "LOW_OVERLAP"
    if not api_heads and not rss_heads:
        status = "BOTH_EMPTY"
    elif not api_heads:
        status = "API_EMPTY"
    elif not rss_heads:
        status = "RSS_EMPTY"

    result = {
        "source": source_key,
        "status": status,
        "overlap": round(overlap, 3),
        "api_headlines": len(api_heads),
        "rss_headlines": len(rss_heads),
        "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }

    if status != "PASS":
        result["api_samples"] = api_heads[:3]
        result["rss_samples"] = rss_heads[:3]
        log(f"  → {status} (overlap: {overlap:.1%}, expected ≥{expected:.0%})")
        if api_heads:
            log(f"  API: {api_heads[0][:60]}")
        if rss_heads:
            log(f"  RSS: {rss_heads[0][:60]}")
    else:
        log(f"  → PASS (overlap: {overlap:.1%})")

    return result


def save_state(check: dict) -> None:
    """Append check result to persistent state."""
    state = {"checks": []}
    if CROSSCHECK_STATE.exists():
        try:
            state = json.loads(CROSSCHECK_STATE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    state.setdefault("checks", []).append(check)
    # Keep last 50 checks
    state["checks"] = state["checks"][-50:]
    state["last_updated"] = dt.datetime.now(dt.timezone.utc).isoformat()
    CROSSCHECK_STATE.parent.mkdir(parents=True, exist_ok=True)
    CROSSCHECK_STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def show_report() -> None:
    """Show recent cross-check history."""
    if not CROSSCHECK_STATE.exists():
        print("No cross-check data yet.")
        return
    try:
        state = json.loads(CROSSCHECK_STATE.read_text())
    except (json.JSONDecodeError, OSError):
        print("Could not read state.")
        return

    checks = state.get("checks", [])
    if not checks:
        print("No checks recorded.")
        return

    print(f"Cross-check history ({len(checks)} total):")
    for c in checks[-10:]:
        marker = "⚠️" if c["status"] != "PASS" else "✅"
        print(f"  {marker} {c['source']:15s} {c['status']:15s} overlap={c.get('overlap',0):.0%} api={c.get('api_headlines',0)} rss={c.get('rss_headlines',0)} [{c['checked_at'][:16]}]")


def main() -> int:
    parser = argparse.ArgumentParser(description="Source cross-check: API vs RSS")
    parser.add_argument("--source", choices=list(CHECKED_SOURCES.keys()), help="Single source to check")
    parser.add_argument("--report", action="store_true", help="Show recent check history")
    parser.add_argument("--all", action="store_true", help="Run all checks (default)")
    args = parser.parse_args()

    if args.report:
        show_report()
        return 0

    sources_to_check = {}
    if args.source:
        sources_to_check[args.source] = CHECKED_SOURCES[args.source]
    else:
        sources_to_check = CHECKED_SOURCES

    for key, cfg in sources_to_check.items():
        result = run_check(key, cfg)
        save_state(result)

        # Write pipeline record for non-pass results
        if result["status"] != "PASS":
            record = {
                "source": f"xcheck-{key}",
                "site_spec_version": "xcheck-v1",
                "method": "crosscheck",
                "nato_admiralty_source_rating": "A",
                "nato_admiralty_info_rating": "2",
                "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "payload": {
                    "status": result["status"],
                    "overlap": result["overlap"],
                    "api_count": result["api_headlines"],
                    "rss_count": result["rss_headlines"],
                    "qc_status": "PENDING_HUMAN_ANALYST_QC_REVIEW",
                },
            }
            subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "append_collection_record.py"),
                 "--record", json.dumps(record)],
                capture_output=True, timeout=10,
            )

    return 0


if __name__ == "__main__":
    main()
