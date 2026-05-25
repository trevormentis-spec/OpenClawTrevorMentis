#!/bin/bash
# Kalshi Position Monitor — cron entry
# Runs every 5 minutes to check positions and enforce guardrails
# 
# Cron: */5 * * * * /home/ubuntu/.openclaw/workspace/skills/kalshi-trader/scripts/cron-monitor.sh
#
# Modes:
#   --alert-only:  Reports exit signals but doesn't trade (default, safer)
#   --auto-exit:   Executes stop-loss/take-profit autonomously

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE="/home/ubuntu/.openclaw/workspace"
LOG_DIR="$WORKSPACE/logs/kalshi"
mkdir -p "$LOG_DIR"

# Load env vars
set -a
source "$WORKSPACE/.env" 2>/dev/null || true
set +a

# Run with auto-exit enabled if flag file exists
AUTO_EXIT_FLAG="$WORKSPACE/tasks/kalshi-auto-exit.flag"
EXIT_FLAG=""
if [ -f "$AUTO_EXIT_FLAG" ]; then
    EXIT_FLAG="--auto-exit"
fi

cd "$WORKSPACE"
python3 "$SCRIPT_DIR/monitor.py" --summary $EXIT_FLAG 2>&1 | \
    tee -a "$LOG_DIR/monitor-$(date +%Y-%m-%d).log"

# If exit actions were taken, log separately
if grep -q "EXIT TRIGGER\|AUTO-EXIT" "$LOG_DIR/monitor-$(date +%Y-%m-%d).log" 2>/dev/null; then
    echo "[$(date -Iseconds)] EXIT ACTION DETECTED" >> "$LOG_DIR/exits.log"
fi
