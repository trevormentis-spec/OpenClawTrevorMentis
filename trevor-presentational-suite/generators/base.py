"""TPS Generator Base — abstract protocol for all asset generators."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GeneratorResult:
    """Result from a generator execution."""
    output_path: str
    output_bytes: bytes = b""
    actual_cost_usd: float = 0.0
    generation_time_sec: float = 0.0
    model_used: str = ""
    provider: str = ""
    metadata: dict = field(default_factory=dict)


class BaseGenerator(ABC):
    """Abstract base for all TPS generators.

    Each generator handles one or more AssetKind values and wraps
    a specific rendering tool or API provider.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Generator identifier, e.g. 'mermaid', 'mapbox_static'."""

    @property
    @abstractmethod
    def supported_kinds(self) -> list[str]:
        """AssetKind values this generator can produce."""

    @abstractmethod
    def generate(self, spec, output_dir: str) -> GeneratorResult:
        """Execute generation for the given AssetSpec.

        Args:
            spec: AssetSpec describing what to generate.
            output_dir: Directory to write output files.

        Returns:
            GeneratorResult with output path and metadata.

        Raises:
            GeneratorError on failure.
        """

    def is_available(self) -> bool:
        """Check if this generator's dependencies are available.

        Override in subclasses that require external binaries or API keys.
        """
        return True

    def validate_spec(self, spec) -> list[str]:
        """Validate an AssetSpec for this generator.

        Returns list of error messages (empty = valid).
        """
        errors = []
        if spec.kind.value not in self.supported_kinds:
            errors.append(
                f"Generator '{self.name}' does not support kind '{spec.kind.value}'. "
                f"Supported: {self.supported_kinds}"
            )
        return errors
