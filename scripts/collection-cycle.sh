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

echo "[collection] $(date -u '+%Y-%m-%d %H:%M UTC') — Start" | tee -a "$LOG"
cd "$REPO"

# 1. OpenWeb API specs + Mexico custom specs + Wikipedia monitor
echo "--- Step 1: OpenWeb pipeline (API specs + Wikipedia) ---" | tee -a "$LOG"
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

echo "[collection] $(date -u '+%Y-%m-%d %H:%M UTC') — Complete" | tee -a "$LOG"
