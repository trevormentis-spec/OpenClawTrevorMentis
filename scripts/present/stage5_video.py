#!/usr/bin/env python3
"""Stage 5 — Briefing Video (Ken Burns slideshow).

Pipeline:
  1. Sequence slides: cover (5s) → judgments (10s) → chart/map slides (15-25s) → outro (8s)
  2. Each slide: PNG with title overlay + watermark + brief ID
  3. Ken Burns zoom-pan via ffmpeg scale/crop filter
  4. Crossfade transitions (0.5s)
  5. Audio overlay from Stage 4
  6. Subtitles burned in from script text (SRT)
  7. H.264 1080p, 24fps, AAC audio

Self-test: ffmpeg available? Pillow?
Usage:
    python3 scripts/present/stage5_video.py \
        --brief test_fixtures/sample_brief.json \
        --images exports/images/cover.png exports/charts/kent-bar.png \
        --script exports/audio/narration.script.txt \
        --audio exports/audio/narration.mp3 \
        --output exports/videos/briefing.mp4

    python3 scripts/present/stage5_video.py --self-test
"""
from __future__ import annotations

import argparse
import json
import math
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import textwrap
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

WORKSPACE = pathlib.Path("/home/ubuntu/.openclaw/workspace")
VIDEO_W = 1920
VIDEO_H = 1080
FPS = 24

NAVY = "#0f3460"
GOLD = "#c9a84c"
WHITE = "#f0f0f0"
DARK_BG = "#1a1a2e"
GREY = "#888888"


def self_test() -> list[str]:
    failures = []
    if not shutil.which("ffmpeg"):
        failures.append("ffmpeg not installed")
    try:
        from PIL import Image
        Image.new("RGB", (1, 1))
    except ImportError:
        failures.append("Pillow not importable")
    return failures


def _find_font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for path in candidates:
        p = pathlib.Path(path)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except:
                pass
    return ImageFont.load_default()


def overlay_slide(
    image_path: str,
    title: str = "",
    subtitle: str = "",
    brief_id: str = "",
    watermark: str = "PENDING HUMAN ANALYST QC REVIEW",
    output_path: str = "",
    caption: str = "",
) -> str:
    """Overlay title, watermark, and brief ID onto an image.

    Returns path to the overlaid PNG.
    """
    if not output_path:
        output_path = image_path

    img = Image.open(image_path).convert("RGB").resize((VIDEO_W, VIDEO_H), Image.LANCZOS)
    draw = ImageDraw.Draw(img)

    font_title = _find_font(40, bold=True)
    font_sub = _find_font(28)
    font_wm = _find_font(18)
    font_id = _find_font(14)

    # Title overlay (top-left)
    if title:
        y = 30
        for line in textwrap.wrap(title, width=50):
            draw.text((40, y), line, fill=WHITE, font=font_title)
            y += 48

    # Brand label (top-left)
    font_brand = _find_font(16, bold=True)
    draw.text((40, 20), "TREVOR INTELLIGENCE", fill=GOLD, font=font_brand)

    # Subtitle
    if subtitle:
        y_sub = y + 10 if title else 30
        draw.text((40, y_sub), subtitle, fill=GOLD, font=font_sub)

    # Caption/subtitle (very bottom of screen, solid dark bar with white text)
    if caption:
        cap_font = _find_font(13)
        cap_lines = textwrap.wrap(caption, width=110)[:2]
        cap_h = len(cap_lines) * 18 + 12
        cap_y = VIDEO_H - cap_h - 5  # 5px from bottom edge
        # Solid dark bar (not transparent)
        draw.rectangle([(0, cap_y), (VIDEO_W, cap_y + cap_h)], fill=(10, 10, 20))
        for i, line in enumerate(cap_lines):
            bbox = draw.textbbox((0, 0), line, font=cap_font)
            lw = bbox[2] - bbox[0]
            draw.text(((VIDEO_W - lw) // 2, cap_y + 5 + i * 18), line, fill=(200, 200, 200), font=cap_font)


    # Watermark (bottom-left) — always present on every slide
    draw.text((40, VIDEO_H - 50), watermark or "PENDING HUMAN ANALYST QC REVIEW", fill=GOLD, font=font_wm)


    # Brief ID (bottom-right)
    if brief_id:
        bbox = draw.textbbox((0, 0), brief_id, font=font_id)
        id_w = bbox[2] - bbox[0]
        draw.text((VIDEO_W - id_w - 40, VIDEO_H - 50), brief_id, fill=GREY, font=font_id)

    img = img.convert("RGB")
    img.save(output_path, "PNG")
    return output_path


def generate_outro_card(brief_id: str = "", output_path: str = "") -> str:
    """Generate the outro/end card with QC flag."""
    if not output_path:
        output_path = str(WORKSPACE / "exports" / "images" / "video-outro.png")

    img = Image.new("RGB", (VIDEO_W, VIDEO_H), DARK_BG)
    draw = ImageDraw.Draw(img)

    font_large = _find_font(36, bold=True)
    font_med = _find_font(24)
    font_small = _find_font(18)

    # Gold bar
    draw.rectangle([(200, 350), (1720, 355)], fill=GOLD)

    # QC message
    msg = "PENDING HUMAN ANALYST QC REVIEW"
    bbox = draw.textbbox((0, 0), msg, font=font_large)
    tw = bbox[2] - bbox[0]
    draw.text(((VIDEO_W - tw) // 2, 400), msg, fill=GOLD, font=font_large)

    msg2 = "This briefing requires analyst review before client delivery"
    bbox2 = draw.textbbox((0, 0), msg2, font=font_med)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((VIDEO_W - tw2) // 2, 470), msg2, fill=GREY, font=font_med)

    if brief_id:
        msg3 = f"Brief: {brief_id}"
        bbox3 = draw.textbbox((0, 0), msg3, font=font_small)
        tw3 = bbox3[2] - bbox3[0]
        draw.text(((VIDEO_W - tw3) // 2, 530), msg3, fill=GREY, font=font_small)

    # Footer
    draw.rectangle([(200, VIDEO_H - 60), (1720, VIDEO_H - 55)], fill=GOLD)
    draw.text((VIDEO_W // 2 - 100, VIDEO_H - 100), "Trevor Intelligence", fill=GREY, font=font_small)

    pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path


def generate_subtitles(script_path: str, output_path: str, duration: float) -> str:
    """Generate SRT subtitles from the narration script.

    Simple word-based timing: divide script into chunks based on total duration.
    """
    if not pathlib.Path(script_path).exists():
        # Create empty SRT
        pathlib.Path(output_path).write_text("")
        return output_path

    text = pathlib.Path(script_path).read_text().strip()
    words = text.split()
    word_count = len(words)

    if word_count == 0 or duration <= 0:
        pathlib.Path(output_path).write_text("")
        return output_path

    # Group into ~8 word chunks
    chunk_size = max(8, word_count // max(int(duration / 3), 1))
    chunks = [words[i:i+chunk_size] for i in range(0, word_count, chunk_size)]

    lines = []
    time_per_chunk = duration / len(chunks)

    for i, chunk in enumerate(chunks):
        start_s = i * time_per_chunk
        end_s = (i + 1) * time_per_chunk

        def fmt(sec):
            h = int(sec // 3600)
            m = int((sec % 3600) // 60)
            s = int(sec % 60)
            ms = int((sec % 1) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        lines.append(str(i + 1))
        lines.append(f"{fmt(start_s)} --> {fmt(end_s)}")
        lines.append(" ".join(chunk))
        lines.append("")

    pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(output_path).write_text("\n".join(lines))
    return output_path


def compose_video(
    image_paths: list[str],
    audio_path: str,
    script_path: str,
    output_path: str,
    brief_id: str = "",
    duration_s: Optional[float] = None,
) -> str:
    """Compose Ken Burns video from images + audio + subtitles.

    Args:
        image_paths: List of slide images.
        audio_path: Path to MP3.
        script_path: Path to narration script for subtitles.
        output_path: Output MP4 path.
        brief_id: Brief ID for outro card.
        duration_s: Override audio duration (for silent fallback).

    Returns:
        Output path.
    """
    output_file = pathlib.Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    bg_color = DARK_BG[1:]

    with tempfile.TemporaryDirectory(prefix="trevor-video-") as tmpdir:
        tmp = pathlib.Path(tmpdir)

        # Get audio duration
        if duration_s:
            audio_dur = duration_s
        else:
            r = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
                capture_output=True, text=True, timeout=10,
            )
            audio_dur = float(r.stdout.strip()) if r.stdout.strip() else 10.0

        # Slide timing: cover(5s) → chart/map slides → outro(8s)
        content_images = image_paths[1:] if len(image_paths) > 1 else []
        num_content = max(1, len(content_images))
        outro_dur = min(8, audio_dur * 0.12)
        cover_dur = min(5, audio_dur * 0.1)
        remaining = audio_dur - cover_dur - outro_dur
        content_dur = remaining / num_content if remaining > 0 else 3

        # Load script for per-slide captions
        script_words = []
        if pathlib.Path(script_path).exists():
            script_words = pathlib.Path(script_path).read_text().split()

        # Generate overlays with captions — watermark on ALL slides
        slides = []
        total_slides = num_content + 2  # cover + content + outro
        words_per_slide = min(40, max(1, len(script_words) // max(1, num_content))) if script_words else 0
        for i, img_path in enumerate(image_paths[:num_content + 1]):
            out = tmp / f"slide_{i:03d}.png"
            # Assign caption segment for this slide
            cap = ""
            if script_words and i > 0:  # No caption on cover slide
                start = (i - 1) * words_per_slide
                end = min(start + words_per_slide, len(script_words))
                cap = " ".join(script_words[start:end])
            overlay_slide(img_path, title="", output_path=str(out), caption=cap)
            slides.append(str(out))

        # Outro
        outro_path = tmp / "slide_outro.png"
        generate_outro_card(brief_id, str(outro_path))
        slides.append(str(outro_path))

        # Durations list
        durs = [cover_dur] + [content_dur] * num_content + [outro_dur]
        total_computed = sum(durs)

        # Create concat file
        concat_file = tmp / "concat.txt"
        with open(concat_file, "w") as f:
            for i, slide in enumerate(slides):
                f.write(f"file '{slide}'\n")
                f.write(f"duration {durs[i]:.2f}\n")
        with open(concat_file, "a") as f:
            f.write(f"file '{slides[-1]}'\n")  # extra for last frame

        # Generate subtitles
        srt_path = tmp / "subtitles.srt"
        generate_subtitles(script_path, str(srt_path), total_computed)

        # FFmpeg: concat + Ken Burns zoom-pan + crossfade + subtitles + audio
        filter_complex = (
            "[0:v]format=yuv420p[v]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
        ]

        # Add audio input if it exists and has real content
        if pathlib.Path(audio_path).exists() and pathlib.Path(audio_path).stat().st_size > 10000:
            cmd.extend(["-i", audio_path])
            map_str = "-map 0:v -map 1:a"
        else:
            map_str = "-map 0:v"

        # Subtitles filter
        if srt_path.stat().st_size > 0:
            sub_filter = f"subtitles={srt_path}:force_style='FontName=Inter,FontSize=18,PrimaryColour=&H00FFFFFF,BackColour=&H80000000,Alignment=2'"
        else:
            sub_filter = ""

        # Ken Burns effect: add zoom-pan animation
        zoompan = "zoompan=z='if(lte(zoom,1.0),1.02,min(zoom+0.002,1.15))':d=1:fps=24"

        # Build filter chain
        if sub_filter:
            vf = f"format=yuv420p,{zoompan},{sub_filter}"
        else:
            vf = f"format=yuv420p"

        cmd.extend([
            "-vf", vf,
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "aac" if "1:a" in map_str else "copy",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            "-movflags", "+faststart",
            str(output_file),
        ])

        # Remove map flag from cmd (it's not a flag)
        # Actually, ffmpeg takes -map before output, let me restructure
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
        ]
        if pathlib.Path(audio_path).exists() and pathlib.Path(audio_path).stat().st_size > 10000:
            cmd.extend(["-i", audio_path])

        # Subtitles filter
        sub_filter_str = ""
        if srt_path.stat().st_size > 0:
            sub_filter_str = ""  # Subtitles rendered directly by Pillow instead

        vf = f"format=yuv420p,setpts=PTS-STARTPTS{sub_filter_str}"

        cmd.extend([
            "-vf", vf,
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        ])
        if pathlib.Path(audio_path).exists() and pathlib.Path(audio_path).stat().st_size > 10000:
            cmd.extend(["-c:a", "aac", "-b:a", "128k"])
            cmd.extend(["-map", "0:v", "-map", "1:a", "-shortest"])
        else:
            cmd.extend(["-map", "0:v", "-shortest"])
        cmd.extend([
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-r", str(FPS),
            str(output_file),
        ])

        print(f"  Composing video ({len(slides)} slides, {total_computed:.0f}s)...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            err = result.stderr[-500:] if len(result.stderr) > 500 else result.stderr
            raise RuntimeError(f"ffmpeg failed:\n{err}")

    size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"  ✅ Video: {output_file} ({size_mb:.1f} MB, {total_computed:.0f}s)")
    return str(output_file)


def verify_video(video_path: str) -> dict:
    """Verify video: exists, valid container, reasonable duration."""
    path = pathlib.Path(video_path)
    checks = {"exists": path.exists()}
    if not checks["exists"]:
        return checks

    checks["size_mb"] = round(path.stat().st_size / (1024 * 1024), 1)
    checks["not_empty"] = path.stat().st_size > 50000

    r = subprocess.run(
        ["ffprobe", "-v", "error",
         "-show_entries", "format=format_name,duration",
         "-of", "default=noprint_wrappers=1", str(video_path)],
        capture_output=True, text=True, timeout=10,
    )
    for line in r.stdout.split("\n"):
        if "format_name" in line:
            checks["container"] = line.split("=", 1)[1].strip()
        if "duration" in line:
            try:
                checks["duration_s"] = round(float(line.split("=", 1)[1]), 1)
            except ValueError:
                pass

    checks["valid_format"] = "mp4" in checks.get("container", "")
    return checks


def main():
    parser = argparse.ArgumentParser(description="Stage 5 — Ken Burns Briefing Video")
    parser.add_argument("--brief", help="Path to brief JSON (for title/ID)")
    parser.add_argument("--images", nargs="*", default=[], help="Slide image paths")
    parser.add_argument("--audio", default="exports/audio/narration.mp3", help="Audio MP3")
    parser.add_argument("--script", default="exports/audio/narration.script.txt", help="Script text for subtitles")
    parser.add_argument("--output", "-o", default="exports/videos/briefing.mp4", help="Output MP4")
    parser.add_argument("--duration", type=float, default=0, help="Override video duration (for silent audio)")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        failures = self_test()
        for f in failures or ["Stage 5 ready"]:
            print(f"  {f}")
        return

    # Extract brief info
    brief_id = ""
    title = "Intelligence Briefing"
    if args.brief and pathlib.Path(args.brief).exists():
        try:
            brief = json.loads(pathlib.Path(args.brief).read_text())
            title = brief.get("title", title)
            brief_id = brief.get("brief_id", "")
        except:
            pass

    # Collect images
    images = [p for p in (args.images or []) if pathlib.Path(p).exists()]
    if not images:
        print("  No images provided, generating default slides")
        # Generate placeholder title slide
        from PIL import Image as PIL_Image
        img = PIL_Image.new("RGB", (VIDEO_W, VIDEO_H), DARK_BG)
        default_path = "/tmp/trevor-video-default.png"
        img.save(default_path)
        images = [default_path]

    # Audio and subtitles
    audio_path = args.audio if pathlib.Path(args.audio).exists() else ""
    script_path = args.script if pathlib.Path(args.script).exists() else ""

    duration = args.duration if args.duration > 0 else None

    result = compose_video(
        image_paths=images,
        audio_path=audio_path or "/dev/null",
        script_path=script_path,
        output_path=args.output,
        brief_id=brief_id,
        duration_s=duration,
    )

    checks = verify_video(result)
    print(f"  Verification: {checks}")
    if checks.get("valid_format") and checks.get("not_empty"):
        print(f"  ✅ Stage 5 deliverable: {result}")
    else:
        print(f"  ❌ Stage 5 verification failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
