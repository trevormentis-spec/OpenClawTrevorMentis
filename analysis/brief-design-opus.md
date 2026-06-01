# Designing the Right Daily Product for Trevor

**Analysis: 2026-06-01**
**Prepared for: Roderick**

---

## 1. What Makes the BBC World Service Daily Update Good?

The BBC World Service operates three distinct daily news formats, each with a clear job:

| Product | Cadence | Length | Job |
|---------|---------|--------|-----|
| **Global News Podcast** | 2x/day weekdays, 1x/day weekends | ~30 min | Curated news digest |
| **The Global Story** | 1x/day weekday | ~25 min | One-topic deep dive |
| **Newshour** | Daily | ~60 min | Expert interview analysis |
| **BBC News Summary** | 2-min bulletins hourly | ~2 min | Headline signal |

**What the BBC does well — and why:**

**1. Curated, not comprehensive.** The Global News Podcast doesn't try to cover every region every day. On June 1, 2026, the episodes covered: Colombia election runoff, Israel-Hezbollah escalation, PSG Champions League fan violence. That's 3-4 stories, not 10+ regions. The editorial team selects what matters and leaves the rest.

**2. Human editorial judgment.** BBC journalists decide: "This is the story, here's why it matters, here's the context you need to understand it." That judgment comes from 250+ correspondents worldwide, decades of institutional knowledge, and a rigorous editorial process.

**3. Narrative structure over bullet points.** Stories are *told*, not summarized. Each segment has a beginning, middle, end. The correspondent explains the *why* — not just the *what*.

**4. Trust as the product.** The BBC's editorial guidelines (impartiality, accuracy, accountability) are the brand. Listeners trust it not because the format is clever but because the BBC has a 100-year track record of getting it right.

**5. Voice matters.** The presenters have distinct, human personalities. Katya Adler, the host of The Global Story, has 25 years of experience covering conflicts in the Middle East, Europe, and Latin America. The authority comes from the person, not the institution.

**6. Depth over breadth.** The Global Story drills into *one* story per episode. The Global News Podcast covers 4-6 stories, but each gets real treatment — interviews, analysis, context. Nothing is covered in one sentence.

---

## 2. Honest Assessment of Trevor's Capabilities

### What Trevor CAN do well

| Capability | Evidence | Notes |
|------------|----------|-------|
| **Focused research on one topic** | LEO Ground Stations (54 entities, 83 sources, deep) | This is Trevor's strongest mode |
| **Signal detection from curated feeds** | 298 working RSS feeds across 10+ regions | Reliable change detection from known sources |
| **Structured data monitoring** | Kalshi market scanner, weekly trend tracking | Running consistently |
| **Source infrastructure monitoring** | Feed health checks, dead feed detection | Unique — no human can track 700+ feeds |
| **Prediction market integration** | Kalshi 60+ markets across geopolitics series | Unique value — real-time pricing of geopolitical outcomes |
| **Week-over-week comparison** | Trend tracker across time windows | Works well with structured data |
| **Production-format output** | PDF rendering, audio narration, slides | Good for final delivery format |

### What Trevor CANNOT do well (and won't)

| Capability | Why it fails |
|------------|--------------|
| **Real-time breaking news** | 16KB context window; pipeline runs once daily; not designed for velocity |
| **10+ region global synthesis** | Every attempt has failed quality checks — empty sections, fabricated KJs, collapsed probabilities |
| **Calibrated probability judgments** | 3% accuracy on past predictions — systematically overconfident |
| **Narrative journalism** | No human editorial judgment, no correspondents, no institutional knowledge |
| **"Why it matters" analysis** | Cannot meaningfully answer "why" — generates plausible-sounding but shallow reasoning |
| **Competing with BBC/FT/WSJ** | $0.47/week inference budget vs $300M/year newsroom |

### The Budget Reality

| Metric | Value |
|--------|-------|
| Weekly inference budget | ~$0.47 |
| Primary model | DeepSeek V4 Flash |
| High-end model | Opus (critical tasks only) |
| Feed health | 41.2% (298/723 working) |
| Context window | 64K token (effective, shared across regions) |

This is not a budget that can produce a competitive global news product. Full stop.

---

## 3. What Should the Daily Product Actually Look Like?

### The Core Insight

The BBC's value is **narrative journalism from human experts**. Trevor's value is **automated signal intelligence from machine-scale monitoring**.

These are not competing products. They're complementary.

Trevor's job should be: **"Here's what your intelligence sources are saying, what changed, and what's worth your attention."** Not: "Here's a globally synthesized executive summary with 10 region analyses and calibrated probabilities."

### Proposed Format: The Signal Board

A single-page daily intelligence summary organized around what actually changed, not regions:

```
─────────────────────────────────────────────────────
  SIGNAL BOARD — 2026-06-01
─────────────────────────────────────────────────────

🔴 WATCH ITEMS (things that moved significantly)
  • Hezbollah drone escalation: 3 new sources confirmed
    fiber-optic capability. Kalshi KXHEZBDRONE → 34¢ (+12)
  • Colombia runoff: outsider wins first round. Kalshi
    unchanged. Market pricing status-quo win.

🟡 TREND LINES (week-over-week tracking)
  • Strait of Hormuz: tension markers at 8/12 (flat).
    Iran-US truce talks still scheduled, no cancellations.
  • Ebola DRC: border coordination established (UG/SSD).
    No new cases beyond initial cluster. Trend: contained.

⚪ SIGNAL SUMMARY (what your feeds said in 24h)
  Top stories by source frequency:
  1. Colombia election (23 sources)
  2. Israel-Lebanon escalation (18 sources)
  3. PSG Champions League violence (12 sources)
  4. US-Iran exchange of fire (11 sources)
  5. Ebola DRC response (9 sources)

📊 MARKET ROUNDUP
  Notable moves across Kalshi geopolitical series:
  • KXUSAIRANAGREEMENT → 19¢ (steady — no new deal signal)
  • KXWTI → 49¢ (+4 — supply disruption premium)
  • KXTARIFFRATEPRC → 13¢ (flat — USMCA review)

🔍 ONE DEEP DIVE: Hezbollah Fiber-Optic Drones
  [Focused research on one story, 300-500 words.
  Includes: what happened, why it's significant,
  what changed from last week, how markets are pricing it.]

⚙️ SOURCE HEALTH
  • 3 Russia feeds went dead this week
  • 2 South America feeds recovered (new domain)
  • Overall: 298/723 working (41.2%)
─────────────────────────────────────────────────────
```

### Why This Format Works for Trevor

| Section | Plays to Trevor's Strength |
|---------|---------------------------|
| **Watch Items** | Change detection is what LLMs do well — compare yesterday's data to today's |
| **Trend Lines** | Structured week-over-week comparison with defined markers |
| **Signal Summary** | Pure frequency analysis — no synthesis required, just "how many sources covered X" |
| **Market Roundup** | Kalshi integration is Trevor's unique differentiator |
| **One Deep Dive** | Focused research on a single topic — Trevor's strongest mode (proven by LEO work) |
| **Source Health** | Machine-scale monitoring humans can't do — unique value |

### What This Format Explicitly Does NOT Do

- ❌ No calibrated probability judgments across 10 regions
- ❌ No narrative "executive summary" pretending to be global synthesis
- ❌ No fabricated key judgments with fake confidence bands
- ❌ No attempt to compete with BBC/FT/WSJ on their terms

---

## 4. The Hard Trade-Offs

### Trade-off 1: Coverage Breadth

**Give up:** Coverage of all 10+ regions every day.
**Get:** Reliable signal detection on the 4-6 things that actually moved.

The BBC Global News Podcast covers 4-6 stories per episode. Not 10+ regions. Not every country. Just what matters today. Trevor should do the same — but Trevor can't judge *what matters*. Trevor can do something the BBC can't: scan 298 feeds and say "here's what the aggregate signal says."

### Trade-off 2: Calibrated Probabilities

**Give up:** Sherman Kent bands and probability ranges on every judgment.
**Get:** Honest signal flags with no false precision.

Trevor's calibration accuracy is ~3%. Publishing calibrated probabilities is actively misleading. Replace "55% confident Hormuz disruption" with "tension markers at 8 of 12 — these specific indicators changed."

### Trade-off 3: The "Executive Summary" Format

**Give up:** The opening BLUF paragraph that synthesizes everything.
**Get:** A format that doesn't require synthesis.

The BLUF format was designed for a human analyst who deeply understands the subject matter. Trevor doesn't — not in the way needed to write a trustworthy one-sentence summary of the day's most important development. Replace with: "Here are the signals. Here's what changed. Here's one thing worth reading about."

### Trade-off 4: Daily Frequency (Maybe)

**Consider:** 3x/week instead of daily.
**Reason:** If every edition requires a deep dive (which is Trevor's best output), daily cadence strains the budget. 3x/week gives more time per edition and reduces the "nothing changed but I have to produce something" problem.

### Trade-off 5: Narrative Quality

**Give up:** A polished, human-voice narrative.
**Get:** A structured, honest, machine-produced intelligence summary.

Trevor will never write like a BBC correspondent. Don't try. The product's value is Trevor's monitoring reach — 298 feeds, 60+ Kalshi markets, week-over-week tracking — not prose quality.

---

## 5. Concrete Proposal

### Format: The Signal Board (daily or 3x/week)

**Length:** ~1 page (readable in 3 minutes)
**Cadence:** Daily for signal scanning, 3x/week if deep dives every edition
**Delivery:** Telegram message (preferred) + optional brief landing page

### Section Breakdown

```
─────────────────────────────────────
  SIGNAL BOARD — YYYY-MM-DD
─────────────────────────────────────

🔴 WATCH ITEMS (3-5 items, 1 line each)
  • [Signal] — [what changed] | [market move if relevant]

🟡 TREND LINES (up to 3 tracked themes, 2-3 lines each)
  • [Theme]: [metric readings] | [direction]

⚪ SIGNAL SUMMARY (auto-generated from feed frequency)
  No synthesis — just "X sources covered Y today"

📊 MARKET ROUNDUP (notable Kalshi moves, 3-5 items)
  • [Ticker] → [price] ([direction] — [driver])

🔍 DEEP DIVE (1 story, 300-500 words)
  Focused analysis on one development.

⚙️ SOURCE HEALTH (status line)
  Feeds working / total / changes since last report
```

### How Each Section Is Produced

| Section | Model | Data Source | Complexity |
|---------|-------|-------------|------------|
| Watch Items | V4 Flash | Compare today's feed data vs yesterday | Low — diff comparison |
| Trend Lines | V4 Flash | Structured JSON from trend tracker | Low — template fill |
| Signal Summary | None (aggregation) | Feed frequency counter | None — pure data |
| Market Roundup | None (aggregation) | Kalshi scanner output | None — price changes |
| Deep Dive | V4 Flash or Opus | Curated sources for one topic | Medium — focused |
| Source Health | None (aggregation) | Feed health check | None — pure data |

### Estimated Cost Per Edition

| Component | Tokens (in) | Tokens (out) | Cost |
|-----------|-------------|--------------|------|
| Feed aggregation | 0 (pre-collected) | 0 | $0 |
| Trend comparison | ~2K | ~1K | ~$0.0004 |
| Watch item extraction | ~4K | ~1K | ~$0.0007 |
| Deep dive (V4 Flash) | ~8K | ~2K | ~$0.0015 |
| Deep dive (Opus, 1x/week) | ~8K | ~2K | ~$0.009 |
| Formatting + delivery | ~1K | ~1K | ~$0.0003 |
| **Total (V4 Flash daily)** | | | **~$0.003/edition** |
| **Total (1 Opus deep dive/week)** | | | **~$0.02/week** |

At current budget (~$0.47/week), this runs for **150+ daily editions** per week. Even with overhead, it's sustainable.

### What the First Edition Would Cover (Demo Topics for Today)

Based on actual Global News Podcast content from June 1:

- **Watch Items:** Colombia runoff (Espriella vs Cepeda), Israel-Lebanon escalation (drone warfare), PSG fan violence, US-Iran exchange of fire, Ebola DRC response
- **Trend Lines:** Strait of Hormuz tension markers, AI regulation developments (Pope Leo encyclical), US-Iran negotiations progress
- **Signal Summary:** Top stories by source frequency
- **Market Roundup:** Colombia election markets, Iran conflict contracts, oil price series
- **Deep Dive:** "Hezbollah's fiber-optic drone capability — what it means for the escalation"
- **Source Health:** Working feed count, new dead feeds, recovered feeds

### Delivery Mechanism

1. **Primary:** Telegram message (markdown-formatted, ~1-2KB)
2. **Secondary:** Auto-posted to landing page (GitHub Pages)
3. **Optional:** Single-page brief PDF (Opus-formatted, once/week)

---

## Summary

**Don't compete with the BBC.** Trevor can't. No one should try.

**Do what the BBC can't:** Monitor 298 feeds across 10+ regions, track 60+ Kalshi markets, compare week-over-week trends, flag source infrastructure decay, and produce one focused deep dive per day — all for ~$0.003 per edition.

The Signal Board format is not "GSIB lite." It's a fundamentally different product designed for Trevor's actual capabilities: signal detection, structured comparison, and focused research. It gives Roderick what he asked for — trends, themes, and global awareness — without the fabricated synthesis and collapsed probabilities that made the old format fail.

**The hard truth:** Roderick gives up the pretense of a mini-GSIB. What he gets is honest, reliable, machine-scale intelligence monitoring that no human news organization can provide.
