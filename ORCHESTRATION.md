# ORCHESTRATION.md — Trevor Agent Orchestration Framework

**Version:** 2.0  
**Date:** 2026-04-28  
**Status:** Active  
**Primary Model:** `deepseek/deepseek-v4-flash`

---

## Core Model Routing

### Primary Model (Default)
- **Model:** `deepseek/deepseek-v4-flash`
- **Use for:** reasoning, research synthesis, document writing, planning, memory interaction, most tasks
- **Cost:** Low (Flash tier)

### Escalation Model
- **Model:** `deepseek/deepseek-v4-pro`
- **Use for:** Complex, ambiguous, or high-precision tasks only
- **Trigger conditions:**
  - Reasoning fails or is insufficient
  - Task is highly complex or ambiguous
  - Final output requires maximum quality
  - User explicitly requests best possible result

**Never escalate automatically.** Only escalate when necessary.

---

## Routing Tiers

| Tier | Model | When |
|------|-------|------|
| Primary | `deepseek/deepseek-v4-flash` | Default for all tasks |
| Escalation | `deepseek/deepseek-v4-pro` | Complex/ambiguous tasks only |
| Fallback | `myclaw/minimax-m2.7` | API failure, model unavailable |

---

## Multimodal Routing

### Image Generation
- Use OpenRouter image generation models
- Prefer cost-efficient diffusion models
- Generate only when **explicitly requested**
- Keep prompts concise and structured

### Diagrams (Preferred Over Images)
- **DO NOT** generate images by default for diagrams
- Generate instead:
  - Mermaid diagrams
  - SVG
  - HTML/CSS diagrams
- Reasons: cheaper, deterministic, editable

### Video Generation
- Use only when **explicitly requested**
- Keep outputs short and simple
- Avoid unnecessary iterations

---

## Cost Optimization Rules

1. Always minimize token usage
2. Never send large raw context unless required
3. Summarize before reasoning (use Hugging Face small models for >5k token inputs)
4. Retrieve only **top 3 relevant memory chunks** from vector index
5. Avoid redundant model calls
6. Cache repeated outputs where possible
7. Default pipeline: **Ingest → Summarize → Filter → Reason → Generate**

---

## Memory Interaction

### Fast Path (default)
- Query vector index via `brain_reflector.py query`
- Inject top 3 relevant chunks into prompt
- **No file reads** in fast path
- **No brain.py synthesis** in fast path

### Slow Path (fallback)
- Use `brain.py synthesize`
- Read source files
- Perform deep cross-referencing
- Use only when:
  - Fast path relevance is low
  - Conflicting memories
  - Identity / critical decisions
  - Complex multi-step reasoning

### Write Path
- Store to file system first (authoritative)
- Sync to vector index via `brain_reflector.py store`
- Update daily log in `memory/YYYY-MM-DD.md`

---

## Tool Usage

- Prefer tools over LLM reasoning when appropriate
- Avoid unnecessary tool loops
- Run independent tasks in parallel when possible
- Use Hugging Face for text preprocessing (summarization, embeddings)

---

## Stop Conditions

- Stop once the task is complete
- Do not over-refine unless requested
- Do not escalate unnecessarily
- Ask only when genuinely blocked

---

## Priority Order

1. **Cost efficiency** — minimize token usage
2. **Speed** — respond promptly
3. **Relevance** — stay on-topic, use fast memory
4. **Output quality** — escalate only when needed

---

## System Configuration

**Config file:** `~/.openclaw/openclaw.json`

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "deepseek/deepseek-v4-flash",
        "fallbacks": [
          "deepseek/deepseek-chat",
          "deepseek/deepseek-v4-pro"
        ]
      }
    }
  },
  "models": {
    "providers": {
      "deepseek": {
        "baseUrl": "https://api.deepseek.com",
        "apiKey": "sk-eee…c894"
      }
    }
  },
  "plugins": {
    "entries": {
      "deepseek": {
        "enabled": true
      }
    }
  }
}
```

---

## Model Availability

| Model | Provider | Context | Cost Tier |
|-------|----------|---------|-----------|
| deepseek-v4-flash | OpenRouter | 195K | Low |
| auto | OpenRouter | Variable | Medium-High |
| kimi-k2.5 | MyClaw | 200K | Free |
| minimax-m2.7 | MyClaw | 204K | Free |

---

## Vocabulary Discipline

Per TREVOR brand voice — use precise, institutional language:

**USE:** methodology, disclosure, candor, completeness, confidence, responsiveness, diligence, briefing, finding, assessment, indicator, posture

**AVOID:** solution, unlock, empower, revolutionary, disrupt, cutting-edge, game-changing, best-in-class, synergy, leverage

---

*This framework optimizes for cost efficiency and output quality. Trevor is a routing system, not a single model.*
