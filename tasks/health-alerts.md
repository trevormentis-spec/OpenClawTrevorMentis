# Trevor Health Alerts

**Generated:** 2026-05-31T18:32:50.803709+00:00
**Health Score:** CRITICAL (25/100)
**Total Alerts:** 6

⚠️ **[WARNING]** cron_health: Correlated error across 7 jobs: FailoverError: ⚠️ deepseek (deepseek-v4-flash) returned a bi
   Affected jobs: ae0d522f, cb039bf5, f10da54a, 1976bd12, 7ca66311
   Root cause: unknown

⚠️ **[WARNING]** cron_health: Correlated error across 5 jobs: FallbackSummaryError: All models failed (1): deepseek/deepse
   Affected jobs: 69d9d778, e0647d21, f5fe6ef6, 02104a0d, 54fa00f7
   Root cause: unknown

⚠️ **[WARNING]** cron_health: Correlated error across 3 jobs: cron: job execution timed out
   Affected jobs: 5026ed81, a20962e6, ce4cb113
   Root cause: unknown

⚠️ **[WARNING]** cron_health: 12 historical billing failures (resolved — DeepSeek balance $98.33). 5 active failures remaining.
   Affected jobs: ae0d522f, 69d9d778, cb039bf5, f10da54a, 1976bd12
   Root cause: DeepSeek billing has been RESOLVED since these failures

🔴 **[CRITICAL]** pipeline: final/brief.md missing or doesn't contain today (2026-05-31)
   Root cause: Daily brief pipeline may not have run

⚠️ **[WARNING]** heartbeat: Stale phases: agentmail_inbox (294h), deepseek_balance (294h), nudge_check (294h), repo_state (294h), calendar (288h), memory_hygiene (288h), openrouter_usage (288h), brain_index (143h), social_monitor (720h), phase_d (143h), cost_snapshot (143h), memory_maintenance (143h), phase_a (119h), feed_audit (119h), phase_c (167h), prune_cycle (52h)
   Root cause: Some heartbeat phases haven't run in >48h
