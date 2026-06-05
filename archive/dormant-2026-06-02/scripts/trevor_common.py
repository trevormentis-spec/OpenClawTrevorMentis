#!/usr/bin/env python3
"""
Trevor common utilities — shared across all pipeline scripts.
Eliminates duplicated log(), load_json(), get_api_key(), and .env loading.

Usage:
    from scripts.trevor_common import log, load_json, get_api_key, REPO_ROOT
"""

import datetime as dt
import json
import os
import pathlib
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Cache for .env values to avoid re-reading on every call
_ENV_CACHE: dict[str, str] = {}
_ENV_LOADED = False


def _load_env() -> None:
    global _ENV_LOADED, _ENV_CACHE
    if _ENV_LOADED:
        return
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                _ENV_CACHE[key.strip()] = val.strip().strip("'\"")
    _ENV_LOADED = True


def log(msg: str) -> None:
    """Standardized log line with timestamp to stderr."""
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> Any:
    """Load and parse a JSON file. Returns None if missing or corrupt."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        log(f"WARN: failed to load {path}: {exc}")
        return None


def get_api_key(key_name: str) -> str:
    """Get an API key from environment or .env file. Check env first, then .env."""
    # Check environment first
    value = os.environ.get(key_name, "")
    if value:
        return value
    # Fall back to .env
    _load_env()
    return _ENV_CACHE.get(key_name, "")


def save_json(path: pathlib.Path, data: Any) -> bool:
    """Save data as JSON. Creates parent dirs. Returns True on success."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return True
    except OSError as exc:
        log(f"ERROR: failed to save {path}: {exc}")
        return False
