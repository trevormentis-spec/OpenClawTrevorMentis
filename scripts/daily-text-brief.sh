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
cd "$REPO"

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

# Step 1d: Simmer market signal overlay (trading context, risk alerts, PnL)
echo "--- Simmer signal overlay ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/simmer_scanner.py" --save >> "$LOG" 2>&1
set -e 2>/dev/null || true

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
    --provider deepseek \
    --tier2-provider deepseek \
    --redteam-model "deepseek/deepseek-v4-pro" \
    --redteam-provider deepseek \
    --no-deliver \
    >> "$LOG" 2>&1
ORCH_RC=${PIPESTATUS[0]}

if [  -ne 0 ]; then
    echo "FATAL: Orchestrator failed with rc=" | tee -a ""
    echo "DELIVERY ABORTED â orchestrator must succeed before quality gate can run." | tee -a ""
    echo "=== Daily Text Brief FAILED â Fri May 29 18:28:51 UTC 2026 ===" | tee -a ""
    exit 
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

ORCH_RC
fi

# =========================================================================
# STEP 3: QUALITY GATE (standalone — runs OUTSIDE orchestrator)
# =========================================================================
# The unified quality gate (analyst/guard_pipeline.py) runs ALL 7 gates:
# 0. STRUCTURAL — files present and valid JSON
# 1. FABRICATION — unverified contracts/prices/tickers/pct claims
# 2. THEMES — required theme coverage
# 3. CALIBRATION — Sherman Kent band ↔ numeric prediction agreement
# 4. COMPLETENESS — no truncation, adequate word count, all sections
# 5. SCOPE — topic within assignment scope
# 6. RED_TEAM — forced dissent note exists and is substantive
#
# Model enforcement: also checks that V4 Pro was used (not Flash)
# =========================================================================

echo "--- Running quality gate ---" | tee -a "$LOG"

WORKING_DIR="$HOME/trevor-briefings/${DATE_UTC}"
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
# STEP 4: DELIVERY — only if ALL gates pass + model is correct
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
    echo "AGENTMAIL_API_KEY not set — text brief saved to $WORKING_DIR/analysis/exec_summary.json" | tee -a "$LOG"
# =========================================================================
# STEP 4b: POST-DELIVERY QUALITY VALIDATION
# =========================================================================
echo "--- Validating delivery quality ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/validate_delivery.py" 
    --brief-dir "$WORKING_DIR" 
    >> "$LOG" 2>&1
VALIDATE_RC=$?
if [ $VALIDATE_RC -ne 0 ]; then
    echo "WARNING: Delivery quality check found issues (see log)" | tee -a "$LOG"
fi
set -e 2>/dev/null || true

fi

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
# STEP 5b: I&W FEEDBACK LOOP — connect calibration to Philby desks
# =========================================================================
echo "--- Running I&W feedback loop ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/iw_feedback_loop.py" --all >> "$LOG" 2>&1
set -e 2>/dev/null || true

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
# STEP 6: MOLTBOOK — post brief to agent social network
# =========================================================================
echo "--- Posting to Moltbook ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/moltbook_post.py" >> "$LOG" 2>&1
set -e 2>/dev/null || true

# =========================================================================
# STEP 7: DEPLOY LANDING PAGE — update GitHub Pages with latest brief content
# =========================================================================
echo "--- Deploying landing page ---" | tee -a "$LOG"
set +e
bash "$REPO/scripts/deploy_landing_page.sh" >> "$LOG" 2>&1
set -e 2>/dev/null || true

echo "=== Daily Text Brief complete — $(date -u) ===" | tee -a "$LOG"
