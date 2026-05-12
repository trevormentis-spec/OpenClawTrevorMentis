#!/usr/bin/env python3
"""
Procedural memory loader — reads skills/procedures from brain/memory/procedural/
and injects them into the analysis system prompt at runtime.

This is how Trevor actually LEARNS from prior operations. When a successful
fix is documented as a skill/procedure in brain/memory/procedural/, this
loader reads it and makes it available to the analyst.

Usage:
    python3 scripts/procedural_memory_loader.py --format markdown
    python3 scripts/procedural_memory_loader.py --format json

Called from:
    orchestrate.py (before analysis step)

Output:
    Writes brain/memory/procedural/compiled.md — a single document with all
    active procedures, dated and versioned.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PROCEDURAL_DIR = REPO_ROOT / "brain" / "memory" / "procedural"
COMPILED_FILE = PROCEDURAL_DIR / "compiled.md"


def log(msg: str) -> None:
    print(f"[procedural] {msg}", file=sys.stderr, flush=True)


def load_procedures() -> list[dict[str, Any]]:
    """Read all .md files from procedural memory directory."""
    if not PROCEDURAL_DIR.exists():
        log(f"procedural dir not found: {PROCEDURAL_DIR}")
        return []

    procedures = []
    for f in sorted(PROCEDURAL_DIR.glob("*.md")):
        if f.name == "compiled.md":
            continue
        content = f.read_text().strip()
        if not content:
            continue
        procedures.append({
            "name": f.stem,
            "filename": f.name,
            "modified": dt.datetime.fromtimestamp(
                f.stat().st_mtime, tz=dt.timezone.utc
            ).isoformat(),
            "content": content[:2000],  # Cap per-file
            "size": len(content),
        })
    return procedures


def compile_markdown(procedures: list[dict[str, Any]]) -> str:
    """Compile all procedures into a single markdown document."""
    date_utc = dt.datetime.utcnow().strftime("%Y-%m-%d")
    lines = [
        f"# Compiled Procedural Memory — {date_utc}",
        "",
        f"Active procedures: {len(procedures)}",
        "These are lessons learned from prior operations, successful fixes,",
        "and operational procedures. Use them to inform analysis.",
        "",
        "---",
        "",
    ]
    for p in procedures:
        lines.append(f"## {p['name']}")
        lines.append(f"*Last modified: {p['modified']}*")
        lines.append("")
        lines.append(p["content"])
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def format_for_prompt(procedures: list[dict[str, Any]]) -> str:
    """Format procedures as a compact block for system prompt injection."""
    if not procedures:
        return ""
    
    date_utc = dt.datetime.utcnow().strftime("%Y-%m-%d")
    parts = [
        f"\n\n### === PROCEDURAL MEMORY ({date_utc}) ===\n"
        f"Learned procedures that should inform this analysis:\n"
    ]
    for p in procedures:
        # Only use the first 500 chars as a "rule" summary
        content = p["content"]
        # Try to extract the procedure description (first paragraph or ## section)
        proc_text = content[:500].strip()
        parts.append(f"\n**{p['name']}**\n{proc_text}\n")
    
    parts.append("\n=== END PROCEDURAL MEMORY ===\n")
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=["markdown", "json", "prompt"],
                        default="markdown",
                        help="Output format (default: markdown)")
    args = parser.parse_args()

    procedures = load_procedures()
    log(f"Loaded {len(procedures)} procedures from {PROCEDURAL_DIR}")

    if not procedures:
        log("No procedures found — nothing to inject.")
        return 0

    if args.format == "markdown":
        output = compile_markdown(procedures)
        PROCEDURAL_DIR.mkdir(parents=True, exist_ok=True)
        COMPILED_FILE.write_text(output)
        log(f"Compiled procedural memory written to {COMPILED_FILE}")
        print(output)

    elif args.format == "json":
        print(json.dumps(procedures, indent=2))

    elif args.format == "prompt":
        prompt_block = format_for_prompt(procedures)
        print(prompt_block)

    return 0


if __name__ == "__main__":
    sys.exit(main())
