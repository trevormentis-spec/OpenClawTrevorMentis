"""TPS Imagen 4 Generator — 4K photoreal with typography balance via fal.ai."""
from __future__ import annotations

import os
import time
from generators.base import BaseGenerator, GeneratorResult
from core.schemas import AssetSpec, AssetKind
from core.style_director import get_image_prompt_suffix
from core.exceptions import GeneratorError
from core.cache import cache_key, cache_get, cache_put

MODEL_ID = "fal-ai/imagen-4/preview"
COST_PER_IMAGE = 0.04


class ImagenGenerator(BaseGenerator):
    """4K photorealistic image generation via Imagen 4 on fal.ai."""

    @property
    def name(self) -> str:
        return "imagen_4"

    @property
    def supported_kinds(self) -> list[str]:
        return [AssetKind.ILLUSTRATION.value, AssetKind.INFOGRAPHIC.value]

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
        output_path = os.path.join(output_dir, f"{spec.asset_id}_imagen.png")

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
            "image_size": spec.parameters.get("image_size", "landscape_16_9"),
            "num_images": 1,
        }

        start = time.time()
        result = submit_and_poll(MODEL_ID, payload)
        elapsed = time.time() - start

        images = result.get("images", [])
        if not images:
            raise GeneratorError("Imagen returned no images")

        image_url = images[0].get("url", "")
        download_image(image_url, output_path)
        cache_put(ck, output_path, ".png")

        return GeneratorResult(
            output_path=output_path,
            actual_cost_usd=COST_PER_IMAGE,
            generation_time_sec=elapsed,
            model_used=MODEL_ID,
            provider="fal.ai",
        )
