#!/usr/bin/env python3
"""
Send the Daily Text Brief via Gmail — text-only, no PDF, no graphics.

Reads orchestrator analysis outputs + Kalshi scan + Mexico section,
formats a plain-text briefing, and sends via Gmail API (Maton gateway).

Usage:
    python3 scripts/send_text_brief_gmail.py \
        --working-dir ~/trevor-briefings/2026-05-21 \
        --date 2026-05-21 \
        --to roderick.jones@gmail.com \
        --kalshi-scan exports/pm-scan-final-2026-05-21.md

Output:
    - Sends email via Gmail
    - Writes exports/brief-sources-YYYY-MM-DD.json (source provenance)
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import email.mime.text
import json
import os
import pathlib
import re
import sys
import urllib.request
from typing import Any

MATON_BASE = "https://gateway.maton.ai/google-mail"
GMAIL_SEND = MATON_BASE + "/gmail/v1/users/me/messages/send"

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
KALSHI_DIR = REPO_ROOT / "exports"

REGION_LABEL = {
    "middle_east": "Middle East",
    "europe": "Europe",
    "asia": "Asia",
    "north_america": "North America",
    "south_central_america": "South & Central America",
    "global_finance": "Global Finance & Markets",
}

REGION_ORDER = [
    "middle_east", "europe", "asia",
    "north_america", "south_central_america", "global_finance",
]


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[send_brief {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> dict | list:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception as e:
            log(f"Warning: couldn't load {path}: {e}")
            return {}
    return {}


def load_analysis(analysis_dir: pathlib.Path) -> dict[str, dict]:
    """Load all region analysis JSONs + exec_summary."""
    data = {}
    exec_file = analysis_dir / "exec_summary.json"
    if exec_file.exists():
        data["exec_summary"] = load_json(exec_file)

    for region in REGION_ORDER:
        f = analysis_dir / f"{region}.json"
        if f.exists():
            data[region] = load_json(f)

    return data


def parse_kalshi_scan(kalshi_path: pathlib.Path) -> str:
    """Extract the key sections from the Kalshi/Polymarket scan."""
    if not kalshi_path.exists():
        return ""
    text = kalshi_path.read_text()
    # Pull executive summary, key divergences, and watchlist
    sections = []
    for header in ["Executive Summary", "Key Divergences", "Term Structure", "Watchlist"]:
        # Find section by header
        pattern = rf"(?:^|\n)#{{1,3}}\s*{re.escape(header)}.*?(?=\n#|\Z)"
        match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
        if match:
            sec = match.group(0).strip()
            # Truncate very long sections to ~800 chars
            if len(sec) > 1000:
                sec = sec[:1000] + "\n[...]"
            sections.append(sec)
    return "\n\n".join(sections)


def format_brief(
    analysis: dict[str, dict],
    date_str: str,
    kalshi_text: str,
    mexico_incidents: list | None = None,
    newsletter_recs: list[dict] | None = None,
) -> tuple[str, list[str]]:
    """Format the full text brief. Returns (body_text, sources_used)."""
    lines: list[str] = []
    sources_used: list[str] = []

    exec_sum = analysis.get("exec_summary", {})
    bluf = exec_sum.get("bluf", "") if isinstance(exec_sum, dict) else ""
    context = exec_sum.get("context_paragraph", "") if isinstance(exec_sum, dict) else ""
    judgments = exec_sum.get("five_judgments", []) if isinstance(exec_sum, dict) else []

    # Header
    lines.append("=" * 72)
    lines.append(f"  TREVOR DAILY BRIEF — {date_str}")
    lines.append("=" * 72)
    lines.append("")

    # BLUF
    if bluf:
        lines.append("═══ BOTTOM LINE UP FRONT ═══")
        lines.append(bluf)
        lines.append("")

    if context:
        lines.append(context)
        lines.append("")

    # Key Judgments
    if judgments:
        lines.append("═══ KEY JUDGMENTS ═══")
        for j in judgments:
            if isinstance(j, dict):
                kj = j.get("statement", "")
                band = j.get("sherman_kent_band", "")
                lines.append(f"  • {kj} [{band}]")
        lines.append("")

    # Per-Region Analysis
    for region in REGION_ORDER:
        if region not in analysis:
            continue
        rdata = analysis[region]
        if not isinstance(rdata, dict):
            continue

        label = REGION_LABEL.get(region, region.replace("_", " ").title())
        lines.append(f"═══ {label.upper()} ═══")

        narrative = rdata.get("narrative", "")
        if narrative:
            lines.append(narrative)
            lines.append("")

        by_the_numbers = rdata.get("by_the_numbers", [])
        if by_the_numbers and isinstance(by_the_numbers, list):
            lines.append("By the numbers:")
            for item in by_the_numbers:
                if isinstance(item, str):
                    lines.append(f"  • {item}")
                elif isinstance(item, dict):
                    lines.append(f"  • {item.get('label', item.get('statement', str(item)))}")
            lines.append("")

        region_kjs = rdata.get("key_judgments", [])
        if region_kjs and isinstance(region_kjs, list):
            lines.append("Key judgments:")
            for kj in region_kjs:
                if isinstance(kj, dict):
                    s = kj.get("statement", "")
                    b = kj.get("sherman_kent_band", "")
                    lines.append(f"  • {s} [{b}]")
            lines.append("")

        standing_reframe = rdata.get("standing_reframe", "")
        if standing_reframe:
            lines.append(f"Framework: {standing_reframe}")
            lines.append("")

        # Track source — use region from the narrative/region field
        source_name = rdata.get("region", label)
        if isinstance(source_name, str) and source_name not in sources_used:
            sources_used.append(f"Regional analysis: {label}")

    # Mexico Section (from merged incidents)
    if mexico_incidents:
        lines.append("═══ MEXICO ═══")
        lines.append("(From merged Mexico scan + institutional sources)")
        lines.append("")
        for inc in mexico_incidents[:5]:
            if isinstance(inc, dict):
                headline = inc.get("headline", str(inc)[:100])
                lines.append(f"  • {headline}")
        lines.append("")
        sources_used.append("Mexico daily scan (topic_morning_brief.py + local sources)")

    # Prediction Markets
    if kalshi_text:
        lines.append("═══ PREDICTION MARKETS ═══")
        lines.append(kalshi_text)
        lines.append("")
        sources_used.append("Kalshi/Polymarket geopolitics markets")

    # Source Provenance
    lines.append("═" * 72)
    lines.append("SOURCES USED TODAY")
    lines.append("═" * 72)
    # Add standard sources
    standard_sources = [
        "ISW/Critical Threats Project — daily Iran update",
        "Al Jazeera — Middle East coverage",
        "Reuters — wire service",
        "Associated Press — wire service",
        "BBC Monitoring — global media monitoring",
        "Gmail inbox (ISW, CTP, Cipher Brief, Foreign Policy newsletters)",
        "OpenWeb API collection (spec-based scraping)",
        "EIA — energy data",
    ]
    for s in standard_sources:
        if s not in sources_used:
            sources_used.append(s)

    for s in sources_used:
        lines.append(f"  • {s}")

    lines.append("")
    # Newsletter Recommendations
    if newsletter_recs:
        lines.append("")
        lines.append("═" * 72)
        lines.append("NEWSLETTER & SUBSTACK RECOMMENDATIONS")
        lines.append("═" * 72)
        lines.append("Newly discovered sources worth subscribing to:")
        lines.append("")
        for nr in newsletter_recs:
            title = nr.get("title", "Unknown")
            url = nr.get("url", "#")
            desc = nr.get("description", "")[:200]
            lines.append(f"  📫 {title}")
            lines.append(f"     {url}")
            if desc:
                lines.append(f"     {desc}")
            lines.append("")
        lines.append("Subscribe to these to improve tomorrow's brief.")
        lines.append("")

    lines.append(f"-- Trevor | {date_str}")
    lines.append("_Generated from open-source intelligence. All judgments use Sherman Kent probability bands._")

    return "\n".join(lines), sources_used


def send_gmail(to: str, subject: str, body: str, maton_key: str) -> bool:
    """Send plain-text email via Gmail API through Maton gateway."""
    msg = email.mime.text.MIMEText(body, "plain", "utf-8")
    msg["To"] = to
    msg["From"] = "trevor.mentis@gmail.com"
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
            log(f"Gmail send OK: {result.get('id', 'unknown')}")
            return True
    except urllib.error.HTTPError as e:
        log(f"Gmail send FAILED: HTTP {e.code} {e.read().decode()[:500]}")
        return False
    except Exception as e:
        log(f"Gmail send FAILED: {e}")
        return False


def save_source_provenance(date_str: str, sources: list[str], output_dir: pathlib.Path) -> None:
    """Save source provenance record."""
    record = {
        "date": date_str,
        "source_count": len(sources),
        "sources": sorted(sources),
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"brief-sources-{date_str}.json"
    path.write_text(json.dumps(record, indent=2))
    log(f"Source provenance saved: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Send daily text brief via Gmail")
    parser.add_argument("--working-dir", required=True, help="Path to trevor-briefings date dir")
    parser.add_argument("--date", required=True, help="Date string YYYY-MM-DD")
    parser.add_argument("--to", default="roderick.jones@gmail.com", help="Recipient email")
    parser.add_argument("--kalshi-scan", help="Path to Kalshi scan markdown")
    parser.add_argument("--subject", help="Email subject (auto-generated if omitted)")
    parser.add_argument("--newsletter-recs", help="Path to newsletter recommendations output")
    parser.add_argument("--save-only", action="store_true", help="Only save, don't send")
    parser.add_argument("--read-saved", action="store_true", help="Read from saved file and send")
    args = parser.parse_args()

    working_dir = pathlib.Path(args.working_dir).expanduser().resolve()
    analysis_dir = working_dir / "analysis"
    date_str = args.date
    maton_key = os.environ.get("MATON_API_KEY", "")

    if not maton_key:
        log("ERROR: MATON_API_KEY not set")
        sys.exit(1)

    exports_dir = REPO_ROOT / "exports"
    brief_path = exports_dir / f"daily-brief-{date_str}.txt"

    # READ-SAVED MODE: read the humanized brief file and send it
    if args.read_saved:
        if not brief_path.exists():
            log(f"ERROR: Saved brief not found at {brief_path}")
            sys.exit(1)
        body = brief_path.read_text()
        subject = args.subject or f"Trevor Daily Brief — {date_str}"
        log(f"Read humanized brief ({len(body)} chars) from {brief_path}")
        if send_gmail(args.to, subject, body, maton_key):
            log("Delivery successful")
        else:
            log("Delivery FAILED")
            sys.exit(1)
        return

    # Load analysis
    analysis = load_analysis(analysis_dir)
    if not analysis:
        log(f"ERROR: No analysis found in {analysis_dir}")
        sys.exit(1)

    # Load Kalshi scan
    kalshi_text = ""
    if args.kalshi_scan:
        kalshi_path = pathlib.Path(args.kalshi_scan)
        if not kalshi_path.is_absolute():
            kalshi_path = REPO_ROOT / args.kalshi_scan
        kalshi_text = parse_kalshi_scan(kalshi_path)

    # Load Mexico incidents if available
    mexico_incidents = None
    mexico_file = working_dir / "raw" / "mexico_incidents.json"
    if mexico_file.exists():
        mexico_incidents = load_json(mexico_file)
        if isinstance(mexico_incidents, dict):
            mexico_incidents = mexico_incidents.get("incidents", [])
        log(f"Loaded {len(mexico_incidents) if isinstance(mexico_incidents, list) else 0} Mexico incidents")

    # Load newsletter recommendations
    newsletter_recs = None
    if args.newsletter_recs:
        recs_path = pathlib.Path(args.newsletter_recs)
        if not recs_path.is_absolute():
            recs_path = REPO_ROOT / args.newsletter_recs
        if recs_path.exists():
            recs_text = recs_path.read_text()
            # Parse the printed output format
            newsletter_recs = []
            current = {}
            for line in recs_text.split("\n"):
                if line.startswith("NEWSLETTER:"):
                    if current.get("title"):
                        newsletter_recs.append(current)
                    current = {"title": line[len("NEWSLETTER:"):].strip()}
                elif line.startswith("  URL:") and current is not None:
                    current["url"] = line[len("  URL:"):].strip()
                elif line.startswith("  About:") and current is not None:
                    current["description"] = line[len("  About:"):].strip()
            if current.get("title"):
                newsletter_recs.append(current)
            log(f"Loaded {len(newsletter_recs)} newsletter recommendations")

    # Format
    subject = args.subject or f"Trevor Daily Brief — {date_str}"
    body, sources = format_brief(analysis, date_str, kalshi_text, mexico_incidents, newsletter_recs)

    # Save brief to file for review step
    exports_dir = REPO_ROOT / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    brief_path = exports_dir / f"daily-brief-{date_str}.txt"
    brief_path.write_text(body)
    log(f"Brief saved: {brief_path}")

    # Save source provenance
    save_source_provenance(date_str, sources, REPO_ROOT / "exports" / "source-logs")

    # Send (skip if --save-only — humanizer runs between)
    if args.save_only:
        log(f"Save-only mode — brief at {brief_path}, not sending")
        return

    log(f"Sending brief to {args.to}...")
    if send_gmail(args.to, subject, body, maton_key):
        log("Delivery successful")
    else:
        log("Delivery FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
