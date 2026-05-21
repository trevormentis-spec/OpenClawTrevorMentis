#!/usr/bin/env bash
#==============================================================================
# heartbeat-source-discovery.sh — Hourly Source Discovery
#
# Runs source_discovery.py every hour with a random query rotation.
# Searches for new RSS feeds and sources across all 10 regions.
# Integrates with source_discovery.py which tests feeds and stores results
# in analyst/meta/sources_tested.json.
#
# Schedule: runs every hour via cron
#   * * * * * /home/ubuntu/.openclaw/workspace/tasks/heartbeat-source-discovery.sh
#
# Usage:
#   ./tasks/heartbeat-source-discovery.sh [--verbose]
#==============================================================================
set -uo pipefail

REPO="/home/ubuntu/.openclaw/workspace"
LOG="$REPO/logs/source-discovery.log"
mkdir -p "$REPO/logs"

DATE_TS=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
VERBOSE=false
[[ "${1:-}" == "--verbose" ]] && VERBOSE=true

# ── Query rotation ──────────────────────────────────────────────────────────
# 10 rotating queries — one per region. The hour value (0-23) selects which
# query to use, cycling through all 10.
HOUR=$(date -u +%H)
HOUR_NUM=$((10#$HOUR))  # strip leading zero
QUERY_IDX=$(( HOUR_NUM % 10 ))

QUERIES=(
  "Europe geopolitics news RSS feed"
  "North America politics defense RSS"
  "Central America Caribbean news sources"
  "South America geopolitics RSS feed"
  "Africa security politics news RSS"
  "Middle East conflict analysis RSS"
  "Central Asia geopolitics Russia China RSS"
  "South East Asia ASEAN security RSS"
  "Oceania Pacific geopolitics news"
  "prediction markets Kalshi Polymarket news RSS"
)

QUERY="${QUERIES[$QUERY_IDX]}"
QUERY_NAME="rot-${HOUR}-${QUERY_IDX}"

echo "[${DATE_TS}] heartbeat source-discovery: query=${QUERY}" >> "$LOG"

# ── Run source discovery ───────────────────────────────────────────────────
# source_discovery.py searches for new RSS feeds based on query,
# tests them, and appends working ones to sources_tested.json.
cd "$REPO"
set +e
RESULT=$(python3 "$REPO/scripts/source_discovery.py" --auto-add --query "${QUERY}" 2>&1)
EXIT_CODE=$?
set -e 2>/dev/null || true

NEW_SOURCES=$(echo "$RESULT" | grep -c "added\|discovered\|found" 2>/dev/null || echo "0")

if [ $EXIT_CODE -eq 0 ]; then
    echo "[${DATE_TS}] OK — ${QUERY_NAME} | ${RESULT}" | tail -1 >> "$LOG"
    if $VERBOSE; then
        echo "Source discovery (${QUERY_NAME}): ${RESULT}"
    fi
else
    echo "[${DATE_TS}] FAIL (rc=${EXIT_CODE}) — ${QUERY_NAME} | ${RESULT:0:200}" >> "$LOG"
fi

# ── Maintenance: check source freshness once per day at hour 3 ────────────
if [ "$HOUR" -eq 3 ]; then
    echo "[${DATE_TS}] Running daily source freshness check..." >> "$LOG"
    python3 "$REPO/scripts/source_crosscheck.py" --all 2>&1 | tail -3 >> "$LOG"
fi

echo "[${DATE_TS}] heartbeat source-discovery: done" >> "$LOG"
exit $EXIT_CODE
