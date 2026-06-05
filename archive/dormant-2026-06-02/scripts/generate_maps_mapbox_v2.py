#!/usr/bin/env python3
"""
generate_maps_mapbox_v2.py — Dynamic Mapbox theatre maps driven by today's analysis data.

Reads analysis JSON files for each theatre to extract narrative-driven locations,
routes, and conflict zones. Uses Mapbox Static API with GeoJSON overlays for
professional base maps with correct geographic rendering.

Usage:
    python3 generate_maps_mapbox_v2.py \
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

MAPBOX_BASE = "https://api.mapbox.com"
# Dark style for intelligence briefing aesthetic
STYLE = "light-v11"

MAP_CONFIG = {
    "europe":              {"center": (52.0, 20.0), "zoom": 4.0, "w": 800, "h": 500},
    "asia":                {"center": (30.0, 85.0), "zoom": 3.5, "w": 800, "h": 500},
    "middle_east":         {"center": (28.0, 48.0), "zoom": 4.5, "w": 800, "h": 500},
    "north_america":       {"center": (30.0, -95.0), "zoom": 3.5, "w": 800, "h": 500},
    "south_central_america":{"center": (-5.0, -60.0), "zoom": 3.5, "w": 800, "h": 500},
    "global_finance":      {"center": (30.0, 30.0), "zoom": 2.5, "w": 800, "h": 500},
}

# Known city coordinates for lookup
CITIES = {
    "kyiv": (50.45, 30.52), "berlin": (52.52, 13.40), "moscow": (55.76, 37.62),
    "warsaw": (52.23, 21.01), "brussels": (50.85, 4.35), "london": (51.51, -0.13),
    "oslo": (59.91, 10.75), "paris": (48.86, 2.35), "rome": (41.90, 12.50),
    "beijing": (39.91, 116.40), "tokyo": (35.68, 139.69), "seoul": (37.57, 126.98),
    "delhi": (28.61, 77.23), "new delhi": (28.61, 77.23), "islamabad": (33.68, 73.05),
    "taipei": (25.03, 121.57), "shanghai": (31.23, 121.47),
    "tehran": (35.69, 51.42), "baghdad": (33.32, 44.36), "riyadh": (24.71, 46.67),
    "abu dhabi": (24.45, 54.37), "dubai": (25.20, 55.27), "sanaa": (15.35, 44.21),
    "beirut": (33.89, 35.50), "jerusalem": (31.77, 35.21), "damascus": (33.51, 36.28),
    "muscat": (23.59, 58.41), "doha": (25.29, 51.53), "kuwait city": (29.38, 47.97),
    "washington": (38.91, -77.04), "mexico city": (19.43, -99.13),
    "ottawa": (45.42, -75.70), "chihuahua": (28.63, -106.07),
    "caracas": (10.48, -66.90), "houston": (29.76, -95.37),
    "havana": (23.11, -82.37), "brasilia": (-15.79, -47.88),
    "brasília": (-15.79, -47.88), "recife": (-8.05, -34.88),
    "bogota": (4.71, -74.07), "lima": (-12.05, -77.04),
    "buenos aires": (-34.60, -58.38), "santiago": (-33.45, -70.67),
    "kabul": (34.56, 69.21), "minsk": (53.90, 27.57),
    "new york": (40.71, -74.01), "hong kong": (22.28, 114.16),
    "singapore": (1.35, 103.82), "ankara": (39.92, 32.85),
    "cape town": (-33.92, 18.42), "cairo": (30.04, 31.24),
    "dakar": (14.69, -17.45), "nairobi": (-1.29, 36.82),
    "addis ababa": (9.03, 38.74), "lagos": (6.52, 3.38),
}


def log(msg):
    print(f"[maps2] {msg}", file=sys.stderr, flush=True)


def find_city(name):
    """Find city coordinates by name (case-insensitive, partial match)."""
    n = name.lower().strip()
    if n in CITIES:
        return CITIES[n]
    for k, v in CITIES.items():
        if k in n or n in k:
            return v
    return None


def build_theatre_data(region, analysis_path, maps_cfg):
    """Build dynamic theatre data from analysis JSON."""
    data = {"lines": [], "zones": [], "cities": [], "title": ""}

    # Try to load analysis JSON
    if not analysis_path or not analysis_path.exists():
        log(f"  No analysis data for {region}, using minimal map")
        return data

    try:
        aj = json.loads(analysis_path.read_text())
    except:
        return data

    narrative = (aj.get("narrative", "") + " " + aj.get("story", "") + " " +
                 " ".join(kj.get("statement", "") for kj in aj.get("key_judgments", [])))
    narrative_lower = narrative.lower()

    region_label = maps_cfg.get("label", region.replace("_", " ").title())

    # Extract cities mentioned in narrative
    mentioned_cities = []
    region_city_map = {
        "europe": ["kyiv", "berlin", "moscow", "warsaw", "brussels", "london", "oslo", "paris", "minsk", "rome"],
        "asia": ["beijing", "tokyo", "seoul", "delhi", "islamabad", "taipei", "shanghai", "hong kong", "singapore"],
        "middle_east": ["tehran", "baghdad", "riyadh", "abu dhabi", "dubai", "sanaa", "beirut", "jerusalem", "damascus", "doha", "muscat", "cairo", "ankara"],
        "north_america": ["washington", "mexico city", "ottawa", "chihuahua", "caracas", "houston"],
        "south_central_america": ["havana", "brasilia", "recife", "bogota", "lima", "caracas", "buenos aires", "santiago"],
        "global_finance": ["london", "new york", "tokyo", "hong kong", "shanghai", "singapore", "dubai", "beijing"],
    }

    for city_name in region_city_map.get(region, []):
        if city_name in narrative_lower:
            coords = CITIES.get(city_name)
            if coords:
                role = "capital"
                if any(kw in city_name for kw in ["kyiv", "sanaa", "chihuahua", "recife"]):
                    role = "target"
                elif city_name in ["moscow", "tehran"]:
                    role = "source"
                elif city_name in ["caracas", "havana"]:
                    role = "flashpoint"
                mentioned_cities.append((city_name.title(), coords[0], coords[1], role))

    # Add key capitals even if not mentioned (context)
    default_cities = {
        "europe": [("Berlin", 52.52, 13.40, "capital"), ("Kyiv", 50.45, 30.52, "target"),
                   ("Moscow", 55.76, 37.62, "source"), ("Warsaw", 52.23, 21.01, "nato")],
        "asia": [("Beijing", 39.91, 116.40, "capital"), ("Tokyo", 35.68, 139.69, "capital"),
                 ("Delhi", 28.61, 77.23, "capital"), ("Taipei", 25.03, 121.57, "flashpoint")],
        "middle_east": [("Tehran", 35.69, 51.42, "source"), ("Baghdad", 33.32, 44.36, "capital"),
                        ("Riyadh", 24.71, 46.67, "capital"), ("Abu Dhabi", 24.45, 54.37, "capital"),
                        ("Beirut", 33.89, 35.50, "target"), ("Jerusalem", 31.77, 35.21, "capital")],
        "north_america": [("Washington", 38.91, -77.04, "capital"),
                          ("Mexico City", 19.43, -99.13, "capital"),
                          ("Caracas", 10.48, -66.90, "flashpoint")],
        "south_central_america": [("Havana", 23.11, -82.37, "flashpoint"),
                                  ("Brasília", -15.79, -47.88, "capital"),
                                  ("Caracas", 10.48, -66.90, "capital")],
        "global_finance": [("London", 51.51, -0.13, "capital"), ("NYC", 40.71, -74.01, "capital"),
                           ("Tokyo", 35.68, 139.69, "capital"), ("Dubai", 25.20, 55.27, "hub")],
    }

    # Merge: add default cities not already mentioned
    seen_names = {c[0].lower() for c in mentioned_cities}
    for dc in default_cities.get(region, []):
        if dc[0].lower() not in seen_names:
            mentioned_cities.append(dc)

    data["cities"] = mentioned_cities

    # Extract incidents count for zone sizing
    incidents = aj.get("incident_count", 0)

    # Build title from section subtitle
    subtitles = {
        "europe": "Truce & Strategic Dynamics", "asia": "Diplomacy & Power Projection",
        "middle_east": "Framework & Kinetic Cycle", "north_america": "Coordination & Sovereignty",
        "south_central_america": "Political & Financial Pressures",
        "global_finance": "Risk & Liquidity Conditions",
    }
    data["title"] = f"{region_label} — {subtitles.get(region, 'Overview')}"

    # Conflict zones based on region
    zone_defs = {
        "europe": {"coords": [[30.0, 50.0], [40.0, 50.0], [40.0, 45.0], [30.0, 45.0]], "color": "#cc0000", "label": "Ukraine conflict zone"},
        "middle_east": [
            {"coords": [[55.0, 27.5], [57.5, 27.5], [57.5, 25.0], [55.0, 25.0]], "color": "#cc0000", "label": "Hormuz chokepoint"},
            {"coords": [[42.0, 15.0], [46.0, 15.0], [46.0, 18.0], [42.0, 18.0]], "color": "#cc0000", "label": "Yemen / Houthi zone"},
        ],
        "north_america": {"coords": [[-108.0, 30.0], [-104.0, 30.0], [-104.0, 27.0], [-108.0, 27.0]], "color": "#cc0000", "label": "Chihuahua cartel corridor"},
        "south_central_america": [
            {"coords": [[-85.0, 24.0], [-77.0, 24.0], [-77.0, 21.0], [-85.0, 21.0]], "color": "#cc0000", "label": "Cuba crisis"},
            {"coords": [[-36.0, -5.0], [-34.0, -5.0], [-34.0, -9.0], [-36.0, -9.0]], "color": "#1c6dc9", "label": "Brazil flooding"},
        ],
        "global_finance": {"coords": [[55.0, 27.5], [57.5, 27.5], [57.5, 25.0], [55.0, 25.0]], "color": "#cc0000", "label": "Hormuz — 20M bpd transit"},
    }

    zd = zone_defs.get(region, [])
    if isinstance(zd, dict):
        zd = [zd]
    for z in zd:
        z["fill_opacity"] = 0.15
        data["zones"].append(z)

    # Route lines from narrative
    route_defs = {
        "europe": [
            {"coords": [[37.62, 55.76], [35.0, 52.0], [30.52, 50.45]], "color": "#cc0000", "label": "Russian strike vectors"},
            {"coords": [[13.40, 52.52], [21.01, 52.24], [30.52, 50.45]], "color": "#3c78d8", "label": "NATO reinforcement corridor"},
            {"coords": [[4.35, 50.85], [10.75, 59.91]], "color": "#b37400", "label": "NATO-HQ to Norway"},
        ],
        "asia": [
            {"coords": [[116.40, 39.91], [121.57, 25.03]], "color": "#b37400", "label": "Cross-strait pressure"},
            {"coords": [[77.23, 28.61], [73.05, 33.68]], "color": "#cc0000", "label": "India-Pakistan friction"},
        ],
        "middle_east": [
            {"coords": [[51.42, 35.69], [56.27, 27.18], [56.25, 26.57]], "color": "#cc0000", "label": "Iran toll demand zone"},
            {"coords": [[44.36, 33.32], [36.28, 33.51]], "color": "#1c6dc9", "label": "Syria oil corridor"},
            {"coords": [[46.67, 24.71], [44.36, 33.32], [36.28, 33.51]], "color": "#38761d", "label": "Overland alternative route"},
            {"coords": [[35.50, 33.89], [35.21, 31.77]], "color": "#cc0000", "label": "Israel-Lebanon front"},
        ],
        "north_america": [
            {"coords": [[-77.04, 38.91], [-106.07, 28.63]], "color": "#cc0000", "label": "Chihuahua incident"},
            {"coords": [[-66.90, 10.48], [-95.37, 29.76]], "color": "#38761d", "label": "Venezuelan crude → USGC"},
        ],
        "south_central_america": [
            {"coords": [[-77.04, 38.91], [-82.37, 23.11]], "color": "#cc0000", "label": "US sanctions pressure"},
            {"coords": [[-82.37, 23.11], [-66.90, 10.48]], "color": "#b37400", "label": "Venezuela-Cuba axis"},
        ],
        "global_finance": [
            {"coords": [[56.25, 26.57], [38.06, 24.09]], "color": "#38761d", "label": "Petroline bypass"},
            {"coords": [[-0.13, 51.51], [55.27, 25.20], [103.82, 1.35]], "color": "#3c78d8", "label": "Global energy trade routes"},
        ],
    }

    for route in route_defs.get(region, []):
        data["lines"].append(route)

    return data


def build_geojson(data):
    """Build GeoJSON FeatureCollection from theatre data."""
    features = []

    def make_point(lng, lat, color, size="l"):
        return {"type": "Feature", "properties": {"marker-color": color, "marker-size": size},
                "geometry": {"type": "Point", "coordinates": [lng, lat]}}

    def make_line(coords, color, width=2, opacity=0.7, dash=None):
        props = {"stroke": color, "stroke-width": width, "stroke-opacity": opacity}
        if dash:
            props["stroke-dasharray": dash]  # noqa: E231
        return {"type": "Feature", "properties": props,
                "geometry": {"type": "LineString", "coordinates": coords}}

    def make_poly(coords, fill_color, fill_opacity, stroke_color="#666", stroke_width=1):
        ring = list(coords)
        if ring and len(ring) > 1 and (ring[0][0] != ring[-1][0] or ring[0][1] != ring[-1][1]):
            ring.append(ring[0])
        return {"type": "Feature", "properties": {"fill": fill_color, "fill-opacity": fill_opacity,
                    "stroke": stroke_color, "stroke-width": stroke_width, "stroke-opacity": 0.6},
                "geometry": {"type": "Polygon", "coordinates": [ring]}}

    for zone in data.get("zones", []):
        features.append(make_poly(zone["coords"], zone["color"], zone.get("fill_opacity", 0.12)))

    for route in data.get("lines", []):
        features.append(make_line(route["coords"], route["color"]))

    for city in data.get("cities", []):
        name, lat, lng, role = city
        mc = {"capital": "#1e3caf", "target": "#cc0000", "source": "#cc0000",
              "nato": "#3c78d8", "flashpoint": "#cc0000", "hub": "#6aa84f",
              "warning": "#b37400", "chokepoint": "#cc0000", "military": "#6aa84f",
              "base": "#6aa84f", "disaster": "#1c6dc9"}.get(role, "#666")
        features.append(make_point(lng, lat, mc))

    return {"type": "FeatureCollection", "features": features}


def render_map(region, data, cfg, token, out_path):
    """Call Mapbox Static API to render map with GeoJSON overlay."""
    lat, lng = cfg["center"]
    z = cfg["zoom"]
    w, h = cfg["w"], cfg["h"]

    geojson = build_geojson(data)
    geo_str = json.dumps(geojson, separators=(",", ":"))
    geo_enc = urllib.parse.quote(geo_str)
    overlay = f"geojson({geo_enc})"

    url = (f"{MAPBOX_BASE}/styles/v1/mapbox/{STYLE}/static"
           f"/{overlay}/{lng},{lat},{z},0,0/{w}x{h}@2x"
           f"?access_token={token}&logo=false&attribution=true")

    log(f"  Fetching {region}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TREVOR-Intel-Brief/2.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            map_data = resp.read()
        if len(map_data) < 2000:
            log(f"  Too small: {len(map_data)} bytes")
            return False
        out_path.write_bytes(map_data)
        log(f"  ✅ {region}: {out_path.name} ({len(map_data)//1024} KB)")
        
        # Composite legend onto image using PIL
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.open(out_path).convert("RGBA")
            leg_data = [
                ("#cc0000", "line", "Conflict / Kinetic"),
                ("#38761d", "line", "Supply / Route"),
                ("#3c78d8", "line", "Alliance / Corridor"),
                ("#1c6dc9", "line", "Maritime / Energy"),
                ("#b37400", "line", "Assessed / Diplomatic"),
                ("#cc0000", "dot", "Incident / Flashpoint"),
                ("#1e3caf", "dot", "Capital / Hub"),
            ]
            nl = len(data.get("lines", []))
            nc = len(data.get("cities", []))
            leg = Image.new("RGBA", (200, 74), (255, 255, 255, 210))
            d = ImageDraw.Draw(leg)
            try:
                fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
            except:
                fnt = ImageFont.load_default()
            iy = 5
            shown = 0
            for clr, knd, lbl in leg_data:
                if knd == "line" and nl == 0:
                    continue
                if knd == "dot" and nc == 0:
                    continue
                if shown >= 4:
                    break
                if knd == "line":
                    d.rectangle([7, iy+3, 25, iy+7], fill=clr)
                else:
                    d.ellipse([9, iy, 23, iy+14], fill=clr, outline="#333", width=1)
                d.text((30, iy), lbl, fill="#222", font=fnt)
                iy += 15
                shown += 1
            d.rectangle([0, 0, leg.width-1, leg.height-1], outline="#ccc", width=1)
            img.paste(leg, (12, img.height - 86), leg)
            img.save(out_path, "PNG")
        except Exception as e:
            log(f"  Legend failed: {e}")
        
        return True
    except urllib.error.HTTPError as e:
        log(f"  HTTP {e.code}: {e.read().decode(errors='replace')[:200]}")
        return False
    except Exception as e:
        log(f"  Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    wd = pathlib.Path(args.working_dir).expanduser()
    out_dir = pathlib.Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    analysis_dir = wd / "analysis"

    token = os.environ.get("MAPBOX_TOKEN", "")
    if not token:
        log("ERROR: No MAPBOX_TOKEN in environment")
        return 1
    log(f"Mapbox token loaded ({token[:10]}...{token[-4:]})")

    regions = ["europe", "asia", "middle_east", "north_america",
               "south_central_america", "global_finance"]
    success = 0

    for region in regions:
        cfg = MAP_CONFIG.get(region, MAP_CONFIG["global_finance"])
        analysis_path = analysis_dir / f"{region}.json"
        data = build_theatre_data(region, analysis_path, cfg)
        out_path = out_dir / f"map_{region}.png"
        if render_map(region, data, cfg, token, out_path):
            success += 1

    log(f"Generated {success}/{len(regions)} theatre maps")
    manifest = []
    for f in sorted(out_dir.glob("map_*.png")):
        manifest.append({"region": f.stem.replace("map_", ""), "path": str(f), "size_kb": f.stat().st_size // 1024})
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return 0 if success > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
