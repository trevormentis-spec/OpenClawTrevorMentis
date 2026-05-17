#!/usr/bin/env python3
"""Source freshness check — flags entity files where last_source_date is stale.

Run daily before brief production. Output goes to the brief's collection-quality
section. Flags entities where (today - last_source_date) > stale_warning_days.

Usage:
    python3 scripts/check_source_freshness.py
    python3 scripts/check_source_freshness.py --json  # machine-readable
    python3 scripts/check_source_freshness.py --stale-only  # only stale entries
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
ACTORS_DIR = REPO_ROOT / "brain" / "memory" / "semantic" / "mexico" / "actors"
GEOGRAPHY_DIR = REPO_ROOT / "brain" / "memory" / "semantic" / "mexico" / "geography"


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def parse_last_source_date(content: str) -> dt.date | None:
    """Extract last_source_date from entity file.

    Matches both "last_source_date: 2026-05-15" and
    "**Last source date:** 2026-05-15" formats.
    """
    m = re.search(r"[Ll]ast source date.*?\*{0,2}\s*(\d{4}-\d{2}-\d{2})", content)
    if m:
        return dt.date.fromisoformat(m.group(1))
    return None


def parse_stale_warning_days(content: str) -> int:
    """Extract stale_warning_days from entity file, default 30."""
    m = re.search(r"stale_warning_days:\s*(\d+)", content)
    return int(m.group(1)) if m else 30


def parse_entity_name(content: str, path: pathlib.Path) -> str:
    """Extract entity name from content or filename."""
    m = re.search(r"^# Entity:\s*(.+)$", content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return path.stem.replace("-", " ").title()


def check_entity_file(path: pathlib.Path, today: dt.date,
                      json_output: bool = False) -> dict:
    """Check a single entity file for freshness. Returns status dict."""
    content = path.read_text()
    name = parse_entity_name(content, path)
    last_date = parse_last_source_date(content)
    warning_days = parse_stale_warning_days(content)

    result = {
        "path": str(path.relative_to(REPO_ROOT)),
        "name": name,
        "last_source_date": str(last_date) if last_date else None,
        "stale_warning_days": warning_days,
        "status": "ok",
        "days_since_update": None,
        "message": "",
    }

    if not last_date:
        result["status"] = "no_date"
        result["message"] = "No last_source_date field found"
        return result

    days_since = (today - last_date).days
    result["days_since_update"] = days_since

    if days_since > warning_days * 2:
        result["status"] = "critical"
        result["message"] = f"{days_since} days since last source (warning: {warning_days}d) — ENTITY IS STALE"
    elif days_since > warning_days:
        result["status"] = "warning"
        result["message"] = f"{days_since} days since last source (warning: {warning_days}d)"
    else:
        result["status"] = "ok"
        result["message"] = f"Fresh — {days_since}d since last source"

    return result


def check_all(today: dt.date | None = None,
              stale_only: bool = False,
              json_output: bool = False) -> list[dict]:
    """Check all entity files in actors/ and geography/ directories."""
    if today is None:
        today = dt.date.today()

    results: list[dict] = []

    for directory in [ACTORS_DIR, GEOGRAPHY_DIR]:
        if not directory.exists():
            continue
        for f in sorted(directory.glob("*.md")):
            result = check_entity_file(f, today, json_output)
            if stale_only and result["status"] == "ok":
                continue
            results.append(result)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Source freshness checker")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--stale-only", action="store_true", help="Only stale entities")
    parser.add_argument("--summary", action="store_true", help="Print summary line")
    args = parser.parse_args()

    today = dt.date.today()
    results = check_all(today, stale_only=args.stale_only, json_output=args.json)

    if args.json:
        output = {
            "checked_at": today.isoformat(),
            "total": len(results),
            "ok": sum(1 for r in results if r["status"] == "ok"),
            "warning": sum(1 for r in results if r["status"] == "warning"),
            "critical": sum(1 for r in results if r["status"] == "critical"),
            "no_date": sum(1 for r in results if r["status"] == "no_date"),
            "entities": results,
        }
        print(json.dumps(output, indent=2))
        return

    if args.summary:
        ok = sum(1 for r in results if r["status"] == "ok")
        warn = sum(1 for r in results if r["status"] == "warning")
        crit = sum(1 for r in results if r["status"] == "critical")
        nod = sum(1 for r in results if r["status"] == "no_date")
        print(f"Source freshness: {ok} fresh, {warn} warning, {crit} critical, {nod} no_date")
        return

    for r in results:
        icon = "✅" if r["status"] == "ok" else "⚠️" if r["status"] == "warning" else "🔴" if r["status"] == "critical" else "❓"
        print(f"{icon} {r['name']}: {r['message']}")

    ok = sum(1 for r in results if r["status"] == "ok")
    warn = sum(1 for r in results if r["status"] == "warning")
    crit = sum(1 for r in results if r["status"] == "critical")
    print(f"\n{ok} fresh, {warn} stale (warning), {crit} critical")


if __name__ == "__main__":
    main()
