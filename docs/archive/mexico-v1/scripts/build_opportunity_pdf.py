#!/usr/bin/env python3
"""Build the Opportunity Landscape PDF with charts."""

import json, os, re, sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

WORKSPACE = Path("/home/ubuntu/.openclaw/workspace")
MD_PATH = WORKSPACE / "exports" / "mexico-opportunity-landscape.md"
CHART_DIR = WORKSPACE / "exports" / "opportunity-charts"
TEMPLATE = WORKSPACE / "exports" / "opportunity-template.html"
HTML_OUT = WORKSPACE / "exports" / "opportunity-rendered.html"
PDF_OUT = WORKSPACE / "exports" / "pdfs" / "mexico-opportunity-landscape.pdf"

PDF_OUT.parent.mkdir(parents=True, exist_ok=True)

with open(MD_PATH) as f:
    md = f.read()

# Parse sections
parts = re.split(r'\n(?=## PART |## Executive)', md)
sections = []
current_section = None

for part in parts:
    title_match = re.match(r'^## (.+)', part)
    if not title_match:
        continue
    title = title_match.group(1).strip()
    
    # Get body (everything after the title line until next ##)
    body_lines = part.split('\n')[1:]
    body = '\n'.join(body_lines).strip()
    
    # Convert markdown to simple HTML
    body_html = body
    body_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', body_html)
    body_html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', body_html)
    
    paragraphs = []
    for para in body_html.split('\n\n'):
        para = para.strip()
        if not para or para.startswith('|---') or para.startswith('|:--'):
            continue
        if para.startswith('|') and '|' in para:
            # Table
            rows = para.strip().split('\n')
            table_rows = [r for r in rows if not re.match(r'^\|[\s\-:|]+\|$', r)]
            if len(table_rows) >= 2:
                table_html = '<table><thead><tr>'
                for c in table_rows[0].split('|')[1:-1]:
                    table_html += f'<th>{c.strip()}</th>'
                table_html += '</tr></thead><tbody>'
                for row in table_rows[1:]:
                    cells = [c.strip() for c in row.split('|')[1:-1]]
                    table_html += '<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>'
                table_html += '</tbody></table>'
                paragraphs.append(table_html)
            continue
        para = para.replace('\n', ' ')
        paragraphs.append(f'<p>{para}</p>')
    
    body_final = '\n'.join(paragraphs)
    
    sections.append({
        "title": title,
        "body": body_final
    })

print(f"Parsed {len(sections)} sections")

# Map charts to sections
chart_map = {
    0: [{"src": f"{CHART_DIR}/01-investment-map.png", "caption": "Investment opportunity map — size × risk × timing for 6 opportunity clusters"}],
    1: [  # Part I all sections
        {"src": f"{CHART_DIR}/04-timeline-actions.png", "caption": "Recommended action timeline for investors and security firms"},
    ],
    2: [  # Part II
        {"src": f"{CHART_DIR}/02-security-opportunity.png", "caption": "Security company opportunity sizing across 6 verticals"},
        {"src": f"{CHART_DIR}/03-cybersecurity-breakdown.png", "caption": "Cybersecurity sub-segment breakdown with growth rates"},
    ],
}

for idx, charts in chart_map.items():
    if idx < len(sections):
        sections[idx]["charts"] = charts

# Create HTML template
template_html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @page { size: A4; margin: 1.8cm 2cm;
    @bottom-right { content: counter(page) " / " counter(pages); font-size: 8pt; color: #7f8c8d; font-family: 'DejaVu Sans', sans-serif; } }
  @page :first { @bottom-right { content: none; } }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'DejaVu Sans', sans-serif; font-size: 8.5pt; line-height: 1.45; color: #2c3e50; }
  .cover { page-break-after: always; display: flex; flex-direction: column; justify-content: center; height: 27.5cm; text-align: center; }
  .cover .badge { display: inline-block; background: #1a1a2e; color: white; padding: 6px 20px; font-size: 10pt; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 40px; align-self: center; }
  .cover h1 { font-size: 22pt; color: #1a1a2e; line-height: 1.25; margin-bottom: 16px; }
  .cover .subtitle { font-size: 12pt; color: #7f8c8d; margin-bottom: 40px; }
  .cover .meta { font-size: 9pt; color: #95a5a6; }
  .cover .meta strong { color: #2c3e50; }
  .cover .classification { margin-top: 60px; border: 2px solid #27ae60; display: inline-block; padding: 8px 24px; color: #27ae60; font-weight: bold; font-size: 9pt; letter-spacing: 1px; align-self: center; }
  .section { page-break-before: always; }
  .section-header { background: #1a1a2e; color: white; padding: 10px 16px; margin-bottom: 12px; }
  .section-header h2 { font-size: 12pt; }
  .section-header .part { font-size: 8pt; opacity: 0.7; text-transform: uppercase; }
  h3 { font-size: 10.5pt; color: #1a1a2e; margin: 14px 0 6px; padding-bottom: 3px; border-bottom: 1px solid #e0e0e0; }
  p { margin-bottom: 6px; text-align: justify; }
  strong { color: #1a1a2e; }
  .bluf { background: #f0f4f8; border-left: 4px solid #27ae60; padding: 10px 14px; margin: 12px 0; font-size: 9pt; }
  table { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 8pt; }
  th { background: #1a1a2e; color: white; padding: 6px 8px; text-align: left; font-weight: bold; }
  td { padding: 4px 8px; border-bottom: 1px solid #e0e0e0; }
  tr:nth-child(even) td { background: #f8f9fa; }
  .chart-container { text-align: center; margin: 14px 0; page-break-inside: avoid; }
  .chart-container img { max-width: 100%; height: auto; }
  .chart-container .chart-title { font-size: 7.5pt; color: #7f8c8d; margin-top: 3px; }
  .info-box { background: #eafaf1; border: 1px solid #a9dfbf; border-radius: 4px; padding: 8px 12px; margin: 10px 0; font-size: 8pt; }
</style>
</head>
<body>

<div class="cover">
  <div class="badge">Open Claw Mexico</div>
  <h1>{{ title }}</h1>
  <div class="subtitle">{{ subtitle }}</div>
  <div class="meta">
    <strong>Produced by:</strong> {{ producer }}<br>
    <strong>Date:</strong> {{ date }}
  </div>
  <div class="classification">COMMERCIAL INTELLIGENCE — FOR QUALIFIED INVESTORS</div>
</div>

{% for sec in sections %}
<div class="section">
  <div class="section-header">
    {% if 'PART' in sec.title %}<div class="part">{{ sec.title.split('—')[0].strip() }}</div>{% endif %}
    <h2>{{ sec.title }}</h2>
  </div>
  {{ sec.body|safe }}
  {% if sec.charts %}
    {% for chart in sec.charts %}
    <div class="chart-container">
      <img src="{{ chart.src }}" alt="Chart">
      <div class="chart-title">{{ chart.caption }}</div>
    </div>
    {% endfor %}
  {% endif %}
</div>
{% endfor %}

<div style="text-align:center; padding:40px 0; font-size:9pt; color:#7f8c8d;">
  <strong>Open Claw Mexico</strong> — Mexico Desk<br>
  Date: {{ date }}<br>
  Questions: trevor_mentis@agentmail.to<br><br>
  <em>{{ title }}</em><br>
  © Open Claw Mexico
</div>

</body>
</html>
"""

with open(TEMPLATE, "w") as f:
    f.write(template_html)

# Render
env = Environment(loader=FileSystemLoader(str(TEMPLATE.parent)), autoescape=False)
t = env.get_template(TEMPLATE.name)
html = t.render(**{
    "title": "Mexico H2 2026: Opportunity Landscape",
    "subtitle": "Investment & Security Sector Guide — Identifying opportunity through the risk cycle",
    "producer": "Open Claw Mexico — Mexico Desk",
    "date": "2026-05-19",
    "sections": sections
})

HTML_OUT.write_text(html, encoding="utf-8")
print(f"✅ HTML written ({len(html):,} bytes, {html.count('<p>')} <p> tags)")

HTML(string=html, base_url=str(WORKSPACE)).write_pdf(str(PDF_OUT))
print(f"✅ PDF written to {PDF_OUT}")

# Check
import subprocess
r = subprocess.run(["pdfinfo", str(PDF_OUT)], capture_output=True, text=True)
for line in r.stdout.split('\n'):
    if 'Pages' in line or 'Page size' in line:
        print(f"   {line.strip()}")

import os
print(f"   File size: {os.path.getsize(PDF_OUT)/1024:.0f} KB")
