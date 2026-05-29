#!/usr/bin/env python3
"""
Philby Daemon — Hourly Trading Report
Reads daemon journal/state and delivers a concise Telegram update.
Called by OpenClaw cron every hour.

Usage:
    python3 philby/trader/hourly_report.py           # Send report
    python3 philby/trader/hourly_report.py --preview  # Print without sending
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
from typing import Any

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
JOURNAL_FILE = REPO / "philby" / "trader" / "journal.jsonl"
POSITIONS_FILE = REPO / "philby" / "trader" / "positions_live.json"
WS_LOG = REPO / "logs" / "kalshi" / "ws-events.jsonl"
DAEMON_LOG = REPO / "logs" / "philby-daemon.log"


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[report {ts}] {msg}", file=sys.stderr, flush=True)


def tail_lines(path: pathlib.Path, n: int = 30) -> list[str]:
    """Read last N lines from a file efficiently."""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            pos = f.tell()
            lines = []
            while pos >= 0 and len(lines) < n:
                f.seek(pos)
                c = f.read(1)
                if c == b"\n":
                    line = f.readline().decode("utf-8", errors="replace").rstrip()
                    if line:
                        lines.append(line)
                pos -= 1
            lines.reverse()
            return lines
    except FileNotFoundError:
        return []


def get_today_trades() -> list[dict]:
    """Get today's trades from journal."""
    today = dt.date.today().isoformat()
    trades = []
    if not JOURNAL_FILE.exists():
        return trades
    for line in JOURNAL_FILE.read_text().splitlines():
        try:
            entry = json.loads(line.strip())
            ts = entry.get("timestamp", "")
            if ts.startswith(today):
                trades.append(entry)
        except (json.JSONDecodeError,):
            pass
    return trades


def get_recent_signals() -> list[dict]:
    """Read latest signals from intel bridge."""
    signals_file = REPO / "philby" / "trader" / "signals" / "latest.json"
    if not signals_file.exists():
        return []
    try:
        data = json.loads(signals_file.read_text())
        return data.get("tradeable", [])
    except (json.JSONDecodeError,):
        return []


def get_positions() -> dict:
    """Read live positions."""
    if not POSITIONS_FILE.exists():
        return {"positions": [], "portfolio_value": 0, "peak_value": 0}
    try:
        return json.loads(POSITIONS_FILE.read_text())
    except (json.JSONDecodeError,):
        return {"positions": [], "portfolio_value": 0}


def check_daemon_running() -> bool:
    """Check if daemon PID file exists and process is alive."""
    pid_file = REPO / "philby" / "trader" / "daemon.pid"
    if not pid_file.exists():
        return False
    try:
        pid = int(pid_file.read_text().strip())
        os.kill(pid, 0)  # signal 0 = check existence
        return True
    except (ValueError, OSError, ProcessLookupError):
        return False


def build_report() -> dict[str, Any]:
    """Compile the hourly trading report."""
    today_trades = get_today_trades()
    positions_data = get_positions()
    signals = get_recent_signals()
    daemon_running = check_daemon_running()

    # Trades summary
    executed = [t for t in today_trades if t.get("status") == "executed"]
    failed = [t for t in today_trades if t.get("status") == "failed"]
    exited = [t for t in today_trades if t.get("type") == "exit"]
    entries = [t for t in today_trades if t.get("type") in (None, "entry") and t.get("status") == "executed"]

    # Positions
    positions = positions_data.get("positions", [])
    portfolio_value = positions_data.get("portfolio_value", 0)
    peak_value = positions_data.get("peak_value", 0)
    daily_pnl = positions_data.get("daily_pnl", 0)

    # Drawdown
    drawdown_pct = 0
    if peak_value and peak_value > 0:
        drawdown_pct = round((peak_value - portfolio_value) / peak_value * 100, 1)

    # Top signals
    top_signals = sorted(
        signals,
        key=lambda s: abs(s.get("edge_pts", 0) or 0),
        reverse=True,
    )[:7]

    # WS log stats
    ws_lines = 0
    try:
        with open(WS_LOG) as f:
            for _ in f:
                ws_lines += 1
    except FileNotFoundError:
        pass

    # Last daemon log lines for recent activity
    recent_activity = tail_lines(DAEMON_LOG, 10)

    return {
        "daemon_running": daemon_running,
        "timestamp": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "portfolio_value": portfolio_value,
        "daily_pnl": daily_pnl,
        "drawdown": drawdown_pct,
        "open_positions": len(positions),
        "total_positions_value": sum(p.get("current_value", 0) for p in positions),
        "trades_today": len(today_trades),
        "executed_today": len(entries),
        "exited_today": len(exited),
        "failed_today": len(failed),
        "top_signals": top_signals,
        "ws_events_total": ws_lines,
        "recent_activity": recent_activity,
    }


def format_telegram(report: dict) -> str:
    """Format report for Telegram delivery."""
    lines = [
        f"🤖 *Philby Trading Report*",
        f"📅 {report['timestamp']}",
        f"",
    ]

    # Status
    status = "🟢 RUNNING" if report["daemon_running"] else "🔴 STOPPED"
    lines.append(f"*Daemon:* {status}")

    # Portfolio
    pnl_icon = "🟢" if report["daily_pnl"] >= 0 else "🔴"
    lines.append(f"*Portfolio:* ${report['portfolio_value']:.2f}")
    lines.append(f"*Today:* {pnl_icon} ${report['daily_pnl']:+.2f} ({report['drawdown']:+.1f}% dd)")
    lines.append(f"")

    # Positions
    lines.append(f"*Positions:* {report['open_positions']} open | {report['exited_today']} exited today")
    lines.append(f"*Trades:* {report['executed_today']} entered / {report['failed_today']} failed today")
    lines.append(f"")

    # Top signals
    if report["top_signals"]:
        lines.append(f"*Top Signals:*")
        for s in report["top_signals"][:5]:
            edge = s.get("edge_pts", 0)
            ticker = s.get("ticker", s.get("mapping", "?"))[:30]
            t_conf = s.get("trevor_confidence", 0)
            m_conf = s.get("market_confidence", 0)
            arrow = "🟢" if edge > 0 else "🔴"
            lines.append(f"  {arrow} {ticker}: T={t_conf:.0f}% M={m_conf:.0f}% edge={edge:+.0f}pts")
        lines.append(f"")

    # Recent activity
    if report["recent_activity"]:
        lines.append(f"*Recent:*")
        for line in report["recent_activity"][-5:]:
            # Trim long lines
            if len(line) > 200:
                line = line[:200] + "..."
            lines.append(f"  `{line[:150]}`")

    return "\n".join(lines)


def format_preview(report: dict) -> str:
    """Format report for console preview (more detail)."""
    lines = [
        "=" * 60,
        f"  Philby Daemon — Hourly Report",
        f"  {report['timestamp']}",
        "=" * 60,
        f"  Daemon: {'🟢 RUNNING' if report['daemon_running'] else '🔴 STOPPED'}",
        f"  Portfolio: ${report['portfolio_value']:.2f} | Today: ${report['daily_pnl']:+.2f} | DD: {report['drawdown']:+.1f}%",
        f"  Positions: {report['open_positions']} open | Trades today: {report['executed_today']} entered, {report['exited_today']} exited, {report['failed_today']} failed",
        f"  WS Events: {report['ws_events_total']:,}",
    ]

    if report["top_signals"]:
        lines.append(f"")
        lines.append(f"  Top Signals:")
        for s in report["top_signals"][:7]:
            edge = s.get("edge_pts", 0)
            ticker = s.get("ticker", s.get("mapping", "?"))
            t_conf = s.get("trevor_confidence", 0)
            m_conf = s.get("market_confidence", 0)
            vol = s.get("volume", 0)
            lines.append(f"    {edge:+.0f}pt {ticker:<40s} T={t_conf:.0f}% M={m_conf:.0f}% vol=${vol:,}")

    if report["recent_activity"]:
        lines.append(f"")
        lines.append(f"  Recent Activity:")
        for line in report["recent_activity"]:
            lines.append(f"    {line[:150]}")

    return "\n".join(lines)


def main() -> int:
    """Build and output the report. When run by cron, stdout is captured and
    delivered to Telegram by the OpenClaw cron system. Use --preview for
    local testing with detailed formatting."""
    parser = argparse.ArgumentParser(description="Philby Hourly Trading Report")
    parser.add_argument("--preview", action="store_true", help="Print detailed preview to console")
    args = parser.parse_args()

    report = build_report()

    if args.preview:
        print(format_preview(report))
    else:
        # Print Telegram-formatted report to stdout for cron delivery
        print(format_telegram(report))
        # Also log to stderr for daemon log
        log("Report printed to stdout for cron delivery")

    return 0


if __name__ == "__main__":
    sys.exit(main())
