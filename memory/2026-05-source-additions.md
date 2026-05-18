# Source Addition Proposals — 2026-05-18

**Status:** PARKED for principal review
**No new skills installed.** Each proposal includes connector approach, schema, expected volume, and theme tags.

---

## (1) GDELT 2.0 via BigQuery

| Field | Value |
|-------|-------|
| Type | API (BigQuery) |
| Cost | Free tier ($300 credits/month) |
| Volume | 15-min cadence, ~1000+ Mexico events/day |
| Themes | cartel_security, political_risk, economy_markets |
| Schema | `{date, location (lat/lon/country/admin1/admin2), actor1, actor2, event_type, goldstein_scale, mention_sources}` |
| Connector | `scripts/gdelt_import.py` — BigQuery query filtered to country=MX or admin1 IN (mexican states). SQL only — no new skills. |
| Risk | BigQuery credits needed. Query optimization matters (don't pull every 15min). |
| Admiralty | C1 — machine-tagged, needs human validation |

**Recommendation:** Wire as the primary incident feed for framework_stress_test and cross_source_correlation. 15-min cadence means near-real-time Mexico event coverage.

---

## (2) ACLED Latin America

| Field | Value |
|-------|-------|
| Type | API (free for non-commercial) |
| Cost | Free |
| Volume | ~50-100 Mexico events/week |
| Themes | cartel_security |
| Schema | `{event_id, date, location, actor1, actor2, event_type (battle/violence against civilians/protests/riots), fatalities, notes}` |
| Connector | `scripts/acled_fetcher.py` — API call with country=Mexico, date filter. |
| Risk | Rate-limited. Better curation than GDELT for security events. |
| Admiralty | B2 — research-grade, manually curated |

**Recommendation:** Primary source for cartel violence incidents. ACLED data carries more weight than GDELT for court- or subscriber-facing analysis.

---

## (3) SESNSP Monthly Municipal Crime Stats

| Field | Value |
|-------|-------|
| Type | Web scrape (public PDF/XLSX) |
| Cost | Free |
| Volume | Monthly batches (~2,500 municipalities × 15 crime categories) |
| Themes | cartel_security |
| Schema | `{state, municipality, period, crime_type (homicide/kidnapping/extortion/vehicle theft/...), count, rate_per_100k}` |
| Connector | Point the existing scraper skill at `https://www.gob.mx/sesnsp/` — structured XLSX download. |
| Risk | File format may change. Monthly cadence means 2-4 week lag. |
| Admiralty | A1 — official government statistics (with caveat for underreporting bias ~15-30%) |

**Recommendation:** Canonical quantitative source for cartel_security. The Bajío brief's insurance premium claim would have been preventable with SESNSP per-municipality homicide data.

---

## (4) INEGI BIE Economic Indicators

| Field | Value |
|-------|-------|
| Type | API (BIE = Banco de Información Económica) |
| Cost | Free |
| Volume | ~50-100 series, monthly refresh |
| Themes | economy_markets, energy_infra |
| Schema | `{indicator_id, indicator_name, frequency, value, unit, geo_level (national/state/municipal)}` |
| Connector | `scripts/inegi_bie_fetcher.py` — simple HTTP GET to `https://www.inegi.org.mx/app/api/indicadores/...` |
| Risk | API key required (free). JSON format is complex/nested. |
| Admiralty | A1 — official national statistics |

**Recommendation:** Required for economy_markets theme. Enables municipality-level economic analysis that currently relies on web-search estimates.

---

## (5) Banxico SIE API

| Field | Value |
|-------|-------|
| Type | API (SIE = Sistema de Información Económica) |
| Cost | Free |
| Volume | ~30 series, daily refresh |
| Themes | economy_markets |
| Schema | `{series_id, series_name, date, value, unit}` |
| Connector | `scripts/banxico_sie_fetcher.py` — HTTP GET to `https://www.banxico.org.mx/SieAPIRest/service/v1/...` |
| Risk | API key required (free). Rate-limited. |
| Admiralty | A1 — central bank official data |

**Recommendation:** Best source for peso FX, Banxico rate decisions, international reserves, inflation data.

---

## (6) DOF (Diario Oficial de la Federación)

| Field | Value |
|-------|-------|
| Type | Web search/API |
| Cost | Free |
| Volume | ~20-50 publications/day |
| Themes | political_risk, energy_infra, economy_markets |
| Schema | `{date, type (decree/agreement/regulation/appointment), issuing_body, title, summary, url}` |
| Connector | RSS feed (`https://www.dof.gob.mx/rss.php`) + keyword filter for energy/security/trade terms |
| Risk | High volume, low signal-to-noise. Need keyword filters. |
| Admiralty | A2 — official publication (published = fact, significance is interpretive) |

**Recommendation:** Best source for Sheinbaum administration regulatory changes, Pemex/CFE appointments, USMCA implementation decrees.

---

## (7) OFAC SDN List

| Field | Value |
|-------|-------|
| Type | Machine-readable XML |
| Cost | Free |
| Volume | ~50-100 new entries/month (Mexico-specific subset) |
| Themes | cartel_security, us_mexico |
| Schema | `{name, aliases, nationality, sanctions_program, designation_date, id_type, id_number}` |
| Connector | `scripts/ofac_sdn_fetcher.py` — parse `https://www.treasury.gov/ofac/downloads/sdn.xml`, filter nationality=Mexico or MX sanctions program. |
| Risk | XML format may change. Need to track entity additions vs modifications. |
| Admiralty | A1 — official U.S. government list |

**Recommendation:** Directly connects cartel_security to us_mexico. Every FTO/SDN designation is a verifiable event the brief can cite.

---

## Summary

| # | Source | Cost | Cadence | Primary Theme | Effort (hours) |
|---|--------|------|---------|---------------|----------------|
| 1 | GDELT 2.0 | Free ($300 credits) | 15-min | cartel_security | 3 |
| 2 | ACLED | Free | Daily | cartel_security | 2 |
| 3 | SESNSP | Free | Monthly | cartel_security | 2 |
| 4 | INEGI BIE | Free | Monthly | economy_markets | 2 |
| 5 | Banxico SIE | Free | Daily | economy_markets | 1 |
| 6 | DOF | Free | Daily | political_risk | 2 |
| 7 | OFAC SDN | Free | Daily | cartel_security, us_mexico | 1 |

**Recommended priority (by theme gap impact):** SESNSP (closes the "no per-municipality crime data" gap from the Bajío brief) → ACLED (best security event data) → INEGI (enables municipal-level economic analysis) → GDELT (near-real-time event feed) → Banxico (reliable FX data) → DOF (regulatory tracking) → OFAC (sanctions monitoring).
