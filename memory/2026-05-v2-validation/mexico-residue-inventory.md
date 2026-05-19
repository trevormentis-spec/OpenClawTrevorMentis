# Mexico Residue Inventory — v2 Cleanup

## Category A — ACTIVE (referenced by non-Mexico v2 code)

| # | File | Referenced By | Notes |
|---|---|---|---|
| 1 | `scripts/mexico-daily-scan.py` | `scripts/daily-brief-cron.sh`, `analyst/planner.py` | Still wired into daily cron. Must be decoupled before archiving. |
| 2 | `scripts/merge_mexico_into_incidents.py` | `scripts/daily-brief-cron.sh` | Still wired into daily cron merge step. |
| 3 | `scripts/daily-brief-cron.sh` (contains mexico steps) | Cron pipeline | Steps 0a and 1b reference Mexico scripts. Needs principal decision on cron migration. |

## Category B — DORMANT (exist but no active references in non-Mexico code)

| # | File | Type | Action |
|---|---|---|---|
| 4 | `analysis/cia-mexico-ground-branch-2026-05-13.md` | Analysis note | Archive to docs/archive/mexico-v1/ |
| 5 | `analysis/mexico-brief-2026-05-15.md` | Analysis note | Archive |
| 6 | `analysis/mexico-flagship-2026-production-brief.md` | Production spec | Archive |
| 7 | `analysis/mexico-flagship-2026-source-compendium.md` | Source compendium | Archive |
| 8 | `analyst/angles/mexico/` | Knowledge directory | Archive |
| 9 | `analyst/directives/2026-05-mexico-pivot.md` | Directive | Archive (there's already a copy in docs/archive/) |
| 10 | `analyst/knowledge/mexico/` | Knowledge directory | Archive |
| 11 | `analyst/meta/sources-mexico.json` | Source registry | Archive |
| 12 | `brain/memory/semantic/mexico/` | Knowledge base | Archive |
| 13 | `memory/2026-05-15-24hr-mexico-status.md` | Status memo | Archive |
| 14 | `memory/2026-05-15-friday-memo-mexico.md` | Status memo | Archive |

## Category C — BROKEN (reference removed v1 modules)

None identified. All Mexico files reference module-internal structures.

## Category D — REUSABLE PATTERN (generalizable)

| # | File | Status |
|---|---|---|
| 15 | `scripts/mexico_morning_brief.py` | Already generalized → `scripts/topic_morning_brief.py` |

---

### Autonomous actions taken:
- `scripts/topic_morning_brief.py` created (generalizes Mexico morning brief pattern)
- Category B files: batched to archive (see below)
- Category D: complete (generalization done)

### Surfaced for principal decision (Category A):
1. `scripts/mexico-daily-scan.py` — still referenced by cron and planner
2. `scripts/merge_mexico_into_incidents.py` — still referenced by cron
3. `scripts/daily-brief-cron.sh` — still has Mexico-specific steps

These cannot be archived until the cron pipeline is updated to be topic-general.
