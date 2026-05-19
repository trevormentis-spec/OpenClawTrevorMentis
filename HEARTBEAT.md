# HEARTBEAT.md — Trevor periodic collection cycle

Trevor runs a full collection cycle on heartbeat.
Each fire: run one phase, report, rotate to next phase.
Goal: every source pulled at least once per day.

## Phases (rotate through; one per heartbeat fire)

- [ ] Phase A — OpenWeb API specs + Mexico custom specs + Wikipedia monitor
- [ ] Phase B — Social monitor (Bluesky + HackerNews) + source cross-check
- [ ] Phase C — RSS feed collection + pipeline stats
- [ ] Phase D — Idle / memory maintenance / cost snapshot

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
