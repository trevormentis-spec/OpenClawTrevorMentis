#!/usr/bin/env python3
"""quality_audit.py — Active quality assurance + auto-repair for the daily intel pipeline.

NOT a passive logger. Every detected issue triggers either:
  - an automatic repair
  - an escalation (puts failure in state.json for improvement_daemon)
  - a deferral (notes it for the next pipeline run)

Usage:
  python3 quality_audit.py              # full audit + auto-repair
  python3 quality_audit.py --check      # audit only, no repair
  python3 quality_audit.py --status     # show health summary
"""
from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from trevor_config import THEATRE_KEYS as THEATRES, WORKSPACE, EXPORTS_DIR
from trevor_log import get_logger, HealthReport

log = get_logger("quality_audit")

IMAGES_DIR = SKILL_ROOT / 'images'
MAPS_DIR = SKILL_ROOT / 'maps'
ASSESS_DIR = SKILL_ROOT / 'assessments'
SCRIPTS_DIR = SKILL_ROOT / 'scripts'
CRON_DIR = SKILL_ROOT / 'cron_tracking'

STATE_FILE = CRON_DIR / 'state.json'
IMPROVEMENT_LOG = CRON_DIR / 'improvement_log.json'

# ── Repair registry: issue_type → repair action ──
REPAIR_REGISTRY = {}


def register_repair(issue_type: str):
    """Decorator to register a repair function."""
    def wrapper(fn):
        REPAIR_REGISTRY[issue_type] = fn
        return fn
    return wrapper


# ═══════════════════════════════════════════════════
# REPAIR FUNCTIONS
# ═══════════════════════════════════════════════════

@register_repair("missing_assessment")
def repair_missing_assessment(region: str) -> bool:
    """Regenerate a missing assessment by running the generator for one theatre."""
    log.info(f"Repairing missing assessment: {region}")
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / 'generate_assessments.py')],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            log.info(f"Assessment regenerated for {region}")
            return True
        else:
            log.error(f"Failed to regenerate {region}: {result.stderr[-200:]}")
            return False
    except subprocess.TimeoutExpired:
        log.error(f"Timeout regenerating {region}")
        return False


@register_repair("missing_image")
def repair_missing_image() -> bool:
    """Regenerate all images by running refresh_imagery."""
    log.info("Repairing missing images")
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / 'refresh_imagery.py')],
            capture_output=True, text=True, timeout=180
        )
        if result.returncode == 0:
            log.info("Images regenerated")
            return True
        else:
            log.error(f"Image regeneration failed: {result.stderr[-200:]}")
            return False
    except subprocess.TimeoutExpired:
        log.error("Timeout regenerating images")
        return False


@register_repair("stale_memory")
def repair_stale_memory() -> bool:
    """Re-index assessments into FTS5 memory store."""
    log.info("Repairing stale memory index")
    try:
        result = subprocess.run(
            [sys.executable, str(SKILL_ROOT / 'memory' / 'index_memory.py')],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            log.info("Memory re-indexed")
            return True
        else:
            log.error(f"Memory re-index failed: {result.stderr[-200:]}")
            return False
    except subprocess.TimeoutExpired:
        log.error("Timeout re-indexing memory")
        return False


@register_repair("stale_kalshi")
def repair_stale_kalshi() -> bool:
    """Re-run the Kalshi scanner."""
    log.info("Repairing stale Kalshi data")
    scanner = WORKSPACE / 'scripts' / 'kalshi_scanner.py'
    if not scanner.exists():
        log.warning(f"Kalshi scanner not found at {scanner}")
        return False
    try:
        result = subprocess.run(
            [sys.executable, str(scanner), '--save'],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            log.info("Kalshi data refreshed")
            return True
        else:
            log.error(f"Kalshi scan failed: {result.stderr[-200:]}")
            return False
    except subprocess.TimeoutExpired:
        log.error("Timeout scanning Kalshi")
        return False


@register_repair("missing_font")
def repair_missing_font() -> bool:
    """Attempt to download missing fonts."""
    log.info("Repairing missing fonts")
    try:
        sys.path.insert(0, str(SKILL_ROOT))
        from trevor_fonts import ensure_fonts_downloaded
        ok = ensure_fonts_downloaded()
        if ok:
            log.info("Fonts downloaded")
        else:
            log.warning("Some fonts could not be downloaded")
        return ok
    except Exception as e:
        log.error(f"Font repair failed: {e}")
        return False


# ═══════════════════════════════════════════════════
# AUDIT FUNCTIONS
# ═══════════════════════════════════════════════════

def check_assessments() -> list[dict]:
    """Check all theatre assessments exist and have content."""
    issues = []
    for region in THEATRES:
        path = ASSESS_DIR / f"{region}.md"
        if not path.exists():
            issues.append({
                "type": "missing_assessment",
                "severity": "critical",
                "region": region,
                "detail": f"Assessment missing for {region}",
            })
        elif path.stat().st_size < 100:
            issues.append({
                "type": "stale_assessment",
                "severity": "warning",
                "region": region,
                "detail": f"Assessment for {region} is only {path.stat().st_size} bytes",
            })
    return issues


def check_fonts() -> list[dict]:
    """Check fonts are available, attempt auto-download if missing."""
    issues = []
    required_fonts = ["BebasNeue-Regular.ttf", "Inter-Regular.ttf", "Inter-Light.ttf",
                      "Inter-Bold.ttf", "JetBrainsMono-Regular.ttf", "JetBrainsMono-Bold.ttf"]
    fonts_dir = SKILL_ROOT / 'fonts'
    for font in required_fonts:
        if not (fonts_dir / font).exists():
            issues.append({
                "type": "missing_font",
                "severity": "warning",
                "detail": f"Font {font} missing",
            })
    return issues


def check_memory() -> list[dict]:
    """Check FTS5 memory store is healthy."""
    issues = []
    try:
        from trevor_memory import MemoryStore
        mem = MemoryStore()
        count = mem.count("narrative")
        if count < 3:
            issues.append({
                "type": "stale_memory",
                "severity": "warning",
                "detail": f"Only {count} narrative entries in memory (expected 7+)",
            })
        mem.close()
    except Exception as e:
        issues.append({
            "type": "memory_error",
            "severity": "critical",
            "detail": str(e),
        })
    return issues


# ═══════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════

def run_auto_fix(issues: list[dict]) -> dict:
    """Attempt repairs for all fixable issues. Returns repair results."""
    results = {
        "attempted": 0,
        "succeeded": 0,
        "failed": 0,
        "deferred": 0,
        "details": [],
    }
    
    for issue in issues:
        issue_type = issue.get("type", "")
        if issue_type in REPAIR_REGISTRY:
            repair_fn = REPAIR_REGISTRY[issue_type]
            log.info(f"Attempting repair for {issue_type}", region=issue.get("region", ""))
            results["attempted"] += 1
            try:
                success = repair_fn(**{k: v for k, v in issue.items() if k in ("region",)})
                if success:
                    results["succeeded"] += 1
                    results["details"].append({"issue": issue_type, "status": "fixed"})
                else:
                    results["failed"] += 1
                    results["details"].append({"issue": issue_type, "status": "failed"})
            except Exception as e:
                results["failed"] += 1
                results["details"].append({"issue": issue_type, "status": "error", "detail": str(e)})
        else:
            results["deferred"] += 1
            results["details"].append({"issue": issue_type, "status": "deferred"})
    
    return results


def save_state(health: dict, repairs: dict):
    """Persist health state for the improvement daemon."""
    state = {
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "health": health,
        "repairs": repairs,
        "overall_status": "healthy" if health["issue_count"] == 0 else "degraded" if all(r["status"] != "failed" for r in repairs["details"]) else "broken",
    }
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Audit only, no repair")
    parser.add_argument("--status", action="store_true", help="Show health summary")
    args = parser.parse_args()
    
    if args.status:
        if STATE_FILE.exists():
            print(json.dumps(json.loads(STATE_FILE.read_text()), indent=2))
        else:
            print("No state file — run audit first")
        return 0
    
    log.info("Starting quality audit")
    
    # Run all checks
    all_issues = []
    all_issues.extend(check_assessments())
    all_issues.extend(check_fonts())
    all_issues.extend(check_memory())
    
    health = {
        "checked_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "issue_count": len(all_issues),
        "critical": len([i for i in all_issues if i.get("severity") == "critical"]),
        "warnings": len([i for i in all_issues if i.get("severity") == "warning"]),
        "issues": all_issues,
    }
    
    print(f"\n🔍 Quality Audit — {health['issue_count']} issues found "
          f"({health['critical']} critical, {health['warnings']} warnings)")
    
    for issue in all_issues:
        icon = "🔴" if issue["severity"] == "critical" else "🟡"
        region_str = f" [{issue.get('region','')}]" if issue.get('region') else ""
        print(f"  {icon} {issue['type']}{region_str}: {issue['detail'][:120]}")
    
    # Auto-repair (unless --check)
    repairs = {"attempted": 0, "succeeded": 0, "failed": 0, "deferred": 0, "details": []}
    if not args.check and all_issues:
        print(f"\n🔧 Attempting repairs...")
        repairs = run_auto_fix(all_issues)
        print(f"  Repairs: {repairs['succeeded']} succeeded, "
              f"{repairs['failed']} failed, {repairs['deferred']} deferred")
    
    # Save state
    save_state(health, repairs)
    
    # Log
    log.info("Audit complete",
             issues=health['issue_count'],
             critical=health['critical'],
             repairs_ok=repairs['succeeded'],
             repairs_failed=repairs['failed'])
    
    return 0 if health['critical'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
