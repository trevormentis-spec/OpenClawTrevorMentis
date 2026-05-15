#!/usr/bin/env bash
#==============================================================================
# genviral-post-brief.sh — Post the Daily Intel Brief via GenViral Studio AI
#
# ╔══════════════════════════════════════════════════════════════════════╗
# ║  Uses the orchestrator's structured analysis to generate original    ║
# ║  per-platform visuals via GenViral Studio AI. No PDF screenshots.   ║
# ╚══════════════════════════════════════════════════════════════════════╝
#
# Source detection (in priority order):
#   1. ~/trevor-briefings/{DATE}/analysis/exec_summary.json (orchestrator output)
#   2. ~/trevor-briefings/{DATE}/final/brief-{DATE}.pdf (orchestrator PDF)
#   3. tasks/news_analysis.md (workspace analysis file)
#   4. exports/pdfs/latest PDF (fallback)
#
# Pipeline per platform:
#   Read BLUF + judgments → craft platform-native prompts → GenViral Studio AI
#   slideshow → render → create-post → log
#
# Usage: ./genviral-post-brief.sh
# Environment: GENVIRAL_API_KEY required
#==============================================================================
set -euo pipefail

REPO="/home/ubuntu/.openclaw/workspace"
GENVIRAL_SCRIPT="$REPO/skills/genviral/scripts/genviral.sh"
DATE_UTC=$(date -u +%Y-%m-%d)
DATE_PT=$(TZ='America/Los_Angeles' date +%Y-%m-%d)
LOG="$REPO/logs/genviral-post-${DATE_UTC}.log"
GENVIRAL_LOG="$REPO/skills/genviral/workspace/performance/log.json"
TMPDIR="/tmp/genviral-brief-${DATE_UTC}"
CONTEXT_DIR="$REPO/skills/genviral/workspace/context"

# Account IDs
LI_ACCOUNT="d3adbc5a-04fe-4dc1-93ab-b920f14ec968"
X_ACCOUNT="95f9ef18-1454-41aa-be98-0716c87791ca"
TT_ACCOUNT="b03637b7-7043-4412-a408-6aac3da0ac25"

# Image packs
PACK_EARTH="ccd880e9-53b0-4d79-9810-4e867e30a805"
PACK_FINANCE="9684c67e-cde6-45a7-a5ec-d9f61830cdc7"
PACK_RETRO="72772438-d1fc-497a-bd89-2b4d0f0ca2b5"

mkdir -p "$TMPDIR" "$REPO/logs"
exec > >(tee -a "$LOG") 2>&1

echo "=== GenViral Post Brief — ${DATE_UTC} ==="
echo "Started at $(date -u)"

for cmd in python3 jq curl; do
    command -v "$cmd" >/dev/null 2>&1 || { echo "ERROR: $cmd not found"; exit 1; }
done

# ---------- Confirm GenViral API ----------
if ! GENV_CHECK=$(bash "$GENVIRAL_SCRIPT" accounts --json 2>&1); then
    echo "ERROR: Cannot reach GenViral API"
    exit 1
fi
echo "GenViral API: OK"

# ---------- Source detection ----------
BRIEF_DIR="$HOME/trevor-briefings/${DATE_UTC}"
BRIEF_TEXT=""
BRIEF_TAG="unknown"
BRIEF_DIR_ARG=""

# Priority 1: orchestrator exec_summary.json
if [ -f "$BRIEF_DIR/analysis/exec_summary.json" ]; then
    BRIEF_TEXT=$(cat "$BRIEF_DIR/analysis/exec_summary.json")
    BRIEF_TAG="orchestrator-json"
    BRIEF_DIR_ARG="$BRIEF_DIR"
    echo "Source: $BRIEF_DIR/analysis/exec_summary.json (orchestrator)"
fi

# Priority 2: orchestrator final PDF
if [ -z "$BRIEF_TEXT" ] && [ -f "$BRIEF_DIR/final/brief-${DATE_UTC}.pdf" ]; then
    BRIEF_TEXT=$(pdftotext "$BRIEF_DIR/final/brief-${DATE_UTC}.pdf" - 2>/dev/null) || true
    BRIEF_TAG="orchestrator-pdf"
    echo "Source: $BRIEF_DIR/final/brief-${DATE_UTC}.pdf (orchestrator PDF)"
fi

# Priority 3: workspace analysis file
if [ -z "$BRIEF_TEXT" ] && [ -f "$REPO/tasks/news_analysis.md" ]; then
    BRIEF_TEXT=$(cat "$REPO/tasks/news_analysis.md")
    BRIEF_TAG="workspace-analysis"
    echo "Source: $REPO/tasks/news_analysis.md (workspace)"
fi

# Priority 4: latest exports PDF
if [ -z "$BRIEF_TEXT" ]; then
    LATEST_PDF=$(ls -t "$REPO/exports/pdfs"/*.pdf 2>/dev/null | head -1)
    if [ -n "$LATEST_PDF" ]; then
        BRIEF_TEXT=$(pdftotext "$LATEST_PDF" - 2>/dev/null) || true
        BRIEF_TAG="exports-pdf"
        echo "Source: $LATEST_PDF (exports PDF)"
    fi
fi

if [ -z "$BRIEF_TEXT" ]; then
    echo "ERROR: No brief source found anywhere"
    exit 1
fi

# Save extracted text to temp file for Python processing (avoids shell escaping issues)
echo "$BRIEF_TEXT" > "$TMPDIR/brief-source.txt"
BRIEF_LEN=$(wc -c < "$TMPDIR/brief-source.txt")
echo "Source size: $BRIEF_LEN bytes"

# ---------- Extract structured content with Python (reads from temp file) ----------
echo "--- Extracting structured content ---"
python3 "$REPO/scripts/_genviral_extract.py" "$TMPDIR/brief-source.txt" "$TMPDIR/structured.json" ${BRIEF_DIR_ARG:+--brief-dir "$BRIEF_DIR_ARG"} 2>&1 || {
    echo "ERROR: Content extraction failed"
    cat "$TMPDIR/structured.json" 2>/dev/null || true
    exit 1
}

BLUF=$(python3 -c "import json; print(json.load(open('$TMPDIR/structured.json'))['bluf'])" 2>/dev/null || echo "Intelligence briefing.")
SECTIONS_LIST=$(python3 -c "import json; d=json.load(open('$TMPDIR/structured.json')); sections=d['sections']; print('\n'.join(sections[:6]))" 2>/dev/null || echo "Geopolitical analysis")
JUDGMENTS_LIST=$(python3 -c "import json; d=json.load(open('$TMPDIR/structured.json')); judgments=d['judgments']; print('\n'.join(judgments[:4]))" 2>/dev/null || echo "")
TOP_JUDGMENT=$(echo "$JUDGMENTS_LIST" | head -1)

echo "BLUF: ${BLUF:0:120}..."
echo "Sections extracted: $(python3 -c "import json; print(len(json.load(open('$TMPDIR/structured.json'))['sections']))" 2>/dev/null || echo 0)"
echo "Judgments extracted: $(python3 -c "import json; print(len(json.load(open('$TMPDIR/structured.json'))['judgments']))" 2>/dev/null || echo 0)"

# Write prompts to temp files to avoid shell escaping issues
python3 -c "
import json, os

bluf = json.load(open('$TMPDIR/structured.json'))['bluf']
sections = json.load(open('$TMPDIR/structured.json'))['sections']
judgments = json.load(open('$TMPDIR/structured.json'))['judgments']
date_pt = '$DATE_PT'

# LinkedIn prompt — 4:5, professional, 3 slides
li_prompt = f'''Global Security & Intelligence Brief — {date_pt}.

BLUF: {bluf[:300]}

Key developments: {' • '.join(sections[:4])}

Format: professional intelligence briefing slides. First slide: title card with date and 'GLOBAL SECURITY & INTELLIGENCE BRIEF'. Second slide: BLUF text. Third slide: key developments as bullet list with call to action for full assessment. Clean, authoritative design.'''
with open('$TMPDIR/prompt_linkedin.txt', 'w') as f:
    f.write(li_prompt.strip())

# X/Twitter prompt — 16:9, concise, 2 slides
top_j = judgments[0] if judgments else 'Intelligence assessment available.'
x_prompt = f'''Intelligence Briefing — {date_pt}.

Headline: {bluf[:200]}

Key data point: {top_j[:200]}

Format: clean, striking slides for Twitter/X. First slide: bold headline with date and brief description. Second slide: key takeaway with 'Full assessment at link in bio' callout. Minimal text, high-impact design.'''
with open('$TMPDIR/prompt_x.txt', 'w') as f:
    f.write(x_prompt.strip())

# TikTok prompt — 9:16, vertical, 3 slides
tt_prompt = f'''Global Security Brief — {date_pt}.

Hook: {bluf[:150]}

Key judgment: {top_j[:200]}

Format: vertical 9:16 TikTok slideshow. First slide: hook/attention slide with provocative headline. Second slide: key insight with data point. Third slide: call to action. Bold, readable text, modern design.'''
with open('$TMPDIR/prompt_tiktok.txt', 'w') as f:
    f.write(tt_prompt.strip())
"

# ---------- Post function ----------
post_to_platform() {
    local platform_name="$1"
    local prompt_file="$2"
    local pack_id="$3"
    local aspect_ratio="$4"
    local num_slides="$5"
    local account_id="$6"
    local caption="$7"
    local tiktok_mode="$8"
    
    echo "=== ${platform_name} ==="
    echo "  Generating slideshow..."
    
    SLIDESHOW_OUT=$(bash "$GENVIRAL_SCRIPT" generate \
        --prompt "$(cat "$prompt_file")" \
        --pack-id "$pack_id" \
        --slides "$num_slides" \
        --type educational \
        --aspect-ratio "$aspect_ratio" \
        --language en 2>&1) || {
        local gen_status=$?
        echo "  WARN: Slideshow generation failed for ${platform_name} (exit code ${gen_status})"
        echo "  Error: $(echo "$SLIDESHOW_OUT" | grep -v '^Info:' | tail -3)"
        return 1
    }
    
    # Extract the JSON portion (genviral.sh prefixes info lines before the JSON)
    JSON_PART=$(echo "$SLIDESHOW_OUT" | sed -n '/^{/,\$p')
    SLIDE_ID=$(echo "$JSON_PART" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('id', ''))
except Exception as e:
    sys.stderr.write(f'JSON parse error: {e}')
    print('')
" 2>/dev/null || echo "")
    
    if [ -z "$SLIDE_ID" ]; then
        # Fallback: grep the ID from the 'OK:' line
        SLIDE_ID=$(echo "$SLIDESHOW_OUT" | grep -oP 'Slideshow generated: \K[a-f0-9-]+' || echo "")
    fi
    
    if [ -z "$SLIDE_ID" ]; then
        echo "  WARN: Unable to parse slideshow ID for ${platform_name}"
        echo "  GenViral output: $(echo "$SLIDESHOW_OUT" | tr '\n' ' ' | head -c 400)"
        return 1
    fi
    
    echo "  Slideshow ID: $SLIDE_ID"
    echo "  Rendering..."
    
    bash "$GENVIRAL_SCRIPT" render --id "$SLIDE_ID" 2>&1 | tail -1 || true
    sleep 5
    
    # Get rendered image URLs
    IMAGE_URLS=$(bash "$GENVIRAL_SCRIPT" review --id "$SLIDE_ID" --json 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    urls = [s.get('image_url', '') for s in d.get('slides', []) if s.get('image_url', '')]
    print(','.join(urls))
except:
    print('')
" 2>/dev/null || echo "")
    
    if [ -z "$IMAGE_URLS" ]; then
        echo "  WARN: No rendered images for ${platform_name}"
        return 1
    fi
    
    echo "  Posting..."
    POST_CMD="bash \"$GENVIRAL_SCRIPT\" create-post \
        --caption \"$caption\" \
        --media-type slideshow \
        --media-urls \"$IMAGE_URLS\" \
        --accounts \"$account_id\""
    
    if [ -n "$tiktok_mode" ]; then
        POST_CMD="$POST_CMD --tiktok-post-mode MEDIA_UPLOAD --tiktok-privacy SELF_ONLY"
    fi
    
    POST_OUT=$(eval "$POST_CMD" 2>&1) || {
        echo "  WARN: Post failed for ${platform_name}"
        echo "  Error: $(echo "$POST_OUT" | tail -2)"
        return 1
    }
    
    POST_ID=$(echo "$POST_OUT" | grep -oP '"id": "[^"]+"' | head -1 | cut -d'"' -f4 || echo "")
    echo "  Post ID: $POST_ID"
    
    # Save post ID for performance logging
    local file_slug=$(printf '%s' "$platform_name" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z' '_')
    echo "$POST_ID" > "$TMPDIR/postid_${file_slug}"
    return 0
}

# ---------- Platform 1: LinkedIn ----------
LI_CAPTION=$(python3 -c "
bluf = '''$BLUF'''
sections = '''$SECTIONS_LIST'''
cap = f'Global Security & Intelligence Brief — $DATE_PT\n\n{bluf[:250]}\n\n{sections[:200]}\n\nFull calibrated assessment with source-graded intelligence. #GlobalSecurity #Intelligence #OSINT #Geopolitics'
print(cap[:490])
")

post_to_platform "LinkedIn" "$TMPDIR/prompt_linkedin.txt" "$PACK_EARTH" "4:5" 3 "$LI_ACCOUNT" "$LI_CAPTION" "" || true

# ---------- Platform 2: X/Twitter ----------
X_CAPTION=$(python3 -c "
bluf = '''$BLUF'''
cap = f'Global Security Brief — $DATE_PT\n\n{bluf[:180]}\n\nFull assessment available. #GlobalSecurity #OSINT'
print(cap[:270])
")

post_to_platform "X/Twitter" "$TMPDIR/prompt_x.txt" "$PACK_RETRO" "1:1" 2 "$X_ACCOUNT" "$X_CAPTION" "" || true

# ---------- Platform 3: TikTok (draft) ----------
TT_CAPTION=$(python3 -c "
bluf = '''$BLUF'''
cap = f'Global Security & Intelligence Brief — $DATE_PT\n\n{bluf[:200]}\n\n#OSINT #GlobalSecurity'
print(cap[:490])
")

post_to_platform "TikTok" "$TMPDIR/prompt_tiktok.txt" "$PACK_EARTH" "9:16" 3 "$TT_ACCOUNT" "$TT_CAPTION" "tiktok" || true

# ---------- Read post IDs ----------
LI_POST_ID=$(cat "$TMPDIR/postid_linkedin" 2>/dev/null || echo "")
X_POST_ID=$(cat "$TMPDIR/postid_x_twitter" 2>/dev/null || echo "")
TT_POST_ID=$(cat "$TMPDIR/postid_tiktok" 2>/dev/null || echo "")

# ---------- Log to Performance ----------
echo "--- Updating performance log ---"
python3 -c "
import json, os

log_path = '$GENVIRAL_LOG'
date_pt = '$DATE_PT'

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
for pid, plat, acc in [
    ('$LI_POST_ID', 'linkedin', 'd3adbc5a-04fe-4dc1-93ab-b920f14ec968'),
    ('$X_POST_ID', 'twitter', '95f9ef18-1454-41aa-be98-0716c87791ca'),
    ('$TT_POST_ID', 'tiktok', 'b03637b7-7043-4412-a408-6aac3da0ac25'),
]:
    if pid:
        entry = {
            'id': pid, 'date': date_pt,
            'hook': f'Daily Intel Brief — {plat}',
            'hook_type': 'educational',
            'account_id': acc,
            'platform': plat,
            'media_type': 'slideshow_ai',
            'media_source': 'genviral_studio_ai',
            'metrics': {'views': 0, 'likes': 0, 'comments': 0, 'shares': 0}
        }
        if plat == 'tiktok':
            entry['notes'] = 'Draft mode — needs trending sound before publishing'
        new_entries.append(entry)

log_data['posts'].extend(new_entries)
tmp = log_path + '.tmp'
with open(tmp, 'w') as f:
    json.dump(log_data, f, indent=2)
os.replace(tmp, log_path)
print(f'Performance log updated ({len(new_entries)} entries)')
"

# ---------- Cleanup ----------
rm -rf "$TMPDIR"

echo "=== GenViral Post Brief — ${DATE_UTC} — Complete ==="
echo "LinkedIn: ${LI_POST_ID:-FAILED}"
echo "X/Twitter: ${X_POST_ID:-FAILED}"
echo "TikTok: ${TT_POST_ID:-FAILED}"
