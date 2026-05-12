#!/usr/bin/env python3
"""
trevor_config.py — Centralized configuration for Trevor DailyIntelAgent.

All path assumptions and environment-specific values live here.
Override any value via environment variable:
  TREVOR_WORKSPACE=/custom/path python3 script.py

Environment variables:
  TREVOR_WORKSPACE   — root workspace directory (default: derived from repo location)
  TREVOR_EXPORTS     — exports directory (default: $WORKSPACE/exports)
  TREVOR_DATA_DIR    — cached geographic data (default: $WORKSPACE/tmp/data)
  TREVOR_FONTS_DIR   — font files (default: $SKILL_ROOT/fonts)
  DEEPSEEK_API_KEY   — DeepSeek API key
  DEEPSEEK_BASE_URL  — DeepSeek API base URL
  DEEPSEEK_MODEL     — model name for generation
  MATON_API_KEY      — Gmail/Maton gateway key
  MOLTBOOK_API_KEY   — Moltbook publishing key
  MAPBOX_TOKEN       — Mapbox API token (optional)
  GENVIRAL_API_KEY   — GenViral image generation key
"""
from __future__ import annotations

import os
from pathlib import Path


def _get_repo_root() -> Path:
    """Find the repository root by walking up from this file's location."""
    # This file lives at skills/daily_intel/trevor_config.py or similar
    # Walk up to find the repo root (where .git lives)
    here = Path(__file__).resolve().parent
    for p in [here] + list(here.parents):
        if (p / ".git").exists() or (p / "skills" / "daily_intel").exists():
            return p
    return here  # fallback


def _get_skill_root() -> Path:
    """Find the daily_intel skill root."""
    here = Path(__file__).resolve().parent
    # If we're in skills/daily_intel/, that's the skill root
    if here.name == "daily_intel":
        return here
    # If we're in scripts/ under daily_intel
    if here.name == "scripts" and here.parent.name == "daily_intel":
        return here.parent
    return here


# ── Derived paths ──
_REPO_ROOT = _get_repo_root()
_SKILL_ROOT = _get_skill_root()
_WORKSPACE_ENV = os.environ.get("TREVOR_WORKSPACE", "")
_FALLBACK_WORKSPACE = _REPO_ROOT.parent.parent / "workspace"  # typical OpenClaw layout


# ── Exported config values (override via env vars) ──
WORKSPACE = Path(_WORKSPACE_ENV) if _WORKSPACE_ENV else (
    _FALLBACK_WORKSPACE if _FALLBACK_WORKSPACE.exists() else Path.home() / ".openclaw" / "workspace"
)

EXPORTS_DIR = Path(os.environ.get("TREVOR_EXPORTS", str(WORKSPACE / "exports")))
DATA_DIR = Path(os.environ.get("TREVOR_DATA_DIR", str(WORKSPACE / "tmp" / "data")))
FONTS_DIR = Path(os.environ.get("TREVOR_FONTS_DIR", str(_SKILL_ROOT / "fonts")))

# ── Theatres (single source of truth) ──
THEATRES = [
    {"key": "europe", "title": "Europe / Russia-Ukraine Conflict"},
    {"key": "africa", "title": "Sahel / Africa"},
    {"key": "asia", "title": "South Asia / Indo-Pacific"},
    {"key": "middle_east", "title": "Middle East / Iran"},
    {"key": "north_america", "title": "North America / Mexico Cartels"},
    {"key": "south_america", "title": "South America / Venezuela"},
    {"key": "global_finance", "title": "Global Finance / Prediction Markets"},
]
THEATRE_KEYS = [t["key"] for t in THEATRES]

# ── API Keys ──
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
MATON_API_KEY = os.environ.get("MATON_API_KEY", "")

# ── Pipeline defaults ──
DEEPSEEK_TIMEOUT_SECONDS = int(os.environ.get("DEEPSEEK_TIMEOUT", "120"))
DEEPSEEK_MAX_RETRIES = int(os.environ.get("DEEPSEEK_MAX_RETRIES", "2"))
HEARTBEAT_INTERVAL_SECONDS = 30
