# Health Engine — Deploy Guide

## Overview

The health engine is a unified health aggregation system for Trevor. It reads
from existing state files across the system and produces two outputs:

- `tasks/health-dashboard.json` — machine-readable health state
- `tasks/health-alerts.md` — human-readable alert log

## Files

| File | Purpose |
|------|---------|
| `scripts/health_engine.py` | Main health engine — 7 layers of checks |
| `scripts/health_status_card.py` | Reads dashboard JSON, prints compact terminal card |

## Cron Registration

Register two cron jobs in OpenClaw's cron system at `/home/ubuntu/.openclaw/cron/jobs.json`:

### 1. Quick check — every 15 minutes

Checks layers 0–2 (GitHub backup, infrastructure, cron health):

```
{
  "id": "health-engine-quick",
  "agentId": "main",
  "sessionKey": "agent:main:main",
  "name": "Trevor health engine — quick check",
  "description": "Every-15-min health check (layers 0-2)",
  "enabled": true,
  "schedule": {
    "kind": "every",
    "everyMs": 900000,
    "anchorMs": <current epoch ms>
  },
  "sessionTarget": "session:agent:main:main",
  "wakeMode": "now",
  "payload": {
    "kind": "agentTurn",
    "message": "REPLY IN ENGLISH ONLY. Run: cd /home/ubuntu/.openclaw/workspace && python3 scripts/health_engine.py --quick --watch. Only relay if the output contains CRITICAL or EMERGENCY alerts. Otherwise reply with NO_REPLY.",
    "timeoutSeconds": 30
  },
  "delivery": {
    "mode": "announce",
    "channel": "telegram",
    "to": "8039230885"
  }
}
```

### 2. Deep check — every hour

Checks all layers (0–6):

```
{
  "id": "health-engine-deep",
  "agentId": "main",
  "sessionKey": "agent:main:main",
  "name": "Trevor health engine — deep check",
  "description": "Hourly full health check (all layers 0-6)",
  "enabled": true,
  "schedule": {
    "kind": "every",
    "everyMs": 3600000,
    "anchorMs": <current epoch ms>
  },
  "sessionTarget": "session:agent:main:main",
  "wakeMode": "now",
  "payload": {
    "kind": "agentTurn",
    "message": "REPLY IN ENGLISH ONLY. Run: cd /home/ubuntu/.openclaw/workspace && python3 scripts/health_engine.py --deep --watch. Only relay if the output contains CRITICAL or EMERGENCY alerts. Otherwise reply with NO_REPLY.",
    "timeoutSeconds": 30
  },
  "delivery": {
    "mode": "announce",
    "channel": "telegram",
    "to": "8039230885"
  }
}
```

> **Important:** Replace `<current epoch ms>` with the current Unix timestamp in
> milliseconds. On Linux: `date +%s%3N`. This anchors the "every" schedule so
> jobs run on a predictable cadence from the anchor point.

### Alternative: Single combined cron

If you prefer a single cron entry, register one hourly job:

```
{
  "id": "health-engine",
  "agentId": "main",
  "sessionKey": "agent:main:main",
  "name": "Trevor health engine",
  "description": "Hourly health check — uses --watch for alert escalation",
  "enabled": true,
  "schedule": {
    "kind": "every",
    "everyMs": 3600000,
    "anchorMs": <current epoch ms>
  },
  "sessionTarget": "session:agent:main:main",
  "wakeMode": "now",
  "payload": {
    "kind": "agentTurn",
    "message": "REPLY IN ENGLISH ONLY. Run: cd /home/ubuntu/.openclaw/workspace && python3 scripts/health_engine.py --quick --watch. Only relay if the output contains CRITICAL or EMERGENCY alerts. Otherwise reply with NO_REPLY.",
    "timeoutSeconds": 30
  },
  "delivery": {
    "mode": "announce",
    "channel": "telegram",
    "to": "8039230885"
  }
}
```

The `--watch` flag prints Telegram-friendly `ALERT:CRITICAL:` lines to stdout,
which the cron delivery pipeline catches and relays.

## Adding after gateway restart

If the gateway is restarted, the health engine will immediately resume on its
scheduled cadence. No special handling needed.

## Manual usage

```bash
# Quick check (layers 0-2)
python3 scripts/health_engine.py --quick

# Quick check + status card
python3 scripts/health_engine.py --quick --status

# Full deep check + status
python3 scripts/health_engine.py --deep --status

# GitHub backup check only
python3 scripts/health_engine.py --check-github

# Watch mode (one-shot, prints CRITICAL alert lines to stdout)
python3 scripts/health_engine.py --watch

# Just the status card (from most recent dashboard)
python3 scripts/health_status_card.py
```

## Output files

- `tasks/health-dashboard.json` — always fresh after each check
- `tasks/health-alerts.md` — human-readable alert log with timestamps
- `logs/health-engine.log` — detailed debug/warn logs

## Alert escalation

| Level | Action |
|-------|--------|
| INFO | Logged to dashboard only |
| WARNING | Written to health-alerts.md, surfaced in next Telegram conversation |
| CRITICAL | Prints `ALERT:CRITICAL:` to stdout (caught by cron delivery) |
| EMERGENCY | Gateway down / disk 100% — immediate Telegram alert |

## Design principles

1. **Aggregator, not re-executor.** The engine reads existing state files. It
   does not replace dedicated health scripts like deepseek_monitor.py or
   agentmail_reader.py.

2. **Graceful degradation.** A failure in one layer never crashes the engine.
   Each layer wraps its checks in try/except and logs errors.

3. **Zero dependencies.** Stdlib only. No pip packages required.

4. **Atomic writes.** Dashboard is written to a temp file then renamed into
   place to prevent partial reads.

5. **Pathlib throughout.** No string path concatenation. All paths resolve
   relative to `REPO_ROOT = /home/ubuntu/.openclaw/workspace`.

## Files referenced by the engine

| File | Used by layer |
|------|---------------|
| `/home/ubuntu/.openclaw/cron/jobs-state.json` | Layer 2 — cron health |
| `tasks/infra-alert-state.json` | Layer 1 — infrastructure |
| `brain/memory/semantic/deepseek-usage.json` | Layer 1, 6 — balance & cost |
| `tasks/runtime-state.json` | Layer 1 — degraded mode |
| `memory/heartbeat-state.json` | Layer 5 — heartbeat cycle |
| `final/brief.md` | Layer 3 — pipeline completion |
| `tasks/qc-alert.md` | Layer 3 — quality gates |
| `brain/memory/episodic/` | Layer 4 — episodic logs |
| `brain/index/index.json` | Layer 4 — brain index freshness |
| `brain/memory/semantic/cognition-promotions.json` | Layer 4 — cognition bridge |
| `config/budget.yaml` | Layer 6 — budget caps |

## Troubleshooting

**No dashboard file after running:**
→ Check `logs/health-engine.log` for errors.
→ Ensure the cron state file exists at `/home/ubuntu/.openclaw/cron/jobs-state.json`.

**All cron jobs show "failing":**
→ Likely a systemic billing error. Check `layer.systemic_errors` in the dashboard.
→ The correlation module groups identical errors across jobs.

**GitHub backup warnings:**
→ These are informational. Push workspace changes with `git push origin main`.
→ The `backup_status` field shows "ok", "stale" (>48h), or "critical" (>72h).
