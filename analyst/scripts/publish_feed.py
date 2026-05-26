#!/usr/bin/env python3
"""
KJ Feed Publisher — sends structured KJ feed to subscribers.

Delivery:
  1. Write feed to exports/kj-feeds/
  2. Send digest to AgentMail (or configured subscribers)
  3. Optional webhook POST for programmatic subscribers

Usage:
  python3 publish_feed.py                          # Generate + publish
  python3 publish_feed.py --feed /path/to/feed.json  # Publish existing feed
  python3 publish_feed.py --dry-run                  # Preview without sending
"""

import sys
import os
import json
import logging
import argparse
import datetime
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger("kj-publish")
logger.setLevel(logging.WARNING)

WORKSPACE = Path(__file__).parent.parent.parent
FEED_SCRIPT = WORKSPACE / "analyst" / "scripts" / "kj_feed.py"
EXPORT_DIR = WORKSPACE / "exports" / "kj-feeds"
SUBSCRIBER_REGISTRY = WORKSPACE / "tasks" / "alert-subscriptions.json"


def load_subscribers() -> list:
    """Load subscriber configuration."""
    if not SUBSCRIBER_REGISTRY.exists():
        # Default: AgentMail
        return [{"channel": "agentmail", "address": os.environ.get("AGENTMAIL_TO", "trevor_mentis@agentmail.to")}]
    try:
        with open(SUBSCRIBER_REGISTRY) as f:
            return json.load(f)
    except Exception:
        return []


def generate_feed(desk: Optional[str] = None, validate: bool = False) -> Optional[dict]:
    """Generate feed using kj_feed.py."""
    result = subprocess.run(
        [sys.executable, str(FEED_SCRIPT), "--stdout"]
        + (["--desk", desk] if desk else [])
        + (["--validate"] if validate else []),
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        logger.error(f"Feed generation failed: {result.stderr}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        logger.error(f"Feed parse failed: {e}")
        return None


def build_digest(feed: dict) -> str:
    """Build a human-readable digest from the KJ feed for email delivery."""
    ts = feed.get("timestamp", "?")
    cycle = feed.get("cycle", "?")
    narratives = feed.get("narratives", [])
    delta = feed.get("delta", {})
    changed = delta.get("changed_narratives", [])
    new_narr = delta.get("new_narratives", [])
    new_escs = delta.get("new_escalations", [])
    system = feed.get("system", {})
    signals = feed.get("weak_signals", [])
    escs = feed.get("escalations", [])

    lines = []
    lines.append(f"TREVOR KJ FEED — Cycle {cycle}")
    lines.append(f"Timestamp: {ts}")
    lines.append(f"System: cognition={system.get('cognition_healthy','?')} | disk={system.get('disk_usage_pct','?')}% | spent=${system.get('total_spent_usd',0):.4f}")
    lines.append("")

    # Changes this cycle
    if changed or new_narr or new_escs:
        lines.append("── Changes this cycle ──")
        for c in changed:
            arrow = "↑" if c["swing"] > 0 else "↓"
            lines.append(f"  {arrow} {c['id']}: {c['previous_confidence']}% → {c['new_confidence']}% ({c['swing']:+d}pt)")
        for n in new_narr:
            lines.append(f"  ✦ New: {n}")
        for e in new_escs:
            lines.append(f"  ⚠ Escalation: {e}")
        lines.append("")

    # Active narratives
    lines.append(f"── Active Narratives ({len(narratives)}) ──")
    for n in narratives:
        band = n.get("kent_band", "?").replace("_", " ")
        lines.append(f"  {n['confidence']:>2}% ({band:12s}) {n['trend']:8s} | {n['id']}")
        if n.get("hours_to_resolution") is not None:
            lines.append(f"      resolves in {n['hours_to_resolution']:.0f}h")
        reasons = n.get("reasoning", "")
        if reasons:
            lines.append(f"      {reasons[:120]}")
    lines.append("")

    # Pending escalations
    pending = [e for e in escs if not e.get("resolved")]
    if pending:
        lines.append(f"── Pending Escalations ({len(pending)}) ──")
        for e in pending:
            lines.append(f"  {e['level'].upper()}: {e['narrative']} — {e['reason'][:80]}")
        lines.append("")

    # Weak signals
    if signals:
        strong = [s for s in signals if s.get("strength", 0) > 0.15]
        if strong:
            lines.append(f"── Weak Signals ({len(strong)}) ──")
            for s in strong[:5]:
                lines.append(f"  {s['strength']:.0%} {s['signal'][:80]}")
            lines.append("")

    # Source trust
    trust = feed.get("source_trust", [])
    lines.append(f"── Source Trust ({len(trust)} tracked) ──")
    for s in trust[:5]:
        lines.append(f"  {s['source_id']:30s} {s['admiralty']:4s} trust={s['track_record']:.0%}")
    lines.append("")

    return "\n".join(lines)


def send_agentmail(subject: str, body: str, to: str) -> bool:
    """Send via AgentMail API."""
    api_key = os.environ.get("AGENTMAIL_API_KEY")
    if not api_key:
        logger.warning("No AGENTMAIL_API_KEY set")
        return False

    import requests
    try:
        resp = requests.post(
            "https://agentmail.to/api/v1/send",
            json={"to": to, "subject": subject, "text": body},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        if resp.status_code == 200:
            logger.info(f"AgentMail sent to {to}: {subject}")
            return True
        else:
            logger.warning(f"AgentMail error {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        logger.warning(f"AgentMail send failed: {e}")
        return False


def send_webhook(feed: dict, url: str) -> bool:
    """Send feed JSON to a webhook subscriber."""
    import requests
    try:
        resp = requests.post(url, json=feed, timeout=15)
        logger.info(f"Webhook sent to {url}: {resp.status_code}")
        return resp.status_code < 500
    except Exception as e:
        logger.warning(f"Webhook failed: {e}")
        return False


def publish(feed: Optional[dict] = None, desk: Optional[str] = None,
            dry_run: bool = False, validate: bool = False) -> bool:
    """Generate (if needed) and publish the KJ feed."""
    if feed is None:
        feed = generate_feed(desk=desk, validate=validate)
    if feed is None:
        return False

    # Write to disk
    result = subprocess.run(
        [sys.executable, str(FEED_SCRIPT)]
        + (["--desk", desk] if desk else [])
        + (["--validate"] if validate else []),
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        logger.warning(f"Feed file write failed: {result.stderr}")

    # Build digest
    digest = build_digest(feed)
    ts = feed.get("timestamp", "?")[:19]
    cycle = feed.get("cycle", "?")

    subscribers = load_subscribers()
    sent = 0

    for sub in subscribers:
        channel = sub.get("channel", "agentmail")
        address = sub.get("address", "")

        if not address:
            continue

        if dry_run:
            print(f"[DRY RUN] Would send to {channel}:{address}")
            continue

        if channel == "agentmail":
            ok = send_agentmail(
                f"[KJ Feed] Cycle {cycle} — {feed.get('narratives', [])[0].get('id', 'intel')[:40] if feed.get('narratives') else 'no narratives'}",
                digest,
                address,
            )
            if ok:
                sent += 1

        elif channel == "webhook":
            ok = send_webhook(feed, address)
            if ok:
                sent += 1

    if not dry_run:
        logger.info(f"Published to {sent}/{len(subscribers)} subscribers")
    return True


def main():
    parser = argparse.ArgumentParser(description="KJ Feed Publisher")
    parser.add_argument("--desk", type=str, help="Topic desk filter")
    parser.add_argument("--feed", type=str, help="Path to existing feed JSON")
    parser.add_argument("--dry-run", action="store_true", help="Preview without sending")
    parser.add_argument("--validate", action="store_true", help="Validate against schema")
    parser.add_argument("--verbose", "-v", action="store_true", help="Debug logging")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.INFO)

    if args.feed:
        with open(args.feed) as f:
            feed = json.load(f)
    else:
        feed = None

    ok = publish(feed=feed, desk=args.desk, dry_run=args.dry_run, validate=args.validate)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
