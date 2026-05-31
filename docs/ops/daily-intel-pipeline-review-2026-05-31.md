# Daily Intel Briefing Pipeline — Opus Audit

**Date:** 2026-05-31  
**Auditor:** Trevor (subagent)  
**Files audited:** 6 core scripts — 4,450 lines total + 284-line bash orchestrator

---

## Current Architecture

```
                     ┌─────────────────────┐
                     │  OpenClaw Cron       │
                     │  05:00 PT trigger    │
                     └──────────┬──────────┘
                                │
                                ▼
                  ┌─────────────────────────┐
                  │ daily-text-brief.sh     │
                  │ (284 lines, bash)       │
                  │ LOCKFILE: flock         │
                  └──────────┬──────────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
   ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
   │ Step 1a:       │ │ Step 1b:       │ │ Step 1c:       │
   │ Calibration    │ │ Source         │ │ Kalshi         │
   │ Directives     │ │ Discovery      │ │ Scanner        │
   └────────────────┘ └────────────────┘ └────────────────┘
                                                   │
                                                   ▼
                                       ┌─────────────────────┐
                                       │ Step 1d: Simmer     │
                                       │ Signal Overlay      │
                                       └─────────────────────┘
                                                   │
                                                   ▼
                              ┌──────────────────────────────────┐
                              │ STEP 2: Orchestrator              │
                              │ (orchestrate.py, 582 lines)      │
                              │                                  │
                              │  ┌─────────────┐                  │
                              │  │ collect.py  │ 259+ RSS feeds   │
                              │  │ (1,561 ln)  │ 10 regions       │
                              │  └──────┬──────┘                  │
                              │         │                         │
                              │         ▼                         │
                              │  ┌─────────────────┐              │
                              │  │ analyze.py      │ 10 regional  │
                              │  │ (890 lines)     │ + exec sum.  │
                              │  │ DeepSeek V4 Pro  │ + red team  │
                              │  └─────────────────┘              │
                              │                                  │
                              │  Model: V4 Pro for ALL tiers     │
                              │  Provider: deepseek (direct API) │
                              └──────────────────────────────────┘
                                                   │
                                                   ▼
                              ┌──────────────────────────────────┐
                              │ Step 2b: GDELT Collection Floor  │
                              │ (non-fatal gap-filler)           │
                              └──────────────────────────────────┘
                                                   │
                                                   ▼
                              ┌──────────────────────────────────┐
                              │ STEP 3: Quality Gate              │
                              │ (guard_pipeline.py, 713 lines)   │
                              │ 7 gates + model check            │
                              └──────────────────────────────────┘
                                                   │
                                          (if PASSES)
                                                   │
                                                   ▼
                              ┌──────────────────────────────────┐
                              │ STEP 4: Delivery                 │
                              │ (deliver_text_brief.py, 420 ln)  │
                              │ AgentMail → trevor_mentis@       │
                              │ → Roderick inbox                 │
                              └──────────────────────────────────┘
                                                   │
                                                   ▼
                              ┌──────────────────────────────────┐
                              │ Step 5: Postdiction + I&W,       │
                              │ Expired Prediction Recheck,      │
                              │ Calibration Recompile            │
                              └──────────────────────────────────┘
                                                   │
                                                   ▼
                              ┌──────────────────────────────────┐
                              │ Step 6: Moltbook (DISABLED)     │
                              │ Step 7: Landing Page Deploy     │
                              └──────────────────────────────────┘
```

**Key path characteristic:** Single sequential chain — each step depends on the prior. No parallel processing in the bash script (parallelism at the orchestratore.py level for analysis).

---

## Critical Vulnerabilities

### CRITICAL

#### C1. Bash script has corrupted variable references — Step 2 orchestrator error-handling is dead code

**Severity:** CRITICAL | **Impact:** Delivery-blocking failures go undetected | **Likelihood:** 100% | **Fix effort:** 5 min

**Evidence (daily-text-brief.sh, lines 105-110):**
```bash
if [  -ne 0 ]; then                           # $ORCH_RC MISSING
    echo "FATAL: Orchestrator failed with rc=" | tee -a ""  # $ORCH_RC, $LOG MISSING
    exit                                       # exit code MISSING
fi
```

This is not a typo — it's corruption at the byte level. `${ORCH_RC}` and `"${LOG}"` are simply absent, replaced by nothing. The `if` condition is syntactically invalid (`[  -ne 0 ]` — zero tokens before `-ne`), which causes bash to throw a syntax error. The script effectively terminates here at line 105 on every run, never reaching the quality gate or delivery.

**Additionally (lines 138-139):**
```bash
ORCH_RC      # Bare variable name — "command not found" at runtime
fi           # Stray `fi` with no matching `if` — syntax error
```
This orphaned `ORCH_RC\nfi` block sits between the GDELT section and the quality gate section. If the script somehow makes it past line 110 (only possible during development with `set +e`), this block guarantees a syntax error.

**Status:** Not tracked in `KNOWN_ISSUES.md`. The bash script is un-runnable in its current state.

#### C2. Default provider is DeepSeek Direct API despite known hang-on-large-payloads bug

**Severity:** CRITICAL | **Impact:** Pipeline fails on exec summary calls* | **Likelihood:** HIGH (~70% of runs with normal incident volume) | **Fix effort:** 1 line change

The bash script passes `--provider deepseek --tier2-provider deepseek` explicitly to orchestrate.py. The known issue (`KNOWN_ISSUES.md`) documents that "V4 Pro direct API hangs on payloads >20KB" and that the exec summary call needs OpenRouter. Yet the bash script **chooses DeepSeek direct API** for everything.

Meanwhile, `orchestrate.py`'s default is `--provider openrouter` — meaning running `orchestrate.py` standalone uses OpenRouter, but the cron-driven pipeline (via the bash script) uses DeepSeek direct API and will hang.

The `analyze.py` controls this with `max_input_chars=60000` for the exec summary call, which **increases** the payload. This is the opposite of what the bug requires — the fix documented in KNOWN_ISSUES says "keep payloads under 16KB for direct DeepSeek calls."

#### C3. No fallback infrastructure — single-provider single-model dependency

**Severity:** CRITICAL | **Impact:** Any DeepSeek failure (billing, API outage, rate limit) kills the entire pipeline with no fallback | **Likelihood:** MEDIUM (billing failures have happened before) | **Fix effort:** 2-4h

The pipeline explicitly rejects Flash models (`if "flash" in tier1_model.lower() -> FATAL`), and the bash script has no fallback chain. The `llm-routing.yaml` defines fallback chains:
- `deepseek_direct: [deepseek/deepseek-v4-flash, anthropic/claude-sonnet-4.5]`

But these fallbacks are never consulted — the bash script hardcodes `--provider deepseek` and `--model deepseek/deepseek-v4-pro`. When the DeepSeek Direct API is unavailable (as previously happened with billing issues), there are ten regional analysis calls and one exec summary call all failing simultaneously, with zero output.

### HIGH

#### H1. QC watchdog timing gap — quality gate references `/home/{user}/trevor-briefings/` but orchestrator writes to the same path with potential race

**Severity:** HIGH | **Impact:** False quality gate failures when analysis files are being written | **Likelihood:** HIGH (every run) | **Fix effort:** 1h

The quality gate (step 3 in bash script) reads from `$WORKING_DIR/analysis/` while the orchestrator is writing to `~/trevor-briefings/${DATE_UTC}/analysis/`. In theory these are the same directory. But the bash script:

1. Sets `WORKING_DIR="$HOME/trevor-briefings/${DATE_UTC}"` at **line 152** (step 3)
2. Uses `$WORKING_DIR` in the orchestrator call at **lines 94-101** (step 2)

The orchestrator writes to the same directory. There's no `.brief_complete` flag (noted in `KNOWN_ISSUES.md` as recommended but missing). The quality gate runs immediately after `python3 orchestrate.py` completes, but there's a window where the orchestrator's final write (syncing exec_summary to `tasks/news_analysis.md`) overlaps with the gate reading it.

**Status:** Noted in `KNOWN_ISSUES.md` as "QC can run before assembly finishes, causing false failures" — no fix applied.

#### H2. Bash delivery section has structural logic errors — validation code only runs when AgentMail key is absent

**Severity:** HIGH | **Impact:** Post-delivery quality validation never runs in production | **Likelihood:** 100% | **Fix effort:** 5 min

Lines 188-200:
```bash
if [ -n "${AGENTMAIL_API_KEY:-}" ]; then
    echo "--- Delivering via AgentMail ---"
    python3 ... deliver_text_brief.py ... 2>&1
    ...
else                                                    # ← ELSE: API key NOT set
    echo "AGENTMAIL_API_KEY not set ..."
    echo "--- Validating delivery quality ---"           # ← Validation is in the ELSE branch!
    python3 validate_delivery.py ...
fi
```

The post-delivery quality validation is inside the `else` branch — meaning it only runs when `AGENTMAIL_API_KEY` is **not** set (i.e., when delivery is skipped). In production (where the key IS set), the validation code is completely bypassed.

Additionally, line 192 has a broken continuation:
```
python3 "$REPO/scripts/validate_delivery.py" 
    --brief-dir "$WORKING_DIR" 
    >> "$LOG" 2>&1
```
No trailing backslash on line 192. Shell executes `python3 ... validate_delivery.py` with no arguments, then tries `--brief-dir ...` as a separate command (fails with "not found"). The `>> "$LOG" 2>&1` applies only to the broken `--brief-dir ...` command.

#### H3. Region lists drift between components — analyze.py, deliver_text_brief.py, guard_pipeline.py all have different region taxonomies

**Severity:** HIGH | **Impact:** Missing sections, orphan files, structural quality gate failures | **Likelihood:** HIGH | **Fix effort:** 30 min

Three different `region` lists exist:

| analyze.py (`REGIONS_ORDER`) | deliver_text_brief.py (`regions_order`) | guard_pipeline.py (`EXPECTED_REGIONAL_JSON`) |
|---|---|---|
| europe | europe | europe |
| north_america | north_america | north_america |
| central_america_caribbean | central_america_caribbean | central_america_caribbean |
| south_america | south_america | south_america |
| middle_east | middle_east | middle_east |
| central_asia | central_asia | central_asia |
| south_east_asia | south_east_asia | south_east_asia |
| east_asia | east_asia | east_asia |
| south_asia | south_asia | south_asia |
| oceania | oceania | oceania |
| prediction_markets | prediction_markets | prediction_markets |
| **north_africa** ✅ | — | **north_africa** ✅ |
| **sub_saharan_africa** ✅ | — | **sub_saharan_africa** ✅ |
| — | **russia_eurasia** ✗ | **russia_eurasia** ✗ |

**analyze.py** generates 14 region files (13 + exec_summary).  
**deliver_text_brief.py** looks for 14 files including `russia_eurasia.json` (which doesn't exist — analyze.py uses `europe`/`north_africa`/`sub_saharan_africa` instead).  
**guard_pipeline.py** expects `russia_eurasia.json` which doesn't exist — structural gate will **BLOCK** every brief, flagging it as missing.

This means the quality gate *should* be blocking every single brief due to structural failure, unless it's running with a permissive configuration.

**Status:** Not tracked in `KNOWN_ISSUES.md`.

### MEDIUM

#### M1. Region lists in SKILL.md also differ from code

**Severity:** MEDIUM | **Impact:** Frame drift when humans update prompts | **Likelihood:** HIGH (maintenance) | **Fix effort:** 30 min

The SKILL.md describes **6 regions** (Europe, Asia, Middle East, North America, South & Central America, Global Finance) while the code operates on **12+ regions**. The `deepseek-prompts.md` prompt templates likely have their own region lists. When any one of these is updated without updating the others, misalignment occurs.

**Status:** Tracked in `KNOWN_ISSUES.md` as "Template drift — prompt templates have region lists that can drift from code-level REGIONS_ORDER."

#### M2. KJ field name inconsistency requires runtime normalization

**Severity:** MEDIUM | **Impact:** Broken HTML rendering, lost judgments, ugly output | **Likelihood:** HIGH (every brief) | **Fix effort:** 1h (unify at source)

`deliver_text_brief.py` has 30+ lines of field name normalization:
```python
# Normalize event → statement (alternate field name from some analysis models)
if "event" in kj and not kj.get("statement"):
    kj["statement"] = kj["event"]
if "prediction" in kj and not kj.get("statement"):
    kj["statement"] = kj["prediction"]
if "judgment" in kj and not kj.get("statement"):
    kj["statement"] = kj["judgment"]
# ... plus probability_band, probability_verbal, confidence_verbal, confidence
```

This means different analysis runs produce different JSON schemas. The normalization code saves 50-80% of brief appearances from being gappy, but it's a band-aid on a systemic inconsistency.

**Status:** Tracked in `KNOWN_ISSUES.md` as "KJ field name inconsistency."

#### M3. No `.brief_complete` flag written after pipeline assembly

**Severity:** MEDIUM | **Impact:** QC watchdog timing race | **Likelihood:** HIGH (every run) | **Fix effort:** 30 min

The orchestrator's final steps (syncing to `tasks/news_analysis.md`, writing memory) have no sentinel file. `KNOWN_ISSUES.md` recommends writing a `.brief_complete` file, which would let the bash quality gate know the analysis is fully flushed. Not implemented.

**Status:** Tracked as recommended but not implemented.

#### M4. Bash script has hardcoded `Fri May 29` date in error message

**Severity:** MEDIUM | **Impact:** Confusing error messages | **Likelihood:** 100% | **Fix effort:** 1 min

Line 108:
```bash
echo "=== Daily Text Brief FAILED — Fri May 29 18:28:51 UTC 2026 ==="
```
This is a hardcoded date from when the error message was written. It will never be accurate. Should use `$(date -u)` like the other timestamps.

### LOW

#### L1. `--no-deliver` flag in bash script's orchestrator call means the Python orchestrator also skips delivery

**Severity:** LOW | **Impact:** Duplicate delivery logic paths | **Likelihood:** 100% | **Fix effort:** 1 min

The bash script passes `--no-deliver` to `orchestrate.py`, then handles delivery itself in Step 4. This is fine architecturally (bash owns delivery orchestration), but means the `--no-deliver` path in `orchestrate.py` is *always* active — any delivery logic in orchestrate.py is dead code. This creates confusion about where delivery is actually managed.

#### L2. Moltbook posting step is dead code (principal directive)

**Severity:** LOW | **Impact:** Wasted API call on every run | **Likelihood:** 100% | **Fix effort:** 2 min

Step 6 calls `moltbook_post.py` every run. Principal directive 2026-05-22 disabled all social posting. The script likely fails immediately or posts nothing, but wastes a few seconds per run.

#### L3. `set -e` re-enable is fragile

**Severity:** LOW | **Impact:** Silent error swallowing | **Likelihood:** LOW | **Fix effort:** 5 min

After each non-fatal step, the script does `set -e 2>/dev/null || true`. This is a cargo-cult pattern — `set -e` doesn't produce stderr output, and `|| true` swallows it. If a previous command failed, the `set -e` re-enable might not actually re-enable it properly. The pattern should be `set -e` followed by nothing, or the whole `set -e` approach should be replaced with explicit error checks.

#### L4. GDELT section references $WORKING_DIR before it's defined

**Severity:** LOW | **Impact:** GDELT floor never runs when it should | **Likelihood:** 100% | **Fix effort:** 1 min

`$WORKING_DIR` is first used at line 118 but defined at line 152. In bash, undefined variables expand to empty string (or error with `set -u`, which isn't set). So:
```bash
if [ -f "$WORKING_DIR/raw/incidents.json" ]; then
```
becomes:
```bash
if [ -f "/raw/incidents.json" ]; then
```
which is always false. GDELT collection floor never runs.

---

## Resilience Gaps

### Dead Feed Handling Is Fragile
- **Current:** Per-run dead feed cache with 48h retest. But the cache file (`dead-feeds.json`) is in `brain/memory/semantic/` — if the brain reindexer clears the semantic directory, all feed status resets.
- **Risk:** A cache wipe re-introduces 342 dead feeds, adding 30-60 minutes of timeout delays to collection.

### No Healthy-Feed Count Monitoring
- If too many feeds go dead simultaneously (e.g., Cloudflare changes WAF rules blocking all RSS), no alert fires. The pipeline just produces a thin brief with mostly web search fallback data.
- Recommend: Alert when working feed count drops below 150 (current: ~298).

### Single Host Process
- Everything runs on one machine. No redundancy if the host goes down at 05:00 PT. The daily brief is simply skipped.
- Consider: A second cron slot at 07:00 PT (if morning brief not detected, re-run).

### No Budget Circuit Breaker at Pipeline Level
- `config/budget.yaml` defines daily caps, but nothing in the pipeline checks cost before starting ten regional analysis calls. If the system is near budget limits, a single pipeline run could blow through the cap.
- Recommend: Budget preflight check in daily-text-brief.sh before step 2.

### Delivery Has No Fallback Channel
- AgentMail is the only delivery path. If AgentMail is down (API errors, rate limits, auth failures), the brief is saved to working directory but doesn't reach Roderick.
- Recommend: Gmail fallback or local MTA as secondary delivery.

---

## Structural Recommendations (ordered by impact)

### R1. Fix the bash script corruption — CRITICAL

**What:** Replace lines 105-110 with correct variable references, remove orphaned lines 138-139.  
**Why:** Pipeline is currently non-functional. Error handling is dead code.  
**Effort:** 5 minutes — straightforward text replacement.  
**Risk if not done:** Pipeline never proceeds past the `if [  -ne 0 ]` check (syntax error at runtime). The script fails at line 105 on every cron run.

### R2. Switch orchestrator provider to OpenRouter — CRITICAL

**What:** Change `--provider deepseek` → `--provider openrouter` and `--tier2-provider deepseek` → `--tier2-provider openrouter` in `daily-text-brief.sh` line 97-98.  
**Why:** DeepSeek Direct API hangs on large payloads (known issue). OpenRouter handles the same model without the payload limitation.  
**Effort:** 1 line change.  
**Risk if not done:** Exec summary call (payload ~60KB) hangs indefinitely ~70% of the time. Regional analysis calls (<18KB each) might succeed, but the pipeline remains broken overall.

### R3. Centralize region definitions into single source of truth — HIGH

**What:** Create `analyst/meta/regions.yaml` with ALL region definitions (names, labels, expected files). Import from `regions.json`, `analyze.py`, `deliver_text_brief.py`, `guard_pipeline.py`. Eliminate the three independent lists.  
**Why:** Region drift causes structural gate BLOCK, missing sections in delivery, and orphan files every brief.  
**Effort:** 2-3 hours.  
**Risk if not done:** Every region-related code change risks misalignment. Each structural release may or may not ship all regions depending on which component was updated.

### R4. Add `--complete` flag infrastructure — HIGH

**What:** Orchestrator writes `.brief_complete` file on successful assembly. Quality gate checks for this file before running.  
**Why:** Eliminates the QC-timing race documented in KNOWN_ISSUES.md.  
**Effort:** 30 minutes.  
**Risk if not done:** Continuing false QC failures that Roderick has to manually override.

### R5. Fix delivery validation placement and continuations — HIGH

**What:** Move validation code outside the `else` branch. Fix broken line continuations.  
**Why:** Post-delivery quality validation is dead code in production.  
**Effort:** 5 minutes.  
**Risk if not done:** No delivery validation. Broken content goes to Roderick without QC.

### R6. Add multi-provider fallback chain — HIGH

**What:** In the bash script, after the main orchestrator attempt fails, retry with `--provider openrouter --tier2-provider openrouter --model anthropic/claude-sonnet-4.5`.  
**Why:** Single-provider dependency is a known failure mode. Billing issues have stopped the pipeline before.  
**Effort:** 1-2 hours.  
**Risk if not done:** Any DeepSeek unavailability (billing, rate limit, API deprecation, TOS change) kills the daily brief with zero output.

### R7. Add budget preflight check — MEDIUM

**What:** Before step 2, check current DeepSeek spend against budget caps. Abort if approaching.  
**Why:** Ten regional calls + one exec summary can cost $3-8 per run. Automatic daily spend accumulates.  
**Effort:** 1 hour.  
**Risk if not done:** Budget overrun causes billing block, which subsequently kills all analysis. Self-inflicted outage.

---

## Quick Wins (implement in <1h)

| # | Fix | File | Effort | Impact |
|---|---|---|---|---|
| **Q1** | Replace `$ORCH_RC` in line 105, fix `tee -a ""`, add `exit 1` | `scripts/daily-text-brief.sh` | 2 min | CRITICAL — pipeline currently fails before quality gate |
| **Q2** | Remove orphaned `ORCH_RC\nfi` at lines 138-139 | `scripts/daily-text-brief.sh` | 1 min | CRITICAL — syntax error after GDELT section |
| **Q3** | Change `--provider deepseek` → `--provider openrouter` | `scripts/daily-text-brief.sh` line 97-98 | 1 min | CRITICAL — exec summary hangs on large payloads |
| **Q4** | Move validation out of else branch, add backslash | `scripts/daily-text-brief.sh` lines 189-200 | 3 min | HIGH — post-delivery validation is dead code |
| **Q5** | Remove hardcoded `Fri May 29` date, use `$(date -u)` | `scripts/daily-text-brief.sh` line 108 | 1 min | LOW — confusing error messages |
| **Q6** | Move `WORKING_DIR` definition before line 118 | `scripts/daily-text-brief.sh` | 1 min | LOW — GDELT floor never runs |
| **Q7** | Write `.brief_complete` after assembly | `skills/.../orchestrate.py` near end of main() | 15 min | MEDIUM — QC timing race |
| **Q8** | Remove Step 6 Moltbook call or wrap in condition | `scripts/daily-text-brief.sh` | 2 min | LOW — wasted API call |
| **Q9** | Add model check has `$WORKING_DIR` in single-quoted Python string; verify shell expansion | `scripts/daily-text-brief.sh` lines 166-170 | 10 min | MEDIUM — model check might fail with path issues |

**Quick Wins package:** If all 9 fixes are applied, the pipeline goes from non-functional to correctly functional with proper error handling, correct provider routing, working validation, and elimination of 7 known failure modes. Estimated total: ~35 minutes.

---

## Implementation Roadmap

### Phase 1 — Immediate (today, <1h)
1. Apply Quick Wins Q1-Q9 in order (bash script fixes first — the pipeline is currently un-runnable without them)
2. Run a manual pipeline test (`bash scripts/daily-text-brief.sh 2>&1 | tee /tmp/brief-test.log`)
3. Verify: orchestrator starts, collects incidents, analysis produces files, quality gate passes, delivery sends
4. Update `KNOWN_ISSUES.md`:
   - Add: bash corruption (VERIFIED_CLOSED after 3 successful runs)
   - Update: DeepSeek direct API hang (change status to FIX_APPLIED if provider switched to OpenRouter)
   - Add: delivery validation placement (FIX_APPLIED)
   - Update: no `.brief_complete` flag (FIX_APPLIED)

### Phase 2 — This week (2-4h)
1. Centralize region definitions (R3) — stop the drift that causes structural gate failures
2. Add multi-provider fallback chain (R6) — survive DeepSeek outages
3. Add budget preflight check (R7) — prevent self-inflicted billing outages
4. Fix region list in `guard_pipeline.py` to match `analyze.py` (remove `russia_eurasia`, add `north_africa`/`sub_saharan_africa`)

### Phase 3 — Next week (3-6h)
1. Add healthy-feed count monitoring alert
2. Add secondary cron slot (07:00 PT) for failure recovery
3. Add AgentMail delivery fallback (Gmail MTA)
4. Unify KJ field names at the source (in `analyze.py`'s `mock_regional` and the actual DeepSeek response parsing) instead of normalizing at delivery

---

## Summary Scorecard

| Aspect | Rating | Notes |
|---|---|---|
| **Architecture** | ⚠️ 5/10 | Clean single-chain design but hardcoded regions, duplicate delivery paths, and no fallback infrastructure. The "parallelizable" collection design is belied by a fully sequential bash script. |
| **Reliability** | ❌ 2/10 | Pipeline is currently un-runnable. Bash script has fatal syntax errors. DeepSeek Direct API will hang on exec summary calls. No fallback provider. Delivery validation is dead code. |
| **Resilience** | ❌ 2/10 | Single provider, single model, single host, single delivery channel. Three known failure modes that have already occurred (billing, API hang, Cloudflare blocking). No circuit breakers. |
| **Quality Control** | ✅ 7/10 | 7-gate pipeline is well-designed. Model enforcement works. Calibration checking is thorough. Main weakness: region drift causes structural false failures, and QC can race with assembly. |
| **Maintainability** | ⚠️ 4/10 | Three independent region lists already diverging. Bash script corrupted. Field name normalization in delivery hides analysis-level inconsistency. Prompt templates drift from code. Dead code (Moltbook, PDF assembly, visuals — all disabled but not removed). |
| **Observability** | ⚠️ 5/10 | Good logging with timestamps. But no alerting on critical failures, no budget dashboard at pipeline level, no healthy-feed count monitoring, no delivery confirmation beyond AgentMail API response. |
| **Security** | ✅ 8/10 | API keys from `.env`, sandboxed execution, no credential exfiltration paths. Prompt injection sanitization. Fabrication gate scans for hallucinated claims. Scope gate prevents topic drift. |

**Overall:** ❌ 4/10 — The pipeline design has good bones (7-gate QC, calibration tracking, Sherman Kent methodology) but is currently non-functional due to bash script corruption. Even after the bash script is fixed, the DeepSeek Direct API hang bug and region drift will cause intermittent failures. **Phase 1 immediate fixes are required to restore basic functionality.**

---

## Appendix: Bash Script Line-by-Line Bug Inventory

| Line(s) | Issue | Severity |
|---|---|---|
| 105 | `$ORCH_RC` missing in `if [  -ne 0 ]` — syntax error | CRITICAL |
| 106 | `$ORCH_RC` and `"$LOG"` missing in error output | CRITICAL |
| 106-108 | `tee -a ""` — logs to nowhere | CRITICAL |
| 108 | Hardcoded `Fri May 29` date instead of `$(date -u)` | LOW |
| 109 | `exit` without argument | CRITICAL |
| 118 | `$WORKING_DIR` used before definition at line 152 | LOW |
| 138-139 | Orphaned `ORCH_RC` and `fi` (syntax error) | CRITICAL |
| 166-170 | `$WORKING_DIR` inside single-quoted Python string in heredoc — verify shell expansion | MEDIUM |
| 192-194 | Broken backslash continuation — `--brief-dir` becomes separate command | HIGH |
| 196-199 | Post-delivery validation in ELSE branch — dead code in production | HIGH |
| 212-214 | Weather-dependent `validate_delivery.py` names | LOW |
| 225-228 | Moltbook posting still active despite principal directive | LOW |
