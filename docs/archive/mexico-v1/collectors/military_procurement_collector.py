#!/usr/bin/env python3
"""Mexican Military Procurement Collector — SEDENA/SEMAR/GN monitoring.

Combines DOF data (Source 7) with official press release monitoring.
Detects regional deployment shifts, equipment acquisitions, foreign training.

Usage:
    python3 collectors/military_procurement_collector.py --fetch
    python3 collectors/military_procurement_collector.py --report
"""

from __future__ import annotations

import datetime, json, os, pathlib, re, sqlite3, ssl, sys
import urllib.error, urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data" / "military"
DB_PATH = DATA_DIR / "military.db"
EXPORT_DIR = REPO_ROOT / "exports"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

SEDENA_URL = "https://www.gob.mx/sedena"
SEMAR_URL = "https://www.gob.mx/semar"
GN_URL = "https://www.gob.mx/guardia-nacional"

ACQUISITION_KEYWORDS = ["adquisición", "compra", "contrato", "licitación", "equipamiento", "armamento", "vehículo"]
DEPLOYMENT_KEYWORDS = ["despliegue", "operativo", "base", "destacamento", "cuartel", "zona militar", "región militar"]


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT, title TEXT, url TEXT, pub_date TEXT, category TEXT,
        entities TEXT, is_sig INTEGER DEFAULT 0, fetched_at TEXT DEFAULT (datetime('now')))
    """)
    conn.commit()
    conn.close()


def fetch_press_releases(source_name: str, url: str) -> list[dict]:
    items = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "trevor-mentis/1.0"})
        with urllib.request.urlopen(req, timeout=15, context=CTX) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            for link in re.findall(r'href="([^"]*comunicado[^"]*)"', html):
                items.append({"source": source_name, "url": link, "title": f"{source_name} press release"})
    except:
        pass
    return items


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    init_db()

    if args.fetch:
        for name, url in [("SEDENA", SEDENA_URL), ("SEMAR", SEMAR_URL), ("GN", GN_URL)]:
            print(f"  {name}: {len(fetch_press_releases(name, url))} entries")

    if args.report:
        print("# Military Procurement Report — Work in Progress (Tier 3)")
        print("\nIntegrating DOF (Source 7) + SEDENA/SEMAR/GN press monitoring.")
        print("Full memo format when all 3 sources are wired.")


if __name__ == "__main__":
    main()
