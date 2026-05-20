#!/usr/bin/env bash
# TPS Provider Setup — simplified.
# OpenRouter covers most needs with one key.
# Add specialized keys only for specific generators.

set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$REPO/.env"

echo "=== TPS Provider Setup ==="
echo ""

# Minimal keys (these are what you actually need)
MINIMAL=(
    "OPENROUTER_API_KEY:covers all LLMs + image gen (flux, ideogram, recraft via OpenRouter)"
    "ELEVENLABS_API_KEY:TTS audio companion (get at https://elevenlabs.io)"
    "MAPBOX_TOKEN:interactive maps (free tier at https://account.mapbox.com)"
)

SPECIALIZED=(
    "FAL_API_KEY:unified fal.ai access for flux/ideogram/recraft/imagen (https://fal.ai)"
    "OPENAI_API_KEY:GPT-4 image gen (https://platform.openai.com)"
    "HEYGEN_API_KEY:AI video briefing (https://heygen.com)"
    "SUNO_API_KEY:AI music (https://suno.ai)"
    "RUNWAY_API_KEY:video gen (https://runwayml.com)"
)

echo "--- Already configured ---"
CONFIGURED=0
MISSING=0
for entry in "${MINIMAL[@]}"; do
    key="${entry%%:*}"
    desc="${entry#*:}"
    if grep -q "$key" "$ENV_FILE" 2>/dev/null; then
        echo "  ✅ $key — $desc"
        CONFIGURED=$((CONFIGURED+1))
    else
        echo "  ⬜ $key — $desc"
        MISSING=$((MISSING+1))
    fi
done

echo ""
echo "--- Minimal setup (OpenRouter covers LLMs + image gen) ---"
echo "  Just OPENROUTER_API_KEY enables:"
echo "    - All text generators (Opus, Sonnet, DeepSeek)"
echo "    - Image generation via OpenRouter proxy"
echo "    - Cost tracking through OpenRouter dashboard"
echo ""
echo "  Add ELEVENLABS_API_KEY + MAPBOX_TOKEN for full TPS."
echo ""
echo "  Specialized keys (only if needed):"
for entry in "${SPECIALIZED[@]}"; do
    echo "    - ${entry%%:*}: ${entry#*:}"
done

echo ""
echo "--- Quick add ---"
echo "  echo 'FAL_API_KEY=your_key_here' >> $ENV_FILE"
echo "  (replaces separate flux/ideogram/recraft/imagen keys)"
echo ""
echo "Then verify: cd trevor-presentational-suite && python3 tests/run_all.py"
