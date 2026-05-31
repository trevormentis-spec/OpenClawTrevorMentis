# Trevor Health Alerts

**Generated:** 2026-05-31T15:57:57.063751+00:00
**Health Score:** CRITICAL (0/100)
**Total Alerts:** 7

⚠️ **[WARNING]** cron_health: Correlated error across 5 jobs: cron: job interrupted by gateway restart
   Affected jobs: 0eb2de56, a1d90107, 5026ed81, a20962e6, 82c2e29c
   Root cause: unknown

⚠️ **[WARNING]** cron_health: Correlated error across 12 jobs: FailoverError: ⚠️ deepseek (deepseek-v4-flash) returned a bi
   Affected jobs: a656b6c8, ae0d522f, e9f62049, ac010c62, cb039bf5
   Root cause: unknown

⚠️ **[WARNING]** cron_health: Correlated error across 8 jobs: FallbackSummaryError: All models failed (1): deepseek/deepse
   Affected jobs: 69d9d778, e0647d21, f082ad3a, 730ec3bb, f5fe6ef6
   Root cause: unknown

🔴 **[CRITICAL]** cron_health: 26/36 enabled jobs failing (72.2%)
   Root cause: >50% of enabled cron jobs failing

🔴 **[CRITICAL]** cron_health: Systemic billing error affecting 20 jobs
   Affected jobs: a656b6c8, ae0d522f, e9f62049, 69d9d778, ac010c62
   Root cause: DeepSeek billing exhausted

🔴 **[CRITICAL]** pipeline: final/brief.md missing or doesn't contain today (2026-05-31)
   Root cause: Daily brief pipeline may not have run

⚠️ **[WARNING]** heartbeat: Stale phases: agentmail_inbox (291h), deepseek_balance (291h), nudge_check (291h), repo_state (291h), calendar (285h), memory_hygiene (285h), openrouter_usage (285h), brain_index (141h), social_monitor (718h), phase_d (141h), cost_snapshot (141h), memory_maintenance (141h), phase_a (116h), feed_audit (116h), phase_c (164h), prune_cycle (49h)
   Root cause: Some heartbeat phases haven't run in >48h
