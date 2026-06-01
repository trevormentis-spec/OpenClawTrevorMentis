#!/usr/bin/env bash
set -euo pipefail
# ──────────────────────────────────────────────────────────────────
# Signal Board Pipeline — Daily intelligence summary production
# Shell wrapper that calls the Python pipeline script
# ──────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATE_STR="${1:-$(date -u +%Y-%m-%d)}"
ENV_FILE="$SCRIPT_DIR/../.env"

# The Python script loads .env internally; Kalshi/AgentMail keys are already in env

echo "=== Signal Board Pipeline — $DATE_STR ==="
echo ""

# Delegate to Python pipeline
python3 "$SCRIPT_DIR/signal_board.py" --date "$DATE_STR" 2>&1

echo ""
echo "Output: $SCRIPT_DIR/../exports/signal-board/$DATE_STR.md"
