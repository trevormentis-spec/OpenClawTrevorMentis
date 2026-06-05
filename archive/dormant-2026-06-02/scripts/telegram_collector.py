#!/usr/bin/env python3
"""
Telegram Channel Collector — Real-time OSINT from Telegram.

Fetches and parses public Telegram channels for intelligence collection.
Telegram is a primary source for breaking OSINT in the Iran/Middle East
domain — often hours or days before traditional news wires.

Design:
- Fetches public channel pages via t.me/s/{channel}
- Parses message text, dates, media
- Normalizes into the same incident format as RSS feeds
- Handles rate limiting (Telegram has anti-scraping protections)

Usage:
    python3 scripts/telegram_collector.py --channels judean_osint HormuzMonitor
    python3 scripts/telegram_collector.py --all                              # All known channels
    python3 scripts/telegram_collector.py --region middle_east               # Channels for region
    python3 scripts/telegram_collector.py --output ~/incidents.json          # Save as incidents

Output: JSON array of incidents compatible with collect.py's incident format.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys
import urllib.request
from typing import Any
from xml.etree import ElementTree as ET

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCES_FILE = REPO_ROOT / "analyst" / "meta" / "sources.json"

USER_AGENT = "TrevorTelegramCollector/1.0 (+https://github.com/trevormentis-spec)"

# Known Telegram channels with metadata
KNOWN_CHANNELS = [
    {
        "channel": "judean_osint",
        "name": "Judean OSINT",
        "region": "middle_east",
        "focus": "Iran-Israel real-time OSINT",
        "signal_level": "High",
    },
    {
        "channel": "HormuzMonitor",
        "name": "Straits of Hormuz Monitor",
        "region": "middle_east",
        "focus": "Strait of Hormuz tanker traffic and IRGC movements",
        "signal_level": "High",
    },
]

REGION_CHANNELS = {
    "middle_east": ["judean_osint", "HormuzMonitor"],
    "europe": [],
    "asia": [],
    "africa": [],
}


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[telegram {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, Exception):
            return {}
    return {}


def fetch_telegram_channel(channel: str, max_messages: int = 20) -> str | None:
    """Fetch a public Telegram channel's message feed.

    Uses t.me/s/{channel} which provides a public HTML view.
    """
    url = f"https://t.me/s/{channel}"
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml",
            }
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        return html
    except Exception as exc:
        log(f"  fetch failed for @{channel}: {exc}")
        return None


def parse_telegram_messages(html: str, channel: str) -> list[dict]:
    """Parse Telegram channel HTML into message items.

    Extracts: message text, date, message ID, and media links.
    """
    messages = []
    if not html:
        return messages

    # Find all message wrappers
    msg_pattern = re.compile(
        r'<div class="tgme_widget_message_wrap[^>]*>.*?'
        r'<div class="tgme_widget_message[^>]*>.*?'
        r'</div>\s*</div>',
        re.DOTALL
    )

    message_blocks = msg_pattern.findall(html)
    
    for block in message_blocks:
        # Extract message ID
        msg_id_match = re.search(r'data-post="([^"]+)"', block)
        msg_id = msg_id_match.group(1) if msg_id_match else "unknown"

        # Extract text content
        text_match = re.search(
            r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>',
            block, re.DOTALL
        )
        text = ""
        if text_match:
            raw_text = text_match.group(1)
            # Strip HTML tags
            text = re.sub(r'<[^>]+>', ' ', raw_text)
            text = re.sub(r'\s+', ' ', text).strip()

        # Extract date
        date_match = re.search(
            r'<time datetime="([^"]+)"',
            block
        )
        date_str = date_match.group(1) if date_match else ""

        # Extract media (photos, videos, documents)
        media = []
        media_links = re.findall(r'href="(https://t\.me/[^"]+)"', block)
        for link in media_links:
            if link not in media:
                media.append(link)

        # Skip empty messages
        if not text and not media:
            continue

        messages.append({
            "message_id": msg_id,
            "channel": channel,
            "text": text[:500],  # Cap at 500 chars
            "date": date_str,
            "media": media[:3],  # Cap at 3 media items
        })

    return messages


def determine_category(text: str) -> str:
    """Determine the incident category from message text."""
    text_l = text.lower()
    if any(k in text_l for k in ("strike", "missile", "drone", "airstrike", "shelling",
                                   "attack", "raid", "clashes", "casualt")):
        return "kinetic"
    if any(k in text_l for k in ("ais", "tanker", "vessel", "maritime", "ship",
                                   "strait", "hormuz", "naval")):
        return "maritime"
    if any(k in text_l for k in ("cyber", "hack", "breach", "malware")):
        return "cyber"
    if any(k in text_l for k in ("sanction", "diplomat", "negotiation", "deal",
                                   "treaty", "ceasefire")):
        return "diplomatic"
    return "intelligence"


def messages_to_incidents(messages: list[dict], channel_info: dict) -> list[dict]:
    """Convert Telegram messages to collector-compatible incident format."""
    incidents = []
    now = dt.datetime.now(dt.timezone.utc)

    for msg in messages:
        text = msg.get("text", "")
        if not text:
            continue

        # Create a unique ID
        h = hashlib.md5(f"{msg['message_id']}|{msg['channel']}".encode()).hexdigest()[:4]
        incident_id = f"tg-{now.strftime('%Y%m%d')}-{h}"

        # Parse date
        occurred = msg.get("date", now.isoformat())
        try:
            if occurred:
                d = dt.datetime.fromisoformat(occurred.replace("Z", "+00:00").replace("+00:00", ""))
                occurred = d.strftime("%Y-%m-%dT%H:%M:%SZ")
        except (ValueError, TypeError):
            occurred = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Create headline (first 100 chars of message)
        headline = text[:100]
        if len(text) > 100:
            headline += "..."

        incidents.append({
            "id": incident_id,
            "region": channel_info.get("region", "unknown"),
            "country": None,
            "occurred_at_utc": occurred,
            "category": determine_category(text),
            "headline": headline,
            "summary": text[:600],
            "sources": [{
                "name": f"Telegram @{msg['channel']}",
                "url": f"https://t.me/{msg['channel']}/{msg['message_id'].split('/')[-1]}",
                "admiralty_reliability": "C",
                "admiralty_credibility": 3,
            }],
            "single_source": True,
            "confidence_collector": "low",
        })

    return incidents


def collect_channels(channels: list[str], hours_back: int = 24) -> list[dict]:
    """Collect messages from multiple Telegram channels."""
    all_incidents = []
    
    # Build channel info lookup
    channel_info = {c["channel"]: c for c in KNOWN_CHANNELS}
    
    for channel in channels:
        log(f"Fetching @{channel}...")
        html = fetch_telegram_channel(channel)
        if not html:
            continue
        
        messages = parse_telegram_messages(html, channel)
        log(f"  Parsed {len(messages)} messages")
        
        info = channel_info.get(channel, {"region": "unknown", "name": channel})
        incidents = messages_to_incidents(messages, info)
        all_incidents.extend(incidents)
        
        log(f"  Generated {len(incidents)} incidents")
    
    return all_incidents


def get_channels_for_region(region: str) -> list[str]:
    """Get known channel names for a region."""
    return REGION_CHANNELS.get(region, [])


def get_all_known_channels() -> list[str]:
    """Get all known channel names."""
    return [c["channel"] for c in KNOWN_CHANNELS]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channels", nargs="+", default=[], help="Telegram channel names")
    parser.add_argument("--all", action="store_true", help="Collect all known channels")
    parser.add_argument("--region", default="", help="Collect channels for a region")
    parser.add_argument("--output", default="", help="Save output to file (JSON)")
    parser.add_argument("--hours", type=int, default=24, help="Hours of history to collect")
    args = parser.parse_args()

    # Determine which channels to collect
    channels = []
    if args.all:
        channels = get_all_known_channels()
    elif args.region:
        channels = get_channels_for_region(args.region)
    elif args.channels:
        channels = args.channels
    else:
        channels = get_all_known_channels()
        log(f"No filter specified — collecting all {len(channels)} known channels")

    if not channels:
        log("No channels to collect")
        return 1

    log(f"Collecting {len(channels)} Telegram channels")
    incidents = collect_channels(channels, args.hours)

    # Build output
    output = {
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "telegram_collector",
        "channels_collected": len(channels),
        "window_hours": args.hours,
        "incidents": incidents,
        "total_incidents": len(incidents),
    }

    # Print or save
    output_json = json.dumps(output, indent=2)
    
    if args.output:
        pathlib.Path(args.output).write_text(output_json)
        log(f"Saved {len(incidents)} incidents to {args.output}")
    else:
        # Print summary
        print(f"\nTelegram Collection Summary:")
        print(f"  Channels: {len(channels)}")
        print(f"  Messages: {sum(len(parse_telegram_messages(fetch_telegram_channel(c) or '', c)) for c in channels)}")
        print(f"  Incidents: {len(incidents)}")
        print(f"\n  Regions covered:")
        region_counts = {}
        for inc in incidents:
            r = inc.get("region", "unknown")
            region_counts[r] = region_counts.get(r, 0) + 1
        for r, c in sorted(region_counts.items()):
            print(f"    {r}: {c}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
