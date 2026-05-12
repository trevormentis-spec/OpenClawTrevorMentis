#!/usr/bin/env python3
"""
Collection state manager — persistent state for adaptive collection.

Tracks:
- Source utilization: which sources were cited vs fetched but unused
- Region activity: incident volume per region over time
- Per-region caps: dynamically adjusted based on activity history
- Collection gaps: regions with insufficient coverage

State is a JSON file at brain/memory/semantic/collection-state.json.
Updated after each analysis run. Read by collect.py before each collection.

Usage:
    # Update state from today's analysis
    python3 scripts/collection_state.py --update --analysis-dir ~/trevor-briefings/2026-05-12/analysis
    
    # Query current state
    python3 scripts/collection_state.py --query
    
    # Predict caps for next collection
    python3 scripts/collection_state.py --predict-caps
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "collection-state.json"

# All known sources (from sources.json)
KNOWN_SOURCES = ["Reuters World", "AP World", "BBC World", "Al Jazeera",
                 "Reuters Business", "FT World"]

ALL_REGIONS = [
    "europe", "asia", "middle_east",
    "north_america", "south_central_america", "global_finance",
]

DEFAULT_CAP = 8
MIN_CAP = 3
MAX_CAP = 20
ACTIVITY_HALFLIFE_DAYS = 3  # How fast old activity scores decay


def log(msg: str) -> None:
    print(f"[collection-state] {msg}", file=sys.stderr, flush=True)


def load_state() -> dict:
    """Load existing collection state, or create fresh."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, Exception):
            pass
    return {
        "version": 2,
        "created": dt.datetime.now(dt.timezone.utc).isoformat(),
        "last_updated": None,
        "source_utilization": {},      # source_name → {fetched_count, cited_count, last_cited}
        "region_activity": {},         # region → {incidents_history: [{date, count}], smoothed_score}
        "per_region_cap": {r: DEFAULT_CAP for r in ALL_REGIONS},
        "region_metadata": {r: {"total_incidents": 0, "days_with_data": 0, "last_incident_date": None} for r in ALL_REGIONS},
        "identified_gaps": [],
        "collection_history": [],
    }


def update_from_analysis(state: dict, analysis_dir: pathlib.Path) -> dict:
    """Parse analysis JSONs to determine source utilization and region activity."""
    if not analysis_dir.exists():
        log(f"analysis dir not found: {analysis_dir}")
        return state

    date_tag = analysis_dir.parent.name if analysis_dir.parent.name != "analysis" else "unknown"
    now = dt.datetime.now(dt.timezone.utc)

    # Scan all analysis JSONs for source references
    source_mentions: dict[str, int] = {}
    region_incidents: dict[str, int] = {}

    for f in sorted(analysis_dir.glob("*.json")):
        if f.name == "exec_summary.json":
            continue
        try:
            payload = json.loads(f.read_text())
        except (json.JSONDecodeError, Exception):
            continue

        region = payload.get("region", f.stem)
        inc_count = payload.get("incident_count", 0)
        if region in ALL_REGIONS:
            region_incidents[region] = region_incidents.get(region, 0) + inc_count

        # Extract source citations from key judgments' evidence
        for kj in payload.get("key_judgments", []):
            evidence_ids = kj.get("evidence_incident_ids", [])
            for eid in evidence_ids:
                # Check if evidence IDs map to known sources
                pass  # evidence IDs are hashes, not source names

        # Also check the narrative for source names
        narrative = payload.get("narrative", "")
        for s in KNOWN_SOURCES:
            if s.lower() in narrative.lower():
                source_mentions[s] = source_mentions.get(s, 0) + 1

    # Check exec_summary for source mentions too
    exec_file = analysis_dir / "exec_summary.json"
    if exec_file.exists():
        try:
            exec_data = json.loads(exec_file.read_text())
            bluf = exec_data.get("bluf", "")
            for s in KNOWN_SOURCES:
                if s.lower() in bluf.lower():
                    source_mentions[s] = source_mentions.get(s, 0) + 1
            # Check judgments
            for kj in exec_data.get("five_judgments", []):
                region = kj.get("drawn_from_region", "")
                if region not in region_incidents:
                    region_incidents[region] = 0
                region_incidents[region] += 1
        except (json.JSONDecodeError, Exception):
            pass

    # Update source utilization — track consecutive zero-citation runs
    for s in KNOWN_SOURCES:
        if s not in state["source_utilization"]:
            state["source_utilization"][s] = {
                "fetched_count": 0, "cited_count": 0, "last_cited": None,
                "consecutive_zero_runs": 0,
            }
        state["source_utilization"][s]["fetched_count"] += 1
        if source_mentions.get(s, 0) > 0:
            state["source_utilization"][s]["cited_count"] += 1
            state["source_utilization"][s]["last_cited"] = now.isoformat()
            state["source_utilization"][s]["consecutive_zero_runs"] = 0
        else:
            state["source_utilization"][s]["consecutive_zero_runs"] = \
                state["source_utilization"][s].get("consecutive_zero_runs", 0) + 1

    # Update region activity (with time decay)
    for region in ALL_REGIONS:
        if region not in state["region_activity"]:
            state["region_activity"][region] = {
                "incidents_history": [], "smoothed_score": 0.0,
            }
        history = state["region_activity"][region]["incidents_history"]
        count = region_incidents.get(region, 0)
        history.append({"date": date_tag, "count": count})
        # Keep last 30 days
        history[:] = history[-30:]

        # Calculate smoothed score with time decay
        total = 0.0
        for i, entry in enumerate(history):
            days_ago = len(history) - i - 1
            weight = (ACTIVITY_HALFLIFE_DAYS / (ACTIVITY_HALFLIFE_DAYS + days_ago))
            total += entry["count"] * weight
        state["region_activity"][region]["smoothed_score"] = round(total, 1)

    # Update region metadata
    for region in ALL_REGIONS:
        meta = state["region_metadata"][region]
        count = region_incidents.get(region, 0)
        if count > 0:
            meta["total_incidents"] += count
            meta["days_with_data"] += 1
            meta["last_incident_date"] = date_tag

    # Recalculate per-region caps based on activity
    scores = {
        r: state["region_activity"][r]["smoothed_score"]
        for r in ALL_REGIONS
    }
    max_score = max(scores.values()) or 1
    for region in ALL_REGIONS:
        ratio = scores[region] / max_score
        # Map ratio to cap: 0.0 → MIN_CAP, 1.0 → MAX_CAP
        new_cap = int(MIN_CAP + (MAX_CAP - MIN_CAP) * ratio)
        state["per_region_cap"][region] = max(MIN_CAP, min(MAX_CAP, new_cap))

    # Identify gaps
    gaps = []
    for region in ALL_REGIONS:
        meta = state["region_metadata"][region]
        if meta["days_with_data"] == 0:
            gaps.append(f"{region}: never had incident data")
        elif meta["last_incident_date"] and meta["last_incident_date"] < date_tag:
            gaps.append(f"{region}: no data today (last: {meta['last_incident_date']})")
        elif region_incidents.get(region, 0) == 0:
            gaps.append(f"{region}: zero incidents collected today")
    state["identified_gaps"] = gaps[-10:]  # Keep last 10

    # Add collection history entry
    state["collection_history"].append({
        "date": date_tag,
        "region_counts": region_incidents,
        "source_citations": source_mentions,
        "caps": dict(state["per_region_cap"]),
    })
    state["collection_history"] = state["collection_history"][-90:]  # Keep 90 days

    state["last_updated"] = now.isoformat()
    return state


def save_state(state: dict) -> None:
    """Write state to disk."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))
    log(f"state saved to {STATE_FILE}")


def query_state(state: dict) -> None:
    """Print human-readable status."""
    print("=== COLLECTION STATE ===")
    print(f"Last updated: {state.get('last_updated', 'never')}")
    print()

    print("--- Per-Region Caps ---")
    for region in ALL_REGIONS:
        cap = state["per_region_cap"].get(region, DEFAULT_CAP)
        score = state["region_activity"].get(region, {}).get("smoothed_score", 0)
        meta = state["region_metadata"].get(region, {})
        total = meta.get("total_incidents", 0)
        last = meta.get("last_incident_date", "never")
        print(f"  {region:25s} cap={cap:2d} score={score:5.1f} total={total:3d} last={last}")

    print()
    print("--- Source Utilization ---")
    for s in KNOWN_SOURCES:
        u = state["source_utilization"].get(s, {})
        fetched = u.get("fetched_count", 0)
        cited = u.get("cited_count", 0)
        pct = round(cited / max(fetched, 1) * 100)
        last = (u.get("last_cited") or "never")[:10]
        print(f"  {s:25s} fetched={fetched:2d} cited={cited:2d} ({pct:3d}%) last_cited={last}")

    print()
    gaps = state.get("identified_gaps", [])
    if gaps:
        print(f"--- Collection Gaps ({len(gaps)} items) ---")
        for g in gaps[-5:]:
            print(f"  ⚠  {g}")
    else:
        print("No collection gaps identified")

    print()
    history = state.get("collection_history", [])
    print(f"Collection history: {len(history)} days")


def predict_feed_priorities(state: dict) -> dict:
    """Output feed priority tiers for collect.py.
    
    Tier-1: Fetch every run (high-quality or unproven)
    Tier-2: Fetch every other run (moderate quality)
    Tier-3: Skip until quality improves (0% citation after 3+ runs)
    """
    utilization = state.get("source_utilization", {})
    run_count = max(u.get("fetched_count", 0) for u in utilization.values()) if utilization else 1
    
    feed_priorities = {}
    for source_name, data in utilization.items():
        fetched = data.get("fetched_count", 0)
        cited = data.get("cited_count", 0)
        consecutive_zero = data.get("consecutive_zero_runs", 0)
        
        # Calculate quality score
        if fetched == 0:
            quality = 0.0
        else:
            quality = cited / fetched
        
        # Determine tier
        if fetched < 3:
            # Not enough data — give benefit of doubt, Tier-1
            tier = 1
        elif quality >= 0.3:
            # High citation rate — Tier-1
            tier = 1
        elif consecutive_zero >= 5:
            # 5 consecutive zero-use runs — Tier-3 (retire until something changes)
            tier = 3
        elif quality >= 0.1 or consecutive_zero < 3:
            # Moderate — Tier-2
            tier = 2
        else:
            # Low quality, multiple zero runs — Tier-3
            tier = 3
        
        feed_priorities[source_name] = {
            "tier": tier,
            "quality_score": round(quality, 3),
            "fetched": fetched,
            "cited": cited,
            "consecutive_zero": consecutive_zero,
        }
    
    return {
        "version": 2,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "run_count": run_count,
        "feed_priorities": feed_priorities,
    }


def set_escalation(state: dict, region: str, severity: str,
                   reason: str, trigger: str = "") -> dict:
    """Set an escalation flag for a region.
    
    Severity levels:
    - critical: major event, double collection intensity
    - significant: notable event, increase collection intensity 50%
    - notable: minor event, moderate increase
    
    Escalations expire after 24 hours.
    """
    if "active_escalations" not in state:
        state["active_escalations"] = []
    
    now = dt.datetime.now(dt.timezone.utc)
    
    # Remove expired escalations for this region
    state["active_escalations"] = [
        e for e in state["active_escalations"]
        if e["region"] != region or (
            (now - dt.datetime.fromisoformat(e["set_at"])).total_seconds() < 86400
        )
    ]
    
    # Add new escalation
    state["active_escalations"].append({
        "region": region,
        "severity": severity,
        "reason": reason,
        "trigger": trigger,
        "set_at": now.isoformat(),
        "expires_at": (now + dt.timedelta(hours=24)).isoformat(),
    })
    
    # Log the escalation as a collection gap
    gap_str = f"ESCALATION [{severity.upper()}]: {region} — {reason}"
    if gap_str not in state.get("identified_gaps", []):
        state.setdefault("identified_gaps", []).append(gap_str)
        state["identified_gaps"] = state["identified_gaps"][-20:]
    
    return state


def clear_expired_escalations(state: dict) -> dict:
    """Remove escalations older than 24h."""
    if "active_escalations" not in state:
        return state
    now = dt.datetime.now(dt.timezone.utc)
    before = len(state["active_escalations"])
    state["active_escalations"] = [
        e for e in state["active_escalations"]
        if (now - dt.datetime.fromisoformat(e["set_at"])).total_seconds() < 86400
    ]
    after = len(state["active_escalations"])
    if before != after:
        log(f"cleared {before - after} expired escalation(s)")
    return state


def predict_caps(state: dict) -> dict:
    """Output the predicted caps for the next collection run.
    
    Factors in active escalations: critical → +100%, significant → +50%.
    """
    caps = state.get("per_region_cap", {r: DEFAULT_CAP for r in ALL_REGIONS})
    base = dict(caps)
    
    # Clear expired first and persist
    state = clear_expired_escalations(state)
    save_state(state)  # Persist cleared state so future calls see fresh data
    
    # Apply escalation multipliers
    escalations = state.get("active_escalations", [])
    for e in escalations:
        region = e["region"]
        severity = e["severity"]
        if severity == "critical":
            caps[region] = min(MAX_CAP * 2, int(caps.get(region, DEFAULT_CAP) * 2.0))
        elif severity == "significant":
            caps[region] = min(MAX_CAP * 2, int(caps.get(region, DEFAULT_CAP) * 1.5))
        elif severity == "notable":
            caps[region] = min(MAX_CAP, int(caps.get(region, DEFAULT_CAP) * 1.25))
    
    if escalations:
        changes = {r: f"{base[r]}→{caps[r]}" for r in set(list(base.keys()) + list(caps.keys())) 
                   if base.get(r) != caps.get(r)}
        if changes:
            log(f"escalation caps applied: {changes}")
    
    return {
        "version": 2,
        "per_region_cap": caps,
        "active_escalations": [
            {"region": e["region"], "severity": e["severity"],
             "reason": e["reason"], "expires_at": e["expires_at"]}
            for e in escalations
        ],
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update", action="store_true",
                        help="Update state from today's analysis")
    parser.add_argument("--analysis-dir", default="",
                        help="Path to analysis directory (required with --update)")
    parser.add_argument("--query", action="store_true",
                        help="Query current collection state")
    parser.add_argument("--predict-caps", action="store_true",
                        help="Output predicted caps for next collection")
    parser.add_argument("--feed-priorities", action="store_true",
                        help="Output feed priority tiers for collect.py")
    parser.add_argument("--set-escalation", action="store_true",
                        help="Set an escalation flag for a region")
    parser.add_argument("--region", default="",
                        help="Region for escalation (required with --set-escalation)")
    parser.add_argument("--severity", choices=["critical", "significant", "notable"],
                        default="significant",
                        help="Escalation severity (default: significant)")
    parser.add_argument("--reason", default="",
                        help="Reason for escalation")
    parser.add_argument("--trigger", default="",
                        help="Trigger event (e.g., 'Kalshi swing 22pts')")
    parser.add_argument("--clear-escalations", action="store_true",
                        help="Clear expired escalations")
    args = parser.parse_args()

    state = load_state()

    if args.set_escalation:
        if not args.region or not args.reason:
            log("ERROR: --region and --reason required with --set-escalation")
            return 1
        state = clear_expired_escalations(state)
        state = set_escalation(state, args.region, args.severity, args.reason, args.trigger)
        save_state(state)
        log(f"escalation set: [{args.severity.upper()}] {args.region} — {args.reason}")
        return 0

    if args.clear_escalations:
        # Remove ALL escalations, not just expired
        if "active_escalations" in state:
            count = len(state["active_escalations"])
            state["active_escalations"] = []
            # Also clean gap entries
            state["identified_gaps"] = [
                g for g in state.get("identified_gaps", [])
                if not g.startswith("ESCALATION")
            ]
            save_state(state)
            log(f"cleared {count} escalation(s)")
        return 0

    if args.update:
        if not args.analysis_dir:
            log("ERROR: --analysis-dir required with --update")
            return 1
        analysis_dir = pathlib.Path(args.analysis_dir).expanduser().resolve()
        state = update_from_analysis(state, analysis_dir)
        save_state(state)

    if args.query:
        query_state(state)

    if args.predict_caps:
        caps = predict_caps(state)
        print(json.dumps(caps))

    if args.feed_priorities:
        priorities = predict_feed_priorities(state)
        print(json.dumps(priorities))

    if not any([args.update, args.query, args.predict_caps, args.feed_priorities]):
        parser.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(main())
