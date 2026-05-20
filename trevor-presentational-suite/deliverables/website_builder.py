"""TPS Website Builder — static HTML intelligence site.

Produces a self-contained static site with:
  - index.html (overview + BLUF + key judgments)
  - sections/*.html (one per brief section)
  - assets/ (all generated visual primitives)
  - style.css (brand-compliant styling)

Designed for deployment to Replit, Vercel, or any static host.
No build tools required — pure HTML/CSS/JS.
"""
from __future__ import annotations

import os
import json
import shutil
from typing import Optional

from core.schemas import (
    PresentationPlan,
    AssetProvenance,
    DeliverableKind,
)
from core.style_director import get_brand, get_kent_color
from deliverables.base import BaseDeliverableBuilder


class WebsiteBuilder(BaseDeliverableBuilder):
    """Build static intelligence briefing website."""

    @property
    def kind(self) -> DeliverableKind:
        return DeliverableKind.WEBSITE

    def build(
        self,
        brief_json: dict,
        plan: PresentationPlan,
        asset_outputs: dict[str, str],
        provenance_records: list[AssetProvenance],
        output_path: str,
    ) -> str:
        brand = get_brand()
        os.makedirs(output_path, exist_ok=True)
        os.makedirs(os.path.join(output_path, "sections"), exist_ok=True)
        assets_dir = os.path.join(output_path, "assets")
        os.makedirs(assets_dir, exist_ok=True)

        title = brief_json.get("title", "Intelligence Brief")
        bluf = brief_json.get("bluf", "")
        produced_at = brief_json.get("produced_at", "")
        judgments = brief_json.get("headline_judgments", [])
        sections = brief_json.get("sections", [])

        # Copy assets to site directory
        asset_map = {}
        for asset_id, src_path in asset_outputs.items():
            if os.path.exists(src_path):
                fname = os.path.basename(src_path)
                dst = os.path.join(assets_dir, fname)
                shutil.copy2(src_path, dst)
                asset_map[asset_id] = f"assets/{fname}"

        # Write CSS
        self._write_css(output_path, brand)

        # Write index.html
        self._write_index(
            output_path, title, bluf, produced_at,
            judgments, sections, asset_map, brand
        )

        # Write section pages
        for i, section in enumerate(sections):
            self._write_section_page(
                output_path, i, section, asset_map, brand
            )

        # Write provenance page
        self._write_provenance_page(
            output_path, provenance_records, brand
        )

        return output_path

    def _write_css(self, output_dir, brand):
        css = f"""
:root {{
    --primary: {brand.color_primary};
    --accent: {brand.color_accent};
    --body: {brand.color_body};
    --surface: #F5F3EF;
    --font: 'Inter', system-ui, sans-serif;
}}
* {{margin:0;padding:0;box-sizing:border-box;}}
body {{
    font-family:var(--font);
    background:var(--surface);
    color:var(--body);
    line-height:1.6;
}}
header {{
    background:var(--primary);
    color:white;
    padding:40px 60px;
}}
header h1 {{font-size:28px;margin-bottom:8px;}}
header p {{font-size:14px;opacity:0.8;max-width:700px;}}
header .date {{font-size:11px;opacity:0.5;margin-top:12px;}}
nav {{
    background:white;
    padding:12px 60px;
    border-bottom:2px solid var(--accent);
    display:flex;
    gap:20px;
    flex-wrap:wrap;
}}
nav a {{
    color:var(--primary);
    text-decoration:none;
    font-size:13px;
    font-weight:500;
}}
nav a:hover {{color:var(--accent);}}
main {{padding:40px 60px;max-width:1200px;}}
.bluf {{
    background:white;
    padding:24px;
    border-left:4px solid var(--accent);
    margin-bottom:32px;
    font-size:15px;
    border-radius:0 4px 4px 0;
}}
.judgment {{
    background:white;
    padding:16px 20px;
    margin-bottom:12px;
    border-radius:4px;
    display:flex;
    align-items:flex-start;
    gap:12px;
}}
.kent-badge {{
    font-size:10px;
    color:white;
    padding:4px 10px;
    border-radius:3px;
    white-space:nowrap;
    flex-shrink:0;
}}
.section-card {{
    background:white;
    padding:24px;
    margin-bottom:16px;
    border-radius:4px;
}}
.section-card h3 {{color:var(--primary);margin-bottom:8px;}}
.section-card p {{font-size:14px;}}
.asset-grid {{
    display:grid;
    grid-template-columns:repeat(auto-fill, minmax(400px, 1fr));
    gap:20px;
    margin:32px 0;
}}
.asset-card {{
    background:white;
    padding:12px;
    border-radius:4px;
    text-align:center;
}}
.asset-card img {{max-width:100%;border-radius:2px;}}
footer {{
    background:var(--primary);
    color:white;
    padding:20px 60px;
    font-size:11px;
    opacity:0.7;
    display:flex;
    justify-content:space-between;
}}
table {{width:100%;border-collapse:collapse;font-size:12px;}}
th,td {{padding:8px 12px;text-align:left;border-bottom:1px solid #ddd;}}
th {{background:var(--primary);color:white;}}
"""
        with open(os.path.join(output_dir, "style.css"), "w") as f:
            f.write(css)

    def _write_index(self, output_dir, title, bluf, produced_at,
                     judgments, sections, asset_map, brand):
        # Navigation links
        nav_links = '<a href="index.html">Overview</a>\n'
        for i, s in enumerate(sections):
            stitle = s.get("title", f"Section {i+1}")
            nav_links += f'    <a href="sections/{i}.html">{stitle}</a>\n'
        nav_links += '    <a href="provenance.html">Provenance</a>\n'

        # Judgment cards
        judgment_html = ""
        for j in judgments[:8]:
            claim = j.get("claim", j.get("judgment", ""))
            kent = j.get("kent_band", "")
            color = get_kent_color(kent) if kent else brand.color_accent
            band_label = kent.replace("_", " ").title() if kent else "—"
            judgment_html += f"""
    <div class="judgment">
        <span class="kent-badge" style="background:{color}">{band_label}</span>
        <span>{claim}</span>
    </div>"""

        # Section cards
        section_html = ""
        for i, s in enumerate(sections):
            stitle = s.get("title", f"Section {i+1}")
            narrative = s.get("narrative", "")[:200]
            section_html += f"""
    <div class="section-card">
        <h3><a href="sections/{i}.html" style="color:inherit;text-decoration:none;">{stitle}</a></h3>
        <p>{narrative}...</p>
    </div>"""

        # Asset grid
        asset_html = ""
        for asset_id, rel_path in asset_map.items():
            if rel_path.endswith(('.png', '.jpg', '.svg')):
                asset_html += f"""
    <div class="asset-card">
        <img src="{rel_path}" alt="{asset_id}" loading="lazy" />
    </div>"""

        html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="style.css">
</head><body>
<header>
    <h1>{title}</h1>
    <p>{bluf[:300]}</p>
    <div class="date">{produced_at}</div>
</header>
<nav>
    {nav_links}
</nav>
<main>
    <div class="bluf">{bluf}</div>

    <h2 style="margin-bottom:16px;">Key Judgments</h2>
    {judgment_html}

    <h2 style="margin:32px 0 16px;">Sections</h2>
    {section_html}

    {f'<h2 style="margin:32px 0 16px;">Visual Assets</h2><div class="asset-grid">{asset_html}</div>' if asset_html else ''}
</main>
<footer>
    <span>Trevor Intelligence</span>
    <span>PENDING HUMAN ANALYST QC REVIEW</span>
</footer>
</body></html>"""

        with open(os.path.join(output_dir, "index.html"), "w") as f:
            f.write(html)

    def _write_section_page(self, output_dir, idx, section, asset_map, brand):
        stitle = section.get("title", f"Section {idx+1}")
        narrative = section.get("narrative", "")
        subsections = section.get("subsections", [])

        sub_html = ""
        for ss in subsections:
            ss_title = ss.get("title", "")
            ss_narrative = ss.get("narrative", "")
            sub_html += f"""
    <div class="section-card" style="margin-left:20px;">
        <h3>{ss_title}</h3>
        <p>{ss_narrative}</p>
    </div>"""

        html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{stitle}</title>
<link rel="stylesheet" href="../style.css">
</head><body>
<header>
    <h1>{stitle}</h1>
</header>
<nav>
    <a href="../index.html">Overview</a>
    <a href="../provenance.html">Provenance</a>
</nav>
<main>
    <div class="bluf">{narrative}</div>
    {sub_html}
</main>
<footer>
    <span>Trevor Intelligence</span>
    <span>PENDING HUMAN ANALYST QC REVIEW</span>
</footer>
</body></html>"""

        with open(os.path.join(output_dir, "sections", f"{idx}.html"), "w") as f:
            f.write(html)

    def _write_provenance_page(self, output_dir, provenance_records, brand):
        rows = ""
        for p in provenance_records:
            rows += f"""
        <tr>
            <td>{p.asset_id}</td>
            <td>{p.kind.value if hasattr(p.kind, 'value') else p.kind}</td>
            <td>{p.generator}</td>
            <td>{p.model_used}</td>
            <td>{p.provider}</td>
            <td>${p.actual_cost_usd:.4f}</td>
            <td>{p.qc_status.value}</td>
        </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Provenance</title>
<link rel="stylesheet" href="style.css">
</head><body>
<header>
    <h1>Asset Provenance</h1>
    <p>All generated assets with model attribution and QC status.</p>
</header>
<nav>
    <a href="index.html">Overview</a>
</nav>
<main>
    <table>
        <thead>
            <tr>
                <th>Asset ID</th>
                <th>Kind</th>
                <th>Generator</th>
                <th>Model</th>
                <th>Provider</th>
                <th>Cost</th>
                <th>QC Status</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
</main>
<footer>
    <span>Trevor Intelligence</span>
    <span>PENDING HUMAN ANALYST QC REVIEW</span>
</footer>
</body></html>"""

        with open(os.path.join(output_dir, "provenance.html"), "w") as f:
            f.write(html)
