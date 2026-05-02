#!/usr/bin/env python3
"""Polymarket Geopolitics Monitor — implements the geopolitics trading playbook.

Runs 15-30 min cycles:
  A. Time-decay shorts on near-term overpriced "good outcome" markets
  B. Term-structure spreads on leader-removal markets
  C. Geo-macro jump detector with lag scanning
  D. Alerts with actionable signals

Usage:
  python3 analyst/polymarket_geopolitics_monitor.py          # Full scan + alerts
  python3 analyst/polymarket_geopolitics_monitor.py --alerts  # Alerts only (from cached data)
  python3 analyst/polymarket_geopolitics_monitor.py --scan    # Data pull only
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GAMMA = os.environ.get("POLYMARKET_GAMMA_HOST", "https://gamma-api.polymarket.com").rstrip("/")

WORKSPACE = Path("/home/ubuntu/.openclaw/workspace")
STATE_FILE = WORKSPACE / "analyst" / "polymarket-price-state.json"
ALERTS_FILE = WORKSPACE / "analyst" / "polymarket-alerts.md"

# ── Core geo markets ──────────────────────────────────────────────────────

GEO_SEARCHES = [
    # Iran complex
    "Iran", "Iranian", "Tehran", "Khamenei", "IRGC",
    "Strait of Hormuz", "Kharg Island", "Hormuz",
    # US-Iran
    "US invades Iran", "US-Iran peace", "US Iran",
    "uranium", "enriched",
    # Leadership
    "regime", "leadership change",
    "Xi Jinping", "Xi out", "China leadership",
    "Netanyahu", "Israeli",
    "Orbán", "Hungary",
    "Putin", "Russia",
    "Starmer", "UK",
    # Conflicts
    "ceasefire", "peace",
    "Taiwan invasion",
    "Russia-Ukraine",
    "sanctions",
    # General
    "Trump foreign", "Trump",
    "election", "elected",
    "world events",
]

# ── Helpers ───────────────────────────────────────────────────────────────

def get_json(url: str, timeout: int = 20) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "Trevor-polymarket-monitor/0.2"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"markets": {}, "last_scan": None, "alert_history": []}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def fetch_geo_markets() -> list[dict]:
    """Fetch all active geo markets from Gamma API."""
    collected = {}
    for term in GEO_SEARCHES:
        try:
            params = urllib.parse.urlencode({"limit": 50, "active": "true", "closed": "false", "q": term})
            url = f"{GAMMA}/markets?{params}"
            data = get_json(url)
            if isinstance(data, list):
                for m in data:
                    mid = str(m.get("id", ""))
                    if mid and mid not in collected:
                        collected[mid] = m
        except Exception:
            continue
    return list(collected.values())


def parse_market(m: dict) -> dict | None:
    """Normalize a market dict and extract key fields."""
    prices = m.get("outcomePrices", [])
    if not prices or len(prices) < 2:
        return None
    try:
        no_price = float(prices[1])
        yes_price = float(prices[0])
    except (ValueError, TypeError):
        return None

    end_str = m.get("endDate") or ""
    days_left = None
    if end_str:
        try:
            end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
            days_left = max(0, (end - datetime.now(timezone.utc)).days)
        except (ValueError, AttributeError):
            pass

    return {
        "id": m.get("id"),
        "slug": m.get("slug", ""),
        "question": m.get("question", ""),
        "outcomes": m.get("outcomes", [""]),
        "yes_price": round(yes_price, 4),
        "no_price": round(no_price, 4),
        "end_date": end_str,
        "days_left": days_left,
        "liquidity": float(m.get("liquidityNum", 0) or m.get("liquidity", 0)),
        "volume_24h": float(m.get("volume24hr", 0) or 0),
        "volume_total": float(m.get("volumeNum", 0) or m.get("volume", 0)),
        "spread": float(m.get("spread", 0) or 0),
        "last_price": float(m.get("lastTradePrice", 0) or 0),
        "clob_token_ids": m.get("clobTokenIds", []),
    }


# ── Screener A: Time-decay shorts ─────────────────────────────────────────

def screen_time_decay(markets: list[dict]) -> list[dict]:
    """Find markets ≤30d to expiry, >15% price, no clear progress → short candidates."""
    results = []
    for m in markets:
        days = m.get("days_left")
        price_yes = m.get("yes_price")
        if days is None or days > 30 or days < 1:
            continue
        if price_yes is None or price_yes <= 0.15:
            continue

        # Check for Iran-related = higher conviction
        q = (m.get("question") or "").lower()
        is_iran = any(kw in q for kw in ["iran", "hormuz", "kharg", "tehran", "khamenei", "regime"])
        is_leader = any(kw in q for kw in ["out before", "out by", "next leader", "re-election"])

        results.append({
            "type": "time_decay_short",
            "priority": "HIGH" if is_iran else ("MEDIUM" if is_leader else "LOW"),
            "market_slug": m["slug"],
            "question": m["question"],
            "yes_price": price_yes,
            "no_price": m["no_price"],
            "days_left": days,
            "liquidity": m["liquidity"],
            "volume_24h": m["volume_24h"],
            "action": "Short Yes (buy No)",
            "rationale": f"Yes at {price_yes:.0%} with only {days}d left",
            "target": f"No moves to {price_yes * 2:.0%}" if price_yes < 0.5 else f"No above 80%",
        })

    results.sort(key=lambda x: (
        {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[x["priority"]],
        x["yes_price"]  # Higher = more overpriced
    ), reverse=False)
    return results


# ── Screener B: Term-structure spreads ─────────────────────────────────────

def screen_term_structure(markets: list[dict]) -> list[dict]:
    """Find same-event different-date markets where spread >25pp."""
    # Group by topic
    topics = {}
    for m in markets:
        q = (m.get("question") or "").lower()
        days = m.get("days_left")
        if days is None:
            continue
        # Extract topic key
        for topic_key in ["netanyahu", "netany", "iranian regime", "iran regime",
                          "strait of hormuz", "strait normal", "hormuz normal",
                          "xi jinping", "putin", "trump"]:
            if topic_key in q:
                topics.setdefault(topic_key, []).append(m)
                break

    results = []
    for topic, ms in topics.items():
        if len(ms) < 2:
            continue
        ms.sort(key=lambda x: x.get("days_left", 999))
        for i in range(len(ms)):
            for j in range(i + 1, len(ms)):
                near = ms[i]
                far = ms[j]
                spread = far["yes_price"] - near["yes_price"]
                if spread > 0.25:
                    results.append({
                        "type": "term_structure_spread",
                        "priority": "MEDIUM",
                        "topic": topic,
                        "near_market": near["slug"],
                        "near_question": near["question"],
                        "near_price": near["yes_price"],
                        "near_days": near["days_left"],
                        "far_market": far["slug"],
                        "far_question": far["question"],
                        "far_price": far["yes_price"],
                        "far_days": far["days_left"],
                        "spread_pp": round(spread * 100, 1),
                        "action": "Short near-term leg",
                        "rationale": f"Spread {spread:.0%} > 25pp threshold with no imminent catalyst",
                        "sizing": "$30-40",
                    })
    return results


# ── Screener C: Jump detector ─────────────────────────────────────────────

def screen_jumps(markets: list[dict], state: dict) -> list[dict]:
    """Detect >10 point moves in 2h on high-volume markets."""
    results = []
    saved = state.get("markets", {})

    for m in markets:
        slug = m.get("slug", "")
        prev = saved.get(slug, {})
        prev_price = prev.get("yes_price")
        curr_price = m.get("yes_price")
        volume = m.get("volume_total", 0)
        volume_24h = m.get("volume_24h", 0)

        if prev_price is None or curr_price is None:
            continue
        if volume < 5_000_000 and volume_24h < 100_000:
            continue

        move = abs(curr_price - prev_price)
        if move >= 0.10:
            direction = "UP" if curr_price > prev_price else "DOWN"
            q = m.get("question", "")

            # Scan related markets for lag
            q_lower = q.lower()
            lagging = []
            for other in markets:
                if other["slug"] == slug:
                    continue
                oq = (other.get("question") or "").lower()
                # Check if related topic
                words = set(q_lower.split()) & set(oq.split())
                if len(words) >= 2:
                    lagging.append({
                        "slug": other["slug"],
                        "question": other["question"][:50],
                        "prev_price": saved.get(other["slug"], {}).get("yes_price"),
                        "curr_price": other["yes_price"],
                    })

            results.append({
                "type": "jump_detected",
                "priority": "HIGH",
                "market_slug": slug,
                "question": q[:80],
                "direction": direction,
                "move_pp": round(move * 100, 1),
                "prev_price": prev_price,
                "curr_price": curr_price,
                "volume": volume,
                "lagging_markets": lagging[:3],
                "action": "Scan related markets for lag",
                "sizing": "$20-30 event trade",
            })

    return results


# ── Alert formatter ────────────────────────────────────────────────────────

def format_alerts(decay: list, spreads: list, jumps: list) -> str:
    """Format screener results into a concise alert message."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"# Polymarket Geopolitics Monitor — {now}", ""]

    if decay:
        lines.append("## ⏱ Time-Decay Shorts")
        lines.append("")
        for d in decay[:5]:
            tag = "🔴" if d["priority"] == "HIGH" else "🟡"
            lines.append(f"{tag} {d['question'][:70]}")
            lines.append(f"   Yes @ {d['yes_price']:.0%} | {d['days_left']}d left | {d['action']}")
            lines.append(f"   Target: {d['target']} | Size: $20-30")
            lines.append(f"   Liq: ${d['liquidity']:,.0f} | Vol: ${d['volume_24h']:,.0f}")
            lines.append("")
        lines.append("---")
        lines.append("")

    if spreads:
        lines.append("## 📊 Term-Structure Spreads")
        lines.append("")
        for s in spreads[:3]:
            lines.append(f"📏 {s['topic'].title()}")
            lines.append(f"   Near ({s['near_days']}d): {s['near_price']:.0%}")
            lines.append(f"   Far  ({s['far_days']}d):  {s['far_price']:.0%}")
            lines.append(f"   Spread: {s['spread_pp']}pp | {s['action']} | Size: {s['sizing']}")
            lines.append("")

    if jumps:
        lines.append("## ⚡ Jump Detector")
        lines.append("")
        for j in jumps[:3]:
            tag = "🔴" if j["direction"] == "UP" else "🔵"
            lines.append(f"{tag} {j['question'][:65]}")
            lines.append(f"   Moved {j['direction']} {j['move_pp']}pp in 2h ({j['prev_price']:.0%} → {j['curr_price']:.0%})")
            if j["lagging_markets"]:
                lines.append(f"   Related lagging markets:")
                for lm in j["lagging_markets"][:2]:
                    lines.append(f"     • {lm['question']}")
            lines.append("")

    if not any([decay, spreads, jumps]):
        lines.append("No actionable signals detected.")
        lines.append("")

    lines.append("---")
    lines.append(f"_Monitor cycle: {now}_")

    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────

def main(argv: list[str]) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Polymarket Geopolitics Monitor")
    parser.add_argument("--scan", action="store_true", help="Data pull only")
    parser.add_argument("--alerts", action="store_true", help="Alerts only from cached data")
    parser.add_argument("--save", action="store_true", help="Save scan to state file")
    parser.add_argument("--cycle", action="store_true", help="Full cycle: scan + alerts + save")
    args = parser.parse_args(argv)

    state = load_state()

    if args.alerts and state.get("markets"):
        # Use cached data
        markets = list(state["markets"].values())
        decay = screen_time_decay(markets)
        spreads = screen_term_structure(markets)
        jumps = screen_jumps(markets, state)
    else:
        # Full data pull
        print(f"Fetching geo markets...", file=sys.stderr)
        raw = fetch_geo_markets()
        print(f"Found {len(raw)} raw markets", file=sys.stderr)

        markets = []
        for r in raw:
            m = parse_market(r)
            if m:
                markets.append(m)
        print(f"Parsed {len(markets)} markets", file=sys.stderr)

        decay = screen_time_decay(markets)
        spreads = screen_term_structure(markets)
        jumps = screen_jumps(markets, state)

        # Update state
        for m in markets:
            state.setdefault("markets", {})[m["slug"]] = m
        state["last_scan"] = datetime.now(timezone.utc).isoformat()

        if args.save or args.cycle:
            save_state(state)
            # Save alerts to file
            alert_text = format_alerts(decay, spreads, jumps)
            ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(ALERTS_FILE, "w") as f:
                f.write(alert_text)
            print(f"Saved to {STATE_FILE.name} + {ALERTS_FILE.name}", file=sys.stderr)

    if args.scan or args.alerts or args.cycle:
        pass  # already handled above

    # Print results
    print(f"\n{'='*60}")
    print(f"  Polymarket Geopolitics Monitor")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")
    print(f"  Markets tracked: {len(markets)}")

    print(f"\n  ⏱  Time-decay shorts: {len(decay)}")
    if decay:
        for d in decay[:3]:
            tag = "🔴" if d["priority"] == "HIGH" else "🟡"
            print(f"     {tag} {d['question'][:65]}")
            print(f"        Yes@{d['yes_price']:.0%} | {d['days_left']}d | Liq: ${d['liquidity']:,.0f}")

    print(f"\n  📊  Term-structure spreads: {len(spreads)}")
    if spreads:
        for s in spreads[:2]:
            print(f"     📏 {s['topic'].title()}: {s['spread_pp']}pp spread")

    print(f"\n  ⚡  Jumps detected: {len(jumps)}")
    if jumps:
        for j in jumps[:2]:
            print(f"     {j['direction']} {j['move_pp']}pp on {j['question'][:50]}")

    print(f"\n  {'='*60}")
    print(f"  State: {STATE_FILE}")
    print(f"  Alerts: {ALERTS_FILE}")
    print(f"  {'='*60}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
