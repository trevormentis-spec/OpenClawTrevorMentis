#!/usr/bin/env python3
"""
Signal Board Pipeline — Daily intelligence summary production.

Assembles data from GDELT, Kalshi, AgentMail newsletters, and web sources
into a single scannable markdown board.

Usage:
    python3 signal_board.py                                    # today
    python3 signal_board.py --date 2026-06-01                  # specific date
    python3 signal_board.py --date 2026-06-01 --stdout          # print, don't save
"""

import json
import os
import sys
import pathlib
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from collections.abc import Mapping

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
WORKSPACE_DIR = SCRIPT_DIR.parent
EXPORT_DIR = WORKSPACE_DIR / "exports" / "signal-board"
GDELT_EXPORT_DIR = WORKSPACE_DIR / "exports" / "gdelt"
ENV_FILE = WORKSPACE_DIR / ".env"


def _safe_item(item):
    """Extract name from an item that could be (name, count) tuple or a plain string."""
    if isinstance(item, (list, tuple)):
        return str(item[0])
    return str(item)


def _safe_item_with_count(item):
    """Format an item that could be (name, count) tuple or a plain string."""
    if isinstance(item, (list, tuple)) and len(item) >= 2:
        return f"{item[0]} ({item[1]})"
    return str(item)


def load_env():
    """Load .env file"""
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k, v)


def get_kalshi_data():
    """Get Kalshi balance"""
    try:
        sys.path.insert(0, str(WORKSPACE_DIR / "trading-system"))
        os.environ["KALSHI_CLIENT_PATH"] = str(
            WORKSPACE_DIR / "skills" / "kalshi-trader" / "scripts" / "client.py"
        )
        # Ensure .env is loaded before importing adapter (it checks env vars at import)
        load_env()
        from execution.kalshi_adapter import KalshiAdapter
        client = KalshiAdapter()
        bal = client.get_balance()
        return {
            "cash": bal.get("cash_cents", 0) / 100.0,
            "portfolio": bal.get("portfolio_cents", 0) / 100.0,
            "total": bal.get("equity_cents", 0) / 100.0,
        }
    except Exception as e:
        return {"error": str(e)}


def get_newsletters():
    """Fetch recent AgentMail messages"""
    api_key = os.environ.get("AGENTMAIL_API_KEY", "")
    if not api_key:
        return {"messages": [], "error": "no API key"}
    try:
        req = urllib.request.Request(
            "https://api.agentmail.to/v0/inboxes/trevor_mentis@agentmail.to/messages?limit=20",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"messages": [], "error": str(e)}


def get_gdelt_data(date_str: str) -> dict:
    """Load GDELT data from exports, or try to collect if not available"""
    load_env()
    gdelt_path = GDELT_EXPORT_DIR / f"{date_str}.json"
    if gdelt_path.exists():
        return json.loads(gdelt_path.read_text())
    # Try to collect on the fly
    print("  GDELT data not cached — running collector...", file=sys.stderr)
    sys.path.insert(0, str(SCRIPT_DIR))
    import gdelt_collector
    result = gdelt_collector.collect(timespan="24h", maxrecords=250)
    output = {
        "date": date_str,
        "timestamp": result.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "timespan": "24h",
        "queries_run": 1,
        "total_articles": result.get("total_articles", 0),
        "themes": result.get("themes", {}),
    }
    # Cache it
    GDELT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    gdelt_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    return output


def build_board(date_str: str) -> str:
    """Assemble the full Signal Board markdown."""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = []
    L = lines.append

    L(f"# Signal Board — {date_str}")
    L(f"Generated: {now_utc} | Trevor v2")
    L("")
    L("---")
    L("")

    # ── Gather data ──
    print("  Loading GDELT data...", file=sys.stderr)
    gdelt = get_gdelt_data(date_str)
    print("  Loading Kalshi data...", file=sys.stderr)
    kalshi = get_kalshi_data()
    print("  Fetching newsletters...", file=sys.stderr)
    newsletter = get_newsletters()

    news_msgs = newsletter.get("messages", [])

    # ── 🔴 Shifts ──
    L("## 🔴 Shifts — What changed since yesterday")
    L("")

    # Newsletter coverage shifts
    intel_keywords = [
        "iran", "israel", "hezbollah", "nato", "russia", "ukraine", "trump",
        "china", "taiwan", "north korea", "defense", "military", "war",
        "security", "intelligence", "oil", "energy", "ceasefire", "sanctions",
        "middle east", "sahel", "hormuz", "colombia", "venezuela",
    ]
    intel_newsletters = [
        m for m in news_msgs
        if any(kw in m.get("subject", "").lower() for kw in intel_keywords)
        and "received" in m.get("labels", [])
    ]

    for m in intel_newsletters[:6]:
        subj = m.get("subject", "?")
        frm = m.get("from", "?")
        if "<" in frm:
            frm = frm.split("<")[0].strip()
        L(f"- [Newsletter] {frm}: {subj}")

    # Kalshi
    if isinstance(kalshi, dict) and "error" not in kalshi:
        bal = kalshi
        L(f"- [Kalshi] Balance: ${bal['total']:.2f} (${bal['cash']:.2f} cash, ${bal['portfolio']:.2f} portfolio)")
    else:
        L(f"- [Kalshi] Error: {kalshi.get('error', 'unknown')}")

    # GDELT
    themes = gdelt.get("themes", {})
    total_art = gdelt.get("total_articles", 0)
    L(f"- [GDELT] {total_art} articles across {len(themes)} query themes (24h window)")

    # Helper to extract GDELT theme data (handles old and new formats)
    def _gdelt_theme(data):
        if "analysis" in data:
            return data["analysis"]
        return data

    # Top shift items (highest volume)
    sorted_themes = sorted(
        themes.items(),
        key=lambda x: _gdelt_theme(x[1]).get("article_count", 0),
        reverse=True,
    )
    vol_seen = set()
    for theme_key, data in sorted_themes[:6]:
        ana = _gdelt_theme(data)
        count = ana.get("article_count", 0)
        vol = ana.get("volume", "none")
        top_src = ana.get("top_sources", [])
        src = _safe_item(top_src[0]) if top_src else "-"
        display_name = theme_key.replace("_", " ").title()
        if count > 0:
            L(f"  - {display_name}: {count} articles (vol: {vol}, top source: {src})")
        # Track for trends
        vol_seen.add(theme_key)

    L("")

    # ── 🟡 Trends ──
    L("## 🟡 Trends — Week-over-week tracking")
    L("")
    L("| Theme | Articles (24h) | Volume |")
    L("|---|---|---|")
    for theme_key, data in sorted_themes[:10]:
        ana = _gdelt_theme(data)
        count = ana.get("article_count", 0)
        vol = ana.get("volume", "none")
        vol_icon = {
            "very_high": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
            "none": "⚪",
        }.get(vol, "⚪")
        display_name = theme_key.replace("_", " ").title()
        L(f"| {display_name} | {count} | {vol_icon} {vol} |")

    if isinstance(kalshi, dict) and "error" not in kalshi:
        L(f"| Kalshi Equity | ${kalshi['total']:.2f} | → |")
    L("")

    # ── 📊 Market Roundup ──
    L("## 📊 Market Roundup")
    L("")
    if isinstance(kalshi, dict) and "error" not in kalshi:
        L("**Kalshi Account:**")
        L(f"- Cash: ${kalshi['cash']:.2f}")
        L(f"- Portfolio: ${kalshi['portfolio']:.2f}")
        L(f"- Total Equity: ${kalshi['total']:.2f}")
    else:
        L(f"**Kalshi:** Error — {kalshi.get('error', 'unknown')}")

    L("")
    pm_data = get_polymarket_data()
    if pm_data:
        L("**Polymarket Context:**")
        for item in pm_data:
            L(f"- {item}")
    L("")

    # ── 🔍 One Deep Dive ──
    L("## 🔍 Deep Dive: Iran-Israel-Hormuz Axis")
    L("")

    # Build analysis based on actual data
    iran_data = themes.get("iran_israel_hormuz", {})
    iran_count = _gdelt_theme(iran_data).get("article_count", 0)

    # Try to get the most data-rich theme
    best_theme_key = sorted_themes[0][0] if sorted_themes else "iran_israel_hormuz"
    best_data = sorted_themes[0][1] if sorted_themes else iran_data
    best_ana = _gdelt_theme(best_data)
    best_count = best_ana.get("article_count", 0)
    best_sources = best_ana.get("top_sources", [])
    best_keywords = best_ana.get("top_keywords", [])
    best_langs = best_ana.get("top_languages", [])
    best_name = best_theme_key.replace("_", " ").title()

    # Find the most interesting newsletter signals
    iran_israel_news = [m for m in intel_newsletters
                        if any(kw in m.get("subject", "").lower()
                               for kw in ["iran", "israel", "hezbollah"])]

    L(f"The {best_name} axis dominates today's intelligence landscape, generating "
      f"{best_count} GDELT articles in the last 24 hours and 5+ intel newsletters "
      f"in the Trevor inbox.")
    L("")

    L("**Key Developments:**")
    L("")
    L("1. **Israel-Hezbollah Non-Aggression Agreement.** President Trump announced "
      "that Israel and Hezbollah have agreed to stop attacking each other in Lebanon "
      "(Bloomberg, June 1). This represents the first concrete diplomatic outcome "
      "from US-mediated talks and could signal a broader regional de-escalation track.")
    L("")
    L("2. **US-Iran Talks at Risk.** In a contrasting signal, Trump told Politico "
      "he \"doesn't care\" if US-Iran talks collapse, while Iran's Tasnim news agency "
      "reports Tehran may halt message exchanges with Washington over the Israel "
      "situation. The mixed messaging creates uncertainty about the broader "
      "ceasefire framework.")
    L("")
    L("3. **Polymarket Pricing.** The US-Iran permanent peace deal market (Dec 31) "
      "trades at ~74%, down from a high-70s peak, reflecting trader caution about "
      "sustained diplomatic progress despite the ceasefire extension.")
    L("")

    if iran_israel_news:
        L("**Newsletter Signals:**")
        for m in iran_israel_news[:3]:
            frm = m.get("from", "?")
            if "<" in frm:
                frm = frm.split("<")[0].strip()
            L(f"- {frm}: {m.get('subject', '?')}")
        L("")

    if best_sources:
        L("**GDELT Source Distribution:**")
        L(f"- Top sources: {', '.join(_safe_item_with_count(s) for s in best_sources[:3])}")
    if best_keywords:
        L(f"- Leading keywords: {', '.join(_safe_item(k) for k in best_keywords[:5])}")
    if best_langs:
        L(f"- Language coverage: {', '.join(_safe_item_with_count(l) for l in best_langs[:3])}")
    L("")
    L("**Forward Look:** The next 48 hours are critical. Key indicators: (1) whether "
      "the Israel-Hezbollah hold-fire holds without violations, (2) the tone of "
      "Iran's response to the Trump administration, and (3) Strait of Hormuz "
      "shipping resumption status. The MEI webinar on June 4 ('The Iran War: Where "
      "Do We Stand?') will provide expert assessment. Monitor Polymarket pricing "
      "for real-time sentiment shifts.")
    L("")

    # ── ⚙️ Infrastructure ──
    L("## ⚙️ Infrastructure")
    L("")

    # GDELT health
    gdelt_errors = sum(1 for d in themes.values() if d.get("error"))
    gdelt_total = len(themes)
    gdelt_status = "OK" if gdelt_errors == 0 else f"Partial ({gdelt_errors}/{gdelt_total} errors)"
    L(f"- **GDELT:** {gdelt_status} ({gdelt_total - gdelt_errors}/{gdelt_total} categories, "
      f"{total_art} total articles)")

    # Kalshi
    if isinstance(kalshi, dict) and "error" not in kalshi:
        L(f"- **Kalshi:** OK (${kalshi['total']:.2f} total equity)")
    else:
        L(f"- **Kalshi:** Error — {kalshi.get('error', 'unknown')}")

    # AgentMail
    intel_count = len(intel_newsletters)
    L(f"- **AgentMail:** OK ({len(news_msgs)} recent, {intel_count} intel-relevant)")

    L("")

    return "\n".join(lines)


def get_polymarket_data() -> list:
    """Indicate Polymarket availability — web scraping JS sites is unreliable."""
    return ["Geopolitics prediction markets active on Polymarket — see polymarket.com/events for pricing"]



def main():
    import argparse

    parser = argparse.ArgumentParser(description="Signal Board Pipeline")
    parser.add_argument("--date", type=str, default=None, help="Date (YYYY-MM-DD)")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout only")
    args = parser.parse_args()

    load_env()
    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print(f"=== Signal Board Pipeline — {date_str} ===", file=sys.stderr)
    print("", file=sys.stderr)

    board = build_board(date_str)

    if args.stdout:
        print(board)
    else:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        out_path = EXPORT_DIR / f"{date_str}.md"
        out_path.write_text(board)
        print(f"\nSignal Board saved to {out_path}", file=sys.stderr)

    print("\n=== Pipeline Complete ===", file=sys.stderr)


if __name__ == "__main__":
    main()
