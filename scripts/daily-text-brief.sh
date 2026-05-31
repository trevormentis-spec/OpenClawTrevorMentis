#!/usr/bin/env bash
#==============================================================================
# daily-text-brief.sh — Text-only Daily Intel Brief (2026-05-23 v2 — HARDENED)
#
# Pipeline:
#   1. Pre-collection: prediction market scan, calibration directives, source discovery
#   2. Orchestrator: collect.py (385+ feeds) → analyze.py (10 regions, V4 Pro ONLY)
#   3. QUALITY GATE (standalone — runs AFTER orchestrator, BEFORE delivery)
#   4. Delivery: AgentMail to trevor_mentis@agentmail.to → forwarded to Roderick
#   5. Postdict: calibration tracking
#   6. Moltbook: post brief to agent social network (r/builds)
#
# Models: DeepSeek V4 Pro for ALL analysis tiers (NO FALLBACK TO FLASH)
# Delivery: AgentMail to trevor_mentis@agentmail.to → forwarded to Roderick
# Constraints: NO visuals, NO PDF, NO social, NO Mexico pipeline, NO Gmail delivery
# Reliability: flock lock prevents duplicate runs, quality gate blocks bad output
#
# Schedule: Triggered by OpenClaw cron at 05:00 PT
# Flow:     05:00 PT — pre-collection
#           05:15 PT — orchestrator (collect + analyze)
#           05:45 PT — quality gate
#           06:00 PT — AgentMail delivery (only if gate passes)
#==============================================================================
set -uo pipefail

REPO="/home/ubuntu/.openclaw/workspace"
DATE_UTC=$(date -u +%Y-%m-%d)
LOG="$REPO/logs/daily-brief-${DATE_UTC}.log"
LOCKFILE="/var/lock/daily-brief.lock"
WORKING_DIR="$HOME/trevor-briefings/${DATE_UTC}"
mkdir -p "$REPO/logs"

# =========================================================================
# FLOCK LOCK — prevent duplicate runs
# =========================================================================
exec 200>"$LOCKFILE"
if ! flock -n 200; then
    echo "[$(date)] FATAL: Another daily brief is already running (lock held on $LOCKFILE). Aborting." | tee -a "$LOG"
    exit 1
fi

echo "=== Daily Text Brief — ${DATE_UTC} ===" | tee -a "$LOG"
echo "Started at $(date -u)" | tee -a "$LOG"

# Source environment with export (cron doesn't inherit shell env)
set -a
source "$REPO/.env" 2>/dev/null || true
set +a
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-}"
export AGENTMAIL_API_KEY="${AGENTMAIL_API_KEY:-}"
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}"
export AVAILABLE_PROVIDER="${AVAILABLE_PROVIDER:-}"
cd "$REPO"

# =========================================================================
# STEP 0b: CALIBRATION ACCURACY CHECK — pre-flight calibration audit
# =========================================================================
# Runs before collection to check whether calibration has drifted.
# Non-fatal — reports findings but doesn't block the pipeline.
# =========================================================================

echo "--- Calibration accuracy check ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/calibration_loop.py" --check >> "$LOG" 2>&1
set -e 2>/dev/null || true

# =========================================================================
# STEP 1: PRE-COLLECTION
# =========================================================================

# Step 1a: Compile calibration directives from postdiction history
echo "--- Compiling calibration directives ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/compile_calibration_directives.py" >> "$LOG" 2>&1
set -e 2>/dev/null || true

# Step 1b: Source discovery — find new RSS/sources
echo "--- Source discovery ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/source_discovery.py" >> "$LOG" 2>&1
set -e 2>/dev/null || true

# Step 1c: Kalshi prediction market scan
echo "--- Scanning prediction markets ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/kalshi_scanner.py" --save >> "$LOG" 2>&1
set -e 2>/dev/null || true

# Step 1d: [REMOVED] Simmer market signal overlay — trading desk archived 2026-05-31
# Commented rather than removed to preserve line numbering for any external references.

# =========================================================================
# STEP 1e: PROVIDER HEALTH CHECK — pre-flight probe
# =========================================================================
# Tests all three providers before spending time on collection.
# Exits gracefully: aborts only if ALL providers fail.
# Exports AVAILABLE_PROVIDER for orchestrator consumption.
# =========================================================================

echo "--- Provider health check (pre-flight) ---" | tee -a "$LOG"
set +e
HEALTH_CHECK=$(python3 "$REPO/scripts/provider_health_check.py" --json 2>&1)
HEALTH_RC=$?
set -e 2>/dev/null || true

# Log the health check results
echo "$HEALTH_CHECK" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    providers = data.get('providers', [])
    for p in providers:
        icon = {'ok': '✅', 'degraded': '⚠️', 'failed': '❌'}.get(p['status'], '❓')
        bill = ' [BILLING]' if p.get('billing_issue') else ''
        lat = f\"{p['latency_ms']}ms\" if p['latency_ms'] >= 0 else 'N/A'
        print(f\"  {icon} {p['provider']}: {p['status']}{bill} ({lat})\")
        if p.get('reason'):
            print(f\"     Reason: {p['reason']}\")
    print(f\"Exit code: {data.get('exit_code')}\")
except Exception as e:
    print(f\"Health check parse error: {e}\")
" >> "$LOG"

if [ "$HEALTH_RC" -eq 1 ]; then
    echo "FATAL: ALL providers failed health check. Aborting pipeline." | tee -a "$LOG"
    echo "=== Daily Text Brief FAILED — ${DATE_UTC} ===" | tee -a "$LOG"
    exit 1
fi

# Export the best available provider for orchestrator use
export AVAILABLE_PROVIDER=$(echo "$HEALTH_CHECK" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    providers = data.get('providers', [])
    # Prefer openrouter > anthropic > deepseek
    for name in ['openrouter', 'anthropic_direct', 'deepseek_direct']:
        for p in providers:
            if p['provider'] == name and p['status'] == 'ok':
                print(name)
                sys.exit(0)
    print('none')
except:
    print('none')
" 2>/dev/null)

echo "Available provider: ${AVAILABLE_PROVIDER:-none}" | tee -a "$LOG"

# =========================================================================
# STEP 2: ORCHESTRATOR — collect + analyze
# =========================================================================
#
# Calls the orchestrator which runs:
#   - collect.py (259 RSS feeds + web search fallback, 10 regions)
#   - analyze.py (10 regional analyses + exec summary + red team, DeepSeek V4 Pro)
#
# NO FALLBACK. If the orchestrator fails, we DO NOT deliver.
# Quality gate runs separately in Step 3.
# =========================================================================

echo "--- Running orchestrator (collect → analyze) ---" | tee -a "$LOG"
python3 skills/daily-intel-brief/scripts/orchestrate.py \
    --model "deepseek/deepseek-v4-pro" \
    --tier2-model "deepseek/deepseek-v4-pro" \
    --provider openrouter \
    --tier2-provider openrouter \
    --redteam-model "deepseek/deepseek-v4-pro" \
    --redteam-provider openrouter \
    --no-deliver \
    >> "$LOG" 2>&1
ORCH_RC=${PIPESTATUS[0]}

# Fallback: if OpenRouter fails, try Anthropic Direct
if [ "${ORCH_RC}" -ne 0 ] && [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    echo "OpenRouter failed (rc=${ORCH_RC}), retrying with Anthropic Direct..." | tee -a "$LOG"
    python3 skills/daily-intel-brief/scripts/orchestrate.py \
        --model "anthropic/claude-opus-4.7" \
        --tier2-model "anthropic/claude-sonnet-4.5" \
        --provider openrouter \
        --tier2-provider openrouter \
        --redteam-model "anthropic/claude-sonnet-4.5" \
        --redteam-provider openrouter \
        --no-deliver \
        >> "$LOG" 2>&1
    ORCH_RC=${PIPESTATUS[0]}
fi

# If both failed, try DeepSeek Direct as last resort
if [ "${ORCH_RC}" -ne 0 ] && [ -n "${DEEPSEEK_API_KEY:-}" ]; then
    echo "Anthropic fallback failed (or skipped), retrying with DeepSeek Direct..." | tee -a "$LOG"
    python3 skills/daily-intel-brief/scripts/orchestrate.py \
        --model "deepseek/deepseek-v4-pro" \
        --tier2-model "deepseek/deepseek-v4-flash" \
        --provider openrouter \
        --tier2-provider openrouter \
        --redteam-model "deepseek/deepseek-v4-flash" \
        --redteam-provider openrouter \
        --no-deliver \
        >> "$LOG" 2>&1
    ORCH_RC=${PIPESTATUS[0]}
fi

if [ "${ORCH_RC}" -ne 0 ]; then
    echo "FATAL: Orchestrator failed with rc=${ORCH_RC} after all fallback attempts." | tee -a "${LOG}"
    echo "DELIVERY ABORTED — orchestrator must succeed before quality gate can run." | tee -a "${LOG}"
    echo "=== Daily Text Brief FAILED — ${DATE_UTC} ===" | tee -a "${LOG}"
    exit 1
fi

# =========================================================================
# STEP 2b: GDELT COLLECTION FLOOR â fills gaps for thin regions
# Uses GDELT 2.0 CSV exports (no API key needed). Non-fatal if unavailable.
# =========================================================================
echo "--- Running GDELT collection floor ---" | tee -a "$LOG"
set +e
if [ -f "$WORKING_DIR/raw/incidents.json" ]; then
    python3 "$REPO/scripts/gdelt_collector_v2.py" \
        --incidents "$WORKING_DIR/raw/incidents.json" \
        --max 15 \
        >> "$LOG" 2>&1
    GDELT_RC=$?
    if [ $GDELT_RC -ne 0 ]; then
        echo "WARNING: GDELT v2 collection floor failed with rc=$GDELT_RC (non-fatal)" | tee -a "$LOG"
    fi
else
    echo "WARNING: No incidents.json found yet â skipping GDELT floor" | tee -a "$LOG"
fi
set -e 2>/dev/null || true

# =========================================================================
# STEP 3: QUALITY GATE (standalone — runs OUTSIDE orchestrator)
# =========================================================================
# The unified quality gate (analyst/guard_pipeline.py) runs ALL 8 gates:
# 0. STRUCTURAL — files present and valid JSON
# 1. FABRICATION — unverified contracts/prices/tickers/pct claims
# 2. THEMES — required theme coverage
# 3. CALIBRATION — Sherman Kent band ↔ numeric prediction agreement
# 4. COMPLETENESS — no truncation, adequate word count, all sections
# 5. SCOPE — topic within assignment scope
# 6. RED_TEAM — forced dissent note exists and is substantive
# 7. BAND_DIVERSITY — at least 3 distinct Sherman Kent bands across all KJs
#
# Model enforcement: also checks that V4 Pro was used (not Flash)
# =========================================================================

echo "--- Running quality gate ---" | tee -a "$LOG"

mkdir -p "$WORKING_DIR"

# Wait for completion sentinel — ensures orchestrator has flushed all files
COMPLETE_FLAG="$WORKING_DIR/.brief_complete"
if [ ! -f "$COMPLETE_FLAG" ]; then
    echo "WARNING: .brief_complete not found — assembly may not be finished. Continuing with caution." | tee -a "$LOG"
else
    echo "Found .brief_complete sentinel: $(cat "$COMPLETE_FLAG")" | tee -a "$LOG"
fi

QG_REPORT=$(python3 "$REPO/analyst/guard_pipeline.py" \
    --brief-dir "$WORKING_DIR" \
    --query "geopolitical intelligence brief" \
    --json 2>&1)

QG_RC=$?

# Log gate results
echo "$QG_REPORT" | python3 -c "
import sys, json
try:
    r = json.load(sys.stdin)
    print(f'Quality gate: {r.get(\"detail\", \"unknown\")}')
    for g in r.get('gates', []):
        icon = {'PASS': '✅', 'WARN': '⚠️', 'BLOCK': '❌'}.get(g['status'], '?')
        print(f'  {icon} {g[\"gate\"]}: {g[\"detail\"]}')
        for issue in g.get('issues', []):
            print(f'     → {issue}')
except:
    print(f'Quality gate parse error: {sys.stdin.read()[:500]}')
" >> "$LOG"

# Also verify model
MODEL_CHECK=$(python3 -c "
import json, sys
exec_summary = '$WORKING_DIR/analysis/exec_summary.json'
import os
if os.path.exists(exec_summary):
    d = json.load(open(exec_summary))
    models = d.get('models_used', [])
    has_fallback = any('flash' in m.lower() for m in models)
    if has_fallback:
        print(f'MODEL VIOLATION: Flash model used — {models}')
        sys.exit(1)
    print(f'Models OK: {models}')
else:
    print('No exec_summary.json')
    sys.exit(1)
" 2>&1)
MODEL_CHECK_RC=$?

echo "Model check: $MODEL_CHECK" | tee -a "$LOG"

if [ $QG_RC -ne 0 ] || [ $MODEL_CHECK_RC -ne 0 ]; then
    echo "FATAL: Quality gate or model check FAILED." | tee -a "$LOG"
    echo "DELIVERY ABORTED — brief does not meet quality standards." | tee -a "$LOG"
    echo "=== Daily Text Brief FAILED — $(date -u) ===" | tee -a "$LOG"
    exit 1
fi

# =========================================================================
# STEP 3b: OPUS QC REVIEW (pre-delivery — runs BEFORE delivery, blocks if FAIL/CRITICAL)
# =========================================================================
# Runs Claude Opus 4.7 deep quality audit via opus_qc_review.py.
# This was originally a post-delivery watchdog (qc-watchdog.sh). Moving it here
# ensures no flawed brief reaches the principal.
# =========================================================================

echo "--- Running Opus QC review (pre-delivery) ---" | tee -a "$LOG"

set +e
OPUS_QC_OUTPUT=$(python3 "$REPO/scripts/opus_qc_review.py" \
    --brief-dir "$WORKING_DIR" \
    --json 2>>"$LOG")
OPUS_QC_RC=$?
set -e 2>/dev/null || true

OPUS_QC_OVERALL=$(echo "$OPUS_QC_OUTPUT" | python3 -c "
import sys, json
try:
    r = json.load(sys.stdin)
    print(r.get('overall', 'UNKNOWN'))
except:
    print('PARSE_ERROR')
" 2>/dev/null || echo "PARSE_ERROR")

echo "Opus QC result: $OPUS_QC_OVERALL" | tee -a "$LOG"

# Log detailed findings
echo "$OPUS_QC_OUTPUT" | python3 -c "
import sys, json
try:
    r = json.load(sys.stdin)
    print('Opus QC dimensions:')
    for dim, data in r.get('dimensions', {}).items():
        rating = data.get('rating', '?')
        icon = {'PASS': '✅', 'WARN': '⚠️', 'FAIL': '❌', 'CRITICAL': '🚨'}.get(rating, '?')
        print(f'  {icon} {dim}: {rating}')
        for finding in data.get('findings', [])[:3]:
            print(f'     → {finding}')
    overall = r.get('overall_note', '')
    if overall:
        print(f'Overall note: {overall}')
except Exception as e:
    print(f'Opus QC parse error: {e}')
" >> "$LOG" 2>&1

if [ "$OPUS_QC_OVERALL" = "FAIL" ] || [ "$OPUS_QC_OVERALL" = "CRITICAL" ]; then
    echo "FATAL: Opus QC returned ${OPUS_QC_OVERALL} — brief does not pass quality audit." | tee -a "$LOG"
    echo "DELIVERY ABORTED — fix quality issues and re-run." | tee -a "$LOG"
    echo "=== Daily Text Brief FAILED — $(date -u) ===" | tee -a "$LOG"
    exit 1
elif [ "$OPUS_QC_OVERALL" = "WARN" ] || [ "$OPUS_QC_OVERALL" = "PASS" ]; then
    echo "Opus QC ${OPUS_QC_OVERALL} — delivery proceeds with confidence." | tee -a "$LOG"
else
    echo "WARNING: Opus QC returned '${OPUS_QC_OVERALL}' (unknown) — proceeding cautiously." | tee -a "$LOG"
fi

# =========================================================================
# STEP 4: DELIVERY — only if ALL gates pass + model is correct + Opus QC passes
# =========================================================================

if [ -n "${AGENTMAIL_API_KEY:-}" ]; then
    echo "--- Delivering via AgentMail ---" | tee -a "$LOG"
    python3 "$REPO/skills/daily-intel-brief/scripts/deliver_text_brief.py" \
        --working-dir "$WORKING_DIR" \
        --to "roderick.jones@gmail.com" \
        --from "trevor_mentis@agentmail.to" \
        >> "$LOG" 2>&1
    DELIVER_RC=${PIPESTATUS[0]}
    if [ $DELIVER_RC -ne 0 ]; then
        echo "WARNING: AgentMail delivery failed with rc=$DELIVER_RC" | tee -a "$LOG"
    fi
else
    echo "AGENTMAIL_API_KEY not set — brief saved to $WORKING_DIR/analysis/exec_summary.json" | tee -a "$LOG"
fi

# =========================================================================
# STEP 4b: POST-DELIVERY QUALITY VALIDATION (always runs)
# =========================================================================
echo "--- Validating delivery quality ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/validate_delivery.py" \
    --brief-dir "$WORKING_DIR" \
    >> "$LOG" 2>&1
VALIDATE_RC=$?
if [ $VALIDATE_RC -ne 0 ]; then
    echo "WARNING: Delivery quality check found issues (see log)" | tee -a "$LOG"
fi
set -e 2>/dev/null || true

# =========================================================================
# STEP 5: POSTDICTION
# =========================================================================
echo "--- Running postdiction ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/postdict.py" \
    --today "$WORKING_DIR" \
    --yesterday "$HOME/trevor-briefings/$(date -u -d 'yesterday' +%Y-%m-%d)" \
    >> "$LOG" 2>&1
set -e 2>/dev/null || true

# =========================================================================
# STEP 5b: [REMOVED] I&W FEEDBACK LOOP — referenced Philby desk config, archived 2026-05-31
# =========================================================================

# =========================================================================
# STEP 5c: RECHECK EXPIRED PREDICTIONS — force-resolve expired judgments
# =========================================================================
echo "--- Rechecking expired predictions ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/postdict.py" --recheck >> "$LOG" 2>&1
set -e 2>/dev/null || true

echo "--- Recompiling calibration directives from fresh postdiction data ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/compile_calibration_directives.py" >> "$LOG" 2>&1
set -e 2>/dev/null || true

# =========================================================================
# STEP 6: DEPLOY LANDING PAGE — update GitHub Pages with latest brief content
# =========================================================================
echo "--- Deploying landing page ---" | tee -a "$LOG"
set +e
if [ -f "$REPO/scripts/deploy_landing_page.sh" ]; then
    bash "$REPO/scripts/deploy_landing_page.sh" >> "$LOG" 2>&1
else
    echo "Landing page deploy script not found — skipping" | tee -a "$LOG"
fi
set -e 2>/dev/null || true — update GitHub Pages with latest brief content
# =========================================================================
echo "--- Deploying landing page ---" | tee -a "$LOG"
set +e
bash "$REPO/scripts/deploy_landing_page.sh" >> "$LOG" 2>&1
set -e 2>/dev/null || true

echo "=== Daily Text Brief complete — $(date -u) ===" | tee -a "$LOG"
