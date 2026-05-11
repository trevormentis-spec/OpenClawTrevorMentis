#!/usr/bin/env python3
"""
index_memory.py — Index assessment markdowns into FTS5 memory store.
Replaces the old Chroma + sentence-transformers indexer.

Usage:
  python3 memory/index_memory.py                     # index all assessments
  python3 memory/index_memory.py --rebuild            # clear and re-index
"""
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from trevor_memory import MemoryStore
from trevor_config import THEATRES, THEATRE_KEYS
from trevor_log import get_logger

ASSESS_DIR = SKILL_ROOT / 'assessments'
log = get_logger("index_memory")


def index_all(rebuild=False):
    """Index all assessment markdowns into FTS5 memory store."""
    mem = MemoryStore()
    
    if rebuild:
        log.info("Rebuilding memory store")
        # Drop and recreate
        import os as _os
        db_path = mem.db_path
        mem.close()
        if db_path.exists():
            db_path.unlink()
        mem = MemoryStore()
    
    count = 0
    # Index assessments
    for theatre in THEATRES:
        key = theatre["key"]
        path = ASSESS_DIR / f"{key}.md"
        if path.exists():
            content = path.read_text(encoding="utf-8")
            mem.index(
                collection="narrative",
                content=content[:5000],  # cap at 5K chars per assessment
                key=f"assessment_{key}",
                source="daily_intel_assessment",
                region=key,
                confidence=0.8,
                metadata={"path": str(path), "title": theatre["title"]},
            )
            count += 1
            log.info(f"Indexed {key}", chars=len(content[:5000]))
    
    # Also index previous assessment files (historical)
    for f in sorted(ASSESS_DIR.glob("*.md")):
        region = f.stem
        if region in THEATRE_KEYS:
            continue  # already indexed above
        if region == "exec_summary":
            content = f.read_text(encoding="utf-8")
            mem.index(
                collection="narrative",
                content=content[:5000],
                key="exec_summary",
                source="daily_intel_assessment",
                region="executive",
                confidence=0.7,
            )
            count += 1
    
    total = mem.count("narrative")
    log.info(f"Indexing complete", new=count, total=total)
    mem.close()
    return count


if __name__ == "__main__":
    rebuild = "--rebuild" in sys.argv
    index_all(rebuild)
