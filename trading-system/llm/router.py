#!/usr/bin/env python3
"""
LLM Router — Opus 4.8 vs DeepSeek Flash Route Selection

Routes tasks to the appropriate model based on:
- Task complexity / stakes
- Budget remaining ($98.05 Opus remaining)
- Frequency (never call Opus in a trading loop)

This is the budget discipline layer. Every Opus call is intentional.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent.parent
ANTHROPIC_MONITOR_FILE = REPO / "brain" / "memory" / "semantic" / "anthropic-usage.json"
ROUTING_LOG = REPO / "trading-system" / "llm" / "routing_log.jsonl"


class LLMRouter:
    """Routes tasks to Opus or DeepSeek based on complexity and budget."""

    # Tasks that ALWAYS use Opus
    OPUS_REQUIRED_KEYWORDS = [
        "conflict arbitration", "tiebreaker",
        "regime break", "regime_change",
        "post-mortem", "postmortem",
        "strategic assessment",
        "architecture decision",
        "kill switch", "halt review",
        "calibration review",
    ]

    # Tasks that NEVER use Opus (use DeepSeek Flash)
    DEEPSEEK_ONLY_KEYWORDS = [
        "scan market", "market scan",
        "fetch", "collect", "poll",
        "log triage", "routine check",
        "heartbeat",
    ]

    def __init__(self):
        self.daily_opus_count = 0
        self.daily_date = ""
        self._load_state()

    def _load_state(self):
        """Load daily Opus call count."""
        from datetime import date
        today = str(date.today())
        entries = self._load_log()
        self.daily_opus_count = sum(
            1 for e in entries
            if e.get("model") == "opus" and e.get("timestamp", "").startswith(today)
        )
        self.daily_date = today

    def _load_log(self) -> list[dict]:
        if not ROUTING_LOG.exists():
            return []
        entries = []
        with open(ROUTING_LOG) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return entries

    def _log_route(self, task: str, model: str, reason: str):
        ROUTING_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = json.dumps({
            "timestamp": __import__('intel.models', fromlist=['']).now_iso(),
            "task": task[:200],
            "model": model,
            "reason": reason,
        })
        with open(ROUTING_LOG, "a") as f:
            f.write(entry + "\n")

    def _get_opus_remaining(self) -> float:
        """Get remaining Opus budget."""
        if ANTHROPIC_MONITOR_FILE.exists():
            try:
                state = json.loads(ANTHROPIC_MONITOR_FILE.read_text())
                return state.get("balance", 0.0)
            except (json.JSONDecodeError, OSError):
                pass
        return 0.0

    def route(self, task: str) -> str:
        """Route a task to the appropriate model.

        Returns: "opus" or "deepseek-flash" or "deepseek-pro"
        """
        task_lower = task.lower()

        # Check Opus-required tasks
        for kw in self.OPUS_REQUIRED_KEYWORDS:
            if kw in task_lower:
                remaining = self._get_opus_remaining()
                if remaining < 1.0:
                    self._log_route(task, "deepseek-pro",
                                    f"Opus required ({kw}) but budget exhausted (${remaining:.2f})")
                    return "deepseek-pro"
                if self.daily_opus_count >= 30:
                    self._log_route(task, "deepseek-pro",
                                    f"Opus required ({kw}) but daily limit reached (30)")
                    return "deepseek-pro"

                self._log_route(task, "opus", f"Opus-required: '{kw}'")
                return "opus"

        # Check DeepSeek-only tasks
        for kw in self.DEEPSEEK_ONLY_KEYWORDS:
            if kw in task_lower:
                self._log_route(task, "deepseek-flash", f"DeepSeek-only: '{kw}'")
                return "deepseek-flash"

        # Default: DeepSeek Flash for everything routine
        self._log_route(task, "deepseek-flash", "default routing")
        return "deepseek-flash"

    def should_use_opus_for(self, task: str, force: bool = False) -> bool:
        """Check if a specific task should use Opus.

        Used for explicit calls where the caller knows it needs Opus
        but wants to respect budget limits.
        """
        if force:
            return True

        remaining = self._get_opus_remaining()
        if remaining < 1.0:
            return False
        if self.daily_opus_count >= 30:
            return False

        return True

    def report(self) -> dict:
        """Get routing statistics."""
        entries = self._load_log()
        total = len(entries)
        opus_count = sum(1 for e in entries if e.get("model") == "opus")
        ds_flash = sum(1 for e in entries if e.get("model") == "deepseek-flash")
        ds_pro = sum(1 for e in entries if e.get("model") == "deepseek-pro")
        opus_remaining = self._get_opus_remaining()

        return {
            "total_routed": total,
            "opus": opus_count,
            "deepseek_flash": ds_flash,
            "deepseek_pro": ds_pro,
            "opus_remaining": round(opus_remaining, 2),
            "daily_opus_used": self.daily_opus_count,
            "daily_opus_limit": 30,
        }
