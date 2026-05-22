#!/usr/bin/env bash
#==============================================================================
# daily-text-brief.sh — Text-only Daily Intel Brief (2026-05-22 rewrite)
#
# Pipeline:
#   1. Pre-collection: prediction market scan, calibration directives, source discovery
#   2. Orchestrator: collect.py (259 feeds) → analyze.py (10 regions, V4 Pro) → AgentMail
#   3. Postdict: calibration tracking
#
# Models: DeepSeek V4 Pro for ALL analysis tiers
# Delivery: AgentMail to trevor_mentis@agentmail.to → forwarded to Roderick
# Constraints: NO visuals, NO PDF, NO social, NO Mexico pipeline, NO Gmail delivery
#
# Schedule: Triggered by OpenClaw cron at 05:00 PT
# Flow:     05:00 PT — pre-collection
#           05:15 PT — orchestrator (collect + analyze)
#           05:45 PT — AgentMail delivery
#==============================================================================
set -uo pipefail

REPO="/home/ubuntu/.openclaw/workspace"
DATE_UTC=$(date -u +%Y-%m-%d)
LOG="$REPO/logs/daily-brief-${DATE_UTC}.log"
mkdir -p "$REPO/logs"

echo "=== Daily Text Brief — ${DATE_UTC} ===" | tee -a "$LOG"
echo "Started at $(date -u)" | tee -a "$LOG"

# Source environment
source "$REPO/.env" 2>/dev/null || true
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-}"
export AGENTMAIL_API_KEY="${AGENTMAIL_API_KEY:-}"

cd "$REPO"

# =========================================================================
# STEP 1: PRE-COLLECTION
# =========================================================================

# Step 1a: Compile calibration directives from postdiction history
echo "--- Compiling calibration directives ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/compile_calibration_directives.py" 2>&1 | tee -a "$LOG"
set -e 2>/dev/null || true

# Step 1b: Source discovery — find new RSS/sources
echo "--- Source discovery ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/source_discovery.py" 2>&1 | tee -a "$LOG"
set -e 2>/dev/null || true

# Step 1c: Kalshi prediction market scan
echo "--- Scanning prediction markets ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/kalshi_scanner.py" --save 2>&1 | tee -a "$LOG"
set -e 2>/dev/null || true

# =========================================================================
# STEP 2: ORCHESTRATOR — collect + analyze + deliver
# =========================================================================
#
# Calls the orchestrator which runs:
#   - collect.py (259 RSS feeds + web search fallback, 10 regions)
#   - analyze.py (10 regional analyses + exec summary + red team, DeepSeek V4 Pro)
#   - postdict.py (calibration against yesterday's predictions)
#   - AgentMail delivery (trevor_mentis@agentmail.to → roderick.jones@gmail.com)
#
# NO visual assets, NO PDF assembly, NO social collection.
# All disabled via principal directive 2026-05-22.
# =========================================================================

echo "--- Running orchestrator (collect → analyze → AgentMail) ---" | tee -a "$LOG"
python3 skills/daily-intel-brief/scripts/orchestrate.py \
    --model "deepseek/deepseek-v4-pro" \
    --tier2-model "deepseek/deepseek-v4-pro" \
    --provider deepseek \
    --tier2-provider deepseek \
    2>&1 | tee -a "$LOG"
ORCH_RC=${PIPESTATUS[0]}

if [ $ORCH_RC -ne 0 ]; then
    echo "ERROR: Orchestrator failed with rc=$ORCH_RC" | tee -a "$LOG"
    # Attempt cleanup delivery with whatever we have
    echo "Attempting emergency delivery of partial analysis..." | tee -a "$LOG"
fi

echo "=== Daily Text Brief complete ===" | tee -a "$LOG"
echo "Finished at $(date -u)" | tee -a "$LOG"
