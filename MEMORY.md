# MEMORY.md

## Core Identity

- Assistant name: Trevor
- Trevor stands for: Threat Research and Evaluation Virtual Operations Resource
- User name: Roderick

## Durable Decisions

- Trevor's durable memory is file-backed in the workspace.
- Trevor's workspace is backed up to GitHub at `git@github.com:trevormentis-spec/OpenClawTrevorMentis.git` (updated 2026-05-01).
- Trevor is being developed toward a more brain-like memory architecture using layered memory and cautious learning.
- Trevor's operational email path is AgentMail via `trevor_mentis@agentmail.to` using the official AgentMail skill.
- Trevor should persistently monitor the AgentMail inbox on an asynchronous cadence and surface only meaningful new emails.
- Trevor has an active long-term analyst training program in `analyst/` covering structured analytic tradecraft, source evaluation, security studies, and analytic writing.
- For future integrations, Trevor should check existing skills/integrations before building custom alternatives.

## Durable Decisions — Social Posting

- **Content source: the daily intel brief analysis from `tasks/news_analysis.md`.** The brief's structured intelligence (BLUF, key judgments, sections) is the source material for all social content.
- **Original visuals via GenViral Studio AI.** No PDF page screenshots ever. Each platform gets AI-generated slideshows with proper text overlays, platform-appropriate aspect ratios, and native captions.
- **No standalone promotional content.** No product launch posts, no methodology posts, no landing page marketing — nothing that isn't the daily intel brief itself.
- **Platforms:** LinkedIn (4:5 slideshow, professional), X/Twitter (16:9 slideshow, concise), TikTok (9:16 slideshow, draft mode).
- **Pipeline:** `scripts/genviral-post-brief.sh` with GenViral API. Runs daily at 13:30 PT via cron. Performance tracked in `skills/genviral/workspace/performance/log.json`.

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
- **Products created:** GSIB Pro ($19/mo, `price_1TTe29KACGnQWpy5eEcHuAIN`), GSIB Enterprise ($99/mo, `price_1TTe2AKACGnQWpy5VskAsyhN`)
- **Payment links:** Pro → https://buy.stripe.com/test_cNi00kgpp7nLfNYg1tc3m00, Enterprise → https://buy.stripe.com/test_4gMdRac995fDbxIcPhc3m01
- **skill-stripe-monitor:** Registered in OpenClaw config with `STRIPE_SECRET_KEY` env var
- **Status:** Live on landing page. Ready for subscriptions when key is switched to live (`sk_live_...`).

### GenViral Social Posting
- **Accounts:** 6 platforms connected — LinkedIn, TikTok, Twitter/X, Instagram, YouTube, Pinterest
- **defaults.yaml:** Updated with all account IDs + platform-specific presets (aspect ratio, style, slide count per platform)
- **Pipeline:** `genviral-post-brief.sh` generates AI slideshows per platform from daily analysis
- **Status:** Verified working (3 posts for 2026-05-12). Posted to build submolts daily via `moltbook-post-brief.sh`.

### Buttondown Newsletter
- **Newsletter:** "Daily Intelligence Brief" at https://buttondown.com/trevormentis
- **API key:** `c2f514c5-560b-4fc6-8234-54bf4e14b142` (registered in OpenClaw config)
- **Pipeline script:** `scripts/buttondown-send.py` + `scripts/buttondown-send.sh` — reads `tasks/news_analysis.md`, converts to HTML, publishes
- **Landing page embed:** Buttondown subscribe form on deployed GitHub Pages
- **Status:** ✅ Verified — test email published successfully (ID: em_1jsvm3hsnd87v8egdg0xp5a5e0)

### Landing Page (GitHub Pages)
- **URL:** https://trevormentis-spec.github.io/trevor-landing-page/
- **Features:** Stripe pricing (Pro $19/mo + Enterprise $99/mo), Buttondown subscribe form, Kalshi prediction market table, latest brief PDF download, theatre coverage grid
- **Deploy:** `scripts/deploy_landing_page.sh` runs after daily brief cron. Sources: `_build_landing.py` injects theatre summaries, Kalshi data, latest PDF, and issue date.
- **Status:** ✅ Live and auto-deployed daily

### Netlify Form Webhook
- **Script:** `scripts/netlify-form-webhook.py` — receives form POSTs, saves subscribers to `exports/subscribers.json`, forwards to AgentMail inbox
- **Status:** Not actively used — landing page on GH Pages uses Buttondown embed for subscribe (forms go directly to Buttondown). Available if needed.

## Durable Decisions — Runtime Architecture

### Tiered Cognition Routing (2026-05-12)
- **Tier-1 (frontier):** Opus 4.7 via OpenRouter — executive summary + red-team adversarial analysis
- **Tier-2 (fast/cheap):** DeepSeek V4 Flash via DeepSeek Direct — 6 regional analyses (Europe, Asia, Middle East, North America, South America, Global Finance)
- **Justification:** Regional analysis is data synthesis (works fine on V4 Flash). Exec summary needs strategic reasoning (requires frontier model). Cost reduction: ~$2.09 → ~$0.56 per run.
- **Status:** Operational in daily-brief-cron.sh

### Memory → Cognition Pipeline (2026-05-12)
- **Step 0b:** Brain recall captures yesterday's memory and formats as `analysis/brain-recall.md`
- **Step 0a:** Procedural memory loader reads `brain/memory/procedural/` for learned procedures
- **Injection:** Both files are piped as `--recall` and `--procedural` flags to `analyze.py`, which injects them into the system prompt as `=== MEMORY CONTEXT ===` / `=== PROCEDURAL MEMORY ===` blocks
- **Best-effort:** If recall fails or times out, pipeline continues without
- **Status:** Operational

### Postdiction / Calibration (2026-05-12)
- `scripts/postdict.py` checks yesterday's 5 key judgments against today's evidence using Opus 4.7
- Each judgment scored: correct / incorrect / unresolved
- Running calibration tracked in `brain/memory/semantic/calibration-tracking.json`
- Broken down by confidence band and region
- **Not yet fed back** into next day's confidence banding — that's the next step
- **Status:** Operational (recording), not yet applied (feedback loop still open)

### Continuous Monitor (2026-05-12)
- `scripts/continuous_monitor.py` runs hourly between cron fires
- Checks: Kalshi swings (>10pt), brief existence, AgentMail inbox
- Writes findings to `brain/memory/episodic/YYYY-MM-DD.jsonl`
- **Design:** Called from cron (not persistent daemon), avoids supervisor dependency
- **Status:** Operational

### Technical Debt Ledger
- `brain/memory/semantic/tech-debt.md` — persistent tracking of all known tech debt
- Fields: severity, discovery date, impact, resolution date
- Currently tracks 21 items (8 resolved, 13 open)
- **Status:** Operational

### Adaptive Collection (2026-05-12)
- `scripts/collection_state.py` — persistent state tracking source utilization and region activity
- **Post-analysis:** updates source citation counts and per-region incident volume
- **Pre-collection:** `--predict-caps` outputs dynamic per-region caps (active regions get cap=20, quiet regions get cap=3-10)
- `collect.py --adaptive-caps` reads the caps and fetches proportionally
- Source utilization tracked: if a source is fetched but never cited, it's flagged
- **Status:** Operational — closed the analysis→collection→analysis adaptive cycle

### Config Validation
- `scripts/validate_config.py` — validate openclaw.json before any edit
- Checks: top-level keys, skill entry structure, env var naming
- **Status:** Operational (manual call — not yet wired into edit workflow)

## Durable Decisions — Pipeline & Operations
- [2026-05-06] **`analyze.py` max_tokens=8192** for DeepSeek V4 Pro calls.
  V4 Pro's reasoning token consumption eats default 2000 tokens leaving empty content.
  Must use 8192+ for call_deepseek() to return substantive analysis.
  See `analyst/pipeline/analyze.py` for the fix.
- Social posting generates original visuals via GenViral Studio AI from the daily intel brief analysis in `tasks/news_analysis.md`.
- [2026-05-11] **Pipeline integration is separate from script fixes.** The cron pipeline
  (`daily-brief-cron.sh`) calls scripts with its OWN argument structure at 05:00 PT daily.
  Manual test runs do not affect automated delivery. After changing render/map/chart scripts,
  ALSO update the pipeline shell script to pass the new flags.
- [2026-05-11] **Delivery schedule:** GSIB arrives ~07:00 PT. 4 Daily Briefings arrive at
  08:00 PT. Cron IDs: GSIB = 250765ae-d951-490c-b3d0-109fca300053, 4 Briefings =
  9ee44803-223c-45cc-ad59-f404919bd5f9.

- [2026-05-11] **Maps removed from GSIB.** After 9 failed iterations (v1-v9),
  maps were removed from the product entirely. Replaced with agent-first structured JSON
  published to Moltbook (agents submolt) + API endpoint. The agent brief at
   and 
  is the primary agent-facing format. Maps disabled per Roderick's decision.