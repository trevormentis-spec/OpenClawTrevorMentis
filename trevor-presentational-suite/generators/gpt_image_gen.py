"""TPS GPT Image 2 Generator — complex instruction-following via OpenAI API."""
from __future__ import annotations

import os
import time

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from generators.base import BaseGenerator, GeneratorResult
from core.schemas import AssetSpec, AssetKind
from core.style_director import get_image_prompt_suffix
from core.exceptions import GeneratorError
from core.cache import cache_key, cache_get, cache_put

COST_STANDARD = 0.04
COST_HD = 0.17


class GPTImageGenerator(BaseGenerator):
    """Complex composition generation via GPT Image 2 (OpenAI)."""

    @property
    def name(self) -> str:
        return "gpt_image_2"

    @property
    def supported_kinds(self) -> list[str]:
        return [AssetKind.ILLUSTRATION.value, AssetKind.INFOGRAPHIC.value]

    def is_available(self) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY", ""))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.ConnectError)),
    )
    def generate(self, spec: AssetSpec, output_dir: str) -> GeneratorResult:
        errors = self.validate_spec(spec)
        if errors:
            raise GeneratorError(f"Validation: {'; '.join(errors)}")
        if not spec.prompt:
            raise GeneratorError("No prompt provided")

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{spec.asset_id}_gptimg.png")

        ck = cache_key(self.name, spec.prompt, spec.parameters)
        cached = cache_get(ck)
        if cached:
            import shutil
            shutil.copy2(cached, output_path)
            return GeneratorResult(
                output_path=output_path, actual_cost_usd=0.0,
                model_used="gpt-image-2", provider="openai (cached)",
            )

        api_key = os.environ.get("OPENAI_API_KEY", "")
        quality = spec.parameters.get("quality", "standard")
        size = spec.parameters.get("size", "1024x1024")
        brand_suffix = get_image_prompt_suffix()

        start = time.time()
        with httpx.Client(timeout=120) as client:
            resp = client.post(
                "https://api.openai.com/v1/images/generations",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "gpt-image-2",
                    "prompt": f"{spec.prompt}\n\n{brand_suffix}",
                    "n": 1,
                    "size": size,
                    "quality": quality,
                    "output_format": "png",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        elapsed = time.time() - start

        images = data.get("data", [])
        if not images:
            raise GeneratorError("GPT Image returned no images")

        # Download from URL or decode b64
        import base64
        b64 = images[0].get("b64_json", "")
        if b64:
            img_bytes = base64.b64decode(b64)
            with open(output_path, "wb") as f:
                f.write(img_bytes)
        else:
            url = images[0].get("url", "")
            if url:
                img_resp = httpx.get(url, timeout=60)
                with open(output_path, "wb") as f:
                    f.write(img_resp.content)

        cache_put(ck, output_path, ".png")
        cost = COST_HD if quality == "hd" else COST_STANDARD

        return GeneratorResult(
            output_path=output_path,
            actual_cost_usd=cost,
            generation_time_sec=elapsed,
            model_used="gpt-image-2",
            provider="openai",
        )
