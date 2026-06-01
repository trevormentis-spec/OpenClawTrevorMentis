"""
execution/kalshi_adapter.py

A clean adapter around the existing KalshiClient that normalizes real Kalshi
API responses into a consistent, cents-based format for the gated client.

All monetary values are normalized to CENTS (integers where possible).
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Import KalshiClient from a hyphenated path (not a valid Python identifier),
# so we load it via importlib rather than a normal `import`.
# ---------------------------------------------------------------------------
def _load_kalshi_client():
    # Try the straightforward import first (in case the path is importable).
    try:
        from skills.kalshi_trader.scripts.client import KalshiClient  # type: ignore
        return KalshiClient
    except Exception:
        pass

    # Fall back to loading the module directly from its file path.
    here = Path(__file__).resolve()
    # __file__ is trading-system/execution/kalshi_adapter.py
    # repo_root is the workspace root (one more level up than trading-system/)
    repo_root = here.parent.parent.parent
    client_path = repo_root / "skills" / "kalshi-trader" / "scripts" / "client.py"

    if not client_path.exists():
        # Try one level up (for non-standard layouts)
        repo_root = here.parent.parent
        client_path = repo_root / "skills" / "kalshi-trader" / "scripts" / "client.py"

    if not client_path.exists():
        # Allow override via env var for non-standard layouts.
        env_path = os.environ.get("KALSHI_CLIENT_PATH")
        if env_path:
            client_path = Path(env_path)

    if not client_path.exists():
        raise ImportError(
            f"Could not locate KalshiClient at {client_path}. "
            f"Set KALSHI_CLIENT_PATH to override."
        )

    spec = importlib.util.spec_from_file_location("kalshi_client_module", client_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to build import spec for {client_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return getattr(module, "KalshiClient")


KalshiClient = _load_kalshi_client()


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------
def _dollars_to_cents(value: Any) -> Optional[int]:
    """Convert a dollar value (str/float/int) to integer cents.

    Returns None if the value is missing or cannot be parsed.
    """
    if value is None:
        return None
    try:
        # Strings like "0.2900" or numeric dollars.
        dollars = float(value)
    except (TypeError, ValueError):
        return None
    return int(round(dollars * 100))


def _to_int_cents(value: Any) -> Optional[int]:
    """Coerce an already-cents value into an int. Returns None if unparseable."""
    if value is None:
        return None
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def _first_present(*values: Any) -> Optional[Any]:
    """Return the first value that is not None."""
    for v in values:
        if v is not None:
            return v
    return None


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------
class KalshiAdapter:
    """Normalizes raw KalshiClient responses into a consistent cents-based shape."""

    def __init__(self, client: Optional[Any] = None, **client_kwargs: Any):
        """
        Args:
            client: An existing KalshiClient instance. If None, a new one is
                    constructed using client_kwargs.
            client_kwargs: Passed to KalshiClient(...) when client is None.
        """
        self.client = client if client is not None else KalshiClient(**client_kwargs)

    # ------------------------------------------------------------------ #
    # Balance
    # ------------------------------------------------------------------ #
    def get_balance(self) -> dict:
        """Return normalized balance in cents.

        Returns:
            {
                "cash_cents": int,
                "portfolio_cents": int,
                "equity_cents": int,
                "peak_equity_cents": int,
            }
        """
        raw = self.client.get_balance() or {}

        # `balance` is already in cents; prefer it, fall back to balance_dollars.
        cash_cents = _first_present(
            _to_int_cents(raw.get("balance")),
            _dollars_to_cents(raw.get("balance_dollars")),
            0,
        )

        # `portfolio_value` is already in cents.
        portfolio_cents = _first_present(
            _to_int_cents(raw.get("portfolio_value")),
            _dollars_to_cents(raw.get("portfolio_value_dollars")),
            0,
        )

        equity_cents = cash_cents + portfolio_cents

        return {
            "cash_cents": cash_cents,
            "portfolio_cents": portfolio_cents,
            "equity_cents": equity_cents,
            # No historical peak is provided by the API; seed with current equity.
            "peak_equity_cents": equity_cents,
        }

    # ------------------------------------------------------------------ #
    # Market
    # ------------------------------------------------------------------ #
    def get_market(self, ticker: str) -> dict:
        """Return a normalized market dict (prices in cents)."""
        raw = self.client.get_market(ticker) or {}
        market = raw.get("market", raw) or {}

        # Prefer integer cent fields, fall back to dollar strings.
        yes_bid = _first_present(
            _to_int_cents(market.get("yes_bid")),
            _dollars_to_cents(market.get("yes_bid_dollars")),
        )
        yes_ask = _first_present(
            _to_int_cents(market.get("yes_ask")),
            _dollars_to_cents(market.get("yes_ask_dollars")),
        )
        no_bid = _first_present(
            _to_int_cents(market.get("no_bid")),
            _dollars_to_cents(market.get("no_bid_dollars")),
        )
        no_ask = _first_present(
            _to_int_cents(market.get("no_ask")),
            _dollars_to_cents(market.get("no_ask_dollars")),
        )

        # Mid price / spread from the YES side when both sides are present.
        mid_price = None
        spread_cents = None
        if yes_bid is not None and yes_ask is not None:
            mid_price = int(round((yes_bid + yes_ask) / 2))
            spread_cents = yes_ask - yes_bid

        # Volume proxy from open interest (float-point string).
        volume = None
        oi = market.get("open_interest_fp", market.get("open_interest"))
        if oi is not None:
            try:
                volume = int(float(oi))
            except (TypeError, ValueError):
                volume = None

        expiry = _first_present(
            market.get("expiration_time"),
            market.get("close_time"),
        )

        # Try to pull orderbook depth if available.
        yes_depth, no_depth = self._safe_depth(ticker)

        return {
            "ticker": market.get("ticker", ticker),
            "title": market.get("title"),
            "yes_bid": yes_bid,
            "yes_ask": yes_ask,
            "no_bid": no_bid,
            "no_ask": no_ask,
            "mid_price": mid_price,
            "spread_cents": spread_cents,
            "expiry": expiry,
            "volume": volume,
            "last_updated": market.get("last_updated_ts") or market.get("updated_ts"),
            "yes_depth": yes_depth,
            "no_depth": no_depth,
            # Pass through original fields requested by the gated client.
            "expiration_time": market.get("expiration_time"),
            "close_time": market.get("close_time"),
            "last_price_dollars": market.get("last_price_dollars"),
        }

    def _safe_depth(self, ticker: str) -> tuple[Optional[int], Optional[int]]:
        """Best-effort total depth (summed sizes) for yes/no sides."""
        try:
            ob = self.get_orderbook(ticker)
        except Exception:
            return None, None

        yes_depth = sum(level["size"] for level in ob.get("yes", [])) or None
        no_depth = sum(level["size"] for level in ob.get("no", [])) or None
        return yes_depth, no_depth

    # ------------------------------------------------------------------ #
    # Orderbook
    # ------------------------------------------------------------------ #
    def get_orderbook(self, ticker: str) -> dict:
        """Return normalized orderbook depth.

        Returns:
            {
                "ticker": str,
                "yes": [{"price": cents:int, "size": int}, ...],
                "no":  [{"price": cents:int, "size": int}, ...],
            }
        """
        # The underlying client may expose this under a few names.
        getter = (
            getattr(self.client, "get_orderbook", None)
            or getattr(self.client, "get_market_orderbook", None)
        )
        if getter is None:
            return {"ticker": ticker, "yes": [], "no": []}

        raw = getter(ticker) or {}
        book = raw.get("orderbook", raw) or {}

        return {
            "ticker": ticker,
            "yes": self._normalize_levels(book.get("yes")),
            "no": self._normalize_levels(book.get("no")),
        }

    @staticmethod
    def _normalize_levels(levels: Any) -> list[dict]:
        """Normalize a list of [price, size] pairs (or dicts) to cent prices."""
        out: list[dict] = []
        if not levels:
            return out

        for level in levels:
            price = None
            size = None
            if isinstance(level, (list, tuple)) and len(level) >= 2:
                # Kalshi typically returns [price_cents, size].
                price = _to_int_cents(level[0])
                size = _to_int_cents(level[1])
            elif isinstance(level, dict):
                price = _first_present(
                    _to_int_cents(level.get("price")),
                    _dollars_to_cents(level.get("price_dollars")),
                )
                size = _to_int_cents(level.get("size") or level.get("count"))

            if price is None or size is None:
                continue
            out.append({"price": price, "size": size})

        return out

    # ------------------------------------------------------------------ #
    # Positions
    # ------------------------------------------------------------------ #
    def get_positions(self) -> list[dict]:
        """Return normalized positions with notional in cents."""
        raw = self.client.get_positions()

        # The client may return a list directly, or a dict wrapping a list.
        if isinstance(raw, dict):
            raw_positions = (
                raw.get("positions")
                or raw.get("market_positions")
                or []
            )
        else:
            raw_positions = raw or []

        normalized: list[dict] = []
        for pos in raw_positions:
            count = _to_int_cents(pos.get("count")) or 0
            entry_price = _first_present(
                _to_int_cents(pos.get("entry_price")),
                _dollars_to_cents(pos.get("entry_price_dollars")),
                0,
            )
            notional_cents = count * (entry_price or 0)

            normalized.append({
                "ticker": pos.get("ticker"),
                "side": pos.get("side"),
                "count": count,
                "entry_price": entry_price,
                "notional_cents": notional_cents,
            })

        return normalized

    # ------------------------------------------------------------------ #
    # Orders
    # ------------------------------------------------------------------ #
    def create_order(
        self,
        ticker: str,
        side: str,
        action: str,
        count: int,
        yes_price: Optional[int] = None,
        no_price: Optional[int] = None,
        **kwargs: Any,
    ) -> dict:
        """Pass through to the real client's create_order with field mapping.

        Args:
            ticker: Market ticker.
            side: "yes" or "no".
            action: "buy" or "sell".
            count: Number of contracts.
            yes_price: Limit price in cents (for yes side).
            no_price: Limit price in cents (for no side).
            kwargs: Additional fields forwarded to the client unchanged
                    (e.g. type, client_order_id, time_in_force).
        """
        order_kwargs: dict[str, Any] = {
            "ticker": ticker,
            "side": side,
            "action": action,
            "count": count,
        }
        if yes_price is not None:
            order_kwargs["yes_price"] = yes_price
        if no_price is not None:
            order_kwargs["no_price"] = no_price

        order_kwargs.update(kwargs)

        return self.client.create_order(**order_kwargs)

    def cancel_order(self, order_id: str, **kwargs: Any) -> dict:
        """Pass through to the real client's cancel_order."""
        return self.client.cancel_order(order_id, **kwargs)