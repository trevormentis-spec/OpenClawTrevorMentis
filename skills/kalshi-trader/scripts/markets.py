#!/usr/bin/env python3
"""
Kalshi Market Discovery & Research

Usage:
  python3 markets.py --search "tariff"
  python3 markets.py --ticker KXTARIFFRATEPRC-25JUL01
  python3 markets.py --status open --limit 20
  python3 markets.py --research "Mexico tariffs will exceed 5% by July 2026"
"""

import sys
import json
import argparse
from client import KalshiClient, KalshiAuthError, KalshiAPIError


def format_market(m: dict) -> str:
    """Format a single market for display."""
    ticker = m.get("ticker", "?")
    title = m.get("title", m.get("subtitle", "?"))
    status = m.get("status", "?")
    yes_bid = m.get("yes_bid", "N/A")
    yes_ask = m.get("yes_ask", "N/A")
    last_price = m.get("last_price", "N/A")
    volume = m.get("volume", "N/A")
    close_time = m.get("close_time", "?")
    return (
        f"  {ticker:<45}  {status:<10}  "
        f"bid:{yes_bid:<6} ask:{yes_ask:<6}  last:{last_price:<8}  "
        f"vol:{str(volume):<12}"
        f"\n    {title}"
        f"\n    closes: {close_time}"
    )


def search_markets(client: KalshiClient, query: str, limit: int = 30):
    """Search markets by keyword in title/ticker."""
    print(f"Searching Kalshi for: \"{query}\"\n")
    # Kalshi API doesn't have a native search endpoint — we fetch with ticker
    # filter and also try a broader fetch to filter client-side
    try:
        # Try exact ticker match first
        resp = client.get_markets(ticker=query, limit=limit)
        markets = resp.get("markets", [])
    except KalshiAPIError:
        markets = []

    if not markets:
        # Broader fetch with event_ticker filter
        try:
            resp = client.get_markets(status="open", limit=limit)
            all_markets = resp.get("markets", [])
            query_lower = query.lower()
            markets = [
                m for m in all_markets
                if query_lower in m.get("title", "").lower()
                or query_lower in m.get("subtitle", "").lower()
                or query_lower in m.get("ticker", "").lower()
            ]
        except KalshiAPIError as e:
            print(f"Error fetching markets: {e}", file=sys.stderr)
            sys.exit(1)

    if not markets:
        print("No markets found.")
        return

    print(f"Found {len(markets)} market(s):\n")
    for m in markets[:limit]:
        print(format_market(m))
        print()


def get_market_detail(client: KalshiClient, ticker: str):
    """Get detailed info for a single market, including order book."""
    print(f"Market: {ticker}\n")

    try:
        market = client.get_market(ticker)
        m = market.get("market", market)
        print("─" * 60)
        print(f"Ticker:      {m.get('ticker')}")
        print(f"Title:       {m.get('title')}")
        print(f"Subtitle:    {m.get('subtitle', 'N/A')}")
        print(f"Status:      {m.get('status')}")
        print(f"Close time:  {m.get('close_time')}")
        print(f"Yes bid:     {m.get('yes_bid')}")
        print(f"Yes ask:     {m.get('yes_ask')}")
        print(f"Last price:  {m.get('last_price')}")
        print(f"Volume:      {m.get('volume')}")
        print(f"Open interest: {m.get('open_interest', 'N/A')}")
        print(f"Min tick:    {m.get('min_tick_size_cents', '?')}¢")
        print(f"Event ticker: {m.get('event_ticker', 'N/A')}")
        print(f"Series ticker: {m.get('series_ticker', 'N/A')}")
        print(f"Rules:       {m.get('rules_primary', 'N/A')}")
        print("─" * 60)
    except KalshiAPIError as e:
        print(f"Error: {e}", file=sys.stderr)

    # Also fetch orderbook
    try:
        ob = client.get_orderbook(ticker)
        print("\nOrder Book:")
        book = ob.get("orderbook", ob)
        if book:
            yes_bids = book.get("yes_bids", [])[:5]
            yes_asks = book.get("yes_asks", [])[:5]
            if yes_bids:
                print("  YES Bids (top 5):")
                for b in yes_bids:
                    print(f"    {b.get('price', '?')}¢ × {b.get('count', '?')}")
            if yes_asks:
                print("  YES Asks (top 5):")
                for a in yes_asks:
                    print(f"    {a.get('price', '?')}¢ × {a.get('count', '?')}")
    except KalshiAPIError as e:
        print(f"Orderbook error: {e}", file=sys.stderr)


def list_markets(
    client: KalshiClient,
    status: str = "open",
    limit: int = 30,
    event_ticker: str = None,
    cursor: str = None,
):
    """List markets with optional filters."""
    params = {"status": status, "limit": limit}
    if event_ticker:
        params["event_ticker"] = event_ticker
    if cursor:
        params["cursor"] = cursor

    print(f"Markets (status={status}, limit={limit}):\n")
    try:
        resp = client.get_markets(**{k: v for k, v in params.items() if v is not None})
        markets = resp.get("markets", [])
        if not markets:
            print("No markets found.")
            return
        for m in markets:
            print(format_market(m))
            print()
        cursor = resp.get("cursor")
        if cursor:
            print(f"\nNext cursor: {cursor}")
    except KalshiAPIError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def research_thesis(client: KalshiClient, thesis: str, limit: int = 10):
    """
    Research a thesis against Kalshi markets.
    Searches open markets and returns relevant matches with pricing.
    """
    print(f"Researching thesis: \"{thesis}\"\n")
    print("=" * 60)

    # Extract keywords from thesis (simple approach)
    keywords = [
        w.lower().strip(".,;:!?\"'()[]")
        for w in thesis.split()
        if len(w.strip(".,;:!?\"'()[]")) > 3
    ]

    try:
        resp = client.get_markets(status="open", limit=200)
        markets = resp.get("markets", [])
    except KalshiAPIError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Score markets by keyword matches in title and subtitle
    scored = []
    for m in markets:
        title = (m.get("title", "") + " " + m.get("subtitle", "")).lower()
        score = sum(1 for kw in keywords if kw in title)
        if score > 0:
            scored.append((score, m))

    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        print("No matching markets found. Try broader terms.")
        return

    print(f"Top {min(limit, len(scored))} matches:\n")
    for score, m in scored[:limit]:
        ticker = m.get("ticker", "?")
        title = m.get("title", "?")
        last = m.get("last_price", "N/A")
        yes_bid = m.get("yes_bid", "N/A")
        yes_ask = m.get("yes_ask", "N/A")
        volume = m.get("volume", "N/A")
        print(f"  [{score} keywords] {ticker}")
        print(f"    {title}")
        print(f"    Last: {last}¢  Bid: {yes_bid}¢  Ask: {yes_ask}¢  Vol: {volume}")
        print(f"    Closes: {m.get('close_time', '?')}")
        print()

    print("=" * 60)
    print("Save tickers of interest and use trade.py to build a plan.")


def main():
    parser = argparse.ArgumentParser(
        description="Kalshi Market Discovery & Research"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--search", type=str, help="Search markets by keyword")
    group.add_argument("--ticker", type=str, help="Get detailed market info")
    group.add_argument("--list", action="store_true", help="List markets")
    group.add_argument("--research", type=str, help="Research a thesis against Kalshi")

    parser.add_argument("--status", type=str, default="open", help="Market status filter")
    parser.add_argument("--limit", type=int, default=30, help="Max results")
    parser.add_argument("--event", type=str, help="Event ticker filter")
    parser.add_argument("--cursor", type=str, help="Pagination cursor")

    args = parser.parse_args()

    try:
        client = KalshiClient()

        if args.search:
            search_markets(client, args.search, args.limit)
        elif args.ticker:
            get_market_detail(client, args.ticker)
        elif args.list:
            list_markets(client, args.status, args.limit, args.event, args.cursor)
        elif args.research:
            research_thesis(client, args.research, args.limit)

    except (KalshiAuthError, KalshiAPIError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
