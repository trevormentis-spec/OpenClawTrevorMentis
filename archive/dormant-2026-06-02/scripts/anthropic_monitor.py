#!/usr/bin/env python3
"""
Anthropic Monitor — Trevor

Tracks Opus 4.8 credit usage to stay within the $100 budget.
Monitors spend, estimates remaining runway, and warns on thresholds.

Usage:
  python3 scripts/anthropic_monitor.py           # Full dashboard
  python3 scripts/anthropic_monitor.py --snapshot # Record and save
  python3 scripts/anthropic_monitor.py --alert    # Check thresholds only
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

REPO = Path(__file__).resolve().parent.parent
STATE_FILE = REPO / "brain" / "memory" / "semantic" / "anthropic-usage.json"
ALERT_STATE = REPO / "tasks" / "infra-alert-state.json"

# ── Budget ────────────────────────────────────────────────────────────
TOTAL_BUDGET = 100.00  # $100 credit
WARN_THRESHOLD = 0.80   # Alert when 80% consumed
CRITICAL_THRESHOLD = 0.95  # Alert when 95% consumed

# Opus 4.8 pricing (per million tokens)
OPUS_INPUT_COST_PER_M = 15.0    # ~$15/M input
OPUS_OUTPUT_COST_PER_M = 75.0   # ~$75/M output
OPUS_CACHE_READ_PER_M = 7.50    # ~50% of input
OPUS_CACHE_WRITE_PER_M = 18.75  # 125% of input

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def load_state() -> dict:
    if STATE_FILE.exists() and STATE_FILE.stat().st_size > 0:
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"total_spent": 0.0, "calls": [], "balance": TOTAL_BUDGET}

def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))

def compute_cost(input_tokens: int, output_tokens: int,
                 cache_read: int = 0, cache_write: int = 0) -> float:
    """Compute cost in dollars for a single API call."""
    input_cost = (input_tokens / 1_000_000) * OPUS_INPUT_COST_PER_M
    output_cost = (output_tokens / 1_000_000) * OPUS_OUTPUT_COST_PER_M
    cache_read_cost = (cache_read / 1_000_000) * OPUS_CACHE_READ_PER_M
    cache_write_cost = (cache_write / 1_000_000) * OPUS_CACHE_WRITE_PER_M
    return round(input_cost + output_cost + cache_read_cost + cache_write_cost, 6)

def record_call(input_tokens: int, output_tokens: int,
                cache_read: int = 0, cache_write: int = 0,
                route: str = "") -> None:
    """Record an Opus API call and update total spend."""
    cost = compute_cost(input_tokens, output_tokens, cache_read, cache_write)
    state = load_state()
    state["calls"].append({
        "ts": now_iso(),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read": cache_read,
        "cache_write": cache_write,
        "cost": cost,
        "route": route,
    })
    # Keep last 10,000 calls
    state["calls"] = state["calls"][-10000:]
    state["total_spent"] = round(sum(c["cost"] for c in state["calls"]), 6)
    state["balance"] = round(TOTAL_BUDGET - state["total_spent"], 6)
    state["last_updated"] = now_iso()
    save_state(state)

def get_estimated_remaining_calls(state: dict, avg_cost_per_call: float | None = None) -> dict:
    """Estimate remaining calls based on recent average."""
    calls = state.get("calls", [])
    if len(calls) < 5:
        return {"estimate": "insufficient_data", "calls_per_dollar": None}

    if avg_cost_per_call is None:
        recent = calls[-20:] if len(calls) >= 20 else calls
        avg_cost = sum(c["cost"] for c in recent) / len(recent)
    else:
        avg_cost = avg_cost_per_call

    remaining = state.get("balance", TOTAL_BUDGET)
    if avg_cost > 0:
        est_calls = int(remaining / avg_cost)
    else:
        est_calls = None

    return {
        "avg_cost_per_call": round(avg_cost, 6),
        "estimated_remaining_calls": est_calls,
        "remaining_balance": remaining,
    }

def check_thresholds(state: dict) -> list[str]:
    """Check budget thresholds and return alert messages."""
    alerts = []
    balance = state.get("balance", TOTAL_BUDGET)
    spent = state.get("total_spent", 0.0)
    usage_pct = spent / TOTAL_BUDGET if TOTAL_BUDGET > 0 else 0

    if usage_pct >= CRITICAL_THRESHOLD:
        alerts.append(f"🔴 CRITICAL: Opus budget {usage_pct:.0%} consumed. ${balance:.2f} remaining.")
    elif usage_pct >= WARN_THRESHOLD:
        alerts.append(f"🟡 WARNING: Opus budget {usage_pct:.0%} consumed. ${balance:.2f} remaining.")

    if balance < 1.0:
        alerts.append(f"🔴 Opus balance below $1.00. Service degradation imminent.")

    return alerts

def run_dashboard() -> None:
    state = load_state()
    calls = state.get("calls", [])
    total_spent = state.get("total_spent", 0.0)
    balance = state.get("balance", TOTAL_BUDGET)
    usage_pct = total_spent / TOTAL_BUDGET * 100 if TOTAL_BUDGET > 0 else 0

    # Breakdown by route
    routes: dict[str, dict] = {}
    for c in calls:
        route = c.get("route", "unknown")
        if route not in routes:
            routes[route] = {"calls": 0, "tokens_in": 0, "tokens_out": 0, "cost": 0.0}
        routes[route]["calls"] += 1
        routes[route]["tokens_in"] += c.get("input_tokens", 0)
        routes[route]["tokens_out"] += c.get("output_tokens", 0)
        routes[route]["cost"] += c.get("cost", 0)

    print("=" * 60)
    print(f"  Anthropic Opus 4.8 — Usage Dashboard")
    print(f"  {now_iso()}")
    print("=" * 60)
    print(f"  Budget:      ${TOTAL_BUDGET:.2f}")
    print(f"  Spent:       ${total_spent:.4f}")
    print(f"  Remaining:   ${balance:.2f}")
    print(f"  Used:        {usage_pct:.1f}%")
    print(f"  Total calls: {len(calls)}")
    print()

    if calls:
        # Last 5 calls
        print("  Last 5 calls:")
        for c in calls[-5:]:
            cost = c.get("cost", 0)
            ts = c.get("ts", "")[11:19]
            route = c.get("route", "")
            inp = c.get("input_tokens", 0)
            out = c.get("output_tokens", 0)
            print(f"    {ts} | {cost:>8.6f} | {inp:>6} in / {out:<6} out | {route}")
        print()

    # Route breakdown
    if routes:
        print("  By route:")
        for route, data in sorted(routes.items(), key=lambda x: -x[1]["cost"]):
            pct = data["cost"] / total_spent * 100 if total_spent > 0 else 0
            print(f"    {route:<25} {data['calls']:>4} calls | ${data['cost']:.4f} ({pct:.0f}%)")
        print()

    # Estimate
    est = get_estimated_remaining_calls(state)
    if est.get("estimated_remaining_calls"):
        print(f"  Est. remaining calls: ~{est['estimated_remaining_calls']}")
        print(f"  Avg cost per call:    ${est['avg_cost_per_call']:.6f}")
    print("=" * 60)

    # Alerts
    alerts = check_thresholds(state)
    for a in alerts:
        print(f"\n  {a}")

if __name__ == "__main__":
    if "--snapshot" in sys.argv:
        run_dashboard()
        print("\n📸 Snapshot recorded")
    elif "--alert" in sys.argv:
        state = load_state()
        alerts = check_thresholds(state)
        for a in alerts:
            print(a)
        if not alerts:
            print("Opus budget OK")
    else:
        run_dashboard()
