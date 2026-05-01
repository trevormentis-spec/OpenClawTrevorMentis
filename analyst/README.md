# analyst/

Trevor's intelligence-tradecraft scaffold. Everything here is **process**, not data.

## Layout

```
analyst/
├── playbooks/         # how to run a piece of work end to end
├── templates/         # blank forms — fill these in for an actual product
├── methodology/       # references the trevor-methodology skill
└── meta/              # durable lists (sources, glossaries, brands)
```

## When to reach in here

| You are about to…                                           | Open                                      |
|-------------------------------------------------------------|-------------------------------------------|
| Run a multi-phase intelligence assessment                   | `playbooks/analytic-workflow.md`          |
| Draft a one-page assessment for the user                    | `templates/analytic-note.md`              |
| Write a TREVOR-format report                                | `methodology/README.md` → trevor-methodology skill |
| Compete two hypotheses against the same evidence            | `templates/ach-matrix.md`                 |
| Score a source you've never used before                     | `templates/source-evaluation-matrix.md`   |
| Build an early-warning checklist                            | `templates/indicators-and-warnings.md`    |
| Map a scenario across political/military/economic dimensions| `templates/pmesii-pt-scan.md`             |
| Stress-test a finding before publication                    | `templates/red-team-review.md`            |
| Decide whether to publish or keep collecting                | `playbooks/quality-gates.md`              |

## Discipline

These templates exist so that when Trevor produces an intelligence product the
**structure is already correct** before any prose is written. Skip-the-template
products tend to confuse confidence with conviction. Don't.

## Source list

`meta/sources.json` is the durable list of monitored OSINT sources (signal
level, focus areas, URLs). Update it when a source proves itself or fails.
