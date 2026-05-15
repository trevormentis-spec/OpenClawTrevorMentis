#!/bin/bash
# DEPRECATED — Replaced by genviral-post-brief.sh
# This script generates text posts for Twitter/LinkedIn/Reddit from PDF screenshots.
# The new pipeline uses GenViral Studio AI to generate original visual slideshows
# from the brief analysis. See scripts/genviral-post-brief.sh for the replacement.
#
# Outputs ready-to-post content to exports/social/*.md
#
# Cron: 0 13 * * * cd /home/ubuntu/.openclaw/workspace && bash scripts/social-posting-pipeline.sh

set -euo pipefail

WORKSPACE="/home/ubuntu/.openclaw/workspace"
OUTPUT_DIR="${WORKSPACE}/exports/social"
LOG_FILE="${WORKSPACE}/logs/social-pipeline.log"
TMPDIR="/tmp/social-pipeline-$$"
MATON_API_KEY="${MATON_API_KEY:-}"
DRY_RUN=false

mkdir -p "$OUTPUT_DIR" "${WORKSPACE}/logs" "$TMPDIR"

# Source .env for API keys
source "${WORKSPACE}/.env" 2>/dev/null || true
export MATON_API_KEY

# ── Dependencies ──
for cmd in pdftotext python3; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "[$(date)] ❌ $cmd not found" | tee -a "$LOG_FILE"
        exit 1
    fi
done

if [ -z "$MATON_API_KEY" ]; then
    echo "[$(date)] ❌ MATON_API_KEY not set — required to fetch PDF from Gmail" | tee -a "$LOG_FILE"
    exit 1
fi

while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run) DRY_RUN=true; shift ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
done

echo "[$(date)] ═══ Social Posting Pipeline ═══" | tee -a "$LOG_FILE"
echo "[$(date)] Source: Gmail label 'Important Myclaw use this'" | tee -a "$LOG_FILE"

# ── Step 1: Fetch the latest brief PDF from Gmail ──
echo "[$(date)] ─── Fetching PDF from Gmail ───" | tee -a "$LOG_FILE"

PDF_PATH=$(python3 << 'PYEOF' 2>/dev/null)
import urllib.request, urllib.parse, json, base64, os, sys

api_key = os.environ.get('MATON_API_KEY', '')
label_query = 'label:important-myclaw-use-this'
tmpdir = os.environ.get('TMPDIR', '/tmp')

# Search by label
url = 'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages?q=' + urllib.parse.quote(label_query) + '&maxResults=1'
req = urllib.request.Request(url)
req.add_header('Authorization', f'Bearer {api_key}')
try:
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read())
except Exception as e:
    print(f'Gmail search failed: {e}', file=sys.stderr)
    sys.exit(1)

if not data.get('messages'):
    print('No messages found with that label', file=sys.stderr)
    sys.exit(1)

msg_id = data['messages'][0]['id']

# Get full message
url2 = f'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/{msg_id}'
req2 = urllib.request.Request(url2)
req2.add_header('Authorization', f'Bearer {api_key}')
try:
    resp2 = urllib.request.urlopen(req2, timeout=30)
    msg = json.loads(resp2.read())
except Exception as e:
    print(f'Failed to fetch message: {e}', file=sys.stderr)
    sys.exit(1)

# Find PDF attachment
def find_pdf(parts):
    for part in parts:
        if part.get('filename', '').endswith('.pdf'):
            body = part.get('body', {})
            if body.get('data'):
                return base64.urlsafe_b64decode(body['data'])
            elif body.get('attachmentId'):
                att_id = body['attachmentId']
                url3 = f'https://gateway.maton.ai/google-mail/gmail/v1/users/me/messages/{msg_id}/attachments/{att_id}'
                req3 = urllib.request.Request(url3)
                req3.add_header('Authorization', f'Bearer {api_key}')
                try:
                    resp3 = urllib.request.urlopen(req3, timeout=30)
                    att = json.loads(resp3.read())
                    if att.get('data'):
                        return base64.urlsafe_b64decode(att['data'])
                except:
                    pass
        if part.get('parts'):
            result = find_pdf(part['parts'])
            if result:
                return result
    return None

pdf_data = find_pdf(msg.get('payload', {}).get('parts', []))

if not pdf_data:
    body = msg.get('payload', {}).get('body', {})
    if body.get('data') and msg.get('payload', {}).get('filename', '').endswith('.pdf'):
        pdf_data = base64.urlsafe_b64decode(body['data'])

if not pdf_data:
    print('No PDF attachment found', file=sys.stderr)
    sys.exit(1)

from datetime import date
today = date.today().isoformat()
local_path = f'{tmpdir}/brief-from-gmail-{today}.pdf'
with open(local_path, 'wb') as f:
    f.write(pdf_data)
print(local_path)
PYEOF
) || {
    echo "[$(date)] ❌ Failed to fetch PDF from Gmail" | tee -a "$LOG_FILE"
    exit 1
}

echo "[$(date)] ✅ PDF fetched: $PDF_PATH ($(du -h "$PDF_PATH" | cut -f1))" | tee -a "$LOG_FILE"

# ── Step 2: Extract text from PDF ──
echo "[$(date)] ─── Extracting content from PDF ───" | tee -a "$LOG_FILE"
FULL_TEXT=$(pdftotext "$PDF_PATH" - 2>/dev/null) || {
    echo "[$(date)] ❌ pdftotext failed" | tee -a "$LOG_FILE"
    exit 1
}

if [ -z "$FULL_TEXT" ]; then
    echo "[$(date)] ⚠️  Empty text from PDF" | tee -a "$LOG_FILE"
    exit 1
fi

# Try to extract date from PDF content
DATE_LINE=$(echo "$FULL_TEXT" | grep -oP '\d{4}-\d{2}-\d{2}' | head -1 || echo "$(date +%F)")

# Extract BLUF (try various formats)
BLUF=$(echo "$FULL_TEXT" | grep -i -A10 -m1 "BLUF\|BOTTOM LINE\|EXECUTIVE SUMMARY\|KEY JUDGMENTS" 2>/dev/null | head -10 | tr '\n' ' ' | sed 's/  */ /g' | cut -c1-400 || true)
if [ -z "$BLUF" ]; then
    # Fallback: first portion of text
    BLUF=$(echo "$FULL_TEXT" | head -c 500 | tr '\n' ' ' | sed 's/  */ /g' || true)
fi

# Extract section headings for key developments list
TOP_SECTIONS=$(echo "$FULL_TEXT" | grep -i -E "^(## |[A-Z][A-Z ]+[A-Z][: ])" | head -6 | sed 's/^[#* ]*//' || true)

echo "[$(date)] 📰 Content extracted — Date: $DATE_LINE" | tee -a "$LOG_FILE"
echo "[$(date)]    BLUF: ${BLUF:0:120}..." | tee -a "$LOG_FILE"

# ── Step 3: Generate platform posts ──
echo "[$(date)] ─── Generating platform posts ───" | tee -a "$LOG_FILE"

# Twitter/X (≤280 chars)
TWITTER="🔍 OSINT Brief ${DATE_LINE}

${BLUF:0:160}...👇"
TWITTER="${TWITTER:0:277}..."
echo "$TWITTER" > "${OUTPUT_DIR}/twitter.txt"

# LinkedIn (professional post)
LINKEDIN="📊 Daily Intelligence Brief — ${DATE_LINE}

${BLUF}

Key developments:
${TOP_SECTIONS}

#OSINT #Intelligence #DailyBrief"
echo "$LINKEDIN" > "${OUTPUT_DIR}/linkedin.txt"

# Reddit (title + body)
REDDIT_TITLE="Daily OSINT Brief — ${DATE_LINE}: ${BLUF:0:120}..."
REDDIT_BODY="**${DATE_LINE} — Daily Intelligence Brief**

${BLUF}

**Key sections tracked:**
${TOP_SECTIONS}"
echo "$REDDIT_TITLE" > "${OUTPUT_DIR}/reddit_title.txt"
echo "$REDDIT_BODY" > "${OUTPUT_DIR}/reddit_body.txt"

echo "[$(date)] ✅ Posts saved to exports/social/" | tee -a "$LOG_FILE"
echo "[$(date)]    Twitter:   ${#TWITTER} chars" | tee -a "$LOG_FILE"
echo "[$(date)]    LinkedIn:  ${#LINKEDIN} chars" | tee -a "$LOG_FILE"
echo "[$(date)]    Reddit:    ${#REDDIT_BODY} chars" | tee -a "$LOG_FILE"

# ── Cleanup ──
rm -rf "$TMPDIR"
echo "[$(date)] ═══ Pipeline complete ═══" | tee -a "$LOG_FILE"
