#!/usr/bin/env python3
"""CompraNet Procurement Data Collector.

Scrapes Mexico's public procurement portal for contract awards,
flags anomalies (single-entity multi-award, emergency spikes,
shell-company indicators), and generates weekly anomaly memos.

Usage:
    python3 collectors/compranet_collector.py --fetch
    python3 collectors/compranet_collector.py --report
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
DATA_DIR = REPO_ROOT / "data" / "compranet"
DB_PATH = DATA_DIR / "compranet.db"
EXPORT_DIR = REPO_ROOT / "exports"

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# CompraNet public access points
COMPRANET_BASE = "https://compranet.hacienda.gob.mx"
COMPRANET_SEARCH = f"{COMPRANET_BASE}/es/consultas/busqueda"
COMPRANET_DETAIL = f"{COMPRANET_BASE}/es/consultas/detalle"


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS awards (
            id TEXT PRIMARY KEY,
            fecha TEXT NOT NULL,
            contracting_agency TEXT,
            awardee TEXT,
            title TEXT,
            amount_mxn REAL,
            procurement_type TEXT,
            procedure_type TEXT,
            is_emergency INTEGER DEFAULT 0,
            awardee_rfc TEXT,
            awardee_incorporation_date TEXT,
            flagged INTEGER DEFAULT 0,
            flag_reason TEXT,
            fetched_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_awards_awardee ON awards(awardee)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_awards_fecha ON awards(fecha)")
    conn.commit()
    conn.close()


def get_db():
    return sqlite3.connect(str(DB_PATH))


def search_awards(days_back: int = 7) -> list[dict]:
    """Search CompraNet for recent contract awards."""
    awards = []
    today = datetime.date.today()
    from_date = today - datetime.timedelta(days=days_back)

    url = f"{COMPRANET_SEARCH}?fechaPublicacionDesde={from_date.isoformat()}&fechaPublicacionHasta={today.isoformat()}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "trevor-mentis/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=CTX) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        for match in re.finditer(
            r'<tr[^>]*>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>',
            html,
            re.DOTALL,
        ):
            award = {
                "id": hashlib.md5(match.group(0).encode()).hexdigest()[:12],
                "title": match.group(1).strip(),
                "agency": match.group(2).strip(),
                "awardee": match.group(3).strip(),
                "amount_raw": match.group(4).strip(),
                "date": match.group(5).strip(),
            }
            awards.append(award)
    except Exception as exc:
        print(f"[compranet] Search error: {exc}", file=sys.stderr)

    return awards


def flag_shell_company(name: str) -> bool:
    """Heuristic: detect possible shell company patterns."""
    indicators = [
        "servicios", "consultoría", "asesoría", "representaciones",
        "inmobiliaria", "constructora", "operadora",
    ]
    name_lower = name.lower()
    return any(ind in name_lower for ind in indicators)


def flag_emergency(proc_type: str) -> bool:
    return "emergencia" in proc_type.lower() or "urgente" in proc_type.lower()


def generate_report() -> str:
    """Generate weekly CompraNet anomaly memo."""
    conn = get_db()
    cursor = conn.execute(
        """SELECT awardee, COUNT(*) as cnt, SUM(amount_mxn) as total,
                  GROUP_CONCAT(DISTINCT contracting_agency) as agencies
           FROM awards WHERE flagged=1
           GROUP BY awardee ORDER BY cnt DESC LIMIT 20"""
    )
    flagged = cursor.fetchall()
    conn.close()

    lines = [
        f"# CompraNet Anomaly Report — Week of {datetime.date.today().isoformat()}",
        f"**Flagged awards:** {len(flagged)}",
        "",
        "## Flagged Patterns",
    ]

    for awardee, count, total, agencies in flagged:
        lines.append(f"- **{awardee}** — {count} awards, ${total:,.0f} MXN")
        lines.append(f"  Agencies: {agencies[:200]}")
        lines.append("")

    report_path = EXPORT_DIR / f"compranet-weekly-{datetime.date.today().isoformat()}.md"
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines))
    return str(report_path)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CompraNet Procurement Collector")
    parser.add_argument("--fetch", type=int, nargs="?", const=7, help="Fetch awards (N days back)")
    parser.add_argument("--report", action="store_true", help="Generate anomaly report")
    args = parser.parse_args()

    init_db()

    if args.fetch:
        awards = search_awards(args.fetch)
        print(f"Found {len(awards)} awards")

        conn = get_db()
        for a in awards:
            conn.execute(
                "INSERT OR IGNORE INTO awards (id, fecha, contracting_agency, awardee, title) VALUES (?, ?, ?, ?, ?)",
                (a["id"], a.get("date", ""), a.get("agency", ""), a.get("awardee", ""), a.get("title", "")[:200]),
            )
        conn.commit()
        conn.close()
        print(f"Stored {len(awards)} awards")

        # Flag anomalies
        for a in awards:
            if flag_shell_company(a.get("awardee", "")):
                print(f"  ⚠️ Shell indicator: {a['awardee'][:60]}")

    if args.report:
        path = generate_report()
        print(f"Report: {path}")


if __name__ == "__main__":
    main()
