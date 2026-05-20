"""TPS ElevenLabs Generator — text-to-speech narration.

Converts brief text to professional narration audio via ElevenLabs API.
"""
from __future__ import annotations

import os
from generators.base import BaseGenerator, GeneratorResult
from core.schemas import AssetSpec, AssetKind
from core.cache import cache_key, cache_get, cache_put
from core.exceptions import GeneratorError


ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel (neutral, professional)


class ElevenLabsGenerator(BaseGenerator):
    """Text-to-speech via ElevenLabs API."""

    @property
    def name(self) -> str:
        return "elevenlabs"

    @property
    def supported_kinds(self) -> list[str]:
        return [AssetKind.NARRATION.value]

    def is_available(self) -> bool:
        return bool(os.environ.get("ELEVENLABS_API_KEY", ""))

    def generate(self, spec: AssetSpec, output_dir: str) -> GeneratorResult:
        import httpx

        api_key = os.environ.get("ELEVENLABS_API_KEY", "")
        if not api_key:
            raise GeneratorError("ELEVENLABS_API_KEY not set")

        text = spec.prompt
        if not text:
            raise GeneratorError("No text provided in spec.prompt for narration")

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{spec.asset_id}_narration.mp3")

        # Check cache
        ck = cache_key("elevenlabs", spec)
        cached = cache_get(ck, output_dir)
        if cached:
            return GeneratorResult(
                output_path=cached, actual_cost_usd=0.0,
                model_used="elevenlabs-v2", provider="elevenlabs",
            )

        voice_id = spec.parameters.get("voice_id", DEFAULT_VOICE_ID)
        model_id = spec.parameters.get("model_id", "eleven_multilingual_v2")
        stability = spec.parameters.get("stability", 0.5)
        similarity_boost = spec.parameters.get("similarity_boost", 0.75)

        url = f"{ELEVENLABS_API_URL}/{voice_id}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
            },
        }

        with httpx.Client(timeout=120) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()

            with open(output_path, "wb") as f:
                f.write(resp.content)

        # Cost: ~$0.00003 per character
        char_count = len(text)
        cost = char_count * 0.00003

        cache_put(ck, output_path)

        return GeneratorResult(
            output_path=output_path,
            actual_cost_usd=round(cost, 6),
            model_used=model_id,
            provider="elevenlabs",
        )
