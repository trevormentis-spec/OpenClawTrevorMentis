#!/usr/bin/env python3
"""AgentMail Integration — newsletter subscription and monitoring.

Subscribes to intelligence newsletters via AgentMail API, receives
incoming content, extracts articles, routes to OSINT pipeline.

Usage:
    python3 scripts/agentmail_subscribe.py --list config/newsletters.yaml
    python3 scripts/agentmail_subscribe.py --subscribe "Insight Crime Mexico"
    python3 scripts/agentmail_subscribe.py --check-inbox --max 10
"""

from __future__ import annotations

import argparse
import email
import email.policy
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
AGENTMAIL_ADDRESS = "trevor_mentis@agentmail.to"


def load_newsletter_list() -> list[dict[str, Any]]:
    """Load newsletter targets from config/newsletters.yaml."""
    config_path = REPO_ROOT / "analyst" / "config" / "newsletters.yaml"
    if config_path.exists():
        try:
            import yaml
            data = yaml.safe_load(config_path.read_text())
            return data.get("newsletters", [])
        except Exception:
            pass
    return []


def get_agentmail_key() -> str:
    """Get AgentMail API key."""
    for env_var in ["AGENTMAIL_API_KEY", "AGENTMAIL_TOKEN"]:
        key = os.environ.get(env_var, "")
        if key:
            return key
    # Fallback: read from .env
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().split("\n"):
            line = line.strip()
            if "AGENTMAIL" in line and "=" in line:
                return line.split("=", 1)[1].strip()
    return ""


def send_email(to: str, subject: str, body: str) -> dict[str, Any]:
    """Send email via AgentMail API."""
    key = get_agentmail_key()
    if not key:
        return {"status": "error", "error": "No AgentMail API key"}

    payload = {
        "from": AGENTMAIL_ADDRESS,
        "to": to,
        "subject": subject,
        "text_body": body,
    }

    req = urllib.request.Request(
        "https://api.agentmail.to/v0/inboxes/trevor_mentis@agentmail.to/messages",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return {"status": "sent", "message_id": result.get("id"), "to": to, "subject": subject}
    except urllib.error.HTTPError as e:
        return {"status": "error", "error": f"HTTP {e.code}: {e.read()[:200]}", "to": to}


def check_inbox(max_messages: int = 10) -> list[dict[str, Any]]:
    """Check AgentMail inbox for incoming newsletters."""
    key = get_agentmail_key()
    if not key:
        return [{"status": "error", "error": "No AgentMail API key"}]

    req = urllib.request.Request(
        f"https://api.agentmail.to/v0/inboxes/trevor_mentis@agentmail.to/messages?limit={max_messages}",
        headers={"Authorization": f"Bearer {key}"},
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            messages = json.loads(resp.read())
            results = []
            for msg in messages.get("messages", messages if isinstance(messages, list) else []):
                results.append({
                    "id": msg.get("id"),
                    "from": msg.get("from", {}).get("email") if isinstance(msg.get("from"), dict) else msg.get("from"),
                    "subject": msg.get("subject", ""),
                    "timestamp": msg.get("created_at", msg.get("timestamp", "")),
                    "body_preview": msg.get("text_body", msg.get("body", ""))[:200],
                })
            return results
    except urllib.error.HTTPError as e:
        return [{"status": "error", "error": f"HTTP {e.code}"}]


def subscribe_newsletter(name: str, email_target: str) -> dict[str, Any]:
    """Subscribe to a newsletter by sending subscription request."""
    body = f"""Hi,

Please subscribe trevor_mentis@agentmail.to to the {name} newsletter.

This is an automated subscription request via AgentMail.

Best,
Open Claw Mexico Desk
"""
    return send_email(email_target, f"Subscribe: {name}", body)


def main():
    parser = argparse.ArgumentParser(description="AgentMail newsletter integration")
    parser.add_argument("--list", action="store_true", help="List configured newsletter targets")
    parser.add_argument("--subscribe", help="Subscribe to a specific newsletter by name")
    parser.add_argument("--subscribe-all", action="store_true", help="Subscribe to all unsubscribed newsletters")
    parser.add_argument("--check-inbox", action="store_true", help="Check for incoming newsletters")
    parser.add_argument("--max", type=int, default=10, help="Max messages to check")
    args = parser.parse_args()

    newsletters = load_newsletter_list()

    if args.list:
        print(f"{'Name':30s} {'Email':35s} {'Priority':10s} {'Status':10s}")
        print("-" * 85)
        for n in newsletters:
            print(f"{n.get('name','?'):30s} {n.get('email','?'):35s} {n.get('priority','?'):10s} {n.get('status','unsubscribed'):10s}")

    elif args.subscribe:
        target = [n for n in newsletters if n.get("name", "").lower() == args.subscribe.lower()]
        if not target:
            print(f"Newsletter '{args.subscribe}' not found in config.")
            return
        n = target[0]
        result = subscribe_newsletter(n["name"], n.get("email", ""))
        print(f"Subscribe: {n['name']} → {result}")

    elif args.subscribe_all:
        results = []
        for n in newsletters:
            if n.get("status") != "subscribed":
                r = subscribe_newsletter(n["name"], n.get("email", ""))
                results.append(r)
                print(f"  {'✅' if r['status']=='sent' else '❌'} {n['name']}")
        print(f"\n{sum(1 for r in results if r['status']=='sent')}/{len(results)} subscribed")

    elif args.check_inbox:
        messages = check_inbox(args.max)
        print(f"Messages in inbox:")
        for m in messages:
            print(f"  [{m.get('from','?')}] {m.get('subject','?')[:60]}")
            if m.get("body_preview"):
                print(f"    {m['body_preview'][:80]}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
