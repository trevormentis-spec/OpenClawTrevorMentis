#!/usr/bin/env python3
"""Build a PDF briefing from the analysis markdown + rendered images.

Usage:
    python3 tasks/build_briefing_pdf.py
    python3 tasks/build_briefing_pdf.py --input tasks/news_analysis.md --output exports/pdfs/briefing.pdf
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORKSPACE = Path("/home/ubuntu/.openclaw/workspace")
DEFAULT_INPUT = WORKSPACE / "tasks" / "news_analysis.md"
DEFAULT_OUTPUT = WORKSPACE / "exports" / "pdfs" / "briefing.pdf"
IMAGES_DIR = WORKSPACE / "exports" / "images"


def read_markdown(path: Path) -> str:
    with open(path) as f:
        return f.read()


def mermaid_to_html(code: str, diagram_idx: int) -> str:
    """Render a Mermaid block as an embedded HTML image via mermaid.ink."""
    try:
        encoded = base64.urlsafe_b64encode(code.encode("utf-8")).decode("utf-8")
        url = f"https://mermaid.ink/img/{encoded}"
        return (
            f'<div class="diagram-container">'
            f'<img src="{url}" alt="Diagram {diagram_idx}" '
            f'style="max-width:100%;border-radius:6px;border:1px solid #1e293b;">'
            f'<div class="caption">Figure {diagram_idx}</div>'
            f"</div>"
        )
    except Exception:
        return f"<pre><code>{code}</code></pre>"


def render_mermaid_block(code: str, output_path: Path) -> bool:
    """Save rendered Mermaid diagram to a local file."""
    try:
        encoded = base64.urlsafe_b64encode(code.encode("utf-8")).decode("utf-8")
        url = f"https://mermaid.ink/img/{encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Trevor-Briefing/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(data)
        return True
    except Exception:
        return False


def markdown_to_pdf_html(markdown: str) -> str:
    """Convert the analysis markdown to a PDF-ready HTML string.
    
    Renders Mermaid diagrams via mermaid.ink and embeds them as images.
    """
    now = datetime.now(timezone.utc)
    
    html_parts = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'>",
        "<style>",
        "@page { size: A4; margin: 2cm 1.8cm; @bottom-right { content: counter(page); font-size: 9pt; color: #666; } @bottom-left { content: 'TREVOR Intelligence Daily Briefing'; font-size: 9pt; color: #666; } }",
        "body { font-family: 'DejaVu Sans', 'Noto Sans', Arial, sans-serif; color: #1a1a2e; font-size: 10.5pt; line-height: 1.5; }",
        "h1 { color: #1e3a5f; font-size: 18pt; border-bottom: 2px solid #c0392b; padding-bottom: 6px; margin-top: 0; }",
        "h2 { color: #1e3a5f; font-size: 14pt; margin-top: 24px; border-bottom: 1px solid #ddd; padding-bottom: 4px; }",
        "h3 { color: #2c3e50; font-size: 12pt; margin-top: 18px; }",
        "h4 { color: #555; font-size: 11pt; }",
        ".bluf-box { background: #fef9f5; border-left: 4px solid #c0392b; padding: 12px 16px; margin: 12px 0; font-size: 10pt; }",
        ".bluf-box strong { color: #1a1a2e; }",
        "table { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 9.5pt; }",
        "th { background: #1e3a5f; color: white; padding: 6px 10px; text-align: left; }",
        "td { padding: 5px 10px; border-bottom: 1px solid #ddd; }",
        "tr:nth-child(even) td { background: #f8f9fa; }",
        ".diagram-container { text-align: center; margin: 16px 0; page-break-inside: avoid; }",
        ".diagram-container img { max-width: 100%; max-height: 16cm; }",
        ".caption { font-size: 8pt; color: #888; margin-top: 4px; font-style: italic; }",
        "strong { color: #1a1a2e; }",
        "code { background: #f0f0f0; padding: 1px 4px; border-radius: 2px; font-size: 9pt; }",
        ".footer { text-align: center; font-size: 8pt; color: #999; margin-top: 24px; border-top: 1px solid #ddd; padding-top: 8px; }",
        "</style></head><body>",
    ]

    # Process markdown line by line
    lines = markdown.split("\n")
    in_mermaid = False
    mermaid_code = ""
    mermaid_idx = 0
    in_table = False
    table_lines: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Mermaid code block
        if stripped == "```mermaid":
            in_mermaid = True
            mermaid_code = ""
            continue
        if in_mermaid:
            if stripped == "```":
                # Render the mermaid block
                mermaid_idx += 1
                html_parts.append(mermaid_to_html(mermaid_code, mermaid_idx))
                in_mermaid = False
                continue
            mermaid_code += line + "\n"
            continue

        # Skip plain code fence markers
        if stripped.startswith("```"):
            continue

        # Headers
        if stripped.startswith("# ") and not stripped.startswith("## "):
            html_parts.append(f"<h1>{stripped[2:]}</h1>")
        elif stripped.startswith("## "):
            html_parts.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("### "):
            html_parts.append(f"<h3>{stripped[4:]}</h3>")
        elif stripped.startswith("#### "):
            html_parts.append(f"<h4>{stripped[5:]}</h4>")

        # BLUF box
        elif stripped.startswith("**BLUF**") or stripped == "BLUF":
            html_parts.append('<div class="bluf-box"><strong>▼ BLUF</strong><br>')

        # Divider
        elif stripped.startswith("---") or stripped.startswith("___"):
            pass

        # Empty line
        elif not stripped:
            html_parts.append("<br>")

        # Table detection (lines starting with |)
        elif stripped.startswith("|"):
            html_parts.append(f"<p>{_md_to_html(stripped)}</p>")

        # Everything else
        else:
            html_parts.append(f"<p>{_md_to_html(stripped)}</p>")

    html_parts.append(
        f'<div class="footer">TREVOR Intelligence Daily Briefing — '
        f'Generated {now.strftime("%Y-%m-%d %H:%M UTC")}</div>'
    )
    html_parts.append("</body></html>")
    return "\n".join(html_parts)


def _md_to_html(text: str) -> str:
    """Simple markdown inline formatting to HTML."""
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def main(argv: list[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Build briefing PDF")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output)

    print(f"📄 Building PDF from {input_path.name}...")

    markdown = read_markdown(input_path)
    html = markdown_to_pdf_html(markdown)

    # Render via WeasyPrint
    from weasyprint import HTML

    output_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html).write_pdf(str(output_path))

    size = output_path.stat().st_size
    print(f"✅ PDF written to {output_path} ({size / 1024:.0f} KB)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
