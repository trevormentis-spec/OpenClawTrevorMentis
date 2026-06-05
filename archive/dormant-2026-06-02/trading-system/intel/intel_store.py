#!/usr/bin/env python3
"""
Intel Store — Append-Only KJ Repository

Stores all ingested Key Judgments with provenance.
Supports query by ID, region, time range, and risk factor.

This is the system's memory. Nothing is ever deleted.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Iterator

from intel.models import KeyJudgment, now_iso, parse_iso

REPO = Path(__file__).resolve().parent.parent.parent
STORE_FILE = REPO / "trading-system" / "intel" / "kj_store.jsonl"


class IntelStore:
    """Append-only store for Key Judgments."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or STORE_FILE
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Touch file if not exists
        if not self.path.exists():
            self.path.touch()

    def ingest(self, kj: KeyJudgment) -> str:
        """Store a KJ and return its ID.

        Validates the KJ before storing. Raises ValueError on invalid input.
        """
        errors = kj.validate()
        if errors:
            raise ValueError(f"Invalid KJ: {'; '.join(errors)}")

        entry = {
            "event": "kj_ingested",
            "timestamp": now_iso(),
            "kj_id": kj.kj_id,
            "data": kj.to_dict(),
        }

        with open(self.path, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

        return kj.kj_id

    def get(self, kj_id: str) -> Optional[KeyJudgment]:
        """Retrieve a KJ by ID."""
        for entry in self._iter():
            if entry.get("kj_id") == kj_id:
                return KeyJudgment.from_dict(entry["data"])
        return None

    def list_recent(self, limit: int = 50) -> list[KeyJudgment]:
        """Get the most recent KJs."""
        all_kjs = list(self._iter())
        return [KeyJudgment.from_dict(e["data"]) for e in all_kjs[-limit:]]

    def list_by_region(self, region: str, limit: int = 50) -> list[KeyJudgment]:
        """Get KJs for a specific region."""
        results = []
        for entry in self._iter():
            if entry.get("data", {}).get("region", "").upper() == region.upper():
                results.append(KeyJudgment.from_dict(entry["data"]))
        return results[-limit:]

    def list_by_factor(self, factor: str, limit: int = 50) -> list[KeyJudgment]:
        """Get KJs tagged with a specific risk factor."""
        results = []
        for entry in self._iter():
            factors = entry.get("data", {}).get("risk_factors", [])
            if factor in factors:
                results.append(KeyJudgment.from_dict(entry["data"]))
        return results[-limit:]

    def list_expiring_before(self, cutoff_iso: str) -> list[KeyJudgment]:
        """Get KJs whose horizon is before cutoff."""
        cutoff = parse_iso(cutoff_iso)
        results = []
        for entry in self._iter():
            horizon = entry.get("data", {}).get("horizon")
            if horizon and parse_iso(horizon) <= cutoff:
                results.append(KeyJudgment.from_dict(entry["data"]))
        return results

    def count(self) -> int:
        """Total number of stored KJs."""
        return sum(1 for _ in self._iter())

    def _iter(self) -> Iterator[dict]:
        """Iterate over stored entries in order."""
        if not self.path.exists():
            return
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
