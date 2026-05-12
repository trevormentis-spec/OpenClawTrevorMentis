#!/usr/bin/env python3
"""
trevor_cost.py — Session cost tracking for Trevor.

Estimates token usage from episodic logs, applies DeepSeek pricing,
and writes daily rollup. Lightweight, file-based, no external deps.

Usage:
    from trevor_cost import CostTracker
    ct = CostTracker()
    ct.snapshot()
    ct.summary()
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent
COST_LOG = SKILL_ROOT / "cron_tracking" / "session-costs.json"

# DeepSeek pricing per 1M tokens
PRICING = {
    "deepseek/deepseek-v4-flash": {"input": 0.14, "output": 0.28},
    "deepseek/deepseek-v4-pro": {"input": 0.435, "output": 0.87},
    "deepseek/deepseek-chat": {"input": 0.14, "output": 0.28},
    "default": {"input": 1.00, "output": 2.00},
}


class CostTracker:
    """Lightweight cost tracking."""

    def __init__(self):
        self.log_path = COST_LOG

    def snapshot(self, input_tokens: int = 0, output_tokens: int = 0,
                 model: str = "deepseek/deepseek-v4-flash",
                 tool_calls: int = 0, messages: int = 0) -> dict:
        """Record a cost snapshot."""
        pricing = PRICING.get(model, PRICING["default"])
        input_cost = input_tokens / 1_000_000 * pricing["input"]
        output_cost = output_tokens / 1_000_000 * pricing["output"]

        entry = {
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(input_cost + output_cost, 6),
            "tool_calls": tool_calls,
            "messages": messages,
        }

        if self.log_path.exists():
            data = json.loads(self.log_path.read_text())
        else:
            data = {"snapshots": [], "total_cost": 0.0}

        data["snapshots"].append(entry)
        data["total_cost"] = round(data["total_cost"] + entry["total_cost"], 4)
        data["updated_at"] = entry["timestamp"]
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.write_text(json.dumps(data, indent=2))

        return entry

    def summary(self) -> dict:
        """Return cost summary across all snapshots."""
        if not self.log_path.exists():
            return {"total_cost": 0.0, "snapshot_count": 0}

        data = json.loads(self.log_path.read_text())
        snapshots = data.get("snapshots", [])
        model_breakdown = {}
        for s in snapshots:
            model = s.get("model", "unknown")
            model_breakdown[model] = model_breakdown.get(model, 0) + s.get("total_cost", 0)

        return {
            "total_cost": data.get("total_cost", 0.0),
            "snapshot_count": len(snapshots),
            "by_model": model_breakdown,
            "updated_at": data.get("updated_at", ""),
        }
