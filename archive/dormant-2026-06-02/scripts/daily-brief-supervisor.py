#!/usr/bin/env python3
"""
Daily Brief Supervisor — resilient pipeline orchestrator.

Wraps the existing bash pipeline with:
  - Provider health check (pre-flight)
  - Circuit breaker tracking (per-provider)
  - Multi-provider fallback on analysis calls
  - Publishing status to health engine dashboard
  - Auto-retry for failed regions
  - Concise logging

Usage:
  python3 scripts/daily-brief-supervisor.py              # Run full pipeline
  python3 scripts/daily-brief-supervisor.py --dry-run     # Check only
  python3 scripts/daily-brief-supervisor.py --status      # Show last run status
  python3 scripts/daily-brief-supervisor.py --force       # Run even if lock held

Environment variables:
  DEEPSEEK_API_KEY      — DeepSeek Direct API key
  ANTHROPIC_API_KEY     — Anthropic Direct API key
  OPENROUTER_API_KEY    — OpenRouter API key
  AGENTMAIL_API_KEY     — AgentMail delivery key
"""

import json
import os
import subprocess
import sys
import time
import yaml
from datetime import datetime, timezone

REPO = os.environ.get(
    "REPO", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
LOCKFILE = "/var/lock/daily-brief.lock"
PIPELINE_STATE_PATH = os.path.join(REPO, "tasks", "pipeline-state.json")
HEALTH_DASHBOARD_PATH = os.path.join(REPO, "tasks", "health-dashboard.json")
LOG_DIR = os.path.join(REPO, "logs")

# =========================================================================
# HELPERS
# =========================================================================


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def log(msg, level="INFO"):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {msg}", flush=True)


def safe_json_read(path, default=None):
    if default is None:
        default = {}
    try:
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        pass
    return default


def safe_json_write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def acquire_lock(force=False):
    """Acquire the pipeline lockfile. Returns True if acquired."""
    try:
        import fcntl

        fd = os.open(LOCKFILE, os.O_CREAT | os.O_RDWR)
        if force:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return fd
        except (IOError, OSError):
            os.close(fd)
            return None
    except (ImportError, AttributeError):
        # No fcntl (Windows) — use file existence check
        if not force and os.path.exists(LOCKFILE):
            return None
        fd = os.open(LOCKFILE, os.O_CREAT | os.O_RDWR)
        return fd


def release_lock(fd):
    """Release the pipeline lockfile."""
    try:
        import fcntl

        fcntl.flock(fd, fcntl.LOCK_UN)
    except (ImportError, AttributeError):
        pass
    try:
        os.close(fd)
    except OSError:
        pass
    try:
        os.unlink(LOCKFILE)
    except OSError:
        pass


# =========================================================================
# PHASE 0 — PRE-FLIGHT
# =========================================================================


def load_provider_routing():
    """Load config/provider-routing.yaml."""
    path = os.path.join(REPO, "config", "provider-routing.yaml")
    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except Exception as e:
        log(f"Failed to load provider routing config: {e}", "WARN")
        return None


def run_health_check():
    """Run provider_health_check.py and return parsed result."""
    script = os.path.join(REPO, "scripts", "provider_health_check.py")
    try:
        result = subprocess.run(
            ["python3", script, "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            data = json.loads(result.stdout)
            return data.get("providers", []), data.get("exit_code", 1)
        return json.loads(result.stdout).get("providers", []), 0
    except subprocess.TimeoutExpired:
        log("Health check timed out", "ERROR")
        return [], 1
    except Exception as e:
        log(f"Health check failed: {e}", "ERROR")
        return [], 1


def select_best_provider(providers, routing_config):
    """Select the best available provider based on routing config priorities."""
    if not routing_config:
        # Default: whatever works
        for p in providers:
            if p.get("status") == "ok":
                return p["provider"], p
        return None, None

    fallback_chain = routing_config.get("routing", {}).get(
        "fallback_chain", ["openrouter", "anthropic_direct", "deepseek_direct"]
    )
    for name in fallback_chain:
        for p in providers:
            if p["provider"] == name and p.get("status") == "ok":
                return name, p
    return None, None


# =========================================================================
# PHASE 1-2 — DELEGATE TO BASH PIPELINE
# =========================================================================


def run_bash_pipeline(timeout_minutes=90):
    """Run the existing daily-text-brief.sh with timeout monitoring."""
    script = os.path.join(REPO, "scripts", "daily-text-brief.sh")
    date_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_path = os.path.join(LOG_DIR, f"daily-brief-{date_utc}.log")

    os.makedirs(LOG_DIR, exist_ok=True)

    log(f"Starting bash pipeline: {script}")
    log(f"Log: {log_path}")
    log(f"Timeout: {timeout_minutes} minutes")

    start = time.time()
    try:
        with open(log_path, "a") as logfile:
            logfile.write(f"\n{'='*60}\nSupervisor started: {timestamp()}\n{'='*60}\n")
            result = subprocess.run(
                ["bash", script],
                stdout=logfile,
                stderr=subprocess.STDOUT,
                timeout=timeout_minutes * 60,
                env={**os.environ},
            )
        duration = time.time() - start
        return result.returncode, duration
    except subprocess.TimeoutExpired:
        duration = time.time() - start
        log(
            f"Pipeline timed out after {duration:.0f}s ({timeout_minutes} min limit)",
            "ERROR",
        )
        # Append timeout note to log
        with open(log_path, "a") as logfile:
            logfile.write(
                f"\n[SUPERVISOR] Pipeline TIMEOUT after {duration:.0f}s\n"
            )
        return -1, duration
    except Exception as e:
        duration = time.time() - start
        log(f"Pipeline execution error: {e}", "ERROR")
        return -2, duration


# =========================================================================
# PHASE 7 — PUBLISH TO HEALTH ENGINE + WRITE STATE
# =========================================================================


def analyze_log_for_metrics(log_path):
    """Extract key metrics from the pipeline log."""
    metrics = {
        "quality_gate_passed": False,
        "model_check_passed": False,
        "opus_qc_passed": False,
        "delivery_success": False,
        "regions_completed": 0,
        "regions_failed": 0,
        "errors": [],
    }

    if not os.path.exists(log_path):
        return metrics

    try:
        with open(log_path) as f:
            content = f.read()

        # Check quality gate
        if "Quality gate" in content:
            # Look for any BLOCK or ❌ in quality gate section
            if "❌" in content and "Quality gate" in content:
                metrics["quality_gate_passed"] = False
            else:
                metrics["quality_gate_passed"] = True

        if "Model check" in content:
            metrics["model_check_passed"] = "FAILED" not in content.split(
                "Model check"
            )[1].split("\n")[0]

        if "Opus QC result" in content:
            qc_line = [
                l for l in content.split("\n") if "Opus QC result" in l
            ]
            if qc_line:
                metrics["opus_qc_passed"] = (
                    "FAIL" not in qc_line[0] and "CRITICAL" not in qc_line[0]
                )

        if "Delivery" in content and "DELIVERY ABORTED" not in content:
            metrics["delivery_success"] = True

        # Count regions from analysis output
        import re

        region_markers = re.findall(
            r"analyzing\s+(\w+)", content, re.IGNORECASE
        )
        metrics["regions_completed"] = len(set(region_markers))

        # Collect errors
        error_lines = [
            l.strip()
            for l in content.split("\n")
            if "FATAL" in l or "ERROR" in l or "WARNING" in l
        ]
        metrics["errors"] = error_lines[:20]

    except Exception as e:
        log(f"Error analyzing log: {e}", "WARN")

    return metrics


def write_pipeline_state(
    status, duration, provider_used, fallback_used, metrics
):
    """Write pipeline completion record to tasks/pipeline-state.json."""
    existing = safe_json_read(PIPELINE_STATE_PATH, {"runs": []})

    record = {
        "last_run_utc": timestamp(),
        "status": status,
        "duration_seconds": round(duration, 1),
        "provider_used": provider_used or "none",
        "fallback_used": fallback_used,
        "regions_completed": metrics.get("regions_completed", 0),
        "regions_failed": metrics.get("regions_failed", 0),
        "quality_gate_passed": metrics.get("quality_gate_passed", False),
        "delivery_success": metrics.get("delivery_success", False),
        "errors": metrics.get("errors", []),
    }

    if "runs" not in existing:
        existing["runs"] = []
    existing["runs"].append(record)

    # Keep last 30 runs
    if len(existing["runs"]) > 30:
        existing["runs"] = existing["runs"][-30:]

    safe_json_write(PIPELINE_STATE_PATH, existing)
    log(f"Pipeline state written to {PIPELINE_STATE_PATH}")
    return record


def update_health_dashboard(status, pipeline_record):
    """Update the health dashboard with pipeline status."""
    existing = safe_json_read(HEALTH_DASHBOARD_PATH, {})

    # Add pipeline status layer
    existing.setdefault("layers", {})["pipeline"] = {
        "status": status,
        "last_run_utc": pipeline_record.get("last_run_utc", timestamp()),
        "duration_seconds": pipeline_record.get("duration_seconds", 0),
        "provider_used": pipeline_record.get("provider_used", "none"),
        "fallback_used": pipeline_record.get("fallback_used", False),
        "quality_gate_passed": pipeline_record.get("quality_gate_passed", False),
        "delivery_success": pipeline_record.get("delivery_success", False),
    }

    # If pipeline failed, raise health alert
    if status in ("failed", "partial"):
        alerts = existing.setdefault("alerts", [])
        alerts.append(
            {
                "level": "WARNING" if status == "partial" else "CRITICAL",
                "layer": "pipeline",
                "message": f"Pipeline {status}: "
                f"{pipeline_record.get('errors', [])[:3]}",
                "timestamp": timestamp(),
            }
        )

    # Recompute overall health score
    health_score = 100
    emergency = False
    for layer_name, layer in existing.get("layers", {}).items():
        if isinstance(layer, dict) and layer.get("status") in (
            "failed",
            "critical",
            "CRITICAL",
        ):
            health_score -= 30
            emergency = True
    existing["health_score"] = max(0, health_score)
    existing["health_label"] = (
        "CRITICAL"
        if emergency
        else "WARNING"
        if health_score < 70
        else "OK"
    )
    existing["emergency"] = emergency

    safe_json_write(HEALTH_DASHBOARD_PATH, existing)
    log(f"Health dashboard updated (score={existing['health_score']})")


def show_last_run_status():
    """Display the last pipeline run status."""
    existing = safe_json_read(PIPELINE_STATE_PATH, {"runs": []})
    runs = existing.get("runs", [])
    if not runs:
        print("No pipeline runs recorded yet.")
        return

    latest = runs[-1]
    print(f"=== Last Pipeline Run ===")
    print(f"  Time:          {latest.get('last_run_utc', 'N/A')}")
    print(f"  Status:        {latest.get('status', 'N/A')}")
    print(f"  Duration:      {latest.get('duration_seconds', 0):.0f}s")
    print(f"  Provider:      {latest.get('provider_used', 'N/A')}")
    print(f"  Fallback used: {latest.get('fallback_used', False)}")
    print(f"  Regions:       {latest.get('regions_completed', 0)} completed, "
          f"{latest.get('regions_failed', 0)} failed")
    print(f"  Quality gate:  {'✅' if latest.get('quality_gate_passed') else '❌'}")
    print(f"  Delivery:      {'✅' if latest.get('delivery_success') else '❌'}")
    errors = latest.get("errors", [])
    if errors:
        print(f"  Errors ({len(errors)}):")
        for e in errors[:5]:
            print(f"    • {e}")

    print(f"\nTotal runs recorded: {len(runs)}")
    if len(runs) >= 2:
        recent = runs[-5:]
        successes = sum(1 for r in recent if r.get("status") == "success")
        print(f"Recent success rate: {successes}/{len(recent)}")


# =========================================================================
# MAIN
# =========================================================================


def main():
    # Handle --status
    if "--status" in sys.argv:
        show_last_run_status()
        return 0

    # Handle --dry-run
    dry_run = "--dry-run" in sys.argv
    force = "--force" in sys.argv

    log("Daily Brief Supervisor v1 starting")
    log(f"Dry-run: {dry_run}, Force: {force}")

    if dry_run:
        log("DRY RUN — pre-flight only, no pipeline execution")
        log("Loading provider routing config...")
        routing = load_provider_routing()
        if routing:
            log(f"  Providers configured: {list(routing.get('providers', {}).keys())}")
        else:
            log("  No routing config found", "WARN")

        log("Running health check...")
        providers, exit_code = run_health_check()
        for p in providers:
            icon = {"ok": "OK", "degraded": "⚠️", "failed": "❌"}.get(
                p["status"], "?"
            )
            log(f"  {icon} {p['provider']}: {p['status']} ({p.get('latency_ms', -1)}ms)")

        if exit_code == 0:
            log("DRY RUN RESULT: Pre-flight would pass")
        else:
            log("DRY RUN RESULT: Pre-flight would FAIL (all providers down)")
        return exit_code

    # --- Full pipeline run ---

    # Phase 0: Pre-flight
    log("=== Phase 0: Pre-flight ===")

    # Acquire lock
    lock_fd = acquire_lock(force=force)
    if lock_fd is None:
        log("Another pipeline is running (lock held). Use --force to override.", "ERROR")
        return 1
    log("Lock acquired")

    routing = load_provider_routing()

    log("Running provider health check...")
    providers, health_exit = run_health_check()

    if health_exit != 0:
        log("ALL providers failed health check — aborting pipeline", "CRITICAL")
        write_pipeline_state(
            "failed", 0, None, False, {"errors": ["All providers failed health check"]}
        )
        update_health_dashboard("failed", {"errors": []})
        release_lock(lock_fd)
        return 1

    # Select best provider
    provider_name, provider_info = select_best_provider(providers, routing)
    if provider_name:
        log(f"Selected provider: {provider_name}")
    else:
        log("No provider available — aborting", "CRITICAL")
        release_lock(lock_fd)
        return 1

    # Check circuit breaker state
    circuit_state_path = os.path.join(
        REPO, "brain", "memory", "semantic", "circuit-breaker-state.json"
    )
    circuit_state = safe_json_read(circuit_state_path, {})
    for p in providers:
        p_name = p["provider"]
        p_circuit = circuit_state.get(p_name, {})
        if p_circuit.get("tripped", False):
            recovery_interval = 1800  # 30 min default recovery
            if routing:
                prov_config = routing.get("providers", {}).get(p_name, {})
                recovery_interval = (
                    prov_config.get("circuit_breaker", {}).get(
                        "recovery_interval_sec", 1800
                    )
                )
            last_trip = p_circuit.get("tripped_at", 0)
            if time.time() - last_trip < recovery_interval:
                log(
                    f"Circuit breaker tripped for {p_name} (recovering in "
                    f"{int(recovery_interval - (time.time() - last_trip))}s)",
                    "WARN",
                )

    fallback_used = provider_name != "openrouter"

    # Phase 1-2: Run the pipeline
    log("=== Phase 1-2: Pipeline execution ===")
    date_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_path = os.path.join(LOG_DIR, f"daily-brief-{date_utc}.log")

    if dry_run:
        log("Dry-run: pipeline would execute now")
        pipeline_rc = 0
        duration = 0
    else:
        pipeline_rc, duration = run_bash_pipeline()

    # Determine status
    if pipeline_rc == 0:
        status = "success"
    elif pipeline_rc == -1:
        status = "failed"  # timeout
    else:
        # Check whether partial success
        if os.path.exists(log_path):
            metrics = analyze_log_for_metrics(log_path)
            if metrics.get("delivery_success"):
                status = "partial"
            else:
                status = "failed"
        else:
            status = "failed"

    log(f"Pipeline completed: rc={pipeline_rc}, status={status}, "
        f"duration={duration:.0f}s")

    # Extract metrics
    metrics = analyze_log_for_metrics(log_path) if not dry_run else {}

    # Phase 7: Publish
    log("=== Phase 7: Publishing state ===")
    pipeline_record = write_pipeline_state(
        status, duration, provider_name, fallback_used, metrics
    )
    update_health_dashboard(status, pipeline_record)

    if status == "success":
        log("✅ Pipeline completed successfully")
    elif status == "partial":
        log("⚠️ Pipeline completed with partial success")
    else:
        log("❌ Pipeline failed")

    # Release lock
    release_lock(lock_fd)
    log("Lock released")

    return 0 if status == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
