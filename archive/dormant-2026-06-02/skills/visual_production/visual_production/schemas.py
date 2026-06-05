"""Data schemas for visual production artefacts and configuration."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class ProductType(str, Enum):
    """Visual product types the pipeline can produce."""

    MAGAZINE = "magazine"
    BRIEF = "brief"
    INFOGRAPHIC = "infographic"
    SLIDE = "slide"
    REPORT = "report"


class NanoBananaRoute(str, Enum):
    """NanoBanana routing labels for visual production."""
    LOGIC_FLOW = "logic_flow"
    FLOW_CHAIN = "flow_chain"
    MAP_PLATE = "map_plate"
    DASHBOARD = "dashboard"
    SVG_CHART = "svg_chart"


class Classification(str, Enum):
    """Security classification banners."""

    UNCLASSIFIED = "UNCLASSIFIED"
    SENSITIVE = "SENSITIVE — For Authorised Recipients Only"
    CONFIDENTIAL = "CONFIDENTIAL"
    SECRET = "SECRET"
    TOP_SECRET = "TOP SECRET"


@dataclass
class InfographicSpec:
    """An infographic to be rasterised and inserted."""

    path: Path
    label: str = ""
    page_break_before: bool = True
    full_width: bool = True

    def __post_init__(self):
        if not self.label:
            self.label = self.path.stem.replace("infographic-", "").replace("-", " ").title()


@dataclass
class MermaidBlock:
    """A parsed Mermaid diagram block ready for rendering."""

    code: str
    index: int = 0
    rendered_path: Optional[Path] = None


@dataclass
class MagazineConfig:
    """Configuration for magazine-format PDF output."""

    title: str = "TREVOR INTELLIGENCE BRIEFING"
    issue: str = ""
    classification: Classification = Classification.SENSITIVE
    output_path: Path = Path("exports/pdfs/magazine-briefing.pdf")
    page_size: str = "A4"
    margin: str = "2cm 2cm 2.5cm 2cm"
    body_font: str = "Georgia, 'Times New Roman', serif"
    body_size: str = "10pt"
    headline_font: str = "Helvetica, Arial, sans-serif"
    accent_color: str = "#1a2744"
    gold_color: str = "#c9a84c"
    column_count: int = 2
    dpi_scale: float = 2.5
    temp_dir: Path = Path(".magazine-temp")

    def __post_init__(self):
        if not self.issue:
            self.issue = datetime.now(timezone.utc).strftime("%d %B %Y")
        if isinstance(self.output_path, str):
            self.output_path = Path(self.output_path)
        if isinstance(self.temp_dir, str):
            self.temp_dir = Path(self.temp_dir)


@dataclass
class VisualProductionPlan:
    """A plan describing how to produce one or more visual assets."""
    route: NanoBananaRoute = NanoBananaRoute.LOGIC_FLOW
    prompt_text: str = ""
    model: str = "google/gemini-3.1-flash-image-preview"
    aspect_ratio: str = "16:9"
    count: int = 1
    output_stem: str = "infographic"


@dataclass
class ProducedVisual:
    """A single produced visual asset."""
    asset_kind: str = "image"  # "image" | "pdf" | "svg"
    content: str = ""           # base64 data URL or path
    route: str = ""
    file_size_kb: float = 0.0
    success: bool = True
    error: str = ""


@dataclass
class ProductionResult:
    """Outcome of a visual production run."""

    success: bool
    output_path: Optional[Path] = None
    page_count: int = 0
    file_size_kb: float = 0.0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    product_type: Optional[ProductType] = None
    duration_seconds: float = 0.0
    visuals: list[ProducedVisual] = field(default_factory=list)

    def dict(self) -> dict:
        d = asdict(self)
        if self.output_path:
            d["output_path"] = str(self.output_path)
        if self.visuals:
            d["visuals"] = [
                {
                    "asset_kind": v.asset_kind,
                    "content": (v.content[:80] + "..." if len(v.content) > 80 else v.content),
                    "route": v.route,
                    "success": v.success,
                }
                for v in self.visuals
            ]
        return d

    def summary(self) -> str:
        status = "✅" if self.success else "❌"
        parts = [
            f"{status} {self.product_type.value if self.product_type else 'Visual'} product"
        ]
        if self.output_path:
            parts.append(f"→ {self.output_path.name}")
        if self.page_count:
            parts.append(f"({self.page_count} pp, {self.file_size_kb:.0f} KB)")
        if self.visuals:
            v_ok = sum(1 for v in self.visuals if v.success)
            parts.append(f"[{v_ok}/{len(self.visuals)} images]")
        if self.warnings:
            parts.append(f"⚠️ {len(self.warnings)} warnings")
        if self.errors:
            parts.append(f"🛑 {len(self.errors)} errors")
        return " ".join(parts)


@dataclass
class QualityReport:
    """Quality gate assessment."""

    passed: bool
    score: float = 0.0  # 0.0 – 1.0
    checks: dict[str, bool] = field(default_factory=dict)
    messages: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] Score: {self.score:.2f} — {len(self.messages)} checks"
