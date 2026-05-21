#!/usr/bin/env bash
#==============================================================================
# heartbeat-source-discovery.sh — Hourly Source Discovery
#
# Rotates through 10 region-specific search queries every hour.
# Finds new RSS feeds and sources for all desks continuously.
# At hour 3 UTC, also runs source freshness check.
#
# Schedule: Runs every hour via cron
#==============================================================================
set -uo pipefail

REPO="/home/ubuntu/.openclaw/workspace"
LOG="$REPO/logs/source-discovery.log"
mkdir -p "$REPO/logs"

source "$REPO/.env" 2>/dev/null || true
export BRAVE_API_KEY="${BRAVE_API_KEY:-}"

DATE_TS=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
VERBOSE=false
[[ "${1:-}" == "--verbose" ]] && VERBOSE=true

HOUR=$(date -u +%H)
HOUR_NUM=$((10#$HOUR))
QUERY_IDX=$(( HOUR_NUM % 10 ))

QUERIES=(
  "Europe geopolitics defense news RSS"
  "North America politics security RSS"
  "Central America Caribbean news sources RSS"
  "South America geopolitics news RSS"
  "Africa security politics news RSS"
  "Middle East conflict analysis RSS"
  "Central Asia geopolitics Russia China RSS"
  "South East Asia ASEAN security RSS"
  "Oceania Pacific geopolitics news"
  "prediction markets Kalshi Polymarket news RSS"
)

REGIONS=(
  "europe" "north_america" "central_america_caribbean" "south_america"
  "africa" "middle_east" "central_asia" "south_east_asia" "oceania" "prediction_markets"
)

QUERY="${QUERIES[$QUERY_IDX]}"
REGION="${REGIONS[$QUERY_IDX]}"

echo "[${DATE_TS}] heartbeat: ${REGION} — ${QUERY}" >> "$LOG"

cd "$REPO"
set +e
RESULT=$(python3 "$REPO/scripts/source_discovery.py" --query "${QUERY}" --auto-add --region "${REGION}" 2>&1)
EXIT_CODE=$?
set -e 2>/dev/null || true

echo "[${DATE_TS}] ${REGION}: ${RESULT}" >> "$LOG"
if $VERBOSE; then
    echo "${RESULT}"
fi

# Source freshness check at hour 3 UTC
if [ "$HOUR_NUM" -eq 3 ]; then
    echo "[${DATE_TS}] Running source freshness check..." >> "$LOG"
    set +e
    python3 "$REPO/scripts/source_crosscheck.py" --all 2>&1 | tail -3 >> "$LOG"
    set -e 2>/dev/null || true
    echo "[${DATE_TS}] Freshness check complete" >> "$LOG"
fi

echo "[${DATE_TS}] heartbeat: done" >> "$LOG"
exit $EXIT_CODE
