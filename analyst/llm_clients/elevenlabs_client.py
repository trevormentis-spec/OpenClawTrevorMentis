#!/usr/bin/env python3
"""ElevenLabs API client for text-to-speech generation.

Handles audio companion generation with consistent voice profiles.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional


ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"
MAX_RETRIES = 2
RETRY_DELAY_S = 3.0


class ElevenLabsClient:
    """Client for ElevenLabs TTS API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY", "")
        if not self.api_key:
            env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
            if os.path.exists(env_path):
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("ELEVENLABS_API_KEY="):
                            self.api_key = line.split("=", 1)[1].strip().strip('"')
                            break

    def generate_audio(
        self,
        text: str,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Rachel (default)
        model_id: str = "eleven_monolingual_v1",
        output_path: Optional[str] = None,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
    ) -> dict:
        """
        Generate audio from text.

        Returns:
            dict with keys: output_path, chars, estimated_cost_usd
        """
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not set")

        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
            },
        }

        headers = {
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }

        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{ELEVENLABS_BASE}/text-to-speech/{voice_id}",
            data=data,
            headers=headers,
            method="POST",
        )

        for attempt in range(MAX_RETRIES):
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    audio_data = resp.read()

                if output_path is None:
                    output_path = f"/tmp/trevor-tts-{int(time.time())}.mp3"

                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(audio_data)

                chars = len(text)
                cost = chars * 0.00003  # ~$0.03 per 1000 chars

                return {
                    "output_path": output_path,
                    "chars": chars,
                    "estimated_cost_usd": round(cost, 6),
                }
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_S * (attempt + 1))
                    continue
                raise
            except urllib.error.URLError as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_S * (attempt + 1))
                    continue
                raise

    def is_available(self) -> bool:
        """Check if ElevenLabs API key is configured."""
        return bool(self.api_key)
