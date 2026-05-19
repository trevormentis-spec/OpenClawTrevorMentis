#!/usr/bin/env python3
"""
Mexico Markets Scanner — Kalshi + Polymarket Mexico-specific contracts.

Scans known Mexico-related prediction markets and outputs structured data.

Usage:
    python3 scripts/mexico-markets.py              # table to stdout
    python3 scripts/mexico-markets.py --save       # save to exports/

Sources KALSHI_API_KEY from .env
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import sys
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
EXPORT_DIR = REPO_ROOT / "exports"

KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"

# Known Mexico-related Kalshi series tickers
KALSHI_MEXICO_TICKERS = {
    "KXPESO": "USD/MXN exchange rate",
    "KXFXPESO": "USD/MXN rate (alt)",
    "KXMEXICODEPUTIES": "Mexico Chamber of Deputies",
    "KXUSMCA": "USMCA withdrawal",
    "KXGULF": "Gulf of Mexico rename",
    "KXFENTANYL": "Fentanyl policy",
}

# Polymarket slugs (to be parameterized)
POLYMARKET_MEXICO = {
    # Need to discover actual slugs — placeholder
}


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[mxmkts {ts}] {msg}", file=sys.stderr, flush=True)


def fetch_kalshi_series(ticker: str) -> dict | None:
    """Fetch full series info and markets."""
    key = os.environ.get("KALSHI_API_KEY", "")
    if not key:
        log("KALSHI_API_KEY not set")
        return None
    
    url = f"{KALSHI_BASE}/series?ticker_prefix={ticker}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data
    except Exception as e:
        log(f"Kalshi {ticker}: {e}")
        return None


def fetch_kalshi_markets(series_ticker: str) -> list[dict]:
    """Fetch markets for a given series."""
    key = os.environ.get("KALSHI_API_KEY", "")
    if not key:
        return []
    
    url = f"{KALSHI_BASE}/events?series_ticker={series_ticker}&limit=25"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("events", [])
    except Exception as e:
        return []


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save", action="store_true")
    args = parser.parse_args()

    # Load env
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("KALSHI_API_KEY="):
                os.environ["KALSHI_API_KEY"] = line.split("=", 1)[1].strip().strip("'\"")

    results = []

    for ticker, description in KALSHI_MEXICO_TICKERS.items():
        data = fetch_kalshi_series(ticker)
        if data:
            series = data.get("series", [])
            markets = fetch_kalshi_markets(ticker)
            results.append({
                "ticker": ticker,
                "description": description,
                "series_count": len(series),
                "market_count": len(markets),
                "markets": [{"title": m.get("title", ""), "event_ticker": m.get("event_ticker", "")} for m in markets[:5]],
            })
            log(f"{ticker}: {len(markets)} markets")
        else:
            results.append({
                "ticker": ticker,
                "description": description,
                "status": "error",
            })

    # Print
    print(f"\n{'='*60}")
    print(f"MEXICO PREDICTION MARKETS — {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*60}")
    
    for r in results:
        if "error" in r:
            print(f"\n❌ {r['ticker']}: {r['description']} — ERROR")
        else:
            print(f"\n📊 {r['ticker']}: {r['description']}")
            print(f"   Series: {r.get('series_count', 0)}, Markets: {r.get('market_count', 0)}")
            for m in r.get("markets", []):
                print(f"   ├ {m['title'][:80]}")
    
    if args.save:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        date_str = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
        path = EXPORT_DIR / f"mexico-markets-{date_str}.json"
        path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
        log(f"Saved to {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
