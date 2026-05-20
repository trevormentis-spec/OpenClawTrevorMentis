"""TPS HeyGen Generator — AI talking-head avatar for briefing videos.

Produces avatar narration clips using the HeyGen API.
"""
from __future__ import annotations

import os
import time
from generators.base import BaseGenerator, GeneratorResult
from core.schemas import AssetSpec, AssetKind
from core.cache import cache_key, cache_get, cache_put
from core.exceptions import GeneratorError


HEYGEN_API_BASE = "https://api.heygen.com/v2"


class HeyGenGenerator(BaseGenerator):
    """AI talking-head avatar via HeyGen API."""

    @property
    def name(self) -> str:
        return "heygen"

    @property
    def supported_kinds(self) -> list[str]:
        return [AssetKind.VIDEO.value]

    def is_available(self) -> bool:
        return bool(os.environ.get("HEYGEN_API_KEY", ""))

    def generate(self, spec: AssetSpec, output_dir: str) -> GeneratorResult:
        import httpx

        api_key = os.environ.get("HEYGEN_API_KEY", "")
        if not api_key:
            raise GeneratorError("HEYGEN_API_KEY not set")

        text = spec.prompt
        if not text:
            raise GeneratorError("No script provided in spec.prompt for HeyGen")

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{spec.asset_id}_heygen.mp4")

        ck = cache_key("heygen", spec)
        cached = cache_get(ck, output_dir)
        if cached:
            return GeneratorResult(
                output_path=cached, actual_cost_usd=0.0,
                model_used="heygen-avatar", provider="heygen",
            )

        avatar_id = spec.parameters.get("avatar_id", "josh_lite3_20230714")
        voice_id = spec.parameters.get("voice_id", "en-US-JennyNeural")
        background = spec.parameters.get("background_color", "#0f3460")

        headers = {
            "X-Api-Key": api_key,
            "Content-Type": "application/json",
        }

        # Create video
        payload = {
            "video_inputs": [{
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal",
                },
                "voice": {
                    "type": "text",
                    "input_text": text,
                    "voice_id": voice_id,
                },
                "background": {
                    "type": "color",
                    "value": background,
                },
            }],
            "dimension": {
                "width": 1920,
                "height": 1080,
            },
        }

        with httpx.Client(timeout=300) as client:
            # Submit video creation
            resp = client.post(
                f"{HEYGEN_API_BASE}/video/generate",
                json=payload, headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            video_id = data.get("data", {}).get("video_id", "")

            if not video_id:
                raise GeneratorError(f"HeyGen returned no video_id: {data}")

            # Poll for completion
            for _ in range(120):  # 10 min timeout
                time.sleep(5)
                status_resp = client.get(
                    f"{HEYGEN_API_BASE}/video_status.get",
                    params={"video_id": video_id},
                    headers=headers,
                )
                status_resp.raise_for_status()
                status_data = status_resp.json()
                status = status_data.get("data", {}).get("status", "")

                if status == "completed":
                    video_url = status_data["data"].get("video_url", "")
                    if not video_url:
                        raise GeneratorError("HeyGen completed but no video_url")

                    # Download
                    dl_resp = client.get(video_url)
                    dl_resp.raise_for_status()
                    with open(output_path, "wb") as f:
                        f.write(dl_resp.content)

                    # Estimate cost: ~$1/min
                    duration_sec = status_data["data"].get("duration", 60)
                    cost = (duration_sec / 60) * 1.00

                    cache_put(ck, output_path)

                    return GeneratorResult(
                        output_path=output_path,
                        actual_cost_usd=round(cost, 4),
                        model_used="heygen-avatar",
                        provider="heygen",
                    )
                elif status == "failed":
                    error = status_data.get("data", {}).get("error", "Unknown")
                    raise GeneratorError(f"HeyGen video failed: {error}")

            raise GeneratorError(f"HeyGen video {video_id} timed out")
