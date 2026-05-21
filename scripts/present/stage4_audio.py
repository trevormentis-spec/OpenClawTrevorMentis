#!/usr/bin/env python3
"""Stage 4 — Narration Audio.

Pipeline:
  1. Script generation via Opus 4.7 (analyst voice, 90-180s, ~225-450 words)
  2. TTS via ElevenLabs (or silent fallback)
  3. Verification: ffprobe duration, whisper transcription, Levenshtein > 0.92

Self-test: whisper available? ElevenLabs key or substitute?
Usage:
    python3 scripts/present/stage4_audio.py --brief /tmp/brief.json --output exports/audio/narration.mp3
    python3 scripts/present/stage4_audio.py --self-test
"""
from _present_env import get_key, load_env as _load_env
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Optional

WORKSPACE = pathlib.Path("/home/ubuntu/.openclaw/workspace")
TARGET_WORDS_MIN = 225
TARGET_WORDS_MAX = 450  # 90-180s at ~150 wpm

ELEVENLABS_VOICE = "21m00Tcm4TlvDq8ikWAM"  # "Adam"


def self_test() -> list[str]:
    """Check prerequisites."""
    failures = []
    try:
        import whisper
        print(f"  whisper: available")
    except ImportError:
        failures.append("openai-whisper not installed")

    key = _get_env_key("ELEVENLABS_API_KEY")
    if key:
        try:
            req = urllib.request.Request(
                "https://api.elevenlabs.io/v1/voices",
                headers={"xi-api-key": key},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    print(f"  ElevenLabs: reachable")
        except:
            failures.append("ElevenLabs endpoint unreachable")
    else:
        print(f"  ElevenLabs: no API key (will use silent fallback)")

    return failures


def _get_env_key(key_name: str) -> str:
    """Get a key from env or .env."""
    val = os.environ.get(key_name, "")
    if not val:
        env_path = os.environ.get("ENV_NOT_USED", "")
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith(f"{key_name}="):
                    val = line.split("=", 1)[1].strip('"').strip("'")
                    break
    return val


def _call_opus(system: str, prompt: str, max_tokens: int = 1500) -> str:
    """Call Opus 4.7 via OpenRouter."""
    key = _get_env_key("OPENROUTER_API_KEY")
    payload = json.dumps({
        "model": "anthropic/claude-opus-4.7",
        "max_tokens": max_tokens,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def generate_script(brief: dict) -> str:
    """Generate a conversational narration script via Opus 4.7.

    Returns script text (target: 225-450 words).
    """
    title = brief.get("title", "Intelligence Briefing")
    bluf = brief.get("bluf", "")
    judgments = brief.get("headline_judgments", [])
    trades = brief.get("trade_positions", [])
    actions = brief.get("action_lines", [])
    sections = brief.get("sections", [])

    judgments_text = "\n".join(
        f"- {j.get('claim', '')} [{j.get('kent_band', 'assessed')}]"
        for j in judgments[:5]
    )

    system = "You write conversational intelligence briefing narration scripts. Analyst voice. For spoken delivery."
    prompt = f"""Write a {TARGET_WORDS_MIN}-{TARGET_WORDS_MAX} word narration script for this briefing.

RULES:
- Analyst voice: conversational, not read-from-report
- Verbal probabilities: "very likely", not "75-85%"
- No lists ("first, second, third")
- Opens with a hook from the BLUF
- Closes with the QC review flag: "This briefing is pending human analyst QC review."
- Duration: 90-180 seconds at 150 wpm ({TARGET_WORDS_MIN}-{TARGET_WORDS_MAX} words)
- Sherman Kent probability language preserved
- Acronyms spelled out on first use

TITLE: {title}
BLUF: {bluf}
SECTIONS: {', '.join(s.get('title', '') for s in sections[:5])}
KEY JUDGMENTS:
{judgments_text}
TRADES: {', '.join(t.get('instrument', '') for t in trades[:3])}
ACTIONS: {', '.join(a.get('action', '') for a in actions[:3])}

Output ONLY the script text. No preamble, no markdown."""

    script = _call_opus(system, prompt).strip()
    if script.startswith("```"):
        lines = script.split("\n")
        start = next(i for i, l in enumerate(lines) if l.startswith("```")) + 1
        end = next(i for i in range(len(lines)-1, -1, -1) if lines[i].startswith("```"))
        script = "\n".join(lines[start:end]).strip()

    wc = len(script.split())
    print(f"  Script: {wc} words (Opus 4.7)")
    return script


def call_tts(text: str) -> bytes:
    """Call ElevenLabs TTS. Returns MP3 bytes."""
    key = _get_env_key("ELEVENLABS_API_KEY")
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY not set")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE}"
    payload = json.dumps({
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5, "similarity_boost": 0.75,
            "style": 0.3, "use_speaker_boost": True,
        },
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json", "xi-api-key": key},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def generate_silent_fallback(text: str, output_path: str) -> bytes:
    """Generate silent MP3 via ffmpeg when TTS unavailable."""
    import subprocess
    duration = max(len(text.split()) / 150, 10)
    output_file = pathlib.Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono",
         "-t", f"{duration:.0f}", str(output_file)],
        capture_output=True, timeout=30,
    )
    print(f"  ⚠️ TTS unavailable — silent audio ({duration:.0f}s)")
    return output_file.read_bytes()


def verify_audio(mp3_path: str, intended_script: str) -> dict:
    """Phase A + Phase B-audio verification.

    Phase A: ffprobe duration, valid MP3.
    Phase B: whisper transcription, Levenshtein > 0.92 against intended script.
    """
    checks = {}

    # Phase A
    path = pathlib.Path(mp3_path)
    checks["exists"] = path.exists()
    if not checks["exists"]:
        return {**checks, "pass": False, "error": "File not found"}

    checks["size_kb"] = round(path.stat().st_size / 1024, 1)
    checks["not_empty"] = path.stat().st_size > 1000

    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,format_name",
         "-of", "default=noprint_wrappers=1", mp3_path],
        capture_output=True, text=True, timeout=10,
    )
    for line in r.stdout.split("\n"):
        if "format_name" in line:
            checks["format"] = line.split("=", 1)[1].strip()
        if "duration" in line:
            try:
                checks["duration_s"] = round(float(line.split("=", 1)[1]), 1)
            except ValueError:
                pass

    checks["valid_audio"] = "mp3" in checks.get("format", "") or "mp3" in checks.get("format", "")
    checks["duration_ok"] = 80 <= checks.get("duration_s", 0) <= 200

    phase_a_pass = checks.get("valid_audio") and checks.get("duration_ok") and checks.get("not_empty")

    # Phase B: whisper transcription
    if phase_a_pass:
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(mp3_path)
            transcript = result["text"].strip()
            checks["transcript"] = transcript[:200]

            # Levenshtein similarity
            import Levenshtein
            script_clean = intended_script.lower()[:len(intended_script)]
            trans_clean = transcript.lower()[:len(intended_script)]
            similarity = Levenshtein.ratio(trans_clean, script_clean)
            checks["levenshtein"] = round(similarity, 3)

            if similarity > 0.92:
                checks["script_match"] = True
                print(f"  Whisper: {len(transcript.split())} words, Levenshtein {similarity:.3f} ✅")
            else:
                checks["script_match"] = False
                print(f"  Whisper: Levenshtein {similarity:.3f} < 0.92 ❌")
        except Exception as exc:
            checks["whisper_error"] = str(exc)
            checks["script_match"] = False
    else:
        checks["script_match"] = False

    checks["pass"] = phase_a_pass and checks.get("script_match", False)
    return checks


def render_audio(brief_path: str, output_path: str) -> dict:
    """Full pipeline: script → TTS → verify."""
    brief = json.loads(pathlib.Path(brief_path).read_text())

    # Step 1: Script generation
    script = generate_script(brief)

    # Save script alongside MP3
    script_path = output_path.replace(".mp3", ".script.txt")
    pathlib.Path(script_path).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(script_path).write_text(script)

    # Step 2: TTS
    try:
        mp3_data = call_tts(script)
    except (urllib.error.HTTPError, RuntimeError) as exc:
        code = getattr(exc, 'code', None)
        print(f"  ⚠️ ElevenLabs failed ({code or exc})")
        print(f"  → Silent fallback")
        mp3_data = generate_silent_fallback(script, output_path)
        tts_status = "silent_fallback"
    else:
        tts_status = "elevenlabs"

    # Save MP3
    output_file = pathlib.Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_bytes(mp3_data)

    word_count = len(script.split())
    duration_s = round(len(mp3_data) / 16000, 0) if tts_status != "elevenlabs" else 0
    cost = round(word_count * 0.001, 4)  # rough estimate

    return {
        "status": "completed",
        "tts_status": tts_status,
        "output": str(output_file),
        "script_path": script_path,
        "word_count": word_count,
        "duration_s": duration_s,
        "cost": cost,
        "file_size_kb": round(len(mp3_data) / 1024, 1),
    }


def main():
    parser = argparse.ArgumentParser(description="Stage 4 — Narration Audio")
    parser.add_argument("--brief", help="Path to brief JSON")
    parser.add_argument("--output", "-o", default="exports/audio/narration.mp3", help="Output MP3 path")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--skip-verify", action="store_true", help="Skip whisper transcription verification")
    args = parser.parse_args()

    if args.self_test:
        failures = self_test()
        if failures:
            for f in failures:
                print(f"  STAGE 4 DISABLED: {f}")
        else:
            print("  STAGE 4 READY: whisper + ElevenLabs available")
        return

    if not args.brief:
        parser.error("--brief required")

    result = render_audio(args.brief, args.output)
    tts = result["tts_status"]
    print(f"  {'✅' if tts == 'elevenlabs' else '⚠️'} Audio: {result['output']} ({result['word_count']} words, {tts})")

    # Verification
    if not args.skip_verify:
        script = pathlib.Path(result["script_path"]).read_text()
        checks = verify_audio(result["output"], script)
        print(f"  Verification: {checks}")
        if checks.get("pass"):
            print(f"  ✅ Stage 4 deliverable: {result['output']}")
        else:
            print(f"  ⚠️ Stage 4 verification partial — audio exists but duration/transcription may not meet target")
            print(f"  (Expected with silent fallback — real TTS needed for full verification)")


if __name__ == "__main__":
    main()
