# OSINT Daily Brief — Product Launch Plan

## Overview

Sell Trevor's Daily Intelligence Brief as a subscription product. This document maps every skill to the pipeline.

**Major update (2026-05-05):** GenViral replaces multiple fragmented posting tools — single API covers TikTok, Instagram, YouTube, Pinterest, LinkedIn, and Facebook through one pipeline.

---

## Pipeline Architecture

```
Daily Intel Brief cron (05:00 PT)
         │
         ▼
   [TREVOR analysis engine]
         │
         ├──→ Newsletter skill          → Email edition (AgentMail)
         ├──→ GenViral skill            → 6-platform social posting
         │       ├──→ TikTok (slideshow drafts)
         │       ├──→ Instagram (carousels)
         │       ├──→ YouTube (Shorts)
         │       ├──→ LinkedIn (articles/snippets)
         │       ├──→ Pinterest (infographics)
         │       └──→ Facebook (cross-posts)
         ├──→ landing-page-generator    → Product sales page
         └──→ visual_production         → Magazine PDF output
                  │
                  ▼
          skill-stripe-monitor          → Revenue tracking
```

**Content prep layer** (runs before posting):
- `cross-poster` → adapts the brief into platform-appropriate copy
- `social-pack` → generates platform variants from one source
- `social-media-scheduler` → manages calendar + cadence

---

## Phase 1: Foundation (week 1)

### 1.1 Landing Page

**Skills:** `landing-page-generator`, `landing-page-roast`

- Generate the product sales page
- Deploy to Netlify (already have auth + pipeline)
- Roast it with `landing-page-roast` before going live
- URL: `https://quiet-kangaroo-c0b94c.netlify.app/` (existing landing page)

**Content:**
- Hero: "Daily OSINT Briefing — Intelligence You Can Act On"
- Features: automated daily analysis, global coverage, structured methodology
- CTA: email capture → waitlist → paid subscription

### 1.2 Email Distribution

**Skills:** `newsletter`, `newsletter-creation-curation`, AgentMail

- Wire the Daily Intel Brief cron output into a newsletter format
- AgentMail is already set up for delivery (`trevor_mentis@agentmail.to`)
- newsletter-creation-curation provides industry positioning and cadence

### 1.3 GenViral Account Setup

**Skill:** `genviral` ✅ (installed, key configured, subscription active)

**Prerequisites — connect accounts:**
GenViral has 0 accounts connected. You'll need to log into https://www.genviral.io and connect at least one platform account per target platform:

| Platform | Recommended for OSINT | Priority |
|---|---|---|
| LinkedIn | Professional / analyst audience | 🥇 HIGH |
| Twitter/X | Real-time thread distribution | 🥇 HIGH |
| Instagram | Visual geopolitics / maps | 🥈 MEDIUM |
| TikTok | Slideshow briefs (trending format) | 🥈 MEDIUM |
| YouTube | Video analysis / Shorts | 🥉 LOWER |
| Pinterest | Infographic distribution | 🥉 LOWER |

**Hosted accounts** are available if you don't want to connect personal profiles. Check in the Genviral dashboard.

**After connecting accounts**, run:
```bash
GENVIRAL_API_KEY="gva_live_..." bash skills/genviral/scripts/genviral.sh accounts
```
Then save the account IDs to `skills/genviral/defaults.yaml` under `posting.default_account_ids`.

---

## Phase 2: Distribution (week 2)

### 2.1 Live Posting — GenViral (Replaces ALL old posting tools)

**Legacy tools removed from the plan:**
- ~~`social-poster` (VibePost)~~ → replaced by GenViral (6 platforms, 1 API)
- ~~`social-post` (Twitter/Farcaster)~~ → replaced by GenViral API
- ~~`social-media-agent` (browser automation)~~ → replaced by GenViral API

**GenViral posting workflow for daily briefs:**

1. **TREVOR finishes analysis** (05:00 PT cron)
2. **cross-poster / social-pack** adapts content into platform-appropriate copy
3. **GenViral create-post** pushes to all connected platforms:
   - **LinkedIn:** Full brief highlight post (direct)
   - **TikTok:** Slideshow draft (MEDIA_UPLOAD mode → human adds trending sound → publishes)
   - **Instagram:** Carousel post (DIRECT_POST)
   - **YouTube:** Shorts video (DIRECT_POST)
   - **Facebook/Pinterest:** Cross-published (DIRECT_POST)
4. **Performance tracking:** GenViral analytics → `workspace/performance/log.json` → weekly review

### 2.2 Content Calendar

**Skills:** `social-media-scheduler`, `content-marketing`, `genviral`

Weekly content mix from the brief:

| Day | Content Type | Platform(s) | Format |
|---|---|---|---|
| Mon | Full brief highlight + BLUF | LinkedIn, Facebook | Text + key image |
| Tue | Regional deep-dive thread | TikTok slideshow draft | 5-7 slide carousel |
| Wed | Key insight + map | Instagram, Pinterest | Infographic carousel |
| Thu | Analysis snippet + methodology | LinkedIn, Facebook | Text + data point |
| Fri | Weekly roundup | YouTube Shorts | 60s video summary |
| Sat | Featured intelligence graphic | Instagram, Pinterest | Visual only |
| Sun | Monday preview hook | TikTok draft | 3-slide teaser |

### 2.3 Trend Intelligence & Niche Research

GenViral's `trend-brief` command provides fast niche intelligence:
- Top hashtags in the OSINT/security space
- Top sounds and creators
- Best posting windows
- Recommended hook angles

This feeds back into content optimization without manual research.

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

## GenViral Subscription Details

- **Tier:** Small (yearly billing)
- **Status:** Active ✅
- **Credits:** 2,400 / 2,400 remaining
- **Reset:** Monthly
- **Billing period:** 2026-05-05 → 2027-05-05
- **Key:** Stored in TOOLS.md and env var `GENVIRAL_API_KEY`

---

## Skill Inventory — Updated Map

```
Category       │ Skill                    │ Role
───────────────┼──────────────────────────┼───────────────────────────
Content Prep   │ cross-poster             │ Platform-adapted drafts
               │ social-pack              │ Multi-platform variants
               │ social-media-scheduler   │ Calendar + cadence
               │ content-marketing        │ Strategy + funnel
───────────────┼──────────────────────────┼───────────────────────────
Posting Engine │ genviral 🆕              │ 6-platform posting (TikTok, IG, YT, LI, FB, Pin)
───────────────┼──────────────────────────┼───────────────────────────
Newsletter     │ newsletter               │ Monetization strategy
               │ newsletter-creation-*    │ Industry positioning
               │ agentmail                │ Email delivery
───────────────┼──────────────────────────┼───────────────────────────
Sales Page     │ landing-page-generator   │ Product page build
               │ landing-page-roast       │ Conversion audit
───────────────┼──────────────────────────┼───────────────────────────
Revenue        │ skill-stripe-monitor     │ MRR / churn / alerts
───────────────┼──────────────────────────┼───────────────────────────
Existing       │ visual_production        │ Magazine PDF output
               │ bluf-report              │ Executive summaries
               │ daily-intel-brief (cron) │ The core product
               │ moltdbook                │ Social presence / community
```

**Retained (content prep only):**
- `cross-poster` — still useful for adapting copy per platform before GenViral posts it
- `social-pack` — still useful for multi-platform variants
- `social-media-scheduler` — still useful for calendar management

**Archived (replaced by GenViral):**
- ~~`social-poster` (VibePost)~~ — replaced
- ~~`social-post` (Twitter/Farcaster)~~ — replaced
- ~~`social-media-agent` (browser automation)~~ — replaced

---

## Environment Variables Needed

| Var | Required By | Source | Status |
|---|---|---|---|
| `GENVIRAL_API_KEY` | genviral skill | GenViral dashboard | ✅ Configured |
| `AGENTMAIL_API_KEY` | Newsletter delivery | AgentMail | ✅ Already configured |
| `STRIPE_SECRET_KEY` | skill-stripe-monitor | Stripe dashboard | ❌ Pending |
| ~~`X_CONSUMER_KEY`~~ | ~~social-post~~ | ~~Twitter~~ | 🗑️ No longer needed |
| ~~`X_CONSUMER_SECRET`~~ | ~~social-post~~ | ~~Twitter~~ | 🗑️ No longer needed |
| ~~`X_ACCESS_TOKEN`~~ | ~~social-post~~ | ~~Twitter~~ | 🗑️ No longer needed |
| ~~`X_ACCESS_TOKEN_SECRET`~~ | ~~social-post~~ | ~~Twitter~~ | 🗑️ No longer needed |
| ~~`VIBEPOST_API_KEY`~~ | ~~social-poster~~ | ~~VibePost~~ | 🗑️ No longer needed |

---

## Current Status — 2026-05-05

### ✅ Completed

| Step | Detail |
|------|--------|
| 1. Connect accounts | LinkedIn + TikTok + Twitter connected ✅ |
| 2. Verify accounts | IDs saved to defaults.yaml ✅ |
| 3. Generate landing page | Built, deployed to https://quiet-kangaroo-c0b94c.netlify.app ✅ |
| 4. Roast landing page | Score 7/10 — full audit at exports/landing-roast.md ✅ |
| 5. Wire GenViral to cron | scripts/genviral-post-brief.sh + Step 4 in daily-brief-cron.sh ✅ |
| 6-7. Deploy | Netlify live, email capture via Netlify Forms, sample preview section ✅ |

### ✅ Completed (2026-05-12)

| Item | Status |
|------|--------|
| Stripe checkout links on pricing | Done ✅ — Pro ($19/mo) + Enterprise ($99/mo) on landing page |
| skill-stripe-monitor activation | Done ✅ — registered in OpenClaw config with STRIPE_SECRET_KEY |
| Form submission backend | Resolved ✅ — GitHub Pages + Buttondown embed handles subscribe forms directly |
| Buttondown newsletter pipeline | Done ✅ — buttondown-send.py auto-publishes daily brief |
| GenViral social posting | Done ✅ — 6 accounts connected, posting verified |
| Landing page auto-deploy | Done ✅ — wired into daily-brief-cron.sh Step 9 |
| Daily cron jobs | Done ✅ — registered in OpenClaw config (daily-intel-brief, kalshi-daily-scan, skill-scanner-audit) |

## Status — All integrations built and wired

The pipeline now runs end-to-end:
```
05:00 PT → Brief analysis → Magazine PDF → Gmail delivery
       → GenViral social posts (6 platforms)
       → Moltbook posts (builds + agents)
       → Agent API JSON build
       → Buttondown newsletter publish
       → Landing page deploy (GitHub Pages)
```
