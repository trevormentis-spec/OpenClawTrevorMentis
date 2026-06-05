#!/usr/bin/env python3
"""
intel_api.py — Intelligence Query API for KJ Feed.

Provides RESTful query endpoints over the KJ feed archive:
  1. Query by narrative ID
  2. Query by region / topic
  3. Query by confidence range
  4. Time-series for a specific narrative
  5. Current state summary (for agent handshake)

Designed for machine consumption by other agents (A2A protocol) and
available as a local file-based API (no HTTP server needed — reads
the KJ feed archive directly).

Usage:
    python3 analyst/scripts/intel_api.py list-narratives
    python3 analyst/scripts/intel_api.py get-narrative <id>
    python3 analyst/scripts/intel_api.py search --query "iran" --min-confidence 60
    python3 analyst/scripts/intel_api.py history --narrative iran_nuclear_deal_before_june --hours 48
    python3 analyst/scripts/intel_api.py timeline --narrative iran_nuclear_deal_before_june
    python3 analyst/scripts/intel_api.py state-summary
    python3 analyst/scripts/intel_api.py agent-handshake     # A2A: full state for agent discovery
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
from typing import Any

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
FEED_DIR = REPO / "exports" / "kj-feeds"
LATEST_FEED = FEED_DIR / "latest.json"
COGNITION_STATE = REPO / "skills" / "continuous-cognition" / "state" / "cognition_state.json"
AGENT_CARD_PATH = REPO / ".well-known" / "agent-card.json"


def log(msg: str) -> None:
    print(f"[intel_api] {msg}", file=sys.stderr, flush=True)


def load_latest() -> dict | None:
    if LATEST_FEED.exists():
        try:
            return json.loads(LATEST_FEED.read_text())
        except (json.JSONDecodeError,):
            pass
    return None


def load_jsonl(path: pathlib.Path) -> list[dict]:
    """Load all entries from a JSONL file."""
    entries = []
    if path.exists():
        for line in path.read_text().splitlines():
            try:
                entries.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                pass
    return entries


def load_history(hours: int = 48) -> list[dict]:
    """Load KJ feed history from JSONL archives within the time window."""
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=hours)
    cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")

    entries = []
    for p in sorted(FEED_DIR.glob("*.jsonl")):
        date_str = p.stem
        try:
            date = dt.date.fromisoformat(date_str)
        except ValueError:
            continue
        if dt.date.fromisoformat(date_str) < cutoff.date():
            continue
        for entry in load_jsonl(p):
            ts = entry.get("timestamp", "")
            if ts >= cutoff_str:
                entries.append(entry)

    # Also try simple date files
    for p in sorted(FEED_DIR.glob("????-??-??.json")):
        date_str = p.stem
        try:
            date = dt.date.fromisoformat(date_str)
        except ValueError:
            continue
        if date < cutoff.date():
            continue
        if p.exists() and p != LATEST_FEED:
            try:
                entries.append(json.loads(p.read_text()))
            except (json.JSONDecodeError,):
                pass

    # Deduplicate by cycle
    seen = set()
    unique = []
    for e in sorted(entries, key=lambda x: x.get("cycle", 0)):
        cycle = e.get("cycle", 0)
        if cycle not in seen:
            seen.add(cycle)
            unique.append(e)
    return unique


def cmd_list_narratives(args):
    feed = load_latest()
    if not feed:
        log("No feed available")
        return 1

    narratives = feed.get("narratives", [])
    if not narratives:
        print("No active narratives.")
        return 0

    print(f"\nActive narratives ({len(narratives)}):")
    print(f"{'ID':<40} {'Conf':>5} {'Band':<20} {'Trend':<10} {'Ev':>4} {'Horizon':>10}")
    print("-" * 95)
    for n in sorted(narratives, key=lambda x: x["id"]):
        horizon = n.get("hours_to_resolution")
        horizon_str = f"{horizon:.0f}h" if horizon else "-"
        print(f"{n['id']:<40} {n['confidence']:>5} {n['kent_band']:<20} {n['trend']:<10} {n['evidence_for']:>3}f/{n['evidence_against']:<2}a {horizon_str:>10}")
    return 0


def cmd_get_narrative(args):
    feed = load_latest()
    if not feed:
        log("No feed available")
        return 1

    nid = args.narrative_id
    for n in feed.get("narratives", []):
        if n["id"] == nid:
            # Enrich with source trust info
            result = dict(n)
            result["source_trust"] = [
                s for s in feed.get("source_trust", [])
                if s.get("source_id") in n.get("catalysts", [])
            ]
            result["feed_timestamp"] = feed["timestamp"]
            result["feed_cycle"] = feed["cycle"]
            print(json.dumps(result, indent=2))
            return 0

    log(f"Narrative '{nid}' not found")
    return 1


def cmd_search(args):
    feed = load_latest()
    if not feed:
        log("No feed available")
        return 1

    query = (args.query or "").lower()
    min_conf = args.min_confidence or 0
    max_conf = args.max_confidence or 100
    band = (args.band or "").lower()

    results = []
    for n in feed.get("narratives", []):
        if query and query not in n["id"].lower() and query not in (n.get("reasoning", "") or "").lower():
            continue
        if n["confidence"] < min_conf or n["confidence"] > max_conf:
            continue
        if band and n["kent_band"] != band:
            continue
        results.append(n)

    if not results:
        print("No matching narratives.")
        return 0

    print(f"\nSearch results ({len(results)}):")
    for n in sorted(results, key=lambda x: x["id"]):
        print(f"  [{n['id']}] {n['kent_band']} ({n['confidence']}%) {n['trend']} — {n.get('reasoning','')[:120]}")
    return 0


def cmd_history(args):
    """Show history for a narrative across cycles."""
    entries = load_history(hours=args.hours or 48)

    # Collect history for this narrative
    history = []
    for feed in entries:
        for n in feed.get("narratives", []):
            if n["id"] == args.narrative:
                history.append({
                    "cycle": feed.get("cycle", 0),
                    "timestamp": feed.get("timestamp", ""),
                    "confidence": n["confidence"],
                    "trend": n["trend"],
                    "kent_band": n["kent_band"],
                    "evidence_for": n["evidence_for"],
                    "evidence_against": n["evidence_against"],
                })
                break

    if not history:
        print(f"No history for '{args.narrative}' in the last {args.hours}h")
        return 0

    print(f"\nConfidence history for '{args.narrative}' ({len(history)} data points):")
    print(f"{'Cycle':>6} {'Timestamp':<22} {'Conf':>5} {'Band':<20} {'Trend':<10}")
    print("-" * 70)
    for h in history:
        print(f"{h['cycle']:>6} {h['timestamp']:<22} {h['confidence']:>5} {h['kent_band']:<20} {h['trend']:<10}")
    return 0


def cmd_timeline(args):
    """Output JSON time-series for a narrative (for charting/consumption)."""
    entries = load_history(hours=args.hours or 48)
    timeline = []
    for feed in entries:
        for n in feed.get("narratives", []):
            if n["id"] == args.narrative:
                timeline.append({
                    "cycle": feed.get("cycle", 0),
                    "timestamp": feed.get("timestamp", ""),
                    "confidence": n["confidence"],
                    "evidence_for": n["evidence_for"],
                    "evidence_against": n["evidence_against"],
                })
                break

    result = {
        "narrative_id": args.narrative,
        "data_points": len(timeline),
        "span_hours": args.hours,
        "timeline": timeline,
    }
    print(json.dumps(result, indent=2))
    return 0


def cmd_state_summary(args):
    """Agent-friendly state summary."""
    feed = load_latest()
    if not feed:
        log("No feed available")
        return 1

    summary = {
        "service": "trevor-intel-api",
        "version": feed.get("feed_version", 1),
        "cycle": feed.get("cycle", 0),
        "timestamp": feed.get("timestamp", ""),
        "narrative_count": len(feed.get("narratives", [])),
        "source_count": len(feed.get("source_trust", [])),
        "signal_count": len(feed.get("weak_signals", [])),
        "escalation_count": len(feed.get("escalations", [])),
        "narratives": [
            {"id": n["id"], "confidence": n["confidence"],
             "kent_band": n["kent_band"], "trend": n["trend"]}
            for n in feed.get("narratives", [])
        ],
        "system": feed.get("system", {}),
        "delta": feed.get("delta", {}),
    }
    print(json.dumps(summary, indent=2))
    return 0


def cmd_agent_handshake(args):
    """A2A agent handshake — full state for agent discovery."""
    feed = load_latest()
    state = None
    if COGNITION_STATE.exists():
        try:
            state = json.loads(COGNITION_STATE.read_text())
        except (json.JSONDecodeError,):
            pass

    card = None
    if AGENT_CARD_PATH.exists():
        try:
            card = json.loads(AGENT_CARD_PATH.read_text())
        except (json.JSONDecodeError,):
            pass

    handshake = {
        "agent_name": "Trevor",
        "agent_description": "Threat Research and Evaluation Virtual Operations Resource",
        "capabilities": [
            "kj_feed_v1",
            "confidence_swing_alerts",
            "continuous_cognition",
            "daily_intel_brief",
            "prediction_market_analysis",
        ],
        "feed_version": feed.get("feed_version", 1) if feed else None,
        "current_cycle": feed.get("cycle", 0) if feed else 0,
        "last_cognition_run": state.get("last_run") if state else None,
        "narrative_count": len(feed.get("narratives", [])) if feed else 0,
        "cognition_healthy": state.get("operational_state", {}).get("healthy", False) if state else False,
        "total_spent_usd": state.get("token_economics", {}).get("total_spent_cents", 0) / 100 if state else 0,
        "agent_card": card,
    }
    print(json.dumps(handshake, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser(description="Intelligence Query API")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list-narratives
    subparsers.add_parser("list-narratives", help="List all active narratives")

    # get-narrative
    gn = subparsers.add_parser("get-narrative", help="Get narrative details")
    gn.add_argument("narrative_id")

    # search
    s = subparsers.add_parser("search", help="Search narratives")
    s.add_argument("--query", default="", help="Search text (narrative ID or reasoning)")
    s.add_argument("--min-confidence", type=int, default=0, help="Minimum confidence %")
    s.add_argument("--max-confidence", type=int, default=100, help="Maximum confidence %")
    s.add_argument("--band", default="", help="Kent band filter")

    # history
    h = subparsers.add_parser("history", help="Confidence history for a narrative")
    h.add_argument("narrative")
    h.add_argument("--hours", type=int, default=48, help="Lookback window (hours)")

    # timeline
    t = subparsers.add_parser("timeline", help="JSON time-series for a narrative")
    t.add_argument("narrative")
    t.add_argument("--hours", type=int, default=48, help="Lookback window (hours)")

    # state-summary
    subparsers.add_parser("state-summary", help="Agent-friendly state summary")

    # agent-handshake
    subparsers.add_parser("agent-handshake", help="A2A agent handshake")

    args = parser.parse_args()

    commands = {
        "list-narratives": cmd_list_narratives,
        "get-narrative": cmd_get_narrative,
        "search": cmd_search,
        "history": cmd_history,
        "timeline": cmd_timeline,
        "state-summary": cmd_state_summary,
        "agent-handshake": cmd_agent_handshake,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
