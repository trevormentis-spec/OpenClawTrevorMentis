#!/usr/bin/env python3
"""
Daily Reconciliation Report — Positions, P&L, Calibration

Runs daily (or on demand) and delivers a structured report showing:
- Open positions with current P&L
- Today's P&L
- Account equity
- Calibration drift (Brier score trend)
- Pending orders
- Kill switch status
- Autonomy level progress
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Import gated client for portfolio data
sys.path.insert(0, str(REPO))

from execution.gated_client import GatedKalshiClient, TradingMode


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def generate_report() -> str:
    """Generate a daily reconciliation report text."""
    lines = []
    lines.append("=" * 60)
    lines.append(f"  KALSHI RECONCILIATION REPORT — {now_iso()[:10]}")
    lines.append("=" * 60)

    # 1. Kill switch status
    try:
        from guardrails.kill_switch import check as ks_check
        ks = ks_check()
        if ks["halted"]:
            lines.append(f"\n⛔ KILL SWITCH: ENGAGED — {ks['reason']}")
        else:
            lines.append(f"\n✅ Kill switch: Off")
    except Exception as e:
        lines.append(f"\n⚠️  Kill switch check failed: {e}")

    # 2. Portfolio
    try:
        client = GatedKalshiClient(mode=TradingMode.PAPER)  # Reads real balance in PAPER too
        p = client.get_portfolio_summary()
        equity = p.get("equity_cents", 0) / 100
        cash = p.get("cash_cents", 0) / 100
        exposure = p.get("exposure_cents", 0) / 100
        drawdown = p.get("drawdown_fraction", 0) * 100
        lines.append(f"\n💰 Portfolio: ${equity:.2f}")
        lines.append(f"   Cash: ${cash:.2f} | Exposure: ${exposure:.2f}")
        lines.append(f"   Drawdown: {drawdown:.1f}% from peak")
    except Exception as e:
        lines.append(f"\n⚠️  Portfolio read failed: {e}")

    # 3. Positions
    try:
        from intel.intel_store import IntelStore
        store = IntelStore()
        kj_count = store.count()
        lines.append(f"\n📊 Intel Store: {kj_count} KJs stored")
    except Exception as e:
        lines.append(f"\n⚠️  Intel store read failed: {e}")

    # 4. Calibration
    try:
        from calibration.brier import CalibrationTracker
        tracker = CalibrationTracker()
        b = tracker.get_brier_score()
        cal_err = tracker.get_calibration_error()
        lines.append(f"\n📈 Calibration:")
        lines.append(f"   Brier: {b['overall_brier'] or 'N/A'}")
        lines.append(f"   Skill: {b['brier_skill'] or 'N/A'}")
        lines.append(f"   Error: {cal_err if cal_err < 999 else 'N/A'}")
        lines.append(f"   Forecasts: {b['total_forecasts']} | Resolved: {b['total_resolved']}")
    except Exception as e:
        lines.append(f"\n⚠️  Calibration read failed: {e}")

    # 5. Pending orders
    try:
        from guardrails.confirmation import get_pending_orders
        pending = get_pending_orders()
        if pending:
            lines.append(f"\n⏳ Pending confirmations: {len(pending)}")
            for o in pending[:5]:
                lines.append(f"   • {o['side']} {o['shares']} {o['ticker']} @ ${o['total_cost_dollars']}")
        else:
            lines.append(f"\n⏳ No pending orders")
    except Exception as e:
        lines.append(f"\n⚠️  Pending orders check failed: {e}")

    # 6. Autonomy progress
    try:
        from calibration.brier import CalibrationTracker
        from intel.models import AutonomyLevel
        for level in [AutonomyLevel.PAPER, AutonomyLevel.TINY_CONFIRMED]:
            t = CalibrationTracker()
            result = t.evaluate_autonomy_promotion(level)
            badge = "✅" if result["eligible_for_promotion"] else "⏳"
            lines.append(f"\n{badge} Autonomy {result['current_level']}:")
            for g, s in result["gates"].items():
                lines.append(f"   {'✅' if s else '❌'} {g}")
    except Exception as e:
        lines.append(f"\n⚠️  Autonomy check failed: {e}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_report())
