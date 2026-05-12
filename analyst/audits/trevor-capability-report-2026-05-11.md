# Trevor Capability & Evolution Report

**Date:** 2026-05-11 22:47 UTC
**Branch:** daily-intel-skill
**Author:** Trevor (self-audit)

---

## 1. What Trevor Currently Is

Trevor is a **daily geopolitical intelligence pipeline** wrapped in an **agent personality**, running on top of **OpenClaw**. The core value is structured estimative analysis — not chat, not code generation, not general assistance. The pipeline generates 7 theatre assessments per day, renders them into a PDF, emails them, and (as of today) publishes structured JSON for agent consumption.

The system has **two codebases**:

| Codebase | Location | Purpose | Maturity |
|----------|----------|---------|----------|
| DailyIntelAgent | `~/.openclaw/skills/OpenClawTrevorMentis/` (daily-intel-skill branch) | Pipeline: enrich → assess → image → PDF → audit → distribute | Operational but fragile |
| Trevor personality | `~/.openclaw/workspace/` (main branch) | Agent identity, Hermes patterns, brain memory, agent-first product | Mixed (some operational, some scaffolded) |

The two codebases are **not synchronized**. The Hermes patterns (skills, nudge, cost tracker, context compressor) live in the workspace but not in the daily-intel-skill branch. The FTS5 memory rebuild lives in the skill branch but not in the workspace.

---

## 2. Subsystem Audit

### 2.1 OpenClaw Runtime

| Attribute | Status |
|-----------|--------|
| **Purpose** | Runtime for agent sessions, tool execution, cron, messaging |
| **Maturity** | FULLY OPERATIONAL |
| **Implemented by** | OpenClaw project, not Trevor |
| **Weaknesses** | None directly — OpenClaw maintains its own runtime |

Trevor does not maintain the runtime. OpenClaw handles session persistence, model routing, tool dispatch, plugin system, cron scheduling, and platform gateways. This is **good** — Trevor gains a production-grade runtime without maintaining one.

### 2.2 DeepSeek Orchestration

| Attribute | Status |
|-----------|--------|
| **Purpose** | Call DeepSeek API for assessment generation |
| **Maturity** | FULLY OPERATIONAL |
| **File** | `skills/daily_intel/deepseek_client.py` (74 lines) |
| **Model** | deepseek-chat via `DEEPSEEK_MODEL` env var |
| **Mode** | Direct API (not OpenRouter) |

**Known weaknesses:**
- No streaming support
- No token counting before send
- Single model — no A/B or model comparison
- API key is read at import time, not runtime (can't hot-reload)

**Recent improvements:**
- 120s hard timeout (was 90s no-timeout)
- Exponential backoff on HTTP 429
- Retry/backoff with structured logging

### 2.3 Cron Systems

| Attribute | Status |
|-----------|--------|
| **Purpose** | Schedule daily pipeline runs |
| **Maturity** | FULLY OPERATIONAL |
| **Implementation** | OpenClaw cron + `improvement_daemon.py` |

Two cron jobs:
- `Daily Intel Brief — main` (ID: `250765ae`): fires at 05:00 PT, runs `daily-brief-cron.sh`
- `Daily 4 Briefings — 8am PT` (ID: `9ee44803`): fires at 08:00 PT, sends email briefings

**Weakness:** The crons call shell scripts that call Python scripts. If any intermediate step fails, error reporting is through stderr capture, not structured. No auto-remediation for missed cron fires.

### 2.4 Retrieval Memory (FTS5)

| Attribute | Status |
|-----------|--------|
| **Purpose** | Persistent narrative memory across pipeline runs |
| **Maturity** | PARTIALLY OPERATIONAL |
| **File** | `skills/daily_intel/trevor_memory.py` (228 lines) |
| **Collections** | narrative, procedural, execution, source, trade_thesis |
| **Engine** | sqlite3 FTS5 (built-in, zero dependencies) |

**What works:**
- Full-text search with ranking
- Incremental indexing
- Portable SQLite database (single file)
- JSON export/import for backup
- TTL-based pruning
- Prior narrative retrieval

**What doesn't work yet:**
- **Empty database.** The FTS5 store was created today but `index_memory.py` has never been run in production. Zero narrative entries exist.
- No automatic indexing at pipeline end (not wired into improvement_daemon --daily flow)
- No source reliability tracking (collection exists, no data)
- No trade_thesis persistence (collection exists, no data)

**Weaknesses vs Chroma (the replaced system):**
- No semantic similarity search (FTS5 is keyword-only, no embeddings)
- No cross-lingual retrieval
- Can't find conceptually similar content that uses different vocabulary

**What was gained:**
- 1.8GB dependency eliminated (torch + transformers + chromadb)
- Query time: <1ms vs 5-10s
- True portability: single SQLite file
- Backward-compatible export/import

### 2.5 Vector Memory (Chroma — Legacy)

| Attribute | Status |
|-----------|--------|
| **Purpose** | Semantic search over assessment content |
| **Maturity** | BROKEN (replaced, can be removed) |
| **Implementation** | `skills/daily_intel/memory/chroma_db/` |
| **Dependency** | chromadb 1.5.8 + sentence-transformers 5.4.1 + torch (1.2GB) |

**Status:** FTS5 replaced Chroma in Phase 2 today. The old chroma_db directory still exists on disk but the index_memory.py and retrieve.py now use FTS5. The old Chroma dependency is still installed in site-packages but not imported by any active code path.

**Retention risk:** The chromadb + sentence-transformers + torch stack is still installed (~1.8GB). Should be removed once the FTS5 replacement is validated in production.

### 2.6 Publication Pipeline

| Attribute | Status |
|-----------|--------|
| **Purpose** | Produce and distribute the daily intelligence brief |
| **Maturity** | FULLY OPERATIONAL |
| **Outputs** | PDF via email + JSON via API + text via Moltbook |

**Steps (in order):**
1. `generate_assessments.py` — 7 parallel DeepSeek calls → markdown assessments
2. `refresh_imagery.py` — maps + photos → PNG/JPEG
3. `build_pdf.py` — reportlab → PDF
4. `quality_audit.py` — scanner + auto-repair
5. Email via Gmail API
6. Agent JSON → `exports/agent-api/latest.json`
7. Moltbook post → agents submolt

**What works:**
- PDF generation (1,174 lines of reportlab — most sophisticated single file in the system)
- Email delivery via Gmail API with env fallback
- Issue numbering and sequential tracking
- Heartbeat logging during long steps

**What doesn't work:**
- No delivery confirmation beyond "email sent OK"
- No proofing/review step before distribution
- No rollback capability (if today's brief is bad, can't re-publish yesterday's)

### 2.7 PDF Renderer

| Attribute | Status |
|-----------|--------|
| **Purpose** | Render intelligence brief as PDF |
| **Maturity** | FULLY OPERATIONAL |
| **File** | `skills/daily_intel/scripts/build_pdf.py` (1,174 lines) |
| **Engine** | reportlab 4.4.10 |

The PDF builder is the single most sophisticated component. It implements:
- Custom page templates (cover, body, section headers)
- Multi-column prose layout
- Edge-to-edge imagery with captions
- ThruDark-inspired dark palette (#161616 base)
- 9 registered fonts with cascading fallback
- Kalshi trade card layout
- Key judgment chips with Sherwood Kent bands

**Font loading** was recently ported to `trevor_fonts.py` with 3-level fallback (dedicated → system → built-in). If fonts are missing, the PDF degrades to DejaVu/Helvetica rather than breaking.

**Weakness:** No plain-text fallback. If reportlab raises any exception (missing font, corrupt image, OOM), the pipeline errors and no output is produced. A MIMEText fallback exists in `_email_brief.py` but is not called by default.

### 2.8 Assessment Generation

| Attribute | Status |
|-----------|--------|
| **Purpose** | Generate theatre assessments via LLM |
| **Maturity** | FULLY OPERATIONAL |
| **File** | `skills/daily_intel/scripts/generate_assessments.py` (221 lines) |
| **Concurrency** | 7 parallel threads via ThreadPoolExecutor |

**What works:**
- Fires 7 parallel DeepSeek calls, one per theatre
- Loads previous assessment for continuity context
- Writes structured markdown with KJs, BLUF, narrative
- Enrichment report consumed if available

**Weakness:** All 7 threads use the same model/prompt template. No adaptive prompting based on narrative state. No A/B testing of prompt variations. No confidence scoring for the generated content itself.

### 2.9 Self-Improvement Loops

| Attribute | Status |
|-----------|--------|
| **Purpose** | Detect issues, repair them, get better over time |
| **Maturity** | SCAFFOLDED |

**Actual behavior (not aspirational):**

| Loop | What it actually does | Maturity |
|------|----------------------|----------|
| `quality_audit.py` | Scans images for size/quality. Calls repair functions for stale memory/Kalshi. | PARTIAL |
| `story_tracker.py` | Computes narrative fingerprints. Diffs against yesterday. Flags stale. Writes JSON. | PARTIAL |
| `briefometer.py` | Records KJs. Calculates Brier scores. Compares to calibration bands. | PARTIAL |
| `improvement_daemon.py` | Reads state from previous run. Skips steps if prior state indicates failure. | SCAFFOLDED |

**What's real:**
- quality_audit's REPAIR_REGISTRY actually runs subprocesses to regenerate missing assets
- story_tracker actually reads assessment files, extracts fingerprints, writes diffs
- The diffs are written to a file that daily_enrichment can consume

**What's not:**
- No Brier score has ever been checked for calibration drift (no resolved KJs exist in the log)
- The improvement_daemon does not dynamically reorder pipeline steps based on state
- No "this fix worked last time, use it again" logic — every auto-fix is a fresh attempt
- The "learning" in "self-improvement" is logging — not behavioral change

### 2.10 Procedural Memory

| Attribute | Status |
|-----------|--------|
| **Purpose** | Remember how to do things between sessions |
| **Maturity** | SCAFFOLDED |
| **Files** | `trevor_skills.py` + `skills/daily_intel/skills/publishing/daily-intel-pipeline.md` |

**What exists:**
- Skill registry module with progressive disclosure (list → view)
- One skill file (daily-intel-pipeline)
- SKILL.md format with frontmatter

**What doesn't:**
- No skill creation from session experience (no nudge → create loop)
- No skill improvement during use (no patch pattern)
- Skills are dead files — no one reads them
- The skill registry is not wired into any pipeline or session start

**Hermes comparison:** Hermes's skill system is *active* — the agent creates skills automatically after complex tasks, patches them during use, and they're surfaced as slash commands. Trevor's is *passive* — files that exist but have no runtime presence.

### 2.11 Autonomy Systems

| Attribute | Status |
|-----------|--------|
| **Purpose** | Trevor acts without human intervention |
| **Maturity** | PARTIALLY OPERATIONAL — but limited |

**What Trevor does autonomously:**
- Fires the daily pipeline on cron schedule ✅
- Generates assessments without human review ✅
- Builds and distributes PDF ✅
- Publishes agent JSON to API + Moltbook ✅
- Detects missing assets and attempts auto-repair ✅

**What Trevor does NOT do autonomously:**
- Does not decide *what* to analyze — follows fixed theatre list
- Does not decide *when* to run — follows fixed cron schedule
- Does not decide *whether* to distribute — always sends at end of pipeline
- Does not prioritize one theatre over another based on breaking news
- Does not interrupt a running pipeline for a critical event
- Does not defer low-priority tasks when resource-constrained
- Does not escalate failures it can't fix — just logs them

### 2.12 Runtime Observability

| Attribute | Status |
|-----------|--------|
| **Purpose** | Know what Trevor is doing, how well, at what cost |
| **Maturity** | PARTIALLY OPERATIONAL |

**What works:**
- `trevor_log.py` — structured JSON logging with task tracing and heartbeat
- `trevor_diag.py` — 23 startup health checks
- `trevor_cost.py` — session cost snapshots with DeepSeek pricing
- Pipeline state persists to `cron_tracking/state.json`

**What doesn't:**
- No real-time dashboard — must SSH in and read log files
- No alerting — if the pipeline fails silently at 2am, no one is notified
- No cost trending — cost snapshots exist but no charting
- No model performance tracking — no token usage per session
- No delivery confirmation beyond HTTP 200 from Gmail API

### 2.13 Fallback Systems

| Attribute | Status |
|-----------|--------|
| **Purpose** | Keep running when things break |
| **Maturity** | SCAFFOLDED |

**What exists:**
- Font fallback (3 levels: dedicated → system → built-in) ✅
- DeepSeek retry with backoff ✅
- Chroma → FTS5 fallback in old retrieve.py ✅
- Enrichment runs without feeds (graceful failure) ✅

**What doesn't:**
- No plain-text fallback for PDF failure ❌
- No email delivery fallback (if Gmail API is down, brief is lost) ❌
- No offline mode (if DeepSeek API is unreachable, pipeline produces nothing) ❌
- No degraded-quality output (could generate shorter assessments with smaller model) ❌

### 2.14 Skill Architecture (Workspace — not in skill branch)

| Attribute | Status |
|-----------|--------|
| **Purpose** | Hermes-inspired procedural memory |
| **Maturity** | SCAFFOLDED — not ported to daily-intel-skill |

**Files (workspace only):**
- `scripts/skill_registry.py` — discovery (190 lines)
- `scripts/skill_patch.py` — evolution (235 lines)
- `scripts/nudge_check.py` — self-improvement triggers (160 lines)
- `scripts/context_compressor.py` — overflow prevention (177 lines)
- `scripts/cost_tracker.py` — economics (225 lines)
- `scripts/frozen_snapshot.py` — memory freeze (158 lines)
- 3 skills in `skills/trevor/publishing/`

**These exist only in the workspace, not in the daily-intel-skill branch.** The daily-intel-skill branch has `trevor_skills.py`, `trevor_cost.py`, and `trevor_freeze.py` as simplified versions of the workspace originals. They are not wired into any session start or heartbeat.

---

## 3. What Trevor Has Actually Learned

**Answer: Nothing. Not really.**

Trevor has:
- **Logs** — extensive logs of what ran, when, and whether it succeeded
- **Configuration** — hardcoded paths that were moved to centralized config (improvement)
- **Scripts** — pipeline scripts that have been iterated and hardened
- **Memory store** — an FTS5 database that is currently **empty**

Trevor does NOT have:
- **Persistent learning** — no behavioral change based on past outcomes
- **Evolution between runs** — each pipeline run is identical in structure to the last
- **Adaptive prompting** — the same prompt templates are used every day
- **Procedural memory** — skills exist as files but are never loaded into context
- **Failure-based improvement** — errors are logged but don't change future behavior
- **Workflow adaptation** — if enrichment fails 10 times in a row, the pipeline still tries it on day 11

**What exists instead:**
- `story_tracker.py` tracks whether narratives are stale. This is the closest thing to "learning" — it detects repetition. But it only logs the detection. It doesn't change assessment prompts.
- `briefometer.py` records Brier scores. This is the closest thing to "calibration." But with zero resolved KJs in the log, it has never detected drift.
- `quality_audit.py` has a REPAIR_REGISTRY. This is the closest thing to "self-healing." But it's a static key-value map — it doesn't learn which repairs work best.

**Verdict:** Trevor stores information between runs. That is logging, not learning. Real learning requires behavioral change based on stored information. Trevor has none.

---

## 4. Recent Improvements (11 May 2026)

| Category | Change | Impact |
|----------|--------|--------|
| **Memory** | Replaced Chroma + sentence-transformers (1.8GB) with FTS5 | Eliminates heaviest dependency, sub-ms queries |
| **Config** | Centralized 28 hardcoded paths into trevor_config.py | Portability: single env var changes all paths |
| **Fonts** | 3-level fallback with auto-download | PDF renders even without specific fonts |
| **Logging** | Structured JSON logging with task tracing | Metrics pipeline exists |
| **Timeout** | DeepSeek client: 120s hard timeout + exponential backoff | No more infinite hangs |
| **Health** | 23 startup diagnostics | Pipeline knows own health |
| **Auto-repair** | quality_audit REPAIR_REGISTRY | Missing assets auto-regenerated |
| **Narrative tracking** | story_tracker fingerprint + diff | Stale narratives detected |
| **Calibration** | briefometer Brier tracking | Calibration drift detectable |
| **Cost tracking** | CostTracker with DeepSeek pricing | Operating cost measurable |
| **Memory freeze** | Frozen snapshot at pipeline start | Context stability |
| **Skills** | Skill registry + 2 pipeline skills | Procedural memory scaffold exists |

**Net architectural change (today only):**

```
Yesterday:        Today:
Chromadb          FTS5 (0 dependency)
28 hardcoded     trevor_config.py (single source)
print() logging  Structured JSON + task tracing
DeepSeek 90s MT  DeepSeek 120s + backoff
No tests         4 test files
No cost tracking  CostTracker
No freeze         MemoryFreeze
No skill system  SkillRegistry + 3 skills
No auto-repair   REPAIR_REGISTRY
Passive scoring  Active calibration (briefometer)
No feed fetching 9 RSS feeds wired
```

---

## 5. Operational Readiness Scores

| Category | Score | Rationale |
|----------|-------|-----------|
| **Runtime stability** | 55/100 | Core pipeline runs. No monitoring, no alerting, no rollback. |
| **Autonomy** | 30/100 | Pipeline runs on schedule. No decision-making. No adaptation. |
| **Intelligence quality** | 65/100 | Assessments are substantive. Prompt templates are static. No A/B. |
| **Portability** | 35/100 | Paths are configurable. Fonts fall back gracefully. Still assumes Linux/Python/reportlab/matplotlib stack. |
| **Maintainability** | 40/100 | Tests exist (4 files). Theatre lists in one place. But no type checking, no CI, no linting. |
| **Memory persistence** | 20/100 | FTS5 database exists. Empty. Not wired into any workflow. |
| **Self-repair** | 25/100 | REPAIR_REGISTRY exists. Static map, no learning. Fixes are subprocess calls. |
| **Observability** | 30/100 | Logging exists. No dashboard, no alerting, no trending. |
| **Publication quality** | 55/100 | PDF is sophisticated. No proofing step. No delivery confirmation. No rollback. |

**Overall: 39/100**

---

## 6. Current Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        OPenClaw RUNTIME                                 │
│  Cron: 05:00 PT ─→ daily-brief-cron.sh ─→ improvement_daemon.py        │
│  Cron: 08:00 PT ─→ 4 Daily Briefings (GPT-generated, sent via Gmail)   │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────────┐
│                    DAIlyIntel PIPELINE                                   │
│                                                                          │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐              │
│  │ Enrich   │──→│ Assess   │──→│ Images   │──→│ PDF      │              │
│  │ RSS feed │   │ DeepSeek │   │ Maps +   │   │ reportlab │             │
│  │ Kalshi   │   │ 7 thrd   │   │ Photos   │   │ ThruDark │              │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘              │
│       │              │              │              │                     │
│  ┌────▼──────────────▼──────────────▼──────────────▼──────┐             │
│  │              QUALITY & DISTRIBUTION                     │             │
│  │  quality_audit → story_tracker → memory_index          │             │
│  │  email (Gmail) + JSON (API) + Moltbook (agents)        │             │
│  └─────────────────────────────────────────────────────────┘             │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────┐            │
│  │  MEMORY (FTS5 — currently empty)                        │            │
│  │  narrative │ procedural │ execution │ source │ trade    │            │
│  └─────────────────────────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────────────────────┘

SEPARATE SYSTEMS (workspace, not in skill branch):
┌─────────────────────────────────────────────────────────────────────────┐
│  brain/ (episodic/semantic/procedural memory — TF-IDF index)            │
│  scripts/ (skill_registry, nudge_check, cost_tracker, frozen_snapshot)  │
│  skills/trevor/ (3 SKILL.md files — publishing workflows)               │
│  exports/agent-api/ (agent-first JSON brief — 55 KB)                    │
└─────────────────────────────────────────────────────────────────────────┘

LEGACY (still installed, no active code paths):
┌─────────────────────────────────────────────────────────────────────────┐
│  chromadb (1.5.8) + sentence-transformers (5.4.1) + torch (1.2GB)      │
│  Total: ~1.8GB of unused dependencies                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. What Would Break First

| # | Risk | Impact | Location | Notes |
|---|------|--------|----------|-------|
| 1 | **Gmail API key expires or quota exhausted** | Brief doesn't arrive | `_email_brief.py` | No fallback delivery method |
| 2 | **DeepSeek API outage** | No assessments generated | `generate_assessments.py` | All 7 threads fail, pipeline produces nothing |
| 3 | **reportlab memory error on large PDF** | PDF not generated, no fallback | `build_pdf.py` | 6MB+ imagery PNGs push memory on low-RAM VPS |
| 4 | **RSS feed format changes** | Enrichment reports silently empty | `daily_enrichment.py` | XML parse failure is caught but not alerted |
| 5 | **Cron miss (OpenClaw restart, timezones)** | Entire day's brief skipped | OpenClaw cron | No catch-up mechanism |

**Weakest subsystem:** The PDF renderer. It's the most complex code (1,174 lines), has the most dependencies (reportlab + PIL + 9 font files), and has no fallback that produces output.

**Biggest operational risk:** Single point of failure at the email delivery step. If Gmail API returns a 500, the entire pipeline output is lost. No retry queue, no alternative delivery channel.

**Biggest architectural flaw:** Two unsynchronized codebases. The workspace has Hermes patterns, agent JSON, and skills that the daily-intel-skill branch doesn't know about. Features built in one place aren't available in the other.

**Biggest false assumption:** That the pipeline runs perfectly every time. There is no monitoring, no alerting, and the first sign of failure is a user asking "where's my brief?"

**Biggest scalability bottleneck:** Sequential PDF generation. The assessment step is parallelized (7 threads), but everything after is single-threaded and blocking. Parallelizing the quality/tracking steps would improve reliability.

---

## 8. Trevor vs Hermes

| Dimension | Trevor | Hermes Agent | Gap |
|-----------|--------|--------------|-----|
| **Memory** | FTS5 (keyword search, empty) | SQLite + FTS5 + LLM summarization (populated, active) | Trevor's DB is empty, no summarization |
| **Autonomy** | Fixed cron → fixed pipeline → fixed distribution | Adaptive task scheduling based on state | Trevor is a washing machine; Hermes is an operator |
| **Portability** | Requires Linux, Python, reportlab, matplotlib, PIL, 9 fonts | Single shell install, works on 6 platforms | Trevor is tied to a specific machine setup |
| **Self-improvement** | Logs errors, doesn't change behavior | Detects failure patterns, creates skills from corrections | Trevor has no learning loop |
| **Retrieval** | FTS5 keyword only | FTS5 + LLM summarization + semantic search | Trevor lacks semantic retrieval |
| **Runtime engineering** | Leverages OpenClaw (good) | Self-contained, no external runtime (also good) | Different approaches, neither inherently better |
| **Observability** | JSON logs + heartbeat + cost snapshots | CLI spinners + tool callbacks + trajectory export | Hermes has richer real-time observability |
| **Procedural memory** | SkillRegistry as file scanner (passive) | Skill management as tool (active, creates/patches/deletes) | Trevor's skills are files that aren't used |

**Hermes wins on:** autonomy, self-improvement, procedural memory, semantic retrieval
**Trevor wins on:** PDF generation, intelligence workflow structure, estimative tradecraft
**Neither has:** True persistent learning that changes behavior over time

---

## 9. Summary

Trevor is a **sophisticated daily intelligence pipeline** with a **real publication output** and a **designed architecture** that is more complete than most agent projects. The estimative analysis content (BLUFs, KJs with falsification criteria, Sherman Kent calibration) is legitimate tradecraft that most AI-generated intel products don't approach.

But Trevor is not:
- A persistent agent (no continuous awareness between runs)
- A self-improving system (no behavioral change from experience)
- A portable product (tied to a specific Linux/Python setup)
- An observable service (no monitoring, no alerting, no dashboard)
- A resilient pipeline (single points of failure at every step)

The improvements from today (Phases 1-5) addressed the **structural weaknesses** — hardcoded paths, heavy dependencies, missing logging, fake autonomy. They did not address the **learning gap** — Trevor still does not get better from doing its job.

The single highest-leverage improvement for tomorrow: **wire the FTS5 memory into the assessment generation step.** Have `generate_assessments.py` query previous narratives and include them in the prompt. This closes the loop between output and input — the first step toward actual persistence.
