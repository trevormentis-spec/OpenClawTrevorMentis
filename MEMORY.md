# MEMORY.md

## Core Identity

- Assistant name: Trevor
- Trevor stands for: Threat Research and Evaluation Virtual Operations Resource
- User name: Roderick

## Durable Decisions
- Trevor should persistently monitor the AgentMail inbox on an asynchronous cadence and surface only meaningful new emails.
- [2026-05-25] **Autonomous Kalshi execution authority granted by Roderick.** Trevor may autonomously execute Kalshi trades within guardrails without per-trade approval. Guardrails: quarter-Kelly sizing, 5% max per position, 30% max exposure, -10% daily loss cap, -20% max drawdown halt, minimum 5pt edge requirement. Simmer/Polymarket trades to be added once backend is stable. Trade reports sent after execution.
- [2026-05-26] **Strategic direction codified** in `memory/strategic-direction.md`. Trevor is persistent adaptive geopolitical intelligence infrastructure, NOT a chatbot/briefing engine/cron generator. All future structural decisions governed by that document.
- Trevor has an active long-term analyst training program in `analyst/` covering structured analytic tradecraft, source evaluation, security studies, and analytic writing.
- For future integrations, Trevor should check existing skills/integrations before building custom alternatives.

## Durable Decisions — Social Posting
- **STATUS: ENABLED (2026-05-24)** — Moltbook reconnected per Roderick directive.
  Agent: trevormentis, 34 karma, 11 followers, 18 following, claimed + active.
  Posts daily brief to r/builds via scripts/moltbook_post.py in pipeline Step 6.
  GenViral + other platforms remain disabled unless explicitly requested.

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
- **analyst/guard_pipeline.py** — rebuilt as the single unified quality gate composing ALL 7 guards:
  0. STRUCTURAL — files present and valid JSON
  1. FABRICATION — unverified contracts/prices/tickers/pct claims (via fabrication_check.py)
  2. THEMES — required theme coverage (via themes_preflight.py, scanning ALL regional files)
  3. CALIBRATION — Sherman Kent band ↔ numeric prediction agreement + single-source cap
  4. COMPLETENESS — no truncation, adequate word count, all sections present
  5. SCOPE — topic within assignment scope (via scope_check.py)
  6. RED_TEAM — forced dissent note exists and is substantive
- **Wired into orchestrate.py** — runs post-analysis, pre-delivery. BLOCK gates stop delivery.
  WARN gates log but proceed. `--block-on-warn` flag available for stricter gating.
- **Theme system broadened** — global keywords added to political_risk, economy_markets, cartel_security.
  New query category "geopolitical_intelligence_brief" for daily brief pipeline.
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
  diagnosis and fixes for daily brief quality failures (model downgrade, regional
  cross-contamination, truncation, quality gate BLOCK, Opus QC FAIL/CRITICAL).
  QC Watchdog cron fires 5 min after delivery (13:10 UTC daily). Alert written to
  tasks/qc-alert.md triggers autonomous fix cycle. Principal surfaced only for
  architectural changes, budget impact, or uncertain fixes.
- [2026-05-23] **AGENTS.md updated** — Brief Quality autonomous fix authority
  codified. Analyst rotation now includes QC alert check and brief self-review.

## Durable Decisions — Perplexity Benchmark
- [2026-05-14] **Perplexity GSIB is the quality benchmark.** A Perplexity-produced Global
  voice, direct address, and trade-inline style. Regional prompt template updated with
  `{prediction_market_data}` and `{standing_assessment}` fields.

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
- **Delivered:** ✅ Text brief sent to roderick.jones@gmail.com via AgentMail (12:45 UTC)
- **Quality gate:** ALL CLEAR 7/7 after fixing calibration band bug
- **Message ID:** `<0100019e5f2ba5df-fd807b8b-0187-40da-a30a-06ba6f4252e0-000000@email.amazonses.com>`
- **Models used:** DeepSeek V4 Pro (10 regions + prediction_markets + red-team), Claude Opus 4.7 (exec summary)

### Issues encountered & fixed:
1. **Exec timeout kills pipeline:** OpenClaw exec sessions SIGTERM long-running processes. Solution: use `nohup` background for pipeline.
2. **Calibration band bug in guard_pipeline.py:** "probable" was mapped to (55, 70) — same range as "likely". Should be (70, 85). Fixed in `analyst/guard_pipeline.py` line 281.
3. **GitHub Pages auth:** Push still failing with "Invalid username or token" — needs new PAT.
4. **BRAVE_API_KEY not set:** Source discovery skipped — non-fatal but means no new sources found.

### Postdiction results (yesterday's 5 predictions):
- 1 confirmed, 4 not yet testable, 0 incorrect

### Lessons:
- Pipeline ~25 minutes end-to-end (5min collect + 20min analyze). Must run backgrounded.
- guard_pipeline.py band definitions need periodic audit — duplicated ranges cause false quality blocks.
