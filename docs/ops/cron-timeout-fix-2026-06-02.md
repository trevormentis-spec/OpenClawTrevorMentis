# Cron Timeout Fix — 2026-06-02

## Summary

Three critical pipeline cron jobs were silently failing with "cron: job execution timed out"
for days (LEO: 7 consecutive errors, DC Security: 3, Brief Auto-Recovery: 3).

## Root Cause

The `timeoutSeconds` values in the cron job payloads were too short for the actual
pipeline execution time:

| Cron | Old Timeout | New Timeout | Consecutive Errors |
|------|-------------|-------------|-------------------|
| LEO Daily Brief (5026ed81) | 600s (10 min) | 1800s (30 min) | 7 |
| DC Security Daily (f5fe6ef6) | 300s (5 min) | 1200s (20 min) | 3 |
| Brief Auto-Recovery (6c54d13f) | 300s (5 min) | 900s (15 min) | 3 |

These are scripts that involve DeepSeek API calls, data collection, brief generation,
and often AgentMail delivery. They can easily take 10-20 minutes.

## Secondary Fix: False Deadline Alarm

`scripts/autonomous_cycle.py` had a hardcoded 12:00 UTC deadline in `check_pipeline()`,
causing multiple false "🔴 No brief found" alarms per day. Actual pipeline crons fire at:
- 08:00 PT (15:00 UTC) — DC Security Daily
- 09:00 PT (16:00 UTC) — LEO Daily Brief
- 12:00 PT (19:00 UTC) — Combined Intel Digest

**Fix:** Deadline moved to 16:30 UTC (30 min after earliest pipeline).

## Verification

- Fixes applied 2026-06-02 13:25 UTC
- Brief Auto-Recovery next run: 07:15 PT (14:15 UTC)
- DC Security Daily next run: 08:00 PT (15:00 UTC)
- LEO Daily Brief next run: 09:00 PT (16:00 UTC)
- Monitor cron states after these runs to verify

## How to Fix in Future

```bash
# Edit timeoutSeconds for a cron job:
openclaw cron edit <id> --timeout-seconds <N>
```

## Relevant Files

- `scripts/autonomous_cycle.py` — check_pipeline deadline
- `KNOWN_ISSUES.md` — entry updated with fix details
- `memory/2026-06-02.md` — 13:25 UTC heartbeat with full details
