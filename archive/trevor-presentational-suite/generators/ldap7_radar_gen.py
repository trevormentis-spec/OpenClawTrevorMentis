"""TPS LDAP-7 Radar Generator — 7-dimension radar chart for leadership scoring."""
from __future__ import annotations

import os
import math
from generators.base import BaseGenerator, GeneratorResult
from core.schemas import AssetSpec, AssetKind
from core.style_director import get_brand
from core.exceptions import GeneratorError


LDAP7_DIMENSIONS = [
    "Decision Speed", "Information Access", "Risk Tolerance",
    "Coalition Strength", "Succession Stability",
    "External Pressure", "Legitimacy",
]


class LDAP7RadarGenerator(BaseGenerator):
    """7-dimension radar chart for LDAP-7 leadership decision scoring."""

    @property
    def name(self) -> str:
        return "ldap7_radar"

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
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            raise GeneratorError("matplotlib not installed")

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{spec.asset_id}_ldap7.png")

        brand = get_brand()
        scores = spec.parameters.get("scores", [5] * 7)
        labels = spec.parameters.get("labels", LDAP7_DIMENSIONS)
        leader_name = spec.parameters.get("leader_name", spec.title)

        if len(scores) != 7:
            scores = (scores + [5] * 7)[:7]
        if len(labels) != 7:
            labels = LDAP7_DIMENSIONS

        angles = np.linspace(0, 2 * np.pi, 7, endpoint=False).tolist()
        scores_plot = scores + [scores[0]]
        angles += [angles[0]]

        fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
        ax.fill(angles, scores_plot, color=brand.color_primary, alpha=0.25)
        ax.plot(angles, scores_plot, color=brand.color_primary, linewidth=2)
        ax.scatter(angles[:-1], scores, color=brand.color_accent, s=60, zorder=5)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, size=9)
        ax.set_ylim(0, 10)
        ax.set_yticks([2, 4, 6, 8, 10])
        ax.set_yticklabels(["2", "4", "6", "8", "10"], size=8, color="#666")
        ax.set_title(f"LDAP-7: {leader_name}", size=14, fontweight="bold",
                      color=brand.color_body, pad=20)
        ax.set_facecolor("#F5F3EF")
        fig.patch.set_facecolor("#F5F3EF")

        plt.tight_layout()
        fig.savefig(output_path, dpi=200, bbox_inches="tight", facecolor="#F5F3EF")
        plt.close(fig)

        return GeneratorResult(
            output_path=output_path, actual_cost_usd=0.0,
            model_used="matplotlib-radar", provider="local",
        )
