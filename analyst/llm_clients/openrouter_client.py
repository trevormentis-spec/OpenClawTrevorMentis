#!/usr/bin/env python3
"""OpenRouter API client for frontier model access.

Handles: Claude Opus 4.7, Claude Sonnet 4.5, Claude Vision, nanobanana, Whisper.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
import urllib.error
from typing import Any, Optional


OPENROUTER_BASE = "https://openrouter.ai/api/v1"
MAX_RETRIES = 3
RETRY_DELAY_S = 2.0


class OpenRouterClient:
    """Client for OpenRouter API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        if not self.api_key:
            # Try loading from .env
            env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
            if os.path.exists(env_path):
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("OPENROUTER_API_KEY="):
                            self.api_key = line.split("=", 1)[1].strip().strip('"')
                            break

    def complete(
        self,
        model: str,
        messages: list[dict],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> dict:
        """
        Send a chat completion request.

        Returns:
            dict with keys: content, model, input_tokens, output_tokens, cost_usd
        """
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set")

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        payload.update(kwargs)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/trevormentis-spec/OpenClawTrevorMentis",
            "X-Title": "Trevor Intelligence Analyst",
        }

        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{OPENROUTER_BASE}/chat/completions",
            data=data,
            headers=headers,
            method="POST",
        )

        for attempt in range(MAX_RETRIES):
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    result = json.loads(resp.read())

                usage = result.get("usage", {})
                choices = result.get("choices", [{}])
                content = choices[0].get("message", {}).get("content", "") if choices else ""

                return {
                    "content": content,
                    "model": result.get("model", model),
                    "input_tokens": usage.get("prompt_tokens", 0),
                    "output_tokens": usage.get("completion_tokens", 0),
                    "cost_usd": 0.0,  # OpenRouter provides this in headers
                    "raw": result,
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
        """Check if OpenRouter API key is configured."""
        return bool(self.api_key)
