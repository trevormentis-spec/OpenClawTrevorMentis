#!/usr/bin/env python3
"""Escalation Guard — pre, mid, and post-generation guards.

(1) Pre-generation: estimate tokens, escalate if model can't handle output.
(2) Mid-generation: detect truncation (output hit max_tokens), retry with Opus.
(3) Post-generation: validate word count meets target within tolerance.

Usage:
    from analyst.escalation_guard import pre_generation_check, post_generation_check

    # Pre-generation
    routing_result = pre_generation_check({"target_words": [4000, 6000]})
    if routing_result["escalated"]:
        print(f"Escalated from {routing_result['from_model']} to {routing_result['to_model']}")

    # Mid-generation
    if detect_truncation(output, max_tokens=8192):
        escalated = escalate_mid_generation(prompt, target_model="opus")

    # Post-generation
    validation = post_generation_check({
        "target_words": [4000, 6000],
        "actual_words": 5847,
        "model_used": "opus",
        "expected_model": "opus"
    })
"""

from __future__ import annotations

import re
from typing import Any

TOKENS_PER_WORD = 1.5
WORD_COUNT_TOLERANCE = 0.10  # 10% tolerance
MAX_TOKENS_DEFAULT = 8192


def estimate_tokens(word_count: int | list[int]) -> int:
    """Estimate output tokens from target word count."""
    if isinstance(word_count, list):
        return int(max(word_count) * TOKENS_PER_WORD)
    return int(word_count * TOKENS_PER_WORD)


def pre_generation_check(task: dict[str, Any]) -> dict[str, Any]:
    """Pre-generation: check if target model can handle output capacity.

    Returns routing decision with escalation info.
    """
    target_words = task.get("target_words", 0)
    if isinstance(target_words, list):
        target_max = max(target_words)
    else:
        target_max = target_words

    est_tokens = estimate_tokens(target_max)
    model_max = task.get("model_max_tokens", MAX_TOKENS_DEFAULT)
    model_name = task.get("proposed_model", "unknown")

    escalated = False
    from_model = model_name
    to_model = model_name

    if est_tokens > model_max * 0.9:
        escalated = True
        to_model = "anthropic/claude-opus-4.7"
        to_model_label = "Opus 4.7"

    return {
        "escalated": escalated,
        "from_model": from_model,
        "to_model": to_model,
        "estimated_tokens": est_tokens,
        "model_max_tokens": model_max,
        "utilization_pct": round(est_tokens / model_max * 100, 1),
    }


def detect_truncation(output: str, max_tokens: int = MAX_TOKENS_DEFAULT) -> bool:
    """Mid-generation: detect if output was truncated.

    Signals of truncation:
    - Output ends mid-sentence (no period/question mark/exclamation)
    - Output is suspiciously short vs expected
    - Output contains partial markdown structures
    """
    if not output or len(output) < 100:
        return True

    last_char = output.strip()[-1] if output.strip() else ""
    if last_char not in (".", "!", "?", '"', "'", ")", "]", "}", "`") and len(output) > 200:
        # Ends mid-sentence — strong truncation signal
        return True

    # Check for incomplete markdown structures
    incomplete_markers = [
        r"```(?!\s*$)",  # Opening code fence not closed
        r"\|[^\n]*$",     # Table row without newline
        r"\*\*[^*]*$",    # Unclosed bold
    ]
    for marker in incomplete_markers:
        if re.search(marker, output[-200:]):
            return True

    return False


def post_generation_check(result: dict[str, Any]) -> dict[str, Any]:
    """Post-generation: validate output against directive requirements.

    Required keys in result dict:
    - target_words: [min, max] list or single int
    - actual_words: int
    - model_used: string
    - expected_model: string (from routing)
    """
    target = result.get("target_words", 0)
    actual = result.get("actual_words", 0)
    model_used = result.get("model_used", "unknown")
    expected_model = result.get("expected_model", "unknown")

    if isinstance(target, list):
        target_min, target_max = target[0], target[1]
    else:
        target_min = int(target * 0.9)
        target_max = int(target * 1.1)

    issues = []

    # Word count check
    if actual < target_min * (1 - WORD_COUNT_TOLERANCE):
        issues.append(f"SHORT: {actual} words vs target {target_min}-{target_max} ({(1 - actual/target_min)*100:.0f}% under min)")
    elif actual < target_min:
        issues.append(f"BELOW MIN: {actual} words vs target min {target_min}")
    elif actual > target_max * (1 + WORD_COUNT_TOLERANCE):
        issues.append(f"OVER: {actual} words vs target {target_min}-{target_max}")

    # Model check
    if model_used != expected_model and expected_model != "unknown":
        issues.append(f"WRONG MODEL: used {model_used}, expected {expected_model}")

    # Section coverage check
    expected_sections = result.get("expected_sections", [])
    actual_sections = result.get("actual_sections", [])
    missing = [s for s in expected_sections if s not in actual_sections]
    if missing:
        issues.append(f"MISSING SECTIONS: {', '.join(missing)}")

    # Visualization check (from JSON)
    expected_viz = result.get("expected_visualizations", [])
    actual_viz = result.get("actual_visualizations", [])
    missing_viz = [v for v in expected_viz if v not in actual_viz]
    if missing_viz:
        issues.append(f"MISSING VISUALIZATIONS: {', '.join(missing_viz)}")

    # Detect truncation by mid-sentence ending
    if actual > 0:
        last_100 = result.get("output_text", "")[-100:] if "output_text" in result else ""
        if not last_100 or last_100.strip()[-1:] not in (".", "!", "?", '"', "'", ")"):
            issues.append("TRUNCATED: output ends mid-sentence")

    return {
        "pass": len(issues) == 0,
        "issues": issues,
        "actual_words": actual,
        "target_range": f"{target_min}-{target_max}" if isinstance(target, list) else f"{int(target*0.9)}-{int(target*1.1)}",
    }


def escalate_mid_generation(prompt: str, target_model: str = "anthropic/claude-opus-4.7") -> dict[str, Any]:
    """Mid-generation escalation: retry with Opus 4.7."""
    return {
        "escalated": True,
        "to_model": target_model,
        "reason": "Truncation detected mid-generation",
        "action": "RETRY_WITH_OPUS",
    }


# ── Test ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Pre-generation check ===")
    r = pre_generation_check({"target_words": [4000, 6000], "proposed_model": "deepseek-chat", "model_max_tokens": 8192})
    print(f"  Escalated: {r['escalated']} — from {r['from_model']} to {r['to_model']}")
    print(f"  Est. tokens: {r['estimated_tokens']} ({r['utilization_pct']}% of model capacity)")

    print("\n=== Post-generation check ===")
    r = post_generation_check({"target_words": [4000, 6000], "actual_words": 3443, "model_used": "deepseek-chat", "expected_model": "anthropic/claude-opus-4.7"})
    print(f"  Pass: {r['pass']}")
    for issue in r["issues"]:
        print(f"  ❌ {issue}")

    print("\n=== Post-generation check (passing) ===")
    r = post_generation_check({"target_words": [4000, 6000], "actual_words": 5200, "model_used": "anthropic/claude-opus-4.7", "expected_model": "anthropic/claude-opus-4.7"})
    print(f"  Pass: {r['pass']}")
    for issue in r["issues"]:
        print(f"  ❌ {issue}")
    if r["pass"]:
        print("  ✅ All checks passed")
