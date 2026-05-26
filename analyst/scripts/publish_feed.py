#!/usr/bin/env python3
"""
publish_feed.py — Publish KJ feed to subscribers.

Delivers the latest structured KJ feed to AgentMail subscribers
and maintains the exports/kj-feeds/ archive.

Called from runtime-health.sh cycle (every 15 min, after cognition).

Usage:
    python3 analyst/scripts/publish_feed.py                     # Publish latest feed
    python3 analyst/scripts/publish_feed.py --feed <path>       # Specific feed file
    python3 analyst/scripts/publish_feed.py --dry-run           # Don't actually send
    python3 analyst/scripts/publish_feed.py --list-subscribers  # Show registered subs
    python3 analyst/scripts/publish_feed.py --desk iran         # Desk-scoped publication
    python3 analyst/scripts/publish_feed.py --moltbook          # Post summary to Moltbook
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
DEFAULT_FEED = REPO / "exports" / "kj-feeds" / "latest.json"
SUBSCRIPTIONS_FILE = REPO / "tasks" / "alert-subscriptions.json"
ARCHIVE_DIR = REPO / "exports" / "kj-feeds"

# AgentMail API config
AGENTMAIL_INBOX = "trevor_mentis@agentmail.to"


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[publish_feed {ts}] {msg}", file=sys.stderr, flush=True)


def load_feed(path: pathlib.Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log(f"Cannot load feed from {path}: {e}")
        return None


def load_subscriptions(path: pathlib.Path) -> dict:
    """Load subscriber registry."""
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError,):
            log(f"Corrupt subscriptions file at {path}, resetting")
    return {
        "version": 1,
        "subscribers": [],
        "created": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def save_subscriptions(subs: dict, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    subs["last_updated"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path.write_text(json.dumps(subs, indent=2))


def send_via_agentmail(subject: str, body: str, dry_run: bool = False) -> bool:
    """Send email via AgentMail REST API."""
    api_key = os.environ.get("AGENTMAIL_API_KEY", "")
    if not api_key and not dry_run:
        log("No AGENTMAIL_API_KEY — cannot send")
        return False

    import urllib.request

    payload = json.dumps({
        "to": AGENTMAIL_INBOX,
        "subject": subject,
        "text": body,
    }).encode()

    if dry_run:
        log(f"[DRY RUN] Would send to {AGENTMAIL_INBOX}")
        log(f"  Subject: {subject}")
        log(f"  Body: {len(body)} chars")
        return True

    req = urllib.request.Request(
        "https://api.agentmail.to/v1/send",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        log(f"Sent to AgentMail: {result.get('message_id', 'ok')}")
        return True
    except urllib.error.HTTPError as e:
        log(f"AgentMail send failed: {e.code} — {e.read().decode(errors='replace')[:200]}")
        return False
    except Exception as e:
        log(f"AgentMail send error: {e}")
        return False


def format_feed_email(feed: dict) -> tuple[str, str]:
    """Format feed as a structured email."""
    cycle = feed.get("cycle", 0)
    ts = feed.get("timestamp", "?")
    n_count = len(feed.get("narratives", []))
    s_count = len(feed.get("source_trust", []))
    esc_count = len(feed.get("escalations", []))

    desk_id = feed.get("desk")
    desk_tag = f"|{desk_id.upper()}" if desk_id else ""
    subject = f"[Philby{desk_tag}] Cycle {cycle} — {n_count} narratives, {esc_count} escalations"

    lines = [
        f"KJ FEED — Cycle {cycle}",
        f"Timestamp: {ts}",
        f"Feed version: {feed.get('feed_version', 1)}",
        "",
        f"Narratives: {n_count}  |  Sources: {s_count}  |  Signals: {len(feed.get('weak_signals', []))}  |  Escalations: {esc_count}",
        "",
        "─── NARRATIVES ───",
    ]

    for n in feed.get("narratives", []):
        swing = ""
        for change in feed.get("delta", {}).get("changed_narratives", []):
            if change["id"] == n["id"]:
                swing = f" (Δ{change['swing']:+.0f}pt)"
                break

        lines.append(f"\n[{n['id']}] {n['kent_band']} ({n['confidence']}%){swing}")
        lines.append(f"  Trend: {n['trend']}  |  Evidence: {n['evidence_for']}f/{n['evidence_against']}a")
        if n.get('hours_to_resolution'):
            lines.append(f"  Resolution: {n['hours_to_resolution']}h  |  {n.get('resolution_date', '?')}")
        if n.get('reasoning'):
            lines.append(f"  Reasoning: {n['reasoning'][:200]}")

    lines.append("\n─── NEW THIS CYCLE ───")
    delta = feed.get("delta", {})
    if delta.get("new_narratives"):
        lines.append(f"  New narratives: {', '.join(delta['new_narratives'])}")
    if delta.get("changed_narratives"):
        lines.append(f"  Changed: {len(delta['changed_narratives'])} narratives")
    if delta.get("new_signals"):
        lines.append(f"  New signals: {', '.join(delta['new_signals'])}")
    if delta.get("new_escalations"):
        lines.append(f"  New escalations: {len(delta['new_escalations'])}")
    if not any(delta.values()):
        lines.append("  No changes this cycle")

    lines.append("\n─── SYSTEM ───")
    sys_info = feed.get("system", {})
    lines.append(f"  Cognition healthy: {sys_info.get('cognition_healthy', '?')}")
    lines.append(f"  Total cycles: {sys_info.get('total_cycles', 0)}")
    lines.append(f"  Total spent: ${sys_info.get('total_spent_usd', 0):.4f}")
    lines.append(f"  Disk: {sys_info.get('disk_usage_pct', 0)}% used")

    body = "\n".join(lines)
    return subject, body


def publish_to_moltbook(feed: dict) -> bool:
    """Optionally post the KJ feed summary to Moltbook."""
    api_key = os.environ.get("MOLTBOOK_API_KEY", "")
    if not api_key:
        return False

    import urllib.request

    cycle = feed.get("cycle", 0)
    n_count = len(feed.get("narratives", []))
    esc_count = len(feed.get("escalations", []))

    lines = [
        f"KJ Feed — Cycle {cycle} | {n_count} narratives | {esc_count} alerts",
        "",
    ]

    # Top narratives
    for n in feed.get("narratives", [])[:5]:
        swing = ""
        for change in feed.get("delta", {}).get("changed_narratives", []):
            if change["id"] == n["id"]:
                swing = f" [{change['swing']:+.0f}pt]"
                break
        lines.append(f"• [{n['id']}] {n['kent_band']} ({n['confidence']}%){swing}")

    # Escalations
    if esc_count:
        lines.append(f"\n⚠️ {esc_count} active escalations")

    lines.append(f"\n*Full structured JSON in exports/kj-feeds/latest.json*")

    content = "\n".join(lines)

    payload = json.dumps({
        "title": f"KJ Feed — Cycle {cycle}",
        "content": content,
        "submolt": "agents",
    }).encode()

    req = urllib.request.Request(
        "https://www.moltbook.com/api/v1/posts",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        log(f"Posted to Moltbook: {result.get('post', {}).get('id', '?')}")
        return True
    except urllib.error.HTTPError as e:
        log(f"Moltbook post failed: {e.code} — {e.read().decode(errors='replace')[:100]}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish KJ feed to subscribers")
    parser.add_argument("--feed", default=str(DEFAULT_FEED), help="Path to latest.json")
    parser.add_argument("--dry-run", action="store_true", help="No actual sends")
    parser.add_argument("--list-subscribers", action="store_true", help="List registered subs")
    parser.add_argument("--desk", default="", help="Desk-scoped publication (e.g. iran, ukraine)")
    parser.add_argument("--moltbook", action="store_true", help="Post summary to Moltbook")
    args = parser.parse_args()

    feed_path = pathlib.Path(args.feed)
    subs_path = SUBSCRIPTIONS_FILE

    # Desk-scoped: resolve to desk-specific feed path
    if args.desk:
        desk_feed = REPO / "exports" / "philby" / "feeds" / args.desk / "latest.json"
        if desk_feed.exists():
            feed_path = desk_feed
            log(f"Desk-scoped publication: {args.desk}")
        else:
            log(f"WARNING: No desk feed for '{args.desk}', falling back to master feed")

    # Load feed
    feed = load_feed(feed_path)
    if not feed:
        log("No feed available — run kj_feed.py first")
        return 1

    # Load subscriptions
    subs = load_subscriptions(subs_path)
    subscriber_list = subs.get("subscribers", [])

    # List subscribers mode
    if args.list_subscribers:
        if subscriber_list:
            print(f"\nRegistered subscribers ({len(subscriber_list)}):")
            for s in subscriber_list:
                print(f"  {s.get('email') or s.get('webhook_url'):40s} narratives={s.get('narratives', ['all'])}")
        else:
            print("No registered subscribers.")
        return 0

    # Format and send email
    subject, body = format_feed_email(feed)
    sent = send_via_agentmail(subject, body, dry_run=args.dry_run)

    # Post to Moltbook if requested
    if args.moltbook:
        publish_to_moltbook(feed)

    # Archive: copy latest.json to dated file if not already done by kj_feed.py
    archive_path = ARCHIVE_DIR / f"{dt.date.today().strftime('%Y-%m-%d')}.json"
    if not archive_path.exists() and not args.dry_run:
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        archive_path.write_text(json.dumps(feed, indent=2))
        log(f"Archived: {archive_path}")

    # Send to individual subscribers (webhook / email)
    if not args.dry_run:
        for sub in subscriber_list:
            email = sub.get("email")
            webhook = sub.get("webhook_url")
            narrative_filter = sub.get("narratives", ["all"])

            if webhook:
                _send_webhook(feed, webhook, narrative_filter)
            elif email:
                sub_subject, sub_body = format_feed_email(feed)
                send_via_agentmail(sub_subject, sub_body, dry_run=False)

    log(f"Published: cycle {feed['cycle']}" + (" [dry run]" if args.dry_run else ""))
    return 0


def _send_webhook(feed: dict, url: str, narrative_filter: list[str]) -> bool:
    """Push feed to a webhook URL."""
    import urllib.request

    # Optionally filter narratives
    if narrative_filter and "all" not in narrative_filter:
        filtered = feed.copy()
        filtered["narratives"] = [n for n in feed.get("narratives", []) if n["id"] in narrative_filter]
        payload = filtered
    else:
        payload = feed

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        urllib.request.urlopen(req, timeout=10)
        log(f"Webhook push to {url}: ok")
        return True
    except urllib.error.HTTPError as e:
        log(f"Webhook {url} failed: {e.code}")
        return False
    except Exception as e:
        log(f"Webhook {url} error: {e}")
        return False


if __name__ == "__main__":
    sys.exit(main())
