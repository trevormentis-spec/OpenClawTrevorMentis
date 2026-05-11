#!/usr/bin/env python3
"""
trevor_skills.py — Procedural memory system for Trevor.

Hermes-inspired skills with progressive disclosure.
Portable SKILL.md format that lives alongside the DailyIntel pipeline.

Usage:
    from trevor_skills import SkillRegistry
    registry = SkillRegistry()
    registry.list()         # Level 0: index
    registry.view("name")   # Level 1: full content
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent / "skills"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)


class SkillRegistry:
    """Procedural memory with progressive disclosure."""

    def __init__(self):
        self.skills_dir = SKILLS_DIR
        self._cache = None

    def _scan(self) -> list[dict]:
        """Scan skills directory and parse SKILL.md files."""
        skills = []
        for md_file in sorted(self.skills_dir.rglob("*.md")):
            if md_file.stat().st_size == 0:
                continue
            content = md_file.read_text(encoding="utf-8")
            fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL)
            if fm_match:
                raw_fm = fm_match.group(1)
                body = fm_match.group(2).strip()
                frontmatter = {}
                for line in raw_fm.split("\n"):
                    if ":" in line:
                        key, _, val = line.partition(":")
                        frontmatter[key.strip()] = val.strip()
                skills.append({
                    "name": frontmatter.get("name", md_file.stem),
                    "description": frontmatter.get("description", "")[:120],
                    "version": frontmatter.get("version", "1.0.0"),
                    "tags": frontmatter.get("tags", ""),
                    "path": str(md_file.relative_to(self.skills_dir)),
                    "content": body,
                    "char_count": len(body),
                })
            else:
                # Plain markdown without frontmatter, use filename as name
                skills.append({
                    "name": md_file.stem,
                    "description": "",
                    "version": "1.0.0",
                    "tags": "",
                    "path": str(md_file.relative_to(self.skills_dir)),
                    "content": content,
                    "char_count": len(content),
                })
        return skills

    def list(self) -> list[dict]:
        """Level 0: lightweight index of all skills."""
        if self._cache is None:
            self._cache = self._scan()
        return [{"name": s["name"], "description": s["description"],
                 "version": s["version"], "tags": s["tags"]}
                for s in self._cache]

    def view(self, name: str) -> str | None:
        """Level 1: full content of a specific skill."""
        if self._cache is None:
            self._cache = self._scan()
        for skill in self._cache:
            if skill["name"] == name:
                return skill["content"]
        return None

    def count(self) -> int:
        """Number of registered skills."""
        if self._cache is None:
            self._cache = self._scan()
        return len(self._cache)
