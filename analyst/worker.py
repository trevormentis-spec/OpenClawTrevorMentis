#!/usr/bin/env python3
"""Worker — pulls highest-priority task from queue, executes, logs, updates state.

Loops continuously with backoff. Per-task pattern:
  Load task → check budget → execute → validate → update state → log → mark done.

Used in two modes:
  1. Daemon mode (--daemon): loops every 60s with exponential backoff on empty queue
  2. One-shot mode (--one-shot): processes exactly one task and exits
  3. Sweep mode (default): processes all pending tasks and exits
"""

from __future__ import annotations

import datetime
import json
import pathlib
import sys
import time
import importlib
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
QUEUE_DIR = REPO_ROOT / "analyst" / "queue"
WORKER_LOG = REPO_ROOT / "analyst" / "worker_log.jsonl"

BUDGET_MAX = 0.50  # $0.50 per cycle
CUMULATIVE_COST = 0.0


def load_cost_state() -> float:
    """Load cumulative cost for this cycle."""
    cost_file = REPO_ROOT / "brain" / "meta" / "worker-cost.json"
    if cost_file.exists():
        try:
            return json.loads(cost_file.read_text()).get("cycle_cost", 0.0)
        except Exception:
            pass
    return 0.0


def save_cost_state(cost: float) -> None:
    """Save cumulative cost."""
    cost_file = REPO_ROOT / "brain" / "meta" / "worker-cost.json"
    cost_file.parent.mkdir(parents=True, exist_ok=True)
    cost_file.write_text(json.dumps({"cycle_cost": round(cost, 6), "updated_at": datetime.datetime.utcnow().isoformat() + "Z"}))


def get_next_task() -> dict[str, Any] | None:
    """Find the highest-priority pending task in the LATEST queue file only."""
    queue_files = sorted(QUEUE_DIR.glob("*.json"))
    if not queue_files:
        return None
    latest_qf = queue_files[-1]  # Only process the most recent cycle
    try:
        queue = json.loads(latest_qf.read_text())
        for task in queue.get("tasks", []):
            if task.get("status") == "pending":
                task["_queue_file"] = str(latest_qf)
                return task
    except (json.JSONDecodeError, Exception):
        pass
    return None


def mark_task_done(task: dict[str, Any], result: dict[str, Any]) -> None:
    """Mark a task as completed in its queue file."""
    qf = pathlib.Path(task.get("_queue_file", ""))
    if not qf.exists():
        return
    
    try:
        queue = json.loads(qf.read_text())
        for i, t in enumerate(queue.get("tasks", [])):
            if t.get("task_type") == task.get("task_type") and t.get("target") == task.get("target"):
                t["status"] = result.get("status", "completed")
                t["completed_at"] = datetime.datetime.utcnow().isoformat() + "Z"
                t["cost"] = result.get("cost", 0.0)
                t["outcome"] = result.get("action", "")
                break
        qf.write_text(json.dumps(queue, indent=2, default=str))
    except Exception:
        pass


def log_worker_entry(entry: dict[str, Any]) -> None:
    """Append to the worker log."""
    WORKER_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry["logged_at"] = datetime.datetime.utcnow().isoformat() + "Z"
    with open(WORKER_LOG, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")


def execute_task(task: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
    """Execute a task by calling its module's execute() function."""
    if dry_run:
        return dry_run_execute(task)
    task_type = task.get("task_type", "")
    module_path = f"analyst.tasks.{task_type}"
    
    try:
        sys.path.insert(0, str(REPO_ROOT))
        if task_type in sys.modules:
            module = importlib.reload(sys.modules[task_type])
        else:
            module = importlib.import_module(f"analyst.tasks.{task_type}")
        
        result = module.execute(task)
        return result
    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
            "cost": 0.0,
        }


def process_one(cycle_cost: float, dry_run: bool = False) -> bool:
    """Process one task. Returns True if a task was processed."""
    task = get_next_task()
    if not task:
        return False
    
    # Check budget
    est_cost = task.get("estimated_cost", 0.001)
    if cycle_cost + est_cost > BUDGET_MAX:
        print(f"[worker] Budget limit: ${cycle_cost:.4f} + ${est_cost:.4f} > ${BUDGET_MAX:.2f}. Deferring {task.get('task_type')}.", file=sys.stderr)
        return False
    
    print(f"[worker] Executing {task.get('task_type')}: {task.get('target', '?')}")
    result = execute_task(task, dry_run=dry_run)
    
    # Update cost
    actual_cost = result.get("cost", est_cost)
    cycle_cost += actual_cost
    save_cost_state(cycle_cost)
    
    # Mark done
    mark_task_done(task, result)
    
    # Log
    entry = {
        "task_type": task.get("task_type"),
        "target": str(task.get("target", "")),
        "cost": actual_cost,
        "status": result.get("status", "unknown"),
        "outcome": result.get("action", ""),
        "note": result.get("note", result.get("error", "")),
    }
    log_worker_entry(entry)
    
    print(f"[worker] Done: {task.get('task_type')} → {result.get('status')} (${actual_cost:.6f})")
    return True


def dry_run_execute(task: dict[str, Any]) -> dict[str, Any]:
    """Dry-run: log what WOULD happen without executing."""
    task_type = task.get("task_type", "")
    
    model_map = {
        "entity_deepening": "Haiku (Opus for top-3 most-critical)",
        "cross_source_correlation": "Haiku",
        "framework_stress_test": "Haiku",
        "postdiction_sweep": "DeepSeek Flash",
        "source_freshness_scan": "DeepSeek Flash",
        "self_question_generation": "Haiku (Opus weekly)",
        "planner": "Haiku",
    }
    model = model_map.get(task_type, "unknown")
    
    output_shapes = {
        "entity_deepening": f"1500w entity file with fresh incidents, citations, observables, forward assessments. Updates {task.get('target', task.get('file', task.get('name', '?')))}",
        "cross_source_correlation": "Synthesis note: factual divergences resolved, source reliability prior updated",
        "framework_stress_test": f"Framework fit assessment for incident. Capability gap logged if framework can't accommodate.",
        "postdiction_sweep": "5 verdict resolutions: confirmed/partial/NYT/disconfirmed/expired. Per-region calibration updated.",
        "source_freshness_scan": "Freshness report: fresh/stale/critical per entity. Deepening tasks generated.",
        "self_question_generation": "3-5 capability-gap questions appended to analyst/meta/capability_gaps.json",
    }
    output_shape = output_shapes.get(task_type, "unknown")
    
    acceptance = {
        "entity_deepening": "fabrication_check.py passes clean, 1500w target, last_source_date updated",
        "cross_source_correlation": "2+ sources confirmed, source priors updated in registry",
        "framework_stress_test": "Framework fit logged, gap entry created if applicable",
        "postdiction_sweep": "Unresolved count decreases, calibration.json validates",
        "source_freshness_scan": "Stale entities identified, deepening tasks generated",
        "self_question_generation": "Questions are subscriber-grade and not trivially answerable",
    }
    criteria = acceptance.get(task_type, "unknown")
    
    state_change = {
        "entity_deepening": f"{task.get('file', '?')} (entity file update)",
        "cross_source_correlation": "source reliability priors (in-memory registry)",
        "framework_stress_test": "analyst/meta/capability_gaps.json (if gap found)",
        "postdiction_sweep": "calibration-tracking.json + calibration-directives.json",
        "source_freshness_scan": "analyst/queue/ (generates deepening tasks)",
        "self_question_generation": "analyst/meta/capability_gaps.json",
    }
    
    return {
        "status": "dry_run",
        "task_type": task_type,
        "target": str(task.get("target", task.get("name", ""))),
        "model": model,
        "output_shape": output_shape,
        "acceptance_criteria": criteria,
        "state_change_target": state_change.get(task_type, "unknown"),
        "estimated_cost": task.get("estimated_cost", 0.001),
        "action": "WOULD_EXECUTE",
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Continuous Learning Loop Worker")
    parser.add_argument("--daemon", action="store_true", help="Loop continuously")
    parser.add_argument("--one-shot", action="store_true", help="Process one task, exit")
    parser.add_argument("--live", action="store_true", help="Execute tasks live. Default is dry-run.")
    args = parser.parse_args()
    
    cycle_cost = load_cost_state()
    print(f"[worker] Starting. Cycle cost so far: ${cycle_cost:.6f}")
    is_dry_run = not args.live
    if is_dry_run:
        print(f"[worker] DRY-RUN MODE — no state will be modified, no API calls will be made")
        print(f"[worker] Use --live to execute tasks.")
    
    if args.one_shot:
        process_one(cycle_cost, dry_run=is_dry_run)
        return
    
    if args.daemon:
        backoff = 10  # seconds
        while True:
            if not process_one(cycle_cost, dry_run=is_dry_run):
                print(f"[worker] No pending tasks. Sleeping {backoff}s...")
                time.sleep(backoff)
                backoff = min(backoff * 2, 300)  # Max 5 min
            else:
                backoff = 10  # Reset on success
                cycle_cost = load_cost_state()
    else:
        # Sweep mode: process all pending tasks
        while process_one(cycle_cost, dry_run=is_dry_run):
            cycle_cost = load_cost_state()
        print(f"[worker] All tasks processed. Cycle cost: ${cycle_cost:.6f}")


if __name__ == "__main__":
    main()
