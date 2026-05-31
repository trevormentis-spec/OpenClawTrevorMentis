#!/usr/bin/env python3
"""
Human Confirmation System — Pending Order Queue

When the gated client needs human confirmation, it writes the proposed order
to `pending/orders/` as a JSON file. The confirmation supervisor checks for
pending orders, formats a Telegram message, and waits for a response.

Phase 3: All trades require human confirmation.
Phase 4+: Only trades above threshold require confirmation.
"""

from __future__ import annotations

import json
import os
import sys
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


def create_pending_order(
    ticker: str,
    side: str,
    shares: int,
    price_cents: float,
    total_cost: float,
    edge_pct: float,
    confidence: str,
    kj_id: str,
    summary: str,
) -> str:
    """Create a pending order awaiting human confirmation.

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
        "summary": summary,
        "created_at": now_iso(),
        "status": "pending",
    }

    path = PENDING_DIR / f"{order_id}.json"
    path.write_text(json.dumps(order, indent=2))

    return order_id


def get_pending_orders() -> list[dict]:
    """Get all pending (unconfirmed) orders."""
    ensure_dirs()
    orders = []
    for f in sorted(PENDING_DIR.glob("*.json")):
        try:
            order = json.loads(f.read_text())
            if order.get("status") == "pending":
                # Check if expired (older than 1 hour)
                try:
                    created = datetime.fromisoformat(order["created_at"].replace("Z", "+00:00"))
                    age_minutes = (datetime.now(timezone.utc) - created).total_seconds() / 60
                    if age_minutes > 60:
                        order["status"] = "expired"
                        f.write_text(json.dumps(order, indent=2))
                        continue
                except (ValueError, KeyError):
                    pass
                orders.append(order)
        except (json.JSONDecodeError, OSError):
            continue
    return orders


def format_confirmation_message(order: dict) -> str:
    """Format a pending order as a Telegram confirmation message."""
    return (
        f"📋 **Trade Confirmation Required**\n\n"
        f"**{order['side']}** {order['shares']} shares **{order['ticker']}**\n"
        f"Price: {order['price_cents']}¢ | Cost: ${order['total_cost_dollars']}\n"
        f"Edge: {order['edge_pct']}pp | Confidence: {order['confidence']}\n"
        f"Intel: {order.get('kj_id', 'N/A')}\n\n"
        f"_{order.get('summary', '')}_\n\n"
        f"Reply with:\n"
        f"  `/confirm {order['order_id']}` to execute\n"
        f"  `/reject {order['order_id']}` to cancel\n"
        f"  Order auto-expires in 60 minutes"
    )


def respond_to_order(order_id: str, decision: str, notes: str = "") -> bool:
    """Record a human decision on a pending order.

    Args:
        order_id: The order ID
        decision: "confirmed" or "rejected"
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

    # Also save response separately
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


def confirmation_required() -> bool:
    """Check if human confirmation is required at current autonomy level."""
    level = check_autonomy_level()
    return level < 3  # Levels 0-2 require confirmation
