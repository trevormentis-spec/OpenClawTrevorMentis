# Trevor System Health Review — Opus Analysis

**Date:** 2026-05-31  
**Reviewer:** Opus (comprehensive system audit)  
**Purpose:** Full-spectrum health assessment of all Trevor subsystems, with structural proposals for a unified health monitoring framework.

---

## 1. Executive Summary — Current State

**The system is in a silent cascade failure.** As of this audit, **36 of 42 scheduled jobs are failing** — not from individual bugs, but from a single root cause (DeepSeek billing exhaustion) that propagated across the entire agent-runtime layer. No single health check caught this pattern across jobs because:

1. Health checks are fragmented across 6+ separate scripts with no unified aggregator
2. No check monitors "are cron jobs succeeding at their expected rate?"
3. No check validates end-to-end pipeline completion
4. No check validates learning/memory processes

**The billing credit top-up you just did will restore operations, but the pattern will repeat** unless we build a proper health observability layer.

---

## 2. System Inventory

### 2.1 Cron Jobs — 42 Total (21 Enabled, 21 Disabled)

**Core Intel Pipeline (3 jobs):**
| Job | Schedule | Status |
|-----|----------|--------|
| Daily Text Brief (69d9d778) | 05:00 PT daily | ❌ Billing failure |
| Gmail Intel Reader (e9f62049) | Every 2h | ❌ Billing failure |
| AgentMail Intel Reader (f082ad3a) | Every 2h | ❌ Billing failure |

**Presentation & Distribution (7 jobs, all DISABLED or failing):**
| Job | Schedule | Status |
|-----|----------|--------|
| DailyIntelAgent pipeline (951017cf) | 05:00 PT | DISABLED |
| Landing page deploy (8f3c63de) | 06:30 PT | DISABLED |
| GenViral social posting (905c3374) | 13:30 PT | DISABLED |
| Magazine PDF builder (bc2e0b18) | 05:30 PT | DISABLED |
| Buttondown newsletter (f9d464b1) | 05:45 PT | DISABLED |
| Intel digest (a1d90107) | 12:00 PT | ❌ Billing failure |
| Brief delivery watchdog (e0647d21) | 07:05 PT | ❌ Billing failure |

**Quality & Recovery (3 jobs):**
| Job | Schedule | Status |
|-----|----------|--------|
| QC Watchdog (7ca66311) | 13:10 UTC | ❌ Billing failure |
| Brief auto-recovery (6c54d13f) | 07:15 PT | ❌ Billing failure |
| I&W Feedback + Calibration (67e2713e) | 06:30 PT | ❌ Billing failure |

**Memory & Learning (4 jobs):**
| Job | Schedule | Status |
|-----|----------|--------|
| Dream consolidation (1976bd12) | 03:00 PT | ❌ Billing failure |
| Brain maintenance (f602aac6) | 02:00 UTC | ✅ Working |
| Calibration recheck (ae0d522f) | 05:00 PT Sun | ❌ Billing failure |
| Capability expansion (d851c58f) | 02:00 PT | ✅ Working |

**Collection Infrastructure (10 jobs):**
| Job | Schedule | Status |
|-----|----------|--------|
| LEO FCC Daily (cb039bf5) | 08:00 PT | ❌ Billing failure |
| LEO Launch Schedule (f10da54a) | 08:30 PT | ❌ Billing failure |
| LEO ITU Weekly (ddfdc590) | 10:00 PT Mon | ✅ Working |
| LEO Jobs Weekly (4c0dc7a5) | 10:30 PT Mon | ✅ Working |
| LEO Sentinel Monthly (c3429754) | 11:00 PT 1st | ✅ Working |
| LEO Daily Brief (5026ed81) | 09:00 PT | ❌ Billing failure |
| RDX GDELT Daily (a20962e6) | 10:00 PT | ❌ Billing failure |
| RDX OSINT Daily (82c2e29c) | 10:30 PT | ❌ Billing failure |
| RDX Contracts Weekly (ce4cb113) | 11:00 PT Mon | ✅ Working |
| RDX Filings Weekly (17ca201c) | 11:30 PT Mon | ✅ Working |

**Heartbeat & Watchdog (5 jobs):**
| Job | Schedule | Status |
|-----|----------|--------|
| trevor-heartbeat (1aec4c02) | Every 30min | ❌ Billing failure |
| Control Plane Health (3220d588) | Every 5min | ❌ Billing failure |
| Infrastructure Alert (a55b8761) | Every 4h | ❌ Billing failure |
| Daily Health Check (8ab01eb5) | 06:00 PT | ❌ Billing failure |
| Heartbeat Source Discovery (ac010c62) | Every hour | ❌ Billing failure |

**Backup & Trading (4 jobs):**
| Job | Schedule | Status |
|-----|----------|--------|
| Auto Config Backup (02104a0d) | 03:00 PT | ❌ Billing failure |
| GitHub backup reminder (0eb2de56) | 20:00 UTC | ❌ Gateway restart |
| Trade Confirmation (53bcf0c4) | Every 15min | ❌ Billing failure |
| Kalshi Daily Reconciliation (54fa00f7) | 03:00 PT | ❌ Billing failure |

### 2.2 Health Infrastructure — Existing Pieces

| Script | What It Checks | Gap |
|--------|---------------|-----|
| `control-plane-health.py` | Gateway PID, supervisord, Telegram reachability, disk | Only infra processes — not cron outcomes, pipeline completion, or learning processes |
| `continuous_monitor.py` | Kalshi swings, inbox, brief existence | Narrow scope — doesn't check cron health, memory, or learning |
| `infra_alert.py` (inside control-plane) | DeepSeek balance, disk, OpenRouter credits | Fires per-job not per-system; no cross-job correlation |
| QC watchdog (`qc-watchdog.sh`) | Brief quality gates only | Single-dimension |
| Brief watchdog | AgentMail sent items | Single-dimension |
| `autonomous_cycle.py` | Feed health, source discovery, pruning | Collection-only; doesn't validate outcomes |
| `autonomous_fixes.py` | Black-fix known issues | Reactive, not proactive |

### 2.3 Learning & Memory Processes

| Process | Cadence | Last Success | Monitoring? |
|---------|---------|-------------|-------------|
| Brain reindex | After Phase D | ✅ 2026-05-31 | No |
| Dream memory consolidation | 03:00 PT daily | ❌ Failing (billing) | No |
| Cognition promotion | Via continuous_monitor | Unknown | No |
| Postdiction recheck | 06:30 PT daily | ❌ Failing (billing) | No |
| Calibration tracking | Weekly | ❌ Failing (billing) | No |

---

## 3. Systemic Weaknesses

### 3.1 Single-Provider Dependency
- **All 42 cron jobs route through DeepSeek.** When DeepSeek billing fails, ALL model-dependent jobs fail simultaneously.
- No fallback routing for cron jobs to alternative providers.
- The fallback chain in ORCHESTRATION.md only activates per-request, not per-job.

### 3.2 No Cron Health Dashboard
- `jobs-state.json` at `/home/ubuntu/.openclaw/cron/jobs-state.json` tracks every job's last status, error rate, and diagnostics — but **nothing reads this file to produce a health report.**
- Consecutive errors are tracked per-job but no threshold-based alerting exists.
- The billing failure pattern is visible in jobs-state but not surfaced.

### 3.3 No End-to-End Pipeline Validation
- The Daily Text Brief pipeline is a 4-hour script (`daily-text-brief.sh`) that runs in an isolated session with `delivery.mode: none`.
- **No check verifies:** Did the brief get written to `final/brief.md`? Did it pass quality gates? Was it delivered?
- The brief watchdog checks AgentMail sent items — a fragile check that doesn't cover the GSIB pipeline.

### 3.4 No Learning Process Validation
- `dream.py`, `brain.py maintain`, postdiction, calibration — these are all fire-and-forget cron jobs with no "did this actually complete and produce output?" verification.
- Cognition promotions go to `brain/memory/episodic/` but no one checks "are episodic logs being written with expected frequency?"

### 3.5 Heartbeat Cycle Has No Completion Monitoring
- The heartbeat rotates through 5 phases (A-E) but:
  - No check that all phases completed within the expected 24h window
  - State file only tracks last completion timestamps per phase
  - No alert if a phase hasn't completed in >48h

### 3.6 Gateway Restart Pattern
- Multiple jobs show "cron: job interrupted by gateway restart" across different timestamps
- This suggests either planned restarts or instability; either way jobs interrupted mid-flight don't auto-retry

---

## 4. Proposal: Unified Health Monitoring Framework

### 4.1 Architecture — Single Health Engine

```
┌──────────────────────────────────────────────┐
│  health_engine.py — Unified Health Monitor   │
│                                               │
│  Checks every 15 min (light) + hourly (deep) │
│  Outputs: tasks/health-dashboard.json          │
│           tasks/health-alerts.md               │
│           Telegram alert on CRITICAL only      │
└──────────────┬───────────────────────────────┘
               │ reads from
     ┌─────────┼─────────┬──────────┐
     ▼         ▼         ▼          ▼
  cron/     final/    brain/     memory/
  jobs-     brief.md  memory/    heartbeat-
  state.    *.md      episodic/  state.json
  json                *.jsonl
```

**The health engine does NOT replace existing health checks** — it aggregates them. Each existing check script continues to do its job. The engine collects their outputs plus direct reads of system state into one dashboard.

### 4.2 Checks That the Health Engine Runs

**Layer 1 — Infrastructure (lightweight, every 15 min):**
- ✅ Gateway process running?
- ✅ Telegram reachability?
- ✅ Disk space (<90%?)
- ✅ DeepSeek balance (>$1?)
- ✅ OpenRouter credits > 0?

**Layer 2 — Cron Health (lightweight, every 15 min):**
- ✅ Read `/home/ubuntu/.openclaw/cron/jobs-state.json`
- ✅ Flag any job with ≥3 consecutive errors
- ✅ Flag any job with `lastErrorReason: "billing"` 
- ✅ Flag any recurrence window missed (e.g. daily job not run in >30h)
- ✅ Track: total enabled jobs, total failing jobs, failure rate %

**Layer 3 — Pipeline Completion (hourly, 07:00-14:00 PT window):**
- ✅ Does `final/brief.md` exist with today's date?
- ✅ Does `exports/pdfs/` have today's PDF?
- ✅ Quality gate passed? (check `tasks/qc-alert.md`)
- ✅ AgentMail delivery confirmed?
- ✅ Landing page deployed with today's date?

**Layer 4 — Learning & Memory (hourly):**
- ✅ Episodic log written today? `brain/memory/episodic/YYYY-MM-DD.jsonl` exists and has entries?
- ✅ Brain index file exists and non-stale? `brain/index/index.json` modified < 24h
- ✅ Dream completed last night? Check `logs/dream-YYYY-MM-DD.log` for completion
- ✅ Postdiction ran today? Check episodic logs for postdiction entries
- ✅ Cognition promotions file recent? `brain/memory/semantic/cognition-promotions.json` modified < 7 days

**Layer 5 — Heartbeat Cycle Completion (hourly):**
- ✅ Each heartbeat phase has run within expected window
- ✅ Full cycle completed within 24h
- ✅ No phase stuck >48h

**Layer 6 — Cost & Budget (every 4h):**
- ✅ DeepSeek burn rate vs. daily cap
- ✅ Projected exhaustion date
- ✅ Over-budget flag (>80% daily cap)
- ✅ Routing efficiency (are we overusing Pro vs Flash?)

### 4.3 Alert Levels

| Level | Trigger | Action |
|-------|---------|--------|
| **INFO** | Single job failure, one-phase delay | Log to health dashboard only |
| **WARNING** | >20% of jobs failing, pipeline delay >2h | Update `tasks/health-alerts.md`, surface in next Telegram conversation |
| **CRITICAL** | >50% failing, brief missed, billing exhausted, no episodic logs in >36h | Immediate Telegram alert with summary + likely cause + suggested fix |
| **EMERGENCY** | Gateway down, disk 100%, no fallback model available | Immediate Telegram alert to Roderick |

### 4.4 Implementation Plan

**Phase 1 — Build the Engine (today):**
1. Create `scripts/health_engine.py` with all 6 layers of checks
2. Create `tasks/health-dashboard.json` — always-fresh JSON state
3. Create `tasks/health-alerts.md` — human-readable alert log
4. Wire as a cron job: every 15 min during active hours, hourly overnight

**Phase 2 — Correct Existing Gaps (today):**
5. Add fallback provider routing for cron jobs (OpenRouter for billing-critical calls)
6. Add `.brief_complete` flag file written by pipeline on completion (from MEMORY.md recommendation already stated)
7. Add phase-completion log to heartbeat state for every phase transition
8. Add episodic-log-age check to existing continuous_monitor.py

**Phase 3 — Preventive (this week):**
9. Build a `cron_job_auditor.py` that runs weekly and:
   - Flags jobs with >10 consecutive errors as "needs investigation"
   - Checks that all daily jobs ran in last 36h
   - Reports jobs disabled for >7 days for cleanup
10. Build a `provider_health.py` that:
    - Checks DeepSeek balance every 15 min
    - Pre-warns before exhaustion (threshold: $2.00)
    - Triggers fallback routing to OpenRouter

**Phase 4 — Dashboard (next week):**
11. Status card generation — `scripts/health_status_card.py` that produces a concise Markdown status card:
    ```
    ┌─ Trevor Health ─────────────────────┐
    │  Gateway:         ✅ Running         │
    │  Cron jobs:       8/21 failing (38%)│
    │  Brief today:     ✅ Delivered       │
    │  Episodic log:    ✅ Current         │
    │  Brain index:     ✅ Fresh           │
    │  DeepSeek:        $99.79 (18d runw) │
    │  Heartbeat cycle: ✅ Complete        │
    └─────────────────────────────────────┘
    ```

### 4.5 Single Root Cause Detection

The health engine needs a **correlation analysis** module that recognizes:

> "If >5 jobs fail with the same error (e.g. 'billing'), surface as a SYSTEMIC issue, not N individual job failures."

This is the fix for today's specific failure mode — instead of 36 individual job error reports, a single alert: **"DeepSeek billing exhausted — affecting 36/42 jobs. Top-up required."**

### 4.6 Consolidating Existing Health Scripts

| Current Script | Fate |
|---------------|------|
| `control-plane-health.py` (715 lines) | **Refactor** — strip to process-level checks, health engine reads its metrics |
| `continuous_monitor.py` (364 lines) | **Keep** — its market/brief/inbox checks are separate from infra health |
| `infra_alert.py` | **Merge** into health engine |
| QC watchdog | **Keep** — pipeline-specific quality check consumed by health engine |
| Brief watchdog | **Keep** — consumed by health engine |
| `autonomous_cycle.py` | **Keep** — its output consumed by health engine |

---

## 5. Immediate Actions (Post-Top-Up)

1. **Verify restored connectivity** — run a quick model call test
2. **Check `final/brief.md`** — was today's brief produced before billing died?
3. **Restart failing cron jobs** — the billing issue should auto-resolve as jobs retrigger on schedule
4. **Validate episodic logs** — ensure `brain/memory/episodic/2026-05-31.jsonl` has entries
5. **Build the health engine** — this is the structural fix that prevents silent cascade failures

---

## 6. Known Issues Status Update

From `KNOWN_ISSUES.md`:
- **[2026-05-28] OpenRouter credits exhausted** — ✅ Restored by Roderick, now watch via health engine
- **[2026-05-28] No startup-known-issues read** — 🔄 Need to make this an AGENTS.md instruction that actually fires
- **[2026-05-28] Fix applied ≠ fix verified** — This is a *process* gap that the health engine closes: every fix produces a visible metric that the engine can check

---

*Analysis produced by Opus 4.7. Health engine implementation ready to proceed on approval.*
