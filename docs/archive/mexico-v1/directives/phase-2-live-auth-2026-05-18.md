# Phase 2 Live Mode Authorization

**Effective:** 2026-05-18
**Source:** Principal review of five pre-condition completion
**Status:** Live mode authorized. 7-day evaluation clock starts at first live cycle.

---

## Operating Terms

1. **Daily budget cap:** $20. Weekly cap: $140. Worker halts at cap and surfaces in checkpoint.
2. **Daily checkpoint memo:** `memory/<date>-phase-2-day-N.md` with per-task tables, cost vs budget, blocked actions, surfaced capability gaps.
3. **Mexico pipeline convergence:** Planner reads from mexico-daily-scan.py output, not global pipeline's incidents.json.
4. **Verdict distribution monitoring:** Track whether new judgments populate `partial_confirmed` and `not_yet_testable`.
5. **All standing rules apply:** No guard modifications, no identity changes, no external publication, no skill installs, no tracking resets, propose-and-park for architectural changes.

---

## Week-End Evaluation (after 7 days)

All 7 success criteria pass → Phase 3. 4-5 pass → tune and re-run. <4 pass → diagnose gaps.

## Change Log

- **2026-05-18:** Phase 2 live mode authorized by principal. Worker default = dry-run, --live flag required for execution.
