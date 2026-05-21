#!/usr/bin/env python3
"""
Log report to brain memory for future recall.

Call this after any report is sent so Trevor can reference back.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import sys

EPISODIC_DIR = pathlib.Path(__file__).resolve().parent.parent / "brain" / "memory" / "episodic"


def log_report(report_type: str, date_str: str, file_path: str, summary: str, 
               word_count: int, sources: list[str] | None = None,
               key_judgments: list[str] | None = None,
               regions: list[str] | None = None,
               model: str = "") -> None:
    """Log a report delivery to episodic memory for future recall."""
    EPISODIC_DIR.mkdir(parents=True, exist_ok=True)
    
    today = dt.date.today().isoformat()
    log_file = EPISODIC_DIR / f"{today}.jsonl"
    
    record = {
        "type": "report_delivery",
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "report_type": report_type,
        "date": date_str,
        "file_path": str(file_path),
        "summary": summary[:300],
        "word_count": word_count,
        "sources": sources or [],
        "key_judgments": (key_judgments or [])[:5],
        "regions": (regions or [])[:10],
        "model": model,
    }
    
    with open(log_file, "a") as f:
        f.write(json.dumps(record) + "\n")
    
    print(f"[report-memory] Logged {report_type} ({date_str}) — {word_count} words, {len(sources or [])} sources", 
          file=sys.stderr)


def main() -> None:
    """CLI for manual logging."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--summary", default="")
    ap.add_argument("--words", type=int, default=0)
    ap.add_argument("--sources", nargs="*", default=[])
    ap.add_argument("--model", default="")
    args = ap.parse_args()
    
    log_report(args.type, args.date, args.file, args.summary, 
               args.words, args.sources, model=args.model)


if __name__ == "__main__":
    main()
