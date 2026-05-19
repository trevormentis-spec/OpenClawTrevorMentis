# Gate Bypass Audit — Full Codebase Inventory

## Methodology

Searched for:
- Direct API endpoint calls (openrouter.ai, api.deepseek.com, api.elevenlabs.io)
- Hardcoded model strings used as args to API calls
- Direct HTTP client calls to model provider endpoints
- Legacy `analyst.routing` references
- Model client imports outside `analyst/llm_clients/`

Classification: **A** = gate-internal, **C** = unauthorized bypass.

---

## Category A — Legitimate (gate-internal or non-model API)

| File | Endpoint | Reason |
|---|---|---|
| `analyst/llm_clients/deepseek_client.py` | api.deepseek.com | Gate-internal model client |
| `analyst/llm_clients/openrouter_client.py` | openrouter.ai | Gate-internal model client |
| `analyst/llm_clients/elevenlabs_client.py` | api.elevenlabs.io | Gate-internal model client |
| `analyst/polymarket_monitor.py` | (non-model URL) | Prediction market data, not a model call |
| `analyst/polymarket_geopolitics_monitor.py` | (non-model URL) | Prediction market data |
| `analyst/agentmail_health.py` | (non-model URL) | Email health check |
| `scripts/*` — Kalshi, Polymarket, Gmail, NewsAPI, AgentMail, Buttondown, Mapbox, social, network feeds, etc. | (non-model URLs) | Data collection / delivery APIs, not model calls |

---

## Category C — Unauthorized Bypasses (needs fix)

### C1. Core Pipeline Scripts

| # | File | Lines | What it calls | Fix |
|---|---|---|---|---|
| 1 | `scripts/generate_intel_analysis.py` | 32, 42 | DeepSeek `chat/completions`, hardcoded `deepseek-chat` | Route through `llm_gate.route()` before calling |
| 2 | `scripts/postdict.py` | 58, 70, 87, 92 | OpenRouter + DeepSeek, hardcoded `anthropic/claude-opus-4.7` + `deepseek/deepseek-v4-flash` | Route through gate per task type |
| 3 | `scripts/trade_engine.py` | 30, 67-80 | OpenRouter, hardcoded `anthropic/claude-opus-4.7` MODEL | Route through `subscriber_brief` task |
| 4 | `scripts/priority_triage.py` | 59, 63, 221-232, 535-578 | OpenRouter + DeepSeek, hardcoded `TIER1_MODEL` + `TIER2_MODEL` | Route through gate with task-appropriate type |
| 5 | `skills/daily-intel-brief/scripts/analyze.py` | 101-111 | OpenRouter + DeepSeek base URLs | Route through gate (this is the daily brief collector) |

### C2. Utility / Translation Scripts

| # | File | Lines | What it calls | Fix |
|---|---|---|---|---|
| 6 | `scripts/translate_es_to_en.py` | 34-80 | DeepSeek `chat/completions`, hardcoded `deepseek-chat` | Route through `translation` task type (or add task type) |
| 7 | `scripts/mexico_morning_brief.py` | 124-137 | DeepSeek via urllib for headline translation | Route through `translation` task |
| 8 | `scripts/render_audio.py` | 34, 123-141 | ElevenLabs TTS + DeepSeek for script generation | Route TTS through gate `audio_generation` task, DeepSeek through `script_writing` |

### C3. Analysis / Quality Scripts

| # | File | Lines | What it calls | Fix |
|---|---|---|---|---|
| 9 | `scripts/benchmark_compare.py` | 57 | OpenRouter (for comparison scoring) | Route through `benchmark` task |
| 10 | `scripts/query_map_designs.py` | 23-89 | OpenRouter, hardcoded `anthropic/claude-opus-4.7` | Route through `design_generation` task |
| 11 | `scripts/deepseek_har_analyzer.py` | 23-80 | DeepSeek + OpenRouter, hardcoded `deepseek-chat` | Route through `har_analysis` task |
| 12 | `analyst/scope_check.py` | 219, 235 | DeepSeek `chat/completions` for LLM scope classification | Route through `scope_classification` task |
| 13 | `skills/visual_production/visual_production/pipeline.py` | 251 | OpenRouter | Route through `visual_pipeline` task |

### C4. Already Fixed This Session

| # | File | Lines | What it was | Fix applied |
|---|---|---|---|---|
| 14 | `analyst/multi_turn_generator.py` | 163-174 | Legacy `analyst.routing` import + OpenRouter/DeepSeek direct calls | Replaced with `llm_gate.route()` + `_log_routing()` |
| 15 | `scripts/produce_brief.py` | 39-63 | Direct OpenRouter/DeepSeek calls with hardcoded model | Follows gate pattern (written as fix) |

---

## Summary

| Category | Count |
|---|---|
| A — Legitimate (gate-internal) | 3 files (llm_clients/) |
| C — Unauthorized bypass (needs fix) | **13 files** |
| Already fixed this session | 2 files |
| Non-model URLs (not bypasses) | ~30+ files |

**13 unauthorized bypasses across the codebase.** The most impactful: `analyze.py` (daily Intel pipeline), `postdict.py` (calibration tracking), `priority_triage.py` (triage engine), `scope_check.py` (LLM scope gate — ironic).

---

## Proposed Fix Priority

1. **High:** `analyze.py` (daily intel pipeline — runs every session), `postdict.py` (calibration — runs daily)
2. **Medium:** `priority_triage.py`, `trade_engine.py`, `benchmark_compare.py`
3. **Low:** `translate_es_to_en.py`, `mexico_morning_brief.py`, `render_audio.py`, `deepseek_har_analyzer.py`, `query_map_designs.py`, `scope_check.py` (its own gate function), `visual_production/pipeline.py`

---

*Produced: 2026-05-19 23:05 UTC*
*Open Claw — Trevor v2 Routing Audit*
