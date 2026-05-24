#!/usr/bin/env python3
"""
Autonomous Operations Cycle — runs regularly to monitor and maintain Trevor.
Replaces the manual HEARTBEAT phases with a single automated check.

Checks (rotated per run):
  1. Cron health — are all crons firing? Any in error state?
  2. Feed health — any new dead feeds? Should we prune?
  3. Collection state — source freshness, coverage gaps
  4. Pipeline health — did the last daily brief succeed? Any QC issues?
  5. Cost snapshot — DeepSeek balance, token usage trends
  6. Brain maintenance — reindex, consolidate memories

For each check: logs findings, auto-fixes what's within autonomy boundaries,
surfaces only what needs human attention.

Usage:
    python3 scripts/autonomous_cycle.py              # run next phase
    python3 scripts/autonomous_cycle.py --all         # run all phases
    python3 scripts/autonomous_cycle.py --crons       # cron health only
"""

import argparse
import json
import os
import pathlib
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta

REPO = pathlib.Path(__file__).resolve().parent.parent
STATE_FILE = REPO / "brain" / "memory" / "semantic" / "autonomous-state.json"
DEAD_FEEDS = REPO / "brain" / "memory" / "semantic" / "dead-feeds.json"
CATALOG = REPO / "analyst" / "meta" / "sources_tested.json"
CRON_JOBS = pathlib.Path(os.path.expanduser("~/.openclaw/cron/jobs.json"))

PHASES = ["crons", "feeds", "collection", "pipeline", "costs", "brain"]
NOW = datetime.now(timezone.utc)


def log(msg: str) -> None:
    ts = NOW.strftime("%H:%M:%S")
    print(f"[auto {ts}] {msg}", file=sys.stderr, flush=True)


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"phase": 0, "last_run": "", "findings": [], "fixes_applied": []}


def save_state(state: dict) -> None:
    state["last_run"] = NOW.isoformat()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


# ── Phase handlers ─────────────────────────────────────────────────

def check_crons(state: dict) -> list[str]:
    """Check all OpenClaw crons for errors."""
    findings = []
    if not CRON_JOBS.exists():
        return ["Cannot read cron jobs — CRON_JOBS path missing"]

    try:
        data = json.loads(CRON_JOBS.read_text())
        jobs = data.get("jobs", [])
    except Exception as e:
        return [f"Cron jobs parse error: {e}"]

    errors = []
    idle_weekly = []
    for j in jobs:
        name = j.get("name", "?")
        enabled = j.get("enabled", True)
        status = j.get("state", {}).get("status", "ok")

        if not enabled:
            continue

        # Check delivery routes
        delivery = j.get("delivery", {})
        route = delivery.get("channel", "last")
        mode = delivery.get("mode", "none")

        if status == "error":
            errors.append(f"{name}: error state")
        elif route == "last" and "no route" in str(delivery.get("to", "")):
            findings.append(f"⚠️ {name}: delivery route broken (no route)")

        # Weekly/monthly crons in idle are expected
        if status == "idle":
            sched = j.get("schedule", {})
            expr = sched.get("expr", "")
            if any(day in expr for day in ["1", "2", "3", "4", "5", "6", "0"]):
                idle_weekly.append(name)

    if errors:
        findings.append(f"🔴 {len(errors)} crons in error: {', '.join(errors)}")
    if findings:
        state.setdefault("findings", []).append(f"[crons] {NOW.strftime('%Y-%m-%d %H:%M')}: {len(findings)} issues")

    return findings or [f"✅ All {len(jobs)} crons healthy ({len(idle_weekly)} idle weekly)"]


def check_feeds(state: dict) -> list[str]:
    """Check feed health — dead feeds, catalog freshness."""
    findings = []

    # Dead feed cache stats
    if DEAD_FEEDS.exists():
        try:
            dead = json.loads(DEAD_FEEDS.read_text())
            findings.append(f"Dead-feed cache: {len(dead)} feeds tracked")
            # Count feeds due for retest (>48h)
            retest = 0
            cutoff = NOW - timedelta(hours=48)
            for url, info in dead.items():
                last = info.get("last_failed_at", "")
                if last:
                    try:
                        failed_dt = datetime.fromisoformat(last)
                        if failed_dt < cutoff:
                            retest += 1
                    except Exception:
                        pass
            if retest:
                findings.append(f"  {retest} feeds due for retest (>48h since last failure)")
        except Exception:
            pass

    # Catalog stats
    if CATALOG.exists():
        try:
            cat = json.loads(CATALOG.read_text())
            total = cat.get("total_entries", 0)
            working = cat.get("working_feeds", 0)
            findings.append(f"Catalog: {working}/{total} working feeds")
            # Region coverage
            regions = cat.get("regions_breakdown", {})
            weak = [(r, c) for r, c in regions.items() if c < 5 and r not in ("oceania",)]
            if weak:
                findings.append(f"  Weak coverage: {', '.join(f'{r}({c})' for r, c in weak)}")
        except Exception:
            pass

    state.setdefault("findings", []).append(f"[feeds] {NOW.strftime('%Y-%m-%d %H:%M')}: checked")
    return findings or ["✅ Feed health nominal"]


def check_pipeline(state: dict) -> list[str]:
    """Check if the last daily brief ran successfully."""
    findings = []
    today = NOW.strftime("%Y-%m-%d")
    brief_dir = pathlib.Path(os.path.expanduser(f"~/trevor-briefings/{today}"))
    exec_file = brief_dir / "analysis" / "exec_summary.json"

    if exec_file.exists():
        try:
            es = json.loads(exec_file.read_text())
            bluf = es.get("bluf", "")[:100]
            findings.append(f"Today's brief: ✅ exists ({len(bluf)} char BLUF)")

            # Check for error patterns
            if "ERROR:" in bluf or "Error generating" in bluf:
                findings.append("🔴 BLUF contains error message!")

            # Check model
            models = es.get("models_used", [])
            if isinstance(models, str):
                models = [models]
            flash_used = any("flash" in str(m).lower() for m in models)
            if flash_used:
                findings.append(f"⚠️ Flash model detected: {models}")
        except Exception as e:
            findings.append(f"⚠️ Brief exists but couldn't parse: {e}")
    else:
        findings.append(f"🔴 No brief found for {today}")

    # Check AgentMail delivery
    # (can't easily check — but log file has delivery status)
    log_file = REPO / "logs" / f"daily-brief-{today}.log"
    if log_file.exists():
        log_text = log_file.read_text()
        if "Delivery successful" in log_text or "Sent via AgentMail" in log_text:
            findings.append("Delivery: ✅ confirmed in logs")
        elif "DELIVERY ABORTED" in log_text or "FAILED" in log_text:
            findings.append("🔴 Delivery failed — check logs")
        else:
            findings.append("⚠️ Delivery status unclear from logs")

    state.setdefault("findings", []).append(f"[pipeline] {NOW.strftime('%Y-%m-%d %H:%M')}: checked")
    return findings


def check_costs(state: dict) -> list[str]:
    """Check DeepSeek balance and usage."""
    findings = []
    usage_file = REPO / "brain" / "memory" / "semantic" / "deepseek-usage.json"
    if usage_file.exists():
        try:
            usage = json.loads(usage_file.read_text())
            balance = usage.get("balance", {}).get("USD", 0)
            if balance:
                findings.append(f"DeepSeek balance: ${balance:.2f}")
                if balance < 1.0:
                    findings.append("⚠️ Low balance — top up soon")
        except Exception:
            pass
    else:
        findings.append("No DeepSeek usage data")

    return findings or ["✅ Costs nominal"]


def check_brain(state: dict) -> list[str]:
    """Brain maintenance — reindex if needed."""
    findings = []
    brain_script = REPO / "brain" / "scripts" / "brain.py"
    if brain_script.exists():
        try:
            result = subprocess.run(
                ["python3", str(brain_script), "reindex"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                findings.append("Brain reindex: ✅")
            else:
                findings.append(f"Brain reindex: ⚠️ {result.stderr[:100]}")
        except subprocess.TimeoutExpired:
            findings.append("Brain reindex: timed out")
        except Exception as e:
            findings.append(f"Brain reindex: {e}")
    else:
        findings.append("Brain script not found")

    state.setdefault("findings", []).append(f"[brain] {NOW.strftime('%Y-%m-%d %H:%M')}: reindexed")
    return findings


def check_collection(state: dict) -> list[str]:
    """Check collection state — source utilization, gaps."""
    findings = []
    coll_state = REPO / "brain" / "memory" / "semantic" / "collection-state.json"
    if coll_state.exists():
        try:
            cs = json.loads(coll_state.read_text())
            uncited = cs.get("uncited_feeds", [])
            if len(uncited) > 5:
                findings.append(f"{len(uncited)} uncited feeds (low signal)")
            findings.append(f"Collection state: {len(cs)} keys tracked")
        except Exception:
            pass
    return findings or ["✅ Collection state nominal"]


# ── Main ───────────────────────────────────────────────────────────

PHASE_MAP = {
    "crons": check_crons,
    "feeds": check_feeds,
    "collection": check_collection,
    "pipeline": check_pipeline,
    "costs": check_costs,
    "brain": check_brain,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Trevor autonomous operations cycle")
    parser.add_argument("--all", action="store_true", help="Run all phases")
    parser.add_argument("--crons", action="store_true", help="Cron health only")
    parser.add_argument("--feeds", action="store_true", help="Feed health only")
    parser.add_argument("--pipeline", action="store_true", help="Pipeline health only")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--quiet", action="store_true", help="No output unless issues found")
    args = parser.parse_args()

    state = load_state()
    all_results = {}

    # Determine which phases to run
    if args.all:
        phases = PHASES
    elif any(getattr(args, p, False) for p in PHASES):
        phases = [p for p in PHASES if getattr(args, p, False)]
    else:
        # Rotate to next phase
        idx = state.get("phase", 0) % len(PHASES)
        phases = [PHASES[idx]]
        state["phase"] = (idx + 1) % len(PHASES)
        save_state(state)

    # Run phases
    for phase in phases:
        log(f"Running phase: {phase}")
        try:
            handler = PHASE_MAP[phase]
            results = handler(state)
            all_results[phase] = results
        except Exception as e:
            all_results[phase] = [f"Phase {phase} failed: {e}"]

    # Output
    if args.json:
        print(json.dumps(all_results, indent=2))
    else:
        has_issues = False
        for phase, results in all_results.items():
            for r in results:
                if r.startswith("🔴") or r.startswith("⚠️") or (not args.quiet):
                    print(r)
                if r.startswith("🔴"):
                    has_issues = True
        if not has_issues and not args.quiet:
            print("✅ All systems nominal")

    save_state(state)
    return 0 if not any(
        any(r.startswith("🔴") for r in results)
        for results in all_results.values()
    ) else 1


if __name__ == "__main__":
    sys.exit(main())
