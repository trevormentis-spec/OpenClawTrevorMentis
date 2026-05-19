# MIGRATION.md — Trevor v1 → v2 Rebuild

**Created:** 2026-05-19
**Branch:** `trevor-v2`
**Archive tag:** `trevor-v1-mexico`

---

## Current State

Mexico-specific MyClaw intelligence analyst instance. Consumer assistant scaffolding (group chat behavior, emoji reactions, heartbeat for weather/Twitter, voice storytelling) mixed with production analyst machinery (Sherman Kent calibration, NATO Admiralty, guard pipeline, multi-turn generation, cost tracking).

## Target State

Domain-general autonomous intelligence analyst agent. Given ANY topic, Trevor onboards it, builds source inventory, applies rigorous analyst methodology, produces calibrated intelligence products. Multi-model routing via llm_gate. Self-improving via skill discovery, forum monitoring, capability gap tracking.

## What's Preserved

- Sherman Kent calibration discipline
- NATO Admiralty source rating
- Three structural guards (scope_check, fabrication_check, themes_preflight) — generalized
- Brain runtime (TF-IDF, episodic/semantic/procedural)
- Worker/planner harness (analyst/worker.py, analyst/planner.py)
- Guard pipeline orchestrator (analyst/guard_pipeline.py)
- Routing logic base (analyst/routing.py) — expanded into llm_gate
- Multi-turn generator (analyst/multi_turn_generator.py)
- PDF renderer (scripts/render_pdf.py)
- Audio renderer (scripts/render_audio.py)
- AgentMail integration
- Cost tracking discipline
- Vocabulary discipline
- Playbooks and templates (analyst/playbooks/, analyst/templates/)

## What's Replaced

- SOUL.md — consumer assistant → analyst identity
- IDENTITY.md — Mexico desk → domain-general analyst
- AGENTS.md — consumer assistant scaffolding → analyst-focused operational rules
- ORCHESTRATION.md — interactive-vs-pipeline contradiction resolved, everything through llm_gate
- Mexico-specific scope → topic-flexible scope via config/topics/
- Mexico-specific themes → topic-flexible themes
- Mexico-specific source registry → topic-flexible source library
- Single-tier interactive routing → llm_gate multi-provider routing
- HEARTBEAT.md — weather/Twitter → analyst rotation (assignments, sources, postdiction, gaps, calibration)
- Hardcoded model selection → explicit gating with logged decisions

---

## Exposed Secrets Audit

### CONFIRMED EXPOSED — Require Principal Rotation

| Provider | Key Value | Files in Working Tree | Commits |
|----------|-----------|----------------------|---------|
| **NewsAPI** | `560850e45ebe4f79987a7a0961d3e275` | `analyst/polymarket_geopolitics_monitor.py:29`, `scripts/discover_sources.py:90`, `TOOLS.md:68` | Multiple commits — hardcoded as default fallback |
| **GenViral** | `gva_live_85f455afed.f31634f6c58668fb8414deb55eb526cbbabbbc7506feffc2` | `TOOLS.md:146` | Committed in TOOLS.md |
| **Kalshi** | `8733a0f8-22a6-4478-87b1-3a4b32dfb583` | `TOOLS.md:60` | Committed in TOOLS.md |

### NOT FOUND (referenced by env var only, properly handled)

- DeepSeek API key — loaded from .env via `os.environ.get("DEEPSEEK_API_KEY")`
- AgentMail API key — loaded from .env
- ElevenLabs API key — loaded from .env
- Kalshi API key — loaded from .env (no actual value found in history)
- Buttondown API key — referenced but no actual value committed

### REMEDIATION PLAN

1. **Immediate (Phase 0):** Remove hardcoded values from working tree files
2. **Phase 6:** git-filter-repo or BFG to scrub values from history
3. **Principal action required:** ROTATE NewsAPI key and GenViral key (both exposed in public repo history)
4. **.gitignore:** Already covers `.env` — verified adequate

---

## File Audit

### analyst/ Directory

#### KEEP_AS_IS (Production-ready, domain-general)
| File | Purpose |
|------|---------|
| `__init__.py` | Package marker |
| `escalation_guard.py` | Pre/mid/post-generation token estimation and truncation detection |
| `fabrication_check.py` | Post-generation quality gate for unverified claims |
| `guard_pipeline.py` | Unified guard orchestrator (fabrication → themes → escalation) |
| `multi_turn_generator.py` | Section-by-section brief generation with context stacking |
| `polymarket_geopolitics_monitor.py` | Polymarket trading playbook (4 modules) |
| `polymarket_monitor.py` | Polymarket price tracking and movement detection |
| `routing.py` | Complexity-based model routing (Opus/V4Pro/Flash) |
| `worker.py` | Task executor with budget validation and dry-run mode |
| `agentmail_health.py` | AgentMail inbox health monitoring |
| `playbooks/*` | 5 domain-general analytical playbooks |
| `templates/*` | 8 domain-general brief templates + PDF template |

#### KEEP_REFACTOR (Good logic, needs generalization)
| File | Change Needed |
|------|---------------|
| `planner.py` | Extract Mexico incident sources/keywords to config |
| `scope_check.py` | Already reads config — verify topic-flexible loading |
| `themes_preflight.py` | Extract Mexico theme signatures to per-topic YAML |
| `status_generator.py` | Extract hardcoded directives/patterns to config |
| `tasks/entity_deepening.py` | Extract hardcoded ACTORS_DIR to config |
| `tasks/cross_source_correlation.py` | Mexico incident filtering → config-driven |
| `tasks/framework_stress_test.py` | Mexico incidents → topic-specific incidents |
| `tasks/source_freshness_scan.py` | Mexico source registry → topic-specific registry |
| `tasks/source_quality_audit.py` | Mexico registry → topic-specific |
| `meta/*` | State files — clean/rotate for new topics |

#### REPLACE (Mexico-specific, needs rewrite)
| File | Reason |
|------|--------|
| `tasks/self_question_generation.py` | Mexico-specific question prompts |
| `tasks/targeted_source_discovery.py` | Mexico-specific search queries |
| `tasks/weekly_source_brainstorm.py` | Mexico-specific brainstorm prompts |

#### ARCHIVE (Move to docs/archive/mexico-v1/)
| File | Reason |
|------|--------|
| `knowledge/mexico/actors/*` (15 files) | Mexico entity profiles |
| `knowledge/mexico/geography/*` (5 files) | Mexico regional profiles |
| `knowledge/mexico/chronologies/*` | USMCA 2026 timeline |
| `knowledge/mexico/frameworks/*` | Cartel dynamics, huachicoleo |
| `audits/*` (4 files) | Historical capability reports |
| `directives/*` (11 files) | Phase 1-2 implementation directives |
| `angles/mexico/*` | Mexico creative angle brainstorms |
| `config/pronunciation_dictionary.yaml` | Mexico pronunciation guide |

#### DELETE (Transient)
| File | Reason |
|------|--------|
| `queue/*` (7 JSON files) | Transient task queue, regenerated by planner |
| `price-scan-result.json` | Legacy scan output |

### collectors/ Directory

#### ARCHIVE (All Mexico-specific)
| File | Purpose |
|------|---------|
| `amis_collector.py` | Mexican insurance association stats |
| `cenace_collector.py` | Mexico grid load data |
| `compranet_collector.py` | Mexico public procurement |
| `dof_collector.py` | Mexico official journal |
| `dof_monitor.py` | Mexico official journal (simplified) |
| `military_procurement_collector.py` | Mexico military procurement |

#### KEEP_REFACTOR (Generalizable patterns)
| File | Generalization |
|------|----------------|
| `maritime_ais_collector.py` | Configurable port list + flag patterns |
| `property_records_collector.py` | Configurable registry URLs + state config |
| `real_estate_collector.py` | Configurable platform patterns |
| `telegram_monitor.py` | Configurable channel list + classification |

### scripts/ Directory

#### KEEP_AS_IS (69 files — core pipeline infrastructure)
Key files: `build_agent_brief.py`, `collection_campaign.py`, `collection_state.py`, `behavioral_state.py`, `autonomy_tracker.py`, `continuous_monitor.py`, `source_discovery.py`, `daily_briefings_cron.py`, `render_pdf.py`, `render_audio.py`, `render_brief_magazine.py`, `kalshi_scanner.py`, `meta_cognition.py`, `self_assessment.py`, `skill_audit_runner.py`, `cost_tracker.py`, `deliver_brief_email.py`, and others.

#### ARCHIVE (Mexico-specific products)
| File | Purpose |
|------|---------|
| `mexico_morning_brief.py` | Mexico daily HTML dashboard |
| `mexico-daily-scan.py` | Mexico news scanning |
| `mexico-markets.py` | Mexico market data |
| `build_flagship_pdf.py` | Mexico flagship PDF |
| `build_opportunity_pdf.py` | Mexico opportunity analysis |
| `build_usmca_assets.py` | USMCA-specific assets |
| `merge_mexico_into_incidents.py` | Mexico incident merge |

#### KEEP_REFACTOR (18 files)
Key files: `generate_brief_maps_v2.py`, `generate_brief_maps_v3.py`, `generate_intel_analysis.py`, `geo_trader.py`, `translate_es_to_en.py`, `genviral_stats.py`, `genviral_extract.py`, `postdict.py`, `product_suggestions.py`, `trade_engine.py`.

### skills/ Directory — Skill Audit

#### ANALYST_ACTIVE (36 skills — keep active in analyst workflow)
Core: `sat-toolkit`, `source-evaluation`, `indicators-and-warnings`, `bluf-report`, `daily-intel-brief`, `collection`, `scraper`, `akashic-doc-analyzer`, `social-intelligence`, `threat-intel-aggregator`, `geopolitics-expert`, `geospatial-osint`, `graph-analysis`, `recursive-knowledge-miner`, `chartgen-ai`, `mermaid`, `pdf-report`, `baoyu-translate`, `quick-translation`, `universal-translate`, `spanish-pdf-ocr`, `agentmail`, `skill-generator`, `visual_production`, `news`, `data-analysis`, `oraclaw-graph`, `corpusgraph`, `renderers`, `mapbox-geospatial-operations`, `mapbox-data-visualization-patterns`, `ldap7`, `genviral`.

#### CONSUMER_DISABLE (16 skills — keep installed, disable from analyst workflow)
`content-generation`, `content-marketing`, `cross-poster`, `landing-page-generator`, `landing-page-roast`, `newsletter`, `newsletter-creation-curation`, `polymarket-trader`, `skill-stripe-monitor`, `social-media-agent`, `social-media-scheduler`, `social-pack`, `social-post`, `social-poster`, `data-charts-visualization`, `data-visualization-studio`.

### Root Files

| File | Classification | Action |
|------|---------------|--------|
| `SOUL.md` | REPLACE | New analyst identity (verbatim from spec) |
| `IDENTITY.md` | REPLACE | New domain-general identity |
| `AGENTS.md` | REPLACE | Analyst-focused operational rules |
| `USER.md` | KEEP_AS_IS | Principal info preserved |
| `MEMORY.md` | KEEP_REFACTOR | Update for v2 context |
| `ORCHESTRATION.md` | REPLACE | Rewrite for llm_gate routing |
| `HEARTBEAT.md` | REPLACE | Analyst rotation checks |
| `TOOLS.md` | KEEP_REFACTOR | Remove hardcoded secrets |
| `STATUS.md` | KEEP_REFACTOR | Add Trevor v2 Rebuild section |
| `README.md` | REPLACE | Update for v2 |
| `brain/` | KEEP_AS_IS | Brain runtime preserved |
| `data/` | KEEP_AS_IS | Collection records preserved |
| `exports/` | KEEP_AS_IS | Output directory preserved |
| `memory/` | KEEP_AS_IS | Working memory preserved |

---

## Phase Plan Summary

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Branch, secrets audit, file audit | IN_PROGRESS |
| 1 | Identity rewrite (SOUL, IDENTITY, AGENTS) | PENDING |
| 2 | LLM gating infrastructure | PENDING |
| 3 | Domain-general framework | PENDING |
| 4 | Self-improvement mechanisms | PENDING |
| 5 | Communication stack | PENDING |
| 6 | Portability and secrets scrub | PENDING |
| 7 | Migration and testing | PENDING |
| 8 | PR open and deployment docs | PENDING |
