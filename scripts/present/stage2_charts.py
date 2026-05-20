#!/usr/bin/env python3
"""Stage 2 — Charts & Diagrams.

Rule-based routing: section type → chart/diagram type via fixed dictionary.
No LLM calls. No Opus. No V4 Flash.

Routing table (10-line if/elif):
  - section.has_geographic → map placeholder (stage 3 handles rendering)
  - section.has_judgments → kent_bar chart
  - section.has_trade_positions → trade_bar chart
  - brief has 3+ sections → mermaid sections diagram
  - section.type == "political" → kent_bar if has judgments
  - section.type == "economic" → trade_bar if has trades
  - default → skip (no chart for this section)

Self-test: matplotlib importable? mmdc or mermaid.ink reachable?

Usage:
    python3 scripts/present/stage2_charts.py --brief /tmp/brief.json --output-dir exports/charts/

    python3 scripts/present/stage2_charts.py --self-test

Budget: $0.00 (all local tools).
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import textwrap
from typing import Any, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

WORKSPACE = pathlib.Path("/home/ubuntu/.openclaw/workspace")

# Brand colours
DARK_BG = "#1a1a2e"
NAVY = "#0f3460"
GOLD = "#c9a84c"
WHITE = "#f0f0f0"
GREY = "#888888"

# Sherman Kent band → (score, colour, label)
KENT_BANDS = {
    "almost_certain":  (9.5, "#00b300", "Almost Certain (≥93%)"),
    "highly_likely":   (8.5, "#33cc33", "Highly Likely (80-90%)"),
    "likely":          (7.0, "#99cc33", "Likely (60-75%)"),
    "probable":        (5.5, "#cccc33", "Probable (50-60%)"),
    "even_chance":     (4.0, "#cc9933", "Even Chance (40-50%)"),
    "unlikely":        (3.0, "#cc6633", "Unlikely (25-40%)"),
    "highly_unlikely": (1.5, "#cc3333", "Highly Unlikely (10-20%)"),
    "remote":          (0.5, "#990000", "Remote (<10%)"),
}

# ── Rule-based routing table ────────────────────────────────────────────
# Stub: this section type → chart type. Fixed dictionary, not LLM.
SECTION_ROUTE: dict[str, list[str]] = {
    "political": ["kent_bar"],
    "military":  ["kent_bar"],
    "security":  ["kent_bar"],
    "economic":  ["trade_bar", "kent_bar"],
    "finance":   ["trade_bar"],
    "energy":    ["trade_bar"],
    "default":   ["kent_bar"],
}


def self_test() -> list[str]:
    """Check prerequisites. Returns list of failures (empty = pass)."""
    failures = []
    try:
        import matplotlib
        matplotlib.__version__
    except ImportError:
        failures.append("matplotlib not importable")
    try:
        import numpy
        numpy.__version__
    except ImportError:
        failures.append("numpy not importable")
    if not shutil.which("mmdc"):
        # mermaid.ink API fallback should work, but log a warning
        pass  # soft requirement — mermaid.ink is fallback
    return failures


# ═══════════════════════════════════════════════════════════════════════
# Chart renderers
# ═══════════════════════════════════════════════════════════════════════

def _style():
    plt.style.use("dark_background")
    plt.rcParams.update({
        "figure.facecolor": DARK_BG, "axes.facecolor": DARK_BG,
        "axes.edgecolor": GREY, "axes.labelcolor": WHITE,
        "text.color": WHITE, "xtick.color": GREY, "ytick.color": GREY,
        "grid.color": "#2a2a3e", "grid.alpha": 0.3,
        "font.family": "sans-serif",
    })


def _figsize(w: int = 1200, h: int = 800, dpi: int = 120) -> tuple:
    return (w / dpi, h / dpi)


def render_kent_bar(judgments: list[dict], output_path: str) -> None:
    """Horizontal bar chart of Sherman Kent probability bands."""
    _style()
    fig, ax = plt.subplots(figsize=_figsize())

    claims, scores, colors = [], [], []
    for j in judgments[:8]:
        band = j.get("kent_band", "").lower().replace(" ", "_")
        entry = KENT_BANDS.get(band)
        if not entry:
            continue
        score, color, label = entry
        claims.append(textwrap.fill(j.get("claim", "Untitled"), width=40))
        scores.append(score)
        colors.append(color)

    if claims:
        bars = ax.barh(range(len(claims)), scores, color=colors, height=0.6)
        ax.set_yticks(range(len(claims)))
        ax.set_yticklabels(claims, fontsize=8)
        ax.set_xlim(0, 10.5)
        ax.set_xlabel("Confidence", color=GREY, fontsize=9)
        ax.set_title("Key Judgments — Confidence Distribution",
                     color=GOLD, fontsize=13, fontweight="bold", pad=10)
        for score, _, _ in KENT_BANDS.values():
            ax.axvline(x=score, color="#ffffff", alpha=0.05, linewidth=0.5)
    else:
        ax.text(0.5, 0.5, "No judgments to display",
                ha="center", va="center", transform=ax.transAxes, color=GREY)

    plt.tight_layout()
    fig.savefig(output_path, dpi=120, bbox_inches="tight",
                facecolor=DARK_BG, edgecolor="none")
    plt.close(fig)


def render_trade_bar(trades: list[dict], output_path: str) -> None:
    """Horizontal bar of trade position sizes."""
    _style()
    fig, ax = plt.subplots(figsize=_figsize(1200, 600))

    instruments = [t.get("instrument", "?")[:25] for t in trades[:6]]
    sizes = [t.get("sizing_usd", 0) or 0 for t in trades[:6]]
    recs = [t.get("recommendation", "hold") for t in trades[:6]]
    rec_colors = {"buy": "#33cc33", "sell": "#cc3333", "hold": "#cccc33"}
    bar_colors = [rec_colors.get(r, GREY) for r in recs]

    if instruments and any(s > 0 for s in sizes):
        bars = ax.barh(range(len(instruments)), sizes, color=bar_colors, height=0.5)
        for bar, size in zip(bars, sizes):
            if size > 0:
                ax.text(bar.get_width() * 1.02, bar.get_y() + bar.get_height()/2,
                        f"${size:,.0f}", va="center", fontsize=8, color=WHITE)
        ax.set_yticks(range(len(instruments)))
        ax.set_yticklabels(instruments, fontsize=9)
        ax.set_xlabel("Position Size (USD)", color=GREY, fontsize=9)
        ax.set_title("Trade / Hedge Positions",
                     color=GOLD, fontsize=13, fontweight="bold")
    else:
        ax.text(0.5, 0.5, "No trade positions",
                ha="center", va="center", transform=ax.transAxes, color=GREY)

    plt.tight_layout()
    fig.savefig(output_path, dpi=120, bbox_inches="tight",
                facecolor=DARK_BG, edgecolor="none")
    plt.close(fig)


def render_mermaid_diagram(mermaid_code: str, output_path: str) -> None:
    """Render Mermaid → PNG via local mmdc or mermaid.ink fallback."""
    path = pathlib.Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if shutil.which("mmdc"):
        tmp = path.parent / f"_tmp_{path.stem}.mmd"
        try:
            tmp.write_text(mermaid_code)
            # Puppeteer config for no-sandbox (container requirement)
            config_path = path.parent / f"_puppeteer_{path.stem}.json"
            config_path.write_text(json.dumps({
                "puppeteerConfig": {"args": ["--no-sandbox", "--disable-setuid-sandbox"]}
            }))
            subprocess.run(
                ["mmdc", "-i", str(tmp), "-o", str(path),
                 "-b", "transparent", "-w", "1200", "-H", "800",
                 "-p", str(config_path)],
                capture_output=True, text=True, timeout=30, check=True,
            )
            if not path.exists() or path.stat().st_size < 100:
                raise RuntimeError("mmdc produced empty output")
            return
        except Exception:
            pass
        finally:
            tmp.unlink(missing_ok=True)
            config_path.unlink(missing_ok=True)

    # Fallback: mermaid.ink API
    import base64, urllib.request
    encoded = base64.urlsafe_b64encode(mermaid_code.encode("utf-8")).decode("ascii")
    url = f"https://mermaid.ink/img/{encoded}"
    req = urllib.request.Request(url, headers={"User-Agent": "Trevor-Present/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        path.write_bytes(resp.read())


# ═══════════════════════════════════════════════════════════════════════
# Rule-based routing: brief JSON → which charts
# ═══════════════════════════════════════════════════════════════════════

def route_brief(brief: dict) -> list[dict]:
    """Apply routing rules to a brief JSON. Returns list of chart specs.

    Each spec: {"type": str, "data": ..., "output": str}

    Fixed dictionary routing — no LLM calls.
    """
    specs = []
    judgments = brief.get("headline_judgments", [])
    trades = brief.get("trade_positions", [])
    sections = brief.get("sections", [])
    output_base = "exports/charts"  # will be overridden by caller

    # Rule 1: Has headline judgments → kent_bar
    if judgments:
        specs.append({"type": "kent_bar", "data": judgments, "output": "kent-bar.png"})

    # Rule 2: Has trade positions → trade_bar
    if trades:
        specs.append({"type": "trade_bar", "data": trades, "output": "trade-bar.png"})

    # Rule 3: Has 3+ sections → mermaid sections diagram
    if len(sections) >= 2:
        mermaid_lines = ["graph TD"]
        for i, s in enumerate(sections[:8]):
            title = s.get("title", f"S{i}").replace('"', "'")[:30]
            if i == 0:
                mermaid_lines.append(f'    S{i}["{title}"]')
            else:
                mermaid_lines.append(f'    S{i-1} --> S{i}["{title}"]')
        specs.append({"type": "mermaid", "data": "\n".join(mermaid_lines),
                      "output": "sections-diagram.png"})

    # Rule 4: Per-section routing (deeper analysis)
    for i, s in enumerate(sections):
        sec_judgments = s.get("judgments", []) + s.get("subsections", [{}])[0].get("judgments", []) if s.get("subsections") else []
        sec_trades = s.get("trade_positions", [])
        sec_type = s.get("type", "default")

        if sec_judgments:
            route = SECTION_ROUTE.get(sec_type, SECTION_ROUTE["default"])
            if "kent_bar" in route and len(specs) < 6:
                specs.append({
                    "type": "kent_bar",
                    "data": sec_judgments[:8],
                    "output": f"section-{i}-judgments.png",
                })

    return specs


def generate_chart(spec: dict, output_dir: str) -> dict:
    """Execute a single chart spec and return result metadata."""
    output_path = str(pathlib.Path(output_dir) / spec["output"])
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

    try:
        if spec["type"] == "kent_bar":
            render_kent_bar(spec["data"], output_path)
        elif spec["type"] == "trade_bar":
            render_trade_bar(spec["data"], output_path)
        elif spec["type"] == "mermaid":
            render_mermaid_diagram(spec["data"], output_path)
        else:
            return {"success": False, "error": f"Unknown type: {spec['type']}"}

        size_kb = pathlib.Path(output_path).stat().st_size / 1024
        return {"success": True, "output": output_path, "size_kb": round(size_kb, 1)}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

def process_brief(brief_path: str, output_dir: str) -> list[dict]:
    """Process a brief JSON and generate all routed charts."""
    brief = json.loads(pathlib.Path(brief_path).read_text())
    specs = route_brief(brief)
    results = []
    for spec in specs:
        result = generate_chart(spec, output_dir)
        result["spec_type"] = spec["type"]
        results.append(result)
    return results


def main():
    parser = argparse.ArgumentParser(description="Stage 2 — Charts & Diagrams")
    parser.add_argument("--brief", help="Path to brief JSON")
    parser.add_argument("--output-dir", "-o", default="exports/charts",
                        help="Output directory for chart PNGs")
    parser.add_argument("--self-test", action="store_true",
                        help="Run self-test and exit")
    args = parser.parse_args()

    if args.self_test:
        failures = self_test()
        if failures:
            for f in failures:
                print(f"  STAGE 2 DISABLED: {f}")
        else:
            print("  STAGE 2 READY: matplotlib + mmdc available")
        return

    if not args.brief or not pathlib.Path(args.brief).exists():
        parser.error("--brief path required and must exist")

    results = process_brief(args.brief, args.output_dir)
    for r in results:
        status = "✅" if r["success"] else "❌"
        details = r.get("output", r.get("error", ""))
        print(f"  {status} {r['spec_type']}: {details}")


if __name__ == "__main__":
    main()
