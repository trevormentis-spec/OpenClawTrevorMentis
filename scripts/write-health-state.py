#!/usr/bin/env python3
"""Write runtime health state JSON from env vars. Used by runtime-report.sh."""
import os, json

def int_val(key, default=-1):
    """Get integer from env var, handling multi-line values."""
    val = os.environ.get(key, "")
    if not val.strip():
        return default
    try:
        return int(val.strip().split("\n")[-1])
    except (ValueError, IndexError):
        return default

data = {
    "report_type": "health_summary",
    "timestamp": os.environ.get("NOW", "?"),
    "disk": {
        "usage_pct": int_val("DISK_PCT", -1),
        "used": os.environ.get("DISK_USED", "?"),
        "total": os.environ.get("DISK_TOTAL", "?"),
    },
    "logs": {
        "total_mb": int_val("TOTAL_LOG_SIZE", -1),
        "ws_mb": int_val("KALSHI_WS_SIZE", -1),
        "monitor_mb": int_val("MONITOR_LOG_SIZE", -1),
    },
    "processes": {
        "monitor": os.environ.get("MONITOR_RUNNING", "?"),
        "ws_listener": os.environ.get("WS_RUNNING", "?"),
        "heavy_jobs": int_val("HEAVY_JOBS", -1),
    },
    "storage": {
        "exports_mb": int_val("EXPORTS_SIZE", -1),
        "tmp_mb": int_val("TMP_SIZE", -1),
    },
    "failures_24h": int_val("RECENT_FAILURES", -1),
    "degraded": os.environ.get("DEGRADED", "?"),
    "risk": os.environ.get("RISK", "?"),
    "bottlenecks": os.environ.get("BOTTLENECKS", "?"),
}

output_path = os.environ.get("HEALTH_STATE", 
    "/home/ubuntu/.openclaw/workspace/tasks/runtime-state.json")
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w") as f:
    json.dump(data, f, indent=2)
