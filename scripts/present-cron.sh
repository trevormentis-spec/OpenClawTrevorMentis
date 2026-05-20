#!/usr/bin/env bash
#==============================================================================
# present-cron.sh — Presentation pipeline cron entry point.
#
# Called by cron after the daily brief pipeline completes.
# Generates all presentation assets (images, charts, maps, audio, video)
# and updates the landing page.
#
# Schedule: daily at 13:45 PT (after brief pipeline at 13:00 PT)
# Cron: 45 13 * * * /home/ubuntu/.openclaw/workspace/scripts/present-cron.sh
#==============================================================================
set -uo pipefail

REPO="/home/ubuntu/.openclaw/workspace"
DATE_UTC=$(date -u +%Y-%m-%d)
DATE_PT=$(TZ='America/Los_Angeles' date +%Y-%m-%d)
LOG="$REPO/logs/present-${DATE_UTC}.log"
OUTDIR="$REPO/exports/present/${DATE_UTC}"
BRIEF_SOURCE="$REPO/tasks/news_analysis.md"
BRIEF_JSON="/tmp/trevor-brief-${DATE_UTC}.json"

mkdir -p "$REPO/logs" "$(dirname "$BRIEF_JSON")"
exec > >(tee -a "$LOG") 2>&1

echo "=== Presentation Pipeline — ${DATE_UTC} ==="
echo "Started at $(date -u)"

# Source env
if [ -f "$REPO/.env" ]; then
    source "$REPO/.env"
fi

# ── Find source brief ──
# Try the existing GSIB JSON path first, then orchestrator, then news_analysis.md
if [ -d "$HOME/trevor-briefings/${DATE_UTC}" ]; then
    BRIEF_DIR="$HOME/trevor-briefings/${DATE_UTC}"
    if [ -f "$BRIEF_DIR/analysis/_gsib_v2.json" ]; then
        cp "$BRIEF_DIR/analysis/_gsib_v2.json" "$BRIEF_JSON"
        echo "Source: GSIB v2 JSON"
    elif [ -f "$BRIEF_DIR/analysis/exec_summary.json" ]; then
        cp "$BRIEF_DIR/analysis/exec_summary.json" "$BRIEF_JSON"
        echo "Source: Orchestrator exec_summary.json"
    fi
fi

if [ ! -f "$BRIEF_JSON" ]; then
    echo "Source: No structured brief found — converting markdown"
    # Convert news_analysis.md to minimal JSON
    python3 -c "
import json
md = open('$BRIEF_SOURCE').read()
title_line = [l for l in md.split('\n') if l.startswith('# ')][:1]
bluf_lines = []
in_bluf = False
for l in md.split('\n'):
    if l.startswith('## BLUF'):
        in_bluf = True; continue
    if in_bluf and l.startswith('##'): break
    if in_bluf and l.strip(): bluf_lines.append(l.strip())

brief = {
    'title': (title_line[0].lstrip('# ') if title_line else 'Daily Intelligence Briefing') + f' — ${DATE_UTC}',
    'bluf': ' '.join(bluf_lines)[:500],
    'headline_judgments': [],
    'sections': [],
}
open('$BRIEF_JSON', 'w').write(json.dumps(brief, indent=2))
print('Converted markdown to minimal brief JSON')
" 2>&1
fi

# ── Run presentation pipeline ──
if [ -f "$BRIEF_JSON" ]; then
    echo ""
    python3 "$REPO/scripts/present/build_presentation.py" \
        --brief "$BRIEF_JSON" \
        --output-dir "$OUTDIR" \
        2>&1 || echo "Pipeline had failures — continuing"
else
    echo "No brief source found — generating standalone visual set"
    python3 "$REPO/scripts/present/build_presentation.py" \
        --brief /dev/null \
        --output-dir "$OUTDIR" \
        --no-cover \
        --skip images maps charts audio video \
        2>&1
fi

echo ""
echo "=== Presentation pipeline complete ==="
echo "Output: $OUTDIR"
echo "Log: $LOG"
