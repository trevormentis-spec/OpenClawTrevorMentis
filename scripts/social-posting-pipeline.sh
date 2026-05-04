#!/bin/bash
# Social Posting Pipeline — Daily OSINT Brief → Platform Posts
#
# Prepares platform-adapted posts from the daily intel brief.
# Posting mechanism depends on available channel:
#   - agent context: social-media-agent (browser, no keys)
#   - CLI: needs Twitter API keys (social-post) or VibePost key
#
# Outputs ready-to-post content to exports/social/*.md
#
# Cron: 0 13 * * * cd /home/ubuntu/.openclaw/workspace && bash scripts/social-posting-pipeline.sh

set -euo pipefail

WORKSPACE="/home/ubuntu/.openclaw/workspace"
BRIEF_FILE="${WORKSPACE}/tasks/news_analysis.md"
OUTPUT_DIR="${WORKSPACE}/exports/social"
LOG_FILE="${WORKSPACE}/logs/social-pipeline.log"
DRY_RUN=false

mkdir -p "$OUTPUT_DIR" "${WORKSPACE}/logs"

while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run) DRY_RUN=true; shift ;;
    --file) BRIEF_FILE="$2"; shift 2 ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
done

if [ ! -f "$BRIEF_FILE" ]; then
  echo "[$(date)] ❌ Brief not found: $BRIEF_FILE" | tee -a "$LOG_FILE"
  exit 1
fi

DATE_LINE=$(grep -oP '\d{4}-\d{2}-\d{2}' "$BRIEF_FILE" | head -1 || echo "$(date +%F)")

# ── Strip markdown helpers ──
strip_md() {
  echo "$1" | sed 's/^## //g; s/^\*\*//g; s/\*\*$//g; s/`//g; s/\[//g; s/\]//g; s/([^)]*)//g' | tr -s ' '
}

BLUF_RAW=$(grep -A 5 "^## BLUF" "$BRIEF_FILE" | grep -v "BLUF\|^--$" | head -3 | tr '\n' ' ' | sed 's/  / /g')
BLUF=$(strip_md "$BLUF_RAW")

TOP_SECTIONS=$(grep "^## [0-9]" "$BRIEF_FILE" | head -6 | sed 's/^## [0-9]*\.\s*//' | sed 's/\*\*//g')

echo "[$(date)] 📰 Pipeline — preparing posts for $DATE_LINE" | tee -a "$LOG_FILE"

# ── Twitter/X (≤280 chars) ──
TWITTER="🔍 OSINT Brief ${DATE_LINE}

${BLUF:0:160}...👇"
TWITTER="${TWITTER:0:277}..."
echo "$TWITTER" > "${OUTPUT_DIR}/twitter.txt"

# ── LinkedIn (professional post) ──
LINKEDIN="📊 Daily Intelligence Brief — ${DATE_LINE}

${BLUF}

Key developments:
${TOP_SECTIONS}

Full analysis with probability judgments, source scoring, and visual exports:
https://quiet-kangaroo-c0b94c.netlify.app

#OSINT #Intelligence #DailyBrief"
echo "$LINKEDIN" > "${OUTPUT_DIR}/linkedin.txt"

# ── Reddit (title + body) ──
REDDIT_TITLE="Daily OSINT Brief — ${DATE_LINE}: ${BLUF:0:120}..."
REDDIT_BODY="**${DATE_LINE} — Daily Intelligence Brief**

${BLUF}

**Key sections tracked:**
${TOP_SECTIONS}

Full brief with calibrated judgments: https://quiet-kangaroo-c0b94c.netlify.app"
echo "$REDDIT_TITLE" > "${OUTPUT_DIR}/reddit_title.txt"
echo "$REDDIT_BODY" > "${OUTPUT_DIR}/reddit_body.txt"

echo "[$(date)] ✅ Posts saved to exports/social/" | tee -a "$LOG_FILE"
echo "[$(date)]    Twitter:   ${#TWITTER} chars" | tee -a "$LOG_FILE"
echo "[$(date)]    LinkedIn:  ${#LINKEDIN} chars" | tee -a "$LOG_FILE"
echo "[$(date)]    Reddit:    ${#REDDIT_BODY} chars" | tee -a "$LOG_FILE"
