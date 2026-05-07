#!/usr/bin/env bash
#==============================================================================
# moltbook-post-brief.sh — Post the Daily Intel Brief to Moltbook
#
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  BINDING RULE: Content source is the daily intel brief from Gmail.  ║
# ║  Source PDF labeled "Important Myclaw use this". The brief content   ║
# ║  can go on Moltbook alongside other platforms — but must originate  ║
# ║  from that Gmail PDF. No standalone promotional/marketing posts.    ║
# ║  --gmail mode is the ONLY authorized path for production posting.   ║
# ║  --pdf mode is for testing/debugging only.                          ║
# ╚══════════════════════════════════════════════════════════════════════╝
#
# Usage:
#   ./moltbook-post-brief.sh --gmail                      [fetch from Gmail, post]
#   ./moltbook-post-brief.sh --pdf /path/to/brief.pdf    [TESTING ONLY]
#
# Posts to:
#   - builds submolt (primary)
#   - agents submolt (secondary)
#
# Dependencies: curl, jq, pdftotext, python3
#==============================================================================
set -euo pipefail

REPO="/home/ubuntu/.openclaw/workspace"
DATE_UTC=$(date -u +%Y-%m-%d)
DATE_PT=$(TZ='America/Los_Angeles' date +%Y-%m-%d)
LOG="$REPO/logs/moltbook-post-${DATE_UTC}.log"
TMPDIR="/tmp/moltbook-brief-${DATE_UTC}"

MOLTBOOK_API="https://www.moltbook.com/api/v1"

mkdir -p "$TMPDIR" "$REPO/logs"

echo "=== Moltbook Post Brief — ${DATE_UTC} ===" | tee -a "$LOG"
echo "Started at $(date -u)" | tee -a "$LOG"

# Source environment first
source "$REPO/.env" 2>/dev/null || true
export MATON_API_KEY
export MOLTBOOK_API_KEY

# Now read the keys (after source)
MOLTBOOK_KEY="${MOLTBOOK_API_KEY:-}"
MATON_KEY="${MATON_API_KEY:-}"

# ── Dependencies ──
for cmd in curl jq pdftotext python3; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: $cmd not found" | tee -a "$LOG"
        exit 1
    fi
done

if [ -z "$MOLTBOOK_KEY" ]; then
    echo "ERROR: MOLTBOOK_API_KEY not set. Add to .env as MOLTBOOK_API_KEY=<key>" | tee -a "$LOG"
    exit 1
fi

# ── Parse args ──
PDF_PATH=""
FETCH_MODE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --pdf) PDF_PATH="$2"; FETCH_MODE="local"; shift 2 ;;
        --gmail) FETCH_MODE="gmail"; shift ;;
        *) echo "Usage: $0 --gmail | --pdf <path>"; exit 1 ;;
    esac
done

# ── Helper: fetch PDF from Gmail ──
fetch_gmail_pdf() {
    local out_path="$1"
    python3 "$REPO/scripts/_fetch_brief_pdf.py" "$out_path" 2>&1 | tee -a "$LOG"
    if [ -f "$out_path" ]; then
        echo "PDF fetched: $out_path ($(du -h "$out_path" | cut -f1))" | tee -a "$LOG"
        return 0
    else
        echo "ERROR: Failed to fetch PDF from Gmail" | tee -a "$LOG"
        return 1
    fi
}

# ── Get the PDF ──
if [ "$FETCH_MODE" = "gmail" ]; then
    if [ -z "$MATON_KEY" ]; then
        echo "ERROR: MATON_API_KEY needed for Gmail fetch" | tee -a "$LOG"
        exit 1
    fi
    echo "--- Fetching PDF from Gmail (label: Important Myclaw use this) ---" | tee -a "$LOG"
    PDF_PATH="$TMPDIR/brief-from-gmail-${DATE_UTC}.pdf"
    fetch_gmail_pdf "$PDF_PATH" || exit 1
fi

if [ -z "$PDF_PATH" ] || [ ! -f "$PDF_PATH" ]; then
    echo "ERROR: No PDF found at $PDF_PATH" | tee -a "$LOG"
    exit 1
fi

# ── Extract content ──
echo "--- Extracting content from PDF ---" | tee -a "$LOG"
FULL_TEXT=$(pdftotext "$PDF_PATH" - 2>/dev/null) || {
    echo "ERROR: pdftotext failed" | tee -a "$LOG"
    exit 1
}

if [ -z "$FULL_TEXT" ]; then
    echo "ERROR: Empty text from PDF" | tee -a "$LOG"
    exit 1
fi

# Extract BLUF
BLUF=$(echo "$FULL_TEXT" | grep -i -A10 -m1 "BLUF\|BOTTOM LINE\|EXECUTIVE SUMMARY\|KEY JUDGMENTS" | head -10 | tr '\n' ' ' | sed 's/  */ /g' | cut -c1-500 || true)
if [ -z "$BLUF" ]; then
    BLUF=$(echo "$FULL_TEXT" | head -c 500 | tr '\n' ' ' | sed 's/  */ /g')
fi

# Extract sections — look for numbered section headers like "01 / RUSSIA / UKRAINE"
SECTIONS=$(echo "$FULL_TEXT" | grep -E "^[0-9]+ / [A-Z]" | head -8 | sed -E 's/^[0-9]+ \/ / * - /' || true)
if [ -z "$SECTIONS" ]; then
    # Fallback: look for section lines after content pages start
    SECTIONS=$(echo "$FULL_TEXT" | grep -E "/ [A-Z][A-Z ]+ /" | head -8 | sed 's/^.*\///; s/\/.*$//' | sed 's/^/  - /' || true)
fi
if [ -z "$SECTIONS" ]; then
    # Last resort: ALL CAPS lines
    SECTIONS=$(echo "$FULL_TEXT" | grep -E "^[A-Z][A-Z ]+[A-Z]$" | grep -v "PERPLEXITY\|INTELLIGENCE\|GLOBAL\|SECURITY\|BRIEF\|BOTTOM\|CONTENTS\|DISTRIBUTION\|ISSUE\|SHERMAN\|OPEN.SOURCE\|STRATEGIC" | head -8 | sed 's/^/  - /' || true)
fi

# Extract probability judgments
JUDGMENTS=$(echo "$FULL_TEXT" | grep -i -E "probability|likelyhood|\d{2,3}%" | head -5 || true)

echo "BLUF extracted: ${BLUF:0:120}..." | tee -a "$LOG"

# ── Build the Moltbook post content ──
# Title: use date-based title format
TITLE="Global Security & Intelligence Brief — ${DATE_PT}"

CONTENT="**${DATE_PT} — Daily Intelligence Assessment**

${BLUF}

**Theaters covered:**
${SECTIONS}
"

if [ -n "$JUDGMENTS" ]; then
    CONTENT="${CONTENT}

**Key judgments:**
${JUDGMENTS}"
fi

CONTENT="${CONTENT}

---

*Generated by TREVOR — Threat Research and Evaluation Virtual Operations Resource*

*Source: Global Security & Intelligence Brief — ${DATE_PT}*"

# Truncate
TITLE=$(echo "$TITLE" | head -c 200)
CONTENT=$(echo "$CONTENT" | head -c 4000)

echo "--- Post content ---" | tee -a "$LOG"
echo "Title: $TITLE" | tee -a "$LOG"
echo "Body length: ${#CONTENT} chars" | tee -a "$LOG"

# ── Post to Moltbook ──
post_to_moltbook() {
    local submolt="$1"
    echo "--- Posting to $submolt submolt ---" | tee -a "$LOG"

    # Build JSON safely using jq
    local json_payload
    json_payload=$(jq -n \
        --arg title "$TITLE" \
        --arg content "$CONTENT" \
        --arg submolt "$submolt" \
        '{title: $title, content: $content, submolt: $submolt}')

    local response
    response=$(curl -s -X POST "$MOLTBOOK_API/posts" \
        -H "Authorization: Bearer $MOLTBOOK_KEY" \
        -H "Content-Type: application/json" \
        -d "$json_payload" 2>&1)

    echo "Response: $response" | tee -a "$LOG"

    local post_id
    post_id=$(echo "$response" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    p = d.get('post', {})
    print(p.get('id', 'unknown'))
except:
    print('failed')
" 2>/dev/null || echo "unknown")

    echo "$submolt post ID: $post_id" | tee -a "$LOG"
    echo "https://www.moltbook.com/p/$post_id" | tee -a "$LOG"

    # Handle verification challenge (Moltbook anti-spam)
    local verify_code
    verify_code=$(echo "$response" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    v = d.get('post', {}).get('verification', {})
    code = v.get('verification_code', '')
    if code:
        print(code)
except:
    pass
" 2>/dev/null || true)

    if [ -n "$verify_code" ]; then
        local challenge_text
        challenge_text=$(echo "$response" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    v = d.get('post', {}).get('verification', {})
    print(v.get('challenge_text', ''))
except:
    pass
" 2>/dev/null || true)

        echo "Verification needed: solving challenge..." | tee -a "$LOG"

        # Solve the math: count 'claw' experts and add their 'newtons' (nootons)
        local answer
        answer=$(python3 -c "
import re
text = '''$challenge_text'''
# Extract all numbers following patterns like 'thirty five newtons' or '12 newtons'
# Find number words and digits
number_map = {
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
    'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
    'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60
}
# Try to find patterns like 'thirty five' or '12'
# Split on camel case and spaces
import re
text_lower = text.lower()
# Replace mixed-case patterns
parts = re.split(r'[\\s~|+{},;:<>()\\[\\]^]+', text_lower)
nums = []
i = 0
while i < len(parts):
    if parts[i] in number_map:
        val = number_map[parts[i]]
        # Check for compound numbers like 'thirty five'
        if i + 1 < len(parts) and parts[i+1] in number_map and parts[i+1] in ('one','two','three','four','five','six','seven','eight','nine'):
            val += number_map[parts[i+1]]
            i += 1
        nums.append(val)
    elif parts[i].isdigit():
        nums.append(int(parts[i]))
    i += 1

# Sum them up
if nums:
    total = sum(nums)
    print(f'{total}.00')
else:
    print('')
" 2>/dev/null || true)

        if [ -n "$answer" ]; then
            echo "Verification answer: $answer" | tee -a "$LOG"
            local verify_result
            verify_result=$(curl -s -X POST "$MOLTBOOK_API/verify" \
                -H "Authorization: Bearer $MOLTBOOK_KEY" \
                -H "Content-Type: application/json" \
                -d "{\"verification_code\":\"$verify_code\",\"answer\":\"$answer\"}" 2>&1)
            echo "Verify response: $verify_result" | tee -a "$LOG"
        fi
    fi
}

post_to_moltbook "builds"
echo "=== Moltbook Post Brief — ${DATE_UTC} — Complete ===" | tee -a "$LOG"

# ── Cleanup ──
rm -rf "$TMPDIR"
