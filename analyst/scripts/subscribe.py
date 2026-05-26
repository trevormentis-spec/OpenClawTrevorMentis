#!/usr/bin/env python3
"""
subscribe.py — I&W Subscription Manager.

Register, list, and deregister subscribers for specific narratives or signal types.

Usage:
    python3 analyst/scripts/subscribe.py add --email user@example.com --narratives iran_nuclear oil_price
    python3 analyst/scripts/subscribe.py add --webhook https://hooks.example.com/alerts --narratives all
    python3 analyst/scripts/subscribe.py list
    python3 analyst/scripts/subscribe.py remove <subscriber-id>
    python3 analyst/scripts/subscribe.py show <subscriber-id>
    python3 analyst/scripts/subscribe.py nuke                          # Clear all subscribers
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
import uuid

SUBSCRIPTIONS_FILE = pathlib.Path(__file__).resolve().parent.parent.parent / "tasks" / "alert-subscriptions.json"


def log(msg: str) -> None:
    print(f"[subscribe] {msg}", file=sys.stderr, flush=True)


def load_subs():
    if SUBSCRIPTIONS_FILE.exists():
        try:
            return json.loads(SUBSCRIPTIONS_FILE.read_text())
        except (json.JSONDecodeError,):
            pass
    return {
        "version": 1,
        "subscribers": [],
        "created": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def save_subs(subs: dict):
    subs["last_updated"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    SUBSCRIPTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SUBSCRIPTIONS_FILE.write_text(json.dumps(subs, indent=2))
    log(f"Saved {len(subs['subscribers'])} subscribers to {SUBSCRIPTIONS_FILE}")


def cmd_add(args):
    subs = load_subs()
    if not args.email and not args.webhook:
        log("ERROR: Must specify --email or --webhook")
        return 1

    subscriber = {
        "id": str(uuid.uuid4())[:8],
        "created": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "email": args.email or None,
        "webhook_url": args.webhook or None,
        "narratives": args.narratives or ["all"],
        "signal_types": args.signal_types or ["all"],
        "active": True,
        "notes": args.notes or "",
    }

    subs["subscribers"].append(subscriber)
    save_subs(subs)
    print(f"✅ Added subscriber {subscriber['id']}: {args.email or args.webhook}")
    print(f"   Narratives: {subscriber['narratives']}")
    print(f"   Signal types: {subscriber['signal_types']}")
    return 0


def cmd_remove(args):
    subs = load_subs()
    before = len(subs["subscribers"])
    subs["subscribers"] = [s for s in subs["subscribers"] if s["id"] != args.subscriber_id]
    after = len(subs["subscribers"])
    if before == after:
        log(f"No subscriber found with id '{args.subscriber_id}'")
        return 1
    save_subs(subs)
    print(f"✅ Removed subscriber {args.subscriber_id}")
    return 0


def cmd_show(args):
    subs = load_subs()
    for s in subs["subscribers"]:
        if s["id"] == args.subscriber_id:
            print(json.dumps(s, indent=2))
            return 0
    log(f"No subscriber found with id '{args.subscriber_id}'")
    return 1


def cmd_list(args):
    subs = load_subs()
    subscribers = subs.get("subscribers", [])
    if not subscribers:
        print("No subscribers registered.")
        return 0

    print(f"\nRegistered subscribers ({len(subscribers)}):")
    print(f"{'ID':<12} {'Contact':<40} {'Narratives':<24} {'Signal Types':<20} Status")
    print("-" * 100)
    for s in subscribers:
        contact = s.get("email") or s.get("webhook_url", "")[:40]
        narratives = ", ".join(s.get("narratives", ["all"]))[:24]
        sig_types = ", ".join(s.get("signal_types", ["all"]))[:20]
        status = "✅" if s.get("active", True) else "❌"
        print(f"{s['id']:<12} {contact:<40} {narratives:<24} {sig_types:<20} {status}")
    return 0


def cmd_nuke(args):
    confirm = input("⚠️  This will DELETE all subscribers. Are you sure? (yes/N): ")
    if confirm.lower() != "yes":
        print("Cancelled.")
        return 0
    subs = {
        "version": 1,
        "subscribers": [],
        "created": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    save_subs(subs)
    print("✅ All subscribers removed.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="I&W Subscription Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # add
    add_p = subparsers.add_parser("add", help="Register a new subscriber")
    add_p.add_argument("--email", help="Email address for alerts")
    add_p.add_argument("--webhook", help="Webhook URL for alerts")
    add_p.add_argument("--narratives", nargs="+", default=None,
                       help="Narrative IDs to subscribe to (default: all)")
    add_p.add_argument("--signal-types", nargs="+", default=None,
                       help="Signal types to subscribe to (default: all)")
    add_p.add_argument("--notes", default="", help="Free-text notes")

    # remove
    rm_p = subparsers.add_parser("remove", help="Remove a subscriber")
    rm_p.add_argument("subscriber_id", help="Subscriber ID to remove")

    # show
    show_p = subparsers.add_parser("show", help="Show subscriber details")
    show_p.add_argument("subscriber_id", help="Subscriber ID to show")

    # list
    subparsers.add_parser("list", help="List all subscribers")

    # nuke
    subparsers.add_parser("nuke", help="Remove all subscribers")

    args = parser.parse_args()

    if args.command == "add":
        return cmd_add(args)
    elif args.command == "remove":
        return cmd_remove(args)
    elif args.command == "show":
        return cmd_show(args)
    elif args.command == "list":
        return cmd_list(args)
    elif args.command == "nuke":
        return cmd_nuke(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
