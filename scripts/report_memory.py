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
    
    # Also append a readable entry to the daily memory file for searchability
    memory_dir = pathlib.Path(__file__).resolve().parent.parent / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    memory_file = memory_dir / f"{today}.md"
    
    memory_entry = f"\n## Report: {report_type} — {date_str}\n"
    memory_entry += f"**File:** {file_path}\n"
    memory_entry += f"**Words:** {word_count} | **Model:** {model}\n"
    memory_entry += f"**Summary:** {summary[:200]}\n"
    if key_judgments:
        memory_entry += "**Key judgments:**\n"
        for kj in key_judgments:
            memory_entry += f"- {kj}\n"
    if regions:
        memory_entry += f"**Regions:** {', '.join(regions)}\n"
    memory_entry += "\n"
    
    with open(memory_file, "a") as f:
        f.write(memory_entry)
    
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
