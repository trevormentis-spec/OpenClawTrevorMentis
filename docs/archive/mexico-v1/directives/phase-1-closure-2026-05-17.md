# Phase 1 Probe #1 — Closure Directive

**Date:** 2026-05-17
**Source:** Principal (Roderick)
**Closes:** Phase 1 probe #1 (identity coherence / scope gate)

## Issues fixed

### (1) Probe C regression — decline reframe-offer restored

Previous terse decline ("no substantive transmission mechanism") for Russia-Ukraine was wrong. Russia-Ukraine has credible Mexico vectors (fertilizer, wheat, Brent). Reframe-offer now requires 2+ vectors to fire; <2 vectors gets the terse decline.

Two-tier decline:
- **Reframe-offer:** for out_of_scope topics with 2+ credible Mexico vectors
- **Terse:** for out_of_scope topics with <2 vectors (e.g., K-pop, NFL, Premier League)

### (2) Confabulated quantification — quality discipline added

Probe A vector 4 contained fabricated specific correlations ("every $0.25/gal increase corresponds to ~15% increase in X"). Added hard rule to both deepseek-prompts.md and adjacent_brief.md: no unsourced specific percentages, correlations, or statistical claims. Direction + magnitude from a named source is fine. Specific numbers without a source are never fine.

### (3) Regression test suite — `--regression-test` flag

Analyst/scope_check.py now has a built-in regression test that runs all four canonical probes and checks expected branch + structural compliance. Must pass before commit after any scope-related change.

Files changed:
- `analyst/scope_check.py` — regression test suite, smarter permissive default (checks vectors before defaulting), two-tier decline
- `analyst/templates/adjacent_brief.md` — quality discipline section
- `skills/daily-intel-brief/references/deepseek-prompts.md` — quality discipline in system prompt
- `memory/2026-05-17.md` — test record
