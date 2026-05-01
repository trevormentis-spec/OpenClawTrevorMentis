# Playbook: Quality Gates

Run before any intelligence product leaves Trevor. If a gate fails, fix it —
don't ship and footnote.

---

## Gate 1 — BLUF discipline

- [ ] BLUF is at the top, not buried.
- [ ] BLUF answers the actual question, not a related one.
- [ ] BLUF is one paragraph max, ideally three sentences.
- [ ] BLUF uses calibrated language ("likely", "highly likely", "probable")
  rather than absolute language ("will", "definitely").

## Gate 2 — Calibration

- [ ] Every key judgment has a Sherman Kent band attached
  (`methodology/sherman-kent-bands.md`).
- [ ] Bands are appropriate to evidence — strong evidence → tighter band.
- [ ] No covertly hedged language that escapes the band system
  (e.g. "could", "may" without a probability).

## Gate 3 — Source hygiene

- [ ] Every source cited has a NATO Admiralty rating (A1 … F6) or an
  explicit "unrated".
- [ ] No single-source key judgments unless flagged as such.
- [ ] Conflicting sources noted, not silently averaged.
- [ ] Open-source primaries preferred over secondary aggregations.

## Gate 4 — Method visibility

- [ ] Hypotheses listed (ACH minimum two).
- [ ] Confidence levels stated.
- [ ] Indicators & Warnings section present for ongoing situations.
- [ ] Limitations / gaps listed (Phase 2 carry-forward).

## Gate 5 — Red-team pass

- [ ] At least one finding has been challenged (devil's advocacy entry).
- [ ] At least one alternative hypothesis received a fair hearing.
- [ ] Pre-mortem performed: "if this judgment is wrong in 30 days, why?"

## Gate 6 — Brand & format

- [ ] Vocabulary discipline followed (`ORCHESTRATION.md` brand voice list).
- [ ] Brand JSON applied if client product (concentric, eclipse, etc.).
- [ ] Document slug + DTG + classification banner present.

## Gate 7 — Delivery readiness

- [ ] Product type matches user expectation (chat / Doc / PDF).
- [ ] Length matches request (no over-delivery on a 1-pager request).
- [ ] Memory archive entry queued for `memory/YYYY-MM-DD.md`.

---

## Failure modes to watch for

1. **Confidence inflation under deadline pressure.** If you're tempted to
   upgrade a band because the user asked for a "definitive answer", stop.
2. **Hypothesis drift.** A 4-hypothesis ACH that ends up favoring the one
   you started with is a warning sign, not a result.
3. **Source laundering.** Citing a think-tank that cited a primary is not
   the same as citing the primary.
4. **Gap erasure.** Limitations that were big in Phase 2 should still be
   big in Phase 5. If they shrank, ask why.
