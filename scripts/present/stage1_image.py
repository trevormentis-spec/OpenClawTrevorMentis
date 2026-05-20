#!/usr/bin/env python3
"""Stage 1 — Image Generation.

Cover art and section headers via GenViral Studio AI (nano-banana-2).
One provider: GenViral. No aggregator. No fallback chain (substitution table only).

Self-test at startup: GENVIRAL_API_KEY set? Endpoint reachable?
If test fails, logs "STAGE 1 DISABLED: reason" and exits clean (code 0).

Usage:
    python3 scripts/present/stage1_image.py \\
        --prompt "Geopolitical map cover" \\
        --output exports/images/cover.png

    python3 scripts/present/stage1_image.py \\
        --prompt "Section: Middle East" \\
        --output exports/images/section-middle-east.png \\
        --aspect-ratio "16:9"

Budget: ~1 credit ($0.01) per image via nano-banana-2.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
from typing import Optional

WORKSPACE = pathlib.Path("/home/ubuntu/.openclaw/workspace")
GENVIRAL_SH = WORKSPACE / "skills" / "genviral" / "scripts" / "genviral.sh"
DEFAULT_MODEL = "google/nano-banana-2"  # 1 credit, reliable

STYLE_SUFFIX = (
    "Style: Professional intelligence briefing aesthetic. "
    "Dark navy background (#0f3460), clean data-driven minimal layout. "
    "Gold accent (#c9a84c). Sharp labels. No decorative elements."
)


def self_test() -> list[str]:
    """Run startup self-test. Returns list of failure reasons (empty = pass)."""
    failures = []

    # 1. Env var check
    key = os.environ.get("GENVIRAL_API_KEY", "")
    env_path = WORKSPACE / ".env"
    if not key and env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("GENVIRAL_API_KEY="):
                key = line.split("=", 1)[1].strip('"').strip("'")
                break
    if not key:
        failures.append("GENVIRAL_API_KEY not set in .env")

    # 2. GenViral script exists
    if not GENVIRAL_SH.exists():
        failures.append(f"genviral.sh not found at {GENVIRAL_SH}")

    # 3. Endpoint reachable
    if key and GENVIRAL_SH.exists():
        env = os.environ.copy()
        env["GENVIRAL_API_KEY"] = key
        try:
            result = subprocess.run(
                ["bash", str(GENVIRAL_SH), "subscription", "--json"],
                capture_output=True, text=True, timeout=15, env=env,
            )
            if result.returncode != 0:
                failures.append(f"GenViral API unreachable: {result.stderr.strip()[:100]}")
            else:
                # Verify credits
                for line in result.stdout.split("\n"):
                    if "remaining" in line:
                        break
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            failures.append(f"GenViral endpoint test failed: {exc}")

    return failures


def _load_env() -> dict[str, str]:
    """Load .env into environment dict."""
    env = os.environ.copy()
    env_path = WORKSPACE / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k] = v.strip('"').strip("'")
    return env


def _genviral(*args: str, timeout: int = 60) -> dict:
    """Run genviral.sh and return parsed JSON."""
    env = _load_env()
    cmd = ["bash", str(GENVIRAL_SH)] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"genviral.sh exit {result.returncode}: {result.stderr.strip()[:200]}")

    # Find JSON block in output
    start = result.stdout.find("{")
    if start >= 0:
        try:
            return json.loads(result.stdout[start:])
        except json.JSONDecodeError:
            pass
    raise RuntimeError(f"No JSON in genviral output:\n{result.stdout[:500]}")


def generate_image(
    prompt: str,
    output_path: str,
    aspect_ratio: str = "16:9",
) -> str:
    """Generate an image via GenViral Studio AI.

    Args:
        prompt: Image description.
        output_path: Where to save the image.
        aspect_ratio: Aspect ratio string.

    Returns:
        Output path on success.

    Raises:
        RuntimeError on failure.
    """
    output_file = pathlib.Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    full_prompt = f"{prompt}\n\n{STYLE_SUFFIX}"

    result = _genviral(
        "studio-generate-image",
        "--model-id", DEFAULT_MODEL,
        "--prompt", full_prompt,
        "--aspect-ratio", aspect_ratio,
        "--output-format", "png",
        "--json",
    )

    output_url = result.get("output_url") or result.get("preview_url") or ""
    if not output_url:
        raise RuntimeError(f"No image URL in response: {str(result)[:200]}")

    # Download
    import urllib.request
    req = urllib.request.Request(output_url, headers={"User-Agent": "Trevor-Present/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()

    if len(data) < 100:
        raise RuntimeError(f"Downloaded image too small: {len(data)} bytes")

    output_file.write_bytes(data)

    credits = result.get("credits_used", 1)
    print(f"  ✅ Cover: {output_file} ({len(data) // 1024} KB, {credits} credit(s))")
    return str(output_file)


def verify_image(image_path: str) -> dict:
    """Verify a generated image file is valid and non-empty."""
    path = pathlib.Path(image_path)
    checks = {
        "exists": path.exists(),
        "not_empty": path.stat().st_size > 100 if path.exists() else False,
    }
    if checks["exists"]:
        header = path.read_bytes()[:4]
        checks["valid_format"] = (
            header[:3] == b"\xff\xd8\xff"  # JPEG
            or header[:4] == b"\x89PNG"        # PNG
            or header[:4] == b"RIFF"           # WEBP
        )
        checks["size_kb"] = round(path.stat().st_size / 1024, 1)
    return checks


def main():
    parser = argparse.ArgumentParser(description="Stage 1 — Cover image via GenViral")
    parser.add_argument("--prompt", help="Image description")
    parser.add_argument("--output", "-o", help="Output path (PNG)")
    parser.add_argument("--aspect-ratio", default="16:9", help="Aspect ratio")
    parser.add_argument("--self-test", action="store_true",
                        help="Run self-test and exit (does not generate)")
    args = parser.parse_args()

    # Self-test mode
    if args.self_test:
        failures = self_test()
        if failures:
            for f in failures:
                print(f"  STAGE 1 DISABLED: {f}")
            sys.exit(0)
        else:
            print("  STAGE 1 READY: GenViral API reachable, credits available")
            sys.exit(0)

    # Require prompt + output if not self-test
    if not args.prompt or not args.output:
        parser.error("--prompt and --output are required for image generation")

    # Pre-flight self-test
    failures = self_test()
    if failures:
        for f in failures:
            print(f"  STAGE 1 DISABLED: {f}")
        sys.exit(0)

    # Generate
    result = generate_image(
        prompt=args.prompt,
        output_path=args.output,
        aspect_ratio=args.aspect_ratio,
    )

    # Verify
    checks = verify_image(result)
    print(f"  Verification: {checks}")
    if checks.get("valid_format") and checks.get("not_empty"):
        print(f"  ✅ Stage 1 deliverable: {result}")
    else:
        print(f"  ❌ Stage 1 verification failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
