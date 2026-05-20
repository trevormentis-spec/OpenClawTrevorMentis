"""TPS Executive Summary Card — single-page visual brief.

Produces a high-density HTML summary card (A4 or 16:9) containing:
  - Title + BLUF
  - Top 3 judgments with kent band colors
  - Key chart or map (embedded)
  - QC watermark

Can be rendered to PNG via weasyprint for distribution.
"""
from __future__ import annotations

import os
from typing import Optional

from core.schemas import (
    PresentationPlan,
    AssetProvenance,
    DeliverableKind,
)
from core.style_director import get_brand, get_kent_color, inject_brand_css
from deliverables.base import BaseDeliverableBuilder


class ExecCardBuilder(BaseDeliverableBuilder):
    """Build executive summary card."""

    @property
    def kind(self) -> DeliverableKind:
        return DeliverableKind.EXEC_CARD

    def build(
        self,
        brief_json: dict,
        plan: PresentationPlan,
        asset_outputs: dict[str, str],
        provenance_records: list[AssetProvenance],
        output_path: str,
    ) -> str:
        brand = get_brand()
        title = brief_json.get("title", "Intelligence Brief")
        bluf = brief_json.get("bluf", "")
        produced_at = brief_json.get("produced_at", "")
        judgments = brief_json.get("headline_judgments", [])

        # Build judgment rows
        judgment_html = ""
        for j in judgments[:4]:
            claim = j.get("claim", j.get("judgment", ""))
            kent = j.get("kent_band", "")
            color = get_kent_color(kent) if kent else brand.color_accent
            band_label = kent.replace("_", " ").title() if kent else "—"
            judgment_html += f"""
            <div class="judgment-row">
                <div class="kent-badge" style="background:{color}">{band_label}</div>
                <div class="judgment-text">{claim[:150]}</div>
            </div>"""

        # Find best asset to embed (prefer chart or map)
        embed_html = ""
        for asset_id, path in asset_outputs.items():
            if path.endswith('.png') or path.endswith('.jpg'):
                embed_html = f'<img src="{path}" class="hero-asset" />'
                break
            elif path.endswith('.svg'):
                embed_html = f'<img src="{path}" class="hero-asset" />'
                break

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
* {{margin:0;padding:0;box-sizing:border-box;}}
body {{
    width:1200px;height:675px;
    font-family:Inter,system-ui,sans-serif;
    background:#F5F3EF;
    color:{brand.color_body};
    overflow:hidden;
    position:relative;
}}
.header {{
    background:{brand.color_primary};
    color:white;
    padding:24px 32px;
    display:flex;
    justify-content:space-between;
    align-items:center;
}}
.header h1 {{font-size:22px;font-weight:700;max-width:70%;}}
.header .date {{font-size:11px;opacity:0.7;}}
.bluf {{
    padding:16px 32px;
    font-size:13px;
    line-height:1.5;
    border-bottom:2px solid {brand.color_accent};
    background:white;
}}
.content {{
    display:flex;
    padding:16px 32px;
    gap:24px;
    height:calc(100% - 160px);
}}
.judgments {{flex:1;}}
.judgments h3 {{
    font-size:11px;
    text-transform:uppercase;
    color:{brand.color_accent};
    margin-bottom:12px;
    letter-spacing:1px;
}}
.judgment-row {{
    display:flex;
    align-items:flex-start;
    gap:10px;
    margin-bottom:10px;
}}
.kent-badge {{
    font-size:9px;
    color:white;
    padding:3px 8px;
    border-radius:3px;
    white-space:nowrap;
    flex-shrink:0;
    margin-top:2px;
}}
.judgment-text {{
    font-size:12px;
    line-height:1.4;
}}
.asset-panel {{
    flex:1;
    display:flex;
    align-items:center;
    justify-content:center;
}}
.hero-asset {{
    max-width:100%;
    max-height:100%;
    object-fit:contain;
    border-radius:4px;
    box-shadow:0 1px 4px rgba(0,0,0,0.1);
}}
.qc-watermark {{
    position:absolute;
    bottom:8px;
    left:32px;
    right:32px;
    font-size:8px;
    color:#999;
    display:flex;
    justify-content:space-between;
}}
</style></head><body>
<div class="header">
    <h1>{title}</h1>
    <div class="date">{produced_at}</div>
</div>
<div class="bluf">{bluf[:300]}</div>
<div class="content">
    <div class="judgments">
        <h3>Key Judgments</h3>
        {judgment_html}
    </div>
    <div class="asset-panel">
        {embed_html if embed_html else '<div style="color:#999;font-size:12px;">No visual assets</div>'}
    </div>
</div>
<div class="qc-watermark">
    <span>Trevor Intelligence</span>
    <span>PENDING HUMAN ANALYST QC REVIEW</span>
</div>
</body></html>"""

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        # Write HTML
        html_path = output_path
        if output_path.endswith('.png'):
            html_path = output_path.replace('.png', '.html')

        with open(html_path, "w") as f:
            f.write(html)

        # Try to render to PNG via weasyprint
        if output_path.endswith('.png'):
            try:
                from weasyprint import HTML
                HTML(string=html).write_png(
                    output_path, presentational_hints=True
                )
                return output_path
            except ImportError:
                pass

        return html_path
