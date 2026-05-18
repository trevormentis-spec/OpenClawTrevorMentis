#!/usr/bin/env python3
"""PDF Renderer — converts brief JSON to branded PDF via weasyprint.

Usage:
    python3 scripts/render_pdf.py --json path/to/brief.json --pdf path/to/output.pdf
    python3 scripts/render_pdf.py --json path/to/brief.json --pdf path/to/output.pdf --template analyst/templates/pdf/brief_template.html

Dependencies: weasyprint (system package, already installed)
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import tempfile
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE = REPO_ROOT / "analyst" / "templates" / "pdf" / "brief_template.html"


def load_template(template_path: str | pathlib.Path) -> str:
    """Load the HTML template."""
    path = pathlib.Path(template_path)
    if not path.exists():
        print(f"Error: template not found: {path}", file=sys.stderr)
        sys.exit(1)
    return path.read_text()


def render_template(template: str, data: dict[str, Any]) -> str:
    """Simple template rendering (Jinja2 not available)."""
    html = template
    
    # Simple variable substitution
    for key, value in data.get("simple_vars", {}).items():
        html = html.replace("{{ " + key + " }}", str(value))
        html = html.replace("{{ " + key + "}}", str(value))
        html = html.replace("{{" + key + " }}", str(value))
    
    # Handle loops: {% for item in list %}...{% endfor %}
    # This is a simplified loop processor — handles one level
    loop_pattern = re.compile(r'\{\%\s*for\s+(\w+)\s+in\s+(\w+)\s*\%\}(.*?)\{\%\s*endfor\s*\%\}', re.DOTALL)
    
    def replace_loop(match):
        var_name = match.group(1)
        list_name = match.group(2)
        loop_body = match.group(3)
        items = data.get(list_name, [])
        result = []
        for item in items:
            item_html = loop_body
            # Replace {{ item.field }}
            if isinstance(item, dict):
                for key, val in item.items():
                    placeholder = "{{ " + var_name + "." + key + " }}"
                    item_html = item_html.replace(placeholder, str(val) if val is not None else "")
                    # Also try without trailing space
                    item_html = item_html.replace("{{ " + var_name + "." + key + "}}", str(val) if val is not None else "")
            # Replace filters like {{ item.field | replace(...) }}
            filter_pattern = re.compile(r'\{\{\s*' + var_name + r'\.(\w+)\s*\|\s*(\w+).*?\}\}')
            item_html = filter_pattern.sub(r'{{\1}}', item_html)
            # Handle conditional display
            item_html = item_html.replace("{% if t.sizing_usd %}", "")
            item_html = item_html.replace("{% else %}", "")
            item_html = item_html.replace("{% endif %}", "")
            item_html = item_html.replace("{% if " + var_name + ".sizing_usd %}", "")
            item_html = item_html.replace("{% else %}", "")
            item_html = item_html.replace("{% endif %}", "")
            # Handle format filter
            fmt_match = re.search(r'\{\{([^}]+)\|format\(([^)]+)\)\}\}', item_html)
            if fmt_match:
                expr = fmt_match.group(1).strip()
                fmt_args = fmt_match.group(2)
                # Simple number formatting
                item_html = item_html.replace(fmt_match.group(0), str(item.get(expr.split('.')[-1], '')))
            result.append(item_html)
        return "\n".join(result)
    
    html = loop_pattern.sub(replace_loop, html)
    
    # Clean up remaining template markers (everything not substituted)
    html = re.sub(r'\{\{.*?\}\}', '', html)
    html = re.sub(r'\{\%.*?\%\}', '', html)
    
    return html


def enrich_brief_data(brief: dict[str, Any]) -> dict[str, Any]:
    """Enrich brief data for rendering — extract simple vars, format lists."""
    
    bluf_text = brief.get("bluf", "")
    cal = brief.get("calibration", {})
    if isinstance(cal, dict):
        cal_band = cal.get("band", "Not assessed")
        cal_pct = f"{cal.get('pct_range', [0, 0])[0]}-{cal.get('pct_range', [0, 0])[1]}%"
    elif isinstance(cal, str):
        cal_band = cal
        cal_pct = ""
    
    simple_vars = {
        "brief_title": brief.get("title", "Intelligence Brief"),
        "bluf": bluf_text[:200],
        "calibration_band": cal_band,
        "calibration_pct": cal_pct,
        "produced_at": brief.get("produced_at", ""),
        "sources_count": str(brief.get("meta", {}).get("sources_cited", 0)),
        "brief_id": brief.get("brief_id", ""),
        "schema_version": brief.get("schema_version", "1.0.0"),
    }
    
    data = {
        "simple_vars": simple_vars,
        "headline_judgments": brief.get("headline_judgments", brief.get("judgments", [])),
        "sections": brief.get("sections", []),
        "watch_items": brief.get("watch_items", []),
        "trade_positions": brief.get("trade_positions", []),
        "gaps": brief.get("gaps", []),
        "action_lines": brief.get("action_lines", []),
        "sources": brief.get("sources", []),
    }
    
    return data


def render_pdf(json_path: str, pdf_path: str, template_path: str | None = None) -> None:
    """Render a brief JSON file to PDF."""
    from weasyprint import HTML
    
    # Load brief
    with open(json_path) as f:
        brief = json.load(f)
    
    # Load template
    template = load_template(template_path or DEFAULT_TEMPLATE)
    
    # Enrich data
    data = enrich_brief_data(brief)
    
    # Render HTML
    html = render_template(template, data)
    
    # Write HTML to temp file for debugging
    html_path = pdf_path.replace(".pdf", ".html")
    with open(html_path, "w") as f:
        f.write(html)
    print(f"  HTML preview: {html_path}")
    
    # Render PDF
    HTML(string=html).write_pdf(pdf_path)
    print(f"  PDF output:   {pdf_path}")
    
    # Report
    file_size = os.path.getsize(pdf_path)
    print(f"  Size:         {file_size:,} bytes")


def main():
    parser = argparse.ArgumentParser(description="Brief JSON → PDF renderer")
    parser.add_argument("--json", required=True, help="Path to brief JSON file")
    parser.add_argument("--pdf", required=True, help="Path to output PDF file")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE), help="Path to HTML template")
    args = parser.parse_args()
    
    if not os.path.exists(args.json):
        print(f"Error: JSON file not found: {args.json}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Rendering {args.json} → {args.pdf}")
    render_pdf(args.json, args.pdf, args.template)
    print("Done.")


if __name__ == "__main__":
    main()
