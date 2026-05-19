# Dimension 5 — Cost Discipline

## Current State
- Monthly budget: $140
- Current spend: ~$12.00 (May 3-18, ~$0.79/day avg)
- Phase 2 daily: $20/day, currently at $0.011 (first cycle)
- Current balance: $84.33 (DeepSeek)
- OpenRouter credits: $169.14 limit, $30.85 used

## Evidence
- DeepSeek usage JSON: snapshots show $0.47→$1.51 cumulative (May 2→May 17)
- OpenRouter credits: $169.14 limit, $22.44/mo usage
- USMCA v3 multi-turn: ~$1.00 (10 Opus calls at ~$0.10 each)
- Worker first cycle: $0.011 of $20 daily budget

## Friction Points
- No real-time cost tracking — requires manual balance API call
- Opus calls at $15/$60 per M tokens can spike quickly if used indiscreetly
- Multi-turn at 10 Opus calls per flagship brief = $1/brief, which at 30 briefs/month = $30/month

## Gaps
1. AUTO_FIX: Add cost check to pre-generation routing (check balance before calling Opus)
2. PRINCIPAL_REVIEW: Opus budget cap — how much is acceptable per month?
