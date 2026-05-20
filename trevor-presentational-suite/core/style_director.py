"""TPS Style Director — enforce house brand across all generated assets.

Reads from brand.yaml and provides brand tokens to every generator.
Milestone 1: basic token injection. Milestone 2: full enforcement.
"""
from __future__ import annotations

from .config import get_config, BrandConfig


def get_brand() -> BrandConfig:
    """Get the current brand configuration."""
    return get_config().brand


def get_image_prompt_suffix() -> str:
    """Return brand guidance to append to image-gen prompts.

    Ensures all image-gen outputs share a coherent visual style.
    """
    brand = get_brand()
    return (
        f"Style: Professional intelligence report aesthetic. "
        f"Color palette: primary {brand.color_primary}, "
        f"accent {brand.color_accent}, dark background {brand.color_body}. "
        f"Clean, minimal, data-driven. No decorative elements. "
        f"Typography: {brand.font_heading} for headings."
    )


def get_kent_color(band: str) -> str:
    """Get the color for a Sherman Kent probability band."""
    brand = get_brand()
    return brand.kent_colors.get(band, "#666666")


def get_chart_colors() -> list[str]:
    """Get the chart color palette (FT-style)."""
    brand = get_brand()
    return list(brand.chart_palette.values())


def get_qc_watermark() -> str:
    """Get the QC watermark text."""
    brand = get_brand()
    return brand.qc_watermark


def inject_brand_css(html: str) -> str:
    """Inject brand CSS variables into an HTML document."""
    brand = get_brand()
    css_vars = f"""
    <style>
      :root {{
        --tps-primary: {brand.color_primary};
        --tps-accent: {brand.color_accent};
        --tps-body: {brand.color_body};
        --tps-surface: {brand.color_surface};
        --tps-font-body: '{brand.font_body}', sans-serif;
        --tps-font-heading: '{brand.font_heading}', sans-serif;
      }}
    </style>
    """
    if "<head>" in html:
        return html.replace("<head>", f"<head>{css_vars}", 1)
    return css_vars + html
