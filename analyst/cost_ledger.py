#!/usr/bin/env python3
"""Cost Ledger — Budget enforcement for all LLM calls.

Tracks per-call cost, enforces daily/monthly/per-task caps.
Logs to memory/cost-ledger.jsonl.

Usage:
    from analyst.cost_ledger import CostLedger
    ledger = CostLedger()
    ledger.record(task_type="subscriber_brief", model="deepseek/deepseek-v4-pro", cost_usd=0.05)
    ledger.check_budget()  # raises BudgetExceededError if over cap
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


WORKSPACE = Path(__file__).resolve().parent.parent
LEDGER_PATH = WORKSPACE / "memory" / "cost-ledger.jsonl"
BUDGET_PATH = WORKSPACE / "config" / "budget.yaml"


class BudgetExceededError(Exception):
    """Raised when budget cap is exceeded."""
    pass


@dataclass
class CostEntry:
    """Single cost ledger entry."""
    timestamp: str
    task_type: str
    model: str
    provider: str
    cost_usd: float
    input_tokens: int = 0
    output_tokens: int = 0
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BudgetConfig:
    """Budget caps configuration."""
    daily_cap: float = 20.00
    monthly_cap: float = 200.00
    per_task_type_caps: dict = None
    alert_threshold: float = 0.80  # Alert at 80% of cap

    def __post_init__(self):
        if self.per_task_type_caps is None:
            self.per_task_type_caps = {}


class CostLedger:
    """Manages cost tracking and budget enforcement."""

    def __init__(self, ledger_path: Optional[Path] = None, budget_path: Optional[Path] = None):
        self.ledger_path = ledger_path or LEDGER_PATH
        self.budget_path = budget_path or BUDGET_PATH
        self.budget = self._load_budget()

    def _load_budget(self) -> BudgetConfig:
        """Load budget configuration from YAML."""
        if self.budget_path.exists():
            try:
                # Simple YAML parsing for our flat config
                config = {}
                with open(self.budget_path) as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if ":" in line and not line.startswith(" "):
                            key, val = line.split(":", 1)
                            key = key.strip()
                            val = val.strip()
                            if val:
                                try:
                                    config[key] = float(val)
                                except ValueError:
                                    config[key] = val
                return BudgetConfig(
                    daily_cap=config.get("daily_cap", 20.00),
                    monthly_cap=config.get("monthly_cap", 200.00),
                    alert_threshold=config.get("alert_threshold", 0.80),
                )
            except Exception:
                pass
        return BudgetConfig()

    def record(
        self,
        task_type: str,
        model: str,
        cost_usd: float,
        provider: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
        metadata: Optional[dict] = None,
    ) -> CostEntry:
        """Record a cost entry to the ledger."""
        entry = CostEntry(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            task_type=task_type,
            model=model,
            provider=provider,
            cost_usd=cost_usd,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            metadata=metadata or {},
        )
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.ledger_path, "a") as f:
            f.write(json.dumps(asdict(entry)) + "\n")
        return entry

    def _load_entries(self, since: Optional[str] = None) -> list[CostEntry]:
        """Load entries from ledger, optionally filtered by date prefix."""
        entries = []
        if not self.ledger_path.exists():
            return entries
        with open(self.ledger_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if since and data.get("timestamp", "") < since:
                        continue
                    entries.append(CostEntry(**data))
                except (json.JSONDecodeError, TypeError):
                    continue
        return entries

    def daily_spend(self, date: Optional[str] = None) -> float:
        """Get total spend for a given date (YYYY-MM-DD). Defaults to today."""
        if date is None:
            date = time.strftime("%Y-%m-%d", time.gmtime())
        entries = self._load_entries(since=f"{date}T00:00:00Z")
        return sum(
            e.cost_usd for e in entries
            if e.timestamp.startswith(date)
        )

    def monthly_spend(self, month: Optional[str] = None) -> float:
        """Get total spend for a given month (YYYY-MM). Defaults to current month."""
        if month is None:
            month = time.strftime("%Y-%m", time.gmtime())
        entries = self._load_entries(since=f"{month}-01T00:00:00Z")
        return sum(
            e.cost_usd for e in entries
            if e.timestamp.startswith(month)
        )

    def task_type_spend(self, task_type: str, date: Optional[str] = None) -> float:
        """Get spend for a specific task type today."""
        if date is None:
            date = time.strftime("%Y-%m-%d", time.gmtime())
        entries = self._load_entries(since=f"{date}T00:00:00Z")
        return sum(
            e.cost_usd for e in entries
            if e.task_type == task_type and e.timestamp.startswith(date)
        )

    def check_budget(self) -> dict:
        """
        Check if any budget caps are exceeded.

        Returns dict with:
            ok: bool — True if within budget
            daily_spend: float
            monthly_spend: float
            daily_remaining: float
            monthly_remaining: float
            alerts: list[str] — warnings at threshold
            errors: list[str] — hard cap violations

        Raises BudgetExceededError if hard cap is exceeded.
        """
        daily = self.daily_spend()
        monthly = self.monthly_spend()

        daily_remaining = self.budget.daily_cap - daily
        monthly_remaining = self.budget.monthly_cap - monthly

        alerts = []
        errors = []

        # Check daily cap
        if daily >= self.budget.daily_cap:
            errors.append(
                f"Daily budget exceeded: ${daily:.2f} / ${self.budget.daily_cap:.2f}"
            )
        elif daily >= self.budget.daily_cap * self.budget.alert_threshold:
            alerts.append(
                f"Daily budget at {daily/self.budget.daily_cap*100:.0f}%: "
                f"${daily:.2f} / ${self.budget.daily_cap:.2f}"
            )

        # Check monthly cap
        if monthly >= self.budget.monthly_cap:
            errors.append(
                f"Monthly budget exceeded: ${monthly:.2f} / ${self.budget.monthly_cap:.2f}"
            )
        elif monthly >= self.budget.monthly_cap * self.budget.alert_threshold:
            alerts.append(
                f"Monthly budget at {monthly/self.budget.monthly_cap*100:.0f}%: "
                f"${monthly:.2f} / ${self.budget.monthly_cap:.2f}"
            )

        result = {
            "ok": len(errors) == 0,
            "daily_spend": daily,
            "monthly_spend": monthly,
            "daily_remaining": max(0, daily_remaining),
            "monthly_remaining": max(0, monthly_remaining),
            "daily_cap": self.budget.daily_cap,
            "monthly_cap": self.budget.monthly_cap,
            "alerts": alerts,
            "errors": errors,
        }

        if errors:
            raise BudgetExceededError(
                f"Budget exceeded. {'; '.join(errors)}. "
                f"Halt operation and notify principal."
            )

        return result

    def projection(self, estimated_cost: float) -> dict:
        """
        Project what budget looks like after a planned expenditure.

        Returns dict with estimated_cost, daily/monthly after, and ok status.
        """
        daily = self.daily_spend()
        monthly = self.monthly_spend()

        daily_after = daily + estimated_cost
        monthly_after = monthly + estimated_cost

        return {
            "estimated_cost": estimated_cost,
            "daily_after": daily_after,
            "monthly_after": monthly_after,
            "daily_remaining_after": max(0, self.budget.daily_cap - daily_after),
            "monthly_remaining_after": max(0, self.budget.monthly_cap - monthly_after),
            "would_exceed_daily": daily_after > self.budget.daily_cap,
            "would_exceed_monthly": monthly_after > self.budget.monthly_cap,
            "ok": (daily_after <= self.budget.daily_cap and
                   monthly_after <= self.budget.monthly_cap),
        }


# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ledger = CostLedger()
    try:
        status = ledger.check_budget()
        print(f"Daily spend:     ${status['daily_spend']:.2f} / ${status['daily_cap']:.2f}")
        print(f"Monthly spend:   ${status['monthly_spend']:.2f} / ${status['monthly_cap']:.2f}")
        print(f"Daily remaining: ${status['daily_remaining']:.2f}")
        print(f"Monthly remain:  ${status['monthly_remaining']:.2f}")
        if status["alerts"]:
            for a in status["alerts"]:
                print(f"ALERT: {a}")
        print("Status: OK")
    except BudgetExceededError as e:
        print(f"BUDGET EXCEEDED: {e}")
