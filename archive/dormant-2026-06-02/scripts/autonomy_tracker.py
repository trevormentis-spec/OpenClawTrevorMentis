#!/usr/bin/env python3
"""
Autonomy Tracker — Phase 9: Measuring Learning.

Tracks behavioral change, learning, and autonomy metrics over time.
Provides a unified dashboard for understanding Trevor's operational evolution.

Reads from:
  - autonomy-tracker.json — event log of all autonomous actions
  - behavioral-state.json — current behavioral constraints
  - calibration-tracking.json — forecasting accuracy by band/region
  - collection-state.json — source utilization and trust scores

Outputs:
  - Structured report to brain/memory/semantic/autonomy-report.json
  - Markdown report

Usage:
    python3 scripts/autonomy_tracker.py                    # Full report
    python3 scripts/autonomy_tracker.py --quick            # Summary only
    python3 scripts/autonomy_tracker.py --metrics-only     # JSON metrics
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
AUTONOMY_TRACKER_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "autonomy-tracker.json"
BEHAVIORAL_STATE_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "behavioral-state.json"
CALIBRATION_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "calibration-tracking.json"
COLLECTION_STATE_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "collection-state.json"
PROCEDURAL_DIR = REPO_ROOT / "brain" / "memory" / "procedural"


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[autonomy {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, Exception):
            return {}
    return {}


def compute_autonomy_metrics() -> dict:
    """Compute all autonomy and learning metrics."""
    tracker = load_json(AUTONOMY_TRACKER_FILE)
    behavioral = load_json(BEHAVIORAL_STATE_FILE)
    calibration = load_json(CALIBRATION_FILE)
    collection = load_json(COLLECTION_STATE_FILE)

    now = dt.datetime.now(dt.timezone.utc)

    # ── Behavioral change metrics ──
    regions_constrained = 0
    total_restrictions = 0
    if behavioral:
        constraints = behavioral.get("per_region_constraints", {})
        for region, c in constraints.items():
            bands = c.get("available_bands", [])
            # Default is 4 bands — any region with fewer has been restricted
            if len(bands) < 4:
                regions_constrained += 1
                total_restrictions += 4 - len(bands)

    # Source trust changes
    source_changes = len(tracker.get("source_trust_changes", []))

    # Collection changes from events
    collection_changes = 0
    if behavioral:
        events = behavioral.get("event_directives", {})
        collection_changes = len(events.get("collection_changes", []))

    # ── Learning metrics ──
    # Calibration improvement
    cal_total = calibration.get("total_judgments", 0)
    cal_correct = calibration.get("correct", 0)
    cal_accuracy = round(cal_correct / max(cal_total, 1) * 100, 1) if cal_total > 0 else 0

    # Overconfidence reduction
    overconfidence_flags = len(calibration.get("overconfidence_flags", []))

    # Procedural memories
    procedural_count = len(tracker.get("procedural_learnings", []))
    # Count on-disk procedural files too
    on_disk_procedural = len(list(PROCEDURAL_DIR.glob("*.md"))) if PROCEDURAL_DIR.exists() else 0

    # ── Autonomy metrics ──
    unscheduled_events = len(tracker.get("unscheduled_cognition_events", []))
    autonomous_prioritizations = len(tracker.get("autonomous_prioritizations", []))

    # Behavioral state version tracking
    behavioral_version = behavioral.get("version", "none") if behavioral else "none"

    # Event-driven adaptations active
    active_escalations = 0
    if behavioral:
        active_escalations = len(behavioral.get("event_directives", {}).get("active_escalations", []))

    return {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "behavioral_change": {
            "regions_with_restricted_bands": regions_constrained,
            "total_band_restrictions": total_restrictions,
            "source_trust_changes": source_changes,
            "collection_changes_from_events": collection_changes,
        },
        "learning": {
            "calibration_accuracy_pct": cal_accuracy,
            "total_judgments": cal_total,
            "overconfidence_flags": overconfidence_flags,
            "procedural_memories_created": procedural_count,
            "procedural_memories_on_disk": on_disk_procedural,
        },
        "autonomy": {
            "unscheduled_cognition_events": unscheduled_events,
            "autonomous_prioritizations": autonomous_prioritizations,
            "active_escalations": active_escalations,
            "behavioral_state_version": behavioral_version,
        },
        "overall_score": compute_overall_score(
            regions_constrained, source_changes, collection_changes,
            cal_accuracy, unscheduled_events, procedural_count,
        ),
    }


def compute_overall_score(
    constrained: int, source_changes: int, coll_changes: int,
    accuracy: float, unscheduled: int, procedural: int,
) -> int:
    """Compute a single autonomy score (0-100)."""
    # Bandwidth: how many regions are behaviorally constrained (out of 6)
    bandwidth_score = min(int(constrained / 6 * 30), 30)

    # Learning: how much the system has evolved its trust and procedures
    learning_score = min((source_changes + procedural) * 10, 30)

    # Autonomy: unscheduled actions
    autonomy_score = min(unscheduled * 20, 20)

    # Calibration honesty: having accuracy < 50% with good tracking is better than
    # not tracking at all
    calibration_score = 10 if accuracy > 0 else 0  # tracking exists

    # Collection adaptation
    collection_score = min(coll_changes * 5, 10)

    return min(bandwidth_score + learning_score + autonomy_score + calibration_score + collection_score, 100)


def render_report(metrics: dict) -> str:
    """Render the autonomy metrics as a markdown report."""
    lines = []
    lines.append("# Autonomy & Learning Report")
    lines.append(f"**Generated:** {metrics['generated_at']}")
    lines.append("")
    lines.append(f"**Overall Autonomy Score:** {metrics['overall_score']}/100")
    lines.append("")

    lines.append("## Behavioral Change Metrics")
    lines.append("")
    lines.append(f"- Regions with restricted confidence bands: {metrics['behavioral_change']['regions_with_restricted_bands']}")
    lines.append(f"- Total band restrictions applied: {metrics['behavioral_change']['total_band_restrictions']}")
    lines.append(f"- Source trust changes recorded: {metrics['behavioral_change']['source_trust_changes']}")
    lines.append(f"- Collection changes from events: {metrics['behavioral_change']['collection_changes_from_events']}")
    lines.append("")

    lines.append("## Learning Metrics")
    lines.append("")
    lines.append(f"- Calibration accuracy: {metrics['learning']['calibration_accuracy_pct']}% ({metrics['learning']['total_judgments']} judgments)")
    lines.append(f"- Overconfidence flags: {metrics['learning']['overconfidence_flags']}")
    lines.append(f"- Procedural memories created: {metrics['learning']['procedural_memories_created']}")
    lines.append(f"- Procedural memories on disk: {metrics['learning']['procedural_memories_on_disk']}")
    lines.append("")

    lines.append("## Autonomy Metrics")
    lines.append("")
    lines.append(f"- Unscheduled cognition events fired: {metrics['autonomy']['unscheduled_cognition_events']}")
    lines.append(f"- Autonomous prioritizations made: {metrics['autonomy']['autonomous_prioritizations']}")
    lines.append(f"- Active escalations: {metrics['autonomy']['active_escalations']}")
    lines.append(f"- Behavioral state version: {metrics['autonomy']['behavioral_state_version']}")
    lines.append("")

    # Score breakdown
    lines.append("## Score Breakdown")
    lines.append("")
    lines.append("| Component | Points | Max |")
    lines.append("|-----------|--------|-----|")
    bw = min(metrics['behavioral_change']['regions_with_restricted_bands'] / 6 * 30, 30)
    lr = min((metrics['learning']['procedural_memories_on_disk'] + metrics['behavioral_change']['source_trust_changes']) * 10, 30)
    au = min(metrics['autonomy']['unscheduled_cognition_events'] * 20, 20)
    ca = 10 if metrics['learning']['calibration_accuracy_pct'] > 0 else 0
    cc = min(metrics['behavioral_change']['collection_changes_from_events'] * 5, 10)
    lines.append(f"| Behavioral constraints | {round(bw)} | 30 |")
    lines.append(f"| Learning & evolution | {round(lr)} | 30 |")
    lines.append(f"| Autonomous action | {round(au)} | 20 |")
    lines.append(f"| Calibration tracking | {round(ca)} | 10 |")
    lines.append(f"| Collection adaptation | {round(cc)} | 10 |")
    lines.append(f"| **Total** | **{metrics['overall_score']}** | **100** |")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="Summary only")
    parser.add_argument("--metrics-only", action="store_true", help="JSON metrics only")
    args = parser.parse_args()

    metrics = compute_autonomy_metrics()

    if args.metrics_only:
        print(json.dumps(metrics, indent=2))
        return 0

    if args.quick:
        print(f"Autonomy Score: {metrics['overall_score']}/100")
        print(f"  Behavioral constraints: {metrics['behavioral_change']['regions_with_restricted_bands']} regions")
        print(f"  Unscheduled cognition: {metrics['autonomy']['unscheduled_cognition_events']} events")
        print(f"  Procedural memories: {metrics['learning']['procedural_memories_on_disk']} on disk")
        print(f"  Calibration accuracy: {metrics['learning']['calibration_accuracy_pct']}%")
        return 0

    report = render_report(metrics)
    print(report)

    # Save to file
    report_dir = REPO_ROOT / "exports" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"autonomy-report-{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')}.md"
    report_path.write_text(report)

    metrics_path = REPO_ROOT / "brain" / "memory" / "semantic" / "autonomy-report.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics, indent=2))

    log(f"Report saved: {report_path}")
    log(f"Metrics saved: {metrics_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
