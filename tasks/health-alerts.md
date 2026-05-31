# Trevor Health Alerts

**Generated:** 2026-05-31T16:12:42.488800+00:00
**Health Score:** CRITICAL (0/100)
**Total Alerts:** 5

⚠️ **[WARNING]** cron_health: Correlated error across 4 jobs: cron: job interrupted by gateway restart
   Affected jobs: 0eb2de56, a1d90107, a20962e6, 82c2e29c
   Root cause: unknown

⚠️ **[WARNING]** cron_health: Correlated error across 9 jobs: FailoverError: ⚠️ deepseek (deepseek-v4-flash) returned a bi
   Affected jobs: ae0d522f, e9f62049, cb039bf5, f10da54a, 1976bd12
   Root cause: unknown

⚠️ **[WARNING]** cron_health: Correlated error across 7 jobs: FallbackSummaryError: All models failed (1): deepseek/deepse
   Affected jobs: 69d9d778, e0647d21, f082ad3a, 730ec3bb, f5fe6ef6
   Root cause: unknown

🔴 **[CRITICAL]** cron_health: 22/38 enabled jobs failing (57.9%)
   Root cause: >50% of enabled cron jobs failing

🔴 **[CRITICAL]** cron_health: Systemic billing error affecting 16 jobs
   Affected jobs: ae0d522f, e9f62049, 69d9d778, cb039bf5, f10da54a
   Root cause: DeepSeek billing exhausted
