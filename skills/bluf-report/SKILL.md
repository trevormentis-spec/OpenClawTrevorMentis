---
name: bluf-report
description: Produce a BLUF (Bottom Line Up Front) executive report — one-page or shorter, headline judgment first, calibrated confidence, three things-you-need-to-know, what-would-change-it, what-we-don't-know. Use when the user asks for a "brief", "executive summary", "1-pager", "BLUF", "snapshot", or "TL;DR" of an assessment. Distinct from the full TREVOR product (16-section).
metadata:
  trevor:
    requires:
      bins: [python3]
---

# BLUF Report

The discipline of putting the answer first. A BLUF report has one job: the
reader stops reading after the first paragraph and is still correctly
oriented.

## When to use

- User asked for a brief, summary, or 1-pager.
- Time pressure: decision in <24h, no time for the full TREVOR product.
- Stakeholder briefing: principal who reads the first paragraph and the
  three bullets and that's it.

Do **not** use BLUF when:
- The user asked for a full TREVOR assessment (use trevor-methodology).
- The question requires showing reasoning more than conclusion (use
  analytic-note).

## Structure

→ Template: `analyst/templates/bluf-report.md`

```
1. Bottom Line Up Front
   - One-sentence headline judgment with confidence band.
   - 2–3 sentences of context.

2. Three things you need to know
   - One sentence each, with confidence band.

3. What would change this assessment (I&W shortlist).

4. What we don't know (gap shortlist).

5. (Optional) Pointer to full assessment.
```

## Discipline rules

- **BLUF goes first. Always.** No throat-clearing. No "in this brief we
  will discuss". Just the answer.
- **Calibrated language.** Use Sherman Kent bands; see
  `skills/source-evaluation`. No "could", "may", "might" without a band.
- **Three is three.** Not four, not "three to five". Forcing the count
  forces prioritization.
- **Length cap: 250 words.** If you can't say it in 250 words, you don't
  understand it well enough to brief it.

## Procedure

```
1. Have the underlying assessment ready (analytic-note or TREVOR product).
2. Identify the headline judgment — the one thing the reader most needs
   to know if they read nothing else.
3. Pick the three top things — the next-most-important judgments.
4. Pick 2–3 indicators from your I&W table that would shift any of
   the above.
5. List 1–3 gaps that genuinely matter to the reader's decision.
6. Tighten. Then tighten again. 250 words max.
```

## Anti-patterns

- BLUF that's actually a thesis statement ("This brief will discuss X").
- Headline judgment without a confidence band.
- Three things that are really one thing rephrased.
- Burying the answer halfway down "for context".
- Padding to a length when the answer is shorter.
