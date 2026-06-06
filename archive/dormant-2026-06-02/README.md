# Archive — Dormant Mode 2026-06-02

## Decision

Per principal directive (Roderick Jones, 2026-06-02), Trevor's operational
scope has been reduced to three brief deliveries and one inbox sweep.
Everything else — autonomy loops, health monitoring, trading infrastructure,
publishing pipelines, skill generators, signal boards — has been moved here.

Nothing has been deleted. Every file is recoverable by `git mv` back to its
original path.

## Previous product surface (pre-2026-06-02)

Trevor ran:
- Autonomous operation cycles (every 4h)
- Health engine (every 15m / every 1h / every 6h)
- Trading system (philby desks, Kalshi execution, Polymarket monitoring)
- Daily Intel Brief (multi-stage pipeline with quality gate)
- Social publishing (newsletter, Twitter/Farcaster cross-posting, landing page)
- Calibration loops, postdiction tracking, I&W feedback
- Dream / memory consolidation (daily)
- Source discovery, feed health checks, narrative freshness
- Signal board, OSINT plans, social posting protocol
- Capability expansion, continuous improvement daemon

## What remains active

| Product | Script | Cadence (PT) |
|---------|--------|-------------|
| DC Security Daily | `scripts/dc_daily_brief.py` | Daily 08:00 |
| LEO Daily Brief | `scripts/leo_daily_brief.py` | Daily 09:00 |
| RDX Weekly Brief | `scripts/rdx_weekly_brief.py` | Monday 08:00 |
| AgentMail Inbox Sweep | `scripts/agentmail_reader.py` | Every 2h |

## How to re-activate archived components

1. `git mv archive/dormant-2026-06-02/<path> <original-path>`
2. Re-enable the corresponding OpenClaw cron job
3. Check `config/` for any routing or budget config that was also archived

## Archive layout

```
archive/dormant-2026-06-02/
├── brain/            — autonomous state, calibration directives, collection state, dead feeds, etc.
├── health/           — health alerts, health dashboard, infra alert state, QC alerts
├── pivot-artifacts/  — signal board, indicator boards, polymarket artifacts, philby HTML/images
├── plans/            — OSINT business plan, product launch, social posting protocol
├── root-artifacts/   — philby-brief.html, philby-dc.html, philby-hero.jpg
├── scripts/          — all ~200 scripts except the 6 brief/inbox/dependency scripts
├── skills/           — 22 archived skills (trading, publishing, genviral, etc.)
├── trading-system/   — full philby + trading-system except kalshi adapter
├── trading/          — philby trader calibration stamp
├── publishing/       — (empty, reserved)
├── .dreams/          — short-term recall, events
├── heartbeat-state.json
└── llm-routing-log.jsonl
```
