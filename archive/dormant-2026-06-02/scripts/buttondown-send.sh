#!/usr/bin/env bash
#==============================================================================
# buttondown-send.sh — Send the daily GSIB brief via Buttondown newsletter
#==============================================================================
# Wraps buttondown-send.py for cron compatibility.
# Usage:
#   ./buttondown-send.sh [--subject "Custom Subject"] [--analysis analysis.md]
#==============================================================================

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
DATE_UTC=$(date -u +%Y-%m-%d)
DATE_PT=$(TZ='America/Los_Angeles' date +%Y-%m-%d)
LOG="$REPO_DIR/logs/buttondown-${DATE_UTC}.log"
mkdir -p "$REPO_DIR/logs"

# Source .env
if [ -f "$REPO_DIR/.env" ]; then
  set -a; source "$REPO_DIR/.env"; set +a
fi

export BUTTONDOWN_API_KEY="${BUTTONDOWN_API_KEY:-}"
export DATE_PT

# Parse additional args and forward to Python
python3 "$REPO_DIR/scripts/buttondown-send.py" "$@" 2>&1 | tee -a "$LOG"
exit ${PIPESTATUS[0]}
