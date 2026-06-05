#!/usr/bin/env python3
"""
Infrastructure Alert Monitor — Trevor

Checks all infrastructure thresholds (credits, disk, API health) and:
  1. Writes findings to a shared state file
  2. Outputs actionable alert lines for cron delivery to Roderick
  3. Supports quiet mode (only output on actual alerts)

Usage:
  python3 scripts/infra_alert.py                      # Full output
  python3 scripts/infra_alert.py --quiet               # Output only on alerts
  python3 scripts/infra_alert.py --alert-only          # JSON alert data
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

REPO = Path(__file__).resolve().parent.parent
ALERT_STATE = REPO / "tasks" / "infra-alert-state.json"
TRACKING_FILE = REPO / "brain" / "memory" / "semantic" / "deepseek-usage.json"

# ── Thresholds ──────────────────────────────────────────────────────
THRESHOLDS = {
    "deepseek_balance_warn": 5.0,
    "deepseek_balance_critical": 1.0,
    "disk_warn_pct": 80,
    "disk_critical_pct": 90,
    "openrouter_credits_warn": 0.50,
    "openrouter_credits_critical": 0.10,
}

# Alert cooldown: don't re-alert on same issue within N seconds
ALERT_COOLDOWN_SEC = 21600  # 6 hours


def load_alert_state() -> dict:
    if ALERT_STATE.exists():
        try:
            return json.loads(ALERT_STATE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_alerts": {}, "active_alerts": []}


def save_alert_state(state: dict):
    ALERT_STATE.parent.mkdir(parents=True, exist_ok=True)
    ALERT_STATE.write_text(json.dumps(state, indent=2))


def should_alert(alert_key: str, state: dict) -> bool:
    """Check cooldown: don't spam same alert within window."""
    last = state.get("last_alerts", {}).get(alert_key, 0)
    return (time.time() - last) > ALERT_COOLDOWN_SEC


def mark_alerted(alert_key: str, state: dict):
    state.setdefault("last_alerts", {})[alert_key] = time.time()


# ── Checks ──────────────────────────────────────────────────────────

def check_deepseek_balance() -> list[dict]:
    """Check DeepSeek account balance. Returns alert dicts."""
    alerts = []
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        return [{"severity": "warn", "key": "deepseek_auth", "msg": "DEEPSEEK_API_KEY not set"}]

    # Try live balance API
    try:
        req = Request("https://api.deepseek.com/user/balance",
                       headers={"Authorization": f"Bearer {api_key}"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            balance = data.get("balance_infos", [{}])[0].get("total_balance", None)
            if balance is None:
                balance = data.get("balance", None)
    except Exception:
        balance = None

    # Fallback: use cached snapshot
    if balance is None and TRACKING_FILE.exists():
        try:
            cached = json.loads(TRACKING_FILE.read_text())
            balance = cached.get("balance", {}).get("USD", None)
            if balance is None:
                balance = cached.get("balance", None)
        except Exception:
            pass

    if balance is not None:
        try:
            balance = float(balance)
        except (ValueError, TypeError):
            balance = None

    if balance is None:
        alerts.append({"severity": "warn", "key": "deepseek_balance_unknown",
                      "msg": "DeepSeek balance: unknown (API unreachable, using stale data)"})
    elif balance < THRESHOLDS["deepseek_balance_critical"]:
        alerts.append({"severity": "critical", "key": "deepseek_balance_critical",
                      "msg": f"🚨 DeepSeek balance critically low: ${balance:.2f} — top up NOW"})
    elif balance < THRESHOLDS["deepseek_balance_warn"]:
        alerts.append({"severity": "warn", "key": "deepseek_balance_warn",
                      "msg": f"⚠️ DeepSeek balance low: ${balance:.2f}"})
    else:
        alerts.append({"severity": "ok", "key": "deepseek_balance",
                      "msg": f"DeepSeek balance: ${balance:.2f} ✅"})

    return alerts


def check_openrouter_credits() -> list[dict]:
    """Check OpenRouter credit balance."""
    alerts = []
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return [{"severity": "ok", "key": "openrouter_disabled",
                "msg": "OpenRouter: no API key configured (disabled) ✅"}]

    try:
        req = Request("https://openrouter.ai/api/v1/auth/key",
                       headers={"Authorization": f"Bearer {api_key}"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            credits = data.get("data", {}).get("credits", None)
            limit = data.get("data", {}).get("limit", None)
    except Exception:
        return [{"severity": "warn", "key": "openrouter_api_error",
                "msg": "OpenRouter: API unreachable (credits unknown)"}]

    if credits is None:
        return [{"severity": "ok", "key": "openrouter_no_credit_data",
                "msg": "OpenRouter: no credit data available (key may be pay-as-you-go) ✅"}]

    try:
        credits = float(credits)
    except (ValueError, TypeError):
        return [{"severity": "ok", "key": "openrouter_credits", "msg": "OpenRouter: credits unknown"}]

    if limit:
        limit = float(limit)

    if credits < THRESHOLDS["openrouter_credits_critical"]:
        alerts.append({"severity": "critical", "key": "openrouter_credits_critical",
                      "msg": f"🚨 OpenRouter credits exhausted: ${credits:.2f} (limit ${limit:.2f}) — provider calls will FAIL"})
    elif credits < THRESHOLDS["openrouter_credits_warn"]:
        alerts.append({"severity": "warn", "key": "openrouter_credits_warn",
                      "msg": f"⚠️ OpenRouter credits low: ${credits:.2f} (limit ${limit:.2f})"})
    else:
        alerts.append({"severity": "ok", "key": "openrouter_credits",
                      "msg": f"OpenRouter: ${credits:.2f} remaining (limit ${limit:.2f}) ✅"})

    return alerts


def check_disk() -> list[dict]:
    """Check disk usage."""
    alerts = []
    try:
        result = subprocess.run(
            ["df", "/"], capture_output=True, text=True, timeout=5)
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 2:
            parts = lines[-1].split()
            # df output: fs total used avail use% mount
            total = parts[1] if len(parts) >= 5 else "?"
            used = parts[2] if len(parts) >= 5 else "?"
            pct_str = parts[4] if len(parts) >= 5 else "0%"
            pct = int(pct_str.replace("%", ""))
        else:
            return [{"severity": "warn", "key": "disk_check_failed",
                    "msg": "Disk: df command returned unexpected output"}]
    except Exception as e:
        return [{"severity": "warn", "key": "disk_check_failed",
                "msg": f"Disk: check failed ({e})"}]

    if pct >= THRESHOLDS["disk_critical_pct"]:
        alerts.append({"severity": "critical", "key": "disk_critical",
                      "msg": f"🚨 Disk CRITICAL: {pct}% used ({used}/{total})"})
    elif pct >= THRESHOLDS["disk_warn_pct"]:
        alerts.append({"severity": "warn", "key": "disk_warn",
                      "msg": f"⚠️ Disk usage high: {pct}% ({used}/{total})"})
    else:
        alerts.append({"severity": "ok", "key": "disk",
                      "msg": f"Disk: {pct}% used ({used}/{total}) ✅"})

    return alerts


def format_alert_line(alert: dict) -> str:
    """One-line alert for human reading."""
    return alert["msg"]


# ── Main ────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Infrastructure alert monitor")
    parser.add_argument("--quiet", action="store_true",
                       help="Only output alerts (no 'ok' lines)")
    args = parser.parse_args()

    state = load_alert_state()
    all_alerts = []
    all_alerts.extend(check_deepseek_balance())
    all_alerts.extend(check_openrouter_credits())
    all_alerts.extend(check_disk())

    active_alerts = []
    new_notifications = []

    for alert in all_alerts:
        if alert["severity"] == "ok":
            if not args.quiet:
                print(format_alert_line(alert))
            continue

        active_alerts.append(alert)

        # Check cooldown before notifying
        if should_alert(alert["key"], state):
            new_notifications.append(alert)
            mark_alerted(alert["key"], state)
            print(format_alert_line(alert))
        elif not args.quiet:
            print(f"{alert['msg']} (cooldown — not re-alerting)")

    # Update state
    state["active_alerts"] = active_alerts
    state["last_check"] = datetime.now(timezone.utc).isoformat()
    state["alert_count"] = len(active_alerts)
    state["new_alert_count"] = len(new_notifications)
    save_alert_state(state)

    # Exit code: 0 = no new alerts, 1 = new alerts fired
    if new_notifications:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
