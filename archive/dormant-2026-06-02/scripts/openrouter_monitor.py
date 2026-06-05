#!/usr/bin/env python3
"""
OpenRouter Usage Monitor for Trevor

Tracks whether any traffic is going through OpenRouter (should be none unless
a specialist LLM is explicitly requested). Monitors:
  1. OpenRouter plugin status (enabled/disabled)
  2. Any session data routing through OpenRouter
  3. Alerts if unexpected OpenRouter usage detected

Usage:
  python3 openrouter_monitor.py              # Show dashboard
  python3 openrouter_monitor.py --snapshot    # Record a check-in point
  python3 openrouter_monitor.py --alert       # Alert if OR is in use
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────

OPENCLAW_CONFIG = Path.home() / ".openclaw" / "openclaw.json"
SESSIONS_DIR = Path.home() / ".openclaw" / "agents" / "main" / "sessions"
WORKSPACE = Path.home() / ".openclaw" / "workspace"
TRACKING_FILE = WORKSPACE / "brain" / "memory" / "semantic" / "openrouter-usage.json"

# ── Helpers ───────────────────────────────────────────────────────────────

def check_or_plugin_enabled():
    """Check if the OpenRouter plugin is enabled in OpenClaw config."""
    if not OPENCLAW_CONFIG.exists():
        return {"status": "unknown", "reason": f"Config not found at {OPENCLAW_CONFIG}"}

    try:
        with open(OPENCLAW_CONFIG) as f:
            config = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return {"status": "error", "reason": str(e)}

    plugins = config.get("plugins", {}).get("entries", {})
    or_plugin = plugins.get("openrouter", {})

    if not or_plugin:
        return {"status": "not_configured", "reason": "No openrouter entry in plugins"}

    enabled = or_plugin.get("enabled", False)
    return {
        "status": "enabled" if enabled else "disabled",
        "enabled": enabled,
    }


def scan_for_openrouter_usage():
    """Scan session trajectory files for any OpenRouter usage."""
    if not SESSIONS_DIR.exists():
        return []

    or_sessions = []
    traj_files = sorted(SESSIONS_DIR.glob("*.trajectory.jsonl"))

    for traj_file in traj_files:
        session_key = traj_file.stem.replace(".trajectory", "")
        try:
            with open(traj_file) as tf:
                for line in tf:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if entry.get("type") == "model.completed":
                        provider = entry.get("provider", "")
                        if provider == "openrouter":
                            edata = entry.get("data", {})
                            usage = edata.get("usage", {})
                            or_sessions.append({
                                "session_id": session_key,
                                "timestamp": entry.get("ts", ""),
                                "model": entry.get("modelId", "unknown"),
                                "input_tokens": usage.get("input", 0),
                                "output_tokens": usage.get("output", 0),
                                "total_tokens": usage.get("total", 0),
                            })
                            break  # one model.completed per trajectory
        except OSError:
            continue

    return or_sessions


def load_tracking():
    if TRACKING_FILE.exists():
        try:
            with open(TRACKING_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "snapshots": [],
        "or_sessions": [],
        "last_scan": None,
    }


def save_tracking(data):
    TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACKING_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def format_dashboard(data):
    lines = []
    lines.append("=" * 56)
    lines.append("  OPENROUTER USAGE MONITOR — Trevor Agent")
    lines.append("=" * 56)
    lines.append("")

    # Plugin status
    plugin = check_or_plugin_enabled()
    if plugin.get("status") == "disabled":
        lines.append("  ✅ OpenRouter plugin: DISABLED (correct)")
    elif plugin.get("status") == "enabled":
        lines.append("  ⚠️  OpenRouter plugin: ENABLED")
        lines.append("     Specialist LLMs will route through OpenRouter.")
    elif plugin.get("status") == "not_configured":
        lines.append("  ℹ️  OpenRouter: not configured in plugins")
    else:
        lines.append(f"  ❓ OpenRouter: {plugin.get('status')} — {plugin.get('reason','')}")
    lines.append("")

    # Scan for OR usage
    or_sessions = scan_for_openrouter_usage()
    data["or_sessions"] = [
        s for s in or_sessions
        if s["session_id"] not in {x["session_id"] for x in data.get("or_sessions", [])}
    ] + data.get("or_sessions", [])

    if or_sessions:
        lines.append(f"  ⚠️  OpenRouter sessions detected: {len(or_sessions)}")
        lines.append("")
        for s in sorted(or_sessions, key=lambda x: x["timestamp"]):
            lines.append(f"     [{s['session_id'][:12]}] {s['model']}")
            lines.append(f"     {s['timestamp'][:19]} — {s['input_tokens']:,} in / {s['output_tokens']:,} out")
        lines.append("")
    else:
        lines.append("  ✅ No OpenRouter usage detected in session data.")

    lines.append("")
    lines.append("  ┌─ Policy reminder")
    lines.append("  │  OpenRouter should only be used for specialist LLMs")
    lines.append("  │  (image generation, video, or explicit user requests).")
    lines.append("  │  DeepSeek routing must use DeepSeek Direct API only.")
    lines.append("")

    # Recent snapshots
    snapshots = data.get("snapshots", [])
    if snapshots:
        latest = snapshots[-1]
        lines.append(f"  ┌─ Last check-in: {latest.get('timestamp', '?')[:19]}")
        lines.append(f"  │  Plugin status: {latest.get('plugin_status', '?')}")
        lines.append(f"  │  Total OR sessions: {latest.get('total_or_sessions', 0)}")
    lines.append("")

    lines.append("=" * 56)
    lines.append(f"  Data: {TRACKING_FILE}")
    lines.append(f"  Last scan: {data.get('last_scan', 'never')[:19]}")
    lines.append("=" * 56)

    return "\n".join(lines)


def record_snapshot(data):
    plugin = check_or_plugin_enabled()
    or_sessions = scan_for_openrouter_usage()

    # Merge new sessions
    existing_ids = {s["session_id"] for s in data.get("or_sessions", [])}
    fresh = [s for s in or_sessions if s["session_id"] not in existing_ids]
    data.setdefault("or_sessions", []).extend(fresh)

    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "plugin_status": plugin.get("status", "unknown"),
        "plugin_enabled": plugin.get("enabled", False),
        "total_or_sessions": len(data["or_sessions"]),
        "new_or_sessions_since_last": len(fresh),
    }
    data.setdefault("snapshots", []).append(snapshot)
    data["last_scan"] = snapshot["timestamp"]

    return data, snapshot


def check_alert(data):
    """Return alert message if unexpected OpenRouter activity found."""
    or_sessions = data.get("or_sessions", [])
    plugin = check_or_plugin_enabled()

    if plugin.get("status") == "enabled":
        return ("⚠️ OPENROUTER PLUGIN IS ENABLED. Specialist LLM routing active. "
                "Verify this is intentional.")

    if or_sessions:
        recent = or_sessions[-1]
        return (f"⚠️ OpenRouter usage detected — {len(or_sessions)} session(s). "
                f"Latest: {recent['model']} on {recent['timestamp'][:19]}. "
                "Per policy, DeepSeek should use Direct API only.")

    return None


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="OpenRouter Usage Monitor")
    parser.add_argument("--snapshot", action="store_true", help="Record a check-in")
    parser.add_argument("--alert", action="store_true", help="Alert if OR is in use")
    parser.add_argument("--dashboard", action="store_true", help="Show dashboard (default)")
    args = parser.parse_args()

    data = load_tracking()

    if args.snapshot:
        data, snap = record_snapshot(data)
        print(f"✅ Snapshot recorded — OpenRouter plugin status: {snap['plugin_status']}")
        if snap["new_or_sessions_since_last"] > 0:
            print(f"   ⚠️  {snap['new_or_sessions_since_last']} new OpenRouter session(s) detected")

    if args.alert:
        alert = check_alert(data)
        if alert:
            print(alert)
        else:
            print("✅ No OpenRouter alert — all clear.")
        save_tracking(data)
        return

    if args.dashboard or not args.snapshot:
        print(format_dashboard(data))

    save_tracking(data)


if __name__ == "__main__":
    main()
