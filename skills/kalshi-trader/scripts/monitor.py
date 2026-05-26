#!/usr/bin/env python3
"""
Kalshi Position Monitor & Autonomous Exit Engine

Monitors open positions, enforces stop-loss/take-profit, and sends alerts.
Runs as a continuous loop (--loop) or one-shot (default).

Usage:
  python3 monitor.py                     # One-shot position check
  python3 monitor.py --loop --interval 60  # Continuous monitoring every 60s
  python3 monitor.py --alert-on-exit       # Execute stop-loss/take-profit
  python3 monitor.py --summary             # P&L summary only
"""

import sys
import json
import time
import signal
import argparse
import logging
from pathlib import Path
import datetime
from typing import Optional, Dict, Any, List

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

from client import KalshiClient, KalshiAPIError, KalshiAuthError
from guard import RiskGuard, PositionState
from runtime_lock import RuntimeLock

logger = logging.getLogger("kalshi-monitor")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [monitor] %(message)s", datefmt="%H:%M:%S"))
logger.addHandler(handler)

# State file for persistence
STATE_FILE = Path(__file__).parent.parent / "state" / "monitor_state.json"


class PositionMonitor:
    """Tracks positions and enforces guardrails with autonomous exit capability."""

    def __init__(self, auto_exit: bool = False):
        self.client = KalshiClient()
        self.guard = RiskGuard()
        self.auto_exit = auto_exit
        self._running = True
        self._positions_cache: Dict[str, PositionState] = {}
        self._load_state()

    def _load_state(self):
        """Load persistent state (peak portfolio, daily P&L)."""
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            if STATE_FILE.exists():
                with open(STATE_FILE) as f:
                    state = json.load(f)
                    self.guard._peak_portfolio_cents = state.get("peak_portfolio", 0)
                    self.guard._daily_pnl_cents = state.get("daily_pnl", 0)
                    # Reset daily if it's a new day
                    last_date = state.get("last_date", "")
                    today = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
                    if last_date != today:
                        self.guard.reset_daily()
        except Exception:
            pass

    def _save_state(self, balance_cents: int):
        """Persist state to disk."""
        self.guard.update_peak(balance_cents)
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(STATE_FILE, "w") as f:
                json.dump({
                    "peak_portfolio": self.guard._peak_portfolio_cents,
                    "daily_pnl": self.guard._daily_pnl_cents,
                    "last_date": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d"),
                    "last_updated": datetime.datetime.now(datetime.UTC).isoformat(),
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save state: {e}")

    def fetch_state(self) -> Dict[str, Any]:
        """Fetch current portfolio state from Kalshi."""
        result = {
            "balance_cents": 0,
            "positions": [],
            "open_orders": [],
            "error": None,
        }

        try:
            bal = self.client.get_balance()
            # Kalshi v2 returns balance_dollars
            balance_dollars = float(bal.get("balance_dollars", bal.get("balance", 0)))
            result["balance_cents"] = int(balance_dollars * 100)
        except KalshiAPIError as e:
            result["error"] = f"Balance: {e}"
            return result

        try:
            pos_resp = self.client.get_positions()
            # Kalshi API returns market_positions (not positions)
            market_positions = pos_resp.get("market_positions", pos_resp.get("positions", []))
            for p in market_positions:
                ticker = p.get("ticker", "?")
                count_fp = float(p.get("position_fp", p.get("count_fp", p.get("count", 0))))
                count = int(count_fp)
                if count == 0:
                    continue

                # Cost basis from API
                cost_dollars = float(p.get("total_traded_dollars", 0))
                if not cost_dollars:
                    cost_dollars = float(p.get("market_exposure_dollars", 0))
                cost_cents = int(cost_dollars * 100)

                # Entry price: cost / count
                entry_cents = int((cost_dollars / count_fp) * 100) if count_fp > 0 else 0

                # Get live market pricing
                current_price_cents = entry_cents
                mkt_value_cents = cost_cents
                yes_bid = 0
                yes_ask = 0
                try:
                    mkt = self.client.get_market(ticker)
                    market = mkt.get("market", mkt)
                    lp = market.get("last_price_dollars")
                    yb = market.get("yes_bid_dollars")
                    ya = market.get("yes_ask_dollars")
                    if lp:
                        current_price_cents = int(float(lp) * 100)
                    if yb:
                        yes_bid = int(float(yb) * 100)
                    if ya:
                        yes_ask = int(float(ya) * 100)
                    mkt_value_cents = count * current_price_cents
                except Exception:
                    pass

                pos = PositionState(
                    ticker=ticker,
                    side="yes",  # All positions in market_positions are YES
                    entry_price_cents=entry_cents,
                    current_price_cents=current_price_cents,
                    count=count,
                    cost_basis_cents=cost_cents,
                    market_value_cents=mkt_value_cents,
                )
                result["positions"].append(pos)
        except KalshiAPIError as e:
            result["error"] = f"Positions: {e}"

        try:
            orders = self.client.get_orders()
            result["open_orders"] = orders.get("orders", [])
        except Exception:
            pass

        return result

    def check_and_exit(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate all positions against guardrails.
        Exits anything that triggers stop-loss or take-profit (if auto_exit enabled).
        Returns list of actions taken.
        """
        actions = []
        balance_cents = state["balance_cents"]

        for pos in state["positions"]:
            should_exit, reason = self.guard.check_exit(pos)

            if should_exit:
                logger.warning(f"EXIT TRIGGER: {pos.ticker} — {reason}")

                if self.auto_exit:
                    try:
                        # Sell YES at market (or NO if we hold NO)
                        if pos.side == "yes":
                            resp = self.client.create_order(
                                ticker=pos.ticker,
                                side="yes",
                                action="sell",
                                count=pos.count,
                                time_in_force="immediate_or_cancel",
                            )
                        else:
                            resp = self.client.create_order(
                                ticker=pos.ticker,
                                side="no",
                                action="sell",
                                count=pos.count,
                                time_in_force="immediate_or_cancel",
                            )

                        order = resp.get("order", resp)
                        actions.append({
                            "action": "exit",
                            "ticker": pos.ticker,
                            "reason": reason,
                            "order_id": order.get("order_id"),
                            "status": order.get("status", "?"),
                            "pnl_pct": round(
                                ((pos.current_price_cents - pos.entry_price_cents) 
                                 / max(pos.entry_price_cents, 1)) * 100, 1
                            ),
                        })
                        logger.info(f"  ✅ Exited {pos.ticker} ({order.get('order_id','?')[:16]}...)")
                    except KalshiAPIError as e:
                        logger.error(f"  ❌ Failed to exit {pos.ticker}: {e}")
                        actions.append({
                            "action": "exit_failed",
                            "ticker": pos.ticker,
                            "reason": reason,
                            "error": str(e),
                        })
                else:
                    # Alert only
                    actions.append({
                        "action": "alert",
                        "ticker": pos.ticker,
                        "reason": reason,
                        "entry_cents": pos.entry_price_cents,
                        "current_cents": pos.current_price_cents,
                        "pnl_pct": round(
                            ((pos.current_price_cents - pos.entry_price_cents) 
                             / max(pos.entry_price_cents, 1)) * 100, 1
                        ),
                    })

        return actions

    def can_trade(self, state: Dict[str, Any]) -> tuple:
        """Check if new trades are allowed."""
        exposure = sum(p.market_value_cents for p in state["positions"])
        can, reason = self.guard.can_open_position(
            balance_cents=state["balance_cents"],
            current_exposure_cents=exposure,
            open_positions=len(state["positions"]),
            daily_pnl_cents=self.guard._daily_pnl_cents,
        )
        return can, reason

    def run_once(self) -> Dict[str, Any]:
        """Single monitoring cycle with 30s hard timeout."""
        signal.alarm(30)
        try:
            state = self.fetch_state()

            if state["error"]:
                logger.error(state["error"])
                return {"error": state["error"]}

            self._save_state(state["balance_cents"])
            actions = self.check_and_exit(state)
            can_trade, trade_reason = self.can_trade(state)

            return {
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
                "balance_cents": state["balance_cents"],
                "positions": state["positions"],
                "position_count": len(state["positions"]),
                "open_order_count": len(state["open_orders"]),
                "actions": actions,
                "can_trade": can_trade,
                "trade_reason": trade_reason,
                "guardrail_status": self.guard.status_report(
                    state["balance_cents"], state["positions"]
                ),
            }
        finally:
            signal.alarm(0)
    def run_loop(self, interval: int = 60):
        """Continuous monitoring loop with graceful shutdown."""
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        with RuntimeLock(f"monitor-{interval}", timeout=86400) as lock:
            if not lock.acquired:
                logger.error("Another monitor instance is running — exiting")
                return

            logger.info(f"Monitor started (interval={interval}s, auto_exit={self.auto_exit})")

            while self._running:
                try:
                    result = self.run_once()

                    if result.get("actions"):
                        for action in result["actions"]:
                            if action["action"] == "exit":
                                logger.warning(
                                    f"🔥 AUTO-EXIT: {action['ticker']} "
                                    f"({action['reason']}, PnL: {action.get('pnl_pct', '?')}%)"
                                )
                            elif action["action"] == "alert":
                                logger.warning(
                                    f"⚠️  EXIT SIGNAL: {action['ticker']} "
                                    f"({action['reason']}, PnL: {action.get('pnl_pct', '?')}%) "
                                    f"— auto_exit disabled"
                                )

                    if not result["can_trade"]:
                        logger.warning(f"🛑 TRADING HALTED: {result['trade_reason']}")

                    # Build position detail string
                    pos_details = "unknown"
                    pos_list = result.get("positions", [])
                    if pos_list:
                        pos_strs = []
                        for p in pos_list:
                            t = getattr(p, "ticker", "?")
                            c = getattr(p, "count", 0)
                            e = getattr(p, "entry_price_cents", 0)
                            pos_strs.append(f"{t}x{c}@${e/100:.2f}")
                        pos_details = ", ".join(pos_strs)

                    logger.info(
                        f"Balance: ${result['balance_cents']/100:.2f} | "
                        f"Positions: {result['position_count']} [{pos_details}] | "
                        f"Orders: {result['open_order_count']} | "
                        f"Can trade: {result['can_trade']}"
                    )

                except Exception as e:
                    logger.error(f"Cycle error: {e}")

            # Run runtime health check every 5 cycles (~10 min at 120s interval)
            if not hasattr(self, '_health_cycle'):
                self._health_cycle = 0
            self._health_cycle += 1
            if self._health_cycle >= 5:
                self._health_cycle = 0
                try:
                    import subprocess
                    subprocess.run(
                        ["bash", "scripts/runtime-health.sh"],
                        cwd="/home/ubuntu/.openclaw/workspace",
                        timeout=60,
                        capture_output=True
                    )
                except Exception:
                    pass

            # Sleep with interruptible check
            for _ in range(interval):
                if not self._running:
                    break
                time.sleep(1)

        logger.info("Monitor stopped")

    def _handle_shutdown(self, signum, frame):
        logger.info("Shutdown signal received, finishing cycle...")
        self._running = False


def main():
    parser = argparse.ArgumentParser(description="Kalshi Position Monitor")
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument("--interval", type=int, default=60, help="Poll interval in seconds")
    parser.add_argument("--auto-exit", action="store_true", 
                        help="Execute stop-loss/take-profit automatically")
    parser.add_argument("--summary", action="store_true", help="Print P&L summary only")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    monitor = PositionMonitor(auto_exit=args.auto_exit)

    if args.loop:
        monitor.run_loop(interval=args.interval)
    else:
        result = monitor.run_once()

        if args.json:
            print(json.dumps(result, indent=2, default=str))
        elif args.summary:
            print(result["guardrail_status"])
        else:
            print(result["guardrail_status"])
            if result.get("actions"):
                print(f"\n⚠️  {len(result['actions'])} exit signal(s):")
                for a in result["actions"]:
                    print(f"  {a['action'].upper()}: {a['ticker']} — {a['reason']}")
            print(f"\nTrading: {'✅ ALLOWED' if result['can_trade'] else '🛑 HALTED'}")


if __name__ == "__main__":
    main()
