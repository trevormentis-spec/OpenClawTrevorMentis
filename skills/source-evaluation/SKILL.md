---
name: source-evaluation
description: Score sources for reliability and credibility using the NATO Admiralty Code (A1–F6) and calibrate confidence using Sherman Kent probability bands. Use whenever Trevor cites an OSINT source, evaluates conflicting reports, or attaches a confidence band to a key judgment. Triggers on any request involving "how reliable is", "rate this source", "what's our confidence", "probability", or "Admiralty code".
metadata:
  trevor:
    requires:
      bins: [python3]
---

# Source Evaluation

Two independent disciplines: **rate the source**, **calibrate the
confidence**. Both are mandatory for Trevor citations.

## NATO Admiralty Code

Score every cited source on two axes:

### Reliability of source

| Code | Meaning              | When to use                                                |
|------|----------------------|------------------------------------------------------------|
| A    | Completely reliable  | Verified track record. Established primaries (UKMTO, IAEA) |
| B    | Usually reliable     | Mostly accurate; rare minor errors (major wires, peer-reviewed) |
| C    | Fairly reliable      | Mixed track record (regional outlets, well-sourced blogs)  |
| D    | Not usually reliable | Bias dominates (state media of an interested party)        |
| E    | Unreliable           | Pattern of inaccuracy                                      |
| F    | Cannot be judged     | Genuinely unknown — not a default for "I didn't check"     |

### Credibility of information

| Code | Meaning                             |
|------|-------------------------------------|
| 1    | Confirmed by independent sources    |
| 2    | Probably true                       |
| 3    | Possibly true                       |
| 4    | Doubtful                            |
| 5    | Improbable                          |
| 6    | Cannot be judged                    |

Cite as `A1`, `B2`, `C3`, etc. **Anything below `C3` should not anchor a key
judgment without independent corroboration.**

→ Full template with worked example: `analyst/templates/source-evaluation-matrix.md`

## Sherman Kent Probability Bands

Use these — and only these — for probability language.

| Band                 | Range       | Verbal anchor          |
|----------------------|-------------|------------------------|
| Almost certain       | 93–99%      | "almost certain"       |
| Highly likely        | 75–85%      | "highly likely"        |
| Likely / Probable    | 55–70%      | "likely", "probable"   |
| Even chance          | 45–55%      | "roughly even chance"  |
| Unlikely             | 25–35%      | "unlikely"             |
| Highly unlikely      | 10–20%      | "highly unlikely"      |
| Almost no chance     | 1–5%        | "remote chance"        |

### Discipline rules

1. **Never** use "could", "may", "might" without a band. They smuggle
   uncertainty.
2. **Never** report a point estimate ("65% probability of X"). Report a
   band.
3. The verbal anchor and the numeric band must agree. If you write
   "highly likely" while feeling 50%, downgrade to "even chance".
4. Sherman Kent bands are about **confidence in a judgment**, not source
   reliability. Don't conflate them.

## Procedure

```
1. For every source you cite:
   a. Look up its Admiralty rating in analyst/meta/sources.json
      (add if missing — see analyst/playbooks/source-acquisition.md)
   b. Score the specific information item independently
   c. Attach the combined code (e.g. B2) at point of citation
2. For every key judgment:
   a. Pick a Sherman Kent band that honestly reflects evidence weight
   b. Use the verbal anchor from the table — don't invent new ones
   c. Note in the assessment which evidence anchors the band
3. Quality-gate before delivery: every cited source has a code; every
   key judgment has a band. (See analyst/playbooks/quality-gates.md
   gates 2 and 3.)
```

## Anti-patterns

- Defaulting to F6 because rating is effort. F6 is for genuinely unknown
  sources.
- Source laundering: think tank cited a primary, you cite the think tank
  as if it were the primary. Score the chain you actually have.
- Round-tripping reliability through credibility — they're independent
  axes.
- Stair-stepping confidence: starting at "highly likely" and creeping to
  "almost certain" as the assessment is written.
