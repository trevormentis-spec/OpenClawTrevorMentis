#!/usr/bin/env python3
"""
Topic Morning Brief — generalized version of the Mexico Morning Brief.

Reads currently-active topics from config/active-assignments.yaml,
runs the morning-brief workflow for each active topic.

Usage:
    python3 scripts/topic_morning_brief.py
    python3 scripts/topic_morning_brief.py --send

Replaces: scripts/mexico_morning_brief.py (Mexico-specific v1 residue)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "exports" / "briefs"


def log(msg: str) -> None:
    print(f"[topic-brief] {msg}", file=sys.stderr, flush=True)


def get_active_topics() -> list[dict]:
    """Parse active-assignments.yaml for assigned topics."""
    path = REPO_ROOT / "config" / "active-assignments.yaml"
    if not path.exists():
        return []
    topics = []
    for line in path.read_text().split("\n"):
        line = line.strip()
        if line.startswith("- topic:"):
            slug = line.split(":", 1)[1].strip()
            topics.append({"slug": slug, "status": "active"})
    return topics


def load_topic_config(slug: str) -> dict | None:
    """Load topic.yaml for a given slug."""
    path = REPO_ROOT / "config" / "topics" / slug / "topic.yaml"
    if not path.exists():
        return None
    config = {"slug": slug, "name": slug}
    for line in path.read_text().split("\n"):
        if line.startswith("name:"):
            config["name"] = line.split(":", 1)[1].strip().strip('"')
        if line.startswith("description:"):
            config["description"] = line.split(":", 1)[1].strip().strip('"')
    return config


def generate_brief(topic: dict) -> str:
    """Generate an HTML morning brief for a single topic."""
    slug = topic["slug"]
    name = topic.get("name", slug)
    today = dt.date.today().isoformat()

    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{name} — Morning Brief {today}</title>
<style>
  body {{ font-family: -apple-system, system-ui, sans-serif; background: #f0f2f5; max-width: 720px; margin: 20px auto; padding: 0 16px; }}
  .header {{ background: #1a1a2e; color: white; padding: 20px; border-radius: 10px; margin-bottom: 16px; }}
  .header h1 {{ font-size: 20px; margin: 0; }}
  .header .sub {{ font-size: 12px; opacity: 0.7; }}
  .section {{ background: white; border-radius: 8px; padding: 16px; margin-bottom: 12px; }}
  .section h2 {{ font-size: 15px; border-bottom: 2px solid #eee; padding-bottom: 6px; }}
  .item {{ padding: 6px 0; border-bottom: 1px solid #f5f5f5; }}
  .item:last-child {{ border-bottom: none; }}
  .item .title {{ font-size: 13px; font-weight: 600; }}
  .item .meta {{ font-size: 11px; color: #7f8c8d; }}
  .stat-grid {{ display: flex; gap: 10px; }}
  .stat-card {{ background: #f8f9fa; padding: 12px; border-radius: 6px; text-align: center; flex: 1; }}
  .stat-card .num {{ font-size: 24px; font-weight: 800; color: #2980b9; }}
  .stat-card .label {{ font-size: 10px; color: #7f8c8d; }}
</style></head>
<body>
<div class="header">
  <h1>☀️ {name}</h1>
  <div class="sub">{today} · Topic Morning Brief · Open Claw</div>
</div>
<div class="section">
  <h2>📋 Topic Overview</h2>
  <p><strong>Slug:</strong> {slug}</p>
  <p><strong>Status:</strong> {topic.get('status', 'active')}</p>
  <p><strong>Data pipeline:</strong> Collection records in SQLite + JSONL</p>
</div>
<div class="section">
  <h2>📊 Quick Stats</h2>
  <div class="stat-grid">
    <div class="stat-card"><div class="num">0</div><div class="label">Articles today</div></div>
    <div class="stat-card"><div class="num">0</div><div class="label">Alerts active</div></div>
    <div class="stat-card"><div class="num">0</div><div class="label">Pending review</div></div>
  </div>
</div>
<div style="text-align:center; padding:20px; font-size:11px; color:#7f8c8d;">
  Generated {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · PENDING HUMAN ANALYST QC REVIEW
</div>
</body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Topic Morning Brief")
    parser.add_argument("--send", action="store_true", help="Send via email")
    parser.add_argument("--topic-slug", help="Single topic slug (omit for all active)")
    args = parser.parse_args()

    topics = get_active_topics()
    if args.topic_slug:
        topics = [t for t in topics if t["slug"] == args.topic_slug]
        if not topics:
            log(f"Topic '{args.topic_slug}' not found in active assignments")
            return 1

    if not topics:
        log("No active topics. Morning brief skipped.")
        print(json.dumps({"status": "skipped", "reason": "no active topics"}))
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated = []

    for topic in topics:
        config = load_topic_config(topic["slug"])
        topic.update(config or {})
        html = generate_brief(topic)
        slug = topic["slug"]
        path = OUTPUT_DIR / f"morning-brief-{slug}-{dt.date.today().isoformat()}.html"
        path.write_text(html)
        generated.append({"slug": slug, "path": str(path), "size": len(html)})
        log(f"Generated: {path} ({len(html)} bytes)")

    result = {"status": "ok", "topics": generated}
    print(json.dumps(result, indent=2))

    if args.send and generated:
        import base64
        from agentmail import AgentMail
        key = os.environ.get("AGENTMAIL_API_KEY", "")
        if key:
            client = AgentMail(api_key=key)
            for g in generated:
                html = open(g["path"]).read()
                client.inboxes.messages.send(
                    inbox_id="trevor_mentis@agentmail.to",
                    to="roderick.jones@gmail.com",
                    subject=f"Morning Brief — {g['slug']} — {dt.date.today().isoformat()}",
                    html=html,
                )
                log(f"Emailed: {g['slug']}")

    return 0


if __name__ == "__main__":
    main()
