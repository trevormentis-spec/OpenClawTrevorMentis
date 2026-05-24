#!/usr/bin/env python3
"""
Simmer Signal Overlay — pulls Simmer briefing data + scans known geopolitics markets.
Complements the Kalshi scanner, doesn't replace it.

Usage:
    python3 scripts/simmer_scanner.py --save     # save to exports/, print summary
    python3 scripts/simmer_scanner.py --json     # JSON to stdout
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/home/ubuntu/.openclaw/workspace")

# Known high-value geopolitics market search terms on Simmer
# These are specific enough to avoid sports noise
GEOPOLITICS_TERMS = [
    "iran", "ukraine", "russia", "china taiwan", "ceasefire",
    "tariff", "recession", "fed rate cut", "oil sanction",
    "nuclear",
]


def scan():
    try:
        from simmer_sdk import SimmerClient
    except ImportError:
        return {"error": "simmer-sdk not installed", "markets": []}

    api_key = os.environ.get("SIMMER_API_KEY")
    if not api_key:
        env_file = REPO / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("SIMMER_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()
                    break
    if not api_key:
        return {"error": "SIMMER_API_KEY not set", "markets": []}

    client = SimmerClient(api_key=api_key)
    now = datetime.now(timezone.utc)

    results = []
    seen_ids = set()

    for term in GEOPOLITICS_TERMS:
        try:
            markets = client.find_markets(term)
        except Exception:
            continue

        for m in markets:
            if m.id in seen_ids:
                continue
            q = m.question.lower()
            # Skip sports
            if any(k in q for k in [" vs ", " vs. ", "spread:", "over/under",
                   "goal", "touchdown", "la liga", "premier league", "serie a",
                   "bundesliga", "ligue 1", "ufc", "boxing", "tennis:",
                   "roland garros", "wimbledon", "champions league", "mls"]):
                continue

            seen_ids.add(m.id)
            prob = getattr(m, 'current_probability', 0.5) or 0.5

            results.append({
                "query": term,
                "market_id": m.id,
                "question": m.question,
                "probability_yes": round(prob, 4),
                "source": getattr(m, 'import_source', 'polymarket'),
                "resolves_at": getattr(m, 'resolves_at', None),
                "status": getattr(m, 'status', 'unknown'),
            })

    # Also pull briefing for risk alerts + opportunities
    briefing = {}
    try:
        raw = client.get_briefing()
        if raw:
            alerts = raw.get("risk_alerts", []) or []
            perf = raw.get("performance", {}) or {}
            briefing = {
                "risk_alerts": len(alerts),
                "total_pnl": perf.get("total_pnl", 0),
                "pnl_percent": perf.get("pnl_percent", 0),
                "win_rate": perf.get("win_rate", 0),
            }
    except Exception:
        pass

    results.sort(key=lambda r: abs(0.5 - r["probability_yes"]), reverse=True)

    return {
        "generated_at": now.isoformat(),
        "markets_found": len(results),
        "markets": results,
        "briefing": briefing,
        "note": "Simmer provides trading-focused data. For broad market discovery, see Kalshi scanner output.",
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Simmer signal overlay for daily brief")
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    data = scan()

    if "error" in data:
        print(f"Simmer: {data['error']} — skipped", file=sys.stderr)
        if args.json:
            print(json.dumps(data))
        return

    b = data.get("briefing", {})
    print(f"Simmer: {data['markets_found']} geopolitics markets | PnL: \${b.get('total_pnl', 0):.2f}")

    if data["markets_found"] == 0:
        print("  (no geopolitics markets currently indexed on Simmer — see Kalshi scanner)")

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        for m in data["markets"][:10]:
            arrow = "↑" if m["probability_yes"] > 0.5 else "↓"
            print(f"  {m['probability_yes']:.1%} {arrow} | {m['question'][:90]}")

    if args.save:
        out_dir = REPO / "exports"
        out_dir.mkdir(exist_ok=True)
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = out_dir / f"simmer-scan-{date_str}.json"
        path.write_text(json.dumps(data, indent=2))
        print(f"\nSaved: {path}")


if __name__ == "__main__":
    main()
