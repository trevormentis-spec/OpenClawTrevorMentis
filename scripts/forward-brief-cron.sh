#!/usr/bin/env bash
#==============================================================================
# forward-brief-cron.sh — Pick up the Trevor brief from Gmail inbox and
#                          forward to Roderick at ~07:00 PT
#
# Flow: 05:00 PT — Trevor pipeline produces brief, delivers to trevor.mentis@gmail.com
#       06:30 PT — This script runs, finds the latest brief, forwards to Roderick
#==============================================================================
set -euo pipefail

REPO="/home/ubuntu/.openclaw/workspace"
DATE_UTC=$(date -u +%Y-%m-%d)
LOG="$REPO/logs/forward-brief-${DATE_UTC}.log"
mkdir -p "$REPO/logs"

echo "=== Forward Brief — ${DATE_UTC} ===" | tee -a "$LOG"
echo "Started at $(date -u)" | tee -a "$LOG"

source "$REPO/.env" 2>/dev/null || true
MATON_API_KEY="${MATON_API_KEY:-}"

cd "$REPO"

# Step 1: Search Gmail inbox for the Trevor brief from today
echo "--- Searching Gmail inbox for today's brief ---" | tee -a "$LOG"

python3 -c "
import urllib.request, urllib.parse, json, base64, sys

api_key = '$MATON_API_KEY'
date_utc = '$DATE_UTC'

# Search for Trevor's brief in inbox today
# The subject format is typically: Global Security & Intelligence Brief — <date>
query = f'in:inbox from:trevor.mentis@gmail.com subject:(Security AND Intelligence AND Brief) after:{date_utc}'
params = urllib.parse.urlencode({'q': query, 'maxResults': '5'})
url = f'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages?{params}'

req = urllib.request.Request(url)
req.add_header('Authorization', f'Bearer {api_key}')
try:
    resp = urllib.request.urlopen(req)
    data = json.load(resp)
    msgs = data.get('messages', [])
except Exception as e:
    print(f'Search 1 failed: {e}')
    msgs = []

if not msgs:
    # Broader search - just look for anything from Trevor today with 'brief'
    query2 = f'in:inbox from:trevor.mentis@gmail.com after:{date_utc}'
    params2 = urllib.parse.urlencode({'q': query2, 'maxResults': '5'})
    url2 = f'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages?{params2}'
    req2 = urllib.request.Request(url2)
    req2.add_header('Authorization', f'Bearer {api_key}')
    try:
        resp2 = urllib.request.urlopen(req2)
        data2 = json.load(resp2)
        msgs = data2.get('messages', [])
    except Exception as e:
        print(f'Search 2 failed: {e}')
        msgs = []

if not msgs:
    print('NO_BRIEF_FOUND')
    sys.exit(0)

msg_id = msgs[0]['id']
print(f'BRIEF_FOUND:{msg_id}')

# Get full message to find attachment and headers
url3 = f'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/{msg_id}'
req3 = urllib.request.Request(url3)
req3.add_header('Authorization', f'Bearer {api_key}')
resp3 = urllib.request.urlopen(req3)
msg = json.load(resp3)

headers = {h['name']: h['value'] for h in msg['payload']['headers']}
subject = headers.get('Subject', 'Global Security & Intelligence Brief')
date_str = headers.get('Date', '')

print(f'SUBJECT:{subject}')
print(f'DATE:{date_str}')

# Save message info for forwarding step
info = {'msg_id': msg_id, 'subject': subject, 'date': date_str}
with open('/tmp/latest_brief_info.json', 'w') as f:
    json.dump(info, f)
" 2>&1 | tee -a "$LOG"

# Check if brief was found
if grep -q "NO_BRIEF_FOUND" "$LOG"; then
    echo "No brief found yet — sleeping 30 min and retrying..." | tee -a "$LOG"
    sleep 1800  # 30 minutes
    
    # Retry once
    python3 -c "
import urllib.request, urllib.parse, json, base64, sys

api_key = '$MATON_API_KEY'
date_utc = '$DATE_UTC'

query = f'in:inbox from:trevor.mentis@gmail.com after:{date_utc}'
params = urllib.parse.urlencode({'q': query, 'maxResults': '5'})
url = f'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages?{params}'
req = urllib.request.Request(url)
req.add_header('Authorization', f'Bearer {api_key}')
try:
    resp = urllib.request.urlopen(req)
    data = json.load(resp)
    msgs = data.get('messages', [])
except Exception as e:
    print(f'Search error in retry: {e}')
    msgs = []
    
    if not msgs:
        print('NO_BRIEF_FOUND')
        sys.exit(0)
    msg_id = msgs[0]['id']
    print(f'BRIEF_FOUND:{msg_id}')
    
    url3 = f'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/{msg_id}'
    req3 = urllib.request.Request(url3)
    req3.add_header('Authorization', f'Bearer {api_key}')
    resp3 = urllib.request.urlopen(req3)
    msg = json.load(resp3)
    headers = {h['name']: h['value'] for h in msg['payload']['headers']}
    subject = headers.get('Subject', 'Global Security & Intelligence Brief')
    date_str = headers.get('Date', '')
    print(f'SUBJECT:{subject}')
    print(f'DATE:{date_str}')
    
    info = {'msg_id': msg_id, 'subject': subject, 'date': date_str}
    with open("/tmp/latest_brief_info.json", "w") as f:
        json.dump(info, f)
" 2>&1 | tee -a "$LOG"
fi

if grep -q "NO_BRIEF_FOUND" "$LOG"; then
    echo "ERROR: No brief from Trevor found in inbox after retry" | tee -a "$LOG"
    # Notify Roderick about the failure
    python3 -c "
import urllib.request, json, base64
api_key = '$MATON_API_KEY'
subject = 'TREVOR Daily Brief — MISSING — ${DATE_UTC}'
body = f'''No daily brief was found in the inbox for ${DATE_UTC}. The Trevor pipeline may not have delivered it yet.

Check trevor.mentis@gmail.com inbox.

TREVOR Automation
'''
boundary = '==TREVOR=='
email = f'''From: trevor.mentis@gmail.com
To: roderick.jones@gmail.com
Subject: $subject
MIME-Version: 1.0
Content-Type: text/plain; charset=\"UTF-8\"

$body'''
raw = base64.urlsafe_b64encode(email.encode()).decode()
req = urllib.request.Request(
    'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/send',
    data=json.dumps({'raw': raw}).encode(), method='POST')
req.add_header('Authorization', f'Bearer {api_key}')
req.add_header('Content-Type', 'application/json')
try:
    urllib.request.urlopen(req, timeout=30)
    print('Missing-brief notification sent')
except Exception as e:
    print(f'Notify failed: {e}')
"
    exit 1
fi

# Step 2: Read the brief info and forward it
echo "--- Forwarding brief to Roderick ---" | tee -a "$LOG"

python3 -c "
import urllib.request, urllib.parse, json, base64, sys, os

api_key = '$MATON_API_KEY'

with open('/tmp/latest_brief_info.json') as f:
    info = json.load(f)

msg_id = info['msg_id']
subject = info['subject']

# Get the full message with attachment
url = f'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/{msg_id}'
req = urllib.request.Request(url)
req.add_header('Authorization', f'Bearer {api_key}')
resp = urllib.request.urlopen(req)
msg = json.load(resp)

# Extract the PDF attachment
def find_attachment(part):
    mt = part.get('mimeType', '')
    fn = part.get('filename', '')
    if mt == 'application/pdf' and fn:
        att_id = part.get('body', {}).get('attachmentId')
        if att_id:
            return att_id, fn
    for sub in part.get('parts', []):
        aid, afn = find_attachment(sub)
        if aid is not None:
            return aid, afn
    return None, None

att_id, att_fn = find_attachment(msg['payload'])

if not att_id:
    print('ERROR: No PDF attachment found in the brief email')
    sys.exit(1)

# Download the PDF attachment
url2 = f'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/{msg_id}/attachments/{att_id}'
req2 = urllib.request.Request(url2)
req2.add_header('Authorization', f'Bearer {api_key}')
resp2 = urllib.request.urlopen(req2)
att_data = json.load(resp2)
pdf_raw = base64.urlsafe_b64decode(att_data['data'] + '===')
pdf_b64 = base64.b64encode(pdf_raw).decode()

# Get the plain text body for the email content
def extract_body(part):
    mt = part.get('mimeType', '')
    if mt == 'text/plain' and part.get('body', {}).get('data'):
        return base64.urlsafe_b64decode(part['body']['data'] + '===').decode('utf-8', errors='replace')
    if mt.startswith('multipart/'):
        for sp in part.get('parts', []):
            result = extract_body(sp)
            if result:
                return result
    return ''

body_text = extract_body(msg['payload']) or msg.get('snippet', '')

# Get date from headers
headers = {h['name']: h['value'] for h in msg['payload']['headers']}
date_str = headers.get('Date', '')
date_short = date_str.split(',')[-1].strip() if ',' in date_str else date_str

# Forward to Roderick
boundary = '==TREVOR_FWD_001=='
forward_subject = f'Global Security & Intelligence Brief — {date_short}'

email_body = f'''From: Trevor <trevor.mentis@gmail.com>
To: Roderick Jones <roderick.jones@gmail.com>
Subject: {forward_subject}
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary=\"{boundary}\"

--{boundary}
Content-Type: text/html; charset=\"UTF-8\"

<html>
<body style=\"font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; background: #f5f5f0; padding: 24px;\">
<div style=\"max-width: 600px; margin: 0 auto; background: white; border-radius: 6px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.08);\">
<div style=\"background: #161616; color: #c9a84c; padding: 24px 32px;\">
<h1 style=\"margin: 0; font-size: 20px; letter-spacing: 1px; text-transform: uppercase;\">Global Security &amp; Intelligence Brief</h1>
<p style=\"margin: 6px 0 0; color: #7a8a3c; font-size: 12px; letter-spacing: 2px; text-transform: uppercase;\">{date_short} — TREVOR Assessment</p>
</div>
<div style=\"padding: 32px;\">
<p style=\"color: #444; font-size: 14px; line-height: 1.6;\">Your daily intelligence assessment is ready.</p>
<p style=\"color: #444; font-size: 14px; line-height: 1.6;\">Full PDF attached — six theatres covered with structured analysis, key judgments, and prediction markets.</p>
<p style=\"color: #888; font-size: 12px; margin-top: 24px; padding-top: 16px; border-top: 1px solid #eee;\">Six theatres: Europe • Sahel • South Asia • Middle East • North America • South America + Global Finance + Prediction Markets</p>
<p style=\"color: #888; font-size: 12px;\">TREVOR — Threat Research and Evaluation Virtual Operations Resource</p>
<p style=\"color: #888; font-size: 12px; margin-top: 8px;\">Delivered daily at ~07:00 PT</p>
</div></div>
</body>
</html>

--{boundary}
Content-Type: application/pdf
Content-Disposition: attachment; filename=\"{att_fn}\"
Content-Transfer-Encoding: base64

{pdf_b64}

--{boundary}--
'''

raw_b64 = base64.urlsafe_b64encode(email_body.encode()).decode()
payload = json.dumps({'raw': raw_b64}).encode()

req = urllib.request.Request(
    'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/send',
    data=payload, method='POST')
req.add_header('Authorization', f'Bearer {api_key}')
req.add_header('Content-Type', 'application/json')

try:
    resp = urllib.request.urlopen(req, timeout=60)
    result = json.loads(resp.read())
    sent_id = result.get('id', 'unknown')
    print(f'Forwarded! Message ID: {sent_id}')
    print(f'To: Roderick Jones <roderick.jones@gmail.com>')
    print(f'Subject: {forward_subject}')
    print(f'Attachment: {att_fn} ({len(pdf_raw)} bytes)')
except Exception as e:
    print(f'Forward failed: {e}')
    sys.exit(1)
" 2>&1 | tee -a "$LOG"

echo "=== Forward Brief — ${DATE_UTC} — Complete ===" | tee -a "$LOG"
