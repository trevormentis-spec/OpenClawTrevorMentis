# Trevor v2 Performance Baseline

**Generated:** 2026-05-19
**Branch:** trevor-v2

## Cost Projections (from llm_gate routing)

### Daily Brief (typical)
- Task type: `daily_ingestion`
- Default model: deepseek/deepseek-v4-flash
- Target words: 500-1000
- Estimated cost per brief: $0.05-0.15
- **Target range: $0.50-2.00/day** (10-15 ingestion calls + triage)

### Flagship Document (typical)
- Task type: `flagship_document`
- Default model: anthropic/claude-opus-4.7
- Target words: 3000-5000
- Estimated cost: $2.00-5.00 (Opus generation)
- Multi-section approach: Sonnet per section + Opus coherence pass
- **Target range: $5-15 per document**

### Standard Subscriber Brief
- Task type: `subscriber_brief`
- Default model: deepseek/deepseek-v4-pro
- Target words: 1000-2500
- Estimated cost: $0.10-0.50
- **Target range: $0.50-2.00 per brief**

## Budget Configuration

| Parameter | Value |
|-----------|-------|
| Daily cap | $20.00 |
| Monthly cap | $200.00 |
| Alert threshold | 80% |

## Test Suite Results

| Suite | Tests | Status |
|-------|-------|--------|
| LLM Gate Routing | 17 groups | ALL PASS |
| Topic Onboarding & Scope | 9 groups | ALL PASS |
| Self-Improvement | 11 groups | ALL PASS |
| **Total** | **37 groups** | **ALL PASS** |

## Health Check Results

| Category | Pass | Fail | Warn |
|----------|------|------|------|
| Environment | 1 | 1* | 0 |
| Core Components | 7 | 0 | 0 |
| Configuration | 4 | 0 | 0 |
| Brain Runtime | 2 | 0 | 0 |
| Renderers | 2 | 0 | 1** |
| Test Suite | 3 | 0 | 0 |
| Identity | 5 | 0 | 0 |

*`.env` not present on dev machine (expected — deploy with real keys)
**weasyprint not installed on dev machine (install for PDF rendering)

## Architecture Metrics

| Component | Files | Lines (approx) |
|-----------|-------|-----------------|
| LLM Gate + Cost Ledger | 2 | ~750 |
| Provider Clients | 3 | ~350 |
| Topic Onboarding | 1 | ~300 |
| Scope Check (generalized) | 1 | ~250 |
| Self-Improvement (4 modules) | 4 | ~600 |
| Tests | 3 | ~900 |
| Deployment Scripts | 4 | ~400 |
| Config Files | 5 | ~150 |

## Topic Onboarding Validation

3 test topics onboarded successfully:
1. **Semiconductor Supply Chain** — 4 themes, 2 sources, 3 entities
2. **Brazil Fiscal Policy** — 3 themes, 1 source, 2 entities
3. **Company XYZ Deep Dive** — 2 themes, 0 sources, 0 entities

Each generates 7 config files in config/topics/<slug>/.

## Routing Decision Coverage

26 task types with explicit routing rules:
- Frontier (Opus 4.7): 8 task types
- Cost-effective frontier (Sonnet 4.5): 2 task types
- Mid-tier (V4 Pro): 6 task types
- High-volume (V4 Flash): 7 task types
- Specialist (Vision, nanobanana, Whisper, ElevenLabs): 4 task types

Escalation/downgrade triggers verified for all applicable types.
