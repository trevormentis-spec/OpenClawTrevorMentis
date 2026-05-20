"""TPS Veo Generator — Google Veo 3.1 video generation via fal.ai.

Produces short video clips for intelligence briefing visuals.
"""
from __future__ import annotations

import os
from generators.base import BaseGenerator, GeneratorResult
from core.schemas import AssetSpec, AssetKind
from core.cache import cache_key, cache_get, cache_put
from core.style_director import get_image_prompt_suffix
from core.exceptions import GeneratorError


class VeoGenerator(BaseGenerator):
    """Video generation via Google Veo 3.1 on fal.ai."""

    @property
    def name(self) -> str:
        return "veo_3_1"

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
        output_path = os.path.join(output_dir, f"{spec.asset_id}_veo.mp4")

        # Check cache
        ck = cache_key("veo_3_1", spec)
        cached = cache_get(ck, output_dir)
        if cached:
            return GeneratorResult(
                output_path=cached, actual_cost_usd=0.0,
                model_used="veo-3.1", provider="fal.ai",
            )

        prompt = spec.prompt or spec.title
        prompt += f" {get_image_prompt_suffix()}"
        duration_sec = spec.parameters.get("duration_sec", 5)
        aspect_ratio = spec.parameters.get("aspect_ratio", "16:9")

        result = submit_and_poll(
            "fal-ai/veo3",
            {
                "prompt": prompt,
                "duration": duration_sec,
                "aspect_ratio": aspect_ratio,
            },
            timeout_sec=300,
        )

        video_url = ""
        if "video" in result:
            video_url = result["video"].get("url", "")
        elif "video_url" in result:
            video_url = result["video_url"]

        if not video_url:
            raise GeneratorError("Veo returned no video URL")

        download_image(video_url, output_path)
        cost = duration_sec * 0.40

        cache_put(ck, output_path)

        return GeneratorResult(
            output_path=output_path,
            actual_cost_usd=round(cost, 4),
            model_used="veo-3.1",
            provider="fal.ai",
        )
