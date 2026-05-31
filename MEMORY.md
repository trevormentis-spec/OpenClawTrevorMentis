# MEMORY.md

## Standing Knowledge

## Core Identity

- Assistant name: Trevor
- Trevor stands for: Threat Research and Evaluation Virtual Operations Resource

## Lessons Learned

### 2026-05-29: Exec Summary Prompt Template Drift — Dead Placeholder Caused CRITICAL QC Failure

**Problem:** The exec summary prompt template (`deepseek-prompts.md`) had a dead `{russia_eurasia_json}` placeholder referencing "RUSSIA & EURASIA" but `analyze.py`'s `REGIONS_ORDER` does not include `russia_eurasia`. The placeholder was never replaced, leaving literal text in the prompt. The model interpreted the dead placeholder as instructions and produced a Russia & Eurasia analysis instead of an executive summary, leaving BLUF, context, and top-level KJs as N/A.

**Secondary issue:** The template was also missing `{east_asia_json}` and `{south_asia_json}` placeholders despite both being in `REGIONS_ORDER`, meaning East Asia and South Asia data was never passed to the exec summary model.

**Tertiary issue:** Different regional analysis models produce KJs with inconsistent field names (`statement` vs `prediction` vs `judgment` vs `event`; `prediction_pct` vs `numeric_probability` vs `probability_numeric` vs embedded in `confidence` string). The `opus_qc_review.py` QC script only checked `kj.get('statement', 'N/A')` and `kj.get('prediction_pct', '?')`, causing false N/A detection for well-populated regions.

**Fix applied:**
1. Removed `{russia_eurasia_json}` section from exec summary template
2. Added `{east_asia_json}` and `{south_asia_json}` sections
3. Updated section count from "TEN" to "13 REGIONAL ASSESSMENTS"
4. Regenerated `exec_summary.json` with corrected prompt
5. Added KJ field name normalization to `opus_qc_review.py` (handles `prediction`, `judgment`, `event`, `numeric_probability`, `probability_numeric`, and `confidence` string parsing)
6. Re-delivered corrected brief to Roderick

**Lesson:** Template files with hardcoded region lists must be kept in sync with code-level `REGIONS_ORDER`. Every prompt placeholder must have a corresponding replacement in code. Deploy a smoke test that verifies all prompt placeholders can be replaced at pipeline startup.

## Durable Decisions
- Trevor should persistently monitor the AgentMail inbox on an asynchronous cadence and surface only meaningful new emails.
- [2026-05-25] **Autonomous Kalshi execution authority granted by Roderick.** Trevor may autonomously execute Kalshi trades within guardrails without per-trade approval. Guardrails: quarter-Kelly sizing, 5% max per position, 30% max exposure, -10% daily loss cap, -20% max drawdown halt, minimum 5pt edge requirement. Simmer/Polymarket trades to be added once backend is stable. Trade reports sent after execution.
- [2026-05-26] **Strategic direction codified** in `memory/strategic-direction.md`. Trevor is persistent adaptive geopolitical intelligence infrastructure, NOT a chatbot/briefing engine/cron generator. All future structural decisions governed by that document.
- Trevor has an active long-term analyst training program in `analyst/` covering structured analytic tradecraft, source evaluation, security studies, and analytic writing.
- For future integrations, Trevor should check existing skills/integrations before building custom alternatives.

## Durable Decisions — Pipeline Reliability
- [2026-05-27] **DeepSeek V4 Pro direct API hangs on payloads >20KB.** Tier-1 exec summary calls must use OpenRouter, not DeepSeek direct. Changed both default providers from `deepseek` to `openrouter` in `analyze.py` and `orchestrate.py`. If a direct DeepSeek call is needed, keep payloads under 16KB and avoid `json_object` response_format. Regional analysis via OpenRouter has been reliable.

## Durable Decisions — Social Posting

## Durable Decisions - Orchestration
- [2026-05-01] **Canonical routing is DeepSeek Direct API.** OpenRouter is disabled.
  Primary `deepseek/deepseek-v4-flash`, escalation `deepseek/deepseek-v4-pro`,
  resilience fallback chain `deepseek-chat` → `deepseek-v4-pro` → `myclaw/minimax-m2.7`.
- [2026-05-01] `ORCHESTRATION.md` v3.0 is the single source of truth for routing.
  REBUILD_ORCHESTRATION.md archived to `docs/archive/`.
- Diagrams (Mermaid/SVG) preferred over image generation.
- Memory retrieval limited to top 3 relevant chunks for cost optimization.

## Durable Decisions — Integrations Built

### Stripe (Test Mode)

### GenViral Social Posting

### Buttondown Newsletter
- **Status:** ✅ Verified — test email published successfully (ID: em_1jsvm3hsnd87v8egdg0xp5a5e0)

### Landing Page (GitHub Pages)

### Netlify Form Webhook
- **Script:** `scripts/netlify-form-webhook.py` — receives form POSTs, saves subscribers to `exports/subscribers.json`, forwards to AgentMail inbox
- **Status:** Not actively used — landing page on GH Pages uses Buttondown embed for subscribe (forms go directly to Buttondown). Available if needed.

## Durable Decisions — Runtime Architecture

### Tiered Cognition Routing (2026-05-12)

### Memory → Cognition Pipeline (2026-05-12)
- **Status:** Operational

### Postdiction / Calibration (2026-05-12)
- **Not yet fed back** into next day's confidence banding — that's the next step
- **Status:** Operational (recording), not yet applied (feedback loop still open)

### Continuous Monitor (2026-05-12)
- **Status:** Operational

### Technical Debt Ledger

### Unified Quality Gate Pipeline (2026-05-23)
- **Status:** ✅ Operational — closes self-assessment gap (Principal Review item 7).

### Adaptive Collection (2026-05-12)
- Source utilization tracked: if a source is fetched but never cited, it's flagged
- **Status:** Operational — closed the analysis→collection→analysis adaptive cycle

### Config Validation
- `scripts/validate_config.py` — validate openclaw.json before any edit
- Checks: top-level keys, skill entry structure, env var naming
- **Status:** Operational (manual call — not yet wired into edit workflow)

## Durable Decisions — Pipeline Constraints (2026-05-22)
  Telegram RSS (t.me/s), Perplexity Sonar social (only if all other paths fail).

## Durable Decisions — Pipeline & Operations
- [2026-05-06] **`analyze.py` max_tokens=8192** for DeepSeek V4 Pro calls.
- [2026-05-11] **Pipeline integration is separate from script fixes.** The cron pipeline
  (`daily-brief-cron.sh`) calls scripts with its OWN argument structure at 05:00 PT daily.
  Manual test runs do not affect automated delivery. After changing render/map/chart scripts,
  ALSO update the pipeline shell script to pass the new flags.
- [2026-05-11] **Delivery schedule:** GSIB arrives ~07:00 PT. 4 Daily Briefings arrive at
  08:00 PT. Cron IDs: GSIB = 250765ae-d951-490c-b3d0-109fca300053, 4 Briefings =
  9ee44803-223c-45cc-ad59-f404919bd5f9.

- [2026-05-11] **Maps removed from GSIB.** After 9 failed iterations (v1-v9),

## Durable Decisions — Autonomy Framework
- [2026-05-13] **Autonomy confirmed by Roderick.** Full operational autonomy for:
  Trevor only pings for genuine anomalies, interesting intel finds, or things that need
  human judgment.
- [2026-05-23] **Autonomous brief-quality authority granted.** Trevor may self-initiate
  architectural changes, budget impact, or uncertain fixes.
- [2026-05-23] **AGENTS.md updated** — Brief Quality autonomous fix authority
  codified. Analyst rotation now includes QC alert check and brief self-review.

## Durable Decisions — Perplexity Benchmark
- [2026-05-14] **Perplexity GSIB is the quality benchmark.** A Perplexity-produced Global
  voice, direct address, and trade-inline style. Regional prompt template updated with
  `{prediction_market_data}` and `{standing_assessment}` fields.

## Durable Decisions — Kalshi Trading Auth (2026-05-27)
- Active strategy: Daedalus — scaled WTI hedge from 17→48 contracts, added to counter Iran concentration.

## Durable Decisions — Mexico Analysis Framework (2026-05-15)

### 4-Layer Huachicoleo Model
4. **Political Risk** — how the resource theft destabilizes governance

### 6-Axis Cartel Framework
Criminal-faction-universal assessment schema (zero Mexico-specific assumptions):
- Territory / Revenue / Succession / Alliances / Tempo / State Penetration

### Key Structural Findings

### Collection Gaps (Tracked)
- Pemex operational data not yet ingested for pipeline tap counts

## 2026-05-25 — Daily Text Brief

### Pipeline completed (with manual intervention)

### Issues encountered & fixed:

### Postdiction results (yesterday's 5 predictions):
- 1 confirmed, 4 not yet testable, 0 incorrect

### Lessons:
- Pipeline ~25 minutes end-to-end (5min collect + 20min analyze). Must run backgrounded.
- guard_pipeline.py band definitions need periodic audit — duplicated ranges cause false quality blocks.

### 2026-05-28: QC Watchdog False Alarm — Pre-Final Assembly Timing

**Fix:** Before investigating CRITICAL QC alerts, verify (1) final brief exists at `final/brief.md`, (2) its timestamp post-dates QC timestamp, (3) substantive content (lines + bytes). If QC is stale, clear the alert.

**Recommendation:** Add a completion-flag file (e.g., `.brief_complete`) written by the pipeline after assembly. QC watchdog checks for this file before running.

## 2026-05-31 — Philby/Kalshi Trading System — TEARDOWN
All trading code archived to /home/ubuntu/.openclaw/workspace/archive/philby-trading-2026-05-31
Trading crons disabled. Auth keys preserved in .env.
See archive//home/ubuntu/.openclaw/workspace/archive/philby-trading-2026-05-31 for full code + audit trail.
