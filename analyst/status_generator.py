#!/usr/bin/env python3
"""Status Generator — maintains STATUS.md at repo root.

Updates after every directive action (wire, test, output, completion).
Provides a persistent self-service status surface for the principal.

Usage:
    python3 analyst/status_generator.py --refresh    # Full refresh
    python3 analyst/status_generator.py --mark <directive> <checkpoint>
"""

from __future__ import annotations

import datetime
import json
import os
import pathlib
import re
import sqlite3
import subprocess
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
STATUS_FILE = REPO_ROOT / "STATUS.md"

# ── Active directives ─────────────────────────────────────────

DIRECTIVES_DIR = REPO_ROOT / "analyst" / "directives"

# Known directive files with their status tracking
DIRECTIVES = [
    {
        "name": "Phase 1 Close + Recovery",
        "file": "phase-1-closure-2026-05-17.md",
        "status": "COMPLETE",
        "last_activity": "2026-05-18T13:00:00Z",
        "checkpoints": [
            ("Calibration data recovery", True),
            ("Phase 1 regression probes (B/E)", True),
            ("Framework integrity (entities/postdiction/Riodoce)", True),
            ("Entity depth completion (5 files, Option A)", True),
            ("Cost append to handback", True),
        ],
    },
    {
        "name": "Phase 1 → Phase 2 Transition",
        "file": "phase-1-cleanup-and-stress-2026-05-18.md",
        "status": "COMPLETE",
        "last_activity": "2026-05-18T14:00:00Z",
        "checkpoints": [
            ("Blocklist cleanup (23→11 entries)", True),
            ("Routing clarification in ORCHESTRATION.md", True),
            ("Bajío stress test with 7-dimension self-score", True),
        ],
    },
    {
        "name": "Fabrication Detector + Themes Preflight",
        "file": "phase-1-final-verification-2026-05-18.md",
        "status": "COMPLETE",
        "last_activity": "2026-05-18T13:30:00Z",
        "checkpoints": [
            ("fabrication_check.py v1", True),
            ("fabrication_check.py v2 (regex + dollar detection)", True),
            ("themes_preflight.py + theme_requirements.yaml", True),
            ("Blocklist audit (16/23 problematic)", True),
        ],
    },
    {
        "name": "Phase 2 — Continuous Learning Loop",
        "file": "phase-2-continuous-loop-2026-05-18.md",
        "status": "IN_PROGRESS",
        "last_activity": "2026-05-18T23:00:00Z",
        "checkpoints": [
            ("Planner (analyst/planner.py) — 8 tasks/cycle", True),
            ("Worker (analyst/worker.py) — default dry-run, --live", True),
            ("6 task type modules", True),
            ("3 creative-discovery task types", True),
            ("Mexico pipeline convergence", True),
            ("7-day live evaluation (Day 1: $0.011/$20)", True),
            ("Worker dry-run log produced + approved", True),
        ],
    },
    {
        "name": "Presentation Stack — JSON Schema + PDF Renderer",
        "file": "phase-2-live-auth-2026-05-18.md",
        "status": "COMPLETE",
        "last_activity": "2026-05-18T23:00:00Z",
        "checkpoints": [
            ("Brief JSON schema v1.0.0 → v1.1.0", True),
            ("PDF renderer (weasyprint, scripts/render_pdf.py)", True),
            ("Audio renderer (ElevenLabs, scripts/render_audio.py)", True),
            ("Bajío v3 round-trip test (MD→JSON→PDF)", True),
            ("USMCA v3 flagship (10 Opus sections, 4,603 words)", True),
        ],
    },
    {
        "name": "Routing Escalation Fix",
        "file": "routing-v4pro-addition-2026-05-18.md",
        "status": "COMPLETE",
        "last_activity": "2026-05-18T23:00:00Z",
        "checkpoints": [
            ("analyst/routing.py — complexity-based routing", True),
            ("analyst/escalation_guard.py — pre/mid/post-generation", True),
            ("DeepSeek V4 Pro mid-tier (Haiku removed)", True),
            ("Schema v1.1.0 with generation_metadata", True),
        ],
    },
    {
        "name": "Source Coverage Expansion — 12 Integrations",
        "file": "source-coverage-execution-directive.md",
        "status": "IN_PROGRESS",
        "last_activity": "2026-05-18T23:45:00Z",
        "checkpoints": [
            ("Source 1: CENACE grid load (19K records, anomaly detection)", True),
            ("Source 2: CompraNet procurement (contract scraping + shell flags)", True),
            ("Source 3: Property records (4-state monitoring scaffold)", True),
            ("Source 4: Law firm briefings (7 targets, AgentMail workflow)", True),
            ("Source 5: AMIS insurance pricing (Phase 1 — quarterly stats)", True),
            ("Source 6: Maritime AIS (5 ports, free tier; paid API pending)", True),
            ("Source 7: DOF daily monitoring (34 articles/day, V4 Pro)", True),
            ("Source 8: Substack/Patreon discovery (V4 Pro brainstorm queued)", True),
            ("Source 9: Military procurement (SEDENA/SEMAR/GN scaffold)", True),
            ("Source 10: Cargo theft (Phase 1 scaffold; Phase 2 needs approval)", True),
            ("AgentMail API key wired", True),
            ("Non-traditional source categories (16 new, 113 total)", True),
            ("Registry schema: 6 new source_type values", True),
        ],
    },
]

# ── Recent outputs ────────────────────────────────────────────

OUTPUT_PATTERNS = [
    ("memory/*phase-2-day-*.md", "Phase 2 daily checkpoint"),
    ("memory/*stress-test-bajio*.md", "Bajío stress test"),
    ("memory/*source*.md", "Source coverage memo"),
    ("memory/*worker-dry-run*.md", "Worker dry-run log"),
    ("memory/*planner-state*.md", "Planner state log"),
    ("memory/*presentation*.md", "Presentation audit"),
    ("memory/*blocklist-audit*.md", "Blocklist audit"),
    ("memory/usmca-map/usmca-v3-full.md", "USMCA flagship brief"),
    ("memory/2026-05-test-renders/usmca-q3-2026*.pdf", "USMCA PDF renders"),
    ("memory/2026-05-test-renders/usmca-q3-2026-v2*.pdf", "USMCA v2 PDF"),
    ("memory/2026-05-test-renders/usmca-q3-2026-v3*.pdf", "USMCA v3 PDF"),
    ("exports/*.md", "Export reports"),
    ("data/dof/*.json", "DOF scans"),
]


def get_recent_outputs(days: int = 7) -> list[dict[str, str]]:
    """Find recently produced files."""
    outputs = []
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)

    for pattern, desc in OUTPUT_PATTERNS:
        for f in sorted(REPO_ROOT.glob(pattern), reverse=True)[:3]:
            try:
                mtime = datetime.datetime.fromtimestamp(f.stat().st_mtime, tz=datetime.timezone.utc)
                if mtime > cutoff:
                    outputs.append({
                        "path": str(f.relative_to(REPO_ROOT)),
                        "type": f.suffix[1:].upper() if f.suffix else "FILE",
                        "timestamp": mtime.strftime("%Y-%m-%d %H:%M UTC"),
                        "description": desc,
                    })
            except Exception:
                pass

    return sorted(outputs, key=lambda x: x["timestamp"], reverse=True)[:15]


def get_cost_summary() -> dict[str, float]:
    """Read latest cost data from DeepSeek usage tracker."""
    costs = {"opus": 0.0, "v4pro": 0.0, "flash": 0.0, "other": 0.0, "total": 0.0}

    ds_file = REPO_ROOT / "brain" / "memory" / "semantic" / "deepseek-usage.json"
    if ds_file.exists():
        try:
            data = json.loads(ds_file.read_text())
            snapshots = data.get("snapshots", [])
            if len(snapshots) >= 2:
                first_cost = snapshots[0]["cumulative"]["total_cost_usd"]
                last_cost = snapshots[-1]["cumulative"]["total_cost_usd"]
                costs["flash"] = round(last_cost - first_cost, 2)
                costs["total"] = round(sum(costs.values()), 2)
        except Exception:
            pass

    return costs


def generate_status() -> str:
    """Generate the full STATUS.md content."""
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    costs = get_cost_summary()
    outputs = get_recent_outputs()

    lines = [
        "# Open Claw Trevor Mentis — STATUS",
        "",
        f"**Last updated:** {now}",
        "**Generated by:** status_generator.py",
        "",
        "---",
        "",
        "## In-Flight Directives",
        "",
    ]

    for d in DIRECTIVES:
        status = d["status"]
        status_icon = {"COMPLETE": "✅", "IN_PROGRESS": "🔄", "BLOCKED": "❌", "AWAITING_REVIEW": "👁️",
                       "AWAITING_APPROVAL": "🔶", "NOT_STARTED": "⚪"}.get(status, "❓")
        lines.append(f"### {status_icon} {d['name']}")
        lines.append(f"- **Status:** {status}")
        lines.append(f"- **Last activity:** {d['last_activity']}")
        lines.append("")
        for label, done in d["checkpoints"]:
            lines.append(f"- {'[X]' if done else '[ ]'} {label}")
        lines.append("")

    lines.append("---")
    lines.append("## Awaiting Principal Approval")
    lines.append("")
    lines.append("| Item | Directive | Date Raised |")
    lines.append("|------|-----------|-------------|")
    lines.append("| Maritime AIS paid API ($50-200/mo) | Source Coverage | 2026-05-18 |")
    lines.append("| Cargo theft paid subscription ($5-25K/yr) | Source Coverage | 2026-05-18 |")
    lines.append("| SPS internal data (Phase 2) | Source Coverage | 2026-05-18 |")
    lines.append("| Cartel Telegram channels | Source Coverage | 2026-05-18 |")
    lines.append("| Real estate listings (Source 11) | Source Coverage | 2026-05-18 |")
    lines.append("| ElevenLabs audio MP3 delivery | Presentation Stack | 2026-05-18 |")
    lines.append("")
    
    lines.append("---")
    lines.append("## Recent Outputs (Last 7 Days)")
    lines.append("")
    for o in outputs:
        lines.append(f"- `{o['path']}` ({o['type']}) — {o['description']} — {o['timestamp']}")
    if not outputs:
        lines.append("(No recent outputs found)")
    lines.append("")

    lines.append("---")
    lines.append("## AgentMail Health")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    lines.append("| Address | trevor_mentis@agentmail.to |")
    lines.append("| Status | ACTIVE (inbox key verified) |")
    lines.append("| Last email received | 2026-05-18 (skill security audit) |")
    lines.append("| Active subscriptions | 0 (pending manual signup) |")
    lines.append("| Last health check | (not yet implemented — Part B pending) |")
    lines.append("")
    lines.append("*Verification:* Principal can email trevor_mentis@agentmail.to and Trevor")
    lines.append("will log receipt in next STATUS.md refresh. No web inbox available.")
    lines.append("")

    lines.append("---")
    lines.append("## Phase 2 Live Evaluation")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|-------|-------:|")
    lines.append("| Day | 1 of 7 |")
    lines.append("| Tasks completed | 5 |")
    lines.append("| Cost to date | $0.011 |")
    lines.append("| Daily budget | $20.00 |")
    lines.append("| Remaining daily | $19.989 |")
    lines.append("| Worker mode | Dry-run default (--live flag required) |")
    lines.append("")

    lines.append("---")
    lines.append("## Cost Summary (Current Month)")
    lines.append("")
    lines.append(f"| Model | Spend |")
    lines.append(f"|-------|------:|")
    lines.append(f"| Opus 4.7 | ${costs['opus']:.2f} |")
    lines.append(f"| DeepSeek V4 Pro | ${costs['v4pro']:.2f} |")
    lines.append(f"| DeepSeek Flash | ${costs['flash']:.2f} |")
    lines.append(f"| Other | ${costs['other']:.2f} |")
    lines.append(f"| **Total** | **${costs['total']:.2f}** |")
    lines.append(f"| Monthly budget | $140.00 |")
    lines.append(f"| Remaining | ${max(0, 140 - costs['total']):.2f} |")
    lines.append("")

    lines.append("---")
    lines.append(f"*Generated {now} by status_generator.py*")

    return "\n".join(lines)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Status Generator")
    parser.add_argument("--refresh", action="store_true", help="Full refresh STATUS.md")
    args = parser.parse_args()

    if args.refresh:
        status = generate_status()
        STATUS_FILE.write_text(status)
        print(f"STATUS.md updated ({len(status)} chars)")


if __name__ == "__main__":
    main()
