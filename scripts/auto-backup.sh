#!/usr/bin/env bash
# Auto-backup: critical config and state files
# Runs daily via cron. Snapshots key files to backups/YYYY-MM-DD/

set -euo pipefail

WORKSPACE="$HOME/.openclaw/workspace"
BACKUP_ROOT="$HOME/.openclaw/backups"
DATE=$(date +%Y-%m-%d)
SNAPSHOT="$BACKUP_ROOT/$DATE"
LOG="$BACKUP_ROOT/backup.log"
RETENTION_DAYS=30

mkdir -p "$SNAPSHOT/config"
mkdir -p "$SNAPSHOT/state"

echo "[$(date '+%Y-%m-%d %H:%M:%S UTC')] Starting backup → $SNAPSHOT" >> "$LOG"

# ── Config files ──
cp /tmp/supervisord-openclaw.conf "$SNAPSHOT/config/supervisord.conf" 2>/dev/null
cp "$HOME/.openclaw/openclaw.json" "$SNAPSHOT/config/openclaw.json" 2>/dev/null
cp "$WORKSPACE/.env" "$SNAPSHOT/config/.env" 2>/dev/null
cp "$WORKSPACE/MEMORY.md" "$SNAPSHOT/config/MEMORY.md" 2>/dev/null

# ── Critical workspace state ──
# Kalshi keys
cp "$WORKSPACE/.kalshi_rsa_key.pem" "$SNAPSHOT/config/" 2>/dev/null

# Active config files
for f in config/active-assignments.yaml config/scope.yaml config/budget.yaml config/topic_themes/; do
  [ -e "$WORKSPACE/$f" ] && cp -r "$WORKSPACE/$f" "$SNAPSHOT/config/" 2>/dev/null || true
done

# Neurotag brain (compact)
cp "$WORKSPACE/brain/memory/semantic/deepseek-usage.json" "$SNAPSHOT/state/" 2>/dev/null
cp "$WORKSPACE/brain/working-memory.json" "$SNAPSHOT/state/" 2>/dev/null || true

# Recent exports (last 7 days)
mkdir -p "$SNAPSHOT/exports"
find "$WORKSPACE/exports" -name "*.md" -type f -mtime -7 -exec cp {} "$SNAPSHOT/exports/" \; 2>/dev/null

# Trade journal
cp "$WORKSPACE/docs/ops/portfolio-overview.md" "$SNAPSHOT/state/" 2>/dev/null || true
for f in "$WORKSPACE/docs/ops/trade-journal-"*.md; do
  [ -f "$f" ] && cp "$f" "$SNAPSHOT/state/"
done

# ── Rotate old backups ──
find "$BACKUP_ROOT" -maxdepth 1 -type d -name "2026-*" -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null

echo "[$(date '+%Y-%m-%d %H:%M:%S UTC')] ✅ Backed up $(find "$SNAPSHOT" -type f | wc -l) files" >> "$LOG"
echo "✅ $DATE backup complete — $(find "$SNAPSHOT" -type f | wc -l) files" >> "$LOG"
