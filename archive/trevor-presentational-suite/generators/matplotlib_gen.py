"""TPS Matplotlib Generator — print-ready static charts matching TREVOR PDF aesthetic."""
from __future__ import annotations

import os
import json
from generators.base import BaseGenerator, GeneratorResult
from core.schemas import AssetSpec, AssetKind
from core.style_director import get_chart_colors, get_kent_color, get_brand
from core.exceptions import GeneratorError


class MatplotlibGenerator(BaseGenerator):
    """Static chart generation via matplotlib."""

    @property
    def name(self) -> str:
        return "matplotlib"

    @property
    def supported_kinds(self) -> list[str]:
        return [AssetKind.CHART.value]

    def is_available(self) -> bool:
        try:
            import matplotlib
            return True
        except ImportError:
            return False

    def generate(self, spec: AssetSpec, output_dir: str) -> GeneratorResult:
        errors = self.validate_spec(spec)
        if errors:
            raise GeneratorError(f"Validation: {'; '.join(errors)}")

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.ticker as ticker
        except ImportError:
            raise GeneratorError("matplotlib not installed")

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{spec.asset_id}_chart.png")

        brand = get_brand()
        colors = get_chart_colors()
        chart_type = spec.parameters.get("chart_type", "bar")
        data = spec.parameters.get("data", {})
        title = spec.parameters.get("chart_title", spec.title)

        # Apply TREVOR PDF aesthetic
        plt.rcParams.update({
            "font.family": "sans-serif",
            "font.size": 10,
            "axes.facecolor": "#F5F3EF",
            "figure.facecolor": "#F5F3EF",
            "axes.edgecolor": "#cccccc",
            "axes.grid": True,
            "grid.color": "#e0e0e0",
            "grid.alpha": 0.5,
        })

        fig, ax = plt.subplots(figsize=(8, 5))

        labels = data.get("labels", [])
        values = data.get("values", [])

        if chart_type == "bar":
            bar_colors = [colors[i % len(colors)] for i in range(len(labels))]
            ax.bar(labels, values, color=bar_colors)
        elif chart_type == "line":
            ax.plot(labels, values, color=colors[0], linewidth=2, marker="o", markersize=4)
        elif chart_type == "pie":
            pie_colors = [colors[i % len(colors)] for i in range(len(labels))]
            ax.pie(values, labels=labels, colors=pie_colors, autopct="%1.0f%%")
        elif chart_type == "horizontal_bar":
            bar_colors = [colors[i % len(colors)] for i in range(len(labels))]
            ax.barh(labels, values, color=bar_colors)
        elif chart_type == "scatter":
            x_vals = data.get("x", values)
            y_vals = data.get("y", values)
            ax.scatter(x_vals, y_vals, color=colors[0], s=50, alpha=0.7)
        elif chart_type == "kent_bar":
            # Sherman Kent probability band chart
            kent_colors_list = [get_kent_color(l) for l in labels]
            ax.barh(labels, values, color=kent_colors_list)
            ax.set_xlabel("Probability (%)")

        ax.set_title(title, fontsize=13, fontweight="bold", color=brand.color_body)

        x_label = data.get("x_label", "")
        y_label = data.get("y_label", "")
        if x_label:
            ax.set_xlabel(x_label)
        if y_label:
            ax.set_ylabel(y_label)

        plt.tight_layout()
        fig.savefig(output_path, dpi=200, bbox_inches="tight", facecolor="#F5F3EF")
        plt.close(fig)

        return GeneratorResult(
            output_path=output_path, actual_cost_usd=0.0,
            model_used="matplotlib", provider="local",
        )
