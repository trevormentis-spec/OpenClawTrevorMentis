#!/usr/bin/env python3
"""Real Estate Listings Collector — Mexican property market monitoring.

Monitors major Mexican real estate platforms for price trends, foreign buyer
activity, and cartel-money laundering signals (cash purchases, below-market
pricing, rapid re-listings).

Sources: Vivanuncios, Inmuebles24, Propiedades.com — all public listing sites.

Usage:
    python3 collectors/real_estate_collector.py --fetch
    python3 collectors/real_estate_collector.py --report
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import re
import sqlite3
import ssl
import sys
import urllib.error
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "realestate"
DB_PATH = DATA_DIR / "realestate.db"
EXPORT_DIR = REPO_ROOT / "exports"

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# Mexican real estate platforms (public, ToS-allowed scraping for non-commercial use)
PLATFORMS = {
    "Vivanuncios": {
        "search_url": "https://www.vivanuncios.com.mx/s-propiedades-inmuebles/venta/{state}/",
        "states": ["cdmx", "jalisco", "nuevo-leon", "quintana-roo"],
        "listing_pattern": r'<div[^>]*class="[^"]*listing-card[^"]*"[^>]*>.*?<h2[^>]*>(.*?)</h2>.*?<span[^>]*class="[^"]*price[^"]*"[^>]*>(.*?)</span>',
        "admiralty": "C-2 — Listing data, not verified transactions",
    },
    "Inmuebles24": {
        "search_url": "https://www.inmuebles24.com/propiedades-en-venta-en-{state}.html",
        "states": ["distrito-federal", "jalisco", "nuevo-leon", "quintana-roo"],
        "listing_pattern": r'<div[^>]*class="[^"]*posting-card[^"]*"[^>]*>.*?<h2[^>]*>(.*?)</h2>.*?<span[^>]*class="[^"]*price[^"]*"[^>]*>(.*?)</span>',
        "admiralty": "C-2",
    },
}

LAUNDERING_INDICATORS = {
    "cash_only": ["efectivo", "contado", "cash"],
    "below_market": ["remate", "urgente", "abajo del mercado", "oportunidad"],
    "rapid_resale": ["herencia", "liquidación", "traspaso"],
    "foreign_buyer": ["extranjero", "americano", "canadiense", "inversión extranjera"],
}


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id TEXT PRIMARY KEY,
            platform TEXT NOT NULL,
            state TEXT,
            title TEXT,
            price_mxn REAL,
            price_usd REAL,
            listing_type TEXT,
            location TEXT,
            flagged INTEGER DEFAULT 0,
            flag_reason TEXT,
            fetched_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_listings_state ON listings(state)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_listings_price ON listings(price_mxn)")
    conn.commit()
    conn.close()


def get_db():
    return sqlite3.connect(str(DB_PATH))


def fetch_platform(platform_name: str, state: str) -> list[dict]:
    """Fetch property listings from a platform for a given state."""
    platform = PLATFORMS.get(platform_name, {})
    url_template = platform.get("search_url", "")
    url = url_template.format(state=state)

    listings = []
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "trevor-mentis/1.0 Mozilla/5.0", "Accept-Language": "es-MX,es;q=0.9"},
        )
        with urllib.request.urlopen(req, timeout=20, context=CTX) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        for match in re.finditer(
            r'<a[^>]*href="([^"]*)"[^>]*>.*?<img[^>]*alt="([^"]*)"[^>]*>.*?\$?\s*([0-9,]+)',
            html,
        ):
            listing = {
                "id": hashlib.md5(match.group(0).encode()).hexdigest()[:12],
                "url": match.group(1),
                "title": match.group(2).strip()[:100],
                "price_raw": match.group(3),
                "state": state,
                "platform": platform_name,
            }
            # Parse price
            try:
                listing["price_mxn"] = float(match.group(3).replace(",", "").replace("$", ""))
                listing["price_usd"] = round(listing["price_mxn"] / 18.0, 2)
            except ValueError:
                listing["price_mxn"] = 0
                listing["price_usd"] = 0

            listings.append(listing)
    except Exception as exc:
        print(f"  [realestate] {platform_name}/{state}: {exc}", file=sys.stderr)

    return listings


def flag_listing(title: str, price_mxn: float) -> str | None:
    """Flag listing for potential money laundering indicators."""
    title_lower = title.lower()

    for flag_type, keywords in LAUNDERING_INDICATORS.items():
        if any(kw in title_lower for kw in keywords):
            return flag_type

    # Flag unusually cheap properties (potential money laundering vehicle)
    if 0 < price_mxn < 500000:
        return "suspiciously_low_price"

    return None


def generate_report() -> str:
    """Generate real estate intelligence memo."""
    conn = get_db()
    cursor = conn.execute(
        "SELECT state, COUNT(*), AVG(price_usd) FROM listings GROUP BY state ORDER BY state"
    )
    state_stats = cursor.fetchall()

    cursor2 = conn.execute(
        "SELECT title, state, price_usd, flag_reason FROM listings WHERE flagged=1 ORDER BY price_usd ASC LIMIT 20"
    )
    flagged = cursor2.fetchall()
    conn.close()

    lines = [
        f"# Real Estate Intelligence Memo — {datetime.date.today().isoformat()}",
        "",
        "## Listings by State",
    ]
    for state, count, avg_price in state_stats:
        state_name = state.replace("-", " ").title()
        lines.append(f"- **{state_name}**: {count} listings, avg ${avg_price:,.0f} USD")

    if flagged:
        lines.append("")
        lines.append("## ⚠️ Flagged Listings (Laundering Indicators)")
        for title, state, price, reason in flagged:
            lines.append(f"- **{title[:60]}** — ${price:,.0f} USD — {state}")
            lines.append(f"  Indicator: {reason}")

    lines.append("")
    lines.append("---")
    lines.append("Sources: Vivanuncios, Inmuebles24 (public listings)")
    lines.append("Note: Listings data reflects asking prices, not transacted values.")
    lines.append("30-day evaluation window required for trend analysis.")

    memo_path = EXPORT_DIR / f"realestate-{datetime.date.today().isoformat()}.md"
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    memo_path.write_text("\n".join(lines))
    return str(memo_path)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Real Estate Listings Collector")
    parser.add_argument("--fetch", action="store_true", help="Fetch listings")
    parser.add_argument("--report", action="store_true", help="Generate memo")
    args = parser.parse_args()

    init_db()

    if args.fetch:
        total = 0
        for platform_name, info in PLATFORMS.items():
            for state in info["states"]:
                listings = fetch_platform(platform_name, state)
                conn = get_db()
                for l in listings:
                    flag = flag_listing(l.get("title", ""), l.get("price_mxn", 0))
                    l["flagged"] = 1 if flag else 0
                    l["flag_reason"] = flag or ""
                    conn.execute(
                        "INSERT OR IGNORE INTO listings (id, platform, state, title, price_mxn, price_usd, flagged, flag_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (l["id"], l["platform"], l["state"], l.get("title", ""), l.get("price_mxn", 0), l.get("price_usd", 0), l["flagged"], l["flag_reason"]),
                    )
                    if flag:
                        print(f"    ⚠️ Flagged: {l.get('title', '')[:60]} ({l.get('price_usd', 0):,.0f} USD)")
                    total += 1
                conn.commit()
                conn.close()
                print(f"  {platform_name}/{state}: {len(listings)} listings")

        print(f"\nTotal: {total} listings")
        print("30-day evaluation window required for trend analysis.")

    if args.report:
        path = generate_report()
        print(f"Memo: {path}")


if __name__ == "__main__":
    main()
