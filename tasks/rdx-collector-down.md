# RDX Weekly Brief — Collector Broken Since 2026-06-05

**Detected:** 2026-09-04 run (cron 0242e59b)
**Status:** OPEN — surfaced to principal, awaiting decision

## Root cause

`scripts/rdx_weekly_brief.py` (kept active) calls `scripts/rdx_collectors.py`
(`--all-daily`, `--all-creative`) every run. That collector was swept into
`archive/dormant-2026-06-02/scripts/` by the 2026-06-05 dormant-mode triage
(commit e443ea1, "archive remaining 195 scripts"), even though the brief
script itself was on the kept-active list.

Result: every run since logs `WARNING: can't open file rdx_collectors.py`,
then falls back to the newest feed files in
`analyst/knowledge/rdx_c4_supply/data_feeds/` — which are frozen at
**2026-06-03**. The brief then presents 3-month-old data as "this week."

## Evidence

- Last feed files: gdelt-sweep / job-signals / patents / trade-remedy /
  car-reports / epa-tri / osint-events all dated 2026-06-03.
- Exports 2026-06-08 through 2026-09-04 all lead with the same story:
  "$8.8B BAE Systems Holston AAP contract" (itself a Dec-2023 GDELT item
  collected Jun 3) framed as the week's dominant signal.
- LEO brief is NOT affected (leo_collectors.py still in scripts/, feeds
  fresh through 2026-08-31). DC brief runs on static registry files
  (different mechanism; feeds static since Jun 5, exports continue —
  worth a separate look).

## Options (for principal)

1. Restore `archive/dormant-2026-06-02/scripts/rdx_collectors.py` → `scripts/`
   (self-contained; stdlib only + BRAVE_API_KEY, which is present in .env;
   also scrapes news.google.com, t.me, usaSpending, EPA, Conflict Armament
   Research). Next Friday run would collect fresh data.
2. Keep archived; change brief to emit "no fresh signal" when feeds are
   stale (SOUL.md-compliant honesty) instead of recycling.
3. Pause the RDX cron until decided.
