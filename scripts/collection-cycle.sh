#!/usr/bin/env bash
# collection-cycle.sh — Full collection pipeline for daily intel.
# Runs: openweb API specs → custom specs → Wikipedia monitor → social monitor
#        → source cross-check → RSS feeds
# Designed for OpenClaw heartbeat or cron.
#
# Usage:
#   bash scripts/collection-cycle.sh              # Collect + check
#   bash scripts/collection-cycle.sh --live       # Passed through to Phase 2

set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$REPO/logs/collection-$(date +%Y%m%d).log"
mkdir -p "$(dirname "$LOG")"

echo "[collection] $(date -u '+%Y-%m-%d %H:%M UTC') — Full heartbeat cycle" | tee -a "$LOG"

# Rotate through all 4 phases
echo "--- Phase A: Feed health audit ---" | tee -a "$LOG"
python3 "$REPO/scripts/feed_health_audit.py" 2>&1 | tee -a "$LOG"

echo "--- Phase B: Source discovery ---" | tee -a "$LOG"
python3 "$REPO/scripts/source_discovery.py" 2>&1 | tee -a "$LOG"

echo "--- Phase C: Source pruning ---" | tee -a "$LOG"
# Phase C: Auto-prune dead feeds (>3 consecutive failures)
python3 "$REPO/scripts/feed_health_audit.py" --prune  # AUTO_PRUNE enabled 2>&1 | tee -a "$LOG"

echo "--- Phase D: Brain reindex + cost snapshot ---" | tee -a "$LOG"
python3 "$REPO/brain/scripts/brain.py" reindex 2>&1 | tee -a "$LOG"
python3 "$REPO/scripts/deepseek_monitor.py" --snapshot 2>&1 | tee -a "$LOG"

echo "[collection] $(date -u '+%Y-%m-%d %H:%M UTC') — Start" | tee -a "$LOG"
cd "$REPO"

# 1. Phase A: Feed health audit
echo "--- Phase A: Feed health audit ---" | tee -a "$LOG"
python3 scripts/pipeline_openweb_collect.py 2>&1 | tee -a "$LOG"

# 2. Social monitor (Bluesky + HackerNews)
echo "--- Step 2: Social monitor ---" | tee -a "$LOG"
python3 scripts/social_monitor.py --keywords "CJNG,Sinaloa,Sheinbaum,USMCA,cartel,fentanyl,Mexico,Brazil,semiconductor" 2>&1 | tee -a "$LOG"

# 3. Source cross-check (API vs RSS quality)
echo "--- Step 3: Source cross-check ---" | tee -a "$LOG"
python3 scripts/source_crosscheck.py --all 2>&1 | tee -a "$LOG"

# 4. RSS feed collection (if daily-intel-brief collect.py exists)
echo "--- Step 4: RSS feed collection ---" | tee -a "$LOG"
if [ -f "skills/daily-intel-brief/scripts/collect.py" ]; then
    python3 skills/daily-intel-brief/scripts/collect.py \
        --working-dir "$REPO" \
        --regions skills/daily-intel-brief/references/regions.json \
        --sources analyst/meta/sources.json 2>&1 | tee -a "$LOG"
fi

# 5. Pipeline stats
echo "--- Step 5: Collection records stats ---" | tee -a "$LOG"
python3 scripts/append_collection_record.py --stats 2>&1 | tee -a "$LOG"

# 6. Source freshness check + auto-demote stale feeds
echo "--- Step 6: Source freshness + auto-demote ---" | tee -a "$LOG"
python3 scripts/check_source_freshness.py --pipeline --auto-demote --summary 2>&1 | tee -a "$LOG"
python3 scripts/check_source_freshness.py --summary 2>&1 | tee -a "$LOG"

# 7. Update STATUS.md
python3 analyst/status_generator.py 2>&1 | tee -a "$LOG"

echo "[collection] $(date -u '+%Y-%m-%d %H:%M UTC') — Full heartbeat cycle" | tee -a "$LOG"

# Rotate through all 4 phases
echo "--- Phase A: Feed health audit ---" | tee -a "$LOG"
python3 "$REPO/scripts/feed_health_audit.py" 2>&1 | tee -a "$LOG"

echo "--- Phase B: Source discovery ---" | tee -a "$LOG"
python3 "$REPO/scripts/source_discovery.py" 2>&1 | tee -a "$LOG"

echo "--- Phase C: Source pruning ---" | tee -a "$LOG"
# Phase C: Auto-prune dead feeds (>3 consecutive failures)
python3 "$REPO/scripts/feed_health_audit.py" --prune  # AUTO_PRUNE enabled 2>&1 | tee -a "$LOG"

echo "--- Phase D: Brain reindex + cost snapshot ---" | tee -a "$LOG"
python3 "$REPO/brain/scripts/brain.py" reindex 2>&1 | tee -a "$LOG"
python3 "$REPO/scripts/deepseek_monitor.py" --snapshot 2>&1 | tee -a "$LOG"

echo "[collection] $(date -u '+%Y-%m-%d %H:%M UTC') — Complete" | tee -a "$LOG"
