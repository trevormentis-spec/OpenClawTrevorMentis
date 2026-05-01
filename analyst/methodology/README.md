# analyst/methodology/

Bridge to Trevor's full methodology toolkit. The deep methodology lives in
the **trevor-methodology** skill (`skills/trevor-methodology/`), not in this
directory.

## Why a bridge?

The `analyst/` tree is workflow-shaped: playbooks (how) and templates
(what to fill in). The `trevor-methodology/` skill is reference-shaped:
canonical definitions of the 16 sections, 11 SATs, 6 calibrations, Sherman
Kent bands, NATO Admiralty codes, scenario triage, and the brand library.

Keeping them separate means:
- The skill can be versioned, audited, and shared independently
- The analyst scaffold stays workflow-clean
- Updating one doesn't invalidate the other

## Pointers

| Looking for…                            | Open                                                   |
|-----------------------------------------|--------------------------------------------------------|
| 16-section structure (sections 12–27)   | `skills/trevor-methodology/methodology/16-sections.md` |
| 6 calibration corrections (Iran review) | `skills/trevor-methodology/methodology/6-calibrations.md` |
| Sherman Kent probability bands          | `skills/trevor-methodology/methodology/sherman-kent-bands.md` |
| NATO Admiralty source rating            | `skills/trevor-methodology/methodology/nato-admiralty.md` |
| 11 Structured Analytic Techniques       | `skills/trevor-methodology/methodology/11-SATs.md`     |
| Hypothesis archetypes                   | `skills/trevor-methodology/methodology/hypothesis-archetypes.md` |
| Brand library (concentric, eclipse, …)  | `skills/trevor-methodology/brands/`                    |
| Validation pipeline                     | `skills/trevor-methodology/pipeline/validate.py`       |

## When the skill is missing

If `skills/trevor-methodology/` is not present locally, Trevor should:

1. Note the absence as a Phase 0 blocker.
2. Fall back to the lightweight templates in `analyst/templates/` (good
   enough for a 1-pager).
3. Surface the gap to the user before producing a full TREVOR product.
