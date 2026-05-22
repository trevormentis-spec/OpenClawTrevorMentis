# HEARTBEAT.md — Trevor periodic collection cycle

Trevor runs a full collection cycle on heartbeat.
Each fire: run one phase, report, rotate to next phase.
Goal: every source pulled at least once per day.

## Phases (rotate through; one per heartbeat fire)

- [ ] Phase A — RSS feed health audit (test all 260+ feeds, flag dead/slow)
- [ ] Phase B — Source discovery (find new RSS/Substack feeds for gap regions)
- [ ] Phase C — Source pruning (remove dead feeds, add replacements from discovery)
- [ ] Phase D — Collection state + cost snapshot + brain reindex

After all phases complete, cycle resets. Each phase contributes to a continuous improvement loop:
test → discover → add → prune, keeping the feed list healthy and coverage balanced.

After all phases complete, cycle resets.

## State

State file: memory/heartbeat-state.json
This file tracks which phase to run next and when the last full
cycle completed.

## Priority

If any phase fails, log the failure and continue to next fire.
Do not stop the cycle on non-critical failures.

## Full cycle override

bash scripts/collection-cycle.sh  # runs ALL phases immediately
