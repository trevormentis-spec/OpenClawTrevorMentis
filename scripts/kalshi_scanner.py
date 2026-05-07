#!/usr/bin/env python3
"""
Kalshi Market Scanner — Scan geopolitics/war/conflict markets for tradeable edges.

Usage:
  python3 scripts/kalshi_scanner.py                         # full scan, print to stdout
  python3 scripts/kalshi_scanner.py --save                  # save to file
  python3 scripts/kalshi_scanner.py --save --compare-polymarket  # include Polymarket comparisons
  python3 scripts/kalshi_scanner.py --watchlist             # just the high-signal watchlist

Uses KALSHI_API_KEY env var (bearer token).
Sources environment from .env by default.
"""

import json, os, sys, urllib.request, urllib.parse, datetime, textwrap, time

# ── Config ──
WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_BASE = "https://api.elections.kalshi.com/trade-api/v2"
POLY_GAMMA = "https://gamma-api.polymarket.com"

# Geopolitics series tickers to scan
WATCHLIST_TICKERS = {
    # Russia-Ukraine
    "KXUKRAINEEU": "Ukraine EU pre-accession",
    "KXZELENSKYYOUT": "Zelenskyy out as president",
    "KXSANCTIONRUSSIA": "Russia sanctions bill",
    "KXUKRAINERESIGN": "Ukraine president resign",
    "KXUKRAINE": "Ukraine agreements",
    "KXZELENSKYRUSSIA": "Zelenskyy Russia meetings",
    
    # Iran
    "KXUSAIRANAGREEMENT": "US-Iran nuclear deal",
    "KXIAEAIRANAGREEMENT": "Iran NPT agreement",
    "KXIRANDEMOCRACY": "Iran democracy index",
    "KXIRANVISITUSA": "Iran official visits White House",
    "KXIRANEMBASSY": "US reopen Iran embassy",
    "KXTRUMPIRAN": "Trump visit Iran",
    "KXPAHLAVIVISITA": "Pahlavi visit Iran",
    "KXNEXTIRANLEADER": "Next Iran supreme leader",
    "KXELECTIRAN": "Iran presidential election",
    "KXOFAC": "Iran OFAC action",
    "KXIRANIMPORTS": "US imports from Iran",
    "KXIRANCPI": "Iran CPI",
    "KXIRANMEET": "US-Iran meetings",
    
    # Military / Sanctions
    "KXMILSPEND": "Military spending",
    "KXSANCTIONEURUSS": "EU sanction Russia",
    "KXSANCTIONSVEN": "Venezuela sanctions",
    "KXVENZUELAMILITARY": "Venezuela military deployment",
    "KXLICENSENUCLEAR": "Nuclear approvals",
    "KXREACTOR": "Nuclear reactor license",
    
    # China / Taiwan
    "KXCHINATARIFF": "China tariffs",
    "KXTARIFFRATEPRC": "China tariff rate",
    "KXTAIWANREF": "Taiwan referendum",
    "KXTAIWANDOUBLETAX": "Taiwan double taxation",
    "KXPRESTAIWAN": "Taiwan presidential election",
    "KXAMBCN": "China ambassador",
    
    # Energy / Oil
    "KXWTI": "WTI oil daily",
    "KXBRENTD": "Brent oil daily",
    "KXOILW": "Oil price weekly",
    "KXWTIMIN": "WTI oil monthly low",
    "KXWTIMAX": "WTI oil yearly high",
    "KXOPECCUTS": "OPEC oil production cuts",
    "KXIEAOIL": "IEA oil reserves release",
    "KXRUCRUDEX": "Russia crude exports",
    "KXINDIAOIL": "India Russian oil",
    
    # Misc geopolitics
    "KXCPTPP": "China CPTPP",
    "KXTRUMPCOUNTIRAN": "Trump Iran truths",
}

def load_env():
    """Load .env file for API keys"""
    env_path = os.path.join(WORKSPACE, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k not in os.environ:
                        os.environ[k] = v
    return os.environ.get("KALSHI_API_KEY", os.environ.get("MATON_API_KEY", ""))

def kalshi_get(path, api_key):
    """Make authenticated GET request to Kalshi API"""
    url = f"{API_BASE}{path}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {api_key}")
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode(errors='replace')[:200]}"}
    except Exception as e:
        return {"error": str(e)}

def get_series_info(ticker, api_key):
    """Get series information for a ticker"""
    data = kalshi_get(f"/series?ticker={ticker}", api_key)
    series_list = data.get("series", [])
    if series_list:
        return series_list[0]
    return None

def get_active_markets(ticker, api_key, retries=2):
    """Get active (open) markets for a series ticker, with retry"""
    params_str = urllib.parse.urlencode({
        "limit": 20, "status": "open", "series_ticker": ticker
    })
    for attempt in range(retries + 1):
        data = kalshi_get(f"/markets?{params_str}", api_key)
        if "error" not in data:
            return data.get("markets", [])
        if attempt < retries:
            time.sleep(1)
    return []

def parse_price(val):
    """Parse dollar price string to float"""
    try:
        return float(val) if val else 0.0
    except (ValueError, TypeError):
        return 0.0

def scan_markets(api_key, watchlist_only=False):
    """Scan all Kalshi geopolitics markets"""
    results = []
    tickers = WATCHLIST_TICKERS if watchlist_only else WATCHLIST_TICKERS
    
    for ticker, description in sorted(tickers.items()):
        markets = get_active_markets(ticker, api_key)
        if not markets:
            continue
        
        for m in markets:
            title = m.get("title", m.get("question", ""))
            tick = m.get("ticker", "")
            yb = parse_price(m.get("yes_bid_dollars", "0"))
            ya = parse_price(m.get("yes_ask_dollars", "0"))
            nb = parse_price(m.get("no_bid_dollars", "0"))
            na = parse_price(m.get("no_ask_dollars", "0"))
            vol = parse_price(m.get("volume_fp", "0"))
            close = m.get("close_time", "")[:10]
            last = parse_price(m.get("last_price_dollars", "0"))
            
            # Calculate spread
            spread = ya - yb if yb > 0 and ya > 0 else 0
            
            results.append({
                "series": ticker,
                "description": description,
                "market_ticker": tick,
                "title": title[:120],
                "yes_bid": yb,
                "yes_ask": ya,
                "no_bid": nb,
                "no_ask": na,
                "mid_price": (yb + ya) / 2 if yb > 0 and ya > 0 else last,
                "spread": spread,
                "volume": vol,
                "close_date": close,
                "last_price": last,
            })
    
    # Sort: by volume descending
    results.sort(key=lambda r: r["volume"], reverse=True)
    return results

def check_polymarket_ceasefire():
    """Quick check of the Russia-Ukraine Ceasefire market on Polymarket"""
    try:
        url = f"{POLY_GAMMA}/markets?slug=russia-ukraine-ceasefire-before-gta-vi-554"
        req = urllib.request.Request(url, headers={"User-Agent": "Trevor/1.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        m = data[0] if isinstance(data, list) else data
        prices = json.loads(m.get("outcomePrices", "[]"))
        return {
            "question": m.get("question", ""),
            "yes": float(prices[0]) if len(prices) > 0 else 0,
            "no": float(prices[1]) if len(prices) > 1 else 0,
            "volume": float(m.get("volume", "0")),
            "end_date": m.get("endDateIso", "")[:10],
        }
    except Exception as e:
        return {"error": str(e)}

def format_report(results, poly_data=None):
    """Format scan results as a readable report"""
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = []
    lines.append(f"╔══════════════════════════════════════════════════════════╗")
    lines.append(f"║  Kalshi Geopolitics Market Scan — {now}  ║")
    lines.append(f"╚══════════════════════════════════════════════════════════╝")
    lines.append("")
    
    if not results:
        lines.append("No active geopolitics markets found.")
        return "\n".join(lines)
    
    lines.append(f"{'Series':<22s} {'Yes Bid':>8s} {'Yes Ask':>8s} {'No Bid':>8s} {'No Ask':>8s} {'Spread':>7s} {'Volume':>12s} {'Expiry':>11s}")
    lines.append("-" * 90)
    
    for r in results:
        series = r["series"][:20]
        yb = f"${r['yes_bid']:.2f}" if r['yes_bid'] > 0 else "—"
        ya = f"${r['yes_ask']:.2f}" if r['yes_ask'] > 0 else "—"
        nb = f"${r['no_bid']:.2f}" if r['no_bid'] > 0 else "—"
        na = f"${r['no_ask']:.2f}" if r['no_ask'] > 0 else "—"
        sp = f"${r['spread']:.2f}" if r['spread'] > 0 else "—"
        vol = f"${r['volume']:,.0f}" if r['volume'] > 0 else "—"
        close = r['close_date'][:10] if r['close_date'] else "—"
        lines.append(f"{series:<22s} {yb:>8s} {ya:>8s} {nb:>8s} {na:>8s} {sp:>7s} {vol:>12s} {close:>11s}")
    
    lines.append("")
    lines.append(f"{len(results)} active markets found across {len(set(r['series'] for r in results))} series.")
    
    # Top markets by volume
    top = [r for r in results if r['volume'] > 1000][:10]
    if top:
        lines.append("")
        lines.append("── Top 10 by Volume ──")
        for r in top:
            mid = r['mid_price']
            lines.append(f"  {r['series']}: ${mid:.2f} mid | ${r['volume']:,.0f} vol | exp {r['close_date']}")
            lines.append(f"    {r['description']}")
    
    # Polymarket comparison
    if poly_data:
        lines.append("")
        lines.append("── Polymarket Comparison ──")
        if "error" in poly_data:
            lines.append(f"  Error: {poly_data['error']}")
        else:
            lines.append(f"  Russia-Ukraine Ceasefire before GTA VI?")
            lines.append(f"    Yes: {poly_data['yes']:.0%} | No: {poly_data['no']:.0%}")
            lines.append(f"    Volume: ${poly_data['volume']:,.0f} | Exp: {poly_data['end_date']}")
    
    return "\n".join(lines)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Kalshi geopolitics market scanner")
    parser.add_argument("--save", action="store_true", help="Save report to exports/")
    parser.add_argument("--compare-polymarket", action="store_true", help="Include Polymarket data")
    parser.add_argument("--watchlist", action="store_true", help="Watchlist-only scan")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    # Get API key
    api_key = load_env() or os.environ.get("KALSHI_API_KEY", "")
    if not api_key or api_key.strip() == "":
        # Try to read from .env directly
        env_path = os.path.join(WORKSPACE, ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("KALSHI_API_KEY="):
                        api_key = line.strip().split("=", 1)[1]
                        break
    
    if not api_key:
        print("ERROR: KALSHI_API_KEY not set. Add to .env or export.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Scanning Kalshi geopolitics markets...", file=sys.stderr)
    results = scan_markets(api_key, watchlist_only=args.watchlist)
    
    poly_data = None
    if args.compare_polymarket:
        print(f"Checking Polymarket...", file=sys.stderr)
        poly_data = check_polymarket_ceasefire()
    
    if args.json:
        output = {
            "scan_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "markets": results,
            "polymarket": poly_data,
        }
        print(json.dumps(output, indent=2))
    else:
        report = format_report(results, poly_data)
        print(report)
    
    if args.save:
        date_str = datetime.date.today().isoformat()
        out_dir = os.path.join(WORKSPACE, "exports")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"kalshi-scan-{date_str}.md")
        with open(out_path, "w") as f:
            f.write(report)
        print(f"\nSaved to {out_path}", file=sys.stderr)

if __name__ == "__main__":
    main()
