#!/usr/bin/env python3
"""Stage 3 — Static Maps via Mapbox API.

Generates branded static map PNGs for geographic brief sections.
One provider: Mapbox Static API (dark-v11 style).

Self-test: MAPBOX_TOKEN set? Endpoint reachable?
If fail, logs "STAGE 3 DISABLED: reason" and exits clean.

Budget: $0.00 within Mapbox free tier (50K tile loads/month).

Usage:
    python3 scripts/present/stage3_map.py \\
        --center -101.2 20.9 --zoom 5 \\
        --output exports/maps/overview.png

    python3 scripts/present/stage3_map.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request
from typing import Optional

WORKSPACE = pathlib.Path("/home/ubuntu/.openclaw/workspace")
STYLE = "dark-v11"


def self_test() -> list[str]:
    """Check prerequisites. Returns list of failures (empty = pass)."""
    failures = []
    token = ""
    env_path = WORKSPACE / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("MAPBOX_TOKEN="):
                token = line.split("=", 1)[1].strip('"').strip("'")
                break
    if not token:
        failures.append("MAPBOX_TOKEN not set in .env")

    if token:
        test_url = (
            f"https://api.mapbox.com/styles/v1/mapbox/{STYLE}/static/"
            f"0,0,2/50x50?access_token={token}&attribution=false"
        )
        try:
            req = urllib.request.Request(test_url,
                                         headers={"User-Agent": "Trevor-Present/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status != 200:
                    failures.append(f"Mapbox API returned HTTP {resp.status}")
        except Exception as exc:
            failures.append(f"Mapbox endpoint unreachable: {exc}")

    return failures


def _get_token() -> str:
    """Get Mapbox token from .env."""
    token = os.environ.get("MAPBOX_TOKEN", "")
    if not token:
        env_path = WORKSPACE / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("MAPBOX_TOKEN="):
                    token = line.split("=", 1)[1].strip('"').strip("'")
                    break
    if not token:
        raise RuntimeError("MAPBOX_TOKEN not set")
    return token


def render_map(
    center_lon: float,
    center_lat: float,
    output_path: str,
    zoom: int = 4,
    width: int = 1200,
    height: int = 800,
    markers: Optional[list[dict]] = None,
) -> str:
    """Generate a static map PNG via Mapbox Static API."""
    token = _get_token()
    output_file = pathlib.Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    overlay_parts = []
    for m in (markers or []):
        mlat = m.get("lat", center_lat)
        mlon = m.get("lon", center_lon)
        color = m.get("color", "e94560")
        overlay_parts.append(f"pin-s+{color}({mlon},{mlat})")

    overlay = ",".join(overlay_parts) + "/" if overlay_parts else ""

    url = (
        f"https://api.mapbox.com/styles/v1/mapbox/{STYLE}/static/"
        f"{overlay}{center_lon},{center_lat},{zoom}/{width}x{height}@2x"
        f"?access_token={token}&attribution=false&logo=false"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Trevor-Present/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except (urllib.error.URLError, urllib.error.HTTPError) as exc:
        raise RuntimeError(f"Mapbox request failed: {exc}") from exc

    if len(data) < 100:
        raise RuntimeError("Mapbox returned empty response")

    output_file.write_bytes(data)
    print(f"  ✅ Map: {output_file} ({len(data) // 1024} KB, zoom {zoom})")
    return str(output_file)


def verify_map(image_path: str) -> dict:
    """Verify a generated map image."""
    path = pathlib.Path(image_path)
    checks = {"exists": path.exists()}
    if checks["exists"]:
        checks["size_kb"] = round(path.stat().st_size / 1024, 1)
        checks["not_empty"] = path.stat().st_size > 100
        header = path.read_bytes()[:4]
        checks["valid_format"] = (
            header[:3] == b"\xff\xd8\xff" or header[:4] == b"\x89PNG"
        )
    return checks


def main():
    parser = argparse.ArgumentParser(description="Stage 3 — Mapbox Static Maps")
    parser.add_argument("--center", nargs=2, type=float, default=[0, 0],
                        help="Center: lon lat")
    parser.add_argument("--zoom", type=int, default=4, help="Zoom level (0-22)")
    parser.add_argument("--markers", default=None,
                        help="JSON array of marker dicts")
    parser.add_argument("--output", "-o", default="exports/maps/map.png",
                        help="Output PNG path")
    parser.add_argument("--self-test", action="store_true",
                        help="Run self-test and exit")
    args = parser.parse_args()

    if args.self_test:
        failures = self_test()
        if failures:
            for f in failures:
                print(f"  STAGE 3 DISABLED: {f}")
        else:
            print("  STAGE 3 READY: Mapbox endpoint reachable")
        return

    markers = json.loads(args.markers) if args.markers else []
    result = render_map(
        center_lon=args.center[0],
        center_lat=args.center[1],
        output_path=args.output,
        zoom=args.zoom,
        markers=markers,
    )

    checks = verify_map(result)
    print(f"  Verification: {checks}")
    if checks.get("valid_format") and checks.get("not_empty"):
        print(f"  ✅ Stage 3 deliverable: {result}")
    else:
        print(f"  ❌ Stage 3 verification failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
