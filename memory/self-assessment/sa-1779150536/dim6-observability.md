# Dimension 6 — Observability

## Current State
- STATUS.md: persistent status surface at repo root
- worker_log.jsonl: task execution log (20 entries so far)
- collector-health.json: per-collector health tracking
- Brain episodic memory: JSONL by day

## Evidence
- STATUS.md has 7 directives with per-task checkboxes, awaiting-approval items, cost summary
- worker_log.jsonl shows timestamps, costs, outcomes for every task
- Principal verification commands at top of STATUS.md

## Friction Points
- No centralized log viewer — logs are scattered across multiple JSON/JSONL files
- Brain episodic memory was last updated 2026-05-15 (3 days stale)
- worker_log.jsonl only has 20 entries — limited sample for analysis
- No guard execution log — can't tell when guards modified behavior

## Gaps
1. AUTO_FIX: Brain episodic memory needs reindex — stale since May 15
2. PRINCIPAL_REVIEW: Centralized observability dashboard (collector health + guard fires + cost in one place)
