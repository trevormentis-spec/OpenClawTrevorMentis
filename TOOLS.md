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
- API key saved at `~/.config/moltbook/credentials.json`
- Profile: https://www.moltbook.com/u/trevormentis
- Base URL: https://www.moltbook.com/api/v1
- Status: active ✅

## Search

### Brave Search
- **API key:** Configured in `openclaw.json` `tools.web.search.apiKey` + `BRAVE_API_KEY` env var
- **Provider:** Brave Search API (replaces Perplexity Sonar for web_search tool)
- **Config:** 5 max results, 30s timeout, 15min cache TTL
- **Plugin:** Brave plugin enabled in `plugins.entries.brave`

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

### Netlify — Project Sentinel Dashboard

- **Dashboard URL:** https://glittering-croquembouche-68ad80.netlify.app/
- **Auth token:** stored in `.env` as `NETLIFY_AUTH_TOKEN` (not committed to git)
- Source content lives in `exports/` directory — HTML files get deployed

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

---

Add whatever helps you do your job. This is your cheat sheet.
