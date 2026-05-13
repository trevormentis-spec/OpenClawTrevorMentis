#!/usr/bin/env python3
"""
Self-assessment daemon — Trevor's meta-cognition loop.

Composes all existing monitoring systems into a unified self-assessment.
Runs daily after the brief. Checks seven dimensions:

  Collection — are we collecting enough diverse intelligence?
  Calibration — are our confidence bands accurate?
  Routing — are we using the right models for the right tasks?
  Config — is the system configuration valid?
  Observation — are we monitoring our own behavior?
  Autonomy — are adaptive loops actually closed?
  Epistemic — are we tracking our own uncertainty accurately?

Output:
  1. Structured assessment to exporters/system-health/YYYY-MM-DD.json
  2. Markdown report to exports/reports/system-health-YYYY-MM-DD.md
  3. If regression detected: injects adjustment file for next brief prompt
  4. If critical regression: writes to state for next pipeline run

Usage:
    python3 scripts/self_assessment.py
    python3 scripts/self_assessment.py --quick  (skip expensive checks)

Called from:
    daily-brief-cron.sh (after Step 9, as post-pipeline audit)
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
HEALTH_DIR = REPO_ROOT / "exports" / "system-health"
REPORT_DIR = REPO_ROOT / "exports" / "reports"
STATE_DIR = REPO_ROOT / "brain" / "memory" / "semantic"
ADJUSTMENT_FILE = REPO_ROOT / "tasks" / "self-assessment-injection.md"

DIMENSION_WEIGHTS = {
    "collection": 0.20,
    "calibration": 0.20,
    "routing": 0.15,
    "config": 0.10,
    "observation": 0.10,
    "autonomy": 0.15,
    "epistemic": 0.10,
}


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[self-assess {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, Exception):
            return {}
    return {}


def yesterday_key() -> str:
    return (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)).strftime("%Y-%m-%d")


def today_key() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


# ── Dimension checkers ──────────────────────────────────────────────

def assess_collection() -> dict:
    """Score collection health: source utilization, region coverage, gaps."""
    state = load_json(STATE_DIR / "collection-state.json")
    if not state:
        return {"score": 0, "problems": ["No collection state data"]}

    utilization = state.get("source_utilization", {})
    cited = sum(1 for u in utilization.values() if u.get("cited_count", 0) > 0)
    total = max(len(utilization), 1)
    citation_rate = cited / total

    gaps = len(state.get("identified_gaps", []))
    region_activity = state.get("region_activity", {})
    dead_regions = sum(1 for r, d in region_activity.items()
                       if d.get("smoothed_score", 0) == 0)

    score = round(
        (citation_rate * 40) +            # 0-40 points for source utilization
        (max(0, 30 - gaps * 5)) +          # 0-30 points (deduct 5 per gap)
        (max(0, 30 - dead_regions * 10)) + # 0-30 points (deduct 10 per dead region)
        0
    )
    score = max(0, min(100, score))

    problems = []
    if citation_rate < 0.3:
        problems.append("Low source citation rate")
    if gaps > 3:
        problems.append(f"{gaps} collection gaps")
    if dead_regions > 0:
        problems.append(f"{dead_regions} region(s) with zero activity")

    return {"score": score, "citation_rate": round(citation_rate, 2),
            "gaps": gaps, "dead_regions": dead_regions, "problems": problems}


def assess_calibration() -> dict:
    """Score calibration health: prediction accuracy, overconfidence, band distribution."""
    cal = load_json(STATE_DIR / "calibration-tracking.json")
    if not cal:
        return {"score": 0, "problems": ["No calibration data — pipeline may not have run"]}

    total = cal.get("total_judgments", 0)
    if total == 0:
        return {"score": 10, "problems": ["Calibration file exists but no judgments logged"]}

    correct = cal.get("correct", 0)
    incorrect = cal.get("incorrect", 0)
    unresolved = cal.get("unresolved", 0)

    resolved = correct + incorrect
    accuracy = correct / max(resolved, 1)
    flags = cal.get("overconfidence_flags", [])
    flag_count = len(flags)

    # Score: accuracy contributes 40, band distribution 30, flag absence 30
    score = round(
        (accuracy * 40) +
        max(0, 30 - (unresolved / max(total, 1)) * 30) +
        max(0, 30 - flag_count * 10)
    )
    score = max(0, min(100, score))

    problems = []
    if accuracy < 0.5 and resolved >= 3:
        problems.append(f"Accuracy {accuracy:.0%} is below 50% threshold")
    if flag_count > 0:
        for f in flags:
            problems.append(f"Overconfidence: {f.get('region','?')} {f.get('band','?')} at {f.get('pct','?')}%")
    if unresolved > total * 0.8:
        problems.append(f"{unresolved}/{total} judgments unresolved — need more postdict runs")

    return {"score": score, "accuracy": round(accuracy, 2),
            "total": total, "correct": correct, "incorrect": incorrect,
            "unresolved": unresolved, "flags": flag_count, "problems": problems}


def assess_routing() -> dict:
    """Score routing health: is the model usage policy consistent with actual behavior?"""
    scanner = REPO_ROOT / "scripts" / "routing_scanner.py"
    if not scanner.exists():
        return {"score": 50, "problems": ["Routing scanner not available"]}

    try:
        result = subprocess.run(
            ["python3", str(scanner)],
            capture_output=True, text=True, timeout=15,
            cwd=str(REPO_ROOT))
        output = result.stdout + result.stderr
    except Exception as exc:
        return {"score": 30, "problems": [f"Routing scan failed: {exc}"]}

    problems = []
    score = 50  # Base score

    if "Routing consistent with policy" in output:
        score += 30
    else:
        problems.append("Routing inconsistent with policy")

    if "No routing policy violations detected" in output:
        score += 20
    else:
        violations = [l for l in output.split('\n') if '⚠️' in l]
        for v in violations[:3]:
            problems.append(v.strip())

    # Check if tiered routing is configured
    cron_file = REPO_ROOT / "scripts" / "daily-brief-cron.sh"
    if cron_file.exists():
        content = cron_file.read_text()
        if "tier2" in content or "--tier2-model" in content:
            score += 20
        else:
            problems.append("Single-model pipeline — tiered routing not configured")
    else:
        problems.append("Cron script not found")

    score = max(0, min(100, score))
    return {"score": score, "problems": problems}


def assess_config() -> dict:
    """Score config health: is the system configuration valid?"""
    validator = REPO_ROOT / "scripts" / "validate_config.py"
    if not validator.exists():
        return {"score": 50, "problems": ["Config validator not available"]}

    try:
        result = subprocess.run(
            ["python3", str(validator)],
            capture_output=True, text=True, timeout=10,
            cwd=str(REPO_ROOT))
        valid = result.returncode == 0
    except Exception:
        return {"score": 30, "problems": ["Config validation failed to run"]}

    if valid:
        return {"score": 100, "problems": []}
    else:
        return {"score": 0, "problems": ["Config validation FAILED"]}


def assess_observation() -> dict:
    """Score observation health: are we watching our own behavior?"""
    log_dir = REPO_ROOT / "logs"
    episodic_dir = REPO_ROOT / "brain" / "memory" / "episodic"
    heartbeat = load_json(REPO_ROOT / "memory" / "heartbeat-state.json")

    score = 0
    problems = []

    # Logs exist?
    if log_dir.exists() and len(list(log_dir.glob("*.log"))) >= 3:
        score += 25
    else:
        problems.append("Insufficient log files")

    # Episodic memory exists?
    if episodic_dir.exists():
        ep_files = list(episodic_dir.glob("*.jsonl"))
        if ep_files:
            score += 25
        else:
            problems.append("No episodic memory entries")
    else:
        problems.append("Episodic memory directory missing")

    # Heartbeat state exists?
    if heartbeat:
        score += 25
        last = heartbeat.get("lastHeartbeat", 0)
        if last:
            score += 25
    else:
        problems.append("Heartbeat state missing")

    # Monitor running?
    monitor_logs = list(log_dir.glob("continuous-monitor-*.log"))
    if monitor_logs:
        score += 25  # bonus
    else:
        problems.append("No continuous monitor logs")

    score = max(0, min(100, score))
    return {"score": score, "log_count": len(list(log_dir.glob("*.log"))),
            "episodic_count": len(list(episodic_dir.glob("*.jsonl"))) if episodic_dir.exists() else 0,
            "problems": problems}


def assess_autonomy() -> dict:
    """Score autonomy health: are adaptive loops actually closed?

    Phase 14 upgrade: checks not just file existence but whether each loop
    has FIRED at least once (produced behavioral output).
    """
    loops = [
        "calibration → confidence restriction",
        "collection quality → band constraint",
        "event → behavioral adaptation",
        "unscheduled cognition",
        "source trust evolution",
        "procedural learning",
        "autonomous prioritization",
    ]
    closed = 0
    problems = []

    # 1. Calibration → confidence restriction: check behavioral state
    bs = load_json(STATE_DIR / "behavioral-state.json")
    if bs:
        constraints = bs.get("per_region_constraints", {})
        restricted_regions = sum(1 for r, c in constraints.items() 
                                 if len(c.get("available_bands", [])) < 4)
        if restricted_regions > 0:
            closed += 1
            _bands_detail = f"{restricted_regions}/6 regions have restricted bands"
        else:
            problems.append("Behavioral state exists but no regions are constrained")
    else:
        problems.append("No behavioral state — calibration cannot restrict bands")

    # 2. Collection quality → band constraint: check collection state + behavioral
    coll_state = load_json(STATE_DIR / "collection-state.json")
    if coll_state and bs:
        # Check if any region's quality tier maps to restricted bands
        coll_confidence = bs.get("collection_directives", {}).get("by_region", {})
        restricted_by_collection = sum(
            1 for r, c in coll_confidence.items()
            if len(c.get("confidence_bands_available", [])) < 4
        )
        if restricted_by_collection > 0:
            closed += 1
        else:
            problems.append("Collection quality is not restricting any bands")
    else:
        problems.append("No collection state or behavioral state for quality→band")

    # 3. Event → behavioral adaptation: check event directives
    if bs:
        events = bs.get("event_directives", {})
        if events.get("active_escalations") or events.get("collection_changes"):
            closed += 1
        else:
            problems.append("No event-driven adaptations have triggered")
    else:
        problems.append("No behavioral state for event adaptation check")

    # 4. Unscheduled cognition: check autonomy tracker
    tracker = load_json(STATE_DIR / "autonomy-tracker.json")
    if tracker:
        uc_count = len(tracker.get("unscheduled_cognition_events", []))
        if uc_count > 0:
            closed += 1
        else:
            problems.append("Unscheduled cognition exists but has never fired")
    else:
        problems.append("No autonomy tracker — unscheduled cognition not measurable")

    # 5. Source trust evolution
    if coll_state:
        utilization = coll_state.get("source_utilization", {})
        trust_scores = [u.get("trust_score", 0) for u in utilization.values()]
        if any(t != 0.5 for t in trust_scores):  # 0.5 is default
            closed += 1
        else:
            problems.append("Source trust scores are all default — no evolution")
    else:
        problems.append("No collection state for source trust check")

    # 6. Procedural learning
    proc_dir = pathlib.Path(REPO_ROOT / "brain" / "memory" / "procedural")
    if proc_dir.exists():
        proc_files = list(proc_dir.glob("*.md"))
        if len(proc_files) > 0:
            closed += 1
        else:
            problems.append("Procedural directory exists but no memories stored")
    else:
        problems.append("No procedural memory directory")

    # 7. Autonomous prioritization
    if bs and bs.get("version", 0) >= 2:
        prio = bs.get("autonomous_prioritization", {})
        varied_scores = len(set(p.get("priority_tier") for p in prio.values())) > 1
        if prio and varied_scores:
            closed += 1
        else:
            problems.append("Prioritization exists but all regions have the same tier")
    else:
        problems.append("No autonomous prioritization in behavioral state")

    score = round((closed / len(loops)) * 100)
    problems = problems[:5]  # Cap at 5 problems in output

    return {
        "score": score, 
        "closed_loops": closed, 
        "total_loops": len(loops),
        "loops": loops,
        "problems": problems,
        "detail": {
            "restricted_regions": len([r for r, c in bs.get("per_region_constraints", {}).items() 
                                       if len(c.get("available_bands", [])) < 4]) if bs else 0,
            "unscheduled_events": len(tracker.get("unscheduled_cognition_events", [])) if tracker else 0,
            "procedural_memories": len(list(proc_dir.glob("*.md"))) if proc_dir.exists() else 0,
        }
    }


def assess_epistemic() -> dict:
    """Score epistemic health: are we tracking our own uncertainty?"""
    score = 0
    problems = []

    # Calibration data exists with bands
    cal = load_json(STATE_DIR / "calibration-tracking.json")
    if cal:
        bands = cal.get("by_confidence_band", {})
        if bands:
            score += 30
            # Check band diversity
            if len(bands) >= 3:
                score += 20
        if cal.get("total_judgments", 0) > 0:
            score += 20

    # Collection quality conditioning exists
    if (REPO_ROOT / "skills" / "daily-intel-brief" / "references" / "deepseek-prompts.md").exists():
        prompts = (REPO_ROOT / "skills" / "daily-intel-brief" / "references" / "deepseek-prompts.md").read_text()
        if "collection_quality" in prompts:
            score += 15
        if "calibration" in prompts.lower():
            score += 15

    if score < 50:
        problems.append("Epistemic tracking incomplete")

    return {"score": score, "band_count": len(cal.get("by_confidence_band", {})) if cal else 0,
            "judgment_count": cal.get("total_judgments", 0) if cal else 0,
            "problems": problems}


# ── Aggregation ─────────────────────────────────────────────────────

def load_previous_scores() -> dict:
    """Load yesterday's assessment for comparison."""
    yesterday = yesterday_key()
    return load_json(HEALTH_DIR / f"{yesterday}.json")


def generate_injection(assessment: dict, previous: dict) -> str | None:
    """Generate a prompt injection block if critical issues found.
    
    Returns markdown string, or None if no injection needed.
    """
    parts = ["\n\n### === SELF-ASSESSMENT FEEDBACK ===\n"]
    triggered = False

    for dim, data in assessment.get("dimensions", {}).items():
        score = data.get("score", 50)
        problems = data.get("problems", [])
        if score < 50:
            triggered = True
            parts.append(f"\n⚠ {dim.upper()} ({score}/100):")
            for p in problems[:3]:
                parts.append(f"  • {p}")
            # If this dimension regressed, flag harder
            prev = previous.get("dimensions", {}).get(dim, {})
            prev_score = prev.get("score", score)
            if score < prev_score - 10:
                parts.append(f"  ↓ REGRESSION from {prev_score} (was {prev_score - score}pts higher)")

    if triggered:
        parts.append(
            "\nAction: Address the flagged issues in this assessment. "
            "For overconfidence: widen bands. For collection gaps: note limitations. "
            "For routing: escalate to user."
        )
        parts.append("\n=== END SELF-ASSESSMENT FEEDBACK ===")
        return "\n".join(parts)

    return None


def generate_report(assessment: dict, previous: dict) -> str:
    """Generate a structured markdown report."""
    today = today_key()
    overall = assessment.get("overall", 50)
    prev_overall = previous.get("overall", overall)

    trend = "↑" if overall > prev_overall else "↓" if overall < prev_overall else "→"
    delta = overall - prev_overall

    lines = [
        f"# System Health Assessment — {today}",
        "",
        f"**Overall: {overall}/100** ({trend} {delta:+.0f} vs {previous.get('date', 'baseline')})",
        "",
        "| Dimension | Score | Trend | Key Issue |",
        "|-----------|-------|-------|-----------|",
    ]

    for dim, data in assessment.get("dimensions", {}).items():
        score = data.get("score", 50)
        prev = previous.get("dimensions", {}).get(dim, {})
        prev_score = prev.get("score", score)
        d = score - prev_score
        arrow = "↑" if d > 5 else "↓" if d < -5 else "→"
        issues = data.get("problems", [])
        top_issue = issues[0] if issues else "none"
        lines.append(f"| {dim.title():15s} | {score}/100 | {arrow} {d:+.0f} | {top_issue} |")

    lines.extend([
        "",
        "---",
        "## Dimension Details",
        "",
    ])

    for dim, data in assessment.get("dimensions", {}).items():
        score = data.get("score", 50)
        problems = data.get("problems", [])
        lines.append(f"### {dim.title()}: {score}/100")
        if problems:
            for p in problems:
                lines.append(f"- ⚠ {p}")
        else:
            lines.append("- ✅ No issues")
        # Add key metric
        for k, v in data.items():
            if k not in ("score", "problems"):
                lines.append(f"  {k}: {v}")
        lines.append("")

    # Recommendations
    critical_issues = sum(1 for d in assessment.get("dimensions", {}).values()
                         if d.get("score", 50) < 40)
    if critical_issues:
        lines.append("## Critical Actions Required")
        lines.append("")
        for dim, data in assessment.get("dimensions", {}).items():
            if data.get("score", 50) < 40:
                lines.append(f"- **{dim.title()}** ({data['score']}/100): {'; '.join(data.get('problems', ['Unknown']))}")

    lines.append(f"\n*Generated by self-assessment daemon at {dt.datetime.now(dt.timezone.utc).isoformat()}Z*")
    return "\n".join(lines)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true",
                        help="Skip expensive checks (routing scan)")
    args = parser.parse_args()

    today = today_key()
    log(f"Self-assessment starting (quick={args.quick})")

    # Run all dimension assessments
    dimensions = {
        "collection": assess_collection(),
        "calibration": assess_calibration(),
        "config": assess_config(),
        "observation": assess_observation(),
        "autonomy": assess_autonomy(),
        "epistemic": assess_epistemic(),
    }
    if not args.quick:
        dimensions["routing"] = assess_routing()
    else:
        dimensions["routing"] = {"score": 50, "problems": ["Skipped (quick mode)"]}

    # Calculate weighted overall score
    overall = 0.0
    for dim, data in dimensions.items():
        weight = DIMENSION_WEIGHTS.get(dim, 0.1)
        overall += data.get("score", 50) * weight
    overall = round(overall)

    # Load previous for comparison
    previous = load_previous_scores()

    assessment = {
        "date": today,
        "overall": overall,
        "dimensions": dimensions,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
    }

    # Save
    HEALTH_DIR.mkdir(parents=True, exist_ok=True)
    (HEALTH_DIR / f"{today}.json").write_text(json.dumps(assessment, indent=2))
    log(f"Assessment saved to {HEALTH_DIR / f'{today}.json'}")

    # Generate report
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = generate_report(assessment, previous)
    (REPORT_DIR / f"system-health-{today}.md").write_text(report)
    log(f"Report saved to {REPORT_DIR / f'system-health-{today}.md'}")

    # Generate prompt injection if critical issues found
    injection = generate_injection(assessment, previous)
    if injection:
        ADJUSTMENT_FILE.parent.mkdir(parents=True, exist_ok=True)
        ADJUSTMENT_FILE.write_text(injection)
        log(f"CRITICAL: injection written to {ADJUSTMENT_FILE} — {overall}/100")
    else:
        # Clear old injection if it exists
        if ADJUSTMENT_FILE.exists():
            ADJUSTMENT_FILE.unlink()
        log(f"All clear: {overall}/100 — no injection needed")

    # Print summary
    print(f"\n{'='*50}")
    print(f"SYSTEM HEALTH: {overall}/100")
    print(f"{'='*50}")
    for dim, data in sorted(dimensions.items()):
        s = data["score"]
        bar = "█" * (s // 10) + "░" * (10 - s // 10)
        issues = len(data.get("problems", []))
        flag = " ⚠" if issues > 0 else ""
        print(f"  {dim:15s} {bar} {s:3d}/100{flag}")
    print(f"{'='*50}")
    print(f"Report: exports/reports/system-health-{today}.md")

    return 1 if overall < 40 else 0


if __name__ == "__main__":
    sys.exit(main())
