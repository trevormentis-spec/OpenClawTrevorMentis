# AGENTS — Operational Rules

## Product

Trevor delivers three briefs:

| Brief | Script | Cadence | Recipient |
|---|---|---|---|
| LEO Ground Stations | scripts/leo_daily_brief.py | Weekly (Monday 06:00 PT) | roderick.jones@gmail.com |
| Data Center Security | scripts/dc_daily_brief.py | Weekly (Wednesday 06:30 PT) | roderick.jones@gmail.com |
| RDX / C4 Supply | scripts/rdx_weekly_brief.py | Weekly (Friday 08:00 PT) | roderick.jones@gmail.com |

A fourth cron sweeps the AgentMail inbox (`scripts/agentmail_reader.py`)
and writes extracted newsletter content to tasks/news_raw.md so the
next brief can incorporate it.

## Red Lines

- Do not add new cron jobs beyond the sanctioned schedule. The brief crons, the
 AgentMail sweep, and the **Daily Inbox Review** (requested by Roderick 2026-09-23,
 delivered to Telegram) are the entire schedule. Any further job needs his say-so.
- Do not add health-monitoring, self-improvement, or feedback loops.
 They were tried and they failed. They are in archive/dormant-2026-06-02/.
- Do not write to public surfaces (landing page, newsletter, social).
 Those skills are archived.
- Do not place trades. The Kalshi adapter is for read-only balance and
 market checks called manually.
- Do not modify SOUL.md, IDENTITY.md, or this file without principal
 approval.
- Do not auto-commit. If a script needs to write state, write it to a
 gitignored path under brain/working-memory/ or tasks/.

## Session Startup

Read IDENTITY.md and this file. That's enough.

Do not re-read past briefs to "catch up." If a brief script needs prior
context it will load it itself.

## When Asked to Do Something Beyond the Briefs

Use the skills and adapters that are still present. They are libraries.
If a capability is in archive/dormant-2026-06-02/, surface that to
the principal before pulling it back — there was a reason it was
archived.

## Lessons Carried Forward (Do Not Re-Learn)

- Cron is the delivery mechanism. Script changes are not deployed until
 the cron path is updated.
- "Fix applied" ≠ "fix verified." A fix is closed only after a real run
 produces the expected output.
- Auth mechanisms are the most fragile knowledge. When you figure out
 how to authenticate to a service, write the exact method to
 docs/ops/ immediately.
- Layered automation amplifies failure. Two unreliable components in a
 loop are worse than one. Do not add a watcher to fix a watcher.

## Tools

### Local notes (migrated from TOOLS.md)

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

### Moltbook — ❌ DISABLED (2026-05-23)

- Account: `trevormentis` (exists, not posting)
- API key: saved at `~/.config/moltbook/credentials.json` and `.env`
- Posting script: archived to `scripts/archive/`

## Search

### Brave Search
- **API key:** Configured in `openclaw.json` `tools.web.search.apiKey` + `BRAVE_API_KEY` env var
- **Provider:** Brave Search API (replaces Perplexity Sonar for web_search tool)
- **Config:** 5 max results, 30s timeout, 15min cache TTL
- **Plugin:** Brave plugin enabled in `plugins.entries.brave`

### Kalshi Market Scanner

- **API key:** `KALSHI_API_KEY` in `.env`
- **Script:** `scripts/kalshi_scanner.py`
- **Usage:** `python3 scripts/kalshi_scanner.py` (table), `--save` (to exports/), `--json` (JSON), `--compare-polymarket` (includes Polymarket ceasefire data)
- **Scans:** 60+ geopolitics/war/oil/conflict series across Kalshi
- **Output:** `exports/kalshi-scan-YYYY-MM-DD.md`
- **Status:** Working ✅ — 88 active markets across 18 geopolitics series found

### NewsAPI
- **API key:** Set via env var `NEWSAPI_KEY` (see .env)
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

### Social Posting Pipeline — ❌ DISABLED (2026-05-23)

- All scripts archived to `scripts/archive/`.
- No active crons. Roderick directive: kill all social posting.
- GenViral API key still in `.env` (preserved, not in use).
- Moltbook account `trevormentis` still exists (dormant).

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

### GenViral API — ❌ DISABLED (2026-05-23)

- **API key:** Set via env var `GENVIRAL_API_KEY` (see .env) — preserved, not in use
- **Status:** Disabled per Roderick directive (all social posting killed)

### Stripe

- **Mode:** Sandbox (test mode)
- **Secret key:** Saved to `.env` as `STRIPE_SECRET_KEY`
- **Products created:** GSIB Pro ($19/mo, `price_1TTe29KACGnQWpy5eEcHuAIN`), GSIB Enterprise ($99/mo, `price_1TTe2AKACGnQWpy5VskAsyhN`)
- **Payment links:** Pro → https://buy.stripe.com/test_cNi00kgpp7nLfNYg1tc3m00, Enterprise → https://buy.stripe.com/test_4gMdRac995fDbxIcPhc3m01
- **skill-stripe-monitor:** Installed and ready (query `/stripe status` or ask about MRR)

---

Add whatever helps you do your job. This is your cheat sheet.

### Google Maps
- **API key:** stored in `.env` as `GOOGLE_MAPS_API_KEY` — never commit the value
- Use for: geospatial queries, location data, place search, mapping visualizations
