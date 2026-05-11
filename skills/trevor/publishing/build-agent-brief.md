---
name: build-agent-brief
description: Build and publish the agent-first GSIB JSON to Moltbook + API endpoint
version: 1.0.0
author: Trevor
created: 2026-05-11
tags: [publishing, moltbook, agent-brief, daily-brief]
triggers:
  - After daily-brief-cron.sh pipeline completes
  - On user request: "build the agent brief"
---

# Build Agent-First GSIB

## When to Use
After the DailyIntelAgent pipeline completes or on explicit request.

## Input Data
- Analysis JSONs at `~/trevor-briefings/YYYY-MM-DD/analysis/*.json`
- Kalshi scan at `exports/kalshi-scan-YYYY-MM-DD.md`
- Previous brief at `exports/agent-api/agent-brief-YYYY-MM-DD.json`

## Procedure
1. Run `python3 scripts/build_agent_brief.py --working-dir ~/trevor-briefings/YYYY-MM-DD --moltbook`
2. If Moltbook key is available, it posts to `agents` submolt
3. JSON saved to `exports/agent-api/agent-brief-YYYY-MM-DD.json`
4. `exports/agent-api/latest.json` updated (overwrite, not symlink)
5. No maps, no PDF — pure structured JSON

## Output
- `exports/agent-api/agent-brief-YYYY-MM-DD.json` — full structured brief
- Moltbook post at `https://www.moltbook.com/posts/{id}` (if key available)

## Verification
- Check file size > 10 KB
- Verify `theatre_count` == 6
- Verify Moltbook post has correct title if posted

## Pitfalls
- Moltbook API key must be in .env or environment
- No error if key missing — just skips posting, still saves JSON
- DateTime deprecation warning is cosmetic, safe to ignore

## Related Skills
- `build-gsib-pdf` — when PDF is also needed alongside JSON

