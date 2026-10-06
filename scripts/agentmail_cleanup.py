#!/usr/bin/env python3
"""
AgentMail Cleanup — monthly sweep of trevor_mentis@agentmail.to.

Keeps messages newer than RETENTION_DAYS (default 14), deletes everything older.
Runs as a cron job on the 1st of each month.

Usage:
    python3 scripts/agentmail_cleanup.py              # Dry run (count only)
    python3 scripts/agentmail_cleanup.py --execute    # Actually delete
    python3 scripts/agentmail_cleanup.py --days 30    # Custom retention
"""

import argparse
import datetime as dt
import json
import logging
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LOG_DIR = REPO_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

DEFAULT_RETENTION_DAYS = 14
API_BASE = "https://api.agentmail.to/v0"
INBOX_ID = "trevor_mentis@agentmail.to"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "agentmail-cleanup.log", mode="a"),
    ],
)
log = logging.getLogger("agentmail-cleanup")


def get_api_key() -> str:
    key = os.environ.get("AGENTMAIL_API_KEY", "")
    if not key:
        # Fallback: try .env
        env_path = REPO_ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("AGENTMAIL_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not key:
        log.error("AGENTMAIL_API_KEY not found in env or .env")
        sys.exit(1)
    return key


def api_request(url: str, method: str = "GET", api_key: str = "",
                retries: int = 3, data: dict | None = None) -> tuple[int, Any]:
    """Make an API request with retry on 429."""
    body_data = None
    if data is not None and method in ("POST", "PUT", "PATCH"):
        body_data = json.dumps(data).encode()

    req = urllib.request.Request(url, data=body_data, method=method)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("User-Agent", "trevor-cleanup/1.0")
    if body_data:
        req.add_header("Content-Type", "application/json")

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read()
                if resp.status == 204:
                    return 204, body
                return resp.status, json.loads(body)
        except urllib.error.HTTPError as e:
            err_body = e.read()
            if e.code == 429:
                wait = 5 * (attempt + 1)
                log.warning("Rate limited (429). Waiting %ds...", wait)
                time.sleep(wait)
                continue
            try:
                return e.code, json.loads(err_body)
            except (json.JSONDecodeError, TypeError):
                return e.code, err_body
        except Exception as e:
            log.warning("Request failed: %s", e)
            time.sleep(3)
            continue

    return 429, None


def _parse_timestamp(ts: Any) -> dt.datetime | None:
    """Parse an ISO timestamp string or return None."""
    if isinstance(ts, str):
        try:
            return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
    if isinstance(ts, dt.datetime):
        return ts
    return None


def delete_messages(api_key: str, dry_run: bool = True) -> int:
    """
    Paginate through the inbox, delete messages older than RETENTION_DAYS.
    Returns count of deleted (or would-delete) messages.
    """
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=RETENTION_DAYS)
    log.info("Retention: %d days (cutoff: %s)", RETENTION_DAYS, cutoff.date())

    page_url = f"{API_BASE}/inboxes/{INBOX_ID}/messages?limit=200"
    page_token: str | None = None
    total_deleted = 0
    total_kept = 0
    page_num = 0

    while True:
        url = page_url
        if page_token:
            url += f"&page_token={urllib.parse.quote(page_token)}"

        status, data = api_request(url, api_key=api_key)
        if status != 200 or not data:
            log.error("Failed to fetch page %d: HTTP %s", page_num + 1, status)
            break

        messages = data.get("messages", [])
        if not messages:
            break

        page_num += 1

        # Messages are returned newest-first. Use created_at from list response
        # directly — no need for individual fetch calls.
        first_created = _parse_timestamp(messages[0].get("created_at"))
        last_created = _parse_timestamp(messages[-1].get("created_at"))
        log.info(
            "Page %d: %d msgs (newest: %s, oldest: %s)",
            page_num, len(messages),
            first_created.date() if first_created else "?",
            last_created.date() if last_created else "?",
        )

        # Bulk optimize: if the newest message is already past cutoff,
        # nothing on this page needs deletion. Stop entirely.
        if first_created and first_created >= cutoff:
            total_kept += len(messages)
            if last_created and last_created >= cutoff:
                # Every message on this page is within retention — stop.
                log.info("  -> All within retention. Done scanning.")
                break
            # Partial page: check each message individually
            for msg in messages:
                created = _parse_timestamp(msg.get("created_at"))
                if created and created < cutoff:
                    if _delete_single(msg["message_id"], api_key, dry_run):
                        total_deleted += 1
                    time.sleep(0.15)
                else:
                    total_kept += 1
        else:
            # Entire page is past cutoff — bulk delete
            log.info("  -> Bulk delete entire page (%d msgs)", len(messages))
            for msg in messages:
                if _delete_single(msg["message_id"], api_key, dry_run):
                    total_deleted += 1
                time.sleep(0.15)

        page_token = data.get("next_page_token")
        if not page_token:
            break
        time.sleep(1)

    action = "Would delete" if dry_run else "Deleted"
    log.info(
        "%s %d messages. Kept: %d. Pages scanned: %d.",
        action, total_deleted, total_kept, page_num,
    )
    return total_deleted


def _delete_single(message_id: str, api_key: str, dry_run: bool) -> bool:
    """Delete a single message. Returns True on success."""
    if dry_run:
        return True

    encoded = urllib.parse.quote(message_id, safe="")
    url = f"{API_BASE}/inboxes/{INBOX_ID}/messages/{encoded}"
    status, _ = api_request(url, "DELETE", api_key=api_key)
    return status == 204


def main():
    parser = argparse.ArgumentParser(
        description="AgentMail inbox cleanup — delete messages older than N days."
    )
    parser.add_argument(
        "--execute", action="store_true",
        help="Actually delete. Without this flag, runs as dry-run (count only)."
    )
    parser.add_argument(
        "--days", type=int, default=DEFAULT_RETENTION_DAYS,
        help=f"Retention period in days (default: {DEFAULT_RETENTION_DAYS})"
    )
    args = parser.parse_args()

    global RETENTION_DAYS
    RETENTION_DAYS = args.days

    api_key = get_api_key()

    log.info("=" * 50)
    log.info("AgentMail Cleanup — %s", "EXECUTE" if args.execute else "DRY RUN")
    log.info("Inbox: %s", INBOX_ID)

    total = delete_messages(api_key, dry_run=not args.execute)

    if args.execute:
        log.info("Cleanup complete: %d messages deleted.", total)
    else:
        log.info(
            "Dry run: %d messages would be deleted. "
            "Re-run with --execute to proceed.", total
        )


if __name__ == "__main__":
    main()
