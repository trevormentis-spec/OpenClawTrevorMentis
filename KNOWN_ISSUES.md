# Known Issues — Persistent problems across sessions
# 
# Every session reads this at startup. DO NOT REMOVE entries until verified fixed
# in production (not just in a dev/test run).
#
# Format:
#   [DATE_FOUND] short description | tracking link/ref
#   Fix: what's needed
#   Status: OPEN | FIX_APPLIED | WAITING_USER | VERIFIED_CLOSED

## Infrastructure

[2026-05-28] **Landing page deploy verification** | scripts/deploy_landing_page.sh
Fix: Verification step added to deploy script (sleep 5s + curl check for issue date)
Status: FIX_APPLIED — needs to pass 3 consecutive daily deploys before close

[2026-05-25] **GitHub PAT for landing page** | ~/.ssh/id_trevormentis
Fix: Switched to SSH auth (github.com-trevormentis host alias). SSH key works (tested).
Status: VERIFIED_CLOSED — SSH auth confirmed working, deploy pushed successfully

[2026-05-28] **OpenRouter credits exhausted** | openrouter.ai
Fix: Credits restored by Roderick. Monitor via infra_alert.py cron (every 4h).
Status: OPEN — will auto-alert if credits drop again

[2026-06-03] **analyze.py crashes on None/empty LLM response** | skills/daily-intel-brief/scripts/analyze.py
Fix: Added None-guard in `parse_json_strict()`. Retry for tier-2 regional analysis and tier-1 exec
summary now falls back to mock payload instead of propagating crash. Single-region failure no longer
kills the entire brief pipeline.
Status: FIX_APPLIED — needs to survive one full pipeline run before close

## Pipeline

[2026-05-28] **Exec summary truncation** | skills/daily-intel-brief/scripts/analyze.py
Fix: max_input_chars increased from 18000 to 60000 for exec summary calls
Status: FIX_APPLIED — needs to survive one full pipeline run (next cron: 05:00 PT May 29)

[2026-05-28] **Landing page build script lacks template insertion markers** | scripts/_build_landing.py
Fix: Changed to inject before pricing grid instead of using non-existent markers
Status: FIX_APPLIED — verified live (26 theatre cards on page)

## Collection

[2026-05-22] **Feed rot — 342 dead feeds returning 403 (Cloudflare WAF)**
Fix: Systemic issue — urllib blocked by Cloudflare. Catalog trimmed to working feeds only.
Status: OPEN — 298 working feeds tracked in sources_tested.json

[2026-05-31] **Philby Collector cron still enabled after trading system teardown** | cron/jobs.json id=25e1c622
Fix: Disabled cron job — collector.py was archived at archive/philby-trading-2026-05-31/philby/collector/collector.py
Status: FIX_APPLIED

## Memory & Process

[2026-05-28] **No startup-known-issues read** | AGENTS.md / session startup
Fix: Sessions MUST read this file (KNOWN_ISSUES.md) to avoid re-discovering same problems
Status: FIX_APPLIED — this file exists, need to add read reference

[2026-05-28] **Fix applied ≠ fix verified** | systemic
Rule: After applying any fix, run it in production context once and verify output. Do not mark closed until verified in actual pipeline run.
Status: OPEN — procedural, needs discipline

[2026-06-02] **Daily brief pipeline crons timing out** | 3 crons: LEO Daily (5026ed81), DC Security (f5fe6ef6), Brief Auto-Recovery (6c54d13f)
Fix (applied 2026-06-02 13:25 UTC):
  - DC Security Daily timeout: 300s → 1200s (20 min)
  - LEO Daily Brief timeout: 600s → 1800s (30 min)
  - Brief Auto-Recovery timeout: 300s → 900s (15 min)
  - autonomous_cycle.py deadline: 12:00 UTC → 16:30 UTC (match actual pipeline schedule)
Still monitored: Brief Auto-Recovery fires at 07:15 PT (14:15 UTC) — will test 900s timeout
Status: FIX_APPLIED — needs to survive one full pipeline cycle before close
