"""TPS Plotly Generator — interactive web charts."""
from __future__ import annotations

import os
import json
from generators.base import BaseGenerator, GeneratorResult
from core.schemas import AssetSpec, AssetKind
from core.style_director import get_chart_colors, get_brand
from core.exceptions import GeneratorError


class PlotlyGenerator(BaseGenerator):
    """Interactive chart generation via Plotly (HTML output)."""

    @property
    def name(self) -> str:
        return "plotly"

    @property
    def supported_kinds(self) -> list[str]:
        return [AssetKind.CHART.value]

    def is_available(self) -> bool:
        try:
            import plotly
            return True
        except ImportError:
            return False

    def generate(self, spec: AssetSpec, output_dir: str) -> GeneratorResult:
        errors = self.validate_spec(spec)
        if errors:
            raise GeneratorError(f"Validation: {'; '.join(errors)}")

        try:
            import plotly.graph_objects as go
        except ImportError:
            raise GeneratorError("plotly not installed")

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{spec.asset_id}_chart.html")

        brand = get_brand()
        colors = get_chart_colors()
        chart_type = spec.parameters.get("chart_type", "bar")
        data = spec.parameters.get("data", {})
        title = spec.parameters.get("chart_title", spec.title)

        labels = data.get("labels", [])
        values = data.get("values", [])

        fig = go.Figure()

        if chart_type == "bar":
            fig.add_trace(go.Bar(x=labels, y=values, marker_color=colors[:len(labels)]))
        elif chart_type == "line":
            fig.add_trace(go.Scatter(x=labels, y=values, mode="lines+markers", line=dict(color=colors[0])))
        elif chart_type == "pie":
            fig.add_trace(go.Pie(labels=labels, values=values, marker=dict(colors=colors[:len(labels)])))
        elif chart_type == "scatter":
            x_vals = data.get("x", values)
            y_vals = data.get("y", values)
            fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode="markers", marker=dict(color=colors[0])))

        fig.update_layout(
            title=dict(text=title, font=dict(size=16, color=brand.color_body)),
            plot_bgcolor="#F5F3EF",
            paper_bgcolor="#F5F3EF",
            font=dict(family="Inter, sans-serif"),
        )

        fig.write_html(output_path, include_plotlyjs="cdn")

        return GeneratorResult(
            output_path=output_path, actual_cost_usd=0.0,
            model_used="plotly", provider="local",
        )
