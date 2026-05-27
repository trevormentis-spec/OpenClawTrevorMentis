# Daily Intel Brief — Complete Process

## Schedule (PT = UTC-7 during PDT)

| Time PT | Time UTC | Step | Description |
|---|---|---|---|
| 05:00 | 12:00 | 1a | Calibration directives compiled |
| 05:00 | 12:00 | 1b | Source discovery (new RSS feeds) |
| 05:00 | 12:00 | 1c | Kalshi prediction market scan |
| 05:00 | 12:00 | 1d | Simmer market signal overlay |
| 05:15 | 12:15 | 2 | Orchestrator: collect.py (385+ feeds) → analyze.py (13 regions, V4 Pro) |
| 05:45 | 12:45 | 3 | Quality gate (7 gates: structural, fabrication, themes, calibration, completeness, scope, red-team) |
| 06:00 | 13:00 | 4 | Delivery via AgentMail → roderick.jones@gmail.com |
| 06:10 | 13:10 | 5 | Postdiction (calibration tracking) |
| 06:15 | 13:15 | 6 | Moltbook post (r/builds) |
| 06:20 | 13:20 | 7 | Deploy landing page (GitHub Pages) |
| 06:30 | 13:30 | QC | QC Watchdog fires (checks quality, fires alert if BLOCK/FAIL) |

**Cron ID:** `69d9d778-9de1-4d63-8697-99f0bd13353f`  
**Script:** `/home/ubuntu/.openclaw/workspace/scripts/daily-text-brief.sh`

## 13 Regions (updated 2026-05-22)

| # | Region | Countries | Notes |
|---|---|---|---|
| 1 | europe | 45 | UK, France, Germany, Baltics, Balkans, Ukraine, etc. |
| 2 | north_america | 6 | US, Canada, Mexico, Greenland, St. Pierre |
| 3 | central_america_caribbean | 21 | Guatemala through Panama, Caribbean islands |
| 4 | south_america | 13 | All SA nations + French Guiana |
| 5 | middle_east | 16 | Iran, Israel, Gulf states, Levant |
| 6 | central_asia | 5 | Kazakhstan, Kyrgyzstan, Tajikistan, Turkmenistan, Uzbekistan |
| 7 | south_east_asia | 12 | ASEAN nations + East Timor |
| 8 | oceania | 14 | Australia, NZ, Pacific islands |
| 9 | east_asia | 10 | China, Japan, Korea, Taiwan, Mongolia |
| 10 | south_asia | 8 | India, Pakistan, Bangladesh, Sri Lanka, Nepal, etc. |
| 11 | prediction_markets | — | Special: market odds, price data, Kalshi/Polymarket |
| 12 | north_africa | 9 | Morocco, Algeria, Tunisia, Libya, Egypt, Sudan, etc. |
| 13 | sub_saharan_africa | 48 | All SSA nations |

**Change:** Africa was split into `north_africa` (9 countries) and `sub_saharan_africa` (48 countries) — previously a single Africa region.

## Model Routing

| Tier | Model | Provider | Used For |
|---|---|---|---|
| Primary (tier-1) | DeepSeek V4 Pro | DeepSeek Direct | All 13 regional analyses |
| Executive summary | Claude Opus 4.7 | OpenRouter | BLUF, synthesis, red team |
| Fallback | NONE | — | If V4 Pro fails, brief fails |

**Enforcement:** Quality gate checks that no Flash model was used. If Flash detected → BLOCK delivery.

## Delivery

- **From:** trevor_mentis@agentmail.to
- **To:** roderick.jones@gmail.com
- **Format:** HTML text brief (no PDF, no visuals, no attachments)
- **Quality gate:** 7 gates must ALL pass. Any BLOCK → no delivery.

## Landing Page (GitHub Pages)

- **URL:** https://trevormentis-spec.github.io/trevor-landing-page/
- **Repo:** trevormentis-spec/trevor-landing-page
- **Deploy script:** `scripts/deploy_landing_page.sh`
- **Updates:** BLUF summaries from all 13 regions, Kalshi scan data, latest brief PDF
- **Wired:** Step 7 of daily-text-brief.sh (runs after Moltbook post)

## Known Issues

- **GitHub PAT:** Landing page deploy blocked (`GH_TOKEN` needs rotation)
- **Feed rot:** ~90 dead feeds in catalog, ~60 more accumulating
- **Calibration:** Low resolution rate on recent predictions
- **QC PARSE_ERROR:** Intermittent quality gate parse failures
- **Cron health:** 3 crons showing error status (daily health checks, QC watchdog, LEO brief — delivery routing issues)
