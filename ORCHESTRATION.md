# ORCHESTRATION.md — Trevor Agent Orchestration Framework

**Version:** 3.0
**Date:** 2026-05-01
**Status:** Active — single source of truth for routing
**Primary Provider:** DeepSeek Direct API

> This is the canonical routing document. If anything in `AGENTS.md`,
> `MEMORY.md`, `REBUILD_ORCHESTRATION.md` (archived), or
> `.openclaw/model-config-note.md` disagrees with this file, this file wins.
> Update this file first, then propagate.

---

## Core Model Routing

### Primary (Default)
- **Model:** `deepseek/deepseek-v4-flash`
- **Provider:** DeepSeek Direct API (no OpenRouter)
- **Use for:** reasoning, research synthesis, document writing, planning,
  memory interaction, the great majority of Trevor's day-to-day work
- **Cost tier:** Low

### Escalation
- **Model:** `deepseek/deepseek-v4-pro`
- **Provider:** DeepSeek Direct API
- **Use for:** complex, ambiguous, or high-precision tasks only
- **Trigger conditions:**
  - Primary reasoning insufficient or self-flagged as low-confidence
  - Final TREVOR product (16-section assessment) requires maximum quality
  - User explicitly requests best possible result
- **Discipline:** never escalate automatically; escalation is opt-in.

### Fallback Chain (resilience, not preference)
Triggered only on 429 / 5xx / timeout / provider-unavailable from primary:

1. Retry primary once with exponential backoff + jitter
2. `deepseek/deepseek-chat` (131K context, simpler)
3. `deepseek/deepseek-v4-pro` (1M context, higher quality, higher cost)
4. `myclaw/minimax-m2.7` (free, last-resort continuity)

---

## Routing Tiers

| Tier        | Model                         | When to use                          |
|-------------|-------------------------------|--------------------------------------|
| Primary     | `deepseek/deepseek-v4-flash`  | Default for all tasks                |
| Escalation  | `deepseek/deepseek-v4-pro`    | Complex / high-stakes only           |
| Resilience  | fallback chain above          | API failure on primary               |

---

## Multimodal Routing

### Diagrams (preferred over images)
- Default: Mermaid (`skills/mermaid`) or hand-rolled SVG / HTML / CSS
- Reasons: cheaper, deterministic, editable, render in chat

### Image Generation
- Only on explicit user request
- Prefer cost-efficient diffusion models via OpenRouter when needed
- Keep prompts concise and structured

### Video Generation
- Only on explicit user request
- Keep outputs short and one-shot

---

## Cost & Performance Discipline

1. Minimize token usage; do not send large raw context unless required
2. For inputs >5K tokens: summarize before reasoning
3. Memory retrieval: top **3** chunks max in fast path
4. Avoid redundant model calls; cache repeated outputs where possible
5. Default pipeline: **Ingest → Summarize → Filter → Reason → Generate**
6. Stop once the task is complete; do not over-refine

---

## Memory Interaction

### Fast Path (default)
- Query vector index via `brain/scripts/brain.py recall "<query>"`
- Inject top 3 relevant chunks into prompt
- **No file reads** in fast path
- **No deep synthesis** in fast path

### Slow Path (deliberate)
- `python3 brain/scripts/brain.py synthesize "<query>"`
- Read recommended source files
- Use only when:
  - Fast-path relevance is low (top score below threshold)
  - Conflicting memories detected
  - Identity / critical decisions in scope
  - Complex multi-step reasoning across memory layers

### Write Path
- Write to file system first (authoritative)
- Refresh vector index via `brain/scripts/brain.py reindex`
- Update daily log in `memory/YYYY-MM-DD.md`

---

## Tool Usage

- Prefer tools over LLM reasoning when a tool exists for the job
- Avoid loops: do not call the same tool twice with the same arguments
  expecting different results
- Run independent tasks in parallel when possible
- Before building a custom integration, check `skills/` for an existing one

---

## Stop Conditions

- Task complete → stop
- Same answer twice → stop, surface to user
- Three consecutive low-confidence outputs → escalate or surface
- Repeated tool failure → ask before retrying

---

## Priority Order

1. **Cost efficiency** — minimize tokens
2. **Speed** — respond promptly; prefer fast path
3. **Relevance** — stay on-topic
4. **Output quality** — escalate only when needed

---

## System Configuration

**Config file:** `~/.openclaw/openclaw.json` (lives outside this repo)

```jsonc
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "deepseek/deepseek-v4-flash",
        "fallbacks": [
          "deepseek/deepseek-chat",
          "deepseek/deepseek-v4-pro",
          "myclaw/minimax-m2.7"
        ]
      }
    }
  },
  "models": {
    "providers": {
      "deepseek": {
        "baseUrl": "https://api.deepseek.com",
        "apiKey": "sk-…"
      }
    }
  },
  "plugins": {
    "entries": {
      "deepseek":   { "enabled": true  },
      "openrouter": { "enabled": false }
    }
  }
}
```

---

## Model Availability

| Model                      | Provider          | Context | Cost Tier   |
|----------------------------|-------------------|---------|-------------|
| deepseek-v4-flash          | DeepSeek Direct   | 195K    | Low         |
| deepseek-chat              | DeepSeek Direct   | 131K    | Low         |
| deepseek-v4-pro            | DeepSeek Direct   | 1M      | Medium-High |
| myclaw/minimax-m2.7        | MyClaw            | 204K    | Free        |
| myclaw/kimi-k2.5           | MyClaw            | 200K    | Free        |

---

## Vocabulary Discipline (TREVOR brand voice)

**Use:** methodology, disclosure, candor, completeness, confidence,
responsiveness, diligence, briefing, finding, assessment, indicator,
posture.

**Avoid:** solution, unlock, empower, revolutionary, disrupt,
cutting-edge, game-changing, best-in-class, synergy, leverage.

---

## Change Log

- **3.0 (2026-05-01):** Reconciled four conflicting routing documents into
  one source of truth. Canonical provider is DeepSeek Direct API.
  REBUILD_ORCHESTRATION.md archived under `docs/archive/`. AGENTS.md,
  MEMORY.md, and `.openclaw/model-config-note.md` aligned.
- **2.0 (2026-04-28):** Switched primary to DeepSeek V4 Flash.
- **1.0 (2026-04-25):** Initial balanced MyClaw default order.

---

*Trevor is a routing system, not a single model. The point of this
framework is to keep that routing legible — to Trevor and to Roderick.*
