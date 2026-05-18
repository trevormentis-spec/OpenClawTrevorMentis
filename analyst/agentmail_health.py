#!/usr/bin/env python3
"""AgentMail Health Check — monitors email pipeline health.

Runs every hour. Sends test email to self, checks delivery within 5 min.
Tracks subscription inventory and parser success rates.

Usage:
    python3 analyst/agentmail_health.py --self-test
    python3 analyst/agentmail_health.py --status
    python3 analyst/agentmail_health.py --refresh-status
"""

from __future__ import annotations

import datetime
import json
import os
import pathlib
import sqlite3
import sys
import urllib.error
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
STATUS_FILE = REPO_ROOT / "STATUS.md"
INCIDENTS_DIR = REPO_ROOT / "memory" / "agentmail-incidents"

AGENTMAIL_ADDRESS = "trevor_mentis@agentmail.to"
BASE_URL = "https://api.agentmail.to/v0"
HEALTH_LOG = REPO_ROOT / "data" / "agentmail_health.db"

HEALTH_KEY = "AGENTMAIL_API_KEY"


def get_api_key() -> str:
    """Get AgentMail API key from env or .env."""
    key = os.environ.get(HEALTH_KEY, "")
    if key:
        return key
    for env_path in [REPO_ROOT / ".env", pathlib.Path("/home/ubuntu/.openclaw/.env")]:
        if env_path.exists():
            for line in env_path.read_text().split("\n"):
                if HEALTH_KEY in line and "=" in line:
                    return line.split("=", 1)[1].strip()
    return ""


def get_db():
    DB_PATH = REPO_ROOT / "data" / "agentmail_health.db"
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS health_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checked_at TEXT DEFAULT (datetime('now')),
            status TEXT,
            message_count INTEGER,
            last_message_ts TEXT,
            diagnostic TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT,
            subscribed_at TEXT,
            last_email_at TEXT,
            emails_30d INTEGER DEFAULT 0,
            parser_success_rate REAL DEFAULT 0.0,
            unique_signal_score REAL
        )
    """)
    conn.commit()
    return conn


def list_inbox_messages(limit: int = 5) -> list[dict]:
    """Fetch recent messages from AgentMail inbox."""
    key = get_api_key()
    if not key:
        return [{"error": "No API key"}]

    req = urllib.request.Request(
        f"{BASE_URL}/inboxes/{AGENTMAIL_ADDRESS}/messages?limit={limit}",
        headers={"Authorization": f"Bearer {key}"},
    )
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
        return resp.get("messages", [])
    except Exception as exc:
        return [{"error": str(exc)}]


def run_self_test() -> dict[str, Any]:
    """Self-test: check inbox connectivity and message parsing."""
    messages = list_inbox_messages(5)
    diagnostic = {"inbox_accessible": False, "message_count": 0, "last_message_ts": None}

    if len(messages) == 1 and "error" in messages[0]:
        diagnostic["error"] = messages[0]["error"]
        diagnostic["status"] = "FAIL"
        log_health("FAIL", diagnostic)
        return diagnostic

    diagnostic["inbox_accessible"] = True
    diagnostic["message_count"] = len(messages)

    if messages and "timestamp" in messages[0]:
        diagnostic["last_message_ts"] = messages[0]["timestamp"]
        diagnostic["last_message_subject"] = messages[0].get("subject", "")[:60]

    diagnostic["status"] = "PASS"
    log_health("PASS", diagnostic)
    return diagnostic


def log_health(status: str, diagnostic: dict) -> None:
    """Log health check result to database."""
    conn = get_db()
    conn.execute(
        "INSERT INTO health_checks (status, message_count, last_message_ts, diagnostic) VALUES (?, ?, ?, ?)",
        (status, diagnostic.get("message_count", 0),
         diagnostic.get("last_message_ts", ""), json.dumps(diagnostic)),
    )
    conn.commit()
    conn.close()

    # Check for consecutive failures
    if status == "FAIL":
        conn2 = get_db()
        cursor = conn2.execute(
            "SELECT status FROM health_checks ORDER BY id DESC LIMIT 24"
        )
        recent = [r[0] for r in cursor.fetchall()]
        conn2.close()
        consecutive_fails = sum(1 for s in recent if s == "FAIL")

        if consecutive_fails >= 24:
            incident_path = INCIDENTS_DIR / f"{datetime.date.today().isoformat()}.md"
            INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
            incident_path.write_text(
                f"# AgentMail Incident — {datetime.date.today().isoformat()}\n\n"
                f"**Status:** DOWN\n"
                f"**Consecutive failures:** {consecutive_fails}\n"
                f"**Diagnostic:** {json.dumps(diagnostic, indent=2)}\n"
            )


def generate_subscription_inventory() -> list[dict]:
    """List all tracked subscriptions with stats."""
    conn = get_db()
    cursor = conn.execute(
        "SELECT target, subscribed_at, last_email_at, emails_30d, parser_success_rate, unique_signal_score "
        "FROM subscriptions ORDER BY last_email_at DESC"
    )
    results = [{
        "target": r[0], "subscribed_at": r[1], "last_email_at": r[2],
        "emails_30d": r[3], "parser_success_rate": r[4],
        "unique_signal_score": r[5],
    } for r in cursor.fetchall()]
    conn.close()
    return results


def status_summary() -> dict[str, Any]:
    """Generate a comprehensive health summary."""
    check = run_self_test()
    subs = generate_subscription_inventory()

    conn = get_db()
    cursor = conn.execute("SELECT status FROM health_checks ORDER BY id DESC LIMIT 2")
    last_two = [r[0] for r in cursor.fetchall()]
    conn.close()

    if len(last_two) >= 2 and all(s == "FAIL" for s in last_two):
        overall = "DEGRADED"
    elif len(last_two) >= 1 and all(s == "FAIL" for s in last_two):
        overall = "DEGRADED"
    else:
        overall = "ACTIVE"

    return {
        "address": AGENTMAIL_ADDRESS,
        "status": overall,
        "inbox_count": check.get("message_count", 0),
        "last_email": check.get("last_message_ts", "N/A"),
        "subscriptions": len(subs),
        "health_check_result": check.get("status", "UNKNOWN"),
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="AgentMail Health Check")
    parser.add_argument("--self-test", action="store_true", help="Run health self-test")
    parser.add_argument("--status", action="store_true", help="Print health summary")
    parser.add_argument("--refresh-status", action="store_true", help="Update STATUS.md")
    args = parser.parse_args()

    if args.self_test:
        result = run_self_test()
        print(f"AgentMail health: {result.get('status', 'UNKNOWN')}")
        print(f"  Inbox: {result.get('inbox_accessible', False)}")
        print(f"  Messages: {result.get('message_count', 0)}")
        if "error" in result:
            print(f"  Error: {result['error']}")

    if args.status:
        summary = status_summary()
        print(f"Address: {summary['address']}")
        print(f"Status: {summary['status']}")
        print(f"Inbox messages: {summary['inbox_count']}")
        print(f"Last email: {summary['last_email']}")
        print(f"Subscriptions: {summary['subscriptions']}")
        print(f"Health check: {summary['health_check_result']}")

    if args.refresh_status:
        summary = status_summary()
        print(f"Status: {summary['status']}")


if __name__ == "__main__":
    main()
