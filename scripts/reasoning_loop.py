#!/usr/bin/env python3
"""
Persistent Reasoning Loop — runs between brief cycles.

Monitors data feeds for changes that confirm or contradict
standing assessments from the last brief. Surfaces deltas
pre-emptively rather than waiting for the next scheduled run.

Architecture:
  - Reads last brief's key judgments from brain/memory/episodic
  - Checks current data feeds (RSS, FCC, Kalshi, email inbox)
  - Compares: same signals? new contradictions? missing expected events?
  - If meaningful delta found: alerts via AgentMail to inbox
  - Logs delta state for next full brief cycle

Schedule: every 10 minutes via cron
  python3 scripts/reasoning_loop.py
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
EPISODIC_DIR = REPO_ROOT / "brain" / "memory" / "episodic"
STATE_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "reasoning-state.json"
FEED_CACHE = REPO_ROOT / "brain" / "memory" / "semantic" / "reasoning-feed-cache.json"

# How far back to look for the last brief
MAX_BRIEF_AGE_HOURS = 36
# How often to re-check data feeds (in minutes, to avoid redundant checks on tight cron)
CHECK_INTERVAL_MINUTES = 10


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[reason-loop {ts}] {msg}", file=sys.stderr, flush=True)


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_check": None, "last_brief_id": None, "active_gaps": [], "deltas_log": []}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def load_feed_cache() -> dict:
    if FEED_CACHE.exists():
        try:
            return json.loads(FEED_CACHE.read_text())
        except Exception:
            pass
    return {"last_rss_headlines": [], "last_kalshi_prices": {}, "last_fcc_count": 0}


def save_feed_cache(cache: dict) -> None:
    FEED_CACHE.parent.mkdir(parents=True, exist_ok=True)
    FEED_CACHE.write_text(json.dumps(cache, indent=2))


def get_last_brief() -> dict | None:
    """Find the most recent brief from episodic memory."""
    now = dt.datetime.now(dt.timezone.utc)
    latest = None
    for f in sorted(EPISODIC_DIR.glob("*.jsonl"), reverse=True):
        for line in f.read_text().split("\n"):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("type") != "report_delivery":
                continue
            ts = rec.get("timestamp", "")
            try:
                rec_time = dt.datetime.fromisoformat(ts)
            except (ValueError, TypeError):
                continue
            age = (now - rec_time).total_seconds() / 3600
            if age > MAX_BRIEF_AGE_HOURS:
                continue
            if latest is None or rec_time > dt.datetime.fromisoformat(latest["timestamp"]):
                latest = rec
    return latest


# =========================================================================
# DATA FEED CHECKERS — each returns a delta dict
# =========================================================================

def check_rss_headlines(cache: dict) -> dict:
    """Check current RSS headlines against last check for new breaking stories."""
    from feedparser import parse as parse_feed

    # Sample a few key feeds for breaking signals
    feed_urls = [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://feeds.bbci.co.uk/news/world/middle_east/rss.xml",
    ]

    current_headlines = []
    breaks = []

    for url in feed_urls:
        try:
            feed = parse_feed(url)
            for entry in feed.get("entries", [])[:5]:
                title = entry.get("title", "")
                link = entry.get("link", "")
                current_headlines.append({"title": title, "url": link, "source": url})
        except Exception:
            continue

    # Compare against cached headlines
    prev_headlines = {h["title"] for h in cache.get("last_rss_headlines", [])}
    new_headlines = [h for h in current_headlines if h["title"] not in prev_headlines]

    if new_headlines:
        # Check if any new headline touches known interest areas
        interest_keywords = [
            "strike", "attack", "ceasefire", "nuclear", "missile", "sanction",
            "election", "coup", "protest", "collapse", "crash", "emergency",
            "ground station", "satellite", "launch", "spacex", "starlink",
            "gsaas", "fcc", "kessler", "debris",
        ]
        for h in new_headlines:
            text = (h["title"] + " " + h.get("url", "")).lower()
            matches = [kw for kw in interest_keywords if kw in text]
            if matches:
                breaks.append({"headline": h["title"], "url": h["url"], "matched_keywords": matches})

    # Update cache
    cache["last_rss_headlines"] = current_headlines[:50]
    save_feed_cache(cache)

    return {
        "feed": "rss_headlines",
        "new_headlines": len(new_headlines),
        "breaking_alerts": breaks,
    }


def check_fcc_filings(cache: dict) -> dict:
    """Check if FCC filings count has changed since last check."""
    url = "https://opendata.fcc.gov/resource/acbv-jbb4.json?$limit=5&$order=sys_updated_on%20DESC"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TrevorIntel/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        return {"feed": "fcc", "error": str(e)}

    # Just track count and most recent filer name
    current_count = len(data)
    current_top_filer = data[0].get("call_sign_licensee_name", "") if data else ""
    prev_count = cache.get("last_fcc_count", 0)

    delta = {}
    if current_count != prev_count:
        delta = {"count_changed": True, "prev": prev_count, "current": current_count,
                 "top_filer": current_top_filer}
        cache["last_fcc_count"] = current_count
        save_feed_cache(cache)

    return {"feed": "fcc", "delta": delta}


def check_kalshi(cache: dict) -> dict:
    """Check key prediction market contracts for significant moves."""
    contracts = [
        ("USAIRAN", "Kalshi USAIRAN YE26"),
        ("KXWTIMAX", "Kalshi Brent > $X"),
    ]
    # Read from latest kalshi scan if available
    scan_dir = REPO_ROOT / "exports"
    scans = sorted(scan_dir.glob("kalshi-scan-*.md"), reverse=True)
    if not scans:
        return {"feed": "kalshi", "error": "no scan found"}

    text = scans[0].read_text()
    changes = []
    for ticker, label in contracts:
        if ticker in text:
            # Extract price
            m = re.search(rf"{ticker}[^0-9]*([0-9.]+)", text)
            if m:
                price = float(m.group(1))
                prev_price = cache.get("last_kalshi_prices", {}).get(ticker)
                if prev_price is not None and abs(price - prev_price) > 2:
                    changes.append({"ticker": ticker, "label": label, "prev": prev_price, "current": price, "move_pp": round(price - prev_price, 1)})
                cache.setdefault("last_kalshi_prices", {})[ticker] = price
                save_feed_cache(cache)

    return {"feed": "kalshi", "significant_moves": changes}


# =========================================================================
# DELTA ANALYZER
# =========================================================================

def analyze_deltas(last_brief: dict, feed_deltas: list[dict]) -> list[dict]:
    """Figure out if any delta matters relative to the last brief."""
    alerts = []
    brief_kjs = last_brief.get("key_judgments", [])
    brief_summary = last_brief.get("summary", "").lower()

    for delta in feed_deltas:
        feed = delta.get("feed", "?")

        # Breaking news alerts
        for alert in delta.get("breaking_alerts", []):
            text = alert.get("headline", "").lower()
            # Check if this touches any recent judgment
            relevant = False
            for kj in brief_kjs:
                kj_words = kj.lower().split()[:5]
                if any(w in text for w in kj_words if len(w) > 4):
                    relevant = True
                    break
            # Also check general interest
            if any(kw in text for kw in ["starlink", "satellite", "ground station", "spacex"]):
                relevant = True

            if relevant:
                alerts.append({
                    "type": "breaking_headline",
                    "headline": alert["headline"],
                    "url": alert["url"],
                    "matched_keywords": alert.get("matched_keywords", []),
                    "relevant_to_judgment": True,
                })

        # FCC count changes
        fcc_delta = delta.get("delta", {})
        if fcc_delta.get("count_changed"):
            alerts.append({
                "type": "fcc_activity",
                "detail": f"FCC filings changed: {fcc_delta['prev']} → {fcc_delta['current']}",
                "top_filer": fcc_delta.get("top_filer", ""),
            })

        # Kalshi moves
        for move in delta.get("significant_moves", []):
            alerts.append({
                "type": "market_move",
                "ticker": move["ticker"],
                "detail": f"{move['label']}: {move['prev']}¢ → {move['current']}¢ ({move['move_pp']:+}pp)",
            })

    return alerts


# =========================================================================
# ALERT DELIVERY
# =========================================================================


def deliver_alert(alert: dict) -> bool:
    """Send an alert via AgentMail SDK to roderick.jones@gmail.com."""
    api_key = os.environ.get("AGENTMAIL_API_KEY", "")
    if not api_key:
        env_path = REPO_ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text().split("\n"):
                if "AGENTMAIL_API_KEY=" in line:
                    api_key = line.split("=", 1)[1].strip().strip("'\"")
                    break

    atype = alert.get("type", "unknown")
    detail = alert.get("detail", alert.get("headline", "Signal detected"))
    subject = f"Reasoning Loop: {atype}"

    body_lines = [
        f"Reasoning Loop - {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"Type: {atype}",
        f"Detail: {detail}",
    ]
    if atype == "breaking_headline":
        body_lines.append(f"Source: {alert.get('url', 'N/A')}")
        body_lines.append(f"Keywords: {', '.join(alert.get('matched_keywords', []))}")
    elif atype == "market_move":
        body_lines.append(f"Contract: {alert.get('ticker', '?')}")
    elif atype == "fcc_activity":
        body_lines.append(f"Filer: {alert.get('top_filer', '?')}")
    body_lines.extend(["", "-- Trevor Reasoning Loop"])

    if not api_key:
        log(f"Would alert but no AGENTMAIL_API_KEY: {subject} - {detail}")
        return False

    try:
        from agentmail import AgentMail
        client = AgentMail(api_key=api_key)
        client.inboxes.messages.send(
            inbox_id="trevor_mentis@agentmail.to",
            to="roderick.jones@gmail.com",
            subject=subject,
            text="\n".join(body_lines),
        )
        log(f"Alert sent: {subject}")
        return True
    except Exception as e:
        log(f"Alert failed: {e}")
        return False

def should_run(state: dict) -> bool:
    """Check if enough time has passed since last run."""
    last = state.get("last_check")
    if not last:
        return True
    try:
        last_time = dt.datetime.fromisoformat(last)
        elapsed = (dt.datetime.now(dt.timezone.utc) - last_time).total_seconds() / 60
        return elapsed >= CHECK_INTERVAL_MINUTES
    except (ValueError, TypeError):
        return True


def main() -> None:
    state = load_state()
    cache = load_feed_cache()

    if not should_run(state):
        log("Skipping — last check was less than 10 minutes ago")
        return

    now = dt.datetime.now(dt.timezone.utc).isoformat()

    # Step 1: Find the last brief
    last_brief = get_last_brief()
    if not last_brief:
        log("No recent brief found — skipping reasoning loop")
        state["last_check"] = now
        save_state(state)
        return

    brief_id = f"{last_brief.get('report_type', '?')}-{last_brief.get('date', '?')}"
    log(f"Last brief: {brief_id} ({last_brief.get('word_count', 0)} words)")

    # Step 2: Check data feeds
    feed_deltas = [
        check_rss_headlines(cache),
        check_fcc_filings(cache),
        check_kalshi(cache),
    ]

    # Step 3: Analyze deltas against last brief
    alerts = analyze_deltas(last_brief, feed_deltas)

    # Step 4: Deliver alerts
    alerts_sent = 0
    already_seen = set(state.get("active_gaps", []))
    for alert in alerts:
        sig = json.dumps(alert, sort_keys=True)
        if sig in already_seen:
            continue
        if deliver_alert(alert):
            alerts_sent += 1
            state.setdefault("active_gaps", []).append(sig)
            state.setdefault("deltas_log", []).append({
                "timestamp": now,
                "alert": alert,
            })

    # Trim delta log to last 50
    state["deltas_log"] = state.get("deltas_log", [])[-50:]

    # Step 5: Update state
    state["last_check"] = now
    state["last_brief_id"] = brief_id
    save_state(state)

    # Write findings to episodic memory for future sessions
    if alerts:
        memory_record = {
            "type": "reasoning_loop_findings",
            "timestamp": now,
            "brief_id": brief_id,
            "feeds_checked": len(feed_deltas),
            "alerts_count": len(alerts),
            "alerts_sent": alerts_sent,
            "alerts": [{"type": a["type"], "detail": a.get("detail", a.get("headline", ""))} for a in alerts],
            "summary": f"{len(alerts)} delta(s) detected across {len(feed_deltas)} feeds, {alerts_sent} alert(s) sent",
        }
        EPISODIC_DIR.mkdir(parents=True, exist_ok=True)
        today = dt.date.today().isoformat()
        with open(EPISODIC_DIR / f"{today}.jsonl", "a") as f:
            f.write(json.dumps(memory_record) + "\n")
        log(f"Written to episodic memory: {len(alerts)} alerts logged")
        # Write gap summary to daily memory file
        memory_dir = REPO_ROOT / "memory"
        memory_file = memory_dir / f"{today}.md"
        gap_lines = [f"\n## Reasoning Loop - {now[:16]}",
                      f"Feeds: {len(feed_deltas)} | Alerts: {len(alerts)}"]
        for a in alerts[:5]:
            gap_lines.append(f"- {a.get('type')}: {a.get('detail', a.get('headline', ''))}")
        if len(alerts) > 5:
            gap_lines.append(f"- ... (+{len(alerts)-5} more)")
        with open(memory_file, "a") as f:
            f.write("\n".join(gap_lines) + "\n")

    log(f"Check complete: {len(feed_deltas)} feeds, {len(alerts)} deltas, {alerts_sent} alerts sent")
    if alerts:
        for a in alerts:
            log(f"  → {a.get('type')}: {a.get('detail', a.get('headline', ''))}")


if __name__ == "__main__":
    main()
