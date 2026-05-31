# Trevor Health Alerts

**Generated:** 2026-05-31T18:13:29.283175+00:00
**Health Score:** CRITICAL (0/100)
**Total Alerts:** 5

⚠️ **[WARNING]** cron_health: Correlated error across 7 jobs: FailoverError: ⚠️ deepseek (deepseek-v4-flash) returned a bi
   Affected jobs: ae0d522f, cb039bf5, f10da54a, 1976bd12, 7ca66311
   Root cause: unknown

⚠️ **[WARNING]** cron_health: Correlated error across 5 jobs: FallbackSummaryError: All models failed (1): deepseek/deepse
   Affected jobs: 69d9d778, e0647d21, f5fe6ef6, 02104a0d, 54fa00f7
   Root cause: unknown

⚠️ **[WARNING]** cron_health: Correlated error across 3 jobs: cron: job execution timed out
   Affected jobs: 5026ed81, a20962e6, ce4cb113
   Root cause: unknown

🔴 **[CRITICAL]** cron_health: 17/34 enabled jobs failing (50.0%)
   Root cause: >50% of enabled cron jobs failing

🔴 **[CRITICAL]** cron_health: Systemic billing error affecting 12 jobs
   Affected jobs: ae0d522f, 69d9d778, cb039bf5, f10da54a, 1976bd12
   Root cause: DeepSeek billing exhausted
