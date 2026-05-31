#!/usr/bin/env python3
"""
Trevor Unified Health Engine

Aggregates health checks from across the system into one pipeline.
Reads from existing state files — does not re-run checks that have their
own dedicated scripts. This is an aggregator, not a replacement.

Layers:
  0 — GitHub backup staleness
  1 — Infrastructure (gateway, disk, DeepSeek, OpenRouter)
  2 — Cron health (jobs-state.json) with correlation
  3 — Pipeline completion (brief delivered today?)
  4 — Learning & memory health
  5 — Heartbeat cycle tracking
  6 — Cost & budget

Exit code 1 if any CRITICAL or EMERGENCY alert was raised.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ─── Constants ────────────────────────────────────────────────────────

REPO_ROOT = Path("/home/ubuntu/.openclaw/workspace")
CRON_STATE_PATH = Path("/home/ubuntu/.openclaw/cron/jobs-state.json")
CRON_JOBS_PATH = Path("/home/ubuntu/.openclaw/cron/jobs.json")
HEARTBEAT_STATE_PATH = REPO_ROOT / "memory" / "heartbeat-state.json"
DEEPSEEK_USAGE_PATH = REPO_ROOT / "brain" / "memory" / "semantic" / "deepseek-usage.json"
COGNITION_PROMOTIONS_PATH = REPO_ROOT / "brain" / "memory" / "semantic" / "cognition-promotions.json"
BRAIN_INDEX_PATH = REPO_ROOT / "brain" / "index" / "index.json"
RUNTIME_STATE_PATH = REPO_ROOT / "tasks" / "runtime-state.json"
BUDGET_CONFIG_PATH = REPO_ROOT / "config" / "budget.yaml"
INFRA_ALERT_PATH = REPO_ROOT / "tasks" / "infra-alert-state.json"
QC_ALERT_PATH = REPO_ROOT / "tasks" / "qc-alert.md"
CONTROL_PLANE_METRICS_PATH = REPO_ROOT / "brain" / "memory" / "semantic" / "control-plane-metrics.json"
FINAL_BRIEF_PATH = REPO_ROOT / "final" / "brief.md"
EXPORTS_PDFS_DIR = REPO_ROOT / "exports" / "pdfs"
EPISODIC_DIR = REPO_ROOT / "brain" / "memory" / "episodic"
LOGS_DIR = REPO_ROOT / "logs"
DASHBOARD_OUT = REPO_ROOT / "tasks" / "health-dashboard.json"
ALERTS_OUT = REPO_ROOT / "tasks" / "health-alerts.md"
HEALTH_LOG_PATH = LOGS_DIR / "health-engine.log"

# ─── Logging ──────────────────────────────────────────────────────────

LOG = logging.getLogger("health_engine")
LOG_HANDLER_SET = False


def _setup_logging() -> None:
    """Configure logging once."""
    global LOG_HANDLER_SET
    if LOG_HANDLER_SET:
        return
    LOG_HANDLER_SET = True
    LOG.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%dT%H:%M:%S%z"
    )
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(str(HEALTH_LOG_PATH))
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    LOG.addHandler(fh)
    sh = logging.StreamHandler(sys.stderr)
    sh.setLevel(logging.WARNING)
    sh.setFormatter(formatter)
    LOG.addHandler(sh)


# ─── Helpers ──────────────────────────────────────────────────────────

def _now_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def _now_ts() -> float:
    """Return current Unix timestamp."""
    return time.time()


def _today_str() -> str:
    """Return today's date as YYYY-MM-DD in UTC."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _yesterday_str() -> str:
    """Return yesterday's date as YYYY-MM-DD in UTC."""
    return (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")


def _now_hour_pt() -> int:
    """Get current hour in America/Los_Angeles timezone."""
    try:
        import zoneinfo
        pt = zoneinfo.ZoneInfo("America/Los_Angeles")
        return datetime.now(pt).hour
    except Exception:
        return (datetime.now(timezone.utc).hour - 7 + 24) % 24


def _file_mod_hours_ago(path: Path) -> Optional[float]:
    """Return hours since file was last modified, or None if missing."""
    try:
        mtime = path.stat().st_mtime
        return (_now_ts() - mtime) / 3600
    except OSError:
        return None


def _parse_ts(ts_str: str) -> float:
    """Parse an ISO timestamp string to Unix timestamp float."""
    for fmt in [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f+00:00",
        "%Y-%m-%dT%H:%M:%S+00:00",
        "%Y-%m-%dT%H:%M:%S",
    ]:
        try:
            dt = datetime.strptime(ts_str, fmt)
            return dt.timestamp()
        except ValueError:
            continue
    return 0.0


def _safe_read_json(path: Path) -> Optional[Any]:
    """Read and parse a JSON file. Returns None on any failure."""
    try:
        if not path.exists():
            LOG.debug("File not found: %s", path)
            return None
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError, PermissionError) as exc:
        LOG.warning("Failed to read %s: %s", path, exc)
        return None


def _safe_read_json_from_str(s: str) -> Optional[Any]:
    """Parse a JSON string safely."""
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return None


def _safe_read_text(path: Path) -> Optional[str]:
    """Read a text file, return None on failure."""
    try:
        if not path.exists():
            return None
        return path.read_text()
    except OSError as exc:
        LOG.warning("Failed to read %s: %s", path, exc)
        return None


def _run_cmd(cmd: List[str], timeout: int = 15,
             cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """Run a command and return (rc, stdout, stderr)."""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cwd) if cwd else None,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except FileNotFoundError:
        return -2, "", "COMMAND_NOT_FOUND"
    except OSError as exc:
        return -3, "", str(exc)


# ─── Alert Helpers ────────────────────────────────────────────────────

ALERT_LEVELS = {"INFO": 0, "WARNING": 1, "CRITICAL": 2, "EMERGENCY": 3}


def _alert(level: str, layer: str, message: str, *,
           affected_jobs: Optional[List[str]] = None,
           root_cause: str = "") -> Dict[str, Any]:
    """Create an alert dictionary."""
    return {
        "level": level,
        "layer": layer,
        "message": message,
        "affected_jobs": affected_jobs or [],
        "root_cause": root_cause,
        "timestamp": _now_iso(),
    }


def _max_alert_level(alerts: List[Dict[str, Any]]) -> str:
    """Find the highest severity level across alerts."""
    if not alerts:
        return "INFO"
    max_lvl = max(ALERT_LEVELS.get(a["level"], 0) for a in alerts)
    rev = {v: k for k, v in ALERT_LEVELS.items()}
    return rev.get(max_lvl, "INFO")


# ─── Layer 0: GitHub Backup ──────────────────────────────────────────

def check_github_backup(dashboard: Dict[str, Any]) -> None:
    """Layer 0 — Check git staleness and uncommitted/unpushed state."""
    layer: Dict[str, Any] = {
        "status": "ok", "details": "", "uncommitted": 0, "unpushed": 0,
        "last_backup_age_hours": 0, "backup_status": "ok",
    }
    alerts: List[Dict[str, Any]] = []

    try:
        rc, out, _ = _run_cmd(["git", "status", "--porcelain"], cwd=REPO_ROOT)
        uncommitted = len([l for l in out.split("\n") if l.strip()]) if rc == 0 else -1
        layer["uncommitted"] = uncommitted

        rc2, out2, _ = _run_cmd(["git", "log", "--oneline", "origin/main..HEAD"], cwd=REPO_ROOT)
        unpushed = len([l for l in out2.split("\n") if l.strip()]) if rc2 == 0 else -1
        layer["unpushed"] = unpushed

        head_ref = REPO_ROOT / ".git" / "refs" / "heads" / "main"
        last_push = _file_mod_hours_ago(head_ref)
        if last_push is not None:
            layer["last_backup_age_hours"] = round(last_push, 1)

        if last_push is not None and last_push > 72:
            layer["backup_status"] = "critical"
            alerts.append(_alert(
                "CRITICAL", "github_backup",
                f"No git backup in {last_push:.0f}h (>72h threshold)",
                root_cause="No push in 3+ days",
            ))
        elif last_push is not None and last_push > 48:
            layer["backup_status"] = "stale"
            alerts.append(_alert(
                "WARNING", "github_backup",
                f"No git backup in {last_push:.0f}h (>48h threshold)",
                root_cause="No push in 2+ days",
            ))
        elif uncommitted > 0 and last_push is not None and last_push > 24:
            alerts.append(_alert(
                "WARNING", "github_backup",
                f"{uncommitted} uncommitted files, last push {last_push:.0f}h ago",
                root_cause="Uncommitted work may be lost",
            ))
        elif unpushed > 0 and last_push is not None and last_push > 48:
            alerts.append(_alert(
                "WARNING", "github_backup",
                f"{unpushed} unpushed commits, last push {last_push:.0f}h ago",
            ))

        layer["details"] = (
            f"{uncommitted} uncommitted, {unpushed} unpushed, "
            f"last push {layer['last_backup_age_hours']}h ago"
            if last_push else "git info unavailable"
        )

    except Exception as exc:
        LOG.exception("GitHub backup check failed")
        layer["status"] = "error"
        layer["details"] = str(exc)
        alerts.append(_alert("CRITICAL", "github_backup",
                             f"GitHub backup check failed: {exc}"))

    layer["alerts"] = alerts
    dashboard["layers"]["github_backup"] = layer
    dashboard["alerts"].extend(alerts)


# ─── Layer 1: Infrastructure ─────────────────────────────────────────

def check_infrastructure(dashboard: Dict[str, Any]) -> None:
    """Layer 1 — Gateway, supervisord, disk, DeepSeek, OpenRouter, system stats."""
    layer: Dict[str, Any] = {
        "status": "ok", "gateway": False, "disk_pct": 0,
        "deepseek_balance": 0.0, "openrouter_ok": False, "supervisord": False,
        "uptime": "", "load_avg": [], "memory_used_gb": 0, "memory_available_gb": 0,
    }
    alerts: List[Dict[str, Any]] = []

    try:
        rc, _, _ = _run_cmd(["pgrep", "-x", "openclaw"])
        gateway_running = rc == 0
        layer["gateway"] = gateway_running
        if not gateway_running:
            alerts.append(_alert("EMERGENCY", "infrastructure",
                                 "Gateway (openclaw) process is NOT running!"))

        rc2, _, _ = _run_cmd(["pgrep", "-x", "supervisord"])
        layer["supervisord"] = rc2 == 0

        rc3, out3, _ = _run_cmd(["df", "-h", "/"])
        disk_pct = 0
        if rc3 == 0:
            for line in out3.split("\n"):
                m = re.search(r"(\d+)%", line)
                if m:
                    disk_pct = int(m.group(1))
                    break
        layer["disk_pct"] = disk_pct

        # System stats: uptime, load, memory
        rc_upt, out_upt, _ = _run_cmd(["uptime"])
        if rc_upt == 0:
            # Extract load avg
            uptime_parts = out_upt.split("load average:")
            if len(uptime_parts) > 1:
                loads = uptime_parts[1].strip().split(", ")
                layer["load_avg"] = [float(x) for x in loads]
            # Extract uptime duration
            m = re.search(r"up\s+(.+?),\s+\d+ user", out_upt)
            if m:
                layer["uptime"] = m.group(1).strip()

        rc_mem, out_mem, _ = _run_cmd(["free", "-g"])
        if rc_mem == 0:
            lines = out_mem.split("\n")
            for line in lines:
                parts = line.split()
                if parts and parts[0] == "Mem:":
                    try:
                        total = float(parts[1])
                        used = float(parts[2])
                        avail = float(parts[6]) if len(parts) > 6 else total - used
                        layer["memory_used_gb"] = used
                        layer["memory_available_gb"] = avail
                    except (ValueError, IndexError):
                        pass
        if disk_pct >= 95:
            alerts.append(_alert("EMERGENCY", "infrastructure",
                                 f"Disk at {disk_pct}% (>95% threshold)"))
        elif disk_pct >= 90:
            alerts.append(_alert("CRITICAL", "infrastructure",
                                 f"Disk at {disk_pct}% (>90% threshold)"))
        elif disk_pct >= 85:
            alerts.append(_alert("WARNING", "infrastructure",
                                 f"Disk at {disk_pct}% (>85% threshold)"))

        deepseek_balance = 0.0
        du = _safe_read_json(DEEPSEEK_USAGE_PATH)
        if du and "snapshots" in du and du["snapshots"]:
            latest = du["snapshots"][-1]
            bal = latest.get("balance", {})
            deepseek_balance = bal.get("total_balance", 0.0)
        layer["deepseek_balance"] = deepseek_balance
        if deepseek_balance < 1.0:
            alerts.append(_alert("CRITICAL", "infrastructure",
                                 f"DeepSeek balance ${deepseek_balance:.2f} < $1.00",
                                 root_cause="DeepSeek billing exhausted"))
        elif deepseek_balance < 5.0:
            alerts.append(_alert("WARNING", "infrastructure",
                                 f"DeepSeek balance ${deepseek_balance:.2f} < $5.00",
                                 root_cause="DeepSeek balance low"))

        rt = _safe_read_json(RUNTIME_STATE_PATH)
        if rt and rt.get("degraded_mode", False):
            layer["openrouter_ok"] = False
            alerts.append(_alert("WARNING", "infrastructure",
                                 "System running in degraded mode"))
        else:
            layer["openrouter_ok"] = True

        critical_cnt = len([a for a in alerts if a["level"] in ("CRITICAL", "EMERGENCY")])
        if critical_cnt > 0:
            layer["status"] = "critical"
        elif alerts:
            layer["status"] = "degraded"

    except Exception as exc:
        LOG.exception("Infrastructure check failed")
        layer["status"] = "error"
        alerts.append(_alert("CRITICAL", "infrastructure",
                             f"Infra check failed: {exc}"))

    layer["alerts"] = alerts
    dashboard["layers"]["infrastructure"] = layer
    dashboard["alerts"].extend(alerts)

    # Absorb crash tracking from old control-plane metrics
    _absorb_crash_tracking(dashboard)


# ─── Crash Tracking ──────────────────────────────────────────────────

def _absorb_crash_tracking(dashboard: Dict[str, Any]) -> None:
    """Read the old control-plane-metrics.json for crash data."""
    try:
        cp = _safe_read_json(CONTROL_PLANE_METRICS_PATH)
        if not cp:
            return

        layer = dashboard["layers"].get("infrastructure", {})

        # Count SIGABRT crash entries
        sigabrt_count = 0
        crash_count_24h = 0
        last_crash_ts = None

        # Check for crash_samples list
        crashes = cp.get("crash_samples", cp.get("crashes", []))
        if crashes:
            now = _now_ts()
            cutoff_24h = now - 86400
            for crash in crashes:
                ts_str = crash.get("ts", crash.get("timestamp", ""))
                crash_ts = _parse_ts(ts_str)
                if crash_ts > cutoff_24h:
                    crash_count_24h += 1
                if crash_ts > last_crash_ts if last_crash_ts else True:
                    last_crash_ts = crash_ts
                reason = (crash.get("reason", "") + " " + crash.get("signal", "")).lower()
                if "sigabrt" in reason or "sigabrt" in crash.get("exit_status", ""):
                    sigabrt_count += 1

        # Check uptime samples
        uptime = cp.get("uptime_samples", cp.get("uptime", []))
        message_reliability = getattr(cp, "get", lambda k, d=None: d)("message_reliability", None)
        if message_reliability is None and uptime:
            recent = [s for s in uptime if _parse_ts(s.get("ts", "")) > _now_ts() - 3600]
            down = sum(1 for s in recent if not s.get("telegram_up", True))
            message_reliability = (len(recent) - down) / max(len(recent), 1) * 100 if recent else 100.0

        layer["crash_tracking"] = {
            "crashes_24h": crash_count_24h,
            "sigabrt_24h": sigabrt_count,
            "last_crash_ts": last_crash_ts,
            "message_reliability_pct": round(message_reliability, 1) if message_reliability is not None else 100.0,
        }

        # Alert on high crash rate
        alerts = layer.get("alerts", [])
        if crash_count_24h > 10:
            alerts.append(_alert(
                "WARNING", "infrastructure",
                f"High crash rate: {crash_count_24h} crashes in 24h ({sigabrt_count} SIGABRTs)",
            ))
        if crash_count_24h > 30:
            alerts.append(_alert(
                "CRITICAL", "infrastructure",
                f"Extreme crash rate: {crash_count_24h} crashes in 24h — investigate gateway stability",
            ))
        layer["alerts"] = alerts

    except Exception as exc:
        LOG.warning("Crash tracking absorb failed (non-fatal): %s", exc)


# ─── Layer 2: Cron Health + Correlation ─────────────────────────────

def check_cron_health(dashboard: Dict[str, Any]) -> None:
    """Layer 2 — Read jobs-state.json, flag failing jobs, correlate."""
    layer: Dict[str, Any] = {
        "status": "ok", "enabled": 0, "failing": 0, "failing_pct": 0,
        "total_jobs": 0, "systemic_errors": [], "correlated_alerts": [],
    }
    alerts: List[Dict[str, Any]] = []

    try:
        state = _safe_read_json(CRON_STATE_PATH)
        if not state or "jobs" not in state:
            alerts.append(_alert("WARNING", "cron_health",
                                 "Cannot read cron jobs-state.json or no jobs found"))
            layer["status"] = "unknown"
            layer["alerts"] = alerts
            dashboard["layers"]["cron_health"] = layer
            dashboard["alerts"].extend(alerts)
            return

        jobs = state.get("jobs", {})
        enabled_count = 0
        failing_jobs: List[Dict[str, Any]] = []
        error_groups: Dict[str, List[str]] = {}
        now_ts = _now_ts()

        for jid, jdata in jobs.items():
            si = _safe_read_json_from_str(jdata.get("scheduleIdentity", "{}"))
            if si is None:
                si = {}
            enabled = si.get("enabled", False)
            if not enabled:
                continue

            enabled_count += 1
            sd = jdata.get("state", {})
            last_status = sd.get("lastRunStatus", "?")
            consec_errors = sd.get("consecutiveErrors", 0)
            last_error = sd.get("lastError", "") or ""
            last_error_reason = sd.get("lastErrorReason", "") or ""
            last_run_ms = sd.get("lastRunAtMs")

            is_failing = False
            job_info: Dict[str, Any] = {
                "id": jid[:8],
                "status": last_status,
                "consecutive_errors": consec_errors,
                "last_error": last_error[:80],
                "last_error_reason": last_error_reason,
            }

            if consec_errors >= 3:
                is_failing = True
                job_info["reason"] = f"{consec_errors} consecutive errors"

            err_lower = (last_error + " " + last_error_reason).lower()
            if "billing" in err_lower:
                is_failing = True
                job_info["reason"] = "billing error"
                if "billing" not in layer["systemic_errors"]:
                    layer["systemic_errors"].append("billing")

            if "timeout" in err_lower:
                is_failing = True
                job_info["reason"] = "timeout"

            if "all models failed" in err_lower:
                is_failing = True
                job_info.setdefault("reasons", []).append("all models failed (DeepSeek?)")

            if "gateway restart" in err_lower:
                is_failing = True
                job_info.setdefault("reasons", []).append("interrupted by gateway restart")

            if last_run_ms:
                age_h = (now_ts - last_run_ms / 1000) / 3600
                job_info["age_hours"] = round(age_h, 1)

            if is_failing:
                failing_jobs.append(job_info)
                if last_error:
                    ek = last_error[:60]
                    error_groups.setdefault(ek, []).append(jid[:8])

        # Correlation: if >=3 jobs share identical error
        for error_text, job_ids in error_groups.items():
            if len(job_ids) >= 3:
                root = "billing" if "billing" in error_text.lower() else "unknown"
                lvl = "CRITICAL" if "billing" in error_text.lower() else "WARNING"
                alerts.append(_alert(
                    lvl, "cron_health",
                    f"Correlated error across {len(job_ids)} jobs: {error_text[:60]}",
                    affected_jobs=job_ids,
                    root_cause=root,
                ))

        layer["enabled"] = enabled_count
        layer["failing"] = len(failing_jobs)
        layer["failing_pct"] = round(len(failing_jobs) / max(enabled_count, 1) * 100, 1)
        layer["total_jobs"] = len(jobs)
        layer["failing_jobs"] = failing_jobs

        if layer["failing_pct"] >= 50:
            layer["status"] = "critical"
            alerts.append(_alert("CRITICAL", "cron_health",
                                 f"{len(failing_jobs)}/{enabled_count} enabled jobs "
                                 f"failing ({layer['failing_pct']}%)",
                                 root_cause=">50% of enabled cron jobs failing"))
        elif layer["failing_pct"] >= 20:
            layer["status"] = "degraded"
            alerts.append(_alert("WARNING", "cron_health",
                                 f"{len(failing_jobs)}/{enabled_count} enabled jobs "
                                 f"failing ({layer['failing_pct']}%)",
                                 root_cause=">20% of enabled cron jobs failing"))

        if "billing" in layer["systemic_errors"]:
            billing_jobs = [j for j in failing_jobs
                            if j.get("reason") == "billing error"]
            if billing_jobs:
                alerts.append(_alert(
                    "CRITICAL", "cron_health",
                    f"Systemic billing error affecting {len(billing_jobs)} jobs",
                    affected_jobs=[j["id"] for j in billing_jobs],
                    root_cause="DeepSeek billing exhausted",
                ))

    except Exception as exc:
        LOG.exception("Cron health check failed")
        layer["status"] = "error"
        alerts.append(_alert("CRITICAL", "cron_health",
                             f"Cron health check failed: {exc}"))

    layer["alerts"] = alerts
    dashboard["layers"]["cron_health"] = layer
    dashboard["alerts"].extend(alerts)


# ─── Layer 3: Pipeline Completion ─────────────────────────────────────

def check_pipeline_completion(dashboard: Dict[str, Any]) -> None:
    """Layer 3 — Did today's brief get delivered?"""
    layer: Dict[str, Any] = {
        "status": "ok", "brief_today": False, "qc_passed": True,
        "landing_page": False, "pdf_today": False,
    }
    alerts: List[Dict[str, Any]] = []
    today = _today_str()

    try:
        brief_text = _safe_read_text(FINAL_BRIEF_PATH)
        if brief_text:
            layer["brief_today"] = today in brief_text
        if not layer["brief_today"]:
            alerts.append(_alert(
                "CRITICAL", "pipeline",
                f"final/brief.md missing or doesn't contain today ({today})",
                root_cause="Daily brief pipeline may not have run",
            ))

        if EXPORTS_PDFS_DIR.exists():
            pdfs = list(EXPORTS_PDFS_DIR.glob("*.pdf"))
            layer["pdf_today"] = any(today in p.name for p in pdfs)

        qc_text = _safe_read_text(QC_ALERT_PATH)
        if qc_text and "CRITICAL" in qc_text:
            layer["qc_passed"] = False
            alerts.append(_alert("CRITICAL", "pipeline",
                                 "QC alert file has CRITICAL failures",
                                 root_cause="Quality control gates blocked"))

        rc, out, _ = _run_cmd(
            ["git", "log", "--oneline", "-1", "--format=%cd",
             "--date=format:%Y-%m-%d"],
            cwd=REPO_ROOT,
        )
        if rc == 0 and out.strip() == today:
            layer["landing_page"] = True

    except Exception as exc:
        LOG.exception("Pipeline check failed")
        layer["status"] = "error"
        alerts.append(_alert("CRITICAL", "pipeline",
                             f"Pipeline check failed: {exc}"))

    layer["alerts"] = alerts
    dashboard["layers"]["pipeline"] = layer
    dashboard["alerts"].extend(alerts)


# ─── Layer 4: Learning & Memory ──────────────────────────────────────

def check_learning_memory(dashboard: Dict[str, Any]) -> None:
    """Layer 4 — Episodic logs, brain index, dreams, cognition."""
    layer: Dict[str, Any] = {
        "status": "ok", "episodic_today": False, "episodic_yesterday": False,
        "brain_index_fresh": False, "dream_completed": False,
        "cognition_recent": False,
    }
    alerts: List[Dict[str, Any]] = []
    today = _today_str()
    yesterday = _yesterday_str()

    try:
        today_ep = EPISODIC_DIR / f"{today}.jsonl"
        if today_ep.exists():
            count = len(today_ep.read_text().splitlines())
            layer["episodic_today"] = count > 0

        yesterday_ep = EPISODIC_DIR / f"{yesterday}.jsonl"
        if yesterday_ep.exists():
            count = len(yesterday_ep.read_text().splitlines())
            layer["episodic_yesterday"] = count > 0

        # Check most recent non-empty episodic file
        all_ep = sorted(EPISODIC_DIR.glob("*.jsonl"), reverse=True)
        most_recent_ep = None
        for ep in all_ep:
            if ep.read_text().strip():
                most_recent_ep = ep
                break
        if most_recent_ep:
            age_h = _file_mod_hours_ago(most_recent_ep) or 0
            if age_h > 36:
                alerts.append(_alert(
                    "CRITICAL", "learning_memory",
                    f"No episodic log in {age_h:.0f}h (>36h)",
                    root_cause="Continuous cognition may have stopped",
                ))
        elif today_ep.exists() and not today_ep.read_text().strip():
            alerts.append(_alert(
                "CRITICAL", "learning_memory",
                "Episodic log exists but is empty",
            ))

        idx_age = _file_mod_hours_ago(BRAIN_INDEX_PATH)
        if idx_age is not None:
            layer["brain_index_fresh"] = idx_age < 24
            if not layer["brain_index_fresh"]:
                alerts.append(_alert(
                    "WARNING", "learning_memory",
                    f"Brain index is {idx_age:.0f}h old (>24h)",
                    root_cause="Brain index not updated",
                ))

        dream_log_path = LOGS_DIR / f"dream-{today}.log"
        if dream_log_path.exists():
            dlog_text = _safe_read_text(dream_log_path) or ""
            layer["dream_completed"] = (
                "completed" in dlog_text.lower()
                or "success" in dlog_text.lower()
            )

        cog_age = _file_mod_hours_ago(COGNITION_PROMOTIONS_PATH)
        if cog_age is not None:
            layer["cognition_recent"] = cog_age < 168
            if not layer["cognition_recent"]:
                alerts.append(_alert(
                    "WARNING", "learning_memory",
                    f"Cognition promotions not updated in {cog_age:.0f}h (>{7*24}h)",
                    root_cause="Cognition bridge may have stopped",
                ))

        if not layer["episodic_today"] and not layer["episodic_yesterday"]:
            alerts.append(_alert(
                "WARNING", "learning_memory",
                "No episodic logs for today or yesterday",
                root_cause="Cognition daemon may not be running",
            ))

    except Exception as exc:
        LOG.exception("Learning/memory check failed")
        layer["status"] = "error"
        alerts.append(_alert("CRITICAL", "learning_memory",
                             f"Check failed: {exc}"))

    layer["alerts"] = alerts
    dashboard["layers"]["learning_memory"] = layer
    dashboard["alerts"].extend(alerts)


# ─── Layer 5: Heartbeat Cycle ────────────────────────────────────────

def check_heartbeat_cycle(dashboard: Dict[str, Any]) -> None:
    """Layer 5 — Heartbeat cycle tracking."""
    layer: Dict[str, Any] = {
        "status": "ok", "cycle_complete": True, "phases_stale": [],
        "last_heartbeat_hours": 0,
    }
    alerts: List[Dict[str, Any]] = []
    now_ts = _now_ts()

    try:
        hb = _safe_read_json(HEARTBEAT_STATE_PATH)
        if not hb:
            alerts.append(_alert("WARNING", "heartbeat",
                                 "Cannot read heartbeat state"))
            layer["status"] = "unknown"
            layer["alerts"] = alerts
            dashboard["layers"]["heartbeat"] = layer
            dashboard["alerts"].extend(alerts)
            return

        last_hb_ts = hb.get("lastHeartbeat", 0)
        layer["last_heartbeat_hours"] = (
            round((now_ts - last_hb_ts) / 3600, 1) if last_hb_ts else 0
        )
        layer["cycle_complete"] = hb.get("currentPhase") is None
        layer["current_phase"] = hb.get("currentPhase")

        last_checks = hb.get("lastChecks", {})
        stale_phases = []
        for phase_key, ts in last_checks.items():
            age_h = (now_ts - ts) / 3600
            if age_h > 48:
                stale_phases.append(f"{phase_key} ({age_h:.0f}h)")
        layer["phases_stale"] = stale_phases

        if stale_phases:
            alerts.append(_alert(
                "WARNING", "heartbeat",
                f"Stale phases: {', '.join(stale_phases)}",
                root_cause="Some heartbeat phases haven't run in >48h",
            ))

        if last_hb_ts and (now_ts - last_hb_ts) > 72 * 3600:
            alerts.append(_alert(
                "CRITICAL", "heartbeat",
                f"Heartbeat not seen in {layer['last_heartbeat_hours']:.0f}h (>72h)",
                root_cause="Heartbeat cycle may be completely stopped",
            ))

    except Exception as exc:
        LOG.exception("Heartbeat check failed")
        layer["status"] = "error"
        alerts.append(_alert("CRITICAL", "heartbeat",
                             f"Check failed: {exc}"))

    layer["alerts"] = alerts
    dashboard["layers"]["heartbeat"] = layer
    dashboard["alerts"].extend(alerts)


# ─── Layer 6: Cost & Budget ──────────────────────────────────────────

def _compute_burn(du: Dict[str, Any]) -> Tuple[float, float]:
    """Compute daily burn rate and runway days from DeepSeek snapshots."""
    snapshots = du.get("snapshots", [])
    if not snapshots:
        return 0.0, 0.0
    latest = snapshots[-1]
    balance = latest.get("balance", {}).get("total_balance", 0.0)
    if len(snapshots) < 2:
        return 0.0, 0.0
    cutoff = _now_ts() - 7 * 86400
    recent = [s for s in snapshots
              if _parse_ts(s.get("timestamp", "")) > cutoff]
    if len(recent) < 2:
        return 0.0, 0.0
    first_bal = recent[0].get("balance", {}).get("total_balance", 0.0)
    last_bal = recent[-1].get("balance", {}).get("total_balance", 0.0)
    span = (_parse_ts(recent[-1].get("timestamp", ""))
            - _parse_ts(recent[0].get("timestamp", "")))
    if span <= 0:
        return 0.0, 0.0
    days = span / 86400
    spent = first_bal - last_bal
    if spent <= 0:
        return 0.0, 0.0
    burn = spent / days
    runway = balance / burn if burn > 0 else 0.0
    return burn, runway


def check_cost_budget(dashboard: Dict[str, Any]) -> None:
    """Layer 6 — Cost, burn rate, runway."""
    layer: Dict[str, Any] = {
        "status": "ok", "balance": 0.0, "burn_rate_daily": 0.0,
        "runway_days": 0.0, "daily_cap_pct": 0.0,
        "daily_cap": 10.0,
    }
    alerts: List[Dict[str, Any]] = []

    try:
        du = _safe_read_json(DEEPSEEK_USAGE_PATH)
        if not du or "snapshots" not in du or not du["snapshots"]:
            alerts.append(_alert("WARNING", "cost_budget",
                                 "No DeepSeek usage snapshots found"))
            layer["status"] = "unknown"
            layer["alerts"] = alerts
            dashboard["layers"]["cost_budget"] = layer
            dashboard["alerts"].extend(alerts)
            return

        latest = du["snapshots"][-1]
        balance = latest.get("balance", {}).get("total_balance", 0.0)
        layer["balance"] = balance

        burn_rate, runway = _compute_burn(du)
        layer["burn_rate_daily"] = round(burn_rate, 2)
        layer["runway_days"] = round(runway, 1)

        # Daily cap from budget config (simple YAML scan)
        daily_cap = 10.0
        budget_text = _safe_read_text(BUDGET_CONFIG_PATH)
        if budget_text:
            m = re.search(r"routine_ops:\s*([0-9.]+)", budget_text)
            if m:
                daily_cap = float(m.group(1))
        layer["daily_cap"] = daily_cap

        if burn_rate > 0:
            cap_pct = (burn_rate / daily_cap) * 100
            layer["daily_cap_pct"] = round(cap_pct, 1)
        else:
            layer["daily_cap_pct"] = 0

        if balance < 2.0:
            alerts.append(_alert("CRITICAL", "cost_budget",
                                 f"DeepSeek balance ${balance:.2f} < $2.00",
                                 root_cause="DeepSeek nearly exhausted"))
        elif balance < 10.0:
            alerts.append(_alert("WARNING", "cost_budget",
                                 f"DeepSeek balance ${balance:.2f} < $10.00"))

        if layer["daily_cap_pct"] >= 80:
            alerts.append(_alert(
                "WARNING", "cost_budget",
                f"Daily burn ${burn_rate:.2f} is {cap_pct:.0f}% of cap (${daily_cap})",
                root_cause="Budget cap approaching",
            ))

    except Exception as exc:
        LOG.exception("Cost/budget check failed")
        layer["status"] = "error"
        alerts.append(_alert("CRITICAL", "cost_budget",
                             f"Check failed: {exc}"))

    layer["alerts"] = alerts
    dashboard["layers"]["cost_budget"] = layer
    dashboard["alerts"].extend(alerts)


# ─── Health Score ─────────────────────────────────────────────────────

def compute_health_score(dashboard: Dict[str, Any]) -> None:
    """Compute 0-100 health score based on layer alerts."""
    score = 100
    alerts = dashboard.get("alerts", [])

    for a in alerts:
        lvl = a.get("level", "INFO")
        if lvl == "EMERGENCY":
            score -= 25
        elif lvl == "CRITICAL":
            score -= 20
        elif lvl == "WARNING":
            score -= 10

    layers = dashboard.get("layers", {})
    pipeline = layers.get("pipeline", {})
    if pipeline.get("status") in ("critical", "error") and not pipeline.get("brief_today", True):
        score -= 15

    learning = layers.get("learning_memory", {})
    if learning.get("status") in ("critical", "error"):
        score -= 10
    elif not learning.get("episodic_today") and not learning.get("episodic_yesterday"):
        score -= 5

    cron = layers.get("cron_health", {})
    failing_pct = cron.get("failing_pct", 0)
    score -= int(failing_pct / 10) * 5

    score = max(0, min(100, score))

    if score >= 90:
        label = "HEALTHY"
    elif score >= 70:
        label = "DEGRADED"
    elif score >= 50:
        label = "SICK"
    else:
        label = "CRITICAL"

    dashboard["health_score"] = score
    dashboard["health_label"] = label


# ─── Output Writers ───────────────────────────────────────────────────

def write_dashboard(dashboard: Dict[str, Any]) -> None:
    """Write dashboard JSON atomically."""
    DASHBOARD_OUT.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(dashboard, indent=2, default=str)
    try:
        tmp = DASHBOARD_OUT.with_suffix(".json.tmp")
        tmp.write_text(data)
        tmp.rename(DASHBOARD_OUT)
        LOG.info("Dashboard written to %s", DASHBOARD_OUT)
    except OSError as exc:
        LOG.error("Failed to write dashboard: %s", exc)


def write_alerts(dashboard: Dict[str, Any]) -> None:
    """Write human-readable alert log."""
    alerts = dashboard.get("alerts", [])
    score = dashboard.get("health_score", 100)
    label = dashboard.get("health_label", "HEALTHY")

    lines = [
        "# Trevor Health Alerts",
        "",
        f"**Generated:** {_now_iso()}",
        f"**Health Score:** {label} ({score}/100)",
        f"**Total Alerts:** {len(alerts)}",
        "",
    ]

    if not alerts:
        lines.append("✅ No alerts — everything is healthy.")
    else:
        for a in alerts:
            level = a.get("level", "INFO")
            emoji = {"INFO": "ℹ️", "WARNING": "⚠️",
                     "CRITICAL": "🔴", "EMERGENCY": "🚨"}
            lines.append(
                f"{emoji.get(level, 'ℹ️')} **[{level}]** {a.get('layer')}: "
                f"{a.get('message')}"
            )
            if a.get("affected_jobs"):
                lines.append(
                    f"   Affected jobs: {', '.join(a['affected_jobs'][:5])}"
                )
            if a.get("root_cause"):
                lines.append(f"   Root cause: {a['root_cause']}")
            lines.append("")

    ALERTS_OUT.parent.mkdir(parents=True, exist_ok=True)
    try:
        ALERTS_OUT.write_text("\n".join(lines))
        LOG.info("Alerts written to %s", ALERTS_OUT)
    except OSError as exc:
        LOG.error("Failed to write alerts: %s", exc)


def escalate_if_needed(dashboard: Dict[str, Any]) -> None:
    """Print Telegram-friendly single-line alert if CRITICAL/EMERGENCY."""
    alerts = dashboard.get("alerts", [])
    severity = _max_alert_level(alerts)
    if severity in ("CRITICAL", "EMERGENCY"):
        criticals = [a for a in alerts
                     if a["level"] in ("CRITICAL", "EMERGENCY")]
        for a in criticals[:5]:
            line = f"ALERT:{a['level']}: {a['layer']}: {a['message']}"
            print(line, flush=True)
    elif severity == "WARNING":
        warns = [a for a in alerts if a["level"] == "WARNING"]
        print(f"ALERT:WARNING: {len(warns)} warning(s) — check health-alerts.md",
              flush=True)


def any_emergency_or_critical(dashboard: Dict[str, Any]) -> bool:
    """Return True if any CRITICAL or EMERGENCY alert exists."""
    return any(
        a["level"] in ("CRITICAL", "EMERGENCY")
        for a in dashboard.get("alerts", [])
    )


# ─── CLI / Status ─────────────────────────────────────────────────────

def print_status_card(dashboard: Dict[str, Any]) -> None:
    """Print compact human-readable status card."""
    layers = dashboard.get("layers", {})
    score = dashboard.get("health_score", 100)
    label = dashboard.get("health_label", "HEALTHY")
    alerts = dashboard.get("alerts", [])
    max_lvl = _max_alert_level(alerts)

    INNER = 42

    def box_line(content: str) -> str:
        if len(content) > INNER - 2:
            content = content[:INNER - 2]
        return f"│ {content:<{INNER - 2}s}│"

    def header() -> str:
        t = " Trevor Health "
        side_len = (INNER - len(t)) // 2
        rem = INNER - side_len - len(t)
        return "┌" + "─" * side_len + t + "─" * rem + "┐"

    score_emoji = (
        "🔴" if score < 50 else
        "🟡" if score < 70 else
        "🟠" if score < 90 else "🟢"
    )

    def s_emoji(s: str) -> str:
        return {"ok": "✅", "degraded": "⚠️", "critical": "🔴",
                "error": "❌", "unknown": "❓"}.get(s, "❓")

    lines = [
        header(),
        box_line(f"Score:  {label} ({score}/100)  {score_emoji}"),
    ]

    # Gateway
    infra = layers.get("infrastructure", {})
    gw = "✅ Running" if infra.get("gateway") else "❌ DOWN"
    lines.append(box_line(f"Gateway:       {gw}"))

    # GitHub
    gh = layers.get("github_backup", {})
    if gh.get("backup_status") == "ok":
        ght = f"✅ Clean (pushed {gh.get('last_backup_age_hours', '?')}h)"
    else:
        ght = f"{s_emoji(gh.get('status', 'unknown'))} {gh.get('details', '?')[:24]}"
    lines.append(box_line(f"GitHub:        {ght}"))

    # Cron
    cron = layers.get("cron_health", {})
    failing = cron.get("failing", 0)
    enabled = cron.get("enabled", 0)
    ok_c = enabled - failing
    lines.append(box_line(f"Cron jobs:     {ok_c}/{enabled} ok ({failing} failing)"))

    # Brief
    pipe = layers.get("pipeline", {})
    brief = "✅ Delivered" if pipe.get("brief_today") else "❌ Missing"
    lines.append(box_line(f"Brief today:   {brief}"))

    # Episodic
    lm = layers.get("learning_memory", {})
    if lm.get("episodic_today"):
        ep = "✅ Current"
    elif lm.get("episodic_yesterday"):
        ep = "⚠️ Yesterday"
    else:
        ep = "❌ Stale"
    lines.append(box_line(f"Episodic log:  {ep}"))

    # Brain index
    if lm.get("brain_index_fresh"):
        idx = "✅ Fresh (<24h)"
    elif lm.get("brain_index_fresh") is False:
        idx = "❌ Old"
    else:
        idx = "❓ Unknown"
    lines.append(box_line(f"Brain index:   {idx}"))

    # DeepSeek
    cost = layers.get("cost_budget", {})
    bal = cost.get("balance", 0)
    runway = cost.get("runway_days", 0)
    ds = f"${bal:.2f} ({runway:.0f}d runway)" if runway else f"${bal:.2f}"
    lines.append(box_line(f"DeepSeek:      {ds}"))

    # Heartbeat
    hb = layers.get("heartbeat", {})
    hb_s = "✅ Complete" if hb.get("cycle_complete") else (
        f"⚠️ {hb.get('current_phase', '?')}"
    )
    lines.append(box_line(f"Heartbeat:     {hb_s}"))

    # Alerts
    warn_c = len([a for a in alerts if a["level"] == "WARNING"])
    crit_c = len([a for a in alerts if a["level"] in ("CRITICAL", "EMERGENCY")])
    if max_lvl == "EMERGENCY":
        al = f"🚨 {crit_c} EMERGENCY"
    elif max_lvl == "CRITICAL":
        al = f"🔴 {crit_c} CRITICAL"
    elif warn_c:
        al = f"⚠️  {warn_c} WARNING"
    else:
        al = "✅ No alerts"
    lines.append(box_line(f"Alerts:        {al}"))

    lines.append("└" + "─" * INNER + "┘")
    print("\n".join(lines))


# ─── Argument Parsing ─────────────────────────────────────────────────

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Trevor Unified Health Engine")
    parser.add_argument("--quick", action="store_true",
                        help="Quick check (layers 0-2 only, default)")
    parser.add_argument("--deep", action="store_true",
                        help="Full check (all layers)")
    parser.add_argument("--status", action="store_true",
                        help="Print status card after check")
    parser.add_argument("--watch", action="store_true",
                        help="One-shot with Telegram alert if CRITICAL")
    parser.add_argument("--check-github", action="store_true",
                        help="GitHub backup check only")
    parser.add_argument("--pipeline", action="store_true",
                        help="Include pipeline layers (3-5)")
    parser.add_argument("--cost", action="store_true",
                        help="Include cost layer (6)")
    return parser.parse_args(argv)


# ─── Main ─────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    _setup_logging()
    args = parse_args(argv)

    if args.check_github:
        dashboard: Dict[str, Any] = {
            "timestamp": _now_iso(), "health_score": 100,
            "health_label": "HEALTHY", "layers": {}, "alerts": [],
            "emergency": False,
        }
        check_github_backup(dashboard)
        gh = dashboard["layers"].get("github_backup", {})
        print(f"GitHub backup status: {gh.get('backup_status', 'unknown')}")
        print(f"  Uncommitted: {gh.get('uncommitted', '?')}")
        print(f"  Unpushed: {gh.get('unpushed', '?')}")
        print(f"  Last push: {gh.get('last_backup_age_hours', '?')}h ago")
        return 0

    quick = args.quick or not (args.deep or args.pipeline or args.cost)

    dashboard: Dict[str, Any] = {
        "timestamp": _now_iso(), "health_score": 100,
        "health_label": "HEALTHY", "layers": {}, "alerts": [],
        "emergency": False,
    }

    check_github_backup(dashboard)
    check_infrastructure(dashboard)
    check_cron_health(dashboard)

    if args.deep or args.pipeline or not quick:
        check_pipeline_completion(dashboard)
        check_learning_memory(dashboard)
        check_heartbeat_cycle(dashboard)

    if args.deep or args.cost or not quick:
        check_cost_budget(dashboard)

    compute_health_score(dashboard)
    dashboard["emergency"] = any_emergency_or_critical(dashboard)

    write_dashboard(dashboard)
    write_alerts(dashboard)
    escalate_if_needed(dashboard)

    if args.status:
        print_status_card(dashboard)

    LOG.info("Health check complete: score=%d label=%s alerts=%d",
             dashboard["health_score"], dashboard["health_label"],
             len(dashboard["alerts"]))

    return 1 if dashboard["emergency"] else 0


if __name__ == "__main__":
    sys.exit(main())
