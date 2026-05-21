#!/usr/bin/env python3
"""Bloomberg-grade brief PDF assembler.

Takes a brief JSON + generated assets (cover, charts, maps) and assembles
them into a single professional PDF via Jinja2 HTML template + WeasyPrint.

Usage:
    python3 scripts/present/assemble_brief.py \\
        --brief test_fixtures/sample_brief.json \\
        --cover exports/present/test-brief-2026-05-20/cover.png \\
        --kent exports/present/test-brief-2026-05-20/kent-bar.png \\
        --trade exports/present/test-brief-2026-05-20/trade-bar.png \\
        --map exports/present/test-brief-2026-05-20/map.png \\
        --output exports/present/test-brief-2026-05-20/briefing.pdf
"""

from __future__ import annotations
import sys
sys.path.insert(0, "/home/ubuntu/.openclaw/workspace")

import sys
if "/home/ubuntu/.openclaw/workspace" not in sys.path:
import sys
import argparse
import json
import pathlib
import sys
import jinja2
from weasyprint import HTML
WORKSPACE = pathlib.Path("/home/ubuntu/.openclaw/workspace")
TEMPLATE = WORKSPACE / "scripts" / "present" / "templates" / "pdf" / "bloomberg_brief.html"
def format_number(value):
    """Jinja2 filter: format number with commas."""
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return str(value)
def build_html(brief: dict, cover: str = "", kent_chart: str = "",
               trade_chart: str = "", map_image: str = "") -> str:
    """Render the Jinja2 template with brief data and asset paths."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATE.parent)),
        autoescape=False,
    )
    env.filters["format_number"] = format_number
    template = env.get_template(TEMPLATE.name)
    def resolve_abs(path_str: str) -> str:
        p = pathlib.Path(path_str)
        if p.exists():
            return p.resolve().as_uri()
        return ""
    context = {
        "title": brief.get("title", "Intelligence Briefing"),
        "date": brief.get("produced_at", "")[:10],
        "brief_id": brief.get("brief_id", ""),
        "bluf": brief.get("bluf", ""),
        "headline_judgments": brief.get("headline_judgments", []),
        "sections": brief.get("sections", []),
        "watch_items": brief.get("watch_items", []),
        "trade_positions": brief.get("trade_positions", []),
        "action_lines": brief.get("action_lines", []),
        "gaps": brief.get("gaps", []),
        "sources": brief.get("sources", []),
        "sources_count": str(len(brief.get("sources", []))),
        "cover_image": resolve_abs(cover),
        "kent_chart": resolve_abs(kent_chart),
        "trade_chart": resolve_abs(trade_chart),
        "map_image": resolve_abs(map_image),
    }
    return template.render(**context)
def assemble(brief_path: str, output_path: str, cover: str = "",
             kent: str = "", trade: str = "", map_img: str = "") -> str:
    """Full assembly pipeline: HTML → PDF.
    Returns output path.
    """
    brief = json.loads(pathlib.Path(brief_path).read_text())
    print("  Rendering HTML template...")
    html = build_html(brief, cover=cover, kent_chart=kent,
                      trade_chart=trade, map_image=map_img)
    html_path = output_path.replace(".pdf", ".html")
    pathlib.Path(html_path).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(html_path).write_text(html)
    print("  Generating PDF via WeasyPrint...")
    HTML(string=html).write_pdf(output_path)
    size_kb = pathlib.Path(output_path).stat().st_size / 1024
    print(f"  ✅ PDF: {output_path} ({size_kb:.0f} KB)")
    return output_path
def main():
    parser = argparse.ArgumentParser(description="Bloomberg-grade brief PDF assembler")
    parser.add_argument("--brief", required=True, help="Path to brief JSON")
    parser.add_argument("--cover", default="", help="Cover image path")
    parser.add_argument("--kent", default="", help="Kent bar chart path")
    parser.add_argument("--trade", default="", help="Trade bar chart path")
    parser.add_argument("--map", default="", help="Map image path")
    parser.add_argument("--output", "-o", default="exports/briefing.pdf",
                        help="Output PDF path")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        try:
            import weasyprint
            print("  weasyprint: available")
            import jinja2
            print("  jinja2: available")
            print("  ASSEMBLER READY")
        except ImportError as e:
            print(f"  ASSEMBLER DISABLED: {e}")
        return
    if not pathlib.Path(args.brief).exists():
        print(f"ERROR: Brief not found: {args.brief}")
        sys.exit(1)
    assemble(
        brief_path=args.brief,
        output_path=args.output,
        cover=args.cover,
        kent=args.kent,
        trade=args.trade,
        map_img=args.map,
    )
if __name__ == "__main__":
    main()
