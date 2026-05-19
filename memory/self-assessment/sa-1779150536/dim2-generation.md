# Dimension 2 — Generation Autonomy

## Current State
- Single-call: DeepSeek Chat / V4 Pro, bounded by 8192 max_tokens
- Multi-turn: 10-section generator, Opus 4.7 per section, ~$1/brief
- USMCA v3: 4603 words, 10 sections, Opus 4.7, clean ending ✅

## Evidence
- USMCA v1 (single-call DeepSeek): 3,443 words, TRUNCATED — sections 7-10 missing
- USMCA v2 (single-call Opus): 2,963 words, max_tokens hit at 8192
- USMCA v3 (multi-turn Opus): 4603 words, all 10 sections complete
- Bajío v1: fabricated Kalshi contracts (routing failure — should have used Opus)
- Bajío v2: fabrication detector caught issues
- Bajío v3: themes_preflight caught energy_infra gap

## Friction Points
- Single-call is fundamentally bounded at ~3,000 words max
- Opus 4.7 single call caps at ~3,000 words even with max_tokens=8192
- Multi-turn requires 10x API calls vs 1x — latency tradeoff

## Gaps
1. AUTO_FIX: No auto-multi-turn-escalation — when single-call target >3000w, should multi-turn automatically
2. PRINCIPAL_REVIEW: V4 Pro sections 7-10 produced 0 words in first multi-turn test (model name issue, now fixed)
3. PRINCIPAL_REVIEW: Multi-turn inconsistency risk — sections generated independently can contradict
