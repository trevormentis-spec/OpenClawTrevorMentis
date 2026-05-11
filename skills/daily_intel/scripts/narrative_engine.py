#!/usr/bin/env python3
"""narrative_engine.py — Persistent narrative continuity tracker.

Tracks evolving geopolitical narratives across editions:
- Detects regime shifts (narrative structure changes fundamentally)
- Identifies stale narratives (same framing persisted too long)
- Preserves unresolved analytical threads
- Generates continuity reports for assessment conditioning

Usage:
    python3 narrative_engine.py --status        # Show narrative landscape
    python3 narrative_engine.py --drift         # Detect drift across editions
    python3 narrative_engine.py --continuity-report  # Produce conditioning context
"""
from __future__ import annotations

import datetime
import hashlib
import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from trevor_config import THEATRE_KEYS as THEATRES
from trevor_log import get_logger
from trevor_memory import MemoryStore

log = get_logger("narrative_engine")

ASSESS_DIR = SKILL_ROOT / 'assessments'
CRON_DIR = SKILL_ROOT / 'cron_tracking'
NARRATIVE_FILE = CRON_DIR / 'narrative_landscape.json'


def extract_fingerprints() -> dict:
    """Extract narrative fingerprints from all current assessments."""
    landscape = {}
    for region in THEATRES:
        path = ASSESS_DIR / f"{region}.md"
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        lines = [l.strip() for l in content.split('\n') if l.strip() and len(l) > 60]
        lead = lines[0][:200] if lines else content[:200]
        landscape[region] = {
            "fingerprint": lead,
            "hash": hashlib.md5(lead.encode()).hexdigest(),
            "date": datetime.date.today().isoformat(),
            "char_count": len(content),
            "line_count": len(lines),
        }
    return landscape


def detect_drift(current: dict, previous: dict | None) -> list[dict]:
    """Compare current vs previous narrative landscapes to detect drift."""
    if not previous:
        return [{"region": r, "status": "baseline", "note": "First recording"} for r in current]

    drifts = []
    for region in THEATRES:
        cur = current.get(region, {})
        prev = previous.get(region, {})
        if not cur.get("fingerprint"):
            drifts.append({"region": region, "status": "missing", "severity": "high"})
            continue
        if not prev.get("fingerprint"):
            drifts.append({"region": region, "status": "new", "severity": "low"})
            continue
        if cur.get("hash") == prev.get("hash"):
            drifts.append({"region": region, "status": "identical",
                          "severity": "medium", "days": "?"})
        elif cur["fingerprint"][:50] == prev["fingerprint"][:50]:
            drifts.append({"region": region, "status": "minor_shift",
                          "severity": "low"})
        else:
            drifts.append({"region": region, "status": "regime_shift",
                          "severity": "high"})

    return drifts


def has_narrative_regime_shift(region: str) -> bool:
    """Check if a theatre's narrative has fundamentally restructured."""
    mem = MemoryStore()
    try:
        prior = mem.get_previous_narrative(region, days=30)
        if not prior:
            return False
        current_path = ASSESS_DIR / f"{region}.md"
        if not current_path.exists():
            return False
        current = current_path.read_text()[:500]
        # If headers differ significantly, flag as regime shift
        prior_header = prior.split('\n')[0][:100] if prior else ""
        current_header = current.split('\n')[0][:100]
        return prior_header != current_header
    finally:
        mem.close()


def produce_continuity_context() -> dict:
    """Produce conditioning context for assessment generation."""
    current = extract_fingerprints()
    previous = None
    if NARRATIVE_FILE.exists():
        try:
            previous = json.loads(NARRATIVE_FILE.read_text()).get("landscape")
        except:
            pass

    drifts = detect_drift(current, previous)
    shifts = [d for d in drifts if d["status"] == "regime_shift"]

    return {
        "generated": datetime.datetime.utcnow().isoformat(),
        "theatre_count": len(current),
        "drift_count": len(drifts),
        "regime_shifts": len(shifts),
        "drifts": drifts,
        "landscape": current,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", action="store_true", help="Show narrative landscape")
    parser.add_argument("--drift", action="store_true", help="Detect drift")
    parser.add_argument("--continuity-report", action="store_true", help="Produce conditioning context")
    args = parser.parse_args()

    if args.continuity_report:
        context = produce_continuity_context()
        print(json.dumps(context, indent=2))
        return 0

    current = extract_fingerprints()
    previous = None
    if NARRATIVE_FILE.exists():
        try:
            previous = json.loads(NARRATIVE_FILE.read_text()).get("landscape")
        except:
            pass

    if args.drift or args.status:
        drifts = detect_drift(current, previous)
        print(f"\n📊 Narrative Landscape ({len(current)} theatres):")
        shifts = [d for d in drifts if d["status"] == "regime_shift"]
        for d in drifts:
            icon = {"identical": "⚪", "minor_shift": "🔄", "regime_shift": "🔴",
                    "missing": "❌", "new": "🆕", "baseline": "📋"}
            print(f"  {icon.get(d['status'], '❓')} {d['region']}: {d['status']}")
        if shifts:
            print(f"\n🔴 Regime shifts detected: {len(shifts)}")
        if not drifts:
            print("  No drifts detected — first recording")

    if not args.drift and not args.status:
        # Default: save landscape
        report = produce_continuity_context()
        CRON_DIR.mkdir(parents=True, exist_ok=True)
        NARRATIVE_FILE.write_text(json.dumps(report, indent=2))
        log.info("Narrative landscape saved", theatres=len(current), shifts=len([d for d in report.get('drifts', []) if d['status'] == 'regime_shift']))
        print(f"Narrative landscape saved: {len(current)} theatres, {len([d for d in report.get('drifts', []) if d['status'] == 'regime_shift'])} regime shifts")

    return 0


if __name__ == "__main__":
    sys.exit(main())
