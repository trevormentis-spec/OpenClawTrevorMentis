#!/usr/bin/env python3
"""Retrieve top-k relevant chunks from FTS5 memory store.

Usage:
  python3 memory/retrieve.py <query>
  python3 memory/retrieve.py <query> --collection narrative --top-k 5
"""
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from trevor_memory import MemoryStore
from trevor_log import get_logger

log = get_logger("retrieve")


def retrieve(query: str, collection: str | None = None, region: str | None = None, top_k: int = 3):
    """Retrieve from FTS5 memory store."""
    mem = MemoryStore()
    try:
        results = mem.search(query, collection=collection, region=region, top_k=top_k)
        log.info(f"Search for '{query}'", results=len(results), collection=collection or "all")
        return results
    except Exception as e:
        log.error(f"Search failed: {e}")
        return []
    finally:
        mem.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Retrieve from FTS5 memory")
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--top-k", type=int, default=3, help="Number of results (default: 3)")
    parser.add_argument("--collection", type=str, default=None, help="Filter by collection")
    parser.add_argument("--region", type=str, default=None, help="Filter by region")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    results = retrieve(args.query, collection=args.collection, region=args.region, top_k=args.top_k)
    
    if args.json:
        import json
        print(json.dumps(results, indent=2))
    else:
        print(f"\n📚 Memory results for: '{args.query}'")
        print(f"{'='*50}")
        for i, r in enumerate(results, 1):
            print(f"\n[{i}] {r.get('collection','?')}/{r.get('region','?')}  (relevance: {r.get('relevance',0):.2f})")
            print(f"    {r.get('content','')[:200]}...")
            print(f"    {r.get('created_at','')}")
