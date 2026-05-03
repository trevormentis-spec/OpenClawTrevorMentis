# OSINT Daily Brief — Product Launch Plan

## Overview

Sell Trevor's Daily Intelligence Brief as a subscription product. This document maps every skill to the pipeline.

---

## Pipeline Architecture

```
Daily Intel Brief cron (05:00 PT)
         │
         ▼
   [TREVOR analysis engine]
         │
         ├──→ Newsletter skill       → Email edition (AgentMail / Substack)
         ├──→ cross-poster           → Platform-adapted social drafts
         ├──→ social-pack            → Twitter/LinkedIn/Reddit variants
         ├──→ social-media-scheduler → Posting calendar + cadence
         ├──→ social-poster          → Live posting (VibePost API)
         └──→ landing-page-generator → Product sales page
                  │
                  ▼
          skill-stripe-monitor       → Revenue tracking
```

---

## Phase 1: Foundation (week 1)

### 1.1 Landing Page

**Skills:** `landing-page-generator`, `landing-page-roast`

- Generate the product sales page
- Deploy to Netlify (already have auth + pipeline)
- Roast it with `landing-page-roast` before going live
- URL: `https://glittering-croquembouche-68ad80.netlify.app/` (existing dashboard)

**Content:**
- Hero: "Daily OSINT Briefing — Intelligence You Can Act On"
- Features: automated daily analysis, global coverage, structured methodology
- CTA: email capture → waitlist → paid subscription

### 1.2 Email Distribution

**Skills:** `newsletter`, `newsletter-creation-curation`, AgentMail

- Wire the Daily Intel Brief cron output into a newsletter format
- AgentMail is already set up for delivery (`trevor_mentis@agentmail.to`)
- newsletter-creation-curation provides industry positioning and cadence

### 1.3 Social Presence

**Skills:** `cross-poster`, `social-pack`, `social-media-scheduler`

- **cross-poster** — Adapt each brief for Twitter/X, LinkedIn, Reddit
- **social-pack** — Generate platform-specific variants from one brief
- **social-media-scheduler** — Plan the posting calendar (daily at 06:00 PT)

---

## Phase 2: Distribution (week 2)

### 2.1 Live Posting

**Skills:** `social-poster`, `social-media-agent`

| Skill | Method | API Key Needed? |
|---|---|---|
| `social-poster` | VibePost API (node script) | x-quack-api-key |
| `social-post` | Twitter OAuth + Farcaster API | Twitter dev creds |
| `social-media-agent` | Browser automation (no keys) | None ✅ |

**Recommended path:** Start with `social-media-agent` (no API keys, browser automation via OpenClaw's `browser` tool). Upgrade to `social-poster` or `social-post` once traffic justifies API costs.

### 2.2 Content Calendar

**Skills:** `social-media-scheduler`, `content-marketing`

Weekly content mix from the brief:

| Day | Content Type | Platform | Skill |
|---|---|---|---|
| Mon | Full brief highlight | LinkedIn | cross-poster |
| Tue | Key finding thread | Twitter/X | social-pack |
| Wed | Analysis snippet | Reddit | cross-poster |
| Thu | Infographic + caption | LinkedIn/Insta | social-pack |
| Fri | Weekly roundup prompt | All | social-media-scheduler |
| Sat | Community engagement | Twitter/X | social-media-agent |
| Sun | Preview of Monday's brief | All | cross-poster |

---

## Phase 3: Revenue (week 3)

### 3.1 Subscription Model

Tiered pricing via Stripe:

| Tier | Price | What They Get |
|---|---|---|
| Free (teaser) | $0 | Headlines + 1 analysis/day |
| Pro | $19/mo | Full brief + PDF export + archive |
| Enterprise | $99/mo | Custom sources + API access + team accounts |

### 3.2 Stripe Integration

**Skill:** `skill-stripe-monitor`

- Set `STRIPE_SECRET_KEY` env var
- Track MRR, churn, new subscriptions, failed payments
- Alert on churn spikes or payment failures

### 3.3 Subscriber Management

- AgentMail handles delivery
- Stripe handles billing
- `skill-stripe-monitor` gives Trevor a revenue dashboard

---

## Skill Inventory — Final Map

```
Category       │ Skill                    │ Role
───────────────┼──────────────────────────┼───────────────────────────
Content        │ cross-poster             │ Platform-adapted drafts
               │ social-pack              │ Multi-platform variants
               │ social-media-scheduler   │ Calendar + cadence
               │ content-marketing        │ Strategy + funnel
               │ content-generation       │ Broader content creation
───────────────┼──────────────────────────┼───────────────────────────
Posting        │ social-poster            │ VibePost API posting
               │ social-post              │ Twitter/Farcaster API
               │ social-media-agent       │ Browser automation posting
───────────────┼──────────────────────────┼───────────────────────────
Newsletter     │ newsletter               │ Monetization strategy
               │ newsletter-creation-*     │ Industry positioning
───────────────┼──────────────────────────┼───────────────────────────
Sales Page     │ landing-page-generator   │ Product page build
               │ landing-page-roast       │ Conversion audit
───────────────┼──────────────────────────┼───────────────────────────
Revenue        │ skill-stripe-monitor     │ MRR / churn / alerts
───────────────┼──────────────────────────┼───────────────────────────
Existing       │ visual_production        │ Magazine PDF output
               │ bluf-report              │ Executive summaries
               │ daily-intel-brief (cron) │ The core product
               │ agentmail                │ Email delivery
               │ moltdbook                │ Social presence / community
```

---

## Environment Variables Needed

| Var | Required By | Source |
|---|---|---|
| `STRIPE_SECRET_KEY` | skill-stripe-monitor | Stripe dashboard |
| `X_CONSUMER_KEY` | social-post | Twitter Developer Portal |
| `X_CONSUMER_SECRET` | social-post | Twitter Developer Portal |
| `X_ACCESS_TOKEN` | social-post | Twitter Developer Portal |
| `X_ACCESS_TOKEN_SECRET` | social-post | Twitter Developer Portal |
| `VIBEPOST_API_KEY` | social-poster | VibePost (third-party) |
| `AGENTMAIL_API_KEY` | Newsletter delivery | Already configured ✅ |

---

## Immediate Next Steps

1. **Generate the landing page** — `landing-page-generator` with product brief
2. **Roast the landing page** — `landing-page-roast` for conversion audit
3. **Wire cross-poster** to the daily brief output — adapt one brief into 3 platform drafts
4. **Set up social-media-scheduler** — define the weekly content pillars
5. **Configure Stripe** — create products + set `STRIPE_SECRET_KEY`
6. **Deploy** — Push to Netlify, activate social posting, open subscriptions
