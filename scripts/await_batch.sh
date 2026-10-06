#!/usr/bin/env bash
# Wait for the next book(s) to finish downloading; emit MEDIA lines; exit.
# Bounded run. Prints nothing until a book is ready (then exits 0) or the queue drains.
cd /home/ubuntu/.openclaw/workspace || exit 1
for i in $(seq 1 180); do
  out="$(python3 scripts/outbox.py 2>/dev/null)"
  if [ -n "$out" ]; then echo "$out"; exit 0; fi
  if ! pgrep -f lg_batch_polite2 >/dev/null; then
    out="$(python3 scripts/outbox.py 2>/dev/null)"
    echo "${out:-#QUEUE_DONE}"
    exit 0
  fi
  sleep 20
done
echo "#TIMEOUT"
