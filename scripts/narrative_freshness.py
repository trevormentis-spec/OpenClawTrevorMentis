#!/usr/bin/env python3
"""
Narrative Freshness Auditor — Self-Improvement Loop.

After each daily brief, compares today's analysis structure with previous
days to detect:
- Same BLUF structure / framing repeated
- Same key judgment patterns (same regions, similar statements)
- Same evidence types being cited
- Same scenario structures used repeatedly

When stale patterns are detected, generates a "freshness challenge" that
forces alternative framing in the next analysis.

Design:
- Reads last N days of exec_summary.json files from ~/trevor-briefings/
- Computes text similarity between today's and yesterday's analysis
- Detects exact or near-exact BLUF repetition
- Tracks judgment patterns over time
- Writes freshness challenge to analysis/freshness-challenges/
- Challenge is injected into next pipeline's analyze.py system prompt

Usage:
    python3 scripts/narrative_freshness.py                    # Check today vs yesterday
    python3 scripts/narrative_freshness.py --days 7           # Compare against last 7 days
    python3 scripts/narrative_freshness.py --report           # Show freshness history
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
CHALLENGE_DIR = REPO_ROOT / "analysis" / "freshness-challenges"
BRIEFINGS_DIR = pathlib.Path.home() / "trevor-briefings"

# Similarity threshold above which we flag as stale
BLUF_SIMILARITY_THRESHOLD = 0.60   # 60%+ BLUF overlap = stale
JUDGMENT_OVERLAP_THRESHOLD = 0.50  # 50%+ judgment overlap = pattern repetition


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[freshness {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, Exception):
            return {}
    return {}


def load_exec_summary(date_str: str) -> dict | None:
    """Load exec_summary.json for a given date."""
    for base in [BRIEFINGS_DIR, REPO_ROOT / "trevor-briefings"]:
        path = base / date_str / "analysis" / "exec_summary.json"
        if path.exists():
            return load_json(path)
    return None


def text_similarity(a: str, b: str) -> float:
    """Simple word-overlap similarity between two texts."""
    if not a or not b:
        return 0.0
    words_a = set(re.findall(r'\b\w+\b', a.lower()))
    words_b = set(re.findall(r'\b\w+\b', b.lower()))
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / max(len(union), 1)


def extract_judgment_patterns(exec_data: dict) -> dict:
    """Extract structural patterns from an exec summary for comparison."""
    judgments = exec_data.get("five_judgments", [])
    regions = [j.get("drawn_from_region", "") for j in judgments]
    bands = [j.get("sherman_kent_band", "") for j in judgments]
    statements = [j.get("statement", "") for j in judgments]
    return {
        "regions": regions,
        "bands": bands,
        "statements": statements,
        "bluf": exec_data.get("bluf", ""),
        "num_judgments": len(judgments),
    }


def compute_freshness_metrics(today_dir: str, days: int = 1) -> dict:
    """Compare today's analysis with previous days for freshness metrics."""
    today = load_exec_summary(today_dir)
    if not today:
        return {"error": f"No exec summary found for {today_dir}"}

    today_patterns = extract_judgment_patterns(today)
    today_date = dt.datetime.strptime(today_dir, "%Y-%m-%d").date()

    metrics = {
        "today": today_dir,
        "days_checked": 0,
        "bluf_similarity": [],
        "judgment_region_overlap": [],
        "judgment_band_overlap": [],
        "statement_similarity": [],
        "stale_bluf_detected": False,
        "repeated_pattern_detected": False,
        "challenges": [],
    }

    for i in range(1, days + 1):
        prev_date = (today_date - dt.timedelta(days=i)).strftime("%Y-%m-%d")
        prev = load_exec_summary(prev_date)
        if not prev:
            continue

        prev_patterns = extract_judgment_patterns(prev)
        metrics["days_checked"] += 1

        # BLUF similarity
        bluf_sim = text_similarity(today_patterns["bluf"], prev_patterns["bluf"])
        metrics["bluf_similarity"].append({"date": prev_date, "similarity": round(bluf_sim, 3)})

        # Judgment region overlap
        today_regions = set(today_patterns["regions"])
        prev_regions = set(prev_patterns["regions"])
        region_overlap = len(today_regions & prev_regions) / max(len(today_regions | prev_regions), 1)
        metrics["judgment_region_overlap"].append({"date": prev_date, "overlap": round(region_overlap, 3)})

        # Judgment band overlap
        today_bands = set(today_patterns["bands"])
        prev_bands = set(prev_patterns["bands"])
        band_overlap = len(today_bands & prev_bands) / max(len(today_bands | prev_bands), 1)
        metrics["judgment_band_overlap"].append({"date": prev_date, "overlap": round(band_overlap, 3)})

        # Statement similarity (average across judgments)
        if today_patterns["statements"] and prev_patterns["statements"]:
            similarities = []
            for ts in today_patterns["statements"]:
                for ps in prev_patterns["statements"]:
                    similarities.append(text_similarity(ts, ps))
            avg_sim = sum(similarities) / max(len(similarities), 1)
            metrics["statement_similarity"].append({"date": prev_date, "similarity": round(avg_sim, 3)})

        # Check for staleness
        if bluf_sim >= BLUF_SIMILARITY_THRESHOLD:
            metrics["stale_bluf_detected"] = True
            metrics["challenges"].append(
                f"BLUF framing shares {round(bluf_sim * 100)}% similarity with {prev_date}. "
                f"Consider: is the core narrative genuinely unchanged, or is this framing inertia?"
            )

        if region_overlap >= JUDGMENT_OVERLAP_THRESHOLD:
            metrics["repeated_pattern_detected"] = True
            metrics["challenges"].append(
                f"Judgment region distribution overlaps {round(region_overlap * 100)}% with {prev_date}. "
                f"Same regions being prioritized — is that analytically justified or habitual?"
            )

        if band_overlap >= 0.80:
            metrics["challenges"].append(
                f"Confidence band distribution nearly identical to {prev_date}. "
                f"Are you varying confidence appropriately, or defaulting to prior patterns?"
            )

    # Limit challenges
    metrics["challenges"] = metrics["challenges"][:5]

    # Generate a human-readable challenge if needed
    if metrics["challenges"]:
        metrics["freshness_score"] = max(0, 100 - len(metrics["challenges"]) * 20)
    else:
        metrics["freshness_score"] = 100

    return metrics


def generate_challenge(metrics: dict) -> str:
    """Generate a freshness challenge block for pipeline injection."""
    if not metrics.get("challenges"):
        return ""

    lines = []
    lines.append("\n\n### === FRESHNESS CHALLENGE ===")
    lines.append("Your recent analysis shows structural repetition. The following patterns")
    lines.append("were detected. They may be analytically justified — or they may be framing inertia.")
    lines.append("")

    if metrics.get("stale_bluf_detected"):
        lines.append("**⚠ Stale BLUF framing detected.**")
    if metrics.get("repeated_pattern_detected"):
        lines.append("**⚠ Repeated judgment structure detected.**")

    lines.append("")
    lines.append("Challenges for this analysis:")
    for i, challenge in enumerate(metrics["challenges"], 1):
        lines.append(f"  {i}. {challenge}")

    lines.append("")
    lines.append("Consider: Is the current framing the best available, or the most familiar?")
    lines.append("If the situation is genuinely stable, say so explicitly rather than")
    lines.append("repeating prior language.")
    lines.append("\n=== END FRESHNESS CHALLENGE ===")

    return "\n".join(lines)


def write_challenge(today_dir: str, metrics: dict) -> pathlib.Path | None:
    """Write freshness challenge to disk for pipeline injection."""
    if not metrics.get("challenges"):
        return None

    CHALLENGE_DIR.mkdir(parents=True, exist_ok=True)
    challenge_path = CHALLENGE_DIR / f"{today_dir}-freshness-challenge.md"
    challenge_text = generate_challenge(metrics)
    
    # Add metadata header
    full_text = (
        f"# Freshness Challenge — {today_dir}\n"
        f"**Generated:** {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC\n"
        f"**Freshness score:** {metrics.get('freshness_score', '?')}/100\n\n"
        + challenge_text
    )
    
    challenge_path.write_text(full_text)
    log(f"Freshness challenge written: {challenge_path}")
    return challenge_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=3, help="Number of previous days to compare")
    parser.add_argument("--report", action="store_true", help="Show freshness report only")
    parser.add_argument("--today", default="", help="Today's date (YYYY-MM-DD)")
    args = parser.parse_args()

    today = args.today or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")

    metrics = compute_freshness_metrics(today, days=args.days)

    if "error" in metrics:
        log(f"Freshness check failed: {metrics['error']}")
        print(metrics['error'])
        return 1

    if args.report:
        print(f"# Narrative Freshness Report — {today}")
        print(f"**Days compared:** {metrics['days_checked']}")
        print(f"**Freshness score:** {metrics.get('freshness_score', '?')}/100")
        print()
        if metrics.get("challenges"):
            print("**Challenges:**")
            for c in metrics["challenges"]:
                print(f"- {c}")
        else:
            print("✅ No freshness issues detected.")
        print()
        for bluf in metrics.get("bluf_similarity", []):
            print(f"BLUF vs {bluf['date']}: {bluf['similarity']}")
        for region in metrics.get("judgment_region_overlap", []):
            print(f"Regions vs {region['date']}: {region['overlap']}")
        return 0

    challenge_path = write_challenge(today, metrics)

    if challenge_path and metrics.get("challenges"):
        log(f"{len(metrics['challenges'])} freshness challenges generated")
        print(f"\nFreshness check: {metrics['freshness_score']}/100")
        for c in metrics["challenges"]:
            print(f"  ⚠ {c[:100]}...")
    else:
        print(f"\nFreshness check: {metrics['freshness_score']}/100 — no issues detected")

    return 0


if __name__ == "__main__":
    sys.exit(main())
