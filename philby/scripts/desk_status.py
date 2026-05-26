#!/usr/bin/env python3
"""
desk_status.py — Philby Desk Status & Reporting.

Shows each desk's health, narrative count, confidence distribution,
and recent changes. Designed for both human reading and agent consumption.

Usage:
    python3 philby/scripts/desk_status.py                           # All desks
    python3 philby/scripts/desk_status.py --desk iran              # Single desk
    python3 philby/scripts/desk_status.py --json                   # Machine-readable
    python3 philby/scripts/desk_status.py --moltbook               # Post status to Moltbook
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent.parent
COGNITION_STATE = REPO / "skills" / "continuous-cognition" / "state" / "cognition_state.json"
PHILBY_CONFIG = REPO / "philby" / "desks" / "philby-config.json"

class DeskStatus:
    """Represents the status of a single Philby desk."""

    def __init__(self, desk_id: str, desk_config: dict, narratives: list[dict]):
        self.id = desk_id
        self.name = desk_config.get("name", desk_id)
        self.description = desk_config.get("description", "")
        self.seeded = desk_config.get("seeded", False)
        self.model_tier = desk_config.get("model_tier", "flash")
        self.narratives = narratives
        self.total = len(narratives)

        # Confidence distribution
        self.confidence_dist = {
            "high_80plus": len([n for n in narratives if n.get("confidence", 0) >= 80]),
            "medium_50to79": len([n for n in narratives if 50 <= n.get("confidence", 0) < 80]),
            "low_under50": len([n for n in narratives if n.get("confidence", 0) < 50]),
        }

        # Trend distribution
        trends = {}
        for n in narratives:
            t = n.get("trend", "stable")
            trends[t] = trends.get(t, 0) + 1
        self.trends = trends

        # Recent changes (from delta)
        self.changed = []
        self.new = []

    def to_dict(self) -> dict:
        return {
            "desk_id": self.id,
            "name": self.name,
            "description": self.description,
            "seeded": self.seeded,
            "model_tier": self.model_tier,
            "narrative_count": self.total,
            "confidence_distribution": self.confidence_dist,
            "trends": self.trends,
            "narratives": [
                {
                    "id": n["id"],
                    "confidence": n["confidence"],
                    "kent_band": n["kent_band"],
                    "trend": n["trend"],
                    "evidence_for": n.get("evidence_for", 0),
                    "evidence_against": n.get("evidence_against", 0),
                    "hours_to_resolution": n.get("hours_to_resolution"),
                    "reasoning_preview": n.get("reasoning", "")[:120],
                }
                for n in sorted(self.narratives, key=lambda x: x["id"])
            ],
            "changed": self.changed,
            "new": self.new,
        }

    def to_table(self) -> str:
        lines = [
            f"\n═══ {self.name} ═══",
            f"  Status: {'✅ Seeded' if self.seeded else '❌ Not seeded'}  |  "
            f"Model: {self.model_tier.upper()}  |  "
            f"Narratives: {self.total}",
            f"  Confidence: H:{self.confidence_dist['high_80plus']} "
            f"M:{self.confidence_dist['medium_50to79']} "
            f"L:{self.confidence_dist['low_under50']}",
        ]
        if self.trends:
            trend_str = "  ".join(f"{t}:{c}" for t, c in sorted(self.trends.items()))
            lines.append(f"  Trends: {trend_str}")

        if self.narratives:
            lines.append("  Narratives:")
            for n in self.narratives:
                trend_mark = {
                    "upward": "▲", "downward": "▼", "stable": "→", "erratic": "~", "divergent": "◈"
                }.get(n.get("trend", ""), "·")
                sw = ""
                for c in self.changed:
                    if c.get("id") == n["id"]:
                        sw = f" [Δ{c['swing']:+.0f}]"
                        break
                lines.append(
                    f"    {trend_mark} [{n['id']}] {n['kent_band']} ({n['confidence']}%){sw}"
                )

        if self.changed:
            lines.append(f"  Changes: {len(self.changed)} narrative(s) shifted")
        if self.new:
            lines.append(f"  New: {', '.join(self.new)}")

        return "\n".join(lines)


def load_state() -> dict:
    try:
        return json.loads(COGNITION_STATE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {"active_narratives": {}, "source_trust": {}, "cycle": 0}


def load_config() -> dict:
    try:
        return json.loads(PHILBY_CONFIG.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {"desks": {}}


def filter_narratives(narratives: list[dict], desk_config: dict) -> list[dict]:
    """Filter narratives to those matching a desk's patterns."""
    import re
    patterns = desk_config.get("narrative_patterns", [])
    def matches(n):
        nid = n.get("id", "")
        return any(nid.startswith(p) or re.search(p, nid) for p in patterns)
    return [n for n in narratives if matches(n)]


def post_to_moltbook(summary: str, desk_id: str = ""):
    """Post desk status to Moltbook."""
    api_key = os.environ.get("MOLTBOOK_API_KEY", "")
    if not api_key:
        return False

    title = f"Philby Desks — {dt.date.today().strftime('%Y-%m-%d')}"
    if desk_id:
        title = f"Philby {desk_id.upper()} Desk — {dt.date.today().strftime('%Y-%m-%d')}"

    payload = json.dumps({
        "title": title,
        "content": summary,
        "submolt": "agents",
    }).encode()

    req = urllib.request.Request(
        "https://www.moltbook.com/api/v1/posts",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        post_url = f"https://www.moltbook.com/posts/{result['post']['id']}"
        print(f"Posted to Moltbook: {post_url}")
        return True
    except urllib.error.HTTPError as e:
        print(f"Moltbook post failed: {e.code}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Philby Desk Status")
    parser.add_argument("--desk", default="", help="Specific desk to report on")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--moltbook", action="store_true", help="Post to Moltbook")
    args = parser.parse_args()

    state = load_state()
    config = load_config()
    desks_config = config.get("desks", {})

    # Build all narratives list with Kent bands
    all_narratives = []
    for nid, ndata in state.get("active_narratives", {}).items():
        confidence = ndata.get("confidence", 50)
        all_narratives.append({
            "id": nid,
            "confidence": confidence,
            "kent_band": _conf_to_band(confidence),
            "trend": ndata.get("trend", "stable"),
            "evidence_for": len(ndata.get("evidence", {}).get("for", [])),
            "evidence_against": len(ndata.get("evidence", {}).get("against", [])),
            "reasoning": ndata.get("last_reasoning", ""),
            "catalysts": ndata.get("catalysts", []),
            "hours_to_resolution": _calc_hours(ndata.get("resolution_date")),
        })

    if args.desk:
        # Single desk
        if args.desk not in desks_config:
            print(f"Unknown desk: {args.desk}")
            return 1
        dcfg = desks_config[args.desk]
        dnarr = filter_narratives(all_narratives, dcfg)
        status = DeskStatus(args.desk, dcfg, dnarr)
        if args.json:
            print(json.dumps(status.to_dict(), indent=2))
        else:
            print(status.to_table())
    else:
        # All desks
        statuses = {}
        for did, dcfg in desks_config.items():
            dnarr = filter_narratives(all_narratives, dcfg)
            statuses[did] = DeskStatus(did, dcfg, dnarr)

        if args.json:
            result = {
                "timestamp": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "cycle": state.get("cycle", 0),
                "desks": {did: s.to_dict() for did, s in statuses.items()},
                "total_narratives": len(all_narratives),
                "total_sources": len(state.get("source_trust", {})),
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"\nPhilby Desk Status — Cycle {state.get('cycle', 0)} — {dt.date.today()}")
            print(f"{'─' * 60}")
            total = 0
            for did in ["iran", "ukraine", "us_china", "cartel", "energy"]:
                if did in statuses:
                    print(statuses[did].to_table())
                    total += statuses[did].total
            print(f"\n{'─' * 60}")
            print(f"Total: {total} narratives, {len(state.get('source_trust', {}))} sources across 5 desks")

    # Moltbook
    if args.moltbook:
        lines = []
        for did in ["iran", "ukraine", "us_china", "cartel", "energy"]:
            if did in statuses:
                s = statuses[did]
                narr_lines = []
                for n in s.narratives:
                    narr_lines.append(f"• [{n['id']}] {n['kent_band']} ({n['confidence']}%) {n['trend']}")
                lines.append(f"**{s.name}** ({s.total} narratives)")
                lines.extend(narr_lines)
                lines.append("")

        post_to_moltbook("\n".join(lines), args.desk)

    return 0


def _conf_to_band(confidence: int) -> str:
    bands = [
        (93, "almost_certain"), (80, "highly_likely"), (60, "likely"),
        (40, "even_chance"), (20, "unlikely"), (5, "highly_unlikely"), (0, "almost_certainly_not"),
    ]
    for lo, band in bands:
        if confidence >= lo:
            return band
    return "no_judgment"


def _calc_hours(res_date) -> float | None:
    if not res_date:
        return None
    try:
        res_dt = dt.datetime.fromisoformat(res_date)
        delta = (res_dt - dt.datetime.now(dt.timezone.utc)).total_seconds() / 3600
        return round(delta, 1)
    except (ValueError, TypeError):
        return None


if __name__ == "__main__":
    sys.exit(main())
