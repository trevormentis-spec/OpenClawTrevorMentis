#!/usr/bin/env python3
"""
Unscheduled Cognition Dispatcher — Phase 14, Primary Unlock.

Monitors behavioral state for critical event directives and fires
targeted regional analysis outside the daily cron schedule.

This is the mechanism that makes Trevor autonomous: conditions change,
analysis fires. Not "it's 06:00, run the brief."

Design:
- Called from continuous_monitor.py after detecting critical events
- CAN be called as standalone: --check-and-fire
- Produces targeted "escalation memo" per region (500-1000 words)
- Lighter than full daily brief — faster, cheaper, focused
- Escalation memos feed into next scheduled brief as context

Usage:
    # Check and fire if conditions warrant
    python3 scripts/unscheduled_cognition.py --check

    # Fire analysis for a specific region immediately
    python3 scripts/unscheduled_cognition.py --fire --region middle_east --trigger "Kalshi swing 25pts"
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BEHAVIORAL_STATE_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "behavioral-state.json"
AUTONOMY_TRACKER_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "autonomy-tracker.json"
ANALYSIS_DIR = REPO_ROOT / "analysis"
STATE_DIR = REPO_ROOT / "brain" / "memory" / "semantic"

# Minimum confidence in the behavioral state to trigger
MIN_TRIGGER_SEVERITY = "critical"

# Cooldown: don't fire unscheduled analysis for same region more than once per N hours
COOLDOWN_HOURS = 4


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[unscheduled {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, Exception):
            return {}
    return {}


def load_autonomy_tracker() -> dict:
    return load_json(AUTONOMY_TRACKER_FILE) or {
        "version": 1,
        "created": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
        "unscheduled_cognition_events": [],
        "source_trust_changes": [],
        "procedural_learnings": [],
        "autonomous_prioritizations": [],
        "last_updated": None,
    }


def save_autonomy_tracker(tracker: dict) -> None:
    tracker["last_updated"] = dt.datetime.now(dt.timezone.utc).isoformat() + "Z"
    AUTONOMY_TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    AUTONOMY_TRACKER_FILE.write_text(json.dumps(tracker, indent=2))


def check_cooldown(region: str, tracker: dict) -> bool:
    """Check if this region is in cooldown (recently analyzed outside schedule)."""
    events = tracker.get("unscheduled_cognition_events", [])
    now = dt.datetime.now(dt.timezone.utc)
    for e in reversed(events):
        if e.get("region") != region:
            continue
        try:
            ts = dt.datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00"))
            if (now - ts).total_seconds() < COOLDOWN_HOURS * 3600:
                return True  # Still in cooldown
        except (ValueError, TypeError):
            continue
    return False


def check_and_fire() -> int:
    """Check behavioral state for critical events and fire analysis if needed."""
    state = load_json(BEHAVIORAL_STATE_FILE)
    if not state:
        log("No behavioral state — nothing to check")
        return 0

    events = state.get("event_directives", {})
    active = events.get("active_escalations", [])
    collection_changes = events.get("collection_changes", [])
    cognition_changes = events.get("cognition_changes", [])

    # Check if there are critical escalations that need immediate cognition
    critical_events = [e for e in active if e.get("severity") == "critical"]

    if not critical_events:
        log("No critical escalations — no unscheduled cognition needed")
        return 0

    tracker = load_autonomy_tracker()

    fired_count = 0
    for event in critical_events:
        region = event.get("region", "global")
        trigger = event.get("trigger", "Unknown trigger")
        severity = event.get("severity", "critical")

        # Check cooldown
        if check_cooldown(region, tracker):
            log(f"  {region} in cooldown — skipping unscheduled analysis")
            continue

        # Check if we have incidents data to analyze
        date_utc = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
        incidents_path = pathlib.Path.home() / "trevor-briefings" / date_utc / "raw" / "incidents.json"
        incidents = load_json(incidents_path).get("incidents", []) if incidents_path.exists() else []
        region_incidents = [i for i in incidents if i.get("region") == region]

        # Fire the analysis
        log(f"FIRING unscheduled analysis for {region} (trigger: {trigger})")

        memo = generate_escalation_memo(region, trigger, severity, region_incidents, date_utc)

        # Save the memo
        memo_dir = ANALYSIS_DIR / date_utc
        memo_dir.mkdir(parents=True, exist_ok=True)
        memo_path = memo_dir / f"escalation-memo-{region}-{dt.datetime.now(dt.timezone.utc).strftime('%H%M%S')}.md"
        memo_path.write_text(memo)
        log(f"  Escalation memo saved: {memo_path}")

        # Track this event
        tracker["unscheduled_cognition_events"].append({
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
            "region": region,
            "trigger": trigger,
            "severity": severity,
            "memo_path": str(memo_path),
            "incidents_available": len(region_incidents),
        })
        fired_count += 1

    # Also track if there were collection/cognition changes that didn't trigger analysis
    if collection_changes:
        log(f"  {len(collection_changes)} collection changes noted (pipelined for next run)")

    save_autonomy_tracker(tracker)
    log(f"Fired {fired_count} unscheduled analyses")
    return fired_count


def generate_escalation_memo(region: str, trigger: str, severity: str,
                              incidents: list[dict], date_utc: str) -> str:
    """Generate a targeted escalation memo for a region.

    Uses a lightweight template rather than the full analysis pipeline.
    Annotates incidents with urgency and relevance framing.
    """
    region_label_map = {
        "middle_east": "Middle East", "europe": "Europe", "asia": "Asia",
        "north_america": "North America", "south_central_america": "South & Central America",
        "global_finance": "Global Finance",
    }
    label = region_label_map.get(region, region.title())

    lines = []
    lines.append(f"# ESCALATION MEMO — {label}")
    lines.append(f"**Generated:** {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC")
    lines.append(f"**Trigger:** {trigger}")
    lines.append(f"**Severity:** {severity.upper()}")
    lines.append(f"**Date:** {date_utc}")
    lines.append("")
    lines.append("## Situation")
    lines.append("")
    lines.append(f"Unscheduled assessment fired for {label} due to: {trigger}.")
    lines.append("This is a targeted escalation memo — NOT a full regional assessment.")
    lines.append("It provides immediate analytical framing for the principal pending the next")
    lines.append("scheduled daily brief.")
    lines.append("")

    if incidents:
        lines.append("## Recent Incidents (from last collection)")
        lines.append("")
        for inc in incidents[:5]:
            headline = inc.get("headline", "No headline")
            sources = ", ".join(
                s.get("name", "?") if isinstance(s, dict) else str(s)
                for s in inc.get("sources", [])
            ) or "No source"
            lines.append(f"- **{headline}** [source: {sources}]")
        if len(incidents) > 5:
            lines.append(f"- *... and {len(incidents) - 5} more incidents*")
        lines.append("")
    else:
        lines.append("*No recent incidents collected for this region.*")
        lines.append("")

    lines.append("## Analytical Implications")
    lines.append("")
    lines.append(f"The {trigger} event suggests heightened attention to {label} is warranted.")
    lines.append("Possible implications to monitor in the next 24-48 hours:")
    lines.append("- Whether the triggering event reflects a trend shift or a single-instance spike")
    lines.append("- Whether adjacent regions or sectors show correlated movement")
    lines.append("- Whether collection reveals corroborating or contradicting signals")
    lines.append("")
    lines.append("## Next Steps")
    lines.append("")
    lines.append("1. Next scheduled brief will have restricted confidence bands for this region")
    lines.append("2. Collection for this region will be augmented (if not already)")
    lines.append("3. This memo will be fed into the next analysis pipeline")
    lines.append("")

    return "\n".join(lines)


def fire_direct(region: str, trigger: str) -> int:
    """Fire unscheduled analysis for a specific region immediately (--fire)."""
    tracker = load_autonomy_tracker()

    date_utc = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    incidents_path = pathlib.Path.home() / "trevor-briefings" / date_utc / "raw" / "incidents.json"
    incidents = load_json(incidents_path).get("incidents", []) if incidents_path.exists() else []
    region_incidents = [i for i in incidents if i.get("region") == region]

    log(f"FIRING DIRECT: unscheduled analysis for {region} (trigger: {trigger})")
    memo = generate_escalation_memo(region, trigger, "direct", region_incidents, date_utc)

    memo_dir = ANALYSIS_DIR / "escalation-memos"
    memo_dir.mkdir(parents=True, exist_ok=True)
    memo_path = memo_dir / f"{region}-{dt.datetime.now(dt.timezone.utc).strftime('%H%M%S')}.md"
    memo_path.write_text(memo)
    print(memo_path)

    tracker["unscheduled_cognition_events"].append({
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
        "region": region,
        "trigger": trigger,
        "severity": "direct",
        "memo_path": str(memo_path),
        "incidents_available": len(region_incidents),
    })
    save_autonomy_tracker(tracker)

    log(f"Escalation memo saved: {memo_path}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check behavioral state and fire if needed")
    parser.add_argument("--fire", action="store_true", help="Fire analysis for a specific region")
    parser.add_argument("--region", default="", help="Region for --fire")
    parser.add_argument("--trigger", default="Unscheduled analysis", help="Trigger description")
    args = parser.parse_args()

    if args.fire and args.region:
        return fire_direct(args.region, args.trigger)

    if args.check or (not args.fire and not args.check):
        fired = check_and_fire()
        return 0 if fired is not None else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
