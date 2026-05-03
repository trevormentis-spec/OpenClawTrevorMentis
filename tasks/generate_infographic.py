#!/usr/bin/env python3
"""
generate_infographic.py — Professional SVG infographic generator for Trevor Intelligence Briefing.

Produces RAND/Stratfor-quality strategic infographics with:
  - Dark navy theme (#0f1923 / #161b2d)
  - 3-stage causal progression (connected boxes with arrows)
  - Tripwire/risk diamond element
  - 4 strategic implication cards
  - Professional typography, drop shadows, color accents
"""

import argparse
import json
import sys
import textwrap
import os

# ──────────────────────────────────────────
# COLOR PALETTE
# ──────────────────────────────────────────
NAVY_BG       = "#0f1923"
NAVY_CARD     = "#161b2d"
DARK_CARD     = "#1b2539"
BORDER_SUBTLE = "#1e2d42"
BORDER_STAGE  = "#2a4a6b"
BLUE_PRIMARY  = "#2b7be4"
BLUE_LIGHT    = "#4d9aff"
CYAN_ACCENT   = "#00bcd4"
TEAL_ACCENT   = "#26c6da"
GOLD_ACCENT   = "#f5c842"
AMBER_ACCENT  = "#ff9800"
RED_ACCENT    = "#e53935"
RED_DARK      = "#b71c1c"
ORANGE_ACCENT = "#ff6d00"
WHITE_TEXT    = "#f0f2f8"
LIGHT_TEXT    = "#b0b8cf"
MUTED_TEXT    = "#6b7a94"

# ──────────────────────────────────────────
# SVG TEMPLATE PARTS
# ──────────────────────────────────────────

HEADER = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{title}">
  <defs>
    <style>
      .h-title  {{ font: 700 24px/1.2 "Inter","Segoe UI",Arial,Helvetica,sans-serif; fill: {WHITE_TEXT}; }}
      .h-sub    {{ font: 500 13px/1.3 "Inter","Segoe UI",Arial,Helvetica,sans-serif; fill: {LIGHT_TEXT}; }}
      .h-label  {{ font: 700 14px/1.2 "Inter","Segoe UI",Arial,Helvetica,sans-serif; fill: {WHITE_TEXT}; }}
      .h-meta   {{ font: 600 12px/1.2 "Inter","Segoe UI",Arial,Helvetica,sans-serif; fill: {LIGHT_TEXT}; }}
      .h-stage  {{ font: 700 16px/1.3 "Inter","Segoe UI",Arial,Helvetica,sans-serif; fill: {WHITE_TEXT}; }}
      .h-detail {{ font: 500 12px/1.4 "Inter","Segoe UI",Arial,Helvetica,sans-serif; fill: {LIGHT_TEXT}; }}
      .h-card-t {{ font: 700 14px/1.3 "Inter","Segoe UI",Arial,Helvetica,sans-serif; fill: {WHITE_TEXT}; }}
      .h-card-d {{ font: 500 12px/1.35 "Inter","Segoe UI",Arial,Helvetica,sans-serif; fill: {LIGHT_TEXT}; }}
      .h-trip   {{ font: 800 13px/1.2 "Inter","Segoe UI",Arial,Helvetica,sans-serif; fill: {WHITE_TEXT}; }}
      .h-trip-d {{ font: 600 11px/1.3 "Inter","Segoe UI",Arial,Helvetica,sans-serif; fill: {ORANGE_ACCENT}; }}
      .h-imp-i  {{ font: 500 14px/1.3 "Inter","Segoe UI",Arial,Helvetica,sans-serif; fill: {LIGHT_TEXT}; }}
      .h-imp-v  {{ font: 700 14px/1.3 "Inter","Segoe UI",Arial,Helvetica,sans-serif; fill: {WHITE_TEXT}; }}
    </style>

    <filter id="shadowCard" x="-15%" y="-15%" width="130%" height="130%">
      <feDropShadow dx="0" dy="3" stdDeviation="5" flood-color="#000" flood-opacity="0.35"/>
    </filter>
    <filter id="shadowStage" x="-15%" y="-15%" width="130%" height="130%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000" flood-opacity="0.40"/>
    </filter>
    <filter id="shadowTrip" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#e53935" flood-opacity="0.25"/>
    </filter>
    <filter id="glowShimmer" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="6" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>

    <linearGradient id="gradNavy" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{NAVY_BG}"/>
      <stop offset="1" stop-color="#0d1520"/>
    </linearGradient>

    <linearGradient id="gradStageBlue" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#1a3366"/>
      <stop offset="1" stop-color="#0f1923"/>
    </linearGradient>
    <linearGradient id="gradStageCyan" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#004d73"/>
      <stop offset="1" stop-color="#0f1923"/>
    </linearGradient>
    <linearGradient id="gradStageAmber" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#5c3d00"/>
      <stop offset="1" stop-color="#0f1923"/>
    </linearGradient>

    <linearGradient id="gradTripwire" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#e53935"/>
      <stop offset="1" stop-color="#b71c1c"/>
    </linearGradient>

    <linearGradient id="gradGoldLine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{GOLD_ACCENT}" stop-opacity="0"/>
      <stop offset="0.5" stop-color="{GOLD_ACCENT}" stop-opacity="0.6"/>
      <stop offset="1" stop-color="{GOLD_ACCENT}" stop-opacity="0"/>
    </linearGradient>

    <marker id="arrowBlue" markerWidth="14" markerHeight="10" refX="12" refY="5" orient="auto">
      <path d="M0,0 L14,5 L0,10 Z" fill="{BLUE_PRIMARY}"/>
    </marker>
    <marker id="arrowCyan" markerWidth="14" markerHeight="10" refX="12" refY="5" orient="auto">
      <path d="M0,0 L14,5 L0,10 Z" fill="{CYAN_ACCENT}"/>
    </marker>
    <marker id="arrowAmber" markerWidth="14" markerHeight="10" refX="12" refY="5" orient="auto">
      <path d="M0,0 L14,5 L0,10 Z" fill="{AMBER_ACCENT}"/>
    </marker>
    <marker id="arrowRed" markerWidth="14" markerHeight="10" refX="12" refY="5" orient="auto">
      <path d="M0,0 L14,5 L0,10 Z" fill="{RED_ACCENT}"/>
    </marker>
    <marker id="arrowGold" markerWidth="14" markerHeight="10" refX="12" refY="5" orient="auto">
      <path d="M0,0 L14,5 L0,10 Z" fill="{GOLD_ACCENT}"/>
    </marker>

    <clipPath id="cardClip">
      <rect x="0" y="0" width="210" height="130" rx="10"/>
    </clipPath>
  </defs>

  <!-- Background -->
  <rect x="0" y="0" width="{width}" height="{height}" fill="url(#gradNavy)"/>

  <!-- Subtle grid pattern -->
  <g opacity="0.03">
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#fff" stroke-width="0.5"/>
    </pattern>
    <rect x="0" y="0" width="{width}" height="{height}" fill="url(#grid)"/>
  </g>
'''

FOOTER = '''  <!-- Footer -->
  <g transform="translate(0, {footer_y})">
    <rect x="40" y="0" width="720" height="1" fill="url(#gradGoldLine)"/>
    <text x="40" y="20" class="h-meta" fill="{MUTED_TEXT}">TREVOR Intelligence Briefing — Generated {date}</text>
    <text x="760" y="20" class="h-meta" fill="{MUTED_TEXT}" text-anchor="end">trevormentis.moltbook.com</text>
  </g>
</svg>'''

# ──────────────────────────────────────────
# HELPER: wrap text into lines
# ──────────────────────────────────────────
def wrap(text, width=28):
    """Simple word wrap returning list of lines."""
    if not text:
        return [""]
    return textwrap.wrap(text, width=width) or [""]


# ──────────────────────────────────────────
# STAGE BOX
# ──────────────────────────────────────────
def stage_box(cx, y, label, detail_lines, color, marker_id, arrow_to_x=None, arrow_to_y=None):
    """Draw a rounded stage box centered at cx, anchored at y.
    Returns SVG fragment string.
    """
    w, h = 220, 72
    x = cx - w // 2
    border_colors = {
        "blue": "#2b7be4",
        "cyan": "#00bcd4",
        "amber": "#ff9800",
        "gold": "#f5c842",
    }
    bcol = border_colors.get(color, "#2b7be4")
    grad_id = f"gradStage{color.capitalize()}" if color in ("blue","cyan","amber") else "gradStageBlue"

    lines = ""
    if len(detail_lines) == 1:
        lines = f'<text x="{cx}" y="{y+48}" text-anchor="middle" class="h-detail">{detail_lines[0]}</text>'
    else:
        for i, ln in enumerate(detail_lines):
            lines += f'<text x="{cx}" y="{y+42+i*16}" text-anchor="middle" class="h-detail">{ln}</text>\n    '

    arrow = ""
    if arrow_to_x is not None and arrow_to_y is not None:
        marker = marker_id or f"arrow{color.capitalize()}"
        mx, my = x + w + 4, y + h//2
        arrow = f'<path d="M{mx},{my} C{mx+20},{my} {arrow_to_x-20},{arrow_to_y} {arrow_to_x},{arrow_to_y}" stroke="{bcol}" stroke-width="2.5" fill="none" marker-end="url(#{marker})" opacity="0.8"/>'

    return f'''  <g filter="url(#shadowStage)">
    <rect x="{x}" y="{y}" rx="12" ry="12" width="{w}" height="{h}" fill="url(#{grad_id})" stroke="{bcol}" stroke-width="1.5"/>
    <rect x="{x}" y="{y}" rx="12" ry="12" width="{w}" height="26" fill="{bcol}" opacity="0.12"/>
    <text x="{cx}" y="{y+30}" text-anchor="middle" class="h-label" fill="white">{label}</text>
    {lines}
  </g>
  {arrow}'''


# ──────────────────────────────────────────
# TRIPWIRE / RISK DIAMOND
# ──────────────────────────────────────────
def tripwire_diamond(cx, cy, label, detail, side="right"):
    """Draw a red diamond tripwire indicator. side: 'right' or 'left' for label."""
    label_x = cx + 35 if side == "right" else cx - 200
    anchor = "start" if side == "right" else "end"

    return f'''  <g filter="url(#shadowTrip)">
    <!-- Diamond -->
    <polygon points="{cx},{cy-14} {cx+14},{cy} {cx},{cy+14} {cx-14},{cy}" fill="url(#gradTripwire)" stroke="#ff7961" stroke-width="1.5"/>
    <polygon points="{cx},{cy-8} {cx+8},{cy} {cx},{cy+8} {cx-8},{cy}" fill="none" stroke="#fff" stroke-width="0.8" opacity="0.4"/>
  </g>
  <text x="{label_x}" y="{cy-3}" class="h-trip" text-anchor="{anchor}">{label}</text>
  <text x="{label_x}" y="{cy+13}" class="h-trip-d" text-anchor="{anchor}">{detail}</text>'''


# ──────────────────────────────────────────
# STRATEGIC IMPLICATION CARD
# ──────────────────────────────────────────
def implication_card(x, y, title, detail, color):
    """Single implication card."""
    accent_colors = {
        "blue": BLUE_PRIMARY,
        "cyan": CYAN_ACCENT,
        "red": RED_ACCENT,
        "amber": AMBER_ACCENT,
        "gold": GOLD_ACCENT,
        "teal": TEAL_ACCENT,
    }
    ac = accent_colors.get(color, BLUE_PRIMARY)
    # multi-line wrap detail
    lines = wrap(detail, 36)
    txt = ""
    for i, ln in enumerate(lines[:2]):
        txt += f'<text x="{x+16}" y="{y+48+i*16}" class="h-card-d">{ln}</text>\n    '
    if len(lines) > 2:
        txt += f'<text x="{x+16}" y="{y+48+2*16}" class="h-card-d">{lines[2]}</text>\n    '

    return f'''  <g filter="url(#shadowCard)">
    <rect x="{x}" y="{y}" rx="10" ry="10" width="210" height="110" fill="{NAVY_CARD}" stroke="#1e2d42" stroke-width="1"/>
    <rect x="{x}" y="{y}" rx="10" ry="10" width="210" height="3" fill="{ac}"/>
    <circle cx="{x+16}" cy="{y+24}" r="5" fill="{ac}"/>
    <text x="{x+28}" y="{y+28}" class="h-card-t">{title}</text>
    {txt}
  </g>'''


# ──────────────────────────────────────────
# HEADER / TITLE BAR
# ──────────────────────────────────────────
def title_bar(x, y, title, subtitle, badge_text="CRITICAL", badge_color="#e53935"):
    return f'''  <g transform="translate({x},{y})">
    <text x="0" y="0" class="h-title">{title}</text>
    <text x="0" y="24" class="h-sub">{subtitle}</text>
    <g transform="translate(600, -4)">
      <rect x="0" y="0" width="120" height="26" rx="13" fill="{badge_color}" opacity="0.2"/>
      <rect x="0" y="0" width="120" height="26" rx="13" fill="none" stroke="{badge_color}" stroke-width="1" opacity="0.6"/>
      <text x="60" y="18" text-anchor="middle" class="h-meta" fill="{badge_color}" font-weight="800">{badge_text}</text>
    </g>
  </g>'''


# ──────────────────────────────────────────
# DASHED CONNECTOR (tripwire to stage)
# ──────────────────────────────────────────
def dashed_connector(x1, y1, x2, y2, color=RED_ACCENT):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="1.8" stroke-dasharray="5,4" opacity="0.5"/>'


# ──────────────────────────────────────────
# MAIN GENERATOR
# ──────────────────────────────────────────
def generate_infographic(topic, data_points, output_file):
    """Generate an infographic SVG and write to output_file."""
    # Parse data points
    if isinstance(data_points, str):
        data = json.loads(data_points)
    else:
        data = data_points

    title = topic
    subtitle = data.get("subtitle", "Strategic Assessment")
    badge = data.get("badge", "CRITICAL")
    badge_color = data.get("badge_color", "#e53935")
    stages = data.get("stages", [])
    tripwire = data.get("tripwire", {})
    implications = data.get("implications", [])
    date = data.get("date", "2026-05-02")
    width = data.get("width", 800)
    height = data.get("height", 950)

    # Layout constants
    STAGE_W = 220
    STAGE_H = 72
    STAGE_GAP = 80  # horizontal gap between stages

    # Position stages horizontally centered
    n_stages = len(stages)
    total_width = n_stages * STAGE_W + (n_stages - 1) * STAGE_GAP
    start_x = (width - total_width) // 2 + STAGE_W // 2

    stage_y = 130
    stage_positions = []  # list of (cx, y, color)

    svg_parts = []

    # Title
    svg_parts.append(title_bar(40, 38, title, subtitle, badge, badge_color))

    # Stage progression
    stage_fragments = []
    for i, stage in enumerate(stages):
        cx = start_x + i * (STAGE_W + STAGE_GAP)
        cy = stage_y
        color = stage.get("color", "blue")
        label = stage.get("label", f"Stage {i+1}")
        detail = stage.get("detail", "")
        detail_lines = wrap(detail, 25)
        arrow_to_x = None
        arrow_to_y = None
        if i < n_stages - 1:
            next_cx = start_x + (i+1) * (STAGE_W + STAGE_GAP)
            mid_x = cx + STAGE_W//2 + STAGE_GAP//2
            arrow_to_x = next_cx - STAGE_W//2 - 4
            arrow_to_y = cy + STAGE_H//2
        sf = stage_box(cx, cy, label, detail_lines, color,
                       f"arrow{color.capitalize()}" if color in ("blue","cyan","amber","gold") else "arrowBlue",
                       arrow_to_x, arrow_to_y)
        stage_fragments.append(sf)
        stage_positions.append((cx, cy, color))

    svg_parts.extend(stage_fragments)

    # Tripwire / Risk Diamond
    if tripwire:
        trip_label = tripwire.get("label", "TRIPWIRE")
        trip_detail = tripwire.get("detail", "")
        trip_cx = tripwire.get("cx")
        trip_cy = tripwire.get("cy")
        trip_side = tripwire.get("side", "right")

        if trip_cx is None or trip_cy is None:
            # Auto-place: center-right or center-left
            trip_cx = width - 80
            trip_cy = stage_y + STAGE_H//2
            trip_side = "right"

        svg_parts.append(tripwire_diamond(trip_cx, trip_cy, trip_label, trip_detail, trip_side))

        # Dashed connectors from tripwire to relevant stages
        connected = tripwire.get("connected_to", [])
        for ci in connected:
            if ci < len(stage_positions):
                scx, scy, _ = stage_positions[ci]
                # connect from tripwire diamond to right edge of stage
                svg_parts.append(dashed_connector(
                    trip_cx - 14, trip_cy,
                    scx + STAGE_W//2, scy + STAGE_H//2
                ))

    # "STRATEGIC IMPLICATIONS" section header
    imp_start_y = stage_y + STAGE_H + 90
    svg_parts.append(f'''  <g transform="translate(40, {imp_start_y})">
    <text x="0" y="0" class="h-label" fill="{GOLD_ACCENT}" font-size="18">STRATEGIC IMPLICATIONS</text>
    <rect x="0" y="10" width="{width-80}" height="1" fill="url(#gradGoldLine)"/>
  </g>''')

    # Accent color lookup for inlined card generation
    _accent_map = {
        "blue": BLUE_PRIMARY,
        "cyan": CYAN_ACCENT,
        "red": RED_ACCENT,
        "amber": AMBER_ACCENT,
        "gold": GOLD_ACCENT,
        "teal": TEAL_ACCENT,
    }

    # Implication cards — auto-fit to width
    n_imp = min(len(implications), 4)
    card_start_y = imp_start_y + 36
    available = width - 80
    card_gap = 16
    card_width = (available - (n_imp - 1) * card_gap) // n_imp
    if card_width > 200:
        card_width = 200
    total_cards_width = n_imp * card_width + (n_imp - 1) * card_gap
    card_start_x = (width - total_cards_width) // 2

    for i, imp in enumerate(implications[:n_imp]):
        x = card_start_x + i * (card_width + card_gap)
        c = _accent_map.get(imp.get('color', 'blue'), BLUE_PRIMARY)
        wrap_w = max(20, card_width // 6)
        lines = wrap(imp.get("detail", ""), wrap_w)
        detail_txt = ""
        for li, ln in enumerate(lines[:3]):
            detail_txt += f'<text x="{x+12}" y="{card_start_y+48+li*16}" class="h-card-d">{ln}</text>\n    '
        svg_parts.append(f'''  <g filter="url(#shadowCard)">
    <rect x="{x}" y="{card_start_y}" rx="10" ry="10" width="{card_width}" height="110" fill="{NAVY_CARD}" stroke="#1e2d42" stroke-width="1"/>
    <rect x="{x}" y="{card_start_y}" rx="10" ry="10" width="{card_width}" height="3" fill="{c}"/>
    <circle cx="{x+12}" cy="{card_start_y+24}" r="5" fill="{c}"/>
    <text x="{x+22}" y="{card_start_y+28}" class="h-card-t" font-size="13">{imp.get('title', '')}</text>
    {detail_txt}
  </g>''')

    # Assemble
    footer_y = card_start_y + 130
    svg_body = "\n".join(svg_parts)

    svg_full = HEADER.format(width=width, height=height, title=title,
                              WHITE_TEXT=WHITE_TEXT, LIGHT_TEXT=LIGHT_TEXT,
                              MUTED_TEXT=MUTED_TEXT,
                              NAVY_BG=NAVY_BG, NAVY_CARD=NAVY_CARD,
                              GOLD_ACCENT=GOLD_ACCENT,
                              BLUE_PRIMARY=BLUE_PRIMARY,
                              CYAN_ACCENT=CYAN_ACCENT,
                              AMBER_ACCENT=AMBER_ACCENT,
                              RED_ACCENT=RED_ACCENT, ORANGE_ACCENT=ORANGE_ACCENT,
                              DARK_CARD=DARK_CARD, BORDER_SUBTLE=BORDER_SUBTLE) + \
               svg_body + \
               FOOTER.format(footer_y=footer_y, date=date,
                             MUTED_TEXT=MUTED_TEXT, GOLD_ACCENT=GOLD_ACCENT)

    # Write
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    with open(output_file, "w") as f:
        f.write(svg_full)

    file_size = os.path.getsize(output_file)
    return output_file, file_size, len(svg_full)


# ──────────────────────────────────────────
# CLI
# ──────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Generate professional SVG infographic")
    parser.add_argument("--topic", required=True, help="Infographic title")
    parser.add_argument("--data-points", required=True, help="JSON string with infographic data")
    parser.add_argument("--output", required=True, help="Output SVG filename")
    args = parser.parse_args()

    path, size, chars = generate_infographic(args.topic, args.data_points, args.output)
    print(f"✅ Generated: {path}")
    print(f"   Size: {size:,} bytes ({size/1024:.1f} KB)")
    print(f"   Characters: {chars:,}")


if __name__ == "__main__":
    main()
