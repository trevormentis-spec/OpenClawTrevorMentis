#!/usr/bin/env python3
"""
Philby Trader — Autonomous Kalshi Trade Execution Engine.

Reads trade signals from intel_bridge.py, evaluates against guardrails,
executes via Kalshi API, and logs every trade to a persistent journal.

Usage:
    python3 philby/trader/trader.py --scan-and-trade        # Full cycle
    python3 philby/trader/trader.py --dry-run               # Report only, no execute
    python3 philby/trader/trader.py --status                # Portfolio + positions
    python3 philby/trader/trader.py --journal               # Full trade history
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
from typing import Any

# ── Load .env for standalone/cron runs (no shell inheritance) ──
_env_loaded = False
def _load_env():
    """Load .env file into os.environ so API keys are available."""
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

REPO = pathlib.Path(__file__).resolve().parent.parent.parent

# Load .env for standalone/cron runs
_load_env()
SIGNALS_FILE = REPO / "philby" / "trader" / "signals" / "latest.json"
JOURNAL_FILE = REPO / "philby" / "trader" / "journal.jsonl"
POSITIONS_FILE = REPO / "philby" / "trader" / "positions.json"
CIRCUIT_BREAKER_FILE = REPO / "philby" / "trader" / "circuit_breaker.json"
MAX_TRADE_ATTEMPTS_PER_DAY = 10
MAX_CONSECUTIVE_FAILURES = 3

# ── Circuit Breaker ─────────────────────────────────────────────────
_TRADER_PAUSED = False
_TRADER_PAUSE_REASON = ""
_TRADER_PAUSE_SENT = False


def _send_agentmail_pause(reason: str):
    """Send AgentMail alert when philby is paused."""
    try:
        from agentmail import AgentMail
        api_key = os.environ.get("AGENTMAIL_API_KEY", "")
        if api_key:
            client = AgentMail(api_key=api_key)
            resp = client.inboxes.messages.send(
                inbox_id="trevor_mentis@agentmail.to",
                to=["roderick.jones@gmail.com"],
                subject="philby paused",
                text=f"Philby trader paused.\n\nReason: {reason}\n\nNo further trade attempts will be made until circuit resets (next UTC day or manual intervention).\n\n-- Trevor",
            )
            log(f"AgentMail sent: {resp.message_id}")
    except Exception as e:
        log(f"AgentMail failed: {e}")

def _load_circuit_breaker() -> dict:
    if CIRCUIT_BREAKER_FILE.exists():
        try:
            return json.loads(CIRCUIT_BREAKER_FILE.read_text())
        except (json.JSONDecodeError,):
            pass
    return {"paused": False, "reason": "", "paused_at": None, "consecutive_failures": 0, "today_attempts": 0, "date": ""}

def _save_circuit_breaker(cb: dict):
    CIRCUIT_BREAKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    CIRCUIT_BREAKER_FILE.write_text(json.dumps(cb, indent=2))

def _check_circuit_breaker() -> str:
    """Check if circuit is open. Returns empty string if ok, pause reason if blocked."""
    cb = _load_circuit_breaker()
    today = dt.date.today().isoformat()
    # Auto-reset when a new UTC day starts (paused or not)
    if cb.get("date") != today:
        _save_circuit_breaker({
            "paused": False,
            "reason": "",
            "paused_at": None,
            "consecutive_failures": 0,
            "today_attempts": 0,
            "date": today,
        })
        return ""
    if cb.get("paused"):
        return cb.get("reason", "circuit breaker active")
    # Check daily limit
    if cb.get("today_attempts", 0) >= MAX_TRADE_ATTEMPTS_PER_DAY:
        return f"daily max attempts reached ({MAX_TRADE_ATTEMPTS_PER_DAY})"
    return ""

def _record_trade_outcome(success: bool):
    """Record trade outcome into circuit breaker state."""
    cb = _load_circuit_breaker()
    cb["today_attempts"] = cb.get("today_attempts", 0) + 1
    if success:
        cb["consecutive_failures"] = 0
    else:
        cb["consecutive_failures"] = cb.get("consecutive_failures", 0) + 1
        if cb["consecutive_failures"] >= MAX_CONSECUTIVE_FAILURES:
            cb["paused"] = True
            cb["reason"] = f"{MAX_CONSECUTIVE_FAILURES} consecutive trade failures — circuit opened"
            cb["paused_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
            global _TRADER_PAUSED, _TRADER_PAUSE_REASON
            _TRADER_PAUSED = True
            _TRADER_PAUSE_REASON = cb["reason"]
    _save_circuit_breaker(cb)

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

# Kalshi client import (wrapped for graceful failure)
try:
    sys.path.insert(0, str(REPO / "scripts"))
    sys.path.insert(0, str(REPO / "skills" / "kalshi-trader" / "scripts"))
    from client import KalshiClient, KalshiAPIError, KalshiAuthError
    KALSHI_AVAILABLE = True
except ImportError:
    KALSHI_AVAILABLE = False


def log(msg: str) -> None:
    print(f"[trader {dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


def load_signals() -> list[dict]:
    if not SIGNALS_FILE.exists():
        return []
    try:
        data = json.loads(SIGNALS_FILE.read_text())
        return data.get("tradeable", [])
    except (json.JSONDecodeError,):
        return []


def load_journal() -> list[dict]:
    trades = []
    if JOURNAL_FILE.exists():
        for line in JOURNAL_FILE.read_text().splitlines():
            try:
                trades.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                pass
    return trades


def append_journal(entry: dict) -> None:
    JOURNAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(JOURNAL_FILE, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")


def load_positions() -> dict:
    if POSITIONS_FILE.exists():
        try:
            return json.loads(POSITIONS_FILE.read_text())
        except (json.JSONDecodeError,):
            pass
    return {"positions": [], "balance": 0.0, "peak_value": 0.0, "last_updated": None}


def save_positions(positions: dict) -> None:
    POSITIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    POSITIONS_FILE.write_text(json.dumps(positions, indent=2))


def compute_kelly(trevor_pct: float, market_price: float) -> float:
    """Compute Kelly fraction for a binary bet."""
    p = trevor_pct / 100.0  # Trevor's assessed win probability
    b = (1 - market_price) / market_price  # Decimal odds from market price
    q = 1 - p  # Loss probability
    if b <= 0:
        return 0.0
    kelly = (p * b - q) / b
    return max(0.0, min(kelly * GUARDRAILS["kelly_fraction"], 1.0))


def execute_trade(signal: dict, client: Any, dry_run: bool = False) -> dict | None:
    """Execute a trade based on an edge signal."""
    ticker_raw = signal["ticker"]
    expiry = signal.get("expiry", "")
    
    # Resolve event ticker to actual market via scanner API
    ticker = ticker_raw
    if "-" not in ticker_raw and expiry:
        import urllib.request, urllib.parse
        try:
            api_key = os.environ.get("KALSHI_API_KEY", "")
            params = urllib.parse.urlencode({"limit": 20, "status": "open", "series_ticker": ticker_raw})
            url = f"https://api.elections.kalshi.com/trade-api/v2/markets?{params}"
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read())
            markets = data.get("markets", [])
            if markets:
                from datetime import datetime
                target = datetime.strptime(expiry, "%Y-%m-%d")
                best, best_delta = None, None
                for m in markets:
                    mt = m.get("ticker", "")
                    ct = m.get("close_time", "")
                    if ct and len(ct) >= 10:
                        try:
                            md = datetime.strptime(ct[:10], "%Y-%m-%d")
                            d = abs((md - target).total_seconds())
                            if best_delta is None or d < best_delta:
                                best_delta, best = d, mt
                        except:
                            pass
                if best:
                    ticker = best
                    log(f"Resolved {ticker_raw} → {ticker}")
        except Exception as e:
            log(f"Ticker resolution failed: {e}")
    
    trevor_conf = signal["trevor_confidence"]
    market_prob = signal["market_confidence"]
    edge = signal["edge_pts"]

    # Compute Kelly sizing
    market_price = market_prob / 100.0 if market_prob else 0.5
    kelly_frac = compute_kelly(trevor_conf, market_price)

    # Get current balance — must succeed, no fallback
    try:
        balance_data = client.get_balance()
        balance = float(balance_data.get("balance_dollars", balance_data.get("balance", "0")))
        if balance < 1.0:
            pause_reason = f"Balance too low: ${balance:.2f} — minimum $1 needed"
            log(f"  ⛔ HALT: {pause_reason}")
            append_journal({
                "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                "ticker": ticker,
                "action": "PAUSED",
                "reason": pause_reason,
                "status": "paused",
            })
            _record_trade_outcome(False)
            return {"ticker": ticker, "status": "paused", "reason": pause_reason}
    except Exception as e:
        pause_reason = f"Balance fetch failed: {e}"
        log(f"  ⛔ HALT: {pause_reason}")
        append_journal({
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "ticker": ticker,
            "action": "PAUSED",
            "reason": pause_reason,
            "status": "paused",
        })
        _record_trade_outcome(False)
        return {"ticker": ticker, "status": "paused", "reason": pause_reason}

    # Compute position size (quarter-Kelly, max 5% of portfolio)
    position_size = balance * kelly_frac * (GUARDRAILS["max_position_pct"] / 100.0)
    position_size = min(position_size, balance * GUARDRAILS["max_position_pct"] / 100.0)
    position_size = max(position_size, 1.0)  # Minimum $1

    # Skip if we already hold this ticker
    try:
        existing = client.get_positions()
        held_markets = existing.get("market_positions", existing.get("positions", []))
        held_tickers = {
            p.get("ticker", "") for p in held_markets
            if float(p.get("count_fp", p.get("count", 0))) > 0
        }
        if ticker in held_tickers:
            log(f"  Already holding {ticker} — skipping")
            return None
    except Exception:
        pass

    log(f"Trade signal: {signal['action']} {ticker}")
    log(f"  Trevor: {trevor_conf}%  Market: {market_prob}%  Edge: {edge:+.0f}pts")
    log(f"  Kelly fraction: {kelly_frac:.2f}  Position size: ${position_size:.2f}")

    if dry_run:
        log(f"  [DRY RUN] Would execute: {signal['action']} ${position_size:.2f} of {ticker}")
        return {
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "ticker": ticker,
            "action": signal["action"],
            "trevor_confidence": trevor_conf,
            "market_probability": market_prob,
            "edge_pts": edge,
            "position_size_dollars": round(position_size, 2),
            "kelly_fraction": round(kelly_frac, 4),
            "status": "dry_run",
            "rationale": f"Trevor {trevor_conf}% vs market {market_prob}% ({edge:+.0f}pt edge)",
        }

    # Execute via Kalshi API with fill monitoring
    try:
        if "BUY Yes" in signal["action"]:
            yes_price_cents = max(1, int(market_prob))
            contract_cost_dollars = yes_price_cents / 100.0
            contract_count = max(1, int(position_size / contract_cost_dollars))
            log(f"  Attempt 1: yes_price={yes_price_cents}c, count={contract_count}")
            
            # Try with maker price first (resting order)
            order = client.create_order(
                ticker=ticker,
                action="buy",
                side="yes",
                yes_price=yes_price_cents,
                count=contract_count,
                time_in_force="good_till_canceled",
            )
        else:
            no_price_cents = max(1, int(100 - market_prob))
            contract_cost_dollars = no_price_cents / 100.0
            contract_count = max(1, int(position_size / contract_cost_dollars))
            log(f"  Attempt 1: no_price={no_price_cents}c, count={contract_count}")
            
            order = client.create_order(
                ticker=ticker,
                action="buy",
                side="no",
                no_price=no_price_cents,
                count=contract_count,
                time_in_force="good_till_canceled",
            )

        order_id = order.get("order_id", "") if isinstance(order, dict) else ""
        log(f"  Order placed: {order_id}")

        # Fill monitoring loop: check fill status at intervals
        import time as _time
        filled = False
        for attempt in range(3):
            _time.sleep(20)  # Wait 20s between checks
            try:
                # Check if order was filled by checking positions
                pos_check = client.get_positions()
                all_pos = pos_check.get("market_positions", pos_check.get("positions", []))
                for p in all_pos:
                    if p.get("ticker", "") == ticker and float(p.get("count_fp", p.get("count", 0))) > 0:
                        filled = True
                        log(f"  ✅ Filled after {attempt*20+20}s")
                        break
                
                if filled:
                    break
                
                # Not filled — escalate price by 2 cents
                if "BUY Yes" in signal["action"]:
                    old_price = yes_price_cents
                    yes_price_cents = min(yes_price_cents + 2, 99)
                    if yes_price_cents != old_price:
                        log(f"  Escalating price {old_price}c → {yes_price_cents}c")
                        order = client.create_order(
                            ticker=ticker, action="buy", side="yes",
                            yes_price=yes_price_cents, count=contract_count,
                            time_in_force="good_till_canceled",
                        )
                else:
                    old_price = no_price_cents
                    no_price_cents = min(no_price_cents + 2, 99)
                    if no_price_cents != old_price:
                        log(f"  Escalating price {old_price}c → {no_price_cents}c")
                        order = client.create_order(
                            ticker=ticker, action="buy", side="no",
                            no_price=no_price_cents, count=contract_count,
                            time_in_force="good_till_canceled",
                        )
                
                # Old orders will be replaced on exchange; no explicit cancel needed
                    
            except Exception as monitor_err:
                log(f"  Fill check error: {monitor_err}")

        # Final status
        if not filled:
            log(f"  ⚠️ Order not confirmed filled after 3 attempts — logged as placed")

        trade_entry = {
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "ticker": ticker,
            "action": signal["action"],
            "trevor_confidence": trevor_conf,
            "market_probability": market_prob,
            "edge_pts": edge,
            "position_size_dollars": round(position_size, 2),
            "kelly_fraction": round(kelly_frac, 4),
            "order_id": order_id,
            "filled": filled,
            "status": "executed" if filled else "order_placed",
        }
        append_journal(trade_entry)
        log(f"  {'✅' if filled else '📋'} {ticker}: {'Filled' if filled else 'Order placed'}")
        return trade_entry

    except Exception as e:
        error_entry = {
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "ticker": ticker,
            "action": signal["action"],
            "error": str(e),
            "status": "failed",
        }
        append_journal(error_entry)
        log(f"  ❌ Execution failed: {e}")
        return None


def cmd_scan_and_trade(args):
    """Full cycle: detect edges → execute trades."""
    global _TRADER_PAUSED, _TRADER_PAUSE_REASON, _TRADER_PAUSE_SENT
    if not KALSHI_AVAILABLE:
        log("Kalshi client not available — can't trade")
        return 1

    # Step 1: Run intel bridge to detect edges
    log("Step 1: Running intel bridge...")
    bridge = REPO / "philby" / "trader" / "intel_bridge.py"
    import subprocess
    result = subprocess.run(
        ["python3", str(bridge), "--json"],
        capture_output=True, text=True, timeout=60, cwd=str(REPO),
    )

    try:
        signals_data = json.loads(result.stdout)
        tradeable = signals_data.get("tradeable", [])
    except (json.JSONDecodeError,):
        log(f"Bridge output parse failed: {result.stderr[:200]}")
        tradeable = []

    if not tradeable:
        log("No tradeable signals found")
        return 0

    log(f"Found {len(tradeable)} tradeable signal(s)")

    # Check circuit breaker before proceeding
    cb_reason = _check_circuit_breaker()
    if cb_reason:
        log(f"⛔ CIRCUIT OPEN: {cb_reason}")
        if _TRADER_PAUSED and not _TRADER_PAUSE_SENT:
            _send_agentmail_pause(cb_reason)
            _TRADER_PAUSE_SENT = True
        return 0

    # Step 2: Connect to Kalshi
    try:
        client = KalshiClient()
        log("Connected to Kalshi API")
    except Exception as e:
        log(f"Kalshi connection failed: {e}")
        _record_trade_outcome(False)
        return 1

    # Step 3: Get current balance and existing positions
    try:
        balance = client.get_balance()
        portfolio_value = float(balance.get("balance_dollars", 0))
        log(f"Balance: ${portfolio_value:.2f}")

        if portfolio_value < 1.0:
            pause_reason = f"Balance too low: ${portfolio_value:.2f}"
            log(f"⛔ HALT: {pause_reason}")
            append_journal({"timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                           "action": "PAUSED", "reason": pause_reason, "status": "paused"})
            _record_trade_outcome(False)
            if not _TRADER_PAUSE_SENT:
                _send_agentmail_pause(pause_reason)
                _TRADER_PAUSE_SENT = True
            return 0

        # Get existing positions to check capacity
        existing = client.get_positions()
        existing_positions = existing.get("positions", [])
        log(f"Existing positions: {len(existing_positions)}")

        if len(existing_positions) >= GUARDRAILS["max_concurrent_positions"]:
            log("Max positions reached — skipping new entries")
            return 0

    except Exception as e:
        log(f"Balance check failed: {e}")
        _record_trade_outcome(False)
        return 1

    # Step 4: Execute best signals
    executed = 0
    for signal in tradeable[:GUARDRAILS["max_concurrent_positions"]]:
        if args.dry_run:
            result = execute_trade(signal, client, dry_run=True)
        else:
            result = execute_trade(signal, client)
        if result:
            executed += 1

    log(f"Done: {executed}/{len(tradeable)} trades executed")
    return 0


def cmd_status(args):
    """Show portfolio and position status."""
    journal = load_journal()
    positions = load_positions()

    print(f"\n=== Philby Trader Status ===")
    print(f"{'─' * 50}")

    # Kalshi live status
    if KALSHI_AVAILABLE:
        try:
            client = KalshiClient()
            balance = client.get_balance()
            bal_dollars = balance.get("balance_dollars", balance.get("balance", "?"))
            print(f"Kalshi balance: ${bal_dollars}")
        except Exception as e:
            print(f"Kalshi API: {e}")
    else:
        print("Kalshi API: not available")

    # Journal stats
    total_trades = len(journal)
    executed = [t for t in journal if t.get("status") == "executed"]
    failed = [t for t in journal if t.get("status") == "failed"]
    print(f"Total trades logged: {total_trades}")
    print(f"  Executed: {len(executed)}  Failed: {len(failed)}")

    # Recent trades
    if executed:
        print(f"\nRecent trades (last 5):")
        for t in executed[-5:]:
            print(f"  {t.get('timestamp','?')[:19]} [{t.get('status','?')}] {t.get('action','?')} {t.get('ticker','?')} ${t.get('position_size_dollars',0):.2f}")

    # Signals
    signals = load_signals()
    print(f"\nLive signals: {len(signals)} tradeable")
    for s in signals[:5]:
        print(f"  {s.get('action','?'):8s} {s.get('ticker','?'):35s} edge={s.get('edge_pts',0):+.0f}pts")
    print()


def cmd_journal(args):
    """Show full trade journal."""
    journal = load_journal()
    if not journal:
        print("No trades in journal.")
        return

    print(f"\n=== Philby Trade Journal ({len(journal)} entries) ===")
    print(f"{'Timestamp':<22} {'Status':<10} {'Action':<10} {'Ticker':<35} {'Size':>8} {'Edge':>6}")
    print("-" * 95)
    for t in journal:
        ts = t.get("timestamp", "?")[:19]
        status = t.get("status", "?")
        action = t.get("action", "?")
        ticker = t.get("ticker", "?")
        size = t.get("position_size_dollars", 0)
        edge = t.get("edge_pts", 0)
        edge_str = f"{edge:+.0f}pt" if edge else ""
        print(f"{ts:<22} {status:<10} {action:<10} {ticker:<35} ${size:>5.2f} {edge_str:>6}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Philby Trader")
    parser.add_argument("--scan-and-trade", action="store_true", help="Full cycle: detect edges → execute")
    parser.add_argument("--dry-run", action="store_true", help="Report only, no execution")
    parser.add_argument("--status", action="store_true", help="Portfolio + positions")
    parser.add_argument("--journal", action="store_true", help="Show full trade history")
    args = parser.parse_args()

    if args.status:
        cmd_status(args)
    elif args.journal:
        cmd_journal(args)
    elif args.scan_and_trade or args.dry_run:
        cmd_scan_and_trade(args)
    else:
        cmd_status(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
