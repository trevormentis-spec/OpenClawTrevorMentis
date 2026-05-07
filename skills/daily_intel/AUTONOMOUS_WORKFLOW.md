# Autonomous Workflow

## Daily Cycle

1. Pull previous state.json
2. Retrieve top narrative continuity memories
3. Search latest geopolitical developments
4. Refresh prediction market pricing
5. Update theatre markdowns
6. Refresh imagery
7. Regenerate maps + infographics
8. Build PDF
9. Persist state
10. Distribute via Telegram/email

## Model Routing

Primary:
- openrouter/deepseek/deepseek-v4-flash

Escalation:
- openrouter/auto

Local:
- ollama/qwen2.5:3b

## Memory Architecture

Vector memory stores:
- prior editions
- prior trade theses
- source credibility
- narrative continuity
- imagery history

## Retrieval Rules

- retrieve top 3 chunks only
- avoid loading full archives
- prefer most recent state
- preserve narrative continuity

## Autonomy Rules

- run once daily via cron
- never publish duplicate lead story
- enforce fresh imagery
- log all repricings >3pp
- preserve estimative language
