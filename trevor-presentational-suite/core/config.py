"""TPS Configuration — loads providers.yaml and brand.yaml.

Uses a simple YAML parser matching TREVOR's existing pattern (no PyYAML).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

TPS_ROOT = Path(__file__).resolve().parent.parent
TREVOR_ROOT = TPS_ROOT.parent
PROVIDERS_PATH = TPS_ROOT / "providers.yaml"
BRAND_PATH = TPS_ROOT / "brand.yaml"


def _parse_simple_yaml(path: Path) -> dict[str, Any]:
    """Parse a flat/nested YAML file into a dict.

    Handles:
    - key: value (scalars)
    - key: (no value → start of nested dict on next indented lines)
    - Indented key: value (nested dict entries)
    - Lists are NOT handled (not needed for our YAML files at this level).
    - Comments (#) and blank lines are skipped.
    """
    if not path.exists():
        return {}

    result: dict[str, Any] = {}
    current_section: str | None = None

    with open(path) as f:
        for line in f:
            stripped = line.rstrip()
            if not stripped or stripped.startswith("#"):
                continue

            indent = len(line) - len(line.lstrip())

            # Top-level key
            if indent == 0 and ":" in stripped:
                key, _, val = stripped.partition(":")
                key = key.strip()
                val = val.strip()
                if val:
                    result[key] = _coerce_value(val)
                    current_section = None
                else:
                    result[key] = {}
                    current_section = key

            # Nested key under current section
            elif indent > 0 and current_section is not None and ":" in stripped:
                key, _, val = stripped.partition(":")
                key = key.strip()
                val = val.strip()
                if isinstance(result[current_section], dict):
                    result[current_section][key] = _coerce_value(val)

    return result


def _coerce_value(val: str) -> Any:
    """Coerce a YAML value string to Python type."""
    if not val:
        return ""

    # Remove quotes
    if (val.startswith('"') and val.endswith('"')) or \
       (val.startswith("'") and val.endswith("'")):
        return val[1:-1]

    # Booleans
    if val.lower() in ("true", "yes"):
        return True
    if val.lower() in ("false", "no"):
        return False

    # Numbers
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        pass

    # List shorthand [a, b]
    if val.startswith("[") and val.endswith("]"):
        items = val[1:-1].split(",")
        return [_coerce_value(item.strip()) for item in items if item.strip()]

    return val


class BrandConfig:
    """Brand configuration loaded from brand.yaml."""

    def __init__(self, data: dict[str, Any] | None = None):
        d = data or {}
        self.brand_name: str = d.get("brand_name", "Trevor Intelligence")
        self.color_primary: str = d.get("color_primary", "#0f3460")
        self.color_accent: str = d.get("color_accent", "#e94560")
        self.color_body: str = d.get("color_body", "#1a1a2e")
        self.color_surface: str = d.get("color_surface", "#f5f5f5")
        self.font_body: str = d.get("font_body", "Inter")
        self.font_heading: str = d.get("font_heading", "Inter")
        self.qc_watermark: str = d.get("qc_watermark", "PENDING HUMAN ANALYST QC REVIEW")
        self.kent_colors: dict[str, str] = d.get("kent_colors", {
            "almost_certain": "#00b300",
            "highly_likely": "#33cc33",
            "likely": "#99cc33",
            "probable": "#cccc33",
            "even_chance": "#cc9933",
            "unlikely": "#cc6633",
            "highly_unlikely": "#cc3333",
            "remote": "#990000",
        })
        self.chart_palette: dict[str, str] = d.get("chart_palette", {
            "cream": "#F5F3EF",
            "red": "#C0392B",
            "blue": "#1B3A5C",
            "gold": "#B8860B",
            "green": "#2E7D32",
            "orange": "#E67E22",
            "grey": "#6B6B6B",
        })


class ProviderInfo:
    """Info for a single provider from providers.yaml."""

    def __init__(self, name: str, data: dict[str, Any]):
        self.name = name
        self.provider_type: str = data.get("type", "remote")
        self.base_url: str = data.get("base_url", "")
        self.env_key: str = data.get("env_key", "")
        self.per_image_usd: float = float(data.get("per_image_usd", 0.0))
        self.per_char_usd: float = float(data.get("per_char_usd", 0.0))
        self.per_sec_usd: float = float(data.get("per_sec_usd", 0.0))
        self.cost_per_render: float = float(data.get("cost_per_render", 0.0))
        self.time_sec: float = float(data.get("time_sec", 5.0))
        self.rate_limit_rpm: int = int(data.get("rate_limit_rpm", 60))
        self.timeout_sec: int = int(data.get("timeout_sec", 120))
        self.last_verified: str = str(data.get("last_verified", ""))
        self.raw = data

    def is_available(self) -> bool:
        """Check if this provider's credentials are set."""
        if self.provider_type == "local":
            return True
        if not self.env_key:
            return True
        return bool(os.environ.get(self.env_key, ""))


class TPSConfig:
    """Top-level TPS configuration."""

    def __init__(self):
        self._providers_data = _parse_simple_yaml(PROVIDERS_PATH)
        self._brand_data = _parse_simple_yaml(BRAND_PATH)
        self.brand = BrandConfig(self._brand_data)
        self.auto_approve_threshold_usd: float = 0.50
        self.high_cost_asset_threshold_usd: float = 5.00
        self.cache_dir: str = str(TPS_ROOT / "cache")
        self.output_dir: str = str(TREVOR_ROOT / "exports" / "tps")

    def get_provider(self, name: str) -> ProviderInfo:
        """Get provider config by name."""
        data = self._providers_data.get(name, {})
        if isinstance(data, dict):
            return ProviderInfo(name, data)
        return ProviderInfo(name, {})

    def get_fallback_chain(self, chain_name: str) -> list[str]:
        """Get a fallback chain by name."""
        chains = self._providers_data.get("fallback_chains", {})
        if isinstance(chains, dict):
            chain = chains.get(chain_name, [])
            if isinstance(chain, list):
                return chain
        return []


# Singleton
_config: TPSConfig | None = None


def get_config() -> TPSConfig:
    """Get or create the singleton TPSConfig."""
    global _config
    if _config is None:
        _config = TPSConfig()
    return _config
