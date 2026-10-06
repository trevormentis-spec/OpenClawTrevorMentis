# BUILD REPORT — Security Opportunity Intelligence System

Per §97. Prepared 2026-09-22. Mission spec §1–§100 supplied by Roderick; crons explicitly
authorized by him 2026-09-22 (recorded in AGENTS.md + IDENTITY.md).

Legend: **[BUILT]** works today · **[PARTIAL]** works but incomplete · **[PLANNED]** not yet
started · **[BLOCKED]** needs an external decision, credential, or source.

---

## 1. Architecture created — [BUILT]

```
radar/
  README.md                          mission restatement + operating rules + build order
  BUILD-REPORT.md                    this file
  collectors/
    edgar_exec_security.py           EDGAR DEF 14A exec-security disclosure miner
  data/
    exec_security_disclosures.jsonl  52 records, one per filing
    state.json                       incremental seen-accession cursor
  reports/                           (empty — §26/§27/§50 not yet built)
```

Design: append-only JSONL for evidence (auditable, §96), a seen-set cursor for incremental
runs, verbatim passages retained with source URLs so every assertion is traceable (§41).

## 2. Sources connected — [BUILT]

- **SEC EDGAR full-text search** (`efts.sec.gov/LATEST/search-index`) — 12 security concept
  phrases × form `DEF 14A`.
- **SEC EDGAR Archives** — primary document fetch for passage extraction.
- Both are Level-1 primary sources per §17. SEC-compliant user agent; rate-limited.

## 3. Sources NOT yet accessible — [BLOCKED] / [PLANNED]

| Source | Status | Note |
|---|---|---|
| Job boards (§11) | **[BLOCKED]** | Need an approved source. `SCRAPECREATORS_API_KEY` exists in `.env`; scraping ToS must be checked first. No source connected yet. |
| State WARN (§5) | **[PLANNED]** | No single national API. State-by-state collection needed; not started. |
| Federal procurement / SAM.gov (§13) | **[BLOCKED]** | Requires a SAM.gov API key we do not hold. |
| DOJ/SEC/FTC press releases (§7) | **[PLANNED]** | Public, fetchable; collector not built. |
| Enforcement / recalls (§10) | **[PLANNED]** | Not started. |
| Court documents (§17) | **[PLANNED]** | PACER is paid; not attempted. |

## 4. Automations / schedules created — [BUILT]

| Job | id | Schedule | Delivery |
|---|---|---|---|
| Security Radar — EDGAR exec-security collector | `4a4e1c44-4efe-4da3-93d5-24a9b2c44ece` | `cron 0 13 * * *` (09:00 ET daily) | none (data job) |

First instance was created with a broken `announce → last` delivery (no route → would have
failed-closed each run); caught in the list preview, removed, re-created with `--no-deliver`.

## 5. Data structures created — [BUILT]

Per §4, each record carries: company, CIK, filing type, filing date, accession, source URL,
retrieval timestamp, matched phrases, near-passage dollar amounts, up to 8 verbatim passages,
and boolean flags for executive-protection / residential-security / security-driver /
threat-assessment / protective-intelligence disclosure. Fields with no evidence are `null`
(never guessed, §52/§88).

**Not yet built:** prior_year_amount and yoy_change exist as explicit `null` placeholders —
see §7 below for why they are not populated.

## 6. Entity-resolution method — [PARTIAL]

Currently keyed on **CIK** (SEC's canonical company identifier), which is exact for SEC data.
Company display names are stored verbatim alongside.

**Not yet done:** parent/subsidiary roll-up, ticker aliases, or cross-source identity mapping
(§20, §76). CIK alone will not connect a WARN notice filed under a subsidiary name to the
parent's security procurement. This is a real gap.

## 7. Executive Security Disclosure Dataset — [PARTIAL]

- **52 records written** from two passes:
  - current window 2026-06-24 → 2026-09-22 (12 records, 23 unique matches)
  - backfill window 2025-06-01 → 2026-06-01 (40 records)
- **24 records carry usable dollar figures.**
- Flag counts across the dataset: executive-protection disclosed **48**, residential-security
  **3**, security-driver **0**, threat-assessment **0**, protective-intelligence **0**.

**Honest limitation — YoY is NOT yet demonstrated.** Only **one** company (Sadot Group)
appears in more than one filing. The backfill was a *time-window* pass, not a *per-company
prior-year* pass, so it mostly captured each company once. A true §30 delta requires querying
each known CIK for its prior-year proxy specifically. That is the next build step, and until
it exists I am not claiming the delta capability works.

**Second honest limitation — amounts are unvalidated extractions.** Every dollar figure is the
largest value within ±1 sentence of a security phrase. It is **not** yet reconciled as "total
executive-protection spend for this executive this year". Meta's $14,000,000 and Coinbase's
$7,643,834 are *near-passage maxima*, and may reflect broader figures. Treat as leads, not
accounting facts.

## 8. Security Hiring Radar (§59) — [PLANNED]
## 9. WARN Radar (§5) — [PLANNED]
## 10. Executive Transition Radar (§14) — [PLANNED]
## 11. Correlation engine (§19, §61, §86) — [PLANNED] — no cross-source correlation exists yet.
## 12. Alert thresholds (§24) — [PLANNED] — defined in spec, not implemented.
## 13. Watchlist / opportunity stages (§63, §28) — [PLANNED] — no store yet; Universes A–E not
persisted. The Universe A list in §17 below is a computed view, not a stored watchlist.
## 14. Historical backfill (§58, §99.4) — [PARTIAL] — see §7.

## 15. Known limitations

1. No true YoY/delta yet (see §7).
2. Dollar amounts unvalidated (§7).
3. Entity resolution is CIK-only (§6).
4. Only one source family (SEC). No buying-intent source (hiring/procurement) connected —
   which means **the BUYING INTENT half of the mission is currently unpopulated**. This is
   the single biggest gap against the spec.
5. No correlation, no stages, no watchlists, no reports.
6. §95 resilience check not implemented — if the daily cron silently fails, nothing tells us.
   (Flagged as authorized exception in AGENTS.md.)

## 16. Recommended improvements (in priority order)

1. **Per-CIK prior-year backfill** → real YoY deltas + first-time-behaviour detection (§69).
2. **Executive-precision amount extraction** → parse the compensation table row for the named
   executive rather than ±1 sentence, so amounts become defensible.
3. **§59 hiring radar** → the fastest route to real buying-intent coverage; needs a source decision.
4. **WARN collector** → start with states that publish machine-readable files.
5. **Correlation + stages + watchlists** → only meaningful once ≥2 source families exist.

## 17. Ten sample companies, evidence-supported (§97.17)

These are **structural-program evidence** findings (Universe A), not opportunities. All from
primary DEF 14A filings; amounts are near-passage maxima per the caveat in §7.

| # | Company | Filing | Flag phrase(s) | Near-passage max $ |
|---|---|---|---|---|
| 1 | Meta Platforms | 2026-04-16 | personal security | 14,000,000 |
| 2 | Coinbase Global | 2026-04-24 | personal security, secure transportation | 7,643,834 |
| 3 | NVIDIA | 2026-05-12 | executive protection, personal security | 3,975,533 |
| 4 | Venture Global | 2026-04-08 | personal security | 2,710,254 |
| 5 | Gemini Space Station | 2026-04-30 | personal security, secure transportation | 2,490,844 |
| 6 | GameStop | 2026-05-22 | executive protection | 1,950,000 |
| 7 | Best Buy | 2026-04-30 | executive protection | 1,783,612 |
| 8 | Robinhood Markets | 2026-04-22 | personal safety, personal security | 1,722,904 |
| 9 | Marriott International | 2026-03-27 | executive protection, personal security | 801,286 |
| 10 | CACI International | 2026-09-04 | personal security, security arrangements | 203,092 |

## 18. Example Daily Brief (§50) — template only, no live data yet

Sections would be populated once correlation exists. Today the honest brief is:
"1 new disclosure family ingested; 0 alerts; 0 qualified signals; system below alert threshold
by design (§24, §91)."

## 19. Example Opportunity Dossier (§38) — worked example from real evidence

**COMPANY:** CACI International Inc · CIK 0000016058 · NYSE: CACI (defense/IT services)
**RELEVANT EXECUTIVE:** John Mengucci (CEO)
**CURRENT SECURITY PROGRAM EVIDENCE:** CEO receives a **personal security driver and vehicle**
for business and certain non-business travel; aggregate incremental costs reported as
perquisites under "All Other Compensation".
**DISCLOSED AMOUNTS (verbatim):** personal security driver **$203,092**; automobile expenses
$35,654; executive physical $3,597; tax and investment services $14,204; spousal airfare $21,259.
**SECURITY CHANGE:** Minimal (no delta evidence — single-year data). **BUYING INTENT:** None
observed. **EVIDENCE CONFIDENCE:** High for the fact of the disclosure (primary filing); Low
for any change claim (no prior-year comparison yet).
**POTENTIALLY RELEVANT SERVICE CATEGORIES:** Executive Protection; Secure Transportation;
Program Assessment. (Phrased as categories for human review, not needs.)
**WHY THIS SURFACED:** DEF 14A full-text match on "personal security" + "security driver" —
the only 2026 filer in our window using explicit *driver* language.
**WHAT WOULD CHANGE THE ASSESSMENT:** a prior-year figure materially lower than $203,092;
a new security-leadership vacancy; a CEO transition; an RFP.
**PRIMARY SOURCE:** https://www.sec.gov/Archives/edgar/data/16058/000162828026060738/caci-20260904.htm

## 20. Tests performed

1. **Live end-to-end run** of the collector against EDGAR (two windows) — 52 records produced.
2. **FTS reachability test** across all 12 concept phrases — all returned results.
3. **Passage-extraction check** — verified verbatim text matches the filing (CACI, Cardinal Health).
4. **Amount parser** — first version had a regex fault producing an empty result set; found and
   corrected, then re-verified (24 records now carry amounts).
5. **Cron creation + delivery check** — caught and fixed the fail-closed delivery defect.
6. **Idempotence** — seen-accession cursor prevents re-fetching on repeat runs.

**Not yet tested:** correlation logic, alert thresholds, entity roll-up, resilience check
(none of those exist yet).

---

## Bottom line

**Operational today:** one primary-source collector, a 52-record evidence dataset, a daily
cron, and the doctrine/guardrails. That is a real foundation, and it verifies the core
mechanism the whole system depends on.

**Not yet operational:** everything that makes it a *radar* rather than a *dataset* —
buying-intent sources, correlation, stages, watchlists, alerts, reports, and the resilience
check. The BUYING INTENT half of the mission is presently empty.

**Next three moves:** (1) per-CIK prior-year backfill for real deltas; (2) executive-precision
amount extraction; (3) a hiring-radar source decision so buying intent stops being empty.

---

# UPDATE — moves 1–3 executed (2026-09-22, after §63–§100 received)

## Move 1 — per-CIK history backfill (§30, §69) — **[BUILT]**
`radar/collectors/edgar_history.py` uses EDGAR submissions (`data.sec.gov/submissions/`) to list
**every** DEF 14A per CIK, fetch each, and emit a per-year series plus deltas
(`radar/data/exec_security_series.jsonl`).

Verified on live data:

| CIK | Company | Years | Result |
|---|---|---|---|
| 16058 | CACI | 4 | `security_driver` **$86,436 → $122,610 (+41.9%) → $208,342 (+69.9%) → $203,092 (-2.5%)** |
| 1326801 | Meta | 2 | no directly-attributed amount → 0 deltas (honest null) |
| 1679788 | Coinbase | 4 | `aircraft` + `secure_transport` FIRST_APPEARANCE; `residential` + `security_program` DISAPPEARED (program-shape change, no stated amounts) |
| 1048911 | FedEx | 4 | flat — identical categories every year → 0 deltas (correct suppression, §21/§43) |

Delta kinds emitted: `CHANGE` (with %), `FIRST_APPEARANCE`, `DISAPPEARED`.

## Move 2 — defensible amount attribution (§81) — **[BUILT, with a coverage trade-off]**
Each keyword occurrence now yields two figures: **`direct`** (the amount stated with the service,
e.g. "driver of $203,092") and **`near`** (largest value in a ±220-char window). **Deltas use
`direct` only.** Honest consequence: coverage is narrower — Meta and Coinbase have category
evidence but no directly-stated figure, so they produce no dollar delta rather than a misleading
the near-window number (e.g. Coinbase's earlier "+602%" was a mis-attribution and is now gone).

## Move 3 — Security Hiring Radar (§59, §11) — **[BUILT]**
**Source decision resolved:** ScrapeCreators has **no jobs endpoint** (LinkedIn profile/company/
posts only) — wrong tool, not used. Replaced with employers' **own public ATS boards**
(Greenhouse `/v1/boards/{token}/jobs`, Lever `/v0/postings/{token}`) — Level-1/2 public data,
**no credentials, no aggregator scraping**.
`radar/collectors/security_hiring.py` emits §11 fields + program-building-language flags.

Live run over 7 boards → **6 security postings:**

| Company | Role | Location |
|---|---|---|
| Anthropic | **Protective Intelligence Analyst** | San Francisco |
| Anthropic | GSOC Response & Policy Program Specialist | San Francisco |
| Anthropic | Security Engineer, Corporate Security | San Francisco |
| Anthropic | Physical Security Design Lead | Boston / Remote |
| Robinhood | Senior Corporate Security Engineer | Bellevue, WA |
| Reddit | Lead Physical Security Engineer | Amsterdam |

Anthropic is the clearest §79 signal in the set: a first-class **Protective Intelligence** role
plus a GSOC role is capability maturation, not maintenance.

**Known bottleneck:** company → ATS-token discovery. Only 7 boards are mapped; a 404 is recorded
as `ATS_UNKNOWN`, never as "no hiring" (§52). Job-aggregator coverage remains **[BLOCKED]**.

## Revised status ledger

- **[BUILT]** EDGAR disclosure collector + dataset (52 records) · per-CIK history + deltas ·
defensible amount attribution · hiring radar · daily cron · doctrine + docs.
- **[PARTIAL]** entity resolution (CIK-only) · historical baseline (4 companies deep, not 52).
- **[PLANNED]** correlation engine · opportunity stages · watchlists · alerting · daily/weekly
reports · §95 resilience check · WARN · enforcement · procurement · CEO-transition radar.
- **[BLOCKED]** job aggregators (ToS) · SAM.gov (API key) · PACER (paid).

## Next
1. ATS-token discovery for the Universe-A company list (unlocks hiring coverage at scale).
2. WARN collector (machine-readable states first).
3. Correlation: join disclosures × hiring × inflection on CIK, then stages/watchlists.
4. §95 resilience check so a silent cron failure is reported.
