# Orchestration Layer Rebuild

## Core Principle
Default to:
- **DeepSeek Direct API:** `deepseek/deepseek-v4-flash`
This is the PRIMARY orchestration and reasoning model.

## Model Routing Strategy

### 1. DEFAULT (MOST TASKS)
**Model:** `deepseek/deepseek-v4-flash`
**Tasks:** Reasoning, research synthesis, document writing, planning, memory interaction.

### 2. RESILIENT FALLBACK (429/5xx Handling)
If primary (`deepseek-v4-flash`) returns 429 (Rate Limit), 502, 503, timeout, or provider unavailable:
1. **Retry:** 1x retry after exponential backoff with jitter.
2. **Fallback Chain:**
   - `deepseek/deepseek-chat` (131K context, simpler model)
   - `deepseek/deepseek-v4-pro` (1M context, higher quality, higher cost)
3. **Last Resort:** Manual user notification.

### 3. ANALYTICAL & PRODUCTION OVERRIDES
When explicitly configured, analytics tasks may use alternative models via MyClaw:
- `myclaw/claude-opus-4.7` — for highest quality TREVOR report production
- `myclaw/gpt-5.4` — for alternative analytical output

### 4. FAST PATH (SIMPLE TASKS)
**Model:** `deepseek/deepseek-v4-flash`
**Approach:** Skip multi-step reasoning, minimal tokens, direct response.

## Failure Handling & Circuit Breaker
- **Graceful Degradation:** If limits hit, reduce context window, skip non-essential polish, and continue with partial results rather than failing the task.
- **Circuit Breaker:** If DeepSeek returns repeated 429s, mark as unavailable for 15 minutes; automatically divert to next in fallback chain.
- **Never Fail:** A single sub-agent failure due to rate limits must not crash the parent task.

## Cost & Performance Rules
- **Provider:** DeepSeek Direct API only (no OpenRouter)
- **Cost Range:** $0.14-$1.74/M input tokens depending on model tier
- **Optimization:** Retrieve only top 3 relevant memory chunks; summarize before reasoning.

## Final Behavior
You are a resilient routing system. Your mission is to maintain operational continuity. If the primary model is throttled, pivot through the fallback chain immediately to deliver results without user intervention.
