#!/usr/bin/env python3
"""Deliver the daily intel brief via AgentMail — text only, no attachments.

Reads WORKING_DIR/analysis/exec_summary.json and builds an HTML email body
with BLUF, context, all 10 regional summaries, key judgments, and
source/model attribution. Article hyperlinks are included from incident
source URLs when available.

Usage:
    python3 deliver_text_brief.py \\
        --working-dir ~/trevor-briefings/2026-05-22 \\
        --to roderick.jones@gmail.com \\
        --from trevor_mentis@agentmail.to
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import sys

AGENTMAIL_API_BASE = "https://api.agentmail.to"


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[deliver {ts}] {msg}", file=sys.stderr, flush=True)


def build_incident_url_map(wd: pathlib.Path) -> dict[str, str]:
    """Build a mapping of incident_id → source URL from raw incidents.json."""
    url_map: dict[str, str] = {}
    incidents_path = wd / "raw" / "incidents.json"
    if not incidents_path.exists():
        return url_map
    try:
        data = json.loads(incidents_path.read_text())
        for inc in data.get("incidents", []):
            inc_id = inc.get("id", "")
            # Use incident-level url field first, then sources[0].url
            url = inc.get("url", "") or ""
            if not url:
                sources = inc.get("sources", [])
                if sources and isinstance(sources[0], dict):
                    url = sources[0].get("url", "") or ""
            if inc_id and url:
                url_map[inc_id] = url
    except Exception as exc:
        log(f"WARN: could not load incident URL map: {exc}")
    return url_map


def format_evidence_ids(evidence_ids: list[str], url_map: dict[str, str]) -> str:
    """Format evidence_incident_ids as HTML with hyperlinks where URLs exist."""
    if not evidence_ids:
        return ""
    links = []
    for eid in evidence_ids:
        url = url_map.get(eid, "")
        if url:
            links.append(f'<a href="{url}" style="color:#0066cc;text-decoration:none;font-size:11px;">{eid}</a>')
        else:
            links.append(f'<span style="font-size:11px;color:#999;">{eid}</span>')
    return " [" + ", ".join(links) + "]"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--to", required=True, help="Recipient email")
    parser.add_argument("--from", dest="from_addr", default="trevor_mentis@agentmail.to",
                        help="Sender inbox (default: trevor_mentis@agentmail.to)")
    args = parser.parse_args()

    wd = pathlib.Path(args.working_dir).expanduser().resolve()
    exec_path = wd / "analysis" / "exec_summary.json"
    if not exec_path.exists():
        log(f"ERROR: exec_summary.json not found at {exec_path}")
        return 1

    exec_data = json.loads(exec_path.read_text())
    date_utc = wd.name

    # Build incident_id → URL lookup
    incident_url_map = build_incident_url_map(wd)
    log(f"loaded {len(incident_url_map)} incident URLs for hyperlinking")

    # Build HTML body — handle nested executive_summary.{bluf}, flat {bluf}, or string executive_summary
    exec_summary_raw = exec_data.get("executive_summary", {})
    if isinstance(exec_summary_raw, str):
        bluf = exec_summary_raw
        context = exec_data.get("context_paragraph", "")
    else:
        bluf = exec_summary_raw.get("bluf", exec_data.get("bluf", "No BLUF available."))
        context = exec_summary_raw.get("context_paragraph", exec_data.get("context_paragraph", ""))
    
    # Aggregated key judgments — handles both regional_assessments and regional_sections formats
    judgments = []
    for ra in exec_data.get("regional_assessments", exec_data.get("regional_sections", [])):
        judgments.extend(ra.get("key_judgments", []))
    sources_used = exec_data.get("sources_used", [])
    models_used = exec_data.get("models_used", [])

    # Parse judgments if stored as string repr
    if isinstance(judgments, str):
        try:
            judgments = eval(judgments)
        except Exception:
            judgments = []
    if isinstance(sources_used, str):
        try:
            sources_used = eval(sources_used)
        except Exception:
            sources_used = [sources_used]
    if isinstance(models_used, str):
        try:
            models_used = eval(models_used)
        except Exception:
            models_used = [models_used]

    region_label = {
        "europe": "Europe", "russia_eurasia": "Russia & Eurasia", "north_america": "North America",
        "central_america_caribbean": "Central America & Caribbean",
        "south_america": "South America", "north_africa": "North Africa", "sub_saharan_africa": "Sub-Saharan Africa",
        "middle_east": "Middle East", "central_asia": "Central Asia",
        "south_east_asia": "Southeast Asia", "east_asia": "East Asia",
        "south_asia": "South Asia", "oceania": "Oceania",
        "prediction_markets": "Prediction Markets",
    }
    region_emoji = {
        "europe": "🇪🇺", "russia_eurasia": "🇷🇺", "north_america": "🇺🇸",
        "central_america_caribbean": "🌴", "south_america": "🌎",
        "north_africa": "🌍", "sub_saharan_africa": "🌍", "middle_east": "🕌",
        "central_asia": "🏔️", "south_east_asia": "🌏",
        "east_asia": "🏯", "south_asia": "🕌",
        "oceania": "🏝️", "prediction_markets": "📊",
    }

    def kent_color(band):
        b = (band or "").lower()
        if "almost cert" in b or "highly likely" in b: return "#1a7a1a"
        if "likely" in b or "better than even" in b: return "#2563eb"
        if "even chance" in b: return "#b8860b"
        if "unlikely" in b: return "#c47000"
        if "highly unlikely" in b or "almost imposs" in b: return "#b22222"
        return "#666"

    def kent_icon(band):
        b = (band or "").lower()
        if "almost cert" in b or "highly likely" in b: return "🟢"
        if "likely" in b or "better than even" in b: return "🔵"
        if "even chance" in b: return "🟡"
        if "unlikely" in b: return "🟠"
        if "highly unlikely" in b or "almost imposs" in b: return "🔴"
        return "⚪"

    from html import escape as h
    import re as _re  # for sentence splitting — imported once, used in loop

    regions_order = [
        "europe", "russia_eurasia", "middle_east", "north_america", "east_asia",
        "south_asia", "central_asia", "south_east_asia",
        "north_africa", "sub_saharan_africa", "south_america", "central_america_caribbean",
        "oceania", "prediction_markets",
    ]

    # Build region cards
    region_cards = ""
    total_incidents = 0
    total_kjs = 0
    region_count = 0

    for region in regions_order:
        region_file = wd / "analysis" / f"{region}.json"
        if not region_file.exists():
            continue
        try:
            rdata = json.loads(region_file.read_text())
        except Exception as exc:
            log(f"WARN: could not load {region}.json: {exc}")
            continue

        narrative = rdata.get("narrative", rdata.get("bluf", ""))
        kjs = rdata.get("key_judgments", [])
        # Normalize KJ field names (analyze.py direct vs orchestrator produce different formats)
        valid_kjs = []
        for kj in kjs:
            # Normalize field names for statement (any of these match)
            for alt_field in ("event", "prediction", "judgment", "text"):
                if alt_field in kj and not kj.get("statement"):
                    kj["statement"] = kj[alt_field]
            # Normalize confidence bands
            if not kj.get("sherman_kent_band"):
                if "probability_band" in kj:
                    kj["sherman_kent_band"] = kj["probability_band"]
                elif "probability_verbal" in kj:
                    kj["sherman_kent_band"] = kj["probability_verbal"]
                elif "confidence_verbal" in kj:
                    kj["sherman_kent_band"] = kj["confidence_verbal"]
                elif "confidence" in kj and isinstance(kj["confidence"], str):
                    kj["sherman_kent_band"] = kj["confidence"]
            # Normalize prediction percentages
            if not kj.get("prediction_pct"):
                if "numeric_probability" in kj:
                    kj["prediction_pct"] = kj["numeric_probability"]
                elif "probability_numeric" in kj:
                    kj["prediction_pct"] = kj["probability_numeric"]
                elif "confidence" in kj:
                    import re
                    conf = str(kj["confidence"])
                    cm = re.match(r'([A-Za-z]+)', conf)
                    if cm:
                        kj["sherman_kent_band"] = cm.group(1).title()
            
            # Render-time validation: skip broken KJs
            stmt = kj.get("statement", "").strip()
            if len(stmt) < 20:
                log(f"    Skipping broken KJ (no statement): {kj.get('statement','')[:40]}")
                continue
            valid_kjs.append(kj)
        
        kjs = valid_kjs
        count = rdata.get("incident_count", 0)
        story = rdata.get("story", "")
        total_incidents += count
        total_kjs += len(kjs)

        label = region_label.get(region, region)
        emoji = region_emoji.get(region, "•")

        # SKIP prediction markets section when it has no usable data
        if region == "prediction_markets" and count == 0 and len(kjs) == 0:
            log(f"Suppressing prediction_markets section — no usable data (count={count}, KJs={len(kjs)})")
            total_incidents -= count  # don't count 0 towards total
            continue

        # Extract bullet points from narrative — natural sentence breaks, no truncation
        bullets = []
        if narrative:
            # Split on sentence boundaries: period, semicolon, or colon followed by space and capital
            sentences = _re.split(r'(?<=[.;])\s+(?=[A-Z])', narrative)
            for s in sentences:
                s = s.strip().rstrip(".")
                if len(s) > 15:
                    if s.lower().startswith("overnight "):
                        s = s[10:]
                    bullets.append(s[0].upper() + s[1:])

        bullet_html = ""
        if bullets:
            bullet_html = '<ul style="margin:0 0 10px;padding-left:18px;font-size:14px;color:#444;line-height:1.7">\n'
            for pt in bullets[:6]:  # max 6 bullet points per region
                bullet_html += f'  <li style="margin-bottom:4px">{h(pt)}</li>\n'
            bullet_html += '</ul>\n'

        # Key judgments
        kj_html = ""
        if kjs:
            kj_html += '<div style="margin-top:8px;padding-top:8px;border-top:1px dashed #e8ecf1">\n'
            kj_html += '<div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#888;margin-bottom:6px">Key Judgments</div>\n'
            for kj in kjs[:2]:
                band = kj.get("sherman_kent_band", "assessed")
                stmt = kj.get("statement", "")
                color = kent_color(band)
                icon = kent_icon(band)
                ss = " ⚠️" if kj.get("single_source_basis") else ""
                ev_ids = kj.get("evidence_incident_ids", [])
                ev_links = format_evidence_ids(ev_ids, incident_url_map)
                kj_html += f'<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:4px;font-size:13px;color:#555">'
                kj_html += f'<span style="flex-shrink:0;margin-top:2px">{icon}</span>'
                kj_html += f'<span><strong style="color:{color}">{h(band).title()}</strong>: {h(stmt)}{ss}{ev_links}</span>'
                kj_html += '</div>\n'
            kj_html += '</div>\n'

        region_count += 1
        region_cards += f"""
<div style="background:#fff;border-radius:8px;padding:16px 18px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.05)">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
    <span style="font-size:16px">{emoji}</span>
    <span style="font-size:15px;font-weight:700;color:#1a2a3a">{h(label)}</span>
    <span style="font-size:11px;color:#999;margin-left:auto">{count if count else ""}</span>
  </div>
  {bullet_html}
  {kj_html}
</div>
"""

    # Build full HTML
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;max-width:680px;margin:0 auto;padding:0;color:#1a1a2e;line-height:1.65;font-size:15px;background:#f8f9fb">

<div style="background:linear-gradient(135deg,#0f1923,#1a2a3a);padding:28px 24px 20px">
  <div style="font-size:11px;text-transform:uppercase;letter-spacing:2px;color:#5a8aaa;margin-bottom:6px">Trevor Intelligence</div>
  <h1 style="font-size:26px;margin:0 0 6px;color:#ffffff;font-weight:700;letter-spacing:-0.5px">Daily Intelligence Brief</h1>
  <div style="font-size:13px;color:#7f9ab0">{date_utc} · {total_incidents} incidents · {total_kjs} judgments · {region_count} regions</div>
</div>

<div style="margin:24px 20px 8px">
  <div style="background:#ffffff;border-radius:10px;padding:20px 22px;border-left:5px solid #c0392b;box-shadow:0 1px 4px rgba(0,0,0,0.06)">
    <div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:#c0392b;font-weight:700;margin-bottom:6px">⚠️ Bottom Line Up Front</div>
    <div style="font-size:17px;font-weight:600;color:#2c3e50;line-height:1.6">{h(bluf)}</div>
  </div>
</div>

<div style="margin:8px 20px 20px;padding:0 2px;font-size:14px;color:#555;line-height:1.7">{h(context[:800])}</div>

<div style="margin:10px 20px 16px;border-top:2px solid #e8ecf1"></div>

<div style="margin:0 20px">
  <h2 style="font-size:18px;color:#1a2a3a;margin:0 0 16px;letter-spacing:-0.3px">Regional Intelligence</h2>
  {region_cards}
</div>

<div style="margin:20px 20px 0;padding:16px 18px;background:#fff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.05)">
  <div style="font-size:11px;text-transform:uppercase;letter-spacing:1.5px;color:#888;margin-bottom:8px">Methodology & Sources</div>
  <div style="display:flex;gap:20px;flex-wrap:wrap;font-size:12px;color:#666;line-height:1.6">
    <div style="flex:1;min-width:150px">
      <div style="font-weight:600;color:#444;margin-bottom:4px">Collection</div>
      <div>286 validated RSS feeds</div>
      <div>Gmail + AgentMail intel</div>
      <div>Web search gap fill</div>
    </div>
    <div style="flex:1;min-width:150px">
      <div style="font-weight:600;color:#444;margin-bottom:4px">Analysis</div>
      <div>DeepSeek V4 Pro</div>
      <div>Claude Opus 4.7</div>
      <div>Sherman Kent calibration</div>
    </div>
    <div style="flex:1;min-width:150px">
      <div style="font-weight:600;color:#444;margin-bottom:4px">Quality</div>
      <div>NATO Admiralty ratings</div>
      <div>Forced dissent on all</div>
      <div>7-gate QC pre-delivery</div>
    </div>
  </div>
</div>

<div style="text-align:center;padding:20px;font-size:11px;color:#aaa">
  Trevor — Threat Research &amp; Evaluation Virtual Operations Resource<br>
  Automated daily brief &nbsp;·&nbsp; Reply: trevor_mentis@agentmail.to<br>
  <a href="https://github.com/trevormentis-spec" style="color:#5a8aaa">github</a> &nbsp;·&nbsp;
  <a href="https://www.moltbook.com/u/trevormentis" style="color:#5a8aaa">moltbook</a>
</div>

</body></html>"""

    # Also build a plain text version with source URLs
    text_parts = [f"TREVOR Daily Brief — {date_utc}", "", f"BLUF: {bluf}", ""]
    if context:
        text_parts.append(f"Context: {context}")
        text_parts.append("")
    for kj in judgments:
        band = kj.get("sherman_kent_band", "assessed")
        pct = kj.get("prediction_pct", "")
        statement = kj.get("statement", "")
        region_val = kj.get("drawn_from_region", "")
        region_name = region_label.get(region_val, region_val.replace("_", " ").title())
        text_parts.append(f"[{region_name}] [{band} {pct}%] {statement}")
    text_parts.append("")
    
    # Include source article URLs in text version
    if incident_url_map:
        text_parts.append("--- Source Articles ---")
        for inc_id, url in sorted(incident_url_map.items()):
            text_parts.append(f"  {inc_id}: {url}")
        text_parts.append("")
    
    text_parts.append("---")
    text_parts.append(f"Models: {', '.join(models_used) if models_used else 'DeepSeek V4 Pro'}")
    text_parts.append(f"Sources: {len(sources_used)} cited")
    text = "\n".join(text_parts)

    # ── Preflight QC — block delivery on CRITICAL issues ──
    import importlib.util as _iu
    _qc_path = pathlib.Path(__file__).resolve().parents[3] / "scripts" / "preflight_qc.py"
    _spec = _iu.spec_from_file_location("preflight_qc", _qc_path)
    _qc = _iu.module_from_spec(_spec)
    _spec.loader.exec_module(_qc)
    qc = _qc.check_report(text, report_type="daily_brief", min_words=200)
    _qc.log_qc_result(qc, "daily_brief")
    if not qc.passed:
        log("QC BLOCKED delivery — fix issues and re-run")
        return 1

    # Send via AgentMail API
    api_key = os.environ.get("AGENTMAIL_API_KEY")
    if not api_key:
        log("AGENTMAIL_API_KEY not set — saving to working directory instead")
        (wd / "final" / "brief.html").write_text(html)
        (wd / "final" / "brief.txt").write_text(text)
        return 0

    from agentmail import AgentMail

    def send_with_retry(client, inbox_id, to, subject, text, html, max_retries=3):
        for attempt in range(max_retries):
            try:
                return client.inboxes.messages.send(
                    inbox_id=inbox_id, to=[to], subject=subject, text=text, html=html)
            except Exception as e:
                if attempt < max_retries - 1:
                    import time; time.sleep(2 ** attempt)
                    continue
                raise

    client = AgentMail(api_key=api_key)
    try:
        resp = send_with_retry(client,
            inbox_id=args.from_addr,
            to=args.to,
            subject=f"TREVOR Daily Brief — {date_utc}",
            text=text,
            html=html,
        )
        log(f"Delivered to {args.to} — message_id: {resp.message_id}")
    except Exception as e:
        log(f"ERROR sending via AgentMail: {e}")
        (wd / "final" / "brief.html").write_text(html)
        (wd / "final" / "brief.txt").write_text(text)
        log("Saved to working directory as fallback")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
