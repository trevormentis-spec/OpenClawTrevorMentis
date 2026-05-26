#!/usr/bin/env python3
"""
Concurrency Lock System for Trevor Runtime

Prevents:
  - Overlapping orchestrators
  - Multiple heavy cognition jobs
  - Cron pileups
  - Runaway monitor loops

Usage:
  from runtime_lock import RuntimeLock

  # Heavy task (blocks duplicates)
  with RuntimeLock("orchestrate", timeout=3600) as lock:
      if lock.acquired:
          # do work
      else:
          # another instance is running

  # Noncritical task (queues if busy)
  with RuntimeLock("image_gen", timeout=300) as lock:
      if lock.acquired:
          # do work

  # Check whether a specific task is running
  is_busy = RuntimeLock.is_running("orchestrate")
"""

import os
import json
import time
import fcntl
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict, Any

logger = logging.getLogger("runtime-lock")
logger.setLevel(logging.WARNING)

LOCK_DIR = Path(os.environ.get("WORKSPACE", "/home/ubuntu/.openclaw/workspace")) / "tasks"
LOCK_DIR.mkdir(parents=True, exist_ok=True)


class RuntimeLock:
    """File-based mutex with timeout and orphan detection."""

    def __init__(self, name: str, timeout: int = 3600):
        self.name = name.replace(" ", "_").replace("/", "_")
        self.timeout = timeout
        self.lock_path = LOCK_DIR / f"lock-{self.name}"
        self._fd = None
        self.acquired = False

    def __enter__(self):
        try:
            self._fd = os.open(self.lock_path, os.O_CREAT | os.O_RDWR)
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.acquired = True

            # Write metadata
            meta = {
                "pid": os.getpid(),
                "name": self.name,
                "acquired_at": time.time(),
                "timeout": self.timeout,
            }
            os.write(self._fd, json.dumps(meta).encode())

            # Timeout enforced by file-based stale check

        except (IOError, BlockingIOError):
            # Lock held by another process
            self.acquired = False
            if self._fd:
                os.close(self._fd)
                self._fd = None

            # Check if the lock is orphaned (stale PID)
            if self._is_orphaned():
                logger.warning(f"Orphaned lock '{self.name}' — stealing")
                os.remove(self.lock_path)
                return self.__enter__()

        return self

    def __exit__(self, *args):
        if self._fd:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
            except Exception:
                pass
            try:
                os.close(self._fd)
            except Exception:
                pass
            self._fd = None
        if self.lock_path.exists():
            try:
                self.lock_path.unlink()
            except Exception:
                pass

    def _is_orphaned(self) -> bool:
        """Check if the process holding this lock still exists."""
        try:
            meta = json.loads(self.lock_path.read_text())
            pid = meta.get("pid", 0)
            acquired = meta.get("acquired_at", 0)
            timeout = meta.get("timeout", 3600)

            # Check if PID exists
            try:
                os.kill(pid, 0)
                exists = True
            except OSError:
                exists = False

            # Check if lock is expired
            expired = (time.time() - acquired) > timeout

            if not exists:
                return True
            if expired:
                return True

            return False
        except Exception:
            return False

    @staticmethod
    def is_running(name: str) -> bool:
        """Check if a task is currently running (lock held)."""
        lock_path = LOCK_DIR / f"lock-{name}"
        if not lock_path.exists():
            return False
        try:
            meta = json.loads(lock_path.read_text())
            pid = meta.get("pid", 0)
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                # Stale lock
                lock_path.unlink(missing_ok=True)
                return False
        except Exception:
            return False

    @staticmethod
    def list_active() -> Dict[str, Any]:
        """List all active runtime locks."""
        active = {}
        for lock_file in LOCK_DIR.glob("lock-*"):
            try:
                meta = json.loads(lock_file.read_text())
                pid = meta.get("pid", 0)
                try:
                    os.kill(pid, 0)
                    active[meta["name"]] = meta
                except OSError:
                    lock_file.unlink(missing_ok=True)
            except Exception:
                pass
        return active

    @staticmethod
    def clear_all():
        """Release all locks (dangerous: only use during startup)."""
        for lock_file in LOCK_DIR.glob("lock-*"):
            try:
                lock_file.unlink()
            except Exception:
                pass


# ── Timeout Wrapper ─────────────────────────────────────────────────

class TimeoutError(Exception):
    """Raised when an operation exceeds its hard timeout."""


def with_timeout(func, timeout: int = 300):
    """
    Execute a function with a hard timeout using SIGALRM.
    Returns (result, time_taken) or raises TimeoutError.
    """
    class TimeoutHandler:
        def __init__(self):
            self.timed_out = False
        def handler(self, signum, frame):
            self.timed_out = True
            raise TimeoutError(f"Operation timed out after {timeout}s")

    handler = TimeoutHandler()
    old_handler = signal.signal(signal.SIGALRM, handler.handler)
    signal.alarm(timeout)

    start = time.time()
    try:
        result = func()
        elapsed = time.time() - start
        return result, round(elapsed, 2)
    except TimeoutError:
        raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


# ── Service Manager ─────────────────────────────────────────────────

class RuntimeServices:
    """
    Centralized service lifecycle management for background processes.
    Ensures singleton processes with auto-restart.
    """

    SERVICE_DIR = LOCK_DIR

    @staticmethod
    def is_service_running(name: str) -> Optional[int]:
        """Returns PID if service running, None otherwise."""
        import subprocess
        result = subprocess.run(
            ["pgrep", "-f", name],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split()
            return int(pids[0])
        return None

    @staticmethod
    def start_service(name: str, cmd: list, timeout: int = 30) -> bool:
        """Start a background service if not already running."""
        existing = RuntimeServices.is_service_running(name)
        if existing:
            logger.debug(f"Service '{name}' already running (PID {existing})")
            return True

        import subprocess
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,  # Detach from parent process group
            )
            # Brief check
            time.sleep(1)
            if proc.poll() is None:
                logger.info(f"Started service '{name}' (PID {proc.pid})")
                return True
            else:
                logger.error(f"Service '{name}' exited immediately (code {proc.returncode})")
                return False
        except Exception as e:
            logger.error(f"Failed to start '{name}': {e}")
            return False


# ── CLI ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if "--list" in sys.argv:
        locks = RuntimeLock.list_active()
        if locks:
            print("Active locks:")
            for name, meta in locks.items():
                age = time.time() - meta["acquired_at"]
                print(f"  {name}: PID {meta['pid']}, age {age:.0f}s")
        else:
            print("No active locks")
    elif "--clear" in sys.argv:
        RuntimeLock.clear_all()
        print("All locks cleared")
    else:
        print("Usage: python3 runtime_lock.py [--list|--clear]")
