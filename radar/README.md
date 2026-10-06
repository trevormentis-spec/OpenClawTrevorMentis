# Security Intelligence & Buying-Intent Radar (US) — build workspace

Mission spec supplied by Roderick 2026-09-22 (§1–§62). This directory is the implementation.
Crons authorized for this system (explicit principal override of the AGENTS.md
"no new cron jobs" red line, 2026-09-22).

## Non-negotiable operating rules (from the spec)

- Two **independent** assessments per org: **SECURITY CHANGE** and **BUYING INTENT**.
  Never collapse into one score. Never imply prediction of violence.
- Fact / Inference / Unverified kept separate in every output.
- Primary sources first (SEC, court, regulatory, procurement, company filings).
- Level-3 sources (job boards, forums, social) are **leads only** — need corroboration.
- No personal threat dossiers. No private residential addresses. No profiling of
  employees, protesters, union members, activists, or critics (§39, §53).
- No autonomous contact with anyone (§54). Intelligence only.
- Optimise for **change / convergence / timing**, never for drama or volume (§30, §62).
- Suppress aggressively; "NOT FOUND" ≠ "DOES NOT EXIST" (§42, §52).

## Architecture

```
radar/
  README.md                     <- this file
  collectors/
    edgar_exec_security.py      <- Phase 1 / Project 1: DEF 14A exec-security disclosures
  data/
    exec_security_disclosures.jsonl   <- structured records (§4 schema)
    state.json                        <- incremental cursor / seen filings
  reports/                      <- daily + weekly outputs (§26, §27, §50)
```

## Build order (per §57–§60)

- **Phase 1** — SEC exec-security disclosures + spending history; security job postings;
  security leadership changes; WARN; CEO changes; major M&A; bankruptcy/restructuring.
- **Phase 2** — procurement; labor events; enforcement; activist campaigns; product crises.
- **Phase 3** — cross-source correlation, sequence detection, industry baselines,
  source-performance optimisation.

### First research project (§58) — Executive Security Disclosure Dataset
Tool: `collectors/edgar_exec_security.py`.
Method: EDGAR full-text search across DEF 14A for the §3 concept list, then fetch each
filing and extract the passages containing those concepts plus dollar amounts.
Output: one JSONL record per (company, executive, year) with YoY comparison where available.

### Second research project (§59) — Security Hiring Radar  [not yet built]
### Third research project (§60) — Security Inflection Radar  [not yet built]

## Classification vocabulary (§22) — use exactly these labels

- SECURITY CHANGE: `Minimal` | `Developing` | `Material` | `Major`
- BUYING INTENT: `None observed` | `Possible` | `Evidence present` | `Strong evidence`
- EVIDENCE CONFIDENCE: `Low` | `Medium` | `High`

Commercial relevance is always phrased "potentially relevant service categories" — never
"They need…" (§23).
