#!/usr/bin/env python3
"""
Grain Supply Monitor — Pipeline

Queries Sentinel-2 L2A via Microsoft Planetary Computer, reads bands at
coarse resolution (~100m), computes NDVI and historical percentiles.

Usage:
    python3 grain_supply_monitor.py [--date YYYY-MM-DD] [--aoi US-CB,BR-MT]
"""

import sys, os, json, argparse, signal
from datetime import datetime, timedelta, date
from pathlib import Path
import numpy as np
from pyproj import Transformer

import pystac_client
import planetary_computer as pc
import rasterio
from rasterio.windows import from_bounds

BASE_DIR = Path(__file__).parent
AOI_PATH = BASE_DIR / "aois" / "aoi_definitions.json"
OUTPUT_DIR = BASE_DIR / "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
HISTORICAL_YEARS = [2022, 2023, 2024, 2025]
SAMPLES_PER_REGION = 3       # samples per region
MAX_TILES = 3                # max tiles per sample
READ_FACTOR = 10             # read every 10th pixel = 100m resolution from 10m

# ── Data Sources ──────────────────────────────────────────────
def get_catalog():
    return pystac_client.Client.open(STAC_URL, modifier=pc.sign_inplace)

def load_aois(aoi_ids=None):
    with open(AOI_PATH) as f:
        data = json.load(f)
    regions = data["regions"]
    if aoi_ids:
        regions = [r for r in regions if r["id"] in aoi_ids]
    return regions


def read_tile_band(url, bbox_wgs84, crs_target=None):
    """Read a band tile, returning data array or None. Uses coarse read factor."""
    with rasterio.open(url) as src:
        crs = src.crs
        transformer = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        lons = transformer.transform(bbox_wgs84[0], bbox_wgs84[1])
        lats = transformer.transform(bbox_wgs84[2], bbox_wgs84[3])
        proj = (
            min(lons[0], lats[0]),
            min(lons[1], lats[1]),
            max(lons[0], lats[0]),
            max(lons[1], lats[1]),
        )

        bounds = src.bounds
        overlap = (
            max(proj[0], bounds[0]), max(proj[1], bounds[1]),
            min(proj[2], bounds[2]), min(proj[3], bounds[3]),
        )
        if overlap[0] >= overlap[2] or overlap[1] >= overlap[3]:
            return None

        window = from_bounds(overlap[0], overlap[1], overlap[2], overlap[3], src.transform)
        window = rasterio.windows.Window(
            col_off=int(max(0, window.col_off)),
            row_off=int(max(0, window.row_off)),
            width=int(min(src.width - max(0, window.col_off), window.width)),
            height=int(min(src.height - max(0, window.row_off), window.height)),
        )
        if window.width < 10 or window.height < 10:
            return None

        # Read at reduced resolution to avoid massive downloads
        out_shape = (
            int(window.height / READ_FACTOR),
            int(window.width / READ_FACTOR),
        )
        if out_shape[0] < 1 or out_shape[1] < 1:
            return None

        data = src.read(1, window=window, out_shape=out_shape).astype(np.float32)
        return data


def _search_with_backoff(catalog, bbox, start, end, max_cc=30):
    """Search STAC with cloud cover backoff. Tries wider window and higher CC tolerance."""
    # Primary: strict cloud cover
    items = _do_search(catalog, bbox, start, end, max_cc)
    if items:
        return items
    # Fallback 1: wider window
    s2 = (datetime.strptime(start, "%Y-%m-%d") - timedelta(days=10)).strftime("%Y-%m-%d")
    e2 = (datetime.strptime(end, "%Y-%m-%d") + timedelta(days=10)).strftime("%Y-%m-%d")
    items = _do_search(catalog, bbox, s2, e2, max_cc)
    if items:
        return items
    # Fallback 2: wider window + higher CC tolerance
    items = _do_search(catalog, bbox, s2, e2, 60)
    return items

def _do_search(catalog, bbox, start, end, max_cc):
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        bbox=bbox,
        datetime=f"{start}/{end}",
        query={"eo:cloud_cover": {"lt": max_cc}},
    )
    return list(search.items())

def compute_ndvi_for_sample(sample, target, catalog, cdays=7):
    """Compute NDVI for a sample bbox at target date ±cdays."""
    bbox = sample["bbox"]
    start = (target - timedelta(days=cdays)).strftime("%Y-%m-%d")
    end = (target + timedelta(days=cdays)).strftime("%Y-%m-%d")

    items = _search_with_backoff(catalog, bbox, start, end)
    if not items:
        return None, "NO_DATA"

    pixels = []
    tiles = 0
    clouds = []
    seen = set()

    for item in items:
        if item.id in seen:
            continue
        seen.add(item.id)
        if tiles >= MAX_TILES:
            break

        cc = item.properties.get("eo:cloud_cover", 100)
        if cc >= 60:
            continue
        clouds.append(cc)

        if "B04" not in item.assets or "B08" not in item.assets:
            continue

        try:
            b04 = read_tile_band(pc.sign(item.assets["B04"].href), bbox)
            if b04 is None:
                continue
            b08 = read_tile_band(pc.sign(item.assets["B08"].href), bbox)
            if b08 is None:
                continue

            mask = (b04 > 0) & (b08 > 0) & (b04 < 10000) & (b08 < 10000)
            ndvi = np.where(mask, ((b08 - b04) / (b08 + b04 + 1e-10)) / 10000.0 * 10000, np.nan)
            # Oops — I already divided by 10000 in a weird way. Let me fix:
            # NDVI = (B08 - B04) / (B08 + B04), where B04 and B08 are reflectances (0-1)
            b04_n = b04 / 10000.0
            b08_n = b08 / 10000.0
            ndvi = np.where(mask, (b08_n - b04_n) / (b08_n + b04_n + 1e-10), np.nan)

            valid = ndvi[~np.isnan(ndvi)]
            if len(valid) > 50:
                pixels.extend(valid.tolist())
                tiles += 1
        except Exception:
            continue

    if not pixels:
        return None, "NO_PIXELS"
    a = np.array(pixels)
    return {
        "mean": float(np.mean(a)),
        "median": float(np.median(a)),
        "std": float(np.std(a)),
        "p10": float(np.percentile(a, 10)),
        "p90": float(np.percentile(a, 90)),
        "n": int(len(a)),
        "tiles": tiles,
        "cc": float(np.mean(clouds)) if clouds else None,
    }, "OK"


def compute_region_ndvi(region, target, catalog, cdays=7):
    """Average NDVI across sampling sub-regions for a region."""
    samples_raw = region.get("sampling_regions", [])
    # Only use first N samples for speed
    samples = samples_raw[:SAMPLES_PER_REGION]

    means = []
    details = []
    for s in samples:
        r, st = compute_ndvi_for_sample(s, target, catalog, cdays)
        if r:
            means.append(r["mean"])
            details.append({**s, "ndvi": r["mean"], "tiles": r["tiles"]})
        else:
            print(f"    ⚠ '{s['name']}': {st}")

    if not means:
        return None, "NO_SAMPLES"
    a = np.array(means)
    return {
        "mean": float(np.mean(a)),
        "median": float(np.median(a)),
        "std": float(np.std(a)),
        "samples": details,
    }, "OK"


def compute_historical(region, target, catalog, current_ndvi):
    """Compute percentile vs same-window historical years."""
    vals = []
    for y in HISTORICAL_YEARS:
        try:
            d = target.replace(year=y)
        except ValueError:
            continue
        if d >= date.today():
            continue
        r, st = compute_region_ndvi(region, datetime.combine(d, datetime.min.time()), catalog, cdays=15)
        if r:
            vals.append(r["mean"])
            print(f"    Hist {y}: NDVI={r['mean']:.4f}")

    if len(vals) < 2:
        return {"percentile": None, "band": "INSUFFICIENT_DATA", "years": len(vals), "values": vals}

    a = np.array(vals)
    pct = float(np.sum(a < current_ndvi) / len(a) * 100)
    band = (
        "WELL_ABOVE_NORMAL" if pct >= 90 else
        "ABOVE_NORMAL" if pct >= 70 else
        "NEAR_NORMAL" if pct >= 30 else
        "BELOW_NORMAL" if pct >= 10 else
        "WELL_BELOW_NORMAL"
    )
    return {"percentile": round(pct, 1), "band": band, "years": len(vals), "values": [round(v, 4) for v in vals]}


def compute_delta(region, target, catalog, current_ndvi):
    prev = target - timedelta(days=30)
    r, st = compute_region_ndvi(region, prev, catalog)
    if not r:
        return None
    c = current_ndvi - r["mean"]
    return {"change": round(c, 4), "prior": round(r["mean"], 4),
            "dir": "INCREASING" if c > 0.02 else ("DECREASING" if c < -0.02 else "STABLE"),
            "date": prev.strftime("%Y-%m-%d")}


def admiralty(region, result, gt):
    ns = len(result.get("samples", []))
    src = "A" if ns >= 2 else "B"
    info = "1" if gt else "2"
    return {"nato": f"{src}{info}", "source": src, "info": info}


def ground_truth(rid):
    table = {
        "US-CB": (True, ["USDA WASDE", "USDA Crop-CASMA"]),
        "BR-MT": (True, ["CONAB"]),
        "EU-FR": (True, ["EU MARS (JRC)"]),
    }
    return table.get(rid, (False, ["FAO GIEWS"]))


# ── Main ──────────────────────────────────────────────────────
def run_pipeline(target_date=None, aoi_ids=None, output_path=None):
    td = target_date or date.today()
    if isinstance(td, str):
        td = datetime.strptime(td, "%Y-%m-%d").date()
    print(f"\nGRAIN SUPPLY MONITOR — {td}")
    print("=" * 60)

    catalog = get_catalog()
    regions = load_aois(aoi_ids)

    out = {"product": "grain_supply_monitor", "report_date": td.strftime("%Y-%m-%d"),
           "regions": [], "pipeline": {"source": "Planetary Computer Sentinel-2 L2A",
                                       "resolution_m": 100, "hist_years": HISTORICAL_YEARS}}

    for region in regions:
        rid = region["id"]
        nm = region["name"]
        print(f"\n── {rid}: {nm} ──")

        r, st = compute_region_ndvi(region, td, catalog)
        if not r:
            out["regions"].append({"region_id": rid, "region_name": nm, "status": "ERROR", "error": st})
            print(f"  ❌ {st}")
            continue

        ndvi = r["mean"]
        print(f"  NDVI: {ndvi:.4f} ({len(r['samples'])} samples)")

        hist = compute_historical(region, td, catalog, ndvi)
        if hist["percentile"] is not None:
            print(f"  Hist: {hist['percentile']:.0f}% ({hist['band']})")
        else:
            print(f"  Hist: {hist['band']}")

        delta = compute_delta(region, td, catalog, ndvi)
        if delta:
            print(f"  30d: {delta['change']:.4f} ({delta['dir']})")

        gt, gs = ground_truth(rid)
        conf = admiralty(region, r, gt)
        print(f"  Conf: {conf['nato']}")

        alert = hist.get("band") in ("WELL_BELOW_NORMAL", "WELL_ABOVE_NORMAL") if hist.get("band") else False

        out["regions"].append({
            "region_id": rid,
            "region_name": nm,
            "crops": region["crops"],
            "ndvi": {"current": round(r["mean"], 4), "median": round(r["median"], 4),
                     "std": round(r["std"], 4), "samples": r["samples"]},
            "historical": hist,
            "delta_30d": delta or {"status": "UNAVAILABLE"},
            "ground_truth": {"available": gt, "sources": gs},
            "confidence": conf,
            "alert": alert,
            "status": "OK",
        })
        print(f"  ✅")

    op = output_path or OUTPUT_DIR / f"gsm-{td.strftime('%Y-%m-%d')}.json"
    with open(op, "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\n{'='*60}\nWritten: {op}")

    print(f"\n{'ID':<8} {'NDVI':>6} {'Pctl':>5} {'Band':<22} {'Conf':>4}")
    print("-" * 50)
    for r2 in out["regions"]:
        if r2["status"] == "OK":
            p = r2["historical"].get("percentile")
            b = r2["historical"].get("band", "?")
            p_str = f"{p:<5.0f}" if p is not None else "?    "
            print(f"{r2['region_id']:<8} {r2['ndvi']['current']:>6.4f} "
                  f"{p_str} {b:<22} {r2['confidence']['nato']:>4}")
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--date")
    p.add_argument("--aoi")
    p.add_argument("--output")
    a = p.parse_args()
    run_pipeline(target_date=a.date, aoi_ids=a.aoi.split(",") if a.aoi else None, output_path=a.output)
