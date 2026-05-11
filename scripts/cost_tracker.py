#!/usr/bin/env python3
"""
cost_tracker.py — Session cost tracking for Trevor.

Parses session activity, estimates token usage, and computes cost
based on model pricing. Writes daily rollup to exports/session-costs.json.

Usage:
    python3 scripts/cost_tracker.py                # Today's cost rollup
    python3 scripts/cost_tracker.py --days 7       # Last 7 days
    python3 scripts/cost_tracker.py --snapshot     # Record a cost snapshot
    python3 scripts/cost_tracker.py --status       # Show current balance info
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import datetime

REPO = pathlib.Path(__file__).resolve().parent.parent
EXPORTS = REPO / "exports"
EPISODIC_DIR = REPO / "brain" / "memory" / "episodic"
COST_LOG = EXPORTS / "session-costs.json"

# DeepSeek pricing (per 1M tokens)
PRICING = {
    "deepseek/deepseek-v4-flash": {"input": 0.14, "output": 0.28},
    "deepseek/deepseek-v4-pro": {"input": 0.435, "output": 0.87},
    "deepseek/deepseek-chat": {"input": 0.14, "output": 0.28},
    "anthropic/claude-opus-4.7": {"input": 15.00, "output": 75.00},
    "default": {"input": 1.00, "output": 2.00},
}

# Estimated token ratios
CHARS_PER_TOKEN_INPUT = 4
CHARS_PER_TOKEN_OUTPUT = 5
TOOL_OVERHEAD = 0.3  # 30% overhead for system prompts, tool schemas


def get_pricing(model: str) -> dict:
    """Get pricing for a model, falling back to defaults."""
    for key in PRICING:
        if key in model:
            return PRICING[key]
    return PRICING["default"]


def estimate_session_cost(lines: list[dict], model: str) -> dict:
    """Estimate token usage and cost for a session from episodic log lines."""
    total_input_chars = 0
    total_output_chars = 0
    tool_calls = 0
    user_messages = 0
    assistant_messages = 0
    
    for line in lines:
        content = str(line.get("content", line.get("text", "")))
        role = str(line.get("role", line.get("type", "")))
        
        if "user" in role.lower():
            total_input_chars += len(content)
            user_messages += 1
        elif "assistant" in role.lower() or "model" in role.lower():
            total_output_chars += len(content)
            assistant_messages += 1
        
        if "tool" in role.lower() or "function" in role.lower():
            total_input_chars += len(content)
            tool_calls += 1
    
    # Estimate tokens
    input_tokens = int(total_input_chars / CHARS_PER_TOKEN_INPUT * (1 + TOOL_OVERHEAD))
    output_tokens = int(total_output_chars / CHARS_PER_TOKEN_OUTPUT)
    
    # Apply pricing
    pricing = get_pricing(model)
    input_cost = input_tokens / 1_000_000 * pricing["input"]
    output_cost = output_tokens / 1_000_000 * pricing["output"]
    total_cost = round(input_cost + output_cost, 4)
    
    return {
        "model": model,
        "estimated_input_tokens": input_tokens,
        "estimated_output_tokens": output_tokens,
        "input_cost": round(input_cost, 4),
        "output_cost": round(output_cost, 4),
        "total_cost": total_cost,
        "message_count": user_messages + assistant_messages,
        "tool_call_count": tool_calls,
    }


def scan_recent_sessions(days: int = 1) -> list[dict]:
    """Scan episodic logs for recent session data."""
    today = datetime.date.today()
    sessions = []
    
    # Look at today's files
    for day_offset in range(days):
        check_date = today - datetime.timedelta(days=day_offset)
        for f in sorted(EPISODIC_DIR.glob("*.jsonl"), reverse=True):
            try:
                lines = [json.loads(l) for l in f.read_text().strip().split("\n") if l]
                if lines:
                    sessions.append({
                        "file": f.name,
                        "date": check_date.isoformat(),
                        "lines": lines,
                        "model": detect_model(lines),
                    })
            except:
                pass
            if len(sessions) >= 5:  # cap at 5 files per day
                break
        if len(sessions) >= 20:  # overall cap
            break
    
    return sessions


def detect_model(lines: list[dict]) -> str:
    """Try to detect which model was used from the session content."""
    for line in lines:
        content = str(line.get("content", ""))
        if "deepseek-v4-flash" in content or "deepseek-v4-flash" in str(line):
            return "deepseek/deepseek-v4-flash"
        if "deepseek-v4-pro" in content or "deepseek-v4-pro" in str(line):
            return "deepseek/deepseek-v4-pro"
        if "claude-opus-4.7" in content:
            return "anthropic/claude-opus-4.7"
    return "deepseek/deepseek-v4-flash"


def daily_rollup(days: int = 1) -> dict:
    """Produce a cost rollup for the specified number of days."""
    sessions = scan_recent_sessions(days)
    
    total_cost = 0.0
    total_input_tokens = 0
    total_output_tokens = 0
    total_tool_calls = 0
    total_messages = 0
    model_costs = {}
    daily_costs = {}
    
    for session in sessions:
        cost = estimate_session_cost(session["lines"], session["model"])
        total_cost += cost["total_cost"]
        total_input_tokens += cost["estimated_input_tokens"]
        total_output_tokens += cost["estimated_output_tokens"]
        total_tool_calls += cost["tool_call_count"]
        total_messages += cost["message_count"]
        
        model = session["model"]
        model_costs[model] = model_costs.get(model, 0) + cost["total_cost"]
        
        date = session["date"]
        daily_costs[date] = daily_costs.get(date, 0) + cost["total_cost"]
    
    return {
        "generated": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "period_days": days,
        "total_cost_usd": round(total_cost, 4),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_tool_calls": total_tool_calls,
        "total_messages": total_messages,
        "avg_cost_per_session": round(total_cost / max(len(sessions), 1), 4),
        "by_model": model_costs,
        "by_day": daily_costs,
        "session_count": len(sessions),
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Session cost tracker")
    parser.add_argument("--days", type=int, default=1, help="Number of days to roll up")
    parser.add_argument("--snapshot", action="store_true", help="Record a cost snapshot")
    parser.add_argument("--status", action="store_true", help="Show current cost info")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    if args.status:
        if COST_LOG.exists():
            data = json.loads(COST_LOG.read_text())
            print(f"Last snapshot: {data.get('generated', '?')}")
            print(f"Total cost (period): ${data.get('total_cost_usd', 0):.4f}")
            print(f"By model: {json.dumps(data.get('by_model', {}), indent=2)}")
            print(f"Session count: {data.get('session_count', 0)}")
        else:
            print("No cost data yet. Run with --snapshot to record.")
        return 0
    
    rollup = daily_rollup(args.days)
    
    if args.snapshot:
        COST_LOG.parent.mkdir(parents=True, exist_ok=True)
        COST_LOG.write_text(json.dumps(rollup, indent=2))
        print(f"[cost] Snapshot saved to {COST_LOG}")
    
    if args.json:
        print(json.dumps(rollup, indent=2))
    else:
        print(f"📊 Session Cost Rollup — Last {args.days} day(s)")
        print(f"{'='*50}")
        print(f"Total cost:        ${rollup['total_cost_usd']:.4f}")
        print(f"Input tokens:      {rollup['total_input_tokens']:,}")
        print(f"Output tokens:     {rollup['total_output_tokens']:,}")
        print(f"Tool calls:        {rollup['total_tool_calls']}")
        print(f"Messages:          {rollup['total_messages']}")
        print(f"Sessions scanned:  {rollup['session_count']}")
        print(f"Avg cost/session:  ${rollup['avg_cost_per_session']:.4f}")
        if rollup['by_model']:
            print(f"\nBy model:")
            for m, c in rollup['by_model'].items():
                print(f"  {m}: ${c:.4f}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
