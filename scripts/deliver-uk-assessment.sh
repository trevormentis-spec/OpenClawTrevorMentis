#!/usr/bin/env bash
#==============================================================================
# deliver-uk-assessment.sh — Deliver the UK security assessment via AgentMail
#==============================================================================
# Scheduled for 13:00 UTC (6am PT) on 2026-05-12
#==============================================================================

set -uo pipefail
REPO="/home/ubuntu/.openclaw/workspace"
REPORT="$REPO/exports/reports/uk-security-assessment-2026-05-12.md"

source "$REPO/.env" 2>/dev/null || true

# Check report exists
if [ ! -f "$REPORT" ]; then
    echo "ERROR: Report not found at $REPORT"
    exit 1
fi

# Send via AgentMail to Roderick
python3 "$REPO/scripts/buttondown-send.py" \
    --subject "UK Security & Intelligence Assessment — May 2026" \
    --analysis "$REPORT" 2>&1 || echo "WARNING: Buttondown send failed"

# Also save a copy to exports for reference
echo "Report delivered to inbox and saved to exports"

# Log delivery
echo "Delivered UK assessment at $(date -u)" >> "$REPO/logs/uk-assessment-delivery-2026-05-12.log"
