#!/usr/bin/env python3
"""
Procedural Learner — Phase 6: Operational Learning.

After each pipeline run, checks for:
- Failed or degraded pipeline steps
- Successful fixes or workarounds
- Repeated error patterns
- Successful recovery patterns

Preserves successful patterns as procedural memory that is loaded at the
start of the next pipeline run (via procedural_memory_loader.py).

Design:
- Scans pipeline logs and output for error signals
- Checks behavioral state for active escalations
- Monitors for patterns that repeat (same failure 2+ times)
- Writes procedural memories to brain/memory/procedural/

Usage:
    python3 scripts/procedural_learner.py                      # Scan today's output for learnings
    python3 scripts/procedural_learner.py --pipeline-log ~/trevor-briefings/2026-05-13/pipeline.log
    python3 scripts/procedural_learner.py --report             # Show all procedural memories
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROCEDURAL_DIR = REPO_ROOT / "brain" / "memory" / "procedural"
AUTONOMY_TRACKER_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "autonomy-tracker.json"
BEHAVIORAL_STATE_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "behavioral-state.json"


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[procedural {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, Exception):
            return {}
    return {}


def load_existing_memories() -> dict[str, dict]:
    """Load all existing procedural memories, keyed by title."""
    memories = {}
    PROCEDURAL_DIR.mkdir(parents=True, exist_ok=True)
    for f in sorted(PROCEDURAL_DIR.glob("*.md")):
        content = f.read_text()
        # Extract title from first line
        title = content.split("\n")[0].replace("# ", "").strip()
        memories[title] = {
            "path": str(f),
            "content": content,
            "modified": dt.datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
        }
    return memories


def detect_failures_from_log(log_path: pathlib.Path | None) -> list[dict]:
    """Parse pipeline log to detect failures."""
    failures = []
    if not log_path or not log_path.exists():
        return failures

    text = log_path.read_text()
    error_lines = re.findall(r"FAILED|FATAL|ERROR|CRASHED|error|failed|traceback", text, re.IGNORECASE)
    if error_lines:
        failures.append({
            "type": "pipeline_error",
            "count": len(error_lines),
            "evidence": f"{len(error_lines)} error indicators in pipeline log",
        })
    return failures


def detect_escalation_patterns() -> list[dict]:
    """Check behavioral state for repeated escalation patterns."""
    learnings = []
    state = load_json(BEHAVIORAL_STATE_FILE)
    if not state:
        return learnings

    events = state.get("event_directives", {})
    active = events.get("active_escalations", [])

    # Track which regions have been escalated repeatedly
    # If a region consistently needs escalation, that's a learning
    region_counts = {}
    for e in active:
        r = e.get("region", "unknown")
        region_counts[r] = region_counts.get(r, 0) + 1

    for region, count in region_counts.items():
        if count >= 2:
            learnings.append({
                "type": "repeated_escalation",
                "region": region,
                "count": count,
                "evidence": f"{region} has {count} active escalations",
                "recommendation": f"Consider pre-emptive increased collection for {region}",
            })

    return learnings


def detect_collection_gaps(state_path: pathlib.Path | None = None) -> list[dict]:
    """Detect persistent collection gaps that need procedural fixes."""
    learnings = []
    if state_path and state_path.exists():
        state = load_json(state_path)
        gaps = state.get("identified_gaps", [])
        if gaps:
            for g in gaps:
                learnings.append({
                    "type": "collection_gap",
                    "detail": g,
                    "evidence": f"Persistent gap: {g}",
                })
    return learnings


def generate_procedural_memory(title: str, body: str) -> str:
    """Format a procedural memory entry."""
    return (
        f"# {title}\n"
        f"_Learned: {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC_\n"
        f"_Source: procedural_learner.py_\n\n"
        f"{body}\n"
    )


def save_procedural_memory(title: str, body: str, tracker: dict) -> pathlib.Path:
    """Save a procedural memory and track it."""
    path = PROCEDURAL_DIR / f"{title.lower().replace(' ', '-')}.md"
    path.write_text(generate_procedural_memory(title, body))
    
    tracker.setdefault("procedural_learnings", []).append({
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
        "title": title,
        "path": str(path),
    })
    
    log(f"Procedural memory saved: {title} → {path}")
    return path


def check_existing_procedure(memories: dict, pattern: str) -> bool:
    """Check if a procedural memory already covers this pattern."""
    for title, info in memories.items():
        if pattern.lower() in title.lower() or pattern.lower() in info["content"].lower():
            return True
    return False


def scan_and_learn(log_path: pathlib.Path | None = None) -> int:
    """Main learning scan — detect issues and preserve fixes."""
    existing = load_existing_memories()
    tracker = load_json(AUTONOMY_TRACKER_FILE) or {
        "version": 1, "created": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
        "unscheduled_cognition_events": [], "source_trust_changes": [],
        "procedural_learnings": [], "autonomous_prioritizations": [],
    }
    
    learned_count = 0
    
    # 1. Check for pipeline failures
    failures = detect_failures_from_log(log_path)
    for failure in failures:
        if not check_existing_procedure(existing, "pipeline failure"):
            title = "Pipeline Failure Recovery"
            body = (
                "When the daily pipeline fails or produces errors:\n\n"
                "1. Check the pipeline log for the specific failure type\n"
                f"2. Found pattern: {failure.get('evidence', 'Unknown')}\n"
                "3. Retry the failed step individually before rerunning the full pipeline\n"
                "4. If the failure is transient (network, timeout), a single retry usually works\n"
                "5. If the failure is persistent, check API keys and network connectivity\n\n"
                "This procedure was auto-generated. Update it as you discover reliable fixes.\n"
            )
            save_procedural_memory(title, body, tracker)
            learned_count += 1

    # 2. Check for repeated escalation patterns
    escalations = detect_escalation_patterns()
    for esc in escalations:
        region = esc.get("region", "unknown")
        pattern = f"escalation {region}"
        if not check_existing_procedure(existing, pattern):
            title = f"Escalation Pattern — {region.title()}"
            body = (
                f"Detected pattern: {region} has shown repeated escalation signals.\n\n"
                f"Evidence: {esc.get('evidence', '')}\n"
                f"Recommendation: {esc.get('recommendation', 'Monitor closely')}\n\n"
                "When this region appears in future escalations:\n"
                "1. Apply restricted confidence bands immediately\n"
                "2. Increase collection intensity pre-emptively\n"
                "3. Flag for unscheduled cognition if critical\n"
            )
            save_procedural_memory(title, body, tracker)
            learned_count += 1

    # 3. Check for collection gaps
    collection_state_path = REPO_ROOT / "brain" / "memory" / "semantic" / "collection-state.json"
    gaps = detect_collection_gaps(collection_state_path)
    for gap in gaps:
        pattern = "collection gap"
        if not check_existing_procedure(existing, pattern):
            title = "Collection Gap Response"
            body = (
                "When collection gaps are detected:\n\n"
                f"Evidence: {gap.get('evidence', 'Unknown gap')}\n\n"
                "Response:\n"
                "1. Document the gap in collection-state.json\n"
                "2. Search for new sources covering the gap region\n"
                "3. Add local-language sources if the gap is linguistic\n"
                "4. Increase collection caps for the gap region\n"
                "5. Flag in next brief as a caveat\n"
            )
            save_procedural_memory(title, body, tracker)
            learned_count += 1

    # Save tracker updates
    AUTONOMY_TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    AUTONOMY_TRACKER_FILE.write_text(json.dumps(tracker, indent=2))
    
    if learned_count > 0:
        log(f"Generated {learned_count} new procedural memories")
    else:
        log("No new procedural learnings detected")
    
    return learned_count


def report_all_memories() -> None:
    """Print all existing procedural memories."""
    memories = load_existing_memories()
    print(f"# Procedural Memories ({len(memories)} total)")
    print("")
    for title, info in sorted(memories.items()):
        modified = info["modified"][:19].replace("T", " ")
        print(f"## {title}")
        print(f"*Last modified: {modified}*")
        print(f"*Path: {info['path']}*")
        print("")
        # Print first few lines
        lines = info["content"].split("\n")
        for line in lines[1:6]:
            print(line)
        print("..." if len(lines) > 6 else "")
        print("")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pipeline-log", default="", help="Path to pipeline log file")
    parser.add_argument("--report", action="store_true", help="Show all procedural memories")
    args = parser.parse_args()

    if args.report:
        report_all_memories()
        return 0

    log_path = pathlib.Path(args.pipeline_log).expanduser() if args.pipeline_log else None
    count = scan_and_learn(log_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
