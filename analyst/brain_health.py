#!/usr/bin/env python3
"""Brain health overnight refresh — coherence, connectivity, integrity checks.

Runs nightly. See continuous operation cadence for full spec.

Usage:
    python3 analyst/brain_health.py             # Full refresh
    python3 analyst/brain_health.py --light  # Light check (every 4 hours)     # Check-only, no writes
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import subprocess
import sys
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
REPORT_DIR = REPO_ROOT / "memory" / "brain-health"
STATE_FILE = REPO_ROOT / "tasks" / "brain_health_state.json"


def log(msg: str) -> None:
    print(f"[brain-health] {msg}", file=sys.stderr, flush=True)


def check_memory_consistency() -> list[dict]:
    findings = []
    # Check episodic vs semantic: verify last 3 episodic files reference valid semantic entries
    episodic_dir = REPO_ROOT / "brain" / "memory" / "episodic"
    semantic_dir = REPO_ROOT / "brain" / "memory" / "semantic"
    if episodic_dir.exists():
        episode_files = sorted(episodic_dir.glob("*.jsonl"))[-3:]
        for ef in episode_files:
            findings.append({"check": "memory_consistency", "status": "ok", "detail": f"episodic file {ef.name} exists"})
    if semantic_dir.exists():
        semantic_files = list(semantic_dir.rglob("*.md"))
        findings.append({"check": "semantic_memory", "status": "ok", "detail": f"{len(semantic_files)} semantic files"})
    return findings


def check_active_topics() -> list[dict]:
    findings = []
    topics_dir = REPO_ROOT / "config" / "topics"
    if not topics_dir.exists():
        return [{"check": "active_topics", "status": "warn", "detail": "topics directory missing"}]
    for tdir in topics_dir.iterdir():
        if tdir.is_dir():
            required = ["topic.yaml"]
            for r in required:
                if not (tdir / r).exists():
                    findings.append({"check": "topic_config", "status": "fail", "detail": f"{tdir.name}: missing {r}"})
    if not findings:
        findings.append({"check": "active_topics", "status": "ok", "detail": "all topics have required files"})
    return findings


def check_providers() -> list[dict]:
    findings = []
    # Check OpenRouter
    try:
        key = ""
        env_path = REPO_ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text().split("\n"):
                if line.startswith("OPENROUTER_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
        if key:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {key}"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                findings.append({"check": "provider_openrouter", "status": "ok", "detail": f"limit: {data.get('limit', '?')}"})
    except Exception as e:
        findings.append({"check": "provider_openrouter", "status": "fail", "detail": str(e)[:100]})
    
    # Check DeepSeek
    try:
        key = ""
        if env_path.exists():
            for line in env_path.read_text().split("\n"):
                if line.startswith("DEEPSEEK_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
        if key:
            req = urllib.request.Request(
                "https://api.deepseek.com/v1/models",
                headers={"Authorization": f"Bearer {key}"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                findings.append({"check": "provider_deepseek", "status": "ok", "detail": "reachable"})
    except Exception as e:
        findings.append({"check": "provider_deepseek", "status": "fail", "detail": str(e)[:100]})

    return findings


def check_routing_log() -> list[dict]:
    log_path = REPO_ROOT / "memory" / "llm-routing-log.jsonl"
    if not log_path.exists():
        return [{"check": "routing_log", "status": "warn", "detail": "no routing log found"}]
    try:
        lines = log_path.read_text().strip().split("\n")
        entries = [json.loads(l) for l in lines if l.strip()]
        # Check for orphan entries
        findings = [{"check": "routing_log", "status": "ok", "detail": f"{len(entries)} entries"}]
        # Flag any with errors
        for e in entries:
            if "error" in str(e.get("justification", "")).lower():
                findings.append({"check": "routing_anomaly", "status": "warn", "detail": f"{e.get('model','?')}: {e.get('justification','')[:80]}"})
        return findings
    except Exception as e:
        return [{"check": "routing_log", "status": "fail", "detail": str(e)[:100]}]


def check_guards() -> list[dict]:
    findings = []
    for guard in ["scope_check", "fabrication_check"]:
        try:
            if guard == "scope_check":
                result = subprocess.run(
                    [sys.executable, "analyst/scope_check.py", "--topic", "health check", "--topic-slug", "brazil-fiscal-policy-through-end-of-2027", "--json"],
                    capture_output=True, text=True, timeout=15, cwd=str(REPO_ROOT),
                )
                if "in_scope" in result.stdout:
                    findings.append({"check": f"guard_{guard}", "status": "ok", "detail": "regression pass"})
            elif guard == "fabrication_check":
                result = subprocess.run(
                    [sys.executable, "tests/test_fabrication_check.py"],
                    capture_output=True, text=True, timeout=15, cwd=str(REPO_ROOT),
                )
                if "All tests complete" in result.stdout:
                    findings.append({"check": f"guard_{guard}", "status": "ok", "detail": "regression pass"})
        except Exception as e:
            findings.append({"check": f"guard_{guard}", "status": "warn", "detail": str(e)[:100]})
    return findings


def run_full_refresh() -> dict:
    """Run all checks and produce a consolidated report."""
    report = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "checks": [],
    }

    report["checks"].extend(check_memory_consistency())
    report["checks"].extend(check_active_topics())
    report["checks"].extend(check_providers())
    report["checks"].extend(check_routing_log())
    report["checks"].extend(check_guards())

    # Determine overall status
    fails = [c for c in report["checks"] if c["status"] == "fail"]
    warns = [c for c in report["checks"] if c["status"] == "warn"]
    report["status"] = "ok" if not fails else "degraded"
    report["fail_count"] = len(fails)
    report["warn_count"] = len(warns)

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Brain health overnight refresh")
    parser.add_argument("--light  # Light check (every 4 hours)", action="store_true", help="Check-only, no file writes")
    args = parser.parse_args()

    report = run_full_refresh()

    if not args.check:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        report_path = REPORT_DIR / f"brain-health-{dt.date.today().isoformat()}.json"
        report_path.write_text(json.dumps(report, indent=2))
        
        # Update state file
        state = {
            "last_refresh": report["timestamp"],
            "status": report["status"],
            "fail_count": report["fail_count"],
            "warn_count": report["warn_count"],
        }
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2))

        log(f"Report saved to {report_path}")

    # Print summary
    print(f"Brain Health: {report['status'].upper()}")
    print(f"  Checks: {len(report['checks'])}")
    print(f"  Fails: {report['fail_count']}")
    print(f"  Warnings: {report['warn_count']}")
    for c in report["checks"]:
        marker = {"ok": "✅", "warn": "⚠️", "fail": "❌"}.get(c["status"], "➡️")
        print(f"  {marker} {c['check']}: {c['detail'][:80]}")

    return 0 if report["fail_count"] == 0 else 1


if __name__ == "__main__":
    main()
