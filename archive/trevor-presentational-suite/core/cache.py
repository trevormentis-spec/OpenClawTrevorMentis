"""TPS Cache — content-addressable asset cache to avoid regeneration.

Cache key: SHA256(provider + spec + brand_version).
Cache index lives in the tps_assets DB table; binary blobs live on disk.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Optional

from .config import get_config


def _cache_dir() -> Path:
    """Get the cache directory, creating it if needed."""
    d = Path(get_config().cache_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


def cache_key(generator: str, spec_or_prompt=None, parameters: dict = None, brand_version: str = "1") -> str:
    """Compute a deterministic cache key for an asset spec.

    Accepts either:
      cache_key("gen", spec)  — extracts prompt and parameters from AssetSpec
      cache_key("gen", "prompt text", {"key": "val"})  — explicit prompt + params
    """
    if spec_or_prompt is not None and hasattr(spec_or_prompt, "prompt"):
        # AssetSpec object
        prompt = spec_or_prompt.prompt or ""
        params = spec_or_prompt.parameters or {}
    elif isinstance(spec_or_prompt, str):
        prompt = spec_or_prompt
        params = parameters or {}
    else:
        prompt = ""
        params = parameters or {}

    blob = json.dumps({
        "generator": generator,
        "prompt": prompt,
        "parameters": params,
        "brand": brand_version,
    }, sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def cache_get(key: str, output_dir: str = None) -> Optional[str]:
    """Look up a cached asset by key. Returns file path or None."""
    d = _cache_dir()
    for f in d.iterdir():
        if f.name.startswith(key[:16]):
            return str(f)
    return None


def cache_put(key: str, source_path: str, extension: str = "") -> str:
    """Store a file in the cache. Returns the cache path."""
    d = _cache_dir()
    if not extension:
        extension = Path(source_path).suffix or ".png"
    dest = d / f"{key[:16]}{extension}"
    shutil.copy2(source_path, dest)
    return str(dest)


def cache_put_bytes(key: str, data: bytes, extension: str = ".png") -> str:
    """Store raw bytes in the cache. Returns the cache path."""
    d = _cache_dir()
    dest = d / f"{key[:16]}{extension}"
    dest.write_bytes(data)
    return str(dest)


def cache_has(key: str) -> bool:
    """Check if a cache entry exists."""
    return cache_get(key) is not None


def cache_clear() -> int:
    """Clear the entire cache. Returns number of files removed."""
    d = _cache_dir()
    count = 0
    for f in d.iterdir():
        if f.is_file():
            f.unlink()
            count += 1
    return count


def cache_size() -> tuple[int, int]:
    """Return (file_count, total_bytes) for the cache."""
    d = _cache_dir()
    files = [f for f in d.iterdir() if f.is_file()]
    total = sum(f.stat().st_size for f in files)
    return len(files), total
