---
name: visual_production
description: Transform intelligence briefings into professionally designed magazine-quality PDFs and visual products. Rasterizes SVGs, renders Mermaid diagrams, and produces editorial A4 layouts via WeasyPrint.
---

# visual_production

Transforms structured intelligence analysis into magazine-quality visual products with:
- **Two-column editorial layout** (Georgia serif body, Helvetica headers)
- **Rasterized infographics** — SVGs → high-DPI PNG via CairoSVG
- **Rendered Mermaid diagrams** — flowchart simplifier → Graphviz DOT → PNG
- **Pull quotes, section dividers, gold-accent typography**
- **Classification banners, publication footers, page numbers**
- **Quality gate** — post-render validation (readability, structure, metadata)

## Package Structure

```
skills/visual_production/
├── SKILL.md                          # This file
├── scripts/
│   └── format_magazine.py            # CLI entry point
└── visual_production/                # Python package
    ├── __init__.py                   # Package init, exports
    ├── router.py                     # Entry point, dispatches by product type
    ├── pipeline.py                   # Markdown → HTML → PDF orchestration
    ├── schemas.py                    # Dataclasses (configs, specs, results, quality)
    ├── prompt_builder.py             # LLM prompt assembly for pre-processing
    ├── nano_prompts.py               # Tiny specialized prompt templates
    └── quality_gate.py               # Post-render validation checks
```

## Requirements

```bash
pip install weasyprint cairosvg
# Mermaid rendering via Graphviz:
sudo apt-get install graphviz   # provides the `dot` binary
```

## Usage

### CLI

```bash
python3 skills/visual_production/scripts/format_magazine.py \
  --input tasks/news_analysis.md \
  --title "TREVOR GLOBAL INTELLIGENCE BRIEFING" \
  --issue "03 May 2026" \
  --infographics exports/images/infographic-hormuz-chain.svg \
                 exports/images/infographic-us-germany.svg \
  --output exports/pdfs/magazine-briefing.pdf
```

### Programmatic (Python)

```python
from visual_production.router import produce

result = produce(
    markdown_path="tasks/news_analysis.md",
    product="magazine",
    title="TREVOR GLOBAL INTELLIGENCE BRIEFING",
    issue="03 May 2026",
    infographics=["exports/images/infographic-hormuz.svg"],
    output="exports/pdfs/magazine-briefing.pdf",
)
print(result.summary())
# ✅ magazine → magazine-briefing.pdf (4 pp, 320 KB)
```

## Pipeline Stages

1. **Mermaid extraction & rendering** — Graphviz DOT → PNG
2. **SVG rasterization** — CairoSVG at 2.5× scale (240 DPI equivalent)
3. **HTML assembly** — editorial CSS with column-span breaks for graphics
4. **PDF generation** — WeasyPrint with A4 @page rules
5. **Quality gate** — 8 checks: file existence, size, pages, classification, sections, readability, infographic references, title

## Design Spec

| Element | Spec |
|---|---|
| Page | A4 (210×297mm), 2cm margins |
| Body | 10pt Georgia, 1.6 line-height, justified, 2-column |
| H1 (masthead) | 28pt Helvetica bold, navy, gold underline, centered |
| H2 | 16pt Helvetica bold, navy, gold bottom border |
| H3 | 11pt Helvetica bold, slate |
| Pull quotes | 11pt Georgia italic, gold 3px left border, warm background |
| Infographics | Full-width, column-span, page-break-before |
| Classification | 8pt Helvetica bold, red, 3pt letter-spacing |

## Extending

Add a new product type:
1. Add entry to `ProductType` enum in `schemas.py`
2. Add a `build_PRODUCT()` pipeline function in `pipeline.py`
3. Add a dispatch case in `router.py` `produce()`
4. Add system context to `prompt_builder.py` `system_context_for_product()`
