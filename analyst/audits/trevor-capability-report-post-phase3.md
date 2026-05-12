# Trevor Capability Report — Post Phase 3

**Date:** 2026-05-11 23:20 UTC
**Audit:** Operational reality only. No TODOs, no aspirations.

---

## Executive Summary

Trevor improved in **infrastructure** today — not in behavior. The pipeline has better logging, lighter dependencies, configurable paths, and FTS5 memory. But the **behavioral loop is still open**: memory is written, nobody reads it yet in production. The pipeline is better engineered. It is not yet more intelligent.

**Scores:**
| Category | Before | After | Change |
|----------|--------|-------|--------|
| Runtime stability | 35/100 | 55/100 | +20 |
| Portability | 20/100 | 35/100 | +15 |
| Memory persistence | 20/100 | 20/100 | 0 |
| Adaptive behavior | 5/100 | 15/100 | +10 |
| Observability | 10/100 | 30/100 | +20 |
| Resilience | 15/100 | 30/100 | +15 |
| Publication quality | 60/100 | 60/100 | 0 |
| Operational coherence | 25/100 | 40/100 | +15 |

**Weighted overall:** 36/100 (was 24/100 before today)

---

## What Trevor Can Now Do That It Could Not Do Before

**Operational changes only:**

1. **FTS5 memory (existed before, was Chroma).** FTS5 replaced Chroma + sentence-transformers. The FTS5 store is currently empty (0 entries), same as before when it was Chroma. The replacement is lighter and faster, but functionally identical: nothing is retrieved because nothing is indexed.

2. **Configurable paths (was hardcoded).** 28 hardcoded paths replaced with `trevor_config.py` env var overrides. If someone deploys Trevor to a different filesystem layout, they can set `TREVOR_WORKSPACE=/custom/path` instead of editing 11 files.

3. **Structured logging (was print statements).** `trevor_log.py` writes JSON log entries with timestamps, levels, logger names, and structured fields. Before: `print(f"  Retry: {error}", file=sys.stderr)`. After: `log.warning("Retry", error=error, attempt=n)`. File output persists. Heartbeat telemetry exists.

4. **Auto-repair registry (did not exist).** `quality_audit.py` now has `REPAIR_REGISTRY` — registered functions for missing assessments, stale memory, missing fonts, and stale Kalshi data. When triggered, they call subprocesses to regenerate assets. Before: quality_audit logged issues and did nothing.

5. **Plain-text fallback (did not exist).** If reportlab raises an exception during PDF generation, `build_pdf.py` now produces a `.txt` file with the assessment content. Before: pipeline errored, no output. After: pipeline produces a degraded (but usable) text brief.

6. **Runtime dashboard (did not exist).** `trevor_dashboard.py` aggregates health, memory, cost, diagnostics, and skills into a single report. Trevor can now answer "what is the state of the system?" with one command.

7. **RSS feed fetching (did not exist).** `daily_enrichment.py` now fetches 9 real RSS feeds (BBC, Reuters, AP, Al Jazeera, etc.) and classifies articles to theatres. Before: the file listed 27 sources with no fetch logic for any of them.

8. **Memory-conditioned prompt scaffolding (did not exist).** `generate_assessments.py` now retrieves prior narratives, KJs, unresolved questions, and trade theses from FTS5 before each assessment. The retrieval path exists in code. It returns nothing because the store is empty — but the code path is operational.

**Total genuinely new operational capabilities: 8**

---

## Is Trevor Still Mostly a Workflow Engine?

**Yes.**

The pipeline runs steps in sequence. The steps are better instrumented. Some steps now have conditional branches. But the fundamental architecture is:

```
Fixed schedule → Fixed steps → Fixed output → Distribute
```

The adaptive additions (Phase 2 today) are conditional branches within the pipeline:
- If stale narratives → `TREVOR_ADAPTATION_FLAG` env var is set
- If calibration drift → warning logged
- If critical issues remain → auto-repair subprocess called

These are **reactive, not adaptive**. They respond to state that was detected in the same run. They do not change behavior for the next run. They do not learn from patterns across runs.

**Where Trevor is static:**
- Same 7 theatres every day (theatre list is hardcoded, not discovered)
- Same prompt template every day (one template for all theatres, all contexts)
- Same model every day (no model switching based on task complexity)
- Same schedule (5am PT, never earlier or later)
- Same output format (PDF/JSON, never varies by content)

**Where Trevor is becoming adaptive:**
- Assessment prompt now includes memory context (when memory has data — currently empty)
- Pipeline reads story_delta.json and acts on stale narratives
- Auto-repair runs when critical issues are detected
- These are first steps, not operational reality yet

**Verdict:** Trevor is a **well-instrumented workflow engine** with three conditional branches. Not an adaptive intelligence operator.

---

## Has Trevor Achieved Real Persistence?

**No.**

The FTS5 store exists. It is empty.

```
BEFORE:  Chroma database existed, populated by old pipeline
AFTER:   FTS5 store exists, empty (0 entries)
```

Memory is written `index_memory.py` runs after assessment generation. It writes today's assessments into the store. Those assessments become retrievable *tomorrow*.

This means:
- Run #1: No memory to retrieve. Generation is blind.
- Run #2: Run #1's assessments are available. Generation is conditioned.
- Run #3: Run #1 and #2 are available.

**Persistence begins on the second pipeline run.** The first run after deployment is always stateless.

**Cross-run context:**
- Prior narratives: Will be retrievable from run #2 onward.
- Unresolved questions: Not currently stored. The prompt contains them but they're not extracted and indexed.
- Modified prompts based on prior outcomes: Code path exists (`memory_context` in build_prompt). Produces no output because store is empty.
- Adapted confidence over time: Not implemented. Calibration drift is detected but not fed back into prompts.

**Verdict:** Persistence infrastructure exists. Production loop is open until run #2.

---

## Autonomy Reality Check

| Layer | Before | After | Verdict |
|-------|--------|-------|---------|
| **Scheduling** | Fixed cron, 5am PT | Fixed cron, 5am PT | Unchanged |
| **Orchestration** | improvement_daemon.py runs steps linearly | improvement_daemon.py with 3 conditional branches | Modestly improved |
| **Adaptation** | None | Reads story_delta.json, sets adaptation flag | Exists but flag is not consumed by any downstream step that varies behavior |
| **Self-maintenance** | None | REPAIR_REGISTRY with 4 repair functions | Operational but static — doesn't learn which repairs work |
| **Behavioral evolution** | None | None | Has not changed behavior based on any historical outcome |

**What adaptation actually controls:**
`TREVOR_ADAPTATION_FLAG` is set as an environment variable when stale narratives are detected. It is not currently read by any template selector or prompt variation logic. The flag exists. Nothing reacts to it.

**What self-maintenance actually does:**
If quality_audit finds a missing assessment, it calls `generate_assessments.py` again. If stale memory, it calls `index_memory.py`. These are fixed function calls — no priority ordering, no cost-benefit analysis, no retry backoff.

**Verdict:** Scheduling is real. Orchestration is real but rigid. Adaptation is scaffolded (code path exists, produces no behavioral change). Self-maintenance is basic. Behavioral evolution is zero.

---

## Current Weakest Links

| # | Weakness | Impact | Location |
|---|----------|--------|----------|
| 1 | **Memory store is empty** | Retrieval-conditioned generation produces nothing | `trevor_memory.db` (0 entries) |
| 2 | **Adaptation flag is consumed by nothing** | Pipeline detects stale narratives but does nothing different | `improvement_daemon.py` line setting `TREVOR_ADAPTATION_FLAG` |
| 3 | **No prompt variation** | Same template every day for every theatre | `generate_assessments.py` `build_prompt()` |
| 4 | **No delivery verification** | Email "sent OK" is the last check before success | `_email_brief.py` |
| 5 | **Single DeepSeek dependency** | If DeepSeek API is down, pipeline produces nothing | `deepseek_client.py` |
| 6 | **Reportlab memory risk** | Large imagery pushes render memory on tight VPS | `build_pdf.py` |
| 7 | **Assessment files accumulate unbounded** | No pruning, no rotation, no archival | `assessments/` directory |

**Biggest fragile capability:** `TREVOR_ADAPTATION_FLAG`. It exists in code. It is set in one place. It is never read in any other place. It is a half-implemented pattern that suggests adaptation where none exists.

**Biggest architecture weakness:** Memory writes after assessment generation, but memory reads happen at the start. The first run is always blind. This is a design choice that guarantees one day of stateless operation on every fresh deployment.

**Biggest source of technical debt:** Two unsynchronized codebases. The workspace (`~/.openclaw/workspace/`) has Hermes patterns, agent JSON products, and 3 production skills. The skill branch (`~/.openclaw/skills/OpenClawTrevorMentis/`) has the pipeline, FTS5 memory, and DAILY_INTEL infrastructure. Neither knows about the other's capabilities.

---

## Production Readiness Scores

| Category | Score | Rationale |
|----------|-------|-----------|
| Runtime stability | 55/100 | Core pipeline runs. No monitoring. No alerting. |
| Portability | 35/100 | Paths configurable. Fonts fall back. Still requires Linux + Python + reportlab + matplotlib + 9 TTF files. |
| Memory persistence | 20/100 | FTS5 store exists. Empty. No production data written yet. |
| Adaptive behavior | 15/100 | Code paths for adaptation exist. No behavioral change has occurred yet. |
| Observability | 30/100 | Dashboard exists. No alerting. No trending. No real-time visibility. |
| Resilience | 30/100 | Text fallback for PDF. Auto-repair for 4 issue types. No email fallback. No retry queue. |
| Publication quality | 60/100 | PDF is sophisticated. No proofing. No delivery verification beyond HTTP 200. |
| Operational coherence | 40/100 | Systems are better integrated than before. Two unsynchronized codebases prevent full coherence. |

**Weighted overall: 36/100** (up from 24/100 before today)

---

## What Would Need To Exist For Trevor To Reach 90/100

Nine things. Each is concrete. None require new research.

1. **Memory populated by at least one production pipeline run.** Without data in the store, retrieval-conditioned generation is theoretical. One successful daily run fixes this.

2. **Adaptation flag consumed by a prompt variation selector.** `TREVOR_ADAPTATION_FLAG` must map to an actual behavioral difference: a different prompt template, a different model temperature, a different source weighting.

3. **Calibration feedback into confidence bands.** briefometer detects drift. The drift must change how confidence is expressed in prompts. If `highly likely` has a Brier > 0.25, the prompt should say "use a wider band until recalibration."

4. **Plain-text delivery path.** If email fails, a backup delivery path (Moltbook DM, Telegram message, SMS) must exist. Currently there is no alternative to Gmail.

5. **Cross-codebase synchronization.** The workspace Hermes patterns and skill branch pipeline should either be merged or share a common config/memory path. Dual maintenance is technical debt.

6. **Runtime alerting.** If the pipeline fails silently at 2am, someone should know. A heartbeat check with delivery failure notification to the same Telegram thread Trevor uses.

7. **Assessment pruning and archival.** Assessment markdowns grow unbounded. A 30-day rotation policy with S3/rsync archival.

8. **Offline degraded mode.** If DeepSeek API is unreachable, a smaller local model (or cached previous assessment with "no update available" header) should produce output rather than nothing.

9. **Memory compaction in production.** FTS5 export + reimport weekly to prevent query degradation on large stores. Currently no compaction schedule is wired.

---

## Current Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        PRODUCTION FLOW                                │
│                                                                       │
│  [Cron 05:00 PT]                                                      │
│       │                                                               │
│       ▼                                                               │
│  daily-brief-cron.sh                                                  │
│       │                                                               │
│       ▼                                                               │
│  improvement_daemon.py --daily                                         │
│       │                                                               │
│       ├─ Phase 1: Enrichment                                          │
│       │   ├─ story_tracker --diff       ✅ reads assessment files     │
│       │   ├─ daily_enrichment           ✅ fetches 9 RSS feeds        │
│       │   └─ kalshi_scan                ✅ loads scan file            │
│       │                                                               │
│       ├─ Phase 2: Generation (retrieval-conditioned scaffolding)      │
│       │   ├─ MemoryStore.search()       ⚠️ returns 0 rows (empty DB) │
│       │   ├─ generate_assessments       ✅ 7 parallel DeepSeek calls  │
│       │   │   └─ build_prompt()         ✅ memory_context injected    │
│       │   ├─ refresh_imagery            ✅ matplotlib + photos        │
│       │   └─ build_pdf                  ✅ reportlab (with text fb)   │
│       │                                                               │
│       ├─ Phase 3: Quality + Memory                                    │
│       │   ├─ quality_audit              ✅ REPAIR_REGISTRY active     │
│       │   ├─ briefometer --calibrate    ✅ detects drift, no action   │
│       │   ├─ story_tracker --save       ✅ writes narrative state     │
│       │   └─ memory/index_memory        ✅ writes to FTS5 (AFTER gen) │
│       │                                                               │
│       ├─ Phase 4: Distribution                                        │
│       │   ├─ email PDF                  ✅ Gmail API                   │
│       │   └─ (JSON + Moltbook)         ⚠️ lives in workspace, not     │
│       │                                   daily-intel-skill branch    │
│       │                                                               │
│       └─ Skill nudge                    ✅ if count < 5                │
│                                                                       │
│  [Separate: workspace, unsynchronized]                                │
│  ├─ brain/ (TF-IDF memory — populated)                                │
│  ├─ scripts/skill_registry.py (3 skills, active)                      │
│  ├─ exports/agent-api/latest.json (55 KB, agent JSON)                 │
│  └─ Moltbook post (agents submolt, live)                              │
│                                                                       │
│  [Fallback paths]                                                     │
│  ├─ PDF fails → generate_text_fallback()      ✅                      │
│  ├─ Email fails → nothing                      ❌                      │
│  └─ DeepSeek fails → nothing                   ❌                      │
└──────────────────────────────────────────────────────────────────────┘

KEY:
✅ = Operational
⚠️ = Exists but produces no output / no effect
❌ = Does not exist
```

---

## Trevor vs Hermes — Updated Comparison

| Dimension | Before Today | After Today | Hermes | Gap Remaining |
|-----------|-------------|-------------|--------|---------------|
| **Memory** | Chroma, populated, slow | FTS5, empty, fast | SQLite+FTS5+LLM summarization | FTS5 is lighter. Hermes data is populated and active. |
| **Autonomy** | Fixed pipeline only | Pipeline + 3 conditional branches | Adaptive task scheduling | Hermes decides *what* to do. Trevor decides *whether to retry*. |
| **Portability** | 28 hardcoded paths, Linux-only | Configurable paths, font fallback, Linux+Python+5 deps | Single shell install, 6 platforms | Both improved. Hermes is still dramatically easier to deploy. |
| **Self-improvement** | Logged errors, no change | REPAIR_REGISTRY + calibration detection | Creates skills from corrections, patches during use | Same gap. Trevor detects issues. Hermes changes behavior. |
| **Retrieval** | Chroma semantic search (slow) | FTS5 keyword (fast, empty) | FTS5 + LLM summarization | Trevor's is lighter. Both retrieve from populated stores. Trevor's is empty. |
| **Observability** | None | Dashboard + structured logging + heartbeat | CLI spinners + callbacks + trajectory export | Hermes has richer real-time visibility. Trevor has better file persistence. |
| **Procedural memory** | None | Skill registry (1 skill, passive) | Active skill management (create/patch/delete) | Same gap. Skills are files. Hermes's skills are runtime agents. |

**Where Trevor has surpassed Hermes concepts:**
- PDF generation (Hermes has no equivalent)
- Intelligence workflow structure (Hermes has no estimative tradecraft pipeline)
- Lightweight FTS5 memory (Hermes uses same approach but with heavier embeddings available)

**Where Hermes is still dramatically ahead:**
- Autonomous behavior (Hermes decides, Trevor retries)
- Skill evolution (Hermes creates skills during use, Trevor has static files)
- Real learning (Hermes changes behavior from corrections)
- Deployment portability (Hermes single-command install on 6 platforms)

**Is Trevor converging toward persistent cognition?** Infrastructure is converging. The FTS5 store + retrieval-conditioned prompt scaffolding + story_tracker + calibration detection form the architectural foundation for it. But operational reality hasn't crossed the threshold yet — because the memory store is empty, none of the retrieval paths produce output in production.

**Does Trevor still lack true learning?** Yes. Learning requires behavioral change from experience. Trevor has:
- Experience storage ✅ (FTS5 store, logs, state files)
- Behavioral scaffolding ✅ (code paths that could change behavior)
- Behavioral change ❌ (nothing has actually changed because nothing has been experienced yet)

The first production pipeline run will break this stalemate.
