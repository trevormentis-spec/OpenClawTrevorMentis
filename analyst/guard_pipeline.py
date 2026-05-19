#!/usr/bin/env python3
"""Unified guard pipeline — runs all quality guards on a deliverable.

Runs: fabrication_check, themes_preflight, escalation_guard (post-generation).
Reports per-guard pass/fail. Blocks delivery on any guard failure.

Usage:
    python3 analyst/guard_pipeline.py --brief path/to/brief.md --json path/to/brief.json
    python3 analyst/guard_pipeline.py --brief path/to/brief.md --query "USMCA review"
    python3 analyst/guard_pipeline.py --brief path/to/brief.md --verbose
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def run_fabrication_check(brief_path: str, verbose: bool = False) -> dict[str, Any]:
    """Run fabrication_check.py against the brief."""
    result = {"guard": "fabrication_check", "passed": False, "issues": [], "detail": ""}

    try:
        proc = subprocess.run(
            [sys.executable, "analyst/fabrication_check.py", "--brief", brief_path, "--json"],
            capture_output=True, text=True, timeout=30,
        )

        if proc.stdout.strip():
            issues = json.loads(proc.stdout)
            fabrication_issues = [i for i in issues if i.get("status") == "UNVERIFIED"]
            result["passed"] = len(fabrication_issues) == 0
            result["issues"] = fabrication_issues
            result["detail"] = f"{len(fabrication_issues)} fabrication issues"
        else:
            # Check exit code
            result["passed"] = proc.returncode == 0
            result["detail"] = f"Exit code {proc.returncode}: {proc.stderr[:200]}"

    except subprocess.TimeoutExpired:
        result["detail"] = "TIMEOUT"
    except json.JSONDecodeError:
        result["passed"] = proc.returncode == 0
        result["detail"] = stderr if (stderr := proc.stderr.strip()) else "JSON parse failed"
    except Exception as exc:
        result["detail"] = str(exc)

    return result


def run_themes_preflight(brief_path: str, query: str, verbose: bool = False) -> dict[str, Any]:
    """Run themes_preflight.py against the brief."""
    result = {"guard": "themes_preflight", "passed": False, "issues": [], "detail": ""}

    try:
        proc = subprocess.run(
            [sys.executable, "analyst/themes_preflight.py", "--query", query, "--brief", brief_path, "--json"],
            capture_output=True, text=True, timeout=30,
        )

        if proc.stdout.strip():
            try:
                data = json.loads(proc.stdout)
                missing = [c for c in data.get("coverage", []) if c.get("status") == "FAIL"]
                result["passed"] = len(missing) == 0
                result["issues"] = missing
                result["detail"] = f"{len(missing)} missing themes"
            except json.JSONDecodeError:
                result["passed"] = proc.returncode == 0
                result["detail"] = proc.stdout[:200]
        else:
            result["passed"] = proc.returncode == 0
            result["detail"] = f"Exit code {proc.returncode}"

    except subprocess.TimeoutExpired:
        result["detail"] = "TIMEOUT"
    except Exception as exc:
        result["detail"] = str(exc)

    return result


def run_escalation_guard(
    brief_path: str,
    brief_json_path: str | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    """Run escalation guard checks on the brief."""
    result = {"guard": "escalation_guard", "passed": True, "issues": [], "detail": ""}

    # Read brief to get word count
    try:
        with open(brief_path) as f:
            text = f.read()
        words = len(text.split())

        # Check for truncation (ends mid-sentence)
        last_char = text.strip()[-1] if text.strip() else ""
        if last_char not in (".", "!", "?", '"', "'", ")", "]", "}", "`"):
            result["issues"].append("TRUNCATED: brief ends mid-sentence")
            result["passed"] = False

        result["detail"] = f"{words} words"
        if result["issues"]:
            result["detail"] += "; " + "; ".join(result["issues"])

    except Exception as exc:
        result["detail"] = str(exc)
        result["passed"] = False

    return result


def run_pipeline(brief_path: str, query: str | None = None, brief_json: str | None = None, verbose: bool = False) -> dict[str, Any]:
    """Run all guards and return aggregated results."""
    if query is None:
        query = "general intelligence assessment"

    results = [
        run_fabrication_check(brief_path, verbose),
        run_escalation_guard(brief_path, brief_json, verbose),
    ]

    # Only run themes_preflight if a meaningful query is provided
    if query and query != "general intelligence assessment":
        results.append(run_themes_preflight(brief_path, query, verbose))

    all_passed = all(r["passed"] for r in results)
    total_issues = sum(len(r["issues"]) for r in results)

    return {
        "passed": all_passed,
        "total_guards": len(results),
        "passed_count": sum(1 for r in results if r["passed"]),
        "total_issues": total_issues,
        "guards": results,
        "detail": f"{sum(1 for r in results if r['passed'])}/{len(results)} guards passing ({total_issues} issues)" if not all_passed else "ALL PASSED",
    }


def main():
    parser = argparse.ArgumentParser(description="Unified guard pipeline")
    parser.add_argument("--brief", required=True, help="Path to brief markdown file")
    parser.add_argument("--json", help="Path to brief JSON file")
    parser.add_argument("--query", default=None, help="Query string for themes_preflight")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    if not os.path.exists(args.brief):
        print(f"Error: brief not found: {args.brief}", file=sys.stderr)
        sys.exit(1)

    results = run_pipeline(args.brief, args.query, args.json, args.verbose)

    if args.verbose:
        for g in results["guards"]:
            status = "✅" if g["passed"] else "❌"
            print(f"{status} {g['guard']}: {g['detail']}")
            for issue in g["issues"]:
                print(f"     {issue}")

    print(f"\n{'✅ ALL GUARDS PASSING' if results['passed'] else '❌ GUARDS BLOCKING'} — {results['detail']}")

    if args.verbose:
        print(f"\nPassing: {results['passed_count']}/{results['total_guards']}")
        print(f"Issues: {results['total_issues']}")

    sys.exit(0 if results["passed"] else 1)


if __name__ == "__main__":
    main()
