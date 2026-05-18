# Routing Addition — DeepSeek V4 Pro Mid-Tier

**Effective:** 2026-05-18
**Source:** Four-tier routing model between Haiku and Opus 4.7

## Change

DeepSeek V4 Pro (`deepseek/deepseek-v4-pro`) added as Tier 2. Pricing: $0.435/M input, $0.87/M output (97% cheaper than Opus 4.7's $15/$60).

## Routing Logic (analyst/routing.py)

- Complexity triggers WITHOUT flagship tag → **V4 Pro** (default for complex work)
- Complexity triggers WITH flagship/subscriber-facing/premium audience → **Opus 4.7**
- Escalation from Haiku → **V4 Pro** first, Opus only if V4 Pro capacity exceeded or flagship

## Test Results

| Scenario | Expected | Actual |
|----------|----------|--------|
| USMCA flagship | Opus 4.7 | Opus 4.7 ✅ |
| Complex entity deepening (no flagship) | V4 Pro | V4 Pro ✅ |
| Daily brief 600-900w | Haiku | Haiku ✅ |
| Bulk mechanical | DeepSeek Flash | Flash ✅ |
| Medium brief no triggers | DeepSeek Flash | Flash ✅ |

## Cost-optimization

V4 Pro at $0.87/M output covers ~85% of complex analytical work at 1.5% of Opus cost ($0.87 vs $60/M). The ~15% of work with flagship/family-office/subscriber-facing tags uses Opus for marginal quality where the commercial value justifies the cost.
