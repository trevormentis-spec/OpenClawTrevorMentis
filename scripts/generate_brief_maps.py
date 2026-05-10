#!/usr/bin/env python3
"""
generate_brief_maps.py — Generate theatre-specific geopolitical maps for the brief.

Reads theatre analysis, extracts location context, and generates styled
maps using Natural Earth land data + matplotlib. Outputs high-DPI PNGs
that get embedded into the magazine PDF.

Usage:
    python3 generate_brief_maps.py \
        --working-dir ~/trevor-briefings/2026-05-10 \
        --out-dir ~/trevor-briefings/2026-05-10/visuals/maps

Depends: matplotlib, PIL (Pillow)
Also downloads: Natural Earth 110m land GeoJSON (once, cached at /tmp)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.request

import matplotlib
matplotlib.use("Agg")  # Headless
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path
import numpy as np

# ── TREVOR Design Colors ──
DARK_BG = "#0f0f1a"
GOLD = "#c9a84c"
WHITE = "#ffffff"
ACCENT = "#b82e2e"
GREEN = "#4a7c3f"
WATER = "#1a1a2e"
LAND = "#2a2a3e"
GRID = (1, 1, 1, 0.08)

# ── Key locations per theatre (city_name, lat, lng, importance) ──
LOCATIONS = {
    "europe": [
        ("Kyiv", 50.45, 30.52, "primary"),
        ("Moscow", 55.76, 37.62, "primary"),
        ("Berlin", 52.52, 13.41, "secondary"),
        ("Brussels", 50.85, 4.35, "secondary"),
        ("Warsaw", 52.23, 21.01, "secondary"),
        ("London", 51.51, -0.13, "secondary"),
        ("Paris", 48.86, 2.35, "secondary"),
        ("Oslo", 59.91, 10.75, "secondary"),
        ("Minsk", 53.90, 27.56, "tertiary"),
        ("Donetsk", 48.02, 37.80, "tertiary"),
    ],
    "asia": [
        ("Beijing", 39.90, 116.40, "primary"),
        ("Taipei", 25.03, 121.57, "primary"),
        ("New Delhi", 28.61, 77.23, "primary"),
        ("Islamabad", 33.68, 73.05, "secondary"),
        ("Tokyo", 35.68, 139.69, "secondary"),
        ("Seoul", 37.57, 126.98, "secondary"),
        ("Mbabane", -26.32, 31.13, "tertiary"),
        ("Shanghai", 31.23, 121.47, "tertiary"),
    ],
    "middle_east": [
        ("Tehran", 35.69, 51.42, "primary"),
        ("Dubai", 25.20, 55.27, "primary"),
        ("Baghdad", 33.32, 44.36, "secondary"),
        ("Beirut", 33.89, 35.50, "secondary"),
        ("Tel Aviv", 32.08, 34.78, "secondary"),
        ("Riyadh", 24.71, 46.67, "secondary"),
        ("Sana'a", 15.37, 44.19, "tertiary"),
        ("Muscat", 23.59, 58.41, "tertiary"),
        ("Strait of Hormuz", 26.57, 56.25, "primary"),
    ],
    "north_america": [
        ("Washington DC", 38.91, -77.04, "primary"),
        ("Mexico City", 19.43, -99.13, "primary"),
        ("Ottawa", 45.42, -75.70, "secondary"),
        ("New York", 40.71, -74.01, "secondary"),
        ("Houston", 29.76, -95.37, "tertiary"),
        ("Ciudad Juárez", 31.72, -106.46, "tertiary"),
        ("Caracas", 10.48, -66.90, "secondary"),
    ],
    "south_central_america": [
        ("Havana", 23.11, -82.37, "primary"),
        ("Caracas", 10.48, -66.90, "primary"),
        ("Brasília", -15.79, -47.88, "secondary"),
        ("Bogotá", 4.71, -74.07, "secondary"),
        ("Lima", -12.05, -77.04, "secondary"),
        ("Recife", -8.05, -34.88, "tertiary"),
        ("Panama City", 8.98, -79.52, "tertiary"),
    ],
    "global_finance": [
        ("New York", 40.71, -74.01, "primary"),
        ("London", 51.51, -0.13, "primary"),
        ("Shanghai", 31.23, 121.47, "primary"),
        ("Dubai", 25.20, 55.27, "secondary"),
        ("Singapore", 1.35, 103.82, "secondary"),
        ("Frankfurt", 50.11, 8.68, "secondary"),
        ("Tokyo", 35.68, 139.69, "secondary"),
        ("Mumbai", 19.08, 72.88, "tertiary"),
    ],
}

# ── Region bounding boxes (min_lon, min_lat, max_lon, max_lat) ──
BOUNDS = {
    "europe": (-10, 35, 40, 65),
    "asia": (60, 5, 140, 45),
    "middle_east": (25, 10, 65, 42),
    "north_america": (-130, 10, -55, 55),
    "south_central_america": (-90, -35, -30, 27),
    "global_finance": (-180, -60, 180, 70),
}

# ── Cover / world map ──
WORLD_BOUNDS = (-180, -60, 180, 75)


def load_land_data() -> list:
    """Load Natural Earth 110m land data, cached at /tmp."""
    cache_path = pathlib.Path("/tmp/ne_110m_land.geojson")
    if cache_path.exists():
        with open(cache_path) as f:
            data = json.load(f)
        return data["features"]

    # Download
    url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.load(resp)
            with open(cache_path, "w") as f:
                json.dump(data, f)
            return data["features"]
    except Exception as e:
        print(f"  ⚠ Could not download land data: {e}", file=sys.stderr)
        return []


def extract_region_locations(region: str, narrative: str, judgments: list) -> list:
    """Filter and rank locations based on analysis content."""
    base = LOCATIONS.get(region, [])
    narr_lower = narrative.lower()

    # Score locations by mention in narrative
    scored = []
    for name, lat, lng, importance in base:
        score = 0
        name_lower = name.lower()
        # Direct mention
        if name_lower in narr_lower:
            score += 3
        # Partial match
        parts = name_lower.split()
        for part in parts:
            if len(part) > 3 and part in narr_lower:
                score += 1
        # Importance boost
        if importance == "primary":
            score += 2
        elif importance == "secondary":
            score += 1
        scored.append((name, lat, lng, importance, score))

    # Sort by score descending
    scored.sort(key=lambda x: -x[4])
    # Return top locations, ensuring at least primary locations are included
    result = [(n, lt, ln, imp) for n, lt, ln, imp, s in scored if s > 0 or imp == "primary"]
    return result[:8]  # Max 8 markers per map


def render_map(
    region: str,
    locations: list,
    bounds: tuple,
    land_features: list,
    date_str: str,
    output_path: str,
) -> bool:
    """Render a single theatre map."""

    min_lon, min_lat, max_lon, max_lat = bounds

    # Create figure
    dpi = 300
    fig_w = 9.0
    fig_h = 6.0
    fig, ax = plt.subplots(1, 1, figsize=(fig_w, fig_h), dpi=dpi)
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(WATER)

    # Plot land masses
    for feature in land_features:
        geom = feature.get("geometry", {})
        if geom.get("type") == "Polygon":
            coords = geom["coordinates"]
            for ring in coords:
                xs, ys = zip(*ring) if ring else ([], [])
                ax.fill(xs, ys, color=LAND, ec="#3a3a4e", linewidth=0.3, zorder=1)
        elif geom.get("type") == "MultiPolygon":
            for poly in geom["coordinates"]:
                for ring in poly:
                    xs, ys = zip(*ring) if ring else ([], [])
                    ax.fill(xs, ys, color=LAND, ec="#3a3a4e", linewidth=0.3, zorder=1)

    # Plot location markers
    for name, lat, lng, importance in locations:
        if importance == "primary":
            ax.plot(lng, lat, "o", color=ACCENT, markersize=8,
                    markeredgecolor=WHITE, markeredgewidth=0.8, zorder=5)
            ax.annotate(name, (lng, lat),
                        textcoords="offset points", xytext=(8, 4),
                        fontsize=6.5, fontweight="bold", color=WHITE,
                        fontfamily="sans-serif", zorder=6)
        elif importance == "secondary":
            ax.plot(lng, lat, "o", color=GOLD, markersize=5,
                    markeredgecolor=WHITE, markeredgewidth=0.5, zorder=5)
            ax.annotate(name, (lng, lat),
                        textcoords="offset points", xytext=(6, 3),
                        fontsize=5.5, color=(1,1,1,0.8),
                        fontfamily="sans-serif", zorder=6)
        else:
            ax.plot(lng, lat, "o", color="#888", markersize=3, zorder=5)
            ax.annotate(name, (lng, lat),
                        textcoords="offset points", xytext=(5, 2),
                        fontsize=5, color=(1,1,1,0.6),
                        fontfamily="sans-serif", zorder=6)

    # Grid lines
    ax.set_xticks(np.arange(-180, 181, 10))
    ax.set_yticks(np.arange(-90, 91, 10))
    ax.grid(True, color=GRID, linewidth=0.3)
    ax.tick_params(colors=(1,1,1,0.3), labelsize=5)

    # Labels
    region_name = {
        "europe": "Europe", "asia": "Asia", "middle_east": "Middle East",
        "north_america": "North America", "south_central_america": "South & Central America",
        "global_finance": "Global Finance", "cover": "Global",
    }.get(region, region.replace("_", " ").title())

    ax.set_title(f"{region_name} — Operational Picture", fontsize=10,
                 fontweight="bold", color=GOLD, fontfamily="sans-serif",
                 pad=8)

    # Set bounds
    # Add a small margin
    margin_lon = (max_lon - min_lon) * 0.05
    margin_lat = (max_lat - min_lat) * 0.05
    ax.set_xlim(min_lon - margin_lon, max_lon + margin_lon)
    ax.set_ylim(min_lat - margin_lat, max_lat + margin_lat)

    # Remove spines
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Footer
    ax.text(0.5, -0.04, f"TREVOR INTELLIGENCE • {date_str}",
            transform=ax.transAxes, fontsize=5.5, color=(1,1,1,0.3),
            fontfamily="sans-serif", ha="center", va="top")

    plt.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight",
                facecolor=DARK_BG, edgecolor="none")
    plt.close(fig)
    return True


def render_world_map(land_features: list, date_str: str, output_path: str) -> bool:
    """Render a global overview map for the cover or finance section."""
    return render_map("global_finance", LOCATIONS["global_finance"],
                      WORLD_BOUNDS, land_features, date_str, output_path)


def main():
    parser = argparse.ArgumentParser(description="Generate theatre maps")
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    wd = pathlib.Path(args.working_dir).expanduser()
    ad = wd / "analysis"
    out_dir = pathlib.Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    date_str = dt.date.today().strftime("%d %B %Y")

    print(f"=== Generate Maps — {dt.datetime.now().isoformat()} ===")
    print(f"Loading land data...", flush=True)
    land_features = load_land_data()
    if not land_features:
        print("ERROR: No land data available")
        return 1
    print(f"Loaded {len(land_features)} land features")

    region_order = ["europe", "asia", "middle_east", "north_america",
                    "south_central_america", "global_finance"]

    map_paths = {}

    for region in region_order:
        rpath = ad / f"{region}.json"
        narrative = ""
        judgments = []
        if rpath.exists():
            with open(rpath) as f:
                t = json.load(f)
            narrative = t.get("narrative", "")
            judgments = t.get("key_judgments", [])

        locations = extract_region_locations(region, narrative, judgments)
        bounds = BOUNDS.get(region, (-180, -60, 180, 75))
        out_path = out_dir / f"map_{region}.png"

        print(f"  {region}: {len(locations)} locations → {out_path.name}", flush=True)
        ok = render_map(region, locations, bounds, land_features,
                        date_str, str(out_path))
        if ok:
            map_paths[region] = str(out_path)
            size_kb = out_path.stat().st_size / 1024
            print(f"    ✅ {size_kb:.0f} KB", flush=True)
        else:
            print(f"    ❌ Failed", flush=True)

    # Save map manifest
    manifest = out_dir / "manifest.json"
    with open(manifest, "w") as f:
        json.dump(map_paths, f, indent=2)
    print(f"✅ Manifest: {manifest} ({len(map_paths)} maps)")


if __name__ == "__main__":
    sys.exit(main())
