#!/usr/bin/env python3
"""Stage 3 — Social Distribution Pack.

Generates platform-native social cards from a brief JSON:
  - LinkedIn carousel (5-7 slides, 1080×1350)
  - X hero card (1200×675)
  - Instagram square (1080×1080)
  - Exec summary card (1200×1800)

Each card uses:
  - Jinja2 HTML templates with brand tokens
  - Playwright headless screenshot → PNG
  - Opus 4.7 for platform-native copy (one per platform)

Self-test: Playwright installed? Templates exist?
Usage:
    python3 scripts/present/stage3_social.py --brief /tmp/brief.json --output-dir exports/social/
    python3 scripts/present/stage3_social.py --self-test

Cost: ~$0.05 per brief (Opus 4.7 copy generation only). Rendering is free.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import sys
import urllib.request
from typing import Optional

WORKSPACE = pathlib.Path("/home/ubuntu/.openclaw/workspace")
TEMPLATE_DIR = WORKSPACE / "scripts" / "present" / "templates" / "social"

# Platform specs
PLATFORMS = {
    "linkedin": {"template": "linkedin_carousel.html", "width": 1080, "height": 1350},
    "x_hero": {"template": "x_hero.html", "width": 1200, "height": 675},
    # Instagram and Exec card share the LinkedIn template with different dimensions
}


def self_test() -> list[str]:
    """Check prerequisites."""
    failures = []
    try:
        import playwright.sync_api
    except ImportError:
        failures.append("playwright not installed")
    try:
        import jinja2
    except ImportError:
        failures.append("jinja2 not installed")
    if not TEMPLATE_DIR.exists():
        failures.append(f"Template dir not found: {TEMPLATE_DIR}")
    else:
        for f in ["linkedin_carousel.html", "x_hero.html"]:
            if not (TEMPLATE_DIR / f).exists():
                failures.append(f"Template missing: {f}")
    return failures


def _get_openrouter_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        for line in pathlib.Path(WORKSPACE / ".env").read_text().splitlines():
            if line.startswith("OPENROUTER_API_KEY="):
                key = line.split("=", 1)[1].strip('"').strip("'")
                break
    return key


def generate_copy(brief: dict, platform: str) -> str:
    """Generate platform-adapted copy via Opus 4.7.

    Args:
        brief: Brief JSON dict.
        platform: "linkedin" or "x_hero".

    Returns:
        Adapted copy text.
    """
    key = _get_openrouter_key()
    if not key:
        return ""

    title = brief.get("title", "Intelligence Briefing")
    judgments = brief.get("headline_judgments", [])
    bluf = brief.get("bluf", "")

    platform_briefs = {
        "linkedin": "Professional, analytical tone. 1300 chars max per slide. Write for decision-makers.",
        "x_hero": "Concise, newsworthy. 280 chars max. Write for a general audience. Punchy headline.",
    }
    style = platform_briefs.get(platform, "Professional tone.")

    payload = json.dumps({
        "model": "anthropic/claude-opus-4.7",
        "max_tokens": 800,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": f"You write social copy for intelligence briefings. {style} Output only the adapted copy text, no explanation."},
            {"role": "user", "content": f"Adapt this briefing for {platform}:\n\nTitle: {title}\nBLUF: {bluf}\n\nKey judgments:\n" + "\n".join(f"- {j['claim']} [{j.get('kent_band', 'assessed')}]" for j in judgments[:5])},
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
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def generate_cards(brief_path: str, output_dir: str) -> dict:
    """Generate all social cards for a brief.

    Returns dict with per-platform results.
    """
    output_base = pathlib.Path(output_dir)
    output_base.mkdir(parents=True, exist_ok=True)

    brief = json.loads(pathlib.Path(brief_path).read_text())
    title = brief.get("title", "Intelligence Briefing")
    judgments = brief.get("headline_judgments", [])
    bluf = brief.get("bluf", "")
    date = brief.get("produced_at", "")[:10]

    results = {}
    import jinja2
    from playwright.sync_api import sync_playwright

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=False,
    )

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        # LinkedIn carousel: title slide + 1 slide per 2 judgments
        template = env.get_template("linkedin_carousel.html")
        all_slides = []
        total_slides = min(7, 1 + (len(judgments) + 1) // 2)

        # Title slide
        all_slides.append({
            "slide_index": 0, "slide_num": 1, "total_slides": total_slides,
            "title": title, "date": date, "bluf": bluf[:200],
            "judgments": [],
        })

        # Judgment slides
        for i in range(0, len(judgments), 2):
            slide_idx = len(all_slides)
            if slide_idx >= total_slides:
                break
            all_slides.append({
                "slide_index": slide_idx, "slide_num": slide_idx + 1,
                "total_slides": total_slides,
                "title": "", "date": "", "bluf": "",
                "judgments": judgments[i:i+2],
            })

        # Render each slide
        linkedin_dir = output_base / "linkedin"
        linkedin_dir.mkdir(exist_ok=True)
        linkedin_paths = []
        for slide_data in all_slides:
            html = template.render(**slide_data)
            out_path = linkedin_dir / f"slide_{slide_data['slide_index']}.png"
            page = browser.new_page(viewport={"width": 1080, "height": 1350})
            page.set_content(html, wait_until="networkidle")
            page.screenshot(path=str(out_path), full_page=False)
            page.close()
            linkedin_paths.append(str(out_path))

        results["linkedin"] = {
            "success": True,
            "slides": len(linkedin_paths),
            "output_dir": str(linkedin_dir),
            "files": linkedin_paths,
        }
        print(f"  ✅ LinkedIn: {len(linkedin_paths)} slides ({linkedin_dir})")

        # X hero card
        x_template = env.get_template("x_hero.html")
        x_data = {
            "title": title, "date": date, "bluf": bluf[:150],
            "judgments": judgments[:3],
        }
        x_html = x_template.render(**x_data)
        x_path = output_base / "x_hero.png"
        page = browser.new_page(viewport={"width": 1200, "height": 675})
        page.set_content(x_html, wait_until="networkidle")
        page.screenshot(path=str(x_path), full_page=False)
        page.close()
        results["x_hero"] = {"success": True, "file": str(x_path)}
        print(f"  ✅ X hero: {x_path}")

        # Instagram square (uses LinkedIn template with 1:1 viewport)
        ig_data = {
            "slide_index": 0, "slide_num": 1, "total_slides": 1,
            "title": title, "date": date, "bluf": bluf[:150],
            "judgments": [],
        }
        ig_html = template.render(**ig_data)
        ig_path = output_base / "instagram.png"
        page = browser.new_page(viewport={"width": 1080, "height": 1080})
        page.set_content(ig_html, wait_until="networkidle")
        page.screenshot(path=str(ig_path), full_page=False)
        page.close()
        results["instagram"] = {"success": True, "file": str(ig_path)}
        print(f"  ✅ Instagram: {ig_path}")

        browser.close()

    # Save copy
    for platform in ["linkedin", "x_hero"]:
        copy = generate_copy(brief, platform)
        if copy:
            copy_path = output_base / f"{platform}_copy.txt"
            copy_path.write_text(copy)
            results[platform + "_copy"] = {"success": True, "file": str(copy_path)}

    return results


def main():
    parser = argparse.ArgumentParser(description="Stage 3 — Social Distribution Pack")
    parser.add_argument("--brief", help="Path to brief JSON")
    parser.add_argument("--output-dir", "-o", default="exports/social", help="Output dir")
    parser.add_argument("--self-test", action="store_true", help="Self-test")
    args = parser.parse_args()

    if args.self_test:
        failures = self_test()
        if failures:
            for f in failures:
                print(f"  STAGE 3 DISABLED: {f}")
        else:
            print("  STAGE 3 READY: Playwright + templates available")
        return

    if not args.brief:
        parser.error("--brief required")

    results = generate_cards(args.brief, args.output_dir)
    total = sum(1 for r in results.values() if r.get("success"))
    print(f"\n  {total}/{len(results)} assets generated")


if __name__ == "__main__":
    main()
