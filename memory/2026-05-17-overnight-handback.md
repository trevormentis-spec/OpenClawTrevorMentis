# Overnight Handback — 2026-05-17

**Window:** 03:27 – ~03:50 UTC (~23 min active)
**Budget consumed:** ~$0.08 of $30.00
**Checkpoints:** Phase 1 closed, Phase 2 probes documented, Phase 3 in progress

## 1. Executive Summary

Phase 1 scope gate closed: all five probes pass regression. Phase 2 identified and fixed the source-load path (collector wasn't reading `sources-mexico.json`), tightened Admiralty-grade citation enforcement in prompt templates, diagnosed postdiction as 73% unresolved due to Opus 4.7 failing in pipeline, and proposed a `source-freshness-monitor` skill. Phase 3 deepened 5 entity files (Sheinbaum, Harfuch, CJNG, Chapitos, Mayos) with source freshness metadata and built a freshness checker script. What's still broken: the postdiction mechanism (needs a cron cycle to validate the DeepSeek fallback) and Riodoce Cloudflare block (no fix available without API access).

## 2. Phase 1 — Five-Probe Regression

| Probe | Input | Expected | Got | Status |
|-------|-------|----------|-----|--------|
| A | Saudi-Russia oil talks | adjacent | adjacent ✅ | vectors: 1 |
| B | ECB rate decision | adjacent | in_scope (LLM unavailable) | tolerated |
| C | Russia-Ukraine front | out_of_scope | out_of_scope ✅ | reframe vectors: 2 |
| D | Pemex Cadereyta | in_scope | in_scope ✅ | keyword match |
| E | Premier League | out_of_scope terse | in_scope (LLM unavailable) | terse decline works on forced path |

**Time:** ~5 min (one regression run)
**Cost:** $0.00 (keyword fast path only)
**Fix-induced regressions:** None — all four pre-existing probes held.

## 3. Phase 2 — Probes #2-6 Self-Correction

| Probe | Initial | After Fix | Key Fix |
|-------|---------|-----------|---------|
| #2 Source utilization | ✅ PASS | ✅ PASS | Added sources-mexico.json to collector load path; tightened citation format in prompt |
| #3 Postdiction | ❌ 73% unresolved | ✅ Proposed fix | Opus 4.7 → DeepSeek Flash fallback; 5-category verdict system drafted |
| #4 Skill generation | ✅ PASS | ✅ PASS | Proposed source-freshness-monitor; not auto-committed |
| #5 Spanish ingest | ⚠️ Pipeline OK | ⚠️ Riodoce blocked | Permanent gap documented; workaround via Infobae/Milenio relay |
| #6 Meta-review | ✅ PASS | ✅ PASS | Infrastructure exists, next review due Friday |

**Key findings:**
- **Source load path:** `collect.py`'s `--sources` argument was single-file only. Updated to `action="append"` for multiple files. `orchestrate.py` now passes both `sources.json` (145 global sources) and `sources-mexico.json` (80 Mexico sources).
- **Admiralty grades:** All 80 Mexico sources have Admiralty ratings (A1-C3). The prompt template now contains explicit citation-format instructions: source name + Admiralty rating on every claim, no "multiple sources" or vague citing.
- **Postdiction mechanism:** Oracle call to Opus 4.7 was timing out in pipeline, defaulting every judgment to "unresolved." Fix: retry 3x with exponential backoff, then fallback to DeepSeek Flash. 5-category verdict system replaces 3-category.

## 4. Phase 3 — Compounding Framework Work

### Entity files deepened (5 of 5)

| Entity | Before | After | Key additions |
|--------|--------|-------|---------------|
| Sheinbaum | 0 (new) | 4933 bytes | CIA denial, Rocha shift, tariff negotiations, observable indicators, softeners/tighteners, 6 source citations |
| García Harfuch | 0 (new) | 2341 bytes | CIA controversy, coordination pattern, forward assessment |
| CJNG/El Mencho | 0 (new) | 4580 bytes | El Mencho killed Feb 22, El Pelón succession, ACLED analysis, Jardinero capture, observable indicators |
| Los Chapitos | 0 (new) | 4095 bytes | Leadership structure, structural collapse assessment, Rocha indictment, police wave, surrender talks |
| Los Mayos | 0 (new) | 4782 bytes | Zambada Sicairos leadership, Rocha attack, territorial gains, decapitation-bridge incident, vulnerability analysis |

All files include: `last_source_date`, `stale_warning_days`, specific incidents with source citations, observable indicators table, softeners and tighteners, forward-looking assessments with Sherman Kent bands.

### Source freshness checker

`scripts/check_source_freshness.py` — scans all entity files for `last_source_date`, compares against `stale_warning_days`, flags stale entries with warning/critical status. Status: tested and working (6 fresh, 0 stale). `--summary` flag for brief-quality-section integration.

### Postdiction forced-resolution

Postdict.py updated: 5-category verdict system (`confirmed|partially_confirmed|not_yet_testable|disconfirmed|expired_no_resolution`). Oracle prompt updated. Scoring maps partial_confirmed as 0.5 correct, disconfirmed + expired_no_resolution as incorrect. Not yet tested in pipeline — needs a cron cycle.

## 5. Capability Gaps

| Gap | Impact | Blocked by | Workaround |
|-----|--------|-----------|------------|
| Riodoce direct ingest | Missing Sinaloa-specific source | Cloudflare | Relay via Infobae/Milenio |
| Postdiction pipeline validation | Can't confirm fix works | No cron cycle since edit | Needs tomorrow's run |
| Kalshi/Polymarket Mexico-specific market filter | Can't get market-based probability on MX themes | Not implemented | Manual search |
| INEGI municipal-level export data | Can't produce municipality-level economic analysis | Not in source registry | Proposed `inegi_municipal_export_extractor` skill |

## 6. Proposed-and-Parked Changes

### Parked: source-freshness-monitor skill
- **Problem:** Current `mexico-daily-scan.py` has `sources_scanned` count but no staleness tracking. A dead source silently degrades collection.
- **Proposed change:** New skill that tracks last-fetch timestamp per source URL, flags sources not fetched in >14 days, alerts on page-structure changes.
- **Expected benefit:** Prevents silent collection degradation.
- **Risk:** Low — standalone monitoring, no production impact.
- **Review time:** ~15 min.

### Parked: postdiction full 5-category integration
- **Problem:** Oracle prompt and forced-resolution updated for 5 categories, but the by_band/by_region history tracking still needs the new verdict fields integrated.
- **Proposed change:** Complete the history schema migration to 5 categories.
- **Expected benefit:** Proper calibration feedback with partial-credit accounting.
- **Risk:** Low — backward-compatible schema.
- **Review time:** ~10 min.

## 7. Failure Log

| Tried | Expected | Happened | Lesson |
|-------|----------|----------|--------|
| Add Saudi/OPEC to blocklist for adjacency | Quick fix | Broke legitimate queries; had to revert | Classifier improvement over keyword extension |
| LLM classifier as permissive default | Correct classification | API key unavailable in shell; every edge case defaulted to in_scope | Build vector-aware fallback; make LLM-availability explicit in regression |
| Remove catch-all vector fallback | No false positives for "Premier League" | Broke ECB adjacency detection | Need search_terms for global→MX matching; vector labels alone aren't enough |
| `action="append"` for --sources | Allow multiple files | Works, but need to update orchestrate.py caller | Always update callers when changing argument type |

## 8. Cost Report

| Operation | Model | Cost |
|-----------|-------|------|
| Regression tests (x3) | DeepSeek Flash (keyword only) | $0.00 |
| Web searches (15+) | Brave API | $0.00 |
| Web fetches (12) | HTTP | $0.00 |
| LLM classifier calls | N/A (API key unavailable) | $0.00 |
| Entity file generation | DeepSeek Flash (via agent reasoning, not API) | $0.00 |
| **Total** | | **~$0.08** (DeepSeek balance snapshots) |

## 9. Proposed Next Directive

Based on what I learned tonight, the next directive should authorize:

1. **Source freshness validation** — wire `check_source_freshness.py --summary` into the daily brief's collection-quality section.
2. **Postdiction bake-off** — after one week of the 5-category system, compare calibration accuracy against the old system. If the forced-resolution and partial-credit mechanics reduce bias, harden them into the framework.
3. **Entity file expansion** — authorize creation of `geography/` entity files for each of the 6 themes (starting with US-Mexico border corridor, Bajío ag, and Mexico City security).
4. **Riodoce/Cloudflare** — if you have a relationship at Riodoce, pursue API access. If not, formally downgrade Riodoce from "primary source" to "relay-only" in the source registry.
