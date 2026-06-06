# Trevor — Dormant-Mode Repository

**Status:** dormant (since 2026-06-02). Produces three intelligence briefs
to the principal's inbox; nothing else runs autonomously.

## What this repo does

| Output | Script | Cadence |
|---|---|---|
| LEO Ground Stations brief | scripts/leo_daily_brief.py | Daily |
| Data Center Security brief | scripts/dc_daily_brief.py | Daily |
| RDX / C4 Supply brief | scripts/rdx_weekly_brief.py | Weekly (Mon) |
| Newsletter inbox sweep | scripts/agentmail_reader.py | Hourly |

All four go to roderick.jones@gmail.com via AgentMail.

## What's in the repo

- scripts/ — brief runners + adapter scripts (AgentMail, Kalshi, GDELT,
 Brave, DeepSeek, etc.). Most still callable directly.
- skills/ — utility skills (mermaid, mapbox, pdf-report, chartgen,
 translation, threat-intel-aggregator, etc.). Library, not autonomous.
- trading-system/execution/kalshi_adapter.py — Kalshi auth + pull.
 Read-only use. No autonomous trader.
- analyst/ — LLM gate, scope/fabrication/themes guards, brain helpers.
- brain/ — TF-IDF memory runtime. Manual invoke only.
- config/topics/ — source inventories and entity tables for LEO, RDX,
 and a few archived topics. The good analytical scaffolding.
- archive/dormant-2026-06-02/ — everything archived in the dormant-mode
 triage. Recoverable.

## How to run a brief manually

```bash
python3 scripts/leo_daily_brief.py --dry-run # preview
python3 scripts/leo_daily_brief.py # full run + send
```

Same pattern for dc_daily_brief.py and rdx_weekly_brief.py.

## Cron

`.crontab` is the single source of truth. Four jobs only.

## What used to be here

A great deal. Trevor v2 was a domain-general autonomous analyst with
feedback loops, a trading desk, a newsletter publisher, social posting,
a landing page, multiple health systems, and a self-improvement engine.
All of it is in archive/dormant-2026-06-02/. The product diverged
from the principal's actual need (three private briefs in his inbox)
and accumulated complexity faster than it could maintain reliability.

The triage was done 2026-06-02. The principle going forward: this repo
is a library of API adapters and a small set of brief scripts. It does
not try to be more than that.

## Adding things back

If you find yourself wanting to add a feedback loop, a health monitor,
or an autonomy layer: stop and ask the principal. The history of doing
that without asking is in the commit log between 2026-04-15 and
2026-06-02. It did not end well.
