#!/usr/bin/env python3
"""
kj_feed.py — Structured KJ Feed (Phase 1, Product 2).

Reads cognition_state.json from the continuous cognition daemon and produces
a validated machine-digestible KJ feed in two formats:
  1. exports/kj-feeds/latest.json — current cycle snapshot
  2. exports/kj-feeds/YYYY-MM-DD.jsonl — append-only daily archive

Schema: analyst/schemas/kj-feed-v1.json

Usage:
    python3 analyst/scripts/kj_feed.py                          # Build feed from default state
    python3 analyst/scripts/kj_feed.py --state <path>           # Custom state path
    python3 analyst/scripts/kj_feed.py --output-dir <dir>       # Custom output dir
    python3 analyst/scripts/kj_feed.py --validate-only          # Validate state, no output
    python3 analyst/scripts/kj_feed.py --desk iran              # Desk-scoped feed
    python3 analyst/scripts/kj_feed.py --list-desks             # Show available desks
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
import jsonschema  # pip install jsonschema if missing

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
DEFAULT_STATE = REPO / "skills" / "continuous-cognition" / "state" / "cognition_state.json"
SCHEMA_PATH = REPO / "analyst" / "schemas" / "kj-feed-v1.json"
PHILBY_CONFIG = REPO / "philby" / "desks" / "philby-config.json"
DEFAULT_OUTPUT = REPO / "exports" / "kj-feeds"
PREVIOUS_FEED = DEFAULT_OUTPUT / "latest.json"

# Kent band mapping: integer confidence -> canonical band
KENT_BANDS = [
    (93, 100, "almost_certain"),
    (80, 92,  "highly_likely"),
    (60, 79,  "likely"),
    (40, 59,  "even_chance"),
    (20, 39,  "unlikely"),
    (5,  19,  "highly_unlikely"),
    (0,   4,  "almost_certainly_not"),
]


def _confidence_to_kent(confidence: int) -> str:
    for lo, hi, band in KENT_BANDS:
        if lo <= confidence <= hi:
            return band
    return "no_judgment"


def _utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[kj_feed {ts}] {msg}", file=sys.stderr, flush=True)


def load_desk_config() -> dict:
    """Load Philby desk configuration."""
    try:
        return json.loads(PHILBY_CONFIG.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {"desks": {}}


def filter_narratives_by_desk(narratives: list, desk_id: str, config: dict) -> list:
    """Filter narratives to only those matching a desk's patterns."""
    desk = config.get("desks", {}).get(desk_id)
    if not desk:
        log(f"Unknown desk: {desk_id}")
        return narratives

    patterns = desk.get("narrative_patterns", [])
    keywords = desk.get("keyword_filters", [])

    def matches(n: dict) -> bool:
        nid = n.get("id", "")
        # Check narrative ID patterns
        for pat in patterns:
            if nid.startswith(pat) or re.search(pat, nid):
                return True
        # Check keyword filters against narrative ID and reasoning
        text = f"{nid} {n.get('reasoning', '')} {' '.join(n.get('catalysts', []))}".lower()
        for kw in keywords:
            if kw.lower() in text:
                return True
        return False

    return [n for n in narratives if matches(n)]


def load_state(path: pathlib.Path) -> dict | None:
    try:
        raw = json.loads(path.read_text())
        log(f"Loaded state: cycle {raw.get('cycle', '?')}, "
            f"{len(raw.get('active_narratives', {}))} narratives, "
            f"last_run {raw.get('last_run', '?')}")
        return raw
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log(f"ERROR: Cannot load state from {path}: {e}")
        return None


def load_previous_feed(path: pathlib.Path) -> dict | None:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError,):
            return None
    return None


def compute_delta(current: dict, previous: dict | None) -> dict:
    """Compute delta between current and previous feed."""
    delta = {
        "changed_narratives": [],
        "new_narratives": [],
        "new_signals": [],
        "new_escalations": [],
    }

    current_narrs = {n["id"]: n for n in current.get("narratives", [])}
    prev_narrs = {n["id"]: n for n in previous.get("narratives", [])} if previous else {}

    # New narratives
    for nid in current_narrs:
        if nid not in prev_narrs:
            delta["new_narratives"].append(nid)

    # Changed narratives
    for nid, cn in current_narrs.items():
        if nid in prev_narrs:
            pn = prev_narrs[nid]
            if cn.get("confidence") != pn.get("confidence"):
                delta["changed_narratives"].append({
                    "id": nid,
                    "previous_confidence": pn.get("confidence", 0),
                    "new_confidence": cn.get("confidence", 0),
                    "swing": cn.get("confidence", 0) - pn.get("confidence", 0),
                })

    # New signals
    current_signals = set(s.get("signal", "") for s in current.get("weak_signals", []))
    prev_signals = set(s.get("signal", "") for s in previous.get("weak_signals", [])) if previous else set()
    delta["new_signals"] = list(current_signals - prev_signals)

    # New escalations
    current_escs = {(e.get("narrative", ""), e.get("level", "")) for e in current.get("escalations", [])}
    prev_escs = {(e.get("narrative", ""), e.get("level", "")) for e in previous.get("escalations", [])} if previous else set()
    new_escs = current_escs - prev_escs
    delta["new_escalations"] = [
        e for e in current.get("escalations", [])
        if (e.get("narrative", ""), e.get("level", "")) in new_escs
    ]

    return delta


def build_feed(state: dict, previous: dict | None = None, desk_id: str | None = None) -> dict:
    """Build a KJ feed from cognition_state.json."""
    cycle = state.get("cycle", 0)
    now = _utcnow()
    prev_ts = previous.get("timestamp") if previous else None

    # Build narratives
    narratives = []
    for nid, ndata in state.get("active_narratives", {}).items():
        confidence = ndata.get("confidence", 50)
        evidence = ndata.get("evidence", {})
        evidence_for = len(evidence.get("for", []))
        evidence_against = len(evidence.get("against", []))

        # Calculate hours_to_resolution if resolution_date exists
        hours_to_resolution = None
        res_date = ndata.get("resolution_date")
        if res_date:
            try:
                res_dt = dt.datetime.fromisoformat(res_date)
                now_dt = dt.datetime.now(dt.timezone.utc)
                delta_h = (res_dt - now_dt).total_seconds() / 3600
                hours_to_resolution = round(delta_h, 1)
            except (ValueError, TypeError):
                pass

        narrative = {
            "id": nid,
            "confidence": confidence,
            "trend": ndata.get("trend", "stable"),
            "kent_band": _confidence_to_kent(confidence),
            "reasoning": ndata.get("last_reasoning", ""),
            "evidence_for": evidence_for,
            "evidence_against": evidence_against,
            "catalysts": ndata.get("catalysts", []),
            "created": ndata.get("created", now),
            "last_updated": ndata.get("last_updated", now),
            "hours_to_resolution": hours_to_resolution,
            "resolution_date": res_date,
        }
        narratives.append(narrative)

    # Build source trust
    source_trust = []
    for sid, sdata in state.get("source_trust", {}).items():
        source_trust.append({
            "source_id": sid,
            "admiralty": sdata.get("admiralty", "C3"),
            "track_record": sdata.get("track_record", 0.5),
            "total_assessments": sdata.get("total_assessments", 0),
            "last_updated": sdata.get("last_updated", now),
        })

    # Build weak signals
    weak_signals = []
    for sig in state.get("weak_signals", []):
        weak_signals.append({
            "signal": sig.get("signal", ""),
            "strength": sig.get("strength", 0.0),
            "related_narratives": sig.get("related_narratives", []),
            "first_seen": sig.get("first_seen", now),
            "sightings": sig.get("sightings", 1),
        })

    # Build escalations
    escalations = []
    for esc in state.get("escalation_queue", []):
        escalations.append({
            "level": esc.get("level", "flash"),
            "narrative": esc.get("narrative", ""),
            "reason": esc.get("reason", ""),
            "detected_at": esc.get("detected_at", now),
            "resolved": esc.get("resolved", False),
        })

    # Delta
    delta = compute_delta({
        "narratives": narratives,
        "weak_signals": weak_signals,
        "escalations": escalations,
    }, previous)

    # System info
    sys_info = {
        "disk_usage_pct": _get_disk_usage(),
        "cognition_healthy": state.get("operational_state", {}).get("healthy", True),
        "total_cycles": state.get("cycle", 0),
        "total_spent_usd": round(state.get("token_economics", {}).get("total_spent_cents", 0) / 100, 4),
    }

    # Desk-scoped filtering
    if desk_id:
        config = load_desk_config()
        pre_count = len(narratives)
        narratives = filter_narratives_by_desk(narratives, desk_id, config)
        log(f"Desk '{desk_id}': {pre_count} → {len(narratives)} narratives after filtering")
        # Recompute delta for desk-scoped narratives
        delta = {
            "changed_narratives": [
                c for c in delta.get("changed_narratives", [])
                if c["id"] in {n["id"] for n in narratives}
            ],
            "new_narratives": [
                n for n in delta.get("new_narratives", [])
                if n in {n2["id"] for n2 in narratives}
            ],
            "new_signals": delta.get("new_signals", []),
            "new_escalations": [
                e for e in delta.get("new_escalations", [])
                if e.get("narrative", "") in {n2["id"] for n2 in narratives}
            ],
        }

    feed = {
        "feed_version": 1,
        "cycle": cycle,
        "timestamp": now,
        "desk": desk_id,
        "previous_timestamp": prev_ts,
        "narratives": sorted(narratives, key=lambda x: x["id"]),
        "source_trust": sorted(source_trust, key=lambda x: x["source_id"]),
        "weak_signals": sorted(weak_signals, key=lambda x: x["signal"]),
        "escalations": sorted(escalations, key=lambda x: x.get("detected_at", "")),
        "delta": delta,
        "system": sys_info,
    }

    return feed


def _get_disk_usage() -> int:
    """Get disk usage percentage of the workspace partition."""
    try:
        st = os.statvfs(str(REPO))
        total = st.f_frsize * st.f_blocks
        free = st.f_frsize * st.f_bfree
        used_pct = int(((total - free) / total) * 100)
        return min(used_pct, 99)
    except Exception:
        return 0


def validate_feed(feed: dict, schema: dict) -> list[str]:
    """Validate against kj-feed-v1.json schema. Returns list of errors."""
    try:
        jsonschema.validate(feed, schema)
        return []
    except jsonschema.ValidationError as e:
        return [str(e)]
    except Exception as e:
        return [f"Validation failed: {e}"]


def write_feed(feed: dict, output_dir: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    """Write feed to latest.json and append to daily JSONL."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # latest.json — current snapshot
    latest_path = output_dir / "latest.json"
    latest_path.write_text(json.dumps(feed, indent=2))
    log(f"Wrote latest.json ({latest_path.stat().st_size // 1024} KB)")

    # Daily JSONL — append-only archive
    today = dt.date.today().strftime("%Y-%m-%d")
    jsonl_path = output_dir / f"{today}.jsonl"
    with open(jsonl_path, "a") as f:
        f.write(json.dumps(feed, separators=(",", ":")) + "\n")
    log(f"Appended to {jsonl_path.name}")

    return latest_path, jsonl_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build structured KJ feed from cognition state")
    parser.add_argument("--state", default=str(DEFAULT_STATE), help="Path to cognition_state.json")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT), help="Output directory for feeds")
    parser.add_argument("--validate-only", action="store_true", help="Only validate the state, no output")
    parser.add_argument("--no-validate-schema", action="store_true", help="Skip JSON Schema validation")
    parser.add_argument("--desk", default="", help="Desk-scoped feed (e.g. iran, ukraine, cartel)")
    parser.add_argument("--list-desks", action="store_true", help="Show available desks")
    args = parser.parse_args()

    state_path = pathlib.Path(args.state)
    output_dir = pathlib.Path(args.output_dir)
    schema_path = SCHEMA_PATH if not args.no_validate_schema else None

    # Handle --list-desks
    if args.list_desks:
        config = load_desk_config()
        desks = config.get("desks", {})
        print(f"\nPhilby — Available Desks ({len(desks)}):")
        print(f"{'Desk ID':<16} {'Name':<24} {'Seeded':<8} {'Narratives':<14}")
        print("-" * 66)
        for did, dd in sorted(desks.items()):
            sealed = dd.get("seeded", False)
            state_desc = "✅" if sealed else "❌"
            patterns = dd.get("narrative_patterns", [])
            print(f"{did:<16} {dd.get('name','?'):<24} {state_desc:<8} {', '.join(patterns)[:40]}")
        return 0

    # Validate desk if specified
    desk_id = args.desk or None
    if desk_id:
        config = load_desk_config()
        if desk_id not in config.get("desks", {}):
            log(f"ERROR: Unknown desk '{desk_id}'. Use --list-desks to see available desks.")
            return 1
        desk_name = config["desks"][desk_id]["name"]
        log(f"Building desk-scoped feed: {desk_name}")
        # Use desk-specific output directory
        desk_out = output_dir.parent / "philby" / "feeds" / desk_id
        desk_out.mkdir(parents=True, exist_ok=True)
        output_dir = desk_out

    # Load state
    state = load_state(state_path)
    if not state:
        return 1

    if args.validate_only:
        log("Validation mode: state loaded successfully")
        if schema_path and schema_path.exists():
            schema = json.loads(schema_path.read_text())
            feed = build_feed(state, desk_id=desk_id)
            errors = validate_feed(feed, schema)
            if errors:
                log(f"FEED INVALID ({len(errors)} errors):")
                for e in errors:
                    log(f"  - {e}")
                return 1
            log("Feed validates against schema ✅")
        else:
            log("No schema found, skipping schema validation")
        return 0

    # Build feed (with optional desk filter)
    previous = load_previous_feed(output_dir / "latest.json")
    feed = build_feed(state, previous, desk_id=desk_id)

    # Validate
    if schema_path and schema_path.exists():
        schema = json.loads(schema_path.read_text())
        errors = validate_feed(feed, schema)
        if errors:
            log(f"FEED INVALID ({len(errors)} errors) — still writing but flagging:")
            for e in errors:
                log(f"  - {e}")

    # Write
    latest_path, jsonl_path = write_feed(feed, output_dir)

    summary = (
        f"✅ KJ feed: cycle {feed['cycle']}, "
        f"{len(feed['narratives'])} narratives, "
        f"{len(feed['source_trust'])} sources, "
        f"{len(feed['weak_signals'])} signals, "
        f"{len(feed['escalations'])} escalations, "
        f"{len(feed['delta']['changed_narratives'])} changes"
    )
    print(summary)
    log(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
