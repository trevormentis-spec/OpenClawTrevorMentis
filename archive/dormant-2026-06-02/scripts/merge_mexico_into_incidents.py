#!/usr/bin/env python3
"""
Merge mexico-daily-scan output into the daily pipeline's incidents.json.

Wired into daily-brief-cron.sh after collect.py runs. Reads the latest
exports/mexico-news-scan-YYYY-MM-DD.json and appends each tagged article
as an incident, tagged region="north_america" with theme metadata so
analyze.py can group by Mexico theme.

This is the bridge between Trevor's Mexico source list and the existing
collect/analyze plumbing, without requiring a parallel pipeline.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
EXPORTS = REPO_ROOT / "exports"


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[mexico-merge {ts}] {msg}", file=sys.stderr, flush=True)


def latest_scan() -> pathlib.Path | None:
    if not EXPORTS.exists():
        return None
    candidates = sorted(EXPORTS.glob("mexico-news-scan-*.json"))
    return candidates[-1] if candidates else None


def article_to_incident(art: dict, source_name: str, themes: list[str]) -> dict:
    title = art.get("title", "").strip()
    url = art.get("url", "")
    h = hashlib.sha1(f"{source_name}|{url}|{title}".encode()).hexdigest()[:16]
    matched_themes = art.get("matched_themes", []) or themes or ["unclassified"]
    return {
        "id": f"mx-{h}",
        "region": "north_america",
        "mexico_themes": matched_themes,
        "title": title,
        "summary": title,
        "geo": {"country": "Mexico"},
        "sources": [{
            "name": source_name,
            "url": url,
            "admiralty_source": "B",
            "admiralty_credibility": 2,
            "language": "es" if "elpais" not in source_name.lower() else "es-mx",
            "retrieved_at_utc": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
        }],
        "single_source": True,
        "confidence_collector": "medium",
        "kind": "mexico_scan",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--working-dir", required=True,
                   help="brief working dir, e.g. ~/trevor-briefings/2026-05-17")
    p.add_argument("--scan", default="",
                   help="path to mexico-news-scan-*.json (default: latest in exports/)")
    p.add_argument("--max-per-source", type=int, default=8)
    args = p.parse_args()

    wd = pathlib.Path(args.working_dir).expanduser().resolve()
    incidents_path = wd / "raw" / "incidents.json"
    if not incidents_path.exists():
        log(f"no incidents.json at {incidents_path} — nothing to merge into")
        return 1

    scan_path = pathlib.Path(args.scan) if args.scan else latest_scan()
    if scan_path is None or not scan_path.exists():
        log("no mexico scan output available — skipping merge")
        return 0

    scan = json.loads(scan_path.read_text())
    incidents_doc = json.loads(incidents_path.read_text())
    existing = incidents_doc.get("incidents", [])
    existing_ids = {i.get("id") for i in existing}

    added = 0
    by_theme: dict[str, int] = {}
    for source in scan.get("results", []):
        if source.get("status") != "ok":
            continue
        source_name = source.get("name", "unknown")
        articles = source.get("articles", [])[: args.max_per_source]
        themes_for_source = []
        for inc in (s for s in scan.get("results", []) if s.get("name") == source_name):
            themes_for_source = inc.get("themes", []) or themes_for_source
        for art in articles:
            inc = article_to_incident(art, source_name, themes_for_source)
            if inc["id"] in existing_ids:
                continue
            existing.append(inc)
            existing_ids.add(inc["id"])
            added += 1
            for t in inc["mexico_themes"]:
                by_theme[t] = by_theme.get(t, 0) + 1

    incidents_doc["incidents"] = existing
    notes = incidents_doc.setdefault("collection_gaps", [])
    notes.append(
        f"mexico-scan merge: +{added} articles from {scan_path.name} "
        f"({', '.join(f'{k}={v}' for k, v in sorted(by_theme.items()))})"
    )
    incidents_path.write_text(json.dumps(incidents_doc, indent=2, ensure_ascii=False))
    log(f"merged {added} Mexico articles into {incidents_path} (themes={by_theme})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
