# Model config note

**Canonical source of truth:** `/ORCHESTRATION.md`. This file is a quick-reference
mirror only.

## Current configuration (2026-05-01)

- **Primary:** `deepseek/deepseek-v4-flash` via DeepSeek Direct API
- **Escalation:** `deepseek/deepseek-v4-pro` (manual)
- **Resilience fallback chain:**
  1. `deepseek/deepseek-chat`
  2. `deepseek/deepseek-v4-pro`
  3. `myclaw/minimax-m2.7`
- **OpenRouter:** disabled.

## History

- 2026-05-01 — Reconciled routing to DeepSeek Direct (this entry).
- 2026-04-28 — Rebuilt to default DeepSeek V4 Flash via OpenRouter.
- 2026-04-25 — Original balanced MyClaw default order
  (gpt-5.4 / minimax-m2.7 / claude-opus-4.7).
