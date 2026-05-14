#!/usr/bin/env bash
#==============================================================================
# daily-brief-cron.sh — Run the Daily Intel Brief pipeline and deliver via Gmail
#
# Pipeline:
#   1. Orchestrate: gather sources → analyze → produce PDF + analysis file
#   2. Deliver to Roderick via Gmail (PDF + HTML summary)
#   3. Post to social via GenViral Studio AI (original visuals from analysis)
#   4. Post to Moltbook
#   5. Build agent API
#
# Schedule: Triggered by OpenClaw cron at 05:00 PT
# Flow:     05:00 PT — collection + analysis + visuals + PDF assembly
#           07:00 PT — delivered to Roderick via Gmail + social posts
#==========================================================================
#
# Schedule: Triggered by OpenClaw cron at 05:00 PT
# Flow:     05:00 PT — starts collection + analysis + visuals + PDF assembly
#           07:00 PT — brief delivered to Roderick via Gmail
#
# The pipeline takes ~90-120 minutes. Output lands at ~07:00 PT.
#==============================================================================
set -uo pipefail
# Trap: disable errexit for piped commands where failure is non-fatal
_pipestatus() { return \${PIPESTATUS[0]}; }

REPO="/home/ubuntu/.openclaw/workspace"
DATE_UTC=$(date -u +%Y-%m-%d)
LOG="$REPO/logs/daily-brief-${DATE_UTC}.log"
mkdir -p "$REPO/logs"

echo "=== Daily Brief Cron — ${DATE_UTC} ===" | tee -a "$LOG"
echo "Started at $(date -u)" | tee -a "$LOG"

# Source environment
source "$REPO/.env" 2>/dev/null || true
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-}"
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"
export MATON_API_KEY="${MATON_API_KEY:-}"
export AGENTMAIL_API_KEY="${AGENTMAIL_API_KEY:-}"
export GENVIRAL_API_KEY="${GENVIRAL_API_KEY:-}"
export STRIPE_SECRET_KEY="${STRIPE_SECRET_KEY:-}"
export MOLTBOOK_API_KEY="${MOLTBOOK_API_KEY:-}"
export BUTTONDOWN_API_KEY="${BUTTONDOWN_API_KEY:-}"

# Check OpenRouter key (primary model provider for writing)
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "ERROR: OPENROUTER_API_KEY not set" | tee -a "$LOG"
    exit 1
fi

cd "$REPO"

# Step 1: Run orchestrator — tiered model routing
# Tier-1: Opus 4.7 (via OpenRouter) for exec summary + red-team
# Tier-2: DeepSeek V4 Flash (via DeepSeek Direct) for 6 regional analyses
# (Switch --model deepseek/deepseek-v4-pro --provider deepseek to fall back)
echo "--- Running orchestrator (tiered: Flash for regions, Opus 4.7 for exec) ---" | tee -a "$LOG"
python3 skills/daily-intel-brief/scripts/orchestrate.py \
    --model "anthropic/claude-opus-4.7" \
    --tier2-model "deepseek/deepseek-chat" \
    --provider openrouter \
    --no-deliver \
    --strict-env 2>&1 | tee -a "$LOG"

ORCHESTRATE_RC=${PIPESTATUS[0]}
if [ $ORCHESTRATE_RC -ne 0 ]; then
    echo "ERROR: Orchestrator failed with rc=$ORCHESTRATE_RC" | tee -a "$LOG"
    # Send failure notification
    set +e  # disable exit on error for failure notification
    python3 scripts/failure_notify.py "$MATON_API_KEY" "$DATE_UTC" "$ORCHESTRATE_RC" "$LOG" 2>/dev/null || true
    set -e 2>/dev/null || true
    exit $ORCHESTRATE_RC
fi

# Step 2: Deliver the brief as a clean email with prediction markets and suggested trades
# No PDF. No graphics. No images. Email-only.
echo "--- Delivering daily brief via AgentMail (email-only, no PDF) ---" | tee -a "$LOG"
python3 "$REPO/scripts/deliver_brief_email.py" --date "$DATE_UTC" --send 2>&1 | tee -a "$LOG"

# Step 3: Post to social platforms via GenViral Studio AI
echo "--- Posting to social platforms via GenViral Studio AI ---" | tee -a "$LOG"
if [ -n "${GENVIRAL_API_KEY:-}" ]; then
    set +e
    bash "$REPO/scripts/genviral-post-brief.sh" 2>&1 | tee -a "$LOG"
    POST_RC=${PIPESTATUS[0]}
    set -e 2>/dev/null || true
    if [ $POST_RC -eq 0 ]; then
        echo "Social posts successful" | tee -a "$LOG"
    else
        echo "WARNING: Social posting failed (exit code $POST_RC) — continuing" | tee -a "$LOG"
    fi
else
    echo "GENVIRAL_API_KEY not set — skipping social posts" | tee -a "$LOG"
fi

# Step 4: Postdiction — check yesterday's predictions against today's evidence
echo "--- Running postdiction (calibration check) ---" | tee -a "$LOG"
YESTERDAY_DIR="$HOME/trevor-briefings/$(TZ='America/Los_Angeles' date -d 'yesterday' +%Y-%m-%d 2>/dev/null || echo '')"
TODAY_DIR="$HOME/trevor-briefings/${DATE_UTC}"
if [ -d "$YESTERDAY_DIR" ] && [ -f "$YESTERDAY_DIR/analysis/exec_summary.json" ]; then
    set +e
    python3 "$REPO/scripts/postdict.py" \
        --today "$TODAY_DIR" \
        --yesterday "$YESTERDAY_DIR" 2>&1 | tee -a "$LOG"
    set -e 2>/dev/null || true
else
    echo "No yesterday brief found — skipping postdiction" | tee -a "$LOG"
fi

# Step 5: Build agent API + publish to Moltbook
echo "--- Building agent API ---" | tee -a "$LOG"
set +e
bash "$REPO/scripts/agent-brief-api.sh" --publish 2>&1 | tee -a "$LOG"
set -e 2>/dev/null || true
python3 "$REPO/scripts/build_agent_brief.py" \
    --working-dir "$HOME/trevor-briefings/${DATE_UTC}" --moltbook 2>&1 | tee -a "$LOG"

# Step 6: Publish to Buttondown newsletter
# Sends the daily brief as a newsletter email to all subscribers
echo "--- Publishing to Buttondown newsletter ---" | tee -a "$LOG"
source "$REPO/.env" 2>/dev/null || true
if [ -n "\${BUTTONDOWN_API_KEY:-}" ]; then
    if bash "$REPO/scripts/buttondown-send.sh" --subject "GSIB Daily Brief — ${DATE_PT}" 2>&1 | tee -a "$LOG"; then
        echo "Buttondown newsletter published" | tee -a "$LOG"
    else
        echo "WARNING: Buttondown publish failed (non-fatal)" | tee -a "$LOG"
    fi
else
    echo "BUTTONDOWN_API_KEY not set — skipping newsletter" | tee -a "$LOG"
fi

# Step 7: Update and deploy landing page (GitHub Pages)
echo "--- Deploying landing page ---" | tee -a "$LOG"
if bash "$REPO/scripts/deploy_landing_page.sh" 2>&1 | tee -a "$LOG"; then
    echo "Landing page deployed to GitHub Pages" | tee -a "$LOG"
else
    echo "WARNING: Landing page deploy failed (non-fatal)" | tee -a "$LOG"
fi

# Step 8: Self-assessment — run after pipeline steps
# Produces a system health report + prompt injection if critical issues found
echo "--- Running self-assessment daemon ---" | tee -a "$LOG"
if python3 "$REPO/scripts/self_assessment.py" 2>&1 | tee -a "$LOG"; then
    echo "Self-assessment complete" | tee -a "$LOG"
else
    echo "WARNING: Self-assessment flagged issues (non-fatal, check report)" | tee -a "$LOG"
fi

# Step 9: Daily Products — product suggestions, Starmer analysis, geo trading
echo "--- Running daily products (suggestions, Starmer, trading) ---" | tee -a "$LOG"
bash "$REPO/scripts/daily-products.sh" 2>&1 | tee -a "$LOG"
PRODUCTS_RC=${PIPESTATUS[0]}
if [ $PRODUCTS_RC -eq 0 ]; then
    echo "Daily products generated successfully" | tee -a "$LOG"
else
    echo "WARNING: Daily products pipeline had issues (rc=$PRODUCTS_RC)" | tee -a "$LOG"
fi

# Step 10: Benchmark comparison — Perplexity GSIB vs Trevor GSIB
echo "--- Running Perplexity benchmark comparison ---" | tee -a "$LOG"
if python3 "$REPO/scripts/benchmark_compare.py" --save 2>&1 | tee -a "$LOG"; then
    echo "Benchmark comparison complete" | tee -a "$LOG"
else
    echo "WARNING: Benchmark comparison failed (non-fatal, may need manual run)" | tee -a "$LOG"
fi

echo "=== Daily Brief Cron — ${DATE_UTC} — Complete ===" | tee -a "$LOG"
