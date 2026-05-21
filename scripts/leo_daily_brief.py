#!/usr/bin/env python3
"""
LEO Ground Station Daily Brief — separate email to roderick.jones@gmail.com.

Runs the data collectors and assembles a text-only market intelligence brief.
Delivered independently from the main daily intel brief.

Usage:
    python3 scripts/leo_daily_brief.py

Output:
    - Saves to exports/leo-daily-brief-YYYY-MM-DD.txt
    - Sends via Gmail to roderick.jones@gmail.com
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import sys
import base64
import email.mime.text
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LEO_DATA_DIR = REPO_ROOT / "analyst" / "knowledge" / "leo_ground_stations" / "data_feeds"
PRINCIPAL_DATA = REPO_ROOT / "config" / "topics" / "leo_ground_stations" / "_principal_data"
MATON_BASE = "https://gateway.maton.ai/google-mail"
GMAIL_SEND = MATON_BASE + "/gmail/v1/users/me/messages/send"

TO_EMAIL = "roderick.jones@gmail.com"
FROM_EMAIL = "trevor.mentis@gmail.com"


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[leo-brief {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> dict | list | None:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return None
    return None


def load_collector_output(prefix: str) -> dict | None:
    """Load the most recent output from a collector."""
    files = sorted(LEO_DATA_DIR.glob(f"{prefix}-*.json"), reverse=True)
    if files:
        return load_json(files[0])
    return None


def get_site_registry_summary() -> str:
    """Get a one-line summary of the 80-site register."""
    reg = load_json(PRINCIPAL_DATA / "global_risk_register_risk_summary.json")
    if not reg:
        return "Site register not loaded."
    
    # Parse the summary table
    by_risk = {}
    for r in reg:
        risk = r.get("Risk Rating")
        if risk and risk not in ("TOTAL", "By Operator", "By Region", "Operator", "Region"):
            try:
                by_risk[risk] = int(r.get("Count", 0))
            except (ValueError, TypeError):
                pass
    
    total = sum(by_risk.values())
    high = by_risk.get("High", 0)
    crit = by_risk.get("Critical", 0)
    return f"{total} sites tracked | {high} High-risk | {crit} Critical | {by_risk.get('Moderate', 0)} Moderate | {by_risk.get('Low', 0)} Low | {by_risk.get('Negligible', 0)} Negligible"


def build_brief() -> tuple[str, list[str]]:
    """Build the LEO daily brief text. Returns (body, sources)."""
    lines = []
    sources_used = []
    
    date_str = dt.date.today().strftime("%B %d, %Y")
    
    # Header
    lines.append("=" * 72)
    lines.append(f"  LEO GROUND STATION DAILY — {date_str}")
    lines.append("=" * 72)
    lines.append("")
    
    # Site registry summary
    lines.append("═══ SITE REGISTRY STATUS ═══")
    lines.append(get_site_registry_summary())
    lines.append("")
    sources_used.append("Concentric 80-site risk register")
    
    # ── FCC Earth Station Licenses ──
    fcc = load_collector_output("fcc-earth-stations")
    if fcc and fcc.get("status") == "ok":
        lines.append("═══ FCC EARTH STATION LICENSES ═══")
        licensees = fcc.get("licensees_found", [])
        total = fcc.get("total_records", 0)
        matches = fcc.get("matched_known_sites", 0)
        lines.append(f"Recent filings in database: {total}")
        lines.append(f"Unique licensees: {len(licensees)}")
        lines.append(f"Matches against known sites: {matches}")
        lines.append("")
        
        # Show notable licensees (filter out generic ones)
        notable = [l for l in licensees if not any(
            x in l.lower() for x in ["university", "college", "sprint", "cogent", "fordham", "antwan"]
        )]
        if notable:
            lines.append("Notable licensees active:")
            for n in notable[:8]:
                lines.append(f"  • {n}")
            lines.append("")
        
        sources_used.append(f"FCC opendata: {total} earth station records")
    else:
        lines.append("═══ FCC EARTH STATIONS ═══")
        lines.append("No FCC data available yet (first run pending).")
        lines.append("")
    
    # ── Launch Schedule ──
    launch = load_collector_output("launch-schedule")
    if launch and launch.get("status") == "ok":
        lines.append("═══ LAUNCH SCHEDULE — CONSTELLATION SIGNALS ═══")
        lib = launch.get("feeds", {}).get("launch_library", {})
        if isinstance(lib, dict):
            total_launches = lib.get("total_upcoming", "?")
            starlink = lib.get("starlink_launches", 0)
            lines.append(f"Upcoming launches globally: {total_launches}")
            lines.append(f"Starlink launches in queue: {starlink}")
            lines.append("")
            
            # Show next 5 notable launches
            all_launches = lib.get("launches", [])
            lines.append("Next 5 launches:")
            for l in all_launches[:5]:
                name = l.get("name", "?")
                net = (l.get("net") or "?")[:16]
                loc = l.get("location", "?")
                lines.append(f"  • {name} | {net} | {loc}")
            lines.append("")
            
            # Spaceflight Now headlines
            sf = launch.get("feeds", {}).get("spaceflight_now", [])
            if sf:
                lines.append("Latest space industry headlines:")
                for article in sf[:3]:
                    lines.append(f"  • {article.get('title', '?')}")
                lines.append("")
        
        sources_used.append("Spaceflight Now / SpaceDevs Launch Library")
    else:
        lines.append("═══ LAUNCH SCHEDULE ═══")
        lines.append("No launch data available yet (first run pending).")
        lines.append("")
    
    # ── ITU Filings ──
    itu = load_collector_output("itu-filings")
    if itu and itu.get("status") == "ok":
        lines.append("═══ ITU COORDINATION FILINGS ═══")
        lines.append(f"Earth station filings: {itu.get('total_filings', 0)}")
        lines.append("")
        sources_used.append("ITU Space Explorer")
    else:
        lines.append("═══ ITU COORDINATION ═══")
        lines.append("Weekly check runs Mondays. Data pending.")
        lines.append("")
    
    # ── Job Posting Signals ──
    jobs = load_collector_output("job-postings")
    if jobs and jobs.get("status") == "ok":
        lines.append("═══ JOB POSTING SIGNALS ═══")
        for result in jobs.get("search_results", []):
            q = result.get("query", "?")
            hits = result.get("hits", 0)
            err = result.get("error")
            if err:
                lines.append(f"  • '{q}': Error — {err}")
            else:
                status = "🟢 Activity detected" if hits > 0 else "⚪ No recent activity"
                lines.append(f"  • '{q}': {hits} mentions {status}")
        lines.append("")
        sources_used.append("Job board search (15 operators tracked)")
    else:
        lines.append("═══ JOB POSTING SIGNALS ═══")
        lines.append("Weekly check runs Mondays. Data pending.")
        lines.append("")
    
    # ── Sentinel-2 Imagery ──
    img = load_collector_output("sentinel-imagery")
    if img:
        lines.append("═══ SATELLITE IMAGERY CHECK ═══")
        api_configured = img.get("sentinel_api_configured", False)
        if api_configured:
            sites = img.get("sites", [])
            lines.append(f"Sites checked: {img.get('sites_checked', 0)}")
            for s in sites[:5]:
                name = s.get("site", "?")
                risk = s.get("composite_risk", "?")
                lines.append(f"  • {name} (risk: {risk})")
        else:
            lines.append("⚠️ Sentinel Hub API key not configured.")
            lines.append("To enable automated site imagery checks:")
            lines.append("  1. Sign up at sentinel-hub.com")
            lines.append(f"  2. Set SENTINEL_CLIENT_ID and SENTINEL_CLIENT_SECRET")
        lines.append("")
        sources_used.append("Copernicus Sentinel-2")
    
    # ── Market Overview Numbers ──
    lines.append("═══ MARKET SNAPSHOT ═══")
    metrics = load_json(PRINCIPAL_DATA / "market_metrics.json")
    if metrics:
        for m in metrics[:8]:
            metric = m.get("Metric", "")
            current = m.get("Current Value", "")
            projected = m.get("Projected Value", "")
            if current:
                line = f"  • {metric}: {current}"
                if projected:
                    line += f" → {projected} ({m.get('CAGR', '')})"
                lines.append(line)
    lines.append("")
    sources_used.append("Concentric market opportunity assessment")
    
    # ── Recommendations ──
    lines.append("═══ NEWSLETTERS & SOURCES TO TRACK ═══")
    lines.append("To deepen the data feed, subscribe to:")
    lines.append("  • Payload Research (daily space industry newsletter)")
    lines.append("  • SpaceNews (daily, already in RSS rotation)")
    lines.append("  • Via Satellite (weekly industry magazine)")
    lines.append("  • Quilty Analytics (quarterly, paid but best market data)")
    lines.append("  • Novaspace (Euroconsult merger, ground segment reports)")
    lines.append("")
    
    # ── Sources ──
    lines.append("═" * 72)
    lines.append("DATA FEEDS USED")
    lines.append("═" * 72)
    for s in sorted(set(sources_used)):
        lines.append(f"  • {s}")
    lines.append("")
    lines.append(f"-- Trevor | LEO Ground Station Desk | {date_str}")
    lines.append("_Data from public FCC/ITU APIs, launch manifests, job boards, and Copernicus imagery._")
    
    return "\n".join(lines), list(set(sources_used))


def send_gmail(to: str, subject: str, body: str, maton_key: str) -> bool:
    """Send plain-text email via Gmail API through Maton gateway."""
    msg = email.mime.text.MIMEText(body, "plain", "utf-8")
    msg["To"] = to
    msg["From"] = FROM_EMAIL
    msg["Subject"] = subject

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
    payload = json.dumps({"raw": raw}).encode("utf-8")

    req = urllib.request.Request(
        GMAIL_SEND,
        data=payload,
        headers={
            "Authorization": f"Bearer {maton_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            log(f"Sent: {result.get('id', 'unknown')}")
            return True
    except Exception as e:
        log(f"Send failed: {e}")
        return False


def main() -> None:
    maton_key = os.environ.get("MATON_API_KEY", "")
    if not maton_key:
        log("ERROR: MATON_API_KEY not set")
        sys.exit(1)
    
    date_str = dt.date.today().isoformat()
    
    # Build brief
    log("Building LEO daily brief...")
    body, sources = build_brief()
    
    # Save
    exports_dir = REPO_ROOT / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    brief_path = exports_dir / f"leo-daily-brief-{date_str}.txt"
    brief_path.write_text(body)
    log(f"Brief saved: {brief_path} ({len(body)} chars)")
    
    # Send
    subject = f"LEO Ground Station Daily — {date_str}"
    log(f"Sending to {TO_EMAIL}...")
    if send_gmail(TO_EMAIL, subject, body, maton_key):
        log("Delivery successful")
    else:
        log("Delivery FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
