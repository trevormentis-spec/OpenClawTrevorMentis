"""Pipeline — core markdown → HTML → PDF orchestration + OpenRouter image generation.

This module handles:

1.  SVG rasterisation (CairoSVG at configurable DPI)
2.  Mermaid diagram rendering (Graphviz DOT → PNG)
3.  OpenRouter image generation (``openclaw infer image generate``)
4.  Markdown-to-HTML conversion with editorial CSS
5.  WeasyPrint PDF generation with per-product @page rules
6.  Text validation (reject Mermaid, tables, raw code before image gen)
"""
from __future__ import annotations

import base64
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import cairosvg

from .schemas import (
    MagazineConfig,
    ProductionResult,
    InfographicSpec,
    MermaidBlock,
    VisualProductionPlan,
    ProducedVisual,
    NanoBananaRoute,
)

WORKSPACE = Path("/home/ubuntu/.openclaw/workspace")

# ── OpenRouter model for image generation ─────────────────────────────
DEFAULT_IMAGE_MODEL = "google/gemini-3.1-flash-image-preview"
FALLBACK_IMAGE_MODEL = "openai/gpt-5.4-image-2"

# Patterns that should NOT be sent to image generation
REJECT_PATTERNS = [
    re.compile(r"```mermaid", re.IGNORECASE),
    re.compile(r"```\s*\n.*(?:graph|flowchart|sequence|class)", re.DOTALL | re.IGNORECASE),
    re.compile(r"\|.*\|.*\|"),  # markdown table row
    re.compile(r"```\w*"),      # any code fence
]


# ═══════════════════════════════════════════════════════════════════════
# Text validation — run BEFORE image generation
# ═══════════════════════════════════════════════════════════════════════

def validate_text_output(text: str) -> list[str]:
    """Check text for content that should not reach image generation.

    Returns a list of rejection reasons. Empty list = pass.
    """
    reasons: list[str] = []
    for pat in REJECT_PATTERNS:
        if pat.search(text):
            # Identify which pattern matched
            if "mermaid" in pat.pattern.lower():
                reasons.append("Contains Mermaid diagram code")
            elif r"\|.*\|" in pat.pattern:
                reasons.append("Contains markdown table syntax")
            elif "code fence" in pat.pattern.lower() or "```" in pat.pattern:
                reasons.append("Contains raw code blocks")
            else:
                reasons.append(f"Matched rejection pattern: {pat.pattern[:40]}")
    return reasons


# ═══════════════════════════════════════════════════════════════════════
# SVG rasterisation
# ═══════════════════════════════════════════════════════════════════════

def rasterize_svg(svg_path: Path, scale: float = 2.5) -> tuple[bytes, int, int]:
    """Convert an SVG file to PNG bytes at the given scale.

    Returns
    -------
    tuple[bytes, int, int]
        (png_bytes, width_px, height_px)
    """
    png_data = cairosvg.svg2png(url=str(svg_path), scale=scale)
    w = int(900 * scale)
    h = int(1050 * scale)
    return png_data, w, h


# ═══════════════════════════════════════════════════════════════════════
# Mermaid → PNG via Graphviz DOT
# ═══════════════════════════════════════════════════════════════════════

def _graphviz_available() -> bool:
    """Check if the ``dot`` binary is on PATH."""
    return shutil.which("dot") is not None


def _render_via_graphviz(mermaid_code: str, out_path: Path) -> Optional[Path]:
    """Parse simplified Mermaid flow-chart syntax and render via Graphviz."""
    try:
        lines = [l.strip() for l in mermaid_code.split("\n") if l.strip()]
        nodes: dict[str, str] = {}
        edges: list[tuple[str, str]] = []

        for line in lines:
            if line.startswith("graph") or line.startswith("%%") or line.startswith("flowchart"):
                continue
            if "-->" in line:
                parts = line.split("-->")
                for i in range(len(parts) - 1):
                    src = parts[i].strip()
                    dst = parts[i + 1].strip()

                    def _parse_node(n: str):
                        n = n.strip()
                        if '"' in n:
                            nid = re.sub(r'[^a-zA-Z0-9_]', "", n.split('"')[0])
                            label = n.split('"')[1]
                            return nid or label, label
                        return n, n

                    src_id, src_label = _parse_node(src)
                    dst_id, dst_label = _parse_node(dst)
                    if src_id:
                        nodes[src_id] = src_label
                    if dst_id:
                        nodes[dst_id] = dst_label
                    edges.append((src_id, dst_id))

        dot = (
            "digraph G {\n"
            "    rankdir=TB;\n"
            '    bgcolor="#0f1923";\n'
            "    node [shape=box, style=\"rounded,filled\","
            ' fillcolor="#1a3366", fontcolor="white",'
            ' fontname="Helvetica", fontsize=11,'
            ' penwidth=1.5, color="#2a4a6b"];\n'
            '    edge [color="#4d9aff", penwidth=2, arrowsize=1.2];\n'
        )
        for nid, nlabel in nodes.items():
            safe = nlabel.replace('"', '\\"')
            dot += f'    {nid} [label="{safe}"];\n'
        for s, d in edges:
            dot += f"    {s} -> {d};\n"
        dot += "}\n"

        result = subprocess.run(
            ["dot", "-Tpng", "-Gdpi=200", f"-o{out_path}"],
            input=dot.encode(),
            capture_output=True,
            timeout=15,
        )
        if out_path.exists() and out_path.stat().st_size > 2000:
            return out_path
        raise ValueError(f"Graphviz output too small: {out_path.stat().st_size} bytes")
    except Exception as exc:
        print(f"    ⚠️  Mermaid/Graphviz: {exc}", file=sys.stderr)
        return None


def render_mermaid_blocks(blocks: list[MermaidBlock], temp_dir: Path) -> list[MermaidBlock]:
    """Render a list of MermaidBlock objects, populating ``rendered_path``."""
    if not _graphviz_available():
        print("    ⚠️  Graphviz 'dot' not found — skipping Mermaid rendering.", file=sys.stderr)
        return blocks

    temp_dir.mkdir(parents=True, exist_ok=True)
    for block in blocks:
        out = temp_dir / f"mermaid_{block.index}.png"
        rendered = _render_via_graphviz(block.code, out)
        if rendered:
            block.rendered_path = rendered
            print(f"    🔷 Mermaid diagram {block.index} rendered ({rendered.stat().st_size // 1024} KB)")
    return blocks


# ═══════════════════════════════════════════════════════════════════════
# OpenRouter image generation via openclaw CLI
# ═══════════════════════════════════════════════════════════════════════

def generate_infographic_image(
    plan: VisualProductionPlan,
    output_dir: Path,
) -> ProducedVisual:
    """Generate an infographic image via the OpenRouter API.

    Calls the OpenRouter chat completions endpoint with an image-generation
    model (``google/gemini-3.1-flash-image-preview``). Uses the
    ``OPENROUTER_API_KEY`` env var — no hardcoded keys, no new client.
    The request format mirrors the built-in OpenClaw OpenRouter provider.

    Falls back to returning the prompt text on failure (does NOT crash).

    Parameters
    ----------
    plan : VisualProductionPlan
        The production plan (route, prompt, model, etc.).
    output_dir : Path
        Directory to write the output image.

    Returns
    -------
    ProducedVisual
    """
    import json
    import os
    from urllib.request import Request, urlopen
    from urllib.error import URLError

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{plan.output_stem}.png"

    # Validate text before sending to image generation
    reject_reasons = validate_text_output(plan.prompt_text)
    if reject_reasons:
        msg = "; ".join(reject_reasons)
        print(f"    ⚠️  Text validation failed: {msg}", file=sys.stderr)
        print(f"    → Falling back: returning prompt text instead of image.", file=sys.stderr)
        return ProducedVisual(
            asset_kind="text",
            content=f"[Text validation rejected] {msg}\n\nPrompt:\n{plan.prompt_text}",
            route=plan.route.value,
            success=False,
            error=msg,
        )

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print(f"    ⚠️  OPENROUTER_API_KEY not set — falling back to prompt text.", file=sys.stderr)
        return ProducedVisual(
            asset_kind="text",
            content=f"[Missing] OPENROUTER_API_KEY\n\nPrompt:\n{plan.prompt_text}",
            route=plan.route.value,
            success=False,
            error="OPENROUTER_API_KEY not configured",
        )

    # Build request body matching the OpenClaw OpenRouter provider format
    body = {
        "model": plan.model,
        "messages": [{"role": "user", "content": plan.prompt_text}],
    }
    if plan.model.startswith("google/gemini-"):
        body["aspect_ratio"] = plan.aspect_ratio

    url = "https://openrouter.ai/api/v1/chat/completions"
    request = Request(
        url,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://openclaw.ai",
            "X-OpenRouter-Title": "Trevor Visual Production",
        },
    )

    print(f"    🖼️  Generating infographic (model={plan.model}, route={plan.route.value})…")

    try:
        with urlopen(request, timeout=90) as resp:
            response_data = json.loads(resp.read().decode())
    except Exception as exc:
        print(f"    ⚠️  OpenRouter API call failed: {exc}", file=sys.stderr)
        print(f"    → Falling back: returning prompt text.", file=sys.stderr)
        return ProducedVisual(
            asset_kind="text",
            content=f"[OpenRouter failure] {exc}\n\nPrompt:\n{plan.prompt_text}",
            route=plan.route.value,
            success=False,
            error=str(exc),
        )

    # Extract image from response — check message.images first, then content
    image_data_url: str | None = None

    for choice in response_data.get("choices", []):
        msg = choice.get("message", {})
        # OpenRouter returns images in message.images
        images = msg.get("images", [])
        for entry in images:
            url_str = entry.get("image_url", {}).get("url", "") or entry.get("imageUrl", {}).get("url", "")
            if url_str:
                image_data_url = url_str
                break
        if image_data_url:
            break

        # Fallback: check content for base64 data URLs
        content = msg.get("content", "")
        if isinstance(content, str) and "data:image" in content:
            import re as _re
            match = _re.search(r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+", content)
            if match:
                image_data_url = match.group(0)
                break

    if not image_data_url:
        err_msg = "No image data in OpenRouter response"
        finish = response_data.get("choices", [{}])[0].get("finish_reason", "")
        if finish and finish != "stop":
            err_msg += f" (finish_reason: {finish})"
        print(f"    ⚠️  {err_msg}", file=sys.stderr)
        print(f"    → Falling back: returning prompt text.", file=sys.stderr)
        return ProducedVisual(
            asset_kind="text",
            content=f"[{err_msg}]\n\nPrompt:\n{plan.prompt_text}",
            route=plan.route.value,
            success=False,
            error=err_msg,
        )

    # Decode base64 data URL and write to file
    try:
        _, b64_data = image_data_url.split(",", 1)
        image_bytes = base64.b64decode(b64_data)
        out_path.write_bytes(image_bytes)
        size_kb = round(out_path.stat().st_size / 1024, 1)
        print(f"    ✅ Image generated: {out_path} ({size_kb} KB)")
        return ProducedVisual(
            asset_kind="image",
            content=image_data_url,
            route=plan.route.value,
            file_size_kb=size_kb,
            success=True,
        )
    except Exception as exc:
        print(f"    ⚠️  Failed to decode image: {exc}", file=sys.stderr)
        return ProducedVisual(
            asset_kind="text",
            content=f"[Decode failure] {exc}",
            route=plan.route.value,
            success=False,
            error=str(exc),
        )


# ═══════════════════════════════════════════════════════════════════════
# NanoBanana flow chain — build a sequence of plans from a route
# ═══════════════════════════════════════════════════════════════════════

def resolve_nano_chain(
    route: NanoBananaRoute,
    raw_text: str,
) -> list[VisualProductionPlan]:
    """Resolve a NanoBanana route into one or more production plans.

    Route → plan chain:
        logic_flow  → nano_banana flow_chain
        flow_chain  → nano_banana flow_chain + map_plate
        map_plate   → nano_banana map_plate
        dashboard   → nano_banana dashboard + svg_chart
        svg_chart   → svg chart
    """
    from .prompt_builder import build_infographic_prompt

    if route == NanoBananaRoute.LOGIC_FLOW:
        prompt = build_infographic_prompt(raw_text, route, "Show the logical flow of events or dependencies.")
        return [VisualProductionPlan(
            route=NanoBananaRoute.FLOW_CHAIN,
            prompt_text=prompt,
            output_stem="flow-chain",
        )]

    elif route == NanoBananaRoute.FLOW_CHAIN:
        prompt_a = build_infographic_prompt(raw_text, route, "Show the chain of events as a sequential flow diagram.")
        prompt_b = build_infographic_prompt(raw_text, NanoBananaRoute.MAP_PLATE, "Show the geographic relationships and key locations.")
        return [
            VisualProductionPlan(
                route=NanoBananaRoute.FLOW_CHAIN, prompt_text=prompt_a,
                output_stem="flow-chain",
            ),
            VisualProductionPlan(
                route=NanoBananaRoute.MAP_PLATE, prompt_text=prompt_b,
                output_stem="map-plate",
            ),
        ]

    elif route == NanoBananaRoute.MAP_PLATE:
        prompt = build_infographic_prompt(raw_text, route, "Focus on geographic relationships, chokepoints, and spatial data.")
        return [VisualProductionPlan(
            route=NanoBananaRoute.MAP_PLATE, prompt_text=prompt,
            output_stem="map-plate",
        )]

    elif route == NanoBananaRoute.DASHBOARD:
        prompt_a = build_infographic_prompt(raw_text, route, "Create a dashboard-style layout with KPI callouts.")
        prompt_b = build_infographic_prompt(raw_text, NanoBananaRoute.SVG_CHART, "Show the data as a clean chart or graph.")
        return [
            VisualProductionPlan(
                route=NanoBananaRoute.DASHBOARD, prompt_text=prompt_a,
                output_stem="dashboard",
            ),
            VisualProductionPlan(
                route=NanoBananaRoute.SVG_CHART, prompt_text=prompt_b,
                output_stem="svg-chart",
            ),
        ]

    elif route == NanoBananaRoute.SVG_CHART:
        prompt = build_infographic_prompt(raw_text, route, "Create a clean analytical chart with labelled axes and annotations.")
        return [VisualProductionPlan(
            route=NanoBananaRoute.SVG_CHART, prompt_text=prompt,
            output_stem="svg-chart",
        )]

    else:
        # Default: treat as logic_flow
        prompt = build_infographic_prompt(raw_text, NanoBananaRoute.LOGIC_FLOW, "")
        return [VisualProductionPlan(
            route=NanoBananaRoute.LOGIC_FLOW, prompt_text=prompt,
            output_stem="infographic",
        )]


# ═══════════════════════════════════════════════════════════════════════
# HTML assembly
# ═══════════════════════════════════════════════════════════════════════

def _img_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


def build_html(
    analysis_text: str,
    config: MagazineConfig,
    svg_infographics: list[InfographicSpec],
    mermaid_blocks: list[MermaidBlock],
) -> str:
    """Assemble a full WeasyPrint-compatible HTML document.

    Parameters
    ----------
    analysis_text : str
        Raw markdown content.
    config : MagazineConfig
        Layout configuration.
    svg_infographics : list[InfographicSpec]
        Rasterised infographic specs.
    mermaid_blocks : list[MermaidBlock]
        Rendered mermaid blocks.

    Returns
    -------
    str
        Complete HTML string ready for WeasyPrint.
    """
    # ── Rasterise SVGs ──────────────────────────────────────────────
    infographic_pages: list[str] = []
    for spec in svg_infographics:
        if spec.path.exists():
            try:
                png_data, w, h = rasterize_svg(spec.path, scale=config.dpi_scale)
                b64 = base64.b64encode(png_data).decode()
                infographic_pages.append(f"""
<div class="infographic-page">
  <div class="infographic-label">{spec.label}</div>
  <img src="data:image/png;base64,{b64}" style="width:100%;max-width:{w}px;">
</div>""")
                print(f"  📊 Rasterised {spec.path.name} → {len(png_data) // 1024} KB")
            except Exception as exc:
                print(f"  ⚠️  SVG failed: {exc}")

    # ── Parse markdown → HTML body ──────────────────────────────────
    lines = analysis_text.split("\n")
    body_parts: list[str] = []
    in_code = False
    mermaid_idx = 0

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```mermaid"):
            in_code = False
            continue
        if stripped == "```" and "mermaid" not in line:
            if in_code:
                body_parts.append("</pre></div>")
                in_code = False
            else:
                body_parts.append('<div class="code-block"><pre>')
                in_code = True
            continue

        if in_code:
            body_parts.append(line)
            continue

        if mermaid_idx < len(mermaid_blocks) and mermaid_blocks[mermaid_idx].rendered_path:
            b64 = _img_b64(mermaid_blocks[mermaid_idx].rendered_path)
            mermaid_idx += 1
            body_parts.append(
                f'<img src="data:image/png;base64,{b64}" class="mermaid-img" alt="Diagram">'
            )
            continue

        if stripped == "---":
            body_parts.append('<hr class="section-divider">')
        elif stripped.startswith("## ") and not stripped.startswith("### "):
            body_parts.append(f'<h2>{stripped[3:]}</h2>')
        elif stripped.startswith("### "):
            body_parts.append(f'<h3>{stripped[4:]}</h3>')
        elif stripped.startswith("> "):
            body_parts.append(f'<blockquote class="pull-quote"><p>{stripped[2:]}</p></blockquote>')
        elif stripped == "":
            body_parts.append('<p class="spacer"></p>')
        else:
            body_parts.append(f"<p>{line}</p>")

    body_html = "\n".join(body_parts)
    infographic_block = "\n".join(infographic_pages) if infographic_pages else ""

    # ── Editorial CSS ───────────────────────────────────────────────
    accent = config.accent_color
    gold = config.gold_color
    today = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%d")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
  @page {{
    size: {config.page_size};
    margin: {config.margin};
    @top-center {{
      content: "{config.title}";
      font: 8pt Helvetica, Arial, sans-serif;
      color: #666;
      text-transform: uppercase;
      letter-spacing: 2px;
    }}
    @bottom-center {{
      content: counter(page);
      font: 8pt Helvetica, Arial, sans-serif;
      color: #999;
    }}
  }}
  @page :first {{ @top-center {{ content: none; }} }}

  * {{ box-sizing: border-box; }}

  body {{
    font-family: {config.body_font};
    font-size: {config.body_size};
    line-height: 1.6;
    color: #1a1a1a;
  }}

  .masthead {{
    text-align: center;
    padding: 2cm 0 1cm 0;
    border-bottom: 3px solid {accent};
    margin-bottom: 0.8cm;
  }}
  .masthead h1 {{
    font: 700 28pt {config.headline_font};
    color: {accent};
    letter-spacing: 4px;
    text-transform: uppercase;
    margin: 0 0 6pt 0;
  }}
  .masthead .gold-line {{
    width: 60mm;
    height: 2px;
    background: {gold};
    margin: 8pt auto;
  }}
  .masthead .issue {{
    font: 400 10pt Georgia, serif;
    color: #666;
    font-style: italic;
  }}
  .masthead .classification {{
    font: 700 8pt {config.headline_font};
    color: #c0392b;
    text-transform: uppercase;
    letter-spacing: 3px;
    margin-top: 10pt;
  }}

  .text-content {{
    column-count: {config.column_count};
    column-gap: 22pt;
    column-rule: 0.5px solid #ddd;
  }}

  h2 {{
    font: 700 15pt {config.headline_font};
    color: {accent};
    margin: 16pt 0 6pt 0;
    padding-bottom: 3pt;
    border-bottom: 1.5px solid {gold};
    break-after: avoid;
  }}
  h2:first-of-type {{ margin-top: 0; }}

  h3 {{
    font: 700 11pt {config.headline_font};
    color: #34495e;
    margin: 10pt 0 4pt 0;
    break-after: avoid;
  }}

  p {{ margin: 0 0 5pt 0; text-align: justify; orphans: 2; widows: 2; }}
  p.spacer {{ height: 5pt; margin: 0; }}

  .pull-quote {{
    margin: 10pt 0;
    padding: 5pt 0 5pt 10pt;
    border-left: 3px solid {gold};
    font: italic 11pt/1.5 Georgia, serif;
    color: #555;
    background: #faf8f4;
  }}
  .pull-quote p {{ margin: 0; }}

  .section-divider {{
    border: none;
    border-top: 1px solid #ddd;
    margin: 16pt 0;
  }}

  .mermaid-img {{
    display: block;
    max-width: 100%;
    margin: 10pt auto;
    border: 0.5px solid #ddd;
    border-radius: 3px;
    column-span: all;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 6pt 0;
    font-size: 8.5pt;
    column-span: all;
  }}
  th {{
    background: {accent};
    color: white;
    font: 700 8pt {config.headline_font};
    padding: 4pt 5pt;
    text-align: left;
    text-transform: uppercase;
    letter-spacing: 1px;
  }}
  td {{
    padding: 3pt 5pt;
    border-bottom: 0.5px solid #ddd;
  }}
  tr:nth-child(even) td {{ background: #fafafa; }}

  .code-block {{
    background: #f5f6fa;
    border: 1px solid #dcdde1;
    padding: 6pt;
    margin: 6pt 0;
    font: 8pt monospace;
    white-space: pre-wrap;
  }}

  ul, ol {{ margin: 3pt 0 5pt 10pt; padding-left: 10pt; }}
  li {{ margin-bottom: 2pt; }}

  .infographic-page {{
    page-break-before: always;
    page-break-after: always;
    text-align: center;
    padding: 0.5cm 0;
  }}
  .infographic-page img {{
    display: block;
    max-width: 160mm;
    height: auto;
    margin: 0 auto;
  }}
  .infographic-label {{
    font: 700 10pt {config.headline_font};
    color: {accent};
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 6pt;
    text-align: center;
  }}
</style>
</head>
<body>

<div class="masthead">
  <div class="classification">{config.classification.value}</div>
  <h1>{config.title}</h1>
  <div class="gold-line"></div>
  <div class="issue">Issue: {config.issue} · Published {today} UTC</div>
</div>

<div class="text-content">
{body_html}
</div>

{infographic_block}

</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════════
# Main magazine pipeline entry point
# ═══════════════════════════════════════════════════════════════════════

def build_magazine(
    markdown_path: Path,
    config: MagazineConfig,
    svg_infographics: list[InfographicSpec] | None = None,
    **kwargs,
) -> ProductionResult:
    """Run the full magazine production pipeline.

    Parameters
    ----------
    markdown_path : Path
        Input markdown file.
    config : MagazineConfig
        Magazine layout configuration.
    svg_infographics : list[InfographicSpec] | None
        Infographics to embed.
    **kwargs
        Ignored (compatibility with router).

    Returns
    -------
    ProductionResult
    """
    from weasyprint import HTML

    warnings: list[str] = []
    errors: list[str] = []
    svg_infographics = svg_infographics or []

    # Read input
    try:
        analysis = markdown_path.read_text(encoding="utf-8")
    except Exception as exc:
        return ProductionResult(
            success=False,
            errors=[f"Cannot read input: {exc}"],
        )

    # Ensure temp dir
    temp = config.temp_dir
    temp.mkdir(parents=True, exist_ok=True)

    # ── Extract and render Mermaid blocks ──
    mermaid_blocks: list[MermaidBlock] = []
    lines = analysis.split("\n")
    in_mermaid = False
    code_lines: list[str] = []
    block_idx = 0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```mermaid"):
            in_mermaid = True
            code_lines = []
            continue
        if in_mermaid and stripped == "```":
            in_mermaid = False
            block = MermaidBlock(code="\n".join(code_lines), index=block_idx)
            mermaid_blocks.append(block)
            block_idx += 1
            continue
        if in_mermaid:
            code_lines.append(line)
            continue

    if mermaid_blocks:
        print(f"  🔷 Rendering {len(mermaid_blocks)} Mermaid diagram(s)…")
        mermaid_blocks = render_mermaid_blocks(mermaid_blocks, temp)
        # Fallback check
        rendered_count = sum(1 for b in mermaid_blocks if b.rendered_path)
        if rendered_count < len(mermaid_blocks):
            warnings.append(f"{len(mermaid_blocks) - rendered_count} Mermaid diagram(s) failed to render.")

    # ── Build HTML ──
    print(f"  📄 Assembling HTML (column-count: {config.column_count})…")
    html = build_html(analysis, config, svg_infographics, mermaid_blocks)

    # ── Render PDF ──
    out = config.output_path
    out.parent.mkdir(parents=True, exist_ok=True)
    print(f"  🖨️  Rendering PDF → {out}…")
    try:
        HTML(string=html).write_pdf(str(out))
    except Exception as exc:
        errors.append(f"WeasyPrint failed: {exc}")
        return ProductionResult(success=False, errors=errors, warnings=warnings)

    size_kb = out.stat().st_size / 1024
    pages = 0
    try:
        r = subprocess.run(
            ["pdfinfo", str(out)], capture_output=True, text=True, timeout=5
        )
        for line in r.stdout.split("\n"):
            if "Pages" in line:
                pages = int(line.split(":")[1].strip())
    except Exception:
        pass

    print(f"  ✅ PDF ready: {out} ({size_kb:.0f} KB, {pages} pages)")

    # Cleanup
    if temp.exists():
        shutil.rmtree(temp)

    return ProductionResult(
        success=True,
        output_path=out,
        page_count=pages,
        file_size_kb=round(size_kb, 1),
        warnings=warnings,
        errors=errors,
        product_type=None,  # set by router
    )
