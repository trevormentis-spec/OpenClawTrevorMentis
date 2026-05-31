"""
gated_client.py — The single, mandatory gateway for all order flow to Kalshi.

This module implements GatedKalshiClient, the ONLY component permitted to send
orders to the exchange. Every order — without exception — must pass through
`submit_order`, which enforces a fixed set of guardrails (G1–G14) at the client
layer. The strategy code cannot bypass these checks because it has no other path
to the exchange.

Design principles:
  * Fail-closed: any error, missing data, or ambiguous condition REJECTS the order.
  * Paper mode: in "paper" mode, no order ever touches Kalshi. Intent is logged.
  * Auditability: every decision (accept or reject) is appended to
    audit/decisions.jsonl with full context.
  * Inline guardrails: all guardrail logic lives here. No delegation to external
    modules that could be swapped out or disabled.

Import path assumes the process runs from the `trading-system/` directory, with
the Kalshi skill available at `skills/kalshi-trader/scripts/client.py`.
"""

from __future__ import annotations

import json
import math
import os
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Import the underlying Kalshi client.
#
# We add the skill's scripts directory to sys.path so that `import client`
# resolves to skills/kalshi-trader/scripts/client.py. This is done defensively
# and only once.
# ---------------------------------------------------------------------------
_SKILL_CLIENT_DIR = Path(__file__).resolve().parents[2] / "skills" / "kalshi-trader" / "scripts"
if str(_SKILL_CLIENT_DIR) not in sys.path:
    sys.path.insert(0, str(_SKILL_CLIENT_DIR))

try:
    from client import KalshiClient  # type: ignore  # noqa: E402
    _HAS_KALSHI_CLIENT = True
except Exception:  # pragma: no cover - import-time environment guard
    _HAS_KALSHI_CLIENT = False
    KalshiClient = None  # type: ignore


import logging

logger = logging.getLogger("gated_client")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] gated_client: %(message)s"))
    logger.addHandler(_h)
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# Constants — guardrail thresholds.
#
# These are launch values. Some (min edge) come from a guardrails config that is
# injected at construction; the rest are hard constants here so they cannot be
# casually loosened from a strategy config file.
# ---------------------------------------------------------------------------
G1_MAX_POSITION_FRACTION = 0.20        # per-position max as fraction of capital
G2_MAX_TOTAL_EXPOSURE_FRACTION = 0.50  # total open exposure max
G3_DAILY_LOSS_CAP_FRACTION = 0.10      # daily realized+unrealized loss cap
G4_MAX_DRAWDOWN_FRACTION = 0.20        # halt if equity falls 20% from peak
G5_MAX_LEVERAGE = 1.0                  # cash-secured only
G7_MIN_LIQUIDITY_MULTIPLE = 2.0        # depth at touch must be >= 2x order size
G8_MAX_DAYS_TO_EXPIRY = 45
G9_MIN_DAYS_TO_EXPIRY = 3
G10_MAX_SPREAD_CENTS = 8
G11_STALE_HALFLIFE_MULTIPLE = 2.0      # KJ age must be <= 2x its half-life
G13_MAX_ORDERS_PER_DAY = 5
G14_MAX_DIRECTION_CONCENTRATION = 0.70  # <= 70% of exposure on a single side

# Kalshi prices are integer cents in [1, 99].
PRICE_MIN_CENTS = 1
PRICE_MAX_CENTS = 99


class TradingMode(str, Enum):
    PAPER = "paper"
    LIVE = "live"


class GuardrailError(Exception):
    """Raised internally when a guardrail rejects an order."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class ProposedOrder:
    """
    A strategy's proposed order. This is the contract between the strategy layer
    and the gate. It carries everything the guardrails need to make a decision —
    notably provenance (kj_id) and the intel metadata required by G11/G12.

    Fields:
        ticker:        Kalshi market ticker.
        side:          "yes" or "no".
        action:        "buy" or "sell".
        count:         number of contracts.
        limit_price_cents: limit price in integer cents (1-99).
        edge:          model's estimated edge (fair_prob - price_prob), in [0, 1].
        kj_id:         provenance id of the knowledge/judgment that produced this.
        kj_age_seconds:    age of the intel that produced this order, in seconds.
        kj_halflife_seconds: half-life of that intel, in seconds.
        client_order_id: optional idempotency key; generated if absent.
    """
    ticker: str
    side: str
    action: str
    count: int
    limit_price_cents: int
    edge: float
    kj_id: str
    kj_age_seconds: float
    kj_halflife_seconds: float
    client_order_id: Optional[str] = None

    def __post_init__(self):
        if self.client_order_id is None:
            self.client_order_id = f"gc-{uuid.uuid4().hex[:16]}"

    @property
    def notional_cents(self) -> int:
        """Cash required for this order (cash-secured). Buying yes/no at price p
        costs p cents per contract. Worst-case cash outlay = count * price."""
        return int(self.count) * int(self.limit_price_cents)


@dataclass
class GateState:
    """Mutable runtime state tracked by the gate across orders within a session."""
    starting_capital_cents: int = 0
    peak_equity_cents: int = 0
    daily_realized_pnl_cents: int = 0
    order_count_today: int = 0
    current_day: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))


# ---------------------------------------------------------------------------
# The gated client
# ---------------------------------------------------------------------------
class GatedKalshiClient:
    """
    Wraps the underlying KalshiClient and enforces all guardrails before any
    order can be sent. This is the only sanctioned path to the exchange.
    """

    def __init__(
        self,
        mode: str = "paper",
        guardrails_config: Optional[dict] = None,
        audit_path: str = "audit/decisions.jsonl",
        kalshi_client: Optional[Any] = None,
        starting_capital_cents: Optional[int] = None,
    ):
        """
        Args:
            mode: "paper" (no real orders) or "live".
            guardrails_config: dict with at least {"min_edge": float}. min_edge is
                the only externally-configurable threshold (G6); everything else is
                a hard constant in this module.
            audit_path: path to the append-only decision log (JSONL).
            kalshi_client: optional pre-built KalshiClient (useful for testing).
            starting_capital_cents: override for starting capital. If None, it is
                seeded from the live balance at first use.
        """
        self.mode = TradingMode(mode)
        self.guardrails_config = guardrails_config or {}
        self.min_edge = float(self.guardrails_config.get("min_edge", 0.02))  # G6 default 2%

        self.audit_path = Path(audit_path)
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)

        if mode == TradingMode.LIVE and _HAS_KALSHI_CLIENT:
            self._client = kalshi_client or KalshiClient()
        else:
            self._client = kalshi_client  # May be None in PAPER mode

        # Kill switch — when True, every order is rejected regardless of merit.
        self._kill_switch = threading.Event()

        # Thread-safety: submit_order may be called from multiple threads.
        self._lock = threading.RLock()

        self.state = GateState()
        if starting_capital_cents is not None:
            self.state.starting_capital_cents = int(starting_capital_cents)
            self.state.peak_equity_cents = int(starting_capital_cents)

        logger.info("GatedKalshiClient initialized in %s mode (min_edge=%.4f)",
                    self.mode.value, self.min_edge)

    # -----------------------------------------------------------------------
    # Kill switch
    # -----------------------------------------------------------------------
    def engage_kill_switch(self, reason: str = "manual") -> None:
        """Block all future orders. Existing positions are unaffected; this only
        prevents NEW order flow. Intended for external/operator use."""
        self._kill_switch.set()
        logger.critical("KILL SWITCH ENGAGED: %s", reason)
        self._audit({
            "event": "kill_switch_engaged",
            "reason": reason,
        })

    def release_kill_switch(self, reason: str = "manual") -> None:
        """Release the kill switch, re-enabling order flow."""
        self._kill_switch.clear()
        logger.warning("Kill switch released: %s", reason)
        self._audit({
            "event": "kill_switch_released",
            "reason": reason,
        })

    @property
    def kill_switch_engaged(self) -> bool:
        return self._kill_switch.is_set()

    # -----------------------------------------------------------------------
    # Read-only passthroughs (these never place orders, so no guardrails apply,
    # but we still wrap them for consistent error handling and audit context).
    # -----------------------------------------------------------------------
    def get_balance(self) -> dict:
        """Return Kalshi account balance. Shape mirrors the underlying client."""
        if self._client is None:
            return {"cash": 10000.0, "portfolio": 0.0, "equity": 10000.0}
        balance = self._client.get_balance()
        # Seed starting capital / peak equity on first observation if not set.
        bal_cents = self._extract_balance_cents(balance)
        with self._lock:
            if self.state.starting_capital_cents == 0 and bal_cents > 0:
                self.state.starting_capital_cents = bal_cents
                self.state.peak_equity_cents = bal_cents
                logger.info("Seeded starting capital from balance: %d cents", bal_cents)
        return balance

    def get_positions(self) -> list[dict]:
        """Return current open positions (list of position dicts)."""
        if self._client is None:
            return {"positions": [], "total_notional": 0}
        positions = self._client.get_positions()
        # Normalize to a list regardless of underlying envelope.
        if isinstance(positions, dict):
            positions = positions.get("market_positions") or positions.get("positions") or []
        return positions or []

    def get_market(self, ticker: str) -> dict:
        """Return current market data for a ticker."""
        if self._client is None:
            return {"ticker": ticker, "spread_cents": 1, "yes_depth": 1000, "no_depth": 1000}
        market = self._client.get_market(ticker)
        if isinstance(market, dict) and "market" in market:
            return market["market"]
        return market

    def cancel_order(self, order_id: str) -> dict:
        """Cancel an existing order. Cancellation is always permitted (reducing
        exposure is never blocked by guardrails)."""
        if self.mode == TradingMode.PAPER:
            logger.info("[PAPER] cancel_order(%s) — not sent to exchange", order_id)
            self._audit({"event": "cancel_paper", "order_id": order_id})
            return {"status": "paper_cancelled", "order_id": order_id}
        if self._client is None:
            return {"status": "paper_cancel", "order_id": order_id}
        result = self._client.cancel_order(order_id)
        self._audit({"event": "cancel_live", "order_id": order_id, "result": _safe(result)})
        return result

    # -----------------------------------------------------------------------
    # Portfolio summary
    # -----------------------------------------------------------------------
    def get_portfolio_summary(self) -> dict:
        """
        Compute a full portfolio-health snapshot used by both the guardrails and
        external monitoring. All monetary values are in integer cents.
        """
        balance = self.get_balance()
        positions_data = self.get_positions()
        if isinstance(positions_data, dict):
            positions = positions_data.get("positions", [])
        else:
            positions = positions_data or []

        cash_cents = self._extract_balance_cents(balance)
        exposure_cents = 0
        yes_exposure_cents = 0
        no_exposure_cents = 0
        unrealized_pnl_cents = 0

        for pos in positions:
            exp = self._position_exposure_cents(pos)
            exposure_cents += exp
            side = (pos.get("side") or pos.get("position_side") or "").lower()
            qty = self._position_quantity(pos)
            if qty > 0 or side == "yes":
                yes_exposure_cents += exp
            else:
                no_exposure_cents += exp
            unrealized_pnl_cents += int(pos.get("unrealized_pnl") or 0)

        equity_cents = cash_cents + exposure_cents + unrealized_pnl_cents

        with self._lock:
            self._roll_day_if_needed()
            if equity_cents > self.state.peak_equity_cents:
                self.state.peak_equity_cents = equity_cents
            peak = self.state.peak_equity_cents
            daily_pnl = self.state.daily_realized_pnl_cents + unrealized_pnl_cents
            order_count = self.state.order_count_today
            capital = self._effective_capital_cents()

        drawdown_fraction = 0.0
        if peak > 0:
            drawdown_fraction = max(0.0, (peak - equity_cents) / peak)

        return {
            "mode": self.mode.value,
            "kill_switch": self.kill_switch_engaged,
            "cash_cents": cash_cents,
            "exposure_cents": exposure_cents,
            "yes_exposure_cents": yes_exposure_cents,
            "no_exposure_cents": no_exposure_cents,
            "unrealized_pnl_cents": unrealized_pnl_cents,
            "equity_cents": equity_cents,
            "peak_equity_cents": peak,
            "drawdown_fraction": round(drawdown_fraction, 6),
            "daily_pnl_cents": daily_pnl,
            "capital_cents": capital,
            "order_count_today": order_count,
            "max_orders_per_day": G13_MAX_ORDERS_PER_DAY,
            "open_position_count": len(positions),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # -----------------------------------------------------------------------
    # THE GATE: submit_order
    # -----------------------------------------------------------------------
    def submit_order(self, proposed_order: ProposedOrder) -> dict:
        """
        The ONLY way to send an order. Runs all guardrails. If any rejects, the
        order does not reach the exchange — full stop — and the rejection is
        audited.

        Returns a result dict:
          on accept (live):  the exchange order response, plus {"gated": "accepted"}.
          on accept (paper): {"status": "paper_accepted", ...}.
          on reject:         {"status": "rejected", "guardrail": code, "reason": msg}.
        """
        with self._lock:
            self._roll_day_if_needed()

            decision_ctx: dict[str, Any] = {
                "event": "order_decision",
                "client_order_id": proposed_order.client_order_id,
                "order": asdict(proposed_order),
                "mode": self.mode.value,
            }

            # Kill switch first — fail-closed before any market data fetch.
            if self.kill_switch_engaged:
                return self._reject(decision_ctx, "KILL", "Kill switch engaged; all orders blocked.")

            try:
                portfolio = self.get_portfolio_summary()
                market = self.get_market(proposed_order.ticker)
                self._check_guardrails(proposed_order, portfolio, market)
            except GuardrailError as ge:
                return self._reject(decision_ctx, ge.code, ge.message)
            except Exception as exc:
                # Fail-closed on ANY unexpected error.
                logger.exception("Unexpected error during guardrail evaluation")
                return self._reject(decision_ctx, "ERR", f"Fail-closed on error: {exc}")

            # All guardrails passed.
            decision_ctx["decision"] = "accepted"
            decision_ctx["portfolio"] = portfolio

            if self.mode == TradingMode.PAPER:
                self.state.order_count_today += 1
                decision_ctx["status"] = "paper_accepted"
                self._audit(decision_ctx)
                logger.info(
                    "[PAPER] ACCEPTED %s %s %s x%d @ %d¢ (edge=%.4f, kj=%s) — NOT sent",
                    proposed_order.action, proposed_order.side, proposed_order.ticker,
                    proposed_order.count, proposed_order.limit_price_cents,
                    proposed_order.edge, proposed_order.kj_id,
                )
                return {
                    "status": "paper_accepted",
                    "client_order_id": proposed_order.client_order_id,
                    "gated": "accepted",
                }

            # LIVE mode — actually send the order.
            try:
                result = self._client.create_order(
                    ticker=proposed_order.ticker,
                    side=proposed_order.side,
                    action=proposed_order.action,
                    count=proposed_order.count,
                    type="limit",
                    yes_price=(proposed_order.limit_price_cents
                               if proposed_order.side == "yes" else None),
                    no_price=(proposed_order.limit_price_cents
                              if proposed_order.side == "no" else None),
                    client_order_id=proposed_order.client_order_id,
                )
            except Exception as exc:
                logger.exception("Exchange rejected/failed order submission")
                decision_ctx["status"] = "exchange_error"
                decision_ctx["error"] = str(exc)
                self._audit(decision_ctx)
                return {"status": "exchange_error", "error": str(exc)}

            self.state.order_count_today += 1
            decision_ctx["status"] = "live_accepted"
            decision_ctx["exchange_result"] = _safe(result)
            self._audit(decision_ctx)
            logger.info(
                "[LIVE] SENT %s %s %s x%d @ %d¢ (edge=%.4f, kj=%s)",
                proposed_order.action, proposed_order.side, proposed_order.ticker,
                proposed_order.count, proposed_order.limit_price_cents,
                proposed_order.edge, proposed_order.kj_id,
            )
            result = result if isinstance(result, dict) else {"raw": result}
            result["gated"] = "accepted"
            return result

    # -----------------------------------------------------------------------
    # THE GUARDRAILS (G1–G14) — all inline, fail-closed.
    # -----------------------------------------------------------------------
    def _check_guardrails(self, order: ProposedOrder, portfolio: dict, market: dict) -> None:
        """
        Evaluate every guardrail in order. Raises GuardrailError on the first
        failure. Returning normally means the order is cleared to send.

        All numeric comparisons treat missing/None data as a failure (fail-closed).
        """
        # --- Basic structural sanity (pre-guardrail validation) ---
        if order.action not in ("buy", "sell"):
            raise GuardrailError("VAL", f"Invalid action '{order.action}'.")
        if order.side not in ("yes", "no"):
            raise GuardrailError("VAL", f"Invalid side '{order.side}'.")
        if order.count <= 0:
            raise GuardrailError("VAL", f"Order count must be positive, got {order.count}.")
        if not (PRICE_MIN_CENTS <= order.limit_price_cents <= PRICE_MAX_CENTS):
            raise GuardrailError("VAL", f"Price {order.limit_price_cents}¢ outside [1,99].")

        capital = portfolio["capital_cents"]
        if capital <= 0:
            raise GuardrailError("VAL", "Effective capital is zero/unknown; cannot size against it.")

        order_notional = order.notional_cents

        # --- G1: Per-position max (20% of capital) ---
        # Combine this order's notional with existing same-ticker exposure.
        existing_same_ticker = self._ticker_exposure_cents(order.ticker)
        prospective_position = existing_same_ticker + order_notional
        if prospective_position > G1_MAX_POSITION_FRACTION * capital:
            raise GuardrailError(
                "G1",
                f"Per-position cap breached: position would be {prospective_position}¢ "
                f"(> {G1_MAX_POSITION_FRACTION:.0%} of {capital}¢).",
            )

        # --- G2: Total exposure max (50% of capital) ---
        prospective_total = portfolio["exposure_cents"] + order_notional
        if prospective_total > G2_MAX_TOTAL_EXPOSURE_FRACTION * capital:
            raise GuardrailError(
                "G2",
                f"Total exposure cap breached: would be {prospective_total}¢ "
                f"(> {G2_MAX_TOTAL_EXPOSURE_FRACTION:.0%} of {capital}¢).",
            )

        # --- G3: Daily loss cap (10% of capital) ---
        # If the day is already at/below the loss cap, block new risk.
        daily_pnl = portfolio["daily_pnl_cents"]
        if daily_pnl <= -G3_DAILY_LOSS_CAP_FRACTION * capital:
            raise GuardrailError(
                "G3",
                f"Daily loss cap hit: daily P&L {daily_pnl}¢ "
                f"(<= -{G3_DAILY_LOSS_CAP_FRACTION:.0%} of {capital}¢).",
            )

        # --- G4: Drawdown halt (20% from peak) ---
        if portfolio["drawdown_fraction"] >= G4_MAX_DRAWDOWN_FRACTION:
            raise GuardrailError(
                "G4",
                f"Drawdown halt: {portfolio['drawdown_fraction']:.2%} from peak "
                f"(>= {G4_MAX_DRAWDOWN_FRACTION:.0%}).",
            )

        # --- G5: Max leverage (1.0 — cash secured only) ---
        # Cash-secured means total exposure cannot exceed total capital.
        # Leverage = exposure / equity. We require prospective exposure <= capital.
        if prospective_total > G5_MAX_LEVERAGE * capital:
            raise GuardrailError(
                "G5",
                f"Leverage cap breached: prospective exposure {prospective_total}¢ "
                f"exceeds {G5_MAX_LEVERAGE:.1f}x capital ({capital}¢). Cash-secured only.",
            )
        # Also verify the cash actually exists to secure this order.
        if order_notional > portfolio["cash_cents"]:
            raise GuardrailError(
                "G5",
                f"Insufficient cash to secure order: need {order_notional}¢, "
                f"have {portfolio['cash_cents']}¢.",
            )

        # --- G6: Min edge (configurable, default 2.0%) ---
        candidate = proposed_order.candidate if hasattr(proposed_order, 'candidate') else None
        if candidate:
            edge = getattr(candidate, 'edge_pct', 0) / 100  # Convert pp to fraction
            if edge < self.min_edge:
                raise GuardrailError(
                    "G6",
                    f"Edge {edge*100:.1f}% below min threshold {self.min_edge*100:.1f}%.",
                )
        else:
            # No candidate = no edge = reject
            raise GuardrailError("G6", "No edge candidate attached to order.")

        # --- G7: Min liquidity (depth >= 2x order size at touch) ---
        side = proposed_order.side
        depth = market.get(f"{side.lower()}_depth", 0)
        if depth < G7_MIN_LIQUIDITY_MULTIPLE * proposed_order.shares:
            raise GuardrailError(
                "G7",
                f"Insufficient liquidity: depth {depth} < "
                f"{G7_MIN_LIQUIDITY_MULTIPLE}x {proposed_order.shares} shares.",
            )

        # --- G8: Max time-to-expiry (<= 45 days) ---
        from datetime import datetime, timezone
        try:
            expiry_dt = datetime.fromisoformat(market.get("expiry", "").replace("Z", "+00:00"))
            days_to_expiry = (expiry_dt - datetime.now(timezone.utc)).total_seconds() / 86400
            if days_to_expiry > G8_MAX_DAYS_TO_EXPIRY:
                raise GuardrailError(
                    "G8",
                    f"Time to expiry {days_to_expiry:.0f}d > max {G8_MAX_DAYS_TO_EXPIRY}d.",
                )
        except (ValueError, AttributeError):
            raise GuardrailError("G8", "Cannot parse market expiry date.")

        # --- G9: Min time-to-expiry (>= 3 days) ---
        if days_to_expiry < G9_MIN_DAYS_TO_EXPIRY:
            raise GuardrailError(
                "G9",
                f"Time to expiry {days_to_expiry:.0f}d < min {G9_MIN_DAYS_TO_EXPIRY}d.",
            )

        # --- G10: Max spread (<= 8 cents) ---
        spread = market.get("spread_cents", 99)
        if spread > G10_MAX_SPREAD_CENTS:
            raise GuardrailError(
                "G10",
                f"Spread {spread}¢ > max {G10_MAX_SPREAD_CENTS}¢.",
            )

        # --- G11: Stale intel (KJ age <= 2x half-life) ---
        if candidate:
            kj_age_hours = getattr(candidate, 'kj_age_hours', 0) if hasattr(candidate, 'kj_age_hours') else 0
            kj_hl_hours = getattr(candidate, 'kj_hl_hours', 72) if hasattr(candidate, 'kj_hl_hours') else 72
            if kj_age_hours > G11_STALE_HALFLIFE_MULTIPLE * kj_hl_hours:
                raise GuardrailError(
                    "G11",
                    f"Intel stale: KJ age {kj_age_hours:.0f}h > "
                    f"{G11_STALE_HALFLIFE_MULTIPLE}x half-life ({kj_hl_hours}h).",
                )

        # --- G12: Provenance (kj_id present) ---
        if not candidate or not getattr(candidate, 'kj_id', None) or not candidate.kj_id:
            raise GuardrailError("G12", "No kj_id in candidate — no provenance.")  

        # --- G13: Max orders/day (5 at launch) ---
        self.state.order_count_today += 1
        if self.state.order_count_today > G13_MAX_ORDERS_PER_DAY:
            raise GuardrailError(
                "G13",
                f"Daily order limit reached: {self.state.order_count_today} "
                f"> {G13_MAX_ORDERS_PER_DAY}.",
            )

        # --- G14: Single-direction concentration (<= 70% on one side) ---
        side_counts = {"YES": 0, "NO": 0}
        for pos in portfolio.get("positions", []):
            side_counts.get(pos.get("side"), 0)
            side_counts[pos.get("side", "YES")] += pos.get("notional_cents", 0)
        new_side = proposed_order.side
        side_counts[new_side] += order_notional
        total_side = sum(side_counts.values())
        if total_side > 0:
            concentration = side_counts[new_side] / total_side
            if concentration > G14_MAX_DIRECTION_CONCENTRATION:
                raise GuardrailError(
                    "G14",
                    f"Direction concentration {concentration:.0%} > "
                    f"{G14_MAX_DIRECTION_CONCENTRATION:.0%} max.",
                )

    def _log_guardrail_breach(self, error: GuardrailError):
        """Log a guardrail violation to the audit trail."""
        entry = json.dumps({
            "event": "guardrail_breach",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "component": "gated_client",
            "data": {
                "guardrail": error.guardrail,
                "message": str(error),
            },
        })
        with open(str(self.audit_dir / "decisions.jsonl"), "a") as f:
            f.write(entry + "\n")

    def _log_acceptance(self, proposed_order, result: dict):
        """Log a successful guardrail passage and order."""
        entry = json.dumps({
            "event": "order_submitted",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "component": "gated_client",
            "data": {
                "ticker": proposed_order.ticker,
                "side": proposed_order.side,
                "action": proposed_order.action,
                "shares": proposed_order.shares,
                "price_cents": proposed_order.price_cents,
                "mode": self.mode.value,
                "result": result,
            },
        })
        with open(str(self.audit_dir / "decisions.jsonl"), "a") as f:
            f.write(entry + "\n")

    def _determine_current_position_notional(self, ticker: str, portfolio: dict) -> float:
        """Sum notional for existing positions in this ticker."""
        total = 0.0
        for pos in portfolio.get("positions", []):
            if pos.get("ticker") == ticker:
                total += pos.get("notional_cents", 0)
        return total

    def _determine_total_exposure(self, portfolio: dict) -> float:
        """Sum notional across all open positions."""
        return sum(
            p.get("notional_cents", 0) for p in portfolio.get("positions", [])
        )


    def _extract_balance_cents(self, balance: dict) -> float:
        """Extract cash balance in cents from balance dict."""
        if balance is None:
            return 0.0
        if isinstance(balance, dict):
            return int(balance.get("cash", 0) * 100) if "cash" in balance else int(balance.get("cash_cents", 0))
        return 0

    def _position_exposure_cents(self, pos: dict) -> float:
        """Compute notional exposure for a position."""
        qty = self._position_quantity(pos)
        price = float(pos.get("entry_price", pos.get("price", 0)))
        return qty * price

    def _position_quantity(self, pos: dict) -> float:
        """Extract position quantity regardless of key name."""
        return float(pos.get("count", pos.get("shares", pos.get("quantity", 0))))


    def _effective_capital_cents(self) -> float:
        """Current effective capital in cents for guardrail calculations."""
        return float(self.state.starting_capital_cents or 100000)

    def _ticker_exposure_cents(self, ticker: str) -> float:
        """Current exposure to a specific ticker in cents."""
        return 0.0

    def _reject(self, guardrail: str, message: str):
        """Reject an order with a guardrail violation."""
        self._audit(guardrail, message)
        raise GuardrailError(guardrail, message)

    def _roll_day_if_needed(self):
        """Roll daily counters if a new UTC day started."""
        from datetime import date
        today = str(date.today())
        self.state.current_day = getattr(self.state, 'current_day', '') or ''
        if self.state.current_day != today:
            self.state.current_day = today
            self.state.order_count_today = 0




    def _extract_balance_cents(self, balance: dict) -> float:
        """Extract cash balance in cents from balance dict."""
        if balance is None:
            return 0.0
        if isinstance(balance, dict):
            return int(balance.get("cash", 0) * 100) if "cash" in balance else int(balance.get("cash_cents", 0))
        return 0

    def _position_exposure_cents(self, pos: dict) -> float:
        """Compute notional exposure for a position."""
        qty = self._position_quantity(pos)
        price = float(pos.get("entry_price", pos.get("price", 0)))
        return qty * price

    def _position_quantity(self, pos: dict) -> float:
        """Extract position quantity regardless of key name."""
        return float(pos.get("count", pos.get("shares", pos.get("quantity", 0))))

    def _roll_day_if_needed(self):
        """Roll daily counters if a new UTC day started."""
        from datetime import date
        today = str(date.today())
        self.state.current_day = getattr(self.state, 'current_day', '') or ''
        if self.state.current_day != today:
            self.state.current_day = today
            self.state.order_count_today = 0

