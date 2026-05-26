#!/bin/bash
# publish_all_desks.sh — Publish all 5 Philby desk feeds + status + Moltbook
# Called from runtime-health.sh after each cognition cycle

set -euo pipefail

WORKSPACE="/home/ubuntu/.openclaw/workspace"
# Export all env vars from .env (they're not pre-exported)
set -a
source "$WORKSPACE/.env" 2>/dev/null || true
set +a
LOG_DIR="$WORKSPACE/logs"
TODAY=$(date -u +"%Y-%m-%d")
NOW=$(date -u +"%H:%M:%S")

cd "$WORKSPACE"

echo "[$NOW] Philby: Publishing all 5 desk feeds..."

for desk in iran ukraine us_china cartel energy; do
    # 1. Generate desk-scoped KJ feed
    python3 analyst/scripts/kj_feed.py --desk "$desk" \
        > "$LOG_DIR/philby-${desk}-${TODAY}.log" 2>&1 && \
    echo "  ✅ $desk feed generated" || \
    echo "  ❌ $desk feed failed"

    # 2. Publish desk feed via AgentMail (dry-run until explicitly enabled)
    python3 analyst/scripts/publish_feed.py --desk "$desk" \
        >> "$LOG_DIR/philby-${desk}-${TODAY}.log" 2>&1 && \
    echo "  ✅ $desk published" || \
    echo "  ❌ $desk publish failed"
done

# 3. Post desk status to Moltbook
python3 philby/scripts/desk_status.py --moltbook \
    >> "$LOG_DIR/philby-moltbook-${TODAY}.log" 2>&1 && \
echo "  ✅ Desk status posted to Moltbook" || \
echo "  ❌ Moltbook post failed"

# 4. Run I&W alert engine for all desks
python3 analyst/scripts/alert_engine.py \
    >> "$LOG_DIR/alert-engine-${TODAY}.log" 2>&1 && \
echo "  ✅ I&W alert check complete" || \
echo "  ❌ I&W alert check failed"

echo "[$NOW] Philby: All desks published"
