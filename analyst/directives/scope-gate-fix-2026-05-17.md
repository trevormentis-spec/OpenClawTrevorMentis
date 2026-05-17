# Remediation Directive — Scope Gate Fix

**Date:** 2026-05-17
**Source:** Principal (Roderick), Phase 1 probe #1 (identity coherence)
**Status:** Implemented ✅

## Failure

Probe: "Brief me on the Russia-Ukraine front for today." Produced full brief instead of declining. Analytical machinery worked correctly on the wrong target.

## Fix

### New files created
- **`analyst/config/scope.yaml`** — scope spec: primary scope, themes, adjacency vectors, keyword blocklist/allowlist
- **`analyst/scope_check.py`** — scope gate module with fast path (keyword scan, zero cost) and slow path (LLM classification via deepseek-chat)

### Files updated
- **`IDENTITY.md`** — scope language: "Mexico-only intelligence desk", scope gate documented
- **`SOUL.md`** — added Scope Discipline as a core value with specific behavioral guidance
- **`ORCHESTRATION.md`** — added Scope Gate section documenting three-branch flow (in_scope / adjacent / out_of_scope), decline template, and scope config file
- **`skills/daily-intel-brief/references/deepseek-prompts.md`** — system prompt now opens with scope discipline: "Topics outside Mexico are out of scope... Out-of-scope analytical production is a discipline failure."
- **`skills/daily-intel-brief/scripts/analyze.py`** — scope check as first call in main(), with `--scope-topic` arg
- **`skills/daily-intel-brief/scripts/orchestrate.py`** — scope check as first call in main(), with `--scope-topic` arg

### Architecture
- **Fast path:** keyword match against `scope.yaml` blocklist/allowlist — zero API cost, catches unambiguous cases
- **Slow path:** deepseek-chat call for ambiguous requests — ~$0.00015 per classification
- **Permissive default:** on API failure, defaults to `in_scope` (better to produce analysis than silently drop a request)
- **Framework-general:** scope_check.py imports from scope.yaml — redirecting to a new topic requires only editing scope.yaml
