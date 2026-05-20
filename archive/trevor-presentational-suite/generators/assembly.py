"""TPS FFmpeg Assembly — combine media assets into composed video.

Handles:
  - Concatenating video clips
  - Overlaying audio (narration, music) on video
  - Adding title cards and transitions
  - Producing final MP4 output
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Optional

from core.exceptions import GeneratorError


@dataclass
class MediaSegment:
    """A segment of media to include in the assembly."""
    path: str
    media_type: str  # "video", "audio", "image"
    duration_sec: Optional[float] = None  # For images/stills
    label: str = ""


@dataclass
class AssemblySpec:
    """Specification for assembling a video."""
    segments: list[MediaSegment] = field(default_factory=list)
    background_audio: Optional[str] = None
    narration_audio: Optional[str] = None
    output_width: int = 1920
    output_height: int = 1080
    fps: int = 30
    background_color: str = "0x0f3460"


def is_available() -> bool:
    """Check if FFmpeg is installed."""
    return shutil.which("ffmpeg") is not None


def create_title_card(
    text: str,
    output_path: str,
    duration_sec: float = 5.0,
    width: int = 1920,
    height: int = 1080,
    bg_color: str = "0x0f3460",
    font_color: str = "white",
    font_size: int = 48,
) -> str:
    """Create a title card video using FFmpeg."""
    if not is_available():
        raise GeneratorError("FFmpeg not installed")

    # Use lavfi to generate a color background with text
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={bg_color}:s={width}x{height}:d={duration_sec}:r=30",
        "-vf", (
            f"drawtext=text='{text}'"
            f":fontcolor={font_color}"
            f":fontsize={font_size}"
            f":x=(w-text_w)/2"
            f":y=(h-text_h)/2"
            f":font=sans"
        ),
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise GeneratorError(f"FFmpeg title card failed: {result.stderr[:500]}")

    return output_path


def image_to_video(
    image_path: str,
    output_path: str,
    duration_sec: float = 5.0,
    width: int = 1920,
    height: int = 1080,
) -> str:
    """Convert a still image to a video clip with optional Ken Burns effect."""
    if not is_available():
        raise GeneratorError("FFmpeg not installed")

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-c:v", "libx264",
        "-t", str(duration_sec),
        "-pix_fmt", "yuv420p",
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:-1:-1:color=0x0f3460",
        "-r", "30",
        "-preset", "fast",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise GeneratorError(f"FFmpeg image_to_video failed: {result.stderr[:500]}")

    return output_path


def concatenate_videos(
    video_paths: list[str],
    output_path: str,
) -> str:
    """Concatenate multiple video clips into one."""
    if not is_available():
        raise GeneratorError("FFmpeg not installed")

    if not video_paths:
        raise GeneratorError("No videos to concatenate")

    # Create concat file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        for path in video_paths:
            f.write(f"file '{os.path.abspath(path)}'\n")
        concat_file = f.name

    try:
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise GeneratorError(f"FFmpeg concat failed: {result.stderr[:500]}")
    finally:
        os.unlink(concat_file)

    return output_path


def mix_audio(
    video_path: str,
    narration_path: Optional[str],
    music_path: Optional[str],
    output_path: str,
    music_volume: float = 0.15,
    narration_volume: float = 1.0,
) -> str:
    """Mix narration and background music onto a video."""
    if not is_available():
        raise GeneratorError("FFmpeg not installed")

    inputs = ["-i", video_path]
    filter_parts = []
    audio_count = 0

    if narration_path:
        inputs.extend(["-i", narration_path])
        audio_count += 1
        filter_parts.append(f"[{audio_count}]volume={narration_volume}[narr]")

    if music_path:
        inputs.extend(["-i", music_path])
        audio_count += 1
        filter_parts.append(f"[{audio_count}]volume={music_volume}[music]")

    if not filter_parts:
        # No audio to mix, just copy
        cmd = ["ffmpeg", "-y", "-i", video_path, "-c", "copy", output_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise GeneratorError(f"FFmpeg copy failed: {result.stderr[:500]}")
        return output_path

    # Build amix filter
    if narration_path and music_path:
        filter_complex = (
            f"[1]volume={narration_volume}[narr];"
            f"[2]volume={music_volume}[music];"
            f"[narr][music]amix=inputs=2:duration=first[aout]"
        )
    elif narration_path:
        filter_complex = f"[1]volume={narration_volume}[aout]"
    else:
        filter_complex = f"[1]volume={music_volume}[aout]"

    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        raise GeneratorError(f"FFmpeg mix_audio failed: {result.stderr[:500]}")

    return output_path


def assemble(spec: AssemblySpec, output_path: str) -> str:
    """Full assembly pipeline: segments → concat → audio mix → output.

    1. Convert images to video clips
    2. Concatenate all video segments
    3. Mix narration and background music
    4. Output final MP4
    """
    if not is_available():
        raise GeneratorError("FFmpeg not installed")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        video_clips = []

        for i, seg in enumerate(spec.segments):
            if seg.media_type == "video" and os.path.exists(seg.path):
                video_clips.append(seg.path)
            elif seg.media_type == "image" and os.path.exists(seg.path):
                clip_path = os.path.join(tmpdir, f"clip_{i}.mp4")
                image_to_video(
                    seg.path, clip_path,
                    duration_sec=seg.duration_sec or 5.0,
                    width=spec.output_width,
                    height=spec.output_height,
                )
                video_clips.append(clip_path)

        if not video_clips:
            raise GeneratorError("No valid video segments to assemble")

        # Concatenate
        if len(video_clips) == 1:
            concat_path = video_clips[0]
        else:
            concat_path = os.path.join(tmpdir, "concat.mp4")
            concatenate_videos(video_clips, concat_path)

        # Mix audio
        if spec.narration_audio or spec.background_audio:
            mix_audio(
                concat_path,
                spec.narration_audio,
                spec.background_audio,
                output_path,
            )
        else:
            shutil.copy2(concat_path, output_path)

    return output_path
