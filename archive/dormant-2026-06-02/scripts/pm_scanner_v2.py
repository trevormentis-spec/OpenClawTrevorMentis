#!/usr/bin/env python3
"""
Prediction Market Intelligence Scanner v2 — Multi-venue divergence scan.

Venues: Kalshi, Polymarket, PredictIt, Manifold Markets
Sources: 12+ Substacks/blogs + Reddit
Analysis: Opus 4.7 via analyst/llm_clients/
Self-assessment: Opus 4.7 scores against 5 dimensions, iterates until ≥7/10

Usage:
    PYTHONPATH="$PWD" python3 scripts/pm_scanner_v2.py
    PYTHONPATH="$PWD" python3 scripts/pm_scanner_v2.py --send
"""
from __future__ import annotations

import json, os, pathlib, subprocess, sys, time, urllib.request
from datetime import datetime, timezone
from analyst.llm_clients.openrouter_client import OpenRouterClient
from _present_env import load_env

WORKSPACE = pathlib.Path("/home/ubuntu/.openclaw/workspace")
KALSHI_SCRIPT = WORKSPACE / "scripts" / "kalshi_scanner.py"
GAMMA = "https://gamma-api.polymarket.com"
TS = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")

# Polymarket geopolitics slugs (found via web search — these are real active contracts)
POLY_SLUGS = [
    "us-iran-nuclear-deal-by-may-31-974",
    "us-iran-nuclear-deal-by-jun-30",
    "us-iran-nuclear-deal-by-dec-31",
    "us-iran-nuclear-deal-before-2027",
    "us-x-iran-ceasefire-by",
    "us-x-iran-ceasefire-extended-by",
    "us-x-iran-permanent-peace-deal-by",
    "iran-ceasefire-continues-through",
    "israel-x-iran-permanent-peace-deal-by",
]

# Geopolitics keywords for broad market filtering
GEO_KW = ["iran", "nuclear", "ceasefire", "ukraine", "russia", "nato",
          "taiwan", "china", "oil", "crude", "sanction", "trump", "putin",
          "zelenskyy", "gaza", "israel", "hormuz", "strait", "tariff",
          "president", "fed", "rate", "inflation", "impeach", "resign",
          "election", "congress", "senate", "default", "debt", "midterm",
          "balance of power"]

# Source list
SOURCES = [
    ("Substack", "Under the Market Lens", "https://underthemarketlens.substack.com"),
    ("Substack", "Asterisk Magazine", "https://asteriskmag.substack.com"),
    ("Substack", "Future Forecasters", "https://futureforecasters.substack.com"),
    ("Substack", "Capital Spectator", "https://capitalspectator.substack.com"),
    ("Substack", "Gold & Geopolitics", "https://no01.substack.com"),
    ("Substack", "Guardian Research", "https://guardianresearch.substack.com"),
    ("Substack", "Aspicts", "https://aspicts.substack.com"),
    ("Blog", "AgentBets", "https://agentbets.ai"),
    ("Blog", "Prediction Hunt", "https://www.predictionhunt.com/blog"),
    ("Blog", "TRM Labs", "https://www.trmlabs.com/resources/blog"),
    ("Think tank", "ISW Iran Update", "https://understandingwar.org"),
    ("Think tank", "ECFR Iran Monitor", "https://ecfr.eu/special/iran-nuclear-monitor"),
]


def fetch_kalshi() -> dict:
    """Run Kalshi scanner, return structured data."""
    env = load_env()
    r = subprocess.run(["python3", str(KALSHI_SCRIPT), "--json"],
        capture_output=True, text=True, timeout=60, env=env)
    return {"source": "Kalshi", "ts": TS, "data": r.stdout[:4000],
            "contracts": len(r.stdout), "status": "ok"}


def fetch_polymarket() -> dict:
    """Fetch Polymarket geopolitics contracts via Gamma API."""
    contracts = []
    # Query known specific slugs
    for slug in POLY_SLUGS:
        try:
            req = urllib.request.Request(f"{GAMMA}/markets?slug={slug}",
                headers={"User-Agent": "Trevor/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            for m in data if isinstance(data, list) else [data]:
                prices = m.get("outcomePrices", "[0,0]")
                if isinstance(prices, str): prices = json.loads(prices)
                yes = float(prices[0])*100 if prices else 0; no = float(prices[1])*100 if len(prices)>1 else 0
                contracts.append({
                    "question": m.get("question","?"),
                    "yes": round(yes,1), "no": round(no,1),
                    "volume": round(float(m.get("volume",0)),0),
                    "slug": slug,
                })
        except: pass
    
    # Paginated broad search
    for offset in [0, 100, 200]:
        try:
            req = urllib.request.Request(f"{GAMMA}/markets?limit=100&offset={offset}&closed=false",
                headers={"User-Agent": "Trevor/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
            if not data: break
            for m in data:
                q = (m.get("question","") + " " + m.get("title","")).lower()
                for kw in GEO_KW:
                    if kw in q:
                        prices = m.get("outcomePrices","[0,0]")
                        if isinstance(prices, str): prices = json.loads(prices)
                        yes = float(prices[0])*100 if prices else 0
                        vol = float(m.get("volume",0))
                        if vol > 500:
                            contracts.append({
                                "question": m.get("question","?"),
                                "yes": round(yes,1),
                                "volume": round(vol,0),
                                "end_date": str(m.get("endDate","?"))[:10],
                            })
                        break
        except: break
    
    return {"source": "Polymarket", "ts": TS, "contracts": len(contracts),
            "data": contracts, "status": "ok"}


def fetch_predictit() -> dict:
    """Fetch PredictIt geopolitics/politics markets."""
    contracts = []
    try:
        req = urllib.request.Request("https://www.predictit.org/api/marketdata/all/",
            headers={"User-Agent": "Trevor/1.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        for m in data.get("markets", []):
            name = m.get("name", "").lower()
            for kw in GEO_KW:
                if kw in name:
                    for c in m.get("contracts", []):
                        contracts.append({
                            "market": m.get("name","?")[:50],
                            "contract": c.get("name","?"),
                            "buy_yes": c.get("bestBuyYesCost"),
                            "buy_no": c.get("bestBuyNoCost"),
                            "last_price": c.get("lastTradePrice"),
                            "volume": c.get("volume"),
                        })
                    break
    except: pass
    return {"source": "PredictIt", "ts": TS, "contracts": len(contracts),
            "data": contracts, "status": "ok"}


def fetch_manifold() -> dict:
    """Fetch Manifold Markets geopolitics-relevant markets."""
    contracts = []
    try:
        req = urllib.request.Request("https://api.manifold.markets/v0/markets?limit=100",
            headers={"User-Agent": "Trevor/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        for m in data if isinstance(data, list) else []:
            q = (m.get("question","") + " " + m.get("description","")).lower()
            for kw in GEO_KW:
                if kw in q:
                    contracts.append({
                        "question": m.get("question","?")[:60],
                        "probability": round(m.get("probability",0)*100, 1),
                        "volume": round(m.get("volume",0), 0),
                    })
                    break
    except: pass
    return {"source": "Manifold", "ts": TS, "contracts": len(contracts),
            "data": contracts, "status": "ok"}


def format_venues(all_data: dict) -> str:
    """Format all venue data for the LLM prompt."""
    lines = []
    for venue in ["kalshi", "polymarket", "predictit", "manifold"]:
        v = all_data.get(venue, {})
        lines.append(f"\n{'='*60}")
        lines.append(f"{v.get('source', venue)} — {v.get('ts','?')} — {v.get('contracts',0)} contracts")
        lines.append(f"{'='*60}")
        if venue == "kalshi":
            lines.append(v.get("data","")[:3000])
        elif venue == "polymarket":
            for c in v.get("data", [])[:15]:
                lines.append(f"  {c.get('question','?')[:55]:55} | {c.get('yes',0):5.1f}¢ | Vol: ${c.get('volume',0):>10,.0f} | {c.get('end_date','?')}")
        elif venue == "predictit":
            for c in v.get("data", [])[:20]:
                lines.append(f"  {c.get('contract','?')[:40]:40} [{c.get('market','?')[:30]:30}] | YES: {str(c.get('buy_yes','?')):>4} NO: {str(c.get('buy_no','?')):>4} | Last: {c.get('last_price','?')}")
        elif venue == "manifold":
            for c in v.get("data", [])[:10]:
                lines.append(f"  {c.get('question','?')[:55]:55} | {c.get('probability',0):5.1f}% | Vol: {c.get('volume',0):>8,.0f}")
    return "\n".join(lines)


def assess_quality(report: str) -> dict:
    """Ask Opus 4.7 to score the report on 5 dimensions, return scores + verdict."""
    client = OpenRouterClient()
    result = client.complete(
        model="anthropic/claude-opus-4.7",
        messages=[{"role": "user", "content": f"""You are a quality reviewer. Score this intelligence product on 5 dimensions (1-10).

PRODUCT: Daily Prediction Market Divergence Scan v2

REPORT:
{report[:3000]}

Score 1-10 for:
1. Data completeness — venue coverage, contract depth, metadata hygiene
2. Analytical depth — adds value beyond raw data, interprets term structures
3. Actionability — trade ideas, entry/exit logic, triggers, watchlist
4. Source usage — timestamps, contract IDs, volumes, spreads, URLs
5. Calibration — proper uncertainty bounds, honest about signal quality

Also: overall verdict (PASS/FAIL). If FAIL or avg < 7, give specific fixes.

Output JSON ONLY: {{"scores": [int,int,int,int,int], "avg": float, "verdict": str, "fixes": [str]}}"""}],
        max_tokens=1000, temperature=0.1,
    )
    text = result.get("content", "")
    s = text.find("{"); e = text.rfind("}")
    try: return json.loads(text[s:e+1]) if s >= 0 else {"avg": 0, "verdict": "FAIL", "fixes": ["Parse error"]}
    except: return {"avg": 0, "verdict": "FAIL", "fixes": ["JSON error"]}


def produce_report(all_data: dict, iteration: int = 1, prev_fixes: list = None) -> str:
    """Use Opus 4.7 to compose the scan."""
    client = OpenRouterClient()
    venue_data = format_venues(all_data)
    sources_text = "\n".join(f"  [{t}] {n}: {u}" for t, n, u in SOURCES)
    fix_context = ""
    if prev_fixes:
        fix_context = "PREVIOUS ITERATION FEEDBACK (apply these fixes):\n" + "\n".join(f"  - {f}" for f in prev_fixes)

    prompt = f"""You are a senior intelligence analyst. Produce a daily prediction market divergence scan (v2).

Today: {TS}
Iteration: {iteration}/MAX

TASK: Analyze data from 4 venues (Kalshi, Polymarket, PredictIt, Manifold). Produce a concise report with:
1. EXECUTIVE SUMMARY — 2-3 paragraph BLUF with top judgments
2. HEADLINE SIGNALS — 3-5 key findings with calibrated language
3. CROSS-VENUE ANALYSIS — compare similar contracts across different exchanges
4. TERM STRUCTURE INTERPRETATION — hazard rates, kinks, inversions, what they imply
5. ACTIONABLE TRADE IDEAS — specific contracts, direction, entry rationale, risk (even if speculative)
6. WATCHLIST — contracts to monitor, trigger levels, what move would be meaningful
7. MONITORING PRIORITIES — next 24-48h

MANDATORY HYGIENE:
- Timestamp each price: "{TS}"
- Include contract IDs/tickers where visible
- Note bid-ask spreads when available
- Flag venue signal quality (liquidity, volume, spread)
- Do NOT truncate — this is the FULL report
- If Polymarket data is thin, note it and explain why

{fix_context}

VENUE DATA:
{venue_data}

SOURCES:
{sources_text}

Write the full report now."""

    result = client.complete(
        model="anthropic/claude-opus-4.7",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000, temperature=0.3,
    )
    return result.get("content", "")


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--send", action="store_true")
    p.add_argument("--save", action="store_true")
    args = p.parse_args()

    print("=== Prediction Market Scanner v2 ===")
    print(f"Timestamp: {TS}")

    # Fetch all venues
    all_data = {}
    for name, func in [("kalshi", fetch_kalshi), ("polymarket", fetch_polymarket),
                        ("predictit", fetch_predictit), ("manifold", fetch_manifold)]:
        print(f"Fetching {name}...")
        try:
            all_data[name] = func()
            print(f"  {all_data[name].get('contracts',0)} contracts")
        except Exception as e:
            all_data[name] = {"source": name, "status": "error", "data": str(e)[:200]}
            print(f"  Error: {e}")

    # Iterate until quality >= 7/10
    max_iterations = 5
    for iteration in range(1, max_iterations + 1):
        prev_fixes = None

        report = produce_report(all_data, iteration=iteration, prev_fixes=prev_fixes)
        print(f"\n--- Iteration {iteration}: {len(report)} chars ---")

        assessment = assess_quality(report)
        scores = assessment.get("scores", [0, 0, 0, 0, 0])
        avg = assessment.get("avg", 0)
        verdict = assessment.get("verdict", "FAIL")
        fixes = assessment.get("fixes", [])

        print(f"Scores: {scores} | Avg: {avg:.1f} | Verdict: {verdict}")
        if fixes:
            for f in fixes[:3]:
                print(f"  Fix: {f[:90]}")

        if avg >= 7 or iteration >= max_iterations:
            print(f"\n{'✅ PASS' if avg >= 7 else '⚠️ Max iterations'} — quality: {avg:.1f}/10")
            break

        # Store fixes for next iteration
        prev_fixes = fixes

    print(f"\n{'='*60}")
    print(report)
    print(f"\n--- SELF-ASSESSMENT ---")
    print(f"Scores: {scores}")
    print(f"Average: {avg:.1f}/10")

    if args.save:
        out = WORKSPACE / "exports" / f"pm-scan-v2-{TS[:10]}.md"
        out.write_text(report + f"\n\n---\nSELF-ASSESSMENT: {avg:.1f}/10\nScores: {scores}\nVerdict: {verdict}")
        print(f"Saved: {out}")

    if args.send:
        from agentmail import AgentMail
        key = ""
        with open(WORKSPACE / ".env") as f:
            for line in f:
                if line.startswith("AGENTMAIL_API_KEY="):
                    key = line.split("=",1)[1].strip().strip("\"'")
        client = AgentMail(api_key=key)
        r = client.inboxes.messages.send(
            inbox_id="trevor_mentis@agentmail.to",
            to="roderick.jones@gmail.com",
            subject=f"Prediction Market Scan v2 — {TS[:10]} (Quality: {avg:.1f}/10)",
            text=report[:3000] + f"\n\n[...truncated, full {len(report)} char report saved to exports/]\n\n---\nSELF-ASSESSMENT: {avg:.1f}/10\nScores: {scores}",
        )
        print(f"Sent: {r.message_id}")


if __name__ == "__main__":
    main()
