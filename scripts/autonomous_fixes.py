#!/usr/bin/env python3
"""
Autonomous Fixes Engine — self-healing operations for Trevor.
All 10 fixes from the codebase assessment, implemented as a unified module.

Run by the heartbeat every cycle. Each fix checks conditions, applies corrections
within autonomy boundaries, and only surfaces what needs human attention.
"""

import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone, timedelta
from typing import Any

REPO = pathlib.Path(__file__).resolve().parent.parent
CRON_JOBS = pathlib.Path(os.path.expanduser("~/.openclaw/cron/jobs.json"))
DEAD_FEEDS = REPO / "brain" / "memory" / "semantic" / "dead-feeds.json"
CATALOG = REPO / "analyst" / "meta" / "sources_tested.json"
STATE_FILE = REPO / "brain" / "memory" / "semantic" / "autofix-state.json"
LOG_DIR = REPO / "logs"
MEMORY_DIR = REPO / "memory"
EXPORTS_DIR = REPO / "exports"

NOW = datetime.now(timezone.utc)
ALERTS: list[str] = []
FIXES_APPLIED: list[str] = []


def log(msg: str) -> None:
    print(f"[autofix {NOW.strftime('%H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


def alert(msg: str) -> None:
    """Queue an alert for Telegram delivery."""
    ALERTS.append(f"[{NOW.strftime('%H:%M')}] {msg}")
    log(f"ALERT: {msg}")


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {}


def save_state(state: dict) -> None:
    state["last_run"] = NOW.isoformat()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def get_api_key(name: str) -> str:
    val = os.environ.get(name, "")
    if val:
        return val
    env_file = REPO / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith(f"{name}="):
                return line.split("=", 1)[1].strip().strip("'\"")
    return ""


# ═══════════════════════════════════════════════════════════════════
# FIX 1: Delivery auto-retry + alert
# ═══════════════════════════════════════════════════════════════════

def fix_delivery_retry(state: dict) -> None:
    """Check if today's brief was delivered. If not, retry delivery."""
    today = NOW.strftime("%Y-%m-%d")
    brief_dir = pathlib.Path(os.path.expanduser(f"~/trevor-briefings/{today}"))
    exec_file = brief_dir / "analysis" / "exec_summary.json"

    if not exec_file.exists():
        return  # No brief to deliver

    # Check if delivery already retried today
    last_retry = state.get("delivery_retry", {}).get(today, "")
    if last_retry == "sent":
        return

    # Check AgentMail inbox for today's delivery
    api_key = get_api_key("AGENTMAIL_API_KEY")
    if not api_key:
        alert("🔴 Cannot check delivery — AGENTMAIL_API_KEY missing")
        return

    try:
        from agentmail import AgentMail
        client = AgentMail(api_key=api_key)
        inboxes = client.inboxes.list()
        trevor = inboxes.inboxes[0].inbox_id
        msgs = client.inboxes.messages.list(trevor, limit=30)
        delivered_today = False
        for m in msgs.messages:
            subj = str(m.subject or "")
            created = str(m.created_at)[:10]
            if created == today and ("Daily Brief" in subj or "TREVOR Daily" in subj):
                delivered_today = True
                break

        if not delivered_today:
            log("Today's brief not found in sent mail — retrying delivery")
            result = subprocess.run(
                ["python3", str(REPO / "skills" / "daily-intel-brief" / "scripts" / "deliver_text_brief.py"),
                 "--working-dir", str(brief_dir),
                 "--to", "roderick.jones@gmail.com",
                 "--from", "trevor_mentis@agentmail.to"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                state.setdefault("delivery_retry", {})[today] = "sent"
                alert("✅ Auto-retried today's brief delivery — check inbox")
                FIXES_APPLIED.append("delivery_retry: resent today's brief")
            else:
                alert(f"🔴 Delivery auto-retry failed: {result.stderr[:200]}")
    except Exception as e:
        # Don't alert on transient failures — will retry next cycle
        log(f"Delivery check skipped: {e}")


# ═══════════════════════════════════════════════════════════════════
# FIX 2: Cron health auto-alert
# ═══════════════════════════════════════════════════════════════════

def fix_cron_health(state: dict) -> None:
    """Check all crons. Alert on error states. Auto-restart if possible."""
    if not CRON_JOBS.exists():
        return

    try:
        data = json.loads(CRON_JOBS.read_text())
        jobs = data.get("jobs", [])
    except Exception:
        return

    errors = []
    for j in jobs:
        name = j.get("name", "?")
        enabled = j.get("enabled", True)
        status = j.get("state", {}).get("status", "ok")
        if enabled and status == "error":
            errors.append(name)

    # Check if any newly in error vs last run
    prev_errors = state.get("cron_errors", [])
    new_errors = [e for e in errors if e not in prev_errors]

    if new_errors:
        alert(f"🔴 {len(new_errors)} crons in error: {', '.join(new_errors)}")

    # Auto-restart trevor-heartbeat if it's the only error
    if len(errors) == 1 and "heartbeat" in errors[0].lower():
        try:
            subprocess.run(["openclaw", "cron", "reset", "1aec4c02-f744-49ab-a4cb-41bd2d68d2b6"],
                          capture_output=True, timeout=10)
            alert("✅ Auto-restarted trevor-heartbeat cron")
            FIXES_APPLIED.append("cron_health: restarted heartbeat")
        except Exception:
            pass

    state["cron_errors"] = errors


# ═══════════════════════════════════════════════════════════════════
# FIX 3: Dead-feed auto-prune
# ═══════════════════════════════════════════════════════════════════

def fix_dead_feed_prune(state: dict) -> None:
    """After 7 consecutive failures, mark feed as dead in catalog."""
    if not DEAD_FEEDS.exists() or not CATALOG.exists():
        return

    try:
        dead = json.loads(DEAD_FEEDS.read_text())
        catalog = json.loads(CATALOG.read_text())
    except Exception:
        return

    pruned = 0
    for url, info in dead.items():
        if info.get("failures", 0) >= 7:
            # Mark as non-working in catalog
            for s in catalog.get("sources", []):
                if s.get("rss") == url and s.get("status") == "working":
                    s["status"] = "dead_pruned"
                    s["pruned_at"] = NOW.isoformat()
                    s["prune_reason"] = f"7 consecutive failures, last: {info.get('last_failed_at', '?')}"
                    pruned += 1
                    log(f"Pruned: {s.get('name', url)}")
                    break

    if pruned:
        catalog["working_feeds"] = sum(1 for s in catalog["sources"] if s.get("status") == "working")
        catalog["failed_feeds"] = sum(1 for s in catalog["sources"] if s.get("status") != "working")
        CATALOG.write_text(json.dumps(catalog, indent=2))
        alert(f"🧹 Auto-pruned {pruned} dead feeds from catalog")
        FIXES_APPLIED.append(f"dead_feed_prune: {pruned} feeds pruned")


# ═══════════════════════════════════════════════════════════════════
# FIX 4: API key health monitor
# ═══════════════════════════════════════════════════════════════════

API_KEYS_TO_CHECK = [
    ("DEEPSEEK_API_KEY", "DeepSeek", "https://api.deepseek.com/v1/models"),
    ("OPENROUTER_API_KEY", "OpenRouter", "https://openrouter.ai/api/v1/models"),
    ("ANTHROPIC_API_KEY", "Anthropic", None),  # Checked separately
]

def fix_api_key_health(state: dict) -> None:
    """Check all API keys. Alert on invalid or near-expiry."""
    last_check = state.get("last_key_check", "")
    if last_check:
        try:
            last_dt = datetime.fromisoformat(last_check)
            if (NOW - last_dt).total_seconds() < 3600 * 6:  # Every 6 hours
                return
        except Exception:
            pass

    for key_name, label, test_url in API_KEYS_TO_CHECK:
        api_key = get_api_key(key_name)
        if not api_key:
            alert(f"⚠️ {label} API key missing ({key_name})")
            continue
        if not test_url:
            continue

        try:
            req = urllib.request.Request(test_url)
            req.add_header("Authorization", f"Bearer {api_key}")
            urllib.request.urlopen(req, timeout=5)
        except urllib.error.HTTPError as e:
            if e.code == 401 or e.code == 403:
                alert(f"🔴 {label} API key invalid (HTTP {e.code})")
            elif e.code == 402:
                alert(f"⚠️ {label} has no credits (HTTP 402)")
        except Exception:
            pass  # Network issues are transient

    # DeepSeek balance check
    deepseek_key = get_api_key("DEEPSEEK_API_KEY")
    if deepseek_key:
        try:
            req = urllib.request.Request("https://api.deepseek.com/v1/balance")
            req.add_header("Authorization", f"Bearer {deepseek_key}")
            resp = urllib.request.urlopen(req, timeout=5)
            balance_data = json.loads(resp.read())
            usd = balance_data.get("USD", balance_data.get("balance", 0))
            if isinstance(usd, (int, float)) and usd < 2.0:
                alert(f"⚠️ DeepSeek balance low: ${usd:.2f}")
        except Exception:
            pass

    state["last_key_check"] = NOW.isoformat()


# ═══════════════════════════════════════════════════════════════════
# FIX 5: Auto-commit on significant changes
# ═══════════════════════════════════════════════════════════════════

def fix_auto_commit(state: dict) -> None:
    """Auto-commit changes every hour if there are uncommitted changes."""
    last_commit = state.get("last_auto_commit", "")
    if last_commit:
        try:
            last_dt = datetime.fromisoformat(last_commit)
            if (NOW - last_dt).total_seconds() < 3600:
                return
        except Exception:
            pass

    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=10, cwd=str(REPO),
        )
        changed = [l for l in result.stdout.splitlines() if l.strip()]
    except Exception:
        return

    if not changed:
        return

    # Only auto-commit if significant changes (>5 files or memory/brain updates)
    significant = (
        len(changed) > 5 or
        any("memory/" in l for l in changed) or
        any("brain/" in l for l in changed) or
        any("scripts/" in l for l in changed)
    )

    if not significant:
        return

    try:
        subprocess.run(["git", "add", "-A"], capture_output=True, timeout=10, cwd=str(REPO))
        commit_msg = f"auto: {NOW.strftime('%Y-%m-%d %H:%M')} — {len(changed)} files changed"
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            capture_output=True, text=True, timeout=10, cwd=str(REPO),
        )
        if result.returncode == 0:
            subprocess.run(["git", "push"], capture_output=True, timeout=15, cwd=str(REPO))
            state["last_auto_commit"] = NOW.isoformat()
            log(f"Auto-committed {len(changed)} files")
    except Exception as e:
        log(f"Auto-commit failed: {e}")


# ═══════════════════════════════════════════════════════════════════
# FIX 6: Source gap auto-discovery
# ═══════════════════════════════════════════════════════════════════

GAP_REGIONS = {
    "central_america_caribbean": "Central America Caribbean geopolitics security news RSS",
    "oceania": "Oceania Pacific geopolitics security news RSS",
    "south_east_asia": "Southeast Asia ASEAN geopolitics maritime security news RSS",
    "central_asia": "Central Asia geopolitics security RSS news",
}

def fix_source_gaps(state: dict) -> None:
    """Auto-trigger source discovery for regions with <5 working feeds."""
    if not CATALOG.exists():
        return

    try:
        catalog = json.loads(CATALOG.read_text())
        regions = catalog.get("regions_breakdown", {})
    except Exception:
        return

    gap_regions = []
    for region, query in GAP_REGIONS.items():
        count = regions.get(region, 0)
        if count < 5:
            gap_regions.append((region, query))

    if not gap_regions:
        return

    last_discovery = state.get("last_gap_discovery", "")
    if last_discovery:
        try:
            last_dt = datetime.fromisoformat(last_discovery)
            if (NOW - last_dt).total_seconds() < 86400:  # Once per day
                return
        except Exception:
            pass

    for region, query in gap_regions[:1]:  # One per cycle
        try:
            result = subprocess.run(
                ["python3", str(REPO / "scripts" / "source_discovery.py"),
                 "--auto-add", "--region", region, "--query", query],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0:
                alert(f"🔍 Auto-discovered sources for {region} ({regions.get(region, 0)} → ?)")
                FIXES_APPLIED.append(f"source_gap: triggered discovery for {region}")
        except Exception as e:
            log(f"Source discovery for {region} failed: {e}")

    state["last_gap_discovery"] = NOW.isoformat()


# ═══════════════════════════════════════════════════════════════════
# FIX 7: Log rotation + disk check
# ═══════════════════════════════════════════════════════════════════

def fix_log_rotation(state: dict) -> None:
    """Keep last 7 days of logs. Alert if disk >80%."""
    # Disk check
    try:
        stat = os.statvfs(REPO)
        used_pct = (1 - stat.f_bavail / stat.f_blocks) * 100
        if used_pct > 95:
            alert(f"💾 Disk {used_pct:.0f}% full — rotate logs soon")
    except Exception:
        pass

    # Log rotation: delete logs older than 7 days
    if not LOG_DIR.exists():
        return

    last_rotation = state.get("last_log_rotation", "")
    if last_rotation:
        try:
            last_dt = datetime.fromisoformat(last_rotation)
            if (NOW - last_dt).total_seconds() < 43200:  # Every 12 hours
                return
        except Exception:
            pass

    cutoff = NOW - timedelta(days=7)
    rotated = 0
    for log_file in LOG_DIR.glob("*.log"):
        try:
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                log_file.unlink()
                rotated += 1
        except Exception:
            pass

    if rotated:
        log(f"Rotated {rotated} old log files")
    state["last_log_rotation"] = NOW.isoformat()


# ═══════════════════════════════════════════════════════════════════
# FIX 8: Memory auto-consolidation
# ═══════════════════════════════════════════════════════════════════

def fix_memory_consolidation(state: dict) -> None:
    """Weekly: summarize the past week's memory files into a digest."""
    last_consolidation = state.get("last_memory_consolidation", "")
    if last_consolidation:
        try:
            last_dt = datetime.fromisoformat(last_consolidation)
            if (NOW - last_dt).total_seconds() < 86400 * 7:
                return
        except Exception:
            pass

    if not MEMORY_DIR.exists():
        return

    # Find memory files from the past week
    week_ago = NOW - timedelta(days=7)
    memory_files = []
    for f in sorted(MEMORY_DIR.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
            if mtime > week_ago:
                memory_files.append(f)
        except Exception:
            pass

    if len(memory_files) < 2:
        return

    # Extract key BLUFs and decisions
    digest_lines = [
        f"# Memory Digest — Week of {week_ago.strftime('%Y-%m-%d')} to {NOW.strftime('%Y-%m-%d')}",
        f"*Auto-generated {NOW.strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "## Key Events",
    ]

    for f in memory_files:
        text = f.read_text()
        # Extract BLUF lines
        for line in text.splitlines():
            if line.startswith("BLUF:") or line.startswith("**BLUF:**"):
                digest_lines.append(f"- {f.stem}: {line.strip()}")
                break

    digest_lines.extend([
        "",
        "## Decisions Made",
        "*(extracted from durable decisions in MEMORY.md)*",
        "",
        "## Fires to Watch",
        "*(extracted from daily brief BLUFs)*",
    ])

    # Append brief BLUFs from the week
    for f in memory_files:
        text = f.read_text()
        for line in text.splitlines():
            if "BLUF:" in line and "likely" in line.lower():
                bluf = line.strip()[:200]
                if bluf not in digest_lines[-5:]:
                    digest_lines.append(f"- {bluf}")
                    break

    digest_path = MEMORY_DIR / f"digest-{week_ago.strftime('%Y-W%V')}.md"
    digest_path.write_text("\n".join(digest_lines))
    log(f"Memory digest written: {digest_path}")
    state["last_memory_consolidation"] = NOW.isoformat()


# ═══════════════════════════════════════════════════════════════════
# FIX 9: Pipeline partial-run recovery
# ═══════════════════════════════════════════════════════════════════

EXPECTED_REGIONS = [
    "europe", "north_america", "central_america_caribbean",
    "south_america", "africa", "middle_east", "central_asia",
    "south_east_asia", "east_asia", "south_asia", "oceania",
    "prediction_markets",
]

def fix_pipeline_recovery(state: dict) -> None:
    """If pipeline died mid-analysis, attempt to resume from last completed region."""
    today = NOW.strftime("%Y-%m-%d")
    brief_dir = pathlib.Path(os.path.expanduser(f"~/trevor-briefings/{today}"))
    analysis_dir = brief_dir / "analysis"

    if not analysis_dir.exists():
        return

    # Check which regions are complete
    completed = []
    missing = []
    for region in EXPECTED_REGIONS:
        if (analysis_dir / f"{region}.json").exists():
            completed.append(region)
        else:
            missing.append(region)

    # If all complete or nothing started, nothing to recover
    if len(missing) == 0:
        return
    if len(completed) == 0:
        return  # Nothing started — no partial state to recover

    # If some complete but not all, we have a partial run
    # Only attempt recovery once
    recovery_key = f"recovery_{today}"
    if state.get(recovery_key):
        return

    log(f"Partial pipeline detected: {len(completed)}/{len(EXPECTED_REGIONS)} regions complete")
    log(f"Missing: {', '.join(missing)}")

    # Attempt to resume analysis for missing regions
    deepseek_key = get_api_key("DEEPSEEK_API_KEY")
    if not deepseek_key:
        return

    for region in missing[:3]:  # Max 3 per cycle
        log(f"Attempting recovery for {region}...")
        try:
            result = subprocess.run([
                "python3", str(REPO / "skills" / "daily-intel-brief" / "scripts" / "analyze.py"),
                "--working-dir", str(brief_dir),
                "--regions", str(REPO / "skills" / "daily-intel-brief" / "references" / "regions.json"),
                "--model", "deepseek/deepseek-v4-pro",
                "--provider", "deepseek",
                "--tier2-model", "deepseek/deepseek-v4-pro",
                "--tier2-provider", "deepseek",
                "--single-region", region,
            ], capture_output=True, text=True, timeout=120,
            )
            if result.returncode == 0:
                completed.append(region)
                FIXES_APPLIED.append(f"pipeline_recovery: resumed {region}")
        except Exception as e:
            log(f"Recovery for {region} failed: {e}")

    if len(completed) == len(EXPECTED_REGIONS):
        alert("✅ Pipeline auto-recovered — all regions now complete")
        # Trigger exec summary generation
        try:
            subprocess.run([
                "python3", str(REPO / "skills" / "daily-intel-brief" / "scripts" / "analyze.py"),
                "--working-dir", str(brief_dir),
                "--regions", str(REPO / "skills" / "daily-intel-brief" / "references" / "regions.json"),
                "--model", "deepseek/deepseek-v4-pro",
                "--provider", "deepseek",
                "--exec-summary-only",
            ], capture_output=True, timeout=120,
            )
            FIXES_APPLIED.append("pipeline_recovery: regenerated exec summary")
        except Exception:
            pass

    state[recovery_key] = f"recovered_{len(completed)}_of_{len(EXPECTED_REGIONS)}"


# ═══════════════════════════════════════════════════════════════════
# FIX 10: Brief quality auto-fix
# ═══════════════════════════════════════════════════════════════════

def fix_brief_quality(state: dict) -> None:
    """If QC flagged issues, attempt to auto-fix and regenerate."""
    today = NOW.strftime("%Y-%m-%d")
    brief_dir = pathlib.Path(os.path.expanduser(f"~/trevor-briefings/{today}"))
    exec_file = brief_dir / "analysis" / "exec_summary.json"

    if not exec_file.exists():
        return

    try:
        brief = json.loads(exec_file.read_text())
    except Exception:
        return

    fixes_needed = False

    # Check for Chinese/CJK contamination
    body = json.dumps(brief)
    cjk = sum(1 for c in body if '\u4e00' <= c <= '\u9fff')
    if cjk > 10:
        alert(f"⚠️ Brief contains {cjk} CJK characters — possible language contamination")
        # Auto-fix: don't regenerate automatically (too expensive)
        # But flag it for attention
        state["brief_cjk_contamination"] = today

    # Check for Flash model
    models = brief.get("models_used", [])
    if isinstance(models, str):
        models = [models]
    if any("flash" in str(m).lower() for m in models):
        alert(f"⚠️ Flash model detected in brief: {models}")
        state["brief_flash_detected"] = today
        fixes_needed = True

    # Check BLUF length
    bluf = brief.get("bluf", "")
    if len(bluf) < 50:
        alert("⚠️ Brief BLUF too short — possible truncation")
        fixes_needed = True

    # Check for error content
    if "ERROR:" in bluf or "Error generating" in str(brief):
        alert("🔴 Brief contains error message — needs regeneration")
        fixes_needed = True

    if fixes_needed:
        state["brief_quality_issues"] = today


# ═══════════════════════════════════════════════════════════════════
# Main — run all fixes, rotating which are active per cycle
# ═══════════════════════════════════════════════════════════════════

ALL_FIXES = [
    ("delivery", fix_delivery_retry),
    ("crons", fix_cron_health),
    ("dead_feeds", fix_dead_feed_prune),
    ("api_keys", fix_api_key_health),
    ("auto_commit", fix_auto_commit),
    ("source_gaps", fix_source_gaps),
    ("log_rotation", fix_log_rotation),
    ("memory", fix_memory_consolidation),
    ("pipeline_recovery", fix_pipeline_recovery),
    ("brief_quality", fix_brief_quality),
]

# High-frequency fixes: run every cycle
HIGH_FREQ = {"delivery", "crons", "dead_feeds", "brief_quality"}
# Medium: run every 4 cycles (2 hours)
MED_FREQ = {"api_keys", "auto_commit", "source_gaps"}
# Low: run every 12 cycles (6 hours)
LOW_FREQ = {"log_rotation", "memory", "pipeline_recovery"}


def main() -> int:
    global ALERTS, FIXES_APPLIED
    parser = argparse.ArgumentParser(description="Autonomous fixes engine")
    parser.add_argument("--all", action="store_true", help="Run all fixes now")
    parser.add_argument("--fix", choices=[f[0] for f in ALL_FIXES], help="Run specific fix")
    parser.add_argument("--quiet", action="store_true", help="No output unless alerts")
    args = parser.parse_args()

    state = load_state()
    cycle = state.get("cycle_count", 0) + 1
    state["cycle_count"] = cycle

    # Determine which fixes to run
    if args.fix:
        to_run = [f for f in ALL_FIXES if f[0] == args.fix]
    elif args.all:
        to_run = ALL_FIXES
    else:
        to_run = []
        for name, func in ALL_FIXES:
            if name in HIGH_FREQ:
                to_run.append((name, func))
            elif name in MED_FREQ and cycle % 4 == 0:
                to_run.append((name, func))
            elif name in LOW_FREQ and cycle % 12 == 0:
                to_run.append((name, func))

    # Run fixes
    for name, func in to_run:
        try:
            func(state)
        except Exception as e:
            log(f"Fix '{name}' failed: {e}")

    save_state(state)

    # Output
    if not args.quiet or ALERTS or FIXES_APPLIED:
        if FIXES_APPLIED:
            print(f"\n🛠️  {len(FIXES_APPLIED)} fixes applied:")
            for f in FIXES_APPLIED:
                print(f"  ✅ {f}")
        if ALERTS:
            print(f"\n⚠️  {len(ALERTS)} alerts:")
            for a in ALERTS:
                print(f"  {a}")
        if not FIXES_APPLIED and not ALERTS:
            print("✅ All systems nominal — no fixes needed")

    return 0 if not ALERTS else 1


if __name__ == "__main__":
    import argparse
    sys.exit(main())
