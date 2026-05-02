# Trevor Brain Memory Improvements

This update keeps the same `brain/scripts/brain.py` CLI but improves recall safety and relevance.

## What changed

- **Automatic stale-index detection:** `load_index()` compares the current memory/source manifest against the saved index manifest and rebuilds automatically when files changed.
- **Compact index:** `index.json` stores metadata, token frequencies, line ranges, and short previews instead of full memory text.
- **Heading-aware chunking:** Markdown files are split by heading sections before line windows are applied, with small overlap for continuity.
- **Layer/source weighting:** durable memory and operating rules are boosted; bulky training docs are downweighted.
- **Episodic recency decay:** daily and episodic notes fade over a 45-day half-life while semantic/procedural memory stays stable.
- **Retrieval-signal learning:** `mark-retrieval useful|not-useful` now affects future ranking with decaying influence.
- **Confidence output:** `recall` returns `high`, `medium`, or `low` confidence and tells Trevor when to fall back to `synthesize`.
- **Gitignore-aware indexing:** `git check-ignore` is used when available so ignored files stay out of the index.
- **Write-path reindexing:** store/promote commands rebuild the index after writing memory.

## Same commands

```bash
python3 brain/scripts/brain.py reindex
python3 brain/scripts/brain.py status
python3 brain/scripts/brain.py recall "routing memory"
python3 brain/scripts/brain.py synthesize "who is Trevor and what are the routing rules"
python3 brain/scripts/brain.py mark-retrieval MEMORY.md:1:24 useful
```

## Suggested validation after pulling/applying

```bash
python3 -m py_compile brain/scripts/brain.py
python3 brain/scripts/brain.py reindex
python3 brain/scripts/brain.py status
python3 brain/scripts/brain.py recall "Trevor routing memory"
```
