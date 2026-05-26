#!/usr/bin/env python3
"""
alert_engine.py — I&W Trigger Engine (Phase 2, Product 3).

Reads the escalation_queue from cognition_state.json and:
  1. Checks against the previous cycle's escalation queue (dedup)
  2. Formats I&W alerts with narrative context
  3. Pushes to subscribers via AgentMail + webhooks
  4. Archives sent alerts to prevent 24h re-send

Called from runtime-health.sh cycle (every 15 min, after cognition).

Usage:
    python3 analyst/scripts/alert_engine.py                          # Process all pending alerts
    python3 analyst/scripts/alert_engine.py --state <path>           # Custom state path
    python3 analyst/scripts/alert_engine.py --dry-run                # No actual sends
    python3 analyst/scripts/alert_engine.py --check-only             # Check for alerts, no send
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
DEFAULT_STATE = REPO / "skills" / "continuous-cognition" / "state" / "cognition_state.json"
SUBSCRIPTIONS_FILE = REPO / "tasks" / "alert-subscriptions.json"
ALERT_LOG = REPO / "exports" / "alerts" / "sent-alerts.jsonl"
DEDUP_WINDOW_HOURS = 24
AGENTMAIL_INBOX = "trevor_mentis@agentmail.to"

# Confidence swing thresholds that trigger alerts
SWING_ALERT_THRESHOLD = 10   # >=10pt swing -> send I&W
CRITICAL_SWING_THRESHOLD = 20  # >=20pt swing -> escalate to Flash level


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[alert_engine {ts}] {msg}", file=sys.stderr, flush=True)


def load_state(path: pathlib.Path) -> dict | None:
    try:
        raw = json.loads(path.read_text())
        return raw
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log(f"Cannot load state: {e}")
        return None


def load_previous_state(path: pathlib.Path) -> dict | None:
    """Load the previous cycle's state (from last backup)."""
    backup = path.with_suffix(".prev.json")
    if backup.exists():
        try:
            return json.loads(backup.read_text())
        except (json.JSONDecodeError,):
            pass
    return None


def save_state_backup(state: dict, path: pathlib.Path) -> None:
    """Save the current state as the reference for the next cycle."""
    backup = path.with_suffix(".prev.json")
    try:
        backup.write_text(json.dumps(state, separators=(",", ":")))
    except Exception as e:
        log(f"Cannot write state backup: {e}")


def load_subscriptions(path: pathlib.Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError,):
            pass
    return {"subscribers": []}


def load_sent_alerts(path: pathlib.Path) -> list[dict]:
    """Load alert dedup log."""
    alerts = []
    if path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        for line in path.read_text().splitlines():
            try:
                alerts.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                pass
    return alerts


def is_deduplicated(alert: dict, sent_alerts: list[dict]) -> bool:
    """Check if an identical alert was sent within the dedup window."""
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=DEDUP_WINDOW_HOURS)
    cutoff_ts = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")

    for sent in sent_alerts:
        if (sent.get("narrative_id") == alert["narrative_id"]
                and sent.get("alert_type") == alert["alert_type"]
                and sent.get("swing_points") == alert.get("swing_points")
                and sent.get("timestamp", "") > cutoff_ts):
            return True
    return False


def log_sent_alert(alert: dict, path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(alert, separators=(",", ":")) + "\n")


def detect_swing_alerts(current: dict, previous: dict) -> list[dict]:
    """Detect confidence swing alerts between state snapshots.
    
    Suppresses alerts for newly seeded narratives (cycle_created == current cycle)
    to avoid false positives from desk seedling.
    """
    alerts = []
    cur_narr = current.get("active_narratives", {})
    prev_narr = previous.get("active_narratives", {}) if previous else {}
    current_cycle = current.get("cycle", 0)

    for nid, cdata in cur_narr.items():
        cur_conf = cdata.get("confidence", 50)
        trend = cdata.get("trend", "stable")

        # Suppress alerts for narratives created this cycle (desk seedling noise)
        cycle_created = cdata.get("cycle_created", current_cycle)
        if cycle_created >= current_cycle - 1:
            continue

        if nid in prev_narr:
            prev_conf = prev_narr[nid].get("confidence", cur_conf)
        else:
            continue  # New narrative without previous state — skip initial alert

        swing = cur_conf - prev_conf
        abs_swing = abs(swing)
        cur_time = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        if abs_swing >= SWING_ALERT_THRESHOLD:
            escalation_level = "flash" if abs_swing >= CRITICAL_SWING_THRESHOLD else "pro"
            direction = "up" if swing > 0 else "down"

            alert = {
                "alert_type": "confidence_swing",
                "narrative_id": nid,
                "narrative": cdata.get("last_reasoning", ""),
                "previous_confidence": prev_conf,
                "new_confidence": cur_conf,
                "swing_points": swing,
                "direction": direction,
                "trend": trend,
                "escalation_level": escalation_level,
                "resolution_date": cdata.get("resolution_date"),
                "timestamp": cur_time,
                "trigger": f"{nid} confidence swing {swing:+.0f}pts ({prev_conf}% → {cur_conf}%)",
            }
            alerts.append(alert)

    # Also check escalation_queue in current state
    for esc in current.get("escalation_queue", []):
        esc_id = esc.get("narrative", "")
        if esc_id:
            alert = {
                "alert_type": "escalation_queue",
                "narrative_id": esc_id,
                "narrative": esc.get("reason", f"Escalation: {esc.get('level', 'flash')}"),
                "previous_confidence": None,
                "new_confidence": None,
                "swing_points": 0,
                "direction": "stable",
                "trend": "stable",
                "escalation_level": esc.get("level", "flash"),
                "resolution_date": None,
                "timestamp": esc.get("detected_at", cur_time()),
                "trigger": f"Narrative {esc_id} escalated to {esc.get('level', 'flash')}",
            }
            alerts.append(alert)

    return alerts


def format_alert_email(alert: dict) -> str:
    """Format a single I&W alert into human-readable text."""
    lines = [
        f"[I&W ALERT] {alert['trigger']}",
        f"Timestamp: {alert['timestamp']}",
        f"Level: {alert['escalation_level'].upper()}",
        "",
        f"Narrative: {alert['narrative_id']}",
    ]

    if alert['alert_type'] == 'confidence_swing':
        lines += [
            f"Previous confidence: {alert['previous_confidence']}%",
            f"New confidence: {alert['new_confidence']}%",
            f"Swing: {alert['swing_points']:+d}pts ({alert['direction']})",
            f"Trend: {alert['trend']}",
        ]
        if alert.get('narrative'):
            lines.append(f"Context: {alert['narrative'][:300]}")
        if alert.get('resolution_date'):
            lines.append(f"Resolution: {alert['resolution_date']}")
    else:
        lines.append(f"Reason: {alert.get('narrative', 'No details')}")

    return "\n".join(lines)


def send_via_agentmail(subject: str, body: str, dry_run: bool = False) -> bool:
    """Send email via AgentMail REST API."""
    api_key = os.environ.get("AGENTMAIL_API_KEY", "")
    if not api_key and not dry_run:
        log("No AGENTMAIL_API_KEY — skipping send")
        return False

    import urllib.request

    payload = json.dumps({
        "to": AGENTMAIL_INBOX,
        "subject": subject,
        "text": body,
    }).encode()

    if dry_run:
        log(f"[DRY RUN] Subject: {subject}")
        log(f"[DRY RUN] Body: {len(body)} chars")
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
        log(f"AgentMail send failed: {e.code}")
        return False
    except Exception as e:
        log(f"AgentMail error: {e}")
        return False


def _send_webhook(alert: dict, url: str) -> bool:
    import urllib.request
    req = urllib.request.Request(
        url,
        data=json.dumps(alert).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception:
        return False


def _maybe_trigger_unscheduled_cognition(alert: dict) -> None:
    """For critical swings, trigger unscheduled analysis."""
    if alert["escalation_level"] == "flash":
        script = REPO / "scripts" / "unscheduled_cognition.py"
        if script.exists():
            import subprocess
            try:
                subprocess.Popen(
                    ["python3", str(script), "--fire",
                     "--region", alert["narrative_id"].split("_")[0] if "_" in alert["narrative_id"] else "global",
                     "--trigger", alert["trigger"]],
                    cwd=str(REPO),
                )
                log(f"Triggered unscheduled cognition for {alert['narrative_id']}")
            except Exception as e:
                log(f"Failed to trigger unscheduled cognition: {e}")


def main() -> int:
    parser = argparse.ArgumentParser(description="I&W Trigger Engine")
    parser.add_argument("--state", default=str(DEFAULT_STATE), help="Path to cognition_state.json")
    parser.add_argument("--dry-run", action="store_true", help="No actual sends")
    parser.add_argument("--check-only", action="store_true", help="Check for alerts, no send")
    parser.add_argument("--force", action="store_true", help="Send even if deduplicated")
    args = parser.parse_args()

    state_path = pathlib.Path(args.state)
    subs_path = SUBSCRIPTIONS_FILE
    alert_log_path = ALERT_LOG

    # Load current and previous state
    current = load_state(state_path)
    if not current:
        log("No state available")
        return 1

    previous = load_previous_state(state_path)

    # Detect alerts
    alerts = detect_swing_alerts(current, previous)
    if not alerts:
        log("No new alerts detected")
        # Still save backup for next cycle comparison
        save_state_backup(current, state_path)
        return 0

    log(f"Detected {len(alerts)} alert(s):")
    for a in alerts:
        log(f"  {a['trigger']} [{a['escalation_level']}]")

    if args.check_only:
        save_state_backup(current, state_path)
        return 0

    # Load dedup log
    sent_alerts = load_sent_alerts(alert_log_path)

    # Load subscribers for webhook delivery
    subs = load_subscriptions(subs_path)
    subscriber_list = subs.get("subscribers", [])

    # Process each alert
    sent_count = 0
    dedup_count = 0

    for alert in alerts:
        # Dedup check
        if not args.force and is_deduplicated(alert, sent_alerts):
            dedup_count += 1
            log(f"  Dedup: {alert['narrative_id']} (already sent within {DEDUP_WINDOW_HOURS}h)")
            continue

        # Format and send email
        body = format_alert_email(alert)
        subject = f"[I&W ALERT] {alert['narrative_id']} — {alert['trigger']}"
        send_via_agentmail(subject, body, dry_run=args.dry_run)

        # Webhook push to subscribers
        for sub in subscriber_list:
            webhook = sub.get("webhook_url")
            if webhook:
                allowed = sub.get("narratives", ["all"])
                if "all" in allowed or alert["narrative_id"] in allowed:
                    _send_webhook(alert, webhook)

        # Trigger unscheduled cognition for critical alerts
        if not args.dry_run:
            _maybe_trigger_unscheduled_cognition(alert)

            # Also write to escalation_queue in cognition_state
            esc_queue = current.setdefault("escalation_queue", [])
            esc_queue.append({
                "level": alert["escalation_level"],
                "narrative": alert["narrative_id"],
                "reason": alert["trigger"],
                "detected_at": alert["timestamp"],
                "resolved": False,
            })

        # Log sent alert
        log_sent_alert(alert, alert_log_path)
        sent_count += 1

    # Save current state as backup for next cycle
    save_state_backup(current, state_path)

    summary = f"{sent_count} alerts sent, {dedup_count} deduplicated"
    log(summary)
    print(f"✅ I&W: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
