# Landing Page Roast — Global Security & Intelligence Brief

**URL:** https://quiet-kangaroo-c0b94c.netlify.app/
**Audience:** Security analysts, investors, journalists, geopolitical risk professionals
**Conversion action:** Email capture → Paid subscription ($19-$99/mo)
**Reviewer:** Trevor Roast

---

## Overall Score: 7/10

Solid foundation. Dark/intel aesthetic is on-brand. But it's missing conversion mechanics — there's no email capture, no social proof, and the pricing section has dead CTAs.

---

## Top 5 Blockers (Ranked by Impact)

### 🔴 Blocker 1: No email capture — zero conversion mechanism
The page has no way to capture leads. No email form. No waitlist. No "Get a free sample." The CTAs all link to `#pricing` which is a dead anchor. Someone lands, reads the whole page, thinks "cool," and... leaves. Nothing stops them.

**Fix:** Add at minimum:
- An email capture form in the hero (free trial / sample edition)
- A "Try a free edition" CTA that actually submits
- Stripe checkout links on the pricing cards (when the key is sorted)

### 🔴 Blocker 2: Pricing CTAs are dead links
Every pricing `href="#"` goes nowhere. In production these need to link to Stripe checkout or at minimum a waitlist. This kills trust — looks like a concept, not a real product.

**Fix:** Wire the Pro tier CTA to a Stripe payment link or waitlist form.

### 🔴 Blocker 3: No social proof — zero testimonials
You have real social proof to use:
- Moltbook engagement (4 comments, 1 follower, notifications)
- Daily briefs that have been delivered for days/weeks
- LinkedIn posts with real engagement

**Fix:** Add at minimum:
- "Trusted by [N] subscribers" counter
- 1-2 real quotes from Moltbook or LinkedIn engagement
- A sample edition preview (screenshot of an actual brief)

### 🟡 Blocker 4: Value prop is slightly inside-baseball
"CIA BLUF format" and "Sherman Kent confidence bands" will resonate with analysts but may lose broader audiences. The headline "Intelligence you can act on" is good but the subhead leads with methodology, not outcome.

**Fix:** Consider adding a clear "who this is for" section early (between hero and coverage) that speaks to specific roles: analyst, investor, security lead, journalist.

### 🟡 Blocker 5: No urgency or scarcity mechanism
Nothing on the page creates a reason to act now vs. later. "Limited launch pricing" was in the generator but didn't make it into the final. Without urgency, visitors bookmark and forget.

**Fix:** Add "Launch pricing — lock in $19/mo forever" or "First 50 subscribers get Enterprise free for 1 month."

---

## Quick Wins (<30 min)

1. **Add a `mailto:` or formspree form** to the hero CTA so people can actually sign up
2. **Replace placeholder `#` links** with functional ones
3. **Add a subscriber count** ("Read by 12 analysts and security professionals")
4. **Add a sample brief screenshot** in the features section
5. **Add launch pricing urgency** to both pricing cards

---

## Structural Rewrites

### Hero rewrite (outcome-first version)
```
TREVOR Assessment — Daily Intelligence

The morning brief that analysts use.
Not a news digest. Intelligence — delivered by 07:00 PT.

Six theaters. 50+ sources. Structured methodology.
```

### Subhead rewrite
```
Every morning by 07:00 PT, you get a structured intelligence briefing
covering Ukraine to Venezuela — with clear confidence bands on
what matters, not a firehose of headlines.
```

### CTA block rewrite
```
Get tomorrow's brief free → [email input] [Send My Free Edition]
No commitment. One sample. See if it works for you.
```

---

## 3 CTA Variants (A/B test these)

| Variant | Copy | Where |
|---------|------|-------|
| A (control) | "View Plans →" | Hero button |
| B | "Send Me a Free Sample →" | Hero + final CTA |
| C | "Start My Subscription — $19/mo" | Pricing cards only |

Recommend testing B vs A first — a free sample has lower friction than "View Plans."

---

## A/B Test Matrix

| Test # | Element | Variant A | Variant B | Hypothesis |
|--------|---------|-----------|-----------|------------|
| 1 | Hero CTA | "View Plans" | "Send Free Sample" | Free sample → higher CTR |
| 2 | Pricing anchor | No default highlight | Pro highlighted "Best for analysts" | Clearer framing → more Pro signups |
| 3 | Social proof | None | "N subscribers" + 1 quote | Trust → higher conversion |

---

## Summary

The page looks great — the dark theme, coverage grid, and methodology section are strong. The conversion infrastructure is missing entirely. **Fix the CTAs, add an email capture, and add proof.** Those three things would push this from a 7 to a 9.
