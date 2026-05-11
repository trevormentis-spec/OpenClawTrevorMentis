#!/usr/bin/env python3
"""
generate_maps_mapbox.py v6 — Data-driven maps via Mapbox GeoJSON overlay.

Each theatre's routes, zones, and cities are passed as a GeoJSON FeatureCollection
to the Mapbox Static API, which renders them at the correct geographic positions.
No PIL pixel-math needed — Mapbox handles all coordinate conversion.

Usage:
    python3 generate_maps_mapbox.py \
        --working-dir ~/trevor-briefings/2026-05-10 \
        --out-dir ~/trevor-briefings/2026-05-10/visuals/maps
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import pathlib
import sys
import urllib.parse
import urllib.request

MAPBOX_BASE = "https://api.mapbox.com"
STYLE = "streets-v12"

# ── Map configuration: fixed zoom/center per theatre ──
MAP_CONFIG = {
    "europe":              {"center": (52.0, 20.0), "zoom": 4.0},
    "asia":                {"center": (30.0, 85.0), "zoom": 3.5},
    "middle_east":         {"center": (28.0, 48.0), "zoom": 4.5},
    "north_america":       {"center": (30.0, -95.0), "zoom": 3.5},
    "south_central_america":{"center": (-5.0, -60.0), "zoom": 3.5},
    "global_finance":      {"center": (30.0, 30.0), "zoom": 2.5},
}

# ── Thematic geographic data per theatre ──
THEATRE_DATA = {
    "europe": {
        "title": "Europe — Strikes, Drawdown, and Watch",
        "lines": [
            {"coords": [[34.0, 50.0], [32.5, 49.5]], "color": "#cc0000", "width": 3, "label": "108 drones + 2 Iskander-M + 1 Kh-31"},
            {"coords": [[8.0, 49.5], [4.5, 52.0]], "color": "#1e3caf", "width": 3, "label": "5,000-troop withdrawal"},
            {"coords": [[27.5, 53.5], [30.0, 50.0]], "color": "#b37400", "width": 2, "label": "Belarus transit facilitation", "dash": [4, 6]},
            {"coords": [[8.0, 49.5], [21.0, 52.0]], "color": "#3c78d8", "width": 2, "label": "Reinforcement corridor ~1,100 km", "dash": [6, 4]},
        ],
        "zones": [
            {"coords": [[28.0, 50.0], [33.0, 50.0], [33.0, 47.5], [28.0, 47.5]], "color": "#cc0000", "fill_opacity": 0.12, "label": "Ukraine strike zone"},
        ],
        "cities": [
            ("Kyiv", 50.45, 30.52, "target"), ("Berlin", 52.52, 13.40, "capital"),
            ("Donetsk", 48.02, 37.80, "target"), ("Warsaw", 52.23, 21.01, "nato"),
            ("Moscow", 55.76, 37.62, "source"), ("Minsk", 53.90, 27.57, "warning"),
        ],
    },
    "asia": {
        "title": "Asia — Pre-Summit Positioning",
        "lines": [
            {"coords": [[77.23, 28.61], [73.05, 33.68]], "color": "#b37400", "width": 2, "label": "India-Pakistan diplomatic friction", "dash": [4, 6]},
            {"coords": [[85.0, 20.0], [95.0, 20.0]], "color": "#1e3caf", "width": 2, "label": "Maritime security patrols", "dash": [6, 4]},
        ],
        "zones": [
            {"coords": [[69.0, 35.5], [72.0, 35.5], [72.0, 33.0], [69.0, 33.0]], "color": "#cc0000", "fill_opacity": 0.12, "label": "Afghanistan security zone"},
        ],
        "cities": [
            ("Beijing", 39.91, 116.40, "capital"), ("Tokyo", 35.68, 139.69, "capital"),
            ("New Delhi", 28.61, 77.23, "capital"), ("Seoul", 37.57, 126.98, "capital"),
            ("Taipei", 25.03, 121.57, "flashpoint"), ("Kabul", 34.56, 69.21, "target"),
        ],
    },
    "middle_east": {
        "title": "Middle East — The Hormuz Toll Trap",
        "lines": [
            {"coords": [[55.0, 27.0], [56.0, 26.5], [56.5, 26.0]], "color": "#38761d", "width": 3, "label": "Inbound shipping lane"},
            {"coords": [[56.5, 26.5], [56.0, 27.0], [55.5, 27.3]], "color": "#38761d", "width": 3, "label": "Outbound shipping lane"},
            {"coords": [[56.27, 27.18], [56.25, 26.57]], "color": "#cc0000", "width": 3, "label": "Toll demand 6 May — rial/OFAC trap"},
            {"coords": [[47.0, 29.0], [51.0, 30.0]], "color": "#b37400", "width": 2, "label": "IAF strike range arc", "dash": [4, 8]},
        ],
        "zones": [
            {"coords": [[55.5, 27.0], [57.0, 27.0], [57.0, 25.5], [55.5, 25.5]], "color": "#cc0000", "fill_opacity": 0.18, "label": "HORMUZ — 33 km chokepoint"},
        ],
        "cities": [
            ("Tehran", 35.69, 51.42, "capital"), ("Bandar Abbas", 27.18, 56.27, "military"),
            ("Hormuz", 26.57, 56.25, "chokepoint"), ("Bahrain (5th Fleet)", 26.22, 50.58, "base"),
            ("Baghdad", 33.32, 44.36, "capital"), ("Sanaa", 15.35, 44.21, "target"),
        ],
    },
    "north_america": {
        "title": "North America — Substitution & Security",
        "lines": [
            {"coords": [[-95.37, 29.76], [-66.90, 10.48]], "color": "#38761d", "width": 3, "label": "1.23M bpd Venezuelan crude → USGC"},
            {"coords": [[-106.07, 28.63], [-77.04, 38.91]], "color": "#cc0000", "width": 3, "label": "Chihuahua incident — 2x CIA fatalities"},
        ],
        "zones": [
            {"coords": [[-107.5, 30.0], [-105.0, 30.0], [-105.0, 27.0], [-107.5, 27.0]], "color": "#cc0000", "fill_opacity": 0.12, "label": "Chihuahua cartel corridor"},
            {"coords": [[-97.0, 30.5], [-88.0, 30.5], [-88.0, 27.5], [-97.0, 27.5]], "color": "#38761d", "fill_opacity": 0.08, "label": "Gulf Coast refining ~9M bpd capacity"},
        ],
        "cities": [
            ("Washington", 38.91, -77.04, "capital"), ("Mexico City", 19.43, -99.13, "capital"),
            ("Chihuahua", 28.63, -106.07, "flashpoint"), ("Houston", 29.76, -95.37, "hub"),
        ],
    },
    "south_central_america": {
        "title": "S. & C. America — Sanctions & Flooding",
        "lines": [
            {"coords": [[-77.04, 38.91], [-82.37, 23.11]], "color": "#cc0000", "width": 3, "label": "New US sanctions: energy, defence, mining"},
            {"coords": [[-66.90, 10.48], [-82.37, 23.11]], "color": "#b37400", "width": 2, "label": "Venezuelan oil — under pressure", "dash": [4, 6]},
        ],
        "zones": [
            {"coords": [[-84.0, 24.5], [-80.0, 24.5], [-80.0, 21.5], [-84.0, 21.5]], "color": "#cc0000", "fill_opacity": 0.12, "label": "Cuba — acute energy distress"},
            {"coords": [[-36.0, -6.0], [-34.0, -6.0], [-34.0, -9.0], [-36.0, -9.0]], "color": "#1c6dc9", "fill_opacity": 0.12, "label": "Pernambuco/Paraiba — 6+ dead"},
        ],
        "cities": [
            ("Havana", 23.11, -82.37, "capital"), ("Caracas", 10.48, -66.90, "capital"),
            ("Brasilia", -15.79, -47.88, "capital"), ("Recife", -8.05, -34.88, "disaster"),
        ],
    },
    "global_finance": {
        "title": "Global Finance — Energy Re-routing",
        "lines": [
            {"coords": [[56.25, 26.57], [38.06, 24.09]], "color": "#38761d", "width": 3, "label": "Petroline bypass: ~4.8M bpd capacity"},
            {"coords": [[52.87, 25.15], [56.34, 25.13]], "color": "#38761d", "width": 2, "label": "Habshan-Fujairah bypass pipeline"},
        ],
        "zones": [
            {"coords": [[55.0, 27.5], [57.5, 27.5], [57.5, 25.0], [55.0, 25.0]], "color": "#cc0000", "fill_opacity": 0.18, "label": "Hormuz chokepoint — ~20M bpd transit"},
        ],
        "cities": [
            ("London (BP)", 51.51, -0.13, "capital"), ("NYC (Chevron)", 40.71, -74.01, "capital"),
            ("Tokyo", 35.68, 139.69, "capital"), ("Hong Kong", 22.28, 114.16, "capital"),
            ("Hormuz", 26.57, 56.25, "chokepoint"), ("Dubai", 25.20, 55.27, "hub"),
        ],
    },
}


def log(msg):
    print(f"[maps] {msg}", file=sys.stderr, flush=True)


def build_geojson(region) -> dict:
    """Build a GeoJSON FeatureCollection for a theatre."""
    data = THEATRE_DATA.get(region, {})
    features = []

    # Helper: create a marker point
    def make_point(lng, lat, color, size="l", label=""):
        props = {"marker-color": color, "marker-size": size}
        if label:
            props["marker-symbol"] = label
        return {"type": "Feature", "properties": props,
                "geometry": {"type": "Point", "coordinates": [lng, lat]}}

    # Helper: create a line
    def make_line(coords, color, width, opacity=0.8, dash=None):
        props = {"stroke": color, "stroke-width": width, "stroke-opacity": opacity}
        if dash:
            props["stroke-dasharray"] = dash  # list, e.g. [4,6]
        return {"type": "Feature", "properties": props,
                "geometry": {"type": "LineString", "coordinates": coords}}

    # Helper: create a polygon (auto-closes the ring)
    def make_poly(coords, fill_color, fill_opacity, stroke_color="#666", stroke_width=1):
        # Ensure ring is closed
        ring = list(coords)
        if ring and len(ring) > 1 and (ring[0][0] != ring[-1][0] or ring[0][1] != ring[-1][1]):
            ring.append(ring[0])
        return {"type": "Feature", "properties": {
                    "fill": fill_color, "fill-opacity": fill_opacity,
                    "stroke": stroke_color, "stroke-width": stroke_width, "stroke-opacity": 0.6},
                "geometry": {"type": "Polygon", "coordinates": [ring]}}

    # Routes as lines
    for line in data.get("lines", []):
        features.append(make_line(line["coords"], line["color"], line.get("width", 2),
                                  dash=line.get("dash")))

    # Zones as polygons
    for zone in data.get("zones", []):
        features.append(make_poly(zone["coords"], zone["color"], zone.get("fill_opacity", 0.12)))

    # Cities as markers
    for city in data.get("cities", []):
        name, lat, lng, role = city
        marker_color = {"capital": "#1e3caf", "target": "#cc0000", "source": "#cc0000",
                        "nato": "#3c78d8", "warning": "#b37400", "flashpoint": "#cc0000",
                        "chokepoint": "#cc0000", "military": "#6aa84f", "base": "#6aa84f",
                        "hub": "#6aa84f", "disaster": "#1c6dc9"}.get(role, "#666")
        features.append(make_point(lng, lat, marker_color, label="marker"))

    return {"type": "FeatureCollection", "features": features}


def draw_map(region, out_path, token):
    """Fetch Mapbox static image with GeoJSON overlay."""
    data = THEATRE_DATA.get(region)
    if not data:
        return False

    cfg = MAP_CONFIG.get(region, {"center": (30, 0), "zoom": 2})
    lat, lng = cfg["center"]
    z = cfg["zoom"]
    w, h = 800, 500

    geojson = build_geojson(region)
    geo_str = json.dumps(geojson, separators=(",", ":"))
    geo_enc = urllib.parse.quote(geo_str)

    overlay = f"geojson({geo_enc})"
    url = (
        f"{MAPBOX_BASE}/styles/v1/mapbox/{STYLE}/static"
        f"/{overlay}/{lng},{lat},{z},0,0/{w}x{h}@2x"
        f"?access_token={token}&logo=false&attribution=true"
    )

    log(f"  Fetching {region} ({w}x{h}@2x, {z=})...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TREVOR-Intel-Brief/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            map_data = resp.read()
        if len(map_data) < 2000:
            log(f"  Too small: {len(map_data)} bytes")
            return False
        out_path.write_bytes(map_data)
        kb = out_path.stat().st_size // 1024
        log(f"  ✅ {region}: {out_path.name} ({kb} KB, {len(url)} URL chars)")
        return True
    except urllib.error.HTTPError as e:
        err = e.read().decode(errors="replace")[:200]
        log(f"  HTTP {e.code}: {err}")
        return False
    except Exception as e:
        log(f"  Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    out_dir = pathlib.Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    token = os.environ.get("MAPBOX_TOKEN", "")
    if not token:
        log("No MAPBOX_TOKEN")
        return 1

    regions = ["europe", "asia", "middle_east", "north_america",
               "south_central_america", "global_finance"]

    for region in regions:
        log(f"Generating {region}...")
        out_path = out_dir / f"map_{region}.png"
        draw_map(region, out_path, token)

    # Manifest
    manifest = []
    for f in sorted(out_dir.glob("map_*.png")):
        manifest.append({"region": f.stem.replace("map_", ""), "path": str(f), "size_kb": f.stat().st_size // 1024})
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    success = len([m for m in manifest if m["size_kb"] > 20])
    log(f"\nGenerated {success}/{len(regions)} maps")
    for m in manifest:
        log(f"  {m['region']}: {m['size_kb']} KB")


if __name__ == "__main__":
    main()
