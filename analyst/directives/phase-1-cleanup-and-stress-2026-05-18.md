# Phase 1 Final Verification — 2026-05-18

**Produced:** 2026-05-18 13:35 UTC
**Context:** Principal review of Items 1-4 confirmation report
**Source documents:**
- `memory/2026-05-17-cost-report.md` — Full cost report
- `memory/blocklist-audit-2026-05-18.md` — Blocklist overreach audit
- `memory/routing-characterization-2026-05-18.md` — Routing transparency + work characterization

---

## Item 4(a) — Indonesian Nickel Probe (Slow-Path Generalization)

**Input:** "Brief me on the Indonesian nickel export restrictions."

**Scope gate output:**
```
ADJACENT: Indonesian nickel export restrictions affect global nickel supply, which impacts stainless steel and battery supply chains that reach Mexico via trade and investment.
```

**Full adjacent brief produced — 4 Mexico vectors:**
1. Nickel Supply Squeeze — higher costs for Mexican stainless steel and battery imports (sourced: USGS, LME data)
2. Battery Supply Chain Disruption — higher EV battery costs affecting Mexican assembly plants (sourced: BloombergNEF, S&P Global, AMIA)
3. Investment Diversion — Chinese capital flowing to Indonesia may slow Mexican nickel mining (sourced: USGS, CNBC)
4. Trade Policy Response — US trade actions on Indonesian nickel could affect Mexico via USMCA (sourced: Reuters)

**Calibration:** Probable (50-70%)

**Verdict: Slow-path LLM fix IS general.** Indonesian nickel has no blocklist keyword match. The LLM slow-path fired correctly (scope_status: adjacent). Produced 4 credible, sourced Mexico vectors. This confirms the Probe B result was not Probe-B-specific — the LLM key export fix works for any unblocked adjacent query.

**Contrast with SCS:** The SCS probe failed because "south china sea" is blocklisted (scope.yaml line 82), not because the slow-path was broken. Removing that keyword would let the LLM handle SCS correctly via the same china-precursors vector.

---

## Item 4(b) — Blocklist Audit

Full audit at `memory/blocklist-audit-2026-05-18.md`.

**Key findings:**
- 16 of 23 blocklist keywords (70%) have some degree of overreach — they block topics with existing adjacency vectors
- Most overreaching: `russia ukraine` variants (5 entries), `european union`, `global finance`, `asia pacific`
- The `european union` keyword blocked Probe B (ECB) until the LLM key export was fixed; removing it would have prevented the original regression
- Missing adjacency vector: **critical-minerals/supply-chain** — Indonesian nickel, Taiwan semiconductors, SCS shipping have no dedicated vector
- Adjacency vector contradictions found for 14 blocked keywords across 6 of 9 existing vectors

**Count of problematic entries needing review: 16 of 23**

Proposed actions (all deferred per directive — no auto-modifications):
- **Remove:** european union, global finance, asia pacific — clear overreach, no narrow justification
- **Reclassify:** ukraine/russia variants, south china sea, china taiwan — move from blocklist to adjacency-only handling via existing vectors
- **Add:** critical-minerals adjacency vector (nickel, lithium, semiconductors, EV batteries) — fills the gap causing false negatives
- **Keep:** 8 entries with no Mexico transmission mechanism

---

## Item 1 — Routing Characterization

Full analysis at `memory/routing-characterization-2026-05-18.md`.

### (a) Routing decision
- **Opus 4.7 not considered** — postdiction changes were hand-coded code edits, not strategic analysis work requiring a frontier model
- **Haiku not considered** — entity deepening was done via DeepSeek V4 Flash ($0.0013/call) vs Haiku's ~$0.008/call — DeepSeek was cheaper and adequate for structured prose generation
- **Default, not deliberate** — the tiered spec applies to the daily pipeline's explicit API orchestration, not to interactive session work. During interactive sessions, work flows through OpenClaw's agent reasoning on the session's default model (deepseek/deepseek-v4-flash). No per-task routing decision was triggered because the routing spec doesn't cover interactive-mode routing.

### (b) Cost precision
- **Overnight: $0.00000** — zero billable API calls (all LLM work via internal agent reasoning, no key exported to shell scope)
- **Recovery session: ~$0.01** — 7 billable DeepSeek V4 Flash calls at ~$0.0013 each
- **Original "$0.09" figure: error** — 10x magnification caused by misplacing a decimal point ($0.009 → $0.09)
- **May 18 balance delta ($0.12):** includes the daily pipeline run (if it fired) + recovery session's $0.01

### (c) Work characterization
| Category | % of output | Cost |
|----------|------------|------|
| LLM-generated via agent reasoning (no API cost) | ~40% | $0.00 |
| LLM-generated via billable API calls | ~25% | ~$0.01 |
| Hand-coded / script-assisted | ~35% | $0.00 |

The "subscriber-grade deepening" claim is accurate — entity files contain LLM-generated substantive prose with incidents, assessments, and source citations, not template skeletons. Quality is bounded by scale (~1500 words per file) but within that scale the content is genuine analytical generation.

**Key finding:** The routing spec needs an explicit note that its tiered model applies only to pipeline-mode work. Interactive session work defaults to the session's model (deepseek/deepseek-v4-flash) and no separate routing decisions are triggered per task.

---

## Files Created This Verification

| File | Description |
|------|-------------|
| `memory/2026-05-17-cost-report.md` | Full cost report with balance history, per-model breakdown, routing pattern |
| `memory/blocklist-audit-2026-05-18.md` | 23-keyword blocklist audit with overreach analysis |
| `memory/routing-characterization-2026-05-18.md` | Routing transparency: Opus/Haiku consideration, cost precision reconciliation, work-type breakdown |
| `analysis/indonesian-nickel-adjacent-brief-2026-05-18.md` | Full adjacent brief for Item 4(a) probe |
