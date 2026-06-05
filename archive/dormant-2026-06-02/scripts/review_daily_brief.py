#!/usr/bin/env python3
"""
Review the Daily Text Brief with Opus 4.7 — improvement suggestions.

Reads today's text brief, sends to Opus 4.7 via OpenRouter with a
structured critique prompt, and saves improvement notes for tomorrow's run.

Usage:
    python3 scripts/review_daily_brief.py \
        --brief exports/daily-brief-2026-05-21.txt \
        --date 2026-05-21
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.request

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPUS_MODEL = "anthropic/claude-opus-4.7"

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

REVIEW_PROMPT = """You are an intelligence editor critiquing a daily open-source intelligence briefing. Your goal is to help the analyst improve tomorrow's product.

Read the briefing below and provide:

1. **Signal Density** (rate 1-10): Does every paragraph move — development, consequence, assessment? Flag any filler or redundancy.

2. **Coverage Gaps** (list): Are there obvious developments or regions that should have been covered but weren't? Note any missing topics that a reader would expect.

3. **Source Mix** (rate 1-10): Does the source list show diversity (think tanks, wire services, OSINT, prediction markets, local-language media)? Or is it too dependent on one type?

4. **Confidence Calibration** (rate 1-10): Are the Sherman Kent bands used appropriately? Any judgments that should have been softer or firmer given the evidence presented?

5. **Prose Quality** (rate 1-10): Is the writing clear, direct, and intelligence-appropriate? Flag any jargon, passive voice, or vague phrasing.

6. **Freshness** (flag): Are any sources or references stale (>48h old)? The brief should include the most recent 24h of developments.

7. **Specific Recommendations** (numbered list): 3-5 concrete, actionable things to do differently tomorrow.

Be honest and specific. This is internal critique — praise is less useful than precise criticism.

BRIEFING:
---BRIEF_START---
{brief_text}
---BRIEF_END---

SOURCES USED:
{sources_text}
"""


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[review {ts}] {msg}", file=sys.stderr, flush=True)


def call_opus(prompt: str) -> str:
    """Call Opus 4.7 via OpenRouter."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        log("ERROR: OPENROUTER_API_KEY not set")
        return ""

    payload = json.dumps({
        "model": OPUS_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4096,
        "temperature": 0.3,
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/trevormentis-spec",
            "X-Title": "TrevorIntel",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            log(f"Opus review complete ({len(content)} chars)")
            return content
    except Exception as e:
        log(f"Opus call failed: {e}")
        return ""


def save_review(date_str: str, review_text: str, reviews_dir: pathlib.Path) -> None:
    """Save the review to disk."""
    reviews_dir.mkdir(parents=True, exist_ok=True)
    path = reviews_dir / f"review-{date_str}.md"
    header = f"""# Daily Brief Review — {date_str}
Generated: {dt.datetime.now(dt.timezone.utc).isoformat()}
Reviewer: Opus 4.7 (anthropic/claude-opus-4.7)

"""
    path.write_text(header + review_text)
    log(f"Review saved: {path}")


def check_run_improvement(review_file: pathlib.Path, brief_file: pathlib.Path) -> None:
    """
    After review, check if the review would change anything fundamental.
    If yes, update a running improvement log.
    """
    if not review_file.exists():
        return
    review = review_file.read_text()

    # Check for low scores or specific issues in the review
    improvement_log = REPO_ROOT / "exports" / "improvement-track.md"
    low_scores = []
    for line in review.split("\n"):
        for metric in ["Signal Density", "Source Mix", "Confidence Calibration", "Prose Quality"]:
            if metric in line and "1-10" in line:
                # Extract score
                import re
                match = re.search(r'(\d+)\s*/\s*10', line)
                if match and int(match.group(1)) <= 6:
                    low_scores.append(f"{metric}: {match.group(1)}/10")

    if low_scores:
        entry = f"\n## {brief_file.stem.replace('daily-brief-', '')}\n"
        for score in low_scores:
            entry += f"- ⚠️ {score}\n"
        entry += f"\n[Full review](reviews/{review_file.name})\n"
        with open(improvement_log, "a") as f:
            f.write(entry)
        log(f"Low scores logged to improvement track: {', '.join(low_scores)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Review daily brief with Opus 4.7")
    parser.add_argument("--brief", required=True, help="Path to brief text file")
    parser.add_argument("--date", required=True, help="Date string YYYY-MM-DD")
    args = parser.parse_args()

    brief_path = pathlib.Path(args.brief)
    if not brief_path.exists():
        log(f"ERROR: Brief not found: {brief_path}")
        sys.exit(1)

    brief_text = brief_path.read_text()

    # Extract sources section from the brief
    sources_text = ""
    if "SOURCES USED TODAY" in brief_text:
        parts = brief_text.split("SOURCES USED TODAY")
        if len(parts) > 1:
            sources_text = parts[1].strip()

    prompt = REVIEW_PROMPT.format(brief_text=brief_text, sources_text=sources_text)

    log("Sending to Opus 4.7 for review...")
    review = call_opus(prompt)

    if not review:
        log("Review failed — no output from Opus")
        sys.exit(1)

    reviews_dir = REPO_ROOT / "exports" / "reviews"
    save_review(args.date, review, reviews_dir)

    # Check for needed improvements
    review_file = reviews_dir / f"review-{args.date}.md"
    check_run_improvement(review_file, brief_path)

    log("Review complete")


if __name__ == "__main__":
    main()
