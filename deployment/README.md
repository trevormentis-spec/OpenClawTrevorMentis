# Trevor v2 Deployment Guide

## Requirements

- MyClaw instance (running)
- Python 3.10+
- Git
- `weasyprint` (optional, for PDF rendering): `pip3 install weasyprint`

## Quick Start

```bash
# 1. Clone or pull the repo
git clone https://github.com/trevormentis-spec/OpenClawTrevorMentis.git
cd OpenClawTrevorMentis

# 2. Configure secrets
cp deployment/.env.example .env
# Edit .env with your API keys

# 3. Run bootstrap
bash deployment/bootstrap.sh

# 4. Health check
bash deployment/health-check.sh

# 5. Onboard your first topic
python3 analyst/topic_onboarding.py --topic "Your Topic Here"
```

## Environment Variables

### Required
| Variable | Provider | Purpose |
|----------|----------|---------|
| `DEEPSEEK_API_KEY` | DeepSeek | Mid-tier and high-volume models |

### Recommended
| Variable | Provider | Purpose |
|----------|----------|---------|
| `OPENROUTER_API_KEY` | OpenRouter | Frontier models (Opus 4.7, Sonnet) |
| `ELEVENLABS_API_KEY` | ElevenLabs | Audio companion generation |
| `AGENTMAIL_API_KEY` | AgentMail | Email send/receive |

### Optional
| Variable | Provider | Purpose |
|----------|----------|---------|
| `NEWSAPI_KEY` | NewsAPI | News monitoring |
| `GENVIRAL_API_KEY` | GenViral | Social content generation |
| `KALSHI_API_KEY` | Kalshi | Prediction market scanning |
| `BUTTONDOWN_API_KEY` | Buttondown | Newsletter publishing |
| `BRAVE_API_KEY` | Brave | Web search |

## First Topic Onboarding

After bootstrap, onboard a topic:

```bash
python3 analyst/topic_onboarding.py --topic "Semiconductor supply chain"
```

This creates `config/topics/semiconductor-supply-chain/` with:
- `topic.yaml` — scope definition
- `themes.yaml` — analytical dimensions
- `sources.yaml` — source inventory
- `entities.yaml` — tracked entities
- `calibration.json` — calibration baseline
- `branding.yaml` — presentation branding
- `routing-overrides.yaml` — model routing overrides

## Backup & Restore

```bash
# Create backup
bash deployment/backup-restore.sh backup

# Restore from backup
bash deployment/backup-restore.sh restore exports/trevor-backup-*.tar.gz
```

## Branch Protection

- All changes should go through PRs
- Tests must pass before merge
- Principal review required for changes to:
  - Structural guards (scope_check, fabrication_check, themes_preflight)
  - Identity files (SOUL.md, IDENTITY.md, AGENTS.md)
  - Routing logic (llm_gate.py, ORCHESTRATION.md)
  - Budget configuration (budget.yaml)

## Rollback

If v2 has issues, roll back to v1:

```bash
git checkout trevor-v1-mexico
bash deployment/bootstrap.sh
# Restore brain backup if needed:
bash deployment/backup-restore.sh restore <v1-backup-tarball>
```

## Troubleshooting

### "DEEPSEEK_API_KEY not set"
Check `.env` file exists and contains the key. The key should not be quoted.

### "weasyprint not available"
Install: `pip3 install weasyprint`. On macOS, you may also need: `brew install pango`.

### Tests failing
Run individual test suites for diagnostics:
```bash
python3 tests/test_llm_gate.py
python3 tests/test_topic_onboarding.py
python3 tests/test_self_improvement.py
```

### Brain index missing
Rebuild: `python3 brain/scripts/brain.py reindex`
