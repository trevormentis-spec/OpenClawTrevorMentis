# Daily Intel Brief — Product Template

The structure of every daily product. The assembler renders this; this
file documents what each section looks like and why each piece is there.

---

## Cover page

```
[Classification banner]

         TREVOR DAILY INTELLIGENCE BRIEF
                {Long date}
            DTG {YYYYMMDDThhmmZ}

   ┌──────────────────────────────────────────────┐
   │  BLUF                                         │
   │  {one-sentence headline judgment, calibrated} │
   │                                               │
   │  {two-to-three-sentence context}              │
   └──────────────────────────────────────────────┘

                                          Page 1 / N
```

---

## Executive Summary (page 2)

```
EXECUTIVE SUMMARY

1. {EXEC-1 statement} ({band}; {pct}% / 7d) [{region}]
2. {EXEC-2 statement} ({band}; {pct}% / 7d) [{region}]
3. {EXEC-3 statement} ({band}; {pct}% / 7d) [{region}]
4. {EXEC-4 statement} ({band}; {pct}% / 7d) [{region}]
5. {EXEC-5 statement} ({band}; {pct}% / 7d) [{region}]

Methodology: NATO Admiralty source rating, Sherman Kent probability bands,
ACH on at least one regional KJ. Red-team challenge captured at Annex C
where present. Calibration window: 7 days; predictions are scored at the
next monthly review.
```

---

## Regional sections (5×)

Each regional section follows this layout, in pages 3 onward.

```
REGION: {Region label}              {Incident count} incidents in 24h to {DTG} UTC

[Map figure — full width]

NARRATIVE
{2 to 3 paragraphs from analyst output, ~200 words. Calibrated language.
Cites incident pin numbers parenthetically: "(pin 0014)".}

INCIDENTS
1. {DTG} | {country} | {category}
   {headline}
   {one-sentence summary, source codes attached: "(Reuters B2; Al Jazeera C2)"}
2. ...
3. ...
4. ...
5. ...

KEY JUDGMENTS

KJ-{REGION-1} ({band}; {pct}% / 7d):
  {statement}
  Evidence: {incident IDs}
  Indicators: would soften if {…}; would tighten if {…}

KJ-{REGION-2} ({band}; {pct}% / 7d):
  {statement}
  Evidence: {incident IDs}
  Indicators: would soften if {…}; would tighten if {…}

[KJ-{REGION-3} if present]

[Optional: SCENARIOS block if region has a structural fork today —
 four-bucket spread per analyst/playbooks/scenario-triage.md]
```

---

## Global Finance section

Same shape but the map is replaced by the 2×2 chart panel and the
incidents schema is interpreted as market events:

```
GLOBAL FINANCE                       {Incident count} market events in 24h to {DTG} UTC

[2×2 chart panel — full width]

NARRATIVE
{2 to 3 paragraphs. Connects FX / equities / commodities / yields where
the linkages matter. Notes any cross-asset divergence.}

MARKET EVENTS
1. {DTG} | {market} | {category}
   {headline}
   {one-sentence summary, source code attached}
2. ...
...

KEY JUDGMENTS

KJ-FIN-1 ({band}; {pct}% / 7d):
  {statement}
  Evidence: {incident IDs}
  Indicators: would soften if {…}; would tighten if {…}

[KJ-FIN-2, KJ-FIN-3 as applicable]
```

---

## Annex A — Sources & methodology

```
ANNEX A — SOURCES & METHODOLOGY

Sources used in this brief (count of citations in parens):

- Reuters World (12)
- AP World (8)
- ...
- UKMTO (3)

Source ratings: NATO Admiralty Code (A1 ... F6) per
skills/source-evaluation. Confidence bands: Sherman Kent. Predictions
are 7-day, falsifiable, scored at the monthly calibration review.

Collection gaps in this window:
- {gap 1}
- {gap 2}
```

---

## Annex B — I&W status board

```
ANNEX B — INDICATORS & WARNINGS — STATUS BOARD

Standing indicators that fired or moved in the last 24h:

| Topic       | Indicator                          | Status      | Direction    | Action          |
|-------------|------------------------------------|-------------|--------------|------------------|
| Hormuz      | UKMTO advisory > LEVEL 3           | Fired (T-2h)| Confirms H1  | Tightened to HL  |
| ...         | ...                                | ...         | ...          | ...              |

Indicators we are still watching for (no movement in window):

| Topic       | Indicator                          | Watching where      | Lead time |
|-------------|------------------------------------|---------------------|------------|
| ...         | ...                                | ...                 | ...        |
```

---

## Annex C — Red-team note (if present)

The red-team note from `analysis/red_team.md`, embedded verbatim. ~300
words. Concludes with a one-sentence verdict.

---

## Annex D — Calibration log (monthly)

Empty in the daily product. Populated at the monthly calibration
review by walking back through 30 days of `prediction_pct` values and
scoring them against what actually happened. The 30-day Brier score is
displayed on the cover of the next month's first daily.

---

## Length budget

| Section                          | Target  | Hard cap |
|----------------------------------|---------|----------|
| Cover                            | 1 page  | 1 page   |
| Executive Summary                | 1 page  | 1 page   |
| Each regional section            | 1.5 pp  | 2 pp     |
| Annex A — Sources                | 0.5 pp  | 1 page   |
| Annex B — I&W board              | 0.5 pp  | 1 page   |
| Annex C — Red-team               | 0.5 pp  | 1 page   |
| **Total**                        | **~10 pp** | **12 pp** |

The principal reads this in five minutes if it is well-structured. They
read it in fifteen if it is not, then stop reading the daily within a
week. Hold the length budget.
