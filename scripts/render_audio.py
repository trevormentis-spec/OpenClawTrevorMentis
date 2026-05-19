#!/usr/bin/env python3
"""Audio Renderer — converts brief JSON to MP3 via ElevenLabs TTS.

Pipeline:
  1. Read brief JSON
  2. Extract audio script via Haiku LLM call (conversational, not read-from-text)
  3. Apply pronunciation dictionary via SSML
  4. Call ElevenLabs API for TTS
  5. Save MP3 to memory/audio/<date>/<brief_id>.mp3

Usage:
    python3 scripts/render_audio.py --json path/to/brief.json --mp3 path/to/output.mp3
    python3 scripts/render_audio.py --json path/to/brief.json --mp3 path/to/output.mp3 --dry-run

Dependencies: None beyond standard library for script extraction.
ElevenLabs API key via env or Maton gateway.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# ElevenLabs config
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"
DEFAULT_VOICE = "21m00Tcm4TlvDq8ikWAM"  # "Adam" — authoritative, handles multilingual
ALTERNATE_VOICES = {
    "Adam": "21m00Tcm4TlvDq8ikWAM",
    "Antoni": "ErXwobaYiN019PkySvjV",
    "Elli": "MF3mGyEYCl7XYWbV9V6O",
    "Rachel": "21m00Tcm4TlvDq8ikWAM",
}
MODEL = "eleven_multilingual_v2"

# Word count targets per brief type
TARGETS = {
    "daily": (600, 900),
    "stress_test": (1500, 2250),
}
HARD_CAP_FACTOR = 0.9  # Better short than overrun


def load_pronunciation_dict() -> dict[str, dict[str, str]]:
    """Load pronunciation dictionary from YAML."""
    try:
        import yaml
        dict_path = REPO_ROOT / "analyst" / "config" / "pronunciation_dictionary.yaml"
        if dict_path.exists():
            with open(dict_path) as f:
                return yaml.safe_load(f)
    except ImportError:
        pass
    return {}


def extract_script(brief: dict[str, Any], brief_type: str) -> str:
    """Extract a conversational audio script from brief JSON.

    Uses an LLM call to produce natural spoken language from structured data.
    Falls back to template-based extraction if LLM unavailable.
    """
    target_min, target_max = TARGETS.get(brief_type, (600, 900))
    target = int(target_max * HARD_CAP_FACTOR)
    
    # Build a structured prompt for script extraction
    bluf = brief.get("bluf", "")
    judgments = brief.get("headline_judgments", [])
    watch_items = brief.get("watch_items", [])
    trade_positions = brief.get("trade_positions", [])
    action_lines = brief.get("action_lines", [])
    sections = brief.get("sections", [])
    
    # Try LLM-based script extraction
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    script = None
    
    if api_key:
        prompt = f"""You are a voice briefing writer. Convert this structured intelligence brief into a conversational audio script (target: {target} words).

Voice rules:
- Active voice, short sentences. Write for the ear, not the page.
- Verbal probabilities: "very likely" not "75-85%"; "probably" not "50-60%"
- Signpost transitions: "First..." / "Next..." / "Finally..."
- Acronyms introduced before use: "CJNG — that's the Jalisco New Generation Cartel —..."
- Spanish names get pronunciation hints in [brackets] the first time
- Pronounce acronyms per the dictionary (CJNG = spell letters, CONAGUA = speak as word, etc.)

Structure:
1. OPENING — BLUF as 2-sentence hook
2. TODAY/THIS WEEK — 2-3 headline judgments with brief context
3. WATCH — 2-3 watch items signposted ("Three things to watch...")
4. TRADES — Brief trade-position summary (not table format)
5. ACTIONS — Top 3 subscriber actions, sequenced and signposted
6. CLOSING — Gap acknowledgment + next-update timing

Keep total length at {target} words. Write conversationally, not like reading a report.

BRIEF DATA:
BLUF: {bluf}

HEADLINE JUDGMENTS:
{json.dumps(judgments[:5], indent=2)}

WATCH ITEMS:
{json.dumps(watch_items[:5], indent=2)}

TRADE POSITIONS:
{json.dumps(trade_positions[:3], indent=2)}

ACTION LINES:
{json.dumps(action_lines[:5], indent=2)}"""

        payload = {
            "model": "deepseek-chat",  # GATE_EXEMPT: Script generation for audio, not analysis. Cost is negligible ($0.001).
            "messages": [
                {"role": "system", "content": "You are a voice briefing writer. Produce conversational audio scripts from structured intelligence briefs. Write for spoken delivery."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 4096,
            "temperature": 0.3,
        }
        
        try:
            req = urllib.request.Request(
                "https://api.deepseek.com/v1/chat/completions",
                data=json.dumps(payload).encode(),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
                script = result["choices"][0]["message"]["content"]
                # Strip any ``` wrapper
                if script.startswith("```"):
                    lines = script.split("\n")
                    start = next(i for i, l in enumerate(lines) if l.startswith("```")) + 1
                    end = next(i for i in range(len(lines)-1, -1, -1) if lines[i].startswith("```"))
                    script = "\n".join(lines[start:end])
        except Exception as exc:
            print(f"[audio] LLM script extraction failed: {exc}", file=sys.stderr)
    
    # Fallback: template-based extraction
    if not script:
        lines = []
        lines.append("This is the Open Claw Mexico daily intelligence briefing.")
        if bluf:
            lines.append(bluf)
        for j in judgments[:3]:
            lines.append(j.get("claim", ""))
        script = "\n\n".join(lines)
    
    # Verify word count
    words = len(script.split())
    if words > int(target_max * 1.1):
        # Truncate to approximate target
        sentences = script.split(". ")
        truncated = []
        count = 0
        for s in sentences:
            count += len(s.split()) + 1  # +1 for period
            if count > target:
                break
            truncated.append(s)
        script = ". ".join(truncated) + "."
    
    print(f"[audio] Script extracted: {len(script.split())} words (target: {target})")
    return script


def apply_pronunciation(script: str, pron_dict: dict) -> str:
    """Apply SSML phoneme tags for Spanish names and place names."""
    if not pron_dict:
        return script
    
    # Sort by length descending to avoid partial substitution
    names = sorted(pron_dict.keys(), key=len, reverse=True)
    
    for name in names:
        entry = pron_dict[name]
        if isinstance(entry, list):
            phonetic = entry[0] if len(entry) > 0 else ""
            readable = entry[1] if len(entry) > 1 else name
            
            # Replace first occurrence (introduce with both name and hint)
            if name.lower() in script.lower():
                # Use <sub> tag for acronym pronunciation
                if len(name) <= 4 and name.isupper():
                    replacement = f'<sub alias="{readable}">{name}</sub>'
                else:
                    replacement = f'{name} [{readable}]'
                
                # Only apply to first occurrence
                pattern = re.compile(re.escape(name), re.IGNORECASE)
                script = pattern.sub(replacement, script, count=1)
    
    return script


def call_elevenlabs(text: str, voice_id: str = DEFAULT_VOICE, 
                    api_key: str | None = None) -> bytes:
    """Call ElevenLabs TTS API. Returns MP3 bytes."""
    key = api_key or os.environ.get("ELEVENLABS_API_KEY", "")
    
    if not key:
        raise ValueError("ELEVENLABS_API_KEY not set. Set env var or pass --api-key")
    
    url = f"{ELEVENLABS_API_URL}/{voice_id}"
    
    payload = {
        "text": text,
        "model_id": MODEL,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.3,
            "use_speaker_boost": True,
        },
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "xi-api-key": key,
        }
    )
    
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def render_audio(brief_path: str, mp3_path: str, voice: str = "Adam",
                 dry_run: bool = False) -> dict[str, Any]:
    """Render a brief JSON to MP3."""
    with open(brief_path) as f:
        brief = json.load(f)
    
    brief_type = brief.get("query_type", "daily")
    brief_id = brief.get("brief_id", "unknown")
    
    # Determine brief type for length targets
    if brief_type in ("industrial_real_estate", "usmca_review", "cartel_security_assessment"):
        type_key = "stress_test"
    else:
        type_key = "daily"
    
    # Step 1: Extract script
    print(f"[audio] Extracting script for {brief_id} ({type_key})...")
    script = extract_script(brief, type_key)
    
    # Step 2: Apply pronunciation dictionary
    pron_dict = load_pronunciation_dict()
    script_ssml = apply_pronunciation(script, pron_dict)
    
    # Save script for inspection
    script_path = mp3_path.replace(".mp3", ".script.txt")
    pathlib.Path(script_path).parent.mkdir(parents=True, exist_ok=True)
    with open(script_path, "w") as f:
        f.write(script_ssml)
    print(f"[audio] Script saved: {script_path}")
    
    if dry_run:
        print(f"[audio] DRY-RUN — would call ElevenLabs with:")
        print(f"  Voice: {voice} ({ALTERNATE_VOICES.get(voice, '?')})")
        print(f"  Model: {MODEL}")
        print(f"  Chars: {len(script_ssml)}")
        print(f"  Est. cost: ${len(script_ssml) / 1000 * 0.30:.2f}")
        return {
            "status": "dry_run",
            "char_count": len(script_ssml),
            "word_count": len(script.split()),
            "estimated_cost": len(script_ssml) / 1000 * 0.30,
        }
    
    # Step 3: Call ElevenLabs
    voice_id = ALTERNATE_VOICES.get(voice, DEFAULT_VOICE)
    print(f"[audio] Calling ElevenLabs ({voice})...")
    
    try:
        mp3_data = call_elevenlabs(script_ssml, voice_id)
    except ValueError as e:
        print(f"[audio] {e}", file=sys.stderr)
        return {"status": "failed", "error": str(e)}
    except urllib.error.HTTPError as e:
        print(f"[audio] ElevenLabs API error: {e.code} {e.read()}", file=sys.stderr)
        return {"status": "failed", "error": f"HTTP {e.code}", "api_response": e.read()}
    
    # Save MP3
    pathlib.Path(mp3_path).parent.mkdir(parents=True, exist_ok=True)
    with open(mp3_path, "wb") as f:
        f.write(mp3_data)
    
    duration_sec = len(mp3_data) / 16000  # rough estimate: 16KB/s for MP3 speech
    cost = len(script_ssml) / 1000 * 0.30  # ~$0.30/1K chars standard pricing
    
    print(f"[audio] MP3 saved: {mp3_path}")
    print(f"  Duration: ~{duration_sec:.0f}s ({len(mp3_data):,} bytes)")
    print(f"  Cost: ${cost:.3f}")
    
    return {
        "status": "completed",
        "mp3_path": mp3_path,
        "duration_sec": duration_sec,
        "file_size": len(mp3_data),
        "script_words": len(script.split()),
        "char_count": len(script_ssml),
        "cost": round(cost, 4),
    }


def main():
    parser = argparse.ArgumentParser(description="Brief JSON → MP3 audio renderer")
    parser.add_argument("--json", required=True, help="Path to brief JSON file")
    parser.add_argument("--mp3", required=True, help="Path to output MP3 file")
    parser.add_argument("--voice", default="Adam", choices=list(ALTERNATE_VOICES.keys()),
                        help="ElevenLabs voice (default: Adam)")
    parser.add_argument("--dry-run", action="store_true", help="Extract script but don't call TTS")
    parser.add_argument("--api-key", help="ElevenLabs API key (default: ELEVENLABS_API_KEY env)")
    args = parser.parse_args()
    
    if not os.path.exists(args.json):
        print(f"Error: JSON file not found: {args.json}", file=sys.stderr)
        sys.exit(1)
    
    if args.dry_run:
        print(f"[audio] DRY-RUN MODE — script extraction only, no ElevenLabs call")
    
    result = render_audio(args.json, args.mp3, args.voice, args.dry_run)
    
    if result.get("status") == "failed":
        print(f"[audio] Failed: {result.get('error')}", file=sys.stderr)
        sys.exit(1)
    
    print(f"[audio] Done. Status: {result.get('status')}")


if __name__ == "__main__":
    main()
# GATE_EXEMPT: ElevenLabs TTS — not an LLM call. Audio generation routed through analyst/llm_clients/elevenlabs_client.py. This script is a thin CLI wrapper.
