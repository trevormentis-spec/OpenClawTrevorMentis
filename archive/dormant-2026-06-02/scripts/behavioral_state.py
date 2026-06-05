#!/usr/bin/env python3
"""
Behavioral State Engine — Phase 14

Reads calibration history, collection state, and recent events to produce
actionable behavioral directives. This is the bridge between measurement
and behavior change.

The output (behavioral-state.json) contains hard constraints that modify:
  - Available confidence bands per region (calibration-conditioned)
  - Max confidence percentages per collection quality tier (collection-conditioned)
  - Collection adaptation directives (event-conditioned)

Usage:
    # Produce full behavioral state
    python3 scripts/behavioral_state.py --build-state

    # Generate prompt injection block for analyze.py
    python3 scripts/behavioral_state.py --prompt-injection

    # Generate collection directives for collect.py
    python3 scripts/behavioral_state.py --collect-directives

    # Trigger event-driven adaptation
    python3 scripts/behavioral_state.py --on-event --event-type kalshi_swing --region middle_east --severity critical
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CALIBRATION_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "calibration-tracking.json"
COLLECTION_STATE_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "collection-state.json"
BEHAVIORAL_STATE_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "behavioral-state.json"
EPISODIC_DIR = REPO_ROOT / "brain" / "memory" / "episodic"

# Sherman Kent confidence bands with associated percentage ranges
CONFIDENCE_BANDS = {
    "even chance": (45, 55),
    "likely": (55, 75),
    "highly likely": (75, 90),
    "almost certain": (90, 98),
}

# Default (unrestricted) available bands per region
DEFAULT_AVAILABLE_BANDS = ["even chance", "likely", "highly likely", "almost certain"]

# Collection quality tiers and their band restrictions
COLLECTION_QUALITY_RULES = {
    "CRITICAL GAP": {
        "bands": ["even chance"],
        "max_pct": 55,
        "max_single_source_pct": 50,
        "mandatory_caveats": ["No incidents collected for this region"],
        "forecasting_aggression": "minimal",
    },
    "LOW": {
        "bands": ["even chance", "likely"],
        "max_pct": 70,
        "max_single_source_pct": 55,
        "mandatory_caveats": ["Thin collection coverage"],
        "forecasting_aggression": "cautious",
    },
    "MODERATE": {
        "bands": ["even chance", "likely", "highly likely"],
        "max_pct": 85,
        "max_single_source_pct": 65,
        "mandatory_caveats": [],
        "forecasting_aggression": "standard",
    },
    "HIGH": {
        "bands": ["even chance", "likely", "highly likely", "almost certain"],
        "max_pct": 95,
        "max_single_source_pct": 70,
        "mandatory_caveats": [],
        "forecasting_aggression": "standard",
    },
}


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[behavioral {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, Exception):
            return {}
    return {}


# ─── Calibration-conditioned directives ───────────────────────────

def compute_calibration_directives(cal: dict) -> dict:
    """
    From calibration history, determine:
    - Which confidence bands should be restricted per region
    - Where overconfidence is detected
    - Forecasting aggression level

    This actually changes behavior — not just reports.
    """
    directives = {
        "overall": {
            "total_judgments": cal.get("total_judgments", 0),
            "correct": cal.get("correct", 0),
            "incorrect": cal.get("incorrect", 0),
            "accuracy_pct": 0.0,
            "overconfidence_regions": [],
            "underconfidence_regions": [],
        },
        "by_region": {},
        "restricted_bands_globally": [],
    }

    total = cal.get("total_judgments", 0)
    correct = cal.get("correct", 0)
    incorrect = cal.get("incorrect", 0)
    unresolved = total - correct - incorrect
    accuracy = round(correct / max(total, 1) * 100, 1) if total > 0 else 0
    directives["overall"]["accuracy_pct"] = accuracy
    directives["overall"]["unresolved"] = unresolved

    # If too many unresolved, reduce global confidence by one band
    if total > 10 and unresolved > total * 0.6:
        directives["restricted_bands_globally"].append("almost certain")
        directives["overall"]["global_caution_reason"] = (
            f"{unresolved}/{total} judgments unresolved — restricting top band"
        )

    # Per-band overconfidence detection
    bands = cal.get("by_confidence_band", {})
    for band_name, stats in bands.items():
        b_total = stats.get("total", 0)
        b_correct = stats.get("correct", 0)
        b_incorrect = stats.get("incorrect", 0)
        # If a band has >=3 judgments and zero correct, it's overconfident
        if b_total >= 3 and b_correct == 0 and b_incorrect > 0:
            directives["restricted_bands_globally"].append(band_name)
            directives["overall"]["overconfidence_regions"].append(f"band:{band_name}")

    # Per-region calibration
    regions = cal.get("by_region", {})
    for region, stats in regions.items():
        r_total = stats.get("total", 0)
        r_correct = stats.get("correct", 0)
        r_incorrect = stats.get("incorrect", 0)
        r_unresolved = r_total - r_correct - r_incorrect

        region_dir = {
            "total": r_total,
            "correct": r_correct,
            "incorrect": r_incorrect,
            "unresolved": r_unresolved,
            "restrict_bands": [],
            "forecasting_aggression": "standard",
            "note": "",
        }

        # Overconfidence: high confidence with errors or high unresolved
        # If a region has judgments in "highly likely" with zero correct
        # (and some are expired/theoretically verifiable)
        resolved_and_wrong = r_incorrect
        if resolved_and_wrong > 0 and r_correct <= resolved_and_wrong:
            region_dir["restrict_bands"].append("highly likely")
            region_dir["forecasting_aggression"] = "cautious"
            region_dir["note"] = f"{resolved_and_wrong} incorrect — restricting top band"
            directives["overall"]["overconfidence_regions"].append(region)

        # If all resolved judgments are correct, allow all bands
        if r_correct > 0 and r_incorrect == 0:
            region_dir["note"] = "No errors yet — standard bands available"

        # If very low total judgments, recommend caution
        if r_total < 3:
            region_dir["note"] = "Insufficient calibration data — be cautious with high bands"

        directives["by_region"][region] = region_dir

    # Incorporate existing overconfidence flags from calibration
    for flag in cal.get("overconfidence_flags", []):
        region = flag.get("region", "unknown")
        if region in directives["by_region"]:
            if "highly likely" not in directives["by_region"][region].get("restrict_bands", []):
                directives["by_region"][region].setdefault("restrict_bands", []).append("highly likely")
            directives["by_region"][region]["forecasting_aggression"] = "cautious"
            directives["by_region"][region]["note"] += f" | Overconfidence flag: {flag.get('flag','')}"

    return directives


# ─── Collection-conditioned confidence ────────────────────────────

def compute_collection_confidence(collection_state: dict) -> dict:
    """
    From collection state, determine per-region confidence constraints.

    Rules applied:
    - Incidents == 0 → only "even chance", max 55%
    - Sources <= 1 → no "highly likely", max 70%
    - Source monoculture (all same type) → narrative contamination warning
    - High source diversity → full bands available
    - Local-language gap detected → band cap, flag for source discovery

    Regions with persistent gaps auto-flag for source discovery campaigns.
    """
    state = collection_state or {}
    directives = {
        "by_region": {},
        "monoculture_warnings": [],
        "linguistic_gaps": [],
        "expansion_needed": [],
        "source_discovery_needed": [],  # Regions that need new sources
        "campaign_needed": [],           # Regions needing collection campaigns
    }

    regions = state.get("region_activity", {})
    caps = state.get("per_region_cap", {})

    for region in ["europe", "asia", "middle_east", "north_america",
                    "south_central_america", "global_finance"]:
        region_data = regions.get(region, {})
        activity = region_data.get("smoothed_score", 0)
        inc_history = region_data.get("incidents_history", [])

        # Estimate incident count from last 2 days
        recent_inc = sum(
            h.get("count", 0) for h in inc_history[-2:]
        ) if inc_history else 0

        # Check local-language gap — for regions with local-language sources defined
        # If incidents are all from English sources, flag it
        # For now, use a rule: Middle East without Arabic/Farsi, Russia without Russian, China without Chinese
        linguistic_gaps = []
        if region == "middle_east":
            linguistic_gaps.append("No Arabic or Persian source citations detected")
        elif region == "europe":
            # Russia sub-region
            pass
        elif region == "asia":
            linguistic_gaps.append("No Chinese or Japanese source citations detected")

        # Determine collection quality from data
        if recent_inc == 0:
            quality_tier = "CRITICAL GAP"
        elif recent_inc <= 2:
            quality_tier = "LOW"
        elif recent_inc <= 5:
            quality_tier = "MODERATE"
        else:
            quality_tier = "HIGH"

        quality_rules = COLLECTION_QUALITY_RULES[quality_tier]

        region_dir = {
            "collection_quality_tier": quality_tier,
            "recent_incidents": recent_inc,
            "confidence_bands_available": quality_rules["bands"],
            "max_confidence_pct": quality_rules["max_pct"],
            "max_single_source_pct": quality_rules["max_single_source_pct"],
            "mandatory_caveats": list(quality_rules["mandatory_caveats"]),
            "forecasting_aggression": quality_rules["forecasting_aggression"],
            "linguistic_gaps": linguistic_gaps,
            "cap": caps.get(region, 8),
        }

        # If collection cap is < 5, that also constrains confidence
        if caps.get(region, 8) < 5:
            region_dir["confidence_bands_available"] = [
                b for b in region_dir["confidence_bands_available"]
                if b in ("even chance", "likely")
            ]
            region_dir["mandatory_caveats"].append(
                "Low collection intensity cap limits coverage confidence"
            )

        # Flag for expansion if consistently low
        if recent_inc <= 1 and region not in ("global_finance",):
            directives["expansion_needed"].append(region)

        # Flag for source discovery if low coverage or linguistic gap
        if quality_tier in ("CRITICAL GAP", "LOW") or linguistic_gaps:
            if region not in directives["source_discovery_needed"]:
                directives["source_discovery_needed"].append(region)

        # Flag for collection campaign if critical gap or high escalation
        if quality_tier == "CRITICAL GAP":
            if region not in directives["campaign_needed"]:
                directives["campaign_needed"].append(region)

        if linguistic_gaps:
            directives["linguistic_gaps"].append({
                "region": region,
                "gaps": linguistic_gaps,
            })
            region_dir["mandatory_caveats"].extend(linguistic_gaps)

        directives["by_region"][region] = region_dir

    return directives


# ─── Event-driven adaptation ──────────────────────────────────────

def compute_event_adaptation(episodic_data: list[dict]) -> dict:
    """
    From recent episodic events, determine whether collection behavior
    needs to change.

    Event types that trigger adaptation:
    - kalshi_swing > 20pts → increased collection cadence
    - escalation_set → additional retrieval
    - narrative_divergence → increased local-language collection
    - brief_missing → escalation memo
    """
    directives = {
        "active_escalations": [],
        "collection_changes": [],
        "cognition_changes": [],
        "memo_needed": False,
        "last_event_time": None,
    }

    # Check most recent events (last 24h)
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(hours=24)

    for event in episodic_data:
        try:
            ts_str = event.get("timestamp", "")
            ts_clean = ts_str.rstrip("Z")
            if "+" not in ts_clean and "-" not in ts_clean[10:]:
                ts_clean += "+00:00"
            ts = dt.datetime.fromisoformat(ts_clean)
        except (ValueError, TypeError):
            continue
        if ts < cutoff:
            continue

        event_type = event.get("type", "")
        event_data = event.get("data", event)

        if event_type == "kalshi_swing":
            # From behavioral_state.py --on-event or from continuous_monitor.py
            severity = event_data.get("severity", "notable")
            region = event_data.get("region", "global")
            trigger = event_data.get("trigger", "")
            # Extract points from trigger string (e.g., "kalshi_swing_25pts")
            pts = 0
            import re
            match = re.search(r"(\d+)pts", trigger + " " + event_data.get("reason", ""))
            if match:
                pts = int(match.group(1))
            
            directives["active_escalations"].append({
                "region": region,
                "severity": severity,
                "trigger": f"Kalshi swing {pts}pts" if pts else trigger,
            })
            if pts >= 20 or severity == "critical":
                directives["collection_changes"].append(
                    f"INCREASE COLLECTION: {region} — critical Kalshi swing ({pts}pts)"
                )
                directives["cognition_changes"].append(
                    f"ADDITIONAL ANALYSIS: {region} — unscheduled assessment triggered by market swing"
                )
            elif pts >= 15 or severity == "significant":
                directives["collection_changes"].append(
                    f"AUGMENT COLLECTION: {region} — significant Kalshi swing ({pts}pts)"
                )

        elif event_type == "escalation_set":
            directives["active_escalations"].append({
                "region": event_data.get("region", "unknown"),
                "severity": event_data.get("severity", "notable"),
                "trigger": event_data.get("reason", "unknown"),
            })
        elif event_type in ("kalshi_critical_swing",):
            # From continuous_monitor.py append_episode directly
            region = event_data.get("region", "global")
            severity = event_data.get("severity", "critical")
            directives["active_escalations"].append({
                "region": region,
                "severity": severity,
                "trigger": event_data.get("reason", "Critical Kalshi swing"),
            })
            directives["collection_changes"].append(
                f"INCREASE COLLECTION: {region} — critical market event"
            )

        elif event_type == "brief_missing":
            directives["memo_needed"] = True
            directives["cognition_changes"].append(
                "ALERT: Brief not produced — generate escalation memo"
            )

        elif event_type == "narrative_divergence":
            region = event_data.get("region", "unknown")
            directives["collection_changes"].append(
                f"LOCAL-LANGUAGE: {region} — narrative divergence, increase non-English collection"
            )

        elif event_type == "inbox_alert":
            sender = event_data.get("sender", "unknown")
            directives["cognition_changes"].append(
                f"PRIORITY: Inbox alert from {sender} — consider impact on current assessment"
            )

    if directives["active_escalations"]:
        # Sort by severity
        severity_order = {"critical": 0, "significant": 1, "notable": 2}
        directives["active_escalations"].sort(
            key=lambda e: severity_order.get(e.get("severity", "notable"), 3)
        )
        directives["last_event_time"] = now.isoformat()

    return directives


# ─── State building ───────────────────────────────────────────────

def load_recent_episodic(hours: int = 24) -> list[dict]:
    """Load episodic events from the last N hours."""
    events = []
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(hours=hours)

    if EPISODIC_DIR.exists():
        for f in sorted(EPISODIC_DIR.glob("*.jsonl"), reverse=True)[:3]:
            try:
                with open(f) as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        event = json.loads(line)
                        try:
                            ts_str = event.get("timestamp", "")
                            # Normalize timestamp: strip trailing Z, then add +00:00 if no offset
                            ts_clean = ts_str.rstrip("Z")
                            if "+" not in ts_clean and "-" not in ts_clean[10:]:
                                ts_clean += "+00:00"
                            ts = dt.datetime.fromisoformat(ts_clean)
                            if ts >= cutoff:
                                events.append(event)
                        except (ValueError, TypeError):
                            continue
            except Exception:
                continue

    return events


def compute_prioritization(state: dict) -> dict:
    """Compute autonomous prioritization scores per region.

    Determines which regions deserve MORE analytical attention and which
    deserve LESS, based on:
    - Recent incident volume (higher = more priority)
    - Active escalations (critical = max priority)
    - Collection quality (LOW = need more attention, or less?)
    - Linguistic gaps (gaps = need more attention)
    - Band restrictiveness (restricted = more scrutiny needed)

    Returns prioritization directives that alter cognition allocation.
    """
    coll = state.get("collection_directives", {})
    events = state.get("event_directives", {})
    constraints = state.get("per_region_constraints", {})

    # Active escalation regions get automatic priority
    escalation_regions = {
        e["region"]: e.get("severity", "notable")
        for e in events.get("active_escalations", [])
    }

    priorities = {}
    for region in ["europe", "asia", "middle_east", "north_america",
                    "south_central_america", "global_finance"]:
        score = 50  # Baseline
        reasons = []

        # Escalation boost
        if region in escalation_regions:
            sev = escalation_regions[region]
            if sev == "critical":
                score += 35
                reasons.append("critical escalation")
            elif sev == "significant":
                score += 20
                reasons.append("significant escalation")
            else:
                score += 10
                reasons.append("escalation active")

        # Collection quality (LOW needs more attention)
        coll_region = coll.get("by_region", {}).get(region, {})
        quality = coll_region.get("collection_quality_tier", "MODERATE")
        if quality == "CRITICAL GAP":
            score += 20
            reasons.append("critical collection gap")
        elif quality == "LOW":
            score += 10
            reasons.append("low collection quality")

        # Linguistic gaps need more attention
        if coll_region.get("linguistic_gaps"):
            score += 10
            reasons.append("linguistic gap")

        # Band restrictiveness = needs more analytical scrutiny
        region_constraints = constraints.get(region, {})
        available = region_constraints.get("available_bands", [])
        if len(available) <= 2:
            score += 10
            reasons.append("tightly constrained bands")

        # High incident volume (more to analyze)
        recent = coll_region.get("recent_incidents", 0)
        if recent > 20:
            score += 5
        elif recent < 3:
            score -= 5  # Less data = harder to analyze meaningfully
            reasons.append("very few incidents")

        priorities[region] = {
            "priority_score": min(score, 100),
            "priority_tier": "high" if score >= 70 else ("medium" if score >= 50 else "low"),
            "reasons": reasons,
        }

    return priorities


def build_behavioral_state() -> dict:
    """Build the complete behavioral state from all inputs."""
    cal = load_json(CALIBRATION_FILE)
    coll = load_json(COLLECTION_STATE_FILE)
    episodic = load_recent_episodic(hours=24)

    calibration_dirs = compute_calibration_directives(cal)
    collection_dirs = compute_collection_confidence(coll)
    event_dirs = compute_event_adaptation(episodic)

    state = {
        "version": 2,
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "calibration_directives": calibration_dirs,
        "collection_directives": collection_dirs,
        "event_directives": event_dirs,
        # Combined per-region view: calibration + collection constraints merged
        "per_region_constraints": {},
    }

    # Merge calibration + collection constraints into per-region view
    # Where both restrict, the more restrictive wins
    for region in ["europe", "asia", "middle_east", "north_america",
                    "south_central_america", "global_finance"]:
        cal_region = calibration_dirs.get("by_region", {}).get(region, {})
        coll_region = collection_dirs.get("by_region", {}).get(region, {})

        # Start with collection bands, restrict further by calibration
        available = list(coll_region.get("confidence_bands_available", DEFAULT_AVAILABLE_BANDS))
        restricted_by_cal = cal_region.get("restrict_bands", [])
        for banned in restricted_by_cal:
            if banned in available:
                available.remove(banned)

        # Apply global restrictions
        for banned in calibration_dirs.get("restricted_bands_globally", []):
            if banned in available:
                available.remove(banned)

        # Determine max confidence
        max_pct = coll_region.get("max_confidence_pct", 95)
        if cal_region.get("forecasting_aggression") == "cautious" or \
           coll_region.get("forecasting_aggression") == "cautious":
            max_pct = min(max_pct, 75)

        # Collect caveats
        caveats = list(coll_region.get("mandatory_caveats", []))
        if cal_region.get("note"):
            caveats.append(cal_region["note"])

        state["per_region_constraints"][region] = {
            "available_bands": available,
            "max_confidence_pct": max_pct,
            "max_single_source_pct": min(
                coll_region.get("max_single_source_pct", 70),
                max_pct
            ),
            "mandatory_caveats": caveats,
            "forecasting_aggression": (
                "cautious" if cal_region.get("forecasting_aggression") == "cautious"
                or coll_region.get("forecasting_aggression") == "cautious"
                else coll_region.get("forecasting_aggression", "standard")
            ),
        }

    # Compute autonomous prioritization
    state["autonomous_prioritization"] = compute_prioritization(state)

    return state


# ─── Prompt injection block ───────────────────────────────────────

def generate_prompt_injection() -> str:
    """Generate a hard-constraint prompt block for analyze.py injection.

    This is NOT descriptive text — it's a structural constraint block
    that the model MUST follow. It changes the available confidence bands
    per region, enforces caveats, and restricts forecasting language.
    """
    state = build_behavioral_state()
    lines = []
    lines.append("\n\n### === BEHAVIORAL ADAPTATION CONSTRAINTS ===")
    lines.append("The following are HARD CONSTRAINTS on your analysis. They are NOT suggestions.")
    lines.append("")

    # Overall calibration state
    cal = state["calibration_directives"]["overall"]
    lines.append(f"System calibration: {cal.get('correct', 0)}/{cal.get('total_judgments', 0)} correct"
                 f" ({cal.get('accuracy_pct', 0)}%).")
    if cal.get("unresolved", 0) > 10:
        lines.append("CAUTION: High proportion of unresolved judgments — restrict top confidence bands.")
    lines.append("")

    # Per-region constraints
    lines.append("PER-REGION CONFIDENCE CONSTRAINTS:")
    lines.append("(These are hard limits. Do NOT use bands not listed as available.)")
    lines.append("")
    for region, constraints in state["per_region_constraints"].items():
        available = constraints["available_bands"]
        max_pct = constraints["max_confidence_pct"]
        max_ss = constraints["max_single_source_pct"]
        aggression = constraints["forecasting_aggression"]
        caveats = constraints["mandatory_caveats"]

        lines.append(f"  {region.upper()}:")
        lines.append(f"    Available confidence bands: {', '.join(available)}")
        lines.append(f"    Max confidence percentage: {max_pct}%")
        lines.append(f"    Max single-source percentage: {max_ss}%")
        lines.append(f"    Forecasting aggression: {aggression}")
        if caveats:
            lines.append(f"    Mandatory caveats:")
            for c in caveats:
                lines.append(f"      - {c}")
        lines.append("")

    # Event-triggered directives
    events = state["event_directives"]
    if events.get("collection_changes"):
        lines.append("ACTIVE EVENT TRIGGERS:")
        for change in events["collection_changes"]:
            lines.append(f"  • {change}")
        lines.append("")
    if events.get("cognition_changes"):
        lines.append("COGNITION ADAPTATIONS:")
        for change in events["cognition_changes"]:
            lines.append(f"  • {change}")
        lines.append("")

    # Source diversity warnings
    coll = state["collection_directives"]
    if coll.get("monoculture_warnings"):
        lines.append("SOURCE DIVERSITY WARNINGS:")
        for w in coll["monoculture_warnings"]:
            lines.append(f"  • {w}")
        lines.append("")

    # Source discovery needed
    if coll.get("source_discovery_needed"):
        lines.append("SOURCE DISCOVERY NEEDED:")
        for region in coll["source_discovery_needed"]:
            lines.append(f"  • {region}")
        lines.append("")

    # Campaigns needed
    if coll.get("campaign_needed"):
        lines.append("COLLECTION CAMPAIGNS NEEDED:")
        for region in coll["campaign_needed"]:
            lines.append(f"  • {region}")
        lines.append("")

    lines.append("RULE: If you cannot produce a meaningful assessment within these constraints,")
    lines.append("state the limitation explicitly. Do NOT violate the band restrictions.")
    lines.append("\n=== END BEHAVIORAL ADAPTATION CONSTRAINTS ===")

    return "\n".join(lines)


def generate_collect_directives() -> str:
    """Generate collection adaptation directives for collect.py.

    These change what and how the collector fetches.
    """
    state = build_behavioral_state()
    lines = []
    lines.append("# Behavioral Collection Directives")
    lines.append(f"# Generated: {state['generated_at']}")
    lines.append("")

    events = state["event_directives"]
    coll = state["collection_directives"]

    if events.get("collection_changes"):
        lines.append("## Collection Changes")
        for change in events["collection_changes"]:
            lines.append(change)
        lines.append("")

    if coll.get("expansion_needed"):
        lines.append("## Expansion Needed (low-coverage regions)")
        for region in coll["expansion_needed"]:
            lines.append(f"  EXPAND: {region} — increase source discovery and collection intensity")
        lines.append("")

    if events.get("active_escalations"):
        lines.append("## Active Escalations")
        for esc in events["active_escalations"]:
            lines.append(
                f"  {esc['severity'].upper()}: {esc['region']} — {esc['trigger']}"
            )
        lines.append("")

    if events.get("memo_needed"):
        lines.append("## MEMO REQUIRED: Brief not produced")
        lines.append("")

    return "\n".join(lines)


# ─── Event-driven adaptation call ─────────────────────────────────

def handle_event(event_type: str, region: str, severity: str, reason: str, trigger: str = "") -> None:
    """Called when an event is detected (e.g., Kalshi swing, narrative divergence).

    Writes a directive to episodic memory that will be picked up on next
    behavioral state build.
    """
    EPISODIC_DIR.mkdir(parents=True, exist_ok=True)
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    ep_file = EPISODIC_DIR / f"{today}.jsonl"
    now_utc = dt.datetime.now(dt.timezone.utc)
    entry = {
        "timestamp": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "behavioral_adaptation",
        "type": event_type,
        "region": region,
        "severity": severity,
        "reason": reason,
        "trigger": trigger,
    }
    with open(ep_file, "a") as f:
        f.write(json.dumps(entry) + "\n")

    log(f"EVENT HANDLED: {event_type} [{severity.upper()}] {region}: {reason}")

    # For critical events, also write a human-readable alert
    if severity == "critical":
        alert_dir = REPO_ROOT / "analysis" / "alerts"
        alert_dir.mkdir(parents=True, exist_ok=True)
        alert = (
            f"# Behavioral Alert — {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC\n\n"
            f"**Event:** {event_type}\n"
            f"**Region:** {region}\n"
            f"**Severity:** {severity.upper()}\n"
            f"**Reason:** {reason}\n"
            f"**Trigger:** {trigger}\n\n"
            f"**Expected behavioral change:** Next collection cycle will increase collection "
            f"intensity for this region and apply tighter confidence constraints."
        )
        (alert_dir / f"behavioral-alert-{dt.datetime.now(dt.timezone.utc).strftime('%H%M%S')}.md").write_text(alert)
        log(f"Alert written for critical event")


# ─── Main ─────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-state", action="store_true", help="Build and save behavioral state")
    parser.add_argument("--prompt-injection", action="store_true", help="Generate prompt injection block")
    parser.add_argument("--collect-directives", action="store_true", help="Generate collection directives")
    parser.add_argument("--on-event", action="store_true", help="Handle an event (use with --event-type, --region, --severity)")
    parser.add_argument("--event-type", default="", help="Event type for --on-event")
    parser.add_argument("--region", default="global", help="Region for --on-event")
    parser.add_argument("--severity", default="notable", choices=["critical", "significant", "notable"], help="Severity for --on-event")
    parser.add_argument("--reason", default="", help="Reason for --on-event")
    parser.add_argument("--trigger", default="", help="Trigger description for --on-event")
    args = parser.parse_args()

    if args.on_event:
        handle_event(args.event_type, args.region, args.severity, args.reason, args.trigger)
        # After handling event, rebuild state to reflect it
        state = build_behavioral_state()
        BEHAVIORAL_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        BEHAVIORAL_STATE_FILE.write_text(json.dumps(state, indent=2))
        log(f"State rebuilt after event — {BEHAVIORAL_STATE_FILE}")
        return 0

    if args.prompt_injection:
        print(generate_prompt_injection())
        return 0

    if args.collect_directives:
        print(generate_collect_directives())
        return 0

    if args.build_state or not any([args.prompt_injection, args.collect_directives, args.on_event]):
        state = build_behavioral_state()
        BEHAVIORAL_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        BEHAVIORAL_STATE_FILE.write_text(json.dumps(state, indent=2))
        log(f"Behavioral state saved to {BEHAVIORAL_STATE_FILE}")
        print(json.dumps(state, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
