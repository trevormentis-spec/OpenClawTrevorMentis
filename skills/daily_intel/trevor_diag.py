#!/usr/bin/env python3
"""Startup diagnostics for Trevor DailyIntelAgent — run at pipeline start.

Verifies:
- Config loads correctly
- All dependencies available
- Fonts registered
- API keys present (non-blocking warnings)
- Disk space
- Reports structured health status

Usage:
    python3 -m trevor_diag
"""
from __future__ import annotations

import os
import sys
import shutil
from pathlib import Path

# Ensure we can import from skill root
_SKILL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_SKILL_ROOT))
sys.path.insert(0, str(_SKILL_ROOT / "scripts"))


def run() -> list[dict]:
    """Run all diagnostics and return results."""
    results = []

    def check(name: str, ok: bool, detail: str = "", severity: str = "info"):
        results.append({"check": name, "status": "ok" if ok else "fail",
                        "detail": str(detail), "severity": severity})
        icon = "✅" if ok else "⚠️" if severity == "warning" else "❌"
        print(f"  {icon} {name}: {detail}"[:120])

    print("\n🔍 Trevor Startup Diagnostics")
    print("=" * 50)

    # 1. Config
    try:
        from trevor_config import WORKSPACE, EXPORTS_DIR, THEATRES, DEEPSEEK_API_KEY
        check("config_import", True, "trevor_config loaded")
        check("workspace_exists", WORKSPACE.exists(), str(WORKSPACE))
        check("exports_exists", EXPORTS_DIR.exists(), str(EXPORTS_DIR))
        check("theatres_count", len(THEATRES) >= 6, f"{len(THEATRES)} theatres")
        check("deepseek_api_key", bool(DEEPSEEK_API_KEY),
              "DEEPSEEK_API_KEY present" if DEEPSEEK_API_KEY else "MISSING",
              severity="warning")
    except Exception as e:
        check("config_import", False, str(e), severity="error")
        return results

    # 2. Dependencies
    deps = [
        ("reportlab", "reportlab", True),
        ("Pillow", "PIL", True),
        ("requests", "requests", True),
        ("matplotlib", "matplotlib", False),  # optional — maps
        ("chromadb", "chromadb", False),  # optional — will be replaced with FTS5
        ("sentence_transformers", "sentence_transformers", False),
    ]
    for name, import_name, required in deps:
        try:
            __import__(import_name)
            check(f"dep_{name}", True, f"{import_name} available")
        except ImportError:
            sev = "error" if required else "warning"
            check(f"dep_{name}", not required, f"{import_name} NOT installed", severity=sev)

    # 3. Fonts
    try:
        from trevor_fonts import register_fonts
        reg = register_fonts()
        all_resolved = all("DejaVu" not in str(v) and v not in ("Helvetica","Helvetica-Bold","Courier") for v in reg.values())
        check("fonts", all_resolved, f"{len(reg)} fonts registered")
        for name, path in reg.items():
            check(f"font_{name.lower().replace('-','_')}", True, f"{name}: {Path(path).name if path else 'built-in'}")
    except Exception as e:
        check("fonts", False, str(e), severity="warning")

    # 4. Disk space
    try:
        ws = WORKSPACE
        usage = shutil.disk_usage(ws)
        gb_free = usage.free / (1024**3)
        check("disk_space", gb_free > 1, f"{gb_free:.1f} GB free at {ws}")
    except Exception as e:
        check("disk_space", False, str(e), severity="warning")

    # 5. Logger
    try:
        from trevor_log import get_logger, HealthReport
        log = get_logger("diagnostics")
        log.info("Startup diagnostics complete", checks=len(results), passed=sum(1 for r in results if r["status"] == "ok"))
        check("logger", True, "structured logger initialized")
    except Exception as e:
        check("logger", False, str(e), severity="warning")

    # Print summary
    passed = sum(1 for r in results if r["status"] == "ok")
    failed = sum(1 for r in results if r["status"] == "fail")
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {len(results)} total checks")
    if failed:
        print("⚠️  Some checks failed — review above for details, pipeline may degrade gracefully")
    print()

    return results


if __name__ == "__main__":
    run()
