#!/usr/bin/env python3
"""
Opus Router — Trevor's Surgical Model Selector

Routes tasks to the appropriate model based on task complexity.
DeepSeek Flash for throughput. Opus 4.8 for quality, autonomy, and code.

This is the budget discipline layer. Every Opus call is intentional.

Usage:
  python3 scripts/opus_router.py --classify <task-description>
  python3 scripts/opus_router.py --report
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

REPO = Path(__file__).resolve().parent.parent
STATE_FILE = REPO / "brain" / "memory" / "semantic" / "opus-routing-log.json"

# ── Opus-Only Tasks (must go through Opus 4.8) ─────────────────────
OPUS_REQUIRED_KEYWORDS = [
    # Control plane & autonomy
    "control plane", "reliability audit", "recovery diagnosis",
    "gateway failure", "root cause analysis",
    "self-diagnostic", "self-improvement",

    # Quality gates (critical)
    "quality gate", "fabrication check", "scope check",
    "red team", "adversarial review", "forced dissent",
    "calibration review",

    # Code generation & architecture
    "generate code", "build script", "create cron",
    "architecture decision", "migration plan",
    "refactor", "rewrite module",

    # Strategic decisions
    "strategy evaluation", "trade-off analysis",
    "risk assessment", "recommendation",
]

# ── DeepSeek Tasks (never send to Opus) ────────────────────────────
DEEPSEEK_ONLY_KEYWORDS = [
    # Collection
    "collect", "fetch rss", "scrape", "scan feeds",
    "news scan", "source collection",

    # Routine analysis
    "daily brief", "summarize", "translate",
    "watchlist", "digest",

    # Trading signals
    "signal scan", "market scan", "kalshi scan",
]

# ── Opus Recommended Tasks (strongly prefer Opus but not required) ──
OPUS_RECOMMENDED_KEYWORDS = [
    "deep analysis", "synthesis", "assessment",
    "calibration", "prediction", "judgment call",
    "analyst note", "analytic workflow",
    "brief quality", "quality review",
    "qc", "quality control",
    "report generation", "intelligence product",
    "strategy", "allocation decision",
]

# ── Classification ─────────────────────────────────────────────────

class RouteDecision:
    """Result of routing classification."""
    def __init__(self, model: str, reason: str, confidence: float = 1.0):
        self.model = model  # "opus" | "deepseek" | "deepseek-pro"
        self.reason = reason
        self.confidence = confidence
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def __repr__(self) -> str:
        return f"Route: {self.model} ({self.reason})"

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "reason": self.reason,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }


def classify(task: str) -> RouteDecision:
    """Classify a task by description and return routing decision."""
    task_lower = task.lower()

    # Check Opus-required tasks first
    for kw in OPUS_REQUIRED_KEYWORDS:
        if kw in task_lower:
            return RouteDecision(
                model="opus",
                reason=f"Opus-required keyword matched: '{kw}'",
                confidence=0.95
            )

    # Check DeepSeek-only tasks
    for kw in DEEPSEEK_ONLY_KEYWORDS:
        if kw in task_lower:
            return RouteDecision(
                model="deepseek",
                reason=f"DeepSeek-only keyword matched: '{kw}'",
                confidence=0.95
            )

    # Check Opus-recommended
    for kw in OPUS_RECOMMENDED_KEYWORDS:
        if kw in task_lower:
            return RouteDecision(
                model="opus",
                reason=f"Opus-recommended keyword matched: '{kw}'",
                confidence=0.75
            )

    # Default: DeepSeek Flash (always the default workhorse)
    return RouteDecision(
        model="deepseek",
        reason="No Opus trigger matched — defaulting to DeepSeek Flash",
        confidence=0.6
    )


# ── Budget check ────────────────────────────────────────────────────

def check_budget() -> dict:
    """Check if we have Opus budget remaining."""
    from anthropic_monitor import load_state, check_thresholds
    state = load_state()
    balance = state.get("balance", 100.0)
    alerts = check_thresholds(state)
    return {
        "remaining": balance,
        "has_budget": balance > 1.0,
        "alerts": alerts,
        "critical": balance < 0.50,
    }


def should_route_to_opus(task: str) -> bool:
    """Full routing decision including budget check."""
    decision = classify(task)

    if decision.model != "opus":
        return False

    # Check budget before routing to Opus
    budget = check_budget()
    if not budget.get("has_budget"):
        print(f"[opus_router] ❌ Budget insufficient (${budget['remaining']:.2f}) — falling back to DeepSeek")
        log_route(task, "deepseek", f"Budget exhausted — ${budget['remaining']:.2f} remaining")
        return False

    log_route(task, "opus", decision.reason)
    return True


# ── Logging ─────────────────────────────────────────────────────────

def log_route(task: str, model: str, reason: str) -> None:
    """Log a routing decision."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task": task[:200],
        "model": model,
        "reason": reason,
    }

    logs = []
    if STATE_FILE.exists():
        try:
            logs = json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            logs = []

    logs.append(entry)
    logs = logs[-5000:]  # Keep last 5000

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(logs, indent=2, default=str))


def print_report() -> None:
    """Print routing report."""
    if not STATE_FILE.exists():
        print("No routing data yet.")
        return

    try:
        logs = json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        print("No routing data yet.")
        return

    if not logs:
        print("No routing data yet.")
        return

    total = len(logs)
    opus_calls = sum(1 for l in logs if l.get("model") == "opus")
    deepseek_calls = sum(1 for l in logs if l.get("model") == "deepseek")
    recent = [l for l in logs if l.get("timestamp", "")[:10] == datetime.now(timezone.utc).strftime("%Y-%m-%d")]

    print(f"  Opus Router — Routing Report")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print(f"  Total routed: {total}")
    print(f"  Opus:         {opus_calls} ({opus_calls/total*100:.0f}%)" if total > 0 else "")
    print(f"  DeepSeek:     {deepseek_calls} ({deepseek_calls/total*100:.0f}%)" if total > 0 else "")
    print(f"  Today:        {len(recent)} calls")

    if opus_calls > 0:
        print(f"\n  Last Opus calls:")
        for l in logs[-5:]:
            if l.get("model") == "opus":
                ts = l.get("timestamp", "")[11:19]
                print(f"    {ts} | {l.get('reason', '')[:60]}")

    print(f"\n  Recent DeepSeek calls:")
    for l in logs[-5:]:
        if l.get("model") == "deepseek":
            ts = l.get("timestamp", "")[11:19]
            print(f"    {ts} | {l.get('reason', '')[:60]}")


# ── CLI ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--classify" in sys.argv:
        idx = sys.argv.index("--classify") + 1
        if idx < len(sys.argv):
            task = sys.argv[idx]
            decision = classify(task)
            print(f"Task: {task}")
            print(f"Route: {decision.model}")
            print(f"Reason: {decision.reason}")
            print(f"Confidence: {decision.confidence}")
        else:
            print("Usage: --classify <task-description>")

    elif "--report" in sys.argv or "-r" in sys.argv:
        print_report()

    elif "--should-route" in sys.argv:
        idx = sys.argv.index("--should-route") + 1
        if idx < len(sys.argv):
            task = sys.argv[idx]
            result = should_route_to_opus(task)
            print(f"true" if result else "false")
        else:
            print("false")

    else:
        # Test mode - classify some sample tasks
        tests = [
            "quality gate — verify brief integrity",
            "collect RSS feeds for South America",
            "daily brief production",
            "control plane recovery diagnosis",
            "kalshi market scan",
            "fabrication check for intel product",
            "generate code for Telegram bot sidecar",
            "trade recommendation allocation decision",
            "source collection for LEO",
            "red team review of analytic methodology",
        ]
        print("Opus Router — Classification Tests")
        print("=" * 60)
        for t in tests:
            d = classify(t)
            badge = "🟢 DeepSeek" if d.model == "deepseek" else "🔴 OPUS"
            print(f"  {badge} | {t:<50} | {d.reason[:50]}")
        print("=" * 60)
