#!/usr/bin/env bash
#==============================================================================
# daily-text-brief.sh — Text-only Daily Intel Brief pipeline
#
# Pipeline:
#   1. Pre-collection: Mexico scan, OpenWeb sweep, prediction markets
#   2. Core collection: web sources → incidents (collect.py)
#   3. Enrich incidents: Mexico merge + Gmail/AgentMail intel
#   4. Analysis: Opus 4.7 for ALL tiers via OpenRouter
#   5. Assemble + deliver: text briefing via Gmail to roderick.jones@gmail.com
#   6. Review: Opus 4.7 critique → improvement suggestions
#   7. Track: postdiction calibration + source cross-check
#
# Intel sources include:
#   - Web: OpenWeb API specs, RSS feeds, Wikipedia monitor
#   - Email: Gmail (ISW, CTP, Cipher Brief, FP) + AgentMail inbox
#   - Markets: Kalshi + Polymarket prediction markets
#   - Mexico: reverse-engineered Spanish-language sources
#
# Schedule: Triggered by OpenClaw cron at 05:00 PT
# Flow:     05:00 PT — collection + enrichment
#           06:00 PT — Opus 4.7 analysis (all tiers)
#           07:00 PT — brief delivered via Gmail
#
# NO PDF. NO SOCIAL POSTS. NO NEWSLETTER. NO LANDING PAGE.
# Just text intelligence delivered to your inbox.
#==============================================================================
set -uo pipefail

REPO="/home/ubuntu/.openclaw/workspace"
DATE_UTC=$(date -u +%Y-%m-%d)
LOG="$REPO/logs/daily-brief-${DATE_UTC}.log"
mkdir -p "$REPO/logs"

echo "=== Daily Text Brief — ${DATE_UTC} ===" | tee -a "$LOG"
echo "Started at $(date -u)" | tee -a "$LOG"

# Source environment
source "$REPO/.env" 2>/dev/null || true
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-}"
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"
export MATON_API_KEY="${MATON_API_KEY:-}"

if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "ERROR: OPENROUTER_API_KEY not set" | tee -a "$LOG"
    exit 1
fi
if [ -z "$MATON_API_KEY" ]; then
    echo "ERROR: MATON_API_KEY not set" | tee -a "$LOG"
    exit 1
fi

cd "$REPO"

# =========================================================================
# STEP 1: PRE-COLLECTION
# =========================================================================

# Step 1a: Mexico scan — Spanish-language + institutional sources
echo "--- Running Mexico daily scan ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/topic_morning_brief.py" 2>&1 | tee -a "$LOG"
set -e 2>/dev/null || true

# Step 1b: OpenWeb API collection — specs, Wikipedia monitor, news sites
echo "--- OpenWeb pipeline collection ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/pipeline_openweb_collect.py" 2>&1 | tee -a "$LOG"
set -e 2>/dev/null || true

# Step 1b.5: RSS feed collection — 161 verified sources from sources_tested.json
# Fetches a rotating subset (25 per day) to keep the pipeline fast while cycling through all sources.
# Output: WORKING_DIR/raw/rss_incidents.json → merged into collect.py incidents.
echo "--- RSS feed collection (rotating, 161 verified sources) ---" | tee -a "$LOG"
WORKING_DIR="$HOME/trevor-briefings/${DATE_UTC}"
mkdir -p "$WORKING_DIR/raw"
set +e
python3 "$REPO/scripts/rss_collector.py" \
    --working-dir "$WORKING_DIR" \
    --rotate \
    --max-feeds 25 \
    --cap-per-region 8 \
    --delay 0.5 2>&1 | tee -a "$LOG"
RSS_RC=${PIPESTATUS[0]}
if [ $RSS_RC -eq 0 ]; then
    echo "RSS collection succeeded — incidents in rss_incidents.json" | tee -a "$LOG"
    RSS_FILE="$WORKING_DIR/raw/rss_incidents.json"
    if [ -f "$RSS_FILE" ]; then
        INCIDENT_COUNT=$(python3 -c "import json; d=json.load(open('$RSS_FILE')); print(len(d))" 2>/dev/null || echo "?")
        echo "RSS incidents collected: $INCIDENT_COUNT" | tee -a "$LOG"
    fi
else
    echo "WARNING: RSS collection failed (non-fatal)" | tee -a "$LOG"
fi
set -e 2>/dev/null || true

# Step 1c: Compile calibration directives from postdiction history
echo "--- Compiling calibration directives ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/compile_calibration_directives.py" 2>&1 | tee -a "$LOG"
set -e 2>/dev/null || true

# Step 1d: Source discovery — find new RSS/sources
# Runs a random-query rotated source discovery to continuously expand coverage
# across all 10 regions.
echo "--- Source discovery (random query rotation) ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/source_discovery.py" 2>&1 | tee -a "$LOG"
set -e 2>/dev/null || true

# Step 1e: Kalshi/Polymarket scan
echo "--- Scanning prediction markets ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/kalshi_scanner.py" --save --compare-polymarket 2>&1 | tee -a "$LOG"
KALSHI_RC=${PIPESTATUS[0]}
set -e 2>/dev/null || true
if [ $KALSHI_RC -eq 0 ]; then
    KALSHI_FILE="$REPO/exports/kalshi-scan-${DATE_UTC}.md"
    if [ -f "$KALSHI_FILE" ]; then
        echo "Kalshi scan saved: $KALSHI_FILE" | tee -a "$LOG"
    fi
else
    echo "Kalshi scan failed (non-fatal)" | tee -a "$LOG"
fi

# =========================================================================
# STEP 2: WEB COLLECTION → incidents.json
# =========================================================================

WORKING_DIR="$HOME/trevor-briefings/${DATE_UTC}"
mkdir -p "$WORKING_DIR/raw"

# Step 2a: Run web collector (sources.json → raw/incidents.json)
echo "--- Running web collector (sources.json → incidents) ---" | tee -a "$LOG"
python3 skills/daily-intel-brief/scripts/collect.py \
    --working-dir "$WORKING_DIR" \
    --regions skills/daily-intel-brief/references/regions.json \
    --sources analyst/meta/sources.json 2>&1 | tee -a "$LOG"
COLLECT_RC=${PIPESTATUS[0]}
if [ $COLLECT_RC -ne 0 ]; then
    echo "ERROR: Web collector failed with rc=$COLLECT_RC" | tee -a "$LOG"
    exit $COLLECT_RC
fi

# Step 2b: Merge RSS incidents into main incidents.json
# RSS collector ran in Step 1b.5; now merge those incidents into the main file
echo "--- Merging RSS incidents into incidents.json ---" | tee -a "$LOG"
RSS_INCIDENTS="$WORKING_DIR/raw/rss_incidents.json"
MAIN_INCIDENTS="$WORKING_DIR/raw/incidents.json"
if [ -f "$RSS_INCIDENTS" ] && [ -f "$MAIN_INCIDENTS" ]; then
    set +e
    python3 -c "
import json
# Load both files
with open('$RSS_INCIDENTS') as f:
    rss_items = json.load(f)
with open('$MAIN_INCIDENTS') as f:
    main_items = json.load(f)

# Merge: add RSS items not already in main (dedup by headline)
existing_headlines = {i['headline'][:60].lower() for i in main_items}
added = 0
for item in rss_items:
    key = item['headline'][:60].lower()
    if key not in existing_headlines:
        main_items.append(item)
        existing_headlines.add(key)
        added += 1

# Re-categorize items by category count
print(f'Merged {added} new RSS incidents into {len(main_items)} total incidents')

with open('$MAIN_INCIDENTS', 'w') as f:
    json.dump(main_items, f, indent=2)
" 2>&1 | tee -a "$LOG"
    set -e 2>/dev/null || true
else
    echo "RSS incidents file not found, skipping merge" | tee -a "$LOG"
fi

# =========================================================================
# STEP 3: ENRICH INCIDENTS (Mexico + Email Intel)
# =========================================================================

# Step 3a: Merge Mexico scan results into incidents.json
echo "--- Merging Mexico scan results ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/topic_morning_brief.py" --send 2>&1 | tee -a "$LOG"
set -e 2>/dev/null || true

# Step 3b: Inject email intel from Gmail + AgentMail into incidents.json
# MUST run AFTER collect.py (which overwrites incidents.json)
echo "--- Injecting email intel (Gmail + AgentMail) into incidents ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/collect_email_intel.py" --working-dir "$WORKING_DIR" 2>&1 | tee -a "$LOG"
EMAIL_INTEL_RC=${PIPESTATUS[0]}
if [ $EMAIL_INTEL_RC -eq 0 ]; then
    echo "Email intel injected into incidents" | tee -a "$LOG"
else
    echo "WARNING: Email intel collection failed (non-fatal)" | tee -a "$LOG"
fi
set -e 2>/dev/null || true

# =========================================================================
# STEP 4: ANALYSIS — Run analyze.py directly (not through orchestrator)
#
# This gives us control over sequencing: collect.py → enrich → analyze
# Using the orchestrator's --use-mock-incidents would skip real analysis.
# =========================================================================

echo "--- Running analysis (Opus 4.7 for all tiers, enriched incidents) ---" | tee -a "$LOG"
python3 skills/daily-intel-brief/scripts/analyze.py \
    --working-dir "$WORKING_DIR" \
    --prompts skills/daily-intel-brief/references/deepseek-prompts.md \
    --regions skills/daily-intel-brief/references/regions.json \
    --model "anthropic/claude-opus-4.7" \
    --tier2-model "deepseek/deepseek-v4-pro" \
    --provider openrouter \
    --tier2-provider deepseek \
    2>&1 | tee -a "$LOG"
ANALYZE_RC=${PIPESTATUS[0]}
if [ $ANALYZE_RC -ne 0 ]; then
    echo "ERROR: Analysis failed with rc=$ANALYZE_RC" | tee -a "$LOG"
    exit $ANALYZE_RC
fi

# Post-analysis: update collection state
set +e
python3 scripts/collection_state.py --update --analysis-dir "$WORKING_DIR/analysis" 2>&1 | tee -a "$LOG"
set -e 2>/dev/null || true

# =========================================================================
# STEP 5: NEWSLETTER RECOMMENDATIONS
# =========================================================================

echo "--- Searching for new newsletter recommendations ---" | tee -a "$LOG"
NEWSLETTER_RECS_FILE="$REPO/exports/newsletter-recs/daily-${DATE_UTC}.txt"
mkdir -p "$REPO/exports/newsletter-recs"
set +e
python3 "$REPO/scripts/daily_newsletter_finder.py" > "$NEWSLETTER_RECS_FILE" 2>&1
FINDER_RC=${PIPESTATUS[0]}
if [ $FINDER_RC -eq 0 ] && grep -q "NEWSLETTER" "$NEWSLETTER_RECS_FILE" 2>/dev/null; then
    echo "Newsletter recommendations found" | tee -a "$LOG"
else
    NEWSLETTER_RECS_FILE=""
    echo "No new newsletter recommendations today" | tee -a "$LOG"
fi
set -e 2>/dev/null || true

# =========================================================================
# STEP 6: ASSEMBLE & DELIVER TEXT BRIEF
# =========================================================================

echo "--- Assembling text brief ---" | tee -a "$LOG"
PM_SCAN_FILE="$REPO/exports/kalshi-scan-${DATE_UTC}.md"

# Fall back to pm-scan-final if kalshi-scan doesn't exist
if [ ! -f "$PM_SCAN_FILE" ]; then
    PM_SCAN_FILE="$REPO/exports/pm-scan-final-${DATE_UTC}.md"
fi
# Fall further back to most recent
if [ ! -f "$PM_SCAN_FILE" ]; then
    PM_SCAN_FILE=$(ls -t "$REPO/exports"/{kalshi-scan,pm-scan-final}-*.md 2>/dev/null | head -1)
fi
if [ ! -f "$PM_SCAN_FILE" ]; then
    PM_SCAN_FILE=""
    echo "No prediction market scan found (non-fatal)" | tee -a "$LOG"
fi

python3 "$REPO/scripts/send_text_brief_gmail.py" \
    --working-dir "$WORKING_DIR" \
    --date "$DATE_UTC" \
    --to "roderick.jones@gmail.com" \
    ${PM_SCAN_FILE:+--kalshi-scan "$PM_SCAN_FILE"} \
    ${NEWSLETTER_RECS_FILE:+--newsletter-recs "$NEWSLETTER_RECS_FILE"} \
    --save-only 2>&1 | tee -a "$LOG"
SAVE_RC=${PIPESTATUS[0]}
if [ $SAVE_RC -ne 0 ]; then
    echo "ERROR: Brief assembly failed with rc=$SAVE_RC" | tee -a "$LOG"
    exit $SAVE_RC
fi

# Step 6b: Humanize — remove AI writing patterns from the assembled brief
BRIEF_FILE="$REPO/exports/daily-brief-${DATE_UTC}.txt"
if [ -f "$BRIEF_FILE" ]; then
    echo "--- Humanizing brief text ---" | tee -a "$LOG"
    python3 "$REPO/scripts/humanize_brief.py" --file "$BRIEF_FILE" --in-place 2>&1 | tee -a "$LOG"
fi

# Step 6c: Send humanized brief via Gmail
# Reads the saved file (now humanized) and sends it
echo "--- Sending humanized brief via Gmail ---" | tee -a "$LOG"
python3 "$REPO/scripts/send_text_brief_gmail.py" \
    --date "$DATE_UTC" \
    --to "roderick.jones@gmail.com" \
    --read-saved 2>&1 | tee -a "$LOG"
if [ $SEND_RC -ne 0 ]; then
    echo "ERROR: Brief delivery failed with rc=$SEND_RC" | tee -a "$LOG"
    exit $SEND_RC
fi
echo "Brief delivered to roderick.jones@gmail.com" | tee -a "$LOG"

# =========================================================================
# STEP 7: OPUS 4.7 REVIEW
# =========================================================================

echo "--- Running Opus 4.7 review ---" | tee -a "$LOG"
BRIEF_FILE="$REPO/exports/daily-brief-${DATE_UTC}.txt"
if [ -f "$BRIEF_FILE" ]; then
    python3 "$REPO/scripts/review_daily_brief.py" \
        --brief "$BRIEF_FILE" \
        --date "$DATE_UTC" 2>&1 | tee -a "$LOG"
    REVIEW_RC=${PIPESTATUS[0]}
    if [ $REVIEW_RC -eq 0 ]; then
        echo "Opus 4.7 review complete — see exports/reviews/review-${DATE_UTC}.md" | tee -a "$LOG"
    else
        echo "WARNING: Review failed (non-fatal)" | tee -a "$LOG"
    fi
else
    echo "WARNING: No brief file found at $BRIEF_FILE — skipping review" | tee -a "$LOG"
fi

# =========================================================================
# STEP 8: POSTDICTION (Calibration Tracking)
# =========================================================================

echo "--- Running postdiction (calibration check) ---" | tee -a "$LOG"
YESTERDAY_DIR="$HOME/trevor-briefings/$(TZ='America/Los_Angeles' date -d 'yesterday' +%Y-%m-%d 2>/dev/null || echo '')"
if [ -d "$YESTERDAY_DIR" ] && [ -f "$YESTERDAY_DIR/analysis/exec_summary.json" ]; then
    set +e
    python3 "$REPO/scripts/postdict.py" \
        --today "$WORKING_DIR" \
        --yesterday "$YESTERDAY_DIR" 2>&1 | tee -a "$LOG"
    set -e 2>/dev/null || true
else
    echo "No yesterday brief found — skipping postdiction" | tee -a "$LOG"
fi

# =========================================================================
# STEP 9: SOURCE CROSS-CHECK
# =========================================================================

echo "--- Source cross-check ---" | tee -a "$LOG"
set +e
python3 "$REPO/scripts/source_crosscheck.py" --all 2>&1 | tee -a "$LOG"
set -e 2>/dev/null || true

# =========================================================================
# DONE
# =========================================================================

echo "=== Daily Text Brief — ${DATE_UTC} — Complete ===" | tee -a "$LOG"
