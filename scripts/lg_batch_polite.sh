#!/usr/bin/env bash
# Polite, resumable libgen batch downloader.
# Usage: lg_batch_polite.sh <listfile> [min_delay=12] [max_delay=25]
#   listfile: lines of "<slug> <md5>"
# Optional: HTTPS_PROXY (or https_proxy) env routes traffic via proxy -> different egress IP.
# Design goal: never trip the per-IP burst throttle. One warm session per file,
# spaced requests, capped retries, exponential backoff, mirror failover, resume.
set -u
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
MIRRORS=("https://libgen.vg" "https://libgen.gl" "https://libgen.bz" "https://libgen.la" "https://libgen.li")
ROOT="${CM_ROOT:-/home/ubuntu/.openclaw/workspace/tmp/copyright-monitor}"
LIST="${1:?listfile required}"; MIND="${2:-12}"; MAXD="${3:-25}"
PROXY="${HTTPS_PROXY:-${https_proxy:-}}"
PCURL=(); [ -n "$PROXY" ] && PCURL=(-x "$PROXY")

log(){ echo "[$(date -u +%H:%M:%S)] $*"; }
backoff(){ local n="${1:-2}"; local s=$(( (1<<n) + RANDOM%6 )); [ "$s" -gt 240 ] && s=240; echo "$s"; }

dl_one(){
  local slug="$1" md5="$2" dir="$ROOT/$1" out jar base key a
  dir="$ROOT/$slug"; mkdir -p "$dir"; out="$dir/$md5"
  # Skip only *complete* files; a partial is resumed below with curl -C -.
  if [ -s "$out" ]; then
    case "$(file -b "$out" 2>/dev/null)" in
      PDF*|EPUB*|Zip*|*EPUB*|Composite*|CDF*|Microsoft*) log "have $slug"; return 0;;
      *) log "$slug: partial present, will resume";;
    esac
  fi
  jar="$(mktemp)"; trap 'rm -f "$jar"' RETURN
  for base in "${MIRRORS[@]}"; do
    # Warm session (homepage first) — required for a usable download token.
    curl -s -m 20 "${PCURL[@]}" -c "$jar" -A "$UA" "$base/" -o /dev/null || continue
    key="$(curl -s -m 25 "${PCURL[@]}" -b "$jar" -c "$jar" -A "$UA" -e "$base/" \
           "$base/ads.php?md5=$md5" | grep -oE "get\.php\?md5=$md5&key=[A-Za-z0-9]+" | head -1)"
    if [ -z "$key" ]; then
      log "$slug @ $base: no key (throttled) — backing off"; sleep "$(backoff 2)"; continue
    fi
    for a in 1 2 3; do
      curl -sL "${PCURL[@]}" -C - --retry 3 --retry-delay 10 --retry-max-time 1800 --max-time 1800 \
        -b "$jar" -A "$UA" -e "$base/ads.php?md5=$md5" "$base/$key" -o "$out"
      case "$(file -b "$out" 2>/dev/null)" in
        PDF*|EPUB*|Zip*|*EPUB*|Composite*|CDF*|Microsoft*) log "OK $slug ($(stat -c%s "$out") B via $base)"; return 0;;
      esac
      log "$slug @ $base attempt $a: partial/blocked ($(stat -c%s "$out" 2>/dev/null) B) — backoff"
      sleep "$(backoff "$a")"
    done
  done
  log "FAIL $slug"; return 1
}

while read -r slug md5; do
  [ -z "${slug:-}" ] && continue
  dl_one "$slug" "$md5"
  d=$(( MIND + RANDOM % (MAXD - MIND + 1) ))
  log "spacing ${d}s"; sleep "$d"
done < "$LIST"
