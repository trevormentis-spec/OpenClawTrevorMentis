#!/bin/bash
# Quick self-heal baseline — start everything. Run on-demand.
cd /home/ubuntu/.openclaw/workspace
export $(grep -v '^#' .env | grep -v '^$' | xargs)

# Start runtime services (idempotent)
pgrep -f "monitor.py.*--loop" > /dev/null || \
    nohup python3 skills/kalshi-trader/scripts/monitor.py --loop --interval 120 --auto-exit > logs/kalshi/monitor-out.log 2>&1 &

pgrep -f "ws_listener" > /dev/null || \
    nohup python3 skills/kalshi-trader/scripts/ws_listener.py \
        --markets KXUSAIRANAGREEMENT-27-26JUN,KXUSAIRANAGREEMENT-27-26JUL,KXUSAIRANAGREEMENT-27-26AUG \
        --log-file logs/kalshi/ws-events.jsonl > logs/kalshi/ws-out.log 2>&1 &

pgrep -f "cognition_pipeline.*--daemon" > /dev/null || \
    nohup python3 skills/continuous-cognition/scripts/cognition_pipeline.py --daemon > logs/cognition-daemon.log 2>&1 &

echo "Runtime services: started"
bash scripts/runtime-report.sh
