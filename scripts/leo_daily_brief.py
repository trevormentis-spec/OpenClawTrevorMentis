#!/usr/bin/env python3
# GATE_EXEMPT: direct API endpoints required for LLM calls without SDK wrapper
"""
LEO Ground Station Daily Brief — DeepSeek V4 Pro analysis, AgentMail delivery.

Collects data from FCC, launch schedules, ITU filings, job boards, Sentinel-2,
then routes to DeepSeek V4 Pro for analyst-quality synthesis.
Delivered via AgentMail (trevor_mentis@agentmail.to → roderick.jones@gmail.com).

Usage:
    python3 scripts/leo_daily_brief.py
    python3 scripts/leo_daily_brief.py --dry-run    # preview only, no send
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.report_memory import log_report

LEO_DATA_DIR = REPO_ROOT / "analyst" / "knowledge" / "leo_ground_stations" / "data_feeds"
PRINCIPAL_DATA = REPO_ROOT / "config" / "topics" / "leo_ground_stations" / "_principal_data"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
AGENTMAIL_SENDER = "trevor_mentis@agentmail.to"
TO_EMAIL = "roderick.jones@gmail.com"
SUBJECT_PREFIX = "🛰️ LEO Ground Station Daily"


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


def get_api_key(key_name: str) -> str:
    key = os.environ.get(key_name, "")
    if key:
        return key
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().split("\n"):
            if line.startswith(f"{key_name}="):
                return line.split("=", 1)[1].strip().strip("'\"")
    return ""


def call_deepseek(system: str, user: str) -> str:
    key = get_api_key("DEEPSEEK_API_KEY")
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

    # Market metrics
    metrics = load_json(PRINCIPAL_DATA / "market_metrics.json")
    if metrics:
        packet["market_metrics"] = [
            {"metric": m.get("Metric"), "current": m.get("Current Value"), "projected": m.get("Projected Value")}
            for m in metrics[:6]
        ]

    return packet


def build_brief() -> tuple[str, str, list[str]]:
    """Build the LEO brief using DeepSeek V4 Pro for analysis.
    Returns (full_body, analysis_text, sources_list).
    """
    date_str = dt.date.today().strftime("%B %d, %Y")
    packet = build_data_packet()
    data_json = json.dumps(packet, indent=2)

    system_prompt = (
        "You are Trevor, an intelligence analyst covering the LEO ground station market. "
        "You brief Roderick directly — analyst-to-analyst, signal-dense, opinionated. "
        "You have access to several data feeds: FCC earth station licenses, launch schedules, "
        "ITU coordination filings, job posting scans, Sentinel-2 satellite imagery, "
        "and a curated market metrics database. "
        "Write an analysis. Structure it as:\n\n"
        "1. EXECUTIVE SUMMARY — what changed, what it means, what to watch (2 paragraphs)\n"
        "2. FCC LICENSES — notable new filings or licensees, trends (if interesting; skip if quiet)\n"
        "3. CONSTELLATION SIGNALS — launch activity and what it means for ground capacity\n"
        "4. SITE & IMAGERY — risk register status, any Sentinel-2 findings\n"
        "5. MARKET SIGNALS — job postings, ITU activity, other indicators\n"
        "6. BOTTOM LINE — what Roderick should do or watch (1 paragraph)\n\n"
        "Rules: cite specific numbers from the data. "
        "If a section has nothing new, say so briefly rather than pad. "
        "Keep the whole brief under 2500 words. "
        "Use plain text with '═══ SECTION ═══' separators between sections. "
        "Do NOT use markdown. Do NOT include a sources section."
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
        return f"LEO Brief for {date_str}\n\nError generating analysis: {analysis}\n\nCheck API key and try again.", analysis, ["deepseek-v4-pro"]

    # Build plain text version (for local save)
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

    return "\n".join(lines), analysis, sources


def analysis_to_html(analysis: str, date_str: str) -> str:
    """Convert the plain-text analysis into a well-formatted HTML email."""
    # Escape HTML
    text = analysis.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Convert ═══ SECTION ═══ to styled headers
    def section_replacer(m):
        name = m.group(1).strip()
        return f'</div><h2 style="color:#1a5276;border-bottom:2px solid #3498db;padding-bottom:6px;margin-top:30px;font-size:18px">{name}</h2><div style="padding-left:10px">'

    text = re.sub(r'═+ ([^═]+) ═+', section_replacer, text)
    text = re.sub(r'═══ ([^═]+) ═══', section_replacer, text)

    # Handle numbered sections
    text = re.sub(r'(\d+)\.\s+([A-Z][A-Z /-]+)', r'<h3 style="color:#2c3e50;margin-top:20px;font-size:15px">\1. \2</h3>', text)

    # Bullet points
    text = re.sub(r'^  • ', '<li>', text, flags=re.MULTILINE)
    text = re.sub(r'^• ', '<li>', text, flags=re.MULTILINE)
    text = re.sub(r'^  - ', '<li>', text, flags=re.MULTILINE)

    # Wrap bullet groups in <ul>
    text = re.sub(r'(<li>[^\n]+(?:<li>[^\n]+)*)', r'<ul style="padding-left:20px">\1</ul>', text)

    # Line breaks
    text = text.replace("\n\n", "<br><br>")
    text = text.replace("\n", "<br>")

    # Sources section at the bottom
    text = re.sub(
        r'(DATA SOURCES.*)',
        r'<div style="margin-top:30px;padding:15px;background:#f5f6fa;border-radius:8px;font-size:12px;color:#666">\1</div>',
        text,
        flags=re.DOTALL,
    )

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;max-width:680px;margin:0 auto;padding:20px;color:#2c3e50;line-height:1.6;font-size:15px;background:#fafbfc">

<div style="text-align:center;padding:20px 0 10px">
  <h1 style="color:#1a5276;font-size:24px;margin:0">🛰️ LEO Ground Station Daily</h1>
  <p style="color:#7f8c8d;font-size:13px;margin:4px 0">{date_str} — Trevor, LEO Desk</p>
</div>

<hr style="border:none;border-top:3px solid #3498db;margin:10px 0 25px">

<div>
{text}
</div>

<hr style="border:none;border-top:1px solid #ddd;margin:30px 0 15px">
<div style="text-align:center;font-size:11px;color:#999">
  Trevor — Threat Research &amp; Evaluation Virtual Operations Resource<br>
  Daily automated brief. Reply to trevor_mentis@agentmail.to
</div>

</body></html>"""

    return html


def send_agentmail(to: str, subject: str, html_body: str, text_body: str) -> bool:
    """Send via AgentMail SDK with HTML + plain text."""
    api_key = get_api_key("AGENTMAIL_API_KEY")
    if not api_key:
        log("ERROR: AGENTMAIL_API_KEY not set")
        return False

    try:
        from agentmail import AgentMail
        client = AgentMail(api_key=api_key)
        result = client.inboxes.messages.send(
            inbox_id=AGENTMAIL_SENDER,
            to=to,
            subject=subject,
            html=html_body,
            text=text_body,
        )
        msg_id = getattr(result, 'id', None) or getattr(result, 'message_id', 'unknown')
        log(f"Sent via AgentMail: message_id={msg_id}")
        return True
    except Exception as e:
        log(f"AgentMail send failed: {e}")
        return False


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="LEO Ground Station Daily Brief")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no send")
    parser.add_argument("--skip-qc", action="store_true", help=argparse.SUPPRESS)  # hidden, dev only
    args = parser.parse_args()

    date_str = dt.date.today().isoformat()
    date_display = dt.date.today().strftime("%B %d, %Y")

    log("Building LEO daily brief with DeepSeek V4 Pro analysis...")
    body, analysis_raw, sources = build_brief()

    # Save plain text locally
    exports_dir = REPO_ROOT / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    brief_path = exports_dir / f"leo-daily-brief-{date_str}.txt"
    brief_path.write_text(body)
    log(f"Saved: {brief_path} ({len(body)} chars)")

    if args.dry_run:
        print("\n" + "=" * 72)
        print(body[:2000])
        sys.exit(0)

    # ── Preflight QC — block delivery on CRITICAL issues ──
    if not args.skip_qc:
        from scripts.preflight_qc import check_report, log_qc_result
        qc = check_report(body, report_type="leo_brief", min_words=100)
        log_qc_result(qc, "leo_brief")
        if not qc.passed:
            log("QC BLOCKED delivery — fix issues and re-run")
            sys.exit(1)

    # Build HTML from the raw analysis + source attribution
    html_body = analysis_to_html(analysis_raw, date_display)

    # Plain text fallback
    text_body = body.replace("═", "-")

    subject = f"{SUBJECT_PREFIX} — {date_display}"

    log(f"Sending to {TO_EMAIL} via AgentMail...")
    if send_agentmail(TO_EMAIL, subject, html_body, text_body):
        log("Delivery successful ✅")
        log_report("leo_daily_brief", date_str, str(brief_path), body[:200],
                   len(body.split()), model="deepseek-v4-pro")
    else:
        log("Delivery FAILED — check AGENTMAIL_API_KEY")
        sys.exit(1)


if __name__ == "__main__":
    main()
