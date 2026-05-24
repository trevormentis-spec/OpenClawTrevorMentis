#!/usr/bin/env python3
"""
AgentMail Reader — fetches recent messages and injects intel into news_raw.md.
Silent pipeline feeder. Mirrors gmail_reader.py behavior for AgentMail inbox.

Usage:
    python3 scripts/agentmail_reader.py --max 10 --save
"""

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW_NEWS_FILE = REPO_ROOT / "tasks" / "news_raw.md"

def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[agentmail-read {ts}] {msg}", file=sys.stderr, flush=True)

def get_api_key() -> str:
    key = os.environ.get("AGENTMAIL_API_KEY", "")
    if key:
        return key
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("AGENTMAIL_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""

def fetch_messages(api_key: str, max_msgs: int = 10) -> list[dict]:
    """Fetch recent messages from AgentMail inbox."""
    from agentmail import AgentMail
    client = AgentMail(api_key=api_key)
    try:
        inboxes = client.inboxes.list()
        trevor = inboxes.inboxes[0].inbox_id
        msgs = client.inboxes.messages.list(trevor, limit=max_msgs)
        results = []
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=6)
        for m in msgs.messages:
            created = m.created_at
            if hasattr(created, 'timestamp'):
                created_dt = dt.datetime.fromtimestamp(created.timestamp(), tz=dt.timezone.utc)
            elif isinstance(created, str):
                created_dt = dt.datetime.fromisoformat(created.replace('Z', '+00:00'))
            else:
                created_dt = created
            if created_dt < cutoff:
                continue
            # Skip outbound (sent by Trevor)
            from_addr = str(m.from_ or "")
            if "trevor" in from_addr.lower():
                continue
            results.append({
                "from": from_addr,
                "subject": m.subject or "(no subject)",
                "body": (m.preview or "")[:500],
                "created_at": str(m.created_at)[:19],
            })
        return results
    except Exception as e:
        log(f"Fetch failed: {e}")
        return []

def save_news_raw(messages: list[dict]) -> int:
    """Append intel items to tasks/news_raw.md."""
    if not messages:
        return 0

    now = dt.datetime.now(dt.timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    ts = now.strftime("%H:%M UTC")

    lines = []
    lines.append(f"\n## AgentMail Intel — {date_str} {ts}")
    lines.append("")

    for msg in messages:
        subject = msg.get("subject", "").strip()
        body = msg.get("body", "").strip()
        sender = msg.get("from", "unknown")
        lines.append(f"### {subject}")
        lines.append(f"**From:** {sender}  ")
        if body:
            # Extract key sentences
            clean = re.sub(r'<[^>]+>', '', body)
            clean = re.sub(r'\s+', ' ', clean).strip()
            lines.append(clean[:600])
        lines.append("")

    content = "\n".join(lines)
    RAW_NEWS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RAW_NEWS_FILE, "a") as f:
        f.write(content)

    return len(messages)

def main():
    parser = argparse.ArgumentParser(description="AgentMail Reader — fetch and inject intel")
    parser.add_argument("--max", type=int, default=10, help="Max messages to fetch")
    parser.add_argument("--save", action="store_true", help="Save to news_raw.md")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead")
    args = parser.parse_args()

    api_key = get_api_key()
    if not api_key:
        log("ERROR: AGENTMAIL_API_KEY not set")
        sys.exit(1)

    log(f"Fetching last {args.max} AgentMail messages...")
    messages = fetch_messages(api_key, args.max)
    log(f"Found {len(messages)} recent inbound messages")

    if args.stdout:
        for msg in messages:
            print(f"\n### {msg['subject']}")
            print(f"From: {msg['from']}")
            print(f"Date: {msg['created_at']}")
            print(msg['body'][:300])
    elif args.save:
        saved = save_news_raw(messages)
        log(f"Saved {saved} items to {RAW_NEWS_FILE}")
    else:
        log("No action specified. Use --save or --stdout.")

if __name__ == "__main__":
    main()
