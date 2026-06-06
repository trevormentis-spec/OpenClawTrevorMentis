# Dormant-Mode Archive — 2026-06-02

Everything in this directory was archived from active use during the
2026-06-02 dormant-mode triage. Nothing was deleted; everything is
recoverable.

## Why this happened

Trevor accumulated control systems faster than reliability. By
2026-06-02 he had:

- 15+ health-monitoring systems watching each other
- 5+ feedback loops (calibration, I&W, reasoning, autonomy tracker,
  weekly meta-review) silently adjusting each other
- An autonomous trading desk (philby) with $0.24 balance and 276
  recent insufficient_balance failures
- A Signal Board, an OSINT business plan, an OSINT product launch
  plan, a landing page deploy chain, a Buttondown newsletter, social
  posting across 6 platforms — none of which the principal asked for
- A daily brief pipeline (`skills/daily-intel-brief/`) that hung on
  model calls, produced empty BLUFs when it ran, and required
  cron-timeout doubling/tripling to compensate
- 313 commits in the 4 days before the triage, ~3/hour, almost all
  auto: self-modifications

The principal's actual need was three private briefs in his inbox.

## What was archived

| Subdirectory | Contents |
|---|---|
| scripts/ | autonomy loops, health monitors, pivot artifacts (signal_board, postdict, behavioral_state, calibration_loop, iw_feedback_loop, reasoning_loop, weekly_meta_review, control-plane-health, health_engine, write-health-state, ...) |
| skills/ | publishing/social/pivot skills (daily-intel-brief, skill-generator, genviral, newsletter, social-poster, cross-poster, landing-page-generator, content-marketing, visual_production, akashic-doc-analyzer, oraclaw-graph, ...) |
| plans/ | osint-business-plan.md, osint-product-launch.md, social-posting-protocol.md |
| philby-trader/, philby-desks/, philby-scripts/ | autonomous prediction-market trading |
| trading-system/ | autonomous trading orchestration (paper_fill, daily_reconciliation, edge, exit, guardrails, llm, intel, audit, calibration, tests, config) |
| root-artifacts/ | philby-brief.html, philby-dc.html, philby-hero.jpg |

## What was kept active

Repository root for the active product. In particular:

- The three brief scripts (`scripts/leo_daily_brief.py`,
  dc_daily_brief.py, `rdx_weekly_brief.py`)
- The inbox sweep (`scripts/agentmail_reader.py`)
- All API adapters and .env (untouched)
- All skills not listed above
- trading-system/execution/kalshi_adapter.py and gated_client.py —
  the Kalshi pull capability, callable manually
- analyst/, brain/, config/topics/ — unchanged
- The source inventories and entity tables for LEO and RDX — these
  represent real analytical scaffolding worth keeping

## Pulling something back

If a capability needs to come back, surface that to the principal
first. There was a reason it was archived. Then git mv it back —
the import paths from the active scripts are unchanged so most
things should work without modification.

## The decision tree, recorded

The triage went through these decisions:

1. Keep all API access and adapters. The wiring was the hard part.
2. Keep skills accessible. They are a library.
3. Briefs deliver via the existing per-beat scripts, not the broken
   multi-stage pipeline.
4. Newsletter inbox sweep stays — useful, contained, single-purpose.
5. Calibration / Sherman Kent / postdiction loop dropped — 3% accuracy
   over months said it wasn't actually serving the product.
6. Brain memory stays available but no autonomous reindexing — manual
   invocation only.
7. Trading: Kalshi adapter stays as a library; autonomous trader gone.

Repo size before triage: 107M, ~2000 tracked files. After: roughly
half that, with the heavy lifting being directory moves rather than
deletions.
