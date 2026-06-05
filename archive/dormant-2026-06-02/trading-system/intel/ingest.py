#!/usr/bin/env python3
"""
Intel Ingest — Entry Point for Intelligence Inputs

Receives KJs from the daily brief pipeline and other intelligence sources.
Validates, enriches with decay config, stores in the append-only store.

This is the ONLY way KJs enter the system. No manual probability creation.
"""

from __future__ import annotations

import sys
import json
from pathlib import Path
from typing import Optional

from intel.models import (
    KeyJudgment, DecayConfig, Provenance, SourceRef, now_iso, VALID_KENT_BANDS
)
from intel.intel_store import IntelStore
from intel.source_weights import SourceWeightManager
from intel.kent_mapper import band_to_probability


# Default decay configs per topic area
DEFAULT_DECAY: dict[str, dict] = {
    "fast": {"model": "exponential", "half_life_hours": 24},       # Tactical events
    "standard": {"model": "exponential", "half_life_hours": 72},   # Most KJs
    "slow": {"model": "exponential", "half_life_hours": 336},      # Strategic trends (14 days)
    "permanent": {"model": "none"},                                 # Structural facts
}

# Default decay assignment by region
REGION_DECAY = {
    "MENA": "standard",
    "EURASIA": "standard",
    "EAST_ASIA": "slow",
    "SOUTH_ASIA": "standard",
    "EUROPE": "standard",
    "AMERICAS": "standard",
    "SUB_SAHARAN_AFRICA": "slow",
    "GLOBAL": "slow",
}


def ingest_kj(
    claim: str,
    kent_band: str,
    region: str,
    kj_id: str,
    sources: Optional[list[dict]] = None,
    risk_factors: Optional[list[str]] = None,
    horizon: Optional[str] = None,
    decay_speed: Optional[str] = None,
    p_point: Optional[float] = None,
    p_ci: Optional[list[float]] = None,
    analyst: str = "trevor",
    model: str = "deepseek-flash",
    brief_id: str = "",
) -> str:
    """Create and store a KJ.

    Returns the kj_id of the stored judgment.
    """
    # Determine decay config
    if decay_speed is None:
        decay_speed = REGION_DECAY.get(region, "standard")

    decay_config_data = DEFAULT_DECAY.get(decay_speed, DEFAULT_DECAY["standard"])
    decay = DecayConfig(**decay_config_data)

    # Build provenance
    source_refs = []
    for s in (sources or []):
        source_refs.append(SourceRef(
            id=s.get("id", f"S-{len(source_refs)+1}"),
            type=s.get("type", "OSINT"),
            ref=s.get("ref", ""),
            weight=s.get("weight", 0.5),
            ts=s.get("ts", now_iso()),
        ))

    provenance = Provenance(
        analyst=analyst,
        model=model,
        brief_id=brief_id,
        sources=source_refs,
    )

    # Build KJ
    kj = KeyJudgment(
        kj_id=kj_id,
        issued_at=now_iso(),
        region=region.upper(),
        claim=claim,
        kent_band=kent_band,
        p_point=p_point,
        p_ci=p_ci,
        horizon=horizon,
        provenance=provenance,
        decay=decay,
        risk_factors=risk_factors or [],
    )

    # Validate
    errors = kj.validate()
    if errors:
        raise ValueError(f"KJ validation failed: {'; '.join(errors)}")

    # Store
    store = IntelStore()
    result_id = store.ingest(kj)

    return result_id


def ingest_from_brief_json(brief_json_path: str) -> list[str]:
    """Batch-ingest KJs from a brief pipeline JSON output.

    Expected format: list of dicts with fields matching ingest_kj()
    """
    path = Path(brief_json_path)
    if not path.exists():
        raise FileNotFoundError(f"Brief file not found: {brief_json_path}")

    with open(path) as f:
        entries = json.load(f)

    if isinstance(entries, dict):
        entries = [entries]

    ids = []
    for entry in entries:
        try:
            kj_id = ingest_kj(
                claim=entry["claim"],
                kent_band=entry["kent_band"],
                region=entry.get("region", "GLOBAL"),
                kj_id=entry.get("kj_id", f"KJ-{now_iso()[:10]}-{len(ids)}"),
                sources=entry.get("sources"),
                risk_factors=entry.get("risk_factors", []),
                horizon=entry.get("horizon"),
                decay_speed=entry.get("decay_speed"),
                p_ci=entry.get("p_ci"),
                brief_id=entry.get("brief_id", ""),
            )
            ids.append(kj_id)
        except (ValueError, KeyError) as e:
            print(f"  ⚠️  Skipped entry: {e}", file=sys.stderr)

    return ids
