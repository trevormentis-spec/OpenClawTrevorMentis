"""Router — entry point that dispatches by product type to the appropriate pipeline.

Usage
-----
    from visual_production.router import produce

    result = produce(
        markdown_path="tasks/briefing.md",
        product="magazine",
        title="TREVOR GLOBAL INTELLIGENCE BRIEFING",
        output="exports/pdfs/briefing.pdf",
    )

NanoBanana routing
------------------
    logic_flow → nano_banana flow_chain
    flow_chain → nano_banana flow_chain → nano_banana map_plate
    map_plate  → nano_banana map_plate
    dashboard  → nano_banana dashboard → svg_chart → svg
    svg_chart  → svg chart
"""
from __future__ import annotations

import time
import tempfile
from pathlib import Path
from typing import Optional

from .schemas import (
    ProductType,
    MagazineConfig,
    ProductionResult,
    Classification,
    InfographicSpec,
    NanoBananaRoute,
    VisualProductionPlan,
    ProducedVisual,
)
from .pipeline import build_magazine, generate_infographic_image, resolve_nano_chain
from .quality_gate import assess_pdf, validate_text_output


def produce(
    markdown_path: str | Path,
    product: str | ProductType = "magazine",
    title: Optional[str] = None,
    issue: Optional[str] = None,
    classification: str = "SENSITIVE — For Authorised Recipients Only",
    infographics: Optional[list[str]] = None,
    output: Optional[str] = None,
    run_quality_gate: bool = True,
    nano_route: Optional[str] = None,
    **kwargs,
) -> ProductionResult:
    """High-level entry point for visual product generation.

    Parameters
    ----------
    markdown_path : str | Path
        Path to the markdown analysis file.
    product : str | ProductType
        Product type (``"magazine"``, ``"brief"``, ``"infographic"``, etc.).
    title : str | None
        Publication title (defaults to MagazineConfig default).
    issue : str | None
        Issue / date label.
    classification : str
        Security classification banner.
    infographics : list[str] | None
        Paths to SVG infographics to include.
    output : str | None
        Output PDF path.
    run_quality_gate : bool
        Run post-render validation.
    nano_route : str | None
        NanoBanana route override (``"logic_flow"``, ``"flow_chain"``,
        ``"map_plate"``, ``"dashboard"``, ``"svg_chart"``).
        If None, defaults based on product type.
    **kwargs
        Additional config overrides passed to the pipeline.

    Returns
    -------
    ProductionResult
    """
    start = time.monotonic()

    # Normalise product type
    if isinstance(product, str):
        try:
            product_type = ProductType(product.lower())
        except ValueError:
            return ProductionResult(
                success=False,
                errors=[f"Unknown product type: {product}. Valid: {[p.value for p in ProductType]}"],
            )
    else:
        product_type = product

    md_path = Path(markdown_path)
    if not md_path.exists():
        return ProductionResult(
            success=False,
            errors=[f"Input markdown not found: {markdown_path}"],
        )

    # Build config
    config = MagazineConfig(
        title=title or "TREVOR INTELLIGENCE BRIEFING",
        issue=issue or "",
        classification=Classification(classification) if classification else Classification.SENSITIVE,
        output_path=Path(output) if output else Path("exports/pdfs/magazine-briefing.pdf"),
    )

    # Parse infographics
    svg_specs: list[InfographicSpec] = []
    if infographics:
        for path in infographics:
            p = Path(path)
            svg_specs.append(InfographicSpec(path=p))

    # Resolve NanoBanana route
    if nano_route:
        try:
            route = NanoBananaRoute(nano_route.lower())
        except ValueError:
            return ProductionResult(
                success=False,
                errors=[f"Unknown nano_route: {nano_route}. Valid: {[r.value for r in NanoBananaRoute]}"],
            )
    else:
        # Default route based on product type
        route_map = {
            ProductType.MAGAZINE: NanoBananaRoute.LOGIC_FLOW,
            ProductType.BRIEF: NanoBananaRoute.FLOW_CHAIN,
            ProductType.INFOGRAPHIC: NanoBananaRoute.MAP_PLATE,
            ProductType.SLIDE: NanoBananaRoute.DASHBOARD,
            ProductType.REPORT: NanoBananaRoute.LOGIC_FLOW,
        }
        route = route_map.get(product_type, NanoBananaRoute.LOGIC_FLOW)

    # Read raw text for NanoBanana processing
    raw_text = md_path.read_text(encoding="utf-8")

    # ── Validate text output BEFORE image generation ──
    rejection = validate_text_output(raw_text)
    if rejection and product_type in (ProductType.INFOGRAPHIC, ProductType.SLIDE):
        return ProductionResult(
            success=False,
            errors=[f"Text validation rejected: {'; '.join(rejection)}"],
            product_type=product_type,
        )

    # ── Dispatch ──
    if product_type == ProductType.MAGAZINE:
        result = build_magazine(
            markdown_path=md_path,
            config=config,
            svg_infographics=svg_specs,
            **kwargs,
        )
    elif product_type == ProductType.INFOGRAPHIC:
        # NanoBanana image generation path
        plans = resolve_nano_chain(route, raw_text)
        with tempfile.TemporaryDirectory(prefix="nanobanana_") as tmpdir:
            img_dir = Path(tmpdir)
            visuals: list[ProducedVisual] = []
            errors_list: list[str] = []

            for plan in plans:
                visual = generate_infographic_image(plan, img_dir)
                visuals.append(visual)
                if not visual.success:
                    errors_list.append(f"{plan.route.value}: {visual.error}")

            result = ProductionResult(
                success=len(errors_list) == 0,
                warnings=[f"{len(visuals)} image(s) generated"] if visuals else [],
                errors=errors_list,
                product_type=product_type,
                visuals=visuals,
                output_path=Path(output) if output else None,
            )
    elif product_type == ProductType.SLIDE:
        # NanoBanana image generation path, dashboard route
        plans = resolve_nano_chain(route, raw_text)
        with tempfile.TemporaryDirectory(prefix="nanobanana_") as tmpdir:
            img_dir = Path(tmpdir)
            visuals = []
            errors_list = []

            for plan in plans:
                visual = generate_infographic_image(plan, img_dir)
                visuals.append(visual)
                if not visual.success:
                    errors_list.append(f"{plan.route.value}: {visual.error}")

            result = ProductionResult(
                success=len(errors_list) == 0,
                warnings=[f"{len(visuals)} slide image(s) generated"] if visuals else [],
                errors=errors_list,
                product_type=product_type,
                visuals=visuals,
            )
    elif product_type == ProductType.BRIEF:
        result = ProductionResult(
            success=False,
            errors=["Brief pipeline not yet implemented — fallback to magazine."],
            product_type=product_type,
        )
    else:
        result = ProductionResult(
            success=False,
            errors=[f"Pipeline for '{product_type.value}' not yet implemented."],
            product_type=product_type,
        )

    result.duration_seconds = round(time.monotonic() - start, 2)
    result.product_type = product_type

    # Quality gate (PDF products only)
    if run_quality_gate and result.success and result.output_path:
        if result.product_type == ProductType.MAGAZINE:
            qr = assess_pdf(
                pdf_path=result.output_path,
                config=config,
                source_text=raw_text,
                svg_paths=[s.path for s in svg_specs],
            )
            if not qr.passed:
                result.warnings.append(f"Quality gate score: {qr.score:.2f}")
                result.warnings.extend(qr.suggestions[:3])

    return result
