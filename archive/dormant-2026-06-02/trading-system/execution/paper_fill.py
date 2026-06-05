#!/usr/bin/env python3
"""
Paper Fill Engine — Simulated Order Execution for Paper Trading

In PAPER mode, the gated client routes orders here instead of to Kalshi.
This engine simulates fills based on:
- Current market depth (real-time book)
- Spread / liquidity conditions
- Partial fill probability
- Slippage model

No real orders ever reach Kalshi from this engine.
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from intel.models import now_iso

REPO = Path(__file__).resolve().parent.parent.parent
AUDIT_LOG = REPO / "trading-system" / "audit" / "decisions.jsonl"
PAPER_BOOK = REPO / "trading-system" / "execution" / "paper_book.json"


class PaperFillEngine:
    """Simulates order fills for paper trading."""

    def __init__(self, fill_probability: float = 0.85):
        self.fill_probability = fill_probability

    def simulate_fill(self, order: dict, market: dict) -> dict:
        """Simulate whether an order would fill and at what price.

        Args:
            order: Proposed order with ticker, side, shares, price_cents
            market: Current market snapshot with depth

        Returns:
            Fill result dict
        """
        # Base fill probability
        fill_p = self.fill_probability

        # Adjust for spread tightness
        spread = market.get("spread_cents", 10)
        if spread <= 3:
            fill_p += 0.10  # Tight spread = more likely to fill
        elif spread >= 15:
            fill_p -= 0.20  # Wide spread = less likely

        # Adjust for depth
        depth = market.get(f"{order.get('side', 'YES').lower()}_depth", 0)
        if depth >= order.get("shares", 0) * 2:
            fill_p += 0.05  # Ample depth
        elif depth < order.get("shares", 0):
            fill_p -= 0.15  # Thin depth

        # Clamp
        fill_p = max(0.1, min(0.99, fill_p))

        # Simulate
        fills = random.random() < fill_p

        if not fills:
            return {
                "status": "rejected",
                "reason": "no_fill_simulated",
                "fill_probability": round(fill_p, 2),
                "filled_shares": 0,
                "fill_price": None,
                "partial": False,
            }

        # Simulate partial fill
        partial_p = 0.15  # 15% chance of partial fill
        partial = random.random() < partial_p

        if partial:
            fill_ratio = random.uniform(0.3, 0.8)
            filled_shares = max(1, int(order.get("shares", 0) * fill_ratio))
        else:
            filled_shares = order.get("shares", 0)

        # Simulate slippage
        entry_price = order.get("price_cents", 50)
        slippage = random.gauss(0, 0.02)  # Mean 0, std 2%
        fill_price = entry_price * (1 + slippage)

        result = {
            "status": "filled",
            "reason": "simulated_fill",
            "fill_probability": round(fill_p, 2),
            "filled_shares": filled_shares,
            "fill_price": round(fill_price, 1),
            "slippage_pct": round(slippage * 100, 2),
            "partial": partial,
        }

        self._log_fill(order, result)
        return result

    def get_paper_positions(self) -> list[dict]:
        """Get current simulated positions from the paper book."""
        if PAPER_BOOK.exists():
            try:
                return json.loads(PAPER_BOOK.read_text()).get("positions", [])
            except (json.JSONDecodeError, OSError):
                pass
        return []

    def save_paper_position(self, order: dict, fill: dict):
        """Record a filled paper position."""
        positions = self.get_paper_positions()
        positions.append({
            "ticker": order.get("ticker"),
            "side": order.get("side"),
            "shares": fill.get("filled_shares", 0),
            "entry_price": fill.get("fill_price", 0),
            "entry_time": now_iso(),
            "status": "open",
        })
        PAPER_BOOK.parent.mkdir(parents=True, exist_ok=True)
        PAPER_BOOK.write_text(json.dumps({"positions": positions}, indent=2))

    def get_paper_portfolio_value(self, current_prices: dict[str, float]) -> float:
        """Compute current paper portfolio mark-to-market."""
        positions = self.get_paper_positions()
        total = 0.0
        for pos in positions:
            ticker = pos.get("ticker")
            price = current_prices.get(ticker, 0)
            shares = pos.get("shares", 0)
            total += shares * price / 100
        return total

    def _log_fill(self, order: dict, result: dict):
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = json.dumps({
            "event": "paper_fill",
            "timestamp": now_iso(),
            "component": "paper_fill",
            "data": {
                "order": {
                    "ticker": order.get("ticker"),
                    "side": order.get("side"),
                    "shares": order.get("shares"),
                },
                "result": result,
            },
        })
        with open(AUDIT_LOG, "a") as f:
            f.write(entry + "\n")
