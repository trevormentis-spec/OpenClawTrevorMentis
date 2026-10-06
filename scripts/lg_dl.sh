#!/usr/bin/env bash
# Slow-but-stubborn libgen downloader with resume. Usage: lg_dl.sh <slug> <md5>
set -u
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0"
BASE="https://libgen.vg"
slug="$1"; md5="$2"
dir="/home/ubuntu/.openclaw/workspace/tmp/copyright-monitor/$slug"
mkdir -p "$dir"
out="$dir/$md5"
jar="/tmp/lg_$md5.jar"; rm -f "$jar"
[ -s "$out" ] && { echo "have $slug"; exit 0; }
for attempt in 1 2 3 4 5; do
  curl -s -m 20 -c "$jar" -A "$UA" "$BASE/" -o /dev/null
  KEY=$(curl -s -m 25 -b "$jar" -c "$jar" -A "$UA" -e "$BASE/" "$BASE/ads.php?md5=$md5" | grep -oE "get.php\?md5=$md5&key=[A-Za-z0-9]+" | head -1)
  if [ -z "$KEY" ]; then echo "$slug attempt $attempt: no key"; sleep 5; continue; fi
  curl -sL -C - --retry 30 --retry-delay 4 --max-time 1200 -b "$jar" -A "$UA" -e "$BASE/ads.php?md5=$md5" "$BASE/$KEY" -o "$out"
  ft=$(file -b "$out" 2>/dev/null)
  echo "$slug attempt $attempt -> $(stat -c%s "$out" 2>/dev/null) bytes : $ft"
  case "$ft" in
    PDF*|EPUB*|Zip*|*EPUB*) echo "OK $slug"; exit 0;;
  esac
  sleep 4
done
echo "FAIL $slug"
exit 1
