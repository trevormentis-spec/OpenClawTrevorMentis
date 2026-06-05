# skills/daily-intel-brief

Trevor's Daily Intelligence Brief.

This is a **standing product** — same shape every day, different content.
It is distinct from the single-question analytic workflow.

## Quick start

```bash
# one-shot
python3 skills/daily-intel-brief/scripts/orchestrate.py

# scheduled (cron, 06:30 local)
30 6 * * * cd /path/to/OpenClawTrevorMentis && \
    python3 skills/daily-intel-brief/scripts/orchestrate.py >> \
    ~/trevor-briefings/log.txt 2>&1
```

## What it is

Six regional sections (Europe, Asia, Middle East, North America,
South & Central America incl. Caribbean, Global Finance) plus a BLUF
exec summary. Each regional key judgment carries a Sherman Kent band
and a 7-day prediction percentage. Final product is PDF + DOCX,
delivered via AgentMail.

## What it's not

Not a single-question deep dive (use `analyst/playbooks/analytic-workflow.md`).
Not a methodology reference (use `skills/sat-toolkit`,
`skills/source-evaluation`, `skills/indicators-and-warnings`).
Not a special assessment (escalation criteria in
`playbooks/escalation-criteria.md`).

## Architecture

Three subagents run in parallel after collection:

```
Step 1: collector  ────► raw/incidents.json
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
Step 2: analyst              Step 3: visuals
  (DeepSeek V4 Pro)            (geospatial-osint, chartgen, mermaid)
              │                     │
              └──────────┬──────────┘
                         ▼
                Step 4: quality gates
                         ▼
                Step 5: assemble (PDF + DOCX)
                         ▼
                Step 6: archive + deliver
```

See `SKILL.md` for the detailed orchestrator workflow.

## Routing

Per `ORCHESTRATION.md` v3.0:

- **Collector**: `deepseek/deepseek-v4-flash` (cheap summarisation)
- **Analyst**: `deepseek/deepseek-v4-pro` (high-stakes, daily principal product)
- **Visuals**: ChartGen / Mermaid / Cesium — no LLM call required for the
  pixels themselves; an LLM is only used to compose the chart spec.

## Required environment

- `DEEPSEEK_API_KEY` — required (analyst will fail loud if missing)
- `MAPBOX_TOKEN` — optional (geospatial-osint falls back to OSM)
- `CHARTGEN_API_KEY` — optional (build_visuals.py falls back to matplotlib)
- `AGENTMAIL_API_KEY` — required for delivery (or skip delivery and use
  --no-deliver flag)
