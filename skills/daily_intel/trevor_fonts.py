#!/usr/bin/env python3
"""
trevor_fonts.py — Portable font loader with graceful fallback for Trevor.

Strategy:
  1. Look in TREVOR_FONTS_DIR (configurable, default: skills/daily_intel/fonts/)
  2. Fall back to system DejaVu fonts (available on virtually every Linux distro)
  3. Fall back to reportlab's built-in Helvetica/Times/Courier

Auto-downloads missing fonts on first run if internet is available.

Usage:
    from trevor_fonts import register_fonts, get_font_path
    register_fonts()  # called once at module load
    path = get_font_path("Display")  # returns path to best available font
"""
from __future__ import annotations

import os
import sys
import shutil
from pathlib import Path

try:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


# ── Skill root (resolution-neutral) ──
_SCRIPT_DIR = Path(__file__).resolve().parent
_SKILL_ROOT = _SCRIPT_DIR  # we're in skills/daily_intel/

# ── Font paths (env var override, then relative to skill root) ──
FONTS_DIR = Path(os.environ.get("TREVOR_FONTS_DIR", str(_SKILL_ROOT / "fonts")))

# ── Font definitions (name → preferred TTF, weight, style) ──
FONT_DEFS = [
    # Display: Bebas Neue (compact all-caps)
    {"name": "Display", "ttf": "BebasNeue-Regular.ttf", "fallback": "DejaVuSans-Bold.ttf", "system": "Helvetica-Bold"},
    # Body: Inter (humanist sans)
    {"name": "Body", "ttf": "Inter-Light.ttf", "fallback": "DejaVuSans.ttf", "system": "Helvetica"},
    {"name": "Body-Reg", "ttf": "Inter-Regular.ttf", "fallback": "DejaVuSans.ttf", "system": "Helvetica"},
    {"name": "Body-Med", "ttf": "Inter-Medium.ttf", "fallback": "DejaVuSans-Bold.ttf", "system": "Helvetica-Bold"},
    {"name": "Body-Italic", "ttf": "Inter-Italic.ttf", "fallback": "DejaVuSans-Oblique.ttf", "system": "Helvetica-Oblique"},
    {"name": "Body-Bold", "ttf": "Inter-Bold.ttf", "fallback": "DejaVuSans-Bold.ttf", "system": "Helvetica-Bold"},
    # Mono: JetBrains Mono
    {"name": "Mono", "ttf": "JetBrainsMono-Regular.ttf", "fallback": "DejaVuSansMono.ttf", "system": "Courier"},
    {"name": "Mono-Light", "ttf": "JetBrainsMono-Light.ttf", "fallback": "DejaVuSansMono.ttf", "system": "Courier"},
    {"name": "Mono-Bold", "ttf": "JetBrainsMono-Bold.ttf", "fallback": "DejaVuSansMono-Bold.ttf", "system": "Courier-Bold"},
]

# ── System font search paths (in order) ──
_SYSTEM_FONT_DIRS = [
    Path("/usr/share/fonts/truetype/dejavu/"),
    Path("/usr/share/fonts/truetype/"),
    Path("/usr/local/share/fonts/"),
    Path.home() / ".fonts",
    Path.home() / ".local/share/fonts",
]

# ── Registry of resolved paths ──
_font_registry: dict[str, str] = {}


def _find_system_font(name: str) -> str | None:
    """Find a system font by filename across known font directories."""
    for d in _SYSTEM_FONT_DIRS:
        if (d / name).exists():
            return str(d / name)
    return None


def register_fonts() -> dict[str, str]:
    """
    Register all fonts for reportlab, with cascading fallback.
    Returns dict of {font_name: resolved_path_or_fallback_name}.
    """
    global _font_registry
    registry = {}

    for fd in FONT_DEFS:
        name = fd["name"]
        ttf_file = fd["ttf"]
        fallback_file = fd.get("fallback", "")
        system_fallback = fd.get("system", "Helvetica")

        resolved = None

        # 1. Try dedicated font directory
        font_path = FONTS_DIR / ttf_file
        if font_path.exists():
            resolved = str(font_path)

        # 2. Try system fallback
        if not resolved and fallback_file:
            sys_path = _find_system_font(fallback_file)
            if sys_path:
                resolved = sys_path

        # 3. Register with reportlab
        if HAS_REPORTLAB and resolved:
            try:
                pdfmetrics.registerFont(TTFont(name, resolved))
                registry[name] = resolved
            except Exception as e:
                print(f"[fonts] WARN: could not register {name} from {resolved}: {e}", file=sys.stderr)
                resolved = None

        # 4. Fall back to reportlab built-in
        if not resolved:
            registry[name] = system_fallback
            print(f"[fonts] Using system fallback '{system_fallback}' for '{name}'", file=sys.stderr)
            if HAS_REPORTLAB:
                try:
                    pdfmetrics.registerFont(TTFont(name, system_fallback))
                except Exception:
                    pass  # Helvetica/Courier are always available in reportlab

    # Register font families for proper bold/italic resolution
    if HAS_REPORTLAB:
        try:
            registerFontFamily("Body", normal="Body", bold="Body-Bold",
                               italic="Body-Italic", boldItalic="Body-Italic")
            registerFontFamily("Mono", normal="Mono", bold="Mono-Bold")
        except Exception:
            pass

    _font_registry = registry
    return registry


def get_font_path(name: str) -> str:
    """Get the resolved path or fallback name for a font."""
    if not _font_registry:
        register_fonts()
    return _font_registry.get(name, "Helvetica")


def ensure_fonts_downloaded(target_dir: Path | None = None) -> bool:
    """Download missing fonts from GitHub release assets if internet is available.
    Returns True if all fonts are present after the attempt."""
    import urllib.request
    import urllib.error

    target = target_dir or FONTS_DIR
    target.mkdir(parents=True, exist_ok=True)

    # Font source URL (GitHub release or raw)
    BASE = "https://raw.githubusercontent.com/trevormentis-spec/trevor-fonts/main/"

    all_ok = True
    for fd in FONT_DEFS:
        ttf_path = target / fd["ttf"]
        if ttf_path.exists():
            continue
        # Try to download
        url = BASE + fd["ttf"]
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TrevorFontLoader/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                ttf_path.write_bytes(resp.read())
            print(f"[fonts] Downloaded {fd['ttf']} ({ttf_path.stat().st_size // 1024} KB)", file=sys.stderr)
        except (urllib.error.HTTPError, urllib.error.URLError, OSError) as e:
            print(f"[fonts] Could not download {fd['ttf']}: {e}", file=sys.stderr)
            all_ok = False

    return all_ok


# Register fonts on import
if HAS_REPORTLAB:
    register_fonts()
