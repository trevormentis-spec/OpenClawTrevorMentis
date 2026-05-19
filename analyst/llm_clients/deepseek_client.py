#!/usr/bin/env python3
"""DeepSeek Direct API client for mid-tier and high-volume model access.

Handles: DeepSeek V4 Pro, DeepSeek V4 Flash.
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
import urllib.error
from typing import Any, Optional


DEEPSEEK_BASE = "https://api.deepseek.com/v1"
MAX_RETRIES = 3
RETRY_DELAY_S = 2.0

# DeepSeek model ID mapping
MODEL_MAP = {
    "deepseek/deepseek-v4-pro": "deepseek-chat",  # V4 Pro uses deepseek-chat endpoint
    "deepseek/deepseek-v4-flash": "deepseek-chat",  # Flash also uses deepseek-chat
}


class DeepSeekClient:
    """Client for DeepSeek Direct API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        if not self.api_key:
            env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
            if os.path.exists(env_path):
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("DEEPSEEK_API_KEY="):
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
        Send a chat completion request to DeepSeek.

        Returns:
            dict with keys: content, model, input_tokens, output_tokens, cost_usd
        """
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not set")

        api_model = MODEL_MAP.get(model, "deepseek-chat")

        payload = {
            "model": api_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        payload.update(kwargs)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{DEEPSEEK_BASE}/chat/completions",
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

                # Calculate cost based on model
                from analyst.llm_gate import PRICING
                pricing = PRICING.get(model, {"input": 0.40, "output": 1.60})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
                cost = (input_tokens / 1_000_000 * pricing["input"] +
                        output_tokens / 1_000_000 * pricing["output"])

                return {
                    "content": content,
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost_usd": round(cost, 6),
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
        """Check if DeepSeek API key is configured."""
        return bool(self.api_key)
