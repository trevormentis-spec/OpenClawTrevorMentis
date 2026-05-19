# Changelog

## v2.0.0 — Domain-General Autonomous Intelligence Analyst

**Date:** 2026-05-19
**Branch:** trevor-v2
**Tag:** v2.0.0-rc1

### Summary

Complete rebuild of Trevor from a Mexico-specific MyClaw intelligence analyst into a domain-general autonomous analyst agent. Given any topic, Trevor onboards it, builds a source inventory, applies rigorous analyst methodology, and produces calibrated intelligence products.

### Breaking Changes

- **Routing model changed:** All model calls now route through `analyst/llm_gate.py` instead of using the MyClaw default model. The interactive-vs-pipeline routing contradiction is resolved.
- **Scope is topic-flexible:** `scope_check.py` reads from `config/topics/<active-topic>/topic.yaml` instead of hardcoded Mexico scope. Legacy `analyst/config/scope.yaml` is a fallback.
- **AGENTS.md is analyst-focused:** Consumer assistant scaffolding (emoji reactions, group chat behavior, heartbeat for weather/Twitter, voice storytelling) is removed. Replaced with analyst rotation checks, autonomy boundaries, data preflight rules.
- **Identity files rewritten:** SOUL.md and IDENTITY.md reflect domain-general analyst identity, not consumer assistant.

### New Features

- **LLM Gating (Phase 2):** 26 task types with explicit routing rules, escalation/downgrade triggers, budget tolerance, fallback chains. Cost ledger with daily/monthly caps and hard halt enforcement.
- **Multi-Provider Routing:** OpenRouter (Opus 4.7, Sonnet 4.5, Vision, nanobanana, Whisper), DeepSeek Direct (V4 Pro, V4 Flash), ElevenLabs (TTS).
- **Topic Onboarding (Phase 3):** `analyst/topic_onboarding.py` creates full config directory for any topic (themes, sources, entities, calibration, branding, routing overrides).
- **Self-Improvement (Phase 4):** Skill discovery (ClawHub scanning, 3/week rate limit), forum monitoring (read-only, 1/week synthesis), capability gap tracking (4 categories), custom skill writer (1/week, principal approval gate).
- **Communication Stack (Phase 5):** Slide renderer interface (PPTX, deferred), image renderer (nanobanana via OpenRouter). Existing PDF and audio renderers preserved.
- **Portability (Phase 6):** Bootstrap script, health check, backup/restore, .env.example, deployment guide.

### Preserved from v1

- Sherman Kent calibration (8-band)
- NATO Admiralty source rating
- Three structural guards (scope_check, fabrication_check, themes_preflight)
- Brain runtime (TF-IDF, episodic/semantic/procedural)
- Worker/planner harness
- Guard pipeline orchestrator
- Multi-turn generator
- PDF renderer (weasyprint)
- Audio renderer (ElevenLabs)
- AgentMail integration
- Cost tracking discipline
- Playbooks and templates

### Archived

- Mexico-specific knowledge base (15 actors, 5 regions, chronologies, frameworks) moved to `docs/archive/mexico-v1/`
- Mexico-specific collectors (6 files), scripts (7 files), config (4 files) archived
- Phase 1-2 implementation directives archived
- Historical audit reports archived

### Migration Notes

- Mexico data is preserved in `docs/archive/mexico-v1/` and can be re-onboarded via `topic_onboarding.py`
- Existing calibration data structure is compatible — calibration.json in topic configs uses the same 8-band schema
- Brain state carries forward unchanged
- `.env` must be configured with provider API keys (see `deployment/.env.example`)

### Security Notes

- 3 API keys found exposed in git history (NewsAPI, GenViral, Kalshi) — removed from working tree, flagged for principal rotation
- Git history scrub via git-filter-repo planned — requires principal to run after key rotation
- All new secrets externalized via `.env` (gitignored)
