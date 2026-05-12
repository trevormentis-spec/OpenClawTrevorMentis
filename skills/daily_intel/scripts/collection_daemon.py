#!/usr/bin/env python3
"""
collection_daemon.py — Lightweight persistent event-driven collection daemon.

Runs as a heartbeat-driven process (not a true daemon) that continuously:
- Monitors RSS feeds for new articles
- Checks prediction market repricing
- Detects narrative shifts
- Scores events for strategic significance
- Updates persistent state model
- Triggers cognition when thresholds crossed

Separates CONTINUOUS COLLECTION (low-cost, lightweight) from
PERIODIC COGNITION (deep reasoning, daily batch).

Design: triggered every 15-60 minutes via cron/heartbeat. Not a
long-running process. State persists in cron_tracking/collection_state.json.

Output: cron_tracking/collection_daemon_state.json
"""
from __future__ import annotations

import datetime
import hashlib
import json
import re
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from trevor_config import THEATRE_KEYS as THEATRES, WORKSPACE
from trevor_log import get_logger

log = get_logger("collection_daemon")
CRON_DIR = SKILL_ROOT / "cron_tracking"
STATE_FILE = CRON_DIR / "collection_daemon_state.json"
EVENT_LOG = CRON_DIR / "collection_events.json"
TRIGGER_LOG = CRON_DIR / "cognition_triggers.json"

# ── Feed registry (lightweight, quick-check only) ──
QUICK_FEEDS = {
    "bbc_world": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "reuters_world": "https://www.reutersagency.com/feed/",
    "al_jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
}

# ── Event significance thresholds ──
SIGNIFICANCE_THRESHOLDS = {
    "critical": 90,   # Crosses -> trigger deep cognition immediately
    "high": 70,       # Crosses -> flag for next daily cycle
    "medium": 40,     # Log only
    "low": 20,        # Ignore
}

# ── Escalation trigger keywords → significance score ──
ESCALATION_KEYWORDS = {
    "nuclear": 95, "mobilization": 85, "ultimatum": 80, "declaration of war": 95,
    "military exercise": 60, "troop buildup": 75, "sanctions": 55, "embargo": 65,
    "ceasefire": 50, "withdrawal": 45, "assassination": 80, "coup": 85,
    "election": 40, "protests": 55, "crackdown": 60, "state of emergency": 75,
    "diplomatic break": 70, "ambassador expelled": 65, "air strike": 75,
    "drone strike": 60, "carrier strike group": 75, "ballistic missile": 85,
    "cyber attack": 55, "critical infrastructure": 65, "supply chain": 40,
    "strategic partnership": 35, "alliance": 30, "military aid": 50,
    "weapons system": 55, "exercises": 45, "deploy": 60, "alert": 50,
}


def load_state() -> dict:
    """Load persistent collection state."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass
    return {
        "first_run": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_run": "",
        "run_count": 0,
        "events_processed": 0,
        "cognition_triggers_fired": 0,
        "active_alerts": [],
        "last_event_hashes": {},
        "escalation_ladders": {},
        "region_volatility": {},
    }


def save_state(state: dict):
    """Save persistent collection state."""
    state["last_run"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    state["run_count"] = state.get("run_count", 0) + 1
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def fetch_quick_feeds(state: dict) -> list[dict]:
    """Fetch recent articles from RSS feeds. Tracks seen hashes to avoid duplicates."""
    events = []
    seen = state.get("last_event_hashes", {})
    
    for feed_id, url in QUICK_FEEDS.items():
        try:
            import xml.etree.ElementTree as ET
            req = urllib.request.Request(url, headers={"User-Agent": "TrevorCollectionDaemon/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                xml_data = resp.read()
            root = ET.fromstring(xml_data)
            
            new_count = 0
            for item in root.iter("item"):
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                pub_date = item.findtext("pubDate", "")
                desc = item.findtext("description", "")[:300]
                
                if not title or not link:
                    continue
                
                event_hash = hashlib.md5(link.encode()).hexdigest()[:12]
                if event_hash in seen.get(feed_id, {}):
                    continue  # already seen
                
                events.append({
                    "feed": feed_id,
                    "title": title,
                    "url": link,
                    "summary": desc[:200],
                    "published": pub_date,
                    "detected_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "hash": event_hash,
                })
                new_count += 1
            
            # Update seen hashes (keep last 50 per feed)
            if feed_id not in seen:
                seen[feed_id] = {}
            for e in events:
                if e["feed"] == feed_id:
                    seen[feed_id][e["hash"]] = True
            # Prune old hashes (keep last 50)
            if len(seen.get(feed_id, {})) > 50:
                seen[feed_id] = dict(list(seen[feed_id].items())[-50:])
            
            log.info(f"Feed {feed_id}: {new_count} new articles")
        except Exception as e:
            log.warning(f"Feed {feed_id} failed: {e}")
    
    state["last_event_hashes"] = seen
    return events


def check_market_repricing(state: dict) -> list[dict]:
    """Quick check for significant prediction market repricing."""
    events = []
    kalshi_dir = WORKSPACE / "exports"
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    for f in sorted(kalshi_dir.glob("kalshi-scan-*.md"), reverse=True)[:2]:
        if not f.exists():
            continue
        try:
            text = f.read_text()
            for line in text.split("\n"):
                parts = line.strip().split()
                if len(parts) >= 8 and parts[0].startswith("KX"):
                    try:
                        yes_bid = float(parts[1].replace("$", ""))
                        volume = int(float(parts[6].replace(",", "")))
                        expiry = parts[7] if len(parts) > 7 else "?"
                        
                        # Score significance
                        sig = 0
                        if volume > 1_000_000:
                            sig += 30
                        elif volume > 500_000:
                            sig += 20
                        elif volume > 100_000:
                            sig += 10
                        if yes_bid > 0.6 or yes_bid < 0.2:
                            sig += 15  # high conviction / extreme pricing
                        if "IRAN" in parts[0] or "HORMUZ" in parts[0]:
                            sig += 20  # geopolitical premium
                        
                        if sig >= SIGNIFICANCE_THRESHOLDS["medium"]:
                            events.append({
                                "type": "market_repricing",
                                "ticker": parts[0],
                                "yes_bid": yes_bid,
                                "volume": volume,
                                "expiry": expiry,
                                "significance": sig,
                                "detected_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                            })
                    except:
                        pass
        except:
            pass
    
    return events


def score_event_significance(event: dict) -> int:
    """Score a single event for strategic significance (0-100)."""
    score = 0
    title = event.get("title", "") + " " + event.get("summary", "")
    text_lower = title.lower()
    
    # Check escalation keywords
    for keyword, sig in ESCALATION_KEYWORDS.items():
        if keyword in text_lower:
            score += sig * 0.3  # scale down, keywords are partial signals
    
    # Cap at 100
    return min(100, int(score))


def check_escalation_ladders(state: dict, events: list[dict]) -> list[dict]:
    """Track escalation signals and detect ladder progression."""
    alerts = []
    for region in THEATRES:
        ladders = state.get("escalation_ladders", {}).get(region, {"level": 0, "signals": [], "last_escalation": ""})
        
        # Count high-significance events for this region
        region_events = [e for e in events if region.lower() in (e.get("title","") + e.get("summary","")).lower()]
        sig_events = [e for e in region_events if e.get("significance", 0) > SIGNIFICANCE_THRESHOLDS["medium"]]
        
        if sig_events:
            ladders["level"] = min(10, ladders["level"] + len(sig_events))
            ladders["signals"].append({
                "count": len(sig_events),
                "detected_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            })
            ladders["last_escalation"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            
            if ladders["level"] >= 7:
                alerts.append({
                    "region": region,
                    "level": ladders["level"],
                    "type": "escalation_high",
                    "triggered_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                })
        
        state["escalation_ladders"][region] = ladders
    
    return alerts


def check_cognition_triggers(events: list[dict], alerts: list[dict]) -> list[dict]:
    """Check if any thresholds are crossed that warrant deep cognition."""
    triggers = []
    
    # Critical escalation alert
    for alert in alerts:
        if alert["level"] >= 8:
            triggers.append({
                "type": "urgent_escalation",
                "region": alert["region"],
                "reason": f"Escalation ladder at level {alert['level']} in {alert['region']}",
                "triggered_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "requires_immediate_attention": True,
            })
    
    # High-significance events
    for event in events:
        sig = event.get("significance", 0)
        if sig >= SIGNIFICANCE_THRESHOLDS["critical"]:
            triggers.append({
                "type": "critical_event",
                "source": event.get("feed", event.get("type", "unknown")),
                "reason": f"Critical significance event: {event.get('title','')[:100]}",
                "significance": sig,
                "triggered_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "requires_immediate_attention": True,
            })
        elif sig >= SIGNIFICANCE_THRESHOLDS["high"]:
            triggers.append({
                "type": "high_priority_event",
                "source": event.get("feed", event.get("type", "unknown")),
                "reason": f"High significance event: {event.get('title','')[:80]}",
                "significance": sig,
                "triggered_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "requires_immediate_attention": False,
            })
    
    return triggers


def main():
    """Run one collection daemon cycle."""
    log.info("Collection daemon cycle starting")
    
    state = load_state()
    all_events = []
    
    # Phase 1: Quick RSS check (continuous collection layer)
    feed_events = fetch_quick_feeds(state)
    for e in feed_events:
        e["significance"] = score_event_significance(e)
    all_events.extend(feed_events)
    
    # Phase 2: Market repricing check
    market_events = check_market_repricing(state)
    all_events.extend(market_events)
    
    # Phase 3: Event significance scoring
    for event in all_events:
        if "significance" not in event:
            event["significance"] = score_event_significance(event)
    
    # Phase 4: Escalation ladder tracking
    escalation_alerts = check_escalation_ladders(state, all_events)
    
    # Phase 5: Cognition trigger check
    triggers = check_cognition_triggers(all_events, escalation_alerts)
    
    # Phase 6: Update state
    state["events_processed"] = state.get("events_processed", 0) + len(all_events)
    state["cognition_triggers_fired"] = state.get("cognition_triggers_fired", 0) + len(triggers)
    state["active_alerts"] = [a for a in state.get("active_alerts", [])] + escalation_alerts
    # Keep only last 10 alerts
    state["active_alerts"] = state["active_alerts"][-10:]
    save_state(state)
    
    # Save events for observability
    event_record = {
        "run_time": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "new_events": len(all_events),
        "total_events": state["events_processed"],
        "triggers_fired": len(triggers),
        "escalation_alerts": len(escalation_alerts),
        "events": [
            {"feed": e.get("feed", e.get("type", "?")), "title": e.get("title", "")[:80],
             "sig": e.get("significance", 0), "time": e.get("detected_at", "")}
            for e in sorted(all_events, key=lambda x: x.get("significance", 0), reverse=True)[:10]
        ],
        "triggers": [
            {"type": t["type"], "reason": t["reason"][:100], "immediate": t.get("requires_immediate_attention", False)}
            for t in triggers
        ],
    }
    EVENT_LOG.write_text(json.dumps(event_record, indent=2))
    
    # Save triggers separately
    if triggers:
        trigger_log = {"triggers": triggers, "fired_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}
        TRIGGER_LOG.write_text(json.dumps(trigger_log, indent=2))
    
    # Report
    print(f"\n{'='*60}")
    print(f"COLLECTION DAEMON — Cycle #{state['run_count']}")
    print(f"{'='*60}")
    print(f"  Events processed this cycle: {len(all_events)}")
    print(f"  Total events: {state['events_processed']}")
    print(f"  Cognition triggers: {len(triggers)}")
    print(f"  Escalation alerts: {len(escalation_alerts)}")
    
    if all_events:
        top = sorted(all_events, key=lambda x: x.get("significance", 0), reverse=True)[:3]
        print(f"\n  Top events:")
        for e in top:
            sig_bar = "█" * (e.get("significance", 0) // 10)
            print(f"  {sig_bar} [{e.get('significance', 0)}] {e.get('title','?')[:80]}")
    
    if triggers:
        print(f"\n  Cognition triggers fired:")
        for t in triggers:
            icon = "🚨" if t.get("requires_immediate_attention") else "⚡"
            print(f"  {icon} {t['reason'][:100]}")
    
    print(f"\n  Escalation ladders:")
    for region, ladder in sorted(state.get("escalation_ladders", {}).items(), key=lambda x: x[1]["level"], reverse=True):
        bar = "█" * ladder["level"] + "░" * (10 - ladder["level"])
        print(f"  {region:<25s} {bar} {ladder['level']}/10")
    
    log.info("Collection daemon cycle complete",
             events=len(all_events),
             triggers=len(triggers),
             total_events=state["events_processed"])
    
    return 0 if not triggers else 1


if __name__ == "__main__":
    sys.exit(main())
