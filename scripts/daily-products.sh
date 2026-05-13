#!/usr/bin/env bash
#==============================================================================
# daily-products.sh — Post-GSIB product generation pipeline
#
# After the daily brief completes, generates three additional products:
#   1. Product suggestions from today's GSIB
#   2. Keir Starmer political survival assessment (LDAP-7)
#   3. Geopolitical trading report ($1000 synthetic portfolio)
#
# All three are included in the daily email delivery.
#==============================================================================
set -uo pipefail

REPO="/home/ubuntu/.openclaw/workspace"
DATE_UTC=$(date -u +%Y-%m-%d)
DATE_PT=$(TZ='America/Los_Angeles' date +%Y-%m-%d)
LOG="$REPO/logs/daily-products-${DATE_UTC}.log"
mkdir -p "$REPO/logs"

echo "=== Daily Products — ${DATE_UTC} ===" | tee -a "$LOG"
echo "Started at $(date -u)" | tee -a "$LOG"

cd "$REPO"

# Step 1: Product Suggestions
echo "--- Generating product suggestions ---" | tee -a "$LOG"
python3 scripts/product_suggestions.py --date "$DATE_UTC" 2>&1 | tee -a "$LOG"
PRODUCT_RC=${PIPESTATUS[0]}
echo "  exit code: $PRODUCT_RC" | tee -a "$LOG"

# Step 2: Starmer Daily Assessment
echo "--- Running Starmer assessment ---" | tee -a "$LOG"
python3 scripts/starmer_daily.py --date "$DATE_UTC" 2>&1 | tee -a "$LOG"
STARMER_RC=${PIPESTATUS[0]}
echo "  exit code: $STARMER_RC" | tee -a "$LOG"

# Step 3: Geopolitical Trading
echo "--- Running geo trader ---" | tee -a "$LOG"
python3 scripts/geo_trader.py --date "$DATE_UTC" 2>&1 | tee -a "$LOG"
GEOTRADE_RC=${PIPESTATUS[0]}
echo "  exit code: $GEOTRADE_RC" | tee -a "$LOG"

# Build combined summary for email
COMBINED="$REPO/analysis/daily-products-${DATE_UTC}.md"
{
  echo "# Daily Products — ${DATE_PT}"
  echo ""
  
  # Product suggestions summary
  if [ -f "$REPO/analysis/product-suggestions/${DATE_UTC}.md" ]; then
    echo "## 📦 New Product Suggestions"
    echo ""
    grep "^## " "$REPO/analysis/product-suggestions/${DATE_UTC}.md" | head -5 | while read line; do
      stripped="${line##*#}"
      echo "- ${stripped:-$line}"
    done
    echo ""
    echo "[See full product suggestions]($REPO/analysis/product-suggestions/${DATE_UTC}.md)"
    echo ""
  fi

  # Starmer summary
  if [ -f "$REPO/analysis/starmer/${DATE_UTC}.md" ]; then
    echo "## 👤 Keir Starmer — Political Survival"
    echo ""
    grep -E "Survival Probability:|Dimension|Score" "$REPO/analysis/starmer/${DATE_UTC}.md" | head -10
    echo ""
    echo "[See full assessment]($REPO/analysis/starmer/${DATE_UTC}.md)"
    echo ""
  fi

  # Geo trader summary
  if [ -f "$REPO/analysis/geotrade/${DATE_UTC}.md" ]; then
    echo "## 💰 Geopolitical Trading — $1000 Portfolio"
    echo ""
    grep -E "Total P&L|Open Positions|Total Value|Total trades|Win rate|Portfolio Summary" "$REPO/analysis/geotrade/${DATE_UTC}.md" | head -10
    echo ""
    echo "[See full trading report]($REPO/analysis/geotrade/${DATE_UTC}.md)"
    echo ""
  fi
} > "$COMBINED"

echo "=== Daily Products — ${DATE_UTC} — Complete ===" | tee -a "$LOG"
