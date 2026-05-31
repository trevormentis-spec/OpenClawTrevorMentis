#!/usr/bin/env python3
"""
Kent Band Mapper

Converts natural-language certainty expressions into structured Kent band
probabilities. Provides lookup by band name and parsing from text.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

from intel.models import KENT_BANDS, VALID_KENT_BANDS

# Expression-to-band mapping for parsing
EXPRESSION_MAP = [
    (re.compile(r'\balmost certain\b', re.I), "almost_certain"),
    (re.compile(r'\bhighly likely\b', re.I), "highly_likely"),
    (re.compile(r'\blikely\b', re.I), "likely"),
    (re.compile(r'\bprobable\b', re.I), "probable"),
    (re.compile(r'\beven chance\b', re.I), "roughly_even_chance"),
    (re.compile(r'\broughly even\b', re.I), "roughly_even_chance"),
    (re.compile(r'\bunlikely\b', re.I), "unlikely"),
    (re.compile(r'\bimprobable\b', re.I), "improbable"),
    (re.compile(r'\bhighly unlikely\b', re.I), "highly_unlikely"),
    (re.compile(r'\bremote\b', re.I), "remote"),
    (re.compile(r'\balmost no chance\b', re.I), "almost_no_chance"),
]


def band_to_probability(band: str) -> Tuple[float, float]:
    """
    Convert a Kent band name to (p, sigma).

    Args:
        band: Kent band name (e.g., "highly_likely", "almost_certain")

    Returns:
        (point_probability, sigma) tuple

    Raises:
        ValueError: if band is not recognized
    """
    band = band.strip().lower().replace(" ", "_")
    if band not in KENT_BANDS:
        raise ValueError(f"Unknown Kent band: '{band}'. Valid: {sorted(VALID_KENT_BANDS)}")
    entry = KENT_BANDS[band]
    return entry["p"], entry["sigma"]


def probability_to_band(p: float) -> str:
    """
    Convert a numeric probability to the nearest Kent band.

    Args:
        p: Probability value (0.0-1.0)

    Returns:
        Nearest Kent band name
    """
    best_band = "roughly_even_chance"
    best_dist = float("inf")
    for band, info in KENT_BANDS.items():
        dist = abs(p - info["p"])
        if dist < best_dist:
            best_dist = dist
            best_band = band
    return best_band


def parse_certainty(text: str) -> Optional[str]:
    """
    Extract a Kent band from natural language text.
    Returns the first matching band name, or None.
    """
    for pattern, band in EXPRESSION_MAP:
        if pattern.search(text):
            return band
    return None


def band_display_name(band: str) -> str:
    """Convert internal band name to display form."""
    return band.replace("_", " ").title()
