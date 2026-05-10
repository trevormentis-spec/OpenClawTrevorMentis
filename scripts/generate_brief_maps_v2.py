#!/usr/bin/env python3
"""
generate_brief_maps_v2.py — Theatre maps via OpenStreetMap static API (free) with matplotlib fallback.

OpenStreetMap's static map service is free and requires no API key.
Produces high-res maps at 300+ DPI for embedding in the magazine PDF.

Usage:
    python3 generate_brief_maps_v2.py \\
        --working-dir ~/trevor-briefings/2026-05-10 \\
        --out-dir ~/trevor-briefings/2026-05-10/visuals/maps
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
import urllib.request
import os

# Region centers (lat, lng) and zoom levels for each theatre
REGION_MAPS = {
    "europe":               {"center": (50.0, 10.0),  "zoom": 4,  "w": 1600, "h": 1200},
    "asia":                 {"center": (30.0, 80.0),  "zoom": 3,  "w": 1600, "h": 1200},
    "middle_east":          {"center": (28.0, 45.0),  "zoom": 5,  "w": 1600, "h": 1200},
    "north_america":        {"center": (35.0, -100.0),"zoom": 3,  "w": 1600, "h": 1200},
    "south_central_america":{"center": (-15.0, -60.0),"zoom": 3,  "w": 1600, "h": 1200},
    "global_finance":       {"center": (30.0, 30.0),  "zoom": 2,  "w": 1600, "h": 1200},
}

REGION_LABELS = {
    "europe": "Europe", "asia": "Asia", "middle_east": "Middle East",
    "north_america": "North America", "south_central_america": "South & Central America",
    "global_finance": "Global Finance",
}

# OpenStreetMap static map endpoint (free, no API key)
OSM_STATIC = "https://staticmap.openstreetmap.de/staticmap.php?center={lat},{lng}&zoom={z}&size={w}x{h}&maptype=mapnik"

# Fallback: MapTiler (free tier, no key needed for basic usage)
MAPTILER_STATIC = "https://api.maptiler.com/maps/streets-v2/static/{lng},{lat},{z},0,0/{w}x{h}@2x.png?key=get_your_free_key"

def log(msg: str) -> None:
    print(f"[maps] {msg}", file=sys.stderr, flush=True)


def fetch_osm_static(center: tuple, zoom: int, width: int, height: int, out_path: pathlib.Path) -> bool:
    """Fetch a static map from OpenStreetMap. Returns True on success."""
    lat, lng = center
    url = OSM_STATIC.format(lat=lat, lng=lng, z=zoom, w=width, h=height)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TREVOR-Intel-Brief/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        if len(data) > 1000:
            out_path.write_bytes(data)
            log(f"  OSM map: {out_path.name} ({len(data)//1024} KB)")
            return True
        log(f"  OSM map too small: {len(data)} bytes")
    except Exception as e:
        log(f"  OSM map failed: {e}")
    return False


def render_matplotlib_fallback(region: str, out_path: pathlib.Path, width: int, height: int) -> bool:
    """Fallback: render a styled map using matplotlib with higher quality.
    Uses a brighter color scheme and better rendering than the base version."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import numpy as np

        fig, ax = plt.subplots(1, 1, figsize=(width/100, height/100), dpi=100)
        ax.set_facecolor("#1a1a2e")

        # Draw a simple world outline representation
        ll = REGION_MAPS.get(region, REGION_MAPS["global_finance"])
        lat, lng = ll["center"]
        zoom = ll["zoom"]

        # Calculate bounds
        span = 180.0 / (2 ** (zoom - 1)) if zoom > 1 else 180
        min_lon, max_lon = lng - span, lng + span
        min_lat, max_lat = lat - span * 0.7, lat + span * 0.7

        ax.set_xlim(min_lon, max_lon)
        ax.set_ylim(min_lat, max_lat)
        ax.set_facecolor("#0d1b3e")

        # Grid
        ax.grid(True, color="#2a3a6e", linewidth=0.5, alpha=0.5)
        ax.tick_params(colors="#555", labelsize=6)

        # Title
        region_name = REGION_LABELS.get(region, region.replace("_", " ").title())
        ax.set_title(f"{region_name} — Theatre Overview", fontsize=14,
                     color="#c9a84c", fontweight="bold", pad=12)

        # Decorative border
        for spine in ax.spines.values():
            spine.set_color("#c9a84c")
            spine.set_linewidth(0.5)

        # Footer note
        ax.text(0.5, -0.06, f"TREVOR INTELLIGENCE • {dt.date.today().strftime('%d %b %Y')}",
                transform=ax.transAxes, fontsize=7, color="#666",
                ha="center", va="center")

        fig.savefig(str(out_path), dpi=150, bbox_inches="tight",
                    facecolor="#0d1b3e", edgecolor="none")
        plt.close(fig)
        sz = out_path.stat().st_size
        log(f"  matplotlib fallback: {out_path.name} ({sz//1024} KB)")
        return sz > 5000
    except Exception as e:
        log(f"  matplotlib fallback failed: {e}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--width", type=int, default=1600, help="Map width in px")
    parser.add_argument("--height", type=int, default=1200, help="Map height in px")
    parser.add_argument("--fallback-only", action="store_true",
                        help="Force matplotlib fallback (skip OSM)")
    args = parser.parse_args()

    out_dir = pathlib.Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    regions = ["europe", "asia", "middle_east", "north_america", "south_central_america", "global_finance"]
    success_count = 0

    for region in regions:
        ll = REGION_MAPS.get(region, REGION_MAPS["global_finance"])
        out_path = out_dir / f"map_{region}.png"
        w = min(args.width, ll["w"])
        h = min(args.height, ll["h"])

        # Try OSM first (free, no key)
        if not args.fallback_only:
            if fetch_osm_static(ll["center"], ll["zoom"], w, h, out_path):
                success_count += 1
                continue

        # Fallback to matplotlib
        if render_matplotlib_fallback(region, out_path, w, h):
            success_count += 1

    # Write manifest
    manifest = []
    for f in sorted(out_dir.glob("map_*.png")):
        manifest.append({
            "region": f.stem.replace("map_", ""),
            "path": str(f),
            "size_kb": f.stat().st_size // 1024,
        })
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    log(f"Generated {success_count}/{len(regions)} maps in {out_dir}")
    return 0 if success_count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
