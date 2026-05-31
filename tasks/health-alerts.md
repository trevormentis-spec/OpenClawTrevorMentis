# Trevor Health Alerts

**Generated:** 2026-05-31T16:17:20.273307+00:00
**Health Score:** CRITICAL (0/100)
**Total Alerts:** 7

⚠️ **[WARNING]** cron_health: Correlated error across 5 jobs: cron: job interrupted by gateway restart
   Affected jobs: 0eb2de56, a1d90107, a20962e6, 82c2e29c, 511d14b2
   Root cause: unknown

⚠️ **[WARNING]** cron_health: Correlated error across 8 jobs: FailoverError: ⚠️ deepseek (deepseek-v4-flash) returned a bi
   Affected jobs: ae0d522f, e9f62049, cb039bf5, f10da54a, 1976bd12
   Root cause: unknown

⚠️ **[WARNING]** cron_health: Correlated error across 6 jobs: FallbackSummaryError: All models failed (1): deepseek/deepse
   Affected jobs: 69d9d778, e0647d21, f082ad3a, f5fe6ef6, 02104a0d
   Root cause: unknown

🔴 **[CRITICAL]** cron_health: 21/34 enabled jobs failing (61.8%)
   Root cause: >50% of enabled cron jobs failing

🔴 **[CRITICAL]** cron_health: Systemic billing error affecting 14 jobs
   Affected jobs: ae0d522f, e9f62049, 69d9d778, cb039bf5, f10da54a
   Root cause: DeepSeek billing exhausted

🔴 **[CRITICAL]** pipeline: final/brief.md missing or doesn't contain today (2026-05-31)
   Root cause: Daily brief pipeline may not have run

⚠️ **[WARNING]** heartbeat: Stale phases: agentmail_inbox (291h), deepseek_balance (291h), nudge_check (291h), repo_state (291h), calendar (285h), memory_hygiene (285h), openrouter_usage (285h), brain_index (141h), social_monitor (718h), phase_d (141h), cost_snapshot (141h), memory_maintenance (141h), phase_a (117h), feed_audit (117h), phase_c (165h), prune_cycle (50h)
   Root cause: Some heartbeat phases haven't run in >48h
