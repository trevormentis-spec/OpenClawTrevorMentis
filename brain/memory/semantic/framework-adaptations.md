# Framework Adaptations Log

Each infrastructure or workflow change is a framework experiment. Log: what changed, why, was the change worth it, did it generalize?

---

## Adaptation #1 — Source Registry Pivot (2026-05-15)

**What changed:**
- Archived `sources.json` (95+ global sources, 90% Iran/Hormuz/Middle East) → `sources.archived.2026-05-15-1510.json`
- Built `sources-mexico.json` — 62 sources across 6 themes, with NATO Admiralty scoring, publication frequency, originality, methodology transparency, track record, language, and paywall status
- Created knowledge architecture directories: `actors/`, `geography/`, `frameworks/`, `chronologies/` under `analyst/knowledge/mexico/`

**Why:**
- Mission pivot from global security posture to Mexico-only intelligence
- Previous source registry was unmaintainable: 130+ entries with no clear tiering or thematic organization
- Need Admiralty scoring for every source to enable systematic source evaluation
- Knowledge architecture needs to be topic-agnostic in structure (generalizes), Mexico-specific in content

**Was it worth it?**
- ✅ Yes — but the actual test is whether the Admiralty scoring gets *used* in analysis, not just created
- ✅ Admiralty scoring on every source is a new capability — framework should require this for all future topics
- Potential issue: 62 sources may be too many for daily triage. May need a tiering system (Tier-1 daily scan, Tier-2 weekly, Tier-3 as-needed)

**Does it generalize?**
- ✅ `admiralty`, `themes[]`, and `frequency` fields are topic-agnostic
- ✅ `signal_level` field maps to any intelligence domain
- ✅ `note` field for evaluation caveats is general
- ⚠️ `language` field is Mexico-specific but this is inherent to source metadata
- ✅ The `actors/geography/frameworks/chronologies` structure generalizes perfectly — replace `mexico/` with `agentina/` or `uhnw/` or `leo-ground-stations/`

## Adaptation #2 — Source Admiralty Evaluation Rollout (2026-05-15)

**What changed:**
- All 80 sources in sources-mexico.json now have NATO Admiralty scores (A1, A2, B2, B3, C3)
- Distribution: 23 A1, 37 A2, 5 B2, 3 B3, 4 C3 (copied from counting, may be off by a few)
- Separated beat reporters from institutional sources with individual Admiralty scores

**Why:**
- Initial source registry had Admiralty scores but no systematic tiering
- Needed to distinguish between authoritative (A1), professional (A2), variable (B2/B3), and low-confidence (C3) sources for daily triage
- Beat reporters need individual trust evaluations separate from their institutions

**Was it worth it?**
- ✅ Yes, but the next critical step is actually *using* the Admiralty tier for collection decisions, not just storing it
- ⚠️ The A1/A2/B/C scale interact with paywall status — some A1 sources (WSJ, FT, Reforma) are behind paywalls, meaning they can't be systematically ingested without subscription

**Does it generalize?**
- ✅ The Admiralty schema is topic-agnostic. Any intelligence domain uses the same trust evaluation structure.

## Adaptation #3 — Cartel Framework Corrective Update (2026-05-15)

**What changed:**
- The cartel factional dynamics framework was initially built with stale intelligence assumptions:
  - Assumed El Mencho was alive with health problems → He was killed Feb 22, 2026
  - Assumed El Mayo was still leading the Mayos faction → He was captured July 2024, sentenced to life Jan 2026
  - Assumed CJNG succession was still open → Juan Carlos Valencia González (El Pelón) confirmed as successor Apr 2026
- Corrected all three in the entity files and the framework assessments

**Why:**
- Initial collection was relying on generalized cartel profiles rather than recent-specific sources
- The accelerated learning session surfaced these gaps within the first hour of focused Mexico research
- The framework structure was correct; the content was stale

**Lesson:** The framework's 6-axis scoring relies on current intelligence. If the entity files haven't been updated in >3 months, the framework assessment is operating on stale ground truth. Need a "last source date" field on each entity file.

**Does it generalize?**
- ✅ Yes — any topic will have the same problem. Entity file "stale date" is a framework feature, not Mexico-specific.

## Adaptation #5 — Postdiction Forced-Resolution Mechanism (2026-05-16)

**What changed:**
- `scripts/postdict.py` recheck logic now force-resolves expired "unresolved" judgments to "incorrect"
- Legacy entries (no horizon_expiry field) auto-calculated as 7 days from entry date
- Top-level aggregation now sums from all daily_score entries regardless of recheck status
- Both `--recheck` and the daily postdiction path now produce honest calibration data

**Result:** Calibration changed from a fake 5/0/50 (correct/incorrect/unresolved) to a real 5/10/40.

**Why:**
- The original design excluded unresolved from accuracy calculations and never forced resolution at horizon expiry
- This systematically biased calibration toward overconfidence — no prediction was ever "wrong"
- Without honest calibration, the entire confidence-banding framework is performative

**Was it worth it?**
- ✅ Yes. This is the single highest-leverage framework fix available.

**Does it generalize?**
- ✅ Pure framework fix. Applies to any topic domain.

## Adaptation #6 — Mexico Daily News Scanner (2026-05-16)

**What changed:**
- Created `scripts/mexico-daily-scan.py` — fetches Spanish-language Mexican news from 8 free sources
- 76 articles from 8 sources on first run, covering Rocha case escalation, Sheinbaum positioning, security operations
- Only blocked source: Reforma (paywall — principal to resolve)

**Why:**
- Spanish-language news was identified as the biggest collection gap in the framework reflection
- English-language wire services filter and delay Mexican local reporting

**Was it worth it?**
- ✅ Yes — covered gaps immediately (detected Rocha co-defendant arrests within first run)
- ⚠️ Animal Politico was not parsed (JS-rendered site) — needs newspaper3k or similar

**Does it generalize?**
- ✅ Source URL list + language = any country/language. Replace URL list with Argentine sources and you have an Argentina daily scan.
- ⚠️ The keyword-based theme matching is Mexico-specific. For generalization, the theme keywords would need to be parameterized.

## Adaptation #4 — Knowledge Architecture Passes Redirect Test (Validated, 2026-05-15)

**What changed:**
- The actors/geography/frameworks/chronologies structure was tested by building 15 entity files, 5 geography files, 3 frameworks, and 1 chronology across ~2 hours of concentrated work

**Result:** The schema survived. Zero structural changes needed. The same directory layout works for Argentina, UHNW self-OSINT, or LEO ground stations with only content replaced.

**What was discovered:**
- The entity file template (who, when, where, what they want, what they control, what they fear, indicators, sources) works well for political actors, less well for corporate entities. KIO Networks and Carlos Slim needed adapted fields (market position, key risks) that don't cleanly map to the cartel profile template. May need a differentiated schema per entity type, or keep one flexible template with optional fields.

**Does it generalize?**
- ✅ Structure passes. Entity template needs flexibility for non-person entities.

---

*Log continued: 2026-05-15*
