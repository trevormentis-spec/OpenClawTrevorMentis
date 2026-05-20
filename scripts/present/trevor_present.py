#!/usr/bin/env python3
"""Trevor Present — integration CLI for Stages 1-5.

Runs all presentational stages in additive order:
  1. Cover image (GenViral)
  2. Charts + diagrams (rule-based routing)
  3. Map (Mapbox)
  4. Audio narration (ElevenLabs, degrades to script)
  5. Video briefing (ffmpeg)

Each stage self-tests prerequisites and disables itself cleanly if missing.
Cost control via --budget flag with hard per-asset ceiling.
State in files on disk. No FastAPI. No database. No approval gates.

Usage:
    # Full run with all stages
    python3 scripts/present/trevor_present.py --brief /tmp/brief.json --output-dir exports/present/2026-05-20

    # With budget limit
    python3 scripts/present/trevor_present.py --brief /tmp/brief.json --budget 0.50

    # Skip specific stages
    python3 scripts/present/trevor_present.py --brief /tmp/brief.json --skip video

    # Self-test all stages
    python3 scripts/present/trevor_present.py --self-test

Budget: $0.06 per run (1 GenViral credit + $0.05 ElevenLabs, when working).
"""

from __future__ import annotations
import sys
sys.path.insert(0, "/home/ubuntu/.openclaw/workspace")

import sys
if "/home/ubuntu/.openclaw/workspace" not in sys.path:
import sys
import argparse
import json
import os
import pathlib
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Optional
WORKSPACE = pathlib.Path("/home/ubuntu/.openclaw/workspace")
STAGE_SCRIPTS = WORKSPACE / "scripts" / "present"
ASSET_CEILINGS = {
    "cover_image": 0.01,   # 1 GenViral credit
    "charts": 0.00,        # matplotlib + Mermaid = free
    "maps": 0.00,          # Mapbox free tier
    "audio": 0.15,         # ElevenLabs per-character
    "video": 0.00,         # ffmpeg = free
}
STAGES = [
    {"name": "cover_image", "script": "stage1_image.py",
     "args": lambda b, o: ["--prompt", f"Intelligence briefing cover for: {b.get('title','Briefing')}",
                           "--output", str(o / "cover.png"), "--aspect-ratio", "16:9"]},
    {"name": "charts", "script": "stage2_charts.py",
     "args": lambda b, o: ["--brief", str(b.get("_path", "")),
                           "--output-dir", str(o)]},
    {"name": "maps", "script": "stage3_map.py",
     "args": lambda b, o: _map_args(b, o)},
    {"name": "audio", "script": "stage4_audio.py",
     "args": lambda b, o: ["--brief", str(b.get("_path", "")),
                           "--output", str(o / "narration.mp3")]},
    {"name": "video", "script": "stage5_video.py",
     "args": lambda b, o: _video_args(b, o)},
]
def _map_args(brief: dict, output_dir: pathlib.Path) -> list[str]:
    """Extract map args from brief geographic data."""
    args = ["--center", "0", "0", "--zoom", "4", "--output", str(output_dir / "map.png")]
    for s in brief.get("sections", []):
        geo = s.get("geographic")
        if geo and geo.get("center"):
            c = geo["center"]
            if len(c) == 2:
                args[1], args[2] = str(c[0]), str(c[1])
            args[4] = str(geo.get("zoom", 5))
            break
    return args
def _video_args(brief: dict, output_dir: pathlib.Path) -> list[str]:
    """Build video args from available assets."""
    args = ["--brief", str(brief.get("_path", "")), "--duration", "30"]
    asset_exts = {
        "cover.png", "kent-bar.png", "trade-bar.png", "sections-diagram.png", "map.png"
    }
    images = [str(output_dir / f) for f in asset_exts if (output_dir / f).exists()]
    if images:
        args.extend(["--images"] + images)
    audio = output_dir / "narration.mp3"
    if audio.exists():
        args.extend(["--audio", str(audio)])
    script = output_dir / "narration.script.txt"
    if script.exists():
        args.extend(["--script", str(script)])
    args.extend(["--output", str(output_dir / "briefing.mp4")])
    return args
def _load_env() -> dict[str, str]:
    """Load environment via shared _env module (not .env directly)."""
    from _present_env import load_env as _le
    return _le()
def run_stage(stage: dict, brief: dict, output_dir: pathlib.Path,
              env: dict[str, str], budget: float, skip: set) -> dict:
    """Run a single stage. Returns result dict."""
    name = stage["name"]
    if name in skip:
        return {"name": name, "skipped": True, "success": True}
    script_path = STAGE_SCRIPTS / stage["script"]
    if not script_path.exists():
        return {"name": name, "skipped": True, "success": False,
                "error": f"Script not found: {script_path}"}
    ceiling = ASSET_CEILINGS.get(name, 0.01)
    if budget < ceiling:
        return {"name": name, "skipped": True, "success": False,
                "error": f"Budget ${budget:.2f} < ceiling ${ceiling:.2f}"}
    args = stage["args"](brief, output_dir)
    full_cmd = ["python3", str(script_path)] + args
    start = time.time()
    result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=300, env=env)
    elapsed = time.time() - start
    success = result.returncode == 0
    if "DISABLED" in result.stdout:
        success = True  # graceful degradation
        elapsed = 0.1
    meta = {
        "name": name,
        "success": success,
        "elapsed_sec": round(elapsed, 1),
        "returncode": result.returncode,
        "stdout": result.stdout[-300:] if result.stdout else "",
        "stderr": result.stderr[-200:] if result.stderr else "",
    }
    return meta
def self_test_all() -> dict[str, list[str]]:
    """Run --self-test on all stages. Returns {stage: [failures]}."""
    env = _load_env()
    results = {}
    for stage in STAGES:
        script_path = STAGE_SCRIPTS / stage["script"]
        result = subprocess.run(
            ["python3", str(script_path), "--self-test"],
            capture_output=True, text=True, timeout=30, env=env,
        )
        output = result.stdout + result.stderr
        disabled = [l.strip() for l in output.split("\n") if "DISABLED" in l]
        results[stage["name"]] = disabled if disabled else []
    return results
def main():
    parser = argparse.ArgumentParser(description="Trevor Present — Stages 1-5 pipeline")
    parser.add_argument("--brief", help="Path to brief JSON")
    parser.add_argument("--output-dir", "-o", default="",
                        help="Output directory (default: exports/present/DATE)")
    parser.add_argument("--skip", nargs="*", default=[],
                        help="Stages to skip")
    parser.add_argument("--budget", type=float, default=0.50,
                        help="Max spend per run in USD (default: $0.50)")
    parser.add_argument("--self-test", action="store_true",
                        help="Self-test all stages and exit")
    parser.add_argument("--skip-qc", action="store_true",
                        help="Skip Phase B vision QC verification")
    args = parser.parse_args()
    if args.self_test:
        print("=== Trevor Present — Self-Test ===\n")
        results = self_test_all()
        all_ok = True
        for stage, failures in results.items():
            if failures:
                for f in failures:
                    print(f"  ❌ {stage}: {f}")
                all_ok = False
            else:
                print(f"  ✅ {stage}: ready")
        print(f"\n{'All stages ready' if all_ok else 'Some stages disabled'}")
        return
    if not args.brief:
        parser.error("--brief is required (unless using --self-test)")
    brief_path = pathlib.Path(args.brief)
    if not brief_path.exists():
        print(f"ERROR: Brief not found: {args.brief}")
        sys.exit(1)
    brief = json.loads(brief_path.read_text())
    brief["_path"] = str(brief_path)
    if not args.output_dir:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        args.output_dir = str(WORKSPACE / "exports" / "present" / date_str)
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    skip_set = set(args.skip)
    env = _load_env()
    remaining_budget = args.budget
    print(f"\n{'='*60}")
    print(f"  Trevor Present")
    print(f"  Brief: {brief.get('title', brief_path.name)}")
    print(f"  Output: {output_dir}")
    print(f"  Budget: ${args.budget:.2f}")
    print(f"  Skip: {skip_set or 'none'}")
    print(f"{'='*60}\n")
    results = []
    total_start = time.time()
    for stage in STAGES:
        name = stage["name"]
        ceiling = ASSET_CEILINGS.get(name, 0.01)
        if remaining_budget < ceiling:
            print(f"  ⏭️  {name}: budget ${remaining_budget:.2f} < ceiling ${ceiling:.2f}")
            results.append({"name": name, "skipped": True, "reason": "budget"})
            continue
        result = run_stage(stage, brief, output_dir, env, remaining_budget, skip_set)
        results.append(result)
        if not result.get("skipped") and result.get("success"):
            remaining_budget -= ceiling
        icon = "✅" if result.get("success") else "❌"
        if result.get("skipped"):
            icon = "⏭️"
        details = result.get("error", f"{result.get('elapsed_sec', 0):.1f}s")
        print(f"  {icon} {name}: {details}")
    total_elapsed = time.time() - total_start
    success_count = sum(1 for r in results if r.get("success"))
    total_stages = len(results)
    manifest = {
        "brief": str(brief_path),
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "title": brief.get("title", ""),
        "output_dir": str(output_dir),
        "budget": args.budget,
        "remaining_budget": round(remaining_budget, 4),
        "results": results,
        "total_elapsed_sec": round(total_elapsed, 1),
        "generated_files": [str(f) for f in output_dir.iterdir() if f.is_file()],
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\n{'='*60}")
    print(f"  Pipeline: {success_count}/{total_stages} stages succeeded")
    print(f"  Duration: {total_elapsed:.1f}s")
    print(f"  Budget used: ${args.budget - remaining_budget:.2f} of ${args.budget:.2f}")
    print(f"  Manifest: {manifest_path}")
    print(f"{'='*60}")
    deliv_files = [str(f) for f in output_dir.iterdir() if f.is_file() and f.suffix in ('.png', '.jpg', '.mp4', '.mp3')]
    if deliv_files and not args.skip_qc:
        print(f"\n--- Running QC on {len(deliv_files)} deliverables ---")
        qc_script = STAGE_SCRIPTS / "qc_vision.py"
        specs = {
            'cover.png': 'Intelligence briefing cover. Dark navy background, gold accents.',
            'kent-bar.png': 'Kent confidence distribution bar chart. Navy background, gold title.',
            'trade-bar.png': 'Trade position sizing bar chart.',
            'map.png': 'Mapbox dark-themed static map with pin markers.',
            'briefing.mp4': 'Briefing video with title slide, visuals, and audio.',
            'narration.mp3': 'Audio narration for intelligence briefing.',
        }
        for f in deliv_files:
            fname = pathlib.Path(f).name
            spec = specs.get(fname, 'TREVOR intelligence briefing artefact')
            result = subprocess.run(
                ['python3', str(qc_script), '--file', f, '--spec', spec],
                capture_output=True, text=True, timeout=120, env=env,
            )
            try:
                verdict = json.loads(result.stdout)
                icon = '✅' if verdict.get('pass') else '⚠️'
                print(f'  {icon} {fname}: {"PASS" if verdict.get("pass") else f"FAIL ({len(verdict.get("issues", []))} issues)"}')
            except:
                print(f'  ❓ {fname}: QC parse error')
    if success_count < total_stages:
        print(f"\n⚠️  {total_stages - success_count} stage(s) failed or skipped.")
        sys.exit(0)  # Graceful exit — degradation is by design
if __name__ == "__main__":
    main()
