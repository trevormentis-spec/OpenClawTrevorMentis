#!/usr/bin/env python3
"""Prediction Market Intelligence Scanner — Daily divergence scan.

Combines Kalshi + Polymarket data with OSINT source monitoring.
Routes analytical composition through Opus 4.7 via analyst/llm_clients/.

Usage:
    python3 scripts/pm_scanner.py                    # print to stdout
    python3 scripts/pm_scanner.py --send              # email via AgentMail
    python3 scripts/pm_scanner.py --save              # save to exports/
"""
from __future__ import annotations

import json, os, pathlib, subprocess, sys, urllib.request

from analyst.llm_clients.openrouter_client import OpenRouterClient
from _present_env import load_env

WORKSPACE = pathlib.Path("/home/ubuntu/.openclaw/workspace")
KALSHI_SCRIPT = WORKSPACE / "scripts" / "kalshi_scanner.py"
GAMMA_API = "https://gamma-api.polymarket.com"

# Geopolitics keywords for Polymarket filtering
GEO_KW = ["iran", "nuclear", "ceasefire", "ukraine", "russia", "nato",
          "taiwan", "china", "oil", "crude", "sanction",
          "president", "fed", "rate", "inflation", "tariff",
          "election", "congress", "senate", "default", "debt",
          "putin", "zelenskyy", "trump", "impeach", "resign",
          "gaza", "israel", "hormuz", "strait", "tariff",
          "balance of power", "midterm"]

# Key Substack/newsletter sources for prediction market analysis
SOURCES = [
    ("Substack", "Under the Market Lens", "https://underthemarketlens.substack.com"),
    ("Substack", "Asterisk Magazine", "https://asteriskmag.substack.com"),
    ("Substack", "Future Forecasters", "https://futureforecasters.substack.com"),
    ("Substack", "Capital Spectator", "https://capitalspectator.substack.com"),
    ("Substack", "Gold & Geopolitics", "https://no01.substack.com"),
    ("Blog", "AgentBets", "https://agentbets.ai"),
    ("Think tank", "ISW Iran Update", "https://understandingwar.org"),
    ("Think tank", "ECFR Iran Monitor", "https://ecfr.eu/special/iran-nuclear-monitor"),
]


def fetch_polymarket_data() -> list[dict]:
    """Fetch geopolitics-relevant Polymarket contracts via Gamma API."""
    results = []
    for offset in [0, 100, 200, 300]:
        url = f"{GAMMA_API}/markets?limit=100&offset={offset}&closed=false"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Trevor/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read())
            if not data:
                break
            for m in data:
                q = (m.get("question", "") + " " + m.get("title", "")).lower()
                for kw in GEO_KW:
                    if kw in q:
                        prices = m.get("outcomePrices", "[0,0]")
                        if isinstance(prices, str):
                            try: prices = json.loads(prices)
                            except: prices = [0, 0]
                        yes = float(prices[0]) * 100 if prices else 0
                        vol = float(m.get("volume", 0))
                        if vol > 500:
                            results.append({
                                "question": m.get("question", "?"),
                                "yes_pct": round(yes, 1),
                                "volume_usd": round(vol, 0),
                                "end_date": str(m.get("endDate", "?"))[:10],
                            })
                        break
        except:
            break
    return results


def fetch_kalshi_data() -> str:
    """Run the existing Kalshi scanner and return its output."""
    env = load_env()
    r = subprocess.run(["python3", str(KALSHI_SCRIPT)], capture_output=True,
                       text=True, timeout=60, env=env)
    return r.stdout


def fetch_source_highlights() -> list[str]:
    """Fetch recent posts from monitored sources."""
    highlights = []
    for src_type, name, url in SOURCES[:5]:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Trevor/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="replace")[:3000]
            highlights.append(f"[{src_type}] {name}: {url}")
        except:
            highlights.append(f"[{src_type}] {name}: (unreachable)")
    return highlights


def produce_report(kalshi_text: str, poly_data: list[dict],
                   source_highlights: list[str]) -> str:
    """Use Opus 4.7 to compose a daily prediction market divergence scan."""
    client = OpenRouterClient()

    polymarket_summary = "\n".join(
        f"  {m['question'][:55]:55} | {m['yes_pct']:5.1f}¢ | Vol: ${m['volume_usd']:>10,.0f} | Exp: {m['end_date']}"
        for m in sorted(poly_data, key=lambda x: x['volume_usd'], reverse=True)[:20]
    ) if poly_data else "  (Polymarket data unavailable)"

    sources_text = "\n".join(source_highlights)

    prompt = f"""You are a senior intelligence analyst producing a daily prediction market divergence scan.

Today's date: 20 May 2026

TASK: Analyze the following data and produce a concise report that:
1. Flags any contracts where market pricing moved significantly
2. Identifies divergence between Kalshi and Polymarket pricing (if comparable contracts exist)
3. Notes any prediction market pricing that contradicts recent OSINT/news
4. Highlights monitoring priorities for the next 24-48 hours
5. Rates overall market signal quality

========================================================================
KALSHI DATA (Geopolitics/Economics markets):
========================================================================
{kalshi_text[:3000]}

========================================================================
POLYMARKET DATA (Geopolitics/Economics markets by volume):
========================================================================
{polymarket_summary}

========================================================================
MONITORED SOURCES:
========================================================================
{sources_text}

========================================================================
OUTPUT FORMAT:
Write in plain text. Include sections for: Executive Summary, Key Divergences,
Market-by-Market Analysis, Source Monitor, Monitoring Priorities.
Use Sherman Kent probability language for any judgments.
This is a paying client. Be specific, be honest about uncertainty."""

    result = client.complete(
        model="anthropic/claude-opus-4.7",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=3000,
        temperature=0.3,
    )
    return result.get("content", "")


def self_assess(report: str) -> str:
    """Ask Opus 4.7 to honestly evaluate the product quality."""
    client = OpenRouterClient()
    result = client.complete(
        model="anthropic/claude-opus-4.7",
        messages=[{"role": "user", "content": f"""You are a quality assurance reviewer. Assess this intelligence product honestly.

PRODUCT: Daily Prediction Market Divergence Scan

REPORT:
{report[:2000]}

Evaluate on a scale of 1-10 for:
1. Data completeness — does it cover the right markets?
2. Analytical depth — does it add value beyond raw data?
3. Actionability — can a reader act on this?
4. Source usage — are sources properly cited?
5. Calibration — are judgments properly bounded?

Then give an overall verdict: PASS / FAIL / PASS WITH RESERVATIONS

Be brutally honest. This is a v1 product and needs real criticism."""}],
        max_tokens=1500, temperature=0.3,
    )
    return result.get("content", "")


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--send", action="store_true", help="Send via AgentMail")
    p.add_argument("--save", action="store_true", help="Save to exports/")
    args = p.parse_args()

    print("=== Prediction Market Scanner ===")
    print("Fetching Kalshi data...")
    kalshi = fetch_kalshi_data()
    print(f"  {len(kalshi)} chars")

    print("Fetching Polymarket data...")
    poly = fetch_polymarket_data()
    print(f"  {len(poly)} contracts found")

    print("Fetching source highlights...")
    sources = fetch_source_highlights()
    print(f"  {len(sources)} sources")

    print("\nProducing report via Opus 4.7...")
    report = produce_report(kalshi, poly, sources)
    print(f"  Report: {len(report)} chars, {len(report.split())} words")

    print("\n--- REPORT ---")
    print(report)

    print("\n--- SELF-ASSESSMENT ---")
    assessment = self_assess(report)
    print(assessment)

    if args.save:
        out = WORKSPACE / "exports" / f"pm-scan-2026-05-20.md"
        out.write_text(report)
        print(f"\nSaved: {out}")

    if args.send:
        from agentmail import AgentMail
        key = ""
        with open(WORKSPACE / ".env") as f:
            for line in f:
                if line.startswith("AGENTMAIL_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip("\"'")
        client = AgentMail(api_key=key)
        r = client.inboxes.messages.send(
            inbox_id="trevor_mentis@agentmail.to",
            to="roderick.jones@gmail.com",
            subject="Prediction Market Divergence Scan — 20 May 2026",
            text=report + "\n\n---\nSELF-ASSESSMENT:\n" + assessment,
        )
        print(f"Sent: {r.message_id}")


if __name__ == "__main__":
    main()
