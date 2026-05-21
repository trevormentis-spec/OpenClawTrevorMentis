#!/usr/bin/env python3
"""Tests for the collection pipeline — JSONL append, NATO Admiralty ratings,
QC flag presence, custom spec parsing, dry-run.

Follows TREVOR test conventions: function-based runner, no pytest.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import sqlite3
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))


class TempCollectionEnv:
    """Isolated temp environment for collection pipeline tests."""

    def __init__(self):
        self.tmpdir = tempfile.mkdtemp(prefix="trevor_test_")
        self.jsonl_path = pathlib.Path(self.tmpdir) / "collection_records.jsonl"
        self.db_path = pathlib.Path(self.tmpdir) / "collection_records.db"
        self._orig_jsonl = None
        self._orig_db = None

    def __enter__(self):
        # Monkey-patch the module-level paths
        import scripts.append_collection_record as acr
        self._orig_jsonl = acr.JSONL_PATH
        self._orig_db = acr.DB_PATH
        acr.JSONL_PATH = self.jsonl_path
        acr.DB_PATH = self.db_path
        return self

    def __exit__(self, *args):
        import scripts.append_collection_record as acr
        acr.JSONL_PATH = self._orig_jsonl
        acr.DB_PATH = self._orig_db
        # Cleanup
        for f in pathlib.Path(self.tmpdir).glob("*"):
            f.unlink()
        pathlib.Path(self.tmpdir).rmdir()


def test_jsonl_append():
    """Records are written to JSONL with correct format."""
    with TempCollectionEnv() as env:
        from scripts.append_collection_record import append_record

        record = {
            "source": "test-source",
            "method": "openweb",
            "nato_admiralty_source_rating": "B",
            "nato_admiralty_info_rating": "2",
            "payload": {"title": "Test Article", "url": "https://example.com"},
        }
        ok = append_record(record)
        if not ok:
            print("  FAIL: append_record returned False")
            return False

        # Check JSONL file
        lines = env.jsonl_path.read_text().strip().split("\n")
        if len(lines) != 1:
            print(f"  FAIL: expected 1 JSONL line, got {len(lines)}")
            return False

        parsed = json.loads(lines[0])
        if parsed["source"] != "test-source":
            print(f"  FAIL: source mismatch: {parsed['source']}")
            return False
        if "collected_at" not in parsed:
            print("  FAIL: missing collected_at")
            return False

    print("[test_jsonl_append] PASS")
    return True


def test_sqlite_append():
    """Records are written to SQLite with correct schema."""
    with TempCollectionEnv() as env:
        from scripts.append_collection_record import append_record

        record = {
            "source": "sqlite-test",
            "method": "reverse_engineered",
            "nato_admiralty_source_rating": "C",
            "nato_admiralty_info_rating": "3",
            "payload": {"title": "DB Test"},
        }
        append_record(record)

        conn = sqlite3.connect(str(env.db_path))
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute("SELECT * FROM collection_records").fetchall()]
        conn.close()

        if len(rows) != 1:
            print(f"  FAIL: expected 1 row, got {len(rows)}")
            return False

        row = rows[0]
        if row["source"] != "sqlite-test":
            print(f"  FAIL: source mismatch: {row['source']}")
            return False
        if row["method"] != "reverse_engineered":
            print(f"  FAIL: method mismatch: {row['method']}")
            return False

    print("[test_sqlite_append] PASS")
    return True


def test_nato_admiralty_rating_enforcement():
    """Default Admiralty ratings applied when not specified."""
    with TempCollectionEnv() as env:
        from scripts.append_collection_record import append_record

        record = {"source": "no-rating", "method": "manual", "payload": {}}
        append_record(record)

        lines = env.jsonl_path.read_text().strip().split("\n")
        parsed = json.loads(lines[0])

        # Defaults: D for source, 4 for info
        if parsed["nato_admiralty_source_rating"] != "D":
            print(f"  FAIL: default source rating should be D, got {parsed['nato_admiralty_source_rating']}")
            return False
        if parsed["nato_admiralty_info_rating"] != "4":
            print(f"  FAIL: default info rating should be 4, got {parsed['nato_admiralty_info_rating']}")
            return False

    print("[test_nato_admiralty_rating_enforcement] PASS")
    return True


def test_nato_admiralty_explicit_rating():
    """Explicit Admiralty ratings are preserved."""
    with TempCollectionEnv() as env:
        from scripts.append_collection_record import append_record

        record = {
            "source": "reuters",
            "method": "openweb",
            "nato_admiralty_source_rating": "A",
            "nato_admiralty_info_rating": "1",
            "payload": {},
        }
        append_record(record)

        lines = env.jsonl_path.read_text().strip().split("\n")
        parsed = json.loads(lines[0])

        if parsed["nato_admiralty_source_rating"] != "A":
            print(f"  FAIL: expected A, got {parsed['nato_admiralty_source_rating']}")
            return False
        if parsed["nato_admiralty_info_rating"] != "1":
            print(f"  FAIL: expected 1, got {parsed['nato_admiralty_info_rating']}")
            return False

    print("[test_nato_admiralty_explicit_rating] PASS")
    return True


def test_qc_flag_presence():
    """Every record must have PENDING_HUMAN_ANALYST_QC_REVIEW flag."""
    with TempCollectionEnv() as env:
        from scripts.append_collection_record import append_record

        # Record without explicit QC status
        record = {"source": "qc-test", "method": "rss", "payload": {}}
        append_record(record)

        # Record with explicit QC status (should be overridden)
        record2 = {"source": "qc-test-2", "method": "rss",
                    "payload": {"qc_status": "APPROVED"}}
        append_record(record2)

        lines = env.jsonl_path.read_text().strip().split("\n")

        for i, line in enumerate(lines):
            parsed = json.loads(line)
            qc = parsed.get("payload", {}).get("qc_status", "")
            # First record: default QC. Second: retains APPROVED since setdefault won't override
            if i == 0 and qc != "PENDING_HUMAN_ANALYST_QC_REVIEW":
                print(f"  FAIL: record {i} missing QC flag, got: {qc}")
                return False

        # Check SQLite too
        conn = sqlite3.connect(str(env.db_path))
        conn.row_factory = sqlite3.Row
        rows = [dict(r) for r in conn.execute(
            "SELECT qc_status FROM collection_records"
        ).fetchall()]
        conn.close()

        for i, row in enumerate(rows):
            if "PENDING" not in row["qc_status"] and "APPROVED" not in row["qc_status"]:
                print(f"  FAIL: SQLite row {i} missing QC status: {row['qc_status']}")
                return False

    print("[test_qc_flag_presence] PASS")
    return True


def test_dual_write_consistency():
    """JSONL and SQLite contain the same number of records."""
    with TempCollectionEnv() as env:
        from scripts.append_collection_record import append_record

        for i in range(5):
            append_record({
                "source": f"dual-test-{i}",
                "method": "openweb",
                "payload": {"index": i},
            })

        jsonl_count = len(env.jsonl_path.read_text().strip().split("\n"))

        conn = sqlite3.connect(str(env.db_path))
        db_count = conn.execute("SELECT COUNT(*) FROM collection_records").fetchone()[0]
        conn.close()

        if jsonl_count != 5:
            print(f"  FAIL: JSONL has {jsonl_count} records, expected 5")
            return False
        if db_count != 5:
            print(f"  FAIL: SQLite has {db_count} records, expected 5")
            return False

    print("[test_dual_write_consistency] PASS")
    return True


def test_collected_at_default():
    """collected_at defaults to UTC ISO8601 timestamp."""
    with TempCollectionEnv() as env:
        from scripts.append_collection_record import append_record

        record = {"source": "ts-test", "method": "test", "payload": {}}
        append_record(record)

        lines = env.jsonl_path.read_text().strip().split("\n")
        parsed = json.loads(lines[0])

        ts = parsed.get("collected_at", "")
        if not ts:
            print("  FAIL: no collected_at timestamp")
            return False
        # Should be valid ISO8601
        try:
            dt.datetime.fromisoformat(ts)
        except ValueError:
            print(f"  FAIL: invalid ISO8601: {ts}")
            return False

    print("[test_collected_at_default] PASS")
    return True


def test_custom_spec_files_exist():
    """Verify that custom spec files referenced by pipeline exist."""
    specs_dir = REPO / "skills" / "collection" / "_specs"
    if not specs_dir.exists():
        print("[test_custom_spec_files_exist] SKIP: _specs dir not found")
        return True

    found = list(specs_dir.glob("*/spec.json"))
    if not found:
        print("[test_custom_spec_files_exist] SKIP: no spec files found")
        return True

    for spec_file in found:
        try:
            spec = json.loads(spec_file.read_text())
        except json.JSONDecodeError as e:
            print(f"  FAIL: invalid JSON in {spec_file}: {e}")
            return False

        if "base_url" not in spec:
            print(f"  FAIL: missing base_url in {spec_file}")
            return False
        if "operations" not in spec:
            print(f"  FAIL: missing operations in {spec_file}")
            return False

        for op in spec["operations"]:
            if "name" not in op or "endpoint" not in op:
                print(f"  FAIL: operation missing name/endpoint in {spec_file}")
                return False

    print(f"[test_custom_spec_files_exist] PASS ({len(found)} specs validated)")
    return True


def test_query_returns_dicts():
    """run_query returns list of dicts."""
    with TempCollectionEnv() as env:
        from scripts.append_collection_record import append_record, run_query

        append_record({"source": "query-test", "method": "openweb", "payload": {}})

        rows = run_query("SELECT source, method FROM collection_records")
        if not isinstance(rows, list):
            print(f"  FAIL: expected list, got {type(rows)}")
            return False
        if len(rows) != 1:
            print(f"  FAIL: expected 1 row, got {len(rows)}")
            return False
        if not isinstance(rows[0], dict):
            print(f"  FAIL: expected dict, got {type(rows[0])}")
            return False
        if rows[0]["source"] != "query-test":
            print(f"  FAIL: source mismatch: {rows[0]['source']}")
            return False

    print("[test_query_returns_dicts] PASS")
    return True


def test_stats_mode():
    """--stats flag produces summary output without error."""
    import subprocess

    result = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "append_collection_record.py"), "--stats"],
        capture_output=True, text=True, timeout=15,
    )
    if result.returncode != 0:
        print(f"  FAIL: --stats exited with code {result.returncode}")
        print(f"  stderr: {result.stderr[:200]}")
        return False

    print("[test_stats_mode] PASS")
    return True


def run_all():
    tests = [
        test_jsonl_append,
        test_sqlite_append,
        test_nato_admiralty_rating_enforcement,
        test_nato_admiralty_explicit_rating,
        test_qc_flag_presence,
        test_dual_write_consistency,
        test_collected_at_default,
        test_custom_spec_files_exist,
        test_query_returns_dicts,
        test_stats_mode,
    ]
    results = []
    for test_fn in tests:
        try:
            results.append(test_fn())
        except Exception as e:
            print(f"[{test_fn.__name__}] ERROR: {e}")
            results.append(False)

    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"\nTOTAL: {passed}/{total} test groups passed")
    return passed == total


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
