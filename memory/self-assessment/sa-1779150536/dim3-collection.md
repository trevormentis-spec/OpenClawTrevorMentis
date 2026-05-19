# Dimension 3 — Collection Autonomy

## Current State
- 10 collector scripts in collectors/
- Sources: 113 in sources-mexico.json
- DOF: 34 articles/day, V4 Pro classification, daily memo
- CENACE: 19,440 records, anomaly detection
- Telegram: 6 channels, 2 posts from SEDENA Press (10 collectors)

## Collectors Status
  - amis_collector: PRODUCING
  - cenace_collector: PRODUCING
  - compranet_collector: PRODUCING
  - dof_collector: PRODUCING
  - dof_monitor: PRODUCING
  - maritime_ais_collector: PRODUCING
  - military_procurement_collector: PRODUCING
  - property_records_collector: PRODUCING
  - real_estate_collector: PRODUCING
  - telegram_monitor: PRODUCING

## Evidence
- DOF backfill: 34 articles from today (2026-05-18)
- CENACE: 19,440 records across 9 regions
- Telegram: 2 posts from SEDENA Press (public channels)
- Real estate scaffold: 4 states, Vivanuncios + Inmuebles24
- Maritime AIS: free tier only (paid API pending)

## Friction Points
- Most collectors are scaffold-only — produce placeholder output until wired into regular cron
- No collector health monitoring (failed fetches, stale data)
- Telegram web preview (t.me/s/) is unreliable — different channels have different HTML structures
- Maritime AIS needs paid API for comprehensive coverage

## Gaps
1. AUTO_FIX: Add collector health tracking (last-fetch timestamp per collector)
2. PRINCIPAL_REVIEW: Maritime AIS paid API needed for production-quality data
3. PRINCIPAL_REVIEW: Cartel Telegram channels still pending (per directive)
