#!/usr/bin/env bash
#==============================================================================
# deploy_landing_page.sh — Update GitHub Pages landing page with latest brief
#                          UPDATED 2026-05-27: SSH auth, 13-region, new pipeline
#==============================================================================
set -uo pipefail

REPO="/home/ubuntu/.openclaw/workspace"
LANDING_REPO="/tmp/trevor-landing-page"
DATE_UTC=$(date -u +%Y-%m-%d)
DATE_PT=$(TZ='America/Los_Angeles' date +%Y-%m-%d)
LOG="$REPO/logs/deploy-landing-${DATE_UTC}.log"
mkdir -p "$REPO/logs"

echo "=== Deploy Landing Page — ${DATE_UTC} ===" | tee -a "$LOG"
echo "Started at $(date -u)" | tee -a "$LOG"

source "$REPO/.env" 2>/dev/null || true

for cmd in git python3; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: $cmd not found" | tee -a "$LOG"; exit 1
    fi
done

# ── Clone/update repo via SSH ──
if [ -d "$LANDING_REPO/.git" ]; then
    cd "$LANDING_REPO" && git pull origin main 2>&1 | tee -a "$LOG"
else
    rm -rf "$LANDING_REPO"
    git clone git@github.com:trevormentis-spec/trevor-landing-page.git "$LANDING_REPO" 2>&1 | tee -a "$LOG"
fi

# ── Get latest brief data ──
BRIEF_DIR="$HOME/trevor-briefings/${DATE_UTC}"
if [ ! -d "$BRIEF_DIR" ]; then
    # Try yesterday
    BRIEF_DIR="$HOME/trevor-briefings/$(date -u -d 'yesterday' +%Y-%m-%d)"
fi

echo "Brief dir: ${BRIEF_DIR}" | tee -a "$LOG"

# 13 regions with labels
declare -A REGION_LABELS
REGION_LABELS["europe"]="Europe"
REGION_LABELS["north_america"]="North America"
REGION_LABELS["central_america_caribbean"]="Central America & Caribbean"
REGION_LABELS["south_america"]="South America"
REGION_LABELS["middle_east"]="Middle East"
REGION_LABELS["central_asia"]="Central Asia"
REGION_LABELS["south_east_asia"]="South East Asia"
REGION_LABELS["oceania"]="Oceania"
REGION_LABELS["east_asia"]="East Asia"
REGION_LABELS["south_asia"]="South Asia"
REGION_LABELS["prediction_markets"]="Prediction Markets"
REGION_LABELS["north_africa"]="North Africa"
REGION_LABELS["sub_saharan_africa"]="Sub-Saharan Africa"

echo "[" > "$REPO/tmp/summaries.json"

first=true
for region in europe north_america central_america_caribbean south_america middle_east central_asia south_east_asia oceania east_asia south_asia prediction_markets north_africa sub_saharan_africa; do
    label="${REGION_LABELS[$region]}"
    file="$BRIEF_DIR/analysis/${region}.json"
    bluf=""
    
    if [ -f "$file" ]; then
        bluf=$(python3 -c "
import json
with open('$file') as f:
    d = json.load(f)
print(d.get('bluf', d.get('summary', d.get('key_judgments', ['']))[0] if isinstance(d.get('key_judgments'), list) else ''))
" 2>/dev/null | cut -c1-300 || true)
    fi
    
    # Escape for JSON
    bluf=$(echo "$bluf" | python3 -c "import json,sys; print(json.dumps(sys.stdin.read().strip()))" 2>/dev/null || echo '""')
    label_e=$(echo "$label" | python3 -c "import json,sys; print(json.dumps(sys.stdin.read().strip()))" 2>/dev/null || echo '""')
    
    if [ "$first" = true ]; then
        first=false
    else
        echo "," >> "$REPO/tmp/summaries.json"
    fi
    echo "  {\"theatre\": \"$region\", \"label\": $label_e, \"bluf\": $bluf}" >> "$REPO/tmp/summaries.json"
done

echo "]" >> "$REPO/tmp/summaries.json"

# ── Kalshi data ──
KALSHI_FILE=$(ls -t "$REPO/exports/kalshi-scan-*.md" 2>/dev/null | head -1)
if [ -n "$KALSHI_FILE" ]; then
    cp "$KALSHI_FILE" "$REPO/tmp/kalshi_latest.md"
fi

# ── Generate the landing page ──
python3 "$REPO/scripts/_build_landing.py" \
    --index "$LANDING_REPO/index.html" \
    --summaries "$REPO/tmp/summaries.json" \
    --kalshi "$REPO/tmp/kalshi_latest.md" \
    --date "$DATE_PT" \
    --issue "$DATE_PT" \
    --pdf "" \
    --pdf-size "" 2>&1 | tee -a "$LOG"

# ── Commit and push via SSH ──
cd "$LANDING_REPO"
git add -A 2>&1 | tee -a "$LOG"
if git diff --cached --quiet 2>/dev/null; then
    echo "No changes to landing page" | tee -a "$LOG"
else
    git commit -m "Daily update: ${DATE_PT}" 2>&1 | tee -a "$LOG"
    git push origin main 2>&1 | tee -a "$LOG"
    echo "✅ Pushed to GitHub Pages" | tee -a "$LOG"
fi

echo "Live: https://trevormentis-spec.github.io/trevor-landing-page/" | tee -a "$LOG"
echo "=== Deploy complete ===" | tee -a "$LOG"
