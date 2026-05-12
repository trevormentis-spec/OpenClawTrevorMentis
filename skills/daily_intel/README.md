# Daily Intel Skill

Autonomous geopolitical intelligence and PDF publication skill for OpenClaw.

## Features
- Multi-theatre intelligence synthesis
- Prediction-market overlay
- Autonomous PDF generation
- Daily state tracking
- Vector memory retrieval
- OpenRouter orchestration
- Local fallback support

## Structure
- assessments/: theatre markdowns
- scripts/: PDF/maps/infographic builders
- memory/: vector memory + retrieval
- cron/: autonomous scheduling
- images/: refreshed imagery

## Runtime
Primary orchestration:
- openrouter/deepseek/deepseek-v4-flash

Local fallback:
- Ollama qwen2.5:3b

## Commands
python3 scripts/build_pdf.py
python3 memory/index_memory.py
python3 cron/run_daily.py
