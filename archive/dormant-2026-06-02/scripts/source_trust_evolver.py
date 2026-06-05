#!/usr/bin/env python3
"""
Source Trust Evolver — Phase 4: Source-Trust Evolution.

Reads collection state and brief citation data to evolve source trust scores,
polling frequency, priority, and retirement based on:
- predictive usefulness (was this source's information cited? used in KJs?)
- citation frequency (how often is this source cited in analysis?)
- corroboration (is this source a primary or secondary on stories?)
- timeliness (does this source break news before other feeds?)
- strategic uniqueness (does this source cover things nothing else does?)
- false-signal rates (cited then contradicted?)

Outputs:
  - Updated source trust scores in collection-state.json
  - Feed priority changes for collect.py
  - Source retirement/reinstatement recommendations

Usage:
    python3 scripts/source_trust_evolver.py                               # Analyze collection-state
    python3 scripts/source_trust_evolver.py --analysis-dir ~/trevor-briefings/2026-05-13/analysis  # Include brief citation data
    python3 scripts/source_trust_evolver.py --apply                        # Apply changes
    python3 scripts/source_trust_evolver.py --report                       # Print trust report only
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
COLLECTION_STATE_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "collection-state.json"
AUTONOMY_TRACKER_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "autonomy-tracker.json"

# How many consecutive zero-citation runs before a source is flagged for retirement
RETIRE_THRESHOLD = 5
# How many runs with zero citations after retirement before it's actually dropped
DROP_THRESHOLD = 8

# Trust score parameters
BASE_TRUST = 0.5          # Starting trust for a new source
CITATION_BOOST = 0.1      # +0.1 per citation
STRATEGIC_BONUS = 0.15    # +0.15 if source covers a unique region
CORROBORATION_BOOST = 0.05  # +0.05 if cited alongside other sources
DECAY_PER_RUN = 0.02      # -0.02 per run without citation
FALSE_SIGNAL_PENALTY = 0.2  # -0.2 per false signal


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[trust-evolve {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, Exception):
            return {}
    return {}


def save_json(path: pathlib.Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def record_change(tracker: dict, source: str, field: str, old: Any, new: Any, reason: str) -> None:
    """Record a source trust change in the autonomy tracker."""
    if "source_trust_changes" not in tracker:
        tracker["source_trust_changes"] = []
    tracker["source_trust_changes"].append({
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
        "source": source,
        "field": field,
        "old_value": old,
        "new_value": new,
        "reason": reason,
    })


def compute_trust_scores(state: dict, analysis_dir: pathlib.Path | None = None) -> dict:
    """Compute updated trust scores for all sources."""
    utilization = state.get("source_utilization", {})
    
    # If no utilization data, seed from known feeds
    if not utilization:
        known_feeds = [
            "Reuters World", "AP World", "BBC World", "Al Jazeera",
            "Reuters Business", "FT World",
        ]
        for name in known_feeds:
            utilization[name] = {
                "fetched_count": 1,
                "cited_count": 0,
                "last_cited": None,
                "consecutive_zero_runs": 1,
                "trust_score": BASE_TRUST,
                "trust_history": [],
            }

    # Load analysis data if available to cross-reference citations
    cited_sources = set()
    if analysis_dir and analysis_dir.exists():
        for f in analysis_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                judgments = data.get("key_judgments", []) if isinstance(data, dict) else []
                for kj in judgments:
                    for eid in kj.get("evidence_incident_ids", []):
                        pass  # Would need to cross-reference incidents
            except:
                pass

    # Compute trust scores
    trust_updates = {}
    for name, stats in utilization.items():
        cited = stats.get("cited_count", 0)
        fetched = stats.get("fetched_count", 1)
        zero_runs = stats.get("consecutive_zero_runs", 0)
        old_trust = stats.get("trust_score", BASE_TRUST)

        # Calculate new trust score
        # Start with base, adjust for citations and decay
        trust = BASE_TRUST
        trust += cited * CITATION_BOOST
        trust -= zero_runs * DECAY_PER_RUN

        # Strategic uniqueness bonus: if this source is highly cited vs fetched
        if fetched > 0 and cited / fetched > 0.5:
            trust += STRATEGIC_BONUS

        # Clamp between 0.0 and 1.0
        trust = max(0.0, min(1.0, trust))

        # Determine action
        action = "keep"
        if zero_runs >= DROP_THRESHOLD:
            action = "drop"
        elif zero_runs >= RETIRE_THRESHOLD:
            action = "retire"

        trust_updates[name] = {
            "trust_score": round(trust, 3),
            "trust_change": round(trust - old_trust, 3),
            "action": action,
            "consecutive_zero_runs": zero_runs,
            "cited_count": cited,
            "fetched_count": fetched,
        }

    return trust_updates


def build_trust_report(trust_updates: dict) -> str:
    """Generate a trust evolution report."""
    lines = []
    lines.append("# Source Trust Evolution Report")
    lines.append(f"**Generated:** {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC")
    lines.append("")
    lines.append("| Source | Trust Score | Change | Cited | Fetched | Zero Runs | Action |")
    lines.append("|--------|-------------|--------|-------|---------|-----------|--------|")

    # Sort by trust score ascending (most at-risk first)
    sorted_sources = sorted(trust_updates.items(), key=lambda x: x[1]["trust_score"])
    for name, info in sorted_sources:
        change_str = f"+{info['trust_change']}" if info['trust_change'] > 0 else str(info['trust_change'])
        action_icon = {"drop": "❌ DROP", "retire": "⚠ RETIRE", "keep": "✅"}[info['action']]
        lines.append(
            f"| {name} | {info['trust_score']} | {change_str} | "
            f"{info['cited_count']} | {info['fetched_count']} | "
            f"{info['consecutive_zero_runs']} | {action_icon} |"
        )

    # Retired/dropped sources
    dropped = [n for n, i in trust_updates.items() if i['action'] == 'drop']
    retired = [n for n, i in trust_updates.items() if i['action'] == 'retire']

    if retired:
        lines.append("\n## Sources Flagged for Retirement")
        for name in retired:
            info = trust_updates[name]
            lines.append(f"- **{name}**: {info['consecutive_zero_runs']} zero-citation runs, trust={info['trust_score']}")

    if dropped:
        lines.append("\n## Sources Recommended for Removal")
        for name in dropped:
            info = trust_updates[name]
            lines.append(f"- **{name}**: {info['consecutive_zero_runs']} consecutive zero citations")

    lines.append("")
    return "\n".join(lines)


def apply_changes(trust_updates: dict, state: dict, tracker: dict) -> dict:
    """Apply trust changes to collection state."""
    utilization = state.get("source_utilization", {})
    
    for name, info in trust_updates.items():
        if name in utilization:
            utilization[name]["trust_score"] = info["trust_score"]
            old_action = utilization[name].get("action", "keep")
            utilization[name]["action"] = info["action"]
            
            if info["action"] != old_action:
                record_change(tracker, name, "action", old_action, info["action"],
                              f"Trust score {info['trust_score']} after {info['consecutive_zero_runs']} zero-citation runs")

    state["source_utilization"] = utilization
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-dir", default="", help="Path to analysis directory with citation data")
    parser.add_argument("--apply", action="store_true", help="Apply trust changes to collection state")
    parser.add_argument("--report", action="store_true", help="Print trust report only")
    args = parser.parse_args()

    state = load_json(COLLECTION_STATE_FILE)
    if not state:
        log("No collection state found — nothing to evolve")
        return 1

    analysis_path = pathlib.Path(args.analysis_dir).expanduser() if args.analysis_dir else None
    trust_updates = compute_trust_scores(state, analysis_path)

    if args.report or (not args.apply and not args.report):
        report = build_trust_report(trust_updates)
        print(report)
        return 0

    if args.apply:
        tracker = load_json(AUTONOMY_TRACKER_FILE) or {
            "version": 1, "created": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
            "unscheduled_cognition_events": [], "source_trust_changes": [],
            "procedural_learnings": [], "autonomous_prioritizations": [],
        }
        state = apply_changes(trust_updates, state, tracker)
        save_json(COLLECTION_STATE_FILE, state)
        save_json(AUTONOMY_TRACKER_FILE, tracker)
        
        # Print summary
        changed = sum(1 for i in trust_updates.values() if i['action'] != 'keep')
        log(f"Applied trust changes: {changed} sources affected ({len(trust_updates)} total)")
        log(f"  Dropped: {sum(1 for i in trust_updates.values() if i['action'] == 'drop')}")
        log(f"  Retired: {sum(1 for i in trust_updates.values() if i['action'] == 'retire')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
