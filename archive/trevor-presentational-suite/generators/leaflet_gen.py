"""TPS Leaflet Generator — tactical dark-tile maps via HTML generation."""
from __future__ import annotations

import os
from generators.base import BaseGenerator, GeneratorResult
from core.schemas import AssetSpec, AssetKind
from core.style_director import get_brand
from core.exceptions import GeneratorError


class LeafletTacticalGenerator(BaseGenerator):
    """Leaflet + CartoDB dark tiles for tactical aesthetic maps."""

    @property
    def name(self) -> str:
        return "leaflet"

    @property
    def supported_kinds(self) -> list[str]:
        return [AssetKind.MAP.value]

    def is_available(self) -> bool:
        return True  # No credentials needed

    def generate(self, spec: AssetSpec, output_dir: str) -> GeneratorResult:
        errors = self.validate_spec(spec)
        if errors:
            raise GeneratorError(f"Validation: {'; '.join(errors)}")

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{spec.asset_id}_leaflet.html")

        brand = get_brand()
        lat = spec.parameters.get("lat", 20.5)
        lon = spec.parameters.get("lon", -100.0)
        zoom = spec.parameters.get("zoom", 6)
        markers = spec.parameters.get("markers", [])

        marker_js = ""
        for m in markers:
            mlat = m.get("lat", lat)
            mlon = m.get("lon", lon)
            label = m.get("label", "")
            marker_js += f"L.marker([{mlat},{mlon}]).addTo(map).bindPopup('{label}');\n"

        html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>body{{margin:0;background:{brand.color_body}}}#map{{width:100%;height:100vh}}</style>
</head><body>
<div id="map"></div>
<script>
var map=L.map('map').setView([{lat},{lon}],{zoom});
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}@2x.png',{{
  attribution:'&copy; CartoDB',maxZoom:19
}}).addTo(map);
{marker_js}
</script>
</body></html>"""

        with open(output_path, "w") as f:
            f.write(html)

        return GeneratorResult(
            output_path=output_path, actual_cost_usd=0.0,
            model_used="leaflet-1.9", provider="local",
        )
