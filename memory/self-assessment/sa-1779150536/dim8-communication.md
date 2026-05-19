# Dimension 8 — Communication

## Current State
- STATUS.md: Persistent, self-service, updated via status_generator.py --refresh
- Handback memo: memory/2026-05-17-overnight-handback.md — 400+ lines, comprehensive
- Principal verification commands: Documented at top of STATUS.md (7 commands)
- Awaiting approval items: 6 items surfaced in STATUS.md

## Evidence
- STATUS.md at repo root: 7 directives tracked
- Handback memo: Covers Phase 1, Phase 2, routing fixes, presentation stack, source expansion
- Principal verification: git pull && cat STATUS.md works from any session

## Friction Points
- STATUS.md only updates when explicitly refreshed (status_generator.py --refresh)
- No automatic update on commit or directive action
- Handback memos and STATUS.md are separate — duplication risk
- Awaiting-approval items in STATUS.md don't auto-age (no "raised N days ago" tracking)

## Gaps
1. AUTO_FIX: Add git hook or watchdog to auto-refresh STATUS.md on relevant changes
2. PRINCIPAL_REVIEW: Auto-age awaiting-approval items — items >7 days surfaced more prominently
