# Dormant Mode — Trevor 2026-06-02

## What changed

Trevor's operational scope has been reduced to four deliveries. Everything not
serving these four is archived under `archive/dormant-2026-06-02/`.

## Active deliveries

| Product | Cadence | Script |
|---------|---------|--------|
| LEO Daily Brief | Daily 09:00 PT | `scripts/leo_daily_brief.py` |
| DC Security Daily | Daily 08:00 PT | `scripts/dc_daily_brief.py` |
| RDX Weekly Brief | Monday 08:00 PT | `scripts/rdx_weekly_brief.py` |
| Inbox Sweep | Every 2h | `scripts/agentmail_reader.py` |

## Retained

- All API keys (`.env` untouched)
- Kalshi data pull: `trading-system/execution/kalshi_adapter.py`, `gated_client.py`
- Brief dependencies (preflight QC, report memory)
- Utility skills (mermaid, mapbox, pdf-report, chartgen-ai, agentmail, translation, threat-intel-aggregator)
- Brain runtime
- Source inventories for LEO and RDX

## Archived (recoverable at `archive/dormant-2026-06-02/`)

### Autonomy loops
autonomous_cycle, calibration_loop, iw_feedback_loop, reasoning_loop,
weekly_meta_review, postdict, behavioral_state, meta_cognition,
autonomy_tracker, self_assessment

### Health monitoring
health_engine, control-plane-health, feed_health_audit, runtime-health,
write-health-state, infra_alert, failure_notify, runtime-report

### Publishing / social
newsletter, social-poster, cross-poster, landing-page-generator,
content-marketing, GenViral, social-post, social-media-agent,
visual-production, content-generation, landing-page-roast

### Trading
philby (all desks, scripts, trader), trading-system
(edge/exit/guardrails/llm/audit/calibration/tests, paper_fill,
daily_reconciliation)

### Other
daily-intel-brief skill, skill-generator, signal board, OSINT plans,
philby-brief.html, philby-dc.html, philby-hero.jpg, source discovery
artifacts, indicator boards, circadian state, dream state, heartbeat state

## Cron jobs disabled (30 total)

All OpenClaw cron jobs have been disabled except the four above.
See `openclaw cron list` for current state and `.crontab` for documentation.

## How to re-activate

Check out `archive/dormant-2026-06-02/` — everything is intact and recoverable
via `git mv <path back>` and re-enabling the relevant OpenClaw cron jobs.
