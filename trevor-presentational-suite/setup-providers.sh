#!/usr/bin/env bash
# TPS Provider Setup — provision API keys for the presentation suite generators.
#
# Usage:
#   bash trevor-presentational-suite/setup-providers.sh
#
# This script checks which providers need keys and prints instructions.
# It does NOT read or store keys itself.

set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$REPO/.env"
PROVIDERS="$REPO/trevor-presentational-suite/providers.yaml"

echo "=== TPS Provider Setup ==="
echo ""

# Check which providers are already configured
echo "--- Checking .env ---"
if [ -f "$ENV_FILE" ]; then
    echo "✅ .env exists"
else
    echo "❌ .env missing — create from deployment/.env.example"
fi

echo ""
echo "--- Generator Key Status ---"

# Check each generator's key requirements
declare -A PROVIDER_KEYS
PROVIDER_KEYS["OpenRouter (all LLM generators)"]="OPENROUTER_API_KEY"
PROVIDER_KEYS["DeepSeek (V4 Flash/Pro)"]="DEEPSEEK_API_KEY"
PROVIDER_KEYS["ElevenLabs (TTS audio)"]="ELEVENLABS_API_KEY"
PROVIDER_KEYS["Flux2 (image gen)"]="FLUX_API_KEY"
PROVIDER_KEYS["OpenAI (GPT-4 image / DALL-E)"]="OPENAI_API_KEY"
PROVIDER_KEYS["Anthropic (Claude vision)"]="ANTHROPIC_API_KEY"
PROVIDER_KEYS["Recraft (vector recolor)"]="RECRAFT_API_KEY"
PROVIDER_KEYS["Ideogram (image gen)"]="IDEOGRAM_API_KEY"
PROVIDER_KEYS["Google (Imagen)"]="GOOGLE_API_KEY"
PROVIDER_KEYS["HeyGen (AI video)"]="HEYGEN_API_KEY"
PROVIDER_KEYS["Suno (AI music)"]="SUNO_API_KEY"
PROVIDER_KEYS["Runway (video gen)"]="RUNWAY_API_KEY"
PROVIDER_KEYS["Kling (video gen)"]="KLING_API_KEY"
PROVIDER_KEYS["Veo (video gen)"]="VEO_API_KEY"

MISSING=0
HAVE=0
for name in "${!PROVIDER_KEYS[@]}"; do
    key="${PROVIDER_KEYS[$name]}"
    if grep -q "$key" "$ENV_FILE" 2>/dev/null; then
        echo "  ✅ $name"
        HAVE=$((HAVE+1))
    else
        echo "  ❌ $name — needs $key in .env"
        MISSING=$((MISSING+1))
    fi
done

echo ""
echo "--- Summary ---"
echo "  Configured: $HAVE"
echo "  Missing: $MISSING"

echo ""
echo "--- Quick Provisioning ---"
echo "Add any missing key to $ENV_FILE with:"
echo "  echo 'PROVIDER_KEY=your_key_here' >> $ENV_FILE"
echo ""
echo "Then verify with:"
echo "  python3 trevor-presentational-suite/tests/run_all.py"
echo ""
echo "For new keys, sign up at:"
echo "  OpenRouter:  https://openrouter.ai/keys"
echo "  ElevenLabs:  https://elevenlabs.io/app/settings/api-keys"
echo "  Flux/Recraft/Ideogram/HeyGen/Suno/Runway/Kling/Veo:"
echo "    → check providers.yaml for endpoint URLs and signup links"
echo "    cat $PROVIDERS | grep -A 3 'endpoint\\|signup'"
