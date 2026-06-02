#!/usr/bin/env bash
set -euo pipefail
# Signal Board Pipeline — Daily intelligence summary production
# Shell wrapper for cron use.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATE_STR="${1:-$(date -u +%Y-%m-%d)}"

echo "=== Signal Board Pipeline — $DATE_STR ==="

# Step 1: Load env vars
export KALSHI_API_KEY=$(grep KALSHI_API_KEY "$SCRIPT_DIR/../.env" | cut -d= -f2-)
export AGENTMAIL_API_KEY=$(grep AGENTMAIL_API_KEY "$SCRIPT_DIR/../.env" | cut -d= -f2-)
export BRAVE_API_KEY=$(grep BRAVE_API_KEY "$SCRIPT_DIR/../.env" | cut -d= -f2-)

# Step 2: Signal Board (handles GDELT + fallback internally)
python3 "$SCRIPT_DIR/signal_board.py" --date "$DATE_STR" 2>&1

echo ""
echo "Done: $SCRIPT_DIR/../exports/signal-board/$DATE_STR.md"
