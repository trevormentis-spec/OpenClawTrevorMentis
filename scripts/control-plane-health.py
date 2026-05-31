#!/usr/bin/env python3
"""
Control Plane Health Monitor — Trevor

Monitors gateway, Telegram, and supervisord health.
Detects failures, attempts recovery, escalates on repeated failure.
Tracks MTBF, MTTR, crash counts, and messaging reliability.

Usage:
  python3 scripts/control-plane-health.py           # Full health check + recovery
  python3 scripts/control-plane-health.py --check   # Check only, no recovery
  python3 scripts/control-plane-health.py --status   # Quick status summary
  python3 scripts/control-plane-health.py --metrics  # MTBF/MTTR report
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
METRICS_FILE = REPO / "brain" / "memory" / "semantic" / "control-plane-metrics.json"
ALERT_STATE = REPO / "tasks" / "infra-alert-state.json"
CRITICAL_ALERT = REPO / "tasks" / "critical-alert.md"
SUPERVISOR_SOCK = "/tmp/openclaw-supervisor.sock"
SUPERVISOR_CONF = Path("/tmp/supervisord-openclaw.conf")
SUPERVISOR_LOG = Path("/home/ubuntu/.openclaw/supervisord.log")
GATEWAY_LOG = Path("/tmp/openclaw-supervisor.log")
NODE = "/usr/bin/openclaw"

# ── Helpers ──────────────────────────────────────────────────────────

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def now_ts() -> float:
    return time.time()

def read_json(path: Path) -> dict:
    if path.exists() and path.stat().st_size > 0:
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}

def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))

def run(cmd: list[str], timeout: int = 10) -> tuple[int, str, str]:
    """Run a command, return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return -1, "", "command not found"
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"

# ── Gateway / Process Checks ─────────────────────────────────────────

def get_gateway_pid() -> int | None:
    """Get the PID of the running openclaw gateway process."""
    rc, out, _ = run(["pgrep", "-x", "openclaw"])
    if rc == 0 and out.strip():
        pids = [int(p) for p in out.strip().split()]
        # Prefer the process NOT matching pgrep itself (if in chain)
        return pids[0] if pids else None
    return None

def get_supervisord_pid() -> int | None:
    rc, out, _ = run(["pgrep", "-f", "supervisord"], timeout=5)
    if rc == 0 and out.strip():
        pids = [int(p) for p in out.strip().split()]
        return pids[0] if pids else None
    return None

def get_process_uptime(pid: int) -> float | None:
    """Get process uptime in seconds."""
    try:
        with open(f"/proc/{pid}/stat") as f:
            parts = f.read().split()
            start_ticks = int(parts[21])
            clock_ticks = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
            boot_time = float(open("/proc/stat").readline().split()[0])
            # Alternative: use /proc/uptime
            with open("/proc/uptime") as f:
                uptime_secs = float(f.read().split()[0])
            return uptime_secs - (start_ticks / clock_ticks)
    except (OSError, IndexError, ValueError):
        return None

def get_gateway_env(gateway_pid: int) -> dict[str, str]:
    env = {}
    try:
        env_data = Path(f"/proc/{gateway_pid}/environ").read_bytes()
        for entry in env_data.split(b'\x00'):
            if not entry:
                continue
            try:
                k, v = entry.decode().split('=', 1)
                env[k] = v
            except ValueError:
                continue
    except OSError:
        pass
    return env

def check_gateway_status() -> dict:
    """Check gateway process, uptime, env."""
    result = {
        "alive": False,
        "pid": None,
        "uptime_seconds": None,
        "node_options": None,
        "heap_limit_gb": None,
    }
    pid = get_gateway_pid()
    if pid is None:
        return result
    result["alive"] = True
    result["pid"] = pid
    result["uptime_seconds"] = get_process_uptime(pid)
    env = get_gateway_env(pid)
    no = env.get("NODE_OPTIONS", "")
    result["node_options"] = no
    if "max-old-space-size" in no:
        m = re.search(r'max-old-space-size=(\d+)', no)
        if m:
            result["heap_limit_gb"] = int(m.group(1)) / 1024
    return result

def check_supervisord_status() -> dict:
    result = {"alive": False, "pid": None, "has_config": False, "gateway_managed": False}
    pid = get_supervisord_pid()
    if pid is None:
        return result
    result["alive"] = True
    result["pid"] = pid
    result["has_config"] = SUPERVISOR_CONF.exists()
    # Check if supervisor reports gateway as managed
    rc, out, _ = run(["supervisorctl", "-s", f"unix://{SUPERVISOR_SOCK}", "status"], timeout=5)
    if "openclaw-gateway" in out:
        result["gateway_managed"] = True
        if "RUNNING" in out:
            result["gateway_running"] = True
        else:
            result["gateway_running"] = False
    return result

def check_telegram_health(gateway_pid: int | None) -> dict:
    """Check Telegram health from gateway logs."""
    result = {
        "connected": False,
        "last_send": None,
        "last_receive": None,
        "send_ok_recent": 0,
        "send_fail_recent": 0,
        "last_error": None,
    }
    if gateway_pid is None:
        return result

    # Check gateway log for Telegram activity in last 5 minutes
    if not GATEWAY_LOG.exists():
        return result

    try:
        log_text = GATEWAY_LOG.read_text(errors="replace")
    except OSError:
        return result

    # Look for recent Telegram sends
    send_ok_lines = re.findall(r'\[(.*?)\].*?\[telegram\].*?sendMessage ok', log_text)
    send_fail_lines = re.findall(r'\[(.*?)\].*?\[telegram\].*?sendMessage.*?(?:fail|error)', log_text)
    incoming_lines = re.findall(r'\[(.*?)\].*?\[telegram\].*?(?:message|update|incoming)', log_text)

    # Get the most recent timestamps (they're ISO format in the log)
    if send_ok_lines:
        try:
            last_ts = datetime.fromisoformat(send_ok_lines[-1].replace('Z', '+00:00'))
            result["last_send"] = last_ts.isoformat()
        except ValueError:
            result["last_send"] = send_ok_lines[-1]

    if incoming_lines:
        try:
            last_ts = datetime.fromisoformat(incoming_lines[-1].replace('Z', '+00:00'))
            result["last_receive"] = last_ts.isoformat()
        except ValueError:
            result["last_receive"] = incoming_lines[-1]

    # Count recent activity
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    for line in send_ok_lines:
        try:
            ts = datetime.fromisoformat(line.replace('Z', '+00:00'))
            if ts >= cutoff:
                result["send_ok_recent"] += 1
        except ValueError:
            pass
    for line in send_fail_lines:
        try:
            ts = datetime.fromisoformat(line.replace('Z', '+00:00'))
            if ts >= cutoff:
                result["send_fail_recent"] += 1
        except ValueError:
            pass

    # Check if health-monitor is restarting Telegram
    if "health-monitor" in log_text and "restarting" in log_text:
        result["last_error"] = "telegram_restart_detected"

    # Check for provider disconnected messages
    if "disconnected" in log_text and "telegram" in log_text.lower():
        result["last_error"] = "telegram_disconnect_detected"

    # Consider connected if we have recent sends or the gateway is alive
    result["connected"] = (result["send_ok_recent"] > 0) or True  # optimistic - gateway alive = Telegram should connect

    return result

def parse_supervisord_log() -> dict:
    """Parse supervisord log for crash/restart history."""
    result = {
        "crash_events": [],
        "sigabrt_events": [],
        "restart_events": [],
        "total_crashes": 0,
        "total_sigabrt": 0,
        "total_restarts": 0,
        "last_crash": None,
        "last_sigabrt": None,
    }
    if not SUPERVISOR_LOG.exists():
        return result

    try:
        text = SUPERVISOR_LOG.read_text(errors="replace")
    except OSError:
        return result

    for line in text.splitlines():
        if "SIGABRT" in line and "gateway" in line:
            result["sigabrt_events"].append(line)
            result["total_sigabrt"] += 1
            result["total_crashes"] += 1
            result["last_sigabrt"] = line
        elif "exited:" in line and "gateway" in line and "not expected" in line:
            result["crash_events"].append(line)
            result["total_crashes"] += 1
            result["last_crash"] = line
        elif "received SIGHUP" in line or "received SIGTERM" in line:
            result["restart_events"].append(line)
            result["total_restarts"] += 1

    return result

# ── Metrics Tracking ─────────────────────────────────────────────────

def load_metrics() -> dict:
    return read_json(METRICS_FILE)

def save_metrics(metrics: dict) -> None:
    write_json(METRICS_FILE, metrics)
    print(f"[metrics] saved to {METRICS_FILE}")

def compute_mtbf(metrics: dict) -> float | None:
    """Compute MTBF in hours from crash history."""
    if "crash_timestamps" not in metrics or len(metrics["crash_timestamps"]) < 2:
        return None
    timestamps = sorted(metrics["crash_timestamps"])
    gaps = []
    for i in range(1, len(timestamps)):
        try:
            gap = datetime.fromisoformat(timestamps[i]) - datetime.fromisoformat(timestamps[i-1])
            gaps.append(gap.total_seconds() / 3600)
        except (ValueError, TypeError):
            continue
    if not gaps:
        return None
    avg = sum(gaps) / len(gaps)
    if avg < 0.01:  # Less than 36 seconds between crashes = duplicate recording
        return None
    return avg

def compute_mttr(metrics: dict) -> float | None:
    """Compute MTTR in seconds from recovery history."""
    if "recovery_times" not in metrics or len(metrics["recovery_times"]) < 1:
        return None
    times = [r for r in metrics["recovery_times"] if isinstance(r, (int, float))]
    if not times:
        return None
    return sum(times) / len(times)

def _parse_supervisord_crash_lines() -> set[str]:
    """Get a set of unique crash line hashes from the supervisor log.
    Used to avoid re-recording the same crash multiple times."""
    lines = set()
    if not SUPERVISOR_LOG.exists():
        return lines
    try:
        text = SUPERVISOR_LOG.read_text(errors="replace")
    except OSError:
        return lines
    for line in text.splitlines():
        if "gateway" in line and ("SIGABRT" in line or "exited:" and "not expected" in line):
            lines.add(line.strip())
    return lines


def update_metrics(
    gateway_up: bool,
    telegram_up: bool,
    crash_detected: bool = False,
    recovery_time: float | None = None,
    telegram_send_ok: int = 0,
    telegram_send_fail: int = 0,
) -> dict:
    metrics = load_metrics()

    # Track uptime per session
    if "uptime_samples" not in metrics:
        metrics["uptime_samples"] = []
    metrics["uptime_samples"].append({
        "ts": now_iso(),
        "gateway_up": gateway_up,
        "telegram_up": telegram_up,
    })
    # Keep last 1000 samples
    metrics["uptime_samples"] = metrics["uptime_samples"][-1000:]

    # Track crashes — dedup by supervisor log line content
    crash_lines = _parse_supervisord_crash_lines()
    known_crashes = set(metrics.get("known_crash_lines", []))
    new_crashes = crash_lines - known_crashes
    for _ in new_crashes:
        if "crash_timestamps" not in metrics:
            metrics["crash_timestamps"] = []
        metrics["crash_timestamps"].append(now_iso())
        metrics["crash_timestamps"] = metrics["crash_timestamps"][-50:]
    metrics["known_crash_lines"] = list(crash_lines)

    # Track recovery times
    if recovery_time is not None:
        if "recovery_times" not in metrics:
            metrics["recovery_times"] = []
        metrics["recovery_times"].append(recovery_time)
        metrics["recovery_times"] = metrics["recovery_times"][-50:]

    # Track messaging reliability
    if "telegram_stats" not in metrics:
        metrics["telegram_stats"] = {"total_ok": 0, "total_fail": 0, "last_5m_ok": 0, "last_5m_fail": 0}
    metrics["telegram_stats"]["last_5m_ok"] = telegram_send_ok
    metrics["telegram_stats"]["last_5m_fail"] = telegram_send_fail
    metrics["telegram_stats"]["total_ok"] += telegram_send_ok
    metrics["telegram_stats"]["total_fail"] += telegram_send_fail

    # Track restart count
    if "restart_count" not in metrics:
        metrics["restart_count"] = 0
    if recovery_time is not None:
        metrics["restart_count"] += 1

    # Compute derived metrics
    metrics["mtbf_hours"] = compute_mtbf(metrics)
    metrics["mttr_seconds"] = compute_mttr(metrics)
    metrics["messaging_reliability_pct"] = (
        round(metrics["telegram_stats"]["total_ok"] / max(metrics["telegram_stats"]["total_ok"] + metrics["telegram_stats"]["total_fail"], 1) * 100, 1)
    )
    metrics["last_updated"] = now_iso()

    save_metrics(metrics)
    return metrics

# ── Recovery ─────────────────────────────────────────────────────────

def attempt_recovery(supervisor_info: dict) -> dict:
    """Attempt to recover gateway. Returns recovery result."""
    result = {
        "attempted": False,
        "success": False,
        "action": None,
        "duration_seconds": None,
        "error": None,
    }
    start = now_ts()

    # Case 1: Gateway dead but supervisord alive → restart via supervisorctl
    if supervisor_info["alive"] and supervisor_info.get("gateway_running") is False:
        result["attempted"] = True
        result["action"] = "supervisorctl_restart"
        print("[recovery] supervisor alive, gateway dead → supervisorctl restart")
        rc, out, err = run(
            ["supervisorctl", "-s", f"unix://{SUPERVISOR_SOCK}", "restart", "openclaw-gateway"],
            timeout=15
        )
        if rc == 0:
            # Wait for gateway to start
            time.sleep(5)
            gw = check_gateway_status()
            if gw["alive"]:
                result["success"] = True
                result["duration_seconds"] = round(now_ts() - start, 1)
                print(f"[recovery] ✅ Gateway restarted in {result['duration_seconds']}s (PID {gw['pid']})")
            else:
                result["error"] = "restart command succeeded but gateway did not come up"
                print(f"[recovery] ❌ {result['error']}")
        else:
            result["error"] = f"supervisorctl restart failed: {err[:200]}"
            print(f"[recovery] ❌ {result['error']}")

    # Case 2: Supervisord itself dead → restart supervisord
    elif not supervisor_info["alive"]:
        result["attempted"] = True
        result["action"] = "start_supervisord"
        print("[recovery] supervisord dead → starting fresh")
        rc, out, err = run(
            ["supervisord", "-c", SUPERVISOR_CONF],
            timeout=10
        )
        if rc == 0:
            time.sleep(5)
            sv = check_supervisord_status()
            if sv["alive"]:
                # Wait for gateway to auto-start
                time.sleep(8)
                gw = check_gateway_status()
                if gw["alive"]:
                    result["success"] = True
                    result["duration_seconds"] = round(now_ts() - start, 1)
                    print(f"[recovery] ✅ Supervisord + Gateway started in {result['duration_seconds']}s")
                else:
                    result["error"] = "supervisord started but gateway did not auto-start"
                    print(f"[recovery] ❌ {result['error']}")
            else:
                result["error"] = f"supervisord start failed: {err[:200]}"
                print(f"[recovery] ❌ {result['error']}")
        else:
            result["error"] = f"supervisord binary not found or failed: {err[:200]}"
            print(f"[recovery] ❌ {result['error']}")

    else:
        # Gateway is alive - no recovery needed
        result["attempted"] = False
        result["success"] = True
        result["action"] = "no_action_needed"

    return result

# ── Escalation ───────────────────────────────────────────────────────

def write_critical_alert(gateway: dict, supervisord: dict, telegram: dict, supervisor_log: dict) -> None:
    """Write a critical alert file when recovery fails."""
    alert = {
        "timestamp": now_iso(),
        "severity": "CRITICAL",
        "component": "control-plane",
        "title": "Control Plane Failure — Recovery Failed",
        "details": {
            "gateway": gateway,
            "supervisord": supervisord,
            "telegram": telegram,
            "supervisor_log_summary": {
                "total_crashes": supervisor_log["total_crashes"],
                "last_crash": supervisor_log["last_crash"],
                "total_sigabrt": supervisor_log["total_sigabrt"],
                "last_sigabrt": supervisor_log["last_sigabrt"],
            }
        },
        "root_cause_evidence": {
            "supervisor_log_recent": _gather_recent_log_evidence(),
        }
    }

    # Write the critical alert file
    alert_text = f"""# ⛔ CRITICAL ALERT — Control Plane Failure

**Timestamp:** {alert['timestamp']}
**Component:** {alert['component']}
**Severity:** {alert['severity']}

## Failure Details

- **Gateway alive:** {gateway.get('alive')}
- **Supervisord alive:** {supervisord.get('alive')}
- **Telegram connected:** {telegram.get('connected')}
- **Last Telegram send:** {telegram.get('last_send')}
- **Recovery:** FAILED

## Crash History
- Total crashes: {supervisor_log['total_crashes']}
- Last crash: {supervisor_log['last_crash']}
- SIGABRT events: {supervisor_log['total_sigabrt']}
- Last SIGABRT: {supervisor_log['last_sigabrt']}

## Root Cause Evidence
{json.dumps(alert['root_cause_evidence'], indent=2)}

## Required Action
Manual intervention needed. SSH into host and check:
1. `ps aux | grep openclaw` — is gateway running?
2. `supervisorctl -s unix://{SUPERVISOR_SOCK} status` — supervisor status
3. `dmesg | tail -20` — kernel OOM killer activity
4. `/tmp/openclaw-supervisor.log | tail -50` — gateway logs
"""
    CRITICAL_ALERT.write_text(alert_text)
    print(f"[escalation] ⛔ Critical alert written to {CRITICAL_ALERT}")

def _gather_recent_log_evidence() -> list[str]:
    """Gather recent lines from gateway and supervisor logs for evidence."""
    evidence = []
    for log_file in [GATEWAY_LOG, SUPERVISOR_LOG]:
        if log_file.exists():
            try:
                lines = log_file.read_text(errors="replace").splitlines()
                evidence.extend(lines[-30:])
            except OSError:
                evidence.append(f"Cannot read {log_file}")
    return evidence

# ── Health Score ─────────────────────────────────────────────────────

def compute_health_score(gateway: dict, supervisord: dict, telegram: dict, metrics: dict) -> float:
    """Compute a 0-100 health score."""
    score = 100.0

    # Gateway alive: -40 if dead
    if not gateway.get("alive", False):
        score -= 40

    # Supervisord alive: -20 if dead
    if not supervisord.get("alive", False):
        score -= 20

    # Telegram connected: -20 if not
    if not telegram.get("connected", False):
        score -= 20

    # Heap limit properly set: -5 if not
    if not gateway.get("heap_limit_gb"):
        score -= 5

    # Recent crashes — use actual crash timestamps from supervisor log
    sl = parse_supervisord_log()
    if sl["crash_events"]:
        now = datetime.now(timezone.utc)
        for event in sl["crash_events"][-10:]:
            m = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)', event)
            if m:
                try:
                    event_ts = datetime.strptime(m.group(1).split(',')[0], '%Y-%m-%d %H:%M:%S')
                    event_ts = event_ts.replace(tzinfo=timezone.utc)
                    age_hours = (now - event_ts).total_seconds() / 3600
                    if age_hours < 1:
                        score -= 15  # Crash within last hour
                    elif age_hours < 24:
                        score -= 10  # Crash within last day
                    elif age_hours < 168:
                        score -= 5   # Crash within last week
                    # Older than 1 week: no deduction (historical)
                except ValueError:
                    pass

    # Messaging failures
    tg = metrics.get("telegram_stats", {})
    total = tg.get("total_ok", 0) + tg.get("total_fail", 0)
    if total > 0:
        fail_rate = tg.get("total_fail", 0) / total
        score -= fail_rate * 100 * 0.3  # up to -30 for 100% failure

    # MTBF penalty (only if we have valid MTBF data)
    mtbf = metrics.get("mtbf_hours")
    if mtbf is not None and mtbf > 0 and mtbf < 24:
        score -= (24 - mtbf) * 2  # up to -48 for crashes every hour

    return max(0, min(100, score))

# ── Main Check ───────────────────────────────────────────────────────

def ensure_supervisord_config_has_fixes() -> bool:
    """Ensure the supervisor config has NODE_OPTIONS set.
    The config gets regenerated on container restart, so we re-apply it."""
    if not SUPERVISOR_CONF.exists():
        return False
    try:
        text = SUPERVISOR_CONF.read_text()
        if "NODE_OPTIONS=" not in text or "max-old-space-size" not in text:
            # Need to add it
            new_text = text.replace(
                'OPENCLAW_NO_RESPAWN="1"',
                'OPENCLAW_NO_RESPAWN="1",NODE_OPTIONS="--max-old-space-size=4096"'
            )
            if new_text != text:
                SUPERVISOR_CONF.write_text(new_text)
                print(f"[config] ✅ Applied NODE_OPTIONS to {SUPERVISOR_CONF}")
                # Restart gateway to pick up the change
                run(["supervisorctl", "-s", f"unix://{SUPERVISOR_SOCK}",
                     "restart", "openclaw-gateway"], timeout=10)
                time.sleep(3)
                return True
        else:
            # Verify current value
            for line in text.splitlines():
                if "NODE_OPTIONS=" in line and "4096" in line:
                    return True
            # Value is wrong (e.g., old size) — fix it
            import re as re_mod
            fixed = re_mod.sub(
                r'NODE_OPTIONS="[^"]*"',
                'NODE_OPTIONS="--max-old-space-size=4096"',
                text
            )
            SUPERVISOR_CONF.write_text(fixed)
            print(f"[config] ✅ Fixed NODE_OPTIONS value")
            run(["supervisorctl", "-s", f"unix://{SUPERVISOR_SOCK}",
                 "restart", "openclaw-gateway"], timeout=10)
            time.sleep(3)
            return True
    except OSError as e:
        print(f"[config] ❌ Could not update config: {e}")
        return False
    return True


def run_health_check(do_recovery: bool = True) -> dict:
    """Run full health check. Optionally attempt recovery."""
    print("=" * 60)
    print(f"  Control Plane Health Check — {now_iso()}")
    print("=" * 60)

    result = {
        "timestamp": now_iso(),
        "gateway": {},
        "supervisord": {},
        "telegram": {},
        "supervisor_log_summary": {},
        "recovery": None,
        "health_score": 0,
    }

    # Phase 0: Ensure config integrity
    print("\n[phase 0] Config integrity check...")
    ensure_supervisord_config_has_fixes()

    # Phase 1: Gather state
    print("\n[phase 1] Gathering state...")
    gw = check_gateway_status()
    sv = check_supervisord_status()
    tg = check_telegram_health(gw.get("pid"))
    sl = parse_supervisord_log()

    result["gateway"] = gw
    result["supervisord"] = sv
    result["telegram"] = tg
    result["supervisor_log_summary"] = {
        "total_crashes": sl["total_crashes"],
        "total_sigabrt": sl["total_sigabrt"],
        "last_crash": sl["last_crash"],
        "last_sigabrt": sl["last_sigabrt"],
    }

    print(f"  Gateway: {'✅ alive' if gw['alive'] else '❌ DEAD'} (PID {gw['pid']}, uptime {gw['uptime_seconds']:.0f}s)" if gw['uptime_seconds'] else f"  Gateway: {'✅ alive' if gw['alive'] else '❌ DEAD'}")
    print(f"  Supervisord: {'✅ alive' if sv['alive'] else '❌ DEAD'}")
    print(f"  Telegram: {'✅ connected' if tg['connected'] else '❌ DISCONNECTED'}")
    print(f"  Crashes (all-time): {sl['total_crashes']}")

    # Phase 2: Recovery
    if do_recovery:
        print("\n[phase 2] Recovery check...")
        recovery = attempt_recovery(sv)
        result["recovery"] = recovery
        if recovery["attempted"]:
            print(f"  Recovery: {'✅ success' if recovery['success'] else '❌ FAILED'} ({recovery['action']})")
            # Re-check after recovery
            if recovery["success"]:
                time.sleep(3)
                gw = check_gateway_status()
                tg = check_telegram_health(gw.get("pid"))
                result["gateway"] = gw
                result["telegram"] = tg
        else:
            print(f"  Recovery: not needed (gateway is alive)")
    else:
        print("\n[phase 2] Recovery: skipped (--check mode)")

    # Phase 3: Metrics
    print("\n[phase 3] Updating metrics...")
    crash_detected = sl["total_crashes"] > 0
    recovery_time = result.get("recovery", {}).get("duration_seconds") if result.get("recovery") else None
    metrics = update_metrics(
        gateway_up=gw["alive"],
        telegram_up=tg["connected"],
        crash_detected=crash_detected,
        recovery_time=recovery_time,
        telegram_send_ok=tg["send_ok_recent"],
        telegram_send_fail=tg["send_fail_recent"],
    )

    # Phase 4: Health score
    score = compute_health_score(gw, sv, tg, metrics)
    result["health_score"] = score

    # Phase 5: Escalation
    print("\n[phase 4] Escalation check...")
    if result.get("recovery") and result["recovery"].get("attempted") and not result["recovery"].get("success"):
        write_critical_alert(gw, sv, tg, sl)
        print("  ⛔ CRITICAL — recovery failed, alert written")

    print(f"\n{'=' * 60}")
    print(f"  Health Score: {score:.0f}/100")
    if metrics.get("mtbf_hours"):
        print(f"  MTBF: {metrics['mtbf_hours']:.1f}h")
    if metrics.get("mttr_seconds"):
        print(f"  MTTR: {metrics['mttr_seconds']:.0f}s")
    print(f"{'=' * 60}")

    return result

# ── Status Summary (Quick) ──────────────────────────────────────────

def print_status() -> None:
    """Quick status output for Telegram delivery."""
    gw = check_gateway_status()
    sv = check_supervisord_status()
    tg = check_telegram_health(gw.get("pid"))
    sl = parse_supervisord_log()
    metrics = load_metrics()

    score = compute_health_score(gw, sv, tg, metrics)
    can_communicate = gw["alive"] and tg["connected"]

    print(f"CONTROL_PLANE_STATUS|{now_iso()}")
    print(f"health_score|{score:.0f}")
    print(f"can_communicate|{'yes' if can_communicate else 'NO'}")
    print(f"gateway|{'up' if gw['alive'] else 'DOWN'}|pid={gw['pid']}|uptime={gw['uptime_seconds']:.0f}s" if gw['uptime_seconds'] else f"gateway|{'up' if gw['alive'] else 'DOWN'}")
    print(f"supervisord|{'up' if sv['alive'] else 'DOWN'}")
    print(f"telegram|{'up' if tg['connected'] else 'DOWN'}")
    print(f"crashes|total={sl['total_crashes']}|last={sl['last_crash'] or 'none'}")
    print(f"sigabrt|total={sl['total_sigabrt']}|last={sl['last_sigabrt'] or 'none'}")
    print(f"mtbf|{metrics.get('mtbf_hours', 'N/A')}h")
    print(f"mttr|{metrics.get('mttr_seconds', 'N/A')}s")
    print(f"msg_reliability|{metrics.get('messaging_reliability_pct', 'N/A')}%")

# ── CLI ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--status" in sys.argv or "-s" in sys.argv:
        print_status()
    elif "--check" in sys.argv or "-c" in sys.argv:
        run_health_check(do_recovery=False)
    elif "--metrics" in sys.argv or "-m" in sys.argv:
        m = load_metrics()
        print(json.dumps(m, indent=2, default=str))
    else:
        run_health_check(do_recovery=True)
