#!/usr/bin/env python3
"""Generate weekly quality report from quality-metrics.json snapshots.

Compares current week vs previous week on:
  - Feed health %
  - Calibration accuracy
  - Provider reliability
  - Collection activity
  - Cost burn rate

Output: docs/reports/quality-weekly-YYYY-MM-DD.md

Environment: No special vars required (reads from filesystem).
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
METRICS_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "quality-metrics.json"
OUTPUT_DIR = REPO_ROOT / "docs" / "reports"


def load_metrics() -> dict | None:
    """Load quality-metrics.json."""
    if not METRICS_FILE.exists():
        print(f"ERROR: quality-metrics.json not found at {METRICS_FILE}", file=sys.stderr)
        return None
    try:
        return json.loads(METRICS_FILE.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"ERROR: Failed to parse {METRICS_FILE}: {e}", file=sys.stderr)
        return None


def find_snapshots(metrics: dict) -> tuple[dict | None, dict | None]:
    """Return (current_snapshot, comparison_snapshot) — latest and 7 days prior."""
    snapshots = metrics.get("snapshots", [])
    if not snapshots:
        return None, None

    current = snapshots[-1]

    if len(snapshots) < 2:
        return current, None

    # Find snapshot from ~7 days ago
    current_ts = current.get("generated_at", "")
    try:
        current_dt = datetime.fromisoformat(current_ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return current, snapshots[-2]  # fallback to previous snapshot

    target_dt = current_dt - timedelta(days=7)
    best = None
    best_diff = timedelta(days=365)

    for s in snapshots[:-1]:  # exclude current
        ts = s.get("generated_at", "")
        try:
            dt_s = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            continue
        diff = abs(dt_s - target_dt)
        if diff < best_diff:
            best_diff = diff
            best = s

    return current, best


def _fmt_pct(v: float) -> str:
    """Format a percentage with a trend sign and arrow."""
    return f"{v:.1f}%"


def _trend_arrow(current: float, previous: float | None) -> str:
    """Return a trend arrow: ↑ ↓ →."""
    if previous is None:
        return "—"
    diff = current - previous
    if diff > 2:
        return "⬆"
    if diff < -2:
        return "⬇"
    return "➡"


def _fmt_delta(current: float, previous: float | None) -> str:
    """Format a delta (positive or negative)."""
    if previous is None:
        return "—"
    diff = current - previous
    sign = "+" if diff > 0 else ""
    return f"{sign}{diff:.1f}pp"


def _extract_cost(snapshot: dict) -> float:
    """Extract cost from snapshot — try various cost keys."""
    return snapshot.get("cost_daily_pct", 0) or snapshot.get("cost_burn_pct", 0) or 0


def generate_report(current: dict | None, previous: dict | None) -> str:
    """Generate the weekly quality report as markdown."""
    now = datetime.now(timezone.utc)
    report: list[str] = []

    report.append(f"# Weekly Quality Report — {now.strftime('%Y-%m-%d')}")
    report.append(f"")
    report.append(f"Generated at: {now.isoformat()}")
    report.append(f"")

    if current is None:
        report.append("## No quality metrics data available")
        report.append("")
        report.append("quality-metrics.json has no snapshots. Run collection + analysis first.")
        return "\n".join(report)

    report.append("## Executive Summary")
    report.append("")

    # Calibration
    cal_current = current.get("calibration", {})
    cal_previous = previous.get("calibration", {}) if previous else {}
    acc_current = cal_current.get("accuracy_pct", 0)
    acc_previous = cal_previous.get("accuracy_pct", 0) if cal_previous else None
    acc_arrow = _trend_arrow(acc_current, acc_previous)
    acc_delta = _fmt_delta(acc_current, acc_previous)

    report.append(f"| Metric | Current | Previous | Trend |")
    report.append(f"|--------|---------|----------|-------|")
    report.append(
        f"| Calibration accuracy | {_fmt_pct(acc_current)} | "
        f"{_fmt_pct(acc_previous) if acc_previous else '—'} | {acc_arrow} {acc_delta} |"
    )

    # Feed health
    fh_current = current.get("feed_health", {})
    fh_previous = previous.get("feed_health", {}) if previous else {}
    fh_pct_current = fh_current.get("health_pct", 0)
    fh_pct_previous = fh_previous.get("health_pct", 0) if fh_previous else None
    fh_arrow = _trend_arrow(fh_pct_current, fh_pct_previous)
    fh_delta = _fmt_delta(fh_pct_current, fh_pct_previous)

    report.append(
        f"| Feed health | {_fmt_pct(fh_pct_current)} ({fh_current.get('working',0)}/{fh_current.get('total',0)}) | "
        f"{_fmt_pct(fh_pct_previous) if fh_pct_previous else '—'} ({fh_previous.get('working',0)}/{fh_previous.get('total',0)}) | {fh_arrow} {fh_delta} |"
    )

    # Provider reliability
    prov_current = current.get("provider_reliability", {})
    prov_previous = previous.get("provider_reliability", {}) if previous else {}
    for provider in ["deepseek_direct", "anthropic_direct", "openrouter"]:
        p_current = prov_current.get(provider, {})
        p_previous = prov_previous.get(provider, {}) if prov_previous else {}
        p_up_current = p_current.get("uptime_pct", 0)
        p_up_previous = p_previous.get("uptime_pct", 0) if p_previous else None
        p_arrow = _trend_arrow(p_up_current, p_up_previous)
        p_delta = _fmt_delta(p_up_current, p_up_previous)
        report.append(
            f"| Provider: {provider} | {_fmt_pct(p_up_current)} | "
            f"{_fmt_pct(p_up_previous) if p_up_previous else '—'} | {p_arrow} {p_delta} |"
        )

    # Collection activity
    coll_current = current.get("collection", {})
    coll_previous = previous.get("collection", {}) if previous else {}
    items_current = coll_current.get("total_items", 0)
    items_previous = coll_previous.get("total_items", 0) if coll_previous else None
    if items_previous is not None:
        diff = items_current - items_previous
        sign = "+" if diff > 0 else ""
        coll_detail = f"{items_current} ({sign}{diff})"
    else:
        coll_detail = str(items_current)
    report.append(f"| Collection items | {coll_detail} | — | — |")

    # Cost estimation
    cost_current = _extract_cost(current)
    cost_previous = _extract_cost(previous) if previous else None
    cost_arrow = _trend_arrow(cost_current, cost_previous)
    cost_delta = _fmt_delta(cost_current, cost_previous)
    report.append(
        f"| Cost burn (%daily) | {_fmt_pct(cost_current)} | "
        f"{_fmt_pct(cost_previous) if cost_previous else '—'} | {cost_arrow} {cost_delta} |"
    )

    report.append("")

    # ── Band Diversity ──
    report.append("## Band Diversity")
    report.append("")
    bands_current = cal_current.get("bands_used", [])
    bands_diversity = cal_current.get("band_diversity", 0)
    bands_previous = cal_previous.get("bands_used", []) if cal_previous else []
    report.append(f"- Bands used this week: {', '.join(bands_current) if bands_current else 'none'}")
    report.append(f"- Band diversity: {bands_diversity}")
    if bands_previous:
        report.append(f"- Previous bands: {', '.join(bands_previous)}")
    report.append("")

    # ── Feed Health Detail ──
    report.append("## Feed Health Detail")
    report.append("")
    report.append(f"- Total feeds tested: {fh_current.get('total', 0)}")
    report.append(f"- Working: {fh_current.get('working', 0)} ({_fmt_pct(fh_current.get('health_pct', 0))})")
    report.append(f"- Dead/403: {fh_current.get('dead_403', 0)}")
    report.append("")

    # ── Key Insights ──
    report.append("## Key Insights")
    report.append("")

    insights: list[str] = []

    # Calibration insight
    if acc_current < 30:
        insights.append(
            f"⚠️ **Calibration drift**: Accuracy is {_fmt_pct(acc_current)}. "
            "Confidence bands require widening. The system is overconfident."
        )
    elif acc_current < 50:
        insights.append(
            f"📊 **Room for improvement**: Accuracy is {_fmt_pct(acc_current)}. "
            "Calibration needs attention but is not critical."
        )

    # Feed health insight
    if fh_pct_current < 70:
        insights.append(
            f"⚠️ **Feed decay**: {_fmt_pct(fh_pct_current)} of feeds are working. "
            f"{fh_current.get('dead_403', 0)} dead feeds should be pruned."
        )

    # Band diversity insight
    if bands_diversity < 2:
        insights.append(
            f"⚠️ **Band collapse**: Only {bands_diversity} band(s) used. "
            "All judgments in a single band indicates calibration failure."
        )

    if not insights:
        insights.append("✅ All metrics within acceptable ranges.")

    for insight in insights:
        report.append(f"- {insight}")

    report.append("")

    # ── Recommendations ──
    report.append("## Recommendations")
    report.append("")

    recs: list[str] = []

    if acc_current < 30:
        recs.append(f"1. **Widen confidence bands** globally — accuracy is {_fmt_pct(acc_current)}.")
        recs.append(f"2. **Reduce KJs per region** to force selectivity.")
        recs.append(f"3. **Retrain prompt calibration** — add explicit band-spread instructions.")

    if fh_pct_current < 70:
        recs.append(f"4. **Run feed pruning** — {fh_current.get('dead_403', 0)} dead feeds.")
        recs.append(f"5. **Restock regions** with low feed counts.")

    if bands_diversity < 2:
        recs.append(f"6. **Enforce band diversity** — require multiple confidence bands per region.")

    if not recs:
        recs.append("Continue current posture. All metrics stable.")

    for rec in recs:
        report.append(f"- {rec}")

    report.append("")
    report.append("---")
    report.append("")
    report.append(f"*Report generated by weekly_quality_report.py at {now.isoformat()}*")

    return "\n".join(report)


def main() -> int:
    metrics = load_metrics()
    if metrics is None:
        return 1

    current, previous = find_snapshots(metrics)
    report = generate_report(current, previous)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = OUTPUT_DIR / f"quality-weekly-{today}.md"
    out_path.write_text(report)

    print(f"Written: {out_path}")
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
