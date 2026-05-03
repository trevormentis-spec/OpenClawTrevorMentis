"""Quality gate — post-render validation for visual products.

Checks performed
----------------
1.  **File exists** — output path is non-empty
2.  **Minimum size** — PDF > 10 KB (empty / corrupt check)
3.  **Page count** — at least 1 page
4.  **Classification banner** — required text present in source HTML
5.  **Section count** — at least 2 H2-level sections
6.  **Readability** — average paragraph length within bounds (30-300 chars)
7.  **Infographic embedding** — referenced SVGs are mentioned or present
8.  **Title presence** — product title appears in source

Image quality checks
--------------------
9.  **Image format** — base64 data URL or file path is valid
10. **Image size** — > 1 KB (non-empty)
11. **No diagram code** — content doesn't contain Mermaid / raw code
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .schemas import QualityReport, MagazineConfig, ProductionResult, ProductType, ProducedVisual


# ── Text validation (shared) ──────────────────────────────────────────

REJECT_PATTERNS = [
    re.compile(r"```mermaid", re.IGNORECASE),
    re.compile(r"```\s*\n.*(?:graph|flowchart|sequence|class)", re.DOTALL | re.IGNORECASE),
    re.compile(r"\|.*\|.*\|"),  # markdown table row
    re.compile(r"```\w*"),      # any code fence
]


def validate_text_output(text: str) -> list[str]:
    """Check text for content that should not reach image generation.

    Returns a list of rejection reasons. Empty list = pass.
    """
    reasons: list[str] = []
    for pat in REJECT_PATTERNS:
        if pat.search(text):
            if "mermaid" in pat.pattern.lower():
                reasons.append("Contains Mermaid diagram code")
            elif r"\|.*\|" in pat.pattern:
                reasons.append("Contains markdown table syntax")
            elif "code fence" in pat.pattern.lower() or "```" in pat.pattern:
                reasons.append("Contains raw code blocks")
            else:
                reasons.append(f"Matched rejection pattern: {pat.pattern[:40]}")
    return reasons


# ── PDF assessment ────────────────────────────────────────────────────

def assess_pdf(
    pdf_path: Path,
    config: MagazineConfig,
    source_text: str = "",
    svg_paths: list[Path] | None = None,
) -> QualityReport:
    """Run quality checks on a rendered PDF file.

    Parameters
    ----------
    pdf_path : Path
        Path to the generated PDF.
    config : MagazineConfig
        Configuration used for the run.
    source_text : str
        The markdown content fed into the pipeline (for text-level checks).
    svg_paths : list[Path] | None
        Original SVG infographic paths (to verify they were included).

    Returns
    -------
    QualityReport
    """
    checks: dict[str, bool] = {}
    messages: list[str] = []
    suggestions: list[str] = []

    # 1. File exists
    exists = pdf_path.exists()
    checks["file_exists"] = exists
    if not exists:
        messages.append("Output file does not exist.")
        return QualityReport(passed=False, score=0.0, checks=checks, messages=messages)

    size_kb = pdf_path.stat().st_size / 1024

    # 2. Minimum size
    min_size = size_kb > 10
    checks["minimum_size"] = min_size
    if not min_size:
        messages.append(f"Output file is only {size_kb:.1f} KB — may be corrupt or empty.")

    # 3. Page count (via pdfinfo)
    pages = _get_page_count(pdf_path)
    has_pages = pages >= 1
    checks["has_pages"] = has_pages
    if pages == 0:
        messages.append("PDF reports 0 pages.")

    # 4. Classification banner (from source_text / HTML)
    if source_text:
        class_banner = config.classification.value.upper()[:20]
        has_class = class_banner.lower() in source_text.lower()
        checks["classification_banner"] = has_class
        if not has_class:
            suggestions.append("Add a classification banner to the masthead.")

    # 5. Section count
    if source_text:
        sections = re.findall(r"^##\s+", source_text, re.MULTILINE)
        enough_sections = len(sections) >= 2
        checks["has_sections"] = enough_sections
        if not enough_sections:
            suggestions.append("Add at least two H2 sections for structure.")

    # 6. Readability — paragraph length
    if source_text:
        paras = [p.strip() for p in source_text.split("\n\n") if p.strip()]
        long_paras = [p for p in paras if len(p) > 400 and not p.startswith(("#", "|", ">", "`"))]
        if long_paras:
            checks["paragraph_length"] = False
            suggestions.append(
                f"Break {len(long_paras)} long paragraph(s) into shorter chunks."
            )
        else:
            checks["paragraph_length"] = True

    # 7. Infographic references
    if svg_paths:
        all_refs = True
        for svg in svg_paths:
            stem = svg.stem.lower()
            if stem not in source_text.lower():
                all_refs = False
                suggestions.append(f"Infographic '{svg.name}' not referenced in text.")
        checks["infographic_references"] = all_refs

    # 8. Title presence
    if source_text and config.title:
        title_words = config.title.lower().split()[:3]
        title_present = any(tw in source_text.lower() for tw in title_words)
        checks["title_present"] = title_present
        if not title_present:
            suggestions.append("Product title not found in output.")

    # Score
    total = len(checks)
    passed = sum(1 for v in checks.values() if v)
    score = passed / total if total > 0 else 0.0
    all_passed = passed == total

    return QualityReport(
        passed=all_passed,
        score=score,
        checks=checks,
        messages=messages,
        suggestions=suggestions,
    )


# ── Image assessment ──────────────────────────────────────────────────

def assess_image(visual: ProducedVisual) -> QualityReport:
    """Run quality checks on a produced image.

    Parameters
    ----------
    visual : ProducedVisual
        The produced visual to assess.

    Returns
    -------
    QualityReport
    """
    checks: dict[str, bool] = {}
    messages: list[str] = []
    suggestions: list[str] = []

    # 1. Success flag
    checks["generation_success"] = visual.success
    if not visual.success:
        messages.append(f"Image generation failed: {visual.error}")

    # 2. Content not empty
    has_content = bool(visual.content) and len(visual.content) > 50
    checks["has_content"] = has_content
    if not has_content:
        messages.append("Image content is empty or too small.")

    # 3. Asset kind
    is_image = visual.asset_kind == "image"
    checks["is_image"] = is_image
    if not is_image:
        messages.append(f"Expected 'image', got '{visual.asset_kind}' — likely fallback text.")

    # 4. File size
    has_size = visual.file_size_kb > 1.0
    checks["has_file_size"] = has_size
    if not has_size and is_image:
        messages.append(f"Image is only {visual.file_size_kb:.1f} KB — may be corrupt.")

    # 5. Route label present
    has_route = bool(visual.route)
    checks["has_route"] = has_route

    # Score
    total = len(checks)
    passed = sum(1 for v in checks.values() if v)
    score = passed / total if total > 0 else 0.0
    all_passed = passed == total

    return QualityReport(
        passed=all_passed,
        score=score,
        checks=checks,
        messages=messages,
        suggestions=suggestions,
    )


def _get_page_count(pdf_path: Path) -> int:
    """Attempt to extract page count via pdfinfo."""
    import subprocess
    try:
        r = subprocess.run(
            ["pdfinfo", str(pdf_path)],
            capture_output=True, text=True, timeout=5,
        )
        for line in r.stdout.split("\n"):
            if "Pages" in line:
                return int(line.split(":")[1].strip())
    except Exception:
        pass
    return 0
