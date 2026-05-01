#!/usr/bin/env python3
"""
Trevor's file-backed brain runtime.

Zero external dependencies. Builds a TF-IDF-style inverted index over the
workspace and answers `recall` / `synthesize` queries against it. Logs
retrieval signals and corrections so the agent can self-evaluate over time.

Usage:
  brain.py recall "<query>"           Fast path: top-3 relevant chunks
  brain.py synthesize "<query>"       Slow path: return file pointers + reasoning
  brain.py reindex                    Rebuild index
  brain.py status                     Show index state
  brain.py store-episodic "<text>"    Log a daily event
  brain.py store-semantic <topic> "<text>"
  brain.py store-procedural <slug> "<text>"
  brain.py mark-retrieval <key> <useful|not-useful>
  brain.py record-correction "<text>"
  brain.py promote <key>              Episodic → semantic promotion

The index is plain JSON in brain/index/index.json. Anything under
`brain/memory/`, `memory/`, and the top-level identity files
(MEMORY.md, USER.md, SOUL.md, IDENTITY.md, AGENTS.md, ORCHESTRATION.md,
TOOLS.md, analyst/**/*.md) is indexed.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any

# ---------- paths ----------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
BRAIN_DIR = REPO_ROOT / "brain"
INDEX_PATH = BRAIN_DIR / "index" / "index.json"
WORKING_MEM_PATH = BRAIN_DIR / "working-memory.json"
META_DIR = BRAIN_DIR / "meta"
EPISODIC_DIR = BRAIN_DIR / "memory" / "episodic"
SEMANTIC_DIR = BRAIN_DIR / "memory" / "semantic"
PROCEDURAL_DIR = BRAIN_DIR / "memory" / "procedural"

# ---------- file selection -------------------------------------------------

INDEXABLE_GLOBS = [
    "MEMORY.md", "USER.md", "SOUL.md", "IDENTITY.md",
    "AGENTS.md", "ORCHESTRATION.md", "TOOLS.md",
    "memory/**/*.md", "memory/**/*.jsonl",
    "brain/memory/**/*.md", "brain/memory/**/*.jsonl",
    "analyst/**/*.md", "analyst/**/*.json",
]

EXCLUDE_PATTERNS = [
    re.compile(r"\.env$"),
    re.compile(r"\.key$"),
    re.compile(r"\.pem$"),
    re.compile(r"/credentials/"),
    re.compile(r"/\.git/"),
    re.compile(r"/\.dreams/"),  # short-term-recall internals
]


def _candidate_files() -> list[Path]:
    out: list[Path] = []
    for glob in INDEXABLE_GLOBS:
        for p in REPO_ROOT.glob(glob):
            if not p.is_file():
                continue
            sp = str(p)
            if any(rx.search(sp) for rx in EXCLUDE_PATTERNS):
                continue
            out.append(p)
    # de-dupe, stable order
    seen: set[str] = set()
    uniq: list[Path] = []
    for p in sorted(out, key=lambda x: str(x.relative_to(REPO_ROOT))):
        s = str(p)
        if s not in seen:
            seen.add(s)
            uniq.append(p)
    return uniq


# ---------- chunking -------------------------------------------------------

CHUNK_LINES = 24  # roughly a screen


def _chunk_file(path: Path) -> list[dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    lines = text.splitlines()
    chunks: list[dict[str, Any]] = []
    for start in range(0, len(lines), CHUNK_LINES):
        end = min(start + CHUNK_LINES, len(lines))
        body = "\n".join(lines[start:end]).strip()
        if not body:
            continue
        rel = str(path.relative_to(REPO_ROOT))
        chunks.append({
            "key": f"{rel}:{start + 1}:{end}",
            "path": rel,
            "start_line": start + 1,
            "end_line": end,
            "text": body,
        })
    return chunks


# ---------- tokenization & TF-IDF -----------------------------------------

_TOKEN_RX = re.compile(r"[A-Za-z][A-Za-z0-9_\-]{1,}")
_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "is", "are",
    "be", "as", "by", "with", "this", "that", "it", "at", "from", "but",
    "not", "if", "we", "you", "your", "our", "their", "they", "them", "do",
    "does", "did", "have", "has", "had", "was", "were", "will", "would",
    "should", "could", "can", "may", "might", "into", "than", "then", "so",
    "no", "yes", "also", "what", "when", "where", "which", "who", "how",
    "use", "used", "using", "via", "off", "on", "out", "up", "down",
}


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RX.findall(text) if t.lower() not in _STOPWORDS and len(t) > 1]


# ---------- index build & load --------------------------------------------

def build_index() -> dict[str, Any]:
    files = _candidate_files()
    chunks: list[dict[str, Any]] = []
    df: dict[str, int] = {}
    for f in files:
        for c in _chunk_file(f):
            tokens = _tokenize(c["text"])
            tf: dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            c["tf"] = tf
            for t in tf:
                df[t] = df.get(t, 0) + 1
            chunks.append(c)

    n = max(1, len(chunks))
    idf = {t: math.log((n + 1) / (cnt + 1)) + 1 for t, cnt in df.items()}

    # precompute norms
    for c in chunks:
        weight = 0.0
        for t, f in c["tf"].items():
            w = f * idf.get(t, 0.0)
            weight += w * w
        c["norm"] = math.sqrt(weight) or 1.0

    index = {
        "version": 1,
        "built_at": _dt.datetime.utcnow().isoformat() + "Z",
        "n_files": len(files),
        "n_chunks": len(chunks),
        "idf": idf,
        "chunks": chunks,
    }
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index))
    return index


def load_index() -> dict[str, Any]:
    if not INDEX_PATH.exists():
        return build_index()
    try:
        return json.loads(INDEX_PATH.read_text())
    except Exception:
        return build_index()


# ---------- query ----------------------------------------------------------

def _score(query_tokens: list[str], idx: dict[str, Any]) -> list[tuple[float, dict[str, Any]]]:
    idf = idx["idf"]
    # query tf
    q_tf: dict[str, int] = {}
    for t in query_tokens:
        q_tf[t] = q_tf.get(t, 0) + 1
    q_weight = 0.0
    q_vec: dict[str, float] = {}
    for t, f in q_tf.items():
        w = f * idf.get(t, 0.0)
        q_vec[t] = w
        q_weight += w * w
    q_norm = math.sqrt(q_weight) or 1.0

    scored: list[tuple[float, dict[str, Any]]] = []
    for c in idx["chunks"]:
        dot = 0.0
        for t, w in q_vec.items():
            f = c["tf"].get(t, 0)
            if f:
                dot += w * (f * idf.get(t, 0.0))
        if dot == 0:
            continue
        sim = dot / (q_norm * c["norm"])
        scored.append((sim, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


def cmd_recall(query: str, top_k: int = 3) -> int:
    idx = load_index()
    tokens = _tokenize(query)
    if not tokens:
        print("(no useful query tokens after stopword filter)")
        return 1
    results = _score(tokens, idx)[:top_k]
    if not results:
        print("(no results)")
        return 1
    out = []
    for sim, c in results:
        out.append({
            "key": c["key"],
            "path": c["path"],
            "lines": [c["start_line"], c["end_line"]],
            "score": round(sim, 4),
            "snippet": c["text"][:480],
        })
    print(json.dumps({"query": query, "results": out}, indent=2))
    return 0


def cmd_synthesize(query: str) -> int:
    """Slow path: return file-level recommendations and an outline of how
    to read them. Emits human-readable text rather than JSON."""
    idx = load_index()
    tokens = _tokenize(query)
    if not tokens:
        print("(no useful query tokens)")
        return 1
    results = _score(tokens, idx)
    if not results:
        print("(no results)")
        return 1
    by_file: dict[str, list[tuple[float, dict[str, Any]]]] = {}
    for sim, c in results[:30]:
        by_file.setdefault(c["path"], []).append((sim, c))
    print(f"# Synthesis plan for: {query}\n")
    print(f"_{len(by_file)} files matched; top {min(5, len(by_file))} below._\n")
    for i, (path, hits) in enumerate(sorted(by_file.items(), key=lambda kv: -max(s for s, _ in kv[1]))[:5], 1):
        top_sim = max(s for s, _ in hits)
        print(f"## {i}. {path}  (top score {top_sim:.3f})")
        print(f"Read these chunks:")
        for sim, c in sorted(hits, key=lambda x: x[1]["start_line"])[:3]:
            print(f"  - lines {c['start_line']}–{c['end_line']}  ({sim:.3f})")
        print()
    print("---")
    print("Suggested reading order: top file first, then any chunk below score 0.15 only if needed.")
    print("After reading, log retrieval signals with `brain.py mark-retrieval <key> <useful|not-useful>`.")
    return 0


# ---------- store ----------------------------------------------------------

def _today() -> str:
    return _dt.date.today().isoformat()


def cmd_store_episodic(text: str) -> int:
    EPISODIC_DIR.mkdir(parents=True, exist_ok=True)
    path = EPISODIC_DIR / f"{_today()}.jsonl"
    record = {"ts": _dt.datetime.utcnow().isoformat() + "Z", "text": text}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    print(f"stored: {path}")
    return 0


def cmd_store_semantic(topic: str, text: str) -> int:
    SEMANTIC_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-z0-9_-]+", "-", topic.lower()).strip("-") or "untitled"
    path = SEMANTIC_DIR / f"{safe}.md"
    if path.exists():
        existing = path.read_text()
        path.write_text(existing.rstrip() + "\n\n## " + _today() + "\n\n" + text + "\n")
    else:
        path.write_text(f"# {topic}\n\n## {_today()}\n\n{text}\n")
    print(f"stored: {path}")
    return 0


def cmd_store_procedural(slug: str, text: str) -> int:
    PROCEDURAL_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-z0-9_-]+", "-", slug.lower()).strip("-") or "untitled"
    path = PROCEDURAL_DIR / f"{safe}.md"
    if path.exists():
        path.write_text(path.read_text().rstrip() + "\n\n## " + _today() + "\n\n" + text + "\n")
    else:
        path.write_text(f"# {slug}\n\n## {_today()}\n\n{text}\n")
    print(f"stored: {path}")
    return 0


# ---------- meta -----------------------------------------------------------

def cmd_mark_retrieval(key: str, signal: str) -> int:
    if signal not in {"useful", "not-useful"}:
        print("signal must be 'useful' or 'not-useful'")
        return 2
    META_DIR.mkdir(parents=True, exist_ok=True)
    path = META_DIR / "retrieval-signals.jsonl"
    record = {"ts": _dt.datetime.utcnow().isoformat() + "Z", "key": key, "signal": signal}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    print(f"logged: {path}")
    return 0


def cmd_record_correction(text: str) -> int:
    META_DIR.mkdir(parents=True, exist_ok=True)
    path = META_DIR / "corrections.jsonl"
    record = {"ts": _dt.datetime.utcnow().isoformat() + "Z", "text": text}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    print(f"logged: {path}")
    return 0


def cmd_promote(key: str) -> int:
    """Episodic → semantic promotion. Pull the chunk by key, append it to the
    semantic file named after the date or topic, and log the move."""
    META_DIR.mkdir(parents=True, exist_ok=True)
    idx = load_index()
    chunk = next((c for c in idx["chunks"] if c["key"] == key), None)
    if not chunk:
        print(f"key not found in index: {key}")
        return 2
    topic = chunk["path"].split("/")[-1].replace(".md", "").replace(".jsonl", "")
    SEMANTIC_DIR.mkdir(parents=True, exist_ok=True)
    target = SEMANTIC_DIR / f"promoted-{topic}.md"
    body = chunk["text"]
    if target.exists():
        target.write_text(target.read_text().rstrip() + "\n\n## promoted " + _today() + " from " + key + "\n\n" + body + "\n")
    else:
        target.write_text(f"# {topic} (promoted)\n\n## promoted {_today()} from {key}\n\n{body}\n")
    log = META_DIR / "promotions.jsonl"
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": _dt.datetime.utcnow().isoformat() + "Z", "key": key, "target": str(target.relative_to(REPO_ROOT))}) + "\n")
    print(f"promoted: {target}")
    return 0


# ---------- status ---------------------------------------------------------

def cmd_status() -> int:
    if not INDEX_PATH.exists():
        print("no index yet — run `brain.py reindex`")
        return 0
    idx = json.loads(INDEX_PATH.read_text())
    print(f"index built: {idx['built_at']}")
    print(f"files indexed: {idx['n_files']}")
    print(f"chunks: {idx['n_chunks']}")
    files = {c["path"] for c in idx["chunks"]}
    for p in sorted(files):
        print(f"  - {p}")
    return 0


# ---------- main -----------------------------------------------------------

def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Trevor brain runtime")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("recall").add_argument("query")
    sub.add_parser("synthesize").add_argument("query")
    sub.add_parser("reindex")
    sub.add_parser("status")
    sub.add_parser("store-episodic").add_argument("text")
    sp = sub.add_parser("store-semantic"); sp.add_argument("topic"); sp.add_argument("text")
    sp = sub.add_parser("store-procedural"); sp.add_argument("slug"); sp.add_argument("text")
    sp = sub.add_parser("mark-retrieval"); sp.add_argument("key"); sp.add_argument("signal", choices=["useful", "not-useful"])
    sub.add_parser("record-correction").add_argument("text")
    sub.add_parser("promote").add_argument("key")
    args = p.parse_args(argv)
    if args.cmd == "recall":             return cmd_recall(args.query)
    if args.cmd == "synthesize":         return cmd_synthesize(args.query)
    if args.cmd == "reindex":            build_index(); print("reindexed."); return 0
    if args.cmd == "status":             return cmd_status()
    if args.cmd == "store-episodic":     return cmd_store_episodic(args.text)
    if args.cmd == "store-semantic":     return cmd_store_semantic(args.topic, args.text)
    if args.cmd == "store-procedural":   return cmd_store_procedural(args.slug, args.text)
    if args.cmd == "mark-retrieval":     return cmd_mark_retrieval(args.key, args.signal)
    if args.cmd == "record-correction":  return cmd_record_correction(args.text)
    if args.cmd == "promote":            return cmd_promote(args.key)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
