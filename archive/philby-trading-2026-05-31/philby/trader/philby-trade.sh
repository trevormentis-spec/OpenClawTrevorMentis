#!/bin/bash
# philby-trade.sh — Philby Trading Cycle
# Runs after each cognition cycle: intel bridge → trade execution → status log
# Handles errors gracefully — trading is secondary to intelligence.

set -euo pipefail

WORKSPACE="/home/ubuntu/.openclaw/workspace"
LOG_DIR="$WORKSPACE/logs"
TODAY=$(date -u +"%Y-%m-%d")
NOW=$(date -u +"%H:%M:%S")

set -a
source "$WORKSPACE/.env" 2>/dev/null || true
set +a

cd "$WORKSPACE"

echo "[$NOW] Philby Trade: Starting cycle..." >> "$LOG_DIR/philby-trade-${TODAY}.log"

# Step 1: Generate fresh KJ feed (intel bridge depends on it)
python3 analyst/scripts/kj_feed.py \
    >> "$LOG_DIR/philby-trade-${TODAY}.log" 2>&1 && \
echo "  ✅ KJ feed updated" || echo "  ❌ KJ feed failed"

# Step 2: Run intel bridge to detect edges
python3 philby/trader/intel_bridge.py --json \
    >> "$LOG_DIR/philby-trade-${TODAY}.log" 2>&1 && \
echo "  ✅ Intel bridge complete" || echo "  ❌ Intel bridge failed"

# Step 3: Execute trades autonomously (intel-driven edges)
python3 philby/trader/trader.py --scan-and-trade \
    >> "$LOG_DIR/philby-trade-${TODAY}.log" 2>&1 && \
echo "  ✅ Trades executed" || echo "  ❌ Trade execution failed"

# Step 4: Log status
python3 philby/trader/trader.py --status \
    >> "$LOG_DIR/philby-trade-${TODAY}.log" 2>&1

echo "[$NOW] Philby Trade: Cycle complete" >> "$LOG_DIR/philby-trade-${TODAY}.log"
