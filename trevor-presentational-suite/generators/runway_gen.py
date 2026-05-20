"""TPS Runway Generator — Runway 4.5 video generation via fal.ai."""
from __future__ import annotations

import os
from generators.base import BaseGenerator, GeneratorResult
from core.schemas import AssetSpec, AssetKind
from core.cache import cache_key, cache_get, cache_put
from core.style_director import get_image_prompt_suffix
from core.exceptions import GeneratorError


class RunwayGenerator(BaseGenerator):
    """Video generation via Runway 4.5 on fal.ai."""

    @property
    def name(self) -> str:
        return "runway_4_5"

    @property
    def supported_kinds(self) -> list[str]:
        return [AssetKind.VIDEO.value]

    def is_available(self) -> bool:
        try:
            from generators.fal_client import is_available
            return is_available()
        except ImportError:
            return False

    def generate(self, spec: AssetSpec, output_dir: str) -> GeneratorResult:
        from generators.fal_client import submit_and_poll, download_image

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{spec.asset_id}_runway.mp4")

        ck = cache_key("runway_4_5", spec)
        cached = cache_get(ck, output_dir)
        if cached:
            return GeneratorResult(
                output_path=cached, actual_cost_usd=0.0,
                model_used="runway-4.5", provider="fal.ai",
            )

        prompt = spec.prompt or spec.title
        prompt += f" {get_image_prompt_suffix()}"
        duration_sec = spec.parameters.get("duration_sec", 5)

        result = submit_and_poll(
            "fal-ai/runway/gen4-turbo",
            {
                "prompt": prompt,
                "duration": duration_sec,
                "ratio": spec.parameters.get("aspect_ratio", "16:9"),
            },
            timeout_sec=300,
        )

        video_url = ""
        if "video" in result:
            video_url = result["video"].get("url", "")
        elif "video_url" in result:
            video_url = result["video_url"]

        if not video_url:
            raise GeneratorError("Runway returned no video URL")

        download_image(video_url, output_path)
        cost = duration_sec * 0.18

        cache_put(ck, output_path)

        return GeneratorResult(
            output_path=output_path,
            actual_cost_usd=round(cost, 4),
            model_used="runway-4.5",
            provider="fal.ai",
        )
