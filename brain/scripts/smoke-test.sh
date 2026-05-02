#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

echo "== compile =="
python3 -m py_compile brain/scripts/brain.py

echo
 echo "== reindex =="
python3 brain/scripts/brain.py reindex

echo
 echo "== doctor =="
python3 brain/scripts/brain.py doctor

echo
 echo "== recall probes =="
queries=(
  "Trevor routing memory"
  "durable decisions"
  "DeepSeek fallback chain"
  "AgentMail email path"
  "analyst training program"
)

for q in "${queries[@]}"; do
  echo
  echo "-- $q --"
  python3 brain/scripts/brain.py recall "$q" --top-k 3
 done
