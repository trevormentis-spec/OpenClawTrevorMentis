#!/usr/bin/env bash
#==============================================================================
# daily-brief-cron.sh — Run the Daily Intel Brief pipeline and deliver via Gmail
#
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  BINDING RULE: Only post the daily intel brief from Gmail.          ║
# ║  No promotional content, no product announcements, no marketing     ║
# ║  posts — ONLY the daily intel brief goes to social platforms.        ║
# ╚══════════════════════════════════════════════════════════════════════╝
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
export MATON_API_KEY="${MATON_API_KEY:-}"
export AGENTMAIL_API_KEY="${AGENTMAIL_API_KEY:-}"
export GENVIRAL_API_KEY="${GENVIRAL_API_KEY:-}"
export STRIPE_SECRET_KEY="${STRIPE_SECRET_KEY:-}"
export MOLTBOOK_API_KEY="${MOLTBOOK_API_KEY:-}"

# Check DeepSeek key
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "ERROR: DEEPSEEK_API_KEY not set" | tee -a "$LOG"
    exit 1
fi

cd "$REPO"

# Step 1: Run orchestrator (produce PDF but skip AgentMail delivery)
echo "--- Running orchestrator ---" | tee -a "$LOG"
python3 skills/daily-intel-brief/scripts/orchestrate.py \
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

# Step 4: Post to social platforms via GenViral
# Uses the same PDF that was just emailed to Roderick
echo "--- Posting to social platforms via GenViral ---" | tee -a "$LOG"
if [ -n "${GENVIRAL_API_KEY:-}" ]; then
    if bash "$REPO/scripts/genviral-post-brief.sh" --pdf "$PDF_PATH" 2>&1 | tee -a "$LOG"; then
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

echo "=== Daily Brief Cron — ${DATE_UTC} — Complete ===" | tee -a "$LOG"
