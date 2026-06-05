#!/usr/bin/env python3
"""Image Renderer — generates custom charts/illustrations via nanobanana (OpenRouter).

For charts and illustrations beyond matplotlib capability.

Usage:
    python3 scripts/render_image.py --prompt "Chart showing semiconductor supply chain flow" --output path/to/image.png
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def render_image(
    prompt: str,
    output_path: str,
    model: str = "nanobanana/image-gen",
    width: int = 1024,
    height: int = 768,
) -> dict:
    """
    Generate an image via OpenRouter.

    Args:
        prompt: Image generation prompt
        output_path: Path for output image
        model: OpenRouter model for image generation
        width: Image width
        height: Image height

    Returns:
        dict with output_path, model, estimated_cost
    """
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print("[image] OPENROUTER_API_KEY not set — cannot generate images")
        return {"output_path": "", "error": "OPENROUTER_API_KEY not set"}

    payload = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": f"{width}x{height}",
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/images/generations",
        data=data,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())

        # Extract image URL and download
        images = result.get("data", [])
        if images and "url" in images[0]:
            img_url = images[0]["url"]
            urllib.request.urlretrieve(img_url, output_path)
            return {
                "output_path": output_path,
                "model": model,
                "estimated_cost": 0.04,
            }
        elif images and "b64_json" in images[0]:
            import base64
            img_data = base64.b64decode(images[0]["b64_json"])
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(img_data)
            return {
                "output_path": output_path,
                "model": model,
                "estimated_cost": 0.04,
            }
        else:
            return {"output_path": "", "error": "No image in response"}

    except Exception as e:
        print(f"[image] Error: {e}")
        return {"output_path": "", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Generate images via OpenRouter")
    parser.add_argument("--prompt", required=True, help="Image generation prompt")
    parser.add_argument("--output", required=True, help="Output image path")
    parser.add_argument("--model", default="nanobanana/image-gen", help="Model to use")
    parser.add_argument("--width", type=int, default=1024, help="Image width")
    parser.add_argument("--height", type=int, default=768, help="Image height")
    args = parser.parse_args()

    result = render_image(args.prompt, args.output, args.model, args.width, args.height)
    if result.get("output_path"):
        print(f"Generated: {result['output_path']}")
    else:
        print(f"Failed: {result.get('error', 'unknown')}")


if __name__ == "__main__":
    main()
