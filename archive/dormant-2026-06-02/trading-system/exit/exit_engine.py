#!/usr/bin/env python3
"""
Exit Engine — Always-On Position Monitoring

Monitors open positions for exit triggers:
- Stop-loss hits
- Time-decay (exit N days before expiry)
- Profit-taking
- Correlation breakdown
- Edge collapse (our estimate moves toward market)

Every entry has a planned exit. This engine ensures it happens.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from intel.models import now_iso, parse_iso

REPO = Path(__file__).resolve().parent.parent.parent
AUDIT_LOG = REPO / "trading-system" / "audit" / "decisions.jsonl"


class ExitEngine:
    """Monitors positions and generates exit signals."""

    def __init__(self):
        pass

    def check_stops(self, position: dict, current_price_cents: float) -> Optional[dict]:
        """Check if a position's stop-loss is hit.

        Args:
            position: {"ticker": str, "side": str, "entry_price_cents": float,
                       "shares": int, "stop_loss_pct": float, ...}
            current_price_cents: Current market price

        Returns:
            Exit signal dict if stop triggered, None otherwise
        """
        entry = position.get("entry_price_cents", 0)
        stop_pct = position.get("stop_loss_pct")

        if not stop_pct or entry <= 0:
            return None

        pnl_pct = (current_price_cents - entry) / entry
        side = position.get("side", "YES")

        if side == "NO":
            pnl_pct = -pnl_pct  # Invert for NO positions

        if pnl_pct <= stop_pct:
            signal = {
                "type": "stop_loss",
                "ticker": position["ticker"],
                "reason": f"Stop loss hit: {pnl_pct*100:.1f}% <= {stop_pct*100:.1f}%",
                "pnl_pct": round(pnl_pct * 100, 1),
                "entry_price": entry,
                "current_price": current_price_cents,
            }
            self._log_exit(signal)
            return signal

        return None

    def check_time_decay(self, position: dict, now_ts: Optional[str] = None) -> Optional[dict]:
        """Check if a position needs to exit due to approaching expiry.

        Args:
            position: {"ticker": str, "expiry": str (ISO), "time_decay_exit_days": int, ...}

        Returns:
            Exit signal dict if time-decay triggered, None otherwise
        """
        expiry_str = position.get("expiry")
        exit_days = position.get("time_decay_exit_days", 7)

        if not expiry_str:
            return None

        try:
            expiry = parse_iso(expiry_str)
            now = parse_iso(now_ts) if now_ts else datetime.now(timezone.utc)
            remaining_days = (expiry - now).total_seconds() / 86400
        except (ValueError, TypeError):
            return None

        if remaining_days <= exit_days and remaining_days > 0:
            signal = {
                "type": "time_decay",
                "ticker": position["ticker"],
                "reason": f"Time decay: {remaining_days:.1f}d to expiry, exit at {exit_days}d",
                "remaining_days": round(remaining_days, 1),
            }
            self._log_exit(signal)
            return signal

        return None

    def check_profit_take(self, position: dict, current_price_cents: float) -> Optional[dict]:
        """Check if a position hit its profit target."""
        entry = position.get("entry_price_cents", 0)
        take_pct = position.get("profit_take_pct")

        if not take_pct or entry <= 0:
            return None

        pnl_pct = (current_price_cents - entry) / entry
        side = position.get("side", "YES")

        if side == "NO":
            pnl_pct = -pnl_pct

        if pnl_pct >= take_pct:
            signal = {
                "type": "profit_take",
                "ticker": position["ticker"],
                "reason": f"Profit target: {pnl_pct*100:.1f}% >= {take_pct*100:.1f}%",
                "pnl_pct": round(pnl_pct * 100, 1),
            }
            self._log_exit(signal)
            return signal

        return None

    def check_max_hold(self, position: dict, now_ts: Optional[str] = None) -> Optional[dict]:
        """Check if position exceeded max hold time."""
        entry_time = position.get("entry_time")
        max_hold_days = position.get("max_hold_days")

        if not entry_time or not max_hold_days:
            return None

        try:
            entered = parse_iso(entry_time)
            now = parse_iso(now_ts) if now_ts else datetime.now(timezone.utc)
            held_days = (now - entered).total_seconds() / 86400
        except (ValueError, TypeError):
            return None

        if held_days >= max_hold_days:
            signal = {
                "type": "max_hold",
                "ticker": position["ticker"],
                "reason": f"Max hold: {held_days:.0f}d >= {max_hold_days}d",
                "held_days": round(held_days, 1),
            }
            self._log_exit(signal)
            return signal

        return None

    def check_collapse(self, position: dict, current_edge_pct: float) -> Optional[dict]:
        """Check if the edge has collapsed (our estimate moved toward market).

        If the edge drops below 50% of original, consider exiting.
        """
        original_edge = position.get("entry_edge_pct", 0)
        if not original_edge:
            return None

        edge_remaining_pct = current_edge_pct / original_edge if original_edge > 0 else 0

        if edge_remaining_pct < 0.5 and current_edge_pct < 2.0:
            signal = {
                "type": "edge_collapse",
                "ticker": position["ticker"],
                "reason": f"Edge collapsed: {current_edge_pct:.1f}pp remaining ({edge_remaining_pct:.0f}% of original)",
                "original_edge": original_edge,
                "current_edge": current_edge_pct,
            }
            self._log_exit(signal)
            return signal

        return None

    def check_all(self, position: dict, current_price_cents: float,
                  current_edge_pct: float = 0) -> Optional[dict]:
        """Run all exit checks on a position. Returns first triggered exit."""
        checks = [
            ("stop_loss", self.check_stops(position, current_price_cents)),
            ("time_decay", self.check_time_decay(position)),
            ("profit_take", self.check_profit_take(position, current_price_cents)),
            ("max_hold", self.check_max_hold(position)),
            ("edge_collapse", self.check_collapse(position, current_edge_pct)),
        ]

        for name, signal in checks:
            if signal is not None:
                signal["check"] = name
                return signal

        return None

    def _log_exit(self, signal: dict):
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = json.dumps({
            "event": "exit_signal",
            "timestamp": now_iso(),
            "component": "exit_engine",
            "data": signal,
        })
        with open(AUDIT_LOG, "a") as f:
            f.write(entry + "\n")


class CorrelationMonitor:
    """Monitors co-movement between positions in the same risk factor cluster.

    If positions that should be uncorrelated start moving together
    (correlation breakdown), signal an alert.
    """

    def __init__(self, window_days: int = 20):
        self.window_days = window_days

    def check_correlation_break(self, positions: list[dict]) -> list[dict]:
        """Check for unusual co-movement in correlated positions.

        Simplified implementation: flags when all positions in a factor
        move in the same direction by > 5% in a single check.
        """
        alerts = []
        factor_groups: dict[str, list[dict]] = {}

        for pos in positions:
            for factor in pos.get("risk_factors", []):
                if factor not in factor_groups:
                    factor_groups[factor] = []
                factor_groups[factor].append(pos)

        for factor, group in factor_groups.items():
            if len(group) < 2:
                continue

            # Check if all positions have recent P&L in same direction
            pnl_signs = set()
            for pos in group:
                pnl = pos.get("unrealized_pnl_pct", 0)
                if abs(pnl) > 5:
                    pnl_signs.add("positive" if pnl > 0 else "negative")

            if len(pnl_signs) == 1:
                alerts.append({
                    "type": "correlation_break_warning",
                    "factor": factor,
                    "positions": len(group),
                    "all_same_direction": list(pnl_signs)[0],
                    "magnitude": max(abs(p.get("unrealized_pnl_pct", 0)) for p in group),
                })

        return alerts
