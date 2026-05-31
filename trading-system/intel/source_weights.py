#!/usr/bin/env python3
"""
Intel Source Weight Manager

Tracks reliability weights for intelligence sources.
Weights decay over time and improve with confirmed accuracy.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent.parent
STATE_FILE = REPO / "trading-system" / "calibration" / "source_weights.json"

# Default weights by source type
DEFAULT_WEIGHTS = {
    "OSINT": 0.5,
    "marketdata": 0.7,
    "official": 0.8,
    "expert": 0.6,
    "news": 0.4,
    "social": 0.2,
    "analyst": 0.3,
}


class SourceWeightManager:
    """Manages per-source reliability weights with decay."""

    def __init__(self, state_file: Optional[Path] = None):
        self.state_file = state_file or STATE_FILE
        self.weights = self._load()

    def _load(self) -> dict:
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {"sources": {}, "default_weights": DEFAULT_WEIGHTS}

    def _save(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.weights, indent=2))

    def get_weight(self, source_id: str, source_type: str) -> float:
        """Get effective weight for a source (0.0-1.0)."""
        return self.weights.get("sources", {}).get(
            source_id,
            DEFAULT_WEIGHTS.get(source_type, 0.3)
        )

    def update_weight(self, source_id: str, outcome_accuracy: float):
        """Update source weight after a confirmed outcome (0.0-1.0)."""
        current = self.weights.get("sources", {}).get(source_id, 0.3)
        # Exponential moving average
        new_weight = 0.7 * current + 0.3 * outcome_accuracy
        self.weights.setdefault("sources", {})[source_id] = round(new_weight, 3)
        self._save()

    def get_all_weights(self) -> dict:
        return dict(self.weights.get("sources", {}))
