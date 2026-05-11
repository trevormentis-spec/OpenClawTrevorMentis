#!/usr/bin/env python3
"""StoryTracker — narrative lifecycle management for the daily intel brief.

Solves the "stuck on same stories" problem by:
  1. Recording yesterday's narrative state per theatre
  2. Detecting delta: what changed vs yesterday
  3. Classifying stories into lifecycle stages
  4. Flagging stale content before generation
  5. Injecting "already covered" framing when stories stall

Usage:
  python3 story_tracker.py --save       # Save today's story state (runs after assessments)
  python3 story_tracker.py --diff       # Compare today vs yesterday (runs before assessments)
  python3 story_tracker.py --status     # Show current story lifecycle status
"""
import os, json, datetime, difflib, hashlib
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
ASSESS_DIR = SKILL_ROOT / 'assessments'
CRON_DIR = SKILL_ROOT / 'cron_tracking'
STORY_FILE = CRON_DIR / 'story_tracker.json'
DIFF_FILE = CRON_DIR / 'story_delta.json'

from trevor_config import THEATRE_KEYS as THEATRES

# Story lifecycle stages
EMERGING = "emerging"      # First time this narrative appears
DEVELOPING = "developing"  # Active, changing day-to-day
STALLED = "stalled"        # Same story, nothing new — stale
RESOLVED = "resolved"      # Narrative concluded
LEGACY = "legacy"          # Still relevant as context, not actively developing


# ─── STORY SIGNATURES ────────────────────────────────────
# Each theatre's key stories are identified by unique "signature phrases"
# that should appear in the assessment. If the SAME phrases appear
# day after day, the story is stalled.

THEATRE_SIGNATURES = {
    "europe": [
        "ceasefire", "victory day", "mosfilm", "drone strike",
        "moscow fortress", "putin", "zelensky", "glide bomb",
        "kostyantynivka", "pokrovsk", "fortress belt",
    ],
    "africa": [
        "jnim", "bamako", "kati", "sahel", "ecowas", "mali",
        "offensive", "mopti", "gao", "sevare", "terrorism",
    ],
    "asia": [
        "sindoor", "iaf", "india forgives", "loc", "pakistan",
        "operation sindoor", "anniversary", "strike",
    ],
    "middle_east": [
        "mou", "witkoff", "kushner", "iran", "hormuz", "blockade",
        "operation epic fury", "rubio", "brent", "crude",
    ],
    "north_america": [
        "sinaloa", "sheinbaum", "culiacan", "mazatlan", "rocha moya",
        "indictment", "cartel", "joint operations",
    ],
    "south_america": [
        "maduro", "rodriguez", "ofac", "treasury", "license",
        "miraflores", "venezuela", "transition",
    ],
}


# ─── SIGNATURE EXTRACTION ────────────────────────────────

def extract_signatures(theatre, text):
    """Extract which signature phrases appear in the text."""
    text_lower = text.lower()
    signatures = THEATRE_SIGNATURES.get(theatre, [])
    found = {}
    for sig in signatures:
        count = text_lower.count(sig.lower())
        if count > 0:
            found[sig] = count
    return found


def compute_text_hash(text):
    """Compute a hash of the core content for comparison."""
    # Normalize: lowercase, strip whitespace, remove punctuation
    normalized = re.sub(r'[^\w\s]', '', text.lower())
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return hashlib.md5(normalized[:500].encode()).hexdigest()


def extract_bottom_line(text):
    """Extract the bottom line / BLUF from an assessment."""
    lines = text.split('\n')
    # Look for BLUF or Bottom Line section
    in_bluf = False
    bluf_lines = []
    for line in lines:
        if re.search(r'(bottom\s*line|bluf|key\s*takeaway)', line.lower()):
            in_bluf = True
            continue
        if in_bluf:
            if line.strip() and not line.startswith('#') and not line.startswith('-') and not line.startswith('*'):
                bluf_lines.append(line.strip())
            elif line.startswith('##') or line.startswith('---'):
                break
    return ' '.join(bluf_lines)[:300] if bluf_lines else ""


# ─── STORY TRACKER ───────────────────────────────────────

def load_tracker():
    """Load the story tracker."""
    if STORY_FILE.exists():
        return json.loads(STORY_FILE.read_text())
    return {"history": [], "latest": {}}


def save_tracker(data):
    """Save the story tracker."""
    CRON_DIR.mkdir(parents=True, exist_ok=True)
    STORY_FILE.write_text(json.dumps(data, indent=2))


# ─── SAVE TODAY'S STATE ───────────────────────────────────

def save_today_state():
    """After assessments are generated, record today's narrative state."""
    date_str = datetime.date.today().isoformat()
    tracker = load_tracker()

    state = {
        "date": date_str,
        "theatres": {},
        "summary": {},
    }

    for theatre in THEATRES:
        ass = ASSESS_DIR / f"{theatre}.md"
        if not ass.exists():
            continue

        text = ass.read_text()
        sigs = extract_signatures(theatre, text)
        word_count = len(text.split())
        bottom_line = extract_bottom_line(text)
        text_hash = compute_text_hash(text)

        # Count sources (same logic as briefometer)
        import re
        sources = set()
        source_patterns = {
            "news": ["bbc", "cnn", "reuters", "ap ", "nyt ", "axios", "al jazeera", "npr",
                     "bloomberg", "wsj", "financial times", "the diplomat", "kyiv post"],
            "academic": ["isw", "critical threats", "csis", "rand", "chatham", "iiss", "aei"],
            "official": ["pentagon", "white house", "centcom", "treasury", "ofac",
                         "state department", "nato", "ecowas", "un "],
            "intel": ["shurkin", "acled", "polymarket", "kalshi", "ukmto", "jmic"],
        }
        for cat, keywords in source_patterns.items():
            for kw in keywords:
                if kw.lower() in text.lower():
                    sources.add(kw)

        state["theatres"][theatre] = {
            "word_count": word_count,
            "signatures": sigs,
            "signature_hash": hashlib.md5(json.dumps(sigs, sort_keys=True).encode()).hexdigest(),
            "text_hash": text_hash,
            "bottom_line": bottom_line,
            "sources": list(sources),
            "source_count": len(sources),
        }

    # Overall summary
    total_words = sum(t.get("word_count", 0) for t in state["theatres"].values())
    total_sources = sum(t.get("source_count", 0) for t in state["theatres"].values())
    state["summary"] = {
        "total_words": total_words,
        "total_sources": total_sources,
        "theatre_count": len(state["theatres"]),
    }

    # Add to history (keep last 7 days)
    tracker["history"] = [h for h in tracker.get("history", []) if h.get("date") != date_str]
    tracker["history"].append(state)
    tracker["history"] = sorted(tracker["history"], key=lambda x: x["date"])[-7:]

    # Update latest
    tracker["latest"] = state

    save_tracker(tracker)
    print(f"✓ Saved story state for {date_str}")
    print(f"  {total_words} words across {len(state['theatres'])} theatres")
    print(f"  {total_sources} unique sources cited")

    return state


# ─── DIFF ANALYSIS ────────────────────────────────────────

def diff_yesterday():
    """Compare today's state against yesterday's. Run BEFORE assessments."""
    tracker = load_tracker()
    history = tracker.get("history", [])

    if len(history) < 2:
        print("ℹ No previous day to compare against.")
        return {}

    today = history[-1]
    yesterday = history[-2]

    t_date = today["date"]
    y_date = yesterday["date"]

    print(f"\n=== Story Delta: {y_date} → {t_date} ===\n")

    deltas = {}
    stalled_count = 0
    changed_count = 0

    for theatre in THEATRES:
        t_state = today["theatres"].get(theatre, {})
        y_state = yesterday["theatres"].get(theatre, {})

        if not t_state or not y_state:
            print(f"  {theatre}: No previous state to compare")
            deltas[theatre] = {"status": "unknown"}
            continue

        t_sigs = t_state.get("signatures", {})
        y_sigs = y_state.get("signatures", {})
        t_bottom = t_state.get("bottom_line", "")
        y_bottom = y_state.get("bottom_line", "")

        # Compare signature overlap
        all_keys = set(list(t_sigs.keys()) + list(y_sigs.keys()))
        overlap = sum(1 for k in all_keys if k in t_sigs and k in y_sigs)
        new_keys = [k for k in t_sigs if k not in y_sigs]
        dropped_keys = [k for k in y_sigs if k not in t_sigs]

        # Word count delta
        wc_delta = t_state.get("word_count", 0) - y_state.get("word_count", 0)

        # Source delta
        t_src = t_state.get("sources", [])
        y_src = y_state.get("sources", [])
        new_sources = [s for s in t_src if s not in y_src]
        dropped_sources = [s for s in y_src if s not in t_src]

        # Determine lifecycle stage
        total_sigs = max(len(t_sigs), 1)
        stall_ratio = overlap / total_sigs if total_sigs > 0 else 0

        if stall_ratio > 0.8 and len(new_keys) == 0:
            lifecycle = STALLED
            stalled_count += 1
            status_icon = "⚠ STALLED"
        elif len(new_keys) >= 2 or len(new_sources) >= 2:
            lifecycle = DEVELOPING
            changed_count += 1
            status_icon = "→ DEVELOPING"
        elif len(new_keys) >= 1:
            lifecycle = DEVELOPING
            changed_count += 1
            status_icon = "→ DEVELOPING (minor)"
        else:
            lifecycle = STALLED
            stalled_count += 1
            status_icon = "⚠ STALLED"

        delta = {
            "status": lifecycle,
            "signature_overlap": overlap,
            "new_signatures": new_keys,
            "dropped_signatures": dropped_keys,
            "word_count_delta": wc_delta,
            "new_sources": new_sources,
            "dropped_sources": dropped_sources,
            "bottom_line_changed": t_bottom != y_bottom,
        }
        deltas[theatre] = delta

        print(f"  {theatre:<16} {status_icon}")
        if new_keys:
            print(f"    New signatures: {', '.join(new_keys)}")
        if dropped_keys:
            print(f"    Dropped: {', '.join(dropped_keys)}")
        if wc_delta != 0:
            print(f"    Word count: {wc_delta:+d}")
        if new_sources:
            print(f"    New sources: {', '.join(new_sources)}")
        print()

    # Summary
    print(f"  Summary: {changed_count} changing  |  {stalled_count} stalled  |  {len(THEATRES)} total\n")

    result = {
        "date": t_date,
        "previous_date": y_date,
        "deltas": deltas,
        "stalled": stalled_count,
        "changing": changed_count,
    }

    # Save delta for use by assessment generator
    CRON_DIR.mkdir(parents=True, exist_ok=True)
    DIFF_FILE.write_text(json.dumps(result, indent=2))

    return result


# ─── STATUS REPORT ────────────────────────────────────────

def show_status():
    """Show current story lifecycle dashboard."""
    tracker = load_tracker()
    latest = tracker.get("latest", {})
    history = tracker.get("history", [])

    if not latest:
        print("No story data yet. Run with --save first.")
        return

    print("\n" + "=" * 72)
    print("  📰 STORY TRACKER — Narrative Lifecycle Status")
    print("=" * 72)

    print(f"\n  Date: {latest.get('date', 'N/A')}")
    print(f"  History: {len(history)} days tracked")
    print(f"  {'─' * 60}")

    for theatre in THEATRES:
        t = latest.get("theatres", {}).get(theatre, {})
        if not t:
            continue

        sigs = t.get("signatures", {})
        sources = t.get("sources", [])
        words = t.get("word_count", 0)
        bottom = t.get("bottom_line", "")[:80]

        # Check history for lifecycle
        lifecycle = EMERGING
        if len(history) >= 2:
            today = history[-1]
            yesterday = history[-2]
            t_today = today.get("theatres", {}).get(theatre, {})
            t_yest = yesterday.get("theatres", {}).get(theatre, {})
            if t_today and t_yest:
                t_hash_today = t_today.get("signature_hash", "")
                t_hash_yest = t_yest.get("signature_hash", "")
                if t_hash_today == t_hash_yest:
                    lifecycle = STALLED
                else:
                    lifecycle = DEVELOPING

        icon = {"emerging": "🆕", "developing": "📈", "stalled": "⚠️",
                "resolved": "✅", "legacy": "💭"}.get(lifecycle, "❓")

        print(f"\n  {icon} {theatre.upper()} — {lifecycle.upper()}")
        print(f"     Words: {words}  |  Sources: {t.get('source_count', 0)}")
        if sigs:
            print(f"     Key terms: {', '.join(list(sigs.keys())[:5])}")
        if bottom:
            print(f"     Bottom line: {bottom}...")

    stalled = sum(1 for t in THEATRES if latest.get("theatres", {}).get(t, {}).get("bottom_line", "") == "")
    print(f"\n  {'─' * 60}")
    print(f"  Run with --diff to see what changed since yesterday")
    print(f"  Run with --save after assessments to record state")
    print("=" * 72 + "\n")


# ─── MAIN ────────────────────────────────────────────────

import re  # needed for text processing

def main():
    import argparse
    parser = argparse.ArgumentParser(description="StoryTracker — narrative lifecycle management")
    parser.add_argument('--save', action='store_true', help='Save today\'s story state')
    parser.add_argument('--diff', action='store_true', help='Compare today vs yesterday')
    parser.add_argument('--status', action='store_true', help='Show lifecycle status')
    args = parser.parse_args()

    if args.save:
        save_today_state()
    elif args.diff:
        diff_yesterday()
    elif args.status:
        show_status()
    else:
        # Default: show what's possible
        print("StoryTracker — Narrative lifecycle for the daily intel brief")
        print()
        print("Commands:")
        print("  --save     Save today's story state (run after assessments)")
        print("  --diff     Compare today vs yesterday (run BEFORE assessments)")
        print("  --status   Show current lifecycle status")
        print()
        print("Used in pipeline as:")
        print("  Step 1: story_tracker.py --diff  (detect stale stories)")
        print("  Step 2: [generate assessments with delta data]")
        print("  Step 3: story_tracker.py --save  (record today's state)")


if __name__ == "__main__":
    main()
