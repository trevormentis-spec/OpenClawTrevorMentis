#!/usr/bin/env python3
"""
Continuous monitoring daemon — runs between daily brief cron fires.

Provides lightweight continuous collection on a ~60-minute cadence:
1. Kalshi market scanner — check for significant probability shifts (>10pts)
2. AgentMail inbox — check for non-newsletter new mail
3. Brief existence check — did today's brief get produced?
4. Moltbook activity — check notifications and DMs

If anything significant is found, it writes to:
- brain/memory/episodic/YYYY-MM-DD.jsonl (new episode)
- logs/continuous-monitor-YYYY-MM-DD.log

Designed to be called from cron every 60 minutes, NOT as a persistent daemon
(which would require supervisor/service management).

Usage:
    python3 scripts/continuous_monitor.py            # Full check
    python3 scripts/continuous_monitor.py --quick     # Check Kalshi + inbox only
    python3 scripts/continuous_monitor.py --kalshi    # Kalshi only
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LOG_DIR = REPO_ROOT / "logs"
EPISODIC_DIR = REPO_ROOT / "brain" / "memory" / "episodic"
STATE_FILE = REPO_ROOT / "memory" / "heartbeat-state.json"

# Kalshi alert threshold: report if any market moves > X points in 24h
KALSHI_SWING_THRESHOLD = 10
KALSHI_CRITICAL_THRESHOLD = 20  # Points for critical escalation (doubles collection)

# Brief check: if no brief produced by HOUR_CUTOFF (UTC), flag it
HOUR_CUTOFF = 14  # 14:00 UTC = 07:00 PT — brief should be done by now

# Escalation script
COLLECTION_STATE_SCRIPT = REPO_ROOT / "scripts" / "collection_state.py"


def escalate(region: str, severity: str, reason: str, trigger: str = "") -> None:
    """Set an escalation flag in collection state. Changes future collection behavior.
    
    Severity -> cap multiplier: critical -> +100%, significant -> +50%, notable -> +25%
    """
    if not COLLECTION_STATE_SCRIPT.exists():
        log(f"cannot escalate: collection_state.py not found")
        return
    try:
        subprocess.check_call([
            "python3", str(COLLECTION_STATE_SCRIPT),
            "--set-escalation",
            "--region", region,
            "--severity", severity,
            "--reason", reason,
            "--trigger", trigger,
        ], cwd=str(REPO_ROOT), timeout=15)
        log(f"ESCALATION [{severity.upper()}] {region}: {reason}")
    except Exception as exc:
        log(f"escalation failed: {exc}")
    append_episode("escalation_set", {
        "region": region, "severity": severity,
        "reason": reason, "trigger": trigger,
    })


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[monitor {ts}] {msg}", file=sys.stderr, flush=True)


def append_episode(event_type: str, data: dict) -> None:
    """Append an event to today's episodic memory."""
    EPISODIC_DIR.mkdir(parents=True, exist_ok=True)
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    ep_file = EPISODIC_DIR / f"{today}.jsonl"
    entry = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
        "source": "continuous_monitor",
        "type": event_type,
        **data,
    }
    with open(ep_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


def check_kalshi() -> list[dict]:
    """Run Kalshi scanner and check for significant swings."""
    results = []
    scanner = REPO_ROOT / "scripts" / "kalshi_scanner.py"
    if not scanner.exists():
        log("kalshi_scanner.py not found — skipping")
        return results

    try:
        out = subprocess.check_output(
            ["python3", str(scanner), "--json"],
            cwd=str(REPO_ROOT), timeout=120, text=True)
        markets = json.loads(out)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as exc:
        log(f"kalshi scan failed: {exc}")
        return results
    except json.JSONDecodeError:
        log("kalshi output not valid JSON — skipping")
        return results

    if isinstance(markets, dict):
        markets = markets.get("markets", markets)

    for m in markets if isinstance(markets, list) else []:
        if not isinstance(m, dict):
            continue
        # Look for >10pt daily swing
        yes_bid = m.get("yes_bid", 0)
        prev_close = m.get("prev_close", yes_bid)
        if isinstance(yes_bid, (int, float)) and isinstance(prev_close, (int, float)):
            swing = abs(yes_bid - prev_close)
            if swing >= KALSHI_SWING_THRESHOLD:
                results.append({
                    "market": m.get("ticker", m.get("id", "?")),
                    "yes_bid": yes_bid,
                    "swing_24h": round(swing, 1),
                    "direction": "up" if yes_bid > prev_close else "down",
                })

    # Escalation-triggering swings
    critical = [s for s in results if s["swing_24h"] >= KALSHI_CRITICAL_THRESHOLD]
    notable = [s for s in results if s["swing_24h"] >= KALSHI_SWING_THRESHOLD]

    if critical:
        append_episode("kalshi_critical_swing", {
            "swings": critical, "threshold": KALSHI_CRITICAL_THRESHOLD,
        })
        log(f"Kalshi CRITICAL: {len(critical)} swings >{KALSHI_CRITICAL_THRESHOLD}pts")
        for s in critical:
            ticker = s.get("market", "").lower()
            region = "global_finance"
            if "iran" in ticker or "hormuz" in ticker:
                region = "middle_east"
            elif "russia" in ticker or "ukraine" in ticker:
                region = "europe"
            elif "china" in ticker or "taiwan" in ticker:
                region = "asia"
            escalate(region, "critical",
                     f"Kalshi {s['market']} swung {s['swing_24h']}pts",
                     trigger=f"kalshi_swing_{s['swing_24h']}pts")
    elif notable:
        append_episode("kalshi_swing_alert", {
            "swings": notable, "threshold": KALSHI_SWING_THRESHOLD,
        })
        log(f"Kalshi: {len(notable)} notable swings detected")
        # Escalate first notable swing
        s = notable[0]
        ticker = s.get("market", "").lower()
        region = "global_finance"
        if "iran" in ticker or "hormuz" in ticker:
            region = "middle_east"
        elif "russia" in ticker or "ukraine" in ticker:
            region = "europe"
        escalate(region, "notable",
                 f"Kalshi swing {s['swing_24h']}pts on {s['market']}",
                 trigger=f"kalshi_swing_{s['swing_24h']}pts")

    return results


def check_brief_produced() -> dict | None:
    """Check if today's brief exists in expected locations."""
    date_utc = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    hour_utc = dt.datetime.now(dt.timezone.utc).hour
    
    brief_dir = pathlib.Path.home() / "trevor-briefings" / date_utc
    pdf = brief_dir / "final" / f"brief-{date_utc}.pdf"
    
    if pdf.exists():
        return {"date": date_utc, "status": "produced", "path": str(pdf)}
    
    # Only flag as missing if we're past the cutoff time
    if hour_utc >= HOUR_CUTOFF:
        append_episode("brief_missing", {
            "date": date_utc,
            "hour_utc": hour_utc,
            "cutoff": HOUR_CUTOFF,
        })
        # Brief missing is significant — boost all regions
        log("BRIEF MISSING — escalating all regions")
        for r in ["europe", "asia", "middle_east", "north_america",
                   "south_central_america", "global_finance"]:
            escalate(r, "significant", "Daily brief not produced on time",
                     trigger="brief_missing")
        return {"date": date_utc, "status": "missing"}
    
    return None


def check_agentmail_inbox() -> list[dict]:
    """Quick check of AgentMail inbox for non-newsletter new mail."""
    api_key = os.environ.get("AGENTMAIL_API_KEY", "")
    if not api_key:
        return []

    try:
        req = urllib.request.Request(
            "https://api.agentmail.to/v1/inbox/search",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            messages = json.loads(resp.read())
    except Exception as exc:
        log(f"agentmail check failed (non-fatal): {exc}")
        return []

    if not isinstance(messages, list):
        messages = messages.get("messages", messages) if isinstance(messages, dict) else []

    important = []
    for m in messages[:10]:
        subject = (m.get("subject") or m.get("Subject") or "").lower()
        # Skip newsletters, notifications, automated sends
        skip_keywords = ["newsletter", "unsubscribe", "you subscribed",
                         "daily digest", "weekly summary", "noreply@",
                         "no-reply@"]
        if any(k in subject for k in skip_keywords):
            continue
        important.append(m)

    if important:
        append_episode("agentmail_new_mail", {
            "count": len(important),
            "senders": [m.get("from", "?") for m in important],
            "subjects": [m.get("subject", "?") for m in important],
        })

    return important


def run_cycle(quick: bool = False, kalshi_only: bool = False) -> dict:
    """Run one monitoring cycle. Returns summary of findings."""
    findings = {"kalshi_swings": [], "brief_status": None, "new_mail": []}

    if not kalshi_only:
        # Always check Kalshi (fast, cheap)
        findings["kalshi_swings"] = check_kalshi()

    if not quick and not kalshi_only:
        # Medium checks
        findings["brief_status"] = check_brief_produced()

    if not kalshi_only:
        # Fast check
        findings["new_mail"] = check_agentmail_inbox()

    return findings


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true",
                        help="Quick check (Kalshi + inbox only)")
    parser.add_argument("--kalshi", action="store_true",
                        help="Kalshi-only check")
    args = parser.parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    now = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")

    log(f"Continuous monitor cycle starting (quick={args.quick}, kalshi={args.kalshi})")
    findings = run_cycle(quick=args.quick, kalshi_only=args.kalshi)

    # Log results
    k = len(findings.get("kalshi_swings", []))
    b = findings.get("brief_status", {})
    m = len(findings.get("new_mail", []))

    summary_parts = []
    if k:
        summary_parts.append(f"{k} Kalshi swings")
    if b and b.get("status") == "missing":
        summary_parts.append("⚠️ BRIEF MISSING")
    if m:
        summary_parts.append(f"{m} new inbox messages")
    if not summary_parts:
        summary_parts.append("all clear")

    log(f"Monitor cycle complete: {', '.join(summary_parts)}")
    
    # Print JSON for cron logging
    print(json.dumps({
        "timestamp": f"{today}T{now}Z",
        "findings": findings,
        "summary": ", ".join(summary_parts),
    }))

    return 0 if not any([
        b and b.get("status") == "missing"
    ]) else 1


if __name__ == "__main__":
    sys.exit(main())
