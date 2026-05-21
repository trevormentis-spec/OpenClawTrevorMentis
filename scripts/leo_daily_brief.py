#!/usr/bin/env python3
"""
LEO Ground Station Daily Brief — DeepSeek V4 Pro analysis, Gmail delivery.

Collects data from FCC, launch schedules, ITU filings, job boards, Sentinel-2,
then routes to DeepSeek V4 Pro for analyst-quality synthesis.
Delivered to roderick.jones@gmail.com independently from the main brief.

Usage:
    python3 scripts/leo_daily_brief.py
"""
from __future__ import annotations

import base64
import datetime as dt
import email.mime.text
import json
import os
import pathlib
import sys
import urllib.request
from scripts.report_memory import log_report

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LEO_DATA_DIR = REPO_ROOT / "analyst" / "knowledge" / "leo_ground_stations" / "data_feeds"
PRINCIPAL_DATA = REPO_ROOT / "config" / "topics" / "leo_ground_stations" / "_principal_data"
MATON_BASE = "https://gateway.maton.ai/google-mail"
GMAIL_SEND = MATON_BASE + "/gmail/v1/users/me/messages/send"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

TO_EMAIL = "roderick.jones@gmail.com"
FROM_EMAIL = "trevor.mentis@gmail.com"


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[leo-brief {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path):
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return None
    return None


def load_collector(prefix: str) -> dict | None:
    files = sorted(LEO_DATA_DIR.glob(f"{prefix}-*.json"), reverse=True)
    if files:
        return load_json(files[0])
    return None


def call_deepseek(system: str, user: str) -> str:
    """Call DeepSeek V4 Pro via Direct API."""
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        # Try reading from .env
        env_path = REPO_ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text().split("\n"):
                if "DEEPSEEK_API_KEY=" in line and "V4" not in line:
                    key = line.split("=", 1)[1].strip().strip("'\"")
                    break

    if not key:
        return "ERROR: No DeepSeek API key"

    payload = json.dumps({
        "model": "deepseek-v4-pro",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": 4096,
        "temperature": 0.3,
    }).encode()

    req = urllib.request.Request(
        DEEPSEEK_URL,
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read())
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        return f"ERROR: {e}"


def build_data_packet() -> dict:
    """Collect all data feeds into a structured packet for the LLM."""
    packet = {
        "date": dt.date.today().isoformat(),
        "site_register": {},
        "fcc": {},
        "launches": {},
        "itu": {},
        "jobs": {},
        "imagery": {},
        "market_metrics": [],
    }

    # Site register summary
    reg = load_json(PRINCIPAL_DATA / "global_risk_register_risk_summary.json")
    if reg:
        by_risk = {}
        for r in reg:
            risk = r.get("Risk Rating")
            if risk not in ("TOTAL", "By Operator", "By Region", "Operator", "Region", None):
                try:
                    by_risk[risk] = int(r.get("Count", 0))
                except (ValueError, TypeError):
                    pass
        packet["site_register"]["by_risk"] = by_risk
        packet["site_register"]["total"] = sum(by_risk.values())

    # FCC
    fcc = load_collector("fcc-earth-stations")
    if fcc and fcc.get("status") == "ok":
        packet["fcc"] = {
            "total_records": fcc.get("total_records", 0),
            "licensees": fcc.get("licensees_found", []),
            "notable_licensees": [l for l in fcc.get("licensees_found", [])
                                  if not any(x in l.lower() for x in ["university", "antwan"])],
        }

    # Launches
    launch = load_collector("launch-schedule")
    if launch and launch.get("status") == "ok":
        lib = launch.get("feeds", {}).get("launch_library", {})
        if isinstance(lib, dict):
            packet["launches"] = {
                "total_upcoming": lib.get("total_upcoming", 0),
                "starlink_launches": lib.get("starlink_launches", 0),
                "next_5": lib.get("launches", [])[:5],
            }

    # ITU
    itu = load_collector("itu-filings")
    if itu and itu.get("status") == "ok":
        packet["itu"]["filings"] = itu.get("total_filings", 0)

    # Jobs
    jobs = load_collector("job-postings")
    if jobs and jobs.get("status") == "ok":
        active_queries = [r for r in jobs.get("search_results", [])
                          if r.get("hits", 0) > 0]
        packet["jobs"]["active_queries"] = active_queries

    # Imagery
    img = load_collector("sentinel-imagery")
    if img:
        api_ok = img.get("sentinel_api_configured", False)
        packet["imagery"] = {
            "api_configured": api_ok,
            "sites_checked": img.get("sites_checked", 0),
            "sites_with_data": img.get("sites_with_recent_imagery", 0),
        }

    # Market metrics (first few as context)
    metrics = load_json(PRINCIPAL_DATA / "market_metrics.json")
    if metrics:
        packet["market_metrics"] = [
            {"metric": m.get("Metric"), "current": m.get("Current Value"), "projected": m.get("Projected Value")}
            for m in metrics[:6]
        ]

    return packet


def build_brief() -> tuple[str, list[str]]:
    """Build the LEO brief using DeepSeek V4 Pro for analysis."""
    date_str = dt.date.today().strftime("%B %d, %Y")
    packet = build_data_packet()
    data_json = json.dumps(packet, indent=2)

    system_prompt = (
        "You are Trevor, an intelligence analyst covering the LEO ground station market. "
        "You brief Roderick directly — analyst-to-analyst, signal-dense, opinionated. "
        "You have access to several data feeds: FCC earth station licenses, launch schedules, "
        "ITU coordination filings, job posting scans, Sentinel-2 satellite imagery, "
        "and a curated market metrics database. "
        "Write a text-only brief (no markdown, no formatting codes). "
        "Structure it as:\n\n"
        "1. EXECUTIVE SUMMARY — what changed, what it means, what to watch (2 paragraphs)\n"
        "2. FCC LICENSES — notable new filings or licensees, trends (if interesting; skip if quiet)\n"
        "3. CONSTELLATION SIGNALS — launch activity and what it means for ground capacity\n"
        "4. SITE & IMAGERY — risk register status, any Sentinel-2 findings\n"
        "5. MARKET SIGNALS — job postings, ITU activity, other indicators\n"
        "6. BOTTOM LINE — what Roderick should do or watch (1 paragraph)\n\n"
        "Rules: cite specific numbers from the data. "
        "If a section has nothing new, say so briefly rather than pad. "
        "Keep the whole brief under 2500 words. "
        "Do NOT use markdown headers — use plain text with '═══ SECTION ═══' style separators. "
        "Do NOT include a sources section — data provenance is listed at the bottom."
    )

    user_prompt = (
        f"LEO Ground Station data for {date_str}.\n\n"
        f"Here is the collected data from all feeds:\n\n{data_json}\n\n"
        f"Produce the brief. Be analytical, not descriptive. "
        f"If the data shows nothing new, say that honestly. "
        f"This is for a domain expert — no hand-holding."
    )

    log(f"Calling DeepSeek V4 Pro with {len(data_json)} bytes of data...")
    analysis = call_deepseek(system_prompt, user_prompt)

    if analysis.startswith("ERROR:"):
        log(f"DeepSeek call failed: {analysis}")
        return f"LEO Brief for {date_str}\n\nError generating analysis: {analysis}\n\nCheck API key and try again.", ["deepseek-v4-pro"]

    # Build the final brief
    lines = []
    lines.append("=" * 72)
    lines.append(f"  LEO GROUND STATION DAILY — {date_str}")
    lines.append("=" * 72)
    lines.append("")
    lines.append(analysis)
    lines.append("")
    lines.append("═" * 72)
    lines.append("DATA SOURCES")
    lines.append("═" * 72)
    lines.append("  • FCC opendata: Protected FSS earth station registrations")
    lines.append("  • Launch Library 2: Upcoming global launch manifest")
    lines.append("  • Spaceflight Now: Space industry RSS feed")
    lines.append("  • Copernicus Sentinel-2: Satellite imagery via Data Space Ecosystem")
    lines.append("  • Concentric 80-site risk register + market opportunity assessment")
    lines.append("  • Job board search: 15 operators, 4 query types")
    lines.append(f"  • Analysis: DeepSeek V4 Pro (deepseek/deepseek-v4-pro) via Direct API")
    lines.append("")
    lines.append(f"-- Trevor | LEO Ground Station Desk | {date_str}")

    sources = [
        "FCC opendata earth station records",
        "Launch Library 2 API",
        "Spaceflight Now RSS",
        "Copernicus Sentinel-2 (Data Space Ecosystem)",
        "Concentric 80-site risk register",
        "Concentric market opportunity assessment",
        "DeepSeek V4 Pro analysis",
    ]

    return "\n".join(lines), sources


def send_gmail(to: str, subject: str, body: str, maton_key: str) -> bool:
    msg = email.mime.text.MIMEText(body, "plain", "utf-8")
    msg["To"] = to
    msg["From"] = FROM_EMAIL
    msg["Subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
    payload = json.dumps({"raw": raw}).encode("utf-8")
    req = urllib.request.Request(
        GMAIL_SEND,
        data=payload,
        headers={"Authorization": f"Bearer {maton_key}", "Content-Type": "application/json"},
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
    log("Building LEO daily brief with DeepSeek V4 Pro analysis...")
    body, sources = build_brief()

    exports_dir = REPO_ROOT / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    brief_path = exports_dir / f"leo-daily-brief-{date_str}.txt"
    brief_path.write_text(body)
    log(f"Saved: {brief_path} ({len(body)} chars)")

    subject = f"LEO Ground Station Daily — {date_str}"
    log(f"Sending to {TO_EMAIL}...")
    if send_gmail(TO_EMAIL, subject, body, maton_key):
        log("Delivery successful")
        log_report("leo_daily_brief", date_str, str(brief_path), body[:200],
                   len(body.split()), model="deepseek-v4-pro")
    else:
        log("Delivery FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
