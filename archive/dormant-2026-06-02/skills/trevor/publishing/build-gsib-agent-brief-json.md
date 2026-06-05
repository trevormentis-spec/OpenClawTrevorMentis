---
name: build-gsib-agent-brief-json
description: Generate structured JSON brief for AI agent consumption from analysis data
version: 1.0.0
author: Trevor
created: 2026-05-11
tags: [agent-brief, json, publishing, api]
---

# Build Agent GSIB JSON

## When to Use
When producing the daily intelligence brief for AI agent subscribers.

## Input
- `scripts/build_agent_brief.py` — the generator script
- Analysis JSONs in `~/trevor-briefings/YYYY-MM-DD/analysis/`
- Kalshi market data at `exports/kalshi-scan-YYYY-MM-DD.md`

## Procedure
1. Change to workspace: `cd /home/ubuntu/.openclaw/workspace`
2. Run: `python3 scripts/build_agent_brief.py --working-dir ~/trevor-briefings/YYYY-MM-DD --moltbook`
3. Verify:
   - Check file `exports/agent-api/agent-brief-YYYY-MM-DD.json` exists and > 10 KB
   - Check latest.json is updated
   - If Moltbook key set, check Moltbook post went through

## Output Fields
- `bluf` — Bottom Line Up Front, one-paragraph
- `key_judgments[]` — array with id, statement, confidence_band, probability range, horizon, falsification
- `theatres[]` — per-region analysis with narrative, judgments, indicators, incident count
- `prediction_markets[]` — Kalshi + Polymarket with prices, volumes, expiry
- `watch_items[]` — prioritized with timeframe and impact
- `indicators` — dashboard-style status/trend/threshold

## Schema Version
Current: `https://trevormentis.spec/agent-brief/v1`

## Pricing Note
Free tier: today's brief, 24h delay. Pro tier: real-time webhook delivery.
