#!/bin/bash
# Runtime Self-Healing & Health System — Trevor
# Runs: every 10 minutes via cron, also callable directly
# 
# Phases:
#   1. Log rotation & pruning
#   2. Storage watchdog
#   3. Process health check
#   4. State consistency check
#   5. Health report generation

set -euo pipefail

WORKSPACE="/home/ubuntu/.openclaw/workspace"
LOG_DIR="$WORKSPACE/logs"
KALSHI_LOG_DIR="$LOG_DIR/kalshi"
HEALTH_LOG="$LOG_DIR/runtime-health.log"
HEALTH_STATE="$WORKSPACE/tasks/runtime-state.json"
LOCK_FILE="$WORKSPACE/tasks/runtime-self-heal.lock"
DEGRADED_FLAG="$WORKSPACE/tasks/degraded-mode.flag"
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TODAY=$(date -u +"%Y-%m-%d")
HOSTNAME=$(hostname 2>/dev/null || echo "unknown")

mkdir -p "$KALSHI_LOG_DIR" "$WORKSPACE/tasks"

# Concurrency guard
if [ -f "$LOCK_FILE" ]; then
    LOCK_AGE=$(( $(date +%s) - $(stat -c %Y "$LOCK_FILE") ))
    if [ $LOCK_AGE -lt 600 ]; then
        echo "[$NOW] Self-heal already running (${LOCK_AGE}s old)" >> "$HEALTH_LOG"
        exit 0
    else
        echo "[$NOW] Stale lock (${LOCK_AGE}s) — removing" >> "$HEALTH_LOG"
        rm -f "$LOCK_FILE"
    fi
fi
touch "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

# ── 1. LOG ROTATION ─────────────────────────────────────────────────

rotate_logs() {
    local log="$1"
    local max_size_mb="${2:-50}"
    local keep_days="${3:-7}"

    if [ ! -f "$log" ]; then
        return 0
    fi

    local size_mb
    size_mb=$(du -m "$log" 2>/dev/null | cut -f1)

    if [ "$size_mb" -gt "$max_size_mb" ]; then
        local rotated="${log}.${TODAY}.gz"
        gzip -c "$log" > "$rotated"
        : > "$log"
        echo "  Rotated: $(basename "$log") ($size_mb MB → gz'd)"
    fi

    # Prune old rotations
    find "$(dirname "$log")" -name "$(basename "$log").*.gz" -mtime +$keep_days -delete
}

rotate_jsonl() {
    local log="$1"
    local max_lines="${2:-100000}"

    if [ ! -f "$log" ]; then
        return 0
    fi

    local lines
    lines=$(wc -l < "$log")
    if [ "$lines" -gt "$max_lines" ]; then
        local rotated="${log}.${TODAY}.gz"
        gzip -c "$log" > "$rotated"
        : > "$log"
        echo "  Rotated: $(basename "$log") ($lines lines → gz'd)"
    fi

    # Prune old rotations
    find "$(dirname "$log")" -name "$(basename "$log").*.gz" -mtime +3 -delete
}

echo "[$NOW] PHASE 1: Log rotation" >> "$HEALTH_LOG"

# Kalshi WebSocket JSONL — cap at 100K lines, rotate daily, keep 3 days
rotate_jsonl "$KALSHI_LOG_DIR/ws-events.jsonl" 50000

# Kalshi monitor log — cap at 10MB, keep 7 days
rotate_logs "$KALSHI_LOG_DIR/monitor-out.log" 10 7
rotate_logs "$KALSHI_LOG_DIR/ws-out.log" 10 7

# General logs — cap at 20MB, keep 14 days
for log in "$LOG_DIR"/*.log; do
    [ -f "$log" ] || continue
    rotate_logs "$log" 20 14
done

# Health log itself
rotate_logs "$HEALTH_LOG" 10 30

# ── 2. STORAGE WATCHDOG ────────────────────────────────────────────

echo "[$NOW] PHASE 2: Storage watchdog" >> "$HEALTH_LOG"

DISK_PCT=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
DISK_USED=$(df -h / | tail -1 | awk '{print $3}')
DISK_TOTAL=$(df -h / | tail -1 | awk '{print $2}')

WARNING_THRESHOLD=80
CRITICAL_THRESHOLD=90
STORAGE_STATUS="ok"

if [ "$DISK_PCT" -ge "$CRITICAL_THRESHOLD" ]; then
    STORAGE_STATUS="critical"
    echo "  CRITICAL: Disk ${DISK_PCT}% (${DISK_USED}/${DISK_TOTAL})" >> "$HEALTH_LOG"
    touch "$DEGRADED_FLAG"

    # Emergency pruning
    echo "  Emergency prune activated" >> "$HEALTH_LOG"
    
    # Prune old exports (keep last 5 PDFs, delete rest)
    find "$WORKSPACE/exports/pdfs" -type f -name "*.pdf" | sort | head -n -5 | xargs -r rm
    find "$WORKSPACE/exports/benchmarks" -type f -mtime +7 -delete
    find "$WORKSPACE/exports/present" -type f -mtime +7 -delete
    find "$WORKSPACE/exports/social" -type f -mtime +3 -delete  # social posts can go faster
    find "$WORKSPACE/exports/images" -type f -mtime +7 -delete
    find "$WORKSPACE/analysis" -type f -mtime +30 -delete
    find "$WORKSPACE/tmp_review_maps2" -type f -mtime +14 -delete

elif [ "$DISK_PCT" -ge "$WARNING_THRESHOLD" ]; then
    STORAGE_STATUS="warning"
    echo "  WARNING: Disk ${DISK_PCT}% (${DISK_USED}/${DISK_TOTAL})" >> "$HEALTH_LOG"
    # Prune old exports
    find "$WORKSPACE/exports/pdfs" -type f -name "*.pdf" | sort | head -n -10 | xargs -r rm
    find "$WORKSPACE/exports/benchmarks" -type f -mtime +14 -delete
    find "$WORKSPACE/exports/present" -type f -mtime +14 -delete
else
    echo "  OK: Disk ${DISK_PCT}% (${DISK_USED}/${DISK_TOTAL})" >> "$HEALTH_LOG"
    # Clean up if no longer critical
    rm -f "$DEGRADED_FLAG"
fi

# ── 3. PROCESS HEALTH CHECK ────────────────────────────────────────

echo "[$NOW] PHASE 3: Process health" >> "$HEALTH_LOG"

RESTARTED_ANY=false

# Load env for subprocesses
export $(grep -v '^#' "$WORKSPACE/.env" | grep -v '^$' | xargs 2>/dev/null) || true

# Kalshi monitor
if ! pgrep -f "monitor.py.*--loop" > /dev/null 2>&1; then
    if [ ! -f "$DEGRADED_FLAG" ]; then
        cd "$WORKSPACE" && nohup python3 skills/kalshi-trader/scripts/monitor.py \
            --loop --interval 120 --auto-exit \
            > "$KALSHI_LOG_DIR/monitor-out.log" 2>&1 &
        echo "  Restarted: kalshi-monitor (PID $!)" >> "$HEALTH_LOG"
        RESTARTED_ANY=true
    fi
fi

# Kalshi WebSocket listener
if ! pgrep -f "ws_listener" > /dev/null 2>&1; then
    if [ ! -f "$DEGRADED_FLAG" ]; then
        cd "$WORKSPACE" && nohup python3 skills/kalshi-trader/scripts/ws_listener.py \
            --markets KXUSAIRANAGREEMENT-27-26JUN,KXUSAIRANAGREEMENT-27-26JUL,KXUSAIRANAGREEMENT-27-26AUG \
            --log-file "$KALSHI_LOG_DIR/ws-events.jsonl" \
            > "$KALSHI_LOG_DIR/ws-out.log" 2>&1 &
        echo "  Restarted: ws-listener (PID $!)" >> "$HEALTH_LOG"
        RESTARTED_ANY=true
    fi
fi

# Continuous cognition daemon
if ! pgrep -f "cognition_pipeline.*--daemon" > /dev/null 2>&1; then
    if [ ! -f "$DEGRADED_FLAG" ]; then
        cd "$WORKSPACE" && nohup python3 skills/continuous-cognition/scripts/cognition_pipeline.py --daemon \
            > "$LOG_DIR/cognition-daemon.log" 2>&1 &
        echo "  Restarted: cognition-daemon (PID $!)" >> "$HEALTH_LOG"
        RESTARTED_ANY=true
    fi
fi

# Check for runaway processes
MONITOR_COUNT=$(pgrep -f "monitor.py.*--loop" | wc -l)
WS_COUNT=$(pgrep -f "ws_listener" | wc -l)
COG_COUNT=$(pgrep -f "cognition_pipeline.*--daemon" | wc -l)
if [ "$MONITOR_COUNT" -gt 1 ]; then
    echo "  WARNING: $MONITOR_COUNT monitor processes — killing duplicates" >> "$HEALTH_LOG"
    pgrep -f "monitor.py.*--loop" | tail -n +2 | xargs -r kill
fi
if [ "$WS_COUNT" -gt 1 ]; then
    echo "  WARNING: $WS_COUNT ws_listener processes — killing duplicates" >> "$HEALTH_LOG"
    pgrep -f "ws_listener" | tail -n +2 | xargs -r kill
fi
if [ "$COG_COUNT" -gt 1 ]; then
    echo "  WARNING: $COG_COUNT cognition daemons — killing duplicates" >> "$HEALTH_LOG"
    pgrep -f "cognition_pipeline.*--daemon" | tail -n +2 | xargs -r kill
fi

if [ "$RESTARTED_ANY" = false ]; then
    echo "  All processes healthy" >> "$HEALTH_LOG"
fi

# ── 5a. CONTINUOUS COGNITION CYCLE ────────────────────────────────

# Run cognition every 3rd health cycle (~30 min at 10-min intervals)
COG_COUNTER="$WORKSPACE/tasks/.cog-counter"
if [ -f "$COG_COUNTER" ]; then
    COG_N=$(( $(cat "$COG_COUNTER") + 1 ))
else
    COG_N=0
fi

echo "$COG_N" > "$COG_COUNTER"

if [ "$COG_N" -ge 3 ] && [ ! -f "$DEGRADED_FLAG" ]; then
    echo "  Running cognition cycle..." >> "$HEALTH_LOG"
    # Use RuntimeLock to prevent overlap with daemon
    python3 "$WORKSPACE/scripts/runtime_lock.py" --list 2>/dev/null | grep -q "cognition-daemon" && {
        echo "  Cognition daemon running — skipping inline cycle" >> "$HEALTH_LOG"
    } || {
        cd "$WORKSPACE" && timeout 120 python3 skills/continuous-cognition/scripts/cognition_pipeline.py \
            > "$LOG_DIR/cognition-${TODAY}.log" 2>&1 && \
        echo "  Cognition cycle complete" >> "$HEALTH_LOG" || \
        echo "  Cognition cycle failed" >> "$HEALTH_LOG"
    }
    # Generate KJ feed after each cognition cycle
    cd "$WORKSPACE" && timeout 30 python3 analyst/scripts/kj_feed.py \
        > "$LOG_DIR/kj-feed-${TODAY}.log" 2>&1 && \
    echo "  KJ feed generated" >> "$HEALTH_LOG" || \
    echo "  KJ feed generation failed" >> "$HEALTH_LOG"
    # Publish KJ feed
    cd "$WORKSPACE" && timeout 30 python3 analyst/scripts/publish_feed.py --validate \
        > "$LOG_DIR/kj-publish-${TODAY}.log" 2>&1 && \
    echo "  KJ feed published" >> "$HEALTH_LOG" || \
    echo "  KJ feed publish skipped" >> "$HEALTH_LOG"
    echo 0 > "$COG_COUNTER"
fi

# ── 4. STATE CONSISTENCY ───────────────────────────────────────────

echo "[$NOW] PHASE 4: State check" >> "$HEALTH_LOG"

# Check python bytecode orphaned files
PYC_COUNT=$(find "$WORKSPACE" -name '*.pyc' 2>/dev/null | wc -l)
if [ "$PYC_COUNT" -gt 50 ]; then
    find "$WORKSPACE" -name '*.pyc' -delete
    echo "  Cleaned: $PYC_COUNT orphaned .pyc files" >> "$HEALTH_LOG"
fi

# Check for stale temp files
TMP_COUNT=$(find "$WORKSPACE/tmp" -type f -mtime +1 2>/dev/null | wc -l)
if [ "$TMP_COUNT" -gt 0 ]; then
    find "$WORKSPACE/tmp" -type f -mtime +1 -delete
    echo "  Cleaned: $TMP_COUNT stale temp files" >> "$HEALTH_LOG"
fi

# Remove stale task files older than 7 days
find "$WORKSPACE/tasks" -type f -name "*.flag" -mtime +7 -delete 2>/dev/null

# ── 5. HEALTH STATE PERSISTENCE ────────────────────────────────────

echo "[$NOW] PHASE 5: State persistence" >> "$HEALTH_LOG"

# Count active runtime processes
RUNTIME_JOBS=$(ps aux | grep -E 'monitor|ws_listener' | grep -v grep | wc -l)
FAILED_JOBS=0

# Check recent log for failures
if grep -q "ERROR\|CRITICAL\|failed" "$KALSHI_LOG_DIR/monitor-out.log" 2>/dev/null; then
    FAILED_JOBS=$((FAILED_JOBS + 1))
fi

# Generate health state JSON
cat > "$HEALTH_STATE" <<JSONEOF
{
  "timestamp": "$NOW",
  "hostname": "$HOSTNAME",
  "disk": {
    "usage_pct": $DISK_PCT,
    "used": "$DISK_USED",
    "total": "$DISK_TOTAL",
    "status": "$STORAGE_STATUS"
  },
  "processes": {
    "active_runtime_jobs": $RUNTIME_JOBS,
    "monitor_running": $(pgrep -f "monitor.py.*--loop" > /dev/null && echo "true" || echo "false"),
    "ws_listener_running": $(pgrep -f "ws_listener" > /dev/null && echo "true" || echo "false"),
    "failed_jobs": $FAILED_JOBS,
    "restarted_services": $([ "$RESTARTED_ANY" = true ] && echo "true" || echo "false")
  },
  "degraded_mode": $( [ -f "$DEGRADED_FLAG" ] && echo "true" || echo "false"),
  "self_healed": $([ "$RESTARTED_ANY" = true ] && echo "true" || echo "false")
}
JSONEOF

echo "[$NOW] Health state: DISK=${DISK_PCT}% ($STORAGE_STATUS)" >> "$HEALTH_LOG"
echo "[$NOW] Complete" >> "$HEALTH_LOG"
