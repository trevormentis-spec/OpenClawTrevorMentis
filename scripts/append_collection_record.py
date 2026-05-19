#!/usr/bin/env python3
"""
Collection Record Pipeline — writes structured collection records to dual storage:
1. tasks/collection_records.jsonl (git-backed, interoperable)
2. data/collection_records.db (SQLite — queryable, schema-enforced, zero-cost)

Replaces the BigQuery target. Schema matches the TREVOR record spec.

Usage:
    echo '{"source":"wikipedia",...}' | python3 scripts/append_collection_record.py
    python3 scripts/append_collection_record.py --record '{"source":"wikipedia",...}'
    python3 scripts/append_collection_record.py --query "SELECT source, count(*) FROM records GROUP BY source"
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sqlite3
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
JSONL_PATH = REPO_ROOT / "tasks" / "collection_records.jsonl"
DB_PATH = REPO_ROOT / "data" / "collection_records.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS collection_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    site_spec_version TEXT,
    method TEXT NOT NULL,
    nato_admiralty_source_rating TEXT,
    nato_admiralty_info_rating TEXT,
    collected_at TEXT NOT NULL,
    qc_status TEXT DEFAULT 'PENDING_HUMAN_ANALYST_QC_REVIEW',
    payload_json TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_source ON collection_records(source);
CREATE INDEX IF NOT EXISTS idx_method ON collection_records(method);
CREATE INDEX IF NOT EXISTS idx_collected_at ON collection_records(collected_at);
CREATE INDEX IF NOT EXISTS idx_qc_status ON collection_records(qc_status);
"""


def ensure_db():
    """Create the SQLite database and schema if not present."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


def append_record(record: dict) -> bool:
    """Append a record to both JSONL and SQLite. Returns True on success."""
    # Normalize fields
    record.setdefault("source", "unknown")
    record.setdefault("method", "unknown")
    record.setdefault("site_spec_version", "manual-v1")
    record.setdefault("nato_admiralty_source_rating", "D")
    record.setdefault("nato_admiralty_info_rating", "4")
    record.setdefault("collected_at", dt.datetime.now(dt.timezone.utc).isoformat())
    record.setdefault("payload", {})
    record["payload"]["qc_status"] = record["payload"].get("qc_status", "PENDING_HUMAN_ANALYST_QC_REVIEW")

    ok = True

    # Write JSONL
    JSONL_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(JSONL_PATH, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"ERROR writing JSONL: {e}", file=sys.stderr)
        ok = False

    # Write SQLite
    ensure_db()
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute(
            """INSERT INTO collection_records
               (source, site_spec_version, method,
                nato_admiralty_source_rating, nato_admiralty_info_rating,
                collected_at, qc_status, payload_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record["source"],
                record["site_spec_version"],
                record["method"],
                record["nato_admiralty_source_rating"],
                record["nato_admiralty_info_rating"],
                record["collected_at"],
                record["payload"].get("qc_status", "PENDING_HUMAN_ANALYST_QC_REVIEW"),
                json.dumps(record["payload"], ensure_ascii=False),
            ),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"ERROR writing SQLite: {e}", file=sys.stderr)
        ok = False

    return ok


def run_query(sql: str) -> list[dict]:
    """Run a SQL query against the SQLite database and return results as dicts."""
    ensure_db()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(sql)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Collection record pipeline (JSONL + SQLite)")
    parser.add_argument("--record", help="JSON record as string")
    parser.add_argument("--query", help="SQL query to run against SQLite")
    parser.add_argument("--stats", action="store_true", help="Show quick stats")
    args = parser.parse_args()

    if args.stats:
        ensure_db()
        rows = run_query("""
            SELECT method,
                   COUNT(*) as total,
                   MIN(collected_at) as earliest,
                   MAX(collected_at) as latest
            FROM collection_records
            GROUP BY method
            ORDER BY total DESC
        """)
        total = run_query("SELECT COUNT(*) as c FROM collection_records")[0]["c"]
        print(f"Collection Records: {total} total")
        for r in rows:
            print(f"  {r['method']:25s} {r['total']:4d}  [{r['earliest'][:16]} → {r['latest'][:16]}]")
        return 0

    if args.query:
        try:
            rows = run_query(args.query)
            print(json.dumps(rows, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"ERROR running query: {e}", file=sys.stderr)
            return 1
        return 0

    if args.record:
        try:
            record = json.loads(args.record)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
            return 1
    else:
        record = json.loads(sys.stdin.read())

    success = append_record(record)
    if success:
        print(json.dumps({"status": "ok", "record": record}, indent=2))
        return 0
    else:
        print(json.dumps({"status": "error", "record": record}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    main()
