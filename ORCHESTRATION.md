# ORCHESTRATION.md — Trevor Agent Orchestration Framework

**Version:** 3.2
**Date:** 2026-05-12
**Status:** Active — single source of truth for routing
**Primary Provider:** DeepSeek Direct API (non-strategic tasks)
**Strategic Provider:** OpenRouter (Tier-1 strategic analysis only)

> This is the canonical routing document. If anything in `AGENTS.md`,
> `MEMORY.md`, `REBUILD_ORCHESTRATION.md` (archived), or
> `.openclaw/model-config-note.md` disagrees with this file, this file wins.
> Update this file first, then propagate.

---

## Core Model Routing

### Tier-1 — Strategic Analysis
- **Model:** `anthropic/claude-opus-4.7`
- **Provider:** OpenRouter
- **Use for:** executive summary composition, key judgment calibration,
  adversarial red-team analysis. Tasks requiring strategic reasoning,
  complex trade-off analysis, and multi-factor synthesis.
- **Cost tier:** High (~$5/M input, ~$25/M output)
- **Discipline:** Only the daily intel brief's highest-value cognitive
  work. Never for routine collection, regional data synthesis, chat
  responses, or tool orchestration.

### Tier-2 — Regional Data Synthesis
- **Model:** `deepseek/deepseek-v4-flash`
- **Provider:** DeepSeek Direct API
- **Use for:** 6 regional analyses (Europe, Asia, Middle East, North
  America, South America, Global Finance). Data synthesis from collected
  incidents into structured analytical JSON.
- **Cost tier:** Low ($0.14/M input, $0.28/M output)
- **Context window:** 1M tokens (handles full incident dumps)

### Tier-3 — Conversational & Tool Use
- **Model:** `deepseek/deepseek-v4-flash`
- **Provider:** DeepSeek Direct API
- **Use for:** chat responses, file operations, memory queries, tool calls,
  planning, document writing, the great majority of Trevor's day-to-day
- **Cost tier:** Low

### Fallback Chain (resilience, not preference)
Triggered only on 429 / 5xx / timeout / provider-unavailable from primary:

1. Retry primary once with exponential backoff + jitter
2. `deepseek/deepseek-chat` (131K context, simpler)
3. `deepseek/deepseek-v4-pro` (1M context, higher quality, higher cost)
4. `myclaw/minimax-m2.7` (free, last-resort continuity)

---

## Routing Tiers Summary

| Tier  | Model                         | Provider          | When to use                          |
|-------|-------------------------------|-------------------|--------------------------------------|
| 1     | `anthropic/claude-opus-4.7`  | OpenRouter        | Strategic analysis (exec summary, red-team) |
| 2     | `deepseek/deepseek-v4-flash` | DeepSeek Direct   | Regional data synthesis (6 regions)  |
| 3     | `deepseek/deepseek-v4-flash` | DeepSeek Direct   | All chat, tools, memory, planning    |
| R     | fallback chain                | DeepSeek/MyClaw  | API failure on primary               |

---

## Multimodal Routing

### Diagrams (preferred over images)
- Default: Mermaid (`skills/mermaid`) or hand-rolled SVG / HTML / CSS
- Reasons: cheaper, deterministic, editable, render in chat

### OpenRouter Policy
- OpenRouter plugin is **enabled** for:
  - **Tier-1 strategic analysis** — `anthropic/claude-opus-4.7` via OpenRouter
  - Image generation (diffusion, Gemini image models)
  - Video generation (Veo, etc.)
  - Text-to-speech
  - Any model not available via DeepSeek Direct or MyClaw
- **Never** route DeepSeek models through OpenRouter — use DeepSeek Direct API.
- **Never** use OpenRouter for Tier-2 or Tier-3 tasks.
- Monitored by `scripts/openrouter_monitor.py` on heartbeat cycle.

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

## Model Availability

| Model                      | Provider          | Context | Cost Tier   | Tier  |
|----------------------------|-------------------|---------|-------------|-------|
| deepseek-v4-flash          | DeepSeek Direct   | 1M      | Low         | 2, 3  |
| deepseek-chat              | DeepSeek Direct   | 131K    | Low         | R     |
| deepseek-v4-pro            | DeepSeek Direct   | 1M      | Medium-High | R     |
| anthropic/claude-opus-4.7  | OpenRouter        | 200K    | High        | 1     |
| myclaw/minimax-m2.7        | MyClaw            | 204K    | Free        | R     |
| myclaw/kimi-k2.5           | MyClaw            | 200K    | Free        | R     |

---

## Vocabulary Discipline (TREVOR brand voice)

**Use:** methodology, disclosure, candor, completeness, confidence,
responsiveness, diligence, briefing, finding, assessment, indicator,
posture.

**Avoid:** solution, unlock, empower, revolutionary, disrupt,
cutting-edge, game-changing, best-in-class, synergy, leverage.

---

## Scope Gate — Three-Branch Flow (since 2026-05-17)

`analyst/scope_check.py` is the FIRST call in every analyst entry
point (chat handler, analyze.py, orchestrate.py, any ad-hoc brief
script). It classifies the incoming request into three branches,
each with a distinct output path:

```
request → scope_check.py
           │
           ├── in_scope
           │   → Full thematic analyst prompt. No reframe needed.
           │   → Standard pipeline (analyze.py with deepseek-prompts.md)
           │   → Produces thematic Mexico brief.
           │
           ├── adjacent
           │   → Adjacency-brief prompt loaded from
           │     analyst/templates/adjacent_brief.md.
           │   → System prompt injected with adjacency preamble
           │     (build_adjacency_preamble from scope_check.py).
           │   → Frame ENTIRE brief through Mexico transmission
           │     vectors. NOT a generic global brief with MX appended.
           │   → Output: BLUF + 3-5 vector sections (development →
           │     mechanism → magnitude/timing → subscriber action) +
           │     calibration band + watch items.
           │
           └── out_of_scope
               → Decline template. No analyst model is called.
               → Verbatim shape:
                 "Open Claw Mexico is scoped to {scope_descriptor}.
                  '{topic}' is out of scope and has no substantive
                  transmission mechanism to Mexico.
                  If you have a specific Mexico question I should be
                  answering, ask that instead."
```

### Classification logic

- **Fast path:** keyword matching against `scope.yaml` blocklist and
  allowlist. Zero API cost. Catches unambiguous in_scope (Mexico
  keywords) and out_of_scope (Russia-Ukraine, K-pop, etc.)
- **Slow path:** cheap LLM call (deepseek-chat, ~$0.00015/query) for
  ambiguous requests. The classifier prompt includes explicit examples
  of all three statuses and a hard adjacency-default rule.
- **Permissive default:** on LLM API failure, defaults to `in_scope`.
  Better to produce than to miss.

### Adjacency default rule (in classifier)

> Adjacency is the DEFAULT for any topic with a credible transmission
> mechanism to Mexico (energy, currency, trade, capital flows, migration,
> supply chains). Out-of-scope is reserved for topics where no credible
> mechanism exists. When in doubt, prefer adjacent over out_of_scope —
> the adjacency branch produces value; refusal trains subscribers to stop
> asking.

### Adjacent brief template (`analyst/templates/adjacent_brief.md`)

Every adjacent brief follows this structure in order:

1. **BLUF** — one sentence on what the topic means for Mexico-exposed
   subscribers.
2. **Vector sections (3-5)** — each section is one transmission vector:
   - **Development:** what happened globally (1-2 sentences)
   - **Mechanism to Mexico:** how this reaches Mexican assets/institutions
   - **Magnitude / Timing:** how big, how fast. Quantify where possible.
   - **Subscriber action line:** what to do with the information.
3. **Calibration** — Sherman Kent band on the directional thesis.
4. **Watch items** — 3-5 forward-looking indicators with triggers and
   signals.

### Scope discipline — no keyword-extension on edge cases

When a probe surfaces an unexpected classification, the right question
is "why did check_scope get this wrong, and what does the classifier
prompt or example set need?" — NOT "what keyword can I add to make
this go away?" Auto-extending the keyword list is rule-fitting; it
makes the gate more brittle as edge cases accumulate. The classifier-
improvement path compounds learning; the keyword-extension path
compounds tech debt. This applies to all future scope edge cases.
If tempted to add a keyword, audit the classifier examples first.

### Framework generalization

Scope spec lives in `analyst/config/scope.yaml`. When redirecting
this framework to a new topic, edit that file: primary_scope,
themes, adjacency_vectors, keyword lists. The scope_check.py module
and the three-branch flow are framework-general and require no changes.
To generalize the adjacency template, replace its Mexico references
with the new scope's transmission vectors.

## Mexico Desk Routing (since 2026-05-17)

Per `analyst/directives/2026-05-mexico-pivot.md`, the six legacy regions
are replaced by six Mexico themes. Tier-2 regional synthesis maps
one-to-one onto themes:

| Tier-2 lane         | Theme                                                          |
|---------------------|----------------------------------------------------------------|
| cartel_security     | cartels, OC factional dynamics, KFR, extortion, fentanyl flows |
| political_risk      | Sheinbaum admin, judicial reform, Morena internals, governors  |
| us_mexico           | tariffs, USMCA review, border, FTO/SDN, migration              |
| energy_infra        | Pemex, CFE, refineries, huachicoleo, data centers, water       |
| economy_markets     | peso, FDI, nearshoring, remittances, Kalshi/Polymarket MX      |
| worldcup_travel     | 2026 venue security, tourist exposure, transit, civil unrest   |

Spanish-language ingest is mandatory, not optional. `scripts/mexico-daily-scan.py`
runs in the cron pre-collection step; results merge into `raw/incidents.json`
via `scripts/merge_mexico_into_incidents.py`. Tier-3 handles translation
prompts to keep cost low.

**Calibration feedback loop (closed 2026-05-17):**
`scripts/compile_calibration_directives.py` runs daily from
`brain/memory/semantic/calibration-tracking.json` and writes per-band /
per-theme directives into `behavioral-state.json` for next day's
`analyze.py` system-prompt injection.

## Change Log

- **3.4 (2026-05-17):** Scope gate added — `analyst/scope_check.py` is the
  first call in every analyst entry point. Three-branch flow (in_scope /
  adjacent / out_of_scope). Scope config at `analyst/config/scope.yaml`.
  Deepseek-prompts.md system prompt updated with scope discipline.
  IDENTITY.md and SOUL.md updated to reflect Mexico-only scope.
- **3.3 (2026-05-17):** Mexico-primary desk routing. Themes replace regions.
  Spanish-language ingest wired into the daily pipeline. Calibration
  compiler closes the postdiction → behavioral-state feedback loop.
  Skill-generator skill added (`skills/skill-generator/`) for autonomous
  capability-gap remediation. Weekly meta-review job (`scripts/weekly_meta_review.py`)
  picks next week's learning focus from gap logs.
- **3.2 (2026-05-12):** Adopted tiered architecture (Tier-1 Opus 4.7 /
  Tier-2/3 DeepSeek V4 Flash). Replaced "Primary/Escalation" model with
  explicit tier names and use-case descriptions. OpenRouter policy
  updated: Tier-1 strategic analysis is now explicitly in-scope.
  Routing scanner updated with accurate policy constants.
  DeepSeek models are never routed through OpenRouter.
- **3.1 (2026-05-10):** Added Pipeline tier for daily intel brief analysis.
  Writing routed through `anthropic/claude-opus-4.7` via OpenRouter.
  Updated `orchestrate.py` and `daily-brief-cron.sh` accordingly.
- **3.0 (2026-05-01):** Reconciled four conflicting routing documents into
  one source of truth. Canonical provider is DeepSeek Direct API.
  REBUILD_ORCHESTRATION.md archived under `docs/archive/`.
- **2.0 (2026-04-28):** Switched primary to DeepSeek V4 Flash.
- **1.0 (2026-04-25):** Initial balanced MyClaw default order.

---

*Trevor is a routing system, not a single model. The point of this
framework is to keep that routing legible — to Trevor and to Roderick.*
