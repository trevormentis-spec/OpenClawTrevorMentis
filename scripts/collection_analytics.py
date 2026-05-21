#!/usr/bin/env python3
"""Collection Analytics — source utilization reports.

Reports:
- Cited vs collected ratio per source
- Collection volume by topic/region
- Time-window breakdown (daily, weekly, monthly)
- Feed tier effectiveness
- Source quality trends

Usage:
    python3 scripts/collection_analytics.py                    # Full report
    python3 scripts/collection_analytics.py --json             # JSON output
    python3 scripts/collection_analytics.py --window 7         # Last 7 days
    python3 scripts/collection_analytics.py --source reuters   # Single source
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sqlite3
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "collection_records.db"
STATE_PATH = REPO_ROOT / "brain" / "memory" / "semantic" / "collection-state.json"


def log(msg: str) -> None:
    print(f"[collection-analytics] {msg}", file=sys.stderr, flush=True)


def _query(sql: str, params: tuple = ()) -> list[dict]:
    """Run a query against collection_records.db."""
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    conn.close()
    return rows


def _load_state() -> dict:
    """Load collection state for utilization data."""
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def source_utilization_report(window_days: int = 30) -> list[dict]:
    """Cited vs collected per source over the given time window."""
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=window_days)).isoformat()

    collected = _query("""
        SELECT source,
               COUNT(*) as collected_count,
               MIN(collected_at) as first_seen,
               MAX(collected_at) as last_seen
        FROM collection_records
        WHERE collected_at >= ?
        GROUP BY source
        ORDER BY collected_count DESC
    """, (cutoff,))

    # Merge with state-tracked citation data
    state = _load_state()
    utilization = state.get("source_utilization", {})

    report = []
    for row in collected:
        source = row["source"]
        util = utilization.get(source, {})
        cited = util.get("cited_count", 0)
        fetched = util.get("fetched_count", 0)
        quality = round(cited / max(fetched, 1), 3)
        consecutive_zero = util.get("consecutive_zero_runs", 0)

        report.append({
            "source": source,
            "collected_in_window": row["collected_count"],
            "total_fetched": fetched,
            "total_cited": cited,
            "quality_score": quality,
            "consecutive_zero_runs": consecutive_zero,
            "first_seen": row["first_seen"][:16] if row["first_seen"] else None,
            "last_seen": row["last_seen"][:16] if row["last_seen"] else None,
        })

    return report


def method_breakdown(window_days: int = 30) -> list[dict]:
    """Collection volume by method (openweb, reverse_engineered, rss, etc)."""
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=window_days)).isoformat()

    return _query("""
        SELECT method,
               COUNT(*) as count,
               COUNT(DISTINCT source) as unique_sources,
               MIN(collected_at) as earliest,
               MAX(collected_at) as latest
        FROM collection_records
        WHERE collected_at >= ?
        GROUP BY method
        ORDER BY count DESC
    """, (cutoff,))


def admiralty_distribution(window_days: int = 30) -> dict:
    """Distribution of NATO Admiralty ratings."""
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=window_days)).isoformat()

    source_ratings = _query("""
        SELECT nato_admiralty_source_rating as rating, COUNT(*) as count
        FROM collection_records
        WHERE collected_at >= ?
        GROUP BY nato_admiralty_source_rating
        ORDER BY rating
    """, (cutoff,))

    info_ratings = _query("""
        SELECT nato_admiralty_info_rating as rating, COUNT(*) as count
        FROM collection_records
        WHERE collected_at >= ?
        GROUP BY nato_admiralty_info_rating
        ORDER BY rating
    """, (cutoff,))

    return {
        "source_ratings": {r["rating"]: r["count"] for r in source_ratings},
        "info_ratings": {r["rating"]: r["count"] for r in info_ratings},
    }


def daily_volume(window_days: int = 30) -> list[dict]:
    """Daily collection volume over time window."""
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=window_days)).isoformat()

    return _query("""
        SELECT DATE(collected_at) as date,
               COUNT(*) as count,
               COUNT(DISTINCT source) as unique_sources
        FROM collection_records
        WHERE collected_at >= ?
        GROUP BY DATE(collected_at)
        ORDER BY date DESC
    """, (cutoff,))


def qc_status_summary() -> dict:
    """QC status breakdown across all records."""
    rows = _query("""
        SELECT qc_status, COUNT(*) as count
        FROM collection_records
        GROUP BY qc_status
        ORDER BY count DESC
    """)
    return {r["qc_status"]: r["count"] for r in rows}


def feed_tier_report() -> list[dict]:
    """Current feed tier assignments from collection state."""
    state = _load_state()
    utilization = state.get("source_utilization", {})

    tiers = []
    for source, data in utilization.items():
        fetched = data.get("fetched_count", 0)
        cited = data.get("cited_count", 0)
        consecutive_zero = data.get("consecutive_zero_runs", 0)

        if fetched == 0:
            quality = 0.0
        else:
            quality = cited / fetched

        if fetched < 3:
            tier = 1
        elif quality >= 0.3:
            tier = 1
        elif consecutive_zero >= 5:
            tier = 3
        elif quality >= 0.1 or consecutive_zero < 3:
            tier = 2
        else:
            tier = 3

        tiers.append({
            "source": source,
            "tier": tier,
            "quality": round(quality, 3),
            "fetched": fetched,
            "cited": cited,
            "consecutive_zero": consecutive_zero,
            "last_cited": (data.get("last_cited") or "never")[:10],
        })

    tiers.sort(key=lambda x: (x["tier"], -x["quality"]))
    return tiers


def generate_full_report(window_days: int = 30, source_filter: str | None = None) -> dict:
    """Generate complete analytics report."""
    report = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "window_days": window_days,
        "source_utilization": source_utilization_report(window_days),
        "method_breakdown": method_breakdown(window_days),
        "admiralty_distribution": admiralty_distribution(window_days),
        "daily_volume": daily_volume(window_days),
        "qc_status": qc_status_summary(),
        "feed_tiers": feed_tier_report(),
    }

    if source_filter:
        report["source_utilization"] = [
            s for s in report["source_utilization"]
            if source_filter.lower() in s["source"].lower()
        ]

    # Summary stats
    total_records = sum(r["collected_in_window"] for r in report["source_utilization"])
    unique_sources = len(report["source_utilization"])
    avg_quality = (
        sum(r["quality_score"] for r in report["source_utilization"]) / max(unique_sources, 1)
    )
    tier1 = sum(1 for t in report["feed_tiers"] if t["tier"] == 1)
    tier2 = sum(1 for t in report["feed_tiers"] if t["tier"] == 2)
    tier3 = sum(1 for t in report["feed_tiers"] if t["tier"] == 3)

    report["summary"] = {
        "total_records_in_window": total_records,
        "unique_sources": unique_sources,
        "avg_quality_score": round(avg_quality, 3),
        "feed_tiers": {"tier1": tier1, "tier2": tier2, "tier3": tier3},
    }

    return report


def format_report(report: dict) -> str:
    """Format report as human-readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append("COLLECTION ANALYTICS REPORT")
    lines.append(f"Generated: {report['generated_at'][:16]}")
    lines.append(f"Window: {report['window_days']} days")
    lines.append("=" * 60)

    summary = report.get("summary", {})
    lines.append(f"\nTotal records: {summary.get('total_records_in_window', 0)}")
    lines.append(f"Unique sources: {summary.get('unique_sources', 0)}")
    lines.append(f"Avg quality score: {summary.get('avg_quality_score', 0):.3f}")
    tiers = summary.get("feed_tiers", {})
    lines.append(f"Feed tiers: T1={tiers.get('tier1', 0)} T2={tiers.get('tier2', 0)} T3={tiers.get('tier3', 0)}")

    lines.append("\n--- Source Utilization ---")
    for s in report.get("source_utilization", []):
        quality_bar = "#" * int(s["quality_score"] * 20)
        lines.append(
            f"  {s['source']:30s} collected={s['collected_in_window']:3d}  "
            f"cited={s['total_cited']:2d}/{s['total_fetched']:2d}  "
            f"quality={s['quality_score']:.3f} [{quality_bar:20s}]"
        )

    lines.append("\n--- Method Breakdown ---")
    for m in report.get("method_breakdown", []):
        lines.append(
            f"  {m['method']:25s} {m['count']:4d} records  "
            f"({m['unique_sources']} sources)"
        )

    lines.append("\n--- Admiralty Ratings ---")
    admiralty = report.get("admiralty_distribution", {})
    src = admiralty.get("source_ratings", {})
    info = admiralty.get("info_ratings", {})
    if src:
        lines.append(f"  Source: {', '.join(f'{k}={v}' for k, v in sorted(src.items()))}")
    if info:
        lines.append(f"  Info:   {', '.join(f'{k}={v}' for k, v in sorted(info.items()))}")

    lines.append("\n--- Daily Volume (last 7) ---")
    for d in report.get("daily_volume", [])[:7]:
        bar = "#" * min(d["count"], 40)
        lines.append(f"  {d['date']}  {d['count']:3d} [{bar}]")

    lines.append("\n--- QC Status ---")
    for status, count in report.get("qc_status", {}).items():
        lines.append(f"  {status:45s} {count:4d}")

    lines.append("\n--- Feed Tiers ---")
    for t in report.get("feed_tiers", []):
        lines.append(
            f"  T{t['tier']} {t['source']:30s} quality={t['quality']:.3f}  "
            f"cited={t['cited']}/{t['fetched']}  zeros={t['consecutive_zero']}"
        )

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Collection analytics report")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--window", type=int, default=30, help="Time window in days (default: 30)")
    parser.add_argument("--source", default=None, help="Filter by source name")
    args = parser.parse_args()

    if not DB_PATH.exists():
        log("No collection database found. Run collection pipeline first.")
        return 1

    report = generate_full_report(window_days=args.window, source_filter=args.source)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_report(report))

    return 0


if __name__ == "__main__":
    sys.exit(main())
