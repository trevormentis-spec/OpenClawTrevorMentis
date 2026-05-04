# Trevor Daily OSINT Brief — Business Plan

## 1. Market Context

### Market Size
- OSINT market growing at **29.4% CAGR** (2026–2035)
- AI security segment dominates with **23% market share**
- US National OSINT Strategy driving demand across government, finance, and journalism
- Increasing public awareness of OSINT driving community growth

### Competitive Landscape

| Product | Format | Platform | Pricing | Est. Audience |
|---|---|---|---|---|
| OSINT Weekly Newsletter | Weekly | Buttondown | Free | 5K+ |
| OSINT Daily Newsletter | Daily | Buttondown | Free | 3K+ |
| The OSINT Newsletter | Weekly | Substack | Free+Paid | 10K+ |
| OSINT Industries | Platform | Web | $99-299/mo | Enterprise |
| **Trevor Daily Brief** | **Daily** | **AgentMail** | **$19/mo** | **0 (launching)** |

### Trevor's Competitive Advantage
- **Fully automated** — zero human effort per brief
- **AI analyst 24/7** — always monitoring, always producing
- **Structured methodology** — SATs, Admiralty Code source scoring, calibrated probability bands
- **Multi-format output** — markdown, magazine PDF, social posts from a single analysis
- **Near-zero marginal cost** — scale to thousands of subscribers without additional overhead

---

## 2. Product Architecture

```
Input Layer (always on)
├── Web search + NewsAPI (geopolitical monitoring)
├── Polymarket prediction markets (probability feeds)
├── Analyst source list (curated OSINT feeds)
│
Processing Layer (05:00 PT daily)
├── DeepSeek v4-Flash → regional analysis (6 regions)
├── DeepSeek v4-Pro → escalation (key judgments)
├── SAT toolkits → structured analysis
├── Source evaluation → Admiralty Code scoring
│
Output Layer (05:30 PT)
├── Markdown brief (tasks/news_analysis.md)
├── Magazine PDF (visual_production → A4 layout)
├── Email edition (newsletter skill + AgentMail)
│
Distribution Layer (throughout the day)
├── Twitter/X post (social-media-agent, browser automation)
├── LinkedIn post (cross-poster adapted)
├── Reddit post (if appropriate)
├── Landing page live at quiet-kangaroo-c0b94c.netlify.app
│
Revenue Layer
├── Stripe subscription billing ($19/mo flat)
├── skill-stripe-monitor dashboard (MRR, churn)
└── AgentMail delivery (trevor_mentis@agentmail.to)
```

---

## 3. Pricing Strategy

### Single Tier: $19/mo
- Full daily brief (6 regions, 16 sections)
- Calibrated probability judgments
- OSINT source scoring
- Magazine PDF export
- Direct email delivery

### Rationale
- Sits between free Substack newsletters ($0) and enterprise platforms ($99-299)
- Low enough for individual analysts, journalists, traders
- High enough to signal value vs. free alternatives
- No free tier — full product, full price (builds perceived value)
- 14-day money-back guarantee removes risk

### Future Expansion
- **$99/mo Pro** — Add custom sources, API access, team accounts
- **Enterprise** — White-label brief, dedicated monitoring, SLA

---

## 4. Promotion Strategy (3 Channels)

### Channel 1: Build in Public on Moltbook (Primary)
Moltbook is where agents build reputation. The playbook:
- Post the brief daily as @trevormentis
- Share methodology posts (how SATs work, how Admiralty Code works)
- Engage with the OSINT/analyst community on Moltbook
- Transparently share metrics (subscriber counts, revenue, learnings)
- **Why this works:** Moltbook's audience is agents and their humans — exactly who would subscribe to an agent-produced brief

**Cadence:** Daily brief summary post + 1 methodology/metacognition post per week

### Channel 2: Twitter/X (Awareness)
- Post daily briefing highlights (automated via browser cron at 13:30 PT)
- Follow and engage with OSINT community accounts
- Share screenshots of the magazine PDF
- Use consistent hashtags: #OSINT #Intelligence #DailyBrief
- **Goal:** Drive traffic to landing page → email capture → paid subscription

**Cadence:** 1 post/day (the brief), 3-5 engagements/week

### Channel 3: Landing Page (Conversion)
- Current: `quiet-kangaroo-c0b94c.netlify.app`
- Need: Sample brief download, pricing CTA, social proof
- SEO-optimized for "daily OSINT briefing" and "intelligence report subscription"

### Channel 4: Referral / Organic
- Every subscriber gets a shareable link (future feature)
- Word of mouth in intelligence/analyst circles
- Cross-promotion with other OSINT newsletters

---

## 5. Phase Plan

### Phase 0: Foundation ✅ (Complete)
- [x] Daily intel brief cron running (05:00 PT)
- [x] Magazine PDF generation (05:30 PT)
- [x] Social posting content pipeline
- [x] Twitter posting cron (13:30 PT, browser automation)
- [x] Landing page live
- [x] GitHub backup (daily)

### Phase 1: Launch (Week 1-2)
- [ ] **First live Twitter post** — need password for trevor.mentis@gmail.com
- [ ] **Stripe setup** — create product, set STRIPE_SECRET_KEY
- [ ] **Landing page upgrades** — add sample brief download, improve CTA
- [ ] **Moltbook presence** — start posting daily brief summary
- [ ] **First subscriber** — manual onboarding via AgentMail

### Phase 2: Growth (Week 3-6)
- [ ] **Buttondown or Substack integration** — automated email delivery with subscriber management
- [ ] **Sample brief download** on landing page (convert visits → email captures)
- [ ] **Social proof** — testimonials from first subscribers
- [ ] **Twitter growth** — follow OSINT community, engage daily
- [ ] **Moltbook weekly methodology post** — build authority
- [ ] **Stripe dashboard active** — track MRR via skill-stripe-monitor

### Phase 3: Scale (Month 2-3)
- [ ] **Pro tier ($99/mo)** — custom sources, API access
- [ ] **Enterprise tier** — white-label, SLA
- [ ] **Affiliate/referral program**
- [ ] **Paid advertising** — targeted Twitter/LinkedIn ads (after 50+ organic subs)
- [ ] **Partnerships** — cross-promote with OSINT communities

---

## 6. Revenue Projections

| Month | Subs (net) | MRR | Cumulative Revenue |
|---|---|---|---|
| Month 1 | 5 | $95 | $95 |
| Month 2 | 20 | $380 | $475 |
| Month 3 | 50 | $950 | $1,425 |
| Month 6 | 150 | $2,850 | ~$8,000 |
| Month 12 | 500 | $9,500 | ~$45,000 |

**Assumptions:**
- Zero ad spend in month 1-2 (organic only)
- 5% conversion rate from landing page visitor → subscriber
- 10% monthly organic growth after initial traction
- 5% monthly churn (conservative for intelligence products)

**Break-even:** The product costs ~$0.47/week in DeepSeek API costs. Break-even is **1 subscriber.**

---

## 7. Immediate Next Steps

1. **Tonight/tomorrow:** First browser-automated Twitter post (need password)
2. **This week:** Set up Stripe product + STRIPE_SECRET_KEY
3. **This week:** Add sample brief download to landing page
4. **This week:** Post first daily brief summary to Moltbook
5. **This week:** Manual first subscriber onboarding

---

*Zero marginal cost. Zero human effort per brief. The product is the pipeline.*
