#!/usr/bin/env bash
# INSTALL.sh — one-shot installer for the daily-intel-brief skill.
#
# Run from the root of your OpenClawTrevorMentis clone. It copies this
# folder into skills/, stages it for git, and prints the commit + push
# commands. It does NOT push for you — that's a deliberate gate.
#
# Usage (after unzipping the bundle anywhere):
#
#     cd ~/path/to/OpenClawTrevorMentis     # the repo root
#     bash ~/Downloads/daily-intel-brief/INSTALL.sh
#
# Or, equivalently, drop the daily-intel-brief folder under skills/
# yourself and run `git add skills/daily-intel-brief && git commit ...`.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(pwd)"

if [ ! -f "$REPO_ROOT/ORCHESTRATION.md" ] || [ ! -d "$REPO_ROOT/skills" ]; then
  echo "ERROR: cd into the OpenClawTrevorMentis repo root first." >&2
  echo "       (Looking for ORCHESTRATION.md and skills/ in $REPO_ROOT)" >&2
  exit 2
fi

DEST="$REPO_ROOT/skills/daily-intel-brief"

if [ -d "$DEST" ]; then
  echo "NOTE: $DEST already exists; overwriting (your local edits will be lost)." >&2
  read -r -p "Continue? [y/N] " ans
  case "$ans" in y|Y|yes) ;; *) echo "aborted."; exit 1 ;; esac
  rm -rf "$DEST"
fi

mkdir -p "$DEST"
# Copy everything from the bundle except this installer itself
( cd "$SCRIPT_DIR" && find . -mindepth 1 -not -name 'INSTALL.sh' -print0 \
    | xargs -0 -I{} cp -R "{}" "$DEST/" )

echo
echo "Installed -> $DEST"
echo
git -C "$REPO_ROOT" add skills/daily-intel-brief
git -C "$REPO_ROOT" status --short -- skills/daily-intel-brief

cat <<'NEXT'

Next steps (run from the repo root):

  git checkout -b feat/daily-intel-brief
  git commit -m "feat(skills): add daily-intel-brief orchestrator + 3 subagents

Composes sat-toolkit, source-evaluation, indicators-and-warnings,
bluf-report, geospatial-osint, chartgen, mermaid, pdf-report into a
six-region + finance daily product. Routes analyst calls to
deepseek/deepseek-v4-pro per ORCHESTRATION.md escalation criteria."
  git push -u origin feat/daily-intel-brief

When git asks for credentials at push:
  Username: your GitHub username
  Password: your Personal Access Token (PAT)

Then open the PR link git printed and merge into main.
NEXT
