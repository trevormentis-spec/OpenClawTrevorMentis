#!/usr/bin/env python3
"""
Model Comparison Script — DeepSeek V4 Pro vs Opus 4.7 (via OpenRouter)

Runs: 
  1. Collector (once, shared input)
  2. Analysis with DeepSeek V4 Pro → outputs/analysis-dsv4/
  3. Analysis with Opus 4.7 via OpenRouter → outputs/analysis-opus/
  4. Side-by-side comparison document

Usage:
    python3 scripts/model_comparison.py [--collect-only] [--skip-collect]
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

REPO = pathlib.Path(__file__).resolve().parents[1]
SKILL_DIR = REPO / "skills" / "daily-intel-brief"
SCRIPTS_DIR = SKILL_DIR / "scripts"
DATE_UTC = dt.datetime.utcnow().strftime("%Y-%m-%d")

# Shared working dirs
SHARED_WD = pathlib.Path("~/trevor-briefings").expanduser() / f"{DATE_UTC}-compare"
DSV4_WD = SHARED_WD / "dsv4"
OPUS_WD = SHARED_WD / "opus"
OUTPUT_DIR = REPO / "exports" / "comparisons"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str) -> None:
    ts = dt.datetime.utcnow().strftime("%H:%M:%S")
    print(f"[compare {ts}] {msg}", flush=True)


def step_collect() -> int:
    """Run collector once. Output goes to SHARED_WD/raw/."""
    raw_dir = SHARED_WD / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "python3", str(SCRIPTS_DIR / "collect.py"),
        "--working-dir", str(SHARED_WD),
        "--regions", str(SKILL_DIR / "references" / "regions.json"),
        "--sources", str(REPO / "analyst" / "meta" / "sources.json"),
    ]
    log(f"Collector: {' '.join(cmd)}")
    t0 = time.monotonic()
    rc = subprocess.call(cmd, cwd=str(REPO))
    log(f"Collector done: rc={rc} ({time.monotonic()-t0:.1f}s)")
    return rc


def prepare_analysis_dir(wd: pathlib.Path, label: str) -> None:
    """Set up analysis dir and symlink to shared raw/incidents.json."""
    wd.mkdir(parents=True, exist_ok=True)
    analysis_dir = wd / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    # Symlink or copy raw incidents
    raw_dest = wd / "raw"
    raw_dest.mkdir(parents=True, exist_ok=True)
    incidents_src = SHARED_WD / "raw" / "incidents.json"
    incidents_dst = raw_dest / "incidents.json"
    if incidents_src.exists() and not incidents_dst.exists():
        shutil.copy2(str(incidents_src), str(incidents_dst))
        log(f"  Copied incidents.json -> {label}/raw/")

    # Copy framing file if it exists
    framing_src = SHARED_WD / "00-framing.md"
    if framing_src.exists():
        shutil.copy2(str(framing_src), str(wd / "00-framing.md"))


def step_analyze(wd: pathlib.Path, label: str, model: str, provider: str) -> int:
    """Run analysis with given model/provider."""
    prepare_analysis_dir(wd, label)
    cmd = [
        "python3", str(SCRIPTS_DIR / "analyze.py"),
        "--working-dir", str(wd),
        "--prompts", str(SKILL_DIR / "references" / "deepseek-prompts.md"),
        "--regions", str(SKILL_DIR / "references" / "regions.json"),
        "--model", model,
        "--provider", provider,
    ]
    log(f"  Analyze ({label}): model={model} provider={provider}")
    t0 = time.monotonic()
    rc = subprocess.call(cmd, cwd=str(REPO))
    log(f"  Analyze ({label}) done: rc={rc} ({time.monotonic()-t0:.1f}s)")
    return rc


def load_json(path: pathlib.Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def compare_outputs():
    """Load both analysis outputs and write a comparison."""
    log("Writing comparison document...")

    # Load exec summaries
    dsv4_exec = load_json(DSV4_WD / "analysis" / "exec_summary.json")
    opus_exec = load_json(OPUS_WD / "analysis" / "exec_summary.json")

    # Load regional files
    regions = ["europe", "asia", "middle_east", "north_america", "south_central_america", "global_finance"]

    lines = []
    lines.append(f"# Model Comparison Report — {DATE_UTC}")
    lines.append(f"")
    lines.append(f"**Generated:** {dt.datetime.utcnow().isoformat()}Z")
    lines.append(f"")
    lines.append(f"| Side | Model | Provider | Cost (per M tokens) |")
    lines.append(f"|------|-------|----------|--------------------|")
    lines.append(f"| A | DeepSeek V4 Pro | DeepSeek Direct | $0.435/M in, $0.87/M out |")
    lines.append(f"| B | Claude Opus 4.7 | OpenRouter | $5.00/M in, $25.00/M out |")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # BLUF comparison
    lines.append(f"## 1. BLUF Comparison")
    lines.append(f"")
    lines.append(f"**DSv4 BLUF:** {dsv4_exec.get('bluf', 'N/A')}")
    lines.append(f"")
    lines.append(f"**Opus 4.7 BLUF:** {opus_exec.get('bluf', 'N/A')}")
    lines.append(f"")

    # Context paragraph comparison
    lines.append(f"## 2. Context Paragraph Comparison")
    lines.append(f"")
    lines.append(f"**DSv4 Context:** {dsv4_exec.get('context_paragraph', 'N/A')}")
    lines.append(f"")
    lines.append(f"**Opus 4.7 Context:** {opus_exec.get('context_paragraph', 'N/A')}")
    lines.append(f"")

    # Key judgments comparison
    lines.append(f"## 3. Key Judgments (Top 5)")
    lines.append(f"")
    lines.append(f"| # | DSv4 V4 Pro | Opus 4.7 |")
    lines.append(f"|---|-------------|----------|")
    dsv4_kjs = dsv4_exec.get("five_judgments", [])
    opus_kjs = opus_exec.get("five_judgments", [])
    for i in range(max(len(dsv4_kjs), len(opus_kjs))):
        kj_ds = dsv4_kjs[i] if i < len(dsv4_kjs) else {"statement": "(missing)", "sherman_kent_band": "", "prediction_pct": ""}
        kj_op = opus_kjs[i] if i < len(opus_kjs) else {"statement": "(missing)", "sherman_kent_band": "", "prediction_pct": ""}
        lines.append(f"| {i+1} | [{kj_ds.get('drawn_from_region','?')}] {kj_ds['statement'][:120]} ({kj_ds.get('sherman_kent_band','')}; {kj_ds.get('prediction_pct','')}%) | [{kj_op.get('drawn_from_region','?')}] {kj_op['statement'][:120]} ({kj_op.get('sherman_kent_band','')}; {kj_op.get('prediction_pct','')}%) |")
    lines.append(f"")

    # Regional analysis comparison
    lines.append(f"## 4. Regional Analysis — Side by Side")
    lines.append(f"")
    for region in regions:
        dsv4_reg = load_json(DSV4_WD / "analysis" / f"{region}.json")
        opus_reg = load_json(OPUS_WD / "analysis" / f"{region}.json")

        region_label = region.replace("_", " ").title()
        lines.append(f"### {region_label}")
        lines.append(f"")
        lines.append(f"**Narrative:**")
        lines.append(f"")
        lines.append(f"- **DSv4:** {dsv4_reg.get('narrative', 'N/A')[:300]}")
        lines.append(f"- **Opus:** {opus_reg.get('narrative', 'N/A')[:300]}")
        lines.append(f"")

        lines.append(f"**Key Judgments:**")
        lines.append(f"")
        lines.append(f"| KJ | DSv4 V4 Pro | Opus 4.7 |")
        lines.append(f"|----|-------------|----------|")
        ds_kjs = dsv4_reg.get("key_judgments", [])
        op_kjs = opus_reg.get("key_judgments", [])
        for i in range(max(len(ds_kjs), len(op_kjs))):
            kj_ds = ds_kjs[i] if i < len(ds_kjs) else {"id": "(missing)", "statement": "", "sherman_kent_band": "", "prediction_pct": ""}
            kj_op = op_kjs[i] if i < len(op_kjs) else {"id": "(missing)", "statement": "", "sherman_kent_band": "", "prediction_pct": ""}
            lines.append(f"| {kj_ds.get('id','?')} | {kj_ds['statement'][:100]} ({kj_ds.get('sherman_kent_band','')}; {kj_ds.get('prediction_pct','')}%) | {kj_op['statement'][:100]} ({kj_op.get('sherman_kent_band','')}; {kj_op.get('prediction_pct','')}%) |")
        lines.append(f"")

    # Word count / verbosity
    lines.append(f"## 5. Verbosity & Style Comparison")
    lines.append(f"")
    dsv4_narratives = ""
    opus_narratives = ""
    for region in regions:
        dsv4_reg = load_json(DSV4_WD / "analysis" / f"{region}.json")
        opus_reg = load_json(OPUS_WD / "analysis" / f"{region}.json")
        dsv4_narratives += dsv4_reg.get("narrative", "")
        opus_narratives += opus_reg.get("narrative", "")
    lines.append(f"- **DSv4 total narrative length:** {len(dsv4_narratives)} chars")
    lines.append(f"- **Opus 4.7 total narrative length:** {len(opus_narratives)} chars")
    lines.append(f"- **DSv4 KJ count:** {sum(len(load_json(DSV4_WD/'analysis'/f'{r}.json').get('key_judgments',[])) for r in regions)}")
    lines.append(f"- **Opus KJ count:** {sum(len(load_json(OPUS_WD/'analysis'/f'{r}.json').get('key_judgments',[])) for r in regions)}")
    lines.append(f"")

    # Cost estimate
    lines.append(f"## 6. Cost Estimate")
    lines.append(f"")
    lines.append(f"Based on typical run (~6 region analyses + exec summary + red-team):")
    lines.append(f"- **DeepSeek V4 Pro:** ~$0.15-0.30 per pipeline run (est.)")
    lines.append(f"- **Claude Opus 4.7:** ~$1.50-3.00 per pipeline run (est.)")
    lines.append(f"- **Delta:** Opus 4.7 is roughly **10x** the cost of DSv4 Pro")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"*Comparison generated by TREVOR — {DATE_UTC}*")

    report = "\n".join(lines)
    report_path = OUTPUT_DIR / f"model-comparison-{DATE_UTC}.md"
    report_path.write_text(report)
    log(f"Comparison written to {report_path}")
    return str(report_path)


def main() -> int:
    log(f"=== Model Comparison: DSv4 Pro vs Opus 4.7 ===")
    log(f"Date: {DATE_UTC}")
    log(f"Shared WD: {SHARED_WD}")
    log(f"")

    # Step 1: Collect
    if not (SHARED_WD / "raw" / "incidents.json").exists():
        rc = step_collect()
        if rc != 0:
            log(f"FATAL: Collector failed (rc={rc})")
            return rc
    else:
        log("Incidents already collected, skipping collector")

    # Step 2: DSv4 Pro analysis
    dsv4_incidents = DSV4_WD / "raw" / "incidents.json"
    if not dsv4_incidents.exists():
        log("Running DSv4 V4 Pro analysis...")
        rc = step_analyze(DSV4_WD, "DSv4-Pro", "deepseek/deepseek-v4-pro", "deepseek")
        if rc != 0:
            log(f"WARN: DSv4 analysis rc={rc}")
    else:
        log("DSv4 analysis already exists, skipping")

    # Step 3: Opus 4.7 via OpenRouter
    opus_incidents = OPUS_WD / "raw" / "incidents.json"
    if not opus_incidents.exists():
        log("Running Opus 4.7 analysis via OpenRouter...")
        # Ensure OPENROUTER_API_KEY is available
        or_key = os.environ.get("OPENROUTER_API_KEY")
        if not or_key:
            log("FATAL: OPENROUTER_API_KEY not set")
            return 1
        rc = step_analyze(OPUS_WD, "Opus-4.7", "anthropic/claude-opus-4.7", "openrouter")
        if rc != 0:
            log(f"WARN: Opus analysis rc={rc}")
    else:
        log("Opus analysis already exists, skipping")

    # Step 4: Compare
    report_path = compare_outputs()
    log(f"Comparison complete: {report_path}")
    log(f"")
    log(f"=== Summary ===")
    log(f"DSv4 analysis: {DSV4_WD / 'analysis'}")
    log(f"Opus analysis: {OPUS_WD / 'analysis'}")
    log(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
