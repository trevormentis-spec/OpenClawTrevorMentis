#!/usr/bin/env python3
"""
Weekly meta-review — Loop 7 / Loop 8 of the Mexico pivot directive.

Compiles the past 7 days of:
  - autonomy-tracker.json          (what Trevor actually did)
  - calibration-tracking.json      (how accurate it was)
  - collection-state.json          (source utilization, gaps)
  - framework-adaptations.md       (infrastructure changes)
  - tech-debt.md                   (known carry-over issues)
  - skill-generation-log.jsonl     (stubs drafted, completion rate)
  - exports/mexico-news-scan-*.json (last 7 days of Mexico ingest)

…and writes:
  analyst/reflections/weekly/YYYY-WW.md

The review picks ONE explicit focus for the coming week and writes it
into the report as "NEXT WEEK FOCUS:". This is the autonomous
direction-setting Trevor was missing.

Run weekly (e.g. Friday 18:00 PT) via the daily cron's day-of-week check
or a dedicated weekly cron entry.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SEM = REPO_ROOT / "brain" / "memory" / "semantic"
EXPORTS = REPO_ROOT / "exports"
REFLECTIONS_DIR = REPO_ROOT / "analyst" / "reflections" / "weekly"

CAL_FILE = SEM / "calibration-tracking.json"
AUTONOMY_FILE = SEM / "autonomy-tracker.json"
COLLECTION_FILE = SEM / "collection-state.json"
FRAMEWORK_FILE = SEM / "framework-adaptations.md"
TECHDEBT_FILE = SEM / "tech-debt.md"
SKILLGEN_LOG = SEM / "skill-generation-log.jsonl"


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[meta-review {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(p: pathlib.Path) -> dict | list | None:
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        log(f"malformed JSON at {p}")
        return None


def load_jsonl(p: pathlib.Path) -> list[dict]:
    if not p.exists():
        return []
    out = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def head(p: pathlib.Path, max_lines: int = 60) -> str:
    if not p.exists():
        return f"_(missing: {p.relative_to(REPO_ROOT)})_"
    return "\n".join(p.read_text().splitlines()[:max_lines])


def last_n_days(items: list[dict], date_key: str, days: int = 7) -> list[dict]:
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    kept = []
    for it in items:
        v = it.get(date_key, "")
        try:
            t = dt.datetime.fromisoformat(v.replace("Z", "+00:00"))
            if t.tzinfo is None:
                t = t.replace(tzinfo=dt.timezone.utc)
        except (ValueError, AttributeError):
            continue
        if t >= cutoff:
            kept.append(it)
    return kept


def mexico_scan_summary(days: int = 7) -> dict:
    if not EXPORTS.exists():
        return {"files": 0, "articles": 0, "by_source": {}}
    cutoff = dt.date.today() - dt.timedelta(days=days)
    by_source: dict[str, int] = {}
    files = 0
    articles = 0
    for f in sorted(EXPORTS.glob("mexico-news-scan-*.json")):
        try:
            stem_date = dt.date.fromisoformat(f.stem.split("mexico-news-scan-")[-1])
        except ValueError:
            continue
        if stem_date < cutoff:
            continue
        files += 1
        try:
            doc = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        for r in doc.get("results", []):
            n = len(r.get("articles", []))
            articles += n
            by_source[r.get("name", "?")] = by_source.get(r.get("name", "?"), 0) + n
    return {"files": files, "articles": articles, "by_source": by_source}


def pick_focus(cal: dict | None, scan: dict, skillgen: list[dict],
               collection: dict | None) -> tuple[str, str]:
    """Return (focus_title, rationale) for next week."""
    candidates: list[tuple[int, str, str]] = []

    if cal:
        for region, stats in (cal.get("by_region") or {}).items():
            total = stats.get("total", 0)
            correct = stats.get("correct", 0)
            incorrect = stats.get("incorrect", 0)
            resolved = correct + incorrect
            if resolved >= 5:
                acc = correct / resolved
                if acc < 0.55:
                    candidates.append((
                        int((0.55 - acc) * 1000),
                        f"Recalibrate {region} forecasting",
                        f"{region} accuracy {int(acc*100)}% over {resolved} resolved judgments — below 55% floor.",
                    ))

    if scan["articles"] < 20 * scan["files"] and scan["files"] >= 3:
        candidates.append((
            150,
            "Improve Mexico ingest yield",
            f"Only {scan['articles']} articles across {scan['files']} scan days — sources may be misconfigured or blocked.",
        ))

    stub_count = sum(1 for s in skillgen if s.get("status") == "stub")
    if stub_count >= 3:
        candidates.append((
            120,
            f"Complete {stub_count} pending skill stubs",
            "Skill-generator stubs are accumulating without implementation — blocking capability growth.",
        ))

    if collection:
        gaps = collection.get("region_gaps") or []
        for g in gaps:
            candidates.append((
                100,
                f"Close collection gap: {g}",
                f"Persistent collection gap in {g} reported by collection_state.",
            ))

    if not candidates:
        return (
            "Deepen one Mexico theme (analyst's pick)",
            "No quantitative trigger fired this week — default to one-theme deep-dive (cartel succession dynamics, Pemex operational realism, or Banxico/peso pressure points).",
        )

    candidates.sort(reverse=True)
    _, focus, rationale = candidates[0]
    return focus, rationale


def render_markdown(week_id: str, cal: dict | None, autonomy: dict | None,
                     collection: dict | None, scan: dict,
                     skillgen: list[dict], focus: str, rationale: str) -> str:
    today = dt.date.today().isoformat()
    lines: list[str] = []
    lines.append(f"# Weekly Meta-Review — {week_id}")
    lines.append("")
    lines.append(f"_Generated {today} by `scripts/weekly_meta_review.py`._")
    lines.append("")
    lines.append("## LOOP STATUS")
    lines.append("")
    if autonomy:
        actions = autonomy.get("actions", []) if isinstance(autonomy, dict) else []
        recent = last_n_days(actions, "ts", 7) if actions else []
        lines.append(f"- Autonomous actions logged this week: **{len(recent)}**")
    else:
        lines.append("- Autonomy tracker missing or empty.")
    lines.append(f"- Mexico scans run this week: **{scan['files']}** files, **{scan['articles']}** articles")
    if scan["by_source"]:
        top = sorted(scan["by_source"].items(), key=lambda x: -x[1])[:6]
        lines.append("  - Top sources: " + ", ".join(f"{n}={c}" for n, c in top))
    lines.append("")

    lines.append("## CALIBRATION")
    lines.append("")
    if cal:
        total = cal.get("total_judgments", 0)
        correct = cal.get("correct", 0)
        incorrect = cal.get("incorrect", 0)
        unresolved = cal.get("unresolved", 0)
        resolved = correct + incorrect
        pct = round(correct / resolved * 100, 1) if resolved else "n/a"
        lines.append(f"- Running: {correct}/{total} correct ({pct}%) — {incorrect} wrong, {unresolved} unresolved")
        bands = cal.get("by_confidence_band", {})
        if bands:
            lines.append("- Per-band:")
            for band, stats in bands.items():
                t = stats.get("total", 0)
                c = stats.get("correct", 0)
                i = stats.get("incorrect", 0)
                r = c + i
                if r >= 1:
                    lines.append(f"  - **{band}**: {c}/{r} resolved correct ({int(c/r*100)}%), {t} total")
    else:
        lines.append("- No calibration data yet.")
    lines.append("")

    lines.append("## CAPABILITY GAPS — STUBS DRAFTED")
    lines.append("")
    recent_stubs = last_n_days(skillgen, "ts", 14)
    if recent_stubs:
        for s in recent_stubs:
            lines.append(f"- `{s.get('name','?')}` — {s.get('status','?')} — _{s.get('gap','')}_")
    else:
        lines.append("- No skill stubs drafted in the last 14 days.")
    lines.append("")

    lines.append("## FRAMEWORK ADAPTATIONS (last 60 lines of log)")
    lines.append("")
    lines.append("```")
    lines.append(head(FRAMEWORK_FILE, 60))
    lines.append("```")
    lines.append("")

    lines.append("## TECH DEBT (top of list)")
    lines.append("")
    lines.append("```")
    lines.append(head(TECHDEBT_FILE, 40))
    lines.append("```")
    lines.append("")

    lines.append("## NEXT WEEK FOCUS")
    lines.append("")
    lines.append(f"**{focus}**")
    lines.append("")
    lines.append(f"_Why_: {rationale}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("_Trevor is expected to lean into this focus across heartbeat cycles and the daily brief — "
                 "but is also expected to deviate and explain if a higher-priority signal arrives mid-week._")
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true",
                   help="print to stdout without writing")
    args = p.parse_args()

    cal = load_json(CAL_FILE)
    autonomy = load_json(AUTONOMY_FILE)
    collection = load_json(COLLECTION_FILE)
    scan = mexico_scan_summary(7)
    skillgen = load_jsonl(SKILLGEN_LOG)

    focus, rationale = pick_focus(cal, scan, skillgen, collection)

    today = dt.date.today()
    iso = today.isocalendar()
    week_id = f"{iso.year}-W{iso.week:02d}"
    md = render_markdown(week_id, cal, autonomy, collection, scan, skillgen, focus, rationale)

    if args.dry_run:
        sys.stdout.write(md)
        return 0

    REFLECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    out = REFLECTIONS_DIR / f"{week_id}.md"
    out.write_text(md)
    log(f"wrote {out} — focus: {focus}")
    print(str(out.relative_to(REPO_ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
