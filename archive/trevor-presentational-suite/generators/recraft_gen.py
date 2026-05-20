"""TPS Recraft V4 Generator — vector/SVG infographics and brand marks."""
from __future__ import annotations

import os
import time
from generators.base import BaseGenerator, GeneratorResult
from core.schemas import AssetSpec, AssetKind
from core.style_director import get_image_prompt_suffix
from core.exceptions import GeneratorError
from core.cache import cache_key, cache_get, cache_put

MODEL_ID = "fal-ai/recraft-v4"
COST_RASTER = 0.04
COST_VECTOR = 0.08


class RecraftGenerator(BaseGenerator):
    """Vector/SVG infographic generation via Recraft V4 on fal.ai."""

    @property
    def name(self) -> str:
        return "recraft_v4"

    @property
    def supported_kinds(self) -> list[str]:
        return [AssetKind.INFOGRAPHIC.value, AssetKind.ILLUSTRATION.value]

    def is_available(self) -> bool:
        from generators.fal_client import is_available
        return is_available()

    def generate(self, spec: AssetSpec, output_dir: str) -> GeneratorResult:
        errors = self.validate_spec(spec)
        if errors:
            raise GeneratorError(f"Validation: {'; '.join(errors)}")
        if not spec.prompt:
            raise GeneratorError("No prompt provided")

        os.makedirs(output_dir, exist_ok=True)
        is_svg = spec.parameters.get("format", "png") == "svg"
        ext = ".svg" if is_svg else ".png"
        output_path = os.path.join(output_dir, f"{spec.asset_id}_recraft{ext}")

        ck = cache_key(self.name, spec.prompt, spec.parameters)
        cached = cache_get(ck)
        if cached:
            import shutil
            shutil.copy2(cached, output_path)
            return GeneratorResult(
                output_path=output_path, actual_cost_usd=0.0,
                model_used=MODEL_ID, provider="fal.ai (cached)",
            )

        from generators.fal_client import submit_and_poll, download_image

        brand_suffix = get_image_prompt_suffix()
        payload = {
            "prompt": f"{spec.prompt}\n\n{brand_suffix}",
            "style": spec.parameters.get("style", "digital_illustration"),
            "output_format": "svg" if is_svg else "png",
        }

        start = time.time()
        result = submit_and_poll(MODEL_ID, payload)
        elapsed = time.time() - start

        images = result.get("images", [])
        if not images:
            raise GeneratorError("Recraft returned no images")

        image_url = images[0].get("url", "")
        if not image_url:
            raise GeneratorError("Recraft returned empty image URL")

        download_image(image_url, output_path)
        cache_put(ck, output_path, ext)

        return GeneratorResult(
            output_path=output_path,
            actual_cost_usd=COST_VECTOR if is_svg else COST_RASTER,
            generation_time_sec=elapsed,
            model_used=MODEL_ID,
            provider="fal.ai",
        )
