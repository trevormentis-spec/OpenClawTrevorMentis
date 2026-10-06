#!/usr/bin/env python3
"""
OpenRouter balance watchdog.

Queries the OpenRouter account credit balance and, when it drops below a
threshold, emails Roderick a warning (via AgentMail) so a top-up can happen
before the model fallback chain loses its second route.

Safe to run repeatedly. Designed to be called from the existing hourly
AgentMail Intel Reader cron (no new cron job created).

Usage:
    python3 scripts/openrouter_balance_alert.py                 # check, warn if low
    python3 scripts/openrouter_balance_alert.py --threshold 25  # override threshold
    python3 scripts/openrouter_balance_alert.py --dry-run       # never send, just report
    python3 scripts/openrouter_balance_alert.py --force-send    # send even if above threshold
    python3 scripts/openrouter_balance_alert.py --test          # send a labelled test warning
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"
STATE_PATH = REPO_ROOT / "brain" / "working-memory" / "openrouter-balance.json"

DEFAULT_THRESHOLD_USD = 20.0
TO_EMAIL = "roderick.jones@gmail.com"
SENDER_INBOX = "trevor_mentis@agentmail.to"


def log(msg: str) -> None:
    print(f"[openrouter-balance] {msg}", flush=True)


def _load_env() -> None:
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v.strip())

def _env_value(name: str) -> str:
    """Read a key straight from .env — the file wins over any inherited/
    injected env var, which may hold a stale or placeholder value."""
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == name:
                    return v.strip().strip('"').strip("'")
    return os.environ.get(name, "").strip()



def get_balance(api_key: str) -> dict:
    """Return {remaining, total_credits, total_usage, raw}. Raises on failure."""
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/credits",
        headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode())
    d = data.get("data", data)
    total = float(d.get("total_credits", 0) or 0)
    used = float(d.get("total_usage", 0) or 0)
    return {
        "remaining": total - used,
        "total_credits": total,
        "total_usage": used,
        "currency": "USD",
        "raw": data,
    }


def write_state(balance: dict, threshold: float, warned: bool) -> None:
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps({
            "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "remaining": round(balance["remaining"], 4),
            "total_credits": balance["total_credits"],
            "total_usage": round(balance["total_usage"], 4),
            "currency": balance["currency"],
            "threshold": threshold,
            "warned": warned,
        }, indent=2))
    except Exception as e:
        log(f"state write failed (non-fatal): {e}")


def send_warning(balance: dict, threshold: float, test: bool = False) -> bool:
    api_key = _env_value("AGENTMAIL_API_KEY")
    if not api_key:
        log("ERROR: AGENTMAIL_API_KEY not set — cannot send warning")
        return False
    tag = "[TEST] " if test else ""
    rem = balance["remaining"]
    subj = f"{tag}⚠️ Low OpenRouter balance: ${rem:.2f} left"
    text = (
        f"OpenRouter credit balance is ${rem:.2f} "
        f"(warning threshold ${threshold:.2f}).\n\n"
        f"Credits ${balance['total_credits']:.2f}, used ${balance['total_usage']:.2f}.\n\n"
        "Top up at https://openrouter.ai/settings/credits so Trevor's model "
        "fallback chain keeps a second route (OpenRouter serves deepseek-v4-flash "
        "and gpt-4o-mini when the DeepSeek direct API is unavailable).\n\n"
        f"Checked: {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
    )
    html = (
        f"<p><strong>⚠️ Low OpenRouter balance</strong></p>"
        f"<p>Balance is <strong>${rem:.2f}</strong> "
        f"(threshold ${threshold:.2f}).</p>"
        f"<p>Top up at "
        f"<a href='https://openrouter.ai/settings/credits'>openrouter.ai/settings/credits</a> "
        f"to keep Trevor's fallback route funded.</p>"
    )
    try:
        from agentmail import AgentMail
        client = AgentMail(api_key=api_key)
        res = client.inboxes.messages.send(
            inbox_id=SENDER_INBOX, to=TO_EMAIL, subject=subj, text=text, html=html,
        )
        log(f"Warning email sent (id={getattr(res, 'id', 'unknown')})")
        return True
    except Exception as e:
        log(f"AgentMail send failed: {e}")
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description="OpenRouter balance watchdog")
    ap.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD_USD)
    ap.add_argument("--dry-run", action="store_true", help="never send")
    ap.add_argument("--force-send", action="store_true", help="send even if above threshold")
    ap.add_argument("--test", action="store_true", help="send a clearly-labelled test warning")
    args = ap.parse_args()

    _load_env()
    api_key = _env_value("OPENROUTER_API_KEY")
    if not api_key:
        log("ERROR: OPENROUTER_API_KEY not set")
        return 2

    try:
        bal = get_balance(api_key)
    except Exception as e:
        log(f"balance query failed: {e}")
        return 2

    low = bal["remaining"] < args.threshold
    log(f"balance ${bal['remaining']:.2f} {bal['currency']} "
        f"(threshold ${args.threshold:.2f}) -> {'LOW' if low else 'ok'}")

    warned = False
    if args.force_send or args.test or low:
        if args.dry_run:
            log("dry-run: would send warning email")
        else:
            warned = send_warning(bal, args.threshold, test=args.test)

    write_state(bal, args.threshold, warned)
    return 0


if __name__ == "__main__":
    sys.exit(main())
