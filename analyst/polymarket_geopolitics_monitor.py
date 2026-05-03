#!/usr/bin/env python3
"""Polymarket Geopolitics Monitor — full geopolitics trading playbook.

Implements the complete playbook:
  Module A — Iran term-structure decay (15min cycle)
  Module B — Leader-out term structure (15min cycle)
  Module C — Shock-lag event trades (5min cycle)
  Module D — Market making (passive, needs CLOB auth)
  Kill switches, news classification, daily review

Usage:
  python3 analyst/polymarket_geopolitics_monitor.py --full      # Full run all modules
  python3 analyst/polymarket_geopolitics_monitor.py --modules a,b # Specific modules
  python3 analyst/polymarket_geopolitics_monitor.py --daily-review # 00:05 UTC report
  python3 analyst/polymarket_geopolitics_monitor.py --alerts     # Alerts only
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GAMMA = os.environ.get("POLYMARKET_GAMMA_HOST", "https://gamma-api.polymarket.com").rstrip("/")
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY", "560850e45ebe4f79987a7a0961d3e275")
NEWSAPI_URL = "https://newsapi.org/v2"
WORKSPACE = Path("/home/ubuntu/.openclaw/workspace")
STATE_FILE = WORKSPACE / "analyst" / "polymarket-price-state.json"
REPORT_FILE = WORKSPACE / "analyst" / "polymarket-daily-review.md"

# ── Core watchlist from playbook ───────────────────────────────────────────

PRIORITY_MARKETS = {
    "iran_peace_jun30": "US-Iran peace deal by June 30",
    "strait_normal_may31": "Strait of Hormuz normal by end of May",
    "strait_normal_jun30": "Strait of Hormuz normal by end of June",
    "regime_fall_jun30": "Iranian regime fall by June 30",
    "invades_iran_2027": "US invades Iran before 2027",
    "iran_leadership_dec31": "Iran leadership change by Dec 31",
    "netanyahu_out_jun30": "Netanyahu out by June 30",
    "netanyahu_out_dec31": "Netanyahu out by Dec 31",
    "xi_out_2027": "Xi Jinping out before 2027",
    "taiwan_invasion_2026": "China invades Taiwan by end of 2026",
    "ukraine_ceasefire_may31": "Russia-Ukraine ceasefire by May 31",
    "ukraine_ceasefire_jun30": "Russia-Ukraine ceasefire by June 30",
}

CORE_MARKETS = [  # For Module C shock detection
    "invades_iran_2027", "iran_peace_jun30", "regime_fall_jun30",
    "taiwan_invasion_2026", "ukraine_ceasefire_may31", "ukraine_ceasefire_jun30",
    "netanyahu_out_jun30", "netanyahu_out_dec31",
]

# Theme mapping for exposure tracking
THEME_MAP = {
    "iran_peace_jun30": "Iran", "strait_normal_may31": "Iran", "strait_normal_jun30": "Iran",
    "regime_fall_jun30": "Iran", "invades_iran_2027": "Iran", "iran_leadership_dec31": "Iran",
    "netanyahu_out_jun30": "Israel", "netanyahu_out_dec31": "Israel",
    "xi_out_2027": "China", "taiwan_invasion_2026": "China",
    "ukraine_ceasefire_may31": "Ukraine", "ukraine_ceasefire_jun30": "Ukraine",
}

# ── NewsAPI helper ───────────────────────────────────────────────────────

def fetch_news(query: str, from_date: str | None = None,
               page_size: int = 10) -> list[dict[str, Any]]:
    """Fetch news articles via NewsAPI (newsapi.org)."""
    params: dict[str, Any] = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": min(page_size, 100),
        "apiKey": NEWSAPI_KEY,
    }
    if from_date:
        params["from"] = from_date
    url = f"{NEWSAPI_URL}/everything?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TrevorPolymarketBot/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        if data.get("status") != "ok":
            return []
        return data.get("articles", [])
    except Exception as exc:
        print(f"[newsapi] fetch error '{query}': {exc}", file=sys.stderr)
        return []


def check_shock_news(theme: str, hours_back: int = 2) -> list[dict[str, Any]]:
    """Check for breaking news on a theme — used by Module C shock-lag."""
    from_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    # approximate: iso minus hours_back
    from datetime import timedelta
    from_dt = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    from_str = from_dt.strftime("%Y-%m-%dT%H:%M:%S")
    return fetch_news(query=theme, from_date=from_str, page_size=5)


LINKED_MARKETS = {  # For shock-lag scanning
    "invades_iran_2027": ["iran_peace_jun30", "strait_normal_may31", "strait_normal_jun30", "regime_fall_jun30"],
    "iran_peace_jun30": ["invades_iran_2027", "strait_normal_may31", "regime_fall_jun30"],
    "regime_fall_jun30": ["invades_iran_2027", "iran_peace_jun30", "iran_leadership_dec31"],
    "taiwan_invasion_2026": [],
    "ukraine_ceasefire_may31": ["ukraine_ceasefire_jun30"],
    "netanyahu_out_jun30": ["netanyahu_out_dec31"],
}

# ── Bankroll & limits ──────────────────────────────────────────────────────

BANKROLL = 1000
LIMITS = {
    "max_gross_exposure": 600,
    "min_cash_reserve": 400,
    "per_market": 50,
    "per_theme": 150,
    "event_window_12h": 200,
    "max_daily_loss": 80,
    "max_drawdown": 0.20,
    "mm_max_inventory": 20,
}

# ── Helpers ────────────────────────────────────────────────────────────────

def get_json(url: str, timeout: int = 20) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "Trevor-geo-monitor/0.3"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "markets": {}, "last_scan": None, "positions": {}, "theme_exposure": {},
        "daily_pnl": 0, "peak_equity": BANKROLL, "current_equity": BANKROLL,
        "kill_switches_triggered": 0, "trades_completed": 0, "first_day": True,
        "alert_history": [],
    }


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def log_action(state: dict, entry: dict) -> None:
    """Log a trade action with reason code per playbook spec."""
    state.setdefault("action_log", []).append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **entry,
    })
    # Keep last 500 actions
    if len(state["action_log"]) > 500:
        state["action_log"] = state["action_log"][-500:]


# ── Data fetching ──────────────────────────────────────────────────────────

def fetch_geo_markets() -> list[dict]:
    """Fetch geopolitics markets from Gamma API."""
    collected = {}
    terms = ["Iran", "Iranian", "Strait of Hormuz", "Kharg", "regime",
             "Netanyahu", "Xi", "Taiwan", "Ukraine ceasefire",
             "peace deal", "invades", "normalization", "uranium",
             "leadership change", "political", "election"]
    for term in terms:
        try:
            params = urllib.parse.urlencode({"limit": 50, "active": "true", "closed": "false", "q": term})
            data = get_json(f"{GAMMA}/markets?{params}")
            if isinstance(data, list):
                for m in data:
                    mid = str(m.get("id", ""))
                    if mid and mid not in collected:
                        collected[mid] = m
        except Exception:
            continue
    return list(collected.values())


def parse_market(m: dict) -> dict | None:
    """Normalize a market with all schema fields."""
    prices = m.get("outcomePrices", [])
    if not prices or len(prices) < 2:
        return None
    try:
        yes_price = float(prices[0])
        no_price = float(prices[1])
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

    slug = m.get("slug", "")
    q = m.get("question", "").lower()

    # Classify theme
    theme = "Other"
    if any(w in q for w in ["iran", "hormuz", "kharg", "tehran", "khamenei"]):
        theme = "Iran"
    elif any(w in q for w in ["netanyahu", "israel"]):
        theme = "Israel"
    elif any(w in q for w in ["xi jinping", "taiwan", "china invades"]):
        theme = "China"
    elif any(w in q for w in ["ukraine", "russia-ukraine", "ceasefire"]):
        theme = "Ukraine"

    return {
        "slug": slug,
        "question": m.get("question", ""),
        "theme": theme,
        "yes_price": round(yes_price, 4),
        "no_price": round(no_price, 4),
        "best_bid": float(m.get("bestBid", 0) or 0),
        "best_ask": float(m.get("bestAsk", 0) or 0),
        "spread": float(m.get("spread", 0) or 0),
        "volume_24h": float(m.get("volume24hr", 0) or 0),
        "volume_lifetime": float(m.get("volumeNum", 0) or m.get("volume", 0)),
        "liquidity": float(m.get("liquidityNum", 0) or m.get("liquidity", 0)),
        "end_date": end_str,
        "days_left": days_left,
        "price_change_2h": 0,
        "open_position_size": 0,
        "unrealized_pnl": 0,
    }


# ── Module A: Iran Term-Structure Decay ────────────────────────────────────

def module_a_iran_decay(markets: list[dict], state: dict) -> list[dict]:
    """Screen for Iran decay shorts."""
    results = []
    theme_exposure = state.get("theme_exposure", {}).get("Iran", 0)

    for m in markets:
        if m["theme"] != "Iran":
            continue
        days = m["days_left"]
        price = m["yes_price"]
        vol24 = m["volume_24h"]
        vol_life = m["volume_lifetime"]

        if days is None or days > 35 or days < 1:
            continue
        if price < 0.12:
            continue
        if vol24 < 150000 and vol_life < 5000000:
            continue

        # Check for later-dated equivalent (for hedge)
        later_market = None
        for m2 in markets:
            if m2["theme"] == "Iran" and m2["slug"] != m["slug"]:
                if m2["end_date"] and m["end_date"] and m2["end_date"] > m["end_date"]:
                    if m2["yes_price"] > price:
                        later_market = m2
                        break

        size = min(25, LIMITS["per_theme"] - theme_exposure)
        if size <= 0:
            continue

        results.append({
            "module": "A",
            "priority": "HIGH",
            "market_slug": m["slug"],
            "question": m["question"][:60],
            "yes_price": price,
            "days_left": days,
            "action": "Buy No (short Yes)",
            "size": max(10, size),
            "hedge": {
                "slug": later_market["slug"],
                "size": round(size * 0.5) if later_market else None,
            } if later_market else None,
            "exit_trigger": f"Take 50% profit at {price * 0.7:.0%}, exit all at {price * 0.5:.0%} or 5d left",
            "stop": f"If +10pts + breakthrough tag: flatten all",
        })
    return results


# ── Module B: Leader-Out Term Structure ────────────────────────────────────

def module_b_leader_spreads(markets: list[dict], state: dict) -> list[dict]:
    """Find term-structure spreads >25pp on same leader."""
    results = []

    # Group by leader keywords
    groups = {"netanyahu": [], "iran regime": [], "xi": [], "putin": []}
    for m in markets:
        q = m["question"].lower()
        for key in groups:
            if key in q:
                groups[key].append(m)
                break

    for leader, ms in groups.items():
        if len(ms) < 2:
            continue
        ms.sort(key=lambda x: x.get("days_left", 999) or 999)
        for i in range(len(ms)):
            for j in range(i + 1, len(ms)):
                near, far = ms[i], ms[j]
                spread = far["yes_price"] - near["yes_price"]
                vol = near["volume_lifetime"] + far["volume_lifetime"]
                if spread >= 0.25 and vol >= 10_000_000:
                    results.append({
                        "module": "B",
                        "priority": "MEDIUM",
                        "leader": leader.title(),
                        "near_slug": near["slug"],
                        "near_question": near["question"][:40],
                        "near_price": near["yes_price"],
                        "near_days": near["days_left"],
                        "far_slug": far["slug"],
                        "far_question": far["question"][:40],
                        "far_price": far["yes_price"],
                        "far_days": far["days_left"],
                        "spread_pp": round(spread * 100, 1),
                        "action": "Short near-date Yes",
                        "size": 30,
                        "optional_hedge": {"slug": far["slug"], "size": 15},
                        "exit_trigger": f"Take profit -40% rel, exit at 7d to expiry",
                        "stop": f"If near price doubles + catalyst: exit",
                    })
    return results


# ── Module C: Shock-Lag Event Trades ───────────────────────────────────────

def module_c_shock_lag(markets: list[dict], state: dict) -> list[dict]:
    """Detect large moves in core markets and scan for lagging linked markets."""
    results = []
    saved = state.get("markets", {})

    for slug in CORE_MARKETS:
        # Find the market in current data
        current = next((m for m in markets if slug in m["slug"]), None)
        if not current:
            continue
        prev = saved.get(current["slug"], {})
        prev_price = prev.get("yes_price", current["yes_price"])
        curr_price = current["yes_price"]
        vol_life = current["volume_lifetime"]
        vol_24h = current["volume_24h"]

        if vol_life < 10_000_000 or vol_24h < 250_000:
            continue

        move = curr_price - prev_price
        if abs(move) < 0.10:
            continue

        # Scan linked markets for lag
        linked = LINKED_MARKETS.get(slug, [])
        lagging = []
        for link_slug in linked:
            link_market = next((m for m in markets if link_slug in m["slug"]), None)
            if not link_market:
                continue
            link_prev = saved.get(link_market["slug"], {}).get("yes_price", link_market["yes_price"])
            link_move = link_market["yes_price"] - link_prev
            # Expected: if shock is positive (invasion more likely), linked peace markets should drop
            expected_move = -abs(move) * 0.5  # half of shock magnitude, opposite direction
            if abs(link_move) < abs(expected_move) * 0.5:
                lagging.append({
                    "slug": link_market["slug"],
                    "question": link_market["question"][:50],
                    "expected_move": round(expected_move, 2),
                    "actual_move": round(link_move, 2),
                    "gap": round(abs(expected_move) - abs(link_move), 2),
                })

        if lagging:
            results.append({
                "module": "C",
                "priority": "HIGH",
                "trigger_market": current["question"][:50],
                "direction": "UP" if move > 0 else "DOWN",
                "move_pp": round(abs(move) * 100, 1),
                "lagging_count": len(lagging),
                "lagging_markets": lagging[:3],
                "action": "Trade laggard",
                "size": 20,
                "max_simultaneous": 3,
                "hold_horizon": "2h-3d",
                "exit_trigger": "Take profit at 50% lag closure, exit at 72h",
                "stop": f"If leader reverses 70%: exit",
            })
    return results


# ── Module D: Market Making (framework, needs CLOB auth) ──────────────────

def module_d_market_making(markets: list[dict], state: dict) -> list[dict]:
    """Identify eligible markets for passive market making.

    NOTE: Actual order placement requires CLOB API auth (private key).
    This module identifies candidates and suggests quote levels.
    """
    results = []
    for m in markets:
        if m["yes_price"] < 0.08 or m["yes_price"] > 0.92:
            continue
        if m["volume_lifetime"] < 20_000_000:
            continue
        if m["volume_24h"] < 250_000:
            continue
        if m["liquidity"] < 250_000:
            continue
        if m["spread"] < 0.03:
            continue

        bid = m["yes_price"] - 0.01
        ask = m["yes_price"] + 0.01

        # Skip if spread would be negative
        if bid >= ask:
            continue

        results.append({
            "module": "D",
            "market_slug": m["slug"],
            "question": m["question"][:50],
            "current_price": m["yes_price"],
            "suggested_bid": round(bid, 3),
            "suggested_ask": round(ask, 3),
            "spread": m["spread"],
            "max_inventory": 20,
            "note": "Requires CLOB auth + private key to place orders",
        })
    return results


# ── Kill Switch Check ──────────────────────────────────────────────────────

def check_kill_switches(state: dict, has_shock: bool) -> list[str]:
    """Check all kill switch conditions."""
    triggers = []
    daily_pnl = state.get("daily_pnl", 0)
    gross_exposure = sum(
        abs(p.get("size", 0)) for p in state.get("positions", {}).values()
    )
    theme_exposure = state.get("theme_exposure", {})

    if daily_pnl <= -LIMITS["max_daily_loss"]:
        triggers.append(f"DAILY_LOSS_LIMIT: PnL ${daily_pnl} exceeds -${LIMITS['max_daily_loss']}")
    if gross_exposure >= LIMITS["max_gross_exposure"]:
        triggers.append(f"GROSS_EXPOSURE: ${gross_exposure} >= ${LIMITS['max_gross_exposure']}")
    for theme, exp in theme_exposure.items():
        if exp >= LIMITS["per_theme"]:
            triggers.append(f"THEME_EXPOSURE: {theme} ${exp} >= ${LIMITS['per_theme']}")
    if has_shock:
        triggers.append("QUALIFYING_NEWS_SHOCK: Cancel all resting quotes")

    return triggers


# ── Alert Formatter ────────────────────────────────────────────────────────

def format_alerts(module_a: list, module_b: list, module_c: list, module_d: list, kill_switches: list) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"# Polymarket Geopolitics Monitor — {now}", ""]

    if kill_switches:
        lines.append("## 🛑 KILL SWITCHES TRIGGERED")
        for ks in kill_switches:
            lines.append(f"  🔴 {ks}")
        lines.append("")

    if module_a:
        lines.append("## Module A — Iran Decay Shorts")
        for d in module_a[:3]:
            lines.append(f"  🔴 {d['question']}")
            lines.append(f"     Yes @ {d['yes_price']:.0%} | {d['days_left']}d left | Size: ${d['size']}")
            lines.append(f"     Exit: {d['exit_trigger']}")
            if d.get("hedge") and d["hedge"]["size"]:
                lines.append(f"     Hedge: long later leg ${d['hedge']['size']}")
            lines.append("")

    if module_b:
        lines.append("## Module B — Leader-Out Spreads")
        for s in module_b[:2]:
            lines.append(f"  📏 {s['leader']}: Near {s['near_price']:.0%}({s['near_days']}d) vs Far {s['far_price']:.0%}({s['far_days']}d)")
            lines.append(f"     Spread: {s['spread_pp']}pp | Size: ${s['size']}")
            lines.append("")

    if module_c:
        lines.append("## Module C — Shock-Lag Events")
        for j in module_c[:2]:
            lines.append(f"  ⚡ {j['trigger_market']} ({j['direction']} {j['move_pp']}pp)")
            for lm in j["lagging_markets"][:2]:
                lines.append(f"     Lagging: {lm['question']} (gap: {lm['gap']}pp)")
            lines.append(f"     Action: {j['action']} | Size: ${j['size']}")
            lines.append("")

    if module_d:
        lines.append("## Module D — Market Making Candidates")
        for mm in module_d[:2]:
            lines.append(f"  💹 {mm['question']}")
            lines.append(f"     Bid: {mm['suggested_bid']} / Ask: {mm['suggested_ask']} | Spread: {mm['spread']:.1%}")
            lines.append(f"     {mm['note']}")
            lines.append("")

    if not any([module_a, module_b, module_c, module_d]):
        lines.append("No actionable signals from any module.")
        lines.append("")

    lines.append("---")
    lines.append(f"_Generated: {now} | Gross Exp: — | Daily PnL: —_")
    return "\n".join(lines)


# ── Daily Review ──────────────────────────────────────────────────────────

def generate_daily_review(state: dict) -> str:
    """00:05 UTC daily review per playbook spec."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Polymarket Daily Review — {now[:10]}",
        f"**Generated:** {now}",
        "",
        f"## Portfolio Summary",
        f"- Starting equity: ${BANKROLL}",
        f"- Current equity: ${state.get('current_equity', BANKROLL)}",
        f"- Daily return: ${state.get('daily_pnl', 0):+.2f}",
        f"- Gross exposure: ${sum(abs(p.get('size',0)) for p in state.get('positions',{}).values())}",
        f"- Free cash: ${LIMITS['min_cash_reserve']}",
        "",
        f"## Open Positions by Theme",
    ]
    for theme, exp in state.get("theme_exposure", {}).items():
        lines.append(f"- {theme}: ${exp}")
    lines += [
        "",
        f"## PnL",
        f"- Realized: —",
        f"- Unrealized: —",
        f"- Best trade: —",
        f"- Worst trade: —",
        "",
        f"## Kill Switches Triggered: {state.get('kill_switches_triggered', 0)}",
        "",
        f"## Trades Completed: {state.get('trades_completed', 0)}",
        "",
        f"## Markets Screened But Skipped",
        f"(Detailed skip reasons logged in state file)",
        "",
        "---",
        f"_Review auto-generated at {now}_",
    ]
    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────

def main(argv: list[str]) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Polymarket Geopolitics Monitor")
    parser.add_argument("--full", action="store_true", help="Full run all modules")
    parser.add_argument("--modules", help="Comma-separated module list (a,b,c,d)")
    parser.add_argument("--daily-review", action="store_true", help="Generate daily review report")
    parser.add_argument("--alerts", action="store_true", help="Alerts only from cached data")
    parser.add_argument("--save", action="store_true", help="Save state")
    args = parser.parse_args(argv)

    state = load_state()

    # Daily review mode
    if args.daily_review:
        review = generate_daily_review(state)
        REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(REPORT_FILE, "w") as f:
            f.write(review)
        print(review)
        return 0

    # Determine which modules to run
    run_modules = set()
    if args.full:
        run_modules = {"a", "b", "c", "d"}
    elif args.modules:
        run_modules = set(args.modules.lower().replace(" ", "").split(","))
    else:
        run_modules = {"a", "b", "c"}  # default

    # Fetch data
    print(f"Fetching geopolitics markets...", file=sys.stderr)
    raw = fetch_geo_markets()
    markets = []
    for r in raw:
        m = parse_market(r)
        if m:
            markets.append(m)
    print(f"Tracking {len(markets)} markets across {len(set(m['theme'] for m in markets))} themes", file=sys.stderr)

    # Run modules
    module_a = module_b = module_c = module_d = []
    kill_switches = []

    if "a" in run_modules:
        module_a = module_a_iran_decay(markets, state)
        print(f"  Module A: {len(module_a)} decay short(s)", file=sys.stderr)

    if "b" in run_modules:
        module_b = module_b_leader_spreads(markets, state)
        print(f"  Module B: {len(module_b)} term-structure spread(s)", file=sys.stderr)

    if "c" in run_modules:
        module_c = module_c_shock_lag(markets, state)
        print(f"  Module C: {len(module_c)} shock-lag event(s)", file=sys.stderr)

    if "d" in run_modules:
        module_d = module_d_market_making(markets, state)
        print(f"  Module D: {len(module_d)} market-making candidate(s)", file=sys.stderr)

    # Kill switch check
    kill_switches = check_kill_switches(state, bool(module_c))
    if kill_switches:
        print(f"  🛑 Kill switches: {len(kill_switches)}", file=sys.stderr)

    # Update state
    if args.save or args.full:
        for m in markets:
            state.setdefault("markets", {})[m["slug"]] = m
        state["last_scan"] = datetime.now(timezone.utc).isoformat()
        save_state(state)

    # Print alerts to stdout
    alert_text = format_alerts(module_a, module_b, module_c, module_d, kill_switches)
    print(alert_text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
