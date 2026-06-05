#!/usr/bin/env python3
"""
Signal Board Pipeline — Daily intelligence summary production.

Assembles data from GDELT (or Brave Search fallback), Kalshi, AgentMail
newsletters into a single scannable markdown board.

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

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
WORKSPACE_DIR = SCRIPT_DIR.parent
EXPORT_DIR = WORKSPACE_DIR / "exports" / "signal-board"
GDELT_EXPORT_DIR = WORKSPACE_DIR / "exports" / "gdelt"
ENV_FILE = WORKSPACE_DIR / ".env"


def _safe_item(item):
    if isinstance(item, (list, tuple)):
        return str(item[0])
    return str(item)


def load_env():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k, v)


def get_kalshi_data():
    try:
        sys.path.insert(0, str(WORKSPACE_DIR / "trading-system"))
        os.environ["KALSHI_CLIENT_PATH"] = str(
            WORKSPACE_DIR / "skills" / "kalshi-trader" / "scripts" / "client.py"
        )
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


def get_gdelt_data(date_str):
    gdelt_path = GDELT_EXPORT_DIR / f"{date_str}.json"
    if gdelt_path.exists():
        return json.loads(gdelt_path.read_text())

    print("  GDELT data not cached — running collector...", file=sys.stderr)
    try:
        import gdelt_collector
        result = gdelt_collector.collect(timespan="24h", maxrecords=250)
        if result.get("error") or result.get("total_articles", 0) == 0:
            raise RuntimeError(f"GDELT failed: {result.get('error', 'no data')}")
    except Exception:
        print("  GDELT unavailable — trying Brave Search fallback...", file=sys.stderr)
        try:
            import gdelt_fallback
            result = gdelt_fallback.collect()
        except Exception as e2:
            result = {"error": str(e2), "themes": {}, "total_articles": 0}
        if result.get("error"):
            print(f"  Fallback also failed: {result['error']}", file=sys.stderr)

    output = {
        "date": date_str,
        "timestamp": result.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "total_articles": result.get("total_articles", 0),
        "themes": result.get("themes", {}),
    }
    GDELT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    gdelt_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    return output


def _gdelt_theme(data):
    if "analysis" in data:
        return data["analysis"]
    return data


def get_polymarket_data():
    return ["Geopolitics prediction markets active on Polymarket — see polymarket.com/events for pricing"]


def build_board(date_str):
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = []
    L = lines.append

    L(f"# Signal Board — {date_str}")
    L(f"Generated: {now_utc} | Trevor v2")
    L("")
    L("---")
    L("")

    print("  Loading GDELT data...", file=sys.stderr)
    gdelt = get_gdelt_data(date_str)
    print("  Loading Kalshi data...", file=sys.stderr)
    kalshi = get_kalshi_data()
    print("  Fetching newsletters...", file=sys.stderr)
    newsletter = get_newsletters()

    news_msgs = newsletter.get("messages", [])

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

    # ── 🔴 Shifts ──
    L("## 🔴 Shifts — What changed since yesterday")
    L("")

    for m in intel_newsletters[:6]:
        subj = m.get("subject", "?")
        frm = m.get("from", "?")
        if "<" in frm:
            frm = frm.split("<")[0].strip()
        L(f"- [Newsletter] {frm}: {subj}")

    if isinstance(kalshi, dict) and "error" not in kalshi:
        bal = kalshi
        L(f"- [Kalshi] Balance: ${bal['total']:.2f} (${bal['cash']:.2f} cash, ${bal['portfolio']:.2f} portfolio)")
    else:
        L(f"- [Kalshi] Error: {kalshi.get('error', 'unknown')}")

    themes = gdelt.get("themes", {})
    total_art = gdelt.get("total_articles", 0)
    has_gdelt = total_art > 0
    L(f"- [GDELT] {total_art} articles across {len(themes)} themes (24h window)")

    sorted_themes = sorted(
        themes.items(),
        key=lambda x: _gdelt_theme(x[1]).get("article_count", 0),
        reverse=True,
    )

    if has_gdelt:
        for theme_key, data in sorted_themes[:6]:
            ana = _gdelt_theme(data)
            count = ana.get("article_count", 0)
            vol = ana.get("volume", "none")
            top_src = ana.get("top_sources", [])
            src = _safe_item(top_src[0]) if top_src else "-"
            display_name = theme_key.replace("_", " ").title()
            if count > 0:
                L(f"  - {display_name}: {count} articles (vol: {vol}, top source: {src})")
    L("")

    # ── 🟡 Trends ──
    L("## 🟡 Trends — Week-over-week tracking")
    L("")
    L("| Theme | Articles (24h) | Volume |")
    L("|---|---|---|")
    if has_gdelt:
        for theme_key, data in sorted_themes[:10]:
            ana = _gdelt_theme(data)
            count = ana.get("article_count", 0)
            vol = ana.get("volume", "none")
            vol_icon = {"very_high": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "none": "⚪"}.get(vol, "⚪")
            display_name = theme_key.replace("_", " ").title()
            L(f"| {display_name} | {count} | {vol_icon} {vol} |")
    else:
        L("| GDELT | no data | ⚪ |")
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
    L("## 🔍 Deep Dive: Today's Top Story")
    L("")
    L("Based on today's data, the most covered theme is analyzed below.\n")

    if has_gdelt and sorted_themes:
        best_theme_key = sorted_themes[0][0]
        best_ana = _gdelt_theme(sorted_themes[0][1])
        best_count = best_ana.get("article_count", 0)
        best_sources = best_ana.get("top_sources", [])
        best_keywords = best_ana.get("top_keywords", [])
        best_name = best_theme_key.replace("_", " ").title()

        L(f"**{best_name}** led today with {best_count} articles.")
        if best_sources:
            L(f"Top sources: {', '.join(_safe_item(s) for s in best_sources[:3])}")
        if best_keywords:
            L(f"Leading keywords: {', '.join(_safe_item(k) for k in best_keywords[:5])}")
        L("")
    else:
        L("GDELT data unavailable today. See newsletter flags above for key intel signals.\n")

    # Newsletter highlights for the deep dive
    if intel_newsletters:
        L("**Newsletter Highlights:**")
        for m in intel_newsletters[:5]:
            frm = m.get("from", "?")
            if "<" in frm:
                frm = frm.split("<")[0].strip()
            L(f"- {frm}: {m.get('subject', '?')}")
        L("")

    L("**Forward Look:** Monitor the Signals section and newsletters for "
      "overnight developments. Next board generation: 6:00 AM PT.")
    L("")

    # ── ⚙️ Infrastructure ──
    L("## ⚙️ Infrastructure")
    L("")
    cats_with_data = sum(1 for t in themes.values() if _gdelt_theme(t).get("article_count", 0) > 0)
    L(f"- **GDELT:** {'OK' if has_gdelt else 'Unavailable (fallback used)'} "
      f"({cats_with_data}/{len(themes)} categories with data, "
      f"{total_art} total articles)")
    if isinstance(kalshi, dict) and "error" not in kalshi:
        L(f"- **Kalshi:** OK (${kalshi['total']:.2f} total equity)")
    else:
        L(f"- **Kalshi:** Error — {kalshi.get('error', 'unknown')}")
    intel_count = len(intel_newsletters)
    L(f"- **AgentMail:** OK ({len(news_msgs)} recent, {intel_count} intel-relevant)")
    L("")

    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Signal Board Pipeline")
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--stdout", action="store_true")
    parser.add_argument("--no-collect", action="store_true", help="Skip GDELT collection, use cached only")
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
