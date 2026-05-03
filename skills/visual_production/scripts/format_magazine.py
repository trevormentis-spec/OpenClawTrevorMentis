#!/usr/bin/env python3
"""CLI entry point — delegates to the visual_production package.

Usage:
    python3 skills/visual_production/scripts/format_magazine.py \\
        --input tasks/news_analysis.md \\
        --title "TREVOR GLOBAL INTELLIGENCE BRIEFING" \\
        --issue "03 May 2026" \\
        --infographics exports/images/infographic-hormuz.svg \\
        --output exports/pdfs/magazine-briefing.pdf
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the package is importable
_PKG = Path(__file__).resolve().parent.parent / "visual_production"
sys.path.insert(0, str(_PKG.parent))

from visual_production.router import produce


def main():
    parser = argparse.ArgumentParser(
        description="Build magazine-style intelligence briefing PDF"
    )
    parser.add_argument("--input", required=True, help="Markdown analysis file path")
    parser.add_argument("--title", default="TREVOR INTELLIGENCE BRIEFING")
    parser.add_argument("--issue", default="")
    parser.add_argument("--output", required=True, help="Output PDF path")
    parser.add_argument("--product", default="magazine", help="Product type (magazine, brief, ...)")
    parser.add_argument(
        "--infographics", nargs="*", default=[], help="SVG infographic paths"
    )
    parser.add_argument("--no-quality-gate", action="store_true", help="Skip post-render checks")
    args = parser.parse_args()

    print(f"📰 Starting visual production: {args.product}")

    result = produce(
        markdown_path=args.input,
        product=args.product,
        title=args.title,
        issue=args.issue or None,
        infographics=args.infographics or None,
        output=args.output,
        run_quality_gate=not args.no_quality_gate,
    )

    print(f"\n{result.summary()}")
    if result.warnings:
        for w in result.warnings:
            print(f"  ⚠️  {w}")
    if result.errors:
        for e in result.errors:
            print(f"  ❌ {e}")

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
