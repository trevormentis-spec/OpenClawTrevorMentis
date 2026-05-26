#!/usr/bin/env python3
"""
KJ Feed Generator — Structured Key Judgment Feed v1

Reads cognition_state.json and produces a validated KJ feed JSON.
Outputs:
  - exports/kj-feeds/kj-feed-latest.json  (latest feed, overwritten each cycle)
  - exports/kj-feeds/kj-feed-YYYY-MM-DD.jsonl  (daily archive, appended per cycle)

Usage:
  python3 kj_feed.py                        # Generate feed, write to exports
  python3 kj_feed.py --validate             # Validate schema only
  python3 kj_feed.py --stdout               # Print to stdout for pipeline use
  python3 kj_feed.py --desk iran            # Scoped feed for one topic desk
"""

import sys
import os
import json
import copy
import datetime
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger("kj-feed")
logger.setLevel(logging.WARNING)

WORKSPACE = Path(__file__).parent.parent.parent
COG_STATE_PATH = WORKSPACE / "skills" / "continuous-cognition" / "state" / "cognition_state.json"
SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "kj-feed-v1.json"
EXPORT_DIR = WORKSPACE / "exports" / "kj-feeds"

# Kent band mapping
KENT_BANDS = {
    (95, 100): "almost_certain",
    (85, 94): "highly_likely",
    (70, 84): "likely",
    (50, 69): "even_chance",
    (30, 49): "unlikely",
    (15, 29): "highly_unlikely",
    (0, 14): "almost_certainly_not",
}


def _calc_kent_band(confidence: int) -> str:
    """Map numeric confidence to Sherman Kent band."""
    if confidence is None:
        return "no_judgment"
    for (lo, hi), band in KENT_BANDS.items():
        if lo <= confidence <= hi:
            return band
    return "no_judgment"


def _resolve_last_timestamp() -> Optional[str]:
    """Read the timestamp from the latest feed file if it exists."""
    latest = EXPORT_DIR / "kj-feed-latest.json"
    if latest.exists():
        try:
            with open(latest) as f:
                prev = json.load(f)
                return prev.get("timestamp")
        except Exception:
            pass
    return None


def _load_cognition_state() -> Optional[dict]:
    """Load the cognition state, handling missing file gracefully."""
    if not COG_STATE_PATH.exists():
        logger.warning("Cognition state not found — has cognition run yet?")
        return None
    try:
        with open(COG_STATE_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Cognition state corrupt: {e}")
        return None


def _calc_delta(prev_state: dict, state: dict) -> dict:
    """Compute what changed between the previous feed and current state."""
    delta = {"changed_narratives": [], "new_narratives": [], "new_signals": [], "new_escalations": []}

    # Narratives present now but not before
    prev_narr = {n["id"]: n for n in prev_state.get("narratives", [])}
    curr_narr = state.get("active_narratives", {})

    for nid, curr in curr_narr.items():
        if nid not in prev_narr:
            delta["new_narratives"].append(nid)
        else:
            prev_conf = prev_narr[nid].get("confidence", 0)
            curr_conf = curr.get("confidence", 0)
            if prev_conf != curr_conf:
                delta["changed_narratives"].append({
                    "id": nid,
                    "previous_confidence": prev_conf,
                    "new_confidence": curr_conf,
                    "swing": curr_conf - prev_conf,
                })

    # Escalations
    curr_esc = state.get("escalation_queue", [])
    prev_esc = prev_state.get("escalations", [])
    if len(curr_esc) > len(prev_esc):
        delta["new_escalations"] = [
            e.get("narrative", "?") for e in curr_esc[len(prev_esc):]
        ]

    return delta


def generate_feed(desk: Optional[str] = None) -> Optional[dict]:
    """Generate a KJ feed from the current cognition state."""
    state = _load_cognition_state()
    if not state:
        return None

    now = datetime.datetime.now(datetime.UTC)
    prev_ts = _resolve_last_timestamp()

    # Build narratives array
    narratives = []
    all_narratives = state.get("active_narratives", {})

    for nid, n in all_narratives.items():
        if desk and desk not in nid.lower():
            continue

        # Estimate resolution timeline from narrative data
        resolution_date = n.get("resolution_date")
        hours_to_resolution = None
        if resolution_date:
            try:
                resol = datetime.datetime.fromisoformat(resolution_date)
                hours_to_resolution = max(0, (resol - now).total_seconds() / 3600)
            except Exception:
                pass

        narratives.append({
            "id": nid,
            "confidence": n.get("confidence", 50),
            "trend": n.get("trend", "stable"),
            "kent_band": _calc_kent_band(n.get("confidence", 50)),
            "reasoning": n.get("last_reasoning", ""),
            "evidence_for": len(n.get("evidence", {}).get("for", [])),
            "evidence_against": len(n.get("evidence", {}).get("against", [])),
            "catalysts": n.get("catalysts", []),
            "created": n.get("created", now.isoformat()),
            "last_updated": n.get("last_updated", now.isoformat()),
            "hours_to_resolution": hours_to_resolution,
            "resolution_date": resolution_date,
        })

    # Source trust
    source_trust = []
    for sid, s in state.get("source_trust", {}).items():
        source_trust.append({
            "source_id": sid,
            "admiralty": s.get("admiralty", "C3"),
            "track_record": round(s.get("track_record", 0.5), 3),
            "total_assessments": s.get("total_assessments", 0),
            "last_updated": s.get("last_updated", now.isoformat()),
        })

    # Weak signals
    weak_signals = state.get("weak_signals", [])

    # Escalations (only pending/unresolved from last cycle)
    es = state.get("escalation_queue", [])
    unp_resolved = [e for e in es if not e.get("resolved", False)]
    escalations = [
        {
            "level": e.get("level", "flash"),
            "narrative": e.get("narrative", ""),
            "reason": e.get("reason", ""),
            "detected_at": e.get("detected_at", now.isoformat()),
            "resolved": e.get("resolved", False),
        }
        for e in unp_resolved[-5:]  # Last 5 only
    ]

    # System health
    ops = state.get("operational_state", {})
    tek = state.get("token_economics", {})

    # Build previous feed for delta computation
    prev_feed = _load_previous_feed()
    delta = _calc_delta(prev_feed, state) if prev_feed else {
        "changed_narratives": [],
        "new_narratives": list(all_narratives.keys()),
        "new_signals": [],
        "new_escalations": [],
    }

    feed = {
        "feed_version": 1,
        "cycle": state.get("cycle", 0),
        "timestamp": now.isoformat(),
        "previous_timestamp": prev_ts,
        "narratives": narratives,
        "source_trust": source_trust,
        "weak_signals": [s for s in weak_signals if s.get("strength", 0) > 0.05][:20],
        "escalations": escalations,
        "delta": delta,
        "system": {
            "disk_usage_pct": int(os.popen("df / | tail -1 | awk '{print $5}' | sed 's/%//'").read().strip() or "0"),
            "cognition_healthy": ops.get("healthy", False),
            "total_cycles": tek.get("cycles_completed", 0),
            "total_spent_usd": round(tek.get("total_spent_cents", 0) / 100, 4),
        },
    }

    return feed


def _load_previous_feed() -> Optional[dict]:
    """Load the previous feed for delta computation."""
    latest = EXPORT_DIR / "kj-feed-latest.json"
    if latest.exists():
        try:
            with open(latest) as f:
                return json.load(f)
        except Exception:
            pass
    return None


def validate_feed(feed: dict) -> bool:
    """Validate feed against the JSON schema."""
    try:
        import jsonschema
        with open(SCHEMA_PATH) as f:
            schema = json.load(f)
        jsonschema.validate(feed, schema)
        return True
    except ImportError:
        logger.warning("jsonschema not installed — skipping validation")
        return True
    except jsonschema.ValidationError as e:
        logger.error(f"Schema validation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False


def write_feed(feed: dict, stdout: bool = False, validate: bool = False) -> bool:
    """Write the feed to disk (or stdout)."""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    if validate and not validate_feed(feed):
        return False

    if stdout:
        print(json.dumps(feed, indent=2, default=str))
        return True

    # Write latest (overwrite)
    latest_path = EXPORT_DIR / "kj-feed-latest.json"
    with open(latest_path, "w") as f:
        json.dump(feed, f, indent=2, default=str)

    # Append to daily archive
    today = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    archive_path = EXPORT_DIR / f"kj-feed-{today}.jsonl"
    with open(archive_path, "a") as f:
        record = {"ts": feed["timestamp"], "cycle": feed["cycle"], "feed": feed}
        f.write(json.dumps(record, default=str) + "\n")

    logger.info(f"Feed written: cycle {feed['cycle']}, {len(feed['narratives'])} narratives")
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description="KJ Feed Generator")
    parser.add_argument("--validate", action="store_true", help="Validate against schema")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout")
    parser.add_argument("--desk", type=str, help="Scope to a topic desk (e.g. iran)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    feed = generate_feed(desk=args.desk)
    if feed is None:
        print("No feed generated — cognition state unavailable", file=sys.stderr)
        sys.exit(1)

    if not write_feed(feed, stdout=args.stdout, validate=args.validate):
        sys.exit(1)


if __name__ == "__main__":
    main()
