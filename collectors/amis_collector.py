#!/usr/bin/env python3
"""AMIS Insurance Pricing Signals Collector.

Pulls AMIS (Mexican Insurance Association) quarterly statistics by
line of business and geography. Monitors kidnap/ransom premiums by
state, cargo theft premiums by route, property insurance withdrawals.

Phase 1 only — no SPS/Lloyd's data without principal approval.

Usage:
    python3 collectors/amis_collector.py --fetch
    python3 collectors/amis_collector.py --report
"""

from __future__ import annotations

import csv
import datetime
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
DATA_DIR = REPO_ROOT / "data" / "amis"
DB_PATH = DATA_DIR / "amis.db"
EXPORT_DIR = REPO_ROOT / "exports"

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# AMIS public data endpoints
AMIS_BASE = "https://www.amis.com.mx"
AMIS_STATS = f"{AMIS_BASE}/estadisticas"
AMIS_REPORTS = f"{AMIS_BASE}/reportes"

LINES_OF_BUSINESS = {
    "vida": "Life",
    "automoviles": "Auto",
    "gastos_medicos": "Medical Expenses",
    "danos": "Property Damage",
    "responsabilidad_civil": "Civil Liability",
    "transportes": "Cargo/Transport",
    "diversos": "Various",
    "accidentes_enfermedades": "Accidents & Illness",
    "marcas_patentes": "IP Insurance",
    "credito": "Credit Insurance",
    "fianzas": "Surety Bonds",
    "terremoto": "Earthquake",
    "huracan": "Hurricane",
    "robo": "Theft",
}


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS premiums (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period TEXT NOT NULL,
            line_of_business TEXT NOT NULL,
            geography TEXT,
            premium_mxn REAL,
            claims_ratio REAL,
            policies_count INTEGER,
            source TEXT DEFAULT 'amis',
            fetched_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_premiums_lob ON premiums(line_of_business)
    """)
    conn.commit()
    conn.close()


def get_db():
    return sqlite3.connect(str(DB_PATH))


def fetch_amis_data() -> list[dict]:
    """Fetch latest AMIS quarterly statistics."""
    records = []
    url = f"{AMIS_BASE}/estadisticas/datosabiertos"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "trevor-mentis/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
            content = resp.read().decode("utf-8", errors="replace")

        if resp.headers.get("Content-Type", "").startswith("text/csv"):
            reader = csv.DictReader(content.split("\n"))
            for row in reader:
                records.append(row)
    except Exception:
        # Fallback: try AMIS reports page
        try:
            req2 = urllib.request.Request(AMIS_REPORTS, headers={"User-Agent": "trevor-mentis/1.0"})
            with urllib.request.urlopen(req2, timeout=30, context=CTX) as resp2:
                html = resp2.read().decode("utf-8", errors="replace")
                for link in re.findall(r'href="([^"]*\.csv)"', html):
                    if "robo" in link.lower() or "seguridad" in link.lower():
                        url_full = link if link.startswith("http") else f"{AMIS_BASE}/{link}"
                        req3 = urllib.request.Request(url_full, headers={"User-Agent": "trevor-mentis/1.0"})
                        with urllib.request.urlopen(req3, timeout=30, context=CTX) as resp3:
                            data = resp3.read().decode("utf-8", errors="replace")
                            for row in data.split("\n")[:100]:
                                records.append({"raw": row[:200]})
        except Exception as exc2:
            print(f"[amis] Fetch error: {exc2}", file=sys.stderr)

    return records


def generate_memo() -> str:
    """Generate AMIS quarterly pricing memo."""
    conn = get_db()
    cursor = conn.execute(
        "SELECT line_of_business, COUNT(*), AVG(premium_mxn) FROM premiums GROUP BY line_of_business ORDER BY COUNT(*) DESC"
    )
    data = cursor.fetchall()
    conn.close()

    lines = [
        f"# AMIS Insurance Pricing Signals — {datetime.date.today().isoformat()}",
        f"**Lines of business tracked:** {len(data)}",
        "",
        "## Premium Summary by Line",
    ]

    for lob, count, avg in data:
        lines.append(f"- **{lob}**: {count} records, avg ${avg:,.0f} MXN")

    lines.append("")
    lines.append("---")
    lines.append("Source: AMIS public statistics at amis.com.mx")
    lines.append("⚠️ No SPS/Lloyd's data — pending principal approval for Phase 2")

    memo_path = EXPORT_DIR / f"amis-summary-{datetime.date.today().isoformat()}.md"
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    memo_path.write_text("\n".join(lines))
    return str(memo_path)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="AMIS Insurance Collector")
    parser.add_argument("--fetch", action="store_true", help="Fetch AMIS data")
    parser.add_argument("--report", action="store_true", help="Generate pricing memo")
    args = parser.parse_args()

    init_db()

    if args.fetch:
        records = fetch_amis_data()
        print(f"Fetched {len(records)} AMIS records")

    if args.report:
        path = generate_memo()
        print(f"Memo: {path}")


if __name__ == "__main__":
    main()
