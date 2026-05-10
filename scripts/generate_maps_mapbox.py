#!/usr/bin/env python3
"""
generate_maps_mapbox.py v2 — Theatre maps via Mapbox Static API.

Uses Mapbox dark-v11 style with:
- Auto-fitted viewports for each theatre's marker set
- Gold-accented markers for major cities
- Red markers for conflict zones/flashpoints
- @2x resolution (2560x2560 effective at 1280x1280)
- Country highlight overlays via marker clusters
- Graceful fallback to matplotlib

Style: mapbox/dark-v11 (matches our magazine's dark theme + gold accent)

Usage:
    python3 generate_maps_mapbox.py \
        --working-dir ~/trevor-briefings/2026-05-10 \
        --out-dir ~/trevor-briefings/2026-05-10/visuals/maps

Requires MAPBOX_TOKEN in environment.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

# ── Theatre map definitions ──
# Key cities with coordinates and types for each theatre
# type: "capital" (gold), "city" (gray), "flashpoint" (red)
THEATRES = {
    "europe": {
        "title": "Europe",
        "zoom": 4.5,
        "center": (50.0, 15.0),
        "bbox": (-10, 36, 40, 60),
        "markers": [
            ("pin-l-city+c9a84c", (52.52, 13.40)),   # Berlin
            ("pin-l-city+c9a84c", (48.86, 2.35)),    # Paris
            ("pin-l-city+c9a84c", (51.51, -0.13)),   # London
            ("pin-l-city+c9a84c", (55.76, 37.62)),   # Moscow
            ("pin-l-city+c9a84c", (50.45, 30.52)),   # Kyiv
            ("pin-l-city+c9a84c", (41.90, 12.50)),   # Rome
            ("pin-l-city+777", (59.33, 18.07)),   # Stockholm
            ("pin-l-danger+cc0000", (48.02, 37.80)),  # Donetsk
            ("pin-l-danger+cc0000", (48.45, 37.75)),  # Kramatorsk
        ],
    },
    "asia": {
        "title": "Asia",
        "zoom": 4.0,
        "center": (30.0, 85.0),
        "bbox": (60, 5, 130, 50),
        "markers": [
            ("pin-l-city+c9a84c", (39.91, 116.40)),  # Beijing
            ("pin-l-city+c9a84c", (35.68, 139.69)),  # Tokyo
            ("pin-l-city+c9a84c", (28.61, 77.23)),   # New Delhi
            ("pin-l-city+c9a84c", (25.03, 121.51)),  # Taipei
            ("pin-l-city+777", (33.68, 73.05)),   # Islamabad
            ("pin-l-city+c9a84c", (37.57, 126.98)),  # Seoul
            ("pin-l-city+c9a84c", (22.32, 114.17)),  # Hong Kong
            ("pin-l-danger+cc0000", (34.56, 69.21)),  # Kabul
        ],
    },
    "middle_east": {
        "title": "Middle East",
        "zoom": 5.0,
        "center": (28.0, 46.0),
        "bbox": (25, 12, 60, 42),
        "markers": [
            ("pin-l-city+c9a84c", (35.69, 51.42)),  # Tehran
            ("pin-l-city+c9a84c", (30.04, 31.24)),  # Cairo
            ("pin-l-city+c9a84c", (39.93, 32.86)),  # Ankara
            ("pin-l-city+777", (33.51, 36.29)),  # Damascus
            ("pin-l-city+c9a84c", (24.71, 46.67)),  # Riyadh
            ("pin-l-city+c9a84c", (32.08, 34.78)),  # Tel Aviv
            ("pin-l-danger+cc0000", (26.27, 56.03)),  # Strait of Hormuz
            ("pin-l-danger+cc0000", (33.32, 44.36)),  # Baghdad
            ("pin-l-danger+cc0000", (15.35, 44.21)),  # Sanaa
        ],
    },
    "north_america": {
        "title": "North America",
        "zoom": 4.0,
        "center": (32.0, -100.0),
        "bbox": (-130, 15, -60, 50),
        "markers": [
            ("pin-l-city+c9a84c", (38.91, -77.04)),  # Washington DC
            ("pin-l-city+c9a84c", (40.71, -74.01)),  # New York
            ("pin-l-city+777", (34.05, -118.24)), # Los Angeles
            ("pin-l-city+c9a84c", (25.76, -80.19)),  # Miami
            ("pin-l-city+c9a84c", (19.43, -99.13)),  # Mexico City
            ("pin-l-danger+cc0000", (28.63, -106.07)), # Chihuahua
        ],
    },
    "south_central_america": {
        "title": "S. & C. America",
        "zoom": 4.0,
        "center": (-8.0, -60.0),
        "bbox": (-85, -35, -30, 25),
        "markers": [
            ("pin-l-danger+cc0000", (23.11, -82.37)),  # Havana (crisis)
            ("pin-l-city+c9a84c", (10.48, -66.90)),  # Caracas
            ("pin-l-city+c9a84c", (-23.55, -46.63)), # São Paulo
            ("pin-l-city+777", (-15.79, -47.88)), # Brasília
            ("pin-l-city+c9a84c", (-34.60, -58.38)), # Buenos Aires
            ("pin-l-city+c9a84c", (4.71, -74.07)),   # Bogotá
        ],
    },
    "global_finance": {
        "title": "Global Finance",
        "zoom": 2.5,
        "center": (25.0, 15.0),
        "bbox": (-130, -40, 150, 60),
        "markers": [
            ("pin-l-city+c9a84c", (40.71, -74.01)),  # NYSE
            ("pin-l-city+c9a84c", (51.51, -0.13)),   # London
            ("pin-l-city+c9a84c", (35.68, 139.69)),  # Tokyo
            ("pin-l-city+c9a84c", (22.28, 114.16)),  # Hong Kong
            ("pin-l-city+777", (1.28, 103.85)),   # Singapore
            ("pin-l-city+c9a84c", (50.11, 8.68)),    # Frankfurt
            ("pin-l-city+c9a84c", (48.86, 2.35)),    # Paris
            ("pin-l-danger+cc0000", (25.20, 55.27)),   # Dubai (Hormuz proximity)
        ],
    },
}

MAPBOX_BASE = "https://api.mapbox.com"

import matplotlib
import io
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None
    ImageDraw = None
    ImageFont = None

matplotlib.use("Agg")
import matplotlib.pyplot as plt

def log(msg: str) -> None:
    print(f"[maps] {msg}", file=sys.stderr, flush=True)


def make_marker_overlay(markers: list) -> str:
    """Build the overlay string for Mapbox static API.
    Use pin-l (large) markers with custom colors.
    Markers are semi-transparent to look professional."""
    parts = []
    for marker_spec, (lat, lng) in markers:
        parts.append(f"{marker_spec}({lng},{lat})")
    return ",".join(parts)


# Map label definitions: name -> (lat, lng, type)
# type: "capital" (gold label), "flashpoint" (red label), "city" (grey label)
MAP_LABELS = {
    "europe": {
        "Berlin": (52.52, 13.40, "capital"),
        "Paris": (48.86, 2.35, "capital"),
        "London": (51.51, -0.13, "capital"),
        "Moscow": (55.76, 37.62, "capital"),
        "Kyiv": (50.45, 30.52, "capital"),
        "Rome": (41.90, 12.50, "city"),
        "Stockholm": (59.33, 18.07, "city"),
        "Donetsk": (48.02, 37.80, "flashpoint"),
        "Kramatorsk": (48.45, 37.75, "flashpoint"),
    },
    "asia": {
        "Beijing": (39.91, 116.40, "capital"),
        "Tokyo": (35.68, 139.69, "capital"),
        "New Delhi": (28.61, 77.23, "capital"),
        "Taipei": (25.03, 121.51, "city"),
        "Islamabad": (33.68, 73.05, "city"),
        "Seoul": (37.57, 126.98, "city"),
        "Hong Kong": (22.32, 114.17, "city"),
        "Kabul": (34.56, 69.21, "flashpoint"),
    },
    "middle_east": {
        "Tehran": (35.69, 51.42, "capital"),
        "Cairo": (30.04, 31.24, "capital"),
        "Ankara": (39.93, 32.86, "capital"),
        "Damascus": (33.51, 36.29, "city"),
        "Riyadh": (24.71, 46.67, "capital"),
        "Tel Aviv": (32.08, 34.78, "city"),
        "Strait of Hormuz": (26.27, 56.03, "flashpoint"),
        "Baghdad": (33.32, 44.36, "flashpoint"),
        "Sanaa": (15.35, 44.21, "flashpoint"),
    },
    "north_america": {
        "Washington": (38.91, -77.04, "capital"),
        "New York": (40.71, -74.01, "capital"),
        "Los Angeles": (34.05, -118.24, "city"),
        "Miami": (25.76, -80.19, "city"),
        "Mexico City": (19.43, -99.13, "capital"),
        "Chihuahua": (28.63, -106.07, "flashpoint"),
    },
    "south_central_america": {
        "Havana": (23.11, -82.37, "flashpoint"),
        "Caracas": (10.48, -66.90, "capital"),
        "São Paulo": (-23.55, -46.63, "city"),
        "Brasília": (-15.79, -47.88, "capital"),
        "Buenos Aires": (-34.60, -58.38, "city"),
        "Bogotá": (4.71, -74.07, "capital"),
    },
    "global_finance": {
        "NYSE": (40.71, -74.01, "capital"),
        "London": (51.51, -0.13, "capital"),
        "Tokyo": (35.68, 139.69, "capital"),
        "Hong Kong": (22.28, 114.16, "capital"),
        "Singapore": (1.28, 103.85, "city"),
        "Frankfurt": (50.11, 8.68, "city"),
        "Paris": (48.86, 2.35, "city"),
        "Dubai": (25.20, 55.27, "city"),
    },
}


def latlng_to_px(lat: float, lng: float, center_lat: float, center_lng: float, zoom: float, img_w: int, img_h: int) -> tuple[int, int]:
    """Convert lat/lng to pixel coordinates on a Web Mercator map image."""
    import math
    # Web Mercator projection
    def merc_x(l): return (l + 180) / 360
    def merc_y(l):
        lat_rad = math.radians(l)
        return 0.5 - math.log(math.tan(math.pi/4 + lat_rad/2)) / (2 * math.pi)
    
    # Center pixel
    cx = merc_x(center_lng) * img_w
    cy = merc_y(center_lat) * img_h
    
    # Point pixel
    px = merc_x(lng) * img_w
    py = merc_y(lat) * img_h
    
    # Zoom scale factor (each zoom level halves the visible world)
    scale = 2 ** zoom
    
    # Convert to image coordinates
    x = int(img_w/2 + (px - cx) * scale)
    y = int(img_h/2 + (py - cy) * scale)
    return (x, y)


def add_labels_to_map(image_data: bytes, markers: list, region: str, theatre: dict) -> bytes | None:
    """Add text labels to a Mapbox static map image using PIL."""
    if Image is None:
        return None
    try:
        img = Image.open(io.BytesIO(image_data)).convert("RGBA")
        img_w, img_h = img.size
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Try to load a font, fall back to default
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except Exception:
            font_large = ImageFont.load_default()
            font_small = font_large
        
        labels = MAP_LABELS.get(region, {})
        center_lat, center_lng = theatre["center"]
        zoom = theatre["zoom"]
        
        for name, (lat, lng, ltype) in labels.items():
            px, py = latlng_to_px(lat, lng, center_lat, center_lng, zoom, img_w, img_h)
            
            # Skip if outside image bounds
            if px < -50 or px > img_w + 50 or py < -50 or py > img_h + 50:
                continue
            
            if ltype == "flashpoint":
                # Red glow circle + red label
                for r in range(20, 5, -5):
                    alpha = 40 if r > 10 else 180
                    draw.ellipse([px-r, py-r, px+r, py+r], fill=(204, 0, 0, alpha))
                draw.ellipse([px-6, py-6, px+6, py+6], fill=(204, 0, 0, 220))
                # White text label below marker
                bbox = draw.textbbox((0, 0), name, font=font_small)
                tw = bbox[2] - bbox[0]
                tx = px - tw // 2
                ty = py + 12
                # Background pill for readability
                draw.rounded_rectangle([tx-4, ty-2, tx+tw+4, ty+18], radius=3, fill=(0, 0, 0, 160))
                draw.text((tx, ty), name, fill=(255, 255, 255, 240), font=font_large)
            elif ltype == "capital":
                # Gold circle marker
                draw.ellipse([px-5, py-5, px+5, py+5], fill=(212, 168, 67, 220))
                draw.ellipse([px-3, py-3, px+3, py+3], fill=(255, 215, 0, 200))
                # Gold label
                bbox = draw.textbbox((0, 0), name, font=font_small)
                tw = bbox[2] - bbox[0]
                tx = px - tw // 2
                ty = py + 10
                draw.rounded_rectangle([tx-3, ty-1, tx+tw+3, ty+17], radius=2, fill=(0, 0, 0, 140))
                draw.text((tx, ty), name, fill=(212, 168, 67, 240), font=font_small)
            else:
                # Grey dot for other cities
                draw.ellipse([px-3, py-3, px+3, py+3], fill=(150, 150, 150, 180))
                bbox = draw.textbbox((0, 0), name, font=font_small)
                tw = bbox[2] - bbox[0]
                tx = px - tw // 2
                ty = py + 10
                draw.text((tx, ty), name, fill=(180, 180, 180, 180), font=font_small)
        
        # Add legend
        legend_x, legend_y = 15, img_h - 80
        draw.rounded_rectangle([legend_x, legend_y, legend_x + 155, legend_y + 70], radius=4, fill=(0, 0, 0, 160))
        draw.text((legend_x + 8, legend_y + 6), "LEGEND", fill=(212, 168, 67, 200), font=font_small)
        draw.ellipse([legend_x + 8, legend_y + 28, legend_x + 16, legend_y + 36], fill=(212, 168, 67, 220))
        draw.text((legend_x + 22, legend_y + 25), "Capital / Key City", fill=(200, 200, 200, 200), font=font_small)
        draw.ellipse([legend_x + 8, legend_y + 48, legend_x + 16, legend_y + 56], fill=(204, 0, 0, 220))
        draw.text((legend_x + 22, legend_y + 45), "Conflict / Flashpoint", fill=(255, 200, 200, 200), font=font_small)
        
        img = Image.alpha_composite(img, overlay)
        output = io.BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()
    except Exception as e:
        log(f"  Label overlay failed: {e}")
        return None


def fetch_mapbox_static(region: str, out_path: pathlib.Path, token: str) -> bool:
    """Fetch a professional static map from Mapbox dark-v11 style."""
    theatre = THEATRES.get(region)
    if not theatre:
        return False

    markers = theatre["markers"]
    overlay = make_marker_overlay(markers)

    # Use auto positioning with padding to fit all markers
    # Max dimensions: 1280x1280 @2x = 2560x2560 effective
    width, height = 1280, 1280
    style = "mapbox/dark-v11"

    # Build URL: use specific center + zoom for a clearer, more focused map
    lat, lng = theatre["center"]
    z = theatre["zoom"]
    # Rectangle aspect ratio: 800x500 fits better on a page
    w, h = 800, 500
    
    url = (
        f"{MAPBOX_BASE}/styles/v1/{style}/static"
        f"/{overlay}/{lng},{lat},{z},0,0"
        f"/{w}x{h}@2x"
        f"?access_token={token}"
        f"&logo=false"
        f"&attribution=true"
    )

    log(f"  Fetching Mapbox {region} map ({w}x{h}@2x)...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TREVOR-Intel-Brief/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        if len(data) < 2000:
            log(f"  Mapbox response too small: {len(data)} bytes")
            return False
        # Enhance map with text labels using PIL
        enhanced = add_labels_to_map(data, markers, region, theatre)
        if enhanced:
            out_path.write_bytes(enhanced)
        else:
            out_path.write_bytes(data)
        kb = out_path.stat().st_size // 1024
        log(f"  ✅ Mapbox {region}: {out_path.name} ({kb} KB)")
        return True
    except urllib.error.HTTPError as e:
        log(f"  Mapbox HTTP {e.code}: {e.read().decode(errors='replace')[:200]}")
        return False
    except Exception as e:
        log(f"  Mapbox error: {e}")
        return False


def render_matplotlib_fallback(region: str, out_path: pathlib.Path) -> bool:
    """Fallback: matplotlib with improved styling."""
    theatre = THEATRES.get(region)
    if not theatre:
        return False

    try:
        fig, ax = plt.subplots(figsize=(10, 10), dpi=150)
        ax.set_facecolor("#0d1b3e")
        fig.patch.set_facecolor("#0d1b3e")

        # Calculate bounds from markers
        all_lats = [m[1][0] for m in theatre["markers"]]
        all_lngs = [m[1][1] for m in theatre["markers"]]
        margin = 8
        min_lat, max_lat = min(all_lats) - margin, max(all_lats) + margin
        min_lng, max_lng = min(all_lngs) - margin, max(all_lngs) + margin

        ax.set_xlim(min_lng, max_lng)
        ax.set_ylim(min_lat, max_lat)

        # Grid
        ax.grid(True, color="#2a3a6e", linewidth=0.5, alpha=0.4)
        ax.tick_params(colors="#555", labelsize=6)

        # Plot markers
        for spec, (lat, lng) in theatre["markers"]:
            if "danger" in spec or "cc0000" in spec:
                ax.plot(lng, lat, "o", color="#cc0000", markersize=10, zorder=5)
                ax.annotate("⚠", (lng, lat), fontsize=8,
                           ha="center", va="center", color="white", zorder=6)
            else:
                ax.plot(lng, lat, "o", color="#c9a84c", markersize=8, zorder=5,
                       markeredgecolor="white", markeredgewidth=0.5)

        # Title
        ax.set_title(theatre["title"], fontsize=14, color="#c9a84c",
                    fontweight="bold", pad=12)

        for spine in ax.spines.values():
            spine.set_color("#c9a84c")
            spine.set_linewidth(0.3)

        ax.text(0.5, -0.04, f"TREVOR INTELLIGENCE • {dt.date.today().strftime('%d %b %Y')}",
                transform=ax.transAxes, fontsize=7, color="#666",
                ha="center", va="center")

        fig.savefig(str(out_path), dpi=150, bbox_inches="tight",
                    facecolor="#0d1b3e", edgecolor="none")
        plt.close(fig)
        kb = out_path.stat().st_size // 1024
        log(f"  matplotlib fallback: {out_path.name} ({kb} KB)")
        return kb > 10
    except Exception as e:
        log(f"  matplotlib error: {e}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--no-mapbox", action="store_true",
                        help="Skip Mapbox, use matplotlib only")
    args = parser.parse_args()

    out_dir = pathlib.Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    token = os.environ.get("MAPBOX_TOKEN", "")
    use_mapbox = bool(token) and not args.no_mapbox

    if use_mapbox:
        log(f"Mapbox token found: {token[:10]}... — using Mapbox Static API")
    else:
        log("No MAPBOX_TOKEN — using matplotlib fallback")

    regions = ["europe", "asia", "middle_east", "north_america",
               "south_central_america", "global_finance"]
    success = 0

    for region in regions:
        out_path = out_dir / f"map_{region}.png"
        rendered = False

        if use_mapbox:
            rendered = fetch_mapbox_static(region, out_path, token)

        if not rendered:
            rendered = render_matplotlib_fallback(region, out_path)

        if rendered:
            success += 1

    # Write manifest
    manifest = []
    for f in sorted(out_dir.glob("map_*.png")):
        manifest.append({
            "region": f.stem.replace("map_", ""),
            "path": str(f),
            "size_kb": f.stat().st_size // 1024,
        })
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    log(f"\nGenerated {success}/{len(regions)} maps in {out_dir}")
    for m in manifest:
        log(f"  {m['region']}: {m['size_kb']} KB")
    return 0 if success > 0 else 1


if __name__ == "__main__":
    main()
