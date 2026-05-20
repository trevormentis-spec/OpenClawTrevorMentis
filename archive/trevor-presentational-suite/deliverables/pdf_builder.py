"""TPS PDF Builder — extends existing scripts/render_pdf.py with TPS assets.

Does NOT replace the existing renderer. Imports its functions and adds:
- Asset image injection into the HTML template
- Provenance metadata table
- QC watermark stamp in footer
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

from deliverables.base import BaseDeliverableBuilder
from core.schemas import (
    PresentationPlan,
    AssetProvenance,
    DeliverableKind,
    QCStatus,
)
from core.style_director import get_qc_watermark
from core.exceptions import TPSError

# Import existing TREVOR render_pdf functions
TREVOR_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(TREVOR_ROOT))

try:
    from scripts.render_pdf import (
        load_template,
        render_template,
        enrich_brief_data,
        DEFAULT_TEMPLATE,
    )
    _RENDER_PDF_AVAILABLE = True
except ImportError:
    _RENDER_PDF_AVAILABLE = False
    DEFAULT_TEMPLATE = None


class PDFBuilder(BaseDeliverableBuilder):
    """Build an enhanced PDF that includes TPS-generated assets."""

    @property
    def kind(self) -> DeliverableKind:
        return DeliverableKind.PDF

    def build(
        self,
        brief_json: dict,
        plan: PresentationPlan,
        asset_outputs: dict[str, str],
        provenance_records: list[AssetProvenance],
        output_path: str,
    ) -> str:
        """Build enhanced PDF with injected TPS assets.

        Pipeline:
        1. Call existing enrich_brief_data()
        2. Load and render the HTML template
        3. Inject TPS asset images
        4. Append provenance metadata table
        5. Stamp QC review flag
        6. Render to PDF via weasyprint
        """
        if not _RENDER_PDF_AVAILABLE:
            raise TPSError(
                "scripts/render_pdf.py not importable. "
                "Ensure TREVOR is properly installed."
            )

        # 1. Enrich brief data using existing function
        data = enrich_brief_data(brief_json)

        # 2. Load and render template
        template = load_template(DEFAULT_TEMPLATE)
        html = render_template(template, data)

        # 3. Inject TPS assets
        html = self._inject_assets(html, plan, asset_outputs)

        # 4. Append provenance table
        html = self._append_provenance_section(html, provenance_records)

        # 5. Stamp QC flag
        html = self._stamp_qc_flag(html)

        # 6. Render PDF
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        try:
            from weasyprint import HTML
            HTML(string=html).write_pdf(output_path)
        except ImportError:
            # Fallback: write HTML only
            html_path = output_path.replace(".pdf", ".html")
            with open(html_path, "w") as f:
                f.write(html)
            return html_path

        return output_path

    def _inject_assets(
        self,
        html: str,
        plan: PresentationPlan,
        asset_outputs: dict[str, str],
    ) -> str:
        """Insert TPS-generated images into the HTML.

        Assets are inserted before the footer div, using the existing
        .chart-container CSS class from brief_template.html.
        """
        if not asset_outputs:
            return html

        asset_html_parts = []
        for spec in plan.assets:
            output_path = asset_outputs.get(spec.asset_id)
            if not output_path or not os.path.exists(output_path):
                continue

            # Convert to file:// URI for weasyprint
            abs_path = os.path.abspath(output_path)
            asset_html_parts.append(
                f'<div class="chart-container">'
                f'<img src="file://{abs_path}" alt="{spec.title}" '
                f'style="max-width:100%; max-height:3in;">'
                f'<div style="font-size:8pt; color:#999; margin-top:4px;">'
                f'{spec.title} &middot; Generated via {spec.generator}'
                f'</div></div>'
            )

        if not asset_html_parts:
            return html

        assets_block = "\n<h1>Generated Visual Assets</h1>\n" + "\n".join(asset_html_parts)

        # Insert before footer
        if '<div class="footer">' in html:
            html = html.replace(
                '<div class="footer">',
                f'{assets_block}\n<div class="footer">',
            )
        else:
            # Append before </body>
            html = html.replace("</body>", f"{assets_block}\n</body>")

        return html

    def _append_provenance_section(
        self,
        html: str,
        provenance_records: list[AssetProvenance],
    ) -> str:
        """Append a provenance metadata table to the HTML."""
        if not provenance_records:
            return html

        rows = []
        for p in provenance_records:
            rows.append(
                f"<tr>"
                f"<td>{p.asset_id}</td>"
                f"<td>{p.generator}</td>"
                f"<td>{p.model_used or 'local'}</td>"
                f"<td>${p.actual_cost_usd:.4f}</td>"
                f"<td>{p.qc_status.value}</td>"
                f"</tr>"
            )

        prov_html = (
            '<h1>Asset Provenance</h1>'
            '<table>'
            '<tr><th>Asset ID</th><th>Generator</th><th>Model</th>'
            '<th>Cost</th><th>QC Status</th></tr>'
            + "\n".join(rows)
            + '</table>'
        )

        if '<div class="footer">' in html:
            html = html.replace(
                '<div class="footer">',
                f'{prov_html}\n<div class="footer">',
            )
        else:
            html = html.replace("</body>", f"{prov_html}\n</body>")

        return html

    def _stamp_qc_flag(self, html: str) -> str:
        """Add PENDING HUMAN ANALYST QC REVIEW to footer."""
        watermark = get_qc_watermark()
        qc_div = f'<div style="color:#e94560; font-weight:700; font-size:9pt; margin-top:8px;">{watermark}</div>'

        if '<div class="footer">' in html:
            html = html.replace(
                '<div class="footer">',
                f'<div class="footer">{qc_div}',
            )
        else:
            html = html.replace("</body>", f"{qc_div}\n</body>")

        return html
