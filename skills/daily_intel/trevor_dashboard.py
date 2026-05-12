#!/usr/bin/env python3
"""trevor_dashboard.py — Runtime observability dashboard.

Aggregates health, cost, memory, and pipeline state into a single
diagnostic report. Trevor can always answer: what is broken, degraded,
slow, changed, or fragile.

Usage:
    python3 trevor_dashboard.py          # full dashboard
    python3 trevor_dashboard.py --health # health only
    python3 trevor_dashboard.py --json   # JSON output for external monitoring
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(SKILL_ROOT))

from trevor_log import get_logger
from trevor_cost import CostTracker
from trevor_memory import MemoryStore
from trevor_freeze import MemoryFreeze

log = get_logger("dashboard")
CRON_DIR = SKILL_ROOT / "cron_tracking"


def collect_health() -> dict:
    """Collect health status from all subsystems."""
    health = {"status": "unknown", "issues": [], "warnings": []}
    
    # 1. State file
    state_file = CRON_DIR / "state.json"
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
            health["last_pipeline_state"] = state.get("overall_status", "unknown")
            if state.get("overall_status") == "broken":
                health["issues"].append("Pipeline state is 'broken'")
            health["last_run"] = state.get("timestamp", "")
        except:
            health["warnings"].append("Could not parse pipeline state")
    else:
        health["warnings"].append("No pipeline state — never run?")
    
    # 2. Cost
    try:
        cost = CostTracker().summary()
        health["cost"] = {
            "total_usd": cost["total_cost"],
            "snapshot_count": cost["snapshot_count"],
        }
    except Exception as e:
        health["warnings"].append(f"Cost tracking unavailable: {e}")
    
    # 3. Memory
    try:
        mem = MemoryStore()
        health["memory"] = {
            "total_entries": mem.count(),
            "narrative": mem.count("narrative"),
            "procedural": mem.count("procedural"),
            "execution": mem.count("execution"),
            "db_size_kb": mem.db_path.stat().st_size // 1024 if mem.db_path.exists() else 0,
        }
        mem.close()
    except Exception as e:
        health["warnings"].append(f"Memory unavailable: {e}")
    
    # 4. Freeze
    try:
        freeze = MemoryFreeze().status()
        health["memory_freeze"] = freeze
    except Exception as e:
        health["warnings"].append(f"Memory freeze unavailable: {e}")
    
    # 5. Diagnostics
    try:
        from trevor_diag import run as run_diag
        diag = run_diag()
        health["diagnostics"] = {
            "passed": sum(1 for r in diag if r["status"] == "ok"),
            "failed": sum(1 for r in diag if r["status"] == "fail"),
            "total": len(diag),
        }
        for r in diag:
            if r["status"] == "fail":
                health["issues"].append(f"Diagnostic: {r['check']} — {r['detail']}")
    except Exception as e:
        health["warnings"].append(f"Diagnostics unavailable: {e}")
    
    # 6. Skills
    try:
        from trevor_skills import SkillRegistry
        skill_count = SkillRegistry().count()
        health["skills"] = {"count": skill_count}
    except:
        health["skills"] = {"count": 0}
    
    # Determine overall status
    if len(health["issues"]) == 0 and len(health["warnings"]) == 0:
        health["status"] = "healthy"
    elif len(health["issues"]) == 0:
        health["status"] = "degraded"
    else:
        health["status"] = "broken"
    
    return health


def print_dashboard(health: dict):
    """Print a human-readable dashboard."""
    print(f"\n{'='*60}")
    print(f" TREVOR RUNTIME DASHBOARD")
    print(f" {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*60}")
    
    status = health.get("status", "unknown")
    status_icon = {"healthy": "✅", "degraded": "🟡", "broken": "🔴", "unknown": "❓"}
    print(f"\n Overall: {status_icon.get(status, '❓')} {status.upper()}")
    
    print(f"\n── Health ──")
    if health.get("issues"):
        for i in health["issues"]:
            print(f"  🔴 {i}")
    if health.get("warnings"):
        for w in health["warnings"]:
            print(f"  🟡 {w}")
    if not health.get("issues") and not health.get("warnings"):
        print(f"  ✅ No issues")
    
    if health.get("memory"):
        m = health["memory"]
        print(f"\n── Memory ──")
        print(f"  Total: {m['total_entries']} entries")
        print(f"  Narrative: {m['narrative']}")
        print(f"  Procedural: {m['procedural']}")
        print(f"  Execution: {m['execution']}")
        print(f"  DB size: {m['db_size_kb']} KB")
    
    if health.get("cost"):
        print(f"\n── Cost ──")
        print(f"  Total: ${health['cost']['total_usd']:.4f}")
        print(f"  Snapshots: {health['cost']['snapshot_count']}")
    
    if health.get("diagnostics"):
        d = health["diagnostics"]
        print(f"\n── Diagnostics ──")
        print(f"  {d['passed']}/{d['total']} checks passed")
        if d['failed'] > 0:
            print(f"  {d['failed']} FAILED")
    
    if health.get("skills"):
        print(f"\n── Skills ──")
        print(f"  {health['skills']['count']} registered")
    
    print()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--health", action="store_true", help="Health summary only")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()
    
    health = collect_health()
    
    if args.json:
        print(json.dumps(health, indent=2))
    elif args.health:
        print(f"Status: {health['status']}")
        for i in health.get("issues", []):
            print(f"  🔴 {i}")
        for w in health.get("warnings", []):
            print(f"  🟡 {w}")
    else:
        print_dashboard(health)
    
    return 0 if health["status"] != "broken" else 1


if __name__ == "__main__":
    sys.exit(main())
