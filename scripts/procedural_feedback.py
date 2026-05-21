#!/usr/bin/env python3
"""Procedural Memory Feedback — logs brief generation outcomes to brain.

After brief generation, captures:
- What worked (model choices, section quality, word count accuracy)
- Fabrication check results (unverified claims caught)
- Source usefulness (which sources contributed to cited judgments)
- Consistency check outcomes
- Guard pipeline results

Writes to brain/memory/procedural/ via brain.py store-procedural.

Usage:
    python3 scripts/procedural_feedback.py --brief-json path/to/brief.json
    python3 scripts/procedural_feedback.py --brief-json path/to/brief.json --guard-json path/to/guard.json
    python3 scripts/procedural_feedback.py --brief-json path/to/brief.json --dry-run
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import subprocess
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BRAIN_SCRIPT = REPO_ROOT / "brain" / "scripts" / "brain.py"
FEEDBACK_LOG = REPO_ROOT / "memory" / "procedural-feedback.jsonl"


def log(msg: str) -> None:
    print(f"[procedural-feedback] {msg}", file=sys.stderr, flush=True)


def _slugify(text: str) -> str:
    """Convert text to filesystem-safe slug."""
    return re.sub(r"[^a-z0-9_-]+", "-", text.lower()).strip("-")[:60]


def analyze_brief(brief_data: dict) -> dict:
    """Analyze brief generation results for procedural feedback."""
    sections = brief_data.get("sections", [])
    total_words = brief_data.get("total_words", 0)
    target_words = brief_data.get("target_words", 0)
    within_range = brief_data.get("within_range", False)
    consistency_issues = brief_data.get("consistency_issues", [])
    validation = brief_data.get("validation", {})
    directive = brief_data.get("directive", "unknown")

    # Section-level analysis
    section_results = []
    for s in sections:
        words = s.get("words", 0)
        target = s.get("target", 0)
        if target > 0:
            accuracy = round(words / target, 2)
        else:
            accuracy = 0.0

        section_results.append({
            "title": s.get("title", "?"),
            "model": s.get("model_used", "unknown"),
            "words": words,
            "target": target,
            "accuracy": accuracy,
            "on_target": 0.8 <= accuracy <= 1.2,
        })

    # Model usage summary
    models_used = {}
    for s in sections:
        model = s.get("model_used", "unknown")
        models_used[model] = models_used.get(model, 0) + 1

    # Word count accuracy
    if target_words > 0:
        overall_accuracy = round(total_words / target_words, 2)
    else:
        overall_accuracy = 0.0

    return {
        "directive": directive,
        "total_words": total_words,
        "target_words": target_words,
        "overall_accuracy": overall_accuracy,
        "within_range": within_range,
        "sections": section_results,
        "models_used": models_used,
        "consistency_issues": consistency_issues,
        "validation_passed": validation.get("pass", True),
        "validation_issues": validation.get("issues", []),
        "sections_on_target": sum(1 for s in section_results if s["on_target"]),
        "sections_total": len(section_results),
    }


def analyze_guard_results(guard_data: dict) -> dict:
    """Analyze guard pipeline results."""
    guards = guard_data.get("guards", [])
    return {
        "all_passed": guard_data.get("passed", False),
        "total_guards": guard_data.get("total_guards", 0),
        "passed_count": guard_data.get("passed_count", 0),
        "total_issues": guard_data.get("total_issues", 0),
        "guard_details": [
            {
                "guard": g.get("guard", "?"),
                "passed": g.get("passed", False),
                "issue_count": len(g.get("issues", [])),
                "detail": g.get("detail", ""),
            }
            for g in guards
        ],
    }


def format_procedural_entry(brief_analysis: dict, guard_analysis: dict | None = None) -> str:
    """Format feedback as markdown for brain procedural memory."""
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    lines = []
    lines.append(f"## {today}\n")
    lines.append(f"**Directive:** {brief_analysis['directive']}")
    lines.append(f"**Words:** {brief_analysis['total_words']}/{brief_analysis['target_words']} "
                 f"(accuracy: {brief_analysis['overall_accuracy']:.0%})")
    lines.append(f"**Within range:** {'Yes' if brief_analysis['within_range'] else 'No'}")
    lines.append(f"**Sections on target:** {brief_analysis['sections_on_target']}/{brief_analysis['sections_total']}")
    lines.append("")

    # Model routing
    lines.append("**Models used:**")
    for model, count in brief_analysis["models_used"].items():
        lines.append(f"- {model}: {count} section(s)")
    lines.append("")

    # Problem sections
    off_target = [s for s in brief_analysis["sections"] if not s["on_target"]]
    if off_target:
        lines.append("**Off-target sections:**")
        for s in off_target:
            lines.append(f"- {s['title']}: {s['words']}/{s['target']}w ({s['accuracy']:.0%})")
        lines.append("")

    # Consistency
    if brief_analysis["consistency_issues"]:
        lines.append("**Consistency issues:**")
        for issue in brief_analysis["consistency_issues"]:
            lines.append(f"- {issue}")
        lines.append("")

    # Validation
    if not brief_analysis["validation_passed"]:
        lines.append("**Validation FAILED:**")
        for issue in brief_analysis["validation_issues"]:
            lines.append(f"- {issue}")
        lines.append("")

    # Guard results
    if guard_analysis:
        status = "PASSED" if guard_analysis["all_passed"] else "FAILED"
        lines.append(f"**Guard pipeline:** {status} ({guard_analysis['passed_count']}/{guard_analysis['total_guards']})")
        for g in guard_analysis["guard_details"]:
            icon = "+" if g["passed"] else "X"
            lines.append(f"  [{icon}] {g['guard']}: {g['detail']}")
        if guard_analysis["total_issues"] > 0:
            lines.append(f"  Total issues: {guard_analysis['total_issues']}")
        lines.append("")

    # Lessons learned (auto-generated)
    lessons = []
    if brief_analysis["overall_accuracy"] < 0.8:
        lessons.append("Brief was significantly under target — consider increasing section targets or reducing compression")
    elif brief_analysis["overall_accuracy"] > 1.2:
        lessons.append("Brief exceeded target by >20% — consider tighter section prompts")
    if off_target and len(off_target) > len(brief_analysis["sections"]) // 2:
        lessons.append(f"{len(off_target)}/{brief_analysis['sections_total']} sections off target — review section-level word count prompting")
    if guard_analysis and not guard_analysis["all_passed"]:
        failed = [g["guard"] for g in guard_analysis["guard_details"] if not g["passed"]]
        lessons.append(f"Guards failed: {', '.join(failed)} — address before next generation")

    if lessons:
        lines.append("**Lessons:**")
        for lesson in lessons:
            lines.append(f"- {lesson}")
        lines.append("")

    return "\n".join(lines)


def write_to_brain(slug: str, content: str) -> bool:
    """Write procedural feedback to brain via brain.py store-procedural."""
    if not BRAIN_SCRIPT.exists():
        log(f"brain.py not found at {BRAIN_SCRIPT}")
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(BRAIN_SCRIPT), "store-procedural", slug, content],
            capture_output=True, text=True, timeout=15,
            cwd=str(REPO_ROOT),
        )
        if result.returncode != 0:
            log(f"brain.py store-procedural failed: {result.stderr[:200]}")
            return False
        log(f"Written to brain/memory/procedural/{slug}.md")
        return True
    except Exception as e:
        log(f"Error writing to brain: {e}")
        return False


def write_feedback_log(entry: dict) -> None:
    """Append structured feedback to JSONL log."""
    FEEDBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(FEEDBACK_LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run_feedback(
    brief_json_path: str,
    guard_json_path: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Run procedural feedback pipeline."""
    # Load brief data
    brief_data = json.loads(pathlib.Path(brief_json_path).read_text())
    brief_analysis = analyze_brief(brief_data)

    # Load guard data if available
    guard_analysis = None
    if guard_json_path and pathlib.Path(guard_json_path).exists():
        guard_data = json.loads(pathlib.Path(guard_json_path).read_text())
        guard_analysis = analyze_guard_results(guard_data)

    # Format entry
    directive = brief_data.get("directive", "unknown-brief")
    slug = f"brief-generation-{_slugify(directive)}"
    content = format_procedural_entry(brief_analysis, guard_analysis)

    # Build log entry
    log_entry = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "directive": directive,
        "slug": slug,
        "brief_analysis": brief_analysis,
        "guard_analysis": guard_analysis,
    }

    if dry_run:
        print("=== DRY RUN — Procedural Feedback ===")
        print(f"Slug: {slug}")
        print(f"Content:\n{content}")
        print(f"Log entry: {json.dumps(log_entry, indent=2)}")
        return log_entry

    # Write to brain
    brain_ok = write_to_brain(slug, content)

    # Write to JSONL log
    write_feedback_log(log_entry)

    log(f"Feedback recorded: slug={slug}, brain={'ok' if brain_ok else 'fail'}")
    return log_entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Procedural memory feedback after brief generation")
    parser.add_argument("--brief-json", required=True, help="Path to brief JSON output")
    parser.add_argument("--guard-json", default=None, help="Path to guard pipeline JSON output")
    parser.add_argument("--dry-run", action="store_true", help="Print feedback without writing")
    args = parser.parse_args()

    if not pathlib.Path(args.brief_json).exists():
        log(f"Brief JSON not found: {args.brief_json}")
        return 1

    result = run_feedback(args.brief_json, args.guard_json, args.dry_run)

    if not args.dry_run:
        print(json.dumps({"status": "ok", "slug": result.get("slug", "")}, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
