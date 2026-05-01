---
name: sat-toolkit
description: Structured Analytic Techniques (SATs) for intelligence work. Use when running an assessment that needs more than intuition — Analysis of Competing Hypotheses, Key Assumptions Check, Pre-mortem, Red Team, Devil's Advocacy, Indicators & Warnings, Scenario Triage. Triggers on any request to "stress-test", "challenge", "red team", "devil's advocate", "compete hypotheses", "pre-mortem", "what could go wrong", or any structured intelligence assessment.
metadata:
  trevor:
    requires:
      bins: [python3]
---

# Structured Analytic Techniques (SAT) Toolkit

A discipline pack for stress-testing intelligence judgments. Each technique
forces a specific kind of rigor that intuitive analysis tends to skip.

## When to use

Apply at least three SATs on any non-trivial assessment. Default starter set:

1. **ACH** — competing hypotheses scored against the evidence
2. **PMESII-PT** — eight-domain environmental scan
3. **I&W** — pre-committed indicators of change

For high-stakes products add KAC, Pre-mortem, Red Team, Devil's Advocacy.

## Techniques

### 1. Analysis of Competing Hypotheses (ACH)

Heuer's method. List 2–4 hypotheses, score each against every piece of
evidence (`++`, `+`, `0`, `-`, `--`). The hypothesis with the **fewest
disconfirming items** wins, not the most confirming.

→ Template: `analyst/templates/ach-matrix.md`

### 2. Key Assumptions Check (KAC)

For each load-bearing assumption: "if wrong, what changes?" + "how would we
know?" Surface the assumptions you didn't realise you were making.

→ Section in `analyst/templates/red-team-review.md` (Assumption audit).

### 3. Pre-mortem

> "It's 30 days from now and this assessment turned out to be wrong. Write
> the post-mortem."

Forces you to invert and surface the failure modes you weren't taking
seriously enough.

→ Section in `analyst/templates/red-team-review.md`.

### 4. Red Team

Steel-man the alternative hypothesis in its strongest form. No straw men.
The point isn't to win — it's to feel the actual force of the alternative.

→ `analyst/templates/red-team-review.md`.

### 5. Devil's Advocacy

Specifically: which counter-evidence did you treat as outliers? What was
their best argument? Why did you discount them?

→ Section in `analyst/templates/red-team-review.md` (Devil's advocacy).

### 6. Indicators & Warnings (I&W)

Commit, **before the fact**, to what would change your mind. If you can't
fill in an I&W table you don't have a judgment, you have a hunch.

→ `analyst/templates/indicators-and-warnings.md`.

### 7. PMESII-PT

Eight-domain scan: Political, Military, Economic, Social, Information,
Infrastructure, Physical environment, Time. Catches blind spots.

→ `analyst/templates/pmesii-pt-scan.md`.

### 8. Scenario Triage

Four-bucket spread: most likely / most dangerous / best case / wildcard.
Probabilities sum to 100.

→ `analyst/playbooks/scenario-triage.md`.

## Procedure

```
1. Read the question and the framing file (tmp/<slug>/00-framing.md)
2. Pick three SATs minimum. Default to ACH + PMESII-PT + I&W.
3. For each SAT:
   a. Open the linked template
   b. Fill it in — don't summarise, fill the actual fields
   c. Save in tmp/<slug>/03-sat-<technique>.md
4. Run a final red-team pass on the integrated assessment.
5. Carry SAT outputs into the analytic-note or TREVOR product.
```

## Anti-patterns

- "I did ACH in my head." No, you didn't. Open the template.
- Hypotheses that aren't really competing (just rephrasings of one).
- I&W indicators that are vibes rather than events.
- Red team that goes through the motions without genuinely challenging.

## See also

- `analyst/playbooks/analytic-workflow.md` — when in the workflow each SAT applies
- `analyst/playbooks/quality-gates.md` — gate 4 (method visibility) and gate 5 (red-team pass)
- `skills/trevor-methodology` — the canonical 11-SATs reference (when present)
