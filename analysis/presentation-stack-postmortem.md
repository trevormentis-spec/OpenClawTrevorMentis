# Presentation Stack Postmortem

**Date:** 2026-05-20
**Author:** Trevor
**Status:** Diagnostic — not yet resolved
**Scope:** All systems built for visual/presentation output from analytical content

---

## 1. Executive Summary

Four separate presentation systems were built, each overlapping in purpose, none completing a full production run. The core failure is **architectural bloat without a working end-to-end path**. Multiple conflicting pipelines, missing API keys, uninstalled dependencies, over-engineered infrastructure, and a planner routing task to Opus 4.7 (costing ~$0.20 per call) for work a 20-line rule-based system can do.

**Total cost of development failures:** ~$5.00 in Opus 4.7 calls on the routing log, 20+ generator stubs never tested, an API server with full database migrations, and zero working output to show for it.

---

## 2. What Was Built (The Four Systems)

### System A: `skills/visual_production/` — Magazine PDF via WeasyPrint

**Built:** ~2026-05-18
**Files:** 6 Python modules + SKILL.md + format_magazine.py CLI

**Pipeline:**
```
Markdown → extract Mermaid → Graphviz DOT → PNG
        → rasterize SVGs → CairoSVG
        → assemble HTML with editorial CSS
        → WeasyPrint → A4 PDF
        → quality gate (8 checks)
```

**Image generation path:** OpenRouter API directly (`google/gemini-3.1-flash-image-preview`), falls back to text on failure.

**LLM routing:** Not through llm_gate — uses `OPENROUTER_API_KEY` directly via `urllib`. No cost tracking, no fallback chains, no budget enforcement.

**Status:** Half-working. PDF pipeline works (WeasyPrint + CairoSVG). Image gen path is shell checking for OPENROUTER_API_KEY and calling OpenRouter directly — no routing through llm_gate.

### System B: `trevor-presentational-suite/` (TPS) — Full Multi-Generator Platform

**Built:** ~2026-05-18/19
**Files:** 40+ files including API server, database, 20 generators, orchestrator, planner, approval gate

**Billed as:** "Trevor Presentational Suite"

**Components:**
- **Planner** (`core/planner.py`): LLM art director — calls Opus 4.7 via llm_gate to decompose a brief into visual asset specs
- **Orchestrator** (`core/orchestrator.py`): executes asset specs across 20+ generators with parallel execution and dependency ordering
- **Generators** (`generators/`): 20 files covering mermaid, matplotlib, plotly, graphviz, D2, timeline, LDAP-7 radar, HTML-to-image, Mapbox (static + interactive), Leaflet, Flux 2 Pro, Ideogram V3, Recraft V4, Imagen 4, GPT Image 2, ElevenLabs, Suno, Veo, Kling, Runway, HeyGen
- **Approval Gate** (`core/approval_gate.py`): plans > $0.50 require explicit CLI approval
- **API Server** (`api/server.py`): FastAPI with CORS, error handlers, database
- **Database** (`db/`): SQLAlchemy + Alembic migrations with full models
- **Provenance** (`core/provenance.py`): audit trail for every generated asset
- **Cost Estimator** (`core/cost_estimator.py`): per-asset cost with stale-pricing warnings
- **Style Director** (`core/style_director.py`): brand token injection from brand.yaml
- **Deliverables** (`deliverables/`): PDF builder, deck builder, briefing video, exec card, social pack, website builder
- **Brand Config** (`brand.yaml`): full visual identity spec with Kent colors, typography, chart palette

**LLM routing:** The planner calls `analyst.llm_gate.route("flagship_document", ...)` which resolves to **anthropic/claude-opus-4.7** by default. System prompt is 300+ lines including few-shot examples.

### System C: `scripts/render_slides.py` — PPTX Generator (Stub)

**Built:** ~2026-05-18
**Status:** Interface-only. Full implementation deferred. Requires `python-pptx` which is NOT installed.

### System D: `tasks/render_briefing_visuals.py` — Daily Brief Visual Renderer

**Built:** ~2026-05-18
**Status:** Renders Mermaid blocks via mermaid.ink API, generates HTML email. Self-contained, no dependencies.

---

## 3. Complete Dependency Inventory Across All Systems

### Working (zero install, verified)

| Dependency | Used By | Notes |
|-----------|---------|-------|
| `weasyprint` ✓ | visual_production, TPS PDF builder | HTML→PDF, working |
| `cairosvg` ✓ | visual_production | SVG→PNG rasterization |
| `matplotlib` ✓ | visual_production, TPS matplotlib_gen | Charts, working |
| `pydantic` ✓ | TPS schemas | All models, working |
| `httpx` ✓ | TPS fal_client, generators | HTTP client, working |
| `fastapi` ✓ | TPS API server | Web framework, working |
| `sqlalchemy` ✓ | TPS db | ORM, working |
| `tenacity` ✓ | TPS fal_client | Retry logic, working |
| `mmdc` (npm) ✓ | TPS mermaid_gen, visual_production | Mermaid CLI, working |
| `dot` (graphviz) ✓ | visual_production | DOT → PNG, working |

### Missing Dependencies (will fail at runtime)

| Dependency | Needed By | Impact |
|-----------|-----------|--------|
| `plotly` ❌ | TPS plotly_gen, data-visualization-studio | All plotly generators fail |
| `python-pptx` ❌ | TPS deck_builder, render_slides.py | PPTX generation fails |
| `d2` binary ❌ | TPS d2_gen | D2 diagram generation fails |
| `openpyxl` ❌ | Generic | Excel export fails |
| `folium` ❌ | Generic | Interactive maps fail |

### Missing API Keys (will fail at runtime)

| Key | Needed By | Impact |
|-----|-----------|--------|
| `FAL_KEY` ❌ | TPS flux_gen, ideogram_gen, recraft_gen, imagen_gen, kling_gen | ALL image generation via fal.ai fails |
| `OPENAI_API_KEY` ❌ | TPS gpt_image_gen, generic | GPT image gen fails |
| `RUNWAY_API_KEY` ❌ | TPS runway_gen | Video gen fails |
| `HEYGEN_API_KEY` ❌ | TPS heygen_gen | Talking-head video fails |
| `SUNO_API_KEY` ❌ | TPS suno_gen | Audio music gen fails |
| `GOOGLE_APPLICATION_CREDENTIALS` ❌ | TPS veo_gen | Google Veo video fails |
| `CHARTGEN_API_KEY` ❌ | chartgen-ai skill | ChartGen API calls fail |

### Working API Keys

| Key | Status |
|-----|--------|
| `OPENROUTER_API_KEY` ✓ | Covers LLMs + OpenRouter image proxy |
| `MAPBOX_TOKEN` ✓ | Mapbox Static/GL API |
| `ELEVENLABS_API_KEY` ✓ | TTS audio |

---

## 4. The LLM Routing Problem

### What Opus 4.7 Was Used For

The TPS planner (`core/planner.py`) calls the LLM to decompose a brief into visual asset specs. This is a **classification + template-matching task** — it reads a brief and decides "Do we need a map? A chart? A diagram?" with known generator mappings.

**Each call costs $0.10–0.26** (Opus 4.7 at ~$5/M input + ~$25/M output).

**The routing log shows 28 Opus 4.7 calls** on May 19-20 for this purpose, plus additional calls for the Brazil flagship document. Estimated total: **~$4.50 in wasted Opus calls**.

### What It Should Use

This is a **Tier-3** task (high-volume, low complexity). DeepSeek V4 Flash ($0.14/M input) or a simple rule-based fallback would suffice. The rule-based fallback (`_rule_based_plan()`) already exists in the code — it's 80 lines and handles all common cases.

### The Missing Routing Path

The visual_production skill and TPS each have their own image generation path:
- **visual_production:** Calls OpenRouter API directly via `urllib` with `OPENROUTER_API_KEY` — bypasses llm_gate entirely. No cost tracking, no budget enforcement.
- **TPS:** Calls fal.ai API via `httpx` with `FAL_KEY` — also bypasses llm_gate. No cost tracking.

Neither path routes through the analyst/llm_gate.py system. Image gen calls are completely invisible to the cost ledger.

---

## 5. The Approval Gate Deadlock

The TPS approval gate (`core/approval_gate.py`) has a critical design flaw:

1. Plans under $0.50: auto-approved ✅
2. Plans over $0.50: requires `sys.stdin.isatty()` to be True
3. On a headless server or non-TTY environment: **returns PENDING and blocks execution**

Since TPS was designed to run via API server (FastAPI) or cron, it will almost always be in a non-TTY environment. This means **every plan over $0.02** (the cost of a single image-gen asset at $0.05) would be blocked by the approval gate.

---

## 6. Timeline of What Actually Happened

| Date | Event | Outcome |
|------|-------|---------|
| ~May 15 | `scripts/render_pdf.py` built | Working PDF renderer (original) |
| May 18 | Presentation skill audit | 20 capabilities assessed, 5 WORKING |
| May 18 | Build proposals documented | 8 priorities ranked, PARKED for review |
| May 18 | `skills/visual_production/` built | Magazine pipeline: WeasyPrint + OpenRouter image gen |
| May 18 | TPS v0.1 scaffolding | 40+ files in trevor-presentational-suite/ |
| May 19 | TPS planner + orchestrator + 20 generators | Full architecture, never production-tested |
| May 19 | TPS API server + DB + migrations | FastAPI with full ORM stack |
| May 19 | 28 Opus 4.7 routing calls | ~$4.50 spent on planning that never executed |
| May 19 | Brazil flagship (v2) via Opus | 3x retries at $0.26/call, finally produced |
| May 20 | **You asked me to diagnose** | This document |

**No TPS output files exist.** No generated images, no PDFs, no slides. Zero production runs.

---

## 7. Root Causes (Prioritized)

### Primary: No Complete End-to-End Path
Four systems were built, but none has a working, tested path from brief → visual output. TPS has the most complete architecture but is blocked by:
- Missing FAL_KEY (all image gen fails)
- Missing plotly/python-pptx/d2 (charts, slides, diagrams fail)
- Approval gate blocks non-TTY execution
- No production test ever run

### Secondary: Architecture Proliferation
Four separate systems instead of one:
1. Original `scripts/render_pdf.py`
2. `skills/visual_production/` (magazine PDF + image gen)
3. `trevor-presentational-suite/` (everything-including-kitchen-sink)
4. `tasks/render_briefing_visuals.py` (daily brief visual)

Each has different conventions, error handling, and dependency requirements.

### Tertiary: Cost Inefficiency
The TPS planner routed through Opus 4.7 for a classification task that DeepSeek V4 Flash ($0.14/M) or a rule-based fallback could handle. This wasted ~$4.50 in development.

### Quaternary: Missing API Keys and Dependencies
6+ missing API keys and 5+ missing system dependencies were never installed. The TPS was designed assuming all would be available, but only 3 of 10+ API keys and 4 of 9+ dependencies were actually present.

---

## 8. What Actually Works Today (and Doesn't)

| Capability | Works? | How |
|-----------|--------|-----|
| Original PDF renderer (`scripts/render_pdf.py`) | ✅ | WeasyPrint, branded template |
| Visual production magazine PDF | ✅ | WeasyPrint + editorial CSS |
| Mermaid → PNG (local mmdc) | ✅ | All systems |
| Mermaid → PNG (mermaid.ink API) | ✅ | Fallback path |
| Graphviz DOT → PNG | ✅ | visual_production |
| SVG → PNG (CairoSVG) | ✅ | visual_production |
| Matplotlib charts | ✅ | All systems |
| Mapbox static maps | ✅ | TPS mapbox_gen (MAPBOX_TOKEN set) |
| TPS planner (Opus 4.7) | ✅ | Works, but expensive and unnecessary |
| **Image generation (Flux/Ideogram/Recraft)** | ❌ | FAL_KEY not set |
| **Plotly charts** | ❌ | Not installed |
| **PPTX slides** | ❌ | python-pptx not installed |
| **D2 diagrams** | ❌ | d2 binary not installed |
| **TPS execution > $0.50** | ❌ | Approval gate blocks non-TTY |
| **TPS API server** | ❌ | Never started |
| **TPS database** | ❌ | Never initialized |

---

## 9. Recommended Path Forward

### Option A: Strip Down to What Works (Recommended)
1. Delete or archive `trevor-presentational-suite/` (it's over-engineered and never ran)
2. Keep `skills/visual_production/` as the visual pipeline — it's simpler, self-contained
3. Keep `scripts/render_pdf.py` as the legacy PDF path
4. Keep `tasks/render_briefing_visuals.py` for daily brief Mermaid render
5. Set a clear routing rule: visuals are **Tier-3** (hardcoded matplotlib/Mermaid/WeasyPrint), not LLM-planned
6. Add a single `--images` flag to the existing pipeline for optional cover art via GenViral or visual_production

**Effort:** 2 hours to archive, 1 hour to test working paths.

### Option B: Fix TPS for Production
1. Install missing deps: `pip install plotly python-pptx && brew install d2`
2. Set FAL_KEY or re-route image gen through OpenRouter (OPENROUTER_API_KEY already works)
3. Fix approval gate for non-TTY auto-approval under configurable threshold
4. Run a single end-to-end test
5. Add the planner to llm_gate with routing rule: `visual_planning → deepseek/deepseek-v4-flash` (Tier-3, not Opus)
6. Remove the FastAPI/database layer unless you actually need a multi-user API

**Effort:** 4-8 hours. Risk: continued bloat.

### Option C: Abandon Custom Visual Stack Entirely
1. Archive all four systems
2. Use GenViral Studio API (already working with `GENVIRAL_API_KEY`) for all AI-generated visuals
3. Use matplotlib directly for data charts (not through TPS)
4. Use Mapbox Static API directly for maps (not through TPS)
5. The daily brief already has a working GenViral pipeline for social — extend it to PDF

**Effort:** 1-2 hours to wire.

---

## 10. Lessons Learned

1. **Build a working end-to-end path before adding generators.** TPS had 20 generators and zero working output. Start with one (matplotlib charts), prove pipeline, then expand.

2. **Route visual planning to the cheapest capable model.** Mapping a brief to "needs map + chart + diagram" is Tier-3 classification, not Tier-1 strategic reasoning. The rule-based fallback planner is actually better than the LLM planner for this task — it's deterministic and costs $0.00.

3. **API keys are infrastructure, not configuration.** If a generator needs FAL_KEY but it's not set, the generator is broken, not "configurable." Either implement a permanent fallback or don't add the generator.

4. **Approval gates that block headless execution are footguns.** If the system runs on a server or via cron, the approval gate must have a sensible auto-approve path.

5. **One working PDF + one working image gen path > 20 half-working generators.** The original `scripts/render_pdf.py` (WeasyPrint, 50 lines) produced the only actual PDF output. Everything else was speculative.

---

## Appendix A: File Inventory

### visual_production skill (working)
```
skills/visual_production/SKILL.md
skills/visual_production/scripts/format_magazine.py
skills/visual_production/visual_production/__init__.py
skills/visual_production/visual_production/router.py          # Entry point
skills/visual_production/visual_production/pipeline.py         # Core pipeline
skills/visual_production/visual_production/schemas.py          # Dataclasses
skills/visual_production/visual_production/prompt_builder.py   # LLM prompt assembly
skills/visual_production/visual_production/nano_prompts.py     # Prompt templates
skills/visual_production/visual_production/quality_gate.py     # Post-render validation
```

### trevor-presentational-suite (never production-tested)
```
trevor-presentational-suite/
├── api/server.py              # FastAPI app (never started)
├── api/routes.py              # REST endpoints (never tested)
├── api/webhook.py             # Webhooks (never tested)
├── core/orchestrator.py       # Plan executor (never exercised)
├── core/planner.py            # LLM art director (ran, wasted $)
├── core/schemas.py            # 20+ pydantic models
├── core/approval_gate.py      # Blocks non-TTY execution
├── core/config.py             # YAML-loaded config
├── core/cost_estimator.py     # Per-asset cost estimation
├── core/style_director.py     # Brand token injection
├── core/provenance.py         # Audit trail (never populated)
├── core/cache.py              # Asset caching
├── core/ingest.py             # Brief ingestion
├── core/exceptions.py         # Error types
├── generators/ (20 files)     # Generator implementations
├── deliverables/ (6 files)    # Output builders
├── db/engine.py               # SQLAlchemy engine (never connected)
├── db/models.py               # ORM models (never migrated)
├── db/migrations/             # Alembic migrations (never run)
├── brand.yaml                 # Full brand spec (never applied)
├── providers.yaml             # Provider catalog (outdated)
├── setup-providers.sh         # Setup script (never run)
├── requirements.txt           # 8 pip packages
└── tests/run_all.py           # Test suite (probably nothing passes)
```

### Other
```
scripts/render_pdf.py           # Original PDF renderer (working)
scripts/render_slides.py        # PPTX stub (deferred)
tasks/render_briefing_visuals.py # Daily brief visual renderer (partial)
```

---

## Appendix B: LLM Routing Log (TPS Planner Calls)

All routed as `flagship_document` → Opus 4.7:

| Time (UTC) | Estimated Cost | Target Words | Notes |
|-----------|---------------|--------------|-------|
| 2026-05-19 22:41 | $0.094 | 1,800 | audience_family_office |
| 2026-05-19 22:42 | $0.094 | 1,800 | Retry |
| 2026-05-20 02:51 | $0.26 | 5,000 | 3 scenarios |
| 2026-05-20 02:52 | $0.21 | 4,000 | has_recommendations |
| 2026-05-20 03:08 | $0.21 | 4,000 | Retry |
| 2026-05-20 03:09-03:43 | 19× $0.01-0.26 | 61-5,000 | Repeated retries with varying targets |

**Total:** ~$4.50 estimated, all on Opus 4.7, all for tasks that should use V4 Flash.

---

*End of diagnostic. Ready for principal review and decision on path forward.*
