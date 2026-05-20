#!/usr/bin/env bash
# present-runner — runs Trevor Present scripts with correct PYTHONPATH
# Usage: present-runner <script.py> [args...]
# Example: present-runner qc_vision --file cover.png --spec "test"
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${REPO}${PYTHONPATH:+:$PYTHONPATH}"
exec python3 "$REPO/scripts/present/$@"