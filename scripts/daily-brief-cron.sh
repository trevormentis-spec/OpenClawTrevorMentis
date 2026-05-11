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
set -euo pipefail

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

# Step 1: Run orchestrator (produce PDF but skip AgentMail delivery)
# Using Claude Opus 4.7 via OpenRouter for analysis writing
# (Switch --model deepseek/deepseek-v4-pro --provider deepseek to fall back)
echo "--- Running orchestrator (Opus 4.7 via OpenRouter) ---" | tee -a "$LOG"
python3 skills/daily-intel-brief/scripts/orchestrate.py \
    --model "anthropic/claude-opus-4.7" \
    --provider openrouter \
    --no-deliver \
    --strict-env 2>&1 | tee -a "$LOG"

ORCHESTRATE_RC=${PIPESTATUS[0]}
if [ $ORCHESTRATE_RC -ne 0 ]; then
    echo "ERROR: Orchestrator failed with rc=$ORCHESTRATE_RC" | tee -a "$LOG"
    # Send failure notification
    python3 -c "
import urllib.request, json, base64
api_key = '$MATON_API_KEY'
subject = 'TREVOR Daily Brief — FAILED — ${DATE_UTC}'
body = f'''The daily brief pipeline failed on ${DATE_UTC} (rc=$ORCHESTRATE_RC).

Check the log at: $LOG

TREVOR Automation
'''
boundary = '==TREVOR_BOUNDARY=='
email = f'''From: trevor.mentis@gmail.com
To: roderick.jones@gmail.com
Subject: $subject
MIME-Version: 1.0
Content-Type: text/plain; charset=\"UTF-8\"

$body'''
raw = base64.urlsafe_b64encode(email.encode()).decode()
req = urllib.request.Request(
    'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/send',
    data=json.dumps({'raw': raw}).encode(),
    method='POST'
)
req.add_header('Authorization', f'Bearer {api_key}')
req.add_header('Content-Type', 'application/json')
try:
    urllib.request.urlopen(req, timeout=30)
    print('Failure notification sent to Roderick')
except Exception as e:
    print(f'Could not send failure notification: {e}')
"
    exit $ORCHESTRATE_RC
fi

# Step 2: Find the generated PDF
PDF_PATH=$(find ~/trevor-briefings/${DATE_UTC}/final -name "brief-${DATE_UTC}.pdf" 2>/dev/null | head -1)
if [ -z "$PDF_PATH" ]; then
    echo "ERROR: No PDF found at ~/trevor-briefings/${DATE_UTC}/final/" | tee -a "$LOG"
    exit 1
fi
echo "PDF found: $PDF_PATH ($(du -h "$PDF_PATH" | cut -f1))" | tee -a "$LOG"

# Step 2b: Maps removed — quality wasn't meeting standards
MAPS_DIR=""
echo "--- Maps disabled per Roderick ---" | tee -a "$LOG"

# Step 2c: Generate AI imagery for the brief sections (optional enhancement)
IMAGES_JSON="$HOME/trevor-briefings/${DATE_UTC}/visuals/section-images.json"
echo "--- Generating section imagery via GenViral Studio AI ---" | tee -a "$LOG"
# Ensure GenViral key is loaded
source "$REPO/.env" 2>/dev/null || true
if [ -n "${GENVIRAL_API_KEY:-}" ]; then
    if python3 "$REPO/scripts/generate_brief_images.py" \
        --working-dir "$HOME/trevor-briefings/${DATE_UTC}" \
        --out-json "$IMAGES_JSON" 2>&1 | tee -a "$LOG"; then
        echo "Section images generated" | tee -a "$LOG"
    else
        echo "WARNING: Image generation failed (non-fatal)" | tee -a "$LOG"
        IMAGES_JSON=""
    fi
else
    echo "GENVIRAL_API_KEY not set — skipping imagery" | tee -a "$LOG"
    IMAGES_JSON=""
fi

# Step 2c: Generate charts for magazine PDF
CHARTS_DIR="$HOME/trevor-briefings/${DATE_UTC}/visuals/charts"
echo "--- Generating infographic charts ---" | tee -a "$LOG"
if python3 "$REPO/scripts/generate_brief_charts.py" \
    --working-dir "$HOME/trevor-briefings/${DATE_UTC}" \
    --out-dir "$CHARTS_DIR" 2>&1 | tee -a "$LOG"; then
    echo "Charts generated" | tee -a "$LOG"
else
    echo "WARNING: Chart generation failed (non-fatal)" | tee -a "$LOG"
    CHARTS_DIR=""
fi

# Step 2d: Generate magazine-quality PDF with maps + imagery
MAGAZINE_PDF="$REPO/exports/pdfs/GSIB-${DATE_UTC}.pdf"
echo "--- Generating magazine-quality PDF ---" | tee -a "$LOG"
VENV_PYTHON="$REPO/.venv_pdf/bin/python"
RENDER_ARGS="--working-dir $HOME/trevor-briefings/${DATE_UTC} --out-pdf $MAGAZINE_PDF"
if [ -n "$MAPS_DIR" ] && [ -d "$MAPS_DIR" ]; then
    RENDER_ARGS="$RENDER_ARGS --maps-dir $MAPS_DIR"
fi
if [ -n "$IMAGES_JSON" ] && [ -f "$IMAGES_JSON" ]; then
    RENDER_ARGS="$RENDER_ARGS --images-json $IMAGES_JSON"
fi
# Add Kalshi data and charts
KALSHI_FILE="$REPO/exports/kalshi-scan-${DATE_UTC}.md"
if [ -f "$KALSHI_FILE" ]; then
    RENDER_ARGS="$RENDER_ARGS --kalshi-json $KALSHI_FILE"
fi
CHARTS_DIR="$HOME/trevor-briefings/${DATE_UTC}/visuals/charts"
if [ -d "$CHARTS_DIR" ]; then
    RENDER_ARGS="$RENDER_ARGS --charts-dir $CHARTS_DIR"
fi
if [ -f "$VENV_PYTHON" ]; then
    if "$VENV_PYTHON" "$REPO/scripts/render_brief_magazine.py" $RENDER_ARGS 2>&1 | tee -a "$LOG"; then
        echo "Magazine PDF generated: $MAGAZINE_PDF" | tee -a "$LOG"
        PDF_PATH="$MAGAZINE_PDF"
    else
        echo "WARNING: Magazine PDF generation failed, using raw brief PDF" | tee -a "$LOG"
    fi
else
    echo "WARNING: .venv_pdf not found, using raw brief PDF" | tee -a "$LOG"
fi

# Step 3: Deliver via Gmail to Roderick
echo "--- Delivering via Gmail ---" | tee -a "$LOG"
python3 -c "
import urllib.request, json, base64, os

api_key = '$MATON_API_KEY'
pdf_path = '$PDF_PATH'
date_utc = '${DATE_UTC}'

with open(pdf_path, 'rb') as f:
    pdf_data = f.read()
pdf_b64 = base64.b64encode(pdf_data).decode()

# Get analysis snippets for the email body
import json as j
exec_summary = {}
try:
    with open(os.path.expanduser(f'~/trevor-briefings/{date_utc}/analysis/exec_summary.json')) as f:
        exec_summary = j.load(f)
except:
    pass

bluf_text = exec_summary.get('bluf', 'Daily intelligence assessment across six theatres.')
judgments = exec_summary.get('five_judgments', [])

judgment_html = ''
for kj in judgments[:5]:
    region = kj.get('drawn_from_region', 'Global')
    statement = kj.get('statement', '')
    band = kj.get('sherman_kent_band', 'assessed')
    pct = kj.get('prediction_pct', '')
    judgment_html += f'<li><strong>[{region}]</strong> {statement} <em>({band}; {pct}% / 7d)</em></li>'

boundary = '==TREVOR_BRIEF_001=='

email_body = f'''From: Trevor <trevor.mentis@gmail.com>
To: Roderick Jones <roderick.jones@gmail.com>
Subject: Global Security & Intelligence Brief — {date_utc}
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary=\"{boundary}\"

--{boundary}
Content-Type: text/html; charset=\"UTF-8\"

<html>
<body style=\"font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; background: #f5f5f0; padding: 24px;\">
<div style=\"max-width: 600px; margin: 0 auto; background: white; border-radius: 6px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.08);\">
<div style=\"background: #161616; color: #c9a84c; padding: 24px 32px;\">
<h1 style=\"margin: 0; font-size: 20px; letter-spacing: 1px; text-transform: uppercase;\">Global Security &amp; Intelligence Brief</h1>
<p style=\"margin: 6px 0 0; color: #7a8a3c; font-size: 12px; letter-spacing: 2px; text-transform: uppercase;\">{date_utc} — TREVOR Assessment</p>
</div>
<div style=\"padding: 32px;\">
<h2 style=\"color: #1a1a2e; font-size: 15px; border-left: 3px solid #c0392b; padding-left: 12px; margin: 0 0 16px;\">BLUF</h2>
<p style=\"color: #444; font-size: 14px; line-height: 1.6;\">''' + bluf_text[:500] + '''</p>
<h2 style=\"color: #1a1a2e; font-size: 15px; border-left: 3px solid #7a8a3c; padding-left: 12px; margin: 24px 0 16px;\">Key Judgments</h2>
<ul style=\"color: #444; font-size: 14px; line-height: 1.7; padding-left: 20px;\">''' + judgment_html + '''</ul>
<p style=\"color: #888; font-size: 12px; margin-top: 24px; padding-top: 16px; border-top: 1px solid #eee;\">Full PDF attached. Six theatres: Europe • Sahel • South Asia • Middle East • North America • South America + Global Finance + Prediction Markets</p>
<p style=\"color: #888; font-size: 12px;\">TREVOR Threat Research and Evaluation Virtual Operations Resource</p>
</div></div>
</body>
</html>

--{boundary}
Content-Type: application/pdf
Content-Disposition: attachment; filename=\"GSIB-{date_utc}.pdf\"
Content-Transfer-Encoding: base64

{pdf_b64}

--{boundary}--
'''

raw_b64 = base64.urlsafe_b64encode(email_body.encode()).decode()
payload = json.dumps({'raw': raw_b64}).encode()

req = urllib.request.Request(
    'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/send',
    data=payload,
    method='POST'
)
req.add_header('Authorization', f'Bearer {api_key}')
req.add_header('Content-Type', 'application/json')

try:
    resp = urllib.request.urlopen(req, timeout=60)
    result = j.loads(resp.read())
    msg_id = result.get('id', 'unknown')
    print(f'Email sent! Message ID: {msg_id}')
    print(f'To: Roderick Jones <roderick.jones@gmail.com>')
    print(f'Subject: Global Security & Intelligence Brief — {date_utc}')
except Exception as e:
    print(f'Delivery failed: {e}')
    exit(1)
" 2>&1 | tee -a "$LOG"

# Step 4: Post to social platforms via GenViral Studio AI
# Uses the brief analysis file to generate original per-platform visuals
echo "--- Posting to social platforms via GenViral Studio AI ---" | tee -a "$LOG"
if [ -n "${GENVIRAL_API_KEY:-}" ]; then
    if bash "$REPO/scripts/genviral-post-brief.sh" 2>&1 | tee -a "$LOG"; then
        echo "Social posts successful" | tee -a "$LOG"
    else
        echo "WARNING: Social posting failed (non-fatal)" | tee -a "$LOG"
    fi
else
    echo "GENVIRAL_API_KEY not set — skipping social posts" | tee -a "$LOG"
fi

# Step 5: Post to Moltbook
# Uses the same PDF — posts brief content to builds + agents submolts
echo "--- Posting to Moltbook ---" | tee -a "$LOG"
if [ -n "${MOLTBOOK_API_KEY:-}" ]; then
    if bash "$REPO/scripts/moltbook-post-brief.sh" --pdf "$PDF_PATH" 2>&1 | tee -a "$LOG"; then
        echo "Moltbook posts successful" | tee -a "$LOG"
    else
        echo "WARNING: Moltbook posting failed (non-fatal)" | tee -a "$LOG"
    fi
else
    echo "MOLTBOOK_API_KEY not set — skipping Moltbook" | tee -a "$LOG"
fi

# Step 6: Generate agent-optimized JSON and notify subscribers
echo "--- Building agent API ---" | tee -a "$LOG"
if bash "$REPO/scripts/agent-brief-api.sh" --publish 2>&1 | tee -a "$LOG"; then
    echo "Agent API ready" | tee -a "$LOG"
else
    echo "WARNING: Agent API step failed (non-fatal)" | tee -a "$LOG"
fi

# Step 7: Build and publish agent-first GSIB
# Structured JSON for AI agent consumption — posted to Moltbook + API
# Replaces maps/images/PDF as the primary delivery format for agents
echo "--- Building agent-first GSIB (no maps, no PDF) ---" | tee -a "$LOG"
source "$REPO/.env" 2>/dev/null || true
export MOLTBOOK_API_KEY="${MOLTBOOK_API_KEY:-}"
if [ -n "${MOLTBOOK_API_KEY:-}" ]; then
    if python3 "$REPO/scripts/build_agent_brief.py" \
        --working-dir "$HOME/trevor-briefings/${DATE_UTC}" \
        --moltbook 2>&1 | tee -a "$LOG"; then
        echo "Agent brief built and posted to Moltbook" | tee -a "$LOG"
    else
        echo "WARNING: Agent brief build failed" | tee -a "$LOG"
    fi
else
    python3 "$REPO/scripts/build_agent_brief.py" \
        --working-dir "$HOME/trevor-briefings/${DATE_UTC}" 2>&1 | tee -a "$LOG"
    echo "Agent brief built (not posted — no Moltbook key)" | tee -a "$LOG"
fi

echo "=== Daily Brief Cron — ${DATE_UTC} — Complete ===" | tee -a "$LOG"
