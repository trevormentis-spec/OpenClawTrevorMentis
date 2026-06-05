#!/usr/bin/env python3
"""
Human Confirmation System — Entry Approval, Automated Management

Entry orders (buying to open a position) → human approval required.
Exit/management orders (selling to close) → fully automated.

Level 0-3: Entry orders require human confirmation.
Level 4+:  Entry orders auto-execute (full autonomy).
Management (exit/sell) orders always auto-execute.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
PENDING_DIR = REPO / "pending" / "orders"
RESPONSES_DIR = REPO / "pending" / "responses"
STATE_FILE = REPO / "guardrails" / "autonomy_state.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dirs():
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    RESPONSES_DIR.mkdir(parents=True, exist_ok=True)


def is_entry_order(action: str) -> bool:
    """Is this a position-opening order?

    In Kalshi: action="buy" opens a position (entry),
    action="sell" closes a position (exit/management).
    """
    return action == "buy"


def create_pending_entry(
    ticker: str,
    side: str,
    shares: int,
    price_cents: float,
    total_cost: float,
    edge_pct: float,
    confidence: str,
    kj_id: str,
    rationale: str,
    portfolio_summary: str = "",
) -> str:
    """Create a pending entry order awaiting human approval.

    Returns the order ID.
    """
    ensure_dirs()
    order_id = str(uuid.uuid4())[:8]
    order = {
        "order_id": order_id,
        "ticker": ticker,
        "side": side,
        "shares": shares,
        "price_cents": round(price_cents, 1),
        "total_cost_dollars": round(total_cost, 2),
        "edge_pct": round(edge_pct, 2),
        "confidence": confidence,
        "kj_id": kj_id,
        "rationale": rationale,
        "portfolio_summary": portfolio_summary,
        "created_at": now_iso(),
        "status": "pending",
    }

    path = PENDING_DIR / f"{order_id}.json"
    path.write_text(json.dumps(order, indent=2))

    return order_id


def get_pending_entries() -> list[dict]:
    """Get all pending (unapproved) entry orders."""
    ensure_dirs()
    orders = []
    for f in sorted(PENDING_DIR.glob("*.json")):
        try:
            order = json.loads(f.read_text())
            if order.get("status") == "pending":
                # Check if expired (older than 30 minutes)
                try:
                    created = datetime.fromisoformat(order["created_at"].replace("Z", "+00:00"))
                    age_minutes = (datetime.now(timezone.utc) - created).total_seconds() / 60
                    if age_minutes > 30:
                        order["status"] = "expired"
                        f.write_text(json.dumps(order, indent=2))
                        continue
                except (ValueError, KeyError):
                    pass
                orders.append(order)
        except (json.JSONDecodeError, OSError):
            continue
    return orders


def format_entry_approval_message(order: dict) -> str:
    """Format a pending entry as a Telegram approval request."""
    direction_arrow = "🟢" if order.get("side") == "yes" else "🔴"
    lines = [
        f"📈 **Entry Approval Needed**",
        "",
        f"{direction_arrow} BUY {order['side'].upper()} {order['ticker']} x{order['shares']}",
        f"   Price: {order['price_cents']}¢ | Cost: ${order['total_cost_dollars']}",
        f"   Edge: {order['edge_pct']}pp | Confidence: {order['confidence']}",
        f"   Intel: {order.get('kj_id', 'N/A')}",
        "",
        f"_{order.get('rationale', '')}_",
        "",
    ]
    if order.get("portfolio_summary"):
        lines.append(f"Portfolio: {order['portfolio_summary']}")
        lines.append("")
    lines.extend([
        f"Reply `/enter {order['order_id']}` to execute",
        f"Reply `/skip {order['order_id']}` to pass",
        "Auto-expires in 30 min",
    ])
    return "\n".join(lines)


def respond_to_entry(order_id: str, decision: str, notes: str = "") -> bool:
    """Record a human decision on a pending entry order.

    Args:
        order_id: The order ID
        decision: "approved" or "skipped"
        notes: Optional human notes

    Returns:
        True if the order was found and updated, False otherwise
    """
    ensure_dirs()
    order_path = PENDING_DIR / f"{order_id}.json"
    if not order_path.exists():
        return False

    try:
        order = json.loads(order_path.read_text())
    except (json.JSONDecodeError, OSError):
        return False

    order["status"] = decision
    order["responded_at"] = now_iso()
    order["response_notes"] = notes
    order_path.write_text(json.dumps(order, indent=2))

    response = {
        "order_id": order_id,
        "decision": decision,
        "notes": notes,
        "responded_at": now_iso(),
        "ticker": order.get("ticker"),
        "side": order.get("side"),
    }
    response_path = RESPONSES_DIR / f"{order_id}.json"
    response_path.write_text(json.dumps(response, indent=2))

    return True


def check_autonomy_level() -> int:
    """Check current autonomy level from state file."""
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
            return state.get("level", 0)
        except (json.JSONDecodeError, OSError):
            pass
    return 0


def entry_confirmation_required() -> bool:
    """Check if entry orders need human approval.

    Management/exit orders never require confirmation — they auto-execute.
    Entry orders require approval at current autonomy level.
    """
    level = check_autonomy_level()
    return level < 4  # Entries approved by human below level 4
