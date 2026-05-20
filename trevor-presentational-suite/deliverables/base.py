"""TPS Deliverable Base — abstract protocol for all deliverable builders."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from core.schemas import (
    PresentationPlan,
    AssetProvenance,
    DeliverableKind,
)


class BaseDeliverableBuilder(ABC):
    """Abstract base for all deliverable builders.

    Each builder takes a TREVOR brief, a plan with generated assets,
    and produces a final deliverable (PDF, deck, website, etc.).
    """

    @property
    @abstractmethod
    def kind(self) -> DeliverableKind:
        """The deliverable type this builder produces."""

    @abstractmethod
    def build(
        self,
        brief_json: dict,
        plan: PresentationPlan,
        asset_outputs: dict[str, str],
        provenance_records: list[AssetProvenance],
        output_path: str,
    ) -> str:
        """Build the deliverable.

        Args:
            brief_json: Original TREVOR brief as dict.
            plan: The approved presentation plan.
            asset_outputs: Map of asset_id → output file path.
            provenance_records: Provenance for all generated assets.
            output_path: Where to write the final deliverable.

        Returns:
            Path to the built deliverable.
        """

    def validate_inputs(
        self,
        brief_json: dict,
        plan: PresentationPlan,
        asset_outputs: dict[str, str],
    ) -> list[str]:
        """Validate inputs before building. Returns list of errors."""
        errors = []
        if not brief_json:
            errors.append("brief_json is empty")
        if not plan.assets:
            errors.append("Plan has no assets")
        return errors
