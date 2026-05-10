#!/usr/bin/env python3
"""
generate_brief_images.py — Generate context-relevant imagery for each brief section.

Reads theatre analysis JSONs, builds thematic prompts from the narrative,
calls GenViral Studio AI for each, and writes a mapping JSON:
  { "europe": { "url": "https://...", "prompt": "..." }, ... }

Usage:
    python3 generate_brief_images.py \\
        --working-dir ~/trevor-briefings/2026-05-09 \\
        --out-json ~/trevor-briefings/2026-05-09/visuals/section-images.json

Requires: GENVIRAL_API_KEY in environment
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys
import time
import datetime

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
GENVIRAL_SCRIPT = REPO / "skills" / "genviral" / "scripts" / "genviral.sh"

# Model choice: best quality for photorealistic intelligence imagery
IMAGE_MODEL = "google/nano-banana-2"  # 1 credit, fast, photorealistic

# Prompt themes per region — these get refined with narrative content
REGION_PROMPT_THEMES = {
    "europe": {
        "style": "photorealistic documentary photography, intelligence briefing aesthetic, muted colors, professional",
        "subjects": [
            "military convoy on a foggy European highway",
            "drone silhouette against a dawn sky over eastern European plains",
            "sandbags and military vehicles at a checkpoint, snow-covered ground",
        ],
    },
    "asia": {
        "style": "photorealistic, diplomatic briefing aesthetic, clean composition, professional lighting",
        "subjects": [
            "diplomatic meeting room with flags, mahogany table, empty chairs",
            "satellite view of a strategic strait, calm waters, cargo ships",
            "government building facade at golden hour, security barriers",
        ],
    },
    "middle_east": {
        "style": "photorealistic, documentary photography, intelligence briefing, muted warm tones",
        "subjects": [
            "aerial view of a strategic strait with oil tanker and naval vessel",
            "desert horizon at dusk with oil refinery silhouettes",
            "diplomatic compound interior, empty negotiation table with two flags",
        ],
    },
    "north_america": {
        "style": "photorealistic, documentary photography, clean composition, professional",
        "subjects": [
            "US Capitol building at twilight, floodlit, security perimeter visible",
            "border crossing infrastructure, desert landscape, dawn light",
            "Pentagon building aerial view, overcast sky, documentary style",
        ],
    },
    "south_central_america": {
        "style": "photorealistic documentary photography, warm tones, professional briefing aesthetic",
        "subjects": [
            "Havana cityscape at dusk, vintage cars, pastel buildings, power lines",
            "Amazon basin aerial view, deforestation boundary line, documentary",
            "oil refinery in a tropical coastal setting, storage tanks, sunset",
        ],
    },
    "global_finance": {
        "style": "photorealistic, financial documentary style, clean modernist, cool blue tones",
        "subjects": [
            "trading floor screens showing oil futures charts, blurred motion",
            "abstract financial data visualization, glowing graphs on dark background",
            "shipping containers at a major port, aerial view, logistics infrastructure",
        ],
    },
    "africa": {
        "style": "photorealistic documentary photography, warm golden hour light, professional",
        "subjects": [
            "Sahel landscape, desert outpost, military vehicle, documentary style",
            "mining operation aerial view, red earth, heavy machinery",
        ],
    },
    "sahel": {
        "style": "photorealistic documentary photography, warm tones, intelligence briefing",
        "subjects": [
            "desert military outpost, sand-colored buildings, flag at half staff",
            "Sahel landscape, dust storm on horizon, solitary road",
        ],
    },
}

# Cover image theme
COVER_THEMES = [
    "aerial photograph of planet Earth at night, city lights visible across continents, deep space background, cinematic lighting, intelligence briefing aesthetic, highly detailed, 8K",
    "satellite view of a geopolitical flashpoint region, grid lines and coordinates overlay, intelligence operations center aesthetic, dark background",
    "global network visualization, interconnected data points across world map, dark navy background, gold accent lighting, professional intelligence briefing",
]


def load_json(path):
    with open(path) as f:
        return json.load(f)


def extract_keywords(region: str, narrative: str, judgments: list) -> tuple[str, str]:
    """Extract the main topic and a specific detail from analysis content."""
    # Extract first location/entity mentioned
    entities = []
    for line in narrative.split(". ")[:3]:
        words = line.split()
        for w in words:
            if w[0].isupper() and len(w) > 3 and w not in ("The", "This", "That", "These", "Those", "However", "While", "Although", "Because", "Therefore", "Meanwhile", "Additionally", "Consequently"):
                entities.append(w)
                if len(entities) >= 3:
                    break
        if len(entities) >= 3:
            break

    entity_str = ", ".join(entities[:3]) if entities else region.replace("_", " ").title()

    # Get a key judgment for the "what's happening" context
    key_judgment = ""
    if judgments:
        kj = judgments[0]
        stmt = kj.get("statement", "")
        if stmt:
            key_judgment = stmt[:150]

    return entity_str, key_judgment


def generate_image(prompt: str, region: str, model: str = IMAGE_MODEL) -> str | None:
    """Generate an image via GenViral Studio AI. Returns the URL or None."""
    aspect = "16:9"
    if region == "cover":
        aspect = "1:1"

    try:
        cmd = [
            "bash", str(GENVIRAL_SCRIPT), "studio-generate-image",
            "--model-id", model,
            "--prompt", prompt,
            "--aspect-ratio", aspect,
        ]
        # Get API key from environment
        api_key = os.environ.get("GENVIRAL_API_KEY", "")
        if not api_key:
            env_path = REPO / ".env"
            if env_path.exists():
                for line in env_path.read_text().splitlines():
                    if "GENVIRAL_API_KEY" in line and "=" in line:
                        api_key = line.split("=", 1)[1].strip().strip("'\"")
                        break

        print(f"    Generating image (model={model}, ratio={aspect})...", flush=True)
        sys.stdout.flush()
        
        env = {**os.environ, "GENVIRAL_API_KEY": api_key}
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
            env=env,
        )

        if result.returncode != 0:
            print(f"    ⚠ GenViral error (rc={result.returncode}): {result.stderr[:200]}", flush=True)
            return None

        output = result.stdout
        json_start = output.find("{")
        if json_start >= 0:
            json_str = output[json_start:]
            try:
                data = json.loads(json_str)
                url = data.get("output_url", "")
                if url:
                    return url
            except json.JSONDecodeError:
                pass

        import re
        match = re.search(r'"output_url":\s*"([^"]+)"', output)
        if match:
            return match.group(1)
        match = re.search(r'"preview_url":\s*"([^"]+)"', output)
        if match:
            return match.group(1)

        print(f"    ⚠ Could not extract URL from response", flush=True)
        return None

    except subprocess.TimeoutExpired:
        print(f"    ⚠ GenViral timeout after 120s", flush=True)
        return None
    except Exception as e:
        print(f"    ⚠ Image generation error: {e}", flush=True)
        return None


def build_prompt(region: str, narrative: str, judgments: list, theme: dict) -> str:
    """Build a context-aware image prompt from analysis content."""
    entity_str, key_judgment = extract_keywords(region, narrative, judgments)
    style = theme.get("style", "photorealistic documentary")
    # Pick the most relevant subject based on narrative keywords
    subjects = theme.get("subjects", [])
    best_subject = subjects[0]

    # Try to match a subject based on narrative content
    narrative_lower = narrative.lower()
    for subject in subjects:
        keywords = subject.lower().split()
        matches = sum(1 for k in keywords if len(k) > 4 and k in narrative_lower)
        if matches >= 2:
            best_subject = subject
            break

    prompt = f"{best_subject}. {style}. Intelligence briefing context: {entity_str}. {key_judgment[:100]}."
    return prompt[:500]  # Keep under length limits


def main():
    parser = argparse.ArgumentParser(description="Generate section images via GenViral Studio AI")
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--skip-existing", action="store_true", help="Skip if output already exists")
    args = parser.parse_args()

    out_path = pathlib.Path(args.out_json).expanduser()
    if args.skip_existing and out_path.exists():
        print(f"Output already exists, skipping: {out_path}")
        return

    wd = pathlib.Path(args.working_dir).expanduser()
    ad = wd / "analysis"

    if not GENVIRAL_SCRIPT.exists():
        print(f"ERROR: genviral.sh not found at {GENVIRAL_SCRIPT}")
        sys.exit(1)

    if not os.environ.get("GENVIRAL_API_KEY"):
        print("ERROR: GENVIRAL_API_KEY not set")
        sys.exit(1)

    print(f"=== Generate Section Images — {datetime.datetime.now().isoformat()} ===", flush=True)
    print(f"Model: {IMAGE_MODEL}", flush=True)
    print(f"Working dir: {wd}", flush=True)

    # ── Generate cover image ──
    results = {}
    print("\n── Cover Image ──")
    import random
    cover_prompt = COVER_THEMES[hash(str(datetime.date.today())) % len(COVER_THEMES)]
    print(f"  Prompt: {cover_prompt[:80]}...")
    cover_url = generate_image(cover_prompt, "cover")
    if cover_url:
        results["cover"] = {"url": cover_url, "prompt": cover_prompt}
        print(f"  ✅ Cover: {cover_url[:60]}...")
    else:
        print(f"  ⚠ Cover image failed")
    time.sleep(2)

    # ── Generate section images ──
    region_order = ["europe", "asia", "middle_east", "north_america", "south_central_america", "global_finance"]
    for region in region_order:
        rpath = ad / f"{region}.json"
        if not rpath.exists():
            print(f"\n── {region} — no analysis file, skipping")
            continue

        t = load_json(rpath)
        narrative = t.get("narrative", "")
        judgments = t.get("key_judgments", [])
        theme = REGION_PROMPT_THEMES.get(region, REGION_PROMPT_THEMES["europe"])

        prompt = build_prompt(region, narrative, judgments, theme)
        print(f"\n── {region} ──")
        print(f"  Prompt: {prompt[:120]}...")

        url = generate_image(prompt, region)
        if url:
            results[region] = {"url": url, "prompt": prompt}
            print(f"  ✅ Image: {url[:60]}...")
        else:
            print(f"  ⚠ Failed")
            results[region] = {"url": "", "prompt": prompt}

        time.sleep(1)  # Brief pause between generations

    # ── Save results ──
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Saved {len(results)} image references to {out_path}")

    successes = sum(1 for v in results.values() if v.get("url"))
    failures = len(results) - successes
    print(f"   {successes} succeeded, {failures} failed")


if __name__ == "__main__":
    main()
