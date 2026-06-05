#!/usr/bin/env python3
"""
Continuous Cognition State Manager

Manages persistent cognitive state:
- Active narratives with confidence bands
- Source trust evolution
- Weak signal cache
- Narrative drift tracking
- Escalation queue
- Token economics

This is the "epistemic bookkeeping" layer.
All mutations go through this module — no direct file writes elsewhere.
"""

import os
import json
import time
import copy
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger("cognition-state")
logger.setLevel(logging.WARNING)

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / "state"
STATE_PATH = STATE_DIR / "cognition_state.json"
CONFIG_PATH = BASE_DIR / "config.yaml"

# Default state
DEFAULT_STATE = {
    "version": 2,
    "cycle": 0,
    "last_run": None,
    "active_narratives": {},
    "source_trust": {},
    "weak_signals": [],
    "narrative_drift": {},
    "escalation_queue": [],
    "token_economics": {
        "total_spent_cents": 0.0,
        "cycles_completed": 0,
        "avg_cost_per_cycle": 0.0,
        "daily_spent_cents": 0.0,
        "last_daily_reset": None,
    },
    "operational_state": {
        "healthy": True,
        "last_error": None,
        "last_error_time": None,
        "cycles_since_error": 0,
        "errors_consecutive": 0,
    },
    "memory_actions": [],
    "anomalies_detected": [],
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ts() -> float:
    return time.time()


# ── Load / Save ─────────────────────────────────────────────────────

def load_state() -> dict:
    """Load state from disk, returning default if corrupt or missing."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not STATE_PATH.exists():
        return copy.deepcopy(DEFAULT_STATE)
    try:
        with open(STATE_PATH) as f:
            state = json.load(f)
        # Merge with defaults (adds missing keys)
        for k, v in DEFAULT_STATE.items():
            if k not in state:
                state[k] = copy.deepcopy(v)
        return state
    except (json.JSONDecodeError, KeyError, Exception) as e:
        logger.warning(f"State file corrupt, resetting: {e}")
        return copy.deepcopy(DEFAULT_STATE)


def save_state(state: dict):
    """Persist state to disk atomically."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".json.tmp")
    try:
        with open(tmp, "w") as f:
            json.dump(state, f, indent=2, default=str)
        tmp.rename(STATE_PATH)
    except Exception as e:
        logger.error(f"Failed to save state: {e}")


# ── Narrative Operations ─────────────────────────────────────────────

def get_narrative(state: dict, narrative_id: str) -> Optional[dict]:
    return state["active_narratives"].get(narrative_id)


def list_narratives(state: dict) -> List[dict]:
    return list(state["active_narratives"].values())


def upsert_narrative(
    state: dict,
    narrative_id: str,
    confidence: int,
    trend: str = "stable",
    evidence_for: Optional[list] = None,
    evidence_against: Optional[list] = None,
    catalysts: Optional[list] = None,
    reasoning: Optional[str] = None,
):
    """Create or update a narrative with new confidence, evidence, and catalysts."""
    now = _now_iso()
    existing = state["active_narratives"].get(narrative_id)

    if existing:
        existing["confidence"] = confidence
        existing["trend"] = trend
        existing["last_updated"] = now
        existing["cycle_updated"] = state["cycle"]
        if evidence_for:
            existing["evidence"]["for"] = _merge_evidence(
                existing["evidence"]["for"], evidence_for
            )
        if evidence_against:
            existing["evidence"]["against"] = _merge_evidence(
                existing["evidence"]["against"], evidence_against
            )
        if catalysts:
            existing["catalysts"] = list(set(existing["catalysts"] + catalysts))
        if reasoning:
            existing["last_reasoning"] = reasoning
    else:
        state["active_narratives"][narrative_id] = {
            "id": narrative_id,
            "confidence": confidence,
            "trend": trend,
            "created": now,
            "last_updated": now,
            "cycle_created": state["cycle"],
            "cycle_updated": state["cycle"],
            "evidence": {
                "for": evidence_for or [],
                "against": evidence_against or [],
            },
            "catalysts": catalysts or [],
            "last_reasoning": reasoning or "Initial assessment",
        }

    # Enforce max narratives
    max_narratives = _get_config("state_management.max_active_narratives", 20)
    while len(state["active_narratives"]) > max_narratives:
        # Remove oldest by last_updated
        oldest_id = min(
            state["active_narratives"],
            key=lambda n: state["active_narratives"][n]["last_updated"],
        )
        del state["active_narratives"][oldest_id]


def _merge_evidence(existing: list, new: list) -> list:
    """Merge new evidence into existing, deduplicating by source."""
    seen = {e.get("source") for e in existing if isinstance(e, dict)}
    merged = list(existing)
    for item in new:
        if isinstance(item, dict) and item.get("source") not in seen:
            merged.append(item)
            seen.add(item.get("source"))
    return merged


# ── Source Trust Operations ─────────────────────────────────────────

def get_source_trust(state: dict, source_id: str) -> Optional[dict]:
    return state["source_trust"].get(source_id)


def update_source_trust(
    state: dict,
    source_id: str,
    track_record: Optional[float] = None,
    admiralty: Optional[str] = None,
    note: Optional[str] = None,
):
    """Update a source's trust score. If no score provided, keeps existing."""
    now = _now_iso()
    existing = state["source_trust"].get(source_id)
    if existing:
        if track_record is not None:
            # Rolling average
            n = existing.get("total_assessments", 0)
            existing["track_record"] = (
                (existing["track_record"] * n + track_record) / (n + 1)
            )
            existing["total_assessments"] = n + 1
        if admiralty:
            existing["admiralty"] = admiralty
        existing["last_updated"] = now
        if note:
            existing.setdefault("notes", []).append(note)
    else:
        state["source_trust"][source_id] = {
            "source_id": source_id,
            "admiralty": admiralty or "C3",
            "track_record": track_record or 0.5,
            "total_assessments": 1 if track_record else 0,
            "created": now,
            "last_updated": now,
            "notes": [note] if note else [],
        }

    # Enforce max
    max_entries = _get_config("state_management.max_source_trust_entries", 100)
    while len(state["source_trust"]) > max_entries:
        oldest_id = min(
            state["source_trust"],
            key=lambda s: state["source_trust"][s]["last_updated"],
        )
        del state["source_trust"][oldest_id]


# ── Weak Signal Operations ──────────────────────────────────────────

def add_weak_signal(state: dict, signal: str, strength: float, related: Optional[list] = None):
    """Add or update a weak signal."""
    now = _now_iso()
    existing = next(
        (s for s in state["weak_signals"] if s["signal"] == signal),
        None,
    )
    if existing:
        existing["strength"] = min(1.0, existing["strength"] + strength * 0.3)
        existing["last_seen"] = now
        existing["sightings"] = existing.get("sightings", 1) + 1
        if related:
            existing.setdefault("related_narratives", []).extend(related)
            existing["related_narratives"] = list(set(existing["related_narratives"]))
    else:
        state["weak_signals"].append({
            "signal": signal,
            "strength": min(1.0, strength),
            "related_narratives": related or [],
            "first_seen": now,
            "last_seen": now,
            "sightings": 1,
        })

    # Enforce max, prune lowest strength
    max_signals = _get_config("state_management.max_weak_signals", 50)
    while len(state["weak_signals"]) > max_signals:
        state["weak_signals"].sort(key=lambda s: s["strength"])
        state["weak_signals"].pop(0)


def decay_weak_signals(state: dict):
    """Apply time decay to weak signals. Old or weak signals are removed."""
    now = _now_iso()
    decay_days = _get_config("state_management.signal_decay_days", 7)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=decay_days)).isoformat()

    state["weak_signals"] = [
        s for s in state["weak_signals"]
        if s["last_seen"] >= cutoff
    ]

    # Apply strength decay for signals not seen recently
    for s in state["weak_signals"]:
        last = datetime.fromisoformat(s["last_seen"])
        hours_since = (datetime.now(timezone.utc) - last).total_seconds() / 3600
        s["strength"] = max(0.0, s["strength"] - hours_since * 0.001)


# ── Narrative Drift Operations ───────────────────────────────────────

def update_drift(state: dict, narrative_id: str, direction: str, magnitude: float):
    """Record narrative drift (how the assessment is changing over time)."""
    state.setdefault("narrative_drift", {})
    state["narrative_drift"][narrative_id] = {
        "direction": direction,  # "upward", "downward", "sideways", "divergent"
        "magnitude": round(magnitude, 3),
        "detected_at": _now_iso(),
        "cycle": state["cycle"],
    }


# ── Escalation Operations ───────────────────────────────────────────

def add_escalation(state: dict, level: str, narrative: str, reason: str):
    """Add an escalation recommendation to the queue."""
    state.setdefault("escalation_queue", [])
    state["escalation_queue"].append({
        "level": level,  # "pro" or "opus"
        "narrative": narrative,
        "reason": reason,
        "detected_at": _now_iso(),
        "cycle": state["cycle"],
        "resolved": False,
    })


def get_pending_escalations(state: dict) -> List[dict]:
    """Get unresolved escalations."""
    return [e for e in state.get("escalation_queue", []) if not e.get("resolved")]


def resolve_escalation(state: dict, idx: int):
    """Mark an escalation as resolved."""
    queue = state.get("escalation_queue", [])
    if 0 <= idx < len(queue):
        queue[idx]["resolved"] = True
        queue[idx]["resolved_at"] = _now_iso()


# ── Token Economics ─────────────────────────────────────────────────

def record_token_spend(state: dict, cost_cents: float):
    """Record token spend for a cognition cycle."""
    te = state["token_economics"]
    te["total_spent_cents"] += cost_cents
    te["cycles_completed"] += 1
    te["avg_cost_per_cycle"] = (
        te["total_spent_cents"] / max(te["cycles_completed"], 1)
    )
    
    # Daily tracking
    now = datetime.now(timezone.utc)
    if te.get("last_daily_reset"):
        last_reset = datetime.fromisoformat(te["last_daily_reset"])
        if now.date() != last_reset.date():
            te["daily_spent_cents"] = 0.0
            te["last_daily_reset"] = now.isoformat()
    else:
        te["daily_spent_cents"] = 0.0
        te["last_daily_reset"] = now.isoformat()
    
    te["daily_spent_cents"] = te.get("daily_spent_cents", 0) + cost_cents


def would_exceed_budget(state: dict, estimated_cost_cents: float) -> bool:
    """Check if this cycle would exceed the daily budget."""
    daily_max = _get_config("token_budget.max_daily_cents", 50)  # Increased for Pro: ~16 cycles/day
    current = state["token_economics"].get("daily_spent_cents", 0)
    return (current + estimated_cost_cents) > daily_max


# ── Operational State ───────────────────────────────────────────────

def mark_healthy(state: dict):
    """Mark cognition as healthy."""
    state["operational_state"]["healthy"] = True
    state["operational_state"]["cycles_since_error"] += 1
    state["operational_state"]["errors_consecutive"] = 0


def mark_error(state: dict, error: str):
    """Record a cognition error."""
    state["operational_state"]["healthy"] = False
    state["operational_state"]["last_error"] = str(error)[:200]
    state["operational_state"]["last_error_time"] = _now_iso()
    state["operational_state"]["errors_consecutive"] += 1
    state["operational_state"]["cycles_since_error"] = 0


# ── Memory Cleanup ──────────────────────────────────────────────────

def archive_stale_narratives(state: dict):
    """Archive narratives that haven't been updated in stale_days."""
    stale_days = _get_config("state_management.narrative_stale_days", 14)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=stale_days)).isoformat()
    to_archive = [
        nid for nid, n in state["active_narratives"].items()
        if n.get("last_updated", "") < cutoff
    ]
    for nid in to_archive:
        logger.info(f"Archiving stale narrative: {nid}")
        del state["active_narratives"][nid]
    return to_archive


def compact_state(state: dict):
    """Run all maintenance operations: decay, archive, prune."""
    decay_weak_signals(state)
    archived = archive_stale_narratives(state)
    # Also clean resolved escalations older than 7 days
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    state["escalation_queue"] = [
        e for e in state.get("escalation_queue", [])
        if not (e.get("resolved") and e.get("detected_at", "") < cutoff)
    ]
    return archived


# ── Snapshot ────────────────────────────────────────────────────────

def snapshot_summary(state: dict) -> dict:
    """Return a compact summary of the current cognitive state."""
    narratives = state.get("active_narratives", {})
    return {
        "cycle": state["cycle"],
        "narratives": len(narratives),
        "narratives_by_confidence": {
            "high_80+": sum(1 for n in narratives.values() if n.get("confidence", 0) >= 80),
            "medium_50-79": sum(1 for n in narratives.values() if 50 <= n.get("confidence", 0) <= 79),
            "low_under50": sum(1 for n in narratives.values() if n.get("confidence", 0) < 50),
        },
        "weak_signals": len(state.get("weak_signals", [])),
        "source_trust": len(state.get("source_trust", {})),
        "pending_escalations": len(get_pending_escalations(state)),
        "drift_count": len(state.get("narrative_drift", {})),
        "total_spent": f"${state.get('token_economics', {}).get('total_spent_cents', 0)/100:.2f}",
        "healthy": state.get("operational_state", {}).get("healthy", True),
    }


# ── Config Helper ───────────────────────────────────────────────────

_config_cache = None


def _get_config(key: str, default=None):
    """Get a config value by dot-separated key."""
    global _config_cache
    
    if _config_cache is None:
        try:
            import yaml
            with open(CONFIG_PATH) as f:
                _config_cache = yaml.safe_load(f)
        except Exception:
            return default
    
    parts = key.split(".")
    val = _config_cache
    for part in parts:
        if isinstance(val, dict):
            val = val.get(part)
        else:
            return default
    return val if val is not None else default


# ── CLI ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    state = load_state()
    
    if "--status" in sys.argv:
        s = snapshot_summary(state)
        print(json.dumps(s, indent=2))
    elif "--list-narratives" in sys.argv:
        for n in list_narratives(state):
            print(f"  {n['id']}: {n['confidence']}% ({n['trend']})")
    elif "--compact" in sys.argv:
        archived = compact_state(state)
        save_state(state)
        print(f"Archived {len(archived)} narratives")
    elif "--show" in sys.argv:
        print(json.dumps(state, indent=2, default=str)[:3000])
    else:
        print("Usage: python3 utils.py [--status|--list-narratives|--compact|--show]")
