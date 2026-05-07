#!/usr/bin/env bash
#==============================================================================
# deploy_landing_page.sh — Update the GitHub Pages landing page with the latest
#                          DailyIntelAgent product content.
#==============================================================================
set -euo pipefail

REPO="/home/ubuntu/.openclaw/workspace"
SKILL_DIR="$HOME/.openclaw/skills/OpenClawTrevorMentis/skills/daily_intel"
LANDING_REPO="/tmp/trevor-landing-page"
DATE_UTC=$(date -u +%Y-%m-%d)
DATE_PT=$(TZ='America/Los_Angeles' date +%Y-%m-%d)
LOG="$REPO/logs/deploy-landing-${DATE_UTC}.log"

mkdir -p "$REPO/logs" "$REPO/tmp"

echo "=== Deploy Landing Page — ${DATE_UTC} ===" | tee -a "$LOG"
echo "Started at $(date -u)" | tee -a "$LOG"

source "$REPO/.env" 2>/dev/null || true

for cmd in git curl jq python3 pdftotext; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: $cmd not found" | tee -a "$LOG"; exit 1
    fi
done

# ── Clone/update repo ──
GH_TOKEN="${GH_TOKEN:-}"
REPO_URL="https://trevormentis-spec:${GH_TOKEN}@github.com/trevormentis-spec/trevor-landing-page.git"

if [ -d "$LANDING_REPO/.git" ]; then
    cd "$LANDING_REPO" && git pull origin main 2>&1 | tee -a "$LOG"
else
    rm -rf "$LANDING_REPO"
    git clone "$REPO_URL" "$LANDING_REPO" 2>&1 | tee -a "$LOG"
fi

# ── Get latest state ──
ISSUE=""
PDF_PATH=""
STATE_FILE="$SKILL_DIR/cron_tracking/state.json"
if [ -f "$STATE_FILE" ]; then
    ISSUE=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('issue_number',''))" 2>/dev/null || echo "")
    PDF_PATH=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('pdf_path',''))" 2>/dev/null || echo "")
fi
if [ -z "$PDF_PATH" ] || [ ! -f "$PDF_PATH" ]; then
    PDF_PATH=$(ls -t "$SKILL_DIR"/security_brief_*.pdf 2>/dev/null | head -1)
fi
ISSUE="${ISSUE:-$DATE_PT}"

echo "Issue: $ISSUE" | tee -a "$LOG"
echo "PDF: ${PDF_PATH:-none}" | tee -a "$LOG"

# ── Extract BLUF summaries to temp files ──
THEATRES=("europe" "middle_east" "africa" "asia" "north_america" "south_america" "global_finance")
THEATRE_LABELS=("Europe" "Middle East" "Africa" "Asia" "North America" "South America" "Global Finance")
THEATRE_ICONS=("🇪🇺" "🌍" "🌍" "🌏" "🌎" "🌎" "💰")

echo "[]" > "$REPO/tmp/summaries.json"

for i in "${!THEATRES[@]}"; do
    t="${THEATRES[$i]}"
    label="${THEATRE_LABELS[$i]}"
    icon="${THEATRE_ICONS[$i]}"
    file="$SKILL_DIR/assessments/${t}.md"
    bluf=""
    
    if [ -f "$file" ]; then
        bluf=$(grep -A5 -m1 "Bottom Line Up Front" "$file" 2>/dev/null | tail -4 | tr '\n' ' ' | sed 's/  */ /g' | cut -c1-300 || true)
        if [ -z "$bluf" ]; then
            bluf=$(grep "^# " "$file" | head -1 | sed 's/^# //' | head -c 100 || true)
        fi
    fi
    
    # Escape for JSON
    bluf=$(echo "$bluf" | python3 -c "import json,sys; print(json.dumps(sys.stdin.read().strip()))" 2>/dev/null || echo '""')
    label_e=$(echo "$label" | python3 -c "import json,sys; print(json.dumps(sys.stdin.read().strip()))" 2>/dev/null || echo '""')
    
    # Append to JSON array using python
    python3 -c "
import json
with open('$REPO/tmp/summaries.json') as f:
    data = json.load(f)
data.append({'theatre': '$t', 'label': $label_e, 'icon': '$icon', 'bluf': $bluf})
with open('$REPO/tmp/summaries.json', 'w') as f:
    json.dump(data, f, indent=2)
" 2>&1 | tee -a "$LOG"
done

# ── Extract Kalshi data ──
KALSHI_FILE=$(ls -t "$REPO/exports/kalshi-scan-*.md" 2>/dev/null | head -1)
if [ -n "$KALSHI_FILE" ]; then
    cp "$KALSHI_FILE" "$REPO/tmp/kalshi_latest.md"
fi

# ── Copy PDF ──
PDF_FILENAME=""
if [ -n "$PDF_PATH" ] && [ -f "$PDF_PATH" ]; then
    PDF_FILENAME=$(basename "$PDF_PATH")
    cp "$PDF_PATH" "$LANDING_REPO/$PDF_FILENAME"
fi

# ── Generate the landing page ──
python3 "$REPO/scripts/_build_landing.py" \
    --index "$LANDING_REPO/index.html" \
    --summaries "$REPO/tmp/summaries.json" \
    --kalshi "$REPO/tmp/kalshi_latest.md" \
    --date "$DATE_PT" \
    --issue "$ISSUE" \
    --pdf "$PDF_FILENAME" \
    --pdf-size "${PDF_SIZE:-?}" 2>&1 | tee -a "$LOG"

# ── Commit and push ──
cd "$LANDING_REPO"
git add -A 2>&1 | tee -a "$LOG"
# Check for changes (git diff --cached --quiet returns 1 when changes exist)
if git diff --cached --quiet 2>/dev/null; then
    echo "No changes" | tee -a "$LOG"
else
    git commit -m "Daily update: issue #${ISSUE} — ${DATE_PT}" 2>&1 | tee -a "$LOG"
    git push origin main 2>&1 | tee -a "$LOG"
fi

echo "Live: https://trevormentis-spec.github.io/trevor-landing-page/" | tee -a "$LOG"
echo "=== Deploy complete ===" | tee -a "$LOG"
