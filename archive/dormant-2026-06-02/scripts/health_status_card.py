#!/usr/bin/env python3
"""Health status card — reads health-dashboard.json, prints compact card."""

from __future__ import annotations

import json
import sys
from pathlib import Path

DASHBOARD_PATH = Path("/home/ubuntu/.openclaw/workspace/tasks/health-dashboard.json")


def load_dashboard() -> dict:
    """Load the health dashboard JSON."""
    if not DASHBOARD_PATH.exists():
        print("❌ No health dashboard found. Run health_engine.py first.")
        sys.exit(1)
    return json.loads(DASHBOARD_PATH.read_text())


def print_card(d: dict) -> None:
    """Print a compact terminal status card from dashboard data."""
    score = d.get("health_score", 100)
    label = d.get("health_label", "HEALTHY")
    layers = d.get("layers", {})
    alerts = d.get("alerts", [])

    warn_c = len([a for a in alerts if a["level"] == "WARNING"])
    crit_c = len([a for a in alerts if a["level"] in ("CRITICAL", "EMERGENCY")])

    def ls(name: str) -> dict:
        return layers.get(name, {})

    INNER = 42

    def bl(content: str) -> str:
        cleaned = content[:INNER - 2]
        return f"│ {cleaned:<{INNER - 2}s}│"

    def hdr() -> str:
        t = " Trevor Health "
        side_len = (INNER - len(t)) // 2
        rem = INNER - side_len - len(t)
        return "┌" + "─" * side_len + t + "─" * rem + "┐"

    score_emoji = "🔴" if score < 50 else ("🟡" if score < 70 else ("🟠" if score < 90 else "🟢"))

    lines = [
        hdr(),
        bl(f"Score:  {label} ({score}/100)  {score_emoji}"),
    ]

    # Gateway
    infra = ls("infrastructure")
    lines.append(bl(f"Gateway:   {'✅ Running' if infra.get('gateway') else '❌ DOWN'}"))

    # GitHub
    gh = ls("github_backup")
    if gh.get("backup_status") == "ok":
        ght = f"✅ Pushed {gh.get('last_backup_age_hours', '?')}h ago"
    else:
        ght = "❌ No push" if gh.get("backup_status") == "critical" else "⚠️ Stale"
    lines.append(bl(f"GitHub:    {ght}"))

    # Cron
    cron = ls("cron_health")
    e = cron.get("enabled", 0)
    # Use active_failing if available (excludes resolved historical failures)
    f = cron.get("active_failing", cron.get("failing", 0))
    ok = e - f
    if f:
        lines.append(bl(f"Cron jobs: {ok}/{e} ok ({f} failing)"))
    else:
        lines.append(bl(f"Cron jobs: {ok}/{e} ok"))

    # Brief
    pipe = ls("pipeline")
    bbrief = pipe.get("brief_today", False)
    lines.append(bl(f"Brief:     {'✅ Delivered' if bbrief else '❌ Missing'}"))

    # Episodic
    lm = ls("learning_memory")
    ep = "✅ Current" if lm.get("episodic_today") else ("⚠️ Yesterday" if lm.get("episodic_yesterday") else "❌ Stale")
    lines.append(bl(f"Episodic:  {ep}"))

    # Brain index
    bix = lm.get("brain_index_fresh")
    ix = "✅ Fresh" if bix else ("❌ Old" if bix is False else "❓")
    lines.append(bl(f"Brain idx: {ix}"))

    # DeepSeek
    cost = ls("cost_budget")
    bal = cost.get("balance", 0)
    ru = cost.get("runway_days", 0)
    ds = f"${bal:.2f}" + (f" ({ru:.0f}d)" if ru else "")
    ds_emoji = "🔴" if bal < 2 else ("🟡" if bal < 10 else "✅")
    lines.append(bl(f"DeepSeek:  {ds}  {ds_emoji}"))

    # Heartbeat
    hb = ls("heartbeat")
    hbs = "✅ Complete" if hb.get("cycle_complete") else f"⚠️ {hb.get('current_phase', '?')}"
    lines.append(bl(f"Heartbeat: {hbs}"))

    # Alerts
    if crit_c:
        alert_line = f"🚨 {crit_c} CRITICAL"
    elif warn_c:
        alert_line = f"⚠️  {warn_c} WARNING"
    else:
        alert_line = "✅ None"
    lines.append(bl(f"Alerts:    {alert_line}"))

    lines.append("└" + "─" * INNER + "┘")
    print("\n".join(lines))


def main() -> int:
    d = load_dashboard()
    print_card(d)
    return 0


if __name__ == "__main__":
    sys.exit(main())
