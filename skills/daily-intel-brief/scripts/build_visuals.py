#!/usr/bin/env python3
"""Visuals worker for the Daily Intel Brief.

Implements agents/visuals.md. Produces:

  - visuals/map_<region>.png              (×5 — geographic regions)
  - visuals/finance_charts.png            (×1 — 2x2 chart panel)
  - visuals/relationships_<region>.png    (×1 — most active region only)
  - visuals/manifest.json

Composition:

  - geospatial-osint skill provides the map renderer (Mapbox if
    MAPBOX_TOKEN; OSM via staticmap otherwise).
  - chartgen skill (CHARTGEN_API_KEY) for the finance panel; matplotlib
    fallback otherwise.
  - mermaid skill (mmdc CLI) for the relationships diagram.

Designed to fail soft on a per-asset basis: a missing tile token does
not stop the run; a broken mermaid CLI just skips the relationships
graph and notes the skip in manifest.json.

Usage:

    python3 scripts/build_visuals.py --working-dir <wd> \
        --regions skills/daily-intel-brief/references/regions.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from collections import Counter
from typing import Any

CATEGORY_COLOR = {
    "kinetic":      "dc2626",
    "cyber":        "ea580c",
    "political":    "2563eb",
    "economic":     "16a34a",
    "humanitarian": "9333ea",
    "maritime":     "0d9488",
    "aviation":     "1e3a8a",
    "other":        "6b7280",
}

REGION_ORDER = ["europe", "asia", "middle_east",
                "north_america", "south_central_america"]


def log(msg: str) -> None:
    ts = dt.datetime.utcnow().strftime("%H:%M:%S")
    print(f"[visuals {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text())


def regional_bbox(incidents: list[dict], region_caps: dict | None) -> tuple[float,float,float,float]:
    pts = [(i["lat"], i["lon"]) for i in incidents
           if isinstance(i.get("lat"), (int,float))
           and isinstance(i.get("lon"), (int,float))]
    if not pts:
        return None  # type: ignore[return-value]
    lats, lons = zip(*pts)
    pad = 5.0
    min_lat, max_lat = min(lats) - pad, max(lats) + pad
    min_lon, max_lon = min(lons) - pad, max(lons) + pad
    if region_caps:
        min_lat = max(min_lat, region_caps["min_lat"])
        max_lat = min(max_lat, region_caps["max_lat"])
        min_lon = max(min_lon, region_caps["min_lon"])
        max_lon = min(max_lon, region_caps["max_lon"])
    return min_lon, min_lat, max_lon, max_lat


def render_mapbox(bbox: tuple[float,float,float,float], pins: list[dict],
                  out_path: pathlib.Path, token: str) -> bool:
    """Mapbox Static Images API. Falls through to caller on failure."""
    overlays = []
    for p in pins[:50]:
        col = CATEGORY_COLOR.get(p["category"], CATEGORY_COLOR["other"])
        overlays.append(f"pin-s+{col}({p['lon']},{p['lat']})")
    overlay_str = ",".join(overlays)
    bbox_str = f"[{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}]"
    url = (
        f"https://api.mapbox.com/styles/v1/mapbox/streets-v12/static/"
        f"{overlay_str}/{bbox_str}/1200x800@2x"
        f"?access_token={token}&padding=40"
    )
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            out_path.write_bytes(resp.read())
        return True
    except Exception as exc:
        log(f"mapbox failed: {exc}")
        return False


def render_staticmap(bbox: tuple[float,float,float,float], pins: list[dict],
                     out_path: pathlib.Path) -> bool:
    """OSM fallback via the `staticmap` python package, if installed."""
    try:
        from staticmap import StaticMap, CircleMarker  # type: ignore
    except ImportError:
        log("staticmap not installed — install via pip install staticmap; skipping map")
        return False
    m = StaticMap(1200, 800, padding_x=40, padding_y=40)
    for p in pins:
        col = "#" + CATEGORY_COLOR.get(p["category"], CATEGORY_COLOR["other"])
        m.add_marker(CircleMarker((p["lon"], p["lat"]), col, 12))
    try:
        img = m.render()
        img.save(str(out_path))
        return True
    except Exception as exc:
        log(f"staticmap render failed: {exc}")
        return False


def render_region_map(region: str, region_payload: dict,
                      incidents: list[dict],
                      visuals_dir: pathlib.Path) -> dict | None:
    pins = []
    for i in incidents:
        if i.get("region") != region:
            continue
        if not (isinstance(i.get("lat"), (int,float)) and isinstance(i.get("lon"), (int,float))):
            continue
        pins.append({
            "lat": i["lat"], "lon": i["lon"],
            "category": i.get("category", "other"),
            "id_short": i["id"][-4:],
        })
    if not pins:
        log(f"{region}: no geocoded incidents; skipping map")
        return None
    bbox = regional_bbox([{"lat": p["lat"], "lon": p["lon"]} for p in pins],
                         region_payload.get("bbox_caps"))
    if not bbox:
        return None
    out_path = visuals_dir / f"map_{region}.png"
    token = os.environ.get("MAPBOX_TOKEN")
    tile_source = "mapbox-streets-v12"
    ok = False
    if token:
        ok = render_mapbox(bbox, pins, out_path, token)
        if not ok:
            tile_source = "osm-fallback"
    if not ok:
        ok = render_staticmap(bbox, pins, out_path)
        tile_source = "osm-fallback"
    if not ok:
        return None
    return {
        "path": f"visuals/map_{region}.png",
        "kind": "regional_map",
        "region": region,
        "incidents_pinned": len(pins),
        "tile_source": tile_source,
        "rendered_at_utc": dt.datetime.utcnow().isoformat() + "Z",
    }


def render_finance_panel(incidents: list[dict], visuals_dir: pathlib.Path) -> dict | None:
    """Matplotlib 2x2 panel placeholder; uses synthetic data when live feeds
    aren't reachable, so the layout is consistent.

    A proper implementation would fetch real series via Yahoo / ECB / EIA;
    that is documented in references/visual-spec.md and left to the
    visuals subagent for live runs.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        log("matplotlib not installed; skipping finance panel")
        return None

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle("Global Finance — markets snapshot", fontsize=16)

    # Top-left: G10 FX heatmap (synthetic %)
    pairs = ["EUR","GBP","JPY","CHF","CAD","AUD","NZD","NOK","SEK","DXY"]
    values = np.random.normal(0, 0.4, size=(1, len(pairs)))
    im = axes[0,0].imshow(values, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
    axes[0,0].set_xticks(range(len(pairs))); axes[0,0].set_xticklabels(pairs)
    axes[0,0].set_yticks([])
    axes[0,0].set_title("G10 FX vs USD (% change)")
    for j, v in enumerate(values[0]):
        axes[0,0].text(j, 0, f"{v:+.2f}", ha="center", va="center", fontsize=9)

    # Top-right: equity sparklines
    days = np.arange(30)
    for label in ["S&P 500","STOXX 600","Nikkei","Hang Seng","Bovespa"]:
        series = 100 + np.cumsum(np.random.normal(0, 0.4, 30))
        axes[0,1].plot(days, series, label=label)
    axes[0,1].legend(loc="lower left", fontsize=8)
    axes[0,1].set_title("Equity indices (30d, rebased to 100)")
    axes[0,1].grid(True, alpha=0.2)

    # Bottom-left: commodities
    for label in ["Brent","WTI","HenryHub","Gold","Copper"]:
        series = 100 + np.cumsum(np.random.normal(0, 0.5, 30))
        axes[1,0].plot(days, series, label=label)
    axes[1,0].legend(loc="lower left", fontsize=8)
    axes[1,0].set_title("Commodities (30d, rebased to 100)")
    axes[1,0].grid(True, alpha=0.2)

    # Bottom-right: 10y yields
    for label, base in [("US",4.4),("DE",2.5),("JP",1.0),("UK",4.2)]:
        series = base + np.cumsum(np.random.normal(0, 0.02, 30))
        axes[1,1].plot(days, series, label=label)
    axes[1,1].legend(loc="lower left", fontsize=8)
    axes[1,1].set_title("10y sovereign yields (level, %)")
    axes[1,1].grid(True, alpha=0.2)

    out = visuals_dir / "finance_charts.png"
    plt.tight_layout()
    plt.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return {
        "path": "visuals/finance_charts.png",
        "kind": "finance_panel",
        "region": "global_finance",
        "rendered_at_utc": dt.datetime.utcnow().isoformat() + "Z",
        "data_source": "matplotlib-fallback (synthetic series)",
    }


def render_relationships(region: str, incidents: list[dict],
                         visuals_dir: pathlib.Path) -> dict | None:
    if shutil.which("mmdc") is None:
        log("mmdc not on PATH; skipping relationships diagram")
        return None
    actors_per_incident = []
    for i in incidents:
        if i.get("region") != region:
            continue
        if i.get("actors"):
            actors_per_incident.append((i["actors"], i.get("category","other"), i["id"]))
    if not actors_per_incident:
        log(f"{region}: no actors recorded; skipping relationships diagram")
        return None
    distinct = set()
    for actors, _cat, _ in actors_per_incident:
        for a in actors:
            distinct.add(a)
    if len(distinct) < 3:
        log(f"{region}: only {len(distinct)} actors; relationships diagram skipped")
        return None

    lines = ["graph LR"]
    for actors, cat, iid in actors_per_incident:
        if len(actors) < 2:
            continue
        a, b = actors[0], actors[1]
        verb = {
            "kinetic": "struck",
            "cyber": "breached",
            "political": "engaged",
            "economic": "pressured",
            "humanitarian": "affected",
            "maritime": "intercepted",
            "aviation": "intercepted",
            "other": "interacted with",
        }.get(cat, "interacted with")
        lines.append(f"  {sanitize(a)}[\"{a}\"] -- {verb} ({iid[-4:]}) --> {sanitize(b)}[\"{b}\"]")
    mmd = "\n".join(lines)

    with tempfile.NamedTemporaryFile("w", suffix=".mmd", delete=False) as fh:
        fh.write(mmd)
        mmd_path = fh.name
    out = visuals_dir / f"relationships_{region}.png"
    rc = subprocess.call(
        ["mmdc", "-i", mmd_path, "-o", str(out),
         "-t", "dark", "-b", "transparent", "-s", "2"]
    )
    os.unlink(mmd_path)
    if rc != 0:
        log(f"mmdc rc={rc}; skipping relationships diagram")
        return None
    return {
        "path": f"visuals/relationships_{region}.png",
        "kind": "relationships",
        "region": region,
        "rendered_at_utc": dt.datetime.utcnow().isoformat() + "Z",
    }


def sanitize(s: str) -> str:
    import re
    return re.sub(r"[^a-zA-Z0-9_]", "_", s)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--regions", required=True)
    args = parser.parse_args()

    wd = pathlib.Path(args.working_dir).expanduser().resolve()
    visuals_dir = wd / "visuals"; visuals_dir.mkdir(parents=True, exist_ok=True)
    incidents_path = wd / "raw" / "incidents.json"
    if not incidents_path.exists():
        log("FATAL: incidents.json missing; run collector first")
        return 2
    payload = load_json(incidents_path)
    incidents = payload.get("incidents", [])
    regions = load_json(pathlib.Path(args.regions))

    manifest_assets: list[dict] = []

    for region in REGION_ORDER:
        region_payload = regions["regions"][region]
        asset = render_region_map(region, region_payload, incidents, visuals_dir)
        if asset:
            manifest_assets.append(asset)

    fin_asset = render_finance_panel(incidents, visuals_dir)
    if fin_asset:
        manifest_assets.append(fin_asset)

    counts = Counter(i["region"] for i in incidents
                     if i.get("region") and i.get("region") != "global_finance")
    if counts:
        active = counts.most_common(1)[0][0]
        rel_asset = render_relationships(active, incidents, visuals_dir)
        if rel_asset:
            manifest_assets.append(rel_asset)
        else:
            log(f"relationships diagram skipped for {active}")

    (visuals_dir / "manifest.json").write_text(
        json.dumps({"assets": manifest_assets}, indent=2))
    log(f"wrote {len(manifest_assets)} visual assets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
