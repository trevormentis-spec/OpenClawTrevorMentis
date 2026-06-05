#!/usr/bin/env python3
"""Build the flagship PDF by creating JSON from the markdown + charts."""

import json
import re
import os

WORKSPACE = "/home/ubuntu/.openclaw/workspace"
MD_PATH = f"{WORKSPACE}/exports/mexico-mid-2026-flagship.md"
CHART_DIR = f"{WORKSPACE}/exports/flagship-charts"
TEMPLATE_PATH = f"{WORKSPACE}/exports/flagship-template.html"
OUTPUT_PATH = f"{WORKSPACE}/exports/pdfs/mexico-mid-2026-flagship.pdf"
HTML_OUT_PATH = f"{WORKSPACE}/exports/flagship-rendered.html"
JSON_PATH = f"{WORKSPACE}/exports/flagship-data.json"

os.makedirs(f"{WORKSPACE}/exports/pdfs", exist_ok=True)

with open(MD_PATH) as f:
    md = f.read()

# Extract sections by ## SECTION pattern
section_pattern = re.compile(r'^## (SECTION \d+.*?)(?=\n## SECTION|\Z)', re.MULTILINE | re.DOTALL)
section_headers = re.findall(r'^## (SECTION \d+.*?)$', md, re.MULTILINE)

# Parse sections
sections_data = []
parts = re.split(r'\n(?=## SECTION \d)', md)

# First part might be header metadata
header_text = parts[0] if parts else ""

bluf_text = ""
bluf_match = re.search(r'\*\*Bottom Line Up Front:\*\*(.*?)(?=\n---|\n\n\*\*Top)', md, re.DOTALL)
if bluf_match:
    bluf_text = bluf_match.group(1).strip()

for sec_idx, section_md in enumerate(parts):
    # Skip header
    if not section_md.startswith("## SECTION"):
        continue
    
    title_match = re.match(r'^## SECTION \d+ — (.+)$', section_md.split('\n')[0])
    if not title_match:
        continue
    
    title = title_match.group(1).strip()
    
    # Get body text (strip the heading line)
    body_lines = section_md.split('\n')[1:]
    body = '\n'.join(body_lines).strip()
    
    # Extract BLUF if present
    sec_bluf = ""
    bluf_match = re.search(r'\*\*Bottom Line Up Front:\*\*(.*?)(?=\n\*\*|\n---|\n#|\n##)', body, re.DOTALL)
    if bluf_match:
        sec_bluf = bluf_match.group(1).strip()[:300]
    
    # Find tables
    tables = []
    table_pattern = re.compile(r'\|(.+?)\|[\s\S]*?(?=\n\n|\n##|\Z)', re.MULTILINE)
    
    # Convert body markdown to simple HTML
    body_html = body
    # Bold
    body_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', body_html)
    # Italic
    body_html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', body_html)
    # Line breaks -> paragraphs
    paragraphs = []
    for para in body_html.split('\n\n'):
        para = para.strip()
        if not para:
            continue
        # Skip table rows in the body
        if para.startswith('|') and '|' in para:
            continue
        para = para.replace('\n', ' ')
        paragraphs.append(f'<p>{para}</p>')
    
    # Convert markdown tables
    table_html = ""
    table_matches = re.findall(r'^(\|.+\|[\s\S]*?)(?=\n\n|\n##|\Z)', body, re.MULTILINE)
    for tm in table_matches:
        rows = tm.strip().split('\n')
        if len(rows) < 2:
            continue
        # Skip separator row
        rows = [r for r in rows if not re.match(r'^\|[\s\-:|]+\|$', r)]
        if not rows:
            continue
        
        th = [c.strip() for c in rows[0].split('|')[1:-1]]
        table_html += '<table><thead><tr>'
        for h in th:
            table_html += f'<th>{h}</th>'
        table_html += '</tr></thead><tbody>'
        
        for row in rows[1:]:
            cells = [c.strip() for c in row.split('|')[1:-1]]
            table_html += '<tr>'
            for c in cells:
                table_html += f'<td>{c}</td>'
            table_html += '</tr>'
        table_html += '</tbody></table>'
    
    body_final = '\n'.join(paragraphs) + '\n' + table_html
    
    sections_data.append({
        "title": title,
        "bluf": sec_bluf,
        "body": body_final,
        "tables": [],
        "charts": [],
        "info": ""
    })

# Map charts to logical positions
chart_mapping = [
    # Section 0 (title+metadata) gets no chart
    # Section 1: Executive Summary — judgments chart
    {"section": 1, "img": f"{CHART_DIR}/02-judgments.png", "title": "Top 10 Judgments — Kent Confidence Bands", "caption": "Figure 1: Calibrated judgment distribution across 10 headline assessments"},
    {"section": 1, "img": f"{CHART_DIR}/09-calibration.png", "title": "Calibration Distribution", "caption": "Figure 2: Judgment confidence band composition"},
    # Section 2: Sheinbaum — approval chart
    {"section": 2, "img": f"{CHART_DIR}/01-approval.png", "title": "Sheinbaum Approval", "caption": "Figure 3: Sheinbaum approval trajectory, Oct 2024 – Mar 2026"},
    # Section 4: Cartel — risk map
    {"section": 4, "img": f"{CHART_DIR}/06-cartel-risk.png", "title": "Cartel Risk", "caption": "Figure 4: State-level cartel commercial risk assessment"},
    # Section 5: USMCA — scenario tree
    {"section": 5, "img": f"{CHART_DIR}/05-usmca-tree.png", "title": "USMCA Scenarios", "caption": "Figure 5: USMCA review decision tree with calibrated probabilities"},
    # Section 6: Economy — macro dashboard
    {"section": 6, "img": f"{CHART_DIR}/03-macro.png", "title": "Macro Dashboard", "caption": "Figure 6: GDP trajectory, inflation, and Banxico policy rate"},
    # Section 10: Sector — bubble chart
    {"section": 10, "img": f"{CHART_DIR}/04-sector-exposure.png", "title": "Sector Exposure", "caption": "Figure 7: Sector exposure bubble chart — export value × USMCA risk"},
    # Section 12: Calendar — timeline
    {"section": 12, "img": f"{CHART_DIR}/07-timeline.png", "title": "H2 2026 Calendar", "caption": "Figure 8: H2 2026 critical path calendar with watch items"},
    # Section 14: Recommendations — recs chart
    {"section": 14, "img": f"{CHART_DIR}/08-recommendations.png", "title": "Recommendations", "caption": "Figure 9: Strategic recommendations summary — 12 actions"},
]

# Insert charts into sections
for cm in chart_mapping:
    idx = cm["section"] - 1  # 0-indexed
    if 0 <= idx < len(sections_data):
        sections_data[idx].setdefault("charts", []).append({
            "src": cm["img"],
            "title": cm["title"],
            "caption": cm["caption"]
        })

# Extract top 10 judgments from section 1 as a table
top_10_table = {
    "headers": ["#", "Judgment", "Confidence", "Admiralty"],
    "rows": [
        ["1", "USMCA 16-yr extension by Q4 2026 after confrontation cycle", "Likely, 55-65%", "B2"],
        ["2", "Sheinbaum accepts tighter ROO + Chinese screening", "Likely, 60-70%", "B2"],
        ["3", "S&P downgrade (sovereign/Pemex) in 12mo", "Likely, 55-65%", "A2"],
        ["4", "CJNG fragmentation violence in Jalisco/Michoacán/Guanajuato", "Highly likely, 80-90%", "B2"],
        ["5", "Technical recession H1 2026 (Q4 2025 + Q1 2026)", "Almost certain, 90-95%", "A1"],
        ["6", "Fixed investment negative through Q3 2026", "Highly likely, 85-90%", "B2"],
        ["7", "Greenfield FDI <2023 levels before 2028", "Likely, 60-70%", "B3"],
        ["8", "World Cup executes w/o major incident", "Likely, 60-70%", "C3"],
        ["9", "CDMX subsidence infrastructure failure in 12mo", "Likely, 55-65%", "B2"],
        ["10", "Banxico floor reached; H2 holds/tightens", "Likely, 60-70%", "A2"],
    ],
    "caption": "Top 10 Headline Judgments with calibrated confidence bands"
}

sections_data[0]["tables"] = [top_10_table]

# Section 3: Cabinet scorecard table
cabinet_table = {
    "headers": ["Portfolio", "Incumbent", "Grade", "Notes"],
    "rows": [
        ["Economy", "Marcelo Ebrard", "B+", "USMCA file; independent political capital; 2030 ambitions"],
        ["Security", "Omar García Harfuch", "A-", "Most effective security secretary in a decade; 2030 potential"],
        ["Energy", "Luz Elena González", "B", "46% private generation reform; constrained by Pemex"],
        ["Foreign Affairs", "Juan Ramón de la Fuente", "B", "Professional, low-drama; subordinate to Ebrard on USMCA"],
    ],
    "caption": "Cabinet Scorecard: Four key portfolios"
}
sections_data[2]["tables"] = [cabinet_table]  # section 3 (0-indexed 2)

# Section 12: Calendar watch items table
calendar_table = {
    "headers": ["Date/Window", "Event", "Significance", "Price Move Prob."],
    "rows": [
        ["May 25, 2026", "US-Mexico bilateral negotiations (CDMX)", "High", "60-70%"],
        ["June 2026", "FIFA World Cup begins", "Moderate", "40-50%"],
        ["June 2", "US off-year primaries (TX, CA)", "Moderate", "30-40%"],
        ["July 1", "USMCA joint review deadline", "Critical", "70-80%"],
        ["Aug-Sep", "Likely extension resolution window", "High", "50-60%"],
        ["Sep 1", "Mexican Congress reconvenes", "Moderate", "30-40%"],
        ["Nov 3", "US midterm elections", "High", "55-65%"],
        ["Ongoing", "Banxico rate decisions", "Moderate", "30-40%/meeting"],
        ["Ongoing", "Pemex debt maturities", "Moderate-High", "40-50%"],
        ["H2 2026", "CJNG fragmentation violence", "Moderate", "Regional"],
    ],
    "caption": "H2 2026 Watch Calendar with material price move probabilities"
}
sections_data[11]["tables"] = [calendar_table]  # section 12 (0-indexed 11)

# Build chart groups (all charts in a dashboard section)
chart_groups = [
    {"img": f"{CHART_DIR}/01-approval.png", "caption": "Sheinbaum Approval Rating Trajectory"},
    {"img": f"{CHART_DIR}/02-judgments.png", "caption": "Top 10 Judgments — Confidence Bands"},
    {"img": f"{CHART_DIR}/03-macro.png", "caption": "Mexico Macro Dashboard"},
    {"img": f"{CHART_DIR}/04-sector-exposure.png", "caption": "Sector Exposure Bubble Chart"},
    {"img": f"{CHART_DIR}/05-usmca-tree.png", "caption": "USMCA Decision Tree"},
    {"img": f"{CHART_DIR}/06-cartel-risk.png", "caption": "Cartel Risk Assessment by State"},
    {"img": f"{CHART_DIR}/07-timeline.png", "caption": "H2 2026 Critical Path Calendar"},
    {"img": f"{CHART_DIR}/08-recommendations.png", "caption": "Strategic Recommendations Summary"},
    {"img": f"{CHART_DIR}/09-calibration.png", "caption": "Calibration Distribution"},
]

data = {
    "title": "Mexico Mid-2026: Sheinbaum 18-Month Retrospective & H2 2026 Strategic Outlook",
    "subtitle": "A decision-grade intelligence assessment for family offices, underwriters, and sovereign wealth funds",
    "producer": "Open Claw Mexico — Mexico Desk",
    "date": "2026-05-19",
    "coverage": "December 2024 – H2 2026",
    "sections": sections_data,
    "chart_groups": chart_groups,
}

with open(JSON_PATH, "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ JSON written to {JSON_PATH}")
print(f"   {len(sections_data)} sections, {len(chart_groups)} chart groups")
