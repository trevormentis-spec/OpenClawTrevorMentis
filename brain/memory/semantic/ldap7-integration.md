# LDAP-7 Integration — Semantic Memory

**Ingested:** 2026-05-11
**Framework:** LDAP-7 Leadership Decision Analysis and Prediction Framework v1.0
**Procedural memory:** `brain/memory/procedural/ldap7-leadership-decision-analysis.md`
**Skill file:** `skills/ldap7/skill.md`
**Status:** ✅ Fully integrated

---

## How Trevor Integrated LDAP-7

The LDAP-7 PDF was parsed, structured, and stored across three memory layers:

1. **Procedural memory** (`brain/memory/procedural/`) — The complete framework: seven dimensions, scoring methodology, decision cycle, D6 sub-phases, CPCA overlay, Predictability Paradox, and output template. This is the retrieval-conditioned analytical engine.

2. **Semantic memory** (this file) — Integration metadata: where LDAP-7 applies automatically, capability changes, invocation triggers, and cross-references to analyst playbooks and other frameworks.

3. **Reusable skill** (`skills/ldap7/skill.md`) — A standalone Trevor skill definition with activation conditions, leader profiles, and invocation protocol. Follows OpenClaw skill conventions.

---

## How LDAP-7 Changes Trevor's Analytical Capability

### Before LDAP-7
- Leader analysis was ad-hoc: qualitative character sketches, narrative description, no structured forecast protocol.
- Predictions mixed structural and content-level reasoning without separation.
- No confidence-calibration rigour tied to evidence density.
- No cognitive-degradation overlay for time-sensitive forecasting.

### After LDAP-7
- **Structured leader profiling:** Every leader analysis starts with scored D1–D7 dimensions backed by cross-domain, cross-temporal evidence.
- **Deterministic cycle mapping:** Situations are mapped onto a fixed 7-step decision cycle, producing *forecast structure first*.
- **Probabilistic output discipline:** All forecasts have explicit probability ranges, confidence levels, and falsification conditions.
- **Cognitive-state adjustment:** The CPCA overlay modifies confidence based on observable markers (sleep, language, impulse ratio, consequence horizon).
- **Degradation-aware forecasting:** Explicit hierarchy of which dimensions degrade first, with the key insight that degradation removes the brake, not the engine (escalation continues, retreat becomes impossible).
- **Double-cycle detection:** Leaders scoring D6 ≥ 9 trigger the Double Cycle refinement — retreat becomes the launch point for a second escalation.

---

## Where LDAP-7 Is Invoked Automatically

LDAP-7 is **retrieval-conditioned** — activated when any of these conditions are met:

| Trigger | Activation |
|---------|-----------|
| User asks to analyse/forecast a political leader, head of state, or CEO | ✅ Full LDAP-7 assessment (all 7 sections) |
| DailyIntelAgent processing a geopolitical escalation event | ✅ Decision-cycle diagnosis + leader profile update |
| Sanctions/trade escalation analysis | ✅ D2 scoring, D6 phase tracking |
| Conflict negotiation analysis | ✅ D1 (optionality), D5 (zero-sum), D6 (cycling) |
| Leadership transition / succession analysis | ✅ D7 (patronage-loyalty architecture) |
| Any assessment involving Trump, Xi, Putin, Netanyahu, Khamenei | ✅ Pre-scored profiles stored; update on new evidence |
| Strategic intent estimation (IO/JIPOE context) | ✅ Cycle-stage diagnosis + D2/D6 projection |
| Late-war / late-negotiation assessments | ✅ CPCA overlay mandatory (cognitive degradation likely) |
| Forecasts with "chaotic" or "unpredictable" subject framing | ✅ Predictability Paradox applied; structural analysis before content |

### Default Behaviour
If no explicit leader analysis is requested but a situational assessment involves a named leader making a strategic decision, Trevor should:
1. Recall the leader's stored dimension profile (if exists) or produce a provisional scored profile from available evidence.
2. Map the current situation onto the LDAP Decision Cycle.
3. Issue the structural forecast before attaching content-level conditional scenarios.

---

## Retrieval-Conditioned Generation Protocol

When Trevor needs LDAP-7 methodology mid-conversation:

**Fast path:**
1. Recall `brain/memory/procedural/ldap7-leadership-decision-analysis.md` for the full framework.
2. Recall this semantic integration file for invocation rules.
3. Generate structured output per Part VII template.

**Qualitative path (when full scoring isn't possible):**
1. Use the Quick Reference Card (Appendix of the procedural memory) for rapid structural framing.
2. State explicitly that the assessment is qualitative, not fully scored.
3. Apply the Predictability Paradox logic as a minimum.

---

## Cross-References

- **Analyst playbook:** `analyst/playbooks/analytic-workflow.md` — structured analysis methods that complement LDAP-7
- **CPCA template:** `analyst/playbooks/ldap7-cpca.md` — dedicated CPCA scoring guide
- **Source evaluation:** `brain/memory/procedural/source-evaluation.md` — used for evidence weighting in D1–D7 scoring
- **DailyIntelAgent:** Pipeline scripts reference LDAP-7 for leader behaviour forecasts within geopolitical briefs
- **Threat intel aggregator:** `skills/threat-intel-aggregator/SKILL.md` — escalation detection informed by D6 cycle tracking

---

## Known Profiles (Maintained as Built)

| Leader | Profile Status | Last Updated |
|--------|---------------|-------------|
| Trump, Donald J. | Full profile (D1–D7 scored HIGH) | 2026-05-11 |
| Putin, Vladimir | Not yet profiled | — |
| Xi, Jinping | Not yet profiled | — |
| Khamenei, Mojtaba | Not yet profiled | — |
| Netanyahu, Benjamin | Not yet profiled | — |
| Zelensky, Volodymyr | Not yet profiled | — |

*Leader profiles are stored in `brain/memory/semantic/ldap7-profiles/` as they are created.*
