#!/usr/bin/env python3
"""CENACE Grid Load Collector — fetches hourly load data by control region.

Mexico's electric grid is divided into 9 control regions. CENACE publishes
hourly load data. Anomaly detection flags when load exceeds 200% of rolling
30-day same-hour baseline for >=2 consecutive hours.

Usage:
    python3 collectors/cenace_collector.py --fetch    # Fetch latest data
    python3 collectors/cenace_collector.py --backfill # Backfill 90 days
    python3 collectors/cenace_collector.py --anomalies # Check for anomalies
    python3 collectors/cenace_collector.py --report   # Regional summary
"""

from __future__ import annotations

import csv
import datetime
import json
import os
import pathlib
import sqlite3
import sys
import urllib.error
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "cenace_load.db"
EXPORT_DIR = REPO_ROOT / "exports"

# CENACE control regions and their SIN (Sistema Interconectado Nacional) codes
REGIONS = {
    "BCA": "Baja California (isolated)",
    "BCS": "Baja California Sur (isolated)",
    "NTE": "Norte",
    "NOE": "Noreste",
    "NOC": "Noroeste",
    "OCC": "Occidental",
    "CEN": "Central",
    "ORl": "Oriental",
    "PEN": "Peninsular",
}

# CENACE SIN API endpoint patterns (public)
CENACE_BASE = "https://www.cenace.gob.mx"
CENACE_API = f"{CENACE_BASE}/SIM/OperacionGraficas/PotenciaGenerada/GeneracionReal"

# Anomaly detection parameters
ANOMALY_BASELINE_DAYS = 30
ANOMALY_MULTIPLIER = 2.0  # 200% of baseline
ANOMALY_MIN_CONSECUTIVE = 2  # hours


def init_db() -> None:
    """Initialize SQLite database for load data."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS load_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT NOT NULL,
            timestamp_utc TEXT NOT NULL,
            load_mw REAL NOT NULL,
            fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(region, timestamp_utc)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_load_region_time
        ON load_data(region, timestamp_utc)
    """)
    conn.commit()
    conn.close()


def get_db() -> sqlite3.Connection:
    return sqlite3.connect(str(DB_PATH))


def fetch_region_load(region: str) -> list[dict[str, Any]]:
    """Fetch hourly load data for a CENACE control region."""
    # CENACE public data — attempt API or CSV download
    today = datetime.date.today()
    records = []
    
    # Try to fetch from CENACE public data
    url = f"{CENACE_BASE}/SID/Load/Regional/{region}/{today.strftime('%Y/%m/%d')}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "trevor-mentis/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()
            if resp.headers.get("Content-Type", "").startswith("text/csv"):
                reader = csv.DictReader(content.decode().split("\n"))
                for row in reader:
                    records.append({
                        "region": region,
                        "timestamp_utc": f"{today}T{row.get('hour','00')}:00:00Z",
                        "load_mw": float(row.get("load_mw", 0)),
                    })
    except Exception as exc:
        print(f"  [cenace] {region}: {exc}", file=sys.stderr)
    
    return records


def store_load_data(records: list[dict]) -> int:
    """Store load records in SQLite."""
    conn = get_db()
    count = 0
    for r in records:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO load_data (region, timestamp_utc, load_mw) VALUES (?, ?, ?)",
                (r["region"], r["timestamp_utc"], r["load_mw"]),
            )
            count += conn.total_changes
        except Exception:
            pass
    conn.commit()
    conn.close()
    return count


def detect_anomalies() -> list[dict]:
    """Detect grid load anomalies."""
    conn = get_db()
    cursor = conn.execute("""
        SELECT region, timestamp_utc, load_mw FROM load_data
        ORDER BY region, timestamp_utc
    """)
    rows = cursor.fetchall()
    conn.close()

    anomalies = []
    window: list[tuple[str, str, float]] = []

    for region, ts, load in rows:
        window.append((region, ts, load))
        # Keep only last ANOMALY_BASELINE_DAYS * 24 entries per region
        if len(window) > ANOMALY_BASELINE_DAYS * 24:
            window.pop(0)

        if len(window) >= 24:
            # Compute baseline for same-hour rolling window
            hour = ts[11:13]
            same_hour = [l for r, t, l in window if r == region and t[11:13] == hour]
            if len(same_hour) >= 10:
                baseline = sum(same_hour) / len(same_hour)
                if load > baseline * ANOMALY_MULTIPLIER:
                    consecutive = sum(1 for w in window[-ANOMALY_MIN_CONSECUTIVE:]
                                      if w[1] >= ts and w[0] == region and w[2] > baseline * ANOMALY_MULTIPLIER)
                    if consecutive >= ANOMALY_MIN_CONSECUTIVE:
                        anomalies.append({
                            "region": region,
                            "timestamp": ts,
                            "load_mw": load,
                            "baseline_mw": round(baseline, 1),
                            "anomaly_pct": round((load / baseline - 1) * 100, 1),
                            "severity": "critical" if load > baseline * 3 else "high",
                        })

    return anomalies


def generate_report() -> str:
    """Generate regional summary report."""
    conn = get_db()
    
    lines = ["# CENACE Grid Load Report", f"**Generated:** {datetime.datetime.utcnow().isoformat()[:16]}Z\n"]
    
    for region_code, region_name in REGIONS.items():
        cursor = conn.execute(
            "SELECT COUNT(*), AVG(load_mw), MAX(load_mw), MIN(load_mw) FROM load_data WHERE region=?",
            (region_code,),
        )
        count, avg, mx, mn = cursor.fetchone()
        
        if count and count > 0:
            anomalies = detect_anomalies()
            region_anomalies = [a for a in anomalies if a["region"] == region_code]
            lines.append(f"## {region_name} ({region_code})")
            lines.append(f"- Records: {count}")
            lines.append(f"- Avg load: {avg:.0f} MW")
            lines.append(f"- Peak: {mx:.0f} MW")
            lines.append(f"- Min: {mn:.0f} MW")
            if region_anomalies:
                lines.append(f"- ⚠️ Anomalies: {len(region_anomalies)}")
                for a in region_anomalies[:3]:
                    lines.append(f"  - {a['timestamp'][:16]}Z: {a['load_mw']:.0f} MW ({a['anomaly_pct']:+.0f}% vs baseline)")
            lines.append("")
    
    conn.close()
    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CENACE Grid Load Collector")
    parser.add_argument("--fetch", action="store_true", help="Fetch latest load data")
    parser.add_argument("--backfill", action="store_true", help="Backfill 90 days")
    parser.add_argument("--anomalies", action="store_true", help="Detect anomalies")
    parser.add_argument("--report", action="store_true", help="Generate regional summary")
    args = parser.parse_args()

    init_db()

    if args.fetch:
        total = 0
        for region in REGIONS:
            print(f"  Fetching {region} ({REGIONS[region]})...")
            records = fetch_region_load(region)
            count = store_load_data(records)
            total += len(records)
            print(f"    Stored {len(records)} records")
        print(f"Total: {total} records stored")

    if args.backfill:
        print("Backfill requires historical API access. Using mock data for MVP.")
        total = 0
        conn = get_db()
        for region in REGIONS:
            for day in range(90):
                d = datetime.date.today() - datetime.timedelta(days=day)
                for hour in range(24):
                    ts = f"{d}T{hour:02d}:00:00Z"
                    base_load = {"CEN": 12000, "OCC": 8000, "NTE": 6000, "NOE": 5000, 
                                 "NOC": 4000, "ORl": 3000, "PEN": 2000, "BCA": 1500, "BCS": 800}
                    load = base_load.get(region, 3000) + (hour * 50) + (day * 10)
                    conn.execute(
                        "INSERT OR IGNORE INTO load_data (region, timestamp_utc, load_mw) VALUES (?, ?, ?)",
                        (region, ts, load),
                    )
                    total += 1
            print(f"  Backfilled {region}: 90d x 24h = 2160 records")
        conn.commit()
        conn.close()
        print(f"Total: {total} records")

    if args.anomalies:
        anomalies = detect_anomalies()
        if anomalies:
            print(f"⚠️  {len(anomalies)} anomalies detected:")
            for a in anomalies[:10]:
                print(f"  [{a['severity']}] {a['region']} {a['timestamp'][:16]}Z: {a['load_mw']:.0f} MW ({a['anomaly_pct']:+.0f}%)")
        else:
            print("No anomalies detected (insufficient data or stable grid)")

    if args.report:
        report = generate_report()
        export_path = EXPORT_DIR / f"cenace-report-{datetime.date.today().isoformat()}.md"
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        export_path.write_text(report)
        print(f"Report saved: {export_path}")
        print(report[:500])


if __name__ == "__main__":
    main()
