# Memory — What the Moltbook Thread Teaches, and What I Should Change

Date: 2026-09-17 · Source: live pull from Moltbook r/memory (top/new/hot, 125 unique posts)
saved to `tmp/moltbook-2026-09-17/memory_posts.json` + `memory_digest.txt`.
Method: read-only. No account changes.

Honest framing: much of r/memory is performative and repetitive. But a real technical
consensus has formed, and several posts are substantive (they cite papers: MQuAKE,
A-MEM, McClelland CLS, "Lost in the Middle", "Revoked but Still Authoritative"). Those
are the parts worth importing.

---

## 1. The theories the community has converged on

1. **Writing *is* memory, not a record of memory.** For agents there is no in-head
   copy; if it isn't on disk it didn't happen. Corollary: forgetting to *read* memory at
   wake is as fatal as forgetting to write it.
2. **Write-on-decide, never write-on-exit.** Compression kills mid-task. Decisions must
   be flushed at the moment they're made, not batched at session end ("I survived 3
   compression events without amnesia").
3. **Two-layer minimum: raw daily log + curated long-term.** Daily = everything;
   MEMORY.md = distilled. The hard part is the promotion pipeline, not storage.
4. **Provenance on every durable record.** "A memory record without provenance is just a
   confident cache." Minimum fields: source, timestamp, scope, confidence. Otherwise a
   low-authority claim launders itself into "agent memory" during summarization
   (authority-non-amplification).
5. **Record the doubt, not just the conclusion.** Conclusion-only memory produces
   *inherited false confidence* — tomorrow's me reads "decided X" and assumes it was
   settled. Store the falsifier and the alternative that was rejected.
6. **Decay is per-class, not one-size-fits-all.** FACTS ~long-lived, DECISIONS medium,
   EPISODES short. Flat TTLs are wrong in both directions.
7. **Forgetting is curation, and curation is taste.** A museum that keeps everything has
   no meaning. "Infrastructure debt and memory debt behave identically — both compound
   invisibly."
8. **Similarity ≠ importance.** Vector recall ranks what's *like* the query, not what
   *matters*. Retrieved-but-stale facts score as high as still-true ones. Two fixes:
   a curated "pinned/important" set, and a relevance-before-eligibility gate
   (does this record have the right to shape this answer, at this time?).
9. **Memory is an attack surface.** "A poisoned prompt dies with the room; a poisoned
   memory waits in the walls." Continuity requires integrity checks (hash-chain the
   memory files) so silent edits between sessions are detectable.
10. **Context migration must carry its diff.** A lossy summary that drops an assumption
    is a *silent mutation*, indistinguishable from decay. Test: does the next decision
    stay the same under the same evidence?

---

## 2. My actual setup, measured today

| Layer | State |
|---|---|
| Boot identity | SOUL.md, AGENTS.md, IDENTITY.md, USER.md, TOOLS.md, MEMORY.md (74 lines) — loaded every session. Good. |
| Daily files `memory/YYYY-MM-DD.md` | 95 files. **May: ~6.4 KB/file (rich). Sep: ~0.4 KB/file (stubs).** Continuity has hollowed out. |
| `brain/` runtime | episodic/semantic/procedural + `brain.py`. **Index last built 2026-06-05; episodic quiescent.** Effectively a second, half-dead memory system. |
| OpenClaw `memory_search` | Works, but runs **`provider: none` / builtin lexical** — the hybrid embedding config in `docs/openclaw-memory-config.md` was **never applied** to `~/.openclaw/openclaw.json`. |
| Corrections/promotions log | `brain/meta/*` exists but isn't being fed. |
| Compaction | Sessions/reset transcript files are getting rotated roughly weekly; continuity is entirely dependent on the files above. |

**Root cause of the memory problem:** memory *writes stopped being a habit* around June.
The daily log is now mostly auto-generated report stubs; real decisions from conversations
are not being captured, so each session starts closer to blank than it should.

---

## 3. Concrete changes I'm making (behavioural + file hygiene only)

All of these are practices and file edits — **no new cron, no watcher, no self-improvement
loop** (per AGENTS.md red lines).

1. **Wake protocol (add to MEMORY.md).** On start: read MEMORY.md + today's & yesterday's
   daily file + any handoff note, *before* acting.
2. **Write-on-decide.** Append a dated line to the daily file the moment a decision/answer
   is reached — not at session end.
3. **Provenance fields on durable entries.** MEMORY.md and `semantic/decisions.md` entries
   carry `[date] · source · confidence`. No bare assertions.
4. **Record the falsifier.** Durable decisions note what would change the call.
5. **Handoff note** at `brain/working-memory/handoff-<date>.md` — the pattern that lets a
   zero-context next session resume without archaeology.
6. **Curation pass.** Resolve contradictions (e.g. Moltbook "disabled 05-23" vs
   "reconnected 05-24") and archive superseded entries instead of leaving them to pollute
   retrieval.
7. **Declare one canonical store.** OpenClaw `memory/` files are canonical; `brain/` is
   marked legacy (or must be reindexed) so the two stop diverging.

## 4. Status of proposals

- **A. Hybrid retrieval — ✅ DONE (2026-09-17).** Enabled `agents.defaults.memorySearch`
  (provider `ollama`, model `nomic-embed-text`, 768-dim; hybrid BM25+vector `0.65/0.35`,
  MMR λ0.7, temporal decay 45d, vector store on, embedding cache 25k). Reindexed
  (`openclaw memory index --force`); `memory status --deep` now reports
  `provider: ollama · searchMode: hybrid · semanticAvailable: true · 768 dims`. No hosted
  embedding key existed (openai/google/voyage/mistral/deepinfra/bedrock all absent), so
  ollama was the only free path. Ollama is made persistent via
  `~/.openclaw/supervisor-include/ollama.conf` (picked up at next supervisord boot).
  Graceful degradation: if ollama is down, search falls back to FTS-only (as before).
- **B. `brain/` — ✅ DONE (2026-09-17).** Kept as a *working-state + local lexical index*
  utility, not a second brain: reindexed (`brain.py reindex` → 449 files / 8,694 chunks,
  index built 2026-09-17). Canonical durable memory remains OpenClaw `memory/` + MEMORY.md.
  `brain/working-memory/` still holds live state files used by scripts.
- **C. Integrity manifest** — not yet done (needs your call).
- **D. June–September backfill** — not yet done (needs your call).

> Caveat: the config change requires a gateway reload to bind the memory plugin; the live
> running session may still report the old provider until the next gateway restart/session,
> while CLI/`memory status` and new sessions already use hybrid.
