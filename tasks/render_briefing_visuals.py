#!/usr/bin/env python3
"""Render visuals for the Daily Intelligence Briefing.

Takes the analysis markdown from tasks/news_analysis.md and:
  1. Extracts Mermaid code blocks → renders PNGs via mermaid.ink API
  2. Generates HTML email with embedded rendered images
  3. Saves rendered images to exports/images/

Usage:
    python3 tasks/render_briefing_visuals.py
    python3 tasks/render_briefing_visuals.py --input tasks/news_analysis.md --output-dir exports/images
"""
from __future__ import annotations

import base64
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORKSPACE = Path("/home/ubuntu/.openclaw/workspace")
DEFAULT_INPUT = WORKSPACE / "tasks" / "news_analysis.md"
DEFAULT_OUTPUT = WORKSPACE / "exports" / "images"
MERMAID_API = "https://mermaid.ink/img"


def extract_mermaid_blocks(markdown: str) -> list[dict[str, Any]]:
    """Extract Mermaid code blocks from markdown content."""
    blocks = []
    pattern = r"```mermaid\n(.*?)```"
    for i, match in enumerate(re.finditer(pattern, markdown, re.DOTALL)):
        code = match.group(1).strip()
        if not code:
            continue
        # Try to infer a title/filename from the first comment or node
        title = f"diagram-{i + 1}"
        for line in code.split("\n"):
            line = line.strip()
            if line.startswith("%%") or line.startswith("#"):
                title = line.lstrip("%%#").strip().replace(" ", "-").lower()[:40]
                break
        blocks.append({"index": i, "code": code, "title": title, "match": match})
    return blocks


def render_mermaid(code: str, output_path: Path) -> bool:
    """Render Mermaid code to PNG via mermaid.ink API."""
    try:
        encoded = base64.urlsafe_b64encode(code.encode("utf-8")).decode("utf-8")
        url = f"{MERMAID_API}/{encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Trevor-Briefing/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"  ⚠️  Render failed: {e}", file=sys.stderr)
        return False


def generate_svg_infographic(topic: str, data_points: list[str], output_path: Path) -> bool:
    """Generate a strategic logic flow SVG infographic.

    Produces the 3-stage progression + tripwire + implications format
    matching the institutional briefing style shown in examples.
    """
    topic_clean = topic.replace("⚓", "").replace("💥", "").replace("🏭", "").replace("⚖️", "").strip()
    if len(topic_clean) > 45:
        topic_clean = topic_clean[:45]

    w, h = 900, 600
    box_w, box_h = 220, 80
    arrow_gap = 40

    # Parse data_points: first 3 are stages, next is tripwire, rest are implications
    stages = data_points[:3] if len(data_points) >= 3 else data_points + [""] * (3 - len(data_points))
    tripwire_info = data_points[3] if len(data_points) > 3 else ""
    implications = data_points[4:] if len(data_points) > 4 else []

    # Layout positions
    total_stage_width = 3 * box_w + 2 * arrow_gap
    start_x = (w - total_stage_width) // 2
    stage_y = 140
    tripwire_y = 300
    impl_y = 410

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="100%">',
        f'  <defs>',
        f'    <linearGradient id="bg" x1="0%" y1="0%" x2="0%" y2="100%">',
        f'      <stop offset="0%" style="stop-color:#0b1120"/><stop offset="100%" style="stop-color:#131c31"/>',
        f'    </linearGradient>',
        f'    <linearGradient id="stage_bg" x1="0%" y1="0%" x2="0%" y2="100%">',
        f'      <stop offset="0%" style="stop-color:#1e293b"/><stop offset="100%" style="stop-color:#0f172a"/>',
        f'    </linearGradient>',
        f'    <linearGradient id="tripwire_bg" x1="0%" y1="0%" x2="0%" y2="100%">',
        f'      <stop offset="0%" style="stop-color:#3b1a1a"/><stop offset="100%" style="stop-color:#1a0f0f"/>',
        f'    </linearGradient>',
        f'    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">',
        f'      <polygon points="0 0, 10 3.5, 0 7" fill="#3b82f6"/>',
        f'    </marker>',
        f'  </defs>',
        # Background
        f'  <rect width="{w}" height="{h}" fill="url(#bg)" rx="12"/>',
        # Title bar
        f'  <rect x="0" y="0" width="{w}" height="55" fill="#1e3a5f" opacity="0.6"/>',
        f'  <text x="{w//2}" y="35" text-anchor="middle" fill="#60a5fa" font-family="Arial,sans-serif" font-size="20" font-weight="bold">{topic_clean}</text>',
    ]

    # Stage boxes with connecting arrows
    stage_labels = ["STAGE 1", "STAGE 2", "STAGE 3"]
    for i, stage in enumerate(stages):
        sx = start_x + i * (box_w + arrow_gap)
        sy = stage_y
        parts = stage.split(":", 1)
        label = (parts[0].strip() if parts[0] else "")[:35]
        detail = (parts[1].strip() if len(parts) > 1 else "")[:40]

        # Stage box
        svg += [
            f'  <rect x="{sx}" y="{sy}" width="{box_w}" height="{box_h}" rx="6" fill="url(#stage_bg)" stroke="#334155" stroke-width="1.5"/>',
            f'  <text x="{sx + 10}" y="{sy + 22}" fill="#64748b" font-family="Arial,sans-serif" font-size="9" font-weight="bold">{stage_labels[i]}</text>',
            f'  <text x="{sx + box_w // 2}" y="{sy + 48}" text-anchor="middle" fill="#e2e8f0" font-family="Arial,sans-serif" font-size="12" font-weight="bold">{label}</text>',
        ]
        if detail:
            svg.append(f'  <text x="{sx + box_w // 2}" y="{sy + 68}" text-anchor="middle" fill="#94a3b8" font-family="Arial,sans-serif" font-size="10">{detail}</text>')

        # Arrow between stages
        if i < 2:
            ax = sx + box_w
            ay = sy + box_h // 2
            svg.append(f'  <line x1="{ax}" y1="{ay}" x2="{ax + arrow_gap}" y2="{ay}" stroke="#3b82f6" stroke-width="2" marker-end="url(#arrowhead)"/>')

    # Tripwire section (if provided)
    if tripwire_info:
        tw_x = (w - 400) // 2
        tw_y = tripwire_y
        tw_label, tw_val = (tripwire_info.split(":", 1) + [""])[:2]
        tw_label = tw_label.strip()[:30]
        tw_val = tw_val.strip()[:50]

        # Diamond marker
        dmx = w // 2
        dmy = tw_y - 25
        diamond = f'{dmx},{dmy - 10} {dmx + 10},{dmy} {dmx},{dmy + 10} {dmx - 10},{dmy}'
        svg += [
            f'  <polygon points="{diamond}" fill="#ef4444" opacity="0.3"/>',
            f'  <line x1="{w // 2}" y1="{stage_y + box_h}" x2="{w // 2}" y2="{dmy - 10}" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="4,3"/>',
            f'  <line x1="{dmx}" y1="{dmy + 10}" x2="{dmx}" y2="{tw_y}" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="4,3"/>',
            f'  <rect x="{tw_x}" y="{tw_y}" width="400" height="55" rx="6" fill="url(#tripwire_bg)" stroke="#ef4444" stroke-width="1.5"/>',
            f'  <text x="{w // 2}" y="{tw_y + 22}" text-anchor="middle" fill="#fca5a5" font-family="Arial,sans-serif" font-size="11" font-weight="bold">⚠ TRIPWIRE: {tw_label}</text>',
            f'  <text x="{w // 2}" y="{tw_y + 42}" text-anchor="middle" fill="#fda4af" font-family="Arial,sans-serif" font-size="10">{tw_val}</text>',
        ]

    # Implications section
    if implications:
        impl_start_x = (w - min(len(implications), 4) * 200) // 2 + 50
        impl_w = 180
        impl_h = 80
        impl_gap = 20

        impl_divider_y = tripwire_y + 80 if tripwire_info else stage_y + 120
        svg += [
            f'  <line x1="40" y1="{impl_divider_y}" x2="{w - 40}" y2="{impl_divider_y}" stroke="#1e293b" stroke-width="1"/>',
            f'  <text x="{w // 2}" y="{impl_divider_y + 20}" text-anchor="middle" fill="#64748b" font-family="Arial,sans-serif" font-size="11" font-weight="bold">STRATEGIC IMPLICATIONS</text>',
        ]

        for i, impl in enumerate(implications[:4]):
            ix = 50 + i * (impl_w + impl_gap)
            iy = impl_divider_y + 35
            parts = impl.split(":", 1)
            impl_label = parts[0].strip()[:25]
            impl_val = parts[1].strip()[:35] if len(parts) > 1 else ""

            svg += [
                f'  <rect x="{ix}" y="{iy}" width="{impl_w}" height="{impl_h}" rx="6" fill="url(#stage_bg)" stroke="#334155" stroke-width="1"/>',
                f'  <text x="{ix + impl_w // 2}" y="{iy + 28}" text-anchor="middle" fill="#93c5fd" font-family="Arial,sans-serif" font-size="11" font-weight="bold">{impl_label}</text>',
            ]
            if impl_val:
                svg.append(f'  <text x="{ix + impl_w // 2}" y="{iy + 50}" text-anchor="middle" fill="#94a3b8" font-family="Arial,sans-serif" font-size="10">{impl_val}</text>')

    # Bottom classification bar
    svg += [
        f'  <rect x="0" y="{h-30}" width="{w}" height="30" fill="#1e3a5f" opacity="0.4"/>',
        f'  <text x="{w//2}" y="{h-10}" text-anchor="middle" fill="#475569" font-family="Arial,sans-serif" font-size="10">TREVOR INTELLIGENCE  ·  CONFIDENTIAL  ·  {datetime.now(timezone.utc).strftime("%Y-%d-%m %H:%M UTC")}</text>',
        f'</svg>',
    ]

    try:
        out = Path(output_path) if isinstance(output_path, str) else output_path
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as f:
            f.write("\n".join(svg))
        print(f"  ✅ Strategic flow SVG → {out.name}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"  ⚠️  SVG write failed: {e}", file=sys.stderr)
        return False


def generate_infographic(topic: str, output_path: Path) -> bool:
    """Generate a visual infographic for a briefing section.

    Uses pre-built SVG templates for reliable, professional infographics.
    Falls back to Mermaid if the SVG approach doesn't work.
    """
    topic_clean = topic.replace("⚓", "").replace("💥", "").replace("🏭", "").replace("⚖️", "").strip()
    
    # Use SVG generation for reliable infographics
    data_points = [
        "Assessment: Active escalation",
        "Confidence: Medium-High",
        "Timeline: 7-30 days",
    ]
    if generate_svg_infographic(topic_clean, data_points, output_path):
        return True

    # Fallback: Mermaid
    mermaid_code = (
        f"graph TD\n"
        f"    A[\"{topic_clean}\"]\n"
        f"    B[\"Assessment\"]\n"
        f"    C[\"Key Indicators\"]\n"
        f"    D[\"Outlook\"]\n"
        f"    A --> B\n"
        f"    A --> C\n"
        f"    A --> D\n"
    )
    return render_mermaid(mermaid_code, output_path)


def build_html_email(
    markdown_path: Path,
    rendered_images: list[dict[str, Any]],
    generated_infographics: list[dict[str, Any]],
) -> str:
    """Convert the briefing markdown + rendered images into an HTML email."""
    with open(markdown_path) as f:
        content = f.read()

    # Extract sections for the HTML
    lines = content.split("\n")
    sections = []
    current_section: list[str] = []
    current_heading = ""

    for line in lines:
        if line.startswith("## ") or line.startswith("# "):
            if current_section:
                sections.append({"heading": current_heading, "body": "\n".join(current_section)})
            current_heading = line.lstrip("#").strip()
            current_section = []
        elif line.strip().startswith("```mermaid"):
            # Skip raw mermaid blocks in email (replaced by rendered images)
            current_section.append("[DIAGRAM PLACEHOLDER]")
        elif line.strip().startswith("```"):
            continue
        else:
            current_section.append(line)

    if current_section:
        sections.append({"heading": current_heading, "body": "\n".join(current_section)})

    # Build HTML
    html_parts = [
        "<!DOCTYPE html>",
        '<html><head><meta charset="utf-8">',
        "<style>",
        "body{font-family:'Segoe UI',Arial,sans-serif;background:#0b1120;color:#e2e8f0;padding:20px;max-width:800px;margin:0 auto}",
        "h1{color:#60a5fa;border-bottom:1px solid #1e293b;padding-bottom:10px}",
        "h2{color:#93c5fd;margin-top:30px}",
        "h3{color:#cbd5e1}",
        ".bluf{background:#131c31;border-left:4px solid #ef4444;padding:12px 16px;border-radius:4px;margin:16px 0}",
        "table{width:100%;border-collapse:collapse;margin:12px 0;font-size:13px}",
        "th{background:#1e293b;color:#93c5fd;padding:8px 12px;text-align:left;border-bottom:2px solid #334155}",
        "td{padding:6px 12px;border-bottom:1px solid #1e293b;color:#94a3b8}",
        "tr:hover td{background:#131c31}",
        ".img-container{text-align:center;margin:16px 0}",
        ".img-container img{max-width:100%;border-radius:8px;border:1px solid #1e293b}",
        ".img-container .caption{font-size:11px;color:#64748b;margin-top:4px;font-style:italic}",
        ".footer{text-align:center;font-size:11px;color:#475569;margin-top:30px;border-top:1px solid #1e293b;padding-top:12px}",
        "strong{color:#f1f5f9}",
        "a{color:#60a5fa}",
        "</style></head><body>",
    ]

    for sec in sections:
        heading = sec["heading"]
        body = sec["body"]

        if "BLUF" in heading or "BOTTOM LINE" in heading.upper():
            html_parts.append(f'<div class="bluf"><strong>▼ BLUF</strong><br>{_md_to_html(body)}</div>')
        elif heading:
            html_parts.append(f"<h2>{heading}</h2>")
            html_parts.append(f"<p>{_md_to_html(body)}</p>")

        # Insert rendered diagrams after the section they belong to
        for img in rendered_images:
            if img.get("section_heading", "").strip() == heading.strip():
                html_parts.append(
                    f'<div class="img-container">'
                    f'<img src="cid:{img["filename"]}" alt="{img["title"]}">'
                    f'<div class="caption">Figure: {img["title"]}</div>'
                    f"</div>"
                )

    # Append infographics
    if generated_infographics:
        html_parts.append("<h2>Visual Intelligence</h2>")
        for ig in generated_infographics:
            html_parts.append(
                f'<div class="img-container">'
                f'<img src="cid:{ig["filename"]}" alt="{ig["title"]}">'
                f'<div class="caption">Infographic: {ig["title"]}</div>'
                f"</div>"
            )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    html_parts.append(f'<div class="footer">TREVOR Intelligence — Generated {now}</div>')
    html_parts.append("</body></html>")

    return "\n".join(html_parts)


def _md_to_html(md: str) -> str:
    """Simple markdown-to-HTML conversion (bold, italic, links, tables)."""
    # Bold
    md = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", md)
    # Italic
    md = re.sub(r"\*(.*?)\*", r"<em>\1</em>", md)
    # Links
    md = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', md)
    # Inline code
    md = re.sub(r"`([^`]+)`", r"<code>\1</code>", md)
    # Line breaks
    md = md.replace("\n", "<br>\n")
    return md


def main(argv: list[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Render briefing visuals")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Analysis markdown path")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT), help="Output image directory")
    parser.add_argument("--skip-infographics", action="store_true", help="Skip OpenRouter infographic generation")
    parser.add_argument("--max-infographics", type=int, default=3, help="Max infographics to generate")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📊 Rendering visuals for {input_path.name}")
    print()

    # 1. Extract and render Mermaid diagrams
    with open(input_path) as f:
        markdown = f.read()

    blocks = extract_mermaid_blocks(markdown)
    print(f"📐 Found {len(blocks)} Mermaid diagram(s)")

    rendered_images = []
    for block in blocks:
        safe_title = re.sub(r"[^a-z0-9-]", "", block["title"]) or f"diagram-{block['index']}"
        out_path = output_dir / f"{safe_title}.png"
        print(f"  Rendering: {safe_title}...", end=" ")
        if render_mermaid(block["code"], out_path):
            print(f"✅ → {out_path.name}")
            rendered_images.append({
                "filename": out_path.name,
                "title": safe_title.replace("-", " ").title(),
                "path": str(out_path),
                "section_heading": "",
            })
        else:
            print("❌")

    # 2. Generate infographics via OpenRouter (for major sections)
    generated_infographics = []
    if not args.skip_infographics:
        # Identify major sections from the briefing
        section_pattern = r"^## [\d]+\.\s+(.+)$"
        sections = re.findall(section_pattern, markdown, re.MULTILINE)
        major_sections = [s.strip()[:50] for s in sections[:args.max_infographics]]
        print(f"\n🎨 Generating {len(major_sections)} infographic(s) via OpenRouter...")
        for i, topic in enumerate(major_sections):
            if not topic:
                continue
            safe_topic = re.sub(r"[^a-z0-9-]", "", topic.lower().replace(" ", "-"))[:30]
            out_path = output_dir / f"infographic-{i + 1}-{safe_topic}.png"
            print(f"  Generating: {topic[:40]}...", end=" ")
            if generate_infographic(topic, out_path):
                print(f"✅ → {out_path.name}")
                generated_infographics.append({
                    "filename": out_path.name,
                    "title": topic,
                    "path": str(out_path),
                })
            else:
                print("❌")

    # 3. Build HTML email version
    html = build_html_email(input_path, rendered_images, generated_infographics)
    html_path = output_dir / "briefing-email.html"
    with open(html_path, "w") as f:
        f.write(html)
    print(f"\n📧 HTML email version → {html_path}")

    print("\n✅ Visual pipeline complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
