#!/usr/bin/env python3
"""
Append a collection record to the existing collection_records JSONL pipeline.

Writes to tasks/collection_records.jsonl for pipeline pickup by collect.py.
Uses the existing GDELT/GKG-adjacent table — does not create a new table.

Usage:
    echo '{"source":"wikipedia", ...}' | python3 scripts/append_collection_record.py
    python3 scripts/append_collection_record.py --record '{"source":"wikipedia", ...}'
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "tasks" / "collection_records.jsonl"


def append_record(record: dict, output_path: pathlib.Path | None = None) -> bool:
    """Append a single collection record to the JSONL file."""
    path = output_path or DEFAULT_OUTPUT

    # Ensure required fields
    required = ["source", "method", "collected_at"]
    for field in required:
        if field not in record:
            record[field] = "unknown"

    # Add defaults
    record.setdefault("site_spec_version", "manual-v1")
    record.setdefault("nato_admiralty_source_rating", "D")
    record.setdefault("nato_admiralty_info_rating", "4")
    record.setdefault("payload", {})
    record["payload"]["qc_status"] = "PENDING_HUMAN_ANALYST_QC_REVIEW"
    record.setdefault("collected_at", dt.datetime.now(dt.timezone.utc).isoformat())

    # Write
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except OSError as e:
        print(f"ERROR writing record: {e}", file=sys.stderr)
        # Fallback
        fallback = path.parent / "collection_records_fallback.jsonl"
        with open(fallback, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"Wrote to fallback: {fallback}", file=sys.stderr)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Append collection record to JSONL pipeline")
    parser.add_argument("--record", help="JSON record as string")
    parser.add_argument("--output", help="Output file path (default: tasks/collection_records.jsonl)")
    args = parser.parse_args()

    if args.record:
        try:
            record = json.loads(args.record)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
            return 1
    else:
        # Read from stdin
        record = json.loads(sys.stdin.read())

    success = append_record(record, pathlib.Path(args.output) if args.output else None)

    if success:
        print(json.dumps({"status": "ok", "record": record}, indent=2))
        return 0
    else:
        print(json.dumps({"status": "error", "record": record}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
