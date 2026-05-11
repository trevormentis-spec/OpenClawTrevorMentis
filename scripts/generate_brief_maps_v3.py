#!/usr/bin/env python3
"""
generate_brief_maps_v3.py — Branded theatre maps with Natural Earth basemap + GeoJSON overlays.

Downloads Natural Earth 110m land/coastline GeoJSON for basemap.
Plots conflict zones, route lines, city markers using matplotlib.
TREVOR brand colors throughout. No external geo libraries needed.

Usage:
    python3 generate_brief_maps_v3.py \\
        --working-dir ~/trevor-briefings/2026-05-10 \\
        --out-dir ~/trevor-briefings/2026-05-10/visuals/maps \\
        --geojson-data ~/trevor-briefings/2026-05-10/visuals/maps/theatre-geodata.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import pathlib
import sys
import urllib.request
import os

# ── Brand Tokens (match render_brief_magazine.py) ──
BG_DARK = "#080e1a"
BG_MID = "#0f1a30"
BG_LIGHT = "#16213e"
GOLD = "#d4a843"
WHITE = "#ffffff"
CREAM = "#f5f3ee"
RED = "#c0392b"
GREEN = "#3a7d44"
BLUE = "#2c6aa0"
ORANGE = "#d47500"
TEAL = "#2b7f8c"
GRAY = "#666666"
LGRAY = "#8899aa"

# Region config — centers, zoom, bbox with padding
REGION_MAPS = {
    "europe": {
        "center": (50.0, 10.0), "zoom": 4,
        "bbox": (-10, 35, 40, 62),  # minLon, minLat, maxLon, maxLat
        "label": "Europe",
        "land_color": "#1a2a4a",
        "water_color": "#0a1228",
        "grid_color": "#1e3050",
    },
    "asia": {
        "center": (30.0, 100.0), "zoom": 3,
        "bbox": (55, -10, 150, 55),
        "label": "Asia & Indo-Pacific",
        "land_color": "#1a2a4a",
        "water_color": "#0a1228",
        "grid_color": "#1e3050",
    },
    "middle_east": {
        "center": (28.0, 45.0), "zoom": 5,
        "bbox": (28, 10, 62, 42),
        "label": "Middle East",
        "land_color": "#1a2a4a",
        "water_color": "#0a1228",
        "grid_color": "#1e3050",
    },
    "north_america": {
        "center": (35.0, -100.0), "zoom": 3,
        "bbox": (-130, 5, -60, 55),
        "label": "North America",
        "land_color": "#1a2a4a",
        "water_color": "#0a1228",
        "grid_color": "#1e3050",
    },
    "south_central_america": {
        "center": (-15.0, -60.0), "zoom": 3,
        "bbox": (-90, -35, -30, 25),
        "label": "South & Central America",
        "land_color": "#1a2a4a",
        "water_color": "#0a1228",
        "grid_color": "#1e3050",
    },
    "global_finance": {
        "center": (30.0, 30.0), "zoom": 2,
        "bbox": (-180, -60, 180, 80),
        "label": "Global Finance",
        "land_color": "#1a2a4a",
        "water_color": "#0a1228",
        "grid_color": "#1e3050",
    },
}

# ── Natural Earth URLs ──
NE_LAND = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson"
NE_COUNTRIES = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"


def log(msg):
    print(f"[maps3] {msg}", file=sys.stderr, flush=True)


def fetch_geo(url, cache_dir):
    """Fetch GeoJSON with caching."""
    name = url.split("/")[-1]
    cache_path = cache_dir / name
    if cache_path.exists():
        log(f"  Loaded cached {name}")
        return json.loads(cache_path.read_text())
    log(f"  Downloading {name}...")
    req = urllib.request.Request(url, headers={"User-Agent": "TREVOR-Intel-Brief/3.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
    except Exception as e:
        log(f"  Download failed: {e}")
        return None
    cache_path.write_text(json.dumps(data))
    log(f"  Cached {name} ({len(data.get('features',[]))} features)")
    return data


def point_in_bbox(lon, lat, bbox):
    """Check if point is within bbox (with margin)."""
    min_lon, min_lat, max_lon, max_lat = bbox
    margin_lon = (max_lon - min_lon) * 0.05
    margin_lat = (max_lat - min_lat) * 0.05
    return (min_lon - margin_lon <= lon <= max_lon + margin_lon and
            min_lat - margin_lat <= lat <= max_lat + margin_lat)


def clip_geojson_to_bbox(fc, bbox):
    """Fast clip: filter features whose centroid is roughly in bbox."""
    if not fc or "features" not in fc:
        return fc
    min_lon, min_lat, max_lon, max_lat = bbox
    margin = 5  # degrees margin
    def in_bbox(f):
        coords = f.get("geometry", {}).get("coordinates", [[]])
        # Check a sample point
        if f["geometry"]["type"] == "Polygon":
            ring = coords[0]
            for pt in ring:
                if min_lon - margin <= pt[0] <= max_lon + margin and min_lat - margin <= pt[1] <= max_lat + margin:
                    return True
        elif f["geometry"]["type"] == "MultiPolygon":
            for poly in coords:
                for ring in poly:
                    for pt in ring:
                        if min_lon - margin <= pt[0] <= max_lon + margin and min_lat - margin <= pt[1] <= max_lat + margin:
                            return True
        return False
    filtered = [f for f in fc["features"] if in_bbox(f)]
    return {"type": "FeatureCollection", "features": filtered}


def draw_polygon(ax, coords, color, alpha, linewidth=0.3):
    """Draw a single polygon from coordinate list."""
    import matplotlib.patches as mpatches
    xs = [p[0] for p in coords]
    ys = [p[1] for p in coords]
    poly = mpatches.Polygon(list(zip(xs, ys)), closed=True,
                            facecolor=color, edgecolor=color, alpha=alpha,
                            linewidth=linewidth)
    ax.add_patch(poly)


def draw_geometry(ax, geom, color="#1a2a4a", alpha=0.8, linewidth=0.2, fill=True):
    """Draw a GeoJSON geometry."""
    if geom["type"] == "Polygon":
        coords = geom["coordinates"][0]
        if fill:
            draw_polygon(ax, coords, color, alpha, linewidth)
    elif geom["type"] == "MultiPolygon":
        for poly in geom["coordinates"]:
            coords = poly[0]
            if fill:
                draw_polygon(ax, coords, color, alpha, linewidth)


def render_theatre_map(
    region, land_data, theatre_data, out_path, width=1600, height=1200, dpi=150
):
    """Render one theatre map with overlays."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np

    cfg = REGION_MAPS.get(region, REGION_MAPS["global_finance"])
    bbox = cfg["bbox"]
    min_lon, min_lat, max_lon, max_lat = bbox

    fig_w = width / dpi
    fig_h = height / dpi
    fig, ax = plt.subplots(1, 1, figsize=(fig_w, fig_h), dpi=dpi)
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(BG_MID)

    # Clip land data to bbox
    clipped = clip_geojson_to_bbox(land_data, bbox) if land_data else None

    # Draw land polygons
    if clipped and "features" in clipped:
        for feat in clipped["features"]:
            geom = feat.get("geometry", {})
            draw_geometry(ax, geom, color=cfg["land_color"], alpha=1.0, linewidth=0.1)

    # Draw theatre data overlays (cities, zones, routes)
    td = theatre_data.get(region, {}) if theatre_data else {}

    # 1. Conflict zones (shaded polygons)
    zones = td.get("conflict_zones", [])
    for zone in zones:
        coords = zone.get("coordinates", [])
        zone_color = zone.get("color", RED)
        zone_label = zone.get("label", "")
        if coords:
            draw_polygon(ax, coords, zone_color, 0.15, linewidth=0.8)
            # Add cross-hatch pattern border
            draw_polygon(ax, coords, zone_color, 0.0, linewidth=1.2)
            # Label center
            cx = sum(p[0] for p in coords) / len(coords)
            cy = sum(p[1] for p in coords) / len(coords)
            ax.text(cx, cy, zone_label, fontsize=5.5, color=zone_color,
                    ha="center", va="center", fontweight="bold",
                    style="italic", alpha=0.9)

    # 2. Route lines (colored polylines)
    routes = td.get("routes", [])
    for route in routes:
        coords = route.get("coordinates", [])
        route_color = route.get("color", ORANGE)
        route_style = route.get("style", "-")
        linewidth = route.get("linewidth", 2.5)
        if coords:
            xs = [p[0] for p in coords]
            ys = [p[1] for p in coords]
            ax.plot(xs, ys, color=route_color, linewidth=linewidth,
                    linestyle=route_style, alpha=0.8, zorder=5)
            # Arrow at midpoint
            if len(coords) >= 3:
                mid = len(coords) // 2
                dx = coords[min(mid+1, len(coords)-1)][0] - coords[mid][0]
                dy = coords[min(mid+1, len(coords)-1)][1] - coords[mid][1]
                angle = math.degrees(math.atan2(dy, dx))
                ax.annotate("", xy=coords[mid], xytext=(coords[mid][0]-dx*0.1, coords[mid][1]-dy*0.1),
                           arrowprops=dict(arrowstyle="->", color=route_color, lw=1.5),
                           zorder=6)

    # 3. City/strategic markers
    cities = td.get("cities", [])
    for city in cities:
        lon, lat = city.get("lon", 0), city.get("lat", 0)
        name = city.get("name", "")
        marker_color = city.get("color", BLUE)
        marker_size = city.get("size", 60)
        marker_type = city.get("marker", "o")
        if not point_in_bbox(lon, lat, bbox):
            continue
        ax.scatter(lon, lat, s=marker_size, c=marker_color, marker=marker_type,
                   edgecolors=WHITE, linewidth=0.6, zorder=10, alpha=0.9)
        # Label offset: alternate sides based on latitude to reduce overlap
        x_off = 0.4 if lat > (min_lat + max_lat) / 2 else -0.4
        y_off = -0.4 if abs(lon - (min_lon + max_lon) / 2) > 10 else 0.4
        ax.text(lon + x_off, lat + y_off, name, fontsize=5.5, color=WHITE,
                ha="left" if x_off > 0 else "right", va="top" if y_off < 0 else "bottom",
                fontweight="bold", zorder=11)

    # 4. Labels for key geographic features
    features = td.get("features", [])
    for feat in features:
        lon, lat = feat.get("lon", 0), feat.get("lat", 0)
        name = feat.get("name", "")
        feat_color = feat.get("color", LGRAY)
        if point_in_bbox(lon, lat, bbox):
            ax.text(lon, lat, name, fontsize=5, color=feat_color,
                    ha="center", va="bottom", alpha=0.7, zorder=3)

    # Set map bounds with padding
    pad_lon = (max_lon - min_lon) * 0.06
    pad_lat = (max_lat - min_lat) * 0.06
    # Extra top padding for title bar
    ax.set_xlim(min_lon - pad_lon, max_lon + pad_lon)
    ax.set_ylim(min_lat - pad_lat - (max_lat - min_lat) * 0.04,
                max_lat + pad_lat + (max_lat - min_lat) * 0.03)

    # Grid lines (subtle)
    ax.grid(True, color=cfg["grid_color"], linewidth=0.3, alpha=0.4)
    # HIDE axis labels and ticks — purely geographical, no lat/lon clutter
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.tick_params(which='both', length=0, pad=0, labelsize=0, colors=cfg["grid_color"])

    # ── TITLE BAR (overlaid in plot space, top-center) ──
    date_str = dt.date.today().strftime("%d %b %Y")
    title_text = f"{cfg['label']} — Theatre Overview"
    ax.text(0.5, 0.98, title_text, transform=ax.transAxes, fontsize=12,
            color=GOLD, fontweight="bold", ha="center", va="top",
            fontfamily="sans-serif")
    ax.text(0.5, 0.935, f"TREVOR INTELLIGENCE · {date_str}",
            transform=ax.transAxes, fontsize=5.5, color=LGRAY,
            ha="center", va="top", fontfamily="sans-serif")

    # Spines
    for spine in ax.spines.values():
        spine.set_color(cfg["grid_color"])
        spine.set_linewidth(0.5)

    # ── LEGEND (compact, readable, bottom-right) ──
    legend_handles = []
    if zones:
        legend_handles.append(mpatches.Patch(facecolor=RED, alpha=0.2,
                                              edgecolor=RED, linewidth=1,
                                              label="Conflict"))
    if routes:
        legend_handles.append(plt.Line2D([0], [0], color=ORANGE, linewidth=2.5,
                                          label="Route"))
    legend_handles.append(plt.Line2D([0], [0], marker='o', color='w',
                                      markerfacecolor=BLUE, markersize=7,
                                      label="City"))
    legend_handles.append(plt.Line2D([0], [0], marker='o', color='w',
                                      markerfacecolor=RED, markersize=7,
                                      label="Incident"))
    if legend_handles:
        leg = ax.legend(handles=legend_handles, loc="lower right",
                        fontsize=6.5, framealpha=0.85,
                        facecolor=BG_MID, edgecolor=GOLD,
                        labelcolor=WHITE, markerscale=0.7, ncol=4,
                        columnspacing=10)
        leg.get_frame().set_linewidth(0.5)

    # TREVOR watermark
    ax.text(0.99, 0.01, "TREVOR", transform=ax.transAxes, fontsize=8,
            color=GOLD, alpha=0.25, ha="right", va="bottom",
            fontweight="bold", fontfamily="sans-serif")

    fig.savefig(str(out_path), dpi=dpi, bbox_inches="tight",
                facecolor=BG_DARK, edgecolor="none")
    plt.close(fig)
    return out_path.stat().st_size > 5000


def load_theatre_data(geojson_path):
    """Load theatre-specific GeoJSON overlay data from file."""
    if not geojson_path or not os.path.exists(geojson_path):
        log("  No theatre GeoJSON data file — using defaults")
        return None
    try:
        data = json.loads(pathlib.Path(geojson_path).read_text())
        log(f"  Loaded theatre GeoJSON data: {len(data)} regions")
        return data
    except Exception as e:
        log(f"  Failed to load theatre data: {e}")
        return None


def generate_default_theatre_data():
    """Generate theatre GeoJSON data from today's analysis JSON files."""
    # This is populated from the analysis data when available
    return {}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--geojson-data", default=None,
                        help="Path to theatre GeoJSON overlays file")
    parser.add_argument("--width", type=int, default=1600)
    parser.add_argument("--height", type=int, default=1200)
    parser.add_argument("--dpi", type=int, default=150)
    args = parser.parse_args()

    out_dir = pathlib.Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = out_dir / "_cache"
    cache_dir.mkdir(exist_ok=True)

    # Load theatre GeoJSON overlays
    theatre_data = load_theatre_data(args.geojson_data)

    # Download Natural Earth basemap
    log("Loading Natural Earth basemap...")
    land_data = fetch_geo(NE_LAND, cache_dir)

    regions = ["europe", "asia", "middle_east", "north_america",
               "south_central_america", "global_finance"]
    success = 0

    for region in regions:
        out_path = out_dir / f"map_{region}.png"
        log(f"Rendering {region}...")
        if render_theatre_map(region, land_data, theatre_data, out_path,
                               args.width, args.height, args.dpi):
            success += 1
            log(f"  ✅ {out_path.name} ({out_path.stat().st_size // 1024} KB)")
        else:
            log(f"  ❌ {out_path.name} failed")

    # Manifest
    manifest = []
    for f in sorted(out_dir.glob("map_*.png")):
        if f.name.startswith("map_"):
            manifest.append({
                "region": f.stem.replace("map_", ""),
                "path": str(f),
                "size_kb": f.stat().st_size // 1024,
            })
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    log(f"Done: {success}/{len(regions)} maps")

    if not theatre_data:
        log("\n⚠️  No theatre GeoJSON data loaded. Maps will show only basemap.")
        log("   Create a GeoJSON overlay file with cities, zones, routes.")
        log("   Example structure:")
        log('   { "europe": { "cities": [{"name":"Berlin","lon":13.4,"lat":52.5,"color":"#2c6aa0"}],')
        log('     "conflict_zones": [{"coordinates":[[...]],"label":"Donbas","color":"#c0392b"}],')
        log('     "routes": [{"coordinates":[[...]],"color":"#d47500"}] } }')

    return 0 if success > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
