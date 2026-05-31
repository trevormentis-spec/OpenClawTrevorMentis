#!/usr/bin/env python3
"""
Confirmation Supervisor — Checks pending orders and sends Telegram alert.

Runs as a cron job. If there are pending orders requiring confirmation,
outputs a message that gets delivered to Telegram via the cron delivery system.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from guardrails.confirmation import get_pending_orders, format_confirmation_message


def main():
    pending = get_pending_orders()

    if not pending:
        print("No pending orders requiring confirmation.")
        return

    print(f"📋 {len(pending)} pending order(s) requiring confirmation:\n")
    for order in pending:
        print(format_confirmation_message(order))
        print()


if __name__ == "__main__":
    main()
