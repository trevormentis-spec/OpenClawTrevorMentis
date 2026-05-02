---
name: daily-intel-brief
description: Produce Trevor's Daily Intelligence Brief — a dated, structured intelligence product with six regional sections (Europe, Asia, Middle East, North America, South & Central America incl. Caribbean, Global Finance), each carrying calibrated key judgments and prediction bands. Trigger this skill on "daily brief", "morning brief", "today's brief", "INTSUM", "daily intel", "Trevor brief", "run the brief", "kick off today's product", "where are we today", or any standing-product request that implies the daily cadence. Composes existing analyst skills (sat-toolkit, source-evaluation, indicators-and-warnings, bluf-report, geospatial-osint, chartgen, mermaid, pdf-report) and the analyst/ scaffold; routes analysis to deepseek-v4-pro per ORCHESTRATION.md escalation criteria. Do not use this skill for ad-hoc single-region deep dives, single-incident analysis, or non-security topics — those should run through the standard analytic-workflow playbook.
metadata:
  trevor:
    requires:
      bins: [python3, mmdc, node]
      env: [DEEPSEEK_API_KEY]
      env_optional: [MAPBOX_TOKEN, CHARTGEN_API_KEY]
    composes:
      skills:
        - sat-toolkit
        - source-evaluation
        - indicators-and-warnings
        - bluf-report
        - geospatial-osint
        - chartgen
        - mermaid
        - pdf-report
      analyst_assets:
        - analyst/playbooks/analytic-workflow.md
        - analyst/playbooks/scenario-triage.md
        - analyst/playbooks/quality-gates.md
        - analyst/templates/bluf-report.md
        - analyst/templates/indicators-and-warnings.md
        - analyst/templates/ach-matrix.md
        - analyst/meta/sources.json
---

# Daily Intelligence Brief

A standing product, not a one-off. Run once per day at the user's chosen
hour (default: 06:30 local). Every run produces the same shape so that
the principal recognises it on sight — same regions, same order, same
field structure, same length budget. Variation is in the content, not
the form.

## Why this is a discrete skill

`analyst/playbooks/analytic-workflow.md` covers single-question
assessments well. The daily brief is a different shape: multiple
parallel mini-assessments (one per region), strict length budget,
ruthless cadence. Trying to bend the analytic-workflow playbook into
this shape every morning loses time and drift-prone consistency.

This skill **orchestrates three subagents** — collector, analyst,
visuals — and assembles their outputs into the daily product. Each
subagent has its own prompt under `agents/` so the work parallelizes.

## Product specification

A finished daily brief is a **PDF** (with the source `.docx` retained for
revision) containing, in this exact order:

1. **Cover page** — date, classification banner ("UNCLASSIFIED // FOR
   OFFICIAL USE — TREVOR DAILY"), product name, BLUF.
2. **Executive summary** — five key judgments. Each has a Sherman Kent
   verbal anchor and a 7-day prediction percentage.
3. **Six regional sections, in fixed order:**
   1. Europe
   2. Asia
   3. Middle East
   4. North America
   5. South & Central America (incl. Caribbean)
   6. Global Finance
4. **Annex A — sources & methodology** (one line per source feed).
5. **Annex B — I&W status board** (running indicators that have fired
   or moved since yesterday).

Each regional section is structured per `references/product-template.md`
(map, narrative, 3–5 incidents, 2–3 numbered key judgments with
prediction bands). The Global Finance section swaps the map for a chart
suite per `references/visual-spec.md`.

Length budget: **8–12 pages**. If you blow past 12, you cut; you do not
ship a 16-page "daily" brief.

## Workflow (orchestrator's view)

You are the orchestrator. Run the steps below in order. Steps 2–4 can
run their three subagents in **parallel** — the data hand-off is
filesystem-based and they don't block each other once collection is
done.

### Step 0 — Frame the day

Read the brain's last 48h of episodic memory:

```bash
python3 brain/scripts/brain.py recall "yesterday's brief and overnight events"
```

Then create today's working directory:

```bash
WD=~/trevor-briefings/$(date -u +%F)
mkdir -p "$WD"/{raw,analysis,visuals,final}
```

Record `00-framing.md` in `$WD` per `analyst/playbooks/analytic-workflow.md`
Phase 0. The framing for the daily product is constant: *"Provide
Trevor's principal with the most decision-relevant security and
financial picture from the last 24h, structured for ~5 minutes of
read time."*

### Step 1 — Spawn the collector subagent

Read `agents/collector.md`. Spawn a subagent with that prompt. Hand it:

- `$WD/raw/` (output dir)
- Today's UTC date
- `analyst/meta/sources.json` (the durable source registry)

It produces `$WD/raw/incidents.json` — a normalised list of
security-incident items tagged by region, each with a NATO Admiralty
reliability/credibility code attached at point of capture (per
`skills/source-evaluation`).

Wait for completion before Step 2 — the analyst needs the full incident
set before scoring.

### Step 2 — Spawn the analyst subagent

Read `agents/analyst.md`. Spawn a subagent with that prompt. Hand it:

- `$WD/raw/incidents.json`
- `$WD/analysis/` (output dir)
- The model identifier: **`deepseek/deepseek-v4-pro`** (escalation tier
  per `ORCHESTRATION.md` — the daily product is a high-stakes principal
  product and qualifies for V4 Pro).

The analyst calls the DeepSeek Direct API once per region (six calls)
plus once for the executive summary, producing
`$WD/analysis/<region>.json` and `$WD/analysis/exec_summary.json`. Each
file contains the regional narrative, 2–3 key judgments with Sherman
Kent bands, and per-judgment prediction percentages over a 7-day
horizon.

### Step 3 — Spawn the visuals subagent

Spawn this subagent **in parallel with Step 2** (it doesn't need
analyst output for the maps; it only needs incident locations from
`$WD/raw/incidents.json`).

Read `agents/visuals.md`. Hand it:

- `$WD/raw/incidents.json`
- `$WD/visuals/` (output dir)

It produces:

- `visuals/map_<region>.png` × 5 (the five geographic regions; finance
  uses charts instead).
- `visuals/finance_charts.png` — composed chart panel for the Global
  Finance section (FX, oil, equities, sovereign yields).
- `visuals/relationships_<region>.png` — Mermaid-rendered actor/event
  graph for the most active region of the day.

Visual generation routes through:

- `skills/geospatial-osint` for regional maps.
- `skills/chartgen` (ChartGen API) for the finance suite.
- `skills/mermaid` for the relationships diagram.

### Step 4 — Quality gates

Run `analyst/playbooks/quality-gates.md` against the assembled
analysis. If a gate fails, **fix it before Step 5** — do not ship and
footnote. Particular attention:

- **Gate 2 (calibration):** every key judgment has both a Sherman Kent
  band *and* a numeric prediction band. The two must agree (verbal
  anchor matching numeric range per
  `skills/source-evaluation`).
- **Gate 3 (source hygiene):** no single-source key judgment unless
  flagged as such in the JSON.
- **Gate 5 (red-team pass):** at least one regional KJ has been
  red-teamed; record the challenge in `$WD/analysis/red_team.md`.

### Step 5 — Assemble

Run the assembler:

```bash
python3 skills/daily-intel-brief/scripts/build_pdf.py \
  --working-dir "$WD" \
  --template skills/daily-intel-brief/templates/daily-product.html \
  --out-pdf "$WD/final/brief-$(date -u +%F).pdf"
```

The assembler builds the structured JSON expected by `skills/pdf-report`
and invokes its renderer. The DOCX equivalent is produced in the same
step via `python-docx` and saved alongside.

### Step 6 — Archive and deliver

1. Append a one-paragraph entry to `memory/$(date -u +%F).md` per
   `AGENTS.md` Memory section. Capture: top 5 KJs, any I&W indicators
   that fired, any new sources promoted to durable list.
2. Refresh the brain index:

   ```bash
   python3 brain/scripts/brain.py reindex
   ```
3. Deliver to the principal:
   - Default channel: AgentMail (`skills/agentmail`) to the address in
     `~/.openclaw/openclaw.json` → `trevor.principal_email`.
   - Confirm send before pushing — agentmail is an external action.

## Subagent boundaries

The point of the three subagents is parallelism + isolation, not just
delegation. Keep each subagent's job tight:

| Subagent  | Reads                       | Writes                         | Does NOT |
|-----------|-----------------------------|--------------------------------|----------|
| Collector | RSS, web, sources.json      | raw/incidents.json             | analyse, judge, predict |
| Analyst   | raw/incidents.json          | analysis/<region>.json         | re-collect, draw maps |
| Visuals   | raw/incidents.json, analysis/ | visuals/*.png                | re-analyse, write narrative |

When a subagent breaks discipline (analyst tries to recollect, visuals
tries to write narrative), the orchestrator calls it back. This isn't
bureaucratic — overlap is the failure mode that turns a 2-hour daily
into a 6-hour one.

## Operating guidance

**On the prediction percentages.** The analyst is instructed to return
calibrated 7-day probabilities, not theatrical ones. A prediction of
"85%" means the analyst would take a bet at 85:15. If V4 Pro returns
suspiciously round, high-confidence numbers across the board (e.g.
everything in 80–95%), that's a calibration smell — surface it in the
hand-off to the user. Over-confidence is the most common failure mode
of LLM analysis and the daily product is the worst place to let it
quietly compound.

**On the regional taxonomy.** The collector and analyst share
`references/regions.json`. Don't ad-hoc reassign countries — Türkiye is
in Middle East here (analyst convention), Russia is in Europe, Mexico
is in North America, Cuba/DR/Haiti are in South & Central America. If
the principal wants a reclassification, edit `regions.json`; don't
argue at runtime.

**On reruns.** If the principal says "rerun the brief" later in the
day, do **not** delete the working directory. Spawn the collector
again into `raw/incidents-<HHMM>.json` and re-run the analyst on the
union of all incidents. Yesterday's brief stays in
`~/trevor-briefings/$(date -u -d yesterday +%F)/` for retrospective
calibration.

**On API keys.** The analyst expects `DEEPSEEK_API_KEY`. The visuals
subagent expects `MAPBOX_TOKEN` (optional — falls back to OSM tiles)
and `CHARTGEN_API_KEY` (optional — falls back to matplotlib). If
required keys are missing, **fail loudly at Step 0** rather than
producing a degraded product silently. Tell the principal exactly which
env var is missing.

**On vocabulary.** TREVOR brand voice (`ORCHESTRATION.md`):
methodology, disclosure, candor, completeness, confidence, indicator,
posture, finding, assessment. Avoid: solution, leverage, unlock,
empower, disrupt, game-changing.

## Files in this skill

```
skills/daily-intel-brief/
├── SKILL.md                              # this file
├── _meta.json
├── README.md
├── agents/
│   ├── collector.md                      # subagent prompt: news harvest
│   ├── analyst.md                        # subagent prompt: DeepSeek V4 Pro analysis
│   └── visuals.md                        # subagent prompt: maps / charts / diagrams
├── playbooks/
│   ├── daily-cadence.md                  # the 90-minute daily run
│   └── escalation-criteria.md            # when the daily flips into a special
├── references/
│   ├── regions.json                      # country → region taxonomy
│   ├── product-template.md               # the daily product structure (per section)
│   ├── deepseek-prompts.md               # per-region prompt templates for V4 Pro
│   └── visual-spec.md                    # what each visual must show
├── scripts/
│   ├── orchestrate.py                    # entrypoint that walks Steps 0–6
│   ├── collect.py                        # collector implementation
│   ├── analyze.py                        # DeepSeek V4 Pro client + prompt assembly
│   ├── build_visuals.py                  # invokes geospatial-osint, mermaid, chartgen
│   └── build_pdf.py                      # assembles the structured JSON for pdf-report
└── templates/
    ├── daily-product.html                # Jinja2 template for pdf-report
    └── daily-product.md                  # markdown mirror (working draft + DOCX source)
```

## See also

- `analyst/playbooks/analytic-workflow.md` — the single-question variant
- `analyst/playbooks/quality-gates.md` — applied at Step 4
- `analyst/playbooks/scenario-triage.md` — used by the analyst when a
  region has a structural fork (rare in a daily, common in a special)
- `ORCHESTRATION.md` — model routing canon (V4 Flash default,
  V4 Pro for this product)
