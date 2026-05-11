---
name: daily-intel-pipeline
description: Run the full DailyIntel improvement daemon pipeline
version: 1.0.0
tags: publishing, daily, pipeline
---

# DailyIntel Pipeline

## When to Use
Before running the daily improvement daemon, or when manually generating a brief.

## Procedure
1. Ensure trevor_config has correct WORKSPACE path (env var TREVOR_WORKSPACE)
2. Run: python3 improvement_daemon.py --daily
3. Monitor heartbeat logs in cron_tracking/daemon_run.log
4. After completion, check cron_tracking/state.json for health status

## Pipeline Steps
1. Enrichment (RSS feeds, Kalshi, story freshness)
2. Assessment generation (DeepSeek V4 Pro, 7 parallel threads)
3. Imagery refresh (maps + photos)
4. PDF build (reportlab, ThruDark style)
5. Quality audit + auto-repair
6. Memory index (FTS5)
7. Narrative tracking
8. Distribution (email)
