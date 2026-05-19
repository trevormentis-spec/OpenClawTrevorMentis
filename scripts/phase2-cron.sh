#!/usr/bin/env bash
# Phase 2 cron entry point — scheduled execution of the continuous learning loop.
#
# Compatible with OpenClaw heartbeat or external scheduler.
# Defaults to DRY-RUN mode. Use --live to execute tasks.
#
# Usage:
#   bash scripts/phase2-cron.sh              # DRY-RUN (safe, $0 — default mode)
#   bash scripts/phase2-cron.sh --live       # REQUIRES activation gate

set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$REPO/logs/phase2-$(date +%Y%m%d).log"
mkdir -p "$(dirname "$LOG")"

echo "[phase2] $(date -u '+%Y-%m-%d %H:%M UTC') — Starting Phase 2 cycle" | tee -a "$LOG"

cd "$REPO"

# Run planner
python3 analyst/planner.py "$@" 2>&1 | tee -a "$LOG"
PLANNER_RC=${PIPESTATUS[0]}

if [ $PLANNER_RC -ne 0 ]; then
    echo "[phase2] Planner failed (rc=$PLANNER_RC)" | tee -a "$LOG"
    exit $PLANNER_RC
fi

# Run worker (processes the task queue created by planner)
python3 analyst/worker.py "$@" 2>&1 | tee -a "$LOG"
WORKER_RC=${PIPESTATUS[0]}

# Update STATUS.md
python3 analyst/status_generator.py 2>&1 | tee -a "$LOG"

echo "[phase2] $(date -u '+%Y-%m-%d %H:%M UTC') — Phase 2 cycle complete (${WORKER_RC})" | tee -a "$LOG"
exit $WORKER_RC
