# Technical Debt Ledger

> Living document. Updated whenever tech debt is discovered or resolved.
> DO NOT delete entries — mark as RESOLVED with date.

---

## Critical

| # | Debt | Discovered | Impact | Status |
|---|---|---|---|---|
| CD-01 | **Brain recall output was discarded** — `orchestrate.py` ran `brain.py recall` but never captured or piped output to the model | 2026-05-12 | Retrieval-conditioned cognition was zero | **RESOLVED** 2026-05-12 via `orchestrate.py` Step 0 + `analyze.py --recall` |
| CD-04 | **Recall query was too generic** — "yesterday's brief and overnight events" returned self-referential operational docs (score ~0.10) instead of brief content | 2026-05-12 | Retrieved content was operationally useless | **RESOLVED** 2026-05-12 via dynamic query built from yesterday's BLUF + key terms (score 0.28, confidence high) |
| CD-05 | **Recent briefs not in memory files** — May 10, 11 exec_summaries existed in `trevor-briefings/` but never reached `memory/DATE.md` → brain couldn't index them | 2026-05-12 | 2 days of brief content invisible to retrieval | **RESOLVED** 2026-05-12 via manual import + reindex |
| CD-06 | **No event-triggered escalation** — monitor detected events but never changed collection behavior | 2026-05-12 | Significance detection existed but zero behavioral response | **RESOLVED** 2026-05-12 via `collection_state.py` escalation flags + `continuous_monitor.py` escalation triggers (critical=2x, significant=1.5x, notable=1.25x region caps) |
| CD-07 | **No meta-cognition daemon** — self-assessment only happened when asked, no scheduled audit, no regression detection, no prompt injection from system health | 2026-05-12 | System couldn't observe or correct its own behavior autonomously | **RESOLVED** 2026-05-12 via `scripts/self_assessment.py` — scores 7 dimensions, detects regressions, injects findings into next brief prompt, wired as cron Step 10 |
| CD-02 | **No calibration feedback loop** — confidence bands were decorative, never checked against outcomes | 2026-05-12 | Epistemic maturity was zero | **RESOLVED** 2026-05-12 via `scripts/postdict.py` + `calibration-tracking.json`; prompt injection added 2026-05-12 via `analyze.py --calibration` |
| CD-03 | **No continuous collection** — everything was one daily batch run | 2026-05-12 | 24h gap between brief cycles with zero collection | **RESOLVED** 2026-05-12 via `scripts/continuous_monitor.py` hourly cron |

## High

| # | Debt | Discovered | Impact | Status |
|---|---|---|---|---|
| HD-01 | **Single-model pipeline** — Opus 4.7 handled ALL analysis (6 regions + exec + red team) | 2026-05-12 | $2.09/run vs $0.56/run with tiered routing | **RESOLVED** 2026-05-12 via `--tier2-model` flag in `analyze.py` + `orchestrate.py` |
| HD-02 | **No procedural memory at runtime** — skills in `brain/memory/procedural/` existed but were never read | 2026-05-12 | Skills were passive documentation only | **RESOLVED** 2026-05-12 via `scripts/procedural_memory_loader.py` + `analyze.py --procedural` |
| HD-03 | **Config was invalid and no one noticed** — I added `cron.jobs` which OpenClaw rejected | 2026-05-12 | Silent config failure | **MITIGATED** 2026-05-12 via `scripts/validate_config.py` |
| HD-04 | **tasks/news_analysis.md was 9 days stale** — workspace analysis file not synced from orchestrator output | 2026-05-12 | Downstream scripts read stale data | **RESOLVED** 2026-05-12 via `orchestrate.py` step 4b |
| HD-05 | **Routing contradiction** — ORCHESTRATION.md says primary=DeepSeek, but cron uses OpenRouter/Opus 4.7 | 2026-05-12 | Policy vs reality mismatch | **OPEN** — needs Roderick decision |
| HD-06 | **No event-driven behavior** — all collection is cron-scheduled batch only | 2026-05-12 | Can't respond to breaking events | **RESOLVED** 2026-05-12 via `continuous_monitor.py` hourly check |
| HD-07 | **No adaptive collection** — fixed per-region cap, no source utilization tracking | 2026-05-12 | Same collection intensity regardless of region activity | **RESOLVED** 2026-05-12 via `scripts/collection_state.py` + `collect.py --adaptive-caps` |
| HD-08 | **No source quality routing** — every feed fetched every run regardless of citation rate | 2026-05-12 | Wasted fetches on never-cited sources, no prioritization | **RESOLVED** 2026-05-12 via `collection_state.py --feed-priorities` + `collect.py --feed-priorities` (tier-3 skip after 5 zero-citation runs) |

## Medium

| # | Debt | Discovered | Impact | Status |
|---|---|---|---|---|
| MD-01 | **Zero local-language sources** — all 70+ sources are English | 2026-05-12 | Systematic blind spot on non-English intelligence | **RESOLVED** 2026-05-13 via 21 local-language sources added to `analyst/meta/sources.json` + `collect.py` `LOCAL_LANGUAGE_FEEDS` (11 languages: ar, fa, ru, zh, he, es, fr, ja, en). RSS feeds integrated into collection pipeline. |
| MD-02 | **Stripe is test mode** — can't process real subscriptions | 2026-05-12 | Product can't generate revenue | **OPEN** — needs live `sk_live_...` key |
| MD-03 | **Buttondown has 0 subscribers** | 2026-05-12 | Newsletter produced but nobody gets it | **OPEN** |
| MD-04 | **No technical debt tracking existed** — this is the first ledger | 2026-05-12 | Problems were discovered ad hoc | **RESOLVED** 2026-05-12 |
| MD-07 | **Collection quality never reached the analyst model** — collection_state.py tracked utilization but analyze.py never saw it | 2026-05-12 | Confidence bands were set without knowing collection quality | **RESOLVED** 2026-05-12 via `analyze.py --collection-state` + `build_collection_quality()` prompt injection |
| MD-05 | **Social log has 2 entries, both posted=False** — social_poster was broken/superseded | 2026-05-12 | Old social log is misleading | **MITIGATED** 2026-05-13 — replaced by `engagement-log.json` (32 history entries, 4 platforms tracked). Old `log.json` (2 entries) superseded by GenViral `log.json` (52 posts). Dashboard at `exports/social/dashboard.json`. |
| MD-06 | **GenViral performance log has 46 entries but no aggregate stats** | 2026-05-12 | Can't see which platform performs best | **RESOLVED** 2026-05-13 via `scripts/genviral_stats.py` — aggregates 52 posts by platform, date, hook type. Report saved to `exports/social/genviral-stats-2026-05-13.md`. Note: all 3 platforms (LinkedIn 18, Twitter 18, TikTok 16) show 0 views — GenViral doesn't push engagement metrics back into log. |

---

## Rules for this document

1. Discovered debts go to the bottom, then get promoted to severity sections
2. RESOLVED entries stay visible — do not delete
3. Each entry has a unique ID (CD = critical, HD = high, MD = medium)
4. When a fix is deployed, update the status, add resolution date, and link to the commit/PR

*Last updated: 2026-05-12*
