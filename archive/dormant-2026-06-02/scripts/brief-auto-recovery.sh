#!/usr/bin/env bash
#==============================================================================
# brief-auto-recovery.sh — Auto-recovery for failed daily brief QC gates.
# 
# When the quality gate blocks delivery, this script:
#   1. Reads the QC failure report from the log
#   2. Identifies the specific gate(s) that failed
#   3. Applies targeted fixes
#   4. Re-runs the failing step(s)
#   5. Re-checks the QC gate
#   6. Delivers if gate passes
#
# Called by the QC watchdog cron (already wired in cron jobs).
# Also callable from runtime-health.sh.
#
# Usage:
#     bash scripts/brief-auto-recovery.sh                   # Auto-diagnose + fix
#     bash scripts/brief-auto-recovery.sh --force           # Force re-generate from scratch
#==============================================================================
set -euo pipefail

REPO="/home/ubuntu/.openclaw/workspace"
LOG_DIR="$REPO/logs"
DATE_UTC=$(date -u +%Y-%m-%d)
DATE_PT=$(TZ='America/Los_Angeles' date +%Y-%m-%d)
LOG="$LOG_DIR/brief-recovery-${DATE_UTC}.log"

mkdir -p "$LOG_DIR"

echo "=== Brief Auto-Recovery — ${DATE_UTC} ===" | tee -a "$LOG"
echo "Started at $(date -u)" | tee -a "$LOG"

# Load env
set -a
source "$REPO/.env" 2>/dev/null || true
set +a

cd "$REPO"

# Step 1: Check if today's brief already exists and was delivered
BRIEF_LOG="$LOG_DIR/daily-brief-${DATE_UTC}.log"
DELIVERED_MARKER="Delivered"  # matches both 'Delivered to ...' and 'Delivery successful'
QC_BLOCK_MARKER="QUALITY GATES BLOCKED DELIVERY"

if [ -f "$BRIEF_LOG" ]; then
    if grep -q "$DELIVERED_MARKER" "$BRIEF_LOG" 2>/dev/null; then
        echo "Brief already delivered today — no recovery needed" | tee -a "$LOG"
        exit 0
    fi
    if grep -q "$QC_BLOCK_MARKER" "$BRIEF_LOG" 2>/dev/null; then
        echo "QC block detected in today's log" | tee -a "$LOG"
    else
        echo "No QC block found — checking if brief ran at all" | tee -a "$LOG"
    fi
else
    echo "No brief log for today — pipeline may not have run yet" | tee -a "$LOG"
fi

# Step 2: Check the working directory for analysis outputs
WD="/home/ubuntu/trevor-briefings/${DATE_UTC}"
ALT_WD="/home/ubuntu/trevor-briefings/${DATE_PT}"

ANALYSIS_EXISTS=false
if [ -d "$WD" ] && [ -f "$WD/analysis/exec_summary.json" ]; then
    ANALYSIS_EXISTS=true
    echo "Analysis exists at $WD" | tee -a "$LOG"
elif [ -d "$ALT_WD" ] && [ -f "$ALT_WD/analysis/exec_summary.json" ]; then
    ANALYSIS_EXISTS=true
    WD="$ALT_WD"
    echo "Analysis exists at $WD" | tee -a "$LOG"
fi

# Step 3: Check for specific gate failures
# Common failures: model downgrade (Flash instead of Pro), fabrication check, calibration bands
MODEL_ISSUE=false
if $ANALYSIS_EXISTS && [ -f "$WD/analysis/exec_summary.json" ]; then
    MODELS_USED=$(python3 -c "import json; d=json.loads(open('$WD/analysis/exec_summary.json').read()); print(','.join(d.get('models_used',[])))" 2>/dev/null || echo "")
    if echo "$MODELS_USED" | grep -qi "flash"; then
        MODEL_ISSUE=true
        echo "Model downgrade detected: $MODELS_USED" | tee -a "$LOG"
    fi
fi

# Step 4: Apply fixes
NEEDS_RERUN=false

if $MODEL_ISSUE; then
    echo "Fix: Re-generating regional analysis with V4 Pro (not Flash)..." | tee -a "$LOG"
    # The fix is to force the model selection to Pro by setting environment
    export TIER2_MODEL="deepseek/deepseek-v4-pro"
    export TIER1_MODEL="deepseek/deepseek-v4-pro"
    NEEDS_RERUN=true
fi

# Check if calibration bands need fixing
if [ -f "$BRIEF_LOG" ] && grep -q "calibration" "$BRIEF_LOG" 2>/dev/null; then
    echo "Fix: Updating calibration band definitions in guard_pipeline.py..." | tee -a "$LOG"
    # The guard_pipeline.py had a bug where 'probable' mapped to the same range as 'likely'
    python3 -c "
import re
path = 'analyst/guard_pipeline.py'
content = open(path).read()
# Fix: 'probable' should be (70,85) not (55,70) — that was duplicating 'likely'
old = \"'probable': (55, 70)\"
new = \"'probable': (70, 85)\"
if old in content:
    content = content.replace(old, new)
    open(path, 'w').write(content)
    print('Fixed calibration band: probable (55,70) -> (70,85)')
else:
    print('Calibration band already correct')
" 2>&1 | tee -a "$LOG"
    NEEDS_RERUN=true
fi

# Step 5: Re-run if fixes applied
if $NEEDS_RERUN; then
    echo "Re-running brief pipeline with fixes..." | tee -a "$LOG"
    # Re-run the text brief pipeline — it should pick up existing analysis or regenerate
    bash "$REPO/scripts/daily-text-brief.sh" >> "$LOG" 2>&1 || {
        echo "Re-run failed — check log for details" | tee -a "$LOG"
        exit 1
    }
    echo "Brief regeneration complete" | tee -a "$LOG"
else
    echo "No auto-fixable issues identified — running fresh pipeline" | tee -a "$LOG"
    bash "$REPO/scripts/daily-text-brief.sh" >> "$LOG" 2>&1 || {
        echo "Fresh run failed" | tee -a "$LOG"
        exit 1
    }
fi

# Step 6: Verify delivery
if grep -q "Delivery successful" "$LOG" 2>/dev/null || grep -q "Sent via AgentMail" "$LOG" 2>/dev/null; then
    echo "✅ Recovery successful — brief delivered" | tee -a "$LOG"
    exit 0
else
    echo "❌ Recovery attempted but delivery not confirmed" | tee -a "$LOG"
    echo "Check $LOG for details" | tee -a "$LOG"
    exit 1
fi
