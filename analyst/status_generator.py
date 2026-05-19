#!/usr/bin/env python3
"""Status Generator — reads pipeline state and writes STATUS.md.

Sources:
  - config/active-assignments.yaml
  - memory/cost-ledger.jsonl (or brain/memory/semantic/cost-ledger.json)
  - memory/llm-routing-log.jsonl
  - memory/skill-installs.jsonl
  - recent git log
  - memory/directives/ (in-flight directives)

Usage:
    python3 analyst/status_generator.py          # Regenerate STATUS.md
    python3 analyst/status_generator.py --json   # Output as JSON only
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

SOURCES = {
    "assignments": REPO_ROOT / "config" / "active-assignments.yaml",
    "cost_ledger": REPO_ROOT / "brain" / "memory" / "semantic" / "cost-ledger.json",
    "routing_log": REPO_ROOT / "memory" / "llm-routing-log.jsonl",
    "skill_installs": REPO_ROOT / "memory" / "skill-installs.jsonl",
    "directives_dir": REPO_ROOT / "memory" / "directives",
}


def log(msg: str) -> None:
    print(f"[status-gen] {msg}", file=sys.stderr, flush=True)


def read_file(path: pathlib.Path) -> str:
    if path.exists():
        return path.read_text().strip()
    return ""


def read_json(path: pathlib.Path) -> dict | list:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def read_jsonl(path: pathlib.Path) -> list[dict]:
    items = []
    if path.exists():
        for line in path.read_text().strip().split("\n"):
            line = line.strip()
            if line:
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return items


def get_git_log(days: int = 7) -> str:
    try:
        result = subprocess.run(
            ["git", "log", f"--since={days}.days", "--oneline", "--no-decorate"],
            capture_output=True, text=True, timeout=10,
            cwd=str(REPO_ROOT),
        )
        return result.stdout.strip()
    except Exception:
        return "(git log unavailable)"


def get_active_topics() -> list[dict]:
    """Parse active-assignments.yaml for topic assignments."""
    content = read_file(SOURCES["assignments"])
    topics = []
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("- topic:"):
            slug = line.split(":", 1)[1].strip()
            topics.append({"slug": slug, "status": "active"})
    return topics


def get_in_flight_directives() -> list[dict]:
    """Scan memory/directives/ for recently modified directive files."""
    dir_path = SOURCES["directives_dir"]
    directives = []
    if dir_path.exists():
        for f in sorted(dir_path.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]:
            directives.append({"file": f.name, "modified": dt.datetime.fromtimestamp(f.stat().st_mtime).isoformat()[:16]})
    return directives


def get_cost_summary() -> dict:
    """Aggregate costs from cost ledger."""
    ledger = read_json(SOURCES["cost_ledger"])
    if isinstance(ledger, dict):
        entries = ledger.get("entries", [])
    elif isinstance(ledger, list):
        entries = ledger
    else:
        entries = []

    total = 0.0
    by_model = {}
    by_provider = {}
    for e in entries:
        cost = e.get("cost_usd", e.get("cost", 0)) or 0
        total += cost
        model = e.get("model", "unknown")
        provider = e.get("provider", "unknown")
        by_model[model] = by_model.get(model, 0) + cost
        by_provider[provider] = by_provider.get(provider, 0) + cost

    return {
        "total_usd": round(total, 4),
        "by_model": {k: round(v, 4) for k, v in sorted(by_model.items(), key=lambda x: -x[1])},
        "by_provider": {k: round(v, 4) for k, v in sorted(by_provider.items(), key=lambda x: -x[1])},
    }


def get_provider_health() -> dict:
    """Latest successful auth per provider from routing log."""
    entries = read_jsonl(SOURCES["routing_log"])
    health = {}
    for e in entries:
        provider = e.get("provider", "")
        ts = e.get("timestamp", "")
        if provider and ts:
            if provider not in health or ts > health[provider]:
                health[provider] = ts[:16]
    return health


def generate_status() -> dict:
    """Generate full status report."""
    topics = get_active_topics()
    directives = get_in_flight_directives()
    cost = get_cost_summary()
    git_log = get_git_log(7)
    provider_health = get_provider_health()

    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "in_flight_directives": directives,
        "active_topics": topics,
        "cost_summary": cost,
        "provider_health": provider_health,
        "recent_git_activity": git_log[:2000] if git_log else "(none)",
    }


def format_markdown(status: dict) -> str:
    """Format status dict as markdown for STATUS.md."""
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = []
    lines.append("# Trevor — Status\n")
    lines.append(f"*Generated: {now}*\n")

    # In-Flight Directives
    lines.append("## In-Flight Directives\n")
    dirs = status.get("in_flight_directives", [])
    if dirs:
        for d in dirs:
            lines.append(f"- `{d['file']}` — last modified {d['modified']}")
    else:
        lines.append("None.\n")
    lines.append("")

    # Active Topics
    lines.append("## Active Topics\n")
    topics = status.get("active_topics", [])
    if topics:
        for t in topics:
            lines.append(f"- **{t['slug']}** ({t['status']})")
    else:
        lines.append("No active assignments. General autonomy maturation mode.\n")
    lines.append("")

    # Cost Summary
    lines.append("## Cost Summary (Current Month)\n")
    cost = status.get("cost_summary", {})
    lines.append(f"**Total:** ${cost.get('total_usd', 0):.4f}\n")
    by_model = cost.get("by_model", {})
    if by_model:
        lines.append("| Model | Cost |")
        lines.append("|---|---|")
        for model, c in by_model.items():
            lines.append(f"| {model} | ${c:.4f} |")
    by_provider = cost.get("by_provider", {})
    if by_provider:
        lines.append("\n| Provider | Cost |")
        lines.append("|---|---|")
        for prov, c in by_provider.items():
            lines.append(f"| {prov} | ${c:.4f} |")
    lines.append("")

    # Provider Health
    lines.append("## Provider Health\n")
    health = status.get("provider_health", {})
    if health:
        lines.append("| Provider | Last Auth |")
        lines.append("|---|---|")
        for prov, ts in health.items():
            lines.append(f"| {prov} | {ts} |")
    else:
        lines.append("No routing log entries yet.\n")
    lines.append("")

    # Recent Git Activity
    lines.append("## Recent Outputs (Last 7 Days)\n")
    git_log = status.get("recent_git_activity", "")
    if git_log:
        lines.append("```\n" + git_log + "\n```")
    else:
        lines.append("No recent git activity.\n")
    lines.append("")

    lines.append("---\n")
    lines.append(f"*Updated by status_generator.py at {now}*\n")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Trevor v2 Status Generator")
    parser.add_argument("--json", action="store_true", help="Output JSON only, don't write STATUS.md")
    args = parser.parse_args()

    status = generate_status()

    if args.json:
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return 0

    md = format_markdown(status)
    status_path = REPO_ROOT / "STATUS.md"
    status_path.write_text(md)
    log(f"Written to {status_path} ({len(md)} chars)")

    if args.json:
        print(json.dumps(status, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    main()
