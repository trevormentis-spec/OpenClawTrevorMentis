"""TPS Timeline Generator — intelligence chronology renderer."""
from __future__ import annotations

import os
from generators.base import BaseGenerator, GeneratorResult
from core.schemas import AssetSpec, AssetKind
from core.style_director import get_brand, get_kent_color
from core.exceptions import GeneratorError


class TimelineGenerator(BaseGenerator):
    """Custom HTML timeline for intelligence chronologies."""

    @property
    def name(self) -> str:
        return "timeline"

    @property
    def supported_kinds(self) -> list[str]:
        return [AssetKind.DIAGRAM.value]

    def is_available(self) -> bool:
        return True

    def generate(self, spec: AssetSpec, output_dir: str) -> GeneratorResult:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{spec.asset_id}_timeline.html")

        brand = get_brand()
        events = spec.parameters.get("events", [])
        title = spec.parameters.get("chart_title", spec.title)

        event_items = ""
        for evt in events:
            date = evt.get("date", "")
            label = evt.get("label", "")
            band = evt.get("kent_band", "")
            color = get_kent_color(band) if band else brand.color_accent
            event_items += f"""
            <div class="tl-item">
              <div class="tl-dot" style="background:{color}"></div>
              <div class="tl-date">{date}</div>
              <div class="tl-content">{label}</div>
            </div>"""

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body{{font-family:Inter,sans-serif;background:#F5F3EF;margin:2rem;color:{brand.color_body}}}
h2{{color:{brand.color_primary};border-bottom:2px solid {brand.color_accent};padding-bottom:6px}}
.tl-item{{display:flex;align-items:flex-start;margin:12px 0;gap:12px}}
.tl-dot{{width:12px;height:12px;border-radius:50%;flex-shrink:0;margin-top:4px}}
.tl-date{{font-size:11px;color:#666;min-width:100px}}
.tl-content{{font-size:13px}}
</style></head><body>
<h2>{title}</h2>
{event_items}
</body></html>"""

        with open(output_path, "w") as f:
            f.write(html)

        return GeneratorResult(
            output_path=output_path, actual_cost_usd=0.0,
            model_used="timeline-html", provider="local",
        )
