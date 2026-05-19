# Dimension 1 — Routing Autonomy

## Current State
- analyst/routing.py: Complexity-based routing with 4 tiers (Opus/V4 Pro/Flash/removed Haiku)
- analyst/escalation_guard.py: Pre/mid/post-generation checks
- ORCHESTRATION.md: Routing table documented
- Tested: USMCA flagship → Opus ✅, entity deepening → V4 Pro ✅, daily brief → Flash ✅

## Evidence
- routing.py line 21-36: 7 Opus triggers (target>=3000, visuals>=8, themes>=5, multi_scenario, flagship_stress_test, premium_audience, output_tokens>=4K)
- routing.py COMMIT: dffd12a — V4 Pro mid-tier added, Haiku removed
- escalation_guard.py COMMIT: dffd12a — pre/mid/post-generation checks
- USMCA v2 test: correct Opus routing ✅
- USMCA v3 test: multi-turn Opus routing ✅

## Friction Points
- Routing only works within analyst/routing.py if explicitly called — no automatic pre-generation hook
- escalation_guard.py post-generation check isn't wired into the generation pipeline (no hook runs it automatically after each brief)
- Multi-turn generator has hardcoded model assignments per section, bypasses routing.py

## Gaps
1. AUTO_FIX: escalation_guard not wired as post-generation hook — briefs can pass without validation
2. PRINCIPAL_REVIEW: routing bypass in multi-turn generator — sections hardcode Opus/V4 Pro instead of calling routing.py
3. PRINCIPAL_REVIEW: no automatic pre-generation routing check on single-call briefs
