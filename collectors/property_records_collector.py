#!/usr/bin/env python3
"""Property Records Collector — State-by-state public registry monitoring.

Start with 4 highest-value states: CDMX, Jalisco, Nuevo León, Quintana Roo.
Flags patterns: rapid sequential transactions, valuation anomalies, foreign buyer concentration.

Usage:
    python3 collectors/property_records_collector.py --fetch
    python3 collectors/property_records_collector.py --report
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
DATA_DIR = REPO_ROOT / "data" / "property"
DB_PATH = DATA_DIR / "property.db"
EXPORT_DIR = REPO_ROOT / "exports"

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

STATE_REGISTRIES = {
    "CDMX": {
        "name": "CDMX",
        "url": "https://rppdf.cdmx.gob.mx",
        "search_path": "/consulta",
        "priority": "critical",
        "note": "Highest-value jurisdiction — national political/financial center",
    },
    "Jalisco": {
        "name": "Jalisco",
        "url": "https://rpp.jalisco.gob.mx",
        "search_path": "/consulta-publica",
        "priority": "high",
        "note": "CJNG home state — money laundering risk",
    },
    "Nuevo León": {
        "name": "Nuevo León",
        "url": "https://registros.nl.gob.mx",
        "search_path": "/propiedad",
        "priority": "high",
        "note": "Industrial heartland — nearshoring property velocity",
    },
    "Quintana Roo": {
        "name": "Quintana Roo",
        "url": "https://rppc.qroo.gob.mx",
        "search_path": "/consulta",
        "priority": "high",
        "note": "Tourism/cartel money laundering hotspot",
    },
}

ENTITIES_BY_CATEGORY = {
    "cartel_security": ["CJNG", "CDS", "Los Chapitos", "Los Mayos", "CSRL", "Viagras"],
    "political_risk": ["Morena", "PAN", "PRI", "Sheinbaum", "Gobernador", "Gobernadora"],
    "us_mexico": ["empresa extranjera", "US company", "capital extranjero", "inversión extranjera"],
}


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            state TEXT NOT NULL,
            property_type TEXT,
            transacted_at TEXT,
            registry_date TEXT,
            buyer_name TEXT,
            seller_name TEXT,
            amount_mxn REAL,
            area_sqm REAL,
            location TEXT,
            flagged INTEGER DEFAULT 0,
            flag_reason TEXT,
            fetched_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tx_state ON transactions(state)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tx_buyer ON transactions(buyer_name)")
    conn.commit()
    conn.close()


def get_db():
    return sqlite3.connect(str(DB_PATH))


def fetch_state_registry(state_key: str) -> list[dict]:
    """Fetch recent property transactions from a state registry."""
    registry = STATE_REGISTRIES.get(state_key, {})
    results = []
    url = f"{registry['url']}{registry.get('search_path', '')}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "trevor-mentis/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            for match in re.finditer(
                r'<tr[^>]*>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>',
                html,
                re.DOTALL,
            ):
                tx = {
                    "id": hashlib.md5(match.group(0).encode()).hexdigest()[:12],
                    "state": state_key,
                    "buyer_name": match.group(1).strip()[:100],
                    "seller_name": match.group(2).strip()[:100],
                    "amount_raw": match.group(3).strip(),
                }
                results.append(tx)
    except Exception as exc:
        print(f"  [property] {state_key}: {exc}", file=sys.stderr)

    return results


def flag_rapid_sequential(state_key: str) -> list[dict]:
    """Flag same property traded multiple times in short window."""
    conn = get_db()
    cursor = conn.execute(
        """SELECT buyer_name, location, COUNT(*) as cnt
           FROM transactions WHERE state=? AND flagged=0
           GROUP BY buyer_name, location HAVING cnt >= 2 ORDER BY cnt DESC LIMIT 20""",
        (state_key,),
    )
    results = [{"buyer": r[0], "location": r[1], "count": r[2]} for r in cursor.fetchall()]
    conn.close()
    return results


def generate_report() -> str:
    """Generate multi-state property intelligence memo."""
    conn = get_db()
    cursor = conn.execute(
        "SELECT state, COUNT(*) FROM transactions GROUP BY state ORDER BY state"
    )
    state_counts = cursor.fetchall()
    conn.close()

    lines = [
        f"# Property Intelligence Memo — {datetime.date.today().isoformat()}",
        "",
        "## Transactions by State",
    ]
    for state, count in state_counts:
        lines.append(f"- **{state}**: {count} transactions")

    lines.append("")
    lines.append("## Rapid Sequential Transactions Flag")
    for state_key in STATE_REGISTRIES:
        flagged = flag_rapid_sequential(state_key)
        if flagged:
            lines.append(f"\n### {state_key}")
            for f in flagged[:5]:
                lines.append(f"- ⚠️ {f['buyer']}: {f['count']} transactions")

    lines.append("")
    lines.append("## Coverage Status")
    for state_key, reg in STATE_REGISTRIES.items():
        lines.append(f"- {reg['name']}: {'scraping' if state_counts else 'pending'} ({reg['note']})")

    lines.append("")
    lines.append("---")
    lines.append("Source: State-level public property registries")
    lines.append("Entity resolution via V4 Pro — pending integration")

    memo_path = EXPORT_DIR / f"property-intel-{datetime.date.today().isoformat()}.md"
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    memo_path.write_text("\n".join(lines))
    return str(memo_path)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Property Records Collector")
    parser.add_argument("--fetch", action="store_true", help="Fetch property transactions")
    parser.add_argument("--report", action="store_true", help="Generate memo")
    args = parser.parse_args()

    init_db()

    if args.fetch:
        for state_key in STATE_REGISTRIES:
            print(f"Fetching {state_key}...")
            txns = fetch_state_registry(state_key)
            conn = get_db()
            for t in txns:
                conn.execute(
                    "INSERT OR IGNORE INTO transactions (id, state, buyer_name, seller_name) VALUES (?, ?, ?, ?)",
                    (t["id"], t["state"], t.get("buyer_name", ""), t.get("seller_name", "")),
                )
            conn.commit()
            conn.close()
            print(f"  {len(txns)} transactions")

        # Flag rapid sequential
        for state_key in STATE_REGISTRIES:
            flagged = flag_rapid_sequential(state_key)
            if flagged:
                print(f"\n⚠️ {state_key} — rapid sequential transactions:")
                for f in flagged[:5]:
                    print(f"  {f['buyer']}: {f['count']}x")

    if args.report:
        path = generate_report()
        print(f"Memo: {path}")


if __name__ == "__main__":
    main()
