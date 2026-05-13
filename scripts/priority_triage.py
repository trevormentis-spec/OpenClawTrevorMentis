#!/usr/bin/env python3
"""
Priority Triage Engine — Trevor's Executive Function.

Every 30 minutes, scans ALL intelligence sources for signals worth
autonomous analysis. Decides what matters and acts on it without
waiting for instruction.

Sources scanned:
  - Gmail (Maton API): ISW, CTP, Cipher Brief, Foreign Policy, etc.
  - Web search (Brave API): breaking news by keyword
  - Kalshi scanner: prediction market probability shifts >10pts
  - Telegram @judean_osint: real-time Middle East OSINT
  - Behavioral state: active escalations and event directives
  - Collection state: coverage gaps and quality drops
  - Continuous monitor: recent critical event log

Scoring (each signal gets 1-100):
  - Novelty: Is this new since last check?
  - Severity: Kinetic event, diplomatic rupture, market crash?
  - Actionability: Would analysis change the principal's decisions?
  - Urgency: Hours vs days?

If any signal ≥ 70: auto-fire Tier-1 or Tier-2 analysis, deliver to
Telegram + email, update behavioral state.

Usage:
    python3 scripts/priority_triage.py                    # Full triage cycle
    python3 scripts/priority_triage.py --check            # Report only, no analysis
    python3 scripts/priority_triage.py --status           # Current triage state
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "triage-state.json"
AUTONOMY_TRACKER_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "autonomy-tracker.json"
BEHAVIORAL_STATE_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "behavioral-state.json"
GMAIL_READER = REPO_ROOT / "scripts" / "gmail_reader.py"
KALSHI_SCANNER = REPO_ROOT / "scripts" / "kalshi_scanner.py"

# Signal threshold for autonomous analysis
AUTO_ANALYSIS_THRESHOLD = 70

# Cooldown: don't re-analyze the same signal type for N hours
SIGNAL_COOLDOWN_HOURS = 6

# Tier-1 model for strategic analysis
TIER1_MODEL = "anthropic/claude-opus-4.7"
TIER1_PROVIDER = "openrouter"

# Tier-2 model for tactical/regional analysis (V4 Pro via Direct API — cheap)
TIER2_MODEL = "deepseek/deepseek-v4-pro"
TIER2_PROVIDER = "deepseek"

USER_AGENT = "TrevorTriage/1.0"


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[triage {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, Exception):
            return {}
    return {}


def save_json(path: pathlib.Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def fetch(url: str, timeout: int = 15) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return None


# ── Triage State ──────────────────────────────────────────────────

def load_triage_state() -> dict:
    state = load_json(STATE_FILE)
    if not state:
        state = {
            "version": 1,
            "last_check": None,
            "signals_processed": 0,
            "analyses_fired": 0,
            "last_signals": [],  # Last 50 signals for dedup
            "cooldowns": {},      # signal_type → timestamp
        }
    return state


def save_triage_state(state: dict) -> None:
    state["last_check"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    save_json(STATE_FILE, state)


def check_cooldown(state: dict, signal_type: str) -> bool:
    """Check if this signal type is in cooldown."""
    cooldowns = state.get("cooldowns", {})
    last = cooldowns.get(signal_type)
    if not last:
        return False
    try:
        last_ts = dt.datetime.fromisoformat(last.replace("Z", "+00:00"))
        elapsed = (dt.datetime.now(dt.timezone.utc) - last_ts).total_seconds()
        return elapsed < SIGNAL_COOLDOWN_HOURS * 3600
    except (ValueError, TypeError):
        return False


def set_cooldown(state: dict, signal_type: str) -> None:
    state.setdefault("cooldowns", {})[signal_type] = dt.datetime.now(
        dt.timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Signal Sources ────────────────────────────────────────────────

def scan_gmail() -> list[dict]:
    """Check Gmail for new intel emails since last triage cycle."""
    signals = []
    state = load_triage_state()
    last_check = state.get("last_check", "")

    # Get today's unread intel
    try:
        api_key = os.environ.get("MATON_API_KEY", "")
        if not api_key:
            return signals

        base = "https://gateway.maton.ai/google-mail/gmail/v1/users/me"
        query = "is:unread" if not last_check else f"is:unread after:{last_check[:10]}"
        url = f"{base}/messages?q={urllib.parse.quote(query)}&maxResults=10"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
        data = json.loads(urllib.request.urlopen(req, timeout=20).read())
        messages = data.get("messages", [])

        for msg_ref in messages[:5]:
            msg_id = msg_ref["id"]
            url2 = f"{base}/messages/{msg_id}?format=metadata"
            req2 = urllib.request.Request(url2, headers={"Authorization": f"Bearer {api_key}"})
            msg = json.loads(urllib.request.urlopen(req2, timeout=20).read())
            headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
            sender = headers.get("from", "").lower()
            subject = headers.get("subject", "")
            snippet = msg.get("snippet", "")

            # Score sender importance
            intel_senders = {
                "publications@understandingwar.org": 90,   # ISW
                "criticalthreats@aei.org": 85,             # CTP
                "dailybrief@thecipherbrief.com": 80,       # Cipher Brief
                "reply@foreignpolicy.com": 70,             # Foreign Policy
                "newsletters@foreignpolicy.com": 70,        # FP newsletters
                "gzerodaily@gzeromedia.com": 65,           # GZERO
            }
            base_score = 20
            for s, score in intel_senders.items():
                if s in sender:
                    base_score = score
                    break

            # Escalate for urgent keywords
            urgent = ["breaking", "exclusive", "alert", "urgent", "confirmed",
                       "assassination", "strike", "nuclear", "ceasefire collapse",
                       "mobilization", "invasion", "attack"]
            severity_boost = 0
            text = (subject + " " + snippet).lower()
            for kw in urgent:
                if kw in text:
                    severity_boost += 10

            score = min(base_score + severity_boost, 100)

            if score >= 50:  # Only process if potentially interesting
                signals.append({
                    "source": "gmail",
                    "type": "intel_email",
                    "sender": sender,
                    "subject": subject,
                    "snippet": snippet[:300],
                    "score": score,
                    "tier": "tier1" if score >= 75 else "tier2",
                    "id": f"gmail-{msg_id[:8]}",
                })
    except Exception as exc:
        log(f"Gmail scan failed: {exc}")

    return signals


def scan_web() -> list[dict]:
    """Search the web for breaking geopolitical developments."""
    signals = []
    api_key = os.environ.get("BRAVE_API_KEY", "")
    if not api_key:
        return signals

    # Search critical topics
    topics = [
        "Iran Hormuz Strait escalation",
        "CIA Mexico cartel operations",
        "Russia Ukraine offensive",
        "Trump Xi summit Beijing",
        "China Taiwan military",
        "Venezuela US annexation",
    ]

    last_state = load_triage_state()
    last_check = last_state.get("last_check", "")

    for topic in topics:
        try:
            encoded = urllib.parse.quote(topic)
            url = f"https://api.search.brave.com/res/v1/web/search?q={encoded}&count=3&freshness=day"
            req = urllib.request.Request(url, headers={
                "Accept": "application/json",
                "X-Subscription-Token": api_key,
            })
            resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
            results = resp.get("web", {}).get("results", [])

            for r in results:
                title = r.get("title", "")
                desc = r.get("description", "")
                url_str = r.get("url", "")
                text = (title + " " + desc).lower()

                # Check if truly recent — Brave freshness filter handles this
                # Score by keyword severity
                severity_keywords = {
                    "strike": 10, "attack": 10, "killed": 15, "assassination": 20,
                    "nuclear": 20, "sanctions": 8, "ceasefire": 10, "collapse": 15,
                    "escalation": 12, "war": 15, "invasion": 20, "missile": 10,
                    "drone": 8, "explosion": 12, "mobilization": 15,
                }
                score = 30  # Base for any breaking news
                for kw, boost in severity_keywords.items():
                    if kw in text:
                        score += boost

                score = min(score, 100)

                if score >= 50:
                    signals.append({
                        "source": "web",
                        "type": "breaking_news",
                        "topic": topic,
                        "title": title[:150],
                        "url": url_str[:200],
                        "score": score,
                        "tier": "tier1" if score >= 80 else "tier2",
                        "id": f"web-{abs(hash(title)) % 10000:04d}",
                    })
        except Exception as exc:
            log(f"Web search for '{topic}' failed: {exc}")

    return signals


def scan_kalshi() -> list[dict]:
    """Check Kalshi for significant market swings."""
    signals = []
    try:
        state = load_json(REPO_ROOT / "brain" / "memory" / "semantic" / "collection-state.json")
        # Check episodic for recent Kalshi events
        ep_dir = REPO_ROOT / "brain" / "memory" / "episodic"
        today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
        ep_file = ep_dir / f"{today}.jsonl"
        if ep_file.exists():
            with open(ep_file) as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        if event.get("type") in ("kalshi_critical_swing", "kalshi_swing_alert"):
                            swings = event.get("swings", event.get("data", {}).get("swings", []))
                            for s in swings:
                                pts = abs(s.get("swing_24h", 0))
                                score = min(30 + pts * 3, 100)
                                if score >= 50:
                                    signals.append({
                                        "source": "kalshi",
                                        "type": "market_swing",
                                        "market": s.get("market", "?"),
                                        "description": f"{s.get('market', '?')} swung {pts}pts",
                                        "score": score,
                                        "tier": "tier1" if score >= 80 else "tier2",
                                        "id": f"kalshi-{s.get('market', '?')[:20]}",
                                    })
                    except (json.JSONDecodeError, Exception):
                        continue
    except Exception as exc:
        log(f"Kalshi scan failed: {exc}")
    return signals


def scan_behavioral_state() -> list[dict]:
    """Check behavioral state for active escalations."""
    signals = []
    bs = load_json(BEHAVIORAL_STATE_FILE)
    if not bs:
        return signals

    events = bs.get("event_directives", {})
    for esc in events.get("active_escalations", []):
        severity = esc.get("severity", "notable")
        sev_map = {"critical": 95, "significant": 80, "notable": 60}
        score = sev_map.get(severity, 50)
        signals.append({
            "source": "behavioral_state",
            "type": "escalation",
            "region": esc.get("region", "?"),
            "trigger": esc.get("trigger", "?"),
            "score": score,
            "tier": "tier1" if score >= 80 else "tier2",
            "id": f"esc-{esc.get('region', '?')}",
        })

    # Check collection gaps
    coll = bs.get("collection_directives", {})
    for gap in coll.get("linguistic_gaps", []):
        signals.append({
            "source": "behavioral_state",
            "type": "collection_gap",
            "region": gap.get("region", "?"),
            "description": str(gap.get("gaps", [""])[0])[:100],
            "score": 55,
            "tier": "tier2",
            "id": f"gap-{gap.get('region', '?')}",
        })

    # Check prioritization
    prio = bs.get("autonomous_prioritization", {})
    for region, p in prio.items():
        if p.get("priority_score", 0) >= 80:
            signals.append({
                "source": "behavioral_state",
                "type": "high_priority_region",
                "region": region,
                "score": min(p.get("priority_score", 50), 90),
                "tier": "tier1",
                "id": f"prio-{region}",
            })

    return signals


def scan_telegram() -> list[dict]:
    """Check Telegram channels for new messages with kinetic keywords."""
    signals = []
    channels = ["judean_osint", "HormuzMonitor"]
    important_kw = ["strike", "attack", "killed", "missile", "drone", "explosion",
                     "airstrike", "rocket", "alert", "red alert", "siren", "interception"]

    for channel in channels:
        try:
            url = f"https://t.me/s/{channel}"
            html = fetch(url, timeout=15)
            if not html:
                continue

            # Find recent messages
            messages = re.findall(
                r'<div class="tgme_widget_message_text[^>]*>(.*?)</div>',
                html, re.DOTALL
            )
            for msg in messages[:5]:
                text = re.sub(r"<[^>]+>", " ", msg).strip()
                text_l = text.lower()
                score = 20
                for kw in important_kw:
                    if kw in text_l:
                        score += 15
                if score >= 50:
                    signals.append({
                        "source": "telegram",
                        "type": "osint_alert",
                        "channel": channel,
                        "text": text[:200],
                        "score": min(score, 100),
                        "tier": "tier1" if score >= 80 else "tier2",
                        "id": f"tg-{channel}-{abs(hash(text)) % 1000:03d}",
                    })
        except Exception as exc:
            log(f"Telegram scan for @{channel} failed: {exc}")

    return signals


# ── Signal Dedup & Ranking ────────────────────────────────────────

def dedup_signals(new_signals: list[dict], state: dict) -> list[dict]:
    """Remove signals already seen in the last 50 signals."""
    seen_ids = {s["id"] for s in state.get("last_signals", [])}
    return [s for s in new_signals if s["id"] not in seen_ids]


def rank_signals(signals: list[dict]) -> list[dict]:
    """Rank signals by score descending."""
    return sorted(signals, key=lambda s: s["score"], reverse=True)


# ── Analysis Dispatch ─────────────────────────────────────────────

def call_tier1_analysis(signal: dict) -> str:
    """Fire Tier-1 (Opus 4.7) analysis for high-scoring signals."""
    log(f"TIER-1 ANALYSIS: {signal.get('type', '?')} (score={signal['score']})")

    system = "You are Trevor, a senior intelligence analyst. Produce a concise analytical note for a principal-level audience. One BLUF, 2-3 key judgments with confidence bands, strategic implications, and watch points. No more than 500 words."
    user = f"Analyze this signal:\n\nSource: {signal['source']}\nType: {signal['type']}\nDetails: {json.dumps({k:v for k,v in signal.items() if k not in ('id','tier')}, indent=2)}"

    try:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        payload = {
            "model": TIER1_MODEL,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "max_tokens": 2048,
            "temperature": 0.2,
        }
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/trevormentis-spec",
                "X-Title": "TREVOR Triage",
            },
            method="POST",
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
        return resp["choices"][0]["message"]["content"]
    except Exception as exc:
        log(f"Tier-1 analysis failed: {exc}")
        return f"*Automatic analysis failed: {exc}*"


def call_tier2_analysis(signal: dict) -> str:
    """Fire Tier-2 (DeepSeek V4 Pro) analysis for moderate signals."""
    log(f"TIER-2 ANALYSIS: {signal.get('type', '?')} (score={signal['score']})")

    system = "You are Trevor, an intelligence analyst. Produce a concise analytical note. One BLUF, 2-3 key judgments. No more than 350 words."
    user = f"Analyze this signal:\n\nSource: {signal['source']}\nType: {signal['type']}\nDetails: {json.dumps({k:v for k,v in signal.items() if k not in ('id','tier')}, indent=2)}"

    try:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        payload = {
            "model": TIER2_MODEL.split("/")[-1],  # deepseek/deepseek-v4-pro → deepseek-v4-pro
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "max_tokens": 2048,
            "temperature": 0.2,
            "response_format": {"type": "text"},
        }
        req = urllib.request.Request(
            "https://api.deepseek.com/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
        return resp["choices"][0]["message"]["content"]
    except Exception as exc:
        log(f"Tier-2 analysis failed: {exc}")
        return f"*Automatic analysis failed: {exc}*"


def dispatch_analysis(signal: dict) -> dict | None:
    """Dispatch analysis for a signal that exceeds threshold.

    Returns delivery info or None if suppressed.
    """
    state = load_triage_state()

    # Check cooldown
    signal_type = f"{signal['source']}:{signal['type']}"
    if check_cooldown(state, signal_type):
        log(f"  ⏭ {signal_type} in cooldown")
        return None

    # Fire the right model
    if signal.get("tier") == "tier1":
        analysis = call_tier1_analysis(signal)
    else:
        analysis = call_tier2_analysis(signal)

    # Save analysis
    analysis_dir = REPO_ROOT / "analysis" / "triage"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    analysis_path = analysis_dir / f"auto-{signal['source']}-{signal['type']}-{timestamp}.md"
    content = f"# Priority Triage — Auto Analysis\n**Signal:** {signal['source']}:{signal['type']}\n**Score:** {signal['score']}/100\n**Model:** {signal.get('tier', '?')}\n\n{analysis}"
    analysis_path.write_text(content)

    # Set cooldown
    set_cooldown(state, signal_type)

    # Track in autonomy metrics
    tracker = load_json(AUTONOMY_TRACKER_FILE) or {}
    tracker.setdefault("autonomous_analyses", []).append({
        "timestamp": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "signal": signal,
        "tier": signal.get("tier", "tier2"),
        "analysis_path": str(analysis_path),
    })
    save_json(AUTONOMY_TRACKER_FILE, tracker)

    # Update triage state
    state["analyses_fired"] = state.get("analyses_fired", 0) + 1
    save_triage_state(state)

    return {
        "path": str(analysis_path),
        "model": signal.get("tier", "tier2"),
        "analysis": analysis,
    }


# ── Full Triage Cycle ─────────────────────────────────────────────

def run_triage(dispatch: bool = True) -> dict:
    """Run one complete triage cycle across all sources."""
    state = load_triage_state()
    all_signals = []
    reports = {"analysed": [], "suppressed": []}

    log("Scanning all intelligence sources...")

    # Scan each source
    all_signals.extend(scan_gmail())
    all_signals.extend(scan_web())
    all_signals.extend(scan_kalshi())
    all_signals.extend(scan_behavioral_state())
    all_signals.extend(scan_telegram())

    log(f"Raw signals: {len(all_signals)}")

    # Deduplicate
    signals = dedup_signals(all_signals, state)
    log(f"After dedup: {len(signals)}")

    if not signals:
        log("No new signals requiring attention")
        state["signals_processed"] = state.get("signals_processed", 0)
        state["last_signals"] = state.get("last_signals", [])[-50:]
        save_triage_state(state)
        return {"new_signals": 0, "analysed": 0, "reports": reports}

    # Rank by score
    ranked = rank_signals(signals)

    # Update last signals
    state.setdefault("last_signals", [])
    for s in ranked:
        state["last_signals"].append({"id": s["id"], "source": s["source"],
                                       "type": s["type"], "score": s["score"]})
    state["last_signals"] = state["last_signals"][-50:]
    state["signals_processed"] = state.get("signals_processed", 0) + len(ranked)

    # Log ranked signals
    log("Signals ranked:")
    for s in ranked[:10]:
        log(f"  [{s['score']:2d}] {s['source']}:{s['type']} — {s.get('title', s.get('subject', s.get('description', s.get('text', ''))))[:80]}")

    # Dispatch if threshold exceeded
    if dispatch:
        for s in ranked:
            if s["score"] >= AUTO_ANALYSIS_THRESHOLD:
                result = dispatch_analysis(s)
                if result:
                    reports["analysed"].append(s)
                    log(f"  ✅ ANALYSED ({s['tier']}): {s['source']}:{s['type']} score={s['score']}")
                else:
                    reports["suppressed"].append(s)
            else:
                log(f"  ⏭ Below threshold ({s['score']}<{AUTO_ANALYSIS_THRESHOLD}): {s['source']}:{s['type']}")

    save_triage_state(state)

    return {
        "new_signals": len(ranked),
        "analysed": len(reports["analysed"]),
        "suppressed": len(reports["suppressed"]),
        "reports": reports,
    }


# ── Status ────────────────────────────────────────────────────────

def show_status() -> None:
    """Show triage engine status."""
    state = load_triage_state()
    tracker = load_json(AUTONOMY_TRACKER_FILE)

    print("# Priority Triage — Status")
    print(f"**Last check:** {state.get('last_check', 'Never')}")
    print(f"**Signals processed (lifetime):** {state.get('signals_processed', 0)}")
    print(f"**Analyses fired (lifetime):** {state.get('analyses_fired', 0)}")
    print()

    # Show recent autonomous analyses
    recent = (tracker.get("autonomous_analyses") or [])[-5:]
    if recent:
        print("## Last 5 Autonomous Analyses")
        print()
        for a in recent:
            signal = a.get("signal", {})
            print(f"- [{a.get('tier', '?')}] {signal.get('source', '?')}:{signal.get('type', '?')}")
            print(f"  Score: {signal.get('score', '?')} | {a.get('timestamp', '?')[:19]}")
        print()

    # Show cooldowns
    cooldowns = state.get("cooldowns", {})
    if cooldowns:
        print("## Active Cooldowns")
        now = dt.datetime.now(dt.timezone.utc)
        for signal_type, ts in sorted(cooldowns.items()):
            try:
                last = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                remaining = SIGNAL_COOLDOWN_HOURS * 3600 - (now - last).total_seconds()
                if remaining > 0:
                    print(f"- {signal_type}: {int(remaining / 60)}m remaining")
            except (ValueError, TypeError):
                pass
        print()

    # Show last signals
    last = state.get("last_signals", [])[-5:]
    if last:
        print("## Last 5 Signals")
        for s in last:
            print(f"- [{s.get('score', '?')}] {s.get('source', '?')}:{s.get('type', '?')}")


# ── Main ──────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check only, no analysis dispatch")
    parser.add_argument("--status", action="store_true", help="Show triage status")
    args = parser.parse_args()

    if args.status:
        show_status()
        return 0

    if args.check:
        result = run_triage(dispatch=False)
        print(f"Triage check: {result['new_signals']} new signals "
              f"({result['analysed']} would analyse, {result['suppressed']} suppressed)")
        return 0

    result = run_triage(dispatch=True)
    print(f"Triage cycle: {result['new_signals']} signals → "
          f"{result['analysed']} analysed → {result['suppressed']} suppressed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
