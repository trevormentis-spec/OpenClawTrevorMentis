# Playbook: Analytic Workflow

The standard end-to-end process for a Trevor intelligence assessment. Run this
when the question is non-trivial and the stakes warrant structure.

> If the question is small ("what time is sunset in Tehran"), don't run this —
> just answer it. The workflow is for assessments, not lookups.

---

## Phase 0 — Frame the question

Before you collect a single source, write down — in `tmp/<slug>/00-framing.md`:

- **Decision the user is making** (or, if none, the judgment they're forming)
- **The question** in one sentence
- **Out of scope** (so you don't drift)
- **Time horizon** (next 72h? 30 days? 12 months?)
- **Confidence threshold** for the user (rough is fine; "tradeable bets" is high)
- **Key terms** defined (what counts as "escalation"? what counts as "success"?)

A sharp framing prevents 80% of the misfires.

---

## Phase 1 — Source acquisition & news collection

- Pull from `analyst/meta/sources.json` filtered by topic and signal level.
- Time-box: 30–45 minutes max for routine; 2 hours for major.
- Output: `tmp/<slug>/01-news_raw.md` — bullets with source attribution and
  timestamp on each item.
- Use the `web-searchplus` skill or direct `web_fetch` for primaries; reach
  for `geospatial-osint` if location/movement matters.
- Note collection gaps explicitly. Empty space matters.

---

## Phase 2 — Gap analysis

For each unanswered piece of the question, write a numbered gap (G1, G2 …) in
`tmp/<slug>/02-gaps.md`. Each gap gets:

- **Description** — what's missing
- **Why it matters** — what judgment depends on it
- **Confidence cost** — what bands you have to widen if you can't fill it
- **Acquisition path** — where you'd look (or "unreachable" if you can't)

If you can fill a gap cheaply, fill it. If you can't, **carry it forward
explicitly** into the assessment — never silently.

---

## Phase 3 — Methodology pass

Apply at least three structured analytic techniques. Default starter set:

1. **ACH** — Analysis of Competing Hypotheses. Use
   `analyst/templates/ach-matrix.md`. Two to four hypotheses minimum.
2. **PMESII-PT** — Political, Military, Economic, Social, Information,
   Infrastructure, Physical environment, Time. Use
   `analyst/templates/pmesii-pt-scan.md`.
3. **Indicators & Warnings** — Use `analyst/templates/indicators-and-warnings.md`.
   Forces you to commit, in advance, to what would change your mind.

For high-stakes products add red team / devil's advocacy
(`analyst/templates/red-team-review.md`) and pre-mortem.

For every claim that ends up in the assessment: tag it with a Sherman Kent
band (`methodology/sherman-kent-bands.md`) and a NATO Admiralty source rating
(`methodology/nato-admiralty.md`).

---

## Phase 4 — Drafting

Use `analyst/templates/analytic-note.md` for a 1-pager.

For a full TREVOR product, use the trevor-methodology skill (16 sections,
12–27, with the 6 calibrations and 11 SATs). Open
`skills/trevor-methodology/SKILL.md` and follow its pipeline.

Drafting rules:
- BLUF first. Always.
- Confidence and probability bands are **mandatory** on every key judgment.
- Distinguish observed evidence, inference, and assumption.
- Carry gaps from Phase 2 into a Limitations section. Do not bury them.

---

## Phase 5 — Quality gates

Before delivery, run `analyst/playbooks/quality-gates.md` as a checklist.

If a gate fails, fix; do not ship and footnote.

---

## Phase 6 — Delivery & archive

- Deliver via the requested channel (chat, AgentMail, Google Doc).
- Archive the final document, the framing file, and the ACH matrix in
  `memory/YYYY-MM-DD.md` with a one-paragraph entry.
- Update `analyst/meta/sources.json` with any new durable sources discovered.

---

## Reference: typical durations

| Product             | Phase 0–2 | Phase 3 | Phase 4 | Phase 5 | Total    |
|---------------------|-----------|---------|---------|---------|----------|
| Quick brief (1 pg)  | 20 min    | 15 min  | 20 min  | 5 min   | ~1 hr    |
| Daily briefing      | 45 min    | 30 min  | 45 min  | 10 min  | ~2 hr    |
| TREVOR assessment   | 2–3 hr    | 2 hr    | 3–4 hr  | 30 min  | ~8–10 hr |

If you're under by half, you cut something. Find what you cut and decide
whether to add it back or note it as a limitation.
