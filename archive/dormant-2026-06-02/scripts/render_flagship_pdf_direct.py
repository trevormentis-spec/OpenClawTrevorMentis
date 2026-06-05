#!/usr/bin/env python3
"""Render the flagship PDF directly using Jinja2 + WeasyPrint, bypassing the skill's normalizer."""

import json, os, sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from weasyprint import HTML

WORKSPACE = Path("/home/ubuntu/.openclaw/workspace")
TEMPLATE = WORKSPACE / "exports" / "flagship-template.html"
JSON_IN = WORKSPACE / "exports" / "flagship-data.json"
PDF_OUT = WORKSPACE / "exports" / "pdfs" / "mexico-mid-2026-flagship-v3.pdf"
HTML_OUT = WORKSPACE / "exports" / "flagship-rendered-v3.html"

PDF_OUT.parent.mkdir(parents=True, exist_ok=True)

# Load JSON
with open(JSON_IN) as f:
    data = json.load(f)

# Render with Jinja2 — no autoescaping since body is pre-Html
from jinja2 import Environment, FileSystemLoader
env = Environment(
    loader=FileSystemLoader(str(TEMPLATE.parent)),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)

template = env.get_template(TEMPLATE.name)
html = template.render(**data)

# Save HTML
HTML_OUT.write_text(html, encoding="utf-8")
print(f"✅ HTML written ({len(html):,} bytes)")

# Render PDF
HTML(string=html, base_url=str(WORKSPACE)).write_pdf(str(PDF_OUT))
print(f"✅ PDF written to {PDF_OUT}")

# Check rendered content
from weasyprint import CSS
p_count = html.count("<p>")
print(f"   <p> tags in HTML: {p_count}")
