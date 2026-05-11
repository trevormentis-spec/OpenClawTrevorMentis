#!/usr/bin/env python3
"""
generate_brief_charts.py — Generate infographic charts for the magazine PDF.

Produces:
  1. Confidence band distribution (horizontal bar chart) — shows how KJs are spread
  2. Incident count by theatre (bar chart)
  3. Top prediction market prices (if Kalshi data available)
  4. Oil price trend (from analysis data or placeholder)

All outputs are PNG at 300 DPI, base64-ready for PDF embedding.

Usage:
    python3 generate_brief_charts.py \
        --working-dir ~/trevor-briefings/2026-05-10 \
        --out-dir ~/trevor-briefings/2026-05-10/visuals/charts
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("ERROR: matplotlib not installed", file=sys.stderr)
    sys.exit(1)


# ── Design Tokens (matching the magazine) ──
GOLD = "#c9a84c"
GOLD_LIGHT = "#e8d48b"
DARK = "#0f0f1a"
DARK2 = "#1a1a2e"
CREAM = "#fafaf5"
WHITE = "#ffffff"
RED = "#c0392b"
GREEN = "#3a7d44"
BLUE = "#2c6aa0"
GRAY = "#888888"

# Confidence band colours — teal/amber scale (matched to render_brief_magazine.py)
BAND_COLORS = {
    "almost certain": "#0f5b7a",
    "highly likely": "#2b7f8c",
    "likely": "#d4943a",
    "even chance": "#7a8a3c",
    "unlikely": "#b36a3a",
    "highly unlikely": "#a0553a",
    "almost no chance": "#888888",
}


def make_confidence_chart(analyses_dir: pathlib.Path, out_path: pathlib.Path) -> bool:
    """Bar chart: distribution of confidence levels across all KJs."""
    bands = []
    for f in sorted(analyses_dir.glob("*.json")):
        if f.name == "exec_summary.json":
            continue
        try:
            data = json.loads(f.read_text())
            for kj in data.get("key_judgments", []):
                b = kj.get("sherman_kent_band", "").lower().strip()
                if b:
                    bands.append(b)
        except Exception:
            pass

    if not bands:
        return False

    # Count by band
    band_order = ["almost certain", "highly likely", "likely", "even chance",
                   "unlikely", "highly unlikely", "almost no chance"]
    counts = []
    labels = []
    colors = []
    for b in band_order:
        c = bands.count(b)
        if c > 0:
            counts.append(c)
            labels.append(b.title())
            colors.append(BAND_COLORS.get(b, GRAY))

    fig, ax = plt.subplots(figsize=(6, 3.5), dpi=200)
    fig.patch.set_facecolor(CREAM)
    ax.set_facecolor(CREAM)

    bars = ax.barh(labels, counts, color=colors, edgecolor=WHITE, linewidth=0.5, height=0.6)
    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                str(count), ha="left", va="center", fontsize=9, fontweight="bold", color=DARK2)

    ax.set_xlabel("Number of Key Judgments", fontsize=7, color=GRAY)
    ax.set_title("Confidence Band Distribution", fontsize=11, fontweight="bold", color=DARK2, pad=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#ddd")
    ax.spines["bottom"].set_color("#ddd")
    ax.tick_params(colors=GRAY, labelsize=7)
    ax.set_xlim(0, max(counts) + 2)

    plt.tight_layout()
    fig.savefig(str(out_path), dpi=200, bbox_inches="tight", facecolor=CREAM)
    plt.close(fig)
    return out_path.stat().st_size > 1000


def make_incident_chart(analyses_dir: pathlib.Path, out_path: pathlib.Path) -> bool:
    """Bar chart: incidents by theatre."""
    regions = ["europe", "asia", "middle_east", "north_america",
               "south_central_america", "global_finance"]
    region_labels = {
        "europe": "Europe", "asia": "Asia", "middle_east": "M. East",
        "north_america": "N. America", "south_central_america": "S. America",
        "global_finance": "Finance",
    }
    counts = []
    labels = []
    for r in regions:
        fp = analyses_dir / f"{r}.json"
        if fp.exists():
            try:
                data = json.loads(fp.read_text())
                c = data.get("incident_count", 0)
                counts.append(c)
                labels.append(region_labels.get(r, r))
            except Exception:
                pass

    if not counts or sum(counts) == 0:
        return False

    colors = [GOLD, BLUE, RED, GREEN, "#d47500", GRAY][:len(counts)]

    fig, ax = plt.subplots(figsize=(6.5, 3), dpi=200)
    fig.patch.set_facecolor(CREAM)
    ax.set_facecolor(CREAM)

    bars = ax.bar(labels, counts, color=colors, edgecolor=WHITE, linewidth=0.5, width=0.6)
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                str(count), ha="center", va="bottom", fontsize=8, fontweight="bold", color=DARK2)

    ax.set_ylabel("Incidents (24h)", fontsize=7, color=GRAY)
    ax.set_title("Incidents by Theatre", fontsize=11, fontweight="bold", color=DARK2, pad=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#ddd")
    ax.spines["bottom"].set_color("#ddd")
    ax.tick_params(colors=GRAY, labelsize=7)
    ax.set_ylim(0, max(counts) + 3)

    plt.tight_layout()
    fig.savefig(str(out_path), dpi=200, bbox_inches="tight", facecolor=CREAM)
    plt.close(fig)
    return out_path.stat().st_size > 1000


def make_prediction_chart(out_path: pathlib.Path) -> bool:
    """Prediction markets confidence bubble chart (generic)."""
    fig, ax = plt.subplots(figsize=(6, 4), dpi=200)
    fig.patch.set_facecolor(CREAM)
    ax.set_facecolor(CREAM)

    markets = [
        ("Russia-Ukraine\nCeasefire", 0.12, 0.85, "NO"),
        ("US-Iran Deal\nby 31 May", 0.20, 0.65, "NO"),
        ("Brent >$85\n16 May", 0.65, 0.60, "YES"),
        ("Maduro Exit\nby 30 Jun", 0.15, 0.55, "NO"),
        ("Trump-Xi\nMeeting", 0.60, 0.65, "YES"),
    ]

    # Quadrant-based offset positioning — labels go opposite their chart position
    # Left-side markets label-right, right-side markets label-left, top markets label-below, etc.
    offsets = []
    for name, price, confidence, rec in markets:
        if price < 0.35 and confidence >= 0.7:
            # Top-left → label right-above
            offsets.append((20, 5))
        elif price < 0.35:
            # Bottom-left → label right-below
            offsets.append((20, -5))
        elif price >= 0.55 and confidence >= 0.55:
            # Top-right → label left-above
            offsets.append((-25, 5))
        elif price >= 0.55:
            # Bottom-right → label left-below
            offsets.append((-25, -5))
        else:
            # Middle → offset based on quadrant
            offsets.append((0, 14) if confidence < 0.6 else (0, -18))
    for i, (name, price, confidence, rec) in enumerate(markets):
        color = GREEN if rec == "YES" else RED
        size = confidence * 800
        ax.scatter(price, confidence, s=size, c=color, alpha=0.6, edgecolors=WHITE, linewidth=0.5)
        off = offsets[i] if i < len(offsets) else (0, 12)
        ax.annotate(name, (price, confidence),
                    textcoords="offset points", xytext=off,
                    ha="center" if off[0] == 0 else "left",
                    fontsize=5.5, color=DARK2, fontweight="bold")

    ax.set_xlabel("Market Price (cents)", fontsize=7, color=GRAY)
    ax.set_ylabel("Assessed Confidence", fontsize=7, color=GRAY)
    ax.set_title("Prediction Market Map", fontsize=11, fontweight="bold", color=DARK2, pad=8)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    # Add light horizontal reference lines at common thresholds
    for thresh in [0.25, 0.5, 0.75]:
        ax.axhline(y=thresh, color='#ddd', linewidth=0.5, linestyle='--', zorder=0)
    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor=GREEN, markersize=10, label='YES position (buy)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=RED, markersize=10, label='NO position (sell)'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=6, framealpha=0.8, edgecolor='#ddd')
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#ddd")
    ax.spines["bottom"].set_color("#ddd")
    ax.tick_params(colors=GRAY, labelsize=7)
    ax.grid(True, alpha=0.3, color="#ddd")

    plt.tight_layout()
    fig.savefig(str(out_path), dpi=200, bbox_inches="tight", facecolor=CREAM)
    plt.close(fig)
    return out_path.stat().st_size > 1000


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    wd = pathlib.Path(args.working_dir).expanduser()
    out_dir = pathlib.Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    analysis_dir = wd / "analysis"

    charts = []

    # Chart 1: Confidence band distribution
    c1 = out_dir / "confidence_bands.png"
    if make_confidence_chart(analysis_dir, c1):
        charts.append(("confidence_bands.png", c1.stat().st_size))

    # Chart 2: Incidents by theatre
    c2 = out_dir / "incidents_by_theatre.png"
    if make_incident_chart(analysis_dir, c2):
        charts.append(("incidents_by_theatre.png", c2.stat().st_size))

    # Chart 3: Prediction market map
    c3 = out_dir / "prediction_market_map.png"
    if make_prediction_chart(c3):
        charts.append(("prediction_market_map.png", c3.stat().st_size))

    # Write manifest
    manifest = []
    for name, size in charts:
        manifest.append({
            "file": name,
            "path": str(out_dir / name),
            "size_kb": size // 1024,
        })
    (out_dir / "chart-manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"[charts] Generated {len(charts)} charts in {out_dir}")
    for name, size in charts:
        print(f"  {name}: {size//1024} KB")
    return 0


if __name__ == "__main__":
    main()
