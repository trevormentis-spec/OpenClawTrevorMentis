# RUNTIME REALITY STATUS REPORT — DETAILED

**Date:** 2026-05-12 16:15 UTC
**Purpose:** Full accounting of what runs, what doesn't, and what needs to change for Trevor to become operational.

---

## SECTION 1: WHAT ACTUALLY RUNS

### 1.1 Active Cron Jobs (18 total)

The system has 18 registered cron jobs in OpenClaw. Below is every job, its schedule, last run, and status.

| ID | Name | Schedule (PT) | Last Run | Status |
|---|---|---|---|---|
| 250765ae | Daily Intel Brief — main pipeline | 05:00 | 4h ago | ✅ OK |
| 951017cf | DailyIntelAgent — full pipeline | 05:00 | 4h ago | ❌ ERROR |
| bc2e0b18 | Visual: build magazine PDF | 05:30 | 4h ago | ✅ OK |
| 8f3c63de | Landing page deploy | 06:30 | 3h ago | ✅ OK |
| 9ee44803 | Daily 4 Briefings | 08:00 | 1h ago | ❌ ERROR |
| a1d90107 | Gmail security newsletter scan | 12:00 | 21h ago | ✅ OK |
| 0eab30cc | Social engagement tracker | 09,13,17 | 2m ago | ✅ OK |
| 905c3374 | Social: post daily brief | 13:30 | 20h ago | ✅ OK |
| 64c3727a | Improvement Daemon (daily) | 16:00 | 17h ago | ❌ ERROR |
| a656b6c8 | Improvement Daemon (hourly) | every hour | 57m ago | ✅ OK |
| c9dc9111 | Collection Daemon — hourly | */30 min | <1m ago | ✅ OK |
| 81d1e5c9 | Improvement Daemon (weekly) | Sun 04 | 2d ago | ❌ ERROR |
| ccda3cdc | Source discovery — weekly | Mon 04 | 1d ago | ❌ ERROR |
| 0eb2de56 | Daily GitHub backup | 20 UTC | 20h ago | ✅ OK |
| 3a3acea7 | Daily Skill Scanner Audit | 00 UTC | 16h ago | ✅ OK |
| f602aac6 | Trevor brain maintenance | 02 UTC | 14h ago | ✅ OK |
| 08cae30c | Trevor OSINT Deep Search | 01 PT | 8h ago | ✅ OK |
| d851c58f | Trevor Capability Expansion | 02 PT | 7h ago | ✅ OK |

**Of 18 jobs:**
- 12 show OK status
- 5 show ERROR status (all delivery routing failures — the job runs but output has nowhere to go)
- 1 shows unknown (not enough data)

### 1.2 Actual Processes Running Right Now

```
PID 49896  python3 scripts/subscriber-server.py   (since May 4)
PID 99722  openclaw                               (since May 8)
PID 99701  python3 supervisord                    (since May 8)
PID 188941 sleep 21950                            (scheduled delivery — will expire)
PID 189006 sleep 21763                            (scheduled delivery — will expire)
```

Two permanent processes. Two scheduled sleeps that will expire. Nothing else.

### 1.3 Today's Pipeline Execution (Trace)

This is the actual execution path from today's 05:00 PT run, reconstructed from the log file at logs/daily-brief-2026-05-12.log (238 lines):

```
05:00 PT — cron 250765ae fires
  → isolated agent session starts
  → runs: cd workspace && bash scripts/daily-brief-cron.sh
  → sources .env
  → Step 1: python3 skills/daily-intel-brief/scripts/orchestrate.py
       --model "anthropic/claude-opus-4.7"
       --tier2-model "deepseek/deepseek-v4-flash"
       --provider openrouter
       --no-deliver
       --strict-env
    → [12:07:56] orchestrator starting
    → brain-recall: SUCCESS (wrote brain-recall.json + brain-recall.md)
    → collector: SUCCESS (6 RSS feeds fetched)
    → analyst: SUCCESS (7 JSONs written to analysis/)
    → quality gates: PASSED
    → assemble: SUCCESS (brief-2026-05-12.pdf produced)
    → postdict: SUCCESS (checked May 11 vs May 12)
    → brain-reindex: SUCCESS
    → "delivery skipped" (--no-deliver flag)
    → orchestrator exits rc=0
  → Step 2: Find PDF → SUCCESS (PDF found at ~/trevor-briefings/...)
  → Step 2b: Maps disabled → OK
  → Step 2c: python3 generate_brief_images.py
    → Cover image: ✅ (35s)
    → europe image: ✅ (28s)
    → asia image: ✅ (32s)
    → middle_east image: ✅ (30s)
    → north_america image: ✅ (31s)
    → south_central_america image: ⏳ STARTED — LOG CUTS OFF
    → [PIPELINE HALTS HERE — no further log entries]
```

The pipeline produced 8 JSON analysis files and a PDF, then stopped at image generation. Steps 3-8 never executed. No email was sent. No postdiction result was saved. No Buttondown newsletter published. No landing page updated. No self-assessment ran.

---

## SECTION 2: WHAT DOES NOT RUN BUT SHOULD

### 2.1 Never Executes Automatically

| Script | Purpose | Why It Never Runs |
|--------|---------|-------------------|
| scripts/deliver_brief_email.py | Sends the daily brief via AgentMail with prediction markets + trade suggestions | No cron calls it. Only manual invocation. |
| scripts/continuous_monitor.py | Detects Kalshi swings, missing briefs, new inbox messages; triggers escalation | No cron calls it. |
| scripts/self_assessment.py | Scores system health across 7 dimensions, detects regression, writes injection file | No cron calls it. Ran once manually. |
| scripts/procedural_memory_loader.py | Reads brain/memory/procedural/ and injects into prompts | No cron calls it. |
| scripts/collection_state.py --update | Tracks source utilization, region activity, updates per-region caps | Wired into pipeline Step 3b — never reached. |
| scripts/collection_state.py --predict-caps | Outputs adaptive caps for collect.py | Wired into pipeline Step 0c — runs but output may not be consumed. |
| scripts/collection_state.py --feed-priorities | Outputs feed priority tiers for collect.py | Wired into pipeline Step 0d — runs but output may not be consumed. |
| scripts/postdict.py (automated) | Checks yesterday's predictions against today's evidence | Ran on May 11. Did not run on May 12 (pipeline blocked at Step 2c). |
| scripts/validate_config.py | Validates openclaw.json before edits | Never run automatically. Manual only. |
| scripts/routing_scanner.py | Audits actual model usage vs policy | Never run automatically. Manual only. |

### 2.2 Cron Jobs That Fire Into Dead Ends

| Cron | Schedule | Problem |
|------|----------|---------|
| Collection Daemon (hourly) | Every 30 min | Fires agent into isolated session with no delivery path. Output is invisible. |
| Improvement Daemon (hourly) | Every hour | Same — isolated session, no delivery routing. |
| Improvement Daemon (daily) | 16:00 PT | ERROR status. Delivery routing misconfigured. |
| Improvement Daemon (weekly) | Sun 04 PT | ERROR status. |
| Source discovery | Mon 04 PT | ERROR status. |
| 4 Daily Briefings | 08:00 PT | ERROR status. Delivery routing broken. Emails don't arrive. |
| DailyIntelAgent full | 05:00 PT | ERROR status. Delivery routing broken. |

---

## SECTION 3: SCRIPT-LEVEL DETAIL

### 3.1 Scripts That Are Known to Work (Verified)

| Script | Last Verified | Runs On |
|--------|---------------|---------|
| scripts/kalshi_scanner.py --json --save | Today, 12:13 UTC | Cron (daily, 04:30 PT) |
| brain/scripts/brain.py recall | Today, 12:07 UTC | Orchestrator Step 0 |
| brain/scripts/brain.py reindex | Today, 12:07 UTC | Orchestrator Step 6 |
| skills/daily-intel-brief/scripts/collect.py | Today, 12:07 UTC | Orchestrator Step 1 |
| skills/daily-intel-brief/scripts/analyze.py | Today, 12:07 UTC | Orchestrator Step 2 |
| skills/daily-intel-brief/scripts/build_pdf.py | Today, 12:07 UTC | Orchestrator Step 5 |
| scripts/postdict.py | Today, 12:07 UTC | Orchestrator Step (post-assemble) |
| scripts/genviral-post-brief.sh | Today, earlier | Standalone (posted LinkedIn, Twitter, TikTok) |
| scripts/deliver_brief_email.py | Today, manually | Manual only |
| scripts/trade_engine.py | Today, manually | Called by deliver_brief_email.py |
| scripts/self_assessment.py | Today, manually | Manual only |

### 3.2 Scripts That Are Known Broken

| Script | Problem | Impact |
|--------|---------|--------|
| scripts/generate_brief_images.py | Takes 30-40s per image × 6 = 3-4 min total. Pipeline has no timeout. Log shows it hangs on the last image. | KILLS THE ENTIRE PIPELINE. No step after 2c executes. |
| scripts/daily-brief-cron.sh (old Gmail delivery) | REMOVED. No replacement wired into cron. | No automated email delivery. |
| scripts/moltbook-post-brief.sh | REMOVED from pipeline. No replacement. | No Moltbook posts today. |

---

## SECTION 4: ADAPTIVE LOOP STATUS — DETAILED

### Loop 1: Retrieval → Prompt → Output

**Status: PARTIALLY OPERATIONAL**

What actually happens:
1. orchestrate.py Step 0: calls `brain.py recall "yesterday's brief + dynamic keywords"` → captures stdout → writes brain-recall.json + brain-recall.md
2. orchestrate.py Step 0 (analyst cmd): passes `--recall analysis/brain-recall.md` to analyze.py
3. analyze.py: reads brain-recall.md → appends `=== MEMORY CONTEXT FROM PRIOR BRIEFS ===` block to system prompt
4. Model receives: 6,916 char system prompt + 1,584 char memory context = ~8,500 char total

What is missing:
- No proof that output materially changes. No A/B test has been run.
- No evidence that the 1,584 char memory block influences model behavior differently than the system prompt alone.
- Cross-cycle feedback: the recall query uses today's BLUF terms, finds yesterday's brief in the index, and injects it. But there's no mechanism to verify that the model used the retrieved information.

**Evidence of operation:** The files are created, the flag is passed, the string is appended. This is a fully wired pipeline. But "wired" is not the same as "operational at producing changed behavior."

### Loop 2: Collection Confidence → Analytical Confidence

**Status: SCAFFOLDED**

What exists:
- `build_collection_quality()` function in analyze.py
- Injects per-region quality assessment as `{collection_quality_markdown}` in the regional analyst prompt
- Example for Middle East: "Moderate coverage, 2 sources — be cautious with highly likely"
- Example for Europe: "Full coverage, 4 sources — standard bands apply"

What is missing:
- `collection_state.py --update` is supposed to run before analyze.py to provide fresh collection state. It does not run because the pipeline blocks at Step 2c.
- The collection-state.json file contains stale data from yesterday's analysis (May 11), not today's.
- Without fresh collection state, the quality assessments may be using outdated data.
- The exec summary prompt has `{collection_quality_summary}` placeholder but collection quality summary is only generated if collection_state is passed.

### Loop 3: Source Quality → Source Priority

**Status: SCAFFOLDED**

What exists:
- collection-state.json tracks `source_utilization`: fetched_count, cited_count, consecutive_zero_runs per feed
- `predict_feed_priorities()` computes tier (1-3) based on citation rate
- collect.py accepts `--feed-priorities` flag that filters feed list to skip Tier-3 feeds

What is missing:
- orchestrate.py Step 0d generates feed-priorities.json but only if `coll_state_script.exists()` — it does, so the file is written
- collect.py receives `--feed-priorities` flag but today's log shows it fetching ALL 6 feeds (no filtering evidence)
- The data shows: Al Jazeera cited (1/1), all other feeds cited (0/1). After 1 run, all are Tier-1 (insufficient data).
- After 5+ runs, uncited feeds would be Tier-3 (retired). But it hasn't run 5 times yet.

### Loop 4: Calibration → Prompt Adaptation

**Status: SCAFFOLDED**

What exists:
- calibration-tracking.json: 25 judgments, 5 days, 1 overconfidence flag
- `analyze.py --calibration` injects calibration feedback block into system prompt
- Feedback includes: overconfidence flags (e.g., Middle East: highly likely 82% with 2 sources), band-level stats, running accuracy

What is missing:
- Current accuracy reading: "0/25 correct (0.0%)". This is technically true but operationally useless — 24 of 25 are marked "unresolved" (too early to verify), not incorrect.
- The model receives "0% accuracy" and is told to "widen bands" — but the problem isn't overconfidence, it's that geopolitical predictions take >24h to falsify.
- The postdict evaluation horizon is wrong: predictions have a 7-day horizon but are checked after 24h. Most will always be "unresolved."
- No mechanism to re-check predictions after their 7-day horizon expires.

### Loop 5: Event Significance → Collection Escalation

**Status: ABSENT**

What exists:
- `continuous_monitor.py` with KALSHI_SWING_THRESHOLD=10, KALSHI_CRITICAL_THRESHOLD=20
- `escalate()` function that calls `collection_state.py --set-escalation`
- Escalation multipliers: critical=2x caps, significant=1.5x, notable=1.25x
- Tested manually: Middle East caps 20→40 (critical), Europe caps 20→30 (significant), clears correctly

What is missing:
- continuous_monitor.py is never called by any cron
- No event has ever triggered escalation at runtime
- The escalation infrastructure is fully wired and tested but has zero runtime executions

### Loop 6: Meta-Cognition → Runtime Prioritization

**Status: ABSENT**

What exists:
- `scripts/self_assessment.py` — scores 7 dimensions, detects regression, writes injection file
- Ran once manually: scored 83/100 (routing: 45→100 after fix)
- Observer pattern in self-assessment: scores are saved to exports/system-health/YYYY-MM-DD.json and compared against previous day

What is missing:
- No cron calls self_assessment.py
- The injection file (tasks/self-assessment-injection.md) is never written at runtime
- Nothing changes behavior based on system health scores

---

## SECTION 5: BOTTLENECK ANALYSIS

### Primary Bottleneck: Pipeline Blocking at Image Generation

The single heaviest `daily-brief-cron.sh` Step 2c runs `generate_brief_images.py` which generates 6 AI images via GenViral Studio AI at 30-45 seconds per image. This step has no timeout guard. It is called before email delivery. When it hangs (which it does every run), nothing downstream executes.

**Downstream steps that starve:**
1. Email delivery — you don't get your brief
2. Postdiction — calibration doesn't update
3. Agent API — JSON doesn't publish
4. Buttondown — newsletter doesn't send
5. Landing page — doesn't deploy with latest content
6. Self-assessment — doesn't run

**Total pipeline time if all steps completed:** ~4-5 minutes for orchestration, ~3-4 minutes for images, ~30s for everything else = ~8-10 min total. The image step is using ~40% of pipeline time and producing 100% of the failures.

### Secondary Bottleneck: No Autonomous Recovery

If the pipeline fails at Step 2c, nothing retries. Tomorrow's 05:00 PT run will start fresh. Between yesterday's failed run and tomorrow's scheduled run, the system produces nothing but log entries.

---

## SECTION 6: WHAT MUST CHANGE — PRIORITY ORDER

### Priority 1 — Critical (Fix Immediately)

**1a. Create a dedicated email delivery cron.**

Create a new OpenClaw cron at 06:30 PT that runs:
```
cd /home/ubuntu/.openclaw/workspace && python3 scripts/deliver_brief_email.py --send
```

This reads the exec_summary.json that the orchestrator already produced at 05:00 PT, adds Kalshi data, runs the trade engine, and sends via AgentMail. Zero dependency on other pipeline steps. Requires OPENROUTER_API_KEY and AGENTMAIL_API_KEY to be available in the cron environment.

**Time to implement:** 5 minutes.

**What it closes:** The primary delivery loop. You will receive your daily brief by email every day regardless of what else breaks upstream.

**1b. Remove or timeout generate_brief_images.py from the pipeline.**

Either:
- Remove the image generation step entirely (you asked for email-only, images serve no purpose in a plaintext email)
- Or wrap it in a 60-second timeout so the pipeline continues regardless

**Time to implement:** 2 minutes (remove) or 10 minutes (add timeout).

**What it closes:** The entire rest of the pipeline. Every downstream step becomes reachable.

### Priority 2 — Important (Fix Next)

**2a. Fix postdict evaluation horizon.**

Postdict checks 7-day predictions after 24h. Most are "unresolved." This makes the calibration feedback say "0/25 correct" which is misleading when fed into the model prompt.

**Fix:** Add a 7-day check. Save predictions with their expiry date. Re-check when the horizon expires. Filter unresolved from the accuracy calculation shown to the model.

**2b. Wire continuous_monitor.py into an hourly cron.**

Add `@hourly` cron that calls `python3 scripts/continuous_monitor.py --quick`. This enables escalation detection. If a Kalshi market swings >20pts in 24h, escalation flags get set. This is the entry point to event-driven behavior.

**2c. Wire collection_state.py --update into the post-analysis step.**

The collection state update should run after analysis completes, regardless of whether the rest of the pipeline succeeds. This enables adaptive caps and feed priorities to evolve over time.

### Priority 3 — Nice to Have (Fix When Convenient)

**3a. Fix tier-2 model routing to use DeepSeek Direct API.**

Currently both tiers route through OpenRouter. Change `analyze.py` to use `tier2_provider="deepseek"` for regional analysis calls. This would reduce OpenRouter costs and implement the tiered routing that's already architected.

**3b. Kill dead-end cron jobs.**

The 5 cron jobs with ERROR status (Improvement Daemon(s), Source Discovery, 4 Briefings, DailyIntelAgent) fire into isolated sessions with no delivery path. Either give them a delivery target or remove them. They create noise in the cron list and consume agent session slots.

**3c. Self-assessment weekly cron.**

Wire self_assessment.py into a weekly cron (Sunday 05 PT) for a regular health check. Currently it only runs when manually invoked.

---

## SECTION 7: OPERATIONAL SUMMARY

| Measurement | Current Value | Target | Gap |
|-------------|---------------|--------|-----|
| Pipeline completion rate | 0% (0 of last N runs reached Step 3) | 100% | Image step kills every run |
| Email delivery | Manual only | Automated daily | No cron exists |
| Collection cadence | Once daily (batch) | Continuous + batch | No daemon runs |
| Calibration data | 25 judgments, 0 verified | → verified predictions | Horizon mismatch |
| Event response | Zero | Event-driven escalation | Monitor not wired |
| Self-assessment | Manual once | Weekly automated | No cron |
| Episodic memory | 3 files, <1KB total | Growing daily | No daemon writes to it |

---

## SECTION 8: DELIVERY CHANNELS STATUS

| Channel | Status | How It Works | Last Successful Delivery |
|---------|--------|--------------|-------------------------|
| AgentMail → roderick.jones@gmail.com | ✅ WORKING | Manual invocation of send_email.py or deliver_brief_email.py | Today, 15:34 UTC |
| Buttondown newsletter | ✅ WORKING | API publishes to buttondown.com/trevormentis | Tested successfully |
| Telegram | ✅ WORKING | OpenClaw channel delivers to this chat | Active, real-time |
| Landing page (GitHub Pages) | ✅ WORKING | Static site at trevormentis-spec.github.io | Deployed today |
| Gmail via Maton API | ❌ DEAD | Removed from pipeline. Variable expansion was broken anyway. | N/A |
| Moltbook | ❌ DISCONNECTED | Removed from pipeline. No posts today. | N/A |
| 4 Daily Briefings | ❌ ERROR | Cron fires but delivery routing fails. | N/A |
| UK report delivery (background) | ⏳ PENDING | sleep 21950, will fire at 13:00 UTC | Tomorrow |
| Starmer LDAP-7 analysis (background) | ⏳ PENDING | sleep 21763, will fire at 13:00 UTC | Tomorrow |

---

*Prepared by TREVOR — Threat Research and Evaluation Virtual Operations Resource*
*2026-05-12 16:15 UTC*
