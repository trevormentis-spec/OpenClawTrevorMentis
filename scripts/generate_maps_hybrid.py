#!/usr/bin/env python3
"""
generate_maps_hybrid.py — Hybrid Mapbox + PIL theatre maps.

Uses Mapbox Static API for a clean basemap (land/water/borders only),
then composites all operational intelligence data using PIL for full
typographic control — exactly as Opus described the maps should be.

Usage:
    python3 generate_maps_hybrid.py \
        --working-dir ~/trevor-briefings/2026-05-11 \
        --out-dir ~/trevor-briefings/2026-05-11/visuals/maps
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request
from PIL import Image, ImageDraw, ImageFont

# ── Mapbox ──
MAPBOX_BASE = "https://api.mapbox.com"
BASEMAP_STYLE = "light-v11"
MAP_CONFIG = {
    "europe":              {"center": (52.0, 20.0), "zoom": 3.3, "w": 1200, "h": 900},
    "asia":                {"center": (30.0, 85.0), "zoom": 3.0, "w": 1200, "h": 900},
    "middle_east":         {"center": (28.0, 48.0), "zoom": 4.2, "w": 1200, "h": 900},
    "north_america":       {"center": (30.0, -95.0), "zoom": 3.0, "w": 1200, "h": 900},
    "south_central_america":{"center": (-5.0, -60.0), "zoom": 3.0, "w": 1200, "h": 900},
    "global_finance":      {"center": (30.0, 30.0), "zoom": 2.2, "w": 1200, "h": 900},
}

# Brand colors
GOLD = (212, 168, 67)
NAVY = (15, 26, 48)
DARK = (8, 14, 26)
WHITE = (255, 255, 255)
RED = (192, 57, 43)
RED_LIGHT = (231, 76, 60)
BLUE = (44, 106, 160)
BLUE_LIGHT = (60, 138, 216)
GREEN = (58, 125, 68)
GREEN_LIGHT = (92, 184, 92)
ORANGE = (212, 117, 0)
TEAL = (43, 127, 140)
GRAY = (102, 102, 102)
LGRAY = (180, 190, 200)
CREAM = (245, 243, 238)

# ── Font loading ──
def get_font(size, bold=False):
    """Load font, fall back to default if unavailable."""
    try:
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)
    except:
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except:
            return ImageFont.load_default()

def log(msg):
    print(f"[hybrid] {msg}", file=sys.stderr, flush=True)

def lonlat_to_px(lon, lat, cfg, img_w, img_h):
    """Convert lon/lat to pixel coordinates on the image.
    cfg['center'] is (lat, lon) — we swap correctly here."""
    center_lat, center_lon = cfg["center"]
    zoom = cfg["zoom"]
    span_lon = 360.0 / (2 ** zoom)
    span_lon = max(span_lon, 3.0)
    span_lat = span_lon * (img_h / img_w)
    min_lon = center_lon - span_lon / 2
    max_lon = center_lon + span_lon / 2
    min_lat = center_lat - span_lat / 2
    max_lat = center_lat + span_lat / 2
    if max_lon == min_lon:
        max_lon = min_lon + 1
    if max_lat == min_lat:
        max_lat = min_lat + 1
    x = (lon - min_lon) / (max_lon - min_lon) * img_w
    y = (1 - (lat - min_lat) / (max_lat - min_lat)) * img_h
    return int(x), int(y)

def fetch_basemap(region, cfg, token):
    """Pure cream canvas — no basemap at all. Like Economist locator map."""
    w, h = cfg["w"] * 2, cfg["h"] * 2
    img = Image.new("RGBA", (w, h), (245, 243, 238, 255))
    return img

def draw_title(draw, cfg, region_label):
    """Economist-style title: thin top line, left-aligned, minimal."""
    w = cfg["w"] * 2
    # Thin gold top bar
    draw.rectangle([0, 0, w, 2], fill=GOLD)
    fnt_l = get_font(16, bold=True)
    fnt_s = get_font(8)
    today = dt.date.today().strftime("%d %b %Y")
    title = f"{region_label} — Theatre Overview"
    draw.text((16, 12), title, fill=DARK, font=fnt_l)
    draw.text((16, 34), f"TREVOR INTELLIGENCE  |  {today}", fill=GRAY, font=fnt_s)
    # Thin separator
    draw.rectangle([16, 50, w - 16, 51], fill=(220, 220, 220))

def draw_legend(draw, data, img_w, img_h):
    """Economist-style legend: minimalist key box, thin border."""
    items = []
    if data.get("lines"):
        items.append((RED, "line", "Conflict / Kinetic"))
        items.append((BLUE, "line", "Alliance / Corridor"))
        items.append((GREEN, "line", "Supply / Energy"))
        items.append((ORANGE, "line", "Assessed / Diplomatic"))
    if data.get("cities"):
        items.append((DARK, "dot", "Capital / Hub"))
        items.append((RED, "dot", "Incident / Flashpoint"))

    if not items:
        return

    fnt = get_font(8)
    item_h = 14
    pad = 8
    leg_w = 155
    leg_h = len(items) * item_h + pad * 2
    leg_x = img_w - leg_w - 14
    leg_y = img_h - leg_h - 14

    leg_img = Image.new("RGBA", (leg_w, leg_h), (255, 255, 255, 220))
    ld = ImageDraw.Draw(leg_img)

    iy = pad
    for color, kind, label in items:
        if kind == "line":
            ld.rectangle([6, iy + 3, 18, iy + 5], fill=color)
        else:
            ld.ellipse([9, iy + 1, 15, iy + 7], fill=color)
        ld.text((24, iy - 1), label, fill="#444", font=fnt)
        iy += item_h

    # Very thin border
    ld.rectangle([0, 0, leg_w - 1, leg_h - 1], outline="#ddd", width=1)
    return leg_img, leg_x, leg_y

def draw_cities(draw, cities, cfg, img_w, img_h):
    """Economist-style city markers: small dots, simple labels, no halo."""
    for city in cities:
        name, lat, lng, role = city
        px, py = lonlat_to_px(lng, lat, cfg, img_w, img_h)
        # Capital vs regular: square vs circle
        is_capital = role == "capital"
        dot_size = 5 if is_capital else 4
        # White outline
        draw.ellipse([px - dot_size - 1, py - dot_size - 1, px + dot_size + 1, py + dot_size + 1], 
                     fill=WHITE, outline=WHITE)
        # Black dot (Economist uses black dots for cities)
        if is_capital:
            draw.rectangle([px - dot_size, py - dot_size, px + dot_size, py + dot_size], fill=DARK)
        else:
            draw.ellipse([px - dot_size, py - dot_size, px + dot_size, py + dot_size], fill=RED if role in ("target","source","flashpoint","chokepoint") else DARK)
        # Small label, right of marker
        fnt = get_font(7)
        bbox = draw.textbbox((0, 0), name, font=fnt)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        lx, ly = px + 8, py - th // 2
        draw.text((lx, ly), name, fill="#444", font=fnt)

def draw_routes(draw, routes, cfg, img_w, img_h):
    """Economist-style routes: thin lines, subtle arrows, minimal labels."""
    for route in routes:
        coords = route["coords"]
        color_map = {"#cc0000": RED, "#38761d": GREEN, "#3c78d8": BLUE,
                     "#b37400": ORANGE, "#1c6dc9": TEAL}
        color = color_map.get(route.get("color", "#cc0000"), RED)
        label = route.get("label", "")
        pixel_coords = [lonlat_to_px(lon, lat, cfg, img_w, img_h) for lon, lat in coords]

        # Thin line (2px instead of 4, no glow)
        for i in range(len(pixel_coords) - 1):
            draw.line([pixel_coords[i], pixel_coords[i+1]], fill=color, width=2)

        # Arrow at endpoint
        if len(pixel_coords) >= 2:
            last = pixel_coords[-1]
            prev = pixel_coords[-2]
            import math
            angle = math.atan2(last[1] - prev[1], last[0] - prev[0])
            arrow_len = 8
            p1 = (int(last[0] - arrow_len * math.cos(angle - 0.4)),
                  int(last[1] - arrow_len * math.sin(angle - 0.4)))
            p2 = (int(last[0] - arrow_len * math.cos(angle + 0.4)),
                  int(last[1] - arrow_len * math.sin(angle + 0.4)))
            draw.polygon([last, p1, p2], fill=color)

        # Label at midpoint
        if label and len(pixel_coords) >= 2:
            mid = len(pixel_coords) // 2
            mx, my = pixel_coords[mid]
            if mid > 0:
                dx = pixel_coords[mid][0] - pixel_coords[mid-1][0]
                dy = pixel_coords[mid][1] - pixel_coords[mid-1][1]
            else:
                dx = pixel_coords[mid+1][0] - pixel_coords[mid][0]
                dy = pixel_coords[mid+1][1] - pixel_coords[mid][1]
            import math
            ang = math.atan2(dy, dx)
            off_x = -15 * math.sin(ang) if dx != 0 else 12
            off_y = 15 * math.cos(ang) if dx != 0 else -12
            lx, ly = mx + int(off_x), my + int(off_y)
            fnt = get_font(7)
            draw.text((lx, ly), label, fill="#555", font=fnt)

def draw_zones(draw, zones, cfg, img_w, img_h):
    """Economist-style zones: very subtle fill, thin outline, small label."""
    for zone in zones:
        coords = zone.get("coords", [])
        color_map = {"#cc0000": RED, "#1c6dc9": TEAL, "#38761d": GREEN}
        color = color_map.get(zone.get("color", "#cc0000"), RED)
        label = zone.get("label", "")
        pixel_coords = [lonlat_to_px(lon, lat, cfg, img_w, img_h) for lon, lat in coords]

        # Very subtle fill (alpha 15) with thin outline
        draw.polygon(pixel_coords, fill=(*color, 25), outline=(*color, 120), width=1)

        # Small label at centroid
        if label:
            cx = sum(p[0] for p in pixel_coords) // len(pixel_coords)
            cy = sum(p[1] for p in pixel_coords) // len(pixel_coords)
            fnt = get_font(8)
            draw.text((cx, cy), label, fill=color, font=fnt, anchor="mm")


def render_region(region, data, cfg, token, out_path):
    """Full hybrid rendering: Mapbox basemap + PIL overlays."""
    # Step 1: Fetch Mapbox basemap
    basemap = fetch_basemap(region, cfg, token)
    if basemap is None:
        return False

    img = basemap
    draw = ImageDraw.Draw(img)
    w, h = img.size  # @2x = 2*w, 2*h

    # Step 2: Draw title bar
    region_label = {
        "europe": "Europe", "asia": "Asia & Indo-Pacific",
        "middle_east": "Middle East", "north_america": "North America",
        "south_central_america": "South & Central America",
        "global_finance": "Global Finance",
    }.get(region, region.replace("_", " ").title())
    draw_title(draw, cfg, region_label)

    # Step 3: Draw conflict zones
    draw_zones(draw, data.get("zones", []), cfg, w, h)

    # Step 4: Draw route lines
    draw_routes(draw, data.get("lines", []), cfg, w, h)

    # Step 5: Draw city markers
    draw_cities(draw, data.get("cities", []), cfg, w, h)

    # Step 6: Draw legend
    legend_data = draw_legend(draw, data, w, h)
    if legend_data:
        leg_img, lx, ly = legend_data
        img.paste(leg_img, (lx, ly), leg_img)

    # Step 7: TREVOR watermark
    fnt_w = get_font(10, bold=True)
    tw = draw.textbbox((0, 0), "TREVOR", font=fnt_w)
    tw_w = tw[2] - tw[0]
    draw.text((w - tw_w - 8, h - 18), "TREVOR", fill=(*GOLD, 60), font=fnt_w)

    # Save
    img.save(out_path, "PNG")
    kb = out_path.stat().st_size // 1024
    log(f"  ✅ {region}: {out_path.name} ({kb} KB, {w}x{h})")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    wd = pathlib.Path(args.working_dir).expanduser()
    out_dir = pathlib.Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    token = "not-needed-no-mapbox"

    regions = ["europe", "asia", "middle_east", "north_america",
               "south_central_america", "global_finance"]
    success = 0

    # Build theatre data from analysis JSONs
    analysis_dir = wd / "analysis"
    city_data = load_city_data(analysis_dir, regions)

    cache_dir = out_dir / "_cache"
    cache_dir.mkdir(exist_ok=True)
    # Copy 110m data to cache if 50m is available (for faster coastline outlines)
    fifty_path = cache_dir / "ne_50m_land.geojson"
    if not fifty_path.exists():
        import shutil
        src = cache_dir.parent / "_cache" / "ne_50m_land.geojson" if False else None
    # Ensure 110m is available for the drawing
    ten_path = cache_dir / "ne_110m_land.geojson"
    if not ten_path.exists():
        # Try to find it from other locations
        import glob
        for f in glob.glob(str(pathlib.Path.home()) + "/trevor-briefings/*/visuals/maps/_cache/ne_110m_land.geojson"):
            import shutil
            shutil.copy(f, ten_path)
            break
    
    for region in regions:
        cfg = MAP_CONFIG.get(region, MAP_CONFIG["global_finance"])
        cfg["_cache_dir"] = str(cache_dir)
        data = build_theatre_data(region, analysis_dir / f"{region}.json", city_data, cfg)
        out_path = out_dir / f"map_{region}.png"
        if render_region(region, data, cfg, token, out_path):
            success += 1

    log(f"Generated {success}/{len(regions)} hybrid maps")
    return 0 if success > 0 else 1


def load_city_data(analysis_dir, regions):
    """Extract mentioned cities from analysis JSONs."""
    city_data = {}
    CITIES = {
        "kyiv": (50.45, 30.52), "berlin": (52.52, 13.40), "moscow": (55.76, 37.62),
        "warsaw": (52.23, 21.01), "brussels": (50.85, 4.35), "london": (51.51, -0.13),
        "oslo": (59.91, 10.75), "paris": (48.86, 2.35),
        "beijing": (39.91, 116.40), "tokyo": (35.68, 139.69), "seoul": (37.57, 126.98),
        "delhi": (28.61, 77.23), "islamabad": (33.68, 73.05),
        "taipei": (25.03, 121.57), "shanghai": (31.23, 121.47),
        "tehran": (35.69, 51.42), "baghdad": (33.32, 44.36), "riyadh": (24.71, 46.67),
        "abu dhabi": (24.45, 54.37), "dubai": (25.20, 55.27),
        "beirut": (33.89, 35.50), "jerusalem": (31.77, 35.21), "damascus": (33.51, 36.28),
        "washington": (38.91, -77.04), "mexico city": (19.43, -99.13),
        "chihuahua": (28.63, -106.07), "caracas": (10.48, -66.90),
        "havana": (23.11, -82.37), "brasilia": (-15.79, -47.88),
        "recife": (-8.05, -34.88), "kabul": (34.56, 69.21),
        "new york": (40.71, -74.01), "hong kong": (22.28, 114.16),
        "singapore": (1.35, 103.82), "cape town": (-33.92, 18.42),
    }

    for region in regions:
        ap = analysis_dir / f"{region}.json"
        if not ap.exists():
            continue
        try:
            aj = json.loads(ap.read_text())
        except:
            continue
        mentions = set()
        narrative = (aj.get("narrative", "") + " " + aj.get("story", "") + " " +
                     " ".join(kj.get("statement", "") for kj in aj.get("key_judgments", [])))
        nl = narrative.lower()
        for name, coords in CITIES.items():
            if name in nl:
                mentions.add((name, coords[0], coords[1]))
        city_data[region] = mentions
    return city_data


def build_theatre_data(region, analysis_path, city_data, cfg):
    """Build theatre data with routes, zones, cities."""
    data = {"lines": [], "zones": [], "cities": []}

    subtitles = {
        "europe": "Truce & Strategic Dynamics", "asia": "Diplomacy & Power Projection",
        "middle_east": "Framework & Kinetic Cycle", "north_america": "Coordination & Sovereignty",
        "south_central_america": "Political & Financial Pressures",
        "global_finance": "Risk & Liquidity Conditions",
    }

    # Default cities per theatre
    default_cities = {
        "europe": [("Berlin", 52.52, 13.40, "capital"), ("Kyiv", 50.45, 30.52, "target"),
                   ("Moscow", 55.76, 37.62, "source"), ("Warsaw", 52.23, 21.01, "nato")],
        "asia": [("Beijing", 39.91, 116.40, "capital"), ("Tokyo", 35.68, 139.69, "capital"),
                 ("Delhi", 28.61, 77.23, "capital"), ("Taipei", 25.03, 121.57, "flashpoint")],
        "middle_east": [("Tehran", 35.69, 51.42, "source"), ("Baghdad", 33.32, 44.36, "capital"),
                        ("Riyadh", 24.71, 46.67, "capital"), ("Abu Dhabi", 24.45, 54.37, "capital")],
        "north_america": [("Washington", 38.91, -77.04, "capital"),
                          ("Mexico City", 19.43, -99.13, "capital"),
                          ("Caracas", 10.48, -66.90, "flashpoint")],
        "south_central_america": [("Havana", 23.11, -82.37, "flashpoint"),
                                  ("Brasilia", -15.79, -47.88, "capital")],
        "global_finance": [("London", 51.51, -0.13, "capital"), ("NYC", 40.71, -74.01, "capital"),
                           ("Tokyo", 35.68, 139.69, "capital"), ("Dubai", 25.20, 55.27, "hub")],
    }

    # Add mentioned cities from narrative
    mentioned = city_data.get(region, set())
    seen = set()
    for name, lat, lng in mentioned:
        role = "target" if name in ["kyiv", "sanaa", "chihuahua", "recife"] else \
               "source" if name in ["moscow", "tehran"] else \
               "flashpoint" if name in ["caracas", "havana"] else "capital"
        data["cities"].append((name.title().replace(" Of ", " of "), lat, lng, role))
        seen.add(name)

    # Add defaults not already mentioned
    for dc in default_cities.get(region, []):
        if dc[0].lower() not in seen:
            data["cities"].append(dc)
            seen.add(dc[0].lower())

    # Routes per theatre
    route_defs = {
        "europe": [
            {"coords": [[37.62, 55.76], [35.0, 52.0], [30.52, 50.45]], "color": "#cc0000", "label": "Strike: 108 munitions, 1 night"},
            {"coords": [[13.40, 52.52], [21.01, 52.24], [30.52, 50.45]], "color": "#3c78d8", "label": "NATO reinforcement corridor"},
            {"coords": [[4.35, 50.85], [10.75, 59.91]], "color": "#b37400", "label": "Weapons delivery delay → Norway"},
        ],
        "asia": [
            {"coords": [[116.40, 39.91], [121.57, 25.03]], "color": "#b37400", "label": "Cross-strait diplomatic pressure"},
            {"coords": [[77.23, 28.61], [73.05, 33.68]], "color": "#cc0000", "label": "India-Pakistan friction"},
        ],
        "middle_east": [
            {"coords": [[51.42, 35.69], [56.27, 27.18], [56.25, 26.57]], "color": "#cc0000", "label": "Iran: Rial-denominated toll demand"},
            {"coords": [[44.36, 33.32], [36.28, 33.51]], "color": "#1c6dc9", "label": "Syria: Overland oil corridor"},
            {"coords": [[35.50, 33.89], [35.21, 31.77]], "color": "#cc0000", "label": "50+ IDF airstrikes in 24h"},
        ],
        "north_america": [
            {"coords": [[-77.04, 38.91], [-106.07, 28.63]], "color": "#cc0000", "label": "Chihuahua: 2x CIA fatalities"},
            {"coords": [[-66.90, 10.48], [-95.37, 29.76]], "color": "#38761d", "label": "Venezuelan crude: 1.1M bpd → USGC"},
        ],
        "south_central_america": [
            {"coords": [[-77.04, 38.91], [-82.37, 23.11]], "color": "#cc0000", "label": "US sanctions: energy, defence, mining"},
            {"coords": [[-36.0, -6.0], [-34.0, -9.0]], "color": "#1c6dc9", "label": "Brazil flooding: 6+ dead, state of emergency"},
        ],
        "global_finance": [
            {"coords": [[56.25, 26.57], [38.06, 24.09]], "color": "#38761d", "label": "Petroline bypass: 4.8M bpd capacity"},
            {"coords": [[-0.13, 51.51], [55.27, 25.20]], "color": "#3c78d8", "label": "Global energy route EUR→ME→ASIA"},
        ],
    }

    for route in route_defs.get(region, []):
        data["lines"].append(route)

    # Zones
    zone_defs = {
        "europe": [{"coords": [[28.0, 50.0], [38.0, 50.0], [38.0, 46.0], [28.0, 46.0]], "color": "#cc0000", "label": "Ukraine"}],
        "middle_east": [
            {"coords": [[55.0, 27.5], [57.5, 27.5], [57.5, 25.0], [55.0, 25.0]], "color": "#cc0000", "label": "Hormuz"},
            {"coords": [[42.0, 15.0], [46.0, 15.0], [46.0, 18.0], [42.0, 18.0]], "color": "#cc0000", "label": "Yemen"},
        ],
        "north_america": [{"coords": [[-108.0, 30.0], [-104.0, 30.0], [-104.0, 27.0], [-108.0, 27.0]], "color": "#cc0000", "label": "Cartel corridor"}],
        "south_central_america": [
            {"coords": [[-85.0, 24.0], [-77.0, 24.0], [-77.0, 21.0], [-85.0, 21.0]], "color": "#cc0000", "label": "Cuba"},
            {"coords": [[-36.0, -4.0], [-34.0, -4.0], [-34.0, -9.0], [-36.0, -9.0]], "color": "#1c6dc9", "label": "Brazil floods"},
        ],
        "global_finance": [{"coords": [[55.0, 27.5], [57.5, 27.5], [57.5, 25.0], [55.0, 25.0]], "color": "#cc0000", "label": "Hormuz: 20M bpd"}],
    }
    for zone in zone_defs.get(region, []):
        data["zones"].append(zone)

    return data


if __name__ == "__main__":
    sys.exit(main())
