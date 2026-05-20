"""TPS Mermaid Generator — Mermaid diagram code → SVG/PNG.

Primary: local mmdc CLI (npm @mermaid-js/mermaid-cli).
Fallback: mermaid.ink HTTP API (zero-cost, no install needed).
"""
from __future__ import annotations

import base64
import os
import shutil
import subprocess
import tempfile
import time
import urllib.request
import urllib.error
from pathlib import Path

from generators.base import BaseGenerator, GeneratorResult
from core.schemas import AssetSpec, AssetKind
from core.exceptions import GeneratorError


MERMAID_INK_URL = "https://mermaid.ink/img/"


class MermaidGenerator(BaseGenerator):
    """Generate diagrams from Mermaid syntax."""

    @property
    def name(self) -> str:
        return "mermaid"

    @property
    def supported_kinds(self) -> list[str]:
        return [AssetKind.DIAGRAM.value]

    def is_available(self) -> bool:
        """Check if mmdc is installed, or mermaid.ink is assumed reachable."""
        return self._has_mmdc() or True  # mermaid.ink is always a fallback

    def generate(self, spec: AssetSpec, output_dir: str) -> GeneratorResult:
        """Render Mermaid code to PNG.

        1. Try local mmdc binary.
        2. Fall back to mermaid.ink HTTP API.
        """
        errors = self.validate_spec(spec)
        if errors:
            raise GeneratorError(f"Validation failed: {'; '.join(errors)}")

        if not spec.prompt:
            raise GeneratorError("No Mermaid code provided in spec.prompt")

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{spec.asset_id}_mermaid.png")

        start = time.time()

        if self._has_mmdc():
            result = self._render_via_cli(spec.prompt, output_path)
        else:
            result = self._render_via_api(spec.prompt, output_path)

        result.generation_time_sec = time.time() - start
        return result

    def _has_mmdc(self) -> bool:
        """Check if mmdc binary is available."""
        return shutil.which("mmdc") is not None

    def _render_via_cli(self, mermaid_code: str, output_path: str) -> GeneratorResult:
        """Render via local mmdc binary."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".mmd", delete=False
        ) as tmp:
            tmp.write(mermaid_code)
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                ["mmdc", "-i", tmp_path, "-o", output_path, "-b", "transparent"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                raise GeneratorError(
                    f"mmdc failed (exit {result.returncode}): {result.stderr}"
                )
        finally:
            os.unlink(tmp_path)

        return GeneratorResult(
            output_path=output_path,
            actual_cost_usd=0.0,
            model_used="mermaid-cli",
            provider="local",
        )

    def _render_via_api(self, mermaid_code: str, output_path: str) -> GeneratorResult:
        """Render via mermaid.ink HTTP API."""
        encoded = base64.urlsafe_b64encode(mermaid_code.encode("utf-8")).decode("ascii")
        url = MERMAID_INK_URL + encoded

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TPS/0.1"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            raise GeneratorError(f"mermaid.ink API failed: {e}") from e

        with open(output_path, "wb") as f:
            f.write(data)

        return GeneratorResult(
            output_path=output_path,
            output_bytes=data,
            actual_cost_usd=0.0,
            model_used="mermaid.ink",
            provider="mermaid.ink",
        )
