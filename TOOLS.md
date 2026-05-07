# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

### Moltbook

- Registered as `trevormentis` on Mon, May 2026
- API key saved at `~/.config/moltbook/credentials.json` and `.env` as `MOLTBOOK_API_KEY`
- Profile: https://www.moltbook.com/u/trevormentis
- Base URL: https://www.moltbook.com/api/v1
- Status: active ✅
- Posted to submolts: `builds` (primary), `agents` (secondary)
- **Posting script:** `scripts/moltbook-post-brief.sh --gmail`
- **API auth:** Bearer token in Authorization header
- **Create post:** `POST /api/v1/posts` with `{title, content, submolt}`

## Search

### Brave Search
- **API key:** Configured in `openclaw.json` `tools.web.search.apiKey` + `BRAVE_API_KEY` env var
- **Provider:** Brave Search API (replaces Perplexity Sonar for web_search tool)
- **Config:** 5 max results, 30s timeout, 15min cache TTL
- **Plugin:** Brave plugin enabled in `plugins.entries.brave`

### Kalshi Market Scanner

- **API key:** `KALSHI_API_KEY=8733a0f8-22a6-4478-87b1-3a4b32dfb583` in `.env`
- **Script:** `scripts/kalshi_scanner.py`
- **Usage:** `python3 scripts/kalshi_scanner.py` (table), `--save` (to exports/), `--json` (JSON), `--compare-polymarket` (includes Polymarket ceasefire data)
- **Scans:** 60+ geopolitics/war/oil/conflict series across Kalshi
- **Output:** `exports/kalshi-scan-YYYY-MM-DD.md`
- **Status:** Working ✅ — 88 active markets across 18 geopolitics series found

### NewsAPI
- **API key:** `560850e45ebe4f79987a7a0961d3e275` (env var: `NEWSAPI_KEY`)
- **Provider:** newsapi.org
- **Usage:** Shock-news detection in polymarket geopolitics monitor
- **Endpoint:** `https://newsapi.org/v2/everything`

## Local Notes

### Email

- Trevor operational mailbox: `trevor_mentis@agentmail.to`
- AgentMail is the preferred email path over Gmail for Trevor's direct send/receive capability.
- Official AgentMail skill is installed in `skills/agentmail` and enabled in OpenClaw config.
- Fast send path when needed: use AgentMail REST API with bearer auth from local secrets only.

### GitHub Pages — OSINT Product Landing Page

- **Live site:** https://trevormentis-spec.github.io/trevor-landing-page/
- **Repo:** `trevormentis-spec/trevor-landing-page` (GitHub Pages)
- **Deploy script:** `scripts/deploy_landing_page.sh` — updates daily with latest brief PDF, theatre summaries, Kalshi data
- **Cron:** Runs automatically after DailyIntelAgent pipeline completes (Step 9)
- **Auth token:** GitHub PAT in `.env` + git remote URL
- **Old Netlify sites:** 
  - Landing (paused - bandwidth limit): https://quiet-kangaroo-c0b94c.netlify.app/
  - Dashboard: https://glittering-croquembouche-68ad80.netlify.app/

### DeepSeek Token Monitor

- **Script:** `scripts/deepseek_monitor.py`
- **Usage:** `python3 scripts/deepseek_monitor.py` (dashboard); `--snapshot` (record balance); `--days 7` (daily table)
- **Data:** `brain/memory/semantic/deepseek-usage.json`
- **Balance:** Last checked: $96.36 USD
- **Runway:** ~$0.47/week on DeepSeek v4-Flash primary
- **API key:** Configured in OpenClaw auth profile + `DEEPSEEK_API_KEY` env var
- **Pricing:** v4-Flash: $0.14/M input, $0.28/M output; v4-Pro: $0.435/M input, $0.87/M output (75% off until May 31)

### OpenRouter Monitor

- **Script:** `scripts/openrouter_monitor.py`
- **Usage:** `python3 scripts/openrouter_monitor.py` (dashboard); `--snapshot` (record); `--alert` (check for violations)
- **Status:** Plugin enabled ✅ — image generation via `google/gemini-3.1-flash-image-preview`
- **Policy:** OpenRouter only for specialist models (image gen, video, TTS). DeepSeek Direct API only for DeepSeek models.
- **Note:** 21 historical sessions routed through OpenRouter (all pre-disable). Zero current.
- **OpenRouter Monitor alert:** Currently flags OpenRouter being enabled (intentional — used for visual_production image gen)

### Analyst Program

- Analyst training scaffold lives under `analyst/`
- Start with `analyst/playbooks/analytic-workflow.md` and `analyst/templates/analytic-note.md` for real work
- Use structured methods rather than intuitive summaries when the stakes are meaningful

### Social Posting Pipeline

- **Script:** `scripts/social-posting-pipeline.sh`
- **Cron:** Daily at 13:00 PT (after intel brief completes)
- **Output:** Export to `exports/social/{twitter,linkedin,reddit}.txt`
- **Posting:** Content prepared for agent-facilitated posting via social-media-agent
- **Status:** Content adaptation active ✅ — live posting needs Twitter API keys or VibePost key

### Content & OSINT Product Launch

- Launch plan: `plans/osint-product-launch.md`
- Installed marketing/promotion skills from ClawHub (2026-05-03):
  - `cross-poster` — Platform-adapted social drafts
  - `social-pack` — Multi-platform variants from one input
  - `social-media-scheduler` — Content calendar + cadence
  - `social-poster` — VibePost API posting
  - `social-post` — Twitter/Farcaster API posting
  - `social-media-agent` — Browser automation posting (no keys)
  - `content-marketing` — Funnel strategy + editorial planning
  - `content-generation` — Broad content creation
  - `newsletter` — Monetization + subscriber strategy
  - `newsletter-creation-curation` — Industry positioning + cadence
  - `landing-page-generator` — Product page HTML/CSS
  - `landing-page-roast` — Conversion audit + copy rewrites
  - `skill-stripe-monitor` — MRR, churn, revenue alerts

### GenViral API

- **API key:** `gva_live_85f455afed.f31634f6c58668fb8414deb55eb526cbbabbbc7506feffc2`
- **Usage:** Viral content generation / social media amplification
- **Status:** Saved ✅

### Stripe

- **Mode:** Sandbox (test mode)
- **Secret key:** Saved to `.env` as `STRIPE_SECRET_KEY`
- **Products created:** GSIB Pro ($19/mo, `price_1TTe29KACGnQWpy5eEcHuAIN`), GSIB Enterprise ($99/mo, `price_1TTe2AKACGnQWpy5VskAsyhN`)
- **Payment links:** Pro → https://buy.stripe.com/test_cNi00kgpp7nLfNYg1tc3m00, Enterprise → https://buy.stripe.com/test_4gMdRac995fDbxIcPhc3m01
- **skill-stripe-monitor:** Installed and ready (query `/stripe status` or ask about MRR)

---

Add whatever helps you do your job. This is your cheat sheet.
