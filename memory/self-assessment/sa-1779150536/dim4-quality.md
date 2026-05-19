# Dimension 4 — Quality Discipline

## Current State
- scope_check.py: 4/4 regression probes passing (Probe C updated from out_of_scope → adjacent)
- fabrication_check.py: Caught 15 issues in Bajío v2 (3 fabricated contracts + 12 unsourced cost ranges)
- themes_preflight.py: Caught energy_infra gap (2 vs required 3 mentions) in Bajío v2
- routing.py: 4-tier model, tested against 5 scenarios
- escalation_guard.py: Pre/mid/post-generation checks

## Evidence
- Blocklist cleanup: removed 12 of 23 overreaching keywords (scope.yaml)
- Fabrication detector blocked Bajío v1 Kalshi fabrications
- Themes preflight caught energy_infra missing from Bajío v2 (2 mentions vs 58 in v3)
- Post-generation check now wired into multi-turn generator

## Friction Points
- Guards are separate scripts — no unified guard pipeline runs on every output
- No guard execution log (who fired, when, for which brief)
- fabrication_check regex missed "rise by 15-25%" pattern (verb-before-number)
- themes_preflight uses keyword counting, not semantic coverage assessment

## Gaps
1. AUTO_FIX: fabrication_check regex now handles verb-before-number (fix applied in v2)
2. PRINCIPAL_REVIEW: Unified guard pipeline — run all guards on every output before delivery
3. PRINCIPAL_REVIEW: Guard execution audit log — track false positive/negative rates
