#!/usr/bin/env python3
"""
Kill Switch — Emergency Halt for All Trading

Independent of the trading logic. Read by the gated client before every order.
Can be triggered via:
  - CLI: python3 guardrails/kill_switch.py --halt
  - CLI: python3 guardrails/kill_switch.py --release
  - File: echo '{"halted":true,"reason":"..."}' > guardrails/kill_switch.json

The kill switch state file is checked by the gated client on every submit_order().
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STATE_FILE = REPO / "guardrails" / "kill_switch.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def check() -> dict:
    """Check kill switch state. Returns {"halted": bool, "reason": str}."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"halted": False, "reason": "", "engaged_at": None}


def halt(reason: str = "Manual halt by operator"):
    """Engage the kill switch."""
    state = {
        "halted": True,
        "reason": reason,
        "engaged_at": now_iso(),
    }
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))
    print(f"⛔ KILL SWITCH ENGAGED: {reason}")
    return state


def release():
    """Release the kill switch."""
    state = {
        "halted": False,
        "reason": "",
        "engaged_at": None,
    }
    STATE_FILE.write_text(json.dumps(state, indent=2))
    print("✅ Kill switch released")
    return state


def status() -> str:
    """Human-readable status."""
    s = check()
    if s["halted"]:
        return f"⛔ HALTED: {s['reason']} (since {s['engaged_at']})"
    return "✅ Trading allowed"


# ── CLI ──
if __name__ == "__main__":
    if "--halt" in sys.argv:
        reason_idx = sys.argv.index("--halt") + 1
        reason = sys.argv[reason_idx] if reason_idx < len(sys.argv) and not sys.argv[reason_idx].startswith("--") else "Manual halt by operator"
        halt(reason)
    elif "--release" in sys.argv:
        release()
    elif "--status" in sys.argv:
        print(status())
    else:
        print(status())
        print("\nUsage: python3 guardrails/kill_switch.py [--halt [reason]] [--release] [--status]")
