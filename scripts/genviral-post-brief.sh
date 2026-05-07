#!/usr/bin/env bash
#==============================================================================
# genviral-post-brief.sh — Post the Daily Intel Brief to social platforms
#
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  BINDING RULE: Content source is the daily intel brief from Gmail.  ║
# ║  Source PDF labeled "Important Myclaw use this". Content can go to  ║
# ║  any platform (LinkedIn, X, TikTok, Moltbook) but must originate    ║
# ║  from that Gmail PDF. No standalone promotional/marketing posts.    ║
# ║  --gmail mode is the ONLY authorized path for production posting.   ║
# ║  --pdf mode is for testing/debugging only.                          ║
# ╚══════════════════════════════════════════════════════════════════════╝
#
# Usage:
#   ./genviral-post-brief.sh --gmail                      [fetch from Gmail by label]
#   ./genviral-post-brief.sh --pdf /path/to/brief.pdf    [TESTING ONLY]
#
# The Gmail PDF is labeled "Important Myclaw use this" — this is the
# authoritative source for all GenViral social posts.
#
# Pipeline:
#   1. Get the PDF (local path or fetch from Gmail)
#   2. pdftotext → extract BLUF + key content for captions
#   3. pdftoppm → extract pages as PNG images
#   4. Upload images to GenViral CDN
#   5. Post slideshow to LinkedIn (3 pages)
#   6. Post slideshow to Twitter/X (2 pages, condensed caption)
#   7. Post slideshow to TikTok (3 pages, draft mode)
#   8. Log everything to genviral workspace performance log
#==============================================================================
set -euo pipefail

REPO="/home/ubuntu/.openclaw/workspace"
GENVIRAL_SCRIPT="$REPO/skills/genviral/scripts/genviral.sh"
DATE_UTC=$(date -u +%Y-%m-%d)
DATE_PT=$(TZ='America/Los_Angeles' date +%Y-%m-%d)
LOG="$REPO/logs/genviral-post-${DATE_UTC}.log"
GENVIRAL_LOG="$REPO/skills/genviral/workspace/performance/log.json"
TMPDIR="/tmp/genviral-brief-${DATE_UTC}"
MATON_API_KEY="${MATON_API_KEY:-}"
GENVIRAL_API_KEY="${GENVIRAL_API_KEY:-}"

mkdir -p "$TMPDIR" "$REPO/logs"

echo "=== GenViral Post Brief — ${DATE_UTC} ===" | tee -a "$LOG"
echo "Started at $(date -u)" | tee -a "$LOG"

# Source environment and export for subprocesses
source "$REPO/.env" 2>/dev/null || true
export MATON_API_KEY
export GENVIRAL_API_KEY

# ---------- Dependencies ----------
for cmd in pdftotext pdftoppm curl jq python3; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: $cmd not found" | tee -a "$LOG"
        exit 1
    fi
done

if [ -z "$GENVIRAL_API_KEY" ]; then
    echo "ERROR: GENVIRAL_API_KEY not set" | tee -a "$LOG"
    exit 1
fi

# ---------- Get the PDF ----------
PDF_PATH=""
FETCH_MODE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --pdf) PDF_PATH="$2"; FETCH_MODE="local"; shift 2 ;;
        --gmail) FETCH_MODE="gmail"; shift ;;
        *) echo "Usage: $0 --pdf <path> | --gmail"; exit 1 ;;
    esac
done

if [ "$FETCH_MODE" = "gmail" ]; then
    if [ -z "$MATON_API_KEY" ]; then
        echo "ERROR: MATON_API_KEY needed for Gmail fetch" | tee -a "$LOG"
        exit 1
    fi
    echo "--- Fetching PDF from Gmail (label: Important Myclaw use this) ---" | tee -a "$LOG"

    PDF_PATH=$(python3 << 'PYEOF'
import urllib.request, urllib.parse, json, base64, os, sys
import datetime

api_key = os.environ.get('MATON_API_KEY', '')
label_query = 'label:important-myclaw-use-this'
tmpdir = os.environ.get('TMPDIR', '/tmp')
date_utc = datetime.date.today().isoformat()

# Search for messages
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

# Find PDF attachment in all parts
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
    # Try inline payload
    body = msg.get('payload', {}).get('body', {})
    if body.get('data') and msg.get('payload', {}).get('filename', '').endswith('.pdf'):
        pdf_data = base64.urlsafe_b64decode(body['data'])

if not pdf_data:
    print('No PDF attachment found in message', file=sys.stderr)
    sys.exit(1)

local_path = f'{tmpdir}/brief-from-gmail-{date_utc}.pdf'
# Note: date_utc comes from heredoc env, fallback 'unknown' is cosmetic only
with open(local_path, 'wb') as f:
    f.write(pdf_data)
print(local_path)
PYEOF
) || {
    echo "ERROR: Failed to fetch PDF from Gmail" | tee -a "$LOG"
    exit 1
}
    echo "PDF fetched: $PDF_PATH ($(du -h "$PDF_PATH" | cut -f1))" | tee -a "$LOG"
fi

if [ -z "$PDF_PATH" ] || [ ! -f "$PDF_PATH" ]; then
    echo "ERROR: No PDF found at $PDF_PATH" | tee -a "$LOG"
    exit 1
fi

# ---------- Extract text for captions ----------
echo "--- Extracting content ---" | tee -a "$LOG"
FULL_TEXT=$(pdftotext "$PDF_PATH" - 2>/dev/null)

# Extract BLUF — try multiple formats (Perplexity brief, magazine brief, standard)
BLUF=$(echo "$FULL_TEXT" | grep -i -A10 -m1 "BLUF\|BOTTOM LINE\|EXECUTIVE SUMMARY" 2>/dev/null | head -10 | tr '\n' ' ' | sed 's/  */ /g' | cut -c1-400 || true)
if [ -z "$BLUF" ]; then
    # Fallback: first 300 chars of the text
    BLUF=$(echo "$FULL_TEXT" | head -c 400 | tr '\n' ' ' | sed 's/  */ /g' || true)
fi
echo "BLUF: ${BLUF:0:120}..." | tee -a "$LOG"

# ---------- Extract pages as images ----------
echo "--- Extracting page images ---" | tee -a "$LOG"
# Extract only first 5 pages (enough for slideshows, avoids timeout on large PDFs)
pdftoppm -png -r 150 -l 5 "$PDF_PATH" "$TMPDIR/brief-page" 2>&1 | tee -a "$LOG"

# Count pages
PAGE_COUNT=$(ls "$TMPDIR"/brief-page-*.png 2>/dev/null | wc -l)
if [ "$PAGE_COUNT" -eq 0 ]; then
    echo "ERROR: No pages extracted" | tee -a "$LOG"
    exit 1
fi
echo "Extracted $PAGE_COUNT pages" | tee -a "$LOG"

# ---------- Upload to GenViral CDN ----------
echo "--- Uploading pages to GenViral CDN ---" | tee -a "$LOG"
ALL_URLS=()
# Sort pages numerically
mapfile -t PAGE_FILES < <(ls "$TMPDIR"/brief-page-*.png 2>/dev/null | sort -t- -k3 -n || true)
for f in "${PAGE_FILES[@]}"; do
    URL=$(GENVIRAL_API_KEY="$GENVIRAL_API_KEY" bash "$GENVIRAL_SCRIPT" upload --file "$f" --content-type image/png 2>&1 | grep -oP 'https://cdn\.vireel\.io[^[:space:]]+' | head -1)
    if [ -n "$URL" ]; then
        ALL_URLS+=("$URL")
        echo "  Uploaded: $(basename $f)" | tee -a "$LOG"
    else
        echo "  WARN: Upload failed for $(basename $f)" | tee -a "$LOG"
    fi
done

if [ ${#ALL_URLS[@]} -eq 0 ]; then
    echo "ERROR: No images uploaded" | tee -a "$LOG"
    exit 1
fi

# Build comma-separated URL strings (up to 3 for LinkedIn, 2 for X, 3 for TikTok)
LI_URLS=$(IFS=,; echo "${ALL_URLS[*]:0:3}")
X_URLS=$(IFS=,; echo "${ALL_URLS[*]:0:2}")
TT_URLS=$(IFS=,; echo "${ALL_URLS[*]:0:3}")

# ---------- Account IDs ----------
LI_ACCOUNT="d3adbc5a-04fe-4dc1-93ab-b920f14ec968"
X_ACCOUNT="95f9ef18-1454-41aa-be98-0716c87791ca"
TT_ACCOUNT="b03637b7-7043-4412-a408-6aac3da0ac25"

# Build LinkedIn caption (max 500 chars)
LI_CAPTION="Global Security & Intelligence Brief — ${DATE_PT}

BLUF: ${BLUF:0:250}...

Key developments across multiple theaters. Full assessment available to subscribers.

#OSINT #Intelligence #GlobalSecurity"
LI_CAPTION=$(echo "$LI_CAPTION" | head -c 490)

# Build X/Twitter caption (max 280 chars)
X_CAPTION="Global Security Brief — ${DATE_PT}

${BLUF:0:180}...

Full assessment available.

#OSINT #GlobalSecurity"
X_CAPTION=$(echo "$X_CAPTION" | head -c 270)

# Build TikTok caption (max 500 chars)
TT_CAPTION="Global Security & Intelligence Brief — ${DATE_PT}

${BLUF:0:200}...

#OSINT #GlobalSecurity"
TT_CAPTION=$(echo "$TT_CAPTION" | head -c 490)

# ---------- Post to LinkedIn ----------
echo "--- Posting to LinkedIn ---" | tee -a "$LOG"
POST_ID_LI=$(GENVIRAL_API_KEY="$GENVIRAL_API_KEY" bash "$GENVIRAL_SCRIPT" create-post \
    --caption "$LI_CAPTION" \
    --media-type slideshow \
    --media-urls "$LI_URLS" \
    --accounts "$LI_ACCOUNT" 2>&1 | grep -oP '"id": "[^"]+"' | head -1 | cut -d'"' -f4)
echo "  LinkedIn post ID: $POST_ID_LI" | tee -a "$LOG"

# ---------- Post to X/Twitter ----------
echo "--- Posting to X/Twitter ---" | tee -a "$LOG"
POST_ID_X=$(GENVIRAL_API_KEY="$GENVIRAL_API_KEY" bash "$GENVIRAL_SCRIPT" create-post \
    --caption "$X_CAPTION" \
    --media-type slideshow \
    --media-urls "$X_URLS" \
    --accounts "$X_ACCOUNT" 2>&1 | grep -oP '"id": "[^"]+"' | head -1 | cut -d'"' -f4)
echo "  X/Twitter post ID: $POST_ID_X" | tee -a "$LOG"

# ---------- Post to TikTok (draft mode) ----------
echo "--- Posting to TikTok (draft) ---" | tee -a "$LOG"
POST_ID_TT=$(GENVIRAL_API_KEY="$GENVIRAL_API_KEY" bash "$GENVIRAL_SCRIPT" create-post \
    --caption "$TT_CAPTION" \
    --media-type slideshow \
    --media-urls "$TT_URLS" \
    --accounts "$TT_ACCOUNT" \
    --tiktok-post-mode MEDIA_UPLOAD \
    --tiktok-privacy SELF_ONLY 2>&1 | grep -oP '"id": "[^"]+"' | head -1 | cut -d'"' -f4)
echo "  TikTok draft ID: $POST_ID_TT" | tee -a "$LOG"

# ---------- Log to Performance ----------
echo "--- Updating performance log ---" | tee -a "$LOG"
python3 << PYEOF
import json, os

log_path = "$GENVIRAL_LOG"
date_pt = "$DATE_PT"
pdf_path = "$PDF_PATH"

log_data = {'posts': []}
if os.path.exists(log_path):
    try:
        with open(log_path) as f:
            log_data = json.load(f)
    except:
        pass

if 'posts' not in log_data:
    log_data['posts'] = []

new_entries = []

if "$POST_ID_LI":
    new_entries.append({
        'id': "$POST_ID_LI", 'date': date_pt,
        'hook': 'Daily Intel Brief — LinkedIn',
        'hook_type': 'educational',
        'account_id': "$LI_ACCOUNT", 'platform': 'linkedin',
        'media_type': 'slideshow', 'media_source': pdf_path,
        'metrics': {'views': 0, 'likes': 0, 'comments': 0, 'shares': 0}
    })

if "$POST_ID_X":
    new_entries.append({
        'id': "$POST_ID_X", 'date': date_pt,
        'hook': 'Daily Intel Brief — X/Twitter',
        'hook_type': 'educational',
        'account_id': "$X_ACCOUNT", 'platform': 'twitter',
        'media_type': 'slideshow', 'media_source': pdf_path,
        'metrics': {'views': 0, 'likes': 0, 'comments': 0, 'shares': 0}
    })

if "$POST_ID_TT":
    new_entries.append({
        'id': "$POST_ID_TT", 'date': date_pt,
        'hook': 'Daily Intel Brief — TikTok draft',
        'hook_type': 'educational',
        'account_id': "$TT_ACCOUNT", 'platform': 'tiktok',
        'media_type': 'slideshow', 'media_source': pdf_path,
        'notes': 'Draft mode — needs trending sound before publishing',
        'metrics': {'views': 0, 'likes': 0, 'comments': 0, 'shares': 0}
    })

log_data['posts'].extend(new_entries)

tmp_path = log_path + '.tmp'
with open(tmp_path, 'w') as f:
    json.dump(log_data, f, indent=2)
os.replace(tmp_path, log_path)
print(f'Performance log updated ({len(new_entries)} entries)')
PYEOF

# ---------- Cleanup ----------
echo "--- Cleanup ---" | tee -a "$LOG"
rm -rf "$TMPDIR"

echo "=== GenViral Post Brief — ${DATE_UTC} — Complete ===" | tee -a "$LOG"
echo "LinkedIn: $POST_ID_LI" | tee -a "$LOG"
echo "X/Twitter: $POST_ID_X" | tee -a "$LOG"
echo "TikTok (draft): $POST_ID_TT" | tee -a "$LOG"
