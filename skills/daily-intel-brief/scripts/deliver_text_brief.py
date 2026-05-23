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

    # Build HTML body
    bluf = exec_data.get("bluf", "No BLUF available.")
    context = exec_data.get("context_paragraph", "")
    judgments = exec_data.get("five_judgments", [])
    sources_used = exec_data.get("sources_used", [])
    models_used = exec_data.get("models_used", [])

    # Build region summaries from individual analysis files
    region_html = ""
    regions_order = [
        "europe", "north_america", "central_america_caribbean",
        "south_america", "africa", "middle_east",
        "central_asia", "south_east_asia", "east_asia", "south_asia",
        "oceania", "prediction_markets",
    ]
    region_label = {
        "europe": "Europe", "north_america": "North America",
        "central_america_caribbean": "Central America & Caribbean",
        "south_america": "South America", "africa": "Africa",
        "middle_east": "Middle East", "central_asia": "Central Asia",
        "south_east_asia": "South East Asia", "east_asia": "East Asia",
        "south_asia": "South Asia", "oceania": "Oceania",
        "prediction_markets": "Prediction Markets",
    }

    for region in regions_order:
        region_file = wd / "analysis" / f"{region}.json"
        if not region_file.exists():
            continue
        try:
            rdata = json.loads(region_file.read_text())
            narrative = rdata.get("narrative", "")
            kjs = rdata.get("key_judgments", [])
            label = region_label.get(region, region.replace("_", " ").title())
            
            # Collect all article URLs referenced in this region
            all_incident_refs = set()
            for kj in kjs[:3]:
                for eid in kj.get("evidence_incident_ids", []):
                    all_incident_refs.add(eid)

            kj_html = ""
            for kj in kjs[:3]:  # Max 3 judgments per region
                band = kj.get("sherman_kent_band", "assessed")
                pct = kj.get("prediction_pct", "")
                statement = kj.get("statement", "")
                single = kj.get("single_source_basis", False)
                ss = " ⚠️ single source" if single else ""
                ev_ids = kj.get("evidence_incident_ids", [])
                ev_links = format_evidence_ids(ev_ids, incident_url_map)
                kj_html += f"<li><strong>{band}</strong> ({pct}%): {statement}{ss}{ev_links}</li>"

            # Incident source links
            incident_links_html = ""
            for eid in sorted(all_incident_refs):
                url = incident_url_map.get(eid)
                if url:
                    incident_links_html += f'<a href="{url}" style="color:#0066cc;font-size:11px;">{eid}</a> '

            source_links_section = ""
            if incident_links_html:
                source_links_section = f'<p style="font-size:11px;color:#666;">Source articles: {incident_links_html}</p>'

            region_html += f"""
<h3 style="color:#1a1a2e;border-bottom:1px solid #eee;padding-bottom:4px;">{label}</h3>
<p>{narrative}</p>
<ul>{kj_html}</ul>
{source_links_section}
"""
        except Exception as exc:
            log(f"WARN: could not load {region}.json: {exc}")

    # Key judgments table
    kj_table = ""
    for kj in judgments:
        band = kj.get("sherman_kent_band", "assessed")
        pct = kj.get("prediction_pct", "")
        statement = kj.get("statement", "")
        region_val = kj.get("drawn_from_region", "")
        region_name = region_label.get(region_val, region_val.replace("_", " ").title())
        kj_table += f"<tr><td>{region_name}</td><td>{band} ({pct}%)</td><td>{statement}</td></tr>"

    # Source attribution with links where available
    src_list = "".join(f"<li>{s}</li>" for s in sources_used[:20]) if sources_used else "<li>Sources listed in regional analysis files</li>"
    model_list = "".join(f"<li>{m}</li>" for m in models_used) if models_used else "<li>DeepSeek V4 Pro (all tiers)</li>"

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:700px;margin:0 auto;padding:20px;color:#333;">
<div style="background:#1a1a2e;color:#fff;padding:20px;border-radius:8px 8px 0 0;">
<h1 style="margin:0;font-size:20px;">TREVOR Daily Brief</h1>
<p style="margin:5px 0 0;font-size:14px;opacity:0.8;">{date_utc} · DeepSeek V4 Pro</p>
</div>

<div style="background:#fff;border:1px solid #ddd;border-top:0;padding:20px;border-radius:0 0 8px 8px;">

<h2 style="color:#1a1a2e;">BLUF</h2>
<p style="font-size:15px;line-height:1.5;">{bluf}</p>

<h2 style="color:#1a1a2e;margin-top:24px;">Context</h2>
<p style="font-size:14px;line-height:1.5;">{context}</p>

<h2 style="color:#1a1a2e;margin-top:24px;">Regional Analysis</h2>
{region_html}

<h2 style="color:#1a1a2e;margin-top:24px;">Key Judgments</h2>
<table style="width:100%;border-collapse:collapse;font-size:13px;">
<tr style="background:#f5f5f5;"><th style="padding:8px;text-align:left;border:1px solid #ddd;">Region</th><th style="padding:8px;text-align:left;border:1px solid #ddd;">Confidence</th><th style="padding:8px;text-align:left;border:1px solid #ddd;">Judgment</th></tr>
{kj_table}
</table>

<h2 style="color:#1a1a2e;margin-top:24px;">Sources Used</h2>
<ul style="font-size:12px;color:#666;">{src_list}</ul>

<h2 style="color:#1a1a2e;margin-top:24px;">Models Used</h2>
<ul style="font-size:12px;color:#666;">{model_list}</ul>

<p style="font-size:11px;color:#999;margin-top:32px;border-top:1px solid #eee;padding-top:12px;">
Generated by TREVOR (Threat Research and Evaluation Virtual Operations Resource) · {date_utc}
</p>
</div>
</body>
</html>"""

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
