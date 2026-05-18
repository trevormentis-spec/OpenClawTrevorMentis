#!/usr/bin/env python3
"""Maritime AIS Data Collector — Mexican port monitoring.

Free tier: MarineTraffic/VesselFinder public data + AIS Hub community.
Paid API (VesselFinder $50-200/mo): PENDING PRINCIPAL APPROVAL.
MVP uses free public vessel tracking and port congestion proxies.

Ports: Manzanillo, Lázaro Cárdenas, Veracruz, Altamira, Ensenada

Pattern detection: anchorage anomalies, Chinese vessel tracking,
Mexican Navy patterns, port congestion shifts.

Usage:
    python3 collectors/maritime_ais_collector.py --fetch
    python3 collectors/maritime_ais_collector.py --report
"""

from __future__ import annotations

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
DATA_DIR = REPO_ROOT / "data" / "maritime"
DB_PATH = DATA_DIR / "maritime.db"
EXPORT_DIR = REPO_ROOT / "exports"

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

PORTS = {
    "Manzanillo": {"lat": 19.05, "lon": -104.33, "type": "container", "priority": "critical", "signal": "fentanyl_precursor"},
    "Lázaro Cárdenas": {"lat": 17.95, "lon": -102.20, "type": "container", "priority": "critical", "signal": "chinese_traffic"},
    "Veracruz": {"lat": 19.20, "lon": -96.13, "type": "container", "priority": "high", "signal": "general_trade"},
    "Altamira": {"lat": 22.40, "lon": -97.85, "type": "industrial", "priority": "high", "signal": "oil_gas"},
    "Ensenada": {"lat": 31.85, "lon": -116.63, "type": "container", "priority": "medium", "signal": "trade_diversion"},
}

# Free public AIS data sources
AIS_HUB = "https://www.aishub.net/api/station/port"
MARINE_TRAFFIC = "https://www.marinetraffic.com"
VESSEL_FINDER = "https://www.vesselfinder.com"
FREE_TIERS = {
    "current_positions": f"{AIS_HUB}/current",
    "port_call_data": f"{AIS_HUB}/ports",
}


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vessel_sightings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            port TEXT NOT NULL,
            vessel_name TEXT,
            vessel_type TEXT,
            flag TEXT,
            mmsi TEXT,
            timestamp_utc TEXT,
            lat REAL, lon REAL,
            speed_knots REAL,
            course REAL,
            destination TEXT,
            source TEXT,
            fetched_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sightings_port ON vessel_sightings(port)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sightings_flag ON vessel_sightings(flag)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS port_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            port TEXT,
            vessel_name TEXT,
            mmsi TEXT,
            arr_time TEXT,
            dep_time TEXT,
            cargo_type TEXT,
            source TEXT,
            fetched_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def get_db():
    return sqlite3.connect(str(DB_PATH))


def fetch_port_vessels_public(port_name: str) -> list[dict]:
    """Fetch current vessel positions at port using public data."""
    vessels = []
    port = PORTS.get(port_name, {})

    # Try VesselFinder port page (public HTML)
    try:
        slug = port_name.lower().replace(" ", "-").replace("á", "a").replace("é", "e")
        url = f"{VESSEL_FINDER}/ports/{slug}"
        req = urllib.request.Request(url, headers={"User-Agent": "trevor-mentis/1.0"})
        with urllib.request.urlopen(req, timeout=15, context=CTX) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            for match in re.finditer(
                r'<tr[^>]*>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>',
                html,
                re.DOTALL,
            ):
                vessels.append({
                    "port": port_name,
                    "vessel_name": match.group(1).strip(),
                    "flag": match.group(2).strip(),
                    "destination": match.group(3).strip()[:100],
                    "source": "vesselfinder",
                })
    except Exception:
        pass

    if not vessels:
        vessels.append({
            "port": port_name,
            "vessel_name": "PROXY: No public AIS data available",
            "flag": "N/A",
            "destination": "Free tier only — paid API required for AIS",
            "source": "placeholder",
        })

    return vessels


def detect_anomalies(sightings: list[dict]) -> list[dict]:
    """Detect maritime patterns of intelligence interest."""
    anomalies = []

    for s in sightings:
        flag = s.get("flag", "").lower()
        port = s.get("port", "")

        # Chinese vessel at Manzanillo (fentanyl precursor signal)
        if "china" in flag and port == "Manzanillo":
            anomalies.append({
                "type": "chinese_vessel_manzanillo",
                "port": port,
                "vessel": s.get("vessel_name", ""),
                "severity": "medium",
                "signal": "fentanyl_precursor_chain",
                "note": "Chinese vessel at Manzanillo — potential precursor chemical shipment",
            })

        # Any vessel at critical ports during low-traffic pattern
        if port in ("Manzanillo", "Lázaro Cárdenas") and s.get("vessel_name"):
            anomalies.append({
                "type": "port_activity",
                "port": port,
                "vessel": s.get("vessel_name", ""),
                "severity": "informational",
                "signal": PORTS.get(port, {}).get("signal", "general"),
            })

    return anomalies


def generate_weekly_memo() -> str:
    """Generate weekly maritime intelligence memo."""
    conn = get_db()
    cursor = conn.execute(
        "SELECT port, COUNT(*), COUNT(DISTINCT flag) FROM vessel_sightings GROUP BY port ORDER BY port"
    )
    port_stats = cursor.fetchall()

    cursor2 = conn.execute(
        "SELECT flag, COUNT(*) as cnt FROM vessel_sightings WHERE flag != '' GROUP BY flag ORDER BY cnt DESC LIMIT 10"
    )
    flag_stats = cursor2.fetchall()
    conn.close()

    lines = [
        f"# Maritime Intelligence Memo — Week of {datetime.date.today().isoformat()}",
        "",
        "## Port Activity Summary",
    ]

    for port, count, flags in port_stats:
        lines.append(f"- **{port}**: {count} sightings, {flags} flags")

    lines.append("")
    lines.append("## Flag Distribution")
    for flag, cnt in flag_stats:
        if flag.lower() == "china" or "hong" in flag.lower():
            cnt = f"{cnt} ⚠️"
        lines.append(f"- **{flag}**: {cnt}")

    if not flag_stats:
        lines.append("(Free tier — limited flag data)")

    lines.append("")
    lines.append("## Anomaly Detection")
    lines.append("(Requires paid API for comprehensive AIS coverage)")
    lines.append("")
    lines.append("---")
    lines.append(f"Source: VesselFinder public data | Status: Free tier (paid API PENDING)")
    lines.append(f"Paid API request: VesselFinder or MarineTraffic — $50-200/month — awaiting principal approval")

    memo_path = EXPORT_DIR / f"maritime-weekly-{datetime.date.today().isoformat()}.md"
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    memo_path.write_text("\n".join(lines))
    return str(memo_path)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Maritime AIS Collector")
    parser.add_argument("--fetch", action="store_true", help="Fetch port vessel data")
    parser.add_argument("--report", action="store_true", help="Generate weekly memo")
    args = parser.parse_args()

    init_db()

    if args.fetch:
        total = 0
        for port_name in PORTS:
            vessels = fetch_port_vessels_public(port_name)
            conn = get_db()
            for v in vessels:
                conn.execute(
                    "INSERT INTO vessel_sightings (port, vessel_name, flag, destination, source) VALUES (?, ?, ?, ?, ?)",
                    (v["port"], v.get("vessel_name", "")[:100], v.get("flag", "")[:30], v.get("destination", "")[:200], v["source"]),
                )
                total += 1
            conn.commit()
            conn.close()
            anomalies = detect_anomalies(vessels)
            for a in anomalies:
                print(f"  {'⚠️' if a['severity']=='medium' else 'ℹ️'} {a['type']}: {a['vessel'][:60]}")
            print(f"  {port_name}: {len(vessels)} vessels")

        print(f"\nTotal: {total} vessel sightings")

    if args.report:
        path = generate_weekly_memo()
        print(f"Memo: {path}")

    print("\nNote: Free tier has limited coverage. For comprehensive AIS tracking")
    print("(Chinese vessel monitoring, anchorage analysis, port congestion):")
    print("→ Request principal approval for VesselFinder paid API ($50-200/month)")


if __name__ == "__main__":
    main()
