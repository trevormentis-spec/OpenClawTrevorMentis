# Playbook: Scenario Triage

When the user asks "what could happen", produce a clean three-or-four scenario
spread instead of a single forecast.

## The four buckets

| Scenario        | Definition                                          | Typical band |
|-----------------|-----------------------------------------------------|--------------|
| Most likely     | Continuation of current trajectory.                 | 50–65%       |
| Most dangerous  | Escalation that's plausible, not preferred.         | 15–30%       |
| Best case       | Material de-escalation given current dynamics.      | 10–20%       |
| Wildcard        | Low-probability, high-impact non-linearity.         | 1–10%        |

Probabilities should sum to 100. If they don't, you're hiding uncertainty
inside one of the buckets.

## Format per scenario

- **One-line description**
- **Probability band** (Sherman Kent)
- **Triggering indicators** — concrete observable events
- **Consequences** — what happens to the user's equities
- **Watch-for tells** — what would move the band up or down

## Anti-patterns

- Three near-identical scenarios with different language. (You're not
  triaging.)
- A "best case" that's actually the analyst's preferred outcome rather
  than a structurally available one.
- A wildcard that's just a less-likely version of "most dangerous".
- Probabilities that sum to less than 100 because nothing was said about
  status quo. Status quo IS a scenario.
