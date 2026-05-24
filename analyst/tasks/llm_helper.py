#!/usr/bin/env python3
# GATE_EXEMPT: direct API endpoints required for LLM routing without SDK wrapper
"""Shared LLM helper for analyst task modules.

Provides a single `call_llm()` function that routes through the task's
preferred provider. All 4 task modules use this.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


def get_api_key(provider: str = "deepseek") -> str:
    """Get API key from env or .env."""
    key_var = "DEEPSEEK_API_KEY" if provider == "deepseek" else "OPENROUTER_API_KEY"
    key = os.environ.get(key_var, "")
    if key:
        return key
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().split("\n"):
            if line.strip().startswith(f"{key_var}="):
                return line.split("=", 1)[1].strip().strip("\"'")
    return ""


def call_llm(
    system: str,
    user: str,
    model: str = "deepseek/deepseek-v4-pro",
    provider: str = "deepseek",
    max_tokens: int = 2048,
    temperature: float = 0.2,
    response_format: str | None = "json_object",
) -> dict[str, Any]:
    """Call an LLM and return parsed JSON response.

    Args:
        system: System prompt
        user: User prompt (data + instructions)
        model: Model ID (deepseek/deepseek-v4-pro or anthropic/claude-opus-4.7)
        provider: "deepseek" or "openrouter"
        max_tokens: Response token limit
        temperature: Sampling temperature
        response_format: "json_object" or None for text

    Returns:
        dict with keys: content, model, provider, cost_estimate, elapsed_ms,
        error (if any)
    """
    import time
    t0 = time.monotonic()

    api_key = get_api_key(provider)
    if not api_key:
        return {"content": "", "error": f"No {provider} API key", "model": model}

    # Build payload
    payload = {
        "model": model.split("/")[-1] if "/" in model and provider == "deepseek" else model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if response_format:
        payload["response_format"] = {"type": response_format}

    # Route to correct endpoint
    if provider == "deepseek":
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    else:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://trevormentis-spec.github.io",
        }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())

        content = result["choices"][0]["message"]["content"]
        elapsed = time.monotonic() - t0

        # Parse JSON if response_format was set
        parsed = None
        if response_format == "json_object":
            try:
                # Strip markdown fences if present
                if content.startswith("```"):
                    content = content.split("\n", 1)[1] if "\n" in content else content[3:]
                    if content.endswith("```"):
                        content = content[:-3]
                if content.startswith("json\n"):
                    content = content[5:]
                parsed = json.loads(content)
            except json.JSONDecodeError:
                parsed = {"raw": content}

        return {
            "content": content,
            "parsed": parsed,
            "model": model,
            "provider": provider,
            "elapsed_ms": int(elapsed * 1000),
            "usage": result.get("usage", {}),
            "error": None,
        }

    except Exception as exc:
        elapsed = time.monotonic() - t0
        return {
            "content": "",
            "parsed": None,
            "error": str(exc),
            "model": model,
            "provider": provider,
            "elapsed_ms": int(elapsed * 1000),
        }
