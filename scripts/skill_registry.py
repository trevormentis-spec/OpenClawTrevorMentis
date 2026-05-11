#!/usr/bin/env python3
"""
skill_registry.py — Procedural memory discovery + progressive disclosure for Trevor.

Scans skills/trevor/ for SKILL.md files with frontmatter, builds a JSON cache,
and provides two access patterns:
  - skills_list()  → lightweight index (~500 tokens)
  - skill_view()   → full content on demand

Usage:
    python3 scripts/skill_registry.py --list              # Print skill index to stdout
    python3 scripts/skill_registry.py --view build-agent-brief  # Print full skill
    python3 scripts/skill_registry.py --rebuild           # Rebuild registry cache only
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO / "skills" / "trevor"
REGISTRY_PATH = REPO / "skills" / "registry.json"


def parse_skill_md(path: pathlib.Path) -> dict | None:
    """Extract frontmatter + sections from a SKILL.md file."""
    content = path.read_text(encoding="utf-8")
    
    # Parse YAML-like frontmatter between --- markers
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
    if not fm_match:
        return None
    
    raw_fm = fm_match.group(1)
    body = fm_match.group(2).strip()
    
    # Parse frontmatter into dict
    frontmatter = {}
    for line in raw_fm.split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            # Handle lists
            if val.startswith("["):
                try:
                    val = json.loads(val)
                except:
                    val = [v.strip().strip("'\"") for v in val.strip("[]").split(",")]
            frontmatter[key] = val
    
    # Parse sections from body
    sections = {}
    current_section = "lead"
    current_lines = []
    for line in body.split("\n"):
        if line.startswith("## "):
            if current_lines:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections[current_section] = "\n".join(current_lines).strip()
    
    return {
        "path": str(path.relative_to(SKILLS_DIR)),
        "name": frontmatter.get("name", path.stem),
        "description": frontmatter.get("description", ""),
        "version": frontmatter.get("version", "1.0.0"),
        "tags": frontmatter.get("tags", []),
        "author": frontmatter.get("author", ""),
        "created": frontmatter.get("created", ""),
        "triggers": frontmatter.get("triggers", []),
        "sections": sections,
        "full_content": body,
        "char_count": len(body),
    }


def build_registry():
    """Scan skills/trevor/ and build the registry index."""
    skills = []
    for md_file in sorted(SKILLS_DIR.rglob("*.md")):
        # Skip non-SKILL.md files (migration notes, readmes, etc.)
        if md_file.stat().st_size == 0:
            continue
        parsed = parse_skill_md(md_file)
        if parsed:
            skills.append(parsed)
    
    registry = {
        "schema": "https://trevormentis.spec/skill-registry/v1",
        "generated": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "skill_count": len(skills),
        "categories": sorted(set(
            t for s in skills for t in (s.get("tags", []) if isinstance(s.get("tags"), list) else [s.get("tags", "")])
        )),
        "skills": skills,
    }
    return registry


def rebuild_cache():
    """Rebuild the registry JSON cache file."""
    registry = build_registry()
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2))
    print(f"[registry] Cached {registry['skill_count']} skills to {REGISTRY_PATH}")
    return registry


def skills_list() -> str:
    """Progressive disclosure Level 0: lightweight index of all skills."""
    if REGISTRY_PATH.exists():
        registry = json.loads(REGISTRY_PATH.read_text())
    else:
        registry = build_registry()
    
    lines = [f"📚 Skills Registry — {registry['skill_count']} skills loaded"]
    lines.append(f"   Categories: {', '.join(registry['categories'])}")
    lines.append("")
    
    for skill in registry["skills"]:
        tags = ", ".join(skill.get("tags", [])[:3]) if skill.get("tags") else ""
        tag_str = f" [{tags}]" if tags else ""
        lines.append(f"   /{skill['name']}{tag_str}")
        lines.append(f"   → {skill['description'][:100]}")
        lines.append("")
    
    return "\n".join(lines)


def skill_view(name: str) -> str:
    """Progressive disclosure Level 1: full content of a specific skill."""
    if REGISTRY_PATH.exists():
        registry = json.loads(REGISTRY_PATH.read_text())
    else:
        registry = build_registry()
    
    for skill in registry["skills"]:
        if skill["name"] == name:
            lines = [
                f"# {skill['name']} v{skill['version']}",
                f"**{skill['description']}**",
                f"Tags: {', '.join(skill.get('tags', [])) if isinstance(skill.get('tags'), list) else skill.get('tags', '')}",
                f"Author: {skill.get('author', 'Trevor')}",
                f"Chars: {skill['char_count']}",
                "",
                skill["full_content"],
            ]
            return "\n".join(lines)
    
    return f"⚠️ Skill '{name}' not found. Use --list to see available skills."


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Skill registry for Trevor")
    parser.add_argument("--list", action="store_true", help="Print skill index")
    parser.add_argument("--view", type=str, default=None, help="View a specific skill")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild registry cache")
    args = parser.parse_args()
    
    if args.rebuild:
        rebuild_cache()
        return 0
    
    if args.list:
        print(skills_list())
        return 0
    
    if args.view:
        print(skill_view(args.view))
        return 0
    
    # Default: rebuild + print list
    rebuild_cache()
    print()
    print(skills_list())
    return 0


if __name__ == "__main__":
    sys.exit(main())
