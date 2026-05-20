"""TPS HTML-to-Image Generator — render HTML/CSS layouts to PNG via weasyprint."""
from __future__ import annotations

import io
import os
from generators.base import BaseGenerator, GeneratorResult
from core.schemas import AssetSpec, AssetKind
from core.exceptions import GeneratorError


class HTMLToImageGenerator(BaseGenerator):
    """Convert HTML/CSS layouts to PNG via weasyprint headless render."""

    @property
    def name(self) -> str:
        return "html_to_png"

    @property
    def supported_kinds(self) -> list[str]:
        return [AssetKind.INFOGRAPHIC.value, AssetKind.TABLE.value]

    def is_available(self) -> bool:
        try:
            from weasyprint import HTML
            return True
        except ImportError:
            return False

    def generate(self, spec: AssetSpec, output_dir: str) -> GeneratorResult:
        errors = self.validate_spec(spec)
        if errors:
            raise GeneratorError(f"Validation: {'; '.join(errors)}")
        if not spec.prompt:
            raise GeneratorError("No HTML provided in spec.prompt")

        try:
            from weasyprint import HTML
        except ImportError:
            raise GeneratorError("weasyprint not installed")

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{spec.asset_id}_render.png")

        html_content = spec.prompt
        width = spec.parameters.get("width", 1200)

        # weasyprint >= 60 removed write_png; render to PDF then convert via pdf2image
        pdf_bytes = io.BytesIO()
        HTML(string=html_content).write_pdf(pdf_bytes, presentational_hints=True)
        pdf_bytes.seek(0)
        from pdf2image import convert_from_bytes
        images = convert_from_bytes(pdf_bytes.read(), dpi=width // 8 if width else 150, first_page=1, last_page=1)
        if images:
            images[0].save(output_path, "PNG")

        return GeneratorResult(
            output_path=output_path, actual_cost_usd=0.0,
            model_used="weasyprint", provider="local",
        )
