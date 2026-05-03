"""Nano-prompts — small, specialised prompt templates for each visual product mode.

Each template is a plain string with {placeholder} variables. Use
`prompt_builder.build()` to hydrate them with context.

Modes
-----
- markdown_polish   — Clean up raw analysis into magazine-ready markdown
- extract_sources   — Pull source citations from raw text
- summary_blurb     — Generate a one-paragraph executive summary
- infographic_label — Suggest a descriptive label for an infographic
- infographic_image — Infographic image generation prompt for OpenRouter
"""

MARKDOWN_POLISH = """You are an intelligence briefing editor. Rewrite the following raw analysis for a professional magazine-format publication.

Rules:
- Keep the BLUF (bottom line up front) structure where present
- Use clear, direct language — no hedging, no filler
- Preserve every factual claim, probability estimate, and source citation
- Break long paragraphs into digestible 3-5 sentence chunks
- Use ## headings for major sections, ### for subsections
- Wrap pull-quote-worthy sentences in > blockquote
- Use --- for section dividers between distinct topics
- Keep tables in pipe-syntax markdown
- Preserve any ```mermaid code blocks exactly as-is

Raw analysis to polish:
---
{raw_text}
---

Output the polished markdown only, no commentary."""

EXTRACT_SOURCES = """Extract all named sources, citations, and references from the text below.
Return them as a markdown unordered list, one source per line.
Include: author/title, publication, date (if available), URL (if available).
If the text contains no explicit sources, return "No explicit sources cited."

Text:
---
{raw_text}
---"""

SUMMARY_BLURB = """Write a one-paragraph executive summary (max 100 words) of the following analysis.
Use plain, direct language suitable for a magazine pull-quote or sidebar.

Analysis:
---
{raw_text}
---"""

INFOGRAPHIC_LABEL = """Given the following SVG infographic filename and a snippet of the analysis it belongs to, suggest a short (3-6 word) descriptive label for the infographic.

Filename: {filename}
Analysis context: {context}

Label:"""

MD_TABLE_TO_GRID = """Convert the following markdown table into a clean grid-style table suitable for PDF layout.
Preserve all data. Use minimal formatting.

{table}
"""

INFOGRAPHIC_IMAGE = """Create a {route} infographic for an intelligence briefing.

Layout structure:
- Top: title and key metric(s) / headline number(s)
- Middle: the core relationship or flow being depicted
- Bottom: key takeaways, callouts, or legend

Styling constraints:
- Flat vector illustration style
- Clean spacing with generous white space
- All labels must be readable at screen resolution
- No clutter, no decorative elements that don't carry information
- Use a professional colour palette: navy, slate, gold accent, white
- Do NOT output diagram code (Mermaid, Graphviz DOT, etc.)
- Do NOT output markdown tables or raw code blocks
- This is a rendered image — produce a clean visual graphic

Content to visualise:
---
{raw_text}
---

{extra_context}"""
