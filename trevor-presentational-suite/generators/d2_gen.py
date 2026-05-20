"""TPS D2 Generator — system and architecture diagrams via Terrastruct D2."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

from generators.base import BaseGenerator, GeneratorResult
from core.schemas import AssetSpec, AssetKind
from core.exceptions import GeneratorError


class D2Generator(BaseGenerator):
    """System/architecture diagrams via D2 language."""

    @property
    def name(self) -> str:
        return "d2"

    @property
    def supported_kinds(self) -> list[str]:
        return [AssetKind.DIAGRAM.value]

    def is_available(self) -> bool:
        return shutil.which("d2") is not None

    def generate(self, spec: AssetSpec, output_dir: str) -> GeneratorResult:
        errors = self.validate_spec(spec)
        if errors:
            raise GeneratorError(f"Validation: {'; '.join(errors)}")
        if not spec.prompt:
            raise GeneratorError("No D2 code provided in spec.prompt")

        os.makedirs(output_dir, exist_ok=True)
        fmt = spec.parameters.get("format", "svg")
        output_path = os.path.join(output_dir, f"{spec.asset_id}_d2.{fmt}")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".d2", delete=False) as tmp:
            tmp.write(spec.prompt)
            tmp_path = tmp.name

        try:
            theme = spec.parameters.get("theme", "200")  # Dark theme
            result = subprocess.run(
                ["d2", f"--theme={theme}", tmp_path, output_path],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                raise GeneratorError(f"d2 failed: {result.stderr}")
        finally:
            os.unlink(tmp_path)

        return GeneratorResult(
            output_path=output_path, actual_cost_usd=0.0,
            model_used="d2", provider="local",
        )
