# ORCHESTRATION.md — Trevor v2 Routing Framework

**Version:** 4.0
**Date:** 2026-05-19
**Status:** Active — single source of truth for routing

> This is the canonical routing document. If anything in `AGENTS.md`,
> `MEMORY.md`, or any other file disagrees with this file, this file wins.
> Update this file first, then propagate.

---

## Core Principle: Everything Routes Through llm_gate

All model calls — interactive, pipeline, scheduled, ad-hoc — route through
`analyst/llm_gate.py`. There is no separate "interactive session uses default
model" rule. The gating system selects the model based on task type, complexity
signals, and budget constraints.

```
Task → route(task_type, metadata) → GatingDecision → provider client → model
                                         ↓
                                  cost_ledger.record()
                                  routing-log.jsonl
```

---

## Model Tiers

### Tier-1 — Frontier (OpenRouter)
**Model:** `anthropic/claude-opus-4.7`
**Cost:** ~$5/M input, ~$25/M output
**Use for:**
- Flagship subscriber-facing documents (>3000 words, multi-section)
- Multi-scenario analysis with explicit probability calibration
- Final calibration application on high-stakes judgments
- Cross-domain creative synthesis (weekly source brainstorm)
- Adversarial red-team analysis
- Framework refinement proposals
- Principal handback memos
- Topic onboarding strategic phase
- Skill discovery and forum synthesis

### Tier-1.5 — Cost-Effective Frontier (OpenRouter)
**Model:** `anthropic/claude-sonnet-4.5`
**Cost:** ~$3/M input, ~$15/M output
**Use for:**
- Complex briefs 2000-4000 words where Opus is overkill
- Multi-turn flagship generation per-section
- Postdiction analysis with calibration feedback

### Tier-2 — Mid-Tier (DeepSeek Direct API)
**Model:** `deepseek/deepseek-v4-pro`
**Cost:** ~$0.40/M input, ~$1.60/M output
**Use for:**
- Standard analytical briefs 1000-2500 words
- Entity deepening on critical entities
- Cross-source correlation
- Source quality auditing
- Framework stress-testing
- Topic onboarding tactical phase
- Capability gap review

### Tier-3 — High-Volume (DeepSeek Direct API)
**Model:** `deepseek/deepseek-v4-flash`
**Cost:** ~$0.14/M input, ~$0.28/M output
**Use for:**
- Daily intel ingestion and triage
- Source classification
- Newsletter parsing
- Translation tasks
- Routine entity work
- Status report generation
- Scope classifier slow-path
- Topic onboarding operational phase

### Specialist Models
- **Claude Vision** (OpenRouter): Chart/diagram extraction, map analysis, document layout
- **nanobanana** (OpenRouter): Custom charts, branded illustrations, diagram generation
- **Whisper** (OpenRouter): Audio transcription
- **ElevenLabs**: Audio companion generation (TTS with consistent voice)

---

## Routing Decision Flow

1. Caller specifies `task_type` and `metadata` (target_words, scenarios, flags)
2. `llm_gate.route()` checks task rules:
   - Start at default model for task type
   - Check escalation triggers (any match → upgrade)
   - Check downgrade triggers (all match → downgrade)
   - Apply budget tolerance adjustment
3. Decision logged to `memory/llm-routing-log.jsonl`
4. Cost recorded to `memory/cost-ledger.jsonl` via `cost_ledger.py`
5. Budget checked against `config/budget.yaml` caps

---

## Budget Enforcement

- **Daily cap:** $20.00 (configurable in config/budget.yaml)
- **Monthly cap:** $200.00
- **Alert threshold:** 80% of cap
- **Hard halt:** operation stops when cap exceeded, principal notified
- **Projection:** before each call, check `cost_ledger.projection(estimated_cost)`

---

## Fallback Chains

- **OpenRouter failure:** Sonnet 4.5 → V4 Pro → V4 Flash
- **DeepSeek failure:** V4 Flash → Sonnet 4.5
- **ElevenLabs failure:** no fallback (surface error)

---

## Scope Gate (unchanged from v1)

Three-branch flow on every analytical query:
1. **in_scope** → proceed with analysis
2. **adjacent** → reframe to current topic, offer alternative
3. **out_of_scope** → decline with valuable redirect

Implementation: `analyst/scope_check.py` reads from `config/topics/<active-topic>/topic.yaml`.

---

## Quality Gates

Post-generation validation pipeline (`analyst/guard_pipeline.py`):
1. `fabrication_check.py` — no unverified prices, tickers, percentages
2. `themes_preflight.py` — required themes covered for topic
3. `escalation_guard.py` — token estimation, truncation detection

Gates are specified per task type in `llm_gate.py TASK_RULES`.

---

## Configuration Files

| File | Purpose |
|------|---------|
| `config/llm-routing.yaml` | Provider URLs, model lists, tier descriptions |
| `config/budget.yaml` | Daily/monthly caps, alert thresholds |
| `analyst/llm_gate.py` | Task-to-model rules (code, authoritative) |
| `analyst/cost_ledger.py` | Budget tracking and enforcement |
| `analyst/llm_clients/` | Provider-specific API clients |
