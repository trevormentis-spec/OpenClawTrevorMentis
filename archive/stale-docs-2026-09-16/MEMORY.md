# MEMORY.md

## Standing Knowledge

## Core Identity

- Assistant name: Trevor
- Trevor stands for: Threat Research and Evaluation Virtual Operations Resource

## Current State: Dormant Mode (since 2026-06-02)

Trevor's product is reduced to four crons: LEO Daily Brief, DC Security Daily, RDX Weekly Brief, and AgentMail Inbox Sweep. Everything else is archived at `archive/dormant-2026-06-02/`. See `IDENTITY.md` for the full archived inventory.

No autonomy loops, health monitors, trading, publishing, or self-improvement are running. Trevor does not auto-recover.

## Retained infrastructure unchanged

- All API adapters and keys (`.env` untouched)
- Kalshi data pull: `trading-system/execution/kalshi_adapter.py` + `gated_client.py`
- Brief dependencies (preflight QC, report memory utilities)
- Utility skills (mermaid, mapbox, pdf-report, chartgen-ai, agentmail, translation, threat-intel-aggregator)
- Brain runtime
- Source inventories for LEO and RDX under `config/topics/`

## Durable Decisions

### Pipeline Constraints
- [2026-05-06] `analyze.py` max_tokens=8192 for DeepSeek V4 Pro calls
- [2026-05-11] Pipeline integration is separate from script fixes. The cron pipeline calls scripts with its own argument structure
- [2026-05-27] DeepSeek V4 Pro direct API hangs on payloads >20KB. Use OpenRouter for tier-1 exec summary calls

### Kalshi Trading Auth
- [2026-05-25] Autonomous Kalshi execution authority granted by Roderick. Retained but inactive in dormant mode.
- All trading code archived at `archive/dormant-2026-06-02/trading-system/`

### Autonomy
- [2026-05-13] Full operational autonomy confirmed by Roderick. Suspended in dormant mode.
- [2026-05-23] Autonomous brief-quality authority granted. Suspended in dormant mode.
