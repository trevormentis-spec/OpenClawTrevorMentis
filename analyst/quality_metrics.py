#!/usr/bin/env python3
"""Quality metrics dashboard — aggregates quality data from across the system.

Reads from:
  - brain/memory/semantic/deepseek-usage.json — cost data
  - brain/memory/semantic/control-plane-metrics.json — crash tracking
  - brain/memory/heartbeat-state.json — feed health
  - brain/memory/semantic/calibration-tracking.json — calibration accuracy
  - brain/memory/semantic/collection-state.json — collection activity
  - tasks/health-dashboard.json — health engine output
  - analyst/meta/sources_tested.json — feed catalog status

Output: brain/memory/semantic/quality-metrics.json with current snapshot and
history array for trend tracking. Additive: reads existing file and appends.

Environment variables: (none required, best-effort reads)

Usage:
  python3 analyst/quality_metrics.py
  python3 analyst/quality_metrics.py --quiet  # no console output
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def safe_json_read(path, default=None):
    """Read a JSON file, returning default on any error."""
    if default is None:
        default = {}
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        pass
    return default


def load_calibration(cal_path):
    """Extract calibration metrics from calibration-tracking.json."""
    data = safe_json_read(cal_path, {})
    return {
        "total_judgments": data.get("total_judgments", 0),
        "correct": data.get("correct", 0),
        "incorrect": data.get("incorrect", 0),
        "unresolved": data.get("unresolved", 0),
        "accuracy_pct": round(
            (data.get("correct", 0) / max(data.get("total_judgments", 1), 1)) * 100,
            1,
        ),
        "bands_used": list(data.get("by_confidence_band", {}).keys()),
        "band_diversity": len(data.get("by_confidence_band", {})),
    }


def load_feed_health(heartbeat_path, sources_path):
    """Extract feed health metrics from heartbeat and source test data."""
    # From heartbeat-state.json phase_a_results
    heartbeat = safe_json_read(heartbeat_path, {})
    phase_a = heartbeat.get("phase_a_results", {})

    # From sources_tested.json
    sources = safe_json_read(sources_path, [])
    dead_count = sum(
        1
        for s in sources
        if s.get("status") in ("forbidden", "dead", "error", "http_401", "http_403", "timeout")
    )
    ok_count = sum(1 for s in sources if s.get("status") == "ok")
    total_sources = len(sources)

    # Use heartbeat if sources file is empty
    if total_sources == 0:
        total_sources = phase_a.get("total", 0)
        dead_count = phase_a.get("dead", 0)
        ok_count = phase_a.get("working", 0)

    # Trend: compare with previous quality-metrics.json
    trend = "unknown"
    qm_path = os.path.join(REPO, "brain", "memory", "semantic", "quality-metrics.json")
    prev = safe_json_read(qm_path, {})
    snapshots = prev.get("snapshots", [])
    if snapshots:
        prev_feed = snapshots[-1].get("feed_health", {})
        prev_health = prev_feed.get("health_pct", 0)
        cur_health = round(
            (ok_count / max(total_sources, 1)) * 100, 1
        ) if total_sources else 0
        if cur_health > prev_health + 1:
            trend = "improving"
        elif cur_health < prev_health - 1:
            trend = "declining"
        else:
            trend = "stable"

    return {
        "total": total_sources,
        "working": ok_count,
        "dead_403": dead_count,
        "health_pct": round((ok_count / max(total_sources, 1)) * 100, 1),
        "trend": trend,
    }


def load_provider_reliability(control_path, health_path):
    """Extract provider reliability from control plane and health dashboard."""
    control = safe_json_read(control_path, {})
    health = safe_json_read(health_path, {})

    infra = health.get("layers", {}).get("infrastructure", {})

    # Collect crash info from control plane
    crashes = control.get("crash_tracking", control.get("uptime_samples", []))

    return {
        "deepseek": {
            "status": "ok" if infra.get("deepseek_balance", 0) > 0 else "degraded",
            "last_failure": None,
            "failures_24h": len(
                [
                    s
                    for s in (crashes if isinstance(crashes, list) else [])
                    if isinstance(s, dict) and s.get("deepseek_ok") is False
                ]
            ),
        },
        "openrouter": {
            "status": "ok" if infra.get("openrouter_ok", True) else "degraded",
            "last_failure": next(
                (
                    s["ts"]
                    for s in (crashes if isinstance(crashes, list) else [])
                    if isinstance(s, dict) and s.get("openrouter_ok") is False
                ),
                None,
            ),
            "failures_24h": len(
                [
                    s
                    for s in (crashes if isinstance(crashes, list) else [])
                    if isinstance(s, dict) and s.get("openrouter_ok") is False
                ]
            ),
        },
        "anthropic": {
            "status": "untested",
            "last_failure": None,
            "failures_24h": 0,
        },
    }


def load_collection_activity(collection_path):
    """Extract collection activity from collection-state.json."""
    data = safe_json_read(collection_path, {})
    regions = data.get("source_utilization", {})
    return {
        "total_regions": len(regions),
        "active_regions": sum(
            1 for r in regions.values() if isinstance(r, dict) and r.get("total_items", 0) > 0
        ),
        "stalled_regions": [
            name
            for name, r in regions.items()
            if isinstance(r, dict) and r.get("total_items", 0) == 0
        ][:20],  # limit to 20
        "total_items_24h": sum(
            r.get("total_items", 0)
            for r in regions.values()
            if isinstance(r, dict)
        ),
    }


def load_costs(cost_path):
    """Extract cost metrics from deepseek-usage.json."""
    data = safe_json_read(cost_path, {})
    snapshots = data.get("snapshots", [])
    if not snapshots:
        return {
            "deepseek_balance": None,
            "burn_rate_daily": 0,
            "runway_days": 0,
            "daily_cap_used_pct": 0,
        }

    latest = snapshots[-1]
    balance = latest.get("balance", {})
    balance_val = balance.get("total_balance", None)

    # Estimate daily burn from last two snapshots
    burn_rate = 0
    if len(snapshots) >= 2:
        prev = snapshots[-2]
        prev_balance = prev.get("balance", {}).get("total_balance", 0)
        current_balance = balance_val or 0
        time_diff = (
            datetime.fromisoformat(latest["timestamp"])
            - datetime.fromisoformat(prev["timestamp"])
        ).total_seconds() / 86400  # in days
        if time_diff > 0 and prev_balance > 0:
            burn_rate = round(max(0, prev_balance - current_balance) / time_diff, 2)

    runway = round(balance_val / burn_rate, 1) if burn_rate > 0 and balance_val else 0

    return {
        "deepseek_balance": balance_val,
        "burn_rate_daily": burn_rate,
        "runway_days": runway,
        "daily_cap_used_pct": min(100, round((burn_rate / 30) * 100, 1))
        if burn_rate > 0
        else 0,
    }


def build_snapshot():
    """Build a single quality metrics snapshot from all available data."""
    base = os.path.join(REPO, "brain", "memory", "semantic")
    heartbeat_path = os.path.join(REPO, "brain", "memory", "heartbeat-state.json")
    sources_path = os.path.join(REPO, "analyst", "meta", "sources_tested.json")
    health_path = os.path.join(REPO, "tasks", "health-dashboard.json")

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "calibration": load_calibration(
            os.path.join(base, "calibration-tracking.json")
        ),
        "feed_health": load_feed_health(heartbeat_path, sources_path),
        "provider_reliability": load_provider_reliability(
            os.path.join(base, "control-plane-metrics.json"), health_path
        ),
        "collection_activity": load_collection_activity(
            os.path.join(base, "collection-state.json")
        ),
        "costs": load_costs(os.path.join(base, "deepseek-usage.json")),
    }


def main():
    snapshot = build_snapshot()

    # Read existing quality-metrics.json
    out_path = os.path.join(
        REPO, "brain", "memory", "semantic", "quality-metrics.json"
    )
    existing = safe_json_read(out_path, {"snapshots": []})

    # Append new snapshot
    if "snapshots" not in existing:
        existing["snapshots"] = []
    existing["snapshots"].append(snapshot)

    # Keep last 90 snapshots for trend tracking
    if len(existing["snapshots"]) > 90:
        existing["snapshots"] = existing["snapshots"][-90:]

    # Write
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(existing, f, indent=2)

    # Console output
    if "--quiet" not in sys.argv:
        print(f"Quality Metrics Dashboard — {snapshot['generated_at']}")
        print(f"  Snapshots stored: {len(existing['snapshots'])}")
        print()
        print("  Calibration:")
        c = snapshot["calibration"]
        print(
            f"    Judgments: {c['total_judgments']} total, "
            f"{c['correct']} correct, {c['accuracy_pct']}%"
        )
        print(f"    Bands used: {c['band_diversity']} ({c['bands_used']})")
        print()
        print("  Feed Health:")
        fh = snapshot["feed_health"]
        print(
            f"    {fh['working']}/{fh['total']} working ({fh['health_pct']}%) — "
            f"trend: {fh['trend']}"
        )
        print(f"    Dead/403: {fh['dead_403']}")
        print()
        print("  Provider Reliability:")
        for name, pr in snapshot["provider_reliability"].items():
            print(f"    {name}: {pr['status']} ({pr['failures_24h']} failures/24h)")
        print()
        print("  Collection Activity:")
        ca = snapshot["collection_activity"]
        print(
            f"    {ca['active_regions']}/{ca['total_regions']} regions active, "
            f"{ca['total_items_24h']} items"
        )
        stalled = ca["stalled_regions"]
        if stalled:
            print(f"    Stalled: {', '.join(stalled[:5])}")
        print()
        print("  Costs:")
        co = snapshot["costs"]
        bal_str = f"${co['deepseek_balance']}" if co["deepseek_balance"] is not None else "N/A"
        print(f"    Balance: {bal_str}")
        print(f"    Burn rate: ${co['burn_rate_daily']}/day")
        print(f"    Runway: {co['runway_days']} days")
        print(f"    Daily cap used: {co['daily_cap_used_pct']}%")

    return 0


if __name__ == "__main__":
    sys.exit(main())
