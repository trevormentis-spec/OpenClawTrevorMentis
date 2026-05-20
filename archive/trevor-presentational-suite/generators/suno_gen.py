"""TPS Suno Generator — AI music/jingle generation.

Generates background music or intro jingles for briefing videos
via the Suno API (through fal.ai or direct).
"""
from __future__ import annotations

import os
from generators.base import BaseGenerator, GeneratorResult
from core.schemas import AssetSpec, AssetKind
from core.cache import cache_key, cache_get, cache_put
from core.exceptions import GeneratorError


class SunoGenerator(BaseGenerator):
    """AI music generation via Suno."""

    @property
    def name(self) -> str:
        return "suno"

    @property
    def supported_kinds(self) -> list[str]:
        return [AssetKind.NARRATION.value]

    def is_available(self) -> bool:
        return bool(os.environ.get("SUNO_API_KEY", "") or
                     os.environ.get("FAL_KEY", ""))

    def generate(self, spec: AssetSpec, output_dir: str) -> GeneratorResult:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{spec.asset_id}_music.mp3")

        # Check cache
        ck = cache_key("suno", spec)
        cached = cache_get(ck, output_dir)
        if cached:
            return GeneratorResult(
                output_path=cached, actual_cost_usd=0.0,
                model_used="suno-v4", provider="suno",
            )

        prompt = spec.prompt or "Professional intelligence briefing intro, minimal, serious, 15 seconds"
        duration = spec.parameters.get("duration_sec", 15)
        style = spec.parameters.get("style", "cinematic, minimal, serious")

        # Try fal.ai first
        try:
            from generators.fal_client import submit_and_poll, is_available as fal_available
            if fal_available():
                result = submit_and_poll(
                    "fal-ai/suno/v4",
                    {
                        "prompt": prompt,
                        "duration": duration,
                        "style": style,
                    },
                    timeout_sec=120,
                )
                audio_url = ""
                if "audio" in result:
                    audio_url = result["audio"].get("url", "")
                elif "audio_url" in result:
                    audio_url = result["audio_url"]

                if audio_url:
                    import httpx
                    with httpx.Client(timeout=60) as client:
                        resp = client.get(audio_url)
                        resp.raise_for_status()
                        with open(output_path, "wb") as f:
                            f.write(resp.content)

                    cache_put(ck, output_path)
                    return GeneratorResult(
                        output_path=output_path,
                        actual_cost_usd=0.10,
                        model_used="suno-v4",
                        provider="fal.ai",
                    )
        except Exception:
            pass

        raise GeneratorError(
            "Suno generation failed — no available provider"
        )
