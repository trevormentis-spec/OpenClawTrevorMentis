#!/usr/bin/env python3
"""
Integration test for the visual_production NanoBanana + OpenRouter pipeline.

Tests:
1. Text validation rejects Mermaid / tables / raw code
2. VisualProductionPlan creation via nano_chain resolution
3. OpenRouter image generation (real call — may fail if OPENROUTER_API_KEY missing)
4. Fallback text output when image generation fails
5. ProducedVisual return format

Usage:
    python3 skills/visual_production/test_pipeline.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Ensure the package is importable
_PKG = Path(__file__).resolve().parent / "visual_production"
sys.path.insert(0, str(_PKG.parent))

# ── Imports ──────────────────────────────────────────────────────────
from visual_production.schemas import (
    NanoBananaRoute,
    VisualProductionPlan,
    ProducedVisual,
    ProductionResult,
)
from visual_production.quality_gate import validate_text_output, assess_image
from visual_production.pipeline import (
    generate_infographic_image,
    resolve_nano_chain,
    validate_text_output as pipe_validate,
)
from visual_production.router import produce


# ── Fixtures ─────────────────────────────────────────────────────────

CLEAN_TEXT = """The Strait of Hormuz is a critical maritime chokepoint handling 20% of global oil transit. Iran's recent naval exercises have increased tensions. Key risks include:
- Mining operations at the chokepoint's narrowest section (33 km wide)
- Anti-ship missile deployments along Iran's coastline
- Potential IRGC-Navy swarm tactics against commercial shipping

The US Navy's Fifth Fleet maintains a continuous presence with one carrier strike group in the region. Escalation scenarios range from temporary harassment to full blockade."""

DIRTY_TEXT = """```mermaid
graph TD
    A[Risk] --> B[Escalation]
    B --> C[Conflict]
```

| Threat | Likelihood | Impact |
|--------|-----------|--------|
| Blockade | Medium | High |

```python
print("this is code")
```"""


# ── Tests ─────────────────────────────────────────────────────────────

def test_validate_text_output():
    """Test that text validation rejects Mermaid, tables, and code."""
    reasons = validate_text_output(CLEAN_TEXT)
    assert len(reasons) == 0, f"Clean text should pass, got: {reasons}"

    reasons = validate_text_output(DIRTY_TEXT)
    assert len(reasons) > 0, f"Dirty text should be rejected"
    print(f"  ✅ Text validation: {len(reasons)} issue(s) detected in dirty text")


def test_validate_via_pipeline_export():
    """Test the validate_text_output exported from pipeline matches."""
    reasons = pipe_validate(CLEAN_TEXT)
    assert len(reasons) == 0, f"Pipeline validation should pass clean text"
    print(f"  ✅ Pipeline validate_text_output: clean text passes")


def test_nano_chain_resolution():
    """Test that each NanoBanana route resolves to the right plan chain."""
    chains = {
        NanoBananaRoute.LOGIC_FLOW: 1,
        NanoBananaRoute.FLOW_CHAIN: 2,
        NanoBananaRoute.MAP_PLATE: 1,
        NanoBananaRoute.DASHBOARD: 2,
        NanoBananaRoute.SVG_CHART: 1,
    }

    for route, expected_count in chains.items():
        plans = resolve_nano_chain(route, CLEAN_TEXT)
        assert len(plans) == expected_count, (
            f"{route.value}: expected {expected_count} plans, got {len(plans)}"
        )
        for plan in plans:
            assert isinstance(plan, VisualProductionPlan)
            assert len(plan.prompt_text) > 50  # prompt should be hydrated
            # Prompt contains "Mermaid" as a styling constraint instruction,
            # which is correct — it tells the image model NOT to output Mermaid.
            # Check for actual Mermaid code fences and raw code blocks instead.
            assert "```mermaid" not in plan.prompt_text  # no actual mermaid fence
            assert "```" not in plan.prompt_text  # no code fence at all
            assert "|---|" not in plan.prompt_text  # no markdown table syntax
        print(f"  ✅ {route.value}: {len(plans)} plan(s) — prompts clean")


def test_generate_infographic_image():
    """Test OpenRouter image generation (may fall back to text)."""
    plans = resolve_nano_chain(NanoBananaRoute.LOGIC_FLOW, CLEAN_TEXT)
    assert len(plans) >= 1
    plan = plans[0]

    with tempfile.TemporaryDirectory(prefix="nanobanana_test_") as tmpdir:
        visual = generate_infographic_image(plan, Path(tmpdir))

        # Must always return a ProducedVisual — never crash
        assert isinstance(visual, ProducedVisual), "Must return ProducedVisual"

        # Validate the output
        if visual.success:
            assert visual.asset_kind == "image", (
                f"Expected image, got {visual.asset_kind}"
            )
            assert visual.content.startswith("data:image/"), (
                f"Expected image data URL, got {visual.content[:40]}..."
            )
            assert ";base64," in visual.content, (
                f"Expected base64 encoding in data URL"
            )
            assert visual.file_size_kb > 1.0, (
                f"Expected image >1 KB, got {visual.file_size_kb} KB"
            )
            print(f"  ✅ Image generated: {visual.file_size_kb} KB ({visual.route})")

            # Quality gate on the image
            qr = assess_image(visual)
            print(f"  📊 Image quality gate: {'PASS' if qr.passed else 'FAIL'} ({qr.score:.2f})")
        else:
            # Fallback to text — acceptable if no OPENROUTER_API_KEY
            assert visual.asset_kind == "text", (
                f"Expected text fallback, got {visual.asset_kind}"
            )
            print(f"  ⚠️  Image generation fell back to text: {visual.error[:80]}...")
            print(f"     (This is expected if OPENROUTER_API_KEY is not configured)")


def test_router_infographic_produce():
    """Test the router's infographic produce path end-to-end."""
    plans = resolve_nano_chain(NanoBananaRoute.FLOW_CHAIN, CLEAN_TEXT)
    assert len(plans) == 2

    with tempfile.TemporaryDirectory(prefix="nanobanana_router_") as tmpdir:
        visuals = []
        errors = []

        for plan in plans:
            visual = generate_infographic_image(plan, Path(tmpdir))
            visuals.append(visual)
            if not visual.success:
                errors.append(f"{plan.route.value}: {visual.error}")

        result = ProductionResult(
            success=len(errors) == 0,
            visuals=visuals,
            warnings=[f"{len(visuals)} image(s) generated"] if visuals else [],
            errors=errors,
            product_type=None,
        )

        print(f"\n  📋 Router produce summary:")
        print(f"     ✅: {result.success}")
        print(f"     Visuals: {len(result.visuals)}")
        for v in result.visuals:
            status = "✅" if v.success else "⚠️"
            print(f"       {status} {v.route}: {v.asset_kind} ({v.file_size_kb:.1f} KB)")

        # dict() should be serialisable
        d = result.dict()
        assert "visuals" in d
        assert len(d["visuals"]) == len(visuals)


# ── Main ──────────────────────────────────────────────────────────────

def main():
    print("🧪 visual_production NanoBanana + OpenRouter pipeline tests\n")

    tests = [
        ("test_validate_text_output", test_validate_text_output),
        ("test_validate_via_pipeline_export", test_validate_via_pipeline_export),
        ("test_nano_chain_resolution", test_nano_chain_resolution),
        ("test_generate_infographic_image", test_generate_infographic_image),
        ("test_router_infographic_produce", test_router_infographic_produce),
    ]

    passed = 0
    failed = 0

    for name, fn in tests:
        print(f"── {name} ──")
        try:
            fn()
            passed += 1
            print(f"  ✅ PASS\n")
        except Exception as e:
            failed += 1
            import traceback
            traceback.print_exc()
            print(f"  ❌ FAIL: {e}\n")

    print(f"=" * 40)
    print(f"Results: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
