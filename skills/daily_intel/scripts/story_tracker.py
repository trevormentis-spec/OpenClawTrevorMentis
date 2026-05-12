#!/usr/bin/env python3
"""StoryTracker — Active narrative lifecycle management.

NOT a passive logger. It:
  - Detects stale narratives (same story 3+ days)
  - Flags them to improve_assessments.py before generation
  - Saves narrative deltas so generation knows what's changed
  - Prevents repeating yesterday's lead story

Usage:
  python3 story_tracker.py --save       # Save today's narrative state (runs after assessments)
  python3 story_tracker.py --diff       # Compare today vs yesterday, output actionable diff
  python3 story_tracker.py --status     # Show stale narratives
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

log = get_logger("story_tracker")

ASSESS_DIR = SKILL_ROOT / 'assessments'
CRON_DIR = SKILL_ROOT / 'cron_tracking'
STALE_THRESHOLD_DAYS = 3  # after 3 days of same narrative, flag as stale

STORY_FILE = CRON_DIR / 'story_tracker.json'
DIFF_FILE = CRON_DIR / 'story_delta.json'


def extract_lead_narrative(text: str) -> str:
    """Extract the first substantive paragraph as the lead narrative."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for line in lines:
        # Skip headers, empty lines, formatting
        if line.startswith('#') or line.startswith('---') or line.startswith('*'):
            continue
        if len(line) > 80:
            # Take first 200 chars as narrative fingerprint
            return line[:200]
    return text[:200]


def get_narrative_fingerprint(region: str) -> str:
    """Get a fingerprint of today's narrative for comparison."""
    path = ASSESS_DIR / f"{region}.md"
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    return extract_lead_narrative(text)


def save_state():
    """Save today's narrative state for all theatres."""
    state = {}
    for region in THEATRES:
        narrative = get_narrative_fingerprint(region)
        state[region] = {
            "fingerprint": narrative,
            "hash": hashlib.md5(narrative.encode()).hexdigest(),
            "date": datetime.date.today().isoformat(),
            "lead": narrative[:100],
        }
    
    CRON_DIR.mkdir(parents=True, exist_ok=True)
    STORY_FILE.write_text(json.dumps(state, indent=2))
    log.info("Story state saved", theatres=len(state))
    return state


def compute_diffs() -> list[dict]:
    """Compare today's narratives to yesterday's and return actionable diffs."""
    if not STORY_FILE.exists():
        log.info("No previous story state to diff against")
        return []
    
    previous = json.loads(STORY_FILE.read_text())
    today = {}
    for region in THEATRES:
        narrative = get_narrative_fingerprint(region)
        today[region] = {
            "fingerprint": narrative,
            "hash": hashlib.md5(narrative.encode()).hexdigest(),
            "date": datetime.date.today().isoformat(),
        }
    
    diffs = []
    for region in THEATRES:
        prev = previous.get(region, {})
        curr = today.get(region, {})
        
        if not curr.get("fingerprint"):
            diffs.append({
                "region": region,
                "status": "missing",
                "action": "generate",
                "note": "No assessment file for today",
            })
            continue
        
        if not prev.get("fingerprint"):
            diffs.append({
                "region": region,
                "status": "new",
                "action": "none",
                "note": "First assessment for this theatre",
            })
            continue
        
        if curr["hash"] == prev["hash"]:
            # Same story as yesterday — check staleness
            prev_date = prev.get("date", "")
            days_same = 0
            if prev_date:
                try:
                    days_same = (datetime.date.today() - datetime.date.fromisoformat(prev_date)).days
                except:
                    pass
                days_same += 1  # count today too
            
            if days_same >= STALE_THRESHOLD_DAYS:
                diffs.append({
                    "region": region,
                    "status": "stale",
                    "action": "refresh_narrative",
                    "days_same": days_same,
                    "note": f"Same lead narrative for {days_same} days — requires fresh reporting",
                })
            else:
                diffs.append({
                    "region": region,
                    "status": "unchanged",
                    "action": "monitor",
                    "days_same": days_same,
                    "note": f"Same as yesterday (day {days_same})",
                })
        else:
            diffs.append({
                "region": region,
                "status": "changed",
                "action": "none",
                "note": "New narrative detected",
            })
    
    # Save diffs for consumption by other pipeline steps
    DIFF_FILE.write_text(json.dumps({
        "generated": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stale_count": len([d for d in diffs if d["status"] == "stale"]),
        "diffs": diffs,
    }, indent=2))
    
    return diffs


def report_stale() -> list[dict]:
    """Report stale narratives that need attention."""
    diffs = compute_diffs()
    stale = [d for d in diffs if d["status"] == "stale"]
    
    if stale:
        log.warning(f"Stale narratives detected", count=len(stale))
        for s in stale:
            log.warning(f"  {s['region']}: {s['note']}")
    else:
        log.info("No stale narratives")
    
    return stale


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--save", action="store_true", help="Save today's narrative state")
    parser.add_argument("--diff", action="store_true", help="Compute and show diffs")
    parser.add_argument("--status", action="store_true", help="Show stale narratives")
    args = parser.parse_args()
    
    if args.save:
        save_state()
        print(f"Story state saved for {len(THEATRES)} theatres")
        return 0
    
    if args.status:
        stale = report_stale()
        if stale:
            for s in stale:
                print(f"  🔴 {s['region']}: {s['note']}")
        else:
            print("  ✅ No stale narratives")
        return 0
    
    if args.diff:
        diffs = compute_diffs()
        print(f"\n📊 Narrative Diffs ({len(diffs)} theatres):")
        for d in diffs:
            icon = {"changed": "🔄", "stale": "🔴", "unchanged": "⚪", "missing": "❌", "new": "🆕"}
            print(f"  {icon.get(d['status'], '❓')} {d['region']}: {d['note']}")
        return 0
    
    # Default: save + report
    save_state()
    report_stale()
    return 0


if __name__ == "__main__":
    sys.exit(main())
