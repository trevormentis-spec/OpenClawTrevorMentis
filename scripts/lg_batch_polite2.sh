#!/usr/bin/env bash
# Polite, resumable libgen batch downloader (v2: strict completeness validation).
# Usage: lg_batch_polite2.sh <listfile> [min_delay=12] [max_delay=25]
#   listfile: lines of "<slug> <md5>"
# Optional: HTTPS_PROXY (or https_proxy) routes traffic via proxy -> different egress IP.
set -u
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
MIRRORS=("https://libgen.vg" "https://libgen.gl" "https://libgen.bz" "https://libgen.la" "https://libgen.li")
ROOT="${CM_ROOT:-/home/ubuntu/.openclaw/workspace/tmp/copyright-monitor}"
LIST="${1:?listfile required}"; MIND="${2:-12}"; MAXD="${3:-25}"
PROXY="${HTTPS_PROXY:-${https_proxy:-}}"
PCURL=(); [ -n "$PROXY" ] && PCURL=(-x "$PROXY")

log(){ echo "[$(date -u +%H:%M:%S)] $*"; }
backoff(){ local n="$1"; local s=$(( (1<<n) + RANDOM%6 )); [ "$s" -gt 240 ] && s=240; printf '%s' "$s"; }

# A file is complete only if the container parses AND has a proper trailer.
is_complete(){
  local f="$1" ft; [ -s "$f" ] || return 1
  ft="$(file -b "$f")"
  case "$ft" in
    PDF*|*PDF*)
      tail -c 8192 "$f" | grep -aq '%%EOF' && return 0
      pdfinfo "$f" >/dev/null 2>&1 && return 0
      return 1;;
  esac
  case "$ft" in
    *EPUB*|*Zip*|*ZIP*|*zip*)
      unzip -tq "$f" >/dev/null 2>&1 && return 0 || return 1;;
  esac
  return 1
}

dl_one(){
  local slug="$1" md5="$2" dir out jar base key a
  dir="$ROOT/$slug"; mkdir -p "$dir"; out="$dir/$md5"
  if is_complete "$out"; then log "have $slug"; return 0; fi
  [ -s "$out" ] && log "$slug: partial present, will resume"
  jar="$(mktemp)"
  for base in "${MIRRORS[@]}"; do
    curl -s -m 20 "${PCURL[@]}" -c "$jar" -A "$UA" "$base/" -o /dev/null || continue
    key="$(curl -s -m 25 "${PCURL[@]}" -b "$jar" -c "$jar" -A "$UA" -e "$base/" \
           "$base/ads.php?md5=$md5" | grep -oE "get\.php\?md5=$md5&key=[A-Za-z0-9]+" | head -1)"
    if [ -z "$key" ]; then
      log "$slug @ $base: no key (throttled) — backing off"; sleep "$(backoff 2)"; continue
    fi
    for a in 1 2 3; do
      curl -sL "${PCURL[@]}" -C - --retry 3 --retry-delay 10 --retry-max-time 1800 --max-time 1800 \
        -b "$jar" -A "$UA" -e "$base/ads.php?md5=$md5" "$base/$key" -o "$out"
      if is_complete "$out"; then log "OK $slug ($(stat -c%s "$out") B via $base)"; rm -f "$jar"; return 0; fi
      log "$slug @ $base attempt $a: incomplete ($(stat -c%s "$out" 2>/dev/null) B) — backoff"
      sleep "$(backoff "$a")"
    done
  done
  rm -f "$jar"; log "FAIL $slug"; return 1
}

while read -r slug md5; do
  [ -z "${slug:-}" ] && continue
  dl_one "$slug" "$md5"
  d=$(( MIND + RANDOM % (MAXD - MIND + 1) ))
  log "spacing ${d}s"; sleep "$d"
done < "$LIST"
