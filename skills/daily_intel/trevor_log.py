#!/usr/bin/env python3
"""
trevor_log.py — Structured logging for Trevor DailyIntelAgent.

Provides:
  - Structured JSON log entries
  - Heartbeat telemetry
  - Task tracing with timing
  - Configurable log levels
  - Both file and stderr output

Usage:
    from trevor_log import get_logger
    log = get_logger("generate_assessments")
    log.info("Starting assessment generation", theatres=7, model="deepseek-v4-pro")
    log.warning("Chroma index miss, falling back to FTS5")
    log.error("PDF generation failed", exc_info=True)
    log.heartbeat("build_pdf", "in_progress", progress="75%")
    log.trace("assess", duration=45.2, tokens_in=12000, tokens_out=3500)
"""
from __future__ import annotations

import datetime
import json
import os
import sys
import time
import traceback
from pathlib import Path


_LOG_DIR = Path(os.environ.get("TREVOR_EXPORTS", Path.home() / ".openclaw" / "workspace" / "exports")) / "logs"
_LOG_FILE = _LOG_DIR / "trevor.log"
_METRICS_FILE = _LOG_DIR / "trevor-metrics.jsonl"

_LOG_DIR.mkdir(parents=True, exist_ok=True)


class Logger:
    """Structured logger with task tracing and heartbeat telemetry."""

    def __init__(self, name: str):
        self.name = name
        self._task_stack: list[dict] = []

    def _write(self, level: str, message: str, **kwargs):
        entry = {
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": level,
            "logger": self.name,
            "message": message,
            **kwargs,
        }
        # Always write to log file
        try:
            with open(_LOG_FILE, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError:
            pass
        # Also print to stderr with a readable format
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        extra = " ".join(f"{k}={v}" for k, v in kwargs.items() if v is not None)
        extra_str = f" [{extra}]" if extra else ""
        print(f"{ts} | {level:7s} | {self.name} | {message}{extra_str}", file=sys.stderr, flush=True)

    def info(self, msg: str, **kwargs):
        self._write("INFO", msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self._write("WARNING", msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self._write("ERROR", msg, **kwargs)

    def debug(self, msg: str, **kwargs):
        self._write("DEBUG", msg, **kwargs)

    def heartbeat(self, step: str, status: str, progress: str | None = None):
        """Telemetry heartbeat for long-running tasks."""
        self._write("HEARTBEAT", f"step={step} status={status}",
                     step=step, status=status, progress=progress, pid=os.getpid())

    def trace(self, task: str, duration: float, **kwargs):
        """Task tracing with timing."""
        self._write("TRACE", f"task={task} duration={duration:.1f}s",
                     task=task, duration_seconds=round(duration, 2), **kwargs)
        # Also append to metrics file
        try:
            with open(_METRICS_FILE, "a") as f:
                f.write(json.dumps({
                    "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "task": task,
                    "duration_seconds": round(duration, 2),
                    **kwargs,
                }) + "\n")
        except OSError:
            pass

    def start_task(self, name: str) -> "TaskSpan":
        """Context manager for timing a task."""
        return TaskSpan(self, name)


class TaskSpan:
    """Timed task span — use with 'with'."""

    def __init__(self, logger: Logger, name: str):
        self.logger = logger
        self.name = name
        self.start = 0.0

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start
        if exc_type:
            self.logger.trace(self.name, duration=duration, error=str(exc_val)[:200])
        else:
            self.logger.trace(self.name, duration=duration)


def get_logger(name: str) -> Logger:
    """Get a named logger instance."""
    return Logger(name)


class HealthReport:
    """Runtime health report — call at startup to verify system state."""

    @staticmethod
    def run(logger: Logger | None = None) -> dict:
        """Run a full health diagnostic and return results."""
        if logger is None:
            logger = get_logger("health")
        
        results = []
        status = "ok"
        
        # 1. Check workspace
        from trevor_config import WORKSPACE, EXPORTS_DIR, FONTS_DIR, DEEPSEEK_API_KEY
        checks = [
            ("workspace", WORKSPACE.exists(), str(WORKSPACE)),
            ("exports", EXPORTS_DIR.exists(), str(EXPORTS_DIR)),
            ("fonts", FONTS_DIR.exists(), str(FONTS_DIR)),
            ("deepseek_key", bool(DEEPSEEK_API_KEY), "DEEPSEEK_API_KEY set"),
        ]
        
        for name, ok, detail in checks:
            entry = {"check": name, "status": "ok" if ok else "fail", "detail": detail}
            results.append(entry)
            if not ok:
                status = "degraded"
                logger.warning(f"Health check failed: {name}", detail=detail)
            else:
                logger.info(f"Health check passed: {name}", detail=detail)
        
        # 2. Check dependencies
        deps = {}
        for dep_name, import_name in [
            ("reportlab", "reportlab"),
            ("PIL", "PIL"),
            ("requests", "requests"),
            ("matplotlib", "matplotlib"),
        ]:
            try:
                __import__(import_name)
                deps[dep_name] = True
            except ImportError:
                deps[dep_name] = False
                status = "degraded"
                logger.warning(f"Dependency missing: {dep_name}")
        
        report = {
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": status,
            "results": results,
            "dependencies": deps,
        }
        
        # Write health report
        health_path = _LOG_DIR / "health-report.json"
        try:
            health_path.write_text(json.dumps(report, indent=2))
        except OSError:
            pass
        
        logger.info(f"Health report: {status}", checks=len(results), deps_ok=sum(1 for v in deps.values() if v))
        return report
