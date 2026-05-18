# Source Coverage Audit — 2026-05-18

**Audit of:** analyst/meta/sources-mexico.json (83 sources)
**Method:** Manual classification per source (status, URL, Admiralty rating, theme tags)
**Key finding:** ALL 83 sources are LISTED only. None are verified WIRED (working fetcher). None are verified USED (cited in briefs from the registry).

---

## Three-State Audit

| State | Count | Definition |
|-------|-------|------------|
| LISTED | 83 | In registry with URL and metadata |
| WIRED | 0 | Verified working RSS/API/scrape fetch |
| USED | 0 | Cited in a brief sourced from registry |
| Blocked | 1 | Riodoce — Cloudflare (documented workaround) |

**Conclusion:** The registry is a directory, not a data pipeline. Sources are catalogued but the collector (`mexico-daily-scan.py` / `scripts/collect.py`) fetches from a separate source list (`sources.json`), not from `sources-mexico.json`. The two lists have diverged. Sources-mexico.json was populated by the overnight handback as a knowledge-management artifact, but it was never wired into the actual fetch pipeline.

---

## Theme-by-Source Coverage Matrix

| Theme | Sources | Signal High | Signal Medium | Signal Low | Admiralty A | Admiralty B | Admiralty C |
|-------|---------|-------------|---------------|------------|-------------|-------------|-------------|
| cartel_security | 59 | — | — | — | — | — | — |
| political_risk | 37 | — | — | — | — | — | — |
| us_mexico | 27 | — | — | — | — | — | — |
| economy_markets | 25 | — | — | — | — | — | — |
| energy_infra | 22 | — | — | — | — | — | — |
| worldcup_travel | 4 | — | — | — | — | — | — |

(Detailed per-source table with signal/Admiralty breakdown available on request — the registry doesn't have machine-parseable signal/Admiralty counts at the aggregate level; they're embedded in descriptive text strings.)

**Gap themes:** energy_infra has 22 LISTED sources — not a registry gap but a pipeline gap. The sources are there (Pemex, CFE, SENER, CRE, CNH, etc.) but the briefs don't cite them because the collector doesn't read from this registry.

---

## Blocked Sources

| Source | Block | Workaround | Status |
|--------|-------|------------|--------|
| Riodoce (Sinaloa) | Cloudflare | Relay via Infobae/Milenio. 3 alternatives added (Debate Sinaloa B2, Luz Noticias C2, El Sol de Sinaloa B3). | Documented |

---

## Sample Registry Entries

| Source | Themes | Signal | Admiralty |
|--------|--------|--------|-----------|
| Animal Politico | cartel_security, political_risk | High | A2 |
| Reforma | cartel_security, political_risk, economy_markets, energy_infra | High | A2 |
| El Universal | cartel_security, political_risk, us_mexico, energy_infra | High | A2 |
| Milenio | cartel_security, political_risk | High | A2 |
| Infobae Mexico | cartel_security, political_risk, us_mexico | High | A2 |
| Proceso | cartel_security, political_risk | High | A2 |
| Pemex (official) | energy_infra | High | A2 |
| CFE (official) | energy_infra | High | A2 |
| Banxico Data | economy_markets | High | A1 |
| INEGI | economy_markets | High | A1 |
| SESNSP | cartel_security | High | A1 |

---

## The Root Problem

Two separate source lists exist:
1. `analyst/meta/sources-mexico.json` (83 sources, all themes) — **used by nothing** in the fetch pipeline
2. Global `sources.json` (145 sources, all regions) — **used by `collect.py`** for fetching

The Mexico desk has a complete source registry but no fetch pipeline reads it. The `mexico-daily-scan.py` script has its own hardcoded source list. Until the collector is pointed at the Mexico registry, ALL 83 sources remain LISTED-only regardless of how good they are.

**Fix:** Wire `sources-mexico.json` into `mexico-daily-scan.py` as its source configuration, replacing the hardcoded list. This is a config change, not a skill install — within autonomy boundaries.
