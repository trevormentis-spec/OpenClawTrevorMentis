# LDAP-7 Leadership Decision Analysis — Trevor Skill

**Name:** LDAP-7 Leadership Decision Analysis
**Version:** v1.0
**Source:** `brain/memory/procedural/ldap7-leadership-decision-analysis.md`
**Semantic memory:** `brain/memory/semantic/ldap7-integration.md`
**CPCA playbook:** `analyst/playbooks/ldap7-cpca.md`

---

## Description

A behavioural-pattern framework for forecasting the decision-making of political leaders, executives, or strategic actors. Seven scored dimensions (D1–D7), a deterministic 7-step decision cycle, a cognitive-capacity overlay (CPCA), and a structured output protocol for probabilistic forecasts.

---

## Activation Conditions

Invoke this skill when ANY of the following apply:

1. **User asks to analyse, profile, or forecast a leader's behaviour** (head of state, CEO, military commander, diplomat)
2. **Geopolitical escalation event** involving a named leader making a strategic decision
3. **Sanctions/trade escalation analysis** — D2 (Coercive Leverage) scoring + D6 cycle tracking
4. **Conflict negotiation assessment** — track D1 optionality, D5 framing, D6 cycling
5. **Strategic intent estimation** (JIPOE/IO context) — cycle-stage diagnosis + projection
6. **Leadership transition or succession** — D7 (Patronage-Loyalty Architecture)
7. **DailyIntelAgent / threat intel brief** involving leadership behaviour forecasts
8. **Any assessment of Trump, Putin, Xi, Netanyahu, Khamenei, or Zelensky** — pre-scored profiles available
9. **Late-war or late-negotiation phase assessments** — CPCA overlay is **mandatory**
10. **User describes a leader as "chaotic" or "unpredictable"** — apply Predictability Paradox

---

## Invocation Protocol

### Step 1: Retrieve Procedural Memory
Load `brain/memory/procedural/ldap7-leadership-decision-analysis.md` for the full framework.

### Step 2: Retrieve or Build Leader Profile
- If leader profile exists in `brain/memory/semantic/ldap7-profiles/`, load it.
- Otherwise, score D1–D7 using the evidence protocol (3+ data points, 2+ domains, 2+ time periods).

### Step 3: Map to Decision Cycle
Identify: current cycle phase, D6 sub-phase, active trigger, coercive instrument, branch-point signals being monitored.

### Step 4: Run CPCA Overlay (mandatory for time-sensitive forecasts)
Score CPCA-1 through CPCA-4 using `analyst/playbooks/ldap7-cpca.md`. Apply composite modifier.

### Step 5: Structure Output
Use the Part VII output template:
1. Subject & Scope
2. Dimension Scores (D1–D7) with evidence
3. Decision-Cycle Diagnosis
4. CPCA Overlay
5. Probabilistic Forecast (structure first, content as conditional scenarios)
6. Validation Against Prior Forecasts
7. Monitoring Indicators + Falsifiers

### Step 6: Record for Future Retrieval
Log new evidence and update the leader profile file in `brain/memory/semantic/ldap7-profiles/`.

---

## Quick Reference (for rapid deployment without full framework load)

### Dimensions
D1 — Optionality (preserve choices, avoid commitment) [1–10]
D2 — Coercion (prefer asymmetric pressure) [1–10]
D3 — Popularity (the noncompensatory gate) [1–10]
D4 — Constraint rejection (bypass institutions) [1–10]
D5 — Zero-sum (every interaction has a winner) [1–10]
D6 — Escalate-retreat (extreme open, reframed climbdown) [1–10]
D7 — Loyalty (personal over institutional) [1–10]

### Decision Cycle
Trigger → D5 frame → D2 option → D6 escalation → D3 screen → branch (advance via D4/D7, or retreat preserving D1) → narrative consolidation

### Degradation Hierarchy
D3 → D6 retreat → D1 → D6 escalation → D5 → D7

### Predictability Paradox
The content of decisions varies; the structure is fixed. **Forecast structure first, content second.**

### CPCA Composite
ALL GREEN → unmodified | 1 AMBER → −1 confidence, +30% timing | 2+ AMBER or any RED → −2 confidence, escalation-without-off-ramp

---

## Assumptions & Boundaries

- LDAP-7 operates at the **behavioural level** — scores derive from observable action, not psychological inference
- Does **not** diagnose psychiatric conditions, attribute motive, or predict specific policy content
- Predicts the **shape of decision sequences**, not the content of decisions
- Cross-domain, cross-temporal evidence required for scored profiles — provisional/rapid assessments must be flagged as such
- Falsifier logic is mandatory: every forecast must specify the observable that would prove it wrong
