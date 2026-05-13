#!/usr/bin/env python3
"""
Product Suggestion Engine — from daily GSIB analysis.

After each daily brief, analyzes the day's intelligence themes and
suggests new security/intelligence products Trevor could build.
Each suggestion includes a rationale, target audience, and a sample
of what the product would look like.

Produces: analysis/product-suggestions/{date}.md
Integrated into: daily email delivery

Usage:
    python3 scripts/product_suggestions.py --date 2026-05-13
    python3 scripts/product_suggestions.py --last-7              # Analyze week trend
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BRIEFINGS_DIR = pathlib.Path.home() / "trevor-briefings"
SUGGESTIONS_DIR = REPO_ROOT / "analysis" / "product-suggestions"


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[products {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, Exception):
            return {}
    return {}


def get_today_themes(date_str: str) -> list[dict]:
    """Extract the dominant intelligence themes from today's GSIB."""
    themes = []
    for base in [BRIEFINGS_DIR, REPO_ROOT / "trevor-briefings"]:
        exec_path = base / date_str / "analysis" / "exec_summary.json"
        if exec_path.exists():
            exec_data = load_json(exec_path)
            bluf = exec_data.get("bluf", "")
            judgments = exec_data.get("five_judgments", [])
            themes.append({"source": "exec_summary", "bluf": bluf, "judgments": judgments})
            break

    # Get regional narratives for deeper theme extraction
    for region in ["europe", "asia", "middle_east", "north_america",
                    "south_central_america", "global_finance"]:
        for base in [BRIEFINGS_DIR, REPO_ROOT / "trevor-briefings"]:
            rpath = base / date_str / "analysis" / f"{region}.json"
            if rpath.exists():
                rdata = load_json(rpath)
                narrative = rdata.get("narrative", "")
                judgments = rdata.get("key_judgments", [])
                themes.append({"source": region, "narrative": narrative[:500], "judgments": judgments})
                break

    return themes


def suggest_products(themes: list[dict], date_str: str) -> list[dict]:
    """Generate product suggestions from today's intelligence themes."""
    suggestions = []

    # Extract key topics from themes
    all_text = " ".join([
        t.get("bluf", "") + " " + " ".join(j.get("statement", "") for j in t.get("judgments", []))
        for t in themes
    ]).lower()

    all_narratives = " ".join([t.get("narrative", "") for t in themes]).lower()

    # Detect dominant themes
    has_hormuz = "hormuz" in all_text or "strait" in all_text or "iran" in all_text
    has_russia_ukraine = "russia" in all_text or "ukraine" in all_text
    has_china = "china" in all_text or "taiwan" in all_text or "beijing" in all_text
    has_energy = "oil" in all_text or "brent" in all_text or "energy" in all_text or "crude" in all_text
    has_middle_east = "middle east" in all_text or "israel" in all_text or "gaza" in all_text or "iran" in all_text
    has_elections = "election" in all_text or "vote" in all_text
    has_cyber = "cyber" in all_text or "ransomware" in all_text or "hack" in all_text

    # ---- Product 1: Hormuz Crisis Daily Brief (if Hormuz is active) ----
    if has_hormuz:
        suggestions.append({
            "product": "Strait of Hormuz — Daily Crisis Monitor",
            "rationale": "Hormuz remains the dominant geopolitical risk. A dedicated daily product "
                         "covering maritime traffic, IRGC activity, insurance markets, and energy "
                         "price impacts would serve maritime insurers, oil traders, and naval analysts.",
            "target_audience": "Maritime insurers, oil traders, naval intelligence, energy ministries",
            "pricing": "$49/month or $499/year",
            "sample": (
                "**STRAIT OF HORMUZ — DAILY CRISIS MONITOR**\n"
                f"*{date_str}*\n\n"
                "**SITUATION:** [From today's GSIB] Iran continues to enforce vessel inspection "
                "regime. 12 commercial vessels inspected in last 24h. 3 detained for 'customs violations.'\n\n"
                "**TRANSIT METRICS:**\n"
                "- Vessels transiting: 17 (vs 35-40 pre-crisis baseline)\n"
                "- Insurance premium (war risk): +450% vs Jan 2026\n"
                "- Tanker waiting time: avg 8.2 hours at inspection point\n\n"
                "**KEY JUDGMENTS:**\n"
                "- 60%: Iran will expand inspection zone within 7 days\n"
                "- 35%: At least one 'incident' (boarding/detention) in next 48h\n\n"
                "**MARKET SIGNALS:**\n"
                "- Brent/WTI spread widening: signaling supply anxiety\n"
                "- VLCC rates: +12% in 24h\n"
            ),
        })

    # ---- Product 2: Energy War Room (if energy is active) ----
    if has_energy:
        suggestions.append({
            "product": "Energy War Room — Daily Geopolitical Risk to Oil & Gas",
            "rationale": "Energy markets are being driven by geopolitics more than fundamentals. "
                         "A product that translates geopolitical events into energy price "
                         "implications would serve traders and energy executives.",
            "target_audience": "Energy traders, hedge funds, oil & gas executives, government energy advisors",
            "pricing": "$99/month or $999/year",
            "sample": (
                "**ENERGY WAR ROOM**\n"
                f"*{date_str}*\n\n"
                "**GEOPOLITICAL RISK TO BRENT:**\n"
                "- Hormuz disruption: +$12-18/bbl risk premium\n"
                "- Russia strike package: +$2-4/bbl (transit risk via Black Sea)\n"
                "- China-Taiwan tensions: +$1-3/bbl\n\n"
                "**CURRENT BRENT: ~$105/bbl**\n"
                "- Bull case (Hormuz escalation): $120-130 within 7 days\n"
                "- Bear case (ceasefire/de-escalation): $85-95 within 14 days\n\n"
                "**TRADE SIGNAL:** Long Brent. Stop loss: $95. Target: $125.\n"
            ),
        })

    # ---- Product 3: Leader Risk Profiles (if leadership/elections active) ----
    if has_elections or has_middle_east:
        suggestions.append({
            "product": "Leader Risk Profiles — LDAP-7 Political Survival Tracking",
            "rationale": "Leadership instability is a first-order intelligence driver. A daily "
                         "tracking product using the LDAP-7 framework for key world leaders "
                         "would serve political risk analysts and hedge funds.",
            "target_audience": "Political risk analysts, hedge funds, foreign ministries, journalism",
            "pricing": "$79/month or $799/year",
            "sample": (
                "**LEADER RISK PROFILES — DAILY TRACKER**\n"
                f"*{date_str}*\n\n"
                "**KEIR STARMER (UK) — Political Survival: 65%**\n"
                "- LDAP-7 Profile: Institutional Cooperative\n"
                "- Key risk: Economic headwinds + internal party divides\n"
                "- Key strength: No viable challenger, opposition in disarray\n\n"
                "**BENJAMIN NETANYAHU (ISRAEL) — Political Survival: 55%**\n"
                "- LDAP-7 Profile: Tactical Competitive\n"
                "- Key risk: War fatigue, coalition fragility\n"
                "- Key strength: Security credentials, no election pressure\n\n"
                "**MASOUD PEZESHKIAN (IRAN) — Political Survival: 40%**\n"
                "- LDAP-7 Profile: Institutional Cooperative (constrained)\n"
                "- Key risk: IRGC dominance, economic collapse\n"
                "- Key strength: Reformist mandate (nominal)\n"
            ),
        })

    # ---- Product 4: Geopolitical Trading Signals (if multiple themes active) ----
    if has_hormuz and has_energy and has_china:
        suggestions.append({
            "product": "Geopolitical Alpha — Daily Trading Signals from Intelligence",
            "rationale": "The convergence of Hormuz, energy markets, and great-power competition "
                         "creates tradable geopolitical signals. A daily product bridging "
                         "intelligence analysis to portfolio positioning.",
            "target_audience": "Hedge funds, family offices, macro traders",
            "pricing": "$199/month or $1,999/year",
            "sample": (
                "**GEOPOLITICAL ALPHA — 2026-05-13**\n\n"
                "**SIGNAL 1: LONG BRENT**\n"
                "Conviction: 75%\n"
                "Thesis: Hormuz disruption + Russia strikes tighten supply\n"
                "Entry: $105 | Stop: $95 | Target: $125\n"
                "Timeframe: 7-14 days\n\n"
                "**SIGNAL 2: LONG GOLD**\n"
                "Conviction: 60%\n"
                "Thesis: De-dollarization + geopolitical uncertainty\n"
                "Entry: $2,350 | Stop: $2,250 | Target: $2,500\n"
                "Timeframe: 14-30 days\n\n"
                "**SIGNAL 3: SHORT EMERGING MARKETS (EEM)**\n"
                "Conviction: 55%\n"
                "Thesis: Energy shock disproportionately hits EM importers\n"
            ),
        })

    # ---- Product 5: Thematic deep-dive (always offer) ----
    suggestions.append({
        "product": "Custom Thematic Deep-Dive",
        "rationale": "Today's brief covered multiple regions at survey depth. A single-theme "
                     "deep-dive (e.g., 'Iran's Toll System Economics' or 'Russia's Post-Truce "
                     "Strategy') would provide actionable detail the daily brief can't.",
        "target_audience": "Existing GSIB subscribers (upsell)",
        "pricing": "$499 per report or $2,999/year for weekly deep-dives",
        "sample": None,  # Theme-specific
    })

    return suggestions


def generate_report(date_str: str, suggestions: list[dict]) -> str:
    """Generate a formatted markdown product suggestion report."""
    lines = []
    lines.append(f"# Product Suggestions — {date_str}")
    lines.append(f"**Generated:** {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC")
    lines.append(f"**Source:** Daily GSIB analysis")
    lines.append("")

    if not suggestions:
        lines.append("No new product suggestions generated from today's brief.")
        return "\n".join(lines)

    for s in suggestions:
        lines.append(f"## {s['product']}")
        lines.append(f"**Target:** {s['target_audience']}")
        lines.append(f"**Pricing:** {s['pricing']}")
        lines.append("")
        lines.append(s['rationale'])
        lines.append("")
        if s.get('sample'):
            lines.append("### Sample")
            lines.append("")
            lines.append(s['sample'])
            lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="", help="Date in YYYY-MM-DD format")
    args = parser.parse_args()

    date_str = args.date or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")

    themes = get_today_themes(date_str)
    if not themes:
        log(f"No GSIB analysis found for {date_str}")
        print(f"No GSIB data for {date_str} — run the daily brief first.")
        return 1

    suggestions = suggest_products(themes, date_str)
    report = generate_report(date_str, suggestions)

    SUGGESTIONS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = SUGGESTIONS_DIR / f"{date_str}.md"
    report_path.write_text(report)
    log(f"Product suggestions saved: {report_path}")

    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
