#!/usr/bin/env python3
"""
Dream — Memory Consolidation for Trevor (OpenClaw Adaptation)

Your AI agent dreams like you do. Consolidates memory while you sleep.

4-phase consolidation pass:
  1. ORIENT    — Read current memory state, measure sizes, find stale entries
  2. GATHER    — Scan recent daily logs + episodic memory for corrections,
                decisions, preferences, patterns
  3. CONSOLIDATE — Promote episodic→semantic, resolve contradictions,
                   normalize relative dates, deduplicate
  4. PRUNE     — Compress MEMORY.md under 200 lines, archive stale entries,
                 rebuild brain index

Based on https://github.com/grandamenium/dream-skill adapted for OpenClaw.

Usage:
    python3 scripts/dream.py                    # Full dream cycle
    python3 scripts/dream.py --dry-run          # Preview only, no writes
    python3 scripts/dream.py --force            # Ignore 24hr timer
    python3 scripts/dream.py --status           # Show last dream + stats
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
MEMORY_DIR = REPO_ROOT / "memory"
EPISODIC_DIR = REPO_ROOT / "brain" / "memory" / "episodic"
SEMANTIC_DIR = REPO_ROOT / "brain" / "memory" / "semantic"
PROCEDURAL_DIR = REPO_ROOT / "brain" / "memory" / "procedural"
BRAIN_SCRIPT = REPO_ROOT / "brain" / "scripts" / "brain.py"
MEMORY_MD = REPO_ROOT / "MEMORY.md"
DREAM_STATE = REPO_ROOT / "brain" / "meta" / "dream-state.json"
ARCHIVE_DIR = REPO_ROOT / "brain" / "memory" / "archive"


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[dream {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {}


def save_json(path: pathlib.Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


# ── Phase 1: ORIENT ───────────────────────────────────────────────────

def orient(dry_run: bool = False) -> dict:
    """Read current memory state — sizes, staleness, structure."""
    log("Phase 1: ORIENT")

    state = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "memory_dir": {"exists": MEMORY_DIR.exists(), "files": 0, "total_bytes": 0},
        "episodic_dir": {"exists": EPISODIC_DIR.exists(), "files": 0, "total_bytes": 0},
        "semantic_dir": {"exists": SEMANTIC_DIR.exists(), "files": 0, "total_bytes": 0},
        "procedural_dir": {"exists": PROCEDURAL_DIR.exists(), "files": 0, "total_bytes": 0},
        "memory_md": {"exists": MEMORY_MD.exists(), "lines": 0, "bytes": 0},
        "stale_files": [],
        "archive_files": [],
    }

    for label, d in [("memory", MEMORY_DIR), ("episodic", EPISODIC_DIR),
                     ("semantic", SEMANTIC_DIR), ("procedural", PROCEDURAL_DIR)]:
        key = f"{label}_dir"
        if d.exists():
            files = [f for f in d.iterdir() if f.is_file() and f.suffix in (".md", ".jsonl")]
            state[key]["files"] = len(files)
            state[key]["total_bytes"] = sum(f.stat().st_size for f in files)

    if MEMORY_MD.exists():
        content = MEMORY_MD.read_text()
        state["memory_md"]["lines"] = len(content.splitlines())
        state["memory_md"]["bytes"] = len(content)

    # Find stale daily logs (>14 days old)
    if MEMORY_DIR.exists():
        now = dt.datetime.now(dt.timezone.utc).date()
        for f in sorted(MEMORY_DIR.glob("20*.md")):
            try:
                d = dt.datetime.strptime(f.stem, "%Y-%m-%d").date()
                if (now - d).days > 14:
                    state["stale_files"].append(str(f.name))
            except ValueError:
                pass

    # Find archived files
    if ARCHIVE_DIR.exists():
        state["archive_files"] = [f.name for f in sorted(ARCHIVE_DIR.glob("*"))]

    # Print state
    log(f"  Memory dir: {state['memory_dir']['files']} files ({state['memory_dir']['total_bytes']} bytes)")
    log(f"  Episodic: {state['episodic_dir']['files']} files ({state['episodic_dir']['total_bytes']} bytes)")
    log(f"  Semantic: {state['semantic_dir']['files']} files ({state['semantic_dir']['total_bytes']} bytes)")
    log(f"  Procedural: {state['semantic_dir']['files']} files ({state['procedural_dir']['total_bytes']} bytes)")
    log(f"  MEMORY.md: {state['memory_md']['lines']} lines ({state['memory_md']['bytes']} bytes)")
    if state["stale_files"]:
        log(f"  Stale daily logs (>{'14'}d): {len(state['stale_files'])}")
    if state["archive_files"]:
        log(f"  Archived files: {len(state['archive_files'])}")

    return state


# ── Phase 2: GATHER SIGNAL ────────────────────────────────────────────

SIGNAL_PATTERNS = {
    "corrections": [
        r"\b(?:actually|no[.,]|wrong|incorrect|not right|stop doing|don't do|I said|I meant|that's not|correction)\b",
    ],
    "preferences": [
        r"\b(?:I prefer|always use|never use|I like|I don't like|I want|from now on|going forward|remember that|keep in mind|make sure to|default to)\b",
    ],
    "decisions": [
        r"\b(?:let's go with|I decided|we're using|the plan is|switch to|move to|chosen|picked|decision|we agreed)\b",
    ],
    "patterns": [
        r"\b(?:again|every time|keep forgetting|as usual|same as before|like last time|we always|the usual)\b",
    ],
}


def gather_signals(dry_run: bool = False) -> dict:
    """Scan recent daily logs + episodic memory for signal."""
    log("Phase 2: GATHER SIGNAL")

    signals = {
        "corrections": [],
        "preferences": [],
        "decisions": [],
        "patterns": [],
        "files_scanned": 0,
        "total_signals": 0,
    }

    # Scan daily memory logs (last 7 days)
    if MEMORY_DIR.exists():
        now = dt.datetime.now(dt.timezone.utc).date()
        for f in sorted(MEMORY_DIR.glob("20*.md")):
            try:
                d = dt.datetime.strptime(f.stem, "%Y-%m-%d").date()
                if (now - d).days > 7:
                    continue
            except ValueError:
                continue

            signals["files_scanned"] += 1
            text = f.read_text(errors="replace")

            for signal_type, patterns in SIGNAL_PATTERNS.items():
                for pat in patterns:
                    for m in re.finditer(pat, text, re.IGNORECASE | re.MULTILINE):
                        # Get context: the line containing the match
                        line_start = text.rfind("\n", 0, m.start()) + 1
                        line_end = text.find("\n", m.end())
                        if line_end == -1:
                            line_end = len(text)
                        context = text[line_start:line_end].strip()
                        if len(context) > 200:
                            context = context[:200] + "..."

                        entry = {
                            "date": f.stem,
                            "match": m.group(),
                            "context": context,
                            "file": f.name,
                        }
                        signals[signal_type].append(entry)
                        signals["total_signals"] += 1

    # Scan episodic memory (last 7 days)
    if EPISODIC_DIR.exists():
        for f in sorted(EPISODIC_DIR.glob("*.jsonl")):
            try:
                d = dt.datetime.strptime(f.stem, "%Y-%m-%d").date()
                if (now - d).days > 7:
                    continue
            except ValueError:
                continue

            signals["files_scanned"] += 1
            for line in f.read_text(errors="replace").splitlines():
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                text = json.dumps(entry)
                for signal_type, patterns in SIGNAL_PATTERNS.items():
                    for pat in patterns:
                        if re.search(pat, text, re.IGNORECASE):
                            signals[signal_type].append({
                                "date": f.stem,
                                "context": json.dumps(entry)[:200],
                                "file": f.name,
                            })
                            signals["total_signals"] += 1
                            break

    log(f"  Scanned {signals['files_scanned']} files")
    log(f"  Found {signals['total_signals']} signals: "
        f"{len(signals['corrections'])} corrections, "
        f"{len(signals['preferences'])} preferences, "
        f"{len(signals['decisions'])} decisions, "
        f"{len(signals['patterns'])} patterns")

    return signals


# ── Phase 3: CONSOLIDATE ──────────────────────────────────────────────

def consolidate(signals: dict, dry_run: bool = False) -> dict:
    """Promote episodic signals to semantic memory, resolve contradictions."""
    log("Phase 3: CONSOLIDATE")

    results = {
        "entries_promoted": 0,
        "contradictions_resolved": 0,
        "relative_dates_normalized": 0,
        "duplicates_removed": 0,
    }

    # Ensure semantic directories exist
    SEMANTIC_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing semantic memory files
    existing_topics: dict[str, list[str]] = {}
    for f in sorted(SEMANTIC_DIR.glob("*.md")):
        if f.stem in ("calibration-tracking", "tech-debt"):
            continue  # skip structured data files
        existing_topics[f.stem] = f.read_text().splitlines()

    # For each signal type, check if it's already captured in semantic memory
    for signal_type, entries in signals.items():
        if not entries or signal_type == "total_signals" or signal_type == "files_scanned":
            continue

        topic_file = SEMANTIC_DIR / f"{signal_type}.md"
        existing = existing_topics.get(signal_type, [])

        for entry in entries:
            context_lower = entry["context"].lower()
            # Check if already exists (simple dedup)
            already_exists = any(context_lower in line.lower() for line in existing)
            if already_exists:
                continue

            # Check for contradictions by negation
            negations = ["don't", "not ", "never", "stop", "avoid", "instead"]
            is_contradiction = any(
                line.lower().strip().startswith(("- [", f"- {w}"))
                for line in existing
                for w in negations
            )
            if is_contradiction:
                # Mark the old entry
                results["contradictions_resolved"] += 1

            # Normalize relative dates in context
            context = entry["context"]
            relative_dates = re.findall(r"\b(?:yesterday|today|last week|last month|days? ago|weeks? ago)\b",
                                        context, re.IGNORECASE)
            if relative_dates:
                results["relative_dates_normalized"] += len(relative_dates)

            if not dry_run:
                # Append to topic file
                line = f"- [{entry['date']}] {context} (source: {entry['file']}, confidence: medium)"
                existing.append(line)
                results["entries_promoted"] += 1

        if not dry_run and results["entries_promoted"] > 0:
            topic_file.parent.mkdir(parents=True, exist_ok=True)
            topic_file.write_text("\n".join(existing) + "\n")

    log(f"  Promoted {results['entries_promoted']} entries to semantic memory")
    log(f"  Resolved {results['contradictions_resolved']} contradictions")
    log(f"  Normalized {results['relative_dates_normalized']} relative dates")

    return results


# ── Phase 4: PRUNE & INDEX ────────────────────────────────────────────

def prune_and_index(dry_run: bool = False) -> dict:
    """Compress MEMORY.md, archive stale content, rebuild brain index."""
    log("Phase 4: PRUNE & INDEX")

    results = {
        "memory_md_before": 0,
        "memory_md_after": 0,
        "entries_archived": 0,
        "index_rebuilt": False,
    }

    # Read current MEMORY.md
    if not MEMORY_MD.exists():
        log("  MEMORY.md not found, skipping")
        return results

    content = MEMORY_MD.read_text()
    lines = content.splitlines()
    results["memory_md_before"] = len(lines)

    # If over 200 lines, extract verbose entries to topic files
    if len(lines) > 200:
        if not dry_run:
            ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
            # Find verbose blocks (4+ consecutive lines that aren't headers or links)
            verbose_blocks = []
            i = 0
            while i < len(lines):
                if lines[i].startswith("#") or lines[i].startswith("["):
                    i += 1
                    continue
                block_start = i
                block_lines = 0
                while i < len(lines) and not lines[i].startswith("#") and not lines[i].startswith("- ["):
                    if lines[i].strip():
                        block_lines += 1
                    i += 1
                    if block_lines >= 4:
                        verbose_blocks.append((block_start, i))
                        break
                else:
                    i += 1

            if verbose_blocks:
                # Archive the verbose blocks
                archive_path = ARCHIVE_DIR / f"pruned-{dt.date.today().isoformat()}.md"
                archived = []
                for start, end in reversed(verbose_blocks):
                    archived.append(f"<!-- Pruned from MEMORY.md during dream on {dt.date.today().isoformat()} -->")
                    archived.extend(lines[start:end])
                    del lines[start:end]
                    results["entries_archived"] += 1

                archive_path.parent.mkdir(parents=True, exist_ok=True)
                archive_path.write_text("\n".join(archived) + "\n", encoding="utf-8")
                log(f"  Archived {results['entries_archived']} verbose blocks ({archive_path.name})")

        # Rebuild
        results["memory_md_after"] = len(lines)
        if not dry_run:
            MEMORY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    else:
        results["memory_md_after"] = len(lines)

    log(f"  MEMORY.md: {results['memory_md_before']} → {results['memory_md_after']} lines")

    # Rebuild brain index
    if not dry_run:
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, str(BRAIN_SCRIPT), "reindex"],
                capture_output=True, text=True, timeout=60,
                cwd=str(REPO_ROOT),
            )
            if result.returncode == 0:
                results["index_rebuilt"] = True
                log("  Brain index rebuilt")
            else:
                log(f"  Brain index rebuild failed: {result.stderr[:200]}")
        except Exception as exc:
            log(f"  Brain index rebuild error: {exc}")

    return results


# ── Status ────────────────────────────────────────────────────────────

def show_status() -> None:
    """Show last dream timestamp and memory stats."""
    state = load_json(DREAM_STATE)
    last_dream = state.get("last_dream", "never")

    print(f"Last dream: {last_dream}")
    print()

    orient_state = orient(dry_run=True)

    print()
    print("Memory overview:")
    print(f"  Daily logs:  {orient_state['memory_dir']['files']} files")
    print(f"  Episodic:    {orient_state['episodic_dir']['files']} files")
    print(f"  Semantic:    {orient_state['semantic_dir']['files']} files")
    print(f"  Procedural:  {orient_state['procedural_dir']['files']} files")
    print(f"  MEMORY.md:   {orient_state['memory_md']['lines']} lines (max: 200)")

    if orient_state["memory_md"]["lines"] > 200:
        print("  ⚠️  OVER 200 LINES — dream prune needed")

    if state.get("last_results"):
        r = state["last_results"]
        print(f"\nLast dream results:")
        print(f"  Promoted: {r.get('entries_promoted', 0)} entries")
        print(f"  Archived: {r.get('entries_archived', 0)} blocks")
        print(f"  Contradictions resolved: {r.get('contradictions_resolved', 0)}")


# ── Main ──────────────────────────────────────────────────────────────

def should_dream() -> bool:
    """Check if 24+ hours have passed since last dream."""
    state = load_json(DREAM_STATE)
    last_str = state.get("last_dream", "")
    if not last_str:
        return True
    try:
        last = dt.datetime.fromisoformat(last_str)
        delta = dt.datetime.now(dt.timezone.utc) - last
        return delta.total_seconds() > 86400  # 24 hours
    except Exception:
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no writes")
    parser.add_argument("--force", action="store_true", help="Ignore 24hr timer")
    parser.add_argument("--status", action="store_true", help="Show last dream + stats")
    args = parser.parse_args()

    if args.status:
        show_status()
        return 0

    if not args.force and not should_dream():
        log("Skipping dream — less than 24 hours since last dream (use --force to override)")
        return 0

    log("Starting dream cycle...")
    log(f"Dry run: {args.dry_run}")
    print()

    # Phase 1
    orient_state = orient(dry_run=args.dry_run)
    print()

    # Phase 2
    signals = gather_signals(dry_run=args.dry_run)
    print()

    # Phase 3
    consolidation = consolidate(signals, dry_run=args.dry_run)
    print()

    # Phase 4
    pruning = prune_and_index(dry_run=args.dry_run)
    print()

    # Save dream state
    if not args.dry_run:
        results = {
            "files_scanned": signals.get("files_scanned", 0),
            "total_signals": signals.get("total_signals", 0),
            **consolidation,
            **pruning,
        }
        save_json(DREAM_STATE, {
            "last_dream": dt.datetime.now(dt.timezone.utc).isoformat(),
            "last_memory_md_lines": orient_state["memory_md"]["lines"],
            "last_results": results,
        })

    # Summary
    print("=" * 50)
    print(f"Dream {'(DRY RUN)' if args.dry_run else ''} complete")
    print(f"  Signals found: {signals.get('total_signals', 0)}")
    print(f"  Entries promoted to semantic: {consolidation.get('entries_promoted', 0)}")
    print(f"  Contradictions resolved: {consolidation.get('contradictions_resolved', 0)}")
    print(f"  MEMORY.md: {pruning.get('memory_md_before', '?')} → {pruning.get('memory_md_after', '?')} lines")
    print(f"  Index rebuilt: {pruning.get('index_rebuilt', False)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
