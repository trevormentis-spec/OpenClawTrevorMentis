#!/usr/bin/env python3
"""Planner — inspects system state, generates 5-15 tasks per cycle.

Runs every 30 minutes via cron or daemon loop. Reads state from:
- Entity file last_source_dates
- Postdiction outcomes
- Recent incident corpus
- Source registry
- Kalshi/Polymarket drift
- Yesterday's brief gap-flags
- Capability gap list

Output: task list at analyst/queue/<timestamp>.json
"""

from __future__ import annotations

import datetime
import json
import pathlib
import sys
import importlib
import time
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
TASKS_DIR = REPO_ROOT / "analyst" / "tasks"
QUEUE_DIR = REPO_ROOT / "analyst" / "queue"

STATE_FILE = REPO_ROOT / "brain" / "meta" / "planner-state.json"
CAL_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "calibration-tracking.json"
CAP_GAP_FILE = REPO_ROOT / "analyst" / "meta" / "capability_gaps.json"

# Task type modules — only load active ones
TASK_TYPES = [
    "entity_deepening",
    "cross_source_correlation",
    "framework_stress_test",
    "postdiction_sweep",
    "source_freshness_scan",
    "self_question_generation",
]

MAX_TASKS_PER_CYCLE = 15
MIN_TASKS_PER_CYCLE = 5


def load_state() -> dict[str, Any]:
    """Load planner state from file."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, Exception):
            pass
    return {
        "last_cycle": None,
        "cycle_count": 0,
        "tasks_generated_total": 0,
        "tasks_completed_total": 0,
        "last_self_question_date": "",
    }


def save_state(state: dict[str, Any]) -> None:
    """Save planner state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


def load_recent_incidents() -> list[dict[str, Any]]:
    """Load recent Mexico incidents.

    PRIMARY: reads from exports/mexico-news-scan-YYYY-MM-DD.json
    (Mexico-specific scan). FALLBACK: reads from ~/trevor-briefings/.../incidents.json
    and filters for Mexico relevance.
    """
    incidents: list[dict] = []
    
    # Primary path: Mexico scan output
    exports_dir = REPO_ROOT / "exports"
    if exports_dir.exists():
        scans = sorted(exports_dir.glob("mexico-news-scan-*.json"), reverse=True)
        if scans:
            try:
                data = json.loads(scans[0].read_text())
                # Normalize scan articles into incident format
                for source_result in data.get("results", []):
                    for art in source_result.get("articles", []):
                        headline = art.get("title", art.get("page_title", ""))
                        # Skip template variable artifacts (unrendered ${...})
                        if '${' in headline or '$' in headline[:3]:
                            continue
                        incidents.append({
                            "id": f"mx-scan-{len(incidents)+1}",
                            "region": "north_america",
                            "country": "Mexico",
                            "headline": headline,
                            "summary": art.get("summary", ""),
                            "sources": [{"name": source_result.get("name", "Mexico scan"), "url": art.get("url", "")}],
                            "category": art.get("type", "security"),
                            "source_scan": "mexico-daily-scan",
                        })
            except (json.JSONDecodeError, Exception) as e:
                print(f"[planner] Error reading Mexico scan: {e}", file=sys.stderr)
    
    # Fallback: try the pipeline incidents
    if not incidents:
        briefings_dir = pathlib.Path.home() / "trevor-briefings"
        if briefings_dir.exists():
            dated_dirs = sorted([d for d in briefings_dir.iterdir() if d.is_dir() and d.name.startswith('2026-')], reverse=True)
            if dated_dirs:
                pipeline_file = dated_dirs[0] / "raw" / "incidents.json"
                if pipeline_file.exists():
                    try:
                        data = json.loads(pipeline_file.read_text())
                        mx_kw = ['méxico', 'mexico', 'mexican', 'pemex', 'cfe', 'conagua', 'cenagas',
                                'sheinbaum', 'harfuch', 'banxico', 'mxn', 'usmca', 'peso',
                                'cartel', 'cjng', 'cds', 'sinaloa', 'michoacán', 'guanajuato', 'jalisco',
                                'queretaro', 'bajío', 'fentanyl', 'nearshore', 'morena', 'amlo', 'rocha',
                                'mencho', 'el pelón', 'huachicoleo']
                        for i in data.get("incidents", []):
                            if (i.get("country") == "Mexico" or
                                any(kw in (i.get('headline','') + i.get('summary','')).lower() for kw in mx_kw)):
                                i["source_scan"] = "pipeline-fallback"
                                incidents.append(i)
                    except Exception:
                        pass
    
    return incidents


def collect_task(task_type: str, state: dict[str, Any]) -> dict[str, Any] | None:
    """Call a task module's plan() function. Returns task spec or None."""
    try:
        sys.path.insert(0, str(REPO_ROOT))
        module_path = f"analyst.tasks.{task_type}"
        if task_type in sys.modules:
            module = importlib.reload(sys.modules[task_type])
        else:
            module = importlib.import_module(f"analyst.tasks.{task_type}")
        
        task_state = {
            "recent_incidents": load_recent_incidents(),
            "last_self_question_date": state.get("last_self_question_date", ""),
        }
        return module.plan(task_state)
    except Exception as exc:
        print(f"[planner] Error in {task_type}.plan(): {exc}", file=sys.stderr)
        return None


def prioritize_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort tasks by priority: high > medium > low."""
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(tasks, key=lambda t: priority_order.get(t.get("priority", "low"), 99))


def main() -> None:
    state = load_state()
    state["last_cycle"] = datetime.datetime.utcnow().isoformat() + "Z"
    state["cycle_count"] += 1
    
    tasks: list[dict[str, Any]] = []
    
    for task_type in TASK_TYPES:
        task = collect_task(task_type, state)
        if task:
            task["task_type"] = task_type
            task["generated_at"] = state["last_cycle"]
            task["status"] = "pending"
            tasks.append(task)
    
    # Ensure minimum number of tasks
    if len(tasks) < MIN_TASKS_PER_CYCLE:
        print(f"[planner] Only {len(tasks)} tasks — below minimum {MIN_TASKS_PER_CYCLE}", file=sys.stderr)
        # Add self-question generation as fallback
        if "self_question_generation" not in {t.get("task_type") for t in tasks}:
            try:
                sys.path.insert(0, str(REPO_ROOT))
                module = importlib.import_module("analyst.tasks.self_question_generation")
                task = module.plan(state)
                if task:
                    task["task_type"] = "self_question_generation"
                    task["generated_at"] = state["last_cycle"]
                    task["status"] = "pending"
                    tasks.append(task)
            except Exception:
                pass
    
    # Prioritize and trim
    tasks = prioritize_tasks(tasks)[:MAX_TASKS_PER_CYCLE]
    
    if not tasks:
        print("[planner] No tasks generated this cycle.")
        save_state(state)
        return
    
    # Write tasks to queue
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    queue_file = QUEUE_DIR / f"{timestamp}.json"
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    
    output = {
        "cycle": state["cycle_count"],
        "generated_at": state["last_cycle"],
        "task_count": len(tasks),
        "tasks": tasks,
    }
    
    queue_file.write_text(json.dumps(output, indent=2, default=str))
    state["tasks_generated_total"] += len(tasks)
    save_state(state)
    
    print(f"[planner] Cycle {state['cycle_count']}: {len(tasks)} tasks → {queue_file}")
    for t in tasks:
        print(f"  [{t.get('priority','low')}] {t.get('task_type','?')}: {t.get('target','?')}")


if __name__ == "__main__":
    main()
