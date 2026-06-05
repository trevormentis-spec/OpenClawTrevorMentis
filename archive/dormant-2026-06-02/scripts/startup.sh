#!/bin/bash
# Trevor Runtime Startup — runs on VM start
# Source this or call from .bashrc / systemd

WORKSPACE="/home/ubuntu/.openclaw/workspace"
LOG_DIR="$WORKSPACE/logs/kalshi"
mkdir -p "$LOG_DIR"

# Load environment
cd "$WORKSPACE"
set -a
source .env 2>/dev/null
set +a

# 1. Runtime health daemon (starts monitor if dead, rotates logs, checks disk)
# Runs every 10 minutes via cron
echo "runtime-health configured for cron (*/10 * * * *)"

# 2. Kalshi position monitor
if ! pgrep -f "monitor.py.*--loop" > /dev/null 2>&1; then
    nohup python3 skills/kalshi-trader/scripts/monitor.py \
        --loop --interval 120 --auto-exit \
        > "$LOG_DIR/monitor-out.log" 2>&1 &
    echo "Started kalshi-monitor (PID $!)"
else
    echo "kalshi-monitor already running"
fi

# 3. Kalshi WebSocket listener
if ! pgrep -f "ws_listener" > /dev/null 2>&1; then
    nohup python3 skills/kalshi-trader/scripts/ws_listener.py \
        --markets KXUSAIRANAGREEMENT-27-26JUN,KXUSAIRANAGREEMENT-27-26JUL,KXUSAIRANAGREEMENT-27-26AUG \
        --log-file "$LOG_DIR/ws-events.jsonl" \
        > "$LOG_DIR/ws-out.log" 2>&1 &
    echo "Started ws-listener (PID $!)"
else
    echo "ws-listener already running"
fi

# 4. Continuous cognition daemon
if ! pgrep -f "cognition_pipeline.*--daemon" > /dev/null 2>&1; then
    nohup python3 skills/continuous-cognition/scripts/cognition_pipeline.py --daemon \
        > "$LOG_DIR/cognition-daemon.log" 2>&1 &
    echo "Started cognition-daemon (PID $!)"
else
    echo "cognition-daemon already running"
fi

echo "Runtime startup complete"
