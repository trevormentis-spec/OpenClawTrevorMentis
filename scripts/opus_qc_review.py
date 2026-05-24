#!/usr/bin/env python3
# GATE_EXEMPT: Opus 4.7 QC review script — hardcoded model + OpenRouter endpoint are intentional design choices for the quality audit pipeline
"""Opus 4.7 QC Review — deep quality audit of the daily intelligence brief.

Calls Claude Opus 4.7 via OpenRouter to review the generated brief across
6 quality dimensions. Returns a structured report with severity ratings.

Usage:
    python3 scripts/opus_qc_review.py --brief-dir ~/trevor-briefings/2026-05-23
    python3 scripts/opus_qc_review.py --brief-dir ~/trevor-briefings/2026-05-23 --json
    python3 scripts/opus_qc_review.py --brief-dir ~/trevor-briefings/2026-05-23 --verbose
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import time
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

QC_SYSTEM_PROMPT = """You are a senior intelligence editor conducting a quality-control review of a daily 
intelligence briefing. Your job is to find flaws, not to praise. Be specific and actionable.

Rate each dimension on this scale:
- PASS — No issues found
- WARN — Minor issue(s) that don't invalidate the intelligence
- FAIL — Material problem that should be fixed before delivery
- CRITICAL — Factual error, fabrication risk, or structural failure

Check these dimensions:

1. CALIBRATION — Are Sherman Kent verbal bands consistent with numeric prediction percentages?
   - Band ranges: almost certain (93-99), highly likely (75-85), likely (55-70), 
     even chance (45-55), unlikely (25-35), highly unlikely (10-20), almost no chance (1-5)
   - Flag ANY mismatch between band name and number.
   - Flag single-source judgments above 70%.
   - Flag round-number bias (too many X0 or X5 values).

2. SOURCING — Are claims attributed? Are there unverified assertions?
   - Flag any specific number (price, percentage, count) stated without a source citation.
   - Flag any named entity action stated as fact without attribution.
   - Flag GAP markers — are gaps honestly acknowledged?

3. COMPLETENESS — Is the brief structurally complete?
   - Does the BLUF capture the most decision-relevant finding?
   - Are all 5 key judgments substantive (not filler)?
   - Is the context paragraph adequate?
   - Any obvious geographic or thematic blind spots?

4. CLARITY — Is the writing crisp and actionable?
   - Flag jargon, passive voice that obscures agency, hedging that collapses into meaninglessness.
   - Flag sentences over 40 words.
   - Flag vague references ("some analysts", "reports suggest", "it is believed").

5. RED_TEAM — Is the forced dissent substantive?
   - Is it a genuine counter-argument or perfunctory?
   - Does it identify specific assumptions that could be wrong?
   - Does it propose alternative interpretations?

6. FABRICATION_RISK — Are there hallucination signals?
   - Flag any specific named prediction market contracts not verifiable.
   - Flag precise numbers that look invented (too specific, suspiciously round, no source).
   - Flag named individuals or organizations not commonly in the news.

Return your review as valid JSON:
{
  "overall": "PASS" | "WARN" | "FAIL" | "CRITICAL",
  "overall_note": "one-sentence summary",
  "dimensions": {
    "calibration": {"rating": "...", "findings": ["specific finding 1", ...]},
    "sourcing": {"rating": "...", "findings": [...]},
    "completeness": {"rating": "...", "findings": [...]},
    "clarity": {"rating": "...", "findings": [...]},
    "red_team": {"rating": "...", "findings": [...]},
    "fabrication_risk": {"rating": "...", "findings": [...]}
  },
  "top_3_fixes": ["most important fix 1", "fix 2", "fix 3"],
  "commendations": ["thing done well 1", ...]
}

RULES:
- Be HONEST. If something is good, say so. If something is bad, say so clearly.
- Be SPECIFIC. Quote the problematic text. Say exactly what's wrong.
- No flattery. No hedging. This is a QC review, not a performance review.
- If you find a CRITICAL issue, the overall must be FAIL or CRITICAL.
"""


def build_brief_text(brief_dir: pathlib.Path) -> str:
    """Compile the full brief text for QC review."""
    analysis_dir = brief_dir / "analysis"
    if not analysis_dir.exists():
        return ""

    text_parts = []

    # Exec summary
    exec_summary = analysis_dir / "exec_summary.json"
    if exec_summary.exists():
        try:
            data = json.loads(exec_summary.read_text())
            text_parts.append("=== EXECUTIVE SUMMARY ===\n")
            text_parts.append(f"BLUF: {data.get('bluf', 'N/A')}\n\n")
            text_parts.append(f"CONTEXT: {data.get('context_paragraph', 'N/A')}\n\n")
            text_parts.append("KEY JUDGMENTS:\n")
            for i, kj in enumerate(data.get("five_judgments", []), 1):
                text_parts.append(
                    f"  {i}. [{kj.get('drawn_from_region', '?')}] "
                    f"{kj.get('statement', 'N/A')}\n"
                    f"     Confidence: {kj.get('sherman_kent_band', '?')} "
                    f"({kj.get('prediction_pct', '?')}% / 7d)\n"
                )
            text_parts.append("\n")
        except Exception:
            pass

    # Regional analysis (summarize — don't send all 11 full files)
    text_parts.append("=== REGIONAL COVERAGE ===\n")
    regions_seen = 0
    for region_file in sorted(analysis_dir.glob("*.json")):
        if region_file.name in ("exec_summary.json", "prediction_markets.json"):
            continue
        try:
            data = json.loads(region_file.read_text())
            region = data.get("region", region_file.stem)
            kjs = data.get("key_judgments", [])
            text_parts.append(f"\n--- {region.upper()} ({len(kjs)} KJs) ---\n")
            for kj in kjs:
                text_parts.append(
                    f"  • {kj.get('statement', 'N/A')}\n"
                    f"    [{kj.get('sherman_kent_band', '?')} / {kj.get('prediction_pct', '?')}%]\n"
                )
            regions_seen += 1
            if regions_seen >= 11:
                break
        except Exception:
            pass

    # Red team
    red_team = analysis_dir / "red_team.md"
    if red_team.exists():
        text_parts.append("\n=== RED TEAM / FORCED DISSENT ===\n")
        rt_text = red_team.read_text()
        # Limit to prevent token overflow
        if len(rt_text) > 2000:
            rt_text = rt_text[:2000] + "\n... [truncated]"
        text_parts.append(rt_text + "\n")

    return "\n".join(text_parts)


def call_opus(brief_text: str, verbose: bool = False) -> dict[str, Any]:
    """Call Claude Opus 4.7 via OpenRouter for QC review."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return {
            "overall": "FAIL",
            "overall_note": "OPENROUTER_API_KEY not set — cannot call Opus",
            "dimensions": {},
            "top_3_fixes": ["Re-run with OPENROUTER_API_KEY set"],
            "commendations": [],
        }

    # Limit text to ~8000 words to stay within reasonable token limits
    words = brief_text.split()
    if len(words) > 8000:
        brief_text = " ".join(words[:8000]) + "\n\n[... text truncated for token limits ...]"

    payload = {
        "model": "anthropic/claude-opus-4.7",
        "messages": [
            {"role": "system", "content": QC_SYSTEM_PROMPT},
            {"role": "user", "content": f"Review this intelligence brief:\n\n{brief_text}"},
        ],
        "temperature": 0.0,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }

    if verbose:
        print(f"Calling Opus 4.7 via OpenRouter ({len(words)} words of brief text)...", file=sys.stderr)

    t0 = time.monotonic()

    # Use subprocess + curl for reliability
    import tempfile
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    tmp.write(json.dumps(payload))
    tmp.close()

    try:
        result = subprocess.run(
            [
                "curl", "-s", "-w", "\n%{http_code}",
                "-X", "POST", "https://openrouter.ai/api/v1/chat/completions",
                "-H", "Content-Type: application/json",
                "-H", f"Authorization: Bearer {api_key}",
                "-H", "HTTP-Referer: https://trevormentis-spec.github.io",
                "-H", "X-Title: Trevor QC Pipeline",
                "--data-binary", f"@{tmp.name}",
                "--connect-timeout", "30", "--max-time", "120",
            ],
            capture_output=True, text=True, timeout=130,
        )
    finally:
        os.unlink(tmp.name)

    elapsed = time.monotonic() - t0

    if verbose:
        print(f"Opus response in {elapsed:.1f}s", file=sys.stderr)

    stdout = result.stdout
    idx = stdout.rfind("\n")
    body = stdout[:idx] if idx >= 0 else stdout
    http_code = stdout[idx+1:].strip() if idx >= 0 else "000"

    if not http_code.startswith("2"):
        return {
            "overall": "FAIL",
            "overall_note": f"OpenRouter returned HTTP {http_code}: {body[:300]}",
            "dimensions": {},
            "top_3_fixes": ["API call failed — check OpenRouter"],
            "commendations": [],
        }

    try:
        resp = json.loads(body)
        content = resp["choices"][0]["message"]["content"].strip()

        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
            if content.endswith("```"):
                content = content[:-3]
        if content.startswith("json\n"):
            content = content[5:]

        review = json.loads(content)
        review["_meta"] = {
            "model": "anthropic/claude-opus-4.7",
            "elapsed_seconds": round(elapsed, 1),
            "brief_words": len(words),
            "usage": resp.get("usage", {}),
        }
        return review

    except (json.JSONDecodeError, KeyError, IndexError) as exc:
        return {
            "overall": "FAIL",
            "overall_note": f"Failed to parse Opus response: {exc}",
            "dimensions": {},
            "top_3_fixes": ["Response parsing failed"],
            "commendations": [],
            "_raw_response": body[:1000],
        }


def format_report(review: dict[str, Any], verbose: bool = False) -> str:
    """Format the Opus QC review as a readable console report."""
    lines = []
    lines.append("=" * 72)
    lines.append("  OPUS 4.7 QUALITY CONTROL REVIEW")
    lines.append("=" * 72)

    # Overall
    rating = review.get("overall", "UNKNOWN")
    icons = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "CRITICAL": "🚨"}
    icon = icons.get(rating, "❓")
    lines.append(f"\n  OVERALL: {icon} {rating}")
    lines.append(f"  {review.get('overall_note', '')}")

    # Meta
    meta = review.get("_meta", {})
    if meta:
        lines.append(f"\n  Model: {meta.get('model', '?')}")
        lines.append(f"  Duration: {meta.get('elapsed_seconds', '?')}s")
        lines.append(f"  Brief size: {meta.get('brief_words', '?')} words")
        if "usage" in meta:
            u = meta["usage"]
            cost = u.get("cost", 0)
            lines.append(f"  Tokens: {u.get('prompt_tokens', '?')} in / {u.get('completion_tokens', '?')} out")
            if cost:
                lines.append(f"  Cost: \${cost:.4f}")

    lines.append("")

    # Dimensions
    dims = review.get("dimensions", {})
    for dim_name in ["calibration", "sourcing", "completeness", "clarity", "red_team", "fabrication_risk"]:
        dim = dims.get(dim_name, {})
        dim_rating = dim.get("rating", "?")
        dim_icon = icons.get(dim_rating, "❓")
        lines.append(f"  {dim_icon} {dim_name.upper().replace('_', ' ')}: {dim_rating}")
        for finding in dim.get("findings", []):
            lines.append(f"     → {finding}")

    # Top fixes
    lines.append(f"\n  {'─' * 68}")
    lines.append("  TOP 3 FIXES:")
    for i, fix in enumerate(review.get("top_3_fixes", []), 1):
        lines.append(f"    {i}. {fix}")

    # Commendations
    comms = review.get("commendations", [])
    if comms:
        lines.append(f"\n  COMMENDATIONS:")
        for c in comms:
            lines.append(f"    ✓ {c}")

    lines.append(f"\n{'=' * 72}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Opus 4.7 QC Review")
    parser.add_argument("--brief-dir", required=True, help="Path to brief working directory")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress")
    args = parser.parse_args()

    brief_dir = pathlib.Path(args.brief_dir).expanduser().resolve()
    if not brief_dir.exists():
        print(f"Error: directory not found: {brief_dir}", file=sys.stderr)
        sys.exit(1)

    # Build brief text
    if args.verbose:
        print("Building brief text for QC...", file=sys.stderr)
    brief_text = build_brief_text(brief_dir)
    if not brief_text:
        print("Error: no brief content found", file=sys.stderr)
        sys.exit(1)

    # Call Opus
    review = call_opus(brief_text, verbose=args.verbose)

    if args.json:
        print(json.dumps(review, indent=2, ensure_ascii=False))
    else:
        print(format_report(review, verbose=args.verbose))

    # Exit code based on overall
    overall = review.get("overall", "FAIL")
    if overall in ("FAIL", "CRITICAL"):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
