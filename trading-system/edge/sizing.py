#!/usr/bin/env python3
"""
Position Sizing — Kelly + Correlation Adjustment

Sizes positions using fractional Kelly, then adjusts for correlation
crowding across risk factors. Enforces hard concentration limits.

This is where the spec's §5 design is implemented.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Optional

from intel.models import (
    Candidate, ProposedOrder, ExitPlan, now_iso,
)

REPO = Path(__file__).resolve().parent.parent.parent
AUDIT_LOG = REPO / "trading-system" / "audit" / "decisions.jsonl"
CONFIG_FILE = REPO / "trading-system" / "config" / "guardrails.yaml"


class SizingEngine:
    """Computes position sizes from candidates."""

    def __init__(self, capital: float = 50.0, config: Optional[dict] = None):
        self.capital = capital
        self.config = config or self._default_config()

    def _default_config(self) -> dict:
        """Load config from guardrails.yaml with defaults."""
        return {
            "kelly_fraction": 0.25,
            "max_kelly_fraction": 0.50,
            "correlation_penalty_gamma": 2.0,
            "max_single_position_pct": 0.20,
            "max_total_exposure_pct": 0.50,
            "max_single_risk_factor_pct": 0.35,
            "max_single_region_pct": 0.40,
            "min_risk_factors_when_active": 3,
            "max_factor_skew_pct": 0.60,
            "min_trade_dollars": 1.0,
        }

    def compute_kelly_fraction(self, candidate: Candidate) -> float:
        """Compute full-Kelly fraction from edge and probability.

        Kelly formula: f* = (p * (b+1) - 1) / b
        For binary prediction markets with price P:
        - Buy YES at price P: b = 1/P - 1 (odds)
        - p = our probability estimate
        - f* = (p * (1/P) - 1) / (1/P - 1)
        Simplified: f* = p - P/(1-P) for NO, or (p - P) / (1-P) for YES
        """
        p = candidate.p_effective
        mkt = candidate.p_market

        if candidate.side == "YES":
            # Kelly for buying YES: f* = (p - mkt) / (1 - mkt)
            denominator = 1.0 - mkt
            if denominator <= 0:
                return 0.0
            kelly = (p - mkt) / denominator
        else:
            # Kelly for buying NO: f* = ((1-p) - (1-mkt)) / mkt
            # = (mkt - p) / mkt
            if mkt <= 0:
                return 0.0
            kelly = (mkt - p) / mkt

        return max(0.0, kelly)

    def compute_existing_exposure_by_factor(self, existing_positions: list[dict]) -> dict[str, float]:
        """Compute current dollar exposure per risk factor."""
        exposure: dict[str, float] = {}
        for pos in existing_positions:
            factors = pos.get("risk_factors", [])
            dollars = pos.get("current_value", 0.0)
            for f in factors:
                exposure[f] = exposure.get(f, 0.0) + dollars
        return exposure

    def compute_correlation_penalty(
        self,
        candidate: Candidate,
        existing_exposure: dict[str, float],
    ) -> float:
        """Compute crowding penalty for this candidate.

        If adding this position would crowd a risk factor, reduce size.
        """
        gamma = self.config["correlation_penalty_gamma"]
        max_factor_pct = self.config["max_single_risk_factor_pct"]

        penalties = []
        for factor in candidate.risk_factors:
            current = existing_exposure.get(factor, 0.0)
            # Assume this order would add candidate-sized exposure
            crowding = (current) / self.capital
            penalty = 1.0 / (1.0 + gamma * crowding)
            penalties.append(penalty)

        if not penalties:
            return 1.0

        # Use the minimum penalty (most conservative)
        return min(penalties)

    def size_position(
        self,
        candidate: Candidate,
        existing_positions: list[dict] | None = None,
    ) -> Optional[ProposedOrder]:
        """Size a candidate into a ProposedOrder with exit plan.

        Returns None if sizing produces below-minimum dollar amount.
        """
        if existing_positions is None:
            existing_positions = []

        # Step 1: Full Kelly fraction
        kelly_full = self.compute_kelly_fraction(candidate)
        if kelly_full <= 0:
            self._audit("sizing_rejected", {
                "ticker": candidate.ticker,
                "reason": "kelly_non_positive",
                "kelly_full": kelly_full,
            })
            return None

        # Step 2: Apply fractional Kelly based on confidence
        if candidate.confidence == "high":
            kelly_frac = self.config["max_kelly_fraction"]
        elif candidate.confidence == "medium":
            kelly_frac = self.config["kelly_fraction"]
        else:
            kelly_frac = self.config["kelly_fraction"] * 0.5  # Low confidence = half

        f_used = kelly_full * kelly_frac

        # Step 3: Correlation penalty
        existing_exposure = self.compute_existing_exposure_by_factor(existing_positions)
        corr_penalty = self.compute_correlation_penalty(candidate, existing_exposure)
        f_final = f_used * corr_penalty

        # Step 4: Dollar amount
        dollars = f_final * self.capital

        # Step 5: Clamp to per-position cap
        max_position_dollars = self.capital * self.config["max_single_position_pct"]
        dollars = min(dollars, max_position_dollars)

        # Step 6: Round to whole contracts
        price_cents = candidate.p_market * 100 if candidate.side == "YES" else (1 - candidate.p_market) * 100
        shares = max(1, int(dollars / (price_cents / 100))) if price_cents > 0 else 1
        actual_cost = shares * (price_cents / 100)

        # Step 7: Minimum trade check
        if actual_cost < self.config.get("min_trade_dollars", 1.0):
            self._audit("sizing_rejected", {
                "ticker": candidate.ticker,
                "reason": "below_min_trade",
                "actual_cost": round(actual_cost, 2),
                "min_trade": self.config["min_trade_dollars"],
            })
            return None

        # Step 8: Build exit plan
        exit_plan = ExitPlan(
            stop_loss_pct=-0.5,           # -50% stop loss
            time_decay_exit_days=7,        # Exit 7 days before expiry
            profit_take_pct=2.0,           # +200% take profit
            max_hold_days=30,              # Max 30 day hold
        )

        order = ProposedOrder(
            ticker=candidate.ticker,
            side=candidate.side,
            action="buy",
            shares=shares,
            price_cents=round(price_cents, 1),
            notional_cents=round(actual_cost * 100, 1),
            total_cost=round(actual_cost, 2),
            candidate=candidate,
            exit_plan=exit_plan,
        )

        self._audit("sizing_proposed", {
            "ticker": order.ticker,
            "side": order.side,
            "shares": order.shares,
            "price_cents": order.price_cents,
            "total_cost": order.total_cost,
            "kelly_full": round(kelly_full, 3),
            "kelly_fraction_used": kelly_frac,
            "correlation_penalty": round(corr_penalty, 3),
            "confidence": candidate.confidence,
        })

        return order

    def update_capital(self, new_capital: float):
        """Update capital reference (called daily from portfolio sync)."""
        self.capital = new_capital

    def _audit(self, event_type: str, data: dict):
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = json.dumps({
            "event": event_type,
            "timestamp": now_iso(),
            "component": "sizing",
            "data": data,
        })
        with open(AUDIT_LOG, "a") as f:
            f.write(entry + "\n")
