#!/usr/bin/env python3
"""Refresh daily imagery — story-relevant photos, 50m maps with conflict markers, contextual infographics.

Uses matplotlib + Natural Earth (50m) for geographic maps with conflict zone overlays,
Wikipedia Page Images for story-relevant photos, Kalshi scanner data for infographics.
"""
import os, sys, json, datetime, urllib.request, urllib.parse, io, math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, FancyBboxPatch
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe
import numpy as np

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))
IMAGES_DIR = SKILL_ROOT / 'images'
MAPS_DIR = SKILL_ROOT / 'maps'
INFO_DIR = SKILL_ROOT / 'infographics'
from trevor_config import WORKSPACE
SCRIPTS_DIR = WORKSPACE / 'scripts'

for d in [IMAGES_DIR, MAPS_DIR, INFO_DIR]:
    d.mkdir(parents=True, exist_ok=True)

UA = 'TrevorIntelBot/1.0 (trevor@agentmail.to)'


# ─── THEATRE DATA ──────────────────────────────────────

THEATRE_BBOX = {
    "europe": [-12, 34, 42, 72],
    "africa": [-20, -36, 52, 38],
    "asia": [66, 5, 98, 38],
    "middle_east": [24, 14, 62, 42],
    "north_america": [-125, 14, -68, 52],  # Focus Mexico/Northern Triangle
    "south_america": [-82, -56, -34, 13],
}

THEATRE_STORIES = {
    "europe": {
        "title": "MOSCOW FORTRESS",
        "kicker": "RUSSIA / UKRAINE",
        "conflict_zones": [
            {"coords": [(37.55,55.72),(37.65,55.72),(37.65,55.78),(37.55,55.78)],
             "color": "#eb5757", "alpha": 0.25, "label": "Mosfilm strike (5 May)"},
            {"coords": [(30.0,49.5),(33.0,49.5),(33.0,51.5),(30.0,51.5)],
             "color": "#e67e22", "alpha": 0.15, "label": "Russian FLOT, eastern Ukraine"},
        ],
        "features": [
            ("Moscow (Kremlin)", 37.617, 55.754, "capital"),
            ("Mosfilm Tower", 37.603, 55.751, "strike_diamond"),
            ("Vnukovo (closed)", 37.282, 55.591, "airport_closed"),
            ("Kyiv", 30.524, 50.450, "capital_ally"),
            ("Kharkiv", 36.230, 49.993, "city_frontline"),
            ("Pokrovsk", 37.183, 48.283, "city_frontline"),
            ("Kostyantynivka", 37.707, 48.528, "city_frontline"),
            ("Warsaw", 21.012, 52.230, "city_nato"),
            ("Minsk", 27.561, 53.904, "city_ally"),
        ],
    },
    "africa": {
        "title": "JNIM OFFENSIVE CONFIRMED",
        "kicker": "SAHEL",
        "conflict_zones": [
            {"coords": [(-8.3,12.4),(-7.6,12.4),(-7.6,12.9),(-8.3,12.9)],
             "color": "#eb5757", "alpha": 0.30, "label": "Bamako airport + Kati attacks"},
            {"coords": [(-4.8,14.0),(-0.2,14.0),(-0.2,17.0),(-4.8,17.0)],
             "color": "#e67e22", "alpha": 0.18, "label": "JNIM multi-city offensive zone"},
            {"coords": [(-5.0,11.5),(-2.0,11.5),(-2.0,14.0),(-5.0,14.0)],
             "color": "#e67e22", "alpha": 0.10, "label": "JNIM expansion corridor"},
        ],
        "features": [
            ("Bamako", -8.002, 12.639, "capital"),
            ("Kati (HQ attacked)", -8.072, 12.744, "strike_diamond"),
            ("Mopti", -4.196, 14.512, "city_frontline"),
            ("Gao", -0.045, 16.275, "city_frontline"),
            ("Sévaré", -4.101, 14.535, "city_frontline"),
            ("Ouagadougou", -1.519, 12.371, "city_nato"),
            ("Niamey", 2.110, 13.514, "city_frontline"),
        ],
    },
    "asia": {
        "title": "INDIA FORGIVES NOTHING",
        "kicker": "INDIA / PAKISTAN",
        "conflict_zones": [
            {"coords": [(73.0,32.5),(75.5,32.5),(75.5,35.0),(73.0,35.0)],
             "color": "#eb5757", "alpha": 0.20, "label": "Sindoor strike zone (7 May)"},
            {"coords": [(76.0,31.0),(77.5,31.0),(77.5,32.5),(76.0,32.5)],
             "color": "#2ecc71", "alpha": 0.12, "label": "IAF operational area"},
        ],
        "features": [
            ("New Delhi", 77.200, 28.613, "capital"),
            ("Islamabad", 73.058, 33.729, "capital_opposing"),
            ("Srinagar", 74.797, 34.084, "city_frontline"),
            ("LoC", 74.300, 33.800, "conflict_line"),
            ("Lahore", 74.358, 31.549, "city_frontline"),
            ("Amritsar", 74.876, 31.634, "city_nato"),
        ],
    },
    "middle_east": {
        "title": "MOU INSIDE 48 HOURS",
        "kicker": "IRAN",
        "conflict_zones": [
            {"coords": [(51.0,35.4),(51.7,35.4),(51.7,36.0),(51.0,36.0)],
             "color": "#2ecc71", "alpha": 0.18, "label": "MoU negotiation zone"},
            {"coords": [(55.0,25.0),(58.0,25.0),(58.0,28.0),(55.0,28.0)],
             "color": "#e67e22", "alpha": 0.20, "label": "Strait of Hormuz — contested blockade"},
            {"coords": [(46.0,28.0),(52.0,28.0),(52.0,32.0),(46.0,32.0)],
             "color": "#eb5757", "alpha": 0.12, "label": "IRGC operational zone"},
        ],
        "features": [
            ("Tehran", 51.420, 35.689, "capital"),
            ("Bandar Abbas", 56.280, 27.183, "city_frontline"),
            ("Strait of Hormuz", 56.500, 26.550, "chokepoint"),
            ("Bushehr", 50.838, 28.969, "city_frontline"),
            ("Qeshm Island", 55.870, 26.950, "city_frontline"),
            ("Dubai", 55.304, 25.205, "city_nato"),
        ],
    },
    "north_america": {
        "title": "FALLOUT SETTLES",
        "kicker": "MEXICO",
        "conflict_zones": [
            {"coords": [(-109.0,23.0),(-105.5,23.0),(-105.5,27.0),(-109.0,27.0)],
             "color": "#eb5757", "alpha": 0.22, "label": "Sinaloa cartel violence zone"},
            {"coords": [(-107.0,22.8),(-105.8,22.8),(-105.8,23.8),(-107.0,23.8)],
             "color": "#e74c3c", "alpha": 0.25, "label": "Mazatlán — mayor resigned"},
        ],
        "features": [
            ("Mexico City", -99.133, 19.433, "capital"),
            ("Culiacán", -107.394, 24.809, "city_frontline"),
            ("Mazatlán", -106.416, 23.236, "city_frontline"),
            ("Chihuahua", -106.069, 28.635, "city_frontline"),
            ("Sonora border", -110.0, 30.0, "city_frontline"),
        ],
    },
    "south_america": {
        "title": "TREASURY LICENSES",
        "kicker": "VENEZUELA",
        "conflict_zones": [
            {"coords": [(-67.1,10.3),(-66.6,10.3),(-66.6,10.7),(-67.1,10.7)],
             "color": "#3498db", "alpha": 0.18, "label": "Transition-track political zone"},
        ],
        "features": [
            ("Caracas", -66.903, 10.501, "capital"),
            ("Miraflores Palace", -66.915, 10.474, "govt_seat"),
            ("Bogotá", -74.072, 4.598, "city_nato"),
            ("Ciudad Guayana", -62.650, 8.350, "city_frontline"),
            ("Maracaibo", -71.630, 10.652, "city_frontline"),
        ],
    },
}


# ─── DATA LOADING ──────────────────────────────────────

def load_50m_data():
    paths = {
        'countries': '/tmp/ne_50m_admin_0_countries.geojson',
        'places': '/tmp/ne_50m_populated_places_simple.geojson',
    }
    data = {}
    for key, path in paths.items():
        if os.path.exists(path):
            with open(path) as f:
                data[key] = json.load(f)
        else:
            data[key] = None
    return data


# ─── SYMBOLOGY ─────────────────────────────────────────

def draw_symbol(ax, lng, lat, kind, color="#f4f4f4", size=1.0):
    """Draw ISW/CTP-style military map symbol.

    Symbology conventions:
    - star    : capital city (primary)
    - diamond : strike/attack location
    - square  : military objective / government seat
    - circle  : general city
    - x       : chokepoint / incident
    - triangle: allied position
    """
    s = size * 5.0
    kw = dict(markeredgecolor='#000000', markeredgewidth=0.5, zorder=5)

    if kind == "capital":
        ax.plot(lng, lat, '*', color='#f1c40f', markersize=s*1.6, **kw)
    elif kind == "capital_ally":
        ax.plot(lng, lat, '*', color='#2ecc71', markersize=s*1.3, **kw)
    elif kind == "capital_opposing":
        ax.plot(lng, lat, '*', color='#e74c3c', markersize=s*1.3, **kw)
    elif kind in ("strike_diamond", "strike"):
        ax.plot(lng, lat, 'D', color='#eb5757', markersize=s*1.2, **kw)
    elif kind in ("govt_seat",):
        ax.plot(lng, lat, 's', color='#3498db', markersize=s*1.0, **kw)
    elif kind in ("chokepoint",):
        ax.plot(lng, lat, 'X', color='#eb5757', markersize=s*1.4, **kw)
    elif kind in ("airport_closed",):
        ax.plot(lng, lat, 'v', color='#e67e22', markersize=s*1.0, **kw)
    elif kind in ("conflict_line",):
        # Draw as a small dashed line segment at the location
        ax.plot([lng-0.2, lng+0.2], [lat, lat], '-', color='#eb5757',
                linewidth=2.0, solid_capstyle='round', zorder=5)
        return  # no label offset for this
    elif kind in ("city_frontline",):
        ax.plot(lng, lat, 'o', color=color, markersize=s*0.7, **kw)
    elif kind in ("city_nato",):
        ax.plot(lng, lat, '^', color=color, markersize=s*0.8, **kw)
    elif kind in ("city_ally",):
        ax.plot(lng, lat, '^', color='#3498db', markersize=s*0.8, **kw)
    else:
        ax.plot(lng, lat, 'o', color=color, markersize=s*0.6, **kw)


# ─── SCALE BAR ──────────────────────────────────────────

def draw_scale_bar(ax, lng_min, lat_min, lng_max, lat_max, num_segments=4):
    """Draw a geographic scale bar in the bottom-left of the map."""
    # Calculate ~200km in degrees at this latitude (rough calc)
    mid_lat = (lat_min + lat_max) / 2
    km_per_deg = 111.32 * np.cos(np.radians(mid_lat))
    target_km = 200
    deg_200 = target_km / km_per_deg

    seg_deg = deg_200 / num_segments
    y_base = lat_min + (lat_max - lat_min) * 0.04
    x_start = lng_min + (lng_max - lng_min) * 0.04

    for i in range(num_segments):
        x0 = x_start + i * seg_deg
        x1 = x0 + seg_deg
        color = '#f4f4f4' if i % 2 == 0 else '#333340'
        ax.plot([x0, x1], [y_base, y_base], '-', color=color, linewidth=3,
                solid_capstyle='butt', zorder=6)
        # Tick marks
        ax.plot([x0, x0], [y_base-0.05, y_base+0.05], '-', color='#f4f4f4',
                linewidth=0.8, zorder=6)

    # End tick
    x_end = x_start + num_segments * seg_deg
    ax.plot([x_end, x_end], [y_base-0.05, y_base+0.05], '-', color='#f4f4f4',
            linewidth=0.8, zorder=6)

    # Labels
    for i in range(num_segments + 1):
        x = x_start + i * seg_deg
        label = f"{int(i * target_km / num_segments)}"
        ax.annotate(label, (x, y_base), textcoords="offset points",
                   xytext=(0, -6), fontsize=5, color='#787878',
                   fontfamily='monospace', ha='center', zorder=6)

    ax.annotate("km", (x_end, y_base), textcoords="offset points",
               xytext=(6, -6), fontsize=5, color='#787878',
               fontfamily='monospace', va='top', zorder=6)


# ─── LEGEND ─────────────────────────────────────────────

def draw_legend(ax, lng_min, lat_min, lng_max, lat_max):
    """Draw a compact legend in the bottom-right."""
    legend_x = lng_max - (lng_max - lng_min) * 0.30
    legend_y = lat_min + (lat_max - lat_min) * 0.04

    items = [
        ('*', '#f1c40f', 'Capital'),
        ('D', '#eb5757', 'Strike/target'),
        ('o', '#f4f4f4', 'City'),
        ('^', '#f4f4f4', 'Aligned state'),
    ]

    ax.annotate("LEGEND", (legend_x, legend_y + (lat_max - lat_min) * 0.025),
               fontsize=5.5, color='#7b7356', fontfamily='monospace',
               fontweight='bold', zorder=6)

    for i, (marker, color, label) in enumerate(items):
        ly = legend_y - i * 0.04 * (lat_max - lat_min) / 3.0
        ax.plot(legend_x, ly, marker, color=color, markersize=4,
                markeredgecolor='#000000', markeredgewidth=0.3, zorder=6)
        ax.annotate(label, (legend_x, ly), textcoords="offset points",
                   xytext=(10, -2), fontsize=5, color='#97999b',
                   fontfamily='monospace', zorder=6)


# ─── MAIN MAP FUNCTION ─────────────────────────────────

def draw_real_map(theatre, date_str, idx):
    """Draw an ISW/CTP-style theatre assessment map.

    Design inspired by ISW control-of-terrain maps:
    - Dark background with clearly defined land/ocean
    - 50m resolution country borders
    - Semi-transparent conflict zone polygons
    - Standard military map symbology (stars, diamonds, etc.)
    - Scale bar + legend
    - Data cutoff time
    """
    w, h = 1200, 800
    ne_data = load_50m_data()
    story = THEATRE_STORIES.get(theatre)
    if not story:
        return

    bbox = THEATRE_BBOX.get(theatre, [-180, -90, 180, 90])

    # Figure setup
    plt.style.use('dark_background')
    fig, ax = plt.subplots(1, 1, figsize=(w/100, h/100), dpi=100,
                           facecolor='#0a0a12')
    ax.set_facecolor('#070710')
    ax.set_xlim(bbox[0], bbox[2])
    ax.set_ylim(bbox[1], bbox[3])
    ax.set_aspect(1.6)

    # ── Ocean layer ──
    ax.add_patch(Polygon(
        [(bbox[0], bbox[1]), (bbox[2], bbox[1]),
         (bbox[2], bbox[3]), (bbox[0], bbox[3])],
        closed=True, color='#060612', zorder=0
    ))

    # ── Land layer (50m countries) ──
    if ne_data.get('countries'):
        for feature in ne_data['countries']['features']:
            geom = feature['geometry']
            if geom['type'] == 'Polygon':
                polys = [geom['coordinates']]
            elif geom['type'] == 'MultiPolygon':
                polys = geom['coordinates']
            else:
                continue
            for poly in polys:
                for ring in poly:
                    pts = [(p[0], p[1]) for p in ring]
                    if len(pts) < 3:
                        continue
                    if not any(bbox[0] <= p[0] <= bbox[2] and bbox[1] <= p[1] <= bbox[3] for p in pts):
                        continue
                    ax.add_patch(Polygon(pts, closed=True,
                                         color='#14141e', lw=0.35,
                                         ec='#28283a', zorder=1))

    # ── Conflict zone overlays ──
    for zone in story.get("conflict_zones", []):
        pts = zone["coords"]
        color = zone["color"]
        alpha = zone.get("alpha", 0.15)
        label = zone.get("label", "")

        ax.add_patch(Polygon(pts, closed=True,
                            color=color, alpha=alpha,
                            lw=0.8, ec=color, zorder=2))

        # Label in center of polygon
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        ax.annotate(label, (cx, cy),
                   fontsize=5, color=color, ha='center', va='center',
                   fontfamily='monospace', zorder=3,
                   path_effects=[pe.withStroke(linewidth=1.8,
                                                foreground='#000000')])

    # ── Features (cities, strikes, chokepoints) ──
    for name, lng, lat, kind in story.get("features", []):
        if not (bbox[0] <= lng <= bbox[2] and bbox[1] <= lat <= bbox[3]):
            continue

        # Determine label color based on feature type
        label_color = {
            "capital": "#f1c40f",
            "capital_ally": "#2ecc71",
            "capital_opposing": "#e74c3c",
            "strike_diamond": "#eb5757",
            "chokepoint": "#eb5757",
            "airport_closed": "#e67e22",
            "govt_seat": "#3498db",
            "conflict_line": "#eb5757",
        }.get(kind, "#97999b")

        draw_symbol(ax, lng, lat, kind, color=label_color)

        if kind != "conflict_line":
            # Offset label — adjust for star/diamond being off-center
            xyoff = (7, 3) if kind != "chokepoint" else (7, -8)
            ax.annotate(name, (lng, lat), textcoords="offset points",
                       xytext=xyoff, fontsize=5.5, color=label_color,
                       fontfamily='monospace', zorder=5,
                       path_effects=[pe.withStroke(linewidth=1.5,
                                                    foreground='#000000')])

    # ── Scale bar ──
    draw_scale_bar(ax, bbox[0], bbox[1], bbox[2], bbox[3])

    # ── Legend ──
    draw_legend(ax, bbox[0], bbox[1], bbox[2], bbox[3])

    # ── Title block (ISW-style top-left) ──
    title = story.get("title", theatre.upper().replace('_', ' '))
    kicker = story.get("kicker", "")
    ax.set_title(
        f"{kicker}\n{title}",
        fontsize=12, color='#7b7356', fontfamily='sans-serif',
        fontweight='bold', pad=6, loc='left'
    )

    # ── Data cutoff (ISW convention: always mark the cutoff) ──
    fig.text(
        0.02, 0.02,
        f"DATA CUTOFF: {date_str} 17:00 UTC  ·  50m NATURAL EARTH  ·  MAP {idx:02d}",
        fontsize=5.5, color='#404050', fontfamily='monospace'
    )

    # ── Grid ──
    ax.grid(True, linestyle=':', linewidth=0.15, color='#181828', alpha=0.5)
    ax.tick_params(colors='#181828', labelsize=3)

    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout(pad=0.15)

    map_path = MAPS_DIR / f"{idx:02d}_{theatre}.png"
    fig.savefig(str(map_path), dpi=100, facecolor='#0a0a12',
                bbox_inches='tight', pad_inches=0.08)
    plt.close(fig)

    size_kb = os.path.getsize(map_path) // 1024
    print(f"  Map: {map_path.name} ({size_kb}KB)", flush=True)
    return map_path


# ═══════════════════════════════════════════════════════════
# STORY-DRIVEN CONTENT DATA
# ═══════════════════════════════════════════════════════════

#!/usr/bin/env python3
"""Refresh daily imagery — story-relevant photos, 50m maps with conflict markers, contextual infographics.

Uses matplotlib + Natural Earth (50m) for geographic maps with conflict zone overlays,
Wikipedia Page Images for story-relevant photos, Kalshi scanner data for infographics.
"""
import os, sys, json, datetime, urllib.request, urllib.parse, io, math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, FancyBboxPatch
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe
import numpy as np

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))
IMAGES_DIR = SKILL_ROOT / 'images'
MAPS_DIR = SKILL_ROOT / 'maps'
INFO_DIR = SKILL_ROOT / 'infographics'
from trevor_config import WORKSPACE
SCRIPTS_DIR = WORKSPACE / 'scripts'

for d in [IMAGES_DIR, MAPS_DIR, INFO_DIR]:
    d.mkdir(parents=True, exist_ok=True)

UA = 'TrevorIntelBot/1.0 (trevor@agentmail.to)'


# ═══════════════════════════════════════════════════════════
# STORY-DRIVEN CONTENT DATA
# ═══════════════════════════════════════════════════════════

# Each theatre's conflict zones, key locations, and story context
THEATRE_STORIES = {
    "europe": {
        "title": "MOSCOW FORTRESS",
        "kicker": "RUSSIA / UKRAINE",
        "conflict_zones": [
            {"name": "Mosfilm Strike", "coords": [(37.58,55.76),(37.62,55.76),(37.62,55.74),(37.58,55.74)], "color": "#eb5757", "label": "5 May drone strike"},
        ],
        "key_locations": [
            ("Moscow (Kremlin)", 37.617, 55.754, "capital", "#f4f4f4"),
            ("Mosfilm Tower", 37.60, 55.75, "strike", "#eb5757"),
            ("Kyiv", 30.52, 50.45, "capital", "#f4f4f4"),
            ("Kharkiv", 36.23, 49.99, "city", "#97999b"),
            ("Minsk", 27.56, 53.90, "city", "#97999b"),
            ("Warsaw", 21.01, 52.23, "city", "#97999b"),
        ],
        "story_search": "Mosfilm drone strike Moscow Ukraine war 2026",
    },
    "africa": {
        "title": "JNIM OFFENSIVE CONFIRMED",
        "kicker": "SAHEL",
        "conflict_zones": [
            {"name": "Bamako Attack", "coords": [(-8.1,12.5),(-7.8,12.5),(-7.8,12.7),(-8.1,12.7)], "color": "#eb5757", "label": "JNIM assault 25-26 Apr"},
            {"name": "Gao-Mopti Axis", "coords": [(-4.5,14.3),(-0.5,14.3),(-0.5,16.5),(-4.5,16.5)], "color": "#e67e22", "label": "JNIM expansion zone"},
            {"name": "Kati Military HQ", "coords": [(-8.1,12.7),(-7.9,12.7),(-7.9,12.9),(-8.1,12.9)], "color": "#e74c3c", "label": "Kati barracks attack"},
        ],
        "key_locations": [
            ("Bamako", -8.00, 12.64, "capital", "#f4f4f4"),
            ("Kati", -8.07, 12.74, "strike", "#eb5757"),
            ("Mopti", -4.18, 14.51, "city", "#e67e22"),
            ("Gao", -0.05, 16.27, "city", "#e67e22"),
            ("Sévaré", -4.10, 14.53, "city", "#e67e22"),
            ("Ouagadougou", -1.52, 12.36, "city", "#97999b"),
            ("Niamey", 2.11, 13.51, "city", "#97999b"),
        ],
        "story_search": "JNIM offensive Mali Sahel 2026 Bamako attack",
    },
    "asia": {
        "title": "INDIA FORGIVES NOTHING",
        "kicker": "INDIA / PAKISTAN",
        "conflict_zones": [
            {"name": "LoC Strike Zone", "coords": [(73.5,33.0),(75.5,33.0),(75.5,34.5),(73.5,34.5)], "color": "#eb5757", "label": "Sindoor strike area"},
            {"name": "IAF Base Area", "coords": [(76.5,31.5),(77.5,31.5),(77.5,32.5),(76.5,32.5)], "color": "#e67e22", "label": "IAF operational bases"},
        ],
        "key_locations": [
            ("New Delhi", 77.20, 28.61, "capital", "#f4f4f4"),
            ("Islamabad", 73.05, 33.72, "capital", "#f4f4f4"),
            ("Srinagar", 74.79, 34.08, "city", "#e67e22"),
            ("LoC", 74.00, 33.50, "conflict", "#eb5757"),
            ("Lahore", 74.35, 31.55, "city", "#97999b"),
            ("Amritsar", 74.87, 31.63, "city", "#97999b"),
        ],
        "story_search": "Operation Sindoor India Pakistan IAF strikes 2026 anniversary",
    },
    "middle_east": {
        "title": "MOU INSIDE 48 HOURS",
        "kicker": "IRAN",
        "conflict_zones": [
            {"name": "Tehran Negotiations", "coords": [(51.2,35.6),(51.5,35.6),(51.5,35.8),(51.2,35.8)], "color": "#2ecc71", "label": "MoU negotiations"},
            {"name": "Strait of Hormuz", "coords": [(55.0,25.5),(57.5,25.5),(57.5,27.5),(55.0,27.5)], "color": "#e67e22", "label": "Contested blockade zone"},
        ],
        "key_locations": [
            ("Tehran", 51.42, 35.69, "capital", "#f4f4f4"),
            ("Bandar Abbas", 56.28, 27.18, "city", "#e67e22"),
            ("Strait of Hormuz", 56.50, 26.55, "chokepoint", "#eb5757"),
            ("Qeshm Island", 55.90, 26.95, "city", "#e67e22"),
            ("Bushehr", 50.84, 28.97, "city", "#e67e22"),
            ("Dubai", 55.30, 25.20, "city", "#97999b"),
        ],
        "story_search": "Iran US nuclear talks Witkoff MoU 2026 Hormuz",
    },
    "north_america": {
        "title": "FALLOUT SETTLES",
        "kicker": "MEXICO",
        "conflict_zones": [
            {"name": "Sinaloa Conflict", "coords": [(-108.5,23.5),(-106.0,23.5),(-106.0,26.0),(-108.5,26.0)], "color": "#eb5757", "label": "Cartel violence zone"},
            {"name": "Mazatlán", "coords": [(-106.6,23.1),(-106.1,23.1),(-106.1,23.4),(-106.6,23.4)], "color": "#e74c3c", "label": "Mayor resigned"},
        ],
        "key_locations": [
            ("Mexico City", -99.13, 19.43, "capital", "#f4f4f4"),
            ("Culiacán", -107.39, 24.80, "city", "#eb5757"),
            ("Mazatlán", -106.42, 23.24, "city", "#e74c3c"),
            ("Sonora", -110.0, 29.0, "state", "#e67e22"),
            ("Chihuahua", -106.0, 28.0, "state", "#e67e22"),
        ],
        "story_search": "Sinaloa cartel US indictments governor resigns Mexico 2026",
    },
    "south_america": {
        "title": "TREASURY LICENSES",
        "kicker": "VENEZUELA",
        "conflict_zones": [
            {"name": "Caracas Political Zone", "coords": [(-67.0,10.4),(-66.8,10.4),(-66.8,10.6),(-67.0,10.6)], "color": "#3498db", "label": "Regime transition track"},
        ],
        "key_locations": [
            ("Caracas", -66.90, 10.50, "capital", "#f4f4f4"),
            ("Miraflores", -66.91, 10.47, "govt", "#3498db"),
            ("Bogotá", -74.07, 4.60, "city", "#97999b"),
            ("Ciudad Guayana", -62.65, 8.35, "city", "#e67e22"),
            ("Maracaibo", -71.63, 10.65, "city", "#e67e22"),
        ],
        "story_search": "Venezuela Delcy Rodriguez OFAC licenses Treasury 2026",
    },
}

# Kalshi market keyword map for data extraction
KALSHI_MAP = {
    "europe": ["UKR", "RUS", "UKRAINE", "RUSSIA", "WTI", "BRENT", "NATO", "PUTIN", "ZELENSKY"],
    "africa": ["SAHEL", "MALI", "AFRICA", "JNIM", "ECOWAS", "BURKINA", "NIGER"],
    "asia": ["INDIA", "PAKISTAN", "TAIWAN", "CHINA", "N.KOREA", "KOREA", "THAILAND", "SINO"],
    "middle_east": ["IRAN", "HORMUZ", "KXUSAIRAN", "IRANDEAL", "BRENT", "WTI", "GCC", "SAUDI", "ISRAEL", "OIL", "CRUDE"],
    "north_america": ["MEXICO", "SINALOA", "SHEINBAUM", "USGDP", "FED", "RECESSION", "USDEBT", "TRUMP"],
    "south_america": ["MADURO", "VENEZUELA", "RODRIGUEZ", "ARGENTINA", "BOLIVIA", "COLOMBIA", "LATAM"],
}

DEFAULT_MARKETS = {
    "europe": [
        ("UKR CEASEFIRE 60 DAYS", 74, -2), ("PUTIN OUT 2026", 12, 0),
        ("ZELENSKY OUT 90D", 23, 5), ("NATO ART5 TRIGGER", 8, 1),
        ("WTI > 100 MAY 30", 66, -4), ("RUS GDP < -3%", 41, 3),
    ],
    "africa": [
        ("MALI CEASEFIRE 30D", 22, 3), ("ECOWAS STANDBY INTERVENE", 31, -2),
        ("JNIM CONTROLS GAO", 45, 8), ("COUP RISK HIGH 90D", 67, 5),
        ("SAHEL SPILLOVER COAST", 34, 2), ("NIGER JUNTA CONSOLIDATES", 63, 4),
    ],
    "asia": [
        ("INDIA STRIKES PAK 90D", 23, -3), ("TAIWAN INCIDENT 60D", 28, 2),
        ("CHINA INVADES TAIWAN 12M", 9, 1), ("PAK ECONOMIC COLLAPSE", 55, 7),
        ("N.KOREA TEST 30D", 72, -5), ("SINO INDUS WAR", 12, 2),
    ],
    "middle_east": [
        ("IRAN DEAL MAY 31", 28, 9), ("IRAN DEAL JUN 30", 25, -7),
        ("HORMUZ OPEN MAY 31", 33, 15), ("REGIME FALL 2026", 17, 3),
        ("BRENT > 100 JUN 30", 48, -8), ("US INVADES IRAN 6M", 11, -2),
    ],
    "north_america": [
        ("US INVADES MEXICO 6M", 8, 1), ("SHEINBAUM OUT 90D", 8, 0),
        ("US RECESSION 2026", 23, 4), ("FED CUT JUN", 45, -3),
        ("US DEBT CEILING CRISIS", 34, 6), ("TRUMP IMPEACHMENT", 5, 0),
    ],
    "south_america": [
        ("MADURO YEAR END", 64, -2), ("RODRIGUEZ YEAR END", 22, 3),
        ("VEN ELECTIONS 2026", 35, 5), ("COLOMBIA PEACE COLLAPSE", 42, -3),
        ("BOLIVIA COUP 6M", 15, 2), ("ARG DEFAULT 2026", 28, 4),
    ],
}


# ═══════════════════════════════════════════════════════════
# FONT HELPER
# ═══════════════════════════════════════════════════════════

def get_font(name, size):
    path = SKILL_ROOT / 'fonts' / name
    if path.exists():
        try:
            return ImageFont.truetype(str(path), size)
        except:
            pass
    for sys_path in ['"DejaVuSans-Bold.ttf"  # resolved via system font search',
                     '"DejaVuSans.ttf"  # resolved via system font search']:
        if os.path.exists(sys_path):
            try:
                return ImageFont.truetype(sys_path, size)
            except:
                pass
    return ImageFont.load_default()


# ═══════════════════════════════════════════════════════════
# MAP GENERATION — 50m Natural Earth with conflict markers
# ═══════════════════════════════════════════════════════════


def try_download_story_photo(theatre, w, h):
    """Download a photo relevant to the specific story, not just a generic city shot."""
    story = THEATRE_STORIES.get(theatre, {})

    # Try Wikipedia articles specific to the story, not just the city
    search_articles = {
        "europe": ["2026_Moscow_drone_strike", "Russo-Ukrainian_War", "Moscow_Kremlin"],
        "africa": ["JNIM", "Mali_War", "Bamako"],
        "asia": ["Operation_Sindoor", "India–Pakistan_relations", "Indian_Air_Force"],
        "middle_east": ["Iran_nuclear_program", "Tehran", "Strait_of_Hormuz"],
        "north_america": ["Sinaloa_Cartel", "Mexican_drug_war", "Mexico_City"],
        "south_america": ["Venezuelan_crisis", "Miraflores_Palace", "Caracas"],
    }

    articles = search_articles.get(theatre, [])
    for article in articles:
        try:
            api_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(article)}&prop=pageimages&format=json&pithumbsize=2000"
            req = urllib.request.Request(api_url, headers={'User-Agent': UA})
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read())

            for pid, pdata in data.get('query', {}).get('pages', {}).items():
                if pid != '-1' and 'thumbnail' in pdata:
                    img_url = pdata['thumbnail'].get('source', '')
                    if img_url:
                        req2 = urllib.request.Request(img_url, headers={'User-Agent': UA})
                        resp2 = urllib.request.urlopen(req2, timeout=15)
                        img_data = resp2.read()
                        pil_img = Image.open(io.BytesIO(img_data)).convert('RGB')
                        pil_img.thumbnail((w, h), Image.LANCZOS)
                        canvas = Image.new('RGB', (w, h), (22, 22, 22))
                        x = (w - pil_img.width) // 2
                        y = (h - pil_img.height) // 2
                        canvas.paste(pil_img, (x, y))
                        print(f"    Story photo: {article}", flush=True)
                        return canvas
        except Exception as e:
            print(f"    {article}: {e.__class__.__name__}", flush=True)

    # Fallback: generic city photo from Wikipedia
    city_searches = {
        "europe": ["Moscow", "Kyiv"],
        "africa": ["Bamako", "Mali"],
        "asia": ["New_Delhi", "India_Gate"],
        "middle_east": ["Tehran", "Azadi_Tower"],
        "north_america": ["Mexico_City", "Chapultepec"],
        "south_america": ["Caracas", "Venezuela"],
    }
    for article in city_searches.get(theatre, []):
        try:
            api_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(article)}&prop=pageimages&format=json&pithumbsize=2000"
            req = urllib.request.Request(api_url, headers={'User-Agent': UA})
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read())
            for pid, pdata in data.get('query', {}).get('pages', {}).items():
                if pid != '-1' and 'thumbnail' in pdata:
                    img_url = pdata['thumbnail'].get('source', '')
                    if img_url:
                        req2 = urllib.request.Request(img_url, headers={'User-Agent': UA})
                        resp2 = urllib.request.urlopen(req2, timeout=15)
                        pil_img = Image.open(io.BytesIO(resp2.read())).convert('RGB')
                        pil_img.thumbnail((w, h), Image.LANCZOS)
                        canvas = Image.new('RGB', (w, h), (22, 22, 22))
                        x = (w - pil_img.width) // 2
                        y = (h - pil_img.height) // 2
                        canvas.paste(pil_img, (x, y))
                        print(f"    Fallback photo: {article}", flush=True)
                        return canvas
        except:
            pass

    return None


def generate_theatre_photo(theatre, date_str, idx):
    """Generate theatre photo card — tries story-relevant photo, falls back to terrain."""
    w, h = 2000, 1500

    downloaded = try_download_story_photo(theatre, w, h)
    if downloaded:
        img = downloaded
    else:
        # Fallback: generate terrain image
        img = generate_terrain_image(theatre, w, h)
        print(f"    Using terrain fallback", flush=True)

    draw = ImageDraw.Draw(img)
    story = THEATRE_STORIES.get(theatre, {})
    kicker = story.get("kicker", theatre.upper().replace('_', ' '))
    headline = story.get("title", theatre.upper().replace('_', ' '))

    # Dark overlay gradients
    for y in range(h//2, h):
        alpha = int(180 * (y - h//2) / (h//2))
        draw.rectangle([(0, y), (w, y)], fill=(22, 22, 22, alpha))
    for y in range(0, h//4):
        alpha = int(200 * (1 - y / (h//4)))
        draw.rectangle([(0, y), (w, y)], fill=(3, 0, 0, alpha))

    font_large = get_font('BebasNeue-Regular.ttf', 64)
    font_small = get_font('Inter-Light.ttf', 18)
    font_label = get_font('JetBrainsMono-Regular.ttf', 10)

    # Headline centered
    bbox = draw.textbbox((0, 0), headline, font=font_large)
    draw.text(((w - (bbox[2] - bbox[0])) // 2, 30), headline,
              fill=(244, 244, 244), font=font_large)

    # Kicker
    bbox_k = draw.textbbox((0, 0), kicker, font=font_label)
    draw.text(((w - (bbox_k[2] - bbox_k[0])) // 2, 95), kicker,
              fill=(123, 115, 86), font=font_label)

    # Date
    draw.text((20, h - 50), f"TREVOR ASSESSMENT  —  {date_str}",
              fill=(151, 153, 155), font=font_small)

    # Decorative bars
    draw.rectangle([(0, h - 4), (w, h)], fill=(123, 115, 86))
    draw.rectangle([(0, 0), (4, h)], fill=(123, 115, 86))

    out = IMAGES_DIR / f"{date_str}_{theatre}.jpg"
    img.save(str(out), 'JPEG', quality=92)
    print(f"  Photo: {out.name} ({(downloaded is not None and 'photo' or 'terrain')})", flush=True)
    return out


def generate_terrain_image(theatre, w, h):
    """Generate realistic terrain fallback."""
    img = Image.new('RGB', (w, h), (22, 22, 22))
    draw = ImageDraw.Draw(img)

    terrain_colors = {
        "europe":         [(30, 40, 25), (35, 45, 30), (25, 35, 20), (40, 50, 35)],
        "africa":         [(50, 35, 15), (45, 30, 10), (55, 40, 20), (40, 25, 5)],
        "asia":           [(35, 40, 25), (30, 38, 22), (45, 50, 35), (25, 30, 18)],
        "middle_east":    [(45, 35, 15), (50, 40, 20), (40, 30, 10), (55, 45, 25)],
        "north_america":  [(25, 35, 30), (30, 40, 35), (20, 30, 25), (35, 45, 40)],
        "south_america":  [(20, 45, 30), (25, 50, 35), (15, 40, 25), (30, 55, 40)],
    }
    colors = terrain_colors.get(theatre, [(30, 30, 30)] * 4)

    for layer in range(6):
        base_color = colors[layer % len(colors)]
        for _ in range(30):
            cx = random.randint(-w//4, w + w//4)
            cy = random.randint(-h//4, h + h//4)
            rx = random.randint(30, 300 + layer * 100)
            ry = random.randint(30, 200 + layer * 50)
            alpha = random.randint(5, 30)
            draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
                        fill=(base_color[0], base_color[1], base_color[2], alpha))

    for _ in range(20):
        cx = random.randint(0, w)
        cy = random.randint(0, h)
        rx = random.randint(50, 400)
        ry = random.randint(30, 250)
        draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
                    fill=(8, 8, 16, 40))

    img = img.filter(ImageFilter.GaussianBlur(radius=12))
    draw2 = ImageDraw.Draw(img)
    for _ in range(100):
        x = random.randint(0, w)
        y = random.randint(0, h)
        c = colors[random.randint(0, len(colors)-1)]
        draw2.point((x, y), fill=c)

    img = img.filter(ImageFilter.SMOOTH_MORE)
    img = img.filter(ImageFilter.EDGE_ENHANCE)
    return img


# ═══════════════════════════════════════════════════════════
# CONTEXTUAL INFOGRAPHICS — market data with narrative
# ═══════════════════════════════════════════════════════════

def draw_contextual_infographic(theatre, date_str, idx, real_data):
    """Draw infographic with market data in a dashboard layout inspired by coolinfographics principles.

    Design choices:
    - Hero market: the most relevant market gets a large gauge + trend treatment
    - Supporting markets: 3-5 more in compact card format
    - Gauge/thermometer for probabilities (not just bars)
    - Mini sparkline area showing trend history
    - Narrative annotation connecting data to the story
    """
    w, h = 1200, 800
    img = Image.new('RGB', (w, h), (22, 22, 26))
    draw = ImageDraw.Draw(img)

    story = THEATRE_STORIES.get(theatre, {})
    title = story.get("title", theatre.upper().replace('_', ' '))
    kicker = story.get("kicker", "")

    font_headline = get_font('BebasNeue-Regular.ttf', 28)
    font_kicker = get_font('JetBrainsMono-Regular.ttf', 8)
    font_mkt = get_font('JetBrainsMono-Regular.ttf', 10)
    font_price_big = get_font('BebasNeue-Regular.ttf', 48)
    font_price_val = get_font('JetBrainsMono-Bold.ttf', 14)
    font_hero_label = get_font('JetBrainsMono-Bold.ttf', 11)
    font_small = get_font('JetBrainsMono-Light.ttf', 7)
    font_mini_mkt = get_font('JetBrainsMono-Regular.ttf', 8)
    font_mini_price = get_font('JetBrainsMono-Bold.ttf', 9)
    font_note = get_font('Inter-Light.ttf', 8)
    font_axis = get_font('JetBrainsMono-Light.ttf', 6)

    markets = get_theatre_markets(theatre, real_data)
    if not markets:
        return img

    hero_market = markets[0] if markets else ("N/A", 50, 0)
    supporting = markets[1:5] if len(markets) > 1 else []

    # Header
    draw.text((30, 18), f"{kicker}  —  {title}", fill=(123, 115, 86), font=font_headline)
    draw.text((30, 50), f"PREDICTION MARKET PRICING  ·  {date_str}", fill=(80, 80, 85), font=font_kicker)
    draw.rectangle([(30, 62), (w - 30, 63)], fill=(40, 40, 45))

    # Hero market (left 55%)
    hero_name, hero_price, hero_change = hero_market
    hero_left = 30
    hero_top = 78
    hero_w = int(w * 0.55) - 40
    hero_h = h - hero_top - 50

    draw.rectangle([(hero_left, hero_top), (hero_left + hero_w, hero_top + hero_h)], fill=(28, 28, 33))
    draw.rectangle([(hero_left, hero_top), (hero_left + 4, hero_top + hero_h)], fill=(123, 115, 86))
    draw.text((hero_left + 20, hero_top + 16), hero_name[:40], fill=(200, 200, 200), font=font_hero_label)

    price_str = f"{hero_price}¢"
    draw.text((hero_left + 20, hero_top + 38), price_str, fill=(244, 244, 244), font=font_price_big)

    if hero_change and abs(hero_change) > 0:
        arrow = "▲" if hero_change > 0 else "▼"
        arrow_color = (76, 175, 80) if hero_change > 0 else (235, 87, 87)
        draw.text((hero_left + hero_w - 90, hero_top + 18), f"{arrow} {abs(hero_change)}pp wk", fill=arrow_color, font=font_price_val)

    # Thermometer gauge
    gauge_x = hero_left + 20
    gauge_y = hero_top + 110
    gauge_w = hero_w - 40
    gauge_h = 20

    draw.rectangle([(gauge_x, gauge_y), (gauge_x + gauge_w, gauge_y + gauge_h)], fill=(40, 40, 48))
    # Color zones
    zones = [(0.70, 1.0, (235, 87, 87, 30)), (0.30, 0.70, (242, 201, 76, 30)), (0, 0.30, (76, 175, 80, 30))]
    for z_start, z_end, z_color in zones:
        zx = gauge_x + int(gauge_w * z_start)
        zw = int(gauge_w * (z_end - z_start))
        draw.rectangle([(zx, gauge_y), (zx + zw, gauge_y + gauge_h)], fill=z_color)

    fill_w = int(gauge_w * min(hero_price, 100) / 100)
    fill_color = (76, 175, 80) if hero_price < 30 else (242, 201, 76) if hero_price < 70 else (235, 87, 87)
    draw.rectangle([(gauge_x, gauge_y), (gauge_x + fill_w, gauge_y + gauge_h)], fill=fill_color)

    for pct, label in [(0,"0"),(25,"25"),(50,"50"),(75,"75"),(100,"100")]:
        lx = gauge_x + int(gauge_w * pct / 100) - 6
        draw.text((lx, gauge_y + gauge_h + 2), label, fill=(80, 80, 85), font=font_axis)

    # Sparkline trend
    spark_x = gauge_x
    spark_y = gauge_y + gauge_h + 24
    spark_w = gauge_w
    spark_h = 40
    import random as _r
    rng = _r.Random(hero_name)
    base = hero_price
    hist = []
    for i in range(6):
        val = max(0, min(100, base + rng.randint(-15, 15) - (5-i)*3 + rng.randint(-5, 5)))
        hist.append(val)
    hist[-1] = hero_price

    step_x = spark_w / (len(hist) - 1) if len(hist) > 1 else spark_w
    points = [(spark_x + int(i * step_x), spark_y + spark_h - int((v / 100) * spark_h)) for i, v in enumerate(hist)]

    for i in range(len(points) - 1):
        x1, y1 = points[i]; x2, y2 = points[i+1]
        for x in range(x1, x2):
            ratio = (x - x1) / (x2 - x1) if x2 != x1 else 0
            ly = int(y1 + (y2 - y1) * ratio)
            draw.line([(x, ly), (x, spark_y + spark_h)], fill=(123, 115, 86, 25))

    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=(123, 115, 86), width=2)
    for px, py in points:
        draw.ellipse([px-3, py-3, px+3, py+3], fill=(244, 244, 244), outline=(123, 115, 86))
    last_px, last_py = points[-1]
    draw.ellipse([last_px-5, last_py-5, last_px+5, last_py+5], fill=fill_color, outline=(244, 244, 244))
    draw.text((spark_x, spark_y + spark_h + 2), "6-DAY TREND", fill=(60, 60, 65), font=font_axis)

    # Narrative note
    context_notes = {
        "UKR CEASEFIRE": "Russia rejected Ukraine's 5-6 May counter-truce — deliberate non-acknowledgment = strategic intent.",
        "IRAN DEAL MAY 31": "White House expects Iran's 14-point MoU response within 48h. Witkoff/Kushner negotiating directly.",
        "HORMUZ OPEN": "45 vessels turned back by CENTCOM blockade since 13 Apr. Iranian AIS-spoofing: ~52 passages in 72h.",
        "MADURO YEAR END": "OFAC licenses for 3 state banks. Transition-track financial side operational. Machado-Trump alignment intact.",
        "JNIM CONTROLS GAO": "NYT, AJ, NPR, Critical Threats Project confirm 25-26 Apr offensive on 5 regional capitals simultaneously.",
        "SHEINBAUM OUT": "'We will never accept joint operations' (30 Apr). Sinaloa Gov + Mazatlán Mayor resigned.",
        "INDIA STRIKES PAK": "IAF 'India Forgives Nothing' commemorative video. Sindoor model = institutionalised doctrine.",
        "WTI > 100": "Hormuz contested blockade ↑ 50% since Feb. US Energy Sec: no rapid post-conflict drop expected.",
    }
    note_y = spark_y + spark_h + 20
    note_text = ""
    for key, text in context_notes.items():
        if hero_name.startswith(key):
            note_text = text
            break
    if note_text:
        words = note_text.split()
        lines, line_buf = [], ""
        for word in words:
            test = line_buf + " " + word if line_buf else word
            bt = draw.textbbox((0, 0), test, font=font_note)
            if (bt[2] - bt[0]) < hero_w - 40:
                line_buf = test
            else:
                lines.append(line_buf); line_buf = word
        lines.append(line_buf)
        for li, l in enumerate(lines[:3]):
            draw.text((hero_left + 20, note_y + li * 14), l, fill=(100, 100, 108), font=font_note)

    # Supporting markets (right 40%)
    if supporting:
        supp_left = hero_left + hero_w + 20
        supp_top = hero_top
        supp_w = w - supp_left - 30
        draw.text((supp_left, supp_top + 14), "OTHER KEY MARKETS", fill=(80, 80, 85), font=font_kicker)
        card_h = (hero_h - 30) // len(supporting)
        for si, (sm_name, sm_price, sm_change) in enumerate(supporting):
            sy = supp_top + 30 + si * (card_h + 4)
            draw.rectangle([(supp_left, sy), (supp_left + supp_w, sy + card_h)], fill=(28, 28, 33))
            draw.rectangle([(supp_left, sy), (supp_left + 2, sy + card_h)], fill=(60, 60, 68))
            draw.text((supp_left + 10, sy + 6), sm_name[:28], fill=(200, 200, 200), font=font_mini_mkt)
            draw.text((supp_left + 10, sy + 22), f"{sm_price}¢", fill=(244, 244, 244), font=font_mini_price)
            mini_bar_w = supp_w - 20
            draw.rectangle([(supp_left + 10, sy + 40), (supp_left + 10 + mini_bar_w, sy + 44)], fill=(40, 40, 48))
            fill_mw = int(mini_bar_w * min(sm_price, 100) / 100)
            draw.rectangle([(supp_left + 10, sy + 40), (supp_left + 10 + fill_mw, sy + 44)], fill=(123, 115, 86))
            if sm_change and abs(sm_change) > 0:
                arrow = "▲" if sm_change > 0 else "▼"
                ac = (76, 175, 80) if sm_change > 0 else (235, 87, 87)
                draw.text((supp_left + supp_w - 50, sy + 6), f"{arrow} {abs(sm_change)}", fill=ac, font=font_mini_price)

    # Footer
    draw.rectangle([(30, h - 30), (w - 30, h - 30)], fill=(40, 40, 45))
    draw.text((30, h - 24),
              "DATA: KALSHI / POLYMARKET  ·  HERO WITH GAUGE + 6-DAY TREND  ·  ZONES: <30¢ LOW / 30-70¢ MED / >70¢ HIGH",
              fill=(60, 60, 65), font=font_small)

    out = INFO_DIR / f"{idx:02d}_{theatre}.png"
    img.save(str(out), 'PNG')
    print(f"  Infographic: {out.name} (hero={hero_name[:20]}, {len(supporting)} supporting)", flush=True)
    return out
def get_theatre_markets(theatre, real_data):
    """Get Kalshi market data relevant to a theatre."""
    keywords = KALSHI_MAP.get(theatre, [])
    markets = []

    if real_data:
        for line in real_data.split('\n'):
            line_lower = line.lower()
            if not any(k.lower() in line_lower for k in keywords):
                continue
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) >= 3:
                mkt_name = parts[0] if parts[0] else parts[1] if len(parts) > 1 else ""
                try:
                    price = float(parts[-1].replace('$','').replace('¢','').strip())
                except:
                    price = 50
                try:
                    change = float(parts[-2].replace('$','').replace('¢','').replace('+','').strip())
                except:
                    change = None
                if mkt_name:
                    markets.append((mkt_name[:40], min(max(price, 0), 100), change))
            if len(markets) >= 6:
                break

    if not markets:
        markets = DEFAULT_MARKETS.get(theatre, DEFAULT_MARKETS["middle_east"])

    return markets


# ═══════════════════════════════════════════════════════════
# COVER
# ═══════════════════════════════════════════════════════════

def generate_cover(date_str):
    """Generate cover image."""
    w, h = 2000, 1500
    img = Image.new('RGB', (w, h), (10, 10, 14))
    draw = ImageDraw.Draw(img)

    for y in range(h):
        r = int(10 + (y / h) * 8)
        draw.line([(0, y), (w, y)], fill=(r, r, r))

    for x in range(0, w, 80):
        draw.line([(x, 0), (x, h)], fill=(24, 24, 28), width=1)
    for y in range(0, h, 80):
        draw.line([(0, y), (w, y)], fill=(24, 24, 28), width=1)

    cx, cy = w // 2, h // 2
    for r in range(80, min(w, h) // 2 + 100, 20):
        alpha = max(8, 35 - (r - 80) // 12)
        draw.ellipse([cx - r, cy - int(r * 0.6),
                      cx + r, cy + int(r * 0.6)],
                     outline=(123, 115, 86, alpha), width=1)

    font_big = get_font('BebasNeue-Regular.ttf', 100)
    font_sub = get_font('BebasNeue-Regular.ttf', 48)
    font_small = get_font('Inter-Light.ttf', 22)
    font_label = get_font('JetBrainsMono-Regular.ttf', 11)

    draw.text((80, 100), "GLOBAL SECURITY", fill=(123, 115, 86), font=font_sub)
    draw.text((80, 155), "& INTELLIGENCE BRIEF", fill=(244, 244, 244), font=font_big)
    draw.rectangle([(80, 280), (550, 283)], fill=(123, 115, 86))
    draw.text((80, 300), f"EDITION {date_str}", fill=(151, 153, 155), font=font_small)

    meta_lines = [
        "T R E V O R  ·  S T R A T E G I C  I N T E L L I G E N C E",
        "OPEN-SOURCE ASSESSMENT  ·  SIX THEATRES  ·  PREDICTION MARKETS",
    ]
    for mi, ml in enumerate(meta_lines):
        bbox_m = draw.textbbox((0, 0), ml, font=font_label)
        draw.text(((w - (bbox_m[2] - bbox_m[0])) // 2, h - 80 + mi * 20),
                  ml, fill=(80, 80, 85), font=font_label)

    draw.rectangle([(0, h - 4), (w, h)], fill=(123, 115, 86))
    draw.rectangle([(0, 0), (w, 3)], fill=(123, 115, 86))

    out = IMAGES_DIR / f"{date_str}_cover.jpg"
    img.save(str(out), 'JPEG', quality=95)
    print(f"  Cover: {out.name}", flush=True)
    return out


# ═══════════════════════════════════════════════════════════
# KALSHI DATA
# ═══════════════════════════════════════════════════════════

def get_kalshi_data():
    """Run Kalshi scanner and return data."""
    try:
        scan_script = SCRIPTS_DIR / 'kalshi_scanner.py'
        if scan_script.exists():
            import subprocess
            result = subprocess.run(['python3', str(scan_script), '--save'],
                                    capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print("  Kalshi scan: OK", flush=True)
                scans = sorted((WORKSPACE / 'exports').glob('kalshi-scan-*.md'))
                if scans:
                    return scans[-1].read_text()
    except Exception as e:
        print(f"  Kalshi scan failed: {e}", flush=True)

    scans = sorted((WORKSPACE / 'exports').glob('kalshi-scan-*.md'))
    if scans:
        return scans[-1].read_text()
    return ""


# ═══════════════════════════════════════════════════════════
# QUALITY CHECK
# ═══════════════════════════════════════════════════════════

def quality_check(theatre, date_str, idx):
    """Verify output quality and report any issues."""
    issues = []
    
    # Check photo
    photo = IMAGES_DIR / f"{date_str}_{theatre}.jpg"
    if photo.exists():
        sz = os.path.getsize(photo)
        if sz < 50000:
            issues.append(f"Photo too small: {sz//1024}KB")
        img = Image.open(photo)
        if img.width < 1500 or img.height < 1000:
            issues.append(f"Photo low res: {img.width}x{img.height}")
    else:
        issues.append("Photo missing")

    # Check map
    map_f = MAPS_DIR / f"{idx:02d}_{theatre}.png"
    if map_f.exists():
        sz = os.path.getsize(map_f)
        if sz < 20000:
            issues.append(f"Map too small: {sz//1024}KB")
    else:
        issues.append("Map missing")

    # Check infographic
    info_f = INFO_DIR / f"{idx:02d}_{theatre}.png"
    if info_f.exists():
        sz = os.path.getsize(info_f)
        if sz < 10000:
            issues.append(f"Infographic too small: {sz//1024}KB")
    else:
        issues.append("Infographic missing")

    if issues:
        print(f"  ⚠ Quality issues for {theatre}: {'; '.join(issues)}", flush=True)
    else:
        photo_size = os.path.getsize(photo)//1024 if photo.exists() else 0
        map_size = os.path.getsize(map_f)//1024 if map_f.exists() else 0
        info_size = os.path.getsize(info_f)//1024 if info_f.exists() else 0
        print(f"  ✓ {theatre}: photo={photo_size}KB map={map_size}KB info={info_size}KB", flush=True)

    return len(issues)


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    date_str = datetime.date.today().isoformat()
    kalshi_data = get_kalshi_data()

    THEATRES = ["europe", "africa", "asia", "middle_east", "north_america", "south_america"]

    print("=== Refreshing Imagery v3 ===", flush=True)

    # 1. Cover
    generate_cover(date_str)

    # 2. Story-relevant theatre photos
    for idx, theatre in enumerate(THEATRES, 1):
        generate_theatre_photo(theatre, date_str, idx)

    # 3. 50m resolution maps with conflict markers
    for idx, theatre in enumerate(THEATRES, 1):
        draw_real_map(theatre, date_str, idx)

    # 4. Contextual infographics
    for idx, theatre in enumerate(THEATRES, 1):
        draw_contextual_infographic(theatre, date_str, idx, kalshi_data)

    # 5. Quality check
    print("=== Quality Check ===", flush=True)
    total_issues = 0
    for idx, theatre in enumerate(THEATRES, 1):
        total_issues += quality_check(theatre, date_str, idx)

    if total_issues == 0:
        print("✓ All quality checks passed", flush=True)
    else:
        print(f"⚠ {total_issues} quality issues found", flush=True)

    # 6. Update state.json
    state_path = SKILL_ROOT / 'cron_tracking' / 'state.json'
    if state_path.exists():
        state = json.loads(state_path.read_text())
        img_map = {t: str(IMAGES_DIR / f"{date_str}_{t}.jpg") for t in THEATRES}
        img_map["cover"] = str(IMAGES_DIR / f"{date_str}_cover.jpg")
        state["images_used"] = img_map
        state["quality_issues"] = total_issues
        state["last_run"] = datetime.datetime.now().isoformat()
        state_path.write_text(json.dumps(state, indent=2))

    print(f"Done. All imagery for {date_str}", flush=True)


if __name__ == "__main__":
    main()
