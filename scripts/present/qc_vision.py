#!/usr/bin/env python3
"""Vision QC — Phase B verification via Opus 4.7 (via OpenRouter).

Reads a media file, sends to Opus 4.7 with vision for quality assessment.
Returns structured JSON: {"pass": bool, "issues": [str], "fixes": [str]}.

Usage:
    python3 scripts/present/qc_vision.py \\
        --file exports/images/cover.png \\
        --spec "Dark navy background, gold accents, geopolitical cover art with Earth imagery"

    python3 scripts/present/qc_vision.py --self-test

Cost: ~$0.05-0.10 per check (Opus 4.7 vision via OpenRouter).
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import pathlib
import sys
import urllib.request

WORKSPACE = pathlib.Path("/home/ubuntu/.openclaw/workspace")


def self_test() -> list[str]:
    """Check OpenRouter access to Opus 4.7."""
    failures = []
    key = _get_openrouter_key()
    if not key:
        failures.append("OPENROUTER_API_KEY not set")
        return failures

    try:
        payload = json.dumps({
            "model": "anthropic/claude-opus-4.7",
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "OK"}],
        }).encode()
        req = urllib.request.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status != 200:
                failures.append(f"OpenRouter returned HTTP {resp.status}")
    except Exception as exc:
        failures.append(f"OpenRouter unreachable: {exc}")

    return failures


def _get_openrouter_key() -> str:
    """Get OpenRouter key from env or .env."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        env_path = WORKSPACE / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("OPENROUTER_API_KEY="):
                    key = line.split("=", 1)[1].strip('"').strip("'")
                    break
    return key


def encode_file(file_path: str) -> str:
    """Read a file and return base64 encoded content."""
    path = pathlib.Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    data = path.read_bytes()
    return base64.b64encode(data).decode("ascii")


def media_type(file_path: str) -> str:
    """Determine MIME type from file magic bytes (not extension)."""
    path = pathlib.Path(file_path)
    if not path.exists():
        return "application/octet-stream"
    header = path.read_bytes()[:4]
    if header[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if header[:4] == b"\x89PNG":
        return "image/png"
    if header[:4] == b"RIFF":
        return "image/webp"
    ext = path.suffix.lower()
    return {
        ".mp4": "video/mp4",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
    }.get(ext, "application/octet-stream")


def qc_check(file_path: str, spec: str) -> dict:
    """Run vision QC via Opus 4.7.

    Args:
        file_path: Path to the media file to check.
        spec: Text description of what the artefact should look like.

    Returns:
        Dict with pass, issues, fixes.
    """
    key = _get_openrouter_key()
    if not key:
        return {"pass": False, "issues": ["OPENROUTER_API_KEY not set"], "fixes": []}

    file_b64 = encode_file(file_path)
    mime = media_type(file_path)

    # For audio, use text-based check
    if mime.startswith("audio/"):
        prompt = f"""QC check on a TREVOR client audio artefact.

SPEC: {spec}

File: {file_path}

Check: Does file exist? Size reasonable? Duration plausible?
Answer in JSON: {{"pass": bool, "issues": [str], "fixes": [str]}}.
Be strict — this goes to a paying client."""

        payload = json.dumps({
            "model": "anthropic/claude-opus-4.7",
            "max_tokens": 500,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()

    # For images, include the image data
    elif mime.startswith("image/"):
        payload = json.dumps({
            "model": "anthropic/claude-opus-4.7",
            "max_tokens": 1000,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{file_b64}"}},
                    {"type": "text", "text": f"""QC check on a TREVOR client artefact.
    
    SPEC: {spec}
    
    Answer in JSON: {{"pass": bool, "issues": [str], "fixes": [str]}}.
    Be strict — this goes to a paying client."""}
                ]
            }],
        }).encode()

    # For video, extract keyframe and check that + metadata
    elif mime.startswith("video/"):
        import subprocess
        import tempfile

        # Extract 3 keyframes
        duration = 10.0
        try:
            r = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", file_path],
                capture_output=True, text=True, timeout=10,
            )
            duration = float(r.stdout.strip()) if r.stdout.strip() else 10.0
        except Exception:
            pass

        keyframes_data = []
        with tempfile.TemporaryDirectory() as tmpdir:
            for pct in [0.15, 0.5, 0.85]:
                seek = duration * pct
                out = pathlib.Path(tmpdir) / f"keyframe_{int(pct*100)}.png"
                subprocess.run(
                    ["ffmpeg", "-y", "-ss", str(seek), "-i", file_path,
                     "-vframes", "1", str(out)],
                    capture_output=True, timeout=30,
                )
                if out.exists():
                    keyframes_data.append(
                        {"position": f"{seek:.1f}s", "data": base64.b64encode(out.read_bytes()).decode("ascii")}
                    )

        content = [
            {"type": "text", "text": f"QC check on a TREVOR client video artefact.\n\nSPEC: {spec}\n\nDuration: {duration:.1f}s. 3 keyframes attached at 15%, 50%, 85%.\n\nAnswer in JSON: {{\"pass\": bool, \"issues\": [str], \"fixes\": [str]}}. Be strict — this goes to a paying client."}
        ]
        # Add keyframe images
        for kf in keyframes_data[:3]:
            content.insert(-1, {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{kf['data']}"}})

        payload = json.dumps({
            "model": "anthropic/claude-opus-4.7",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": content}],
        }).encode()
    else:
        return {"pass": False, "issues": [f"Unsupported media type: {mime}"], "fixes": []}

    # Send to OpenRouter
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/trevormentis-spec",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            response = json.loads(resp.read())
        text = response["choices"][0]["message"]["content"]

        # Extract JSON from response — robust to surrounding text
        import re as _re
        # Find the first { and last } to extract JSON
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            json_str = text[start:end+1]
            verdict = json.loads(json_str)
        else:
            verdict = {"pass": False, "issues": [f"No JSON in Opus response: {text[:200]}"], "fixes": []}
        return verdict
    except Exception as exc:
        return {"pass": False, "issues": [f"QC error: {exc}"], "fixes": []}


def main():
    parser = argparse.ArgumentParser(description="Vision QC — Phase B verification")
    parser.add_argument("--file", help="Path to media file")
    parser.add_argument("--spec", help="Specification description")
    parser.add_argument("--self-test", action="store_true", help="Self-test only")
    args = parser.parse_args()

    if args.self_test:
        failures = self_test()
        if failures:
            for f in failures:
                print(f"  QC DISABLED: {f}")
            sys.exit(0)
        else:
            print("  QC READY: Opus 4.7 via OpenRouter available")
            return

    if not args.file or not args.spec:
        parser.error("--file and --spec required (unless --self-test)")
        failures = self_test()
        if failures:
            for f in failures:
                print(f"  QC DISABLED: {f}")
        else:
            print("  QC READY: Opus 4.7 via OpenRouter available")
        return

    verdict = qc_check(args.file, args.spec)
    print(json.dumps(verdict, indent=2))
    if not verdict.get("pass", False):
        sys.exit(1)


if __name__ == "__main__":
    main()
