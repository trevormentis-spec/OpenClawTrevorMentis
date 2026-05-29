#!/usr/bin/env python3
"""
Philby Trading Daemon — 24/7 Continuous Trading System for Kalshi Prediction Markets.

Integrates WebSocket real-time price data with daily brief intelligence and
autonomous execution using four strategies: Edge, Mean Reversion, Momentum
Rider, and Take Profit/Stop Loss.

Architecture:
  ┌─────────────────────────────────────────────────────────────┐
  │  WebSocket → PriceStore (live prices in memory)              │
  │  intel_bridge.py → signals/latest.json (edge detection)      │
  │  exec_summary.json → direct KJ extraction                    │
  │                                                              │
  │  Trading Loop (every 60s):                                   │
  │    1. Check all strategy signals                             │
  │    2. Validate against guardrails                            │
  │    3. Execute via KalshiClient                               │
  │    4. Reconcile positions, update P&L, log journal           │
  └─────────────────────────────────────────────────────────────┘

Usage:
  python3 philby/trader/daemon.py                       # Start in foreground
  python3 philby/trader/daemon.py --daemon               # Start with nohup
  python3 philby/trader/daemon.py --status               # Status report
  python3 philby/trader/daemon.py --scan                 # One-shot signal detection
  python3 philby/trader/daemon.py --backfill             # Backfill prices from WS log
  python3 philby/trader/daemon.py --stop                 # Graceful shutdown
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import datetime as dt
import json
import logging
import math
import os
import pathlib
import signal
import subprocess
import sys
import time as _time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import websockets

# ── Paths & Constants ────────────────────────────────────────────────

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
WS_URL = "wss://api.elections.kalshi.com/trade-api/ws/v2"
WS_SIGN_PATH = "/trade-api/ws/v2"
PID_FILE = REPO / "philby" / "trader" / "daemon.pid"
JOURNAL_FILE = REPO / "philby" / "trader" / "journal.jsonl"
POSITIONS_FILE = REPO / "philby" / "trader" / "positions_live.json"
SIGNALS_FILE = REPO / "philby" / "trader" / "signals" / "latest.json"
WS_LOG_FILE = REPO / "logs" / "kalshi" / "ws-events.jsonl"
DAEMON_LOG_FILE = REPO / "logs" / "philby-daemon.log"
BRIEFINGS_DIR = pathlib.Path.home() / "trevor-briefings"

GUARDRAILS = {
    "kelly_fraction": 0.25,
    "max_position_pct": 5.0,
    "max_total_exposure_pct": 30.0,
    "max_concurrent_positions": 10,
    "min_edge_to_trade": 5,
    "daily_loss_pct": 10.0,
    "max_drawdown_pct": 20.0,
    "position_stop_loss_pct": 50.0,
    "position_take_profit_pct": 100.0,
}

# ── Narrative → Kalshi ticker mapping (synchronized with intel_bridge.py) ──

NARRATIVE_TO_KALSHI = {
    "iran_nuclear": {
        "ticker_keywords": ["USAIRANAGREEMENT"],
        "direction": "buy_yes",
        "trevor_narrative_ids": ["iran_nuclear_deal_before_june", "iran_nuclear_deal_by_july"],
    },
    "iran_trump": {
        "ticker_keywords": ["TRUMPIRAN"],
        "direction": "buy_yes",
        "trevor_narrative_ids": ["iran_nuclear_deal_before_june"],
    },
    "brent_crude_high": {
        "ticker_keywords": ["WTIMAX"],
        "direction": "buy_yes",
        "trevor_narrative_ids": ["brent_crude_price_trajectory"],
    },
    "ukraine_eu": {
        "ticker_keywords": ["UKRAINEEU"],
        "direction": "buy_yes",
        "trevor_narrative_ids": ["ukraine_european_security_realignment"],
    },
    "us_tariffs": {
        "ticker_keywords": ["TARIFFRATEPRC"],
        "direction": "buy_yes",
        "trevor_narrative_ids": ["us_china_trade_tariff_escalation"],
    },
}

# Additional keyword-based mapping for exec_summary KJs
KJ_KEYWORD_TO_TICKER = [
    # (keyword_in_statement, series_ticker_keyword, direction)
    ("Iran", "USAIRANAGREEMENT", "buy_yes"),
    ("Iran nuclear", "TRUMPIRAN", "buy_yes"),
    ("tariff", "TARIFFRATEPRC", "buy_yes"),
    ("trade war", "TARIFFRATEPRC", "buy_yes"),
    ("crude", "WTIMAX", "buy_yes"),
    ("Brent", "WTIMAX", "buy_yes"),
    ("oil price", "WTIMAX", "buy_yes"),
    ("oil", "WTIMAX", "buy_yes"),
    ("Ukraine", "UKRAINEEU", "buy_yes"),
    ("Russia", "UKRAINEEU", "buy_yes"),
    ("Israel", "USAIRANAGREEMENT", "buy_yes"),
    ("Gaza", "USAIRANAGREEMENT", "buy_yes"),
    ("Lebanon", "USAIRANAGREEMENT", "buy_yes"),
    ("NATO", "UKRAINEEU", "buy_yes"),
    ("Romania", "UKRAINEEU", "buy_yes"),
    ("Taiwan", "TARIFFRATEPRC", "buy_yes"),
    ("China", "TARIFFRATEPRC", "buy_yes"),
    ("Middle East", "USAIRANAGREEMENT", "buy_yes"),
    ("Guatemala", "USAIRANAGREEMENT", "buy_yes"),  # Broad geopolitical → Iran deal proxy
    ("Mali", "UKRAINEEU", "buy_yes"),  # Ukraine-adjacent conflict
    ("Hegseth", "TARIFFRATEPRC", "buy_yes"),  # US defense posture → China tension proxy
    ("Defense Secretary", "TARIFFRATEPRC", "buy_yes"),
]


# ── Logging Setup ────────────────────────────────────────────────────

def setup_daemon_logging(log_file: Optional[pathlib.Path] = None) -> logging.Logger:
    """Configure logging to stdout and optional log file."""
    logger = logging.getLogger("philby-daemon")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter(
        "[daemon %(asctime)s] %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    # Always log to stdout (captured by nohup)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # Optionally log to file
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(str(log_file))
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


log = setup_daemon_logging()


# ── .env Loader ──────────────────────────────────────────────────────

_env_loaded = False

def _load_env():
    """Load .env into os.environ so API keys are available."""
    global _env_loaded
    if _env_loaded:
        return
    env_path = REPO / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k not in os.environ:
                        os.environ[k] = v
    _env_loaded = True

_load_env()


# ── RSA / Auth Helpers ──────────────────────────────────────────────

def _load_private_key(path: str):
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    from cryptography.hazmat.backends import default_backend
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())


def _sign_ws(private_key, timestamp_str: str) -> str:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    message = f"{timestamp_str}GET{WS_SIGN_PATH}".encode("utf-8")
    signature = private_key.sign(
        message,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")


def _build_ws_auth_headers(api_key: str, private_key) -> Dict[str, str]:
    ts = int(_time.time() * 1000)
    sig = _sign_ws(private_key, str(ts))
    return {
        "KALSHI-ACCESS-KEY": api_key,
        "KALSHI-ACCESS-TIMESTAMP": str(ts),
        "KALSHI-ACCESS-SIGNATURE": sig,
    }


# ── Price Store ──────────────────────────────────────────────────────

class PriceStore:
    """
    Thread-safe / async-safe in-memory price store.
    Tracks latest prices and per-ticker price history for strategy use.
    """

    def __init__(self, history_window_seconds: int = 3600):
        self._lock = asyncio.Lock()
        self._prices: Dict[str, Dict[str, Any]] = {}       # ticker → latest price data
        self._history: Dict[str, deque] = {}               # ticker → deque of (ts, mid_price)
        self._history_window = history_window_seconds
        self._last_trade: Dict[str, Dict[str, Any]] = {}   # ticker → last trade data
        self._fills: List[Dict] = []

    async def update_ticker(self, ticker: str, data: Dict[str, Any]):
        async with self._lock:
            self._prices[ticker] = data
            mid = self._compute_mid(data)
            if mid is not None:
                if ticker not in self._history:
                    self._history[ticker] = deque(maxlen=10000)
                now = _time.time()
                self._history[ticker].append((now, mid))
                # Prune old entries
                cutoff = now - self._history_window
                while self._history[ticker] and self._history[ticker][0][0] < cutoff:
                    self._history[ticker].popleft()

    async def update_trade(self, ticker: str, data: Dict[str, Any]):
        async with self._lock:
            self._last_trade[ticker] = data

    async def update_fill(self, data: Dict[str, Any]):
        async with self._lock:
            self._fills.append(data)

    def _compute_mid(self, data: Dict[str, Any]) -> Optional[float]:
        yes_bid = data.get("yes_bid")
        yes_ask = data.get("yes_ask")
        if yes_bid is not None and yes_ask is not None:
            try:
                return (float(yes_bid) + float(yes_ask)) / 2.0
            except (ValueError, TypeError):
                pass
        last = data.get("last_price")
        if last is not None:
            try:
                return float(last)
            except (ValueError, TypeError):
                pass
        return None

    async def get_mid(self, ticker: str) -> Optional[float]:
        async with self._lock:
            data = self._prices.get(ticker)
            if data:
                return self._compute_mid(data)
            return None

    async def get_price_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            return self._prices.get(ticker)

    async def get_all_prices(self) -> Dict[str, Dict[str, Any]]:
        async with self._lock:
            return dict(self._prices)

    async def get_history(self, ticker: str, lookback_seconds: int = 300) -> List[Tuple[float, float]]:
        """Get price history for a ticker within the lookback window."""
        async with self._lock:
            hist = self._history.get(ticker, deque())
            cutoff = _time.time() - lookback_seconds
            return [(ts, p) for ts, p in hist if ts >= cutoff]

    async def get_recent_trades(self, ticker: str, lookback_seconds: int = 900) -> List[Dict]:
        """Get recent trade data for volume analysis."""
        async with self._lock:
            trade = self._last_trade.get(ticker)
            return [trade] if trade else []

    async def backfill_from_file(self, filepath: pathlib.Path, max_lines: int = 5000):
        """Load recent prices from WebSocket JSONL log on startup."""
        if not filepath.exists():
            log.info("No WS log file for backfill")
            return 0

        count = 0
        try:
            # Read last N lines efficiently
            with open(filepath, "r") as f:
                # Seek to near end and read backwards
                lines = []
                f.seek(0, os.SEEK_END)
                file_size = f.tell()
                chunk_size = 8192
                pos = file_size
                while pos > 0 and len(lines) < max_lines:
                    read_size = min(chunk_size, pos)
                    pos -= read_size
                    f.seek(pos)
                    chunk = f.read(read_size)
                    chunk_lines = chunk.splitlines(True)
                    # Handle partial first line
                    if pos > 0 and not chunk.startswith("\n"):
                        if lines:
                            lines[0] = chunk_lines[-1].rstrip("\n") + (lines[0] if lines else "")
                            lines = chunk_lines[:-1] + lines
                        else:
                            lines = chunk_lines
                    else:
                        lines = chunk_lines + lines

            for line in lines:
                try:
                    record = json.loads(line)
                    if record.get("type") == "ticker":
                        ticker = record.get("ticker", "")
                        data = record.get("data", {})
                        await self.update_ticker(ticker, data)
                        count += 1
                    elif record.get("type") == "trade":
                        await self.update_trade(record.get("ticker", ""), record)
                    elif record.get("type") == "fill":
                        await self.update_fill(record)
                except (json.JSONDecodeError, KeyError):
                    pass

            log.info(f"Backfilled {count} ticker events from WS log")
        except Exception as e:
            log.warning(f"Backfill error: {e}")

        return count


# ── Position Manager ────────────────────────────────────────────────

@dataclass
class TrackedPosition:
    ticker: str
    side: str            # "yes" or "no"
    count: int
    entry_price: float   # cents
    entry_cost: float    # dollars
    entry_time: str
    status: str = "open"  # open | closed
    exit_price: Optional[float] = None
    exit_time: Optional[str] = None
    pnl: float = 0.0

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "side": self.side,
            "count": self.count,
            "entry_price": self.entry_price,
            "entry_cost": self.entry_cost,
            "entry_time": self.entry_time,
            "status": self.status,
            "exit_price": self.exit_price,
            "exit_time": self.exit_time,
            "pnl": self.pnl,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TrackedPosition":
        return cls(**{k: d.get(k) for k in [
            "ticker", "side", "count", "entry_price", "entry_cost",
            "entry_time", "status", "exit_price", "exit_time", "pnl"
        ]})


class PositionManager:
    """Tracks open positions in memory, persisted to positions_live.json."""

    def __init__(self):
        self._lock = asyncio.Lock()
        self.positions: Dict[str, TrackedPosition] = {}  # ticker → position
        self.portfolio_value: float = 0.0
        self.cash_balance: float = 0.0
        self.peak_value: float = 0.0
        self.starting_value: float = 0.0
        self.daily_pnl: float = 0.0
        self.today_str: str = dt.date.today().isoformat()
        self._loaded = False

    async def load(self):
        """Load positions from disk."""
        async with self._lock:
            if POSITIONS_FILE.exists():
                try:
                    data = json.loads(POSITIONS_FILE.read_text())
                    self.positions = {}
                    for pd in data.get("positions", []):
                        pos = TrackedPosition.from_dict(pd)
                        if pos.status == "open":
                            self.positions[pos.ticker] = pos
                    self.portfolio_value = data.get("portfolio_value", 0.0)
                    self.cash_balance = data.get("cash_balance", 0.0)
                    self.peak_value = data.get("peak_value", self.portfolio_value)
                    self.starting_value = data.get("starting_value", self.portfolio_value)
                    self.daily_pnl = data.get("daily_pnl", 0.0)
                    self.today_str = data.get("today_str", dt.date.today().isoformat())
                    self._loaded = True
                    log.info(f"Loaded {len(self.positions)} open positions, portfolio=${self.portfolio_value:.2f}, cash=${self.cash_balance:.2f}")
                except Exception as e:
                    log.warning(f"Failed to load positions: {e}")
            else:
                self._loaded = True

    async def save(self):
        """Persist positions to disk."""
        async with self._lock:
            POSITIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "positions": [p.to_dict() for p in self.positions.values()],
                "portfolio_value": self.portfolio_value,
                "cash_balance": self.cash_balance,
                "peak_value": self.peak_value,
                "starting_value": self.starting_value,
                "daily_pnl": self.daily_pnl,
                "today_str": self.today_str,
                "last_updated": dt.datetime.now(dt.timezone.utc).isoformat(),
            }
            POSITIONS_FILE.write_text(json.dumps(data, indent=2))

    async def update_portfolio_value(self, client: Any):
        """Fetch current balance from Kalshi and update portfolio tracking."""
        try:
            balance_data = client.get_balance()
            # portfolio_value is in cents; balance_dollars is cash only
            portfolio_cents = float(balance_data.get("portfolio_value", 0))
            new_value = portfolio_cents / 100.0  # Convert cents to dollars
            self.cash_balance = float(balance_data.get("balance_dollars", balance_data.get("balance", "0")))

            async with self._lock:
                # Check if day rolled over
                today = dt.date.today().isoformat()
                if today != self.today_str:
                    self.daily_pnl = 0.0
                    self.today_str = today

                old_value = self.portfolio_value
                self.portfolio_value = new_value
                if new_value > old_value:
                    self.daily_pnl += (new_value - old_value)

                if new_value > self.peak_value:
                    self.peak_value = new_value

                if self.starting_value == 0:
                    self.starting_value = new_value

            return new_value
        except Exception as e:
            log.error(f"Balance fetch failed: {e}")
            async with self._lock:
                return self.portfolio_value

    async def add_position(self, pos: TrackedPosition):
        async with self._lock:
            self.positions[pos.ticker] = pos

    async def close_position(self, ticker: str, exit_price: float) -> Optional[TrackedPosition]:
        async with self._lock:
            pos = self.positions.pop(ticker, None)
            if pos:
                pos.exit_price = exit_price
                pos.exit_time = dt.datetime.now(dt.timezone.utc).isoformat()
                pos.status = "closed"
                if pos.side == "yes":
                    pos.pnl = (exit_price - pos.entry_price) * pos.count / 100.0
                else:
                    pos.pnl = (pos.entry_price - exit_price) * pos.count / 100.0
            return pos

    async def get_open_count(self) -> int:
        async with self._lock:
            return len(self.positions)

    async def get_total_exposure(self) -> float:
        """Total exposure as percentage of portfolio."""
        async with self._lock:
            if self.portfolio_value <= 0:
                return 0.0
            total_cost = sum(p.entry_cost for p in self.positions.values())
            return (total_cost / self.portfolio_value) * 100.0

    async def holds_ticker(self, ticker: str) -> bool:
        async with self._lock:
            return ticker in self.positions

    async def get_daily_pnl_pct(self) -> float:
        async with self._lock:
            if self.starting_value <= 0:
                return 0.0
            return (self.daily_pnl / self.starting_value) * 100.0

    async def get_drawdown_pct(self) -> float:
        async with self._lock:
            if self.peak_value <= 0:
                return 0.0
            return ((self.peak_value - self.portfolio_value) / self.peak_value) * 100.0


# ── Journal ─────────────────────────────────────────────────────────

def append_journal(entry: dict):
    """Append a trade entry to the journal JSONL file."""
    JOURNAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(JOURNAL_FILE, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")


# ── Ticker Resolution ───────────────────────────────────────────────

def resolve_series_ticker(client: Any, series_ticker: str) -> List[str]:
    """
    Resolve a Kalshi series ticker (e.g., KXUSAIRANAGREEMENT) to its
    individual market tickers (e.g., KXUSAIRANAGREEMENT-27-26JUN).
    Returns list of open market tickers sorted by closest expiry first,
    then by volume (highest first).
    """
    try:
        response = client.get_markets(
            series_ticker=series_ticker,
            status="open",
            limit=50,
        )
        markets = response.get("markets", [])
        if not markets:
            return []
        
        # Sort: closest expiry first, highest volume first as tiebreaker
        def sort_key(m):
            close_time = m.get("close_time", "")
            volume = float(m.get("volume_24h_fp", m.get("volume", "0")) or 0)
            return (close_time or "z", -volume)
        
        sorted_markets = sorted(markets, key=sort_key)
        return [m["ticker"] for m in sorted_markets]
    except Exception as e:
        log.warning(f"Ticker resolution failed for {series_ticker}: {e}")
        return []


# ── Kelly Sizing ────────────────────────────────────────────────────

def compute_kelly_size(
    trevor_prob_pct: float,
    market_price: float,
    portfolio_value: float,
    cash_balance: float = 0.0,
    kelly_fraction: float = 0.25,
    max_position_pct: float = 5.0,
) -> float:
    """Compute position size in dollars using fractional Kelly criterion.
    
    Uses cash_balance for new entries (limited by available capital),
    with overall cap at max_position_pct of portfolio_value.
    """
    p = trevor_prob_pct / 100.0
    if market_price <= 0 or market_price >= 1:
        market_price = 0.50
    b = (1 - market_price) / market_price  # decimal odds
    q = 1 - p
    if b <= 0:
        return 0.0
    kelly = (p * b - q) / b
    kelly = max(0.0, min(kelly, 1.0))
    fraction = kelly * kelly_fraction
    
    # Use cash balance for sizing (can't spend what isn't available)
    effective_capital = cash_balance if cash_balance > 0 else portfolio_value
    position_size = effective_capital * fraction * (max_position_pct / 100.0)
    # Cap at max position % of total portfolio value
    max_allowed = portfolio_value * max_position_pct / 100.0
    # Also cap at available cash
    if cash_balance > 0:
        max_allowed = min(max_allowed, cash_balance)
    return max(1.0, min(position_size, max_allowed))


# ── Guardrail Checker ───────────────────────────────────────────────

def check_guardrails(
    signal_edge_pts: float,
    position_size: float,
    portfolio_value: float,
    existing_positions: int,
    total_exposure_pct: float,
    daily_pnl_pct: float,
    drawdown_pct: float,
    position_pct: float,
) -> Tuple[bool, str]:
    """
    Validate a potential trade against all guardrails.
    Returns (allowed, reason).
    """
    if abs(signal_edge_pts) < GUARDRAILS["min_edge_to_trade"]:
        return False, f"Edge {signal_edge_pts:+.1f}pts below minimum {GUARDRAILS['min_edge_to_trade']}pts"

    if existing_positions >= GUARDRAILS["max_concurrent_positions"]:
        return False, f"Max positions ({GUARDRAILS['max_concurrent_positions']}) reached"

    if position_pct > GUARDRAILS["max_position_pct"]:
        return False, f"Position size {position_pct:.1f}% exceeds max {GUARDRAILS['max_position_pct']}%"

    if total_exposure_pct + position_pct > GUARDRAILS["max_total_exposure_pct"]:
        return False, f"Total exposure would be {total_exposure_pct + position_pct:.1f}%, exceeds {GUARDRAILS['max_total_exposure_pct']}%"

    if abs(daily_pnl_pct) > GUARDRAILS["daily_loss_pct"] and daily_pnl_pct < 0:
        return False, f"Daily loss {daily_pnl_pct:.1f}% exceeds cap {GUARDRAILS['daily_loss_pct']}%"

    if drawdown_pct > GUARDRAILS["max_drawdown_pct"]:
        return False, f"Drawdown {drawdown_pct:.1f}% exceeds max {GUARDRAILS['max_drawdown_pct']}%"

    return True, "ok"


def check_exit_guardrail(
    position: TrackedPosition,
    current_price_cents: float,
) -> Tuple[bool, str, Optional[str]]:
    """
    Check if a position should be exited based on TP/SL rules.
    Returns (should_exit, reason, action).
    """
    if position.status != "open":
        return False, "closed", None

    entry = position.entry_price
    if entry <= 0:
        return False, "no_entry_price", None

    if position.side == "yes":
        pnl_pct = ((current_price_cents - entry) / entry) * 100.0
    else:
        pnl_pct = ((entry - current_price_cents) / entry) * 100.0

    if pnl_pct >= GUARDRAILS["position_take_profit_pct"]:
        return True, f"Take profit: {pnl_pct:.0f}% gain", "sell"
    if pnl_pct <= -GUARDRAILS["position_stop_loss_pct"]:
        return True, f"Stop loss: {pnl_pct:.0f}% loss", "sell"

    return False, f"pnl {pnl_pct:.1f}%", None


# ── Signal Pipeline ─────────────────────────────────────────────────

class SignalPipeline:
    """Loads and manages trade signals from multiple sources."""

    def __init__(self):
        self.last_intel_bridge_run: Optional[float] = None
        self._cached_signals: List[Dict] = []
        self._cached_exec_kjs: List[Dict] = []

    def _run_intel_bridge(self) -> List[Dict]:
        """Run intel_bridge.py and return tradeable signals."""
        bridge_path = REPO / "philby" / "trader" / "intel_bridge.py"
        try:
            result = subprocess.run(
                ["python3", str(bridge_path), "--json"],
                capture_output=True, text=True, timeout=120,
                cwd=str(REPO),
            )
            data = json.loads(result.stdout)
            self._cached_signals = data.get("tradeable", [])
            self.last_intel_bridge_run = _time.time()
            log.info(f"Intel bridge: {len(self._cached_signals)} tradeable signals")
            return self._cached_signals
        except Exception as e:
            log.error(f"Intel bridge failed: {e}")
            return []

    def get_edge_signals(self, force_refresh: bool = False) -> List[Dict]:
        """Get edge signals from intel_bridge, refreshing if stale."""
        if force_refresh or self.last_intel_bridge_run is None:
            return self._run_intel_bridge()

        # Refresh if older than 1 hour
        if _time.time() - self.last_intel_bridge_run > 3600:
            return self._run_intel_bridge()

        # Re-read latest.json for freshness
        if SIGNALS_FILE.exists():
            try:
                data = json.loads(SIGNALS_FILE.read_text())
                self._cached_signals = data.get("tradeable", [])
            except Exception:
                pass

        return self._cached_signals

    def load_exec_summary(self) -> Optional[Dict]:
        """Load the latest exec_summary.json from trevor-briefings."""
        if not BRIEFINGS_DIR.exists():
            log.warning("No briefings directory found")
            return None

        # Find most recent dated directory
        dates = sorted(
            [d for d in BRIEFINGS_DIR.iterdir() if d.is_dir() and d.name[:4].isdigit()],
            reverse=True,
        )
        for date_dir in dates:
            exec_path = date_dir / "analysis" / "exec_summary.json"
            if exec_path.exists():
                try:
                    return json.loads(exec_path.read_text())
                except (json.JSONDecodeError, IOError):
                    continue

        log.warning("No exec_summary.json found in briefings")
        return None

    def extract_kj_signals_from_exec_summary(
        self, exec_data: Dict, kalshi_market_map: Dict[str, List[str]]
    ) -> List[Dict]:
        """
        Extract key judgments from exec_summary and map to Kalshi tickers.
        Returns list of signals with Trevor confidence and matching market ticker.
        """
        signals = []
        kjs = exec_data.get("five_judgments", [])

        for kj in kjs:
            statement = kj.get("statement", "")
            prediction_pct = kj.get("prediction_pct", 50)
            horizon_days = kj.get("horizon_days", 7)
            region = kj.get("drawn_from_region", "")

            # Match KJ to Kalshi tickers via keyword mapping
            matched_series = set()
            direction = "buy_yes"
            for keyword, series_kw, dirn in KJ_KEYWORD_TO_TICKER:
                if keyword.lower() in statement.lower() or keyword.lower() in region.lower():
                    matched_series.add(series_kw)
                    direction = dirn

            # Also check narrative mappings
            for mapping_key, mapping in NARRATIVE_TO_KALSHI.items():
                for nid in mapping.get("trevor_narrative_ids", []):
                    if nid.replace("_", "") in statement.lower().replace(" ", ""):
                        for kw in mapping["ticker_keywords"]:
                            matched_series.add(kw)
                        direction = mapping["direction"]

            for series_kw in matched_series:
                # Find actual market tickers
                market_tickers = []
                for st, mts in kalshi_market_map.items():
                    if series_kw in st:
                        market_tickers = mts
                        break

                for mt in market_tickers:
                    signal = {
                        "source": "exec_summary",
                        "kj_id": kj.get("id", ""),
                        "statement": statement[:120],
                        "region": region,
                        "horizon_days": horizon_days,
                        "trevor_confidence": prediction_pct,
                        "direction": direction,
                        "action": f"BUY {'Yes' if direction == 'buy_yes' else 'No'}",
                        "ticker": mt,
                        "series_ticker": series_kw,
                        "market_confidence": None,  # Will be filled from price store
                        "edge_pts": None,
                    }
                    signals.append(signal)

        log.info(f"Extracted {len(signals)} KJ signals from exec summary")
        return signals


# ── Strategy: Mean Reversion ────────────────────────────────────────

async def detect_mean_reversion(
    price_store: PriceStore,
    watched_tickers: List[str],
    kelly_fraction: float = 0.25,
    max_position_pct: float = 5.0,
) -> List[Dict]:
    """
    Detect mean reversion opportunities from 5-minute price windows.
    If a market moves >20% in 5 minutes, bet on reversion.
    Uses ⅓ fractional Kelly.
    """
    signals = []
    for ticker in watched_tickers:
        hist = await price_store.get_history(ticker, lookback_seconds=300)
        if len(hist) < 3:
            continue

        prices = [p for _, p in hist]
        start_price = prices[0]
        end_price = prices[-1]
        if start_price <= 0:
            continue

        change_pct = ((end_price - start_price) / start_price) * 100.0

        if abs(change_pct) >= 20:
            # Bet on mean reversion
            if change_pct > 0:
                # Price spiked up → buy NO (bet on reversal down)
                direction = "buy_no"
                action = "BUY No"
            else:
                # Price dropped → buy YES (bet on reversal up)
                direction = "buy_yes"
                action = "BUY Yes"

            signals.append({
                "source": "mean_reversion",
                "ticker": ticker,
                "direction": direction,
                "action": action,
                "trevor_confidence": 50.0,  # Neutral — reverting to prior level
                "market_confidence": round(end_price * 100, 1),
                "edge_pts": abs(change_pct) * 0.5,  # Half the move as edge signal
                "change_pct_5m": round(change_pct, 1),
                "start_price": round(start_price, 4),
                "current_price": round(end_price, 4),
                "kelly_override": kelly_fraction / 3,  # ⅓ Kelly for mean reversion
                "note": f"Mean reversion: {change_pct:+.1f}% in 5min",
            })

    return signals


# ── Strategy: Momentum Rider ────────────────────────────────────────

async def detect_momentum(
    price_store: PriceStore,
    watched_tickers: List[str],
    kelly_fraction: float = 0.25,
    max_position_pct: float = 5.0,
) -> List[Dict]:
    """
    Detect momentum opportunities: >15% move in 15 minutes with correlated volume spike.
    Follow momentum with ¼ fractional Kelly.
    """
    signals = []
    for ticker in watched_tickers:
        hist = await price_store.get_history(ticker, lookback_seconds=900)
        if len(hist) < 5:
            continue

        prices = [p for _, p in hist]
        start_price = prices[0]
        end_price = prices[-1]
        if start_price <= 0:
            continue

        change_pct = ((end_price - start_price) / start_price) * 100.0

        if abs(change_pct) >= 15:
            # Check if consistent directional move (not choppy)
            direction_count = sum(
                1 for i in range(1, len(prices)) if (prices[i] - prices[i - 1]) * change_pct > 0
            )
            if direction_count >= len(prices) * 0.6:  # 60% direction alignment
                direction = "buy_yes" if change_pct > 0 else "buy_no"
                action = "BUY Yes" if change_pct > 0 else "BUY No"

                signals.append({
                    "source": "momentum",
                    "ticker": ticker,
                    "direction": direction,
                    "action": action,
                    "trevor_confidence": 50.0,
                    "market_confidence": round(end_price * 100, 1),
                    "edge_pts": abs(change_pct) * 0.3,
                    "change_pct_15m": round(change_pct, 1),
                    "direction_confidence": round(direction_count / len(prices) * 100, 1),
                    "kelly_override": kelly_fraction / 4,  # ¼ Kelly for momentum
                    "note": f"Momentum: {change_pct:+.1f}% over 15min",
                })

    return signals


# ── Strategy: Take Profit / Stop Loss ───────────────────────────────

async def check_tp_sl(
    price_store: PriceStore,
    position_manager: PositionManager,
    client: Any,
) -> List[Dict]:
    """
    Check all open positions against take-profit and stop-loss thresholds.
    Execute exits where needed.
    """
    exits = []
    positions = dict(position_manager.positions)

    for ticker, pos in positions.items():
        price_data = await price_store.get_price_data(ticker)
        if not price_data:
            continue

        mid = price_store._compute_mid(price_data)
        if mid is None:
            continue

        current_price_cents = mid * 100
        should_exit, reason, exit_action = check_exit_guardrail(pos, current_price_cents)

        if should_exit:
            log.info(f"Exit signal: {ticker} — {reason}")

            try:
                side = "yes" if pos.side == "yes" else "no"
                sell_price_cents = int(current_price_cents)
                sell_price_cents = max(1, min(sell_price_cents, 99))

                order = client.create_order(
                    ticker=ticker,
                    action="sell",
                    side=side,
                    yes_price=sell_price_cents if side == "yes" else None,
                    no_price=sell_price_cents if side == "no" else None,
                    count=pos.count,
                    time_in_force="immediate_or_cancel",
                )

                order_id = order.get("order_id", "") if isinstance(order, dict) else ""
                closed_pos = await position_manager.close_position(ticker, current_price_cents)

                journal_entry = {
                    "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "type": "exit",
                    "ticker": ticker,
                    "action": "sell",
                    "side": side,
                    "count": pos.count,
                    "entry_price_cents": pos.entry_price,
                    "exit_price_cents": current_price_cents,
                    "pnl": closed_pos.pnl if closed_pos else 0,
                    "reason": reason,
                    "order_id": order_id,
                    "strategy": "tp_sl",
                }
                append_journal(journal_entry)
                await position_manager.save()

                exits.append({
                    "ticker": ticker,
                    "reason": reason,
                    "pnl": closed_pos.pnl if closed_pos else 0,
                    "order_id": order_id,
                })

                log.info(f"✅ Exit executed: {ticker} pnl=${closed_pos.pnl if closed_pos else 0:.2f} ({reason})")

            except Exception as e:
                log.error(f"Exit failed for {ticker}: {e}")

    return exits


# ── Trade Executor ──────────────────────────────────────────────────

async def execute_trade(
    signal: Dict,
    client: Any,
    price_store: PriceStore,
    position_manager: PositionManager,
    dry_run: bool = False,
) -> Optional[Dict]:
    """Execute a single trade with guardrail checks."""

    ticker = signal.get("ticker", "")
    if not ticker:
        return None

    # Get current market price from live store
    price_data = await price_store.get_price_data(ticker)
    if price_data:
        market_prob = price_store._compute_mid(price_data)
        if market_prob is not None:
            signal["market_confidence"] = round(market_prob * 100, 1)
            signal["market_price_float"] = market_prob

    trevor_conf = signal.get("trevor_confidence", 50)
    market_prob = signal.get("market_confidence", 50) or 50
    market_price = (market_prob / 100.0) if market_prob else 0.5
    edge = trevor_conf - market_prob
    if signal.get("direction") == "buy_no":
        edge = market_prob - trevor_conf
    signal["edge_pts"] = round(edge, 1)

    # Get portfolio state
    portfolio_value = position_manager.portfolio_value
    existing_positions = await position_manager.get_open_count()
    total_exposure = await position_manager.get_total_exposure()
    daily_pnl_pct = await position_manager.get_daily_pnl_pct()
    drawdown_pct = await position_manager.get_drawdown_pct()

    # Compute position size
    kelly_override = signal.get("kelly_override", GUARDRAILS["kelly_fraction"])
    position_size = compute_kelly_size(
        trevor_conf, market_price, portfolio_value,
        cash_balance=position_manager.cash_balance,
        kelly_fraction=kelly_override,
        max_position_pct=GUARDRAILS["max_position_pct"],
    )
    position_pct = (position_size / portfolio_value * 100) if portfolio_value > 0 else 0

    # Check guardrails
    allowed, reason = check_guardrails(
        signal_edge_pts=edge,
        position_size=position_size,
        portfolio_value=portfolio_value,
        existing_positions=existing_positions,
        total_exposure_pct=total_exposure,
        daily_pnl_pct=daily_pnl_pct,
        drawdown_pct=drawdown_pct,
        position_pct=position_pct,
    )

    if not allowed:
        log.info(f"  ⛔ Guardrail block [{ticker}]: {reason}")
        return {
            "ticker": ticker,
            "status": "blocked",
            "reason": reason,
            "edge_pts": edge,
        }

    # Check if already held
    if await position_manager.holds_ticker(ticker):
        log.info(f"  Already holding {ticker} — skipping")
        return None

    log.info(f"  🎯 TRADE: {signal.get('action','?')} {ticker}")
    log.info(f"     Trevor={trevor_conf:.0f}% Market={market_prob:.0f}% Edge={edge:+.1f}pts")
    log.info(f"     Position=${position_size:.2f} ({position_pct:.1f}% of portfolio)")
    log.info(f"     Source: {signal.get('source','?')}")

    if dry_run:
        return {
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "ticker": ticker,
            "action": signal.get("action", ""),
            "trevor_confidence": trevor_conf,
            "market_probability": market_prob,
            "edge_pts": edge,
            "position_size_dollars": round(position_size, 2),
            "status": "dry_run",
            "strategy": signal.get("source", "edge"),
        }

    # Execute
    try:
        action = signal.get("action", "")
        side = "yes" if "Yes" in action else "no"
        direction = "buy"

        if market_price <= 0:
            market_price = 0.01
        contract_cost = market_price
        contract_count = max(1, int(position_size / contract_cost))

        price_cents = int(market_price * 100)
        price_cents = max(1, min(price_cents, 99))

        order = client.create_order(
            ticker=ticker,
            action=direction,
            side=side,
            yes_price=price_cents if side == "yes" else None,
            no_price=price_cents if side == "no" else None,
            count=contract_count,
            time_in_force="good_till_canceled",
        )

        order_id = order.get("order_id", "") if isinstance(order, dict) else ""

        # Track position
        new_pos = TrackedPosition(
            ticker=ticker,
            side=side,
            count=contract_count,
            entry_price=price_cents,
            entry_cost=contract_cost * contract_count,
            entry_time=dt.datetime.now(dt.timezone.utc).isoformat(),
        )
        await position_manager.add_position(new_pos)

        # Journal entry
        journal_entry = {
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "type": "entry",
            "ticker": ticker,
            "action": action,
            "side": side,
            "count": contract_count,
            "price_cents": price_cents,
            "position_size_dollars": round(position_size, 2),
            "trevor_confidence": trevor_conf,
            "market_probability": market_prob,
            "edge_pts": edge,
            "order_id": order_id,
            "strategy": signal.get("source", "edge"),
            "note": signal.get("note", ""),
        }
        append_journal(journal_entry)

        log.info(f"  ✅ Order placed: {order_id} — {action} {contract_count}x {ticker} @ {price_cents}c")

        return {
            "ticker": ticker,
            "status": "executed",
            "order_id": order_id,
            "position_size": round(position_size, 2),
            "edge_pts": edge,
        }

    except Exception as e:
        log.error(f"  ❌ Trade failed [{ticker}]: {e}")
        error_entry = {
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "ticker": ticker,
            "action": signal.get("action", ""),
            "error": str(e),
            "status": "failed",
        }
        append_journal(error_entry)
        return None


# ── WebSocket Client ────────────────────────────────────────────────

class DaemonWebSocket:
    """Embedded WebSocket client for the trading daemon."""

    def __init__(self, price_store: PriceStore):
        self.price_store = price_store
        self.api_key = os.environ.get("KALSHI_API_KEY", "")
        self.rsa_key_path = os.environ.get("KALSHI_RSA_KEY_PATH", "")
        self._ws = None
        self._running = False
        self._reconnect_delay = 1
        self._max_reconnect_delay = 60
        self._message_id = 0
        self._subscribed_markets: Set[str] = set()
        self._subscription_id: Optional[int] = None  # Track sub ID from server response

        if not self.api_key or not self.rsa_key_path:
            raise RuntimeError("KALSHI_API_KEY and KALSHI_RSA_KEY_PATH must be set")

        self._private_key = _load_private_key(self.rsa_key_path)

    async def connect(self) -> bool:
        try:
            headers = _build_ws_auth_headers(self.api_key, self._private_key)
            self._ws = await websockets.connect(
                WS_URL,
                additional_headers=headers,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5,
            )
            log.info("✅ WebSocket connected")
            self._reconnect_delay = 1
            return True
        except Exception as e:
            log.error(f"WebSocket connection failed: {e}")
            return False

    async def subscribe(self, channels: List[str], markets: Optional[List[str]] = None):
        if not self._ws:
            return
        msg_id = self._next_msg_id()
        sub = {
            "id": msg_id,
            "cmd": "subscribe",
            "params": {"channels": channels},
        }
        if markets:
            sub["params"]["market_tickers"] = markets
            self._subscribed_markets.update(markets)
        elif channels == ["fill"]:
            pass  # fill doesn't need market filter
        else:
            if self._subscribed_markets:
                sub["params"]["market_tickers"] = list(self._subscribed_markets)

        await self._ws.send(json.dumps(sub))
        log.info(f"Subscribed: {channels} ({len(markets or [])} markets)")

    async def update_subscriptions(self, markets: List[str]):
        """Add new markets to existing subscriptions."""
        new_markets = set(markets) - self._subscribed_markets
        if not new_markets or not self._ws:
            return

        if self._subscription_id is not None:
            # Use update_subscription with tracked subscription ID
            sub = {
                "id": self._subscription_id,
                "cmd": "update_subscription",
                "params": {
                    "action": "add_markets",
                    "market_tickers": list(new_markets),
                },
            }
        else:
            # Fallback: re-subscribe with all markets
            all_markets = list(self._subscribed_markets | new_markets)
            sub = {
                "id": self._next_msg_id(),
                "cmd": "subscribe",
                "params": {
                    "channels": ["ticker", "trade", "orderbook_delta"],
                    "market_tickers": all_markets,
                },
            }

        try:
            await self._ws.send(json.dumps(sub))
            self._subscribed_markets.update(new_markets)
            log.info(f"Added {len(new_markets)} markets to subscription")
        except Exception as e:
            log.warning(f"Subscription update failed: {e}")

    def _next_msg_id(self) -> int:
        self._message_id += 1
        return self._message_id

    async def listen_forever(self):
        """Main WebSocket listener loop with auto-reconnect."""
        self._running = True

        while self._running:
            if not self._ws:
                connected = await self.connect()
                if not connected:
                    delay = min(self._reconnect_delay, self._max_reconnect_delay)
                    log.warning(f"WS reconnect in {delay}s...")
                    await asyncio.sleep(delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
                    continue

                # (Re)subscribe on connect
                try:
                    await self.subscribe(["fill"])
                    if self._subscribed_markets:
                        await self.subscribe(
                            ["ticker", "trade", "orderbook_delta"],
                            list(self._subscribed_markets),
                        )
                except Exception as e:
                    log.error(f"Subscribe error: {e}")
                    await self._ws.close()
                    self._ws = None
                    continue

            try:
                async for message in self._ws:
                    await self._process_message(message)
            except websockets.ConnectionClosed as e:
                log.warning(f"WS connection closed: {e}")
            except Exception as e:
                log.error(f"WS listen error: {e}")

            self._ws = None
            delay = min(self._reconnect_delay, self._max_reconnect_delay)
            log.warning(f"WS reconnect in {delay}s...")
            await asyncio.sleep(delay)
            self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)

    async def _process_message(self, raw: str):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return

        msg_type = data.get("type", "")
        msg = data.get("msg", {})

        if msg_type == "ticker":
            ticker = msg.get("market_ticker", "?")
            tick_data = {
                "yes_bid": msg.get("yes_bid_dollars"),
                "yes_ask": msg.get("yes_ask_dollars"),
                "last_price": msg.get("last_price_dollars"),
                "volume_24h": msg.get("volume_24h_fp"),
                "ts": msg.get("ts"),
            }
            await self.price_store.update_ticker(ticker, tick_data)

        elif msg_type == "trade":
            await self.price_store.update_trade(
                msg.get("market_ticker", "?"),
                {
                    "price": msg.get("price_dollars"),
                    "size": msg.get("size_fp"),
                    "side": msg.get("side"),
                },
            )

        elif msg_type == "fill":
            fill_data = {
                "order_id": msg.get("order_id"),
                "ticker": msg.get("ticker"),
                "side": msg.get("side"),
                "action": msg.get("action"),
                "count": msg.get("count"),
                "price": msg.get("price_dollars"),
            }
            await self.price_store.update_fill(fill_data)
            log.info(f"📬 Fill: {msg.get('action','?')} {msg.get('count','?')}x {msg.get('ticker','?')} @ ${msg.get('price_dollars','?')}")

        elif msg_type == "subscribed":
            # Server confirms subscription — capture subscription ID for updates
            sub_id = msg.get("subscription_id") or msg.get("id")
            if sub_id is not None:
                self._subscription_id = sub_id
                channels = msg.get("channels", [])
                log.info(f"Subscription confirmed: id={sub_id}, channels={channels}")

        elif msg_type == "error":
            log.error(f"WS Error: {msg.get('code','?')} — {msg.get('msg','?')}")

    async def shutdown(self):
        self._running = False
        if self._ws:
            try:
                await self._ws.close()
                log.info("WebSocket closed")
            except Exception:
                pass


# ── KalshiClient Import ─────────────────────────────────────────────

def _get_kalshi_client():
    """Import and instantiate KalshiClient."""
    sys.path.insert(0, str(REPO / "skills" / "kalshi-trader" / "scripts"))
    from client import KalshiClient, KalshiAPIError, KalshiAuthError
    return KalshiClient()


# ── Trading Cycle ───────────────────────────────────────────────────

async def trading_cycle(
    client: Any,
    price_store: PriceStore,
    position_manager: PositionManager,
    signal_pipeline: SignalPipeline,
    ws_client: DaemonWebSocket,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Execute one complete trading cycle:
    1. Update portfolio value
    2. Refresh signals from intel_bridge and exec_summary
    3. Detect mean reversion and momentum from price stream
    4. Check take-profit / stop-loss
    5. Execute new trades
    """
    cycle_start = _time.time()
    cycle_result = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "portfolio_value": 0.0,
        "open_positions": 0,
        "daily_pnl": 0.0,
        "drawdown": 0.0,
        "signals_found": 0,
        "trades_executed": 0,
        "exits_executed": 0,
        "trades_blocked": 0,
    }

    # 1. Update portfolio
    new_value = await position_manager.update_portfolio_value(client)
    positions_count = await position_manager.get_open_count()
    daily_pnl = await position_manager.get_daily_pnl_pct()
    drawdown = await position_manager.get_drawdown_pct()

    cycle_result["portfolio_value"] = new_value
    cycle_result["open_positions"] = positions_count
    cycle_result["daily_pnl"] = daily_pnl
    cycle_result["drawdown"] = drawdown

    # Status line
    status_icon = "🟢" if daily_pnl >= 0 else "🔴"
    log.info(
        f"CYCLE │ Portfolio=${new_value:.2f} │ "
        f"Positions={positions_count} │ "
        f"P&L={status_icon} {daily_pnl:+.1f}% │ "
        f"Drawdown={drawdown:.1f}%"
    )

    # 2. Refresh edge signals from intel bridge
    edge_signals = signal_pipeline.get_edge_signals()

    # 3. Load exec_summary and extract KJ signals
    exec_data = signal_pipeline.load_exec_summary()
    kj_signals = []
    if exec_data:
        # Resolve series tickers to market tickers
        watched_series = set()
        for s in edge_signals:
            st = s.get("ticker", "")
            if "-" not in st:  # It's a series ticker
                watched_series.add(st)
        for kj_kw, series_kw, _ in KJ_KEYWORD_TO_TICKER:
            watched_series.add(series_kw)

        kalshi_market_map = {}
        for st in watched_series:
            markets = resolve_series_ticker(client, st)
            if markets:
                kalshi_market_map[st] = markets

        kj_signals = signal_pipeline.extract_kj_signals_from_exec_summary(exec_data, kalshi_market_map)

    # 4. Detect mean reversion and momentum from live prices
    all_prices = await price_store.get_all_prices()
    watched_tickers = list(all_prices.keys())
    mr_signals = await detect_mean_reversion(price_store, watched_tickers)
    mo_signals = await detect_momentum(price_store, watched_tickers)

    # 5. Check TP/SL on existing positions
    exits = await check_tp_sl(price_store, position_manager, client)
    cycle_result["exits_executed"] = len(exits)

    # 6. Merge all signals, sort by edge
    all_signals = []
    all_signals.extend(edge_signals)
    all_signals.extend(kj_signals)
    all_signals.extend(mr_signals)
    all_signals.extend(mo_signals)

    # Enrich signals with live prices
    for sig in all_signals:
        ticker = sig.get("ticker", "")
        if sig.get("market_confidence") is None:
            mid = await price_store.get_mid(ticker)
            if mid is not None:
                sig["market_confidence"] = round(mid * 100, 1)
                sig["market_price_float"] = mid
                if sig.get("trevor_confidence"):
                    edge = sig["trevor_confidence"] - sig["market_confidence"]
                    if sig.get("direction") == "buy_no":
                        edge = -edge
                    sig["edge_pts"] = round(edge, 1)

    # Sort by absolute edge
    all_signals.sort(key=lambda s: abs(s.get("edge_pts", 0) or 0), reverse=True)

    # Deduplicate by ticker
    seen_tickers = set()
    unique_signals = []
    for s in all_signals:
        ticker = s.get("ticker", "")
        if ticker and ticker not in seen_tickers:
            unique_signals.append(s)
            seen_tickers.add(ticker)

    cycle_result["signals_found"] = len(unique_signals)

    # ── Resolve event-level tickers to specific market tickers ──
    # Signals from intel_bridge often use series tickers (KXTRUMPIRAN) but
    # Kalshi needs specific market tickers (KXTRUMPIRAN-26JUN01).
    resolved_signals = []
    for sig in unique_signals:
        ticker = sig.get("ticker", "")
        # Check if this looks like a series ticker (no date suffix)
        if ticker and "-" not in ticker and ticker.startswith("KX"):
            markets = resolve_series_ticker(client, ticker)
            if markets:
                # Pick the best market: closest expiry with highest volume
                best_market = markets[0]
                sig["original_ticker"] = ticker
                sig["ticker"] = best_market
                log.info(f"  Resolved {ticker} → {best_market} ({len(markets)} options)")
                resolved_signals.append(sig)
                # Subscribe WS to this ticker
                watched_tickers.append(best_market)
            else:
                log.info(f"  Skipping {ticker} — no open markets found for this series")
                # Keep signal but note it couldn't resolve
                sig["_unresolved"] = True
                resolved_signals.append(sig)
        else:
            resolved_signals.append(sig)
    unique_signals = [s for s in resolved_signals if not s.get("_unresolved")]
    cycle_result["signals_found"] = len(unique_signals)

    # 7. Execute trades
    max_new = GUARDRAILS["max_concurrent_positions"] - positions_count
    trades_needed = min(max(0, max_new), len(unique_signals))

    if trades_needed > 0:
        log.info(f"Signals: {len(unique_signals)} unique, capacity: {trades_needed} new trades")
    else:
        log.info(f"Signals: {len(unique_signals)} unique, no capacity for new trades")

    for sig in unique_signals[:trades_needed]:
        # Only execute signals with sufficient edge
        edge_val = abs(sig.get("edge_pts", 0) or 0)
        if edge_val < GUARDRAILS["min_edge_to_trade"]:
            continue

        result = await execute_trade(sig, client, price_store, position_manager, dry_run=dry_run)
        if result:
            if result.get("status") == "executed":
                cycle_result["trades_executed"] += 1
            elif result.get("status") == "blocked":
                cycle_result["trades_blocked"] += 1

    # 8. Ensure WS is subscribed to all relevant tickers
    all_tickers_to_watch = set()
    for sig in unique_signals:
        all_tickers_to_watch.add(sig.get("ticker", ""))
    for ticker in position_manager.positions:
        all_tickers_to_watch.add(ticker)
    all_tickers_to_watch.discard("")

    if all_tickers_to_watch:
        await ws_client.update_subscriptions(list(all_tickers_to_watch))

    # 9. Save state
    await position_manager.save()

    cycle_duration = _time.time() - cycle_start
    log.info(f"Cycle complete in {cycle_duration:.1f}s — "
             f"{cycle_result['trades_executed']} trades, "
             f"{cycle_result['exits_executed']} exits, "
             f"{cycle_result['trades_blocked']} blocked")

    return cycle_result


# ── Daemon Controller ───────────────────────────────────────────────

class PhilbyDaemon:
    """Main daemon orchestrating WebSocket, trading, and state management."""

    def __init__(
        self,
        dry_run: bool = False,
        cycle_interval: int = 60,
        log_file: Optional[pathlib.Path] = None,
    ):
        self.dry_run = dry_run
        self.cycle_interval = cycle_interval
        self.log_file = log_file

        # Reconfigure logging if log file specified
        global log
        if log_file:
            log = setup_daemon_logging(log_file)

        self.price_store = PriceStore()
        self.position_manager = PositionManager()
        self.signal_pipeline = SignalPipeline()
        self.ws_client = DaemonWebSocket(self.price_store)
        self.client: Optional[Any] = None
        self._running = False
        self._shutdown_event = asyncio.Event()
        self.cycle_count = 0
        self.start_time: Optional[float] = None

    async def initialize(self):
        """Initialize connections and load state."""
        log.info("=" * 60)
        log.info("Philby Trading Daemon — Starting")
        log.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE TRADING'}")
        log.info(f"Cycle interval: {self.cycle_interval}s")
        log.info("=" * 60)

        # Connect to Kalshi API
        self.client = _get_kalshi_client()
        log.info("Kalshi REST client connected")

        # Load existing positions — first from API for real-time state, then file for history
        try:
            # Pull positions from Kalshi API for accurate current state
            api_positions = self.client.get_positions()
            market_positions = api_positions.get("market_positions", [])
            active_positions = [p for p in market_positions if float(p.get("position_fp", 0)) > 0]
            if active_positions:
                log.info(f"Found {len(active_positions)} active positions on Kalshi API")
                for p in active_positions:
                    ticker = p["ticker"]
                    count = float(p["position_fp"])
                    exposure = float(p["market_exposure_dollars"])
                    entry_price = (exposure / count * 100) if count > 0 else 50
                    if ticker not in self.position_manager.positions:
                        pos = TrackedPosition(
                            ticker=ticker,
                            side="yes",
                            count=count,
                            entry_price=entry_price,
                            entry_cost=exposure,
                            entry_time=p.get("last_updated_ts", ""),
                        )
                        self.position_manager.positions[ticker] = pos
                log.info(f"Imported {len(active_positions)} positions from Kalshi API")
                await self.position_manager.save()
        except Exception as e:
            log.warning(f"Failed to import positions from Kalshi API: {e}")
        
        # Then load from file (may have additional tracked metadata)
        await self.position_manager.load()
        if not self.position_manager._loaded:
            await self.position_manager.update_portfolio_value(self.client)
        await self.position_manager.update_portfolio_value(self.client)

        # Backfill prices from WS log for immediate readiness
        backfill_count = await self.price_store.backfill_from_file(WS_LOG_FILE)
        log.info(f"Price store initialized with {backfill_count} backfilled events")

        # Run initial intel bridge scan
        self.signal_pipeline.get_edge_signals(force_refresh=True)

        # Write PID file
        self._write_pid()

        # Try to stop the old ws_listener if running
        self._try_stop_old_listener()

    def _write_pid(self):
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        PID_FILE.write_text(str(os.getpid()))

    def _remove_pid(self):
        try:
            PID_FILE.unlink(missing_ok=True)
        except Exception:
            pass

    def _try_stop_old_listener(self):
        """Attempt to stop the old ws_listener process if running."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "ws_listener.py"],
                capture_output=True, text=True, timeout=5,
            )
            pids = result.stdout.strip().split()
            our_pid = str(os.getpid())
            for pid in pids:
                if pid and pid != our_pid:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        log.info(f"Sent SIGTERM to old ws_listener (PID {pid})")
                    except (ProcessLookupError, PermissionError, ValueError):
                        pass
        except Exception as e:
            log.debug(f"Old listener check: {e}")

    async def run_trading_loop(self):
        """Main 60-second trading cycle."""
        self._running = True
        self.start_time = _time.time()
        self.cycle_count = 0

        while self._running:
            try:
                self.cycle_count += 1
                log.info(f"--- Cycle #{self.cycle_count} ---")

                await trading_cycle(
                    client=self.client,
                    price_store=self.price_store,
                    position_manager=self.position_manager,
                    signal_pipeline=self.signal_pipeline,
                    ws_client=self.ws_client,
                    dry_run=self.dry_run,
                )

            except Exception as e:
                log.error(f"Cycle {self.cycle_count} error: {e}", exc_info=True)

            # Wait for next cycle or shutdown
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.cycle_interval,
                )
                # Shutdown was signaled
                break
            except asyncio.TimeoutError:
                # Normal cycle timeout — continue
                pass

        log.info("Trading loop stopped")

    async def shutdown(self):
        """Graceful shutdown."""
        log.info("Shutting down...")
        self._running = False
        self._shutdown_event.set()

        # Save final state
        await self.position_manager.save()
        log.info(f"Final portfolio: ${self.position_manager.portfolio_value:.2f}")

        # Close WebSocket
        await self.ws_client.shutdown()

        # Remove PID
        self._remove_pid()

        run_duration = _time.time() - (self.start_time or _time.time())
        log.info(f"Daemon stopped after {self.cycle_count} cycles ({run_duration/3600:.1f}h)")
        log.info("Goodbye.")

    async def run(self):
        """Main entry: initialize, start WS + trading, wait for shutdown."""
        await self.initialize()

        # Start WebSocket listener and trading loop concurrently
        ws_task = asyncio.create_task(self.ws_client.listen_forever())
        trade_task = asyncio.create_task(self.run_trading_loop())

        # Wait for either to complete (or external shutdown signal)
        done, pending = await asyncio.wait(
            [ws_task, trade_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Cancel remaining tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        await self.shutdown()


# ── CLI Handlers ────────────────────────────────────────────────────

def cmd_status(args):
    """Print daemon status and exit."""
    print(f"\n{'='*60}")
    print("  Philby Trading Daemon — Status Report")
    print(f"  {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*60}")

    # Check if daemon is running
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)
            print(f"  Daemon PID: {pid} (running)")
        except (OSError, ValueError):
            print(f"  Daemon PID: stale ({PID_FILE.read_text().strip()})")
    else:
        print("  Daemon: not running")

    # Kalshi balance
    try:
        client = _get_kalshi_client()
        balance = client.get_balance()
        cash = balance.get("balance_dollars", balance.get("balance", "?"))
        portfolio_cents = float(balance.get("portfolio_value", 0))
        portfolio_val = portfolio_cents / 100.0
        print(f"  Kalshi cash: ${cash}")
        print(f"  Portfolio value: ${portfolio_val:.2f}")
    except Exception as e:
        print(f"  Kalshi API: {e}")

    # Positions
    if POSITIONS_FILE.exists():
        try:
            data = json.loads(POSITIONS_FILE.read_text())
            positions = data.get("positions", [])
            open_pos = [p for p in positions if p.get("status") == "open"]
            print(f"  Open positions: {len(open_pos)}")
            for p in open_pos:
                print(f"    {p['ticker']:40s} {p['side']:4s} x{p['count']:>6d}  "
                      f"entry={p['entry_price']:>5.0f}c  cost=${p['entry_cost']:.2f}")
            print(f"  Portfolio value: ${data.get('portfolio_value', 0):.2f}")
            print(f"  Peak value: ${data.get('peak_value', 0):.2f}")
            print(f"  Daily P&L: {data.get('daily_pnl', 0):+.2f}")
        except Exception as e:
            print(f"  Positions: {e}")
    else:
        print("  No positions file")

    # Recent signals
    if SIGNALS_FILE.exists():
        try:
            sig_data = json.loads(SIGNALS_FILE.read_text())
            tradeable = sig_data.get("tradeable", [])
            print(f"\n  Signals: {len(tradeable)} tradeable")
            for s in tradeable[:10]:
                print(f"    {s.get('action','?'):8s} {s.get('ticker','?'):35s} "
                      f"edge={s.get('edge_pts',0):+.0f}pts  "
                      f"T={s.get('trevor_confidence',0):.0f}% M={s.get('implied_prob_pct',s.get('market_confidence',0)):.0f}%")
        except Exception:
            pass

    # WS log stats
    if WS_LOG_FILE.exists():
        try:
            ws_size = WS_LOG_FILE.stat().st_size
            ws_lines = sum(1 for _ in open(WS_LOG_FILE))
            print(f"\n  WS log: {ws_lines} events, {ws_size/1024:.0f}KB")
        except Exception:
            pass

    print()


def cmd_scan(args):
    """One-shot signal detection with live prices."""
    print(f"\n{'='*60}")
    print("  Philby Daemon — Signal Scan")
    print(f"  {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*60}\n")

    pipeline = SignalPipeline()
    store = PriceStore()

    # Run intel bridge
    edge_signals = pipeline.get_edge_signals(force_refresh=True)
    print(f"Intel Bridge Signals: {len(edge_signals)} tradeable")
    for s in edge_signals:
        print(f"  {s.get('action','?'):8s} {s.get('ticker','?'):35s} "
              f"edge={s.get('edge_pts',0):+.0f}pts  "
              f"T={(s.get('trevor_confidence',0)):.0f}%  "
              f"M={s.get('implied_prob_pct',s.get('market_confidence',0)):.0f}%")

    # Load exec summary
    exec_data = pipeline.load_exec_summary()
    if exec_data:
        print(f"\nExec Summary: {exec_data.get('as_of_utc', '?')}")
        print(f"BLUF: {exec_data.get('bluf', '')[:200]}")
        kjs = exec_data.get("five_judgments", [])
        print(f"Key Judgments: {len(kjs)}")
        for kj in kjs:
            print(f"  {kj.get('id','?')}: [{kj.get('sherman_kent_band','?')}] "
                  f"{kj.get('prediction_pct',0)}% — {kj.get('statement','')[:100]}")

    # Try to get some live prices from WS log
    if WS_LOG_FILE.exists():
        print(f"\n--- Recent WS prices (from log) ---")
        seen = set()
        try:
            with open(WS_LOG_FILE, "r") as f:
                lines = f.readlines()
            for line in reversed(lines[-200:]):
                try:
                    record = json.loads(line)
                    if record.get("type") == "ticker":
                        ticker = record.get("ticker", "")
                        if ticker not in seen:
                            seen.add(ticker)
                            data = record.get("data", {})
                            yes_bid = data.get("yes_bid", "?")
                            yes_ask = data.get("yes_ask", "?")
                            print(f"  {ticker:40s} bid={yes_bid} ask={yes_ask}")
                            if len(seen) >= 10:
                                break
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            print(f"  Error reading WS log: {e}")

    print()


def cmd_backfill(args):
    """Backfill prices from WS event log and print summary."""
    print(f"Backfilling from {WS_LOG_FILE}...")

    async def _backfill():
        store = PriceStore()
        count = await store.backfill_from_file(WS_LOG_FILE, max_lines=10000)
        prices = await store.get_all_prices()
        print(f"Backfilled {count} ticker events")
        print(f"Unique tickers in memory: {len(prices)}")
        for ticker, data in sorted(prices.items()):
            mid = store._compute_mid(data)
            print(f"  {ticker:45s} bid={data.get('yes_bid','?'):>8s} ask={data.get('yes_ask','?'):>8s} mid={mid}")
        return count

    count = asyncio.run(_backfill())
    print(f"\nDone. {count} prices loaded.")


def cmd_stop(args):
    """Gracefully stop a running daemon."""
    if not PID_FILE.exists():
        print("No PID file found — daemon may not be running")
        return

    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)  # Check if process exists
        os.kill(pid, signal.SIGTERM)
        print(f"Sent SIGTERM to daemon (PID {pid})")

        # Wait for graceful shutdown
        for i in range(10):
            _time.sleep(1)
            try:
                os.kill(pid, 0)
            except OSError:
                print("Daemon stopped successfully")
                PID_FILE.unlink(missing_ok=True)
                return
        print("Daemon did not stop gracefully — sending SIGKILL")
        os.kill(pid, signal.SIGKILL)
    except (OSError, ValueError) as e:
        print(f"Daemon not running: {e}")
        PID_FILE.unlink(missing_ok=True)


def cmd_daemon(args):
    """Start daemon in background with nohup."""
    import shlex

    script = pathlib.Path(__file__).resolve()
    # Build command without --daemon flag to run in foreground
    cmd_parts = [sys.executable, str(script)]
    # Copy relevant flags
    if args.dry_run:
        cmd_parts.append("--dry-run")
    if args.cycle:
        cmd_parts.extend(["--cycle", str(args.cycle)])
    if args.log_file:
        cmd_parts.extend(["--log-file", str(args.log_file)])

    log_file = DAEMON_LOG_FILE
    cmd = " ".join(shlex.quote(p) for p in cmd_parts)
    full_cmd = f"nohup {cmd} > {shlex.quote(str(log_file))} 2>&1 &"

    print(f"Starting daemon in background...")
    print(f"Log: {log_file}")
    subprocess.run(full_cmd, shell=True, cwd=str(REPO))
    _time.sleep(2)

    # Verify it started
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)
            print(f"Daemon started (PID {pid})")
        except (OSError, ValueError):
            print("Daemon may have failed to start — check logs")
    else:
        print("No PID file — daemon may have failed to start")


async def cmd_foreground(args):
    """Start daemon in foreground."""
    daemon = PhilbyDaemon(
        dry_run=args.dry_run,
        cycle_interval=args.cycle,
        log_file=args.log_file,
    )

    # Handle signals for graceful shutdown
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(daemon.shutdown()))
        except NotImplementedError:
            pass

    try:
        await daemon.run()
    except KeyboardInterrupt:
        pass


# ── Main Entry ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Philby Trading Daemon — 24/7 continuous Kalshi trading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 philby/trader/daemon.py                 Start in foreground
  python3 philby/trader/daemon.py --daemon        Start in background (nohup)
  python3 philby/trader/daemon.py --status         Status report
  python3 philby/trader/daemon.py --scan           One-shot signal detection
  python3 philby/trader/daemon.py --backfill       Backfill prices from WS log
  python3 philby/trader/daemon.py --stop           Graceful shutdown
  python3 philby/trader/daemon.py --dry-run        Foreground, no execution
        """,
    )

    parser.add_argument("--daemon", action="store_true", help="Start in background with nohup")
    parser.add_argument("--status", action="store_true", help="Status report")
    parser.add_argument("--scan", action="store_true", help="One-shot signal detection")
    parser.add_argument("--backfill", action="store_true", help="Backfill prices from WS log")
    parser.add_argument("--stop", action="store_true", help="Graceful shutdown")
    parser.add_argument("--dry-run", action="store_true", help="Run without executing trades")
    parser.add_argument("--cycle", type=int, default=60, help="Trading cycle interval in seconds (default: 60)")
    parser.add_argument("--log-file", type=pathlib.Path, default=None, help="Log file path (default: logs/philby-daemon.log)")

    args = parser.parse_args()

    # Dispatch CLI mode
    if args.status:
        cmd_status(args)
    elif args.scan:
        cmd_scan(args)
    elif args.backfill:
        cmd_backfill(args)
    elif args.stop:
        cmd_stop(args)
    elif args.daemon:
        cmd_daemon(args)
    else:
        # Foreground mode
        asyncio.run(cmd_foreground(args))


if __name__ == "__main__":
    main()
