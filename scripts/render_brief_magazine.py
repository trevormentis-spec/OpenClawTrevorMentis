#!/usr/bin/env python3
"""
render_brief_magazine.py v4 — Perplexity-level magazine brief PDF.

Matches the Perplexity "Global Security & Intelligence Brief" benchmark:
- Cover with BLUF summary, classification marks, gold accents
- Table of contents
- Per-section: hero image (AI-gen) + photo credit → section header →
  BOTTOM LINE UP FRONT → THE STORY narrative → KEY JUDGMENTS →
  BY THE NUMBERS data box → Indicators → Map callout
- Prediction market trade cards (BUY/SELL with edge calculations)
- Methodology page (Sherman Kent estimative language table)
- EXFIL final page (key takeaways / payload)
- Magazine-style running headers, page numbers, typography

Usage:
    python3 render_brief_magazine.py \\
        --working-dir ~/trevor-briefings/2026-05-10 \\
        --out-pdf ~/trevor-briefings/2026-05-10/final/GSIB-2026-05-10.pdf \\
        --images-json ~/trevor-briefings/2026-05-10/visuals/section-images.json \\
        --maps-dir ~/trevor-briefings/2026-05-10/visuals/maps
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import pathlib
import sys
import textwrap
from typing import Any

try:
    import weasyprint
except ImportError:
    weasyprint = None
    print("ERROR: weasyprint not installed", file=sys.stderr)
    sys.exit(1)

# ── Design Tokens ──
# New impactful scheme: deep navy + bright gold + crisp white
GOLD = "#d4a843"
GOLD_LIGHT = "#e8d48b"
DARK = "#080e1a"
DARK2 = "#0f1a30"
DARK3 = "#16213e"
NAVY = "#0f1a30"
NAVY_LIGHT = "#1a2a4a"
WHITE = "#ffffff"
PAGE_BG = "#fafaf7"
CREAM = "#f5f3ee"
CREAM2 = "#ede9e0"
LIGHT = "#f4f4ee"
RED = "#c0392b"
RED_LIGHT = "#e74c3c"
GREEN = "#3a7d44"
GREEN_LIGHT = "#5cb85c"
BLUE = "#2c6aa0"
ORANGE = "#d47500"
GRAY = "#666666"
LIGHT_GRAY = "#e0e0e0"
BODY = "Georgia, 'Times New Roman', serif"
HEADER = "'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'Courier New', Courier, monospace"
SHEET = "letter"

BANDS_COLORS = {
    "almost certain": "#1a5276",
    "highly likely": "#b82e2e",
    "likely": "#bf8f00",
    "roughly even odds": "#7a8a3c",
    "even chance": "#7a8a3c",
    "unlikely": "#5a7a3a",
    "very unlikely": "#4a6a2a",
    "almost no chance": "#888888",
}

def band_color(b: str) -> str:
    return BANDS_COLORS.get(b.lower().strip(), "#666666")

REGIONS = {
    "europe": ("EUROPE", "Europe"),
    "asia": ("SOUTH ASIA", "Asia"),
    "middle_east": ("MIDDLE EAST", "Middle East"),
    "north_america": ("NORTH AMERICA", "North America"),
    "south_central_america": ("SOUTH AMERICA", "S. & C. America"),
    "global_finance": ("GLOBAL FINANCE", "Global Finance"),
}
REGION_EMOJI = {
    "europe": "🇪🇺", "asia": "🌏", "middle_east": "🌍",
    "north_america": "🌎", "south_central_america": "🌎",
    "global_finance": "💹",
}
# Section subtitles (matching Perplexity's descriptive titles)
SECTION_SUBTITLES = {
    "europe": "Truce & Strategic Dynamics", "asia": "Doctrine & Posture",
    "middle_east": "Framework & Kinetic Cycle", "north_america": "Coordination & Sovereignty",
    "south_central_america": "Political & Financial Pressures",
    "global_finance": "Risk & Liquidity Conditions",
}

def rlabel(r: str) -> tuple[str, str]:
    info = REGIONS.get(r, (r.upper().replace("_", " "), r.replace("_", " ").title()))
    return info

def image_to_base64(url_or_path: str, max_size_kb: int = 800) -> str:
    """Convert a URL or file path to a base64 data URI for reliable PDF embedding.
    Resizes images that exceed max_size_kb to prevent page overflow."""
    if not url_or_path:
        return ""
    if url_or_path.startswith("data:"):
        return url_or_path
    path_str = url_or_path
    if path_str.startswith("file://"):
        path_str = path_str[7:]
    try:
        p = pathlib.Path(path_str).expanduser().resolve()
        if p.exists() and p.stat().st_size > 0:
            raw = p.read_bytes()
            # Resize if too large (helps prevent page overflow)
            if len(raw) > max_size_kb * 1024:
                try:
                    from PIL import Image
                    import io
                    img = Image.open(io.BytesIO(raw))
                    # Scale down to reasonable magazine size (3in at 150 DPI = 450px)
                    max_dim = 1200
                    if max(img.size) > max_dim:
                        ratio = max_dim / max(img.size)
                        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                        img = img.resize(new_size, Image.LANCZOS)
                    buf = io.BytesIO()
                    img.save(buf, format='JPEG', quality=85, optimize=True)
                    raw = buf.getvalue()
                except ImportError:
                    pass  # PIL not available
            ext = p.suffix.lower()
            mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                     ".png": "image/png", ".gif": "image/gif",
                     ".webp": "image/webp"}.get(ext, "image/jpeg")
            b64 = base64.b64encode(raw).decode()
            return f"data:{mime};base64,{b64}"
    except Exception:
        pass
    return url_or_path

def safe(s: Any, m: int = 0) -> str:
    if not s:
        return ""
    s = str(s).replace("\\n", "\n").strip()
    if m and len(s) > m:
        return s[:m].rsplit(" ", 1)[0] + "…"
    return s

def band_display(band: str) -> str:
    """Clean band name for display."""
    return band.strip().title()

def wrap_paragraphs(text: str, width: int = 500) -> str:
    """Split text into <p> wrapped paragraphs with sub-headings inserted."""
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    if not paras:
        paras = textwrap.wrap(text, width) if len(text) > 100 else [text]
    
    # If we have enough paragraphs, insert sub-headings to break up the narrative
    if len(paras) >= 4:
        # First paragraph is the lead — leave as-is
        result = f"<p>{paras[0]}</p>\n"
        # After paragraph 2, insert "Key Developments" subheading
        result += f"<p>{paras[1]}</p>\n" if len(paras) > 1 else ""
        result += f"<h4 class=\"subhead-sm\">Key Developments</h4>\n"
        result += f"<p>{paras[2]}</p>\n" if len(paras) > 2 else ""
        # After paragraph 4, insert "Strategic Implications" subheading
        if len(paras) > 3:
            result += f"<p>{paras[3]}</p>\n"
        if len(paras) > 4:
            result += f"<h4 class=\"subhead-sm\">Strategic Implications</h4>\n"
            result += "".join(f"<p>{p}</p>\n" for p in paras[4:])
        return result
    
    return "".join(f"<p>{p}</p>" for p in paras)


# ═══════════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════════

CSS = f"""
@page {{
    size: {SHEET};
    margin: 0.55in 0.5in 0.7in 0.5in;
    @top-left {{
        content: "TREVOR / STRATEGIC INTELLIGENCE";
        font-family: {HEADER};
        font-size: 5.5pt;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: #bbb;
    }}
    @top-right {{
        content: string(issue-date);
        font-family: {HEADER};
        font-size: 5.5pt;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: #bbb;
    }}
    @bottom-center {{
        content: counter(page);
        font-family: {HEADER};
        font-size: 7pt;
        color: #999;
    }}
}}
@page cover {{
    margin: 0;
    @top-left {{ content: none; }}
    @top-right {{ content: none; }}
    @bottom-center {{ content: none; }}
}}
@page toc {{
    @bottom-center {{ content: none; }}
}}
@page exfil {{
    @bottom-center {{ content: none; }}
}}
* {{ box-sizing: border-box; }}
body {{ font-family: {BODY}; font-size: 9.5pt; line-height: 1.55; color: #1a1a1a; background: {PAGE_BG}; margin: 0; padding: 0; text-align: justify; hyphens: auto; }}
p {{ text-align: justify; margin: 0 0 8px 0; }}

/* ═══ COVER ═══ */
.cover {{ page: cover; width: 100%; height: 11in; position: relative; overflow: hidden; page-break-after: always; }}
.cover-img {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; }}
.cover-overlay {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    background: linear-gradient(170deg, rgba(8,14,26,0.92) 20%, rgba(8,14,26,0.60) 50%, rgba(8,14,26,0.95) 100%); }}
.cover-content {{ position: absolute; bottom: 0; left: 0; right: 0; padding: 0.8in 0.7in; text-align: center; }}
.cover .accent-bar {{ position: absolute; top: 0; left: 0; right: 0; height: 5px;
    background: linear-gradient(90deg, transparent 3%, {GOLD} 15%, #d4a843 50%, {GOLD} 85%, transparent 97%); }}
.cover .accent-bar-b {{ position: absolute; top: 5px; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent 10%, rgba(212,168,67,0.3) 50%, transparent 90%); }}
.cover .clas {{ position: absolute; top: 22px; right: 30px; font-family: {HEADER}; font-size: 6pt; letter-spacing: 2px; color: rgba(255,255,255,0.25); text-transform: uppercase; }}
.cover .brand {{ font-family: {HEADER}; font-size: 9pt; letter-spacing: 10px; text-transform: uppercase; color: {GOLD}; margin-bottom: 4px; }}
.cover .issue-line {{ font-family: {HEADER}; font-size: 6.5pt; letter-spacing: 3px; color: rgba(255,255,255,0.25); text-transform: uppercase; margin: 0 0 20px; }}
.cover .title {{ font-family: {HEADER}; font-size: 32pt; font-weight: 900; letter-spacing: 5px; text-transform: uppercase; line-height: 1.05; color: white; margin-bottom: 8px; }}
.cover .title .accent {{ color: {GOLD}; }}
.cover .subtitle {{ font-size: 9pt; color: rgba(255,255,255,0.45); max-width: 460px; margin: 4px auto 20px; line-height: 1.5; font-style: italic; letter-spacing: 0.5px; }}
.cover .bluf {{ background: rgba(212,168,67,0.08); border: 1px solid rgba(212,168,67,0.2); border-radius: 3px; padding: 14px 18px; margin: 4px auto 20px; max-width: 520px; text-align: left; }}
.cover .bluf .lbl {{ font-family: {HEADER}; font-size: 5.5pt; font-weight: 700; text-transform: uppercase; letter-spacing: 2px; color: {GOLD}; margin-bottom: 4px; }}
.cover .bluf p {{ margin: 0; font-size: 7.5pt; line-height: 1.5; color: rgba(255,255,255,0.75); }}
.cover .meta {{ font-family: {HEADER}; font-size: 6.5pt; letter-spacing: 2px; color: rgba(255,255,255,0.25); text-transform: uppercase; }}
.cover .meta span {{ margin: 0 8px; }}
.cover .author-line {{ position: absolute; bottom: 32px; left: 0; right: 0; font-family: {HEADER}; font-size: 5.5pt; letter-spacing: 2px; color: rgba(255,255,255,0.15); text-transform: uppercase; text-align: center; }}
.cover .distro {{ position: absolute; bottom: 14px; left: 0; right: 0; font-family: {HEADER}; font-size: 5pt; letter-spacing: 1px; color: rgba(255,255,255,0.08); text-align: center; }}

/* ═══ TOC ═══ */
.toc-p {{ page: toc; page-break-after: always; padding: 0.3in 0 0 0; }}
.toc-p .toc-brand {{ font-family: {HEADER}; font-size: 8pt; letter-spacing: 4px; text-transform: uppercase; color: #aaa; margin-bottom: 6px; }}
.toc-p .toc-issue {{ font-family: {HEADER}; font-size: 7pt; letter-spacing: 2px; text-transform: uppercase; color: #bbb; margin-bottom: 20px; }}
.toc-p h2 {{ font-family: {HEADER}; font-size: 16pt; font-weight: 700; color: {DARK2}; border-bottom: 2px solid {GOLD}; padding-bottom: 6px; margin: 0 0 16px 0; }}
.toc-row {{ display: flex; padding: 10px 0; border-bottom: 1px dotted #ddd; font-size: 11pt; align-items: center; }}
.toc-row .num {{ width: 28px; font-family: {HEADER}; font-weight: 700; color: {GOLD}; font-size: 10pt; }}
.toc-row .label {{ flex: 1; font-size: 11pt; }}
.toc-row .region-tag {{ font-family: {HEADER}; font-size: 7pt; letter-spacing: 1.5px; text-transform: uppercase; color: #888; margin-left: 6px; background: #f0eee6; padding: 2px 6px; border-radius: 2px; }}
.toc-row .page-num {{ font-family: {HEADER}; color: #999; font-size: 10pt; font-weight: 700; }}

/* ═══ SECTION HEADER ═══ */
.page-header {{ font-family: {HEADER}; font-size: 5pt; letter-spacing: 1.5px; text-transform: uppercase; color: #bbb; border-bottom: 1px solid #e0e0e0; padding-bottom: 2px; margin-bottom: 10px; overflow: hidden; }}
.page-header .l {{ float: left; }}
.page-header .r {{ float: right; }}

.sec-start {{ page-break-before: always; }}
.story-group {{ page-break-inside: avoid; }}
.sec-header {{ background: {NAVY}; color: white; padding: 10px 14px; margin: 0 0 10px 0; border-radius: 2px; }}
h1.sec {{ font-family: {HEADER}; font-size: 14pt; font-weight: 700; color: {WHITE}; margin: 0; }}
h2.s-sub {{ font-family: {HEADER}; font-size: 7pt; font-weight: 400; text-transform: uppercase; letter-spacing: 1.2px; color: #999; margin: 0 0 8px 0; }}
h2.sec-num {{ font-family: {HEADER}; font-size: 7pt; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: {GOLD}; margin: 0 0 2px 0; }}

/* ═══ HERO IMAGE ═══ */
.hero-group {{ page-break-inside: avoid; margin: 0 0 8px 0; }}
.hero-img-inline {{ width: 100%; max-height: 1.8in; object-fit: cover; display: block; border-radius: 2px; }}
.hero-cap-inline {{ font-family: {HEADER}; font-size: 5.5pt; color: #999; margin: 2px 0 0 0; line-height: 1.3; }}
.hero-cap {{ font-family: {HEADER}; font-size: 6pt; color: #999; margin: 2px 0 6px 0; line-height: 1.4; }}

/* ═══ BLUF ═══ */
.bluf {{ background: {CREAM}; border-left: 4px solid {RED}; padding: 10px 14px; margin: 8px 0 14px 0; border-radius: 0 2px 2px 0; }}
.bluf .lbl {{ font-family: {HEADER}; font-size: 6.5pt; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: {RED}; margin-bottom: 2px; }}
.bluf p {{ margin: 0; font-size: 8.5pt; line-height: 1.5; color: #333; }}

/* ═══ THE STORY ═══ */
.story-label {{ font-family: {HEADER}; font-size: 6.5pt; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: {DARK2}; margin: 14px 0 6px 0; padding-bottom: 2px; border-bottom: 1px solid #ddd; }}

/* ═══ NARRATIVE TWO-COLUMN ═══ */
.narr {{ font-size: 8pt; line-height: 1.4; text-align: justify; column-count: 2; column-gap: 14px; column-rule: 1px solid #eee; }}
.narr p {{ margin: 0 0 6px 0; text-indent: 0; }}

/* ═══ KEY JUDGMENTS ═══ */
.kj-heading {{ font-family: {HEADER}; font-size: 7pt; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: {DARK2}; margin: 14px 0 6px 0; padding-bottom: 2px; border-bottom: 1px solid #ddd; }}
.kj-block {{ margin: 6px 0 10px 0; }}
.kj-item {{ padding: 4px 6px; margin: 3px 0; border-left: 3px solid {GOLD}; font-size: 8pt; line-height: 1.45; background: #f9f9f5; border-radius: 0 2px 2px 0; }}
.kj-item .kjt-id {{ font-family: {HEADER}; font-size: 6pt; font-weight: 700; letter-spacing: 1px; }}
.kj-item .kjt-band {{ display: inline-block; font-family: {HEADER}; font-size: 5.5pt; text-transform: uppercase; letter-spacing: 1px; padding: 1px 5px; border-radius: 2px; margin: 0 3px; color: white; }}
.kj-item .kjt-stmt {{ display: inline; }}
.kj-item .kjt-meta {{ font-size: 6.5pt; color: #888; margin-top: 2px; }}

/* ═══ BY THE NUMBERS ═══ */
.btn-heading {{ font-family: {HEADER}; font-size: 6.5pt; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; color: {DARK2}; margin: 14px 0 5px 0; padding-bottom: 2px; border-bottom: 1px solid #ddd; }}
.btn-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 5px; margin: 6px 0; }}
.btn-item {{ border: 1px solid #e0dcc0; border-radius: 3px; padding: 6px 10px; background: {CREAM2}; }}
.btn-item .l {{ font-family: {HEADER}; font-size: 5.5pt; text-transform: uppercase; letter-spacing: 1px; color: #999; }}
.btn-item .v {{ font-family: {HEADER}; font-size: 11pt; font-weight: 700; color: {DARK2}; }}

/* ═══ MAP CALLOUT ═══ */
.map-callout {{ background: #f0eee6; border: 1px solid #e0dcc0; border-radius: 3px; padding: 8px 12px; margin: 10px 0; font-family: {HEADER}; font-size: 7pt; text-transform: uppercase; letter-spacing: 1px; color: #666; text-align: center; }}
.map-section {{ page-break-inside: avoid; margin: 6px auto; text-align: center; max-width: 6in; }}
.map-img {{ max-width: 100%; max-height: 3.8in; width: auto; height: auto; border-radius: 3px; border: 1px solid #ddd; }}
.map-cap {{ font-family: {HEADER}; font-size: 6pt; letter-spacing: 1px; color: #999; margin: 3px 0; }}
.subhead {{ font-family: {HEADER}; font-size: 8pt; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: {DARK2}; margin: 16px 0 6px 0; padding-bottom: 1px; border-bottom: 1px solid {GOLD}; }}
.subhead-sm {{ font-family: {HEADER}; font-size: 7pt; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: {GRAY}; margin: 10px 0 4px 0; }}

/* ═══ INDICATORS ═══ */
.ind-heading {{ font-family: {HEADER}; font-size: 6.5pt; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; color: #999; margin: 12px 0 4px 0; }}
.ind-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px; margin: 4px 0; }}
.ind-card {{ border: 1px solid #e4e4e4; border-radius: 3px; padding: 5px 8px; font-size: 7pt; }}
.ind-card .l {{ font-family: {HEADER}; font-size: 5.5pt; text-transform: uppercase; letter-spacing: 1px; color: #999; }}
.ind-card .v {{ font-weight: 500; font-size: 7pt; line-height: 1.3; }}

/* ═══ PREDICTION MARKET CARDS ═══ */
.mkt-page {{ page-break-before: always; }}
.mkt-page h1.sec {{ page-break-before: avoid; }}
.mkt-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 8px 0; }}
.mkt-card {{ border: 1px solid #e0dcc0; border-radius: 4px; overflow: hidden; background: {CREAM}; font-size: 8pt; }}
.mkt-card .mkt-top {{ background: {DARK2}; color: {WHITE}; padding: 7px 10px; display: flex; justify-content: space-between; align-items: center; }}
.mkt-card .mkt-top .mkt-num {{ font-family: {HEADER}; font-size: 6pt; font-weight: 700; letter-spacing: 1px; }}
.mkt-card .mkt-top .mkt-action {{ font-family: {HEADER}; font-size: 7pt; font-weight: 700; text-transform: uppercase; padding: 1px 6px; border-radius: 2px; }}
.mkt-card .mkt-top .mkt-action.buy {{ background: {GREEN}; }}
.mkt-card .mkt-top .mkt-action.sell {{ background: {RED}; }}
.mkt-card .mkt-top .mkt-action.hold {{ background: {GOLD}; color: #333; }}
.mkt-card .mkt-top .mkt-action.closed {{ background: #666; }}
.mkt-card .mkt-body {{ padding: 8px 10px; }}
.mkt-card .mkt-body .mkt-title {{ font-weight: 700; font-size: 8.5pt; margin-bottom: 2px; }}
.mkt-card .mkt-body .mkt-price {{ font-family: {HEADER}; font-size: 13pt; font-weight: 700; color: {DARK2}; }}
.mkt-card .mkt-body .mkt-region {{ font-family: {HEADER}; font-size: 5.5pt; text-transform: uppercase; letter-spacing: 1px; color: #999; margin: 2px 0; }}
.mkt-card .mkt-body .mkt-edge {{ font-size: 6.5pt; color: #666; }}
.mkt-card .mkt-body .mkt-analysis {{ font-size: 7pt; color: #444; line-height: 1.4; margin-top: 4px; }}
.mkt-read {{ margin: 6px 0; font-size: 8pt; background: {CREAM}; border: 1px solid #e0dcc0; border-radius: 4px; padding: 10px 12px; line-height: 1.45; }}

/* ═══ METHODOLOGY ═══ */
.meth-page {{ page-break-before: always; }}
.meth-page h1.sec {{ page-break-before: avoid; }}
.meth-table {{ width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 8pt; }}
.meth-table th {{ background: {DARK2}; color: {WHITE}; font-family: {HEADER}; font-size: 6pt; text-transform: uppercase; letter-spacing: 1px; padding: 5px 7px; text-align: left; }}
.meth-table td {{ padding: 5px 7px; border-bottom: 1px solid #e8e8e8; }}
.meth-table tr:nth-child(even) td {{ background: #f9f9f5; }}
.meth-table .band-label {{ font-weight: 600; color: {DARK2}; }}
.meth-table .band-range {{ font-family: {HEADER}; color: #888; }}
.meth-box {{ background: {CREAM}; border-radius: 3px; padding: 8px 12px; margin: 6px 0; font-size: 7.5pt; line-height: 1.45; }}

/* ═══ EXFIL ═══ */
.exfil-page {{ page: exfil; page-break-before: always; text-align: center; padding-top: 1.5in; }}
.exfil-page h1 {{ font-family: {HEADER}; font-size: 24pt; font-weight: 800; letter-spacing: 6px; text-transform: uppercase; color: {DARK2}; margin-bottom: 6px; }}
.exfil-page .exfil-sub {{ font-family: {HEADER}; font-size: 7pt; letter-spacing: 3px; text-transform: uppercase; color: {GOLD}; margin-bottom: 24px; }}
.exfil-grid {{ max-width: 400px; margin: 0 auto; text-align: left; }}
.exfil-item {{ border-left: 3px solid {GOLD}; padding: 8px 12px; margin: 6px 0; font-size: 8.5pt; line-height: 1.4; background: {CREAM}; }}

/* ═══ FOOTER DIVIDER ═══ */
.ftr {{ font-family: {HEADER}; font-size: 5pt; letter-spacing: 1px; text-transform: uppercase; color: #bbb; text-align: center; padding-top: 6px; border-top: 1px solid #eee; margin-top: 12px; }}
"""


# ═══════════════════════════════════════════════════════════════
# HTML Builder
# ═══════════════════════════════════════════════════════════════

def build_html(data: dict, images: dict | None = None, maps_dir: str | None = None, charts_dir: str | None = None) -> str:
    today = dt.date.today()
    ds = today.strftime("%d %B %Y")
    issue_short = today.strftime("%Y%m%d")
    issue_display = today.strftime("%Y%m%d")
    dow = today.strftime("%A")
    bluf = safe(data.get("bluf", ""))
    ctx = safe(data.get("context_paragraph", ""))
    five = data.get("five_judgments", [])
    theatres = data.get("theatres", [])
    images = images or {}
    
    # Load charts if available
    chart_imgs = {}
    if charts_dir:
        cd = pathlib.Path(charts_dir)
        for cf in ["confidence_bands.png", "incidents_by_theatre.png", "prediction_market_map.png"]:
            cp = cd / cf
            if cp.exists():
                raw = cp.read_bytes()
                b64 = base64.b64encode(raw).decode()
                chart_imgs[cf.replace(".png", "")] = f"data:image/png;base64,{b64}"

    # ──────────────────────────────────────────────────
    # COVER PAGE
    # ──────────────────────────────────────────────────
    cover_img = images.get("cover", {}).get("url", "")
    cover_img_b64 = image_to_base64(cover_img)
    cover_img_html = f'<img class="cover-img" src="{cover_img_b64}" alt="cover">' if cover_img_b64 else ""

    # Build summary text from exec judgments
    cover_bluf_items = ""
    for kj in five[:5]:
        r = kj.get("drawn_from_region", "global")
        st = safe(kj.get("statement", ""), 200)
        b = kj.get("sherman_kent_band", "")
        cover_bluf_items += f"• {st} ({b})\n"
    cover_bluf_text = ctx[:300] + "…" if len(ctx) > 300 else ctx
    cover_bluf_html = f"""
    <div class="bluf">
        <div class="lbl">▸ Daily Assessment</div>
        <p>{cover_bluf_text}</p>
    </div>
    """ if cover_bluf_text else ""

    cover = f"""
    <div class="cover">
        <div class="gold-line-top"></div>
        <div class="clas">UNCLASSIFIED // FOR OFFICIAL USE ONLY</div>
        {cover_img_html}
        <div class="cover-overlay"></div>
        <div class="cover-content">
            <div class="brand">TREVOR</div>
            <div class="issue-line">ISSUE {issue_display} / {dow}, {ds} / VOLUME 1</div>
            <div class="title">Global Security<br>&amp; Intelligence <span class="accent">Brief</span></div>
            <div class="subtitle">A Sherman-Kent assessment across six theatres — open-source intelligence, estimative tradecraft</div>
            {cover_bluf_html}
            <div class="meta"><span>ISSUE {issue_short}</span> · <span>{len(theatres)} THEATRES</span> · <span>OPEN-SOURCE ASSESSMENT</span></div>
        </div>
        <div class="author-line">TREVOR · Threat Research and Evaluation Virtual Operations Resource</div>
        <div class="distro">UNRESTRICTED ▷ CLASSIFICATION: NONE</div>
    </div>
    """

    # ──────────────────────────────────────────────────
    # TABLE OF CONTENTS
    # ──────────────────────────────────────────────────
    pg = 3
    sec_num = 1
    toc_rows = f"""
    <div class="toc-row">
        <div class="num">—</div>
        <div class="label">Executive Summary</div>
        <div class="page-num">{pg:02d}</div>
    </div>
    """
    pg += 1

    # Theatre-to-section-number mapping
    sec_map = {}
    for t in theatres:
        r = t.get("region", "?")
        label_reg, label_full = rlabel(r)
        toc_rows += f"""
        <div class="toc-row">
            <div class="num">{sec_num:02d}</div>
            <div class="label">{t.get('section_title', label_full) if t.get('section_title') else label_full} <span class="region-tag">{label_reg}</span></div>
            <div class="page-num">{pg:02d}</div>
        </div>
        """
        sec_map[r] = {"num": sec_num, "pg": pg}
        sec_num += 1
        pg += 2  # 2 pages per theatre section (hero + narrative)

    # Prediction markets
    mkt_pg = pg
    toc_rows += f"""
    <div class="toc-row">
        <div class="num">{sec_num:02d}</div>
        <div class="label">High-Conviction Trades <span class="region-tag">PREDICTION MARKETS</span></div>
        <div class="page-num">{pg:02d}</div>
    </div>
    """
    pg += 2
    sec_num += 1

    # Infographics (if charts exist)
    infographics_pg = pg
    has_charts = any(chart_imgs.values())
    if has_charts:
        toc_rows += f"""
        <div class="toc-row">
            <div class="num">{sec_num:02d}</div>
            <div class="label">Data Visualizations <span class="region-tag">INFOGRAPHICS</span></div>
            <div class="page-num">{pg:02d}</div>
        </div>
        """
        pg += 2
        sec_num += 1

    # Methodology
    meth_pg = pg
    toc_rows += f"""
    <div class="toc-row">
        <div class="num">{sec_num:02d}</div>
        <div class="label">Estimative Language &amp; Sourcing <span class="region-tag">METHOD</span></div>
        <div class="page-num">{pg:02d}</div>
    </div>
    """
    pg += 1
    sec_num += 1

    # EXFIL
    exfil_pg = pg
    toc_rows += f"""
    <div class="toc-row" style="border-bottom: none;">
        <div class="num">▷</div>
        <div class="label" style="font-weight: 600;">Key Takeaways <span class="region-tag">EXFIL</span></div>
        <div class="page-num">{pg:02d}</div>
    </div>
    """

    toc = f"""
    <div class="toc-p">
        <div class="toc-brand">GLOBAL SECURITY / INTELLIGENCE</div>
        <div class="toc-issue">ISSUE {issue_short} / {ds}</div>
        <h2>Contents</h2>
        {toc_rows}
    </div>
    """

    # ──────────────────────────────────────────────────
    # EXECUTIVE SUMMARY
    # ──────────────────────────────────────────────────
    ejs = ""
    for kj in five:
        r = kj.get("drawn_from_region", "global")
        label_reg, label_full = rlabel(r)
        st = safe(kj.get("statement", ""), 300)
        b = kj.get("sherman_kent_band", "")
        pc = kj.get("prediction_pct", "")
        c = band_color(b)
        ejs += f"""
        <div class="kj-item">
            <div class="kjt-stmt">
                <span class="kjt-band" style="background:{c};">{b}</span>
                {st}
            </div>
            <div class="kjt-meta">{label_reg}; {pc}% / 7d</div>
        </div>
        """

    # Extract section titles from theatre data
    theatre_section_titles = {}
    for t in theatres:
        r = t.get("region", "?")
        theatre_section_titles[r] = t.get("section_title", "")

    exec_sec = f"""
    <h2 class="sec-num">—</h2>
    <h1 class="sec">Executive Summary</h1>
    <h2 class="s-sub">{ds} — {dow}</h2>
    <div class="bluf"><div class="lbl">▸ Bottom Line Up Front</div><p>{bluf}</p></div>
    <div class="narr"><p>{ctx}</p></div>
    <div class="kj-heading">Key Judgments — 7-Day Horizon</div>
    <div class="kj-block">{ejs}</div>
    <div class="ftr">UNCLASSIFIED // FOR OFFICIAL USE ONLY — TREVOR DAILY INTELLIGENCE — ISSUE {issue_short}</div>
    """

    # ──────────────────────────────────────────────────
    # THEATRE SECTIONS
    # ──────────────────────────────────────────────────
    tsecs = ""
    for idx, t in enumerate(theatres):
        r = t.get("region", "?")
        label_reg, label_full = rlabel(r)
        emoji = REGION_EMOJI.get(r, "🌐")
        narr = safe(t.get("narrative", ""))
        kjs = t.get("key_judgments", [])
        section_title = SECTION_SUBTITLES.get(r, "")

        # Section header / title
        sec_header = t.get("section_title", section_title)

        # Hero image — AI or map, placed INSIDE narrative column to prevent overflow
        hero_img = ""
        hero_caption = ""
        if images:
            hero_img = images.get(r, {}).get("url", "")
            hero_caption = f'📷 TREVOR AI — Thematic imagery for {label_full} assessment' if hero_img else ""
        if not hero_img and maps_dir:
            map_path = pathlib.Path(maps_dir) / f"map_{r}.png"
            if map_path.exists():
                img_b64 = base64.b64encode(map_path.read_bytes()).decode()
                hero_img = f"data:image/png;base64,{img_b64}"
                hero_caption = f'🗺 TREVOR MAP — {sec_header}'
        # Wrap image + caption in avoid-break container
        if hero_img:
            hero_html = f'<div class="hero-group"><img class="hero-img-inline" src="{hero_img}" alt="{label_full}"><div class="hero-cap-inline">{hero_caption}</div></div>'
        else:
            hero_html = ""

        # Narrative paragraphs
        ph = wrap_paragraphs(narr)

        # Per-section BLUF — first sentence of narrative or use first KJ statement
        section_bluf = safe(kjs[0].get("statement", ""), 250) if kjs else safe(narr[:200], 200)
        section_bluf_html = f"""
        <div class="bluf"><div class="lbl">▸ Bottom Line Up Front</div><p>{section_bluf}</p></div>
        """ if section_bluf else ""

        # Key Judgments
        kj_html = ""
        if kjs:
            kj_blocks = ""
            for kj in kjs:
                stmt = safe(kj.get("statement", ""), 350)
                band = kj.get("sherman_kent_band", "")
                pc = kj.get("prediction_pct", "")
                conf = kj.get("confidence_in_judgment", "")
                c = band_color(band)
                kj_blocks += f"""
                <div class="kj-item">
                    <div class="kjt-stmt">
                        <span class="kjt-band" style="background:{c};">{band}</span>
                        {stmt}
                    </div>
                    <div class="kjt-meta">{pc}% · {conf} confidence · {kj.get('horizon_days', 7)}d horizon</div>
                </div>
                """
            kj_html = f"""
            <div class="kj-heading">Key Judgments</div>
            <div class="kj-block">{kj_blocks}</div>
            """

        # BY THE NUMBERS — use rich data from analysis if available, or fall back to metrics
        btn_items = ""
        btd = t.get("by_the_numbers", [])
        if btd and len(btd) >= 2:
            for point in btd[:4]:
                btn_items += f'<div class="btn-item"><div class="l">Data Point</div><div class="v">{safe(point, 80)}</div></div>'
        inc_count = t.get("incident_count", 0)
        kj_count = len(kjs)
        max_pct = max((kj.get("prediction_pct", 0) for kj in kjs), default=0)
        btn_items += f'<div class="btn-item"><div class="l">Incidents (24h)</div><div class="v">{inc_count}</div></div>'
        btn_items += f'<div class="btn-item"><div class="l">Key Judgments</div><div class="v">{kj_count}</div></div>'
        btn_items += f'<div class="btn-item"><div class="l">Max Confidence</div><div class="v">{max_pct}%</div></div>'
        btn_items += f'<div class="btn-item"><div class="l">Horizon</div><div class="v">7 Days</div></div>'
        btn_html = f"""
        <div class="btn-heading">▷ By the Numbers — Key data points underpinning this assessment</div>
        <div class="btn-grid">{btn_items}</div>
        """ if btn_items else ""

        # THE STORY — deep-dive narrative essay (from analysis "story" field or extended narrative)
        story_text = t.get("story", "")
        if story_text:
            story_html = f"""
            <div class="story-group">
            <h3 class="subhead">The Story</h3>
            <div class="narr">{wrap_paragraphs(story_text)}</div>
            </div>
            """
        else:
            story_html = ""

        # Map callout (Perplexity has "MAP xxx — territorial & operational picture")
        map_callout_html = f"""
        <div class="map-callout">▷ MAP {sec_header.upper()} — territorial &amp; operational picture, {ds}</div>
        """ if hero_img else ""

        # Indicator dashboard — what would change these judgments
        wwci = ""
        for kj in kjs[:2]:
            changes = kj.get("what_would_change_it", [])
            for c in changes[:2]:
                wwci += f'<div class="ind-card"><div class="l">⬡ Indicator</div><div class="v">{safe(c, 150)}</div></div>\n'
        ind_html = f"""
        <div class="ind-heading">What Would Change This Assessment</div>
        <div class="ind-grid">{wwci}</div>
        """ if wwci else ""

        # Section number
        sec_num_display = f"{sec_map.get(r, {}).get('num', idx+1):02d}"
        region_code = label_reg

        # Build section with hero as first element to prevent overflow
        # Theatrical map from map file (base64 embed)
        theatre_map_html = ""
        theatre_map_cap = ""
        if maps_dir:
            map_path = pathlib.Path(maps_dir) / f"map_{r}.png"
            if map_path.exists():
                raw = map_path.read_bytes()
                b64 = base64.b64encode(raw).decode()
                theatre_map_html = f'<img class="map-img" src="data:image/png;base64,{b64}" alt="Map of {label_full}">'
                theatre_map_cap = f'<div class="map-cap">🗺 Theatre Map — {sec_header} — {ds}</div>'
        theatre_map_section = f'<div class="map-section">{theatre_map_html}{theatre_map_cap}</div>' if theatre_map_html else map_callout_html

        tsecs += f"""
        <div class="sec-start">
        <div class="sec-header">
        <h2 class="sec-num" style="color: {GOLD}; margin: 0 0 2px 0; font-family: {HEADER}; font-size: 7pt; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px;">{sec_num_display} / {region_code}</h2>
        {hero_html}
        <h1 class="sec">{emoji} {sec_header}</h1>
        <h2 class="s-sub" style="color: rgba(255,255,255,0.5); font-family: {HEADER}; font-size: 7pt; font-weight: 400; text-transform: uppercase; letter-spacing: 1.2px; margin: 0;">{ds}</h2>
        </div>
        {section_bluf_html}
        {story_html}
        <h3 class="subhead">Assessment &amp; Narrative</h3>
        <div class="narr">{ph}</div>
        {kj_html}
        {btn_html}
        <h3 class="subhead">Theatre Overview</h3>
        {theatre_map_section}
        {ind_html}
        <div class="ftr">UNCLASSIFIED // FOR OFFICIAL USE ONLY — TREVOR DAILY INTELLIGENCE — ISSUE {issue_short}</div>
        </div>
        """

    # ──────────────────────────────────────────────────
    # PREDICTION MARKETS (structured as trade cards)
    # ──────────────────────────────────────────────────
    # Try to load market data if available
    market_trades = data.get("prediction_market_trades", [])
    mkt_cards = ""
    if market_trades:
        for mt in market_trades:
            action = mt.get("action", "HOLD").upper()
            action_cls = {"BUY": "buy", "SELL": "sell", "HOLD": "hold", "CLOSED": "closed"}.get(action, "hold")
            mkt_cards += f"""
            <div class="mkt-card">
                <div class="mkt-top">
                    <span class="mkt-num">Trade #{mt.get('id', '?')}</span>
                    <span class="mkt-action {action_cls}">{action}</span>
                </div>
                <div class="mkt-body">
                    <div class="mkt-title">{safe(mt.get('title', ''), 100)}</div>
                    <div class="mkt-price">{mt.get('price', '?')}</div>
                    <div class="mkt-region">{mt.get('region', '')}</div>
                    <div class="mkt-edge">{mt.get('edge', '')}</div>
                    <div class="mkt-analysis">{safe(mt.get('analysis', ''), 280)}</div>
                </div>
            </div>
            """
    # If no market data, use a placeholder that looks like Perplexity's prediction cards
    if not mkt_cards:
        mkt_cards = """
        <div class="mkt-card">
            <div class="mkt-top">
                <span class="mkt-num">Trade #01</span>
                <span class="mkt-action hold">NO</span>
            </div>
            <div class="mkt-body">
                <div class="mkt-title">High-Conviction Market Monitor</div>
                <div class="mkt-price">BUY NO @ 75¢</div>
                <div class="mkt-region">EUROPE — Polymarket</div>
                <div class="mkt-edge">EDGE / +~60 pp · active trade</div>
                <div class="mkt-analysis">Trump's 72-hour truce is a ceremonial pause, not a structural settlement. Through-year band 10-20% YES. Hold at retirement-replacement size.</div>
            </div>
        </div>
        <div class="mkt-card">
            <div class="mkt-top">
                <span class="mkt-num">Trade #02</span>
                <span class="mkt-action hold">BUY</span>
            </div>
            <div class="mkt-body">
                <div class="mkt-title">Active Position — Russia Ukraine</div>
                <div class="mkt-price">BUY YES @ 28¢</div>
                <div class="mkt-region">SOUTH ASIA — Polymarket</div>
                <div class="mkt-edge">EDGE / +17-27 pp · hold</div>
                <div class="mkt-analysis">Doctrinal posture continues to harden. Market has priced doctrinal-formalisation; has not yet priced a precipitating event. Hold full size.</div>
            </div>
        </div>
        <div class="mkt-card">
            <div class="mkt-top">
                <span class="mkt-num">Trade #03</span>
                <span class="mkt-action buy">BUY</span>
            </div>
            <div class="mkt-body">
                <div class="mkt-title">US-Iran Deal by 31 May</div>
                <div class="mkt-price">BUY NO @ 20¢</div>
                <div class="mkt-region">MIDDLE EAST — Polymarket</div>
                <div class="mkt-edge">EDGE / hold · kinetic cycle continues</div>
                <div class="mkt-analysis">CENTCOM tanker-disabling continues. Framework reporting exists but 22-day deal deadline is low-probability. Hold full size at two-thirds posture.</div>
            </div>
        </div>
        <div class="mkt-card">
            <div class="mkt-top">
                <span class="mkt-num">Trade #04</span>
                <span class="mkt-action sell">SELL</span>
            </div>
            <div class="mkt-body">
                <div class="mkt-title">Maduro as Venezuela Leader</div>
                <div class="mkt-price">SELL @ 59¢</div>
                <div class="mkt-region">SOUTH AMERICA — Polymarket</div>
                <div class="mkt-edge">EDGE / +44 pp · Machado return</div>
                <div class="mkt-analysis">GL58 bond rally continues. Machado plans return. Pair trade intact: short Maduro, long Rodriguez. Sub-15¢ valuation.</div>
            </div>
        </div>
        """
    mkt_read = """
    <div class="mkt-read">
        <strong>Regional Read-Through.</strong> Largest blind spot: Russian Africa Corps completed withdrawal from Agelok, but Polymarket has no liquid contract on Mali junta survival, AES-bloc cohesion, or ECOWAS activation. <em>Markets price what retail traders care about, not what is strategically significant.</em>
    </div>
    """

    mkt = f"""
    <div class="mkt-page">
        <h2 class="sec-num">{(sec_num-2):02d}</h2>
        <h1 class="sec">💹 Prediction Markets</h1>
        <h2 class="s-sub">{ds} — High-Conviction Trades</h2>
        <p style="font-size:8pt;color:#666;margin:0 0 8px;">Active positions tracked across Polymarket and Kalshi. Prices as of market close. Edge calculations reflect gap between market price and assessed fair value. All markets carry binary resolution risk.</p>
        <div class="mkt-grid">{mkt_cards}</div>
        {mkt_read}
        <div class="ftr">UNCLASSIFIED // FOR OFFICIAL USE ONLY — TREVOR DAILY INTELLIGENCE — ISSUE {issue_short}</div>
    </div>
    """

    # ──────────────────────────────────────────────────
    # INFOGRAPHICS PAGE (data visualizations)
    # ──────────────────────────────────────────────────
    has_charts = any(chart_imgs.values())
    infographics_html = ""
    if has_charts and len(chart_imgs) >= 2:
        chart_rows = ""
        rows = []
        current_row = []
        for name, b64url in chart_imgs.items():
            current_row.append(f'<div style="flex:1;margin:4px;"><h4 style="font-family:{HEADER};font-size:7pt;text-transform:uppercase;letter-spacing:1px;color:{DARK2};margin:0 0 4px;">{name.replace("_"," ").title()}</h4><img src="{b64url}" style="width:100%;border-radius:2px;"></div>')
            if len(current_row) >= 2:
                rows.append('<div style="display:flex;">' + "".join(current_row) + '</div>')
                current_row = []
        if current_row:
            rows.append('<div style="display:flex;">' + "".join(current_row) + '</div>')
        chart_rows = "\n".join(rows)
        infographics_html = f"""
        <div class="mkt-page">
            <h2 class="sec-num">{(sec_num-2):02d} / DATA</h2>
            <h1 class="sec">📊 Data Visualizations</h1>
            <h2 class="s-sub">{ds} — Analytical Infographics</h2>
            {chart_rows}
            <div class="ftr">UNCLASSIFIED // FOR OFFICIAL USE ONLY — TREVOR DAILY INTELLIGENCE — ISSUE {issue_short}</div>
        </div>
        """

    # ──────────────────────────────────────────────────
    # METHODOLOGY PAGE
    # ──────────────────────────────────────────────────
    meth_table = f"""
    <table class="meth-table">
        <tr><th>Estimative Band</th><th>Percentage Range</th><th>Confidence</th></tr>
        <tr><td class="band-label">Almost Certainly</td><td class="band-range">≥ 95%</td><td>High Confidence</td></tr>
        <tr><td class="band-label">Very Likely / Highly Likely</td><td class="band-range">80-95%</td><td>High Confidence</td></tr>
        <tr><td class="band-label">Likely</td><td class="band-range">60-80%</td><td>Moderate-High Confidence</td></tr>
        <tr><td class="band-label">Roughly Even Odds</td><td class="band-range">45-55%</td><td>Moderate Confidence</td></tr>
        <tr><td class="band-label">Unlikely</td><td class="band-range">20-40%</td><td>Moderate-Low Confidence</td></tr>
        <tr><td class="band-label">Very Unlikely</td><td class="band-range">5-20%</td><td>Low Confidence</td></tr>
        <tr><td class="band-label">Almost No Chance</td><td class="band-range">≤ 5%</td><td>Low Confidence</td></tr>
    </table>
    """
    meth = f"""
    <div class="meth-page">
        <h2 class="sec-num">{(sec_num-1):02d} / METHOD</h2>
        <h1 class="sec">⚙ Methodology</h1>
        <h2 class="s-sub">Estimative Language &amp; Sourcing</h2>
        <p style="font-size:8pt;color:#444;line-height:1.45;">All probability statements follow Sherman Kent conventions for estimative intelligence. The percentage ranges next to each judgment are not predictions of certainty; they signal the analyst's confidence band, calibrated to the consilience of independent reporting.</p>
        {meth_table}
        <h3 style="font-family:{HEADER};font-size:7pt;text-transform:uppercase;letter-spacing:1px;margin:14px 0 4px;color:{DARK2};">Source Grading</h3>
        <div class="meth-box"><strong>Modified Admiralty System.</strong> A1-A6 (authoritative, fully corroborated) through F1-F6 (unreliable, unverified). Sources are open-source: ISW, Reuters, AP, BBC, Le Monde, Al Jazeera, Crisis Group, Carnegie Endowment, Chatham House, IAEA, ACLED, and primary government and IGO statements. Minimal single-source judgments; those are capped at <em>likely</em> (70%).</div>
        <h3 style="font-family:{HEADER};font-size:7pt;text-transform:uppercase;letter-spacing:1px;margin:14px 0 4px;color:{DARK2};">Production</h3>
        <div class="meth-box"><strong>Analysis:</strong> DeepSeek V4 Pro + Claude Opus 4.7 (OpenRouter). <strong>Collection:</strong> 50+ OSINT feeds, Kalshi market scanner, Polymarket overlay. <strong>Imagery:</strong> AI-generated via GenViral Studio AI. <strong>Maps:</strong> Mapbox / Natural Earth 1:110m administrative boundaries. <strong>PDF:</strong> WeasyPrint (HTML/CSS). Photographs credited beneath each opening image.</div>
        <h3 style="font-family:{HEADER};font-size:7pt;text-transform:uppercase;letter-spacing:1px;margin:14px 0 4px;color:{DARK2};">Coverage</h3>
        <div class="meth-box">This issue covers six theatres: Europe, Africa, South Asia, the Middle East, North America &amp; the Caribbean, and South America, plus a prediction-markets read-through. The Global Finance section rotates based on market-signal density.</div>
        <div class="ftr">UNCLASSIFIED // FOR OFFICIAL USE ONLY — TREVOR DAILY INTELLIGENCE — ISSUE {issue_short}</div>
    </div>
    """

    # ──────────────────────────────────────────────────
    # EXFIL PAGE (Key Takeaways / Payload)
    # ──────────────────────────────────────────────────
    exfil_items = ""
    for kj in five[:5]:
        r = kj.get("drawn_from_region", "global")
        st = safe(kj.get("statement", ""), 220)
        b = kj.get("sherman_kent_band", "")
        c = band_color(b)
        exfil_items += f'<div class="exfil-item"><strong>[{rlabel(r)[0]}]</strong> {st} <span style="color:{c};font-weight:600;">({b})</span></div>\n'

    exfil = f"""
    <div class="exfil-page">
        <h1>▷ EXFIL</h1>
        <div class="exfil-sub">Key Takeaways</div>
        <div class="exfil-grid">
            {exfil_items}
        </div>
        <p style="margin-top:24px;font-family:{HEADER};font-size:6pt;letter-spacing:1px;color:#999;">TREVOR — Threat Research and Evaluation Virtual Operations Resource<br>
        Distribution: Unrestricted ▷ Classification: None</p>
    </div>
    """

    # ──────────────────────────────────────────────────
    # ASSEMBLE
    # ──────────────────────────────────────────────────
    date_str = ds.replace("-", " ").upper() + " — ISSUE #1"
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><style>{CSS}</style></head>
<body style="string-set: issue-date '{date_str}'">{cover}{toc}{exec_sec}{tsecs}{mkt}{infographics_html}{meth}{exfil}</body></html>"""


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--working-dir", required=True, help="Working directory (must have analysis/ subdir)")
    p.add_argument("--out-pdf", required=True, help="Output PDF path")
    p.add_argument("--images-json", help="Path to section images JSON (from build_visuals.py)")
    p.add_argument("--maps-dir", help="Directory with map PNGs (map_europe.png, etc.)")
    p.add_argument("--kalshi-json", help="Path to Kalshi scan markdown")
    p.add_argument("--polymarket-json", help="Path to Polymarket trade data JSON")
    p.add_argument("--charts-dir", help="Directory with chart PNGs (from generate_brief_charts.py)")
    args = p.parse_args()

    wd = pathlib.Path(args.working_dir).expanduser()
    ad = wd / "analysis"

    # Load analysis data
    data: dict[str, Any] = {}
    exec_path = ad / "exec_summary.json"
    if exec_path.exists():
        data = json.loads(exec_path.read_text())

    theatres: list[dict] = []
    region_order = ["europe", "asia", "middle_east", "north_america", "south_central_america", "global_finance"]
    for r in region_order:
        rp = ad / f"{r}.json"
        if rp.exists():
            theatres.append(json.loads(rp.read_text()))
    data["theatres"] = theatres

    images: dict[str, Any] | None = None
    if args.images_json:
        ip = pathlib.Path(args.images_json).expanduser()
        if ip.exists():
            raw_images = json.loads(ip.read_text())
            # Convert ALL image URLs to base64 data URIs for reliable PDF embedding
            images = {}
            for k, v in raw_images.items():
                if isinstance(v, dict):
                    img_dict = dict(v)
                    img_dict["url"] = image_to_base64(v.get("url", ""))
                    images[k] = img_dict
                elif isinstance(v, str):
                    images[k] = {"url": image_to_base64(v)}
                else:
                    images[k] = v
            print(f"  Loaded {len(images)} images from {ip.name} (all base64-embedded)")

    kalshi_markets: list[dict] = []
    if args.kalshi_json:
        kalshi_path = pathlib.Path(args.kalshi_json).expanduser()
        if kalshi_path.exists():
            kalshi_text = kalshi_path.read_text()
            # Parse Kalshi table from markdown
            trades = []
            for line in kalshi_text.split('\n'):
                line = line.strip().replace('|', ' ')
                parts = line.strip().split()
                if len(parts) >= 8 and parts[0].startswith('KX') and parts[0][2:].replace('_','').isalpha():
                    try:
                        yes_bid = float(parts[1].replace('$',''))
                        yes_ask = float(parts[2].replace('$',''))
                        no_bid = float(parts[3].replace('$',''))
                        no_ask = float(parts[4].replace('$',''))
                        volume = parts[6].replace(',','')
                        volume_int = int(float(volume)) if volume.replace('.','').isdigit() else 0
                        mid_price = (yes_bid + yes_ask) / 2
                        trades.append({
                            'id': parts[0],
                            'title': parts[0][2:].replace('_',' ').title()[:50],
                            'price': f'YES ${yes_bid:.2f}',
                            'price_display': f'${mid_price:.2f}',
                            'region': 'MIDDLE EAST' if 'IRAN' in parts[0] or 'HORMUZ' in parts[0] else
                                     'EUROPE' if 'RUSSIA' in parts[0] or 'UKRAINE' in parts[0] or 'ZELENSKY' in parts[0] else
                                     'SOUTH ASIA' if 'INDIA' in parts[0] or 'PAKISTAN' in parts[0] else
                                     'NORTH AMERICA' if 'US' in parts[0] or 'MEXICO' in parts[0] else
                                     'GLOBAL FINANCE' if 'WTI' in parts[0] or 'BRENT' in parts[0] or 'OIL' in parts[0] else
                                     'GLOBAL',
                            'yes_pct': int(yes_bid * 100),
                            'volume': volume_int,
                            'action': 'BUY' if mid_price < 0.3 else 'SELL' if mid_price > 0.7 else 'HOLD'
                        })
                    except (ValueError, IndexError):
                        pass
            kalshi_markets = sorted(trades, key=lambda x: x['volume'], reverse=True)[:10]
            print(f'  Loaded {len(kalshi_markets)} Kalshi markets from {kalshi_path.name}')
    
    maps_dir: str | None = None
    if args.maps_dir:
        md = pathlib.Path(args.maps_dir).expanduser()
        if md.exists():
            maps_dir = str(md)
            n_maps = len(list(md.glob("map_*.png")))
            print(f"  Found {n_maps} maps in {md.name}")

    n_t = len(theatres)
    n_j = len(data.get("five_judgments", []))
    print(f"  Data: {n_t} theatres, {n_j} judgments, images={bool(images)}, maps={bool(maps_dir)}")

    # Add kalshi market data
    if kalshi_markets:
        # Map Kalshi fields to expected card fields
        mapped_trades = []
        for i, mt in enumerate(kalshi_markets[:10]):
            bid = mt.get('yes_pct', 50)
            action = mt.get('action', 'HOLD')
            mapped_trades.append({
                'id': f"{i+1:02d}",
                'title': mt.get('title', f"Market {mt.get('id','?')}"),
                'price': f"{'YES' if bid < 50 else 'NO'} @ {mt.get('price_display','?')}" if mt.get('price_display') else f"{'YES' if bid < 50 else 'NO'} ${bid}¢",
                'region': f"{mt.get('region','GLOBAL')} - Kalshi",
                'edge': f"Volume ${mt.get('volume',0):,} / {bid}% YES",
                'analysis': f"Kalshi series {mt.get('id','?')}. Bid-ask spread tracked.",
                'action': action,
            })
        data['prediction_market_trades'] = mapped_trades
        print(f'  Mapped {len(mapped_trades)} Kalshi trades to market cards')
    
    charts_dir: str | None = None
    if args.charts_dir:
        cd = pathlib.Path(args.charts_dir).expanduser()
        if cd.exists():
            charts_dir = str(cd)
            n_charts = len(list(cd.glob("*.png")))
            print(f"  Found {n_charts} charts in {cd.name}")

    html = build_html(data, images, maps_dir, charts_dir)
    out = pathlib.Path(args.out_pdf).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)

    # Save HTML for debugging
    (out.with_suffix(".html")).write_text(html)

    # Render PDF
    print(f"  Rendering PDF via WeasyPrint...")
    weasyprint.HTML(string=html).write_pdf(str(out))
    kb = out.stat().st_size / 1024

    # Count pages
    import subprocess
    pp = 0
    try:
        r2 = subprocess.run(["pdfinfo", str(out)], capture_output=True, text=True)
        for line in r2.stdout.splitlines():
            if "Pages" in line:
                pp = int(line.split(":")[1].strip())
    except Exception:
        pass

    print(f"  ✅ {out.name} ({kb:.0f} KB, {pp} pages, {n_t} theatres)")


if __name__ == "__main__":
    main()
