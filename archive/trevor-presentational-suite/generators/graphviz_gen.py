"""TPS Graphviz Generator — network, relationship, and org diagrams."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

from generators.base import BaseGenerator, GeneratorResult
from core.schemas import AssetSpec, AssetKind
from core.exceptions import GeneratorError


class GraphvizGenerator(BaseGenerator):
    """Network/relationship diagrams via Graphviz dot."""

    @property
    def name(self) -> str:
        return "graphviz"

    @property
    def supported_kinds(self) -> list[str]:
        return [AssetKind.DIAGRAM.value]

    def is_available(self) -> bool:
        return shutil.which("dot") is not None

    def generate(self, spec: AssetSpec, output_dir: str) -> GeneratorResult:
        errors = self.validate_spec(spec)
        if errors:
            raise GeneratorError(f"Validation: {'; '.join(errors)}")
        if not spec.prompt:
            raise GeneratorError("No DOT code provided in spec.prompt")

        os.makedirs(output_dir, exist_ok=True)
        fmt = spec.parameters.get("format", "png")
        output_path = os.path.join(output_dir, f"{spec.asset_id}_graphviz.{fmt}")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".dot", delete=False) as tmp:
            tmp.write(spec.prompt)
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                ["dot", f"-T{fmt}", tmp_path, "-o", output_path],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                raise GeneratorError(f"dot failed: {result.stderr}")
        finally:
            os.unlink(tmp_path)

        return GeneratorResult(
            output_path=output_path, actual_cost_usd=0.0,
            model_used="graphviz-dot", provider="local",
        )
