#!/usr/bin/env python3
"""
Gmail Reader — via Maton API Gateway.

Reads trevor.mentis@gmail.com for:
- OSINT newsletters (Cipher Brief, Foreign Policy, Defense One, etc.)
- Security alerts
- Any useful news or intelligence
- Forwarded brief content

Uses the Maton API gateway to access Gmail API.
Designed to be called from cron every 1-2 hours during working hours.

Usage:
    python3 scripts/gmail_reader.py                   # Fetch recent unseen emails
    python3 scripts/gmail_reader.py --since "2026-05-12"  # Fetch since date
    python3 scripts/gmail_reader.py --save            # Save to tasks/news_raw.md
    python3 scripts/gmail_reader.py --search "Iran"   # Search specific term
    python3 scripts/gmail_reader.py --all             # Fetch all recent (not just unseen)
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW_NEWS_FILE = REPO_ROOT / "tasks" / "news_raw.md"
GMAIL_BASE = "https://gateway.maton.ai/google-mail/gmail/v1/users/me"

# Labels to check (Gmail labels)
TARGET_LABELS = ["INBOX", "IMPORTANT"]

# Known OSINT/newsletter senders to highlight
KNOWN_INTEL_SOURCES = [
    "cipherbrief", "foreignpolicy", "defenseone", "breakingdefense",
    "warontherocks", "lawfare", "understandingwar", "criticalthreats",
    "isw", "acled", "soufan", "janes", "ihs", "jamestown",
    "reuters", "ap", "bbc", "ft", "wsj", "nytimes", "washingtonpost",
    "economist", "bloomberg", "politico", "axios",
]

# Newsletters that should be parsed for intelligence content
NEWSLETTER_SENDERS = [
    "cipherbrief", "foreignpolicy", "defenseone",
]

USER_AGENT = "TrevorGmailReader/1.0"


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[gmail {ts}] {msg}", file=sys.stderr, flush=True)


def get_api_key() -> str:
    key = os.environ.get("MATON_API_KEY", "")
    if not key:
        raise RuntimeError("MATON_API_KEY not set")
    return key


def gmail_get(path: str, params: dict | None = None) -> dict:
    """GET request to Gmail API via Maton gateway."""
    api_key = get_api_key()
    url = f"{GMAIL_BASE}/{path}"
    if params:
        qs = urllib.parse.urlencode(params)
        url = f"{url}?{qs}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("User-Agent", USER_AGENT)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")[:500]
        log(f"HTTP {exc.code} on GET {path}: {body}")
        return {}
    except Exception as exc:
        log(f"GET {path} failed: {exc}")
        return {}


def list_messages(query: str = "", max_results: int = 20) -> list[dict]:
    """List Gmail messages matching query."""
    params = {"maxResults": max_results}
    if query:
        params["q"] = query
    data = gmail_get("messages", params)
    return data.get("messages", [])


def get_message(msg_id: str) -> dict:
    """Get full message content including body."""
    data = gmail_get(f"messages/{msg_id}", {"format": "full"})
    return data


def decode_body(part: dict) -> str:
    """Decode message body from a MIME part."""
    body = part.get("body", {})
    data = body.get("data", "")
    if data:
        try:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        except Exception:
            return data
    return ""


def extract_text_from_parts(payload: dict) -> str:
    """Recursively extract text from MIME parts."""
    parts = payload.get("parts", [])
    mime_type = payload.get("mimeType", "")
    text = ""

    if mime_type == "text/plain":
        text = decode_body(payload)
    elif mime_type == "text/html":
        html = decode_body(payload)
        # Strip HTML tags
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
    elif parts:
        for part in parts:
            text += extract_text_from_parts(part)

    return text


def parse_headers(payload: dict) -> dict:
    """Extract email headers from payload."""
    headers = {}
    for h in payload.get("headers", []):
        name = h.get("name", "").lower()
        if name in ("from", "to", "subject", "date"):
            headers[name] = h.get("value", "")
    return headers


def classify_email(msg_data: dict) -> dict:
    """Classify an email: newsletter, alert, personal, etc."""
    headers = parse_headers(msg_data.get("payload", {}))
    sender = headers.get("from", "").lower()
    subject = headers.get("subject", "").lower()

    classification = {
        "type": "unknown",
        "is_intel": False,
        "source": headers.get("from", "Unknown"),
        "subject": headers.get("subject", "No subject"),
        "importance": "low",
    }

    # Check sender against known intel sources
    for src in KNOWN_INTEL_SOURCES:
        if src in sender:
            classification["is_intel"] = True
            classification["source"] = headers.get("from", src)
            break

    # Check for newsletter patterns
    for ns in NEWSLETTER_SENDERS:
        if ns in sender:
            classification["type"] = "newsletter"
            classification["importance"] = "medium"
            break

    # Check for direct/important patterns
    if "trevor" in sender:
        classification["type"] = "direct"
        classification["importance"] = "high"

    # Check subject for urgency signals
    urgent_kw = ["alert", "urgent", "breaking", "critical", "flash",
                  "immediate", "security", "warning"]
    if any(k in subject for k in urgent_kw):
        classification["type"] = "alert"
        classification["importance"] = "high"
        classification["is_intel"] = True

    return classification


def fetch_and_classify(query: str = "", max_results: int = 20) -> list[dict]:
    """Fetch emails, classify them, and return structured results."""
    messages = list_messages(query, max_results)
    results = []

    for msg_ref in messages:
        msg_id = msg_ref.get("id", "")
        if not msg_id:
            continue

        msg_data = get_message(msg_id)
        if not msg_data:
            continue

        classification = classify_email(msg_data)
        headers = parse_headers(msg_data.get("payload", {}))
        text = extract_text_from_parts(msg_data.get("payload", {}))

        results.append({
            "id": msg_id,
            "date": headers.get("date", ""),
            "from": headers.get("from", ""),
            "subject": headers.get("subject", ""),
            **classification,
            "text_preview": text[:500],
            "text_length": len(text),
        })

    return results


def save_news_raw(emails: list[dict]) -> int:
    """Save newsletter/intel content to tasks/news_raw.md for pipeline pickup."""
    intel_emails = [e for e in emails if e.get("is_intel")]
    if not intel_emails:
        log("No intel emails to save")
        return 0

    content = f"# Gmail Intel Digest — {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC\n\n"

    for email in intel_emails[:10]:  # Max 10 emails
        content += f"## {email.get('subject', 'No subject')}\n"
        content += f"**From:** {email.get('from', 'Unknown')}\n"
        content += f"**Date:** {email.get('date', 'Unknown')}\n"
        content += f"**Type:** {email.get('type', 'unknown')} | **Importance:** {email.get('importance', 'low')}\n\n"
        content += email.get("text_preview", "")[:1000]
        content += "\n\n---\n\n"

    RAW_NEWS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RAW_NEWS_FILE.write_text(content)
    log(f"Saved {len(intel_emails)} intel emails to {RAW_NEWS_FILE}")
    return len(intel_emails)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", default="", help="Date (YYYY-MM-DD) to fetch from")
    parser.add_argument("--search", default="", help="Gmail search query")
    parser.add_argument("--save", action="store_true", help="Save intel emails to news_raw.md")
    parser.add_argument("--all", action="store_true", help="Fetch all recent, not just unseen")
    parser.add_argument("--max", type=int, default=20, help="Max results")
    args = parser.parse_args()

    # Build search query
    query_parts = []

    if args.search:
        query_parts.append(args.search)
    elif args.since:
        query_parts.append(f"after:{args.since}")
    elif not args.all:
        query_parts.append("is:unread")

    if args.all:
        query_parts = [q for q in query_parts if "is:unread" not in q]

    query = " ".join(query_parts) if query_parts else "is:unread"

    log(f"Searching: '{query}'")
    emails = fetch_and_classify(query, args.max)
    log(f"Fetched {len(emails)} emails")

    if not emails:
        log("No emails found matching query")
        return 0

    # Print summary
    intel_count = sum(1 for e in emails if e.get("is_intel"))
    high_importance = sum(1 for e in emails if e.get("importance") == "high")
    newsletters = sum(1 for e in emails if e.get("type") == "newsletter")

    print(f"\nGmail Reader — {len(emails)} emails fetched")
    print(f"  Intel sources: {intel_count}")
    print(f"  High importance: {high_importance}")
    print(f"  Newsletters: {newsletters}")
    print()

    for email in emails[:15]:
        imp_mark = "🔴" if email["importance"] == "high" else "🟡" if email["importance"] == "medium" else "⚪"
        intel_mark = "📡" if email.get("is_intel") else "  "
        print(f"  {imp_mark}{intel_mark} [{email['type']}] {email['subject'][:80]}")
        print(f"     {email['from'][:60]}")
        if email.get("text_preview"):
            preview = email["text_preview"][:120].replace("\n", " ")
            print(f"     {preview}...")
        print()

    # Save if requested
    if args.save:
        saved = save_news_raw(emails)
        log(f"Saved {saved} intel emails to pipeline")

    # Mark as read (successfully processed)
    log("Done — unread emails remain unread for next check")

    return 0


if __name__ == "__main__":
    sys.exit(main())
