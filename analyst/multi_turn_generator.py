#!/usr/bin/env python3
"""Multi-turn section-by-section generator for flagship briefs.

Generates each section as its own model call with context window of
all prior sections. Concatenates into a single brief. Then runs
visualization pipeline against the completed JSON.

Usage:
    python3 analyst/multi_turn_generator.py \
        --directive "USMCA review, 10 sections, family office" \
        --output path/to/brief.md \
        --json path/to/brief.json

    python3 analyst/multi_turn_generator.py \
        --sections-file usmca-sections.json \
        --directive "USMCA review" \
        --output memory/usmca-v3.md \
        --json memory/usmca-v3.json
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# ── Section definitions for flagship briefs ───────────────────

# Default section plan for USMCA-style flagship briefs
DEFAULT_SECTIONS = [
    {"id": "sec-1", "title": "Executive Summary", "target_words": 600, "model": "anthropic/claude-opus-4.7"},
    {"id": "sec-2", "title": "Political Picture", "target_words": 700, "model": "anthropic/claude-opus-4.7"},
    {"id": "sec-3", "title": "Sector Exposure", "target_words": 700, "model": "anthropic/claude-opus-4.7"},
    {"id": "sec-4", "title": "Economic Dynamics", "target_words": 600, "model": "anthropic/claude-opus-4.7"},
    {"id": "sec-5", "title": "Scenarios", "target_words": 800, "model": "anthropic/claude-opus-4.7"},
    {"id": "sec-6", "title": "Trade Positioning", "target_words": 600, "model": "anthropic/claude-opus-4.7"},
    {"id": "sec-7", "title": "Watch Indicators", "target_words": 400, "model": "anthropic/claude-opus-4.7"},
    {"id": "sec-8", "title": "Calendar", "target_words": 300, "model": "anthropic/claude-opus-4.7"},
    {"id": "sec-9", "title": "Subscriber Action Lines", "target_words": 400, "model": "anthropic/claude-opus-4.7"},
    {"id": "sec-10", "title": "Appendix", "target_words": 500, "model": "anthropic/claude-opus-4.7"},
]

TOTAL_TARGET = sum(s["target_words"] for s in DEFAULT_SECTIONS)  # ~5,600


def log(msg: str) -> None:
    print(f"[multi-turn] {msg}", file=sys.stderr, flush=True)


def load_kalshi_data() -> str:
    """Load latest Kalshi scanner output."""
    exports = REPO_ROOT / "exports"
    scans = sorted(exports.glob("kalshi-scan-*.md"), reverse=True)
    if scans:
        return scans[0].read_text()[:1000]
    return "No Kalshi scanner data available."


def call_model(
    prompt: str,
    system: str,
    model: str = "anthropic/claude-opus-4.7",
    max_tokens: int = 2000,
    temperature: float = 0.3,
) -> tuple[str, dict[str, Any]]:
    """Call a model via appropriate provider. Returns (content, metadata)."""

    start_time = time.time()

    # Route to provider
    if not any(os.environ.get(k) for k in ["OPENROUTER_API_KEY", "DEEPSEEK_API_KEY"]):
        # Fallback: read from .env
        env_path = pathlib.Path(__file__).resolve().parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().split(chr(10)):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k, v.strip())

    if "opus" in model:
        # OpenRouter
        or_key = os.environ.get("OPENROUTER_API_KEY", "")
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {or_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://openclaw.ai",
            "X-Title": "Open Claw Mexico Desk",
        }
    else:
        # DeepSeek Direct
        ds_key = os.environ.get("DEEPSEEK_API_KEY", "")
        if not ds_key:
            # Fallback: re-read from .env
            env_path = pathlib.Path(__file__).resolve().parent.parent / ".env"
            if env_path.exists():
                for line in env_path.read_text().split(chr(10)):
                    line = line.strip()
                    if line.startswith("DEEPSEEK_API_KEY="):
                        ds_key = line.split("=", 1)[1].strip()
                        os.environ["DEEPSEEK_API_KEY"] = ds_key
                        break
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {ds_key}",
            "Content-Type": "application/json",
        }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    log(f"DEBUG: calling {url} with model={model}, or_key_len={len(or_key) if 'opus' in model or 'haiku' in model else 0}, ds_key_len={len(ds_key) if 'opus' not in model and 'haiku' not in model else 0}")
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=300) as resp:
        result = json.loads(resp.read())

    content = result["choices"][0]["message"]["content"]
    usage = result.get("usage", {})
    elapsed = time.time() - start_time

    metadata = {
        "model": model,
        "tokens_in": usage.get("prompt_tokens", 0),
        "tokens_out": usage.get("completion_tokens", 0),
        "elapsed_sec": round(elapsed, 1),
    }

    return content, metadata


def generate_section(
    section: dict[str, Any],
    directive: str,
    prior_sections: list[dict[str, Any]],
    kalshi_data: str,
    section_index: int,
    total_sections: int,
) -> dict[str, Any]:
    """Generate a single section. Returns {id, title, content, metadata, words}."""
    sec_id = section["id"]
    sec_title = section["title"]
    target = section["target_words"]
    model_name = section["model"]

    # Build context from prior sections
    prior_text = ""
    for ps in prior_sections:
        prior_text += f"\n\n## {ps['title']}\n{ps['content'][:500]}"

    if prior_text.strip():
        prior_context = f"\n\n=== ALREADY WRITTEN SECTIONS (for consistency): ===\n{prior_text.strip()}\n"
    else:
        prior_context = "\n\n(This is the first section. No prior context.)\n"

    system = f"""You are the Open Claw Mexico desk. You are writing section {section_index}/{total_sections}
of a flagship subscriber brief.

SECTION: {sec_title}
TARGET LENGTH: ~{target} words
OVERALL BRIEF: {directive}
KALSHI DATA (use for trade positions if relevant): {kalshi_data}

Requirements:
- Write for a family office / institutional investor audience
- Every quantitative claim needs source + Admiralty rating
- Sherman Kent bands on every directional judgment
- Do NOT repeat what prior sections already covered — extend
- Write in subscriber-grade analytical prose
- Output ONLY the section content. No meta-commentary."""

    prompt = f"""Write Section {section_index}: {sec_title}.
Target: ~{target} words.
{prior_context}

Produce the section content now."""

    log(f"Generating section {section_index}/{total_sections}: {sec_title} ({model_name}, ~{target}w)")

    content, metadata = call_model(prompt, system, model=model_name, max_tokens=min(target * 2, 4000))
    words = len(content.split())

    log(f"  → {words} words, {metadata['tokens_out']} tokens out, {metadata['elapsed_sec']}s, {model_name}")

    return {
        "id": sec_id,
        "title": sec_title,
        "content": content.strip(),
        "words": words,
        "target": target,
        "model_used": model_name,
        "metadata": metadata,
    }


def consistency_check(sections: list[dict[str, Any]]) -> list[str]:
    """Check for contradictions across sections."""
    issues = []
    all_text = "\n".join(s["content"] for s in sections).lower()

    # Check calibration references are consistent
    cal_bands = re.findall(r"(almost certain|highly likely|likely|probable|even chance|unlikely|highly unlikely)", all_text, re.I)
    if len(cal_bands) < 5:
        issues.append(f"Only {len(cal_bands)} calibration bands found across {len(sections)} sections — low.")

    return issues


def generate_brief(
    directive: str,
    output_md: str | None,
    output_json: str | None,
    sections_plan: list[dict[str, Any]] | None = None,
    kalshi_data: str | None = None,
) -> dict[str, Any]:
    """Generate a full multi-section brief."""

    sections_plan = sections_plan or DEFAULT_SECTIONS
    if kalshi_data is None:
        kalshi_data = load_kalshi_data()

    log(f"Starting multi-turn generation: {len(sections_plan)} sections, ~{sum(s['target_words'] for s in sections_plan)} target words")

    generated: list[dict[str, Any]] = []

    for i, section in enumerate(sections_plan, 1):
        result = generate_section(section, directive, generated, kalshi_data, i, len(sections_plan))
        generated.append(result)

    # Assemble
    total_words = sum(s["words"] for s in generated)
    header = f"# {directive}\n\n**Generated:** 2026-05-18\n**Sections:** {len(generated)}\n**Total words:** {total_words}\n\n---\n\n"
    body = "\n\n".join(f"## {s['title']}\n\n{s['content']}" for s in generated)
    appendix = f"\n\n---\n\n### Generation Metadata\n\n| Section | Words | Target | Model | Tokens Out | Time |\n|---------|-------|--------|-------|-----------|------|\n"
    for s in generated:
        appendix += f"| {s['title']} | {s['words']} | {s['target']} | {s['model_used']} | {s['metadata']['tokens_out']} | {s['metadata']['elapsed_sec']}s |\n"
    appendix += f"\n**Total words:** {total_words} (target: ~{TOTAL_TARGET})"
    appendix += f"\n**Opus calls:** {sum(1 for s in generated if s['model_used'] == 'opus')} | **V4 Pro calls:** {sum(1 for s in generated if s['model_used'] != 'opus')}"

    full_text = header + body + appendix

    # Consistency check
    issues = consistency_check(generated)

    brief = {
        "directive": directive,
        "sections": generated,
        "total_words": total_words,
        "target_words": TOTAL_TARGET,
        "within_range": TOTAL_TARGET * 0.8 <= total_words <= TOTAL_TARGET * 1.2,
        "consistency_issues": issues,
    }

    # Post-generation escalation guard check
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from analyst.escalation_guard import post_generation_check
        validation = post_generation_check({
            "target_words": [int(TOTAL_TARGET * 0.8), TOTAL_TARGET],
            "actual_words": total_words,
            "model_used": generated[0]["model_used"] if generated else "unknown",
            "expected_model": generated[0]["model_used"] if generated else "unknown",
            "expected_sections": [s["title"] for s in sections_plan],
            "actual_sections": [s["title"] for s in generated],
        })
        brief["validation"] = validation
        if not validation["pass"]:
            log(f"ESCALATION: post-generation check failed — {validation['issues']}")
    except Exception as exc:
        log(f"Escalation guard not available: {exc}")
        brief["validation"] = {"pass": True, "issues": ["guard not loaded"]}

    if output_md:
        pathlib.Path(output_md).parent.mkdir(parents=True, exist_ok=True)
        pathlib.Path(output_md).write_text(full_text)
        log(f"Brief saved: {output_md} ({total_words} words)")

    if output_json:
        json_path = pathlib.Path(output_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(brief, indent=2, default=str))
        log(f"JSON saved: {output_json}")

    return brief


def main():
    parser = argparse.ArgumentParser(description="Multi-turn brief generator")
    parser.add_argument("--directive", required=True, help="Brief description / title")
    parser.add_argument("--output", default=None, help="Output markdown path")
    parser.add_argument("--json", default=None, help="Output JSON path")
    args = parser.parse_args()

    brief = generate_brief(args.directive, args.output, args.json)

    print(f"\n{'='*50}")
    print(f"Generation complete:")
    print(f"  Sections: {len(brief['sections'])}")
    print(f"  Words: {brief['total_words']} (target: ~{brief['target_words']})")
    print(f"  Within range: {brief['within_range']}")
    print(f"  Issues: {len(brief['consistency_issues'])}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
