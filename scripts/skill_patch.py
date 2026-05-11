#!/usr/bin/env python3
"""
skill_patch.py — Skill evolution loop for Trevor.

Token-efficient skill editing using old_string/new_string pattern matching
(Hermes-inspired). Combined with nudge_check, this creates a real learning loop:
use skill → notice issue → patch skill → next use is better.

Usage:
    python3 scripts/skill_patch.py --list                    # List all skills
    python3 scripts/skill_patch.py --view <name>             # View full skill
    python3 scripts/skill_patch.py --patch <name> <old> <new>  # Patch a skill
    python3 scripts/skill_patch.py --create <name> <content>    # Create new skill
    python3 scripts/skill_patch.py --delete <name>              # Delete a skill
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import sys
import datetime

REPO = pathlib.Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO / "skills" / "trevor"
REGISTRY_PATH = REPO / "skills" / "registry.json"


def log(msg):
    print(f"[skill] {msg}", file=sys.stderr)


def find_skill_file(name: str) -> pathlib.Path | None:
    """Find a skill by name in the skills directory."""
    for f in SKILLS_DIR.rglob("*.md"):
        if f.stem == name or f.stem.replace("-", "") == name.replace("-", ""):
            return f
    return None


def skill_list() -> list[dict]:
    """List all skills with metadata."""
    if REGISTRY_PATH.exists():
        registry = json.loads(REGISTRY_PATH.read_text())
        return registry.get("skills", [])
    
    skills = []
    for f in sorted(SKILLS_DIR.rglob("*.md")):
        skills.append({"name": f.stem, "path": str(f.relative_to(REPO))})
    return skills


def skill_patch(name: str, old_text: str, new_text: str) -> dict:
    """
    Patch a skill using old_string/new_string replacement.
    Returns dict with success status and match info.
    """
    skill_file = find_skill_file(name)
    if not skill_file:
        return {"success": False, "error": f"Skill '{name}' not found"}
    
    content = skill_file.read_text(encoding="utf-8")
    
    # Count occurrences of old_text
    count = content.count(old_text)
    
    if count == 0:
        return {"success": False, "error": f"Text not found in skill '{name}'"}
    
    if count > 1:
        return {"success": False, "error": f"Text matches {count} times — need more specific match"}
    
    # Do the replacement
    new_content = content.replace(old_text, new_text)
    skill_file.write_text(new_content, encoding="utf-8")
    
    # Rebuild registry
    try:
        import subprocess
        subprocess.run([sys.executable, str(REPO / "scripts" / "skill_registry.py"), "--rebuild"],
                      capture_output=True, timeout=10)
    except:
        pass
    
    return {
        "success": True,
        "skill": name,
        "file": str(skill_file.relative_to(REPO)),
        "old_text_length": len(old_text),
        "new_text_length": len(new_text),
    }


def skill_create(name: str, content: str) -> dict:
    """Create a new skill."""
    # Clean name
    safe_name = re.sub(r'[^a-z0-9-]', '', name.lower().replace(" ", "-"))
    skill_path = SKILLS_DIR / f"{safe_name}.md"
    
    if skill_path.exists():
        return {"success": False, "error": f"Skill '{safe_name}' already exists"}
    
    # If content doesn't have frontmatter, add a minimal template
    if not content.startswith("---"):
        content = f"""---
name: {safe_name}
description: Auto-created skill
version: 1.0.0
author: Trevor
created: {datetime.date.today().isoformat()}
tags: []
---

{content}
"""
    
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(content, encoding="utf-8")
    
    # Rebuild registry
    try:
        import subprocess
        subprocess.run([sys.executable, str(REPO / "scripts" / "skill_registry.py"), "--rebuild"],
                      capture_output=True, timeout=10)
    except:
        pass
    
    log(f"Created: {skill_path}")
    return {"success": True, "skill": safe_name, "file": str(skill_path.relative_to(REPO))}


def skill_delete(name: str) -> dict:
    """Delete a skill."""
    skill_file = find_skill_file(name)
    if not skill_file:
        return {"success": False, "error": f"Skill '{name}' not found"}
    
    skill_file.unlink()
    
    # Rebuild registry
    try:
        import subprocess
        subprocess.run([sys.executable, str(REPO / "scripts" / "skill_registry.py"), "--rebuild"],
                      capture_output=True, timeout=10)
    except:
        pass
    
    log(f"Deleted: {skill_file}")
    return {"success": True, "skill": name}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Skill evolution for Trevor")
    parser.add_argument("--list", action="store_true", help="List all skills")
    parser.add_argument("--view", type=str, default=None, help="View a skill")
    parser.add_argument("--patch", nargs=3, metavar=("NAME", "OLD", "NEW"),
                       help="Patch a skill: old_string → new_string")
    parser.add_argument("--create", nargs=2, metavar=("NAME", "CONTENT_FILE"),
                       help="Create a new skill (content from file or inline)")
    parser.add_argument("--delete", type=str, default=None, help="Delete a skill")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    if args.list:
        skills = skill_list()
        if args.json:
            print(json.dumps(skills, indent=2))
        else:
            print(f"📚 Skills ({len(skills)}):")
            for s in skills:
                print(f"  /{s['name']}  —  {s.get('path', s.get('description', ''))}")
        return 0
    
    if args.view:
        skill_file = find_skill_file(args.view)
        if not skill_file:
            print(f"⚠️  Skill '{args.view}' not found")
            return 1
        content = skill_file.read_text()
        if args.json:
            print(json.dumps({"name": args.view, "content": content}))
        else:
            print(content)
        return 0
    
    if args.patch:
        name, old_text, new_text = args.patch
        result = skill_patch(name, old_text, new_text)
        if args.json:
            print(json.dumps(result, indent=2))
        elif result["success"]:
            print(f"✅ Patched /{name} ({result['old_text_length']} → {result['new_text_length']} chars)")
        else:
            print(f"❌ {result['error']}")
        return 0 if result["success"] else 1
    
    if args.create:
        name, content_input = args.create
        # Content can be inline or a file path
        content_path = pathlib.Path(content_input)
        if content_path.exists():
            content = content_path.read_text()
        else:
            content = content_input
        result = skill_create(name, content)
        if args.json:
            print(json.dumps(result, indent=2))
        elif result["success"]:
            print(f"✅ Created /{result['skill']} at {result['file']}")
        else:
            print(f"❌ {result['error']}")
        return 0 if result["success"] else 1
    
    if args.delete:
        result = skill_delete(args.delete)
        if args.json:
            print(json.dumps(result, indent=2))
        elif result["success"]:
            print(f"✅ Deleted /{result['skill']}")
        else:
            print(f"❌ {result['error']}")
        return 0 if result["success"] else 1
    
    # Default: list
    skills = skill_list()
    print(f"📚 Skills ({len(skills)}):")
    for s in skills:
        print(f"  /{s['name']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
