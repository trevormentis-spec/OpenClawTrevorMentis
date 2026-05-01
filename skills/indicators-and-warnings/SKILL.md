---
name: indicators-and-warnings
description: Pre-commit to observable events that would change a judgment. Use whenever Trevor produces a forward-looking assessment, scenario spread, or anything where the question "what would make us update" matters. Triggers on "what would change", "monitor for", "watch for", "indicators", "early warning", "warning signs", or any forecasting product.
metadata:
  trevor:
    requires:
      bins: [python3]
---

# Indicators & Warnings (I&W)

The discipline of writing down, **before the fact**, what would move your
judgment. If you can't fill in an I&W table you don't have a judgment, you
have a hunch.

## Why I&W matters

Most analytic failure modes come from one of two things: missing the change
of state when it happened, or rationalizing post-hoc that you'd have caught
it. I&W defends against both because the indicators are committed in
advance.

## Format

Each indicator must be:

- **Concrete** — a specific event a journalist could report on.
- **Observable** — Trevor can actually monitor for it (RSS, API, search,
  or designated source).
- **Time-bounded** — within a defined window.
- **Direction-tagged** — confirms which hypothesis, or a wildcard tell.

## Template

→ `analyst/templates/indicators-and-warnings.md`

## Procedure

```
1. After picking your top hypothesis (post-ACH), list the 4–8 events
   that, if observed, would tighten or break that hypothesis.
2. For each event:
   - Specific phrasing (no vibes — events, not "tensions rise")
   - Where you'd see it (UKMTO advisory? IAEA bulletin? Bloomberg wire?)
   - Lead time you'd expect from event to consequence
   - Direction: confirms / disconfirms / wildcard
3. Set decision rules: "≥2 confirming I1+I3 in 72h → tighten band".
4. Hand the I&W table to the user with the assessment so they can
   monitor with you.
5. When an indicator fires, log it in memory/YYYY-MM-DD.md and
   re-evaluate. Don't quietly downgrade the band.
```

## Anti-patterns

- Vibes-as-indicators ("public sentiment shifts"). Not an event.
- Indicators on the confirming side only. You need disconfirmers too,
  otherwise you've built confirming-bias instrumentation.
- Indicators that are guaranteed to fire ("there will be a statement").
  Decorative.
- Disconnected from monitoring: you wrote 8 indicators but you're not
  actually watching the channels they'd appear on.

## Companion: standing I&W boards

For ongoing situations (Hormuz, Lebanon, US-Iran), maintain a standing
I&W table that updates over time. Save under
`analyst/iw-boards/<topic>.md` (create the directory when needed).

The standing board's value compounds: it becomes a record of what
fired and what didn't, useful for retrospective calibration.
