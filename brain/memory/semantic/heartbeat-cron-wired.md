# heartbeat-cron-wired

## 2026-05-22

Heartbeat cron job wired: openclaw cron ID 1aec4c02-f744-49ab-a4cb-41bd2d68d2b6 fires every 30m in isolated session. Rotates through: A=feed health audit (scripts/feed_health_audit.py), B=source discovery (scripts/source_discovery.py), C=source pruning (feed_health_audit.py --prune), D=reindex+cost (brain.py reindex). State tracked at brain/memory/heartbeat-state.json. Full cycle: bash scripts/collection-cycle.sh.
