#!/usr/bin/env python3
"""
Geopolitical Trader — Synthetic $1000 Portfolio.

Trades synthetic positions using geopolitical intelligence from the GSIB.
Decisions based on: Hormuz risk, Russia-Ukraine trajectory, great-power
dynamics, energy market signals, and economic indicators.

Rules:
- Maximum 3 open positions at any time
- No leverage
- Stop losses: -10% per position
- Position sizing: 25-50% of portfolio per trade
- Tracks every trade + cumulative P&L

Portfolio state: brain/memory/semantic/geotrade-portfolio.json
Daily report: analysis/geotrade/{date}.md

Usage:
    python3 scripts/geo_trader.py --date 2026-05-13           # Daily assessment + trade
    python3 scripts/geo_trader.py --date 2026-05-13 --mock    # No trade, just report
    python3 scripts/geo_trader.py --report                     # Portfolio summary
    python3 scripts/geo_trader.py --close <trade_id>           # Close a specific trade
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import pathlib
import re
import sys
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BRIEFINGS_DIR = pathlib.Path.home() / "trevor-briefings"
PORTFOLIO_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "geotrade-portfolio.json"
GEOTRADE_DIR = REPO_ROOT / "analysis" / "geotrade"

# Available synthetic instruments
INSTRUMENTS = {
    "BRENT": {"name": "Brent Crude Oil", "type": "commodity", "current_price": 105.50,
              "sector": "energy", "volatility": "high"},
    "WTI": {"name": "WTI Crude Oil", "type": "commodity", "current_price": 101.20,
            "sector": "energy", "volatility": "high"},
    "GLD": {"name": "SPDR Gold Shares", "type": "etf", "current_price": 235.00,
            "sector": "precious_metals", "volatility": "medium"},
    "SPY": {"name": "S&P 500 ETF", "type": "etf", "current_price": 542.00,
            "sector": "equity", "volatility": "medium"},
    "TLT": {"name": "20+ Year Treasury Bond ETF", "type": "etf", "current_price": 94.50,
            "sector": "bonds", "volatility": "medium"},
    "UUP": {"name": "US Dollar Index ETF", "type": "etf", "current_price": 28.50,
            "sector": "currency", "volatility": "low"},
    "EEM": {"name": "Emerging Markets ETF", "type": "etf", "current_price": 41.20,
            "sector": "equity", "volatility": "high"},
    "SLV": {"name": "Silver Trust", "type": "etf", "current_price": 29.80,
            "sector": "precious_metals", "volatility": "high"},
    "XLE": {"name": "Energy Select Sector ETF", "type": "etf", "current_price": 89.50,
            "sector": "energy", "volatility": "medium"},
    "FXF": {"name": "Swiss Franc ETF", "type": "etf", "current_price": 112.00,
            "sector": "currency", "volatility": "low"},
}

USER_AGENT = "TrevorGeoTrader/1.0"


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[geotrade {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, Exception):
            return {}
    return {}


def save_json(path: pathlib.Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


# ── Portfolio Management ──────────────────────────────────────────

def load_portfolio() -> dict:
    """Load portfolio state or create initial $1000 portfolio."""
    portfolio = load_json(PORTFOLIO_FILE)
    if not portfolio:
        portfolio = {
            "version": 2,
            "created": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
            "initial_capital": 1000.00,
            "cash": 1000.00,
            "positions": [],
            "trade_history": [],
            "total_pl": 0.0,
            "total_pl_pct": 0.0,
        }
    return portfolio


def save_portfolio(portfolio: dict) -> None:
    portfolio["last_updated"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    save_json(PORTFOLIO_FILE, portfolio)


def get_portfolio_value(portfolio: dict) -> float:
    """Calculate current portfolio value (cash + mark-to-market positions)."""
    mtm = sum(p["size"] * p["entry_price"] for p in portfolio.get("positions", []))
    return portfolio.get("cash", 0) + (portfolio.get("total_pl", 0) + mtm)


# ── Trade Execution ───────────────────────────────────────────────

def open_trade(portfolio: dict, instrument: str, direction: str,
               size_pct: float, price: float, reason: str, date_str: str) -> dict | None:
    """Open a new position."""
    if instrument not in INSTRUMENTS:
        log(f"Unknown instrument: {instrument}")
        return None

    if len(portfolio.get("positions", [])) >= 3:
        log("Max 3 positions — cannot open new trade")
        return None

    cash = portfolio.get("cash", 0)
    trade_value = cash * (size_pct / 100)
    if trade_value < 50:
        log(f"Trade value ${trade_value:.2f} too small (<$50)")
        return None

    size = trade_value / price

    position = {
        "trade_id": f"GT-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        "instrument": instrument,
        "direction": direction,
        "size": round(size, 4),
        "entry_price": price,
        "entry_value": round(trade_value, 2),
        "entry_date": date_str,
        "current_price": price,
        "reason": reason,
        "stop_loss": price * 0.90 if direction == "long" else price * 1.10,
        "target": price * 1.15 if direction == "long" else price * 0.85,
        "unrealized_pl": 0.0,
        "unrealized_pl_pct": 0.0,
        "status": "open",
    }

    portfolio.setdefault("positions", []).append(position)
    portfolio["cash"] = round(cash - trade_value, 2)

    log(f"OPENED: {direction.upper()} {instrument} @ ${price:.2f} "
        f"(size=${trade_value:.2f}, {size_pct}% of cash)")
    return position


def close_trade(portfolio: dict, trade_id: str, price: float, reason: str, date_str: str) -> dict | None:
    """Close an existing position."""
    for i, pos in enumerate(portfolio.get("positions", [])):
        if pos.get("trade_id") == trade_id and pos.get("status") == "open":
            entry_val = pos["entry_value"]
            dir_mult = 1 if pos["direction"] == "long" else -1
            exit_val = pos["size"] * price
            pl = round((exit_val - entry_val) * dir_mult, 2)
            pl_pct = round((pl / entry_val) * 100, 2)

            trade_record = {
                **pos,
                "exit_price": price,
                "exit_date": date_str,
                "exit_value": round(exit_val, 2),
                "realized_pl": pl,
                "realized_pl_pct": pl_pct,
                "close_reason": reason,
                "status": "closed",
            }

            portfolio["positions"][i]["status"] = "closed"
            portfolio["cash"] = round(portfolio["cash"] + exit_val, 2)
            portfolio["total_pl"] = round(portfolio["total_pl"] + pl, 2)
            portfolio["total_pl_pct"] = round((portfolio["total_pl"] / portfolio["initial_capital"]) * 100, 2)

            portfolio.setdefault("trade_history", []).append(trade_record)

            log(f"CLOSED: {pos['direction'].upper()} {pos['instrument']} "
                f"P&L=${pl:.2f} ({pl_pct}%) — {reason}")
            return trade_record

    log(f"Trade {trade_id} not found or already closed")
    return None


def update_prices(portfolio: dict) -> None:
    """Update all open positions with current prices and MTM."""
    for pos in portfolio.get("positions", []):
        if pos.get("status") != "open":
            continue
        instr = INSTRUMENTS.get(pos["instrument"], {})
        current_price = instr.get("current_price", pos["entry_price"])
        pos["current_price"] = current_price
        dir_mult = 1 if pos["direction"] == "long" else -1
        mtm = (current_price - pos["entry_price"]) * pos["size"] * dir_mult
        pos["unrealized_pl"] = round(mtm, 2)
        pos["unrealized_pl_pct"] = round((mtm / pos["entry_value"]) * 100, 2)


def update_prices_from_web(portfolio: dict) -> None:
    """Try to fetch live prices via web, fall back to defaults."""
    # For synthetic trading, use default prices from INSTRUMENTS
    # In production, would fetch from Alpha Vantage, Yahoo Finance, etc.
    update_prices(portfolio)


# ── Trading Signal Generation ─────────────────────────────────────

def get_gsib_signals(date_str: str) -> dict:
    """Extract geopolitical trade signals from today's GSIB."""
    signals = {
        "brent_bias": "neutral",
        "gold_bias": "neutral",
        "dollar_bias": "neutral",
        "equity_bias": "neutral",
        "emerging_market_bias": "neutral",
        "conviction": "low",
        "drivers": [],
    }

    # Try to load today's GSIB exec summary
    exec_data = {}
    for base in [BRIEFINGS_DIR, REPO_ROOT / "trevor-briefings"]:
        path = base / date_str / "analysis" / "exec_summary.json"
        if path.exists():
            exec_data = load_json(path)
            break

    if not exec_data:
        return signals

    bluf = exec_data.get("bluf", "").lower()
    judgments = exec_data.get("five_judgments", [])
    j_text = " ".join(j.get("statement", "") for j in judgments).lower()

    all_text = bluf + " " + j_text

    # Energy signals
    energy_upside_kw = ["hormuz", "strait", "iran", "oil", "brent", "crude",
                         "supply disruption", "blockade", "tanker", "irgc"]
    energy_downside_kw = ["ceasefire", "de-escalation", "negotiation", "truce",
                           "diplomatic breakthrough", "reopening"]

    upside_count = sum(1 for k in energy_upside_kw if k in all_text)
    downside_count = sum(1 for k in energy_downside_kw if k in all_text)

    # Bias from judgment statements
    if any("brent" in j.get("statement", "").lower() for j in judgments):
        for j in judgments:
            s = j.get("statement", "").lower()
            if "brent" in s and ("above" in s or "increase" in s or "rise" in s):
                signals["brent_bias"] = "bullish"
                signals["drivers"].append(f"GSIB judgment: {s[:100]}")
            elif "brent" in s and ("below" in s or "decrease" in s or "fall" in s):
                signals["brent_bias"] = "bearish"

    if upside_count > downside_count + 1:
        signals["brent_bias"] = "bullish"
        signals["gold_bias"] = "bullish"
        signals["dollar_bias"] = "bullish"
        signals["equity_bias"] = "bearish"
        signals["emerging_market_bias"] = "bearish"
        signals["conviction"] = "moderate"
        signals["drivers"].append(f"Energy disruption signals: +{upside_count} vs -{downside_count}")
    elif downside_count > upside_count:
        signals["brent_bias"] = "bearish"
        signals["gold_bias"] = "bearish"
        signals["dollar_bias"] = "bearish"
        signals["equity_bias"] = "bullish"
        signals["emerging_market_bias"] = "bullish"
        signals["conviction"] = "moderate"
        signals["drivers"].append(f"De-escalation signals: +{downside_count} vs -{upside_count}")

    # Check for China/Taiwan risk
    if any(k in all_text for k in ["china", "taiwan", "beijing", "pla"]):
        signals["equity_bias"] = "bearish"
        signals["dollar_bias"] = "bullish"

    if signals.get("brent_bias") == "bullish" and signals.get("equity_bias") == "bearish":
        signals["conviction"] = "high"

    return signals


def generate_trade_decision(portfolio: dict, signals: dict, date_str: str) -> list[dict]:
    """Generate trades based on portfolio state and geopolitical signals."""
    decisions = []
    positions = portfolio.get("positions", [])
    open_count = len([p for p in positions if p.get("status") == "open"])
    cash = portfolio.get("cash", 0)
    total_value = get_portfolio_value(portfolio)

    # Check if any existing positions need closing
    for pos in positions:
        if pos.get("status") != "open":
            continue
        instr = INSTRUMENTS.get(pos["instrument"], {})
        price = instr.get("current_price", pos["entry_price"])
        dir_mult = 1 if pos["direction"] == "long" else -1
        mtm_pct = ((price - pos["entry_price"]) / pos["entry_price"]) * dir_mult * 100

        # Stop loss hit
        stop = pos.get("stop_loss", 0)
        if (pos["direction"] == "long" and price <= stop) or \
           (pos["direction"] == "short" and price >= stop):
            decisions.append({
                "action": "close",
                "trade_id": pos["trade_id"],
                "price": price,
                "reason": f"Stop loss triggered ({mtm_pct:.1f}%)",
            })

        # Take profit
        target = pos.get("target", 0)
        if (pos["direction"] == "long" and price >= target) or \
           (pos["direction"] == "short" and price <= target):
            decisions.append({
                "action": "close",
                "trade_id": pos["trade_id"],
                "price": price,
                "reason": f"Target reached ({mtm_pct:.1f}%)",
            })

    # Check if we should open new positions
    if open_count < 3 and cash > 100:
        if signals["brent_bias"] == "bullish" and cash > 200:
            decisions.append({
                "action": "open",
                "instrument": "BRENT",
                "direction": "long",
                "size_pct": 30,
                "price": INSTRUMENTS["BRENT"]["current_price"],
                "reason": f"Bullish energy signal from GSIB: {signals['drivers'][:1] if signals['drivers'] else 'geopolitical risk'}",
            })
        elif signals["brent_bias"] == "bearish" and cash > 200:
            decisions.append({
                "action": "open",
                "instrument": "BRENT",
                "direction": "short",
                "size_pct": 25,
                "price": INSTRUMENTS["BRENT"]["current_price"],
                "reason": "Bearish energy signal from GSIB",
            })

        if signals["gold_bias"] == "bullish" and cash > 150:
            decisions.append({
                "action": "open",
                "instrument": "GLD",
                "direction": "long",
                "size_pct": 25,
                "price": INSTRUMENTS["GLD"]["current_price"],
                "reason": "Safe haven demand from geopolitical uncertainty",
            })

        if signals["dollar_bias"] == "bullish" and cash > 150:
            decisions.append({
                "action": "open",
                "instrument": "UUP",
                "direction": "long",
                "size_pct": 20,
                "price": INSTRUMENTS["UUP"]["current_price"],
                "reason": "USD strength from flight-to-safety",
            })

    return decisions


# ── Reporting ─────────────────────────────────────────────────────

def generate_report(portfolio: dict, signals: dict, decisions: list[dict],
                    date_str: str) -> str:
    """Generate a daily trading report."""
    total_value = get_portfolio_value(portfolio)
    total_pl = portfolio.get("total_pl", 0)
    open_positions = [p for p in portfolio.get("positions", []) if p.get("status") == "open"]

    lines = []
    lines.append(f"# Geopolitical Trading — Daily Report")
    lines.append(f"**Date:** {date_str}")
    lines.append("")

    # Portfolio summary
    lines.append("## Portfolio Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Initial Capital | ${portfolio['initial_capital']:.2f} |")
    lines.append(f"| Current Cash | ${portfolio['cash']:.2f} |")
    lines.append(f"| Open Positions | {len(open_positions)}/3 |")
    lines.append(f"| Total P&L | ${total_pl:.2f} ({portfolio.get('total_pl_pct', 0):.1f}%) |")
    lines.append(f"| Total Value | ${total_value:.2f} |")
    lines.append("")

    # Open positions
    if open_positions:
        lines.append("## Open Positions")
        lines.append("")
        lines.append("| Trade ID | Instrument | Direction | Entry | Current | Size | P&L | P&L % | Target | Stop |")
        lines.append("|----------|-------------|-----------|-------|---------|------|-----|-------|--------|------|")
        for pos in open_positions:
            pl_sym = "+" if pos.get("unrealized_pl", 0) >= 0 else ""
            lines.append(
                f"| {pos['trade_id']} | {pos['instrument']} | {pos['direction']} | "
                f"${pos['entry_price']:.2f} | ${pos.get('current_price', 0):.2f} | "
                f"${pos['size']:.4f} | {pl_sym}${pos.get('unrealized_pl', 0):.2f} | "
                f"{pos.get('unrealized_pl_pct', 0):.1f}% | ${pos.get('target', 0):.2f} | "
                f"${pos.get('stop_loss', 0):.2f} |"
            )
        lines.append("")

    # Recent trades
    recent_trades = portfolio.get("trade_history", [])[-5:]
    if recent_trades:
        lines.append("## Recent Closed Trades")
        lines.append("")
        for t in reversed(recent_trades):
            pl_sym = "+" if t.get("realized_pl", 0) >= 0 else "🔴" if t.get("realized_pl", 0) < 0 else ""
            sign = "+" if t.get("realized_pl", 0) >= 0 else ""
            lines.append(f"- {t['exit_date']}: {t['direction'].upper()} {t['instrument']} "
                         f"→ {sign}${t.get('realized_pl', 0):.2f} ({t.get('realized_pl_pct', 0):.1f}%) — {t.get('close_reason', 'closed')}")
        lines.append("")

    # Today's signals
    lines.append("## Today's Geopolitical Signals")
    lines.append("")
    lines.append(f"| Instrument | Bias |")
    lines.append(f"|------------|------|")
    lines.append(f"| Brent Crude | {signals.get('brent_bias', 'neutral').upper()} |")
    lines.append(f"| Gold | {signals.get('gold_bias', 'neutral').upper()} |")
    lines.append(f"| USD Index | {signals.get('dollar_bias', 'neutral').upper()} |")
    lines.append(f"| S&P 500 | {signals.get('equity_bias', 'neutral').upper()} |")
    lines.append(f"| EM ETFs | {signals.get('emerging_market_bias', 'neutral').upper()} |")
    lines.append(f"**Conviction:** {signals.get('conviction', 'low')}")
    if signals.get("drivers"):
        lines.append(f"**Drivers:** {'; '.join(signals['drivers'][:3])}")
    lines.append("")

    # Today's trades
    if decisions:
        lines.append("## Trades Executed Today")
        lines.append("")
        for d in decisions:
            if d["action"] == "open":
                lines.append(f"- ✅ OPEN {d['direction'].upper()} {d['instrument']} "
                             f"@ ${d['price']:.2f} ({d['size_pct']}% of cash)")
                lines.append(f"  Reason: {d['reason']}")
            elif d["action"] == "close":
                lines.append(f"- 🔒 CLOSE {d['trade_id']} @ ${d['price']:.2f}")
                lines.append(f"  Reason: {d['reason']}")
        lines.append("")
    else:
        lines.append("No trades executed today.")
        lines.append("")

    # Performance tracker
    lines.append("## Running Performance")
    lines.append("")
    created_date = dt.datetime.strptime(
        portfolio.get("created", date_str), "%Y-%m-%d"
    ).replace(tzinfo=dt.timezone.utc)
    days_trading = (dt.datetime.now(dt.timezone.utc) - created_date).days + 1
    lines.append(f"- Days active: {days_trading}")
    lines.append(f"- Total trades: {len(portfolio.get('trade_history', []))}")
    lines.append(f"- Win rate: {_compute_win_rate(portfolio)}%")
    lines.append(f"- Sharpe (approx): {_compute_sharpe(portfolio)}")

    return "\n".join(lines)


def _compute_win_rate(portfolio: dict) -> float:
    trades = portfolio.get("trade_history", [])
    if not trades:
        return 0.0
    wins = sum(1 for t in trades if t.get("realized_pl", 0) > 0)
    return round(wins / len(trades) * 100, 1)


def _compute_sharpe(portfolio: dict) -> float:
    trades = portfolio.get("trade_history", [])
    if len(trades) < 2:
        return 0.0
    returns = [t.get("realized_pl_pct", 0) for t in trades]
    avg_return = sum(returns) / len(returns)
    std_dev = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
    if std_dev == 0:
        return 0.0
    return round(avg_return / std_dev, 2)


def run_daily(date_str: str, mock: bool = False) -> dict:
    """Run the daily trading cycle: signals → decisions → execute."""
    portfolio = load_portfolio()

    # Update prices
    update_prices_from_web(portfolio)

    # Get signals from GSIB
    signals = get_gsib_signals(date_str)

    # Generate trade decisions
    decisions = generate_trade_decision(portfolio, signals, date_str)

    if not mock:
        # Execute decisions
        for d in decisions:
            if d["action"] == "open":
                open_trade(portfolio, d["instrument"], d["direction"],
                            d["size_pct"], d["price"], d["reason"], date_str)
            elif d["action"] == "close":
                close_trade(portfolio, d["trade_id"], d["price"], d["reason"], date_str)

        # Save portfolio state
        save_portfolio(portfolio)

    # Generate report
    report = generate_report(portfolio, signals, decisions, date_str)

    # Save report
    GEOTRADE_DIR.mkdir(parents=True, exist_ok=True)
    report_path = GEOTRADE_DIR / f"{date_str}.md"
    report_path.write_text(report)

    return {
        "portfolio": portfolio,
        "signals": signals,
        "decisions": decisions,
        "report": report,
        "report_path": str(report_path),
    }


def show_report() -> None:
    """Show the portfolio summary."""
    portfolio = load_portfolio()
    open_pos = [p for p in portfolio.get("positions", []) if p.get("status") == "open"]
    total_value = get_portfolio_value(portfolio)

    print(f"# Geopolitical Portfolio Summary")
    print(f"**Initial:** ${portfolio['initial_capital']:.2f}")
    print(f"**Current:** ${total_value:.2f}")
    print(f"**Total P&L:** ${portfolio.get('total_pl', 0):.2f} ({portfolio.get('total_pl_pct', 0):.1f}%)")
    print(f"**Open Positions:** {len(open_pos)}/3")
    print(f"**Cash:** ${portfolio['cash']:.2f}")
    print(f"**Total Trades:** {len(portfolio.get('trade_history', []))}")
    print()
    if open_pos:
        print("**Open Positions:**")
        for p in open_pos:
            print(f"  {p['instrument']} ({p['direction']}): entry=${p['entry_price']:.2f}, "
                  f"current=${p.get('current_price', 0):.2f}, "
                  f"unrealized=${p.get('unrealized_pl', 0):.2f} ({p.get('unrealized_pl_pct', 0):.1f}%)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="", help="Date in YYYY-MM-DD format")
    parser.add_argument("--mock", action="store_true", help="Dry run — no trades executed")
    parser.add_argument("--report", action="store_true", help="Portfolio summary")
    args = parser.parse_args()

    if args.report:
        show_report()
        return 0

    date_str = args.date or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")

    result = run_daily(date_str, mock=args.mock)

    print(result["report"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
