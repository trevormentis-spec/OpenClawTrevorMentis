#!/usr/bin/env python3
"""
Kalshi Risk Guard Engine
Position sizing, circuit breakers, and exit triggers.

Usage:
  from guard import RiskGuard
  rg = RiskGuard()
  
  # Before trading:
  can, reason = rg.can_open_position()
  size = rg.size_position(edge_pct=55, price_cents=7, balance=18500)
  
  # During monitoring:
  should_exit, reason = rg.check_exit(pos)
"""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Any, List


@dataclass
class PositionState:
    """Snapshot of a position for guard evaluation."""
    ticker: str
    side: str  # "yes" or "no"
    entry_price_cents: int
    current_price_cents: int
    count: int
    cost_basis_cents: int  # total cost in cents
    market_value_cents: int  # current market value in cents
    hours_open: float = 0.0
    highest_price_cents: int = 0


class RiskGuard:
    """Centralized risk management for Kalshi trading."""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "guardrails.yaml"
        with open(config_path) as f:
            self.cfg = yaml.safe_load(f)
        
        self._daily_pnl_cents = 0
        self._peak_portfolio_cents = 0
        self._circuit_breakers_triggered: List[str] = []

    # ── Position Sizing ──────────────────────────────────────────────

    def size_position(
        self,
        edge_pct: float,
        price_cents: int,
        balance_cents: int,
        max_loss_cents: Optional[int] = None,
    ) -> int:
        """
        Calculate optimal contract count using fractional Kelly.
        
        Args:
            edge_pct: Edge in percentage points (e.g. 55 means 55pt edge)
            price_cents: Current market price in cents (what we'd pay)
            balance_cents: Available balance in cents
            max_loss_cents: Optional hard cap on loss
            
        Returns:
            Recommended contract count (integer)
        """
        sizing = self.cfg["position_sizing"]
        kelly_frac = sizing["kelly_fraction"]
        max_pct = sizing["max_position_pct"] / 100.0
        
        # Kelly for binary: f = (p*b - q) / b
        p = (100 - price_cents + edge_pct) / 100.0  # win probability
        p = max(0.01, min(0.99, p))  # clamp
        q = 1.0 - p
        b = (100.0 - price_cents) / price_cents  # odds (payout / cost)
        
        kelly_f = max(0, (p * b - q) / b) if b > 0 else 0
        fractional_kelly = kelly_f * kelly_frac
        
        # Cap by max position % of portfolio
        max_by_pct = int(balance_cents * max_pct / price_cents)
        
        # Kelly size in contracts
        kelly_contracts = int(balance_cents * fractional_kelly / price_cents)
        
        # Take the minimum
        contracts = min(kelly_contracts, max_by_pct)
        
        # Apply hard loss cap if set
        if max_loss_cents and price_cents > 0:
            loss_capped = max_loss_cents // price_cents
            contracts = min(contracts, loss_capped)
        
        return max(1, contracts)  # minimum 1 contract

    # ── Circuit Breakers ─────────────────────────────────────────────

    def can_open_position(
        self,
        balance_cents: int,
        current_exposure_cents: int,
        open_positions: int,
        daily_pnl_cents: int = 0,
    ) -> Tuple[bool, str]:
        """
        Check if a new position is allowed.
        Returns (allowed, reason).
        """
        cb = self.cfg["circuit_breakers"]
        sizing = self.cfg["position_sizing"]
        
        # Daily loss circuit breaker
        self._daily_pnl_cents = daily_pnl_cents
        daily_loss_pct = abs(daily_pnl_cents) / max(balance_cents, 1) * 100
        if daily_pnl_cents < 0 and daily_loss_pct > cb["daily_loss_pct"]:
            return False, f"Daily loss {daily_loss_pct:.1f}% exceeds {cb['daily_loss_pct']}% cap"

        # Max drawdown
        if balance_cents < self._peak_portfolio_cents * (1 - cb["max_drawdown_pct"] / 100):
            drawdown = (1 - balance_cents / self._peak_portfolio_cents) * 100
            return False, f"Drawdown {drawdown:.1f}% exceeds {cb['max_drawdown_pct']}% cap"

        # Max concurrent positions
        if open_positions >= sizing["max_concurrent_positions"]:
            return False, f"At max concurrent positions ({sizing['max_concurrent_positions']})"

        # Max total exposure
        exposure_pct = (current_exposure_cents / max(balance_cents, 1)) * 100
        max_exp_pct = sizing["max_total_exposure_pct"]
        if exposure_pct > max_exp_pct:
            return False, f"Exposure {exposure_pct:.1f}% exceeds {max_exp_pct}% cap"

        return True, "ok"

    def has_edge(self, edge_pct: float) -> Tuple[bool, str]:
        """Check if edge meets minimum threshold."""
        min_edge = self.cfg["position_sizing"]["min_edge_to_trade"]
        if abs(edge_pct) < min_edge:
            return False, f"Edge {edge_pct:.1f}pts below minimum {min_edge}pts"
        return True, "ok"

    # ── Position Exit Triggers ──────────────────────────────────────

    def check_exit(self, pos: PositionState) -> Tuple[bool, str]:
        """
        Evaluate whether a position should be exited.
        Returns (should_exit, reason).
        """
        cb = self.cfg["circuit_breakers"]
        
        if pos.cost_basis_cents <= 0:
            return False, "no cost basis"

        # P&L calculation
        if pos.side == "yes":
            pnl_pct = ((pos.current_price_cents - pos.entry_price_cents) 
                       / max(pos.entry_price_cents, 1)) * 100
        else:  # "no" side
            pnl_pct = ((pos.entry_price_cents - pos.current_price_cents) 
                       / max(pos.entry_price_cents, 1)) * 100

        # Stop loss
        stop_loss = cb["position_stop_loss_pct"]
        if pnl_pct <= -stop_loss:
            return True, f"STOP LOSS: {pnl_pct:.0f}% (limit: -{stop_loss}%)"

        # Take profit
        take_profit = cb["position_take_profit_pct"]
        if pnl_pct >= take_profit:
            return True, f"TAKE PROFIT: +{pnl_pct:.0f}% (limit: +{take_profit}%)"

        # Trailing stop
        trail_pct = cb.get("trailing_stop_pct", 0)
        if trail_pct > 0 and pos.highest_price_cents > 0:
            drawdown_from_high = ((pos.highest_price_cents - pos.current_price_cents) 
                                  / max(pos.highest_price_cents, 1)) * 100
            if pnl_pct > 0 and drawdown_from_high > trail_pct:
                return True, f"TRAILING STOP: -{drawdown_from_high:.0f}% from high (limit: -{trail_pct}%)"

        return False, "ok"

    # ── State Management ─────────────────────────────────────────────

    def update_peak(self, portfolio_cents: int):
        """Update peak portfolio value for drawdown tracking."""
        self._peak_portfolio_cents = max(self._peak_portfolio_cents, portfolio_cents)

    def add_daily_pnl(self, pnl_cents: int):
        """Track daily P&L."""
        self._daily_pnl_cents += pnl_cents

    def reset_daily(self):
        """Reset daily tracking (call at UTC midnight)."""
        self._daily_pnl_cents = 0

    # ── Reporting ────────────────────────────────────────────────────

    def status_report(self, balance_cents: int, positions: List[PositionState]) -> str:
        """Generate a guardrail status summary."""
        sizing = self.cfg["position_sizing"]
        cb = self.cfg["circuit_breakers"]
        
        total_exposure = sum(p.market_value_cents for p in positions)
        exposure_pct = (total_exposure / max(balance_cents, 1)) * 100
        
        lines = [
            "═══ Guardrail Status ═══",
            f"Balance: ${balance_cents/100:.2f}",
            f"Positions: {len(positions)}/{sizing['max_concurrent_positions']}",
            f"Exposure: {exposure_pct:.1f}%/{sizing['max_total_exposure_pct']}%",
            f"Daily P&L: ${self._daily_pnl_cents/100:+.2f} (limit: -{cb['daily_loss_pct']}%)",
        ]
        
        if self._peak_portfolio_cents > 0:
            dd = (1 - balance_cents / self._peak_portfolio_cents) * 100
            lines.append(f"Drawdown: {dd:.1f}% (limit: {cb['max_drawdown_pct']}%)")
        
        if positions:
            lines.append("")
            for p in positions:
                if p.side == "yes":
                    pnl_pct = ((p.current_price_cents - p.entry_price_cents) 
                              / max(p.entry_price_cents, 1)) * 100
                else:
                    pnl_pct = ((p.entry_price_cents - p.current_price_cents) 
                              / max(p.entry_price_cents, 1)) * 100
                lines.append(
                    f"  {p.ticker} {p.side.upper()} ×{p.count} "
                    f"@{p.entry_price_cents}¢→{p.current_price_cents}¢ "
                    f"({pnl_pct:+.0f}%)"
                )
        
        return "\n".join(lines)


# ── Quick diagnostic ─────────────────────────────────────────────────

if __name__ == "__main__":
    rg = RiskGuard()
    print(rg.status_report(balance_cents=18574, positions=[]))
    
    # Test sizing
    size = rg.size_position(edge_pct=55, price_cents=7, balance_cents=18574)
    print(f"\nTest size (55pt edge, 7¢, $185.74): {size} contracts")
    
    # Test exit check
    pos = PositionState(
        ticker="KXUSAIRANAGREEMENT-27-26JUN",
        side="yes",
        entry_price_cents=9,
        current_price_cents=4,
        count=100,
        cost_basis_cents=900,
        market_value_cents=400,
        hours_open=72,
    )
    exit_now, reason = rg.check_exit(pos)
    print(f"\nExit check (9¢→4¢): {exit_now} — {reason}")
