#!/usr/bin/env bash
#==============================================================================
# rss-digest-heartbeat.sh — Lightweight geopolitics RSS digest for heartbeat
#
# Runs on heartbeat cycles (Phase E). Uses rss-feed-digest skill to keyword-
# filter geopolitics feeds and produce a short markdown summary.
#
# Output: exports/rss-digest/YYYY-MM-DD.md
# Cycle: Intended for 30-min heartbeat, filters last 6 hours per run
#==============================================================================
set -uo pipefail

REPO="/home/ubuntu/.openclaw/workspace"
DATE_UTC=$(date -u +%Y-%m-%d)
OUT_DIR="$REPO/exports/rss-digest"
DIGEST="$OUT_DIR/${DATE_UTC}.md"

mkdir -p "$OUT_DIR"

SKILL_DIR="$REPO/skills/rss-feed-digest"
FEEDS_FILE="$REPO/config/rss-digest/geopolitics-feeds.txt"

# Geopolitics keyword set — broad coverage, topic-agnostic
# Covers: conflict, diplomacy, sanctions, military, energy, elections, treaties
KEYWORDS="war,conflict,sanctions,military,strike,ceasefire,diplomacy,treaty,nuclear,missile,drone,oil,gas,energy,arms,weapons,defense,election,sanction,negotiation,alliance,escalation,retaliation"

cd "$REPO" || exit 1

python3 "$SKILL_DIR/scripts/rss_digest.py" fetch \
    --feed-file "$FEEDS_FILE" \
    --hours 6 \
    --keywords "$KEYWORDS" \
    --limit 30 \
    --format markdown \
    --output "$DIGEST" 2>&1 | tail -1

echo "[rss-digest] Geopolitics digest -> $DIGEST"
