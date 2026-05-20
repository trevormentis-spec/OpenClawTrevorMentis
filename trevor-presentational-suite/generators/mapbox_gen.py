"""TPS Mapbox Generators — static PNG maps and interactive GL JS embeds."""
from __future__ import annotations

import os
import time
import urllib.request
import urllib.error
import urllib.parse

from generators.base import BaseGenerator, GeneratorResult
from core.schemas import AssetSpec, AssetKind
from core.exceptions import GeneratorError
from core.cache import cache_key, cache_get, cache_put


class MapboxStaticGenerator(BaseGenerator):
    """Static PNG/JPEG maps via Mapbox Static Images API."""

    @property
    def name(self) -> str:
        return "mapbox_static"

    @property
    def supported_kinds(self) -> list[str]:
        return [AssetKind.MAP.value]

    def is_available(self) -> bool:
        return bool(os.environ.get("MAPBOX_TOKEN", ""))

    def generate(self, spec: AssetSpec, output_dir: str) -> GeneratorResult:
        errors = self.validate_spec(spec)
        if errors:
            raise GeneratorError(f"Validation: {'; '.join(errors)}")

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{spec.asset_id}_map.png")

        ck = cache_key(self.name, spec.prompt, spec.parameters)
        cached = cache_get(ck)
        if cached:
            import shutil
            shutil.copy2(cached, output_path)
            return GeneratorResult(
                output_path=output_path, actual_cost_usd=0.0,
                model_used="mapbox-static-v1", provider="mapbox (cached)",
            )

        token = os.environ.get("MAPBOX_TOKEN", "")
        lon = spec.parameters.get("lon", 0)
        lat = spec.parameters.get("lat", 0)
        zoom = spec.parameters.get("zoom", 5)
        width = spec.parameters.get("width", 800)
        height = spec.parameters.get("height", 600)
        style = spec.parameters.get("style", "dark-v11")

        # Build overlay GeoJSON if markers provided
        overlay = ""
        markers = spec.parameters.get("markers", [])
        if markers:
            parts = []
            for m in markers:
                mlat = m.get("lat", lat)
                mlon = m.get("lon", lon)
                color = m.get("color", "e94560")
                parts.append(f"pin-s+{color}({mlon},{mlat})")
            overlay = ",".join(parts) + "/"

        url = (
            f"https://api.mapbox.com/styles/v1/mapbox/{style}/static/"
            f"{overlay}{lon},{lat},{zoom}/{width}x{height}@2x"
            f"?access_token={token}&attribution=false"
        )

        start = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TPS/0.1"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            raise GeneratorError(f"Mapbox API failed: {e}") from e

        elapsed = time.time() - start

        with open(output_path, "wb") as f:
            f.write(data)

        cache_put(ck, output_path, ".png")

        return GeneratorResult(
            output_path=output_path,
            actual_cost_usd=0.0,  # Free tier
            generation_time_sec=elapsed,
            model_used="mapbox-static-v1",
            provider="mapbox",
        )


class MapboxInteractiveGenerator(BaseGenerator):
    """Interactive GL JS map HTML embeds for websites."""

    @property
    def name(self) -> str:
        return "mapbox_interactive"

    @property
    def supported_kinds(self) -> list[str]:
        return [AssetKind.MAP.value]

    def is_available(self) -> bool:
        return bool(os.environ.get("MAPBOX_TOKEN", ""))

    def generate(self, spec: AssetSpec, output_dir: str) -> GeneratorResult:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{spec.asset_id}_map.html")

        token = os.environ.get("MAPBOX_TOKEN", "")
        lon = spec.parameters.get("lon", 0)
        lat = spec.parameters.get("lat", 0)
        zoom = spec.parameters.get("zoom", 5)
        style = spec.parameters.get("style", "dark-v11")

        html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<script src="https://api.mapbox.com/mapbox-gl-js/v3.4.0/mapbox-gl.js"></script>
<link href="https://api.mapbox.com/mapbox-gl-js/v3.4.0/mapbox-gl.css" rel="stylesheet">
<style>body{{margin:0}}#map{{width:100%;height:100vh}}</style>
</head><body>
<div id="map"></div>
<script>
mapboxgl.accessToken='{token}';
const map=new mapboxgl.Map({{container:'map',style:'mapbox://styles/mapbox/{style}',center:[{lon},{lat}],zoom:{zoom}}});
</script>
</body></html>"""

        with open(output_path, "w") as f:
            f.write(html)

        return GeneratorResult(
            output_path=output_path, actual_cost_usd=0.0,
            model_used="mapbox-gl-js-v3", provider="mapbox",
        )
