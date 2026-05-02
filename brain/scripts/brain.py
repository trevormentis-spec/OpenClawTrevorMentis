#!/usr/bin/env python3
"""Trevor's file-backed brain runtime.

Builds a compact TF-IDF index for recall/synthesis. Source files remain the
authoritative memory; index.json stores only metadata, token weights, previews,
and a manifest used for automatic stale-index detection.
"""
from __future__ import annotations

import argparse, datetime as dt, hashlib, json, math, re, subprocess, sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BRAIN = ROOT / "brain"
INDEX = BRAIN / "index" / "index.json"
META = BRAIN / "meta"
EPISODIC = BRAIN / "memory" / "episodic"
SEMANTIC = BRAIN / "memory" / "semantic"
PROCEDURAL = BRAIN / "memory" / "procedural"

VERSION = 2
MAX_LINES = 40
OVERLAP = 6
PREVIEW = 360
EPISODIC_HALF_LIFE_DAYS = 45.0
SIGNAL_HALF_LIFE_DAYS = 90.0

INDEXABLE_GLOBS = [
    "MEMORY.md", "USER.md", "SOUL.md", "IDENTITY.md", "AGENTS.md",
    "ORCHESTRATION.md", "TOOLS.md", "memory/**/*.md", "memory/**/*.jsonl",
    "brain/memory/**/*.md", "brain/memory/**/*.jsonl", "analyst/**/*.md",
    "analyst/**/*.json",
]
EXCLUDES = [re.compile(p) for p in [r"\.env$", r"\.key$", r"\.pem$", r"/credentials/", r"/\.git/", r"/\.dreams/"]]
SOURCE_WEIGHTS = [
    ("MEMORY.md", 1.35), ("brain/memory/semantic/", 1.30),
    ("brain/memory/procedural/", 1.20), ("ORCHESTRATION.md", 1.25),
    ("AGENTS.md", 1.15), ("memory/", 1.00),
    ("brain/memory/episodic/", 0.95), ("analyst/", 0.80),
]
TOKEN_RX = re.compile(r"[A-Za-z][A-Za-z0-9_\-]{1,}")
STOP = set("""the a an and or of to in on for is are be as by with this that it at from but not if we you your our their they them do does did have has had was were will would should could can may might into than then so no yes also what when where which who how use used using via off out up down""".split())


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


def utc_stamp() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def rel(p: Path) -> str: return p.relative_to(ROOT).as_posix()


def git_ignored(r: str) -> bool:
    try:
        return subprocess.run(["git", "check-ignore", "-q", "--", r], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    except Exception:
        return False


def excluded(p: Path) -> bool:
    r = rel(p); sp = "/" + r
    return any(rx.search(sp) for rx in EXCLUDES) or git_ignored(r)


def candidates() -> list[Path]:
    out: list[Path] = []
    for g in INDEXABLE_GLOBS:
        out += [p for p in ROOT.glob(g) if p.is_file() and not excluded(p)]
    seen, uniq = set(), []
    for p in sorted(out, key=rel):
        s = str(p.resolve())
        if s not in seen:
            seen.add(s); uniq.append(p)
    return uniq


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""): h.update(b)
    return h.hexdigest()


def manifest(files: list[Path]) -> dict[str, dict[str, Any]]:
    m = {}
    for p in files:
        try:
            s = p.stat(); m[rel(p)] = {"mtime_ns": s.st_mtime_ns, "size": s.st_size, "sha256": sha256(p)}
        except OSError: pass
    return m


def manifest_matches(idx: dict[str, Any]) -> bool:
    return idx.get("version") == VERSION and idx.get("manifest") == manifest(candidates())


def windows(start: int, end: int) -> list[tuple[int, int]]:
    out, i = [], start
    while i < end:
        j = min(i + MAX_LINES, end); out.append((i + 1, j))
        if j >= end: break
        i = max(j - OVERLAP, i + 1)
    return out


def md_sections(lines: list[str]) -> list[tuple[int, int]]:
    """Return heading-aware sections, merging heading-only stubs forward.

    Markdown often has a top-level title followed immediately by a subsection,
    or a parent heading followed immediately by child headings. Indexing those
    heading-only stubs creates high-scoring chunks with almost no useful memory
    content, so we merge them into the next meaningful section.
    """
    hs = [i for i, line in enumerate(lines) if re.match(r"^#{1,6}\s+", line)]
    if not hs:
        return [(0, len(lines))]

    raw: list[tuple[int, int]] = []
    if hs[0] > 0:
        raw.append((0, hs[0]))
    raw.extend((s, hs[i + 1] if i + 1 < len(hs) else len(lines)) for i, s in enumerate(hs))

    def has_body(s: int, e: int) -> bool:
        return any(line.strip() and not re.match(r"^#{1,6}\s+", line) for line in lines[s:e])

    merged: list[tuple[int, int]] = []
    pending_start: int | None = None
    for s, e in raw:
        if pending_start is not None:
            s = pending_start
            pending_start = None
        if not has_body(s, e) and e < len(lines):
            pending_start = s
            continue
        merged.append((s, e))
    if pending_start is not None:
        merged.append((pending_start, len(lines)))
    return merged


def read_lines(path: str, a: int, b: int) -> str:
    p = ROOT / path
    if not p.is_file() or excluded(p): return ""
    try: lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception: return ""
    return "\n".join(lines[a - 1:b]).strip()


def chunk_file(p: Path) -> list[dict[str, Any]]:
    try: lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception: return []
    if not lines: return []
    r, chunks = rel(p), []
    spans = md_sections(lines) if p.suffix.lower() == ".md" else [(0, len(lines))]
    for s, e in spans:
        for a, b in windows(s, e):
            body = "\n".join(lines[a - 1:b]).strip()
            if body: chunks.append({"key": f"{r}:{a}:{b}", "path": r, "start_line": a, "end_line": b, "preview": body[:PREVIEW]})
    return chunks


def toks(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RX.findall(text) if t.lower() not in STOP and len(t) > 1]


def build_index() -> dict[str, Any]:
    files, chunks, df = candidates(), [], {}
    for f in files:
        for c in chunk_file(f):
            tf = {}
            for t in toks(read_lines(c["path"], c["start_line"], c["end_line"])): tf[t] = tf.get(t, 0) + 1
            c["tf"] = tf
            for t in tf: df[t] = df.get(t, 0) + 1
            chunks.append(c)
    n = max(1, len(chunks)); idf = {t: math.log((n + 1) / (c + 1)) + 1 for t, c in df.items()}
    for c in chunks:
        c["norm"] = math.sqrt(sum((f * idf.get(t, 0.0)) ** 2 for t, f in c["tf"].items())) or 1.0
    idx = {"version": VERSION, "built_at": utc_stamp(), "n_files": len(files), "n_chunks": len(chunks), "manifest": manifest(files), "idf": idf, "chunks": chunks}
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps(idx, separators=(",", ":")), encoding="utf-8")
    return idx


def load_index() -> dict[str, Any]:
    if not INDEX.exists(): return build_index()
    try: idx = json.loads(INDEX.read_text(encoding="utf-8"))
    except Exception: return build_index()
    return idx if manifest_matches(idx) else build_index()


def source_weight(path: str) -> float:
    for prefix, w in SOURCE_WEIGHTS:
        if path == prefix or path.startswith(prefix): return w
    return 1.0


def date_from_path(path: str) -> dt.date | None:
    m = re.search(r"(20\d{2}-\d{2}-\d{2})", path)
    if not m: return None
    try: return dt.date.fromisoformat(m.group(1))
    except ValueError: return None


def recency_weight(path: str) -> float:
    if not (path.startswith("memory/") or path.startswith("brain/memory/episodic/")): return 1.0
    d = date_from_path(path)
    if not d: return 1.0
    return max(0.50, 0.5 ** (max(0, (dt.date.today() - d).days) / EPISODIC_HALF_LIFE_DAYS))


def signal_weights() -> dict[str, float]:
    p = META / "retrieval-signals.jsonl"
    if not p.exists(): return {}
    now, scores = utc_now(), {}
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try: rec = json.loads(line)
        except json.JSONDecodeError: continue
        key, sig = rec.get("key"), rec.get("signal")
        if not isinstance(key, str) or sig not in {"useful", "not-useful"}: continue
        age = 0.0
        try:
            then = dt.datetime.fromisoformat(str(rec.get("ts", "")).replace("Z", "+00:00"))
            if then.tzinfo is None:
                then = then.replace(tzinfo=dt.UTC)
            age = max(0.0, (now - then).total_seconds() / 86400.0)
        except ValueError: pass
        decay = 0.5 ** (age / SIGNAL_HALF_LIFE_DAYS)
        scores[key] = scores.get(key, 0.0) + (decay if sig == "useful" else -decay)
    return {k: (min(1.30, 1 + 0.10 * s) if s >= 0 else max(0.70, 1 + 0.15 * s)) for k, s in scores.items()}


def confidence(score: float) -> str:
    return "high" if score >= 0.18 else "medium" if score >= 0.10 else "low"


def score(qtokens: list[str], idx: dict[str, Any]) -> list[tuple[float, float, dict[str, Any]]]:
    idf, sigs, qtf, out = idx["idf"], signal_weights(), {}, []
    for t in qtokens: qtf[t] = qtf.get(t, 0) + 1
    qvec = {t: f * idf.get(t, 0.0) for t, f in qtf.items()}; qnorm = math.sqrt(sum(w * w for w in qvec.values())) or 1.0
    for c in idx["chunks"]:
        dot = sum(w * (c["tf"].get(t, 0) * idf.get(t, 0.0)) for t, w in qvec.items())
        if not dot: continue
        raw = dot / (qnorm * c["norm"])
        final = raw * source_weight(c["path"]) * recency_weight(c["path"]) * sigs.get(c["key"], 1.0)
        out.append((final, raw, c))
    return sorted(out, key=lambda x: x[0], reverse=True)


def cmd_recall(query: str, top_k: int = 3) -> int:
    qtokens = toks(query)
    if not qtokens:
        print(json.dumps({"query": query, "confidence": "none", "recommendation": "Use a more specific query.", "results": []}, indent=2)); return 1
    results = score(qtokens, load_index())[:top_k]
    if not results:
        print(json.dumps({"query": query, "confidence": "none", "recommendation": "No memory chunks matched; use synthesize or read files directly.", "results": []}, indent=2)); return 1
    top, conf = results[0][0], confidence(results[0][0])
    rows = [{"key": c["key"], "path": c["path"], "lines": [c["start_line"], c["end_line"]], "score": round(final, 4), "raw_score": round(raw, 4), "source_weight": source_weight(c["path"]), "recency_weight": round(recency_weight(c["path"]), 4), "snippet": c.get("preview", "")} for final, raw, c in results]
    print(json.dumps({"query": query, "top_score": round(top, 4), "confidence": conf, "recommendation": "Use fast-path results." if conf != "low" else "Low confidence: run `brain.py synthesize` or read source files before relying on this memory.", "results": rows}, indent=2)); return 0


def cmd_synthesize(query: str) -> int:
    qtokens = toks(query)
    if not qtokens: print("(no useful query tokens)"); return 1
    results = score(qtokens, load_index())
    if not results: print("(no results)"); return 1
    by_file: dict[str, list[tuple[float, float, dict[str, Any]]]] = {}
    for final, raw, c in results[:30]: by_file.setdefault(c["path"], []).append((final, raw, c))
    print(f"# Synthesis plan for: {query}\n\n_{len(by_file)} files matched; top {min(5, len(by_file))} below._\n")
    for i, (path, hits) in enumerate(sorted(by_file.items(), key=lambda kv: -max(s for s, _, _ in kv[1]))[:5], 1):
        top = max(s for s, _, _ in hits); print(f"## {i}. {path}  (top score {top:.3f}, confidence {confidence(top)})\nRead these chunks:")
        for final, raw, c in sorted(hits, key=lambda x: x[2]["start_line"])[:3]: print(f"  - lines {c['start_line']}-{c['end_line']}  (score {final:.3f}, raw {raw:.3f})")
        print()
    print("---\nSuggested reading order: top file first; log retrieval signals with `brain.py mark-retrieval <key> <useful|not-useful>`."); return 0


def today() -> str: return dt.date.today().isoformat()


def cmd_store_episodic(text: str) -> int:
    EPISODIC.mkdir(parents=True, exist_ok=True); p = EPISODIC / f"{today()}.jsonl"
    with p.open("a", encoding="utf-8") as f: f.write(json.dumps({"ts": utc_stamp(), "text": text}) + "\n")
    build_index(); print(f"stored: {p}\nreindexed."); return 0


def cmd_store_semantic(topic: str, text: str) -> int:
    SEMANTIC.mkdir(parents=True, exist_ok=True); safe = re.sub(r"[^a-z0-9_-]+", "-", topic.lower()).strip("-") or "untitled"; p = SEMANTIC / f"{safe}.md"
    body = (p.read_text(encoding="utf-8", errors="replace").rstrip() + "\n\n" if p.exists() else f"# {topic}\n\n") + f"## {today()}\n\n{text}\n"
    p.write_text(body, encoding="utf-8"); build_index(); print(f"stored: {p}\nreindexed."); return 0


def cmd_store_procedural(slug: str, text: str) -> int:
    PROCEDURAL.mkdir(parents=True, exist_ok=True); safe = re.sub(r"[^a-z0-9_-]+", "-", slug.lower()).strip("-") or "untitled"; p = PROCEDURAL / f"{safe}.md"
    body = (p.read_text(encoding="utf-8", errors="replace").rstrip() + "\n\n" if p.exists() else f"# {slug}\n\n") + f"## {today()}\n\n{text}\n"
    p.write_text(body, encoding="utf-8"); build_index(); print(f"stored: {p}\nreindexed."); return 0


def cmd_mark_retrieval(key: str, signal: str) -> int:
    META.mkdir(parents=True, exist_ok=True); p = META / "retrieval-signals.jsonl"
    with p.open("a", encoding="utf-8") as f: f.write(json.dumps({"ts": utc_stamp(), "key": key, "signal": signal}) + "\n")
    print(f"logged: {p}"); return 0


def cmd_record_correction(text: str) -> int:
    META.mkdir(parents=True, exist_ok=True); p = META / "corrections.jsonl"
    with p.open("a", encoding="utf-8") as f: f.write(json.dumps({"ts": utc_stamp(), "text": text}) + "\n")
    print(f"logged: {p}"); return 0


def cmd_promote(key: str) -> int:
    idx = load_index(); c = next((x for x in idx["chunks"] if x["key"] == key), None)
    if not c: print(f"key not found in index: {key}"); return 2
    body = read_lines(c["path"], c["start_line"], c["end_line"])
    if not body: print(f"could not read source chunk for key: {key}"); return 2
    SEMANTIC.mkdir(parents=True, exist_ok=True); META.mkdir(parents=True, exist_ok=True)
    topic = c["path"].split("/")[-1].replace(".md", "").replace(".jsonl", ""); target = SEMANTIC / f"promoted-{topic}.md"
    addition = f"## promoted {today()} from {key}\n\n{body}\n"
    target.write_text((target.read_text(encoding="utf-8", errors="replace").rstrip() + "\n\n" if target.exists() else f"# {topic} (promoted)\n\n") + addition, encoding="utf-8")
    with (META / "promotions.jsonl").open("a", encoding="utf-8") as f: f.write(json.dumps({"ts": utc_stamp(), "key": key, "target": rel(target)}) + "\n")
    build_index(); print(f"promoted: {target}\nreindexed."); return 0


def cmd_status() -> int:
    if not INDEX.exists(): print("no index yet - run `brain.py reindex`"); return 0
    idx = load_index(); print(f"index built: {idx['built_at']}\nindex version: {idx.get('version')}\nfiles indexed: {idx['n_files']}\nchunks: {idx['n_chunks']}")
    for p in sorted({c["path"] for c in idx["chunks"]}): print(f"  - {p}")
    return 0


def cmd_doctor() -> int:
    """Run a lightweight health check for Trevor's memory runtime."""
    checks: list[tuple[str, str, str]] = []

    def ok(name: str, detail: str = "") -> None:
        checks.append(("ok", name, detail))

    def warn(name: str, detail: str = "") -> None:
        checks.append(("warn", name, detail))

    def fail(name: str, detail: str = "") -> None:
        checks.append(("fail", name, detail))

    if (ROOT / ".git").exists(): ok("git repository", rel(ROOT / ".git"))
    else: warn("git repository", "workspace is not a git checkout")

    if BRAIN.exists(): ok("brain directory", rel(BRAIN))
    else: fail("brain directory", "brain/ is missing")

    for d in [META, EPISODIC, SEMANTIC, PROCEDURAL]:
        if d.exists(): ok(f"directory {rel(d)}")
        else: warn(f"directory {rel(d)}", "will be created when first written")

    files = candidates()
    if files: ok("indexable files", f"{len(files)} candidate files")
    else: fail("indexable files", "no files matched INDEXABLE_GLOBS")

    idx = load_index()
    if manifest_matches(idx): ok("index freshness", f"version {idx.get('version')} manifest matches")
    else: fail("index freshness", "manifest mismatch after load_index")

    if idx.get("n_chunks", 0) > 0: ok("chunks", f"{idx.get('n_chunks')} chunks indexed")
    else: fail("chunks", "index has no chunks")

    ignored_chunks = [c.get("path", "") for c in idx.get("chunks", []) if excluded(ROOT / c.get("path", ""))]
    if ignored_chunks: fail("ignored files excluded", ", ".join(sorted(set(ignored_chunks))[:5]))
    else: ok("ignored files excluded")

    tiny = []
    for c in idx.get("chunks", []):
        snippet = str(c.get("preview", ""))
        if len(toks(snippet)) < 3:
            tiny.append(c.get("key", "<unknown>"))
    if tiny: warn("tiny chunks", f"{len(tiny)} tiny chunks; sample: {tiny[0]}")
    else: ok("tiny chunks", "none detected")

    probes = [
        "Trevor routing memory",
        "durable decisions",
        "AgentMail email path",
        "analyst training program",
    ]
    for q in probes:
        hits = score(toks(q), idx)[:1]
        if not hits:
            warn(f"probe: {q}", "no results")
            continue
        top, _, chunk = hits[0]
        conf = confidence(top)
        detail = f"{conf} {top:.3f} -> {chunk['key']}"
        if conf == "low": warn(f"probe: {q}", detail)
        else: ok(f"probe: {q}", detail)

    print("# Trevor brain doctor\n")
    for status, name, detail in checks:
        icon = {"ok": "OK", "warn": "WARN", "fail": "FAIL"}[status]
        print(f"[{icon}] {name}" + (f" — {detail}" if detail else ""))

    fails = sum(1 for s, _, _ in checks if s == "fail")
    warns = sum(1 for s, _, _ in checks if s == "warn")
    print(f"\nSummary: {fails} fail(s), {warns} warning(s), {len(checks) - fails - warns} ok.")
    return 1 if fails else 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Trevor brain runtime"); sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("recall"); sp.add_argument("query"); sp.add_argument("--top-k", type=int, default=3)
    sub.add_parser("synthesize").add_argument("query"); sub.add_parser("reindex"); sub.add_parser("status"); sub.add_parser("doctor"); sub.add_parser("store-episodic").add_argument("text")
    sp = sub.add_parser("store-semantic"); sp.add_argument("topic"); sp.add_argument("text")
    sp = sub.add_parser("store-procedural"); sp.add_argument("slug"); sp.add_argument("text")
    sp = sub.add_parser("mark-retrieval"); sp.add_argument("key"); sp.add_argument("signal", choices=["useful", "not-useful"])
    sub.add_parser("record-correction").add_argument("text"); sub.add_parser("promote").add_argument("key")
    a = p.parse_args(argv)
    if a.cmd == "recall": return cmd_recall(a.query, a.top_k)
    if a.cmd == "synthesize": return cmd_synthesize(a.query)
    if a.cmd == "reindex": build_index(); print("reindexed."); return 0
    if a.cmd == "status": return cmd_status()
    if a.cmd == "doctor": return cmd_doctor()
    if a.cmd == "store-episodic": return cmd_store_episodic(a.text)
    if a.cmd == "store-semantic": return cmd_store_semantic(a.topic, a.text)
    if a.cmd == "store-procedural": return cmd_store_procedural(a.slug, a.text)
    if a.cmd == "mark-retrieval": return cmd_mark_retrieval(a.key, a.signal)
    if a.cmd == "record-correction": return cmd_record_correction(a.text)
    if a.cmd == "promote": return cmd_promote(a.key)
    return 1


if __name__ == "__main__": sys.exit(main(sys.argv[1:]))
