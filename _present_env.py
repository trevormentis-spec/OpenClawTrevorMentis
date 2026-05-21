"""Shared environment loader for Trevor Present scripts.

Single source of truth for ALL API keys. No script should read .env directly.
LLM API keys (OPENROUTER, DEEPSEEK) are loaded through analyst/llm_clients/ ONLY.
Non-LLM keys (GENVIRAL, MAPBOX) are loaded here.

This module also ensures the workspace root is on sys.path so that
analyst/llm_clients/ can be imported.

Usage:
    from scripts.present._env import get_key, load_env
    
    key = get_key("GENVIRAL_API_KEY")
    env = load_env()
"""
from __future__ import annotations

import os
import pathlib
import sys
from typing import Optional

# Ensure workspace root is on sys.path for analyst/ imports
_ws = pathlib.Path(__file__).resolve().parent.parent.parent
_ws_path = str(_ws)
if _ws_path not in sys.path:
    sys.path.insert(0, _ws_path)

WORKSPACE = pathlib.Path("/home/ubuntu/.openclaw/workspace")
ENV_PATH = WORKSPACE / ".env"

# Keys that should NEVER be loaded here — they must go through analyst/llm_clients/
# Only actual LLM model providers. TTS, image gen, maps are NOT LLMs.
LLM_GATE_KEYS = frozenset({
    "OPENROUTER_API_KEY",
    "DEEPSEEK_API_KEY",
    "ANTHROPIC_API_KEY",
})

# Keys that ARE safe to load here (non-LLM services)
# ElevenLabs is TTS, not an LLM — safe to load here
SAFE_KEYS = frozenset({
    "GENVIRAL_API_KEY",
    "MAPBOX_TOKEN",
    "ELEVENLABS_API_KEY",
    "AGENTMAIL_API_KEY",
    "GITHUB_TOKEN",
})


def _load_env_file() -> dict[str, str]:
    """Load .env file once and cache."""
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip('"').strip("'")
    return env


# Load once at module level
_ENV_CACHE = _load_env_file()


def get_key(name: str) -> str:
    """Get a non-LLM API key. Raises ValueError if it's an LLM key."""
    name = name.upper()
    if name in LLM_GATE_KEYS:
        raise ValueError(
            f"{name} is an LLM provider key and must be accessed through "
            f"analyst/llm_clients/ — not through _env.py"
        )
    return _ENV_CACHE.get(name, "")


def load_env() -> dict[str, str]:
    """Get full environment dict (os.environ + .env), excluding LLM keys.

    Safe to pass to subprocess.run(env=...).
    """
    env = os.environ.copy()
    for k, v in _ENV_CACHE.items():
        if k not in LLM_GATE_KEYS:
            env[k] = v
    return env


def check_available(name: str) -> bool:
    """Check if a non-LLM key is available."""
    return bool(get_key(name))
