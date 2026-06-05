#!/bin/bash
# Runtime health report — every 6 hours
# Generates structured health overview.

WORKSPACE="/home/ubuntu/.openclaw/workspace"
HEALTH_LOG="$WORKSPACE/logs/runtime-health.log"
HEALTH_STATE="$WORKSPACE/tasks/runtime-state.json"
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

mkdir -p "$WORKSPACE/logs/kalshi"

# Collect data
DISK_PCT=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
DISK_USED=$(df -h / | tail -1 | awk '{print $3}')
DISK_TOTAL=$(df -h / | tail -1 | awk '{print $2}')

KALSHI_WS_SIZE=$(du -m "$WORKSPACE/logs/kalshi/ws-events.jsonl" 2>/dev/null | cut -f1 || echo "0")
MONITOR_LOG_SIZE=$(du -m "$WORKSPACE/logs/kalshi/monitor-out.log" 2>/dev/null | cut -f1 || echo "0")
TOTAL_LOG_SIZE=$(du -sm "$WORKSPACE/logs" 2>/dev/null | cut -f1 || echo "0")

pgrep -f "monitor.py.*--loop" > /dev/null 2>&1 && MONITOR_RUNNING="yes" || MONITOR_RUNNING="no"
pgrep -f "ws_listener" > /dev/null 2>&1 && WS_RUNNING="yes" || WS_RUNNING="no"

HEAVY_JOBS=$(python3 "$WORKSPACE/scripts/runtime_lock.py" --list 2>/dev/null | grep -c "  " | head -1 || echo "0")
DEGRADED="no"
[ -f "$WORKSPACE/tasks/degraded-mode.flag" ] && DEGRADED="yes"

RECENT_FAILURES=$(grep -c "ERROR\|CRITICAL\|Traceback" "$WORKSPACE/logs/kalshi/monitor-out.log" 2>/dev/null | tail -1 || echo "0")
EXPORTS_SIZE=$(du -sm "$WORKSPACE/exports" 2>/dev/null | cut -f1 || echo "0")
TMP_SIZE=$(du -sm "$WORKSPACE/tmp" 2>/dev/null | cut -f1 || echo "0")

# State file age
STATE_AGE="?"
if [ -f "$HEALTH_STATE" ]; then
    STATE_AGE=$(( $(date +%s) - $(stat -c %Y "$HEALTH_STATE") ))
    STATE_AGE="$((STATE_AGE / 60))m"
fi

# Determine risk
RISK="low"
BOTTLENECKS="none"
if [ "$DISK_PCT" -ge 90 ]; then RISK="high"; BOTTLENECKS="disk_critical"; fi
if [ "$DISK_PCT" -ge 80 ] && [ "$DISK_PCT" -lt 90 ]; then RISK="medium"; BOTTLENECKS="disk_warning"; fi
if [ "$MONITOR_RUNNING" = "no" ]; then RISK="high"; BOTTLENECKS="${BOTTLENECKS} monitor_down"; fi
if [ "$DEGRADED" = "yes" ]; then RISK="high"; BOTTLENECKS="${BOTTLENECKS} degraded_mode"; fi

# Print report
{
    echo "=== RUNTIME HEALTH REPORT ==="
    echo "Time: $NOW"
    echo "Disk: ${DISK_PCT}% (${DISK_USED}/${DISK_TOTAL}) Status: ${RISK}"
    echo "Logs: ${TOTAL_LOG_SIZE}M (WS:${KALSHI_WS_SIZE}M Monitor:${MONITOR_LOG_SIZE}M)"
    echo "Procs: Monitor=${MONITOR_RUNNING} WS=${WS_RUNNING} Heavy=${HEAVY_JOBS}"
    echo "Storage: Exports=${EXPORTS_SIZE}M Tmp=${TMP_SIZE}M"
    echo "Failures: ${RECENT_FAILURES} Degraded=${DEGRADED} Age=${STATE_AGE}"
    echo "Bottlenecks: ${BOTTLENECKS}"
    echo ""
} | tee -a "$HEALTH_LOG"

# Write structured state via Python
export NOW DISK_PCT DISK_USED DISK_TOTAL
export KALSHI_WS_SIZE MONITOR_LOG_SIZE TOTAL_LOG_SIZE
export MONITOR_RUNNING WS_RUNNING HEAVY_JOBS
export EXPORTS_SIZE TMP_SIZE RECENT_FAILURES
export DEGRADED RISK BOTTLENECKS HEALTH_STATE

python3 "$WORKSPACE/scripts/write-health-state.py"
