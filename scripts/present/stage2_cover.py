#!/usr/bin/env python3
"""Stage 2 — Cover art iteration loop.

Phase C: up to 3 attempts. Each iteration:
  1. Ask Opus 4.7 to review the QC failure + previous prompt, generate improved prompt
  2. Generate cover via GenViral
  3. Run Phase A + Phase B verification
  4. If pass → done. If fail after 3 → ship with cover_quality: degraded.

Usage:
    python3 scripts/present/stage2_cover.py \\
        --title "Global Security Briefing" \\
        --output exports/covers/briefing.png

    python3 scripts/present/stage2_cover.py --self-test

Cost: ~$0.05 per iteration (1 GenViral credit + 1 Opus prompt refinement)
Ceiling: $0.50 max (3 iterations at ~$0.15 each)
"""
from _present_env import get_key, load_env as _load_env
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import urllib.request

WORKSPACE = pathlib.Path("/home/ubuntu/.openclaw/workspace")
GENVIRAL_SH = WORKSPACE / "skills" / "genviral" / "scripts" / "genviral.sh"
QC_SCRIPT = WORKSPACE / "scripts" / "present" / "qc_vision.py"
BASE_PROMPT = (
    "Professional intelligence briefing cover. "
    "Dark navy background (#0f3460) with gold accent (#c9a84c). "
    "Clean, atmospheric, serious tone. "
    "NO text in the image — text will be added later. "
    "NO specific real people, NO recognizable faces. "
    "NO maps with country labels. "
    "Abstract geopolitical visualization: subtle Earth outline or data network overlays. "
    "Minimal, elegant, suited for a confidential document cover."
)

MAX_ATTEMPTS = 3


def self_test() -> list[str]:
    """Check prerequisites."""
    failures = []
    if not GENVIRAL_SH.exists():
        failures.append("GENVIRAL_API_KEY or genviral.sh not found")
    return failures


def _load_env_original() -> dict[str, str]:
    env = os.environ.copy()
    env_path = os.environ.get("ENV_NOT_USED", "")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k] = v.strip('"').strip("'")
    return env


def _get_openrouter_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        for line in pathlib.Path(os.environ.get("ENV_NOT_USED", "")).read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                key = line.split("=", 1)[1].strip('"').strip("'")
                break
    return key


def _call_opus(system: str, prompt: str, max_tokens: int = 1000) -> str:
    """Call Opus 4.7 via OpenRouter. Returns response text."""
    key = _get_openrouter_key()
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
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def refine_prompt(
    brief_title: str,
    previous_prompt: str,
    qc_issues: list[str],
    qc_fixes: list[str],
) -> str:
    """Ask Opus 4.7 to generate an improved GenViral prompt.

    Give it the original prompt + QC feedback. Returns a refined prompt string.
    """
    system = "You are an art director for an intelligence briefing cover. Improve GenViral Studio AI prompts."
    user = f"""I need a better GenViral image generation prompt for an intelligence briefing cover.

BRIEF TITLE: {brief_title}

PREVIOUS PROMPT:
```
{previous_prompt}
```

QC FAILURE ISSUES:
{chr(10).join(f'  - {i}' for i in qc_issues[:5])}

QC SUGGESTED FIXES:
{chr(10).join(f'  - {f}' for f in qc_fixes[:3])}

Generate a new GenViral prompt that:
- Starts with the title/subject context
- Uses BRAND: navy (#0f3460), gold (#c9a84c), dark background, elegant
- Has NO text in the image (text added later)
- Has NO specific real people, NO recognizable country outlines with labels, NO maps
- Abstract, atmospheric, serious — suited for confidential cover
- Is 2-4 sentences, concise

Output ONLY the prompt. No explanation, no markdown."""

    return _call_opus(system, user, max_tokens=500).strip().strip("`").strip()


def generate_cover(prompt: str, output_path: str) -> bool:
    """Generate a cover image via GenViral. Returns True on success."""
    output_file = pathlib.Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    env = _load_env()
    result = subprocess.run(
        ["bash", str(GENVIRAL_SH), "studio-generate-image",
         "--model-id", "google/nano-banana-2",
         "--prompt", prompt,
         "--aspect-ratio", "16:9",
         "--output-format", "png",
         "--json"],
        capture_output=True, text=True, timeout=60, env=env,
    )
    if result.returncode != 0:
        print(f"  ⚠️  GenViral failed: {result.stderr[:200]}")
        return False

    # Find JSON in output
    start = result.stdout.find("{")
    if start < 0:
        print(f"  ⚠️  No JSON in GenViral output")
        return False

    data = json.loads(result.stdout[start:])
    url = data.get("output_url") or data.get("preview_url", "")
    if not url:
        print(f"  ⚠️  No image URL from GenViral")
        return False

    import urllib.request as _req
    _req_url = _req.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with _req.urlopen(_req_url, timeout=60) as resp:
        img_data = resp.read()
    output_file.write_bytes(img_data)
    print(f"  ✅ Generated: {output_file} ({len(img_data)//1024} KB, {data.get('credits_used', 1)} credits)")
    return True


def run_qc(image_path: str) -> dict:
    """Run Opus 4.7 vision QC on the image. Returns verdict dict."""
    result = subprocess.run(
        ["python3", str(QC_SCRIPT), "--file", image_path,
         "--spec", "Intelligence briefing cover. Dark navy background, gold accents. Abstract, atmospheric, professional. NO text in image, NO real faces, NO country labels. Elegant and minimal."],
        capture_output=True, text=True, timeout=60, env=_load_env(),
    )
    try:
        start = result.stdout.find("{")
        if start >= 0:
            end = result.stdout.rfind("}")
            return json.loads(result.stdout[start:end+1])
    except (json.JSONDecodeError, IndexError):
        pass
    return {"pass": False, "issues": [f"QC parse error"], "fixes": []}


def main():
    parser = argparse.ArgumentParser(description="Stage 2 — Cover iteration loop")
    parser.add_argument("--title", default="Intelligence Briefing", help="Brief title")
    parser.add_argument("--output", "-o", default="exports/covers/cover.png", help="Output path")
    parser.add_argument("--self-test", action="store_true", help="Self-test")
    args = parser.parse_args()

    if args.self_test:
        failures = self_test()
        for f in failures or ["Stage 2 ready"]:
            print(f"  {f}")
        return

    print(f"\n=== Stage 2 — Cover Iteration ===")
    print(f"  Title: {args.title}")
    print(f"  Output: {args.output}")

    prompt = BASE_PROMPT
    attempts = 0

    while attempts < MAX_ATTEMPTS:
        attempts += 1
        print(f"\n--- Attempt {attempts}/{MAX_ATTEMPTS} ---")

        # Generate
        prompt_text = f"{args.title}. {prompt}"
        print(f"  Prompt: {prompt_text[:100]}...")
        ok = generate_cover(prompt_text, args.output)
        if not ok:
            print(f"  ⚠️  Generation failed, retrying...")
            continue

        # Phase A verification
        img_path = pathlib.Path(args.output)
        if not img_path.exists() or img_path.stat().st_size < 100:
            print(f"  ⚠️  Image corrupt or empty")
            continue

        print(f"  Phase A: {img_path.stat().st_size // 1024} KB ✅")

        # Phase B — Opus 4.7 vision QC
        verdict = run_qc(str(img_path))
        qc_pass = verdict.get("pass", False)
        issues = verdict.get("issues", [])
        fixes = verdict.get("fixes", [])

        if qc_pass:
            print(f"  Phase B: ✅ PASS")
            print(f"  Cover quality: good")
            print(f"\n✅ Stage 2 complete after {attempts} attempt(s)")
            return
        else:
            print(f"  Phase B: ❌ FAIL ({len(issues)} issues)")
            for i in issues[:3]:
                print(f"    • {i[:90]}")

        if attempts >= MAX_ATTEMPTS:
            print(f"\n  ⚠️  Max attempts ({MAX_ATTEMPTS}) reached.")
            print(f"  Shipping with cover_quality: degraded")
            print(f"  QC issues: {'; '.join(issues[:3])}")
            return

        # Refine prompt for next attempt
        print(f"  Refining prompt via Opus 4.7...")
        prompt = refine_prompt(args.title, prompt, issues, fixes)
        print(f"  New prompt: {prompt[:100]}...")

    print(f"\n✅ Stage 2 complete (cover_quality: degraded)")


if __name__ == "__main__":
    main()
