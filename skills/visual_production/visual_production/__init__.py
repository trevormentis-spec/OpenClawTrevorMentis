"""visual_production — Transform intelligence briefings into professionally designed visual products.

Sub-packages and key exports:
    router          — CLI/API entry point, dispatches by product type
    pipeline        — Markdown → HTML → PDF orchestration + OpenRouter image gen
    prompt_builder  — System/user prompt assembly for LLM pre-processing
    nano_prompts    — Tiny, specialised prompt templates per output mode
    schemas         — Dataclasses for config, artefacts, plans, visuals
    quality_gate    — Post-render validation (readability, design, metadata, images)

NanoBanana image generation uses ``openclaw infer image generate`` via OpenRouter
(``google/gemini-3.1-flash-image-preview``), routed through the existing
OpenClaw capability layer — no raw HTTP, no hardcoded keys.

Typical usage:
    from visual_production.router import produce

    # Magazine PDF
    result = produce(
        markdown_path="tasks/briefing.md",
        product="magazine",
        title="TREVOR GLOBAL INTELLIGENCE BRIEFING",
        issue="03 May 2026",
        infographics=["exports/images/infographic.svg"],
        output="exports/pdfs/briefing.pdf",
    )

    # Infographic image via OpenRouter
    result = produce(
        markdown_path="tasks/briefing.md",
        product="infographic",
        nano_route="flow_chain",
    )
    for v in result.visuals:
        print(f"  {v.route}: {v.asset_kind} ({v.file_size_kb} KB)")
"""

__version__ = "1.1.0"
__all__ = [
    "router",
    "pipeline",
    "prompt_builder",
    "nano_prompts",
    "schemas",
    "quality_gate",
]
