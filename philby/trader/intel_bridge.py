#!/usr/bin/env python3
"""
Philby Intel-Kalshi Bridge — Edge Detection Engine.

Reads Philby KJ feed narratives + Kalshi scanner data, finds mispricings
where Trevor's intelligence assessment diverges from market pricing.

Each detected edge → trade signal that the trader can execute.

Usage:
    python3 philby/trader/intel_bridge.py                     # Scan for edges
    python3 philby/trader/intel_bridge.py --kalshi-file <path>  # Custom scanner data
    python3 philby/trader/intel_bridge.py --kj-feed <path>      # Custom KJ feed
    python3 philby/trader/intel_bridge.py --json               # Machine-readable output
    python3 philby/trader/intel_bridge.py --verbose            # Show reasoning
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
from typing import Any

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
DEFAULT_KJ_FEED = REPO / "exports" / "kj-feeds" / "latest.json"
DEFAULT_KALSHI_SCAN = None  # Try today's date

# Known Kalshi contract mapping: narrative ID patterns → Kalshi ticker keywords
# Each entry maps a Philby narrative to searchable Kalshi market identifiers.
NARRATIVE_TO_KALSHI = {
    "iran_nuclear": {
        "ticker_keywords": ["USAIRANAGREEMENT"],
        "direction": "buy_yes",
        "trevor_narrative_ids": ["iran_nuclear_deal_before_june", "iran_nuclear_deal_by_july"],
    },
    "iran_trump": {
        "ticker_keywords": ["TRUMPIRAN"],
        "direction": "buy_yes",
        "trevor_narrative_ids": ["iran_nuclear_deal_before_june"],
    },
    "brent_crude_high": {
        "ticker_keywords": ["WTIMAX"],
        "direction": "buy_yes",
        "trevor_narrative_ids": ["brent_crude_price_trajectory"],
    },
    "ukraine_eu": {
        "ticker_keywords": ["UKRAINEEU"],
        "direction": "buy_yes",
        "trevor_narrative_ids": ["ukraine_european_security_realignment"],
    },
    "us_tariffs": {
        "ticker_keywords": ["TARIFFRATEPRC"],
        "direction": "buy_yes",
        "trevor_narrative_ids": ["us_china_trade_tariff_escalation"],
    },
}

# Minimum Trevor confidence to generate a signal
MIN_CONFIDENCE_TO_TRADE = 45
# Minimum edge in percentage points
MIN_EDGE_PTS = 10


def log(msg: str) -> None:
    print(f"[intel-bridge {dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


def load_kj_feed(path: pathlib.Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def load_kalshi_scan() -> list[dict]:
    """Load the latest Kalshi scanner output."""
    today = dt.date.today().strftime("%Y-%m-%d")
    scan_path = REPO / "exports" / f"kalshi-scan-{today}.md"
    if not scan_path.exists():
        # Try yesterday
        yesterday = (dt.date.today() - dt.timedelta(days=1)).strftime("%Y-%m-%d")
        scan_path = REPO / "exports" / f"kalshi-scan-{yesterday}.md"
    if not scan_path.exists():
        log("No Kalshi scan found — run kalshi_scanner.py first")
        return []

    markets = []
    for line in scan_path.read_text().split("\n"):
        parts = line.strip().split()
        # Only process lines from the detail table (not top-10 summary)
        if not (len(parts) >= 8 and parts[0].startswith("KX") and len(parts[0]) > 3):
            continue
        if parts[1] in ("bid=",):  # Skip summary section lines
            continue
        try:
            ticker = parts[0]
            yes_bid = float(parts[1].replace("$", "").replace(",", ""))
            yes_ask = float(parts[2].replace("$", "").replace(",", ""))
            volume_str = parts[6].replace("$", "").replace(",", "")
            if volume_str == "—":
                volume = 0
            else:
                volume = int(float(volume_str))
            expiry = parts[7] if len(parts) > 7 else ""
            markets.append({
                "ticker": ticker,
                "yes_bid": yes_bid,
                "yes_ask": yes_ask,
                "mid_price": round((yes_bid + yes_ask) / 2, 4),
                "implied_prob_pct": round((yes_bid + yes_ask) / 2 * 100, 1),
                "volume": volume,
                "expiry": expiry,
            })
        except (ValueError, IndexError):
            pass
    return markets


def detect_edges(
    kj_feed: dict | None,
    kalshi_markets: list[dict],
) -> list[dict]:
    """Detect trading edges where Philby intel diverges from market pricing."""
    if not kj_feed:
        log("No KJ feed available")
        return []

    narratives = {n["id"]: n for n in kj_feed.get("narratives", [])}
    edges = []

    for mapping_key, mapping in NARRATIVE_TO_KALSHI.items():
        # Get Trevor's confidence for this narrative
        trevor_confidences = []
        for nid in mapping["trevor_narrative_ids"]:
            if nid in narratives:
                trevor_confidences.append(narratives[nid]["confidence"])

        if not trevor_confidences:
            continue

        avg_trevor_conf = sum(trevor_confidences) / len(trevor_confidences)

        if avg_trevor_conf < MIN_CONFIDENCE_TO_TRADE:
            continue

        # Find matching Kalshi markets
        matching_markets = []
        for m in kalshi_markets:
            for kw in mapping["ticker_keywords"]:
                if kw in m["ticker"]:
                    matching_markets.append(m)
                    break

        if not matching_markets:
            # No matching market — note the gap
            edges.append({
                "mapping": mapping_key,
                "trevor_confidence": round(avg_trevor_conf, 1),
                "market_confidence": None,
                "edge_pts": None,
                "direction": mapping["direction"],
                "matching_markets": [],
                "status": "no_market_found",
                "note": f"Philby assesses {mapping_key} at {avg_trevor_conf:.0f}% but no matching Kalshi contract found",
            })
            continue

        # For each matching market, compute edge
        for market in matching_markets:
            market_prob = market["implied_prob_pct"]

            if mapping["direction"] == "buy_yes":
                edge = avg_trevor_conf - market_prob
                action = "BUY Yes"
            else:
                edge = market_prob - avg_trevor_conf
                action = "BUY No"

            signal = {
                "mapping": mapping_key,
                "trevor_confidence": round(avg_trevor_conf, 1),
                "market_confidence": market_prob,
                "edge_pts": round(edge, 1),
                "direction": mapping["direction"],
                "action": action,
                "ticker": market["ticker"],
                "market_price_cents": round(market["mid_price"] * 100),
                "implied_prob_pct": market_prob,
                "volume": market["volume"],
                "expiry": market["expiry"],
                "status": "tradeable" if abs(edge) >= MIN_EDGE_PTS else "below_threshold",
            }
            edges.append(signal)

    # Sort by edge magnitude (largest first)
    edges.sort(key=lambda e: abs(e.get("edge_pts", 0) or 0), reverse=True)
    return edges


def format_signal(signal: dict) -> str:
    """Format an edge signal for display."""
    if signal["status"] == "no_market_found":
        return f"[GAP] {signal['mapping']}: {signal['note']}"

    direction_mark = "🟢" if signal["edge_pts"] > 0 else "🔴"
    return (
        f"{direction_mark} {signal['action']:8s} {signal['ticker']:<35s} "
        f"Trevor={signal['trevor_confidence']:.0f}%  "
        f"Market={signal['implied_prob_pct']:.0f}%  "
        f"Edge={signal['edge_pts']:+.0f}pts  "
        f"Vol=${signal['volume']:,}  "
        f"Exp={signal['expiry']}"
    )


def save_signals(edges: list[dict]) -> None:
    """Save detected signals to a JSON file for the trader to consume."""
    output_dir = REPO / "philby" / "trader" / "signals"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Latest signals
    (output_dir / "latest.json").write_text(json.dumps({
        "timestamp": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cycle": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M"),
        "total_signals": len(edges),
        "tradeable": [e for e in edges if e.get("status") == "tradeable"],
        "sub_threshold": [e for e in edges if e.get("status") == "below_threshold"],
        "gaps": [e for e in edges if e.get("status") == "no_market_found"],
    }, indent=2))
    
    # Also append to daily signal log
    today = dt.date.today().strftime("%Y-%m-%d")
    signal_log = output_dir / f"{today}.jsonl"
    with open(signal_log, "a") as f:
        f.write(json.dumps({
            "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            "signals": edges,
        }) + "\n")
    
    log(f"Saved {len(edges)} signals ({sum(1 for e in edges if e.get('status')=='tradeable')} tradeable)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Philby Intel-Kalshi Edge Detection")
    parser.add_argument("--kj-feed", default=str(DEFAULT_KJ_FEED), help="Path to KJ feed JSON")
    parser.add_argument("--kalshi-file", default="", help="Path to Kalshi scanner output")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--verbose", action="store_true", help="Show full reasoning")
    args = parser.parse_args()

    # Load KJ feed
    kj_feed = load_kj_feed(pathlib.Path(args.kj_feed))
    if not kj_feed:
        log("ERROR: No KJ feed — run kj_feed.py first or specify --kj-feed")
        return 1

    # Load Kalshi markets
    kalshi_markets = load_kalshi_scan()

    # Detect edges
    edges = detect_edges(kj_feed, kalshi_markets)

    if args.json:
        print(json.dumps({
            "timestamp": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "kj_feed_cycle": kj_feed.get("cycle", 0),
            "kalshi_markets_scanned": len(kalshi_markets),
            "total_signals": len(edges),
            "tradeable": [e for e in edges if e.get("status") == "tradeable"],
            "sub_threshold": [e for e in edges if e.get("status") == "below_threshold"],
            "gaps": [e for e in edges if e.get("status") == "no_market_found"],
        }, indent=2))
    else:
        tradeable = [e for e in edges if e.get("status") == "tradeable"]
        sub = [e for e in edges if e.get("status") == "below_threshold"]
        gaps = [e for e in edges if e.get("status") == "no_market_found"]

        print(f"\n=== Philby Intel-Kalshi Edge Detection ===")
        print(f"KJ feed cycle: {kj_feed.get('cycle', '?')}  |  Markets scanned: {len(kalshi_markets)}")
        print(f"Total signals: {len(edges)}  |  Tradeable: {len(tradeable)}  |  Below threshold: {len(sub)}  |  Gaps: {len(gaps)}")
        print()

        if tradeable:
            print(f"--- TRADEABLE SIGNALS (≥{MIN_EDGE_PTS}pt edge) ---")
            for e in tradeable:
                print(f"  {format_signal(e)}")
            print()

        if sub:
            print("--- BELOW THRESHOLD ---")
            for e in sub:
                print(f"  {format_signal(e)}")
            print()

        if gaps:
            print("--- GAPS (no matching market) ---")
            for e in gaps:
                print(f"  {format_signal(e)}")
            print()

    # Always save signals for the trader
    save_signals(edges)

    # Return exit code based on tradeable signals
    if any(e.get("status") == "tradeable" for e in edges):
        return 0  # Signals found
    return 0


if __name__ == "__main__":
    sys.exit(main())
