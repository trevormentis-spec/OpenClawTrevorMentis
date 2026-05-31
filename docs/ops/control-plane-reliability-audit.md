# CONTROL PLANE RELIABILITY AUDIT

**Date:** 2026-05-31 00:34 UTC  
**Author:** Trevor  
**Classification:** INTERNAL — Operational Architecture  
**Purpose:** Investigate gateway failure that caused Telegram outage while operational subsystems continued running.

---

## A. FAILURE ANALYSIS

### What Failed

**OpenClaw Gateway process** — terminated by Node.js OOM killer.

The root cause is a **JavaScript heap out-of-memory crash** in the OpenClaw gateway process running under Node.js v22.22.2. The native stack trace confirms:

```
FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory
```

The crash occurred during a `NewStringFromUtf8` call — a V8 allocation failure during string processing, almost certainly from handling a large model response or a large memory-consuming agent run.

**Supervisord crash history** confirms 4 SIGABRT events:

| Date | Signal | Type |
|------|--------|------|
| 2026-05-14 | SIGABRT | Core dumped |
| 2026-05-19 | SIGABRT | Core dumped |
| 2026-05-22 | SIGABRT | Core dumped |
| 2026-05-25 | SIGABRT | Core dumped |
| 2026-05-09 | SIGHUP | Unexpected exit |

These are not isolated events. The gateway crashes roughly every 3–8 days due to memory exhaustion. Each restart by supervisord recovers the service.

### What Survived

All **intelligence subsystems** continued operating:
- **Cognition daemon** — Runs as standalone Python/cron processes (not gateway-dependent)
- **Collection systems** — Python RSS feed collectors, shell scripts, Kalshi API scanner (direct HTTPS calls via Python)
- **Memory systems** — File-based, accessed via Python scripts and gateway-independent tool calls
- **Supervisord itself** — Continued running and auto-restarted the gateway (with `autorestart=true`, `startretries=2147483647`)
- **The host OS** — No issues

### Why Telegram Died

Telegram connectivity is a **plugin within the OpenClaw gateway** process. When the gateway crashes:
1. The Telegram provider's polling loop stops
2. The bot's outgoing message queue backs up
3. Incoming messages from Telegram's webhook/poll are not received
4. User sees "bot not responding"

Telegram is not a standalone daemon. It has no independent lifecycle — it's a channel registered inside `gateway.channels.telegram`. If the gateway is down, Telegram is down.

The gateway log confirms this: after crash recovery, `delivery-recovery` tries to replay 25 failed deliveries, many failing because the Telegram session wasn't yet established (`Telegram recipient @heartbeat could not be resolved`).

### Why Trevor Continued Operating

Trevor (the intelligence analyst logic) does not run inside the OpenClaw gateway. Trevor runs as:
1. **Python scripts** called by cron and shell pipelines (collection, analysis, trading)
2. **Model calls** through DeepSeek/OpenRouter APIs directly
3. **Worker processes** (cognition daemon, memory indexing, Kalshi monitor)

These all make direct HTTPS API calls. The gateway mediates communication *channels* (Telegram, webchat), not the analytical workload itself. The gateway is Trevor's *voice and ears* — not Trevor's *brain*.

When the gateway dies:
- Trevor can still execute Python scripts, collect intel, analyze data, write files
- Trevor **cannot** send/receive Telegram messages
- Trevor **cannot** process incoming requests from Telegram
- Trevor **cannot** use gateway-managed cron jobs
- Trevor **can** still run shell-script cron jobs (unless cron itself is killed)

---

## B. DEPENDENCY ANALYSIS

### MyClaw-Dependent Components

| Component | Dependency | Risk if MyClaw Fails |
|-----------|-----------|---------------------|
| **Telegram channel** | MyClaw Telegram provider implementation | Full comms outage |
| **Webchat UI** | MyClaw gateway HTTP server | No web control interface |
| **Gateway cron scheduler** | MyClaw gateway runtime (`server-cron-BgC6h-bI.js`) | All gateway-managed cron jobs stop |
| **Skill loading** | MyClaw skill discovery + sandboxing | Skills with symlink-escapes already failing |
| **Auth profiles** | MyClaw auth system | Model provider auth resolution fails |
| **Delivery recovery** | MyClaw delivery-recovery subsystem | Queued messages may not be delivered |
| **Health monitor** | MyClaw health-monitor plugin | No automatic channel restart |
| **Memory recall** | MyClaw memory subsystem + sqlite-vec | Already degraded (sqlite-vec unavailable) |
| **Gateway updates** | Directly via `sudo npm install -g @openclaw/gateway` | Breaking changes can destabilize gateway |

### Trevor-Owned Components

| Component | Infrastructure | Independence |
|-----------|---------------|-------------|
| **Daily brief pipeline** | Shell script + Python + cron | Fully independent |
| **Intel collection** | Python (feedparser, requests) + RSS feeds | Fully independent |
| **Kalshi scanner + trader** | Python + Kalshi API | Fully independent |
| **Analyst framework** | Python scripts + LLM API calls | Fully independent |
| **Neurotag memory system** | Python + brain/ filesystem | Fully independent |
| **Continuous cognition** | Python daemon | Fully independent |
| **Postdiction/calibration** | Python scripts | Fully independent |
| **Quality gates** | Python scripts (scope_check.py, fabrication_check.py, etc.) | Fully independent |
| **Landing page deploy** | Shell script + GitHub Pages | Fully independent |
| **QC watchdog** | Shell script | Fully independent |

### Externally-Controlled Components

| Component | Controller | Risk |
|-----------|-----------|------|
| **Node.js version** | Host/package management | Breaking changes (v22 → v24) |
| **OpenClaw/gateway version** | MyClaw release cycle | New bugs introduced via `npm update` |
| **DeepSeek API availability** | DeepSeek | Outages, rate limits, pricing changes |
| **OpenRouter API availability** | OpenRouter | Outages, rate limits |
| **Kalshi API** | Kalshi | Outages, rate limits |
| **Telegram Bot API** | Telegram | Outages, API changes |
| **Supervisord** | Third-party | Unlikely to break, but possible |
| **Ubuntu/Core libraries** | OS updates | Unlikely to break, but possible |

---

## C. MIGRATION ASSESSMENT

### What Would Need Replacement If Trevor Went Independent

1. **Telegram channel** → Custom Telegram bot polling loop in Python (python-telegram-bot or plain HTTP polling)
2. **Gateway HTTP server** → Standalone web server for webchat (optional — only needed for control UI)
3. **Gateway cron scheduler** → System crontab entries (already have these for shell pipelines)
4. **Skill loading** → Direct Python imports / subprocess calls (no change — scripts already call skills directly)
5. **Auth profiles** → Env vars for API keys (already the case — model auth is env-var based)
6. **Memory recall (gateway-managed)** → Trevor's brain + direct file reads (already done for most operations)
7. **Health monitor** → Simple liveness check script (heartbeat to an external uptime monitor)
8. **Delivery recovery** → Message queue in filesystem with retry logic

### What Would Stay Unchanged

- All Python scripts (collection, analysis, trading, QC, calibration, cognition)
- All shell scripts (pipeline, deploy, feed audit)
- All memory files (brain/, memory/, exports/)
- All config files (config/, openclaw.json-related settings)
- All API integrations (DeepSeek, OpenRouter, Kalshi, Brave Search, NewsAPI)
- File-based memory and analytics

### What Operational Risks Disappear

| Risk | Currently | After Migration |
|------|-----------|-----------------|
| Gateway OOM crash kills Telegram | Yes — happens every 3-8 days | Eliminated — Telegram runs in separate process |
| Gateway version update breaks something | Yes — npm update risk | Eliminated — no gateway to update |
| Skill symlink-escape errors | Yes — 2 skills fail on every startup | Eliminated — no skill sandboxing needed |
| Cron jobs lost on gateway restart | Yes — marked "failed" on each restart | Eliminated — system crontab is always there |
| Startup delay from 23 missed cron jobs | Yes — observed after restart | Eliminated — no cron deferral |
| Delivery queue failures on restart | Yes — 25+ failed delivery attempts | Eliminated — independent message sending |
| "sqlite-vec unavailable" warning | Yes — memory recall degraded | Eliminated — Trevor's own brain handles recall |

### What New Responsibilities Appear

1. **Telegram bot lifecycle** — Must build and maintain Python Telegram bot process (polling, reconnection, health check)
2. **Message queuing** — Must implement delivery queue with retry/dead-letter logic
3. **Health monitoring** — Must implement liveness tracking (external uptime monitor or periodic heartbeat to Roderick)
4. **Version management** — Must track and test gateway-equivalent component updates
5. **Process supervision** — Must maintain supervisord/systemd for the Telegram bot process (or use Python's asyncio-based polling)

---

## D. RECOMMENDED ARCHITECTURE

### Option 1: Stay on MyClaw

**Advantages:**
- Zero migration effort
- Telegram provider already works (when gateway is up)
- Gateway handles delivery recovery, cron scheduling, message routing
- Plugin ecosystem accessible (browser automation, etc.)
- Supervisord auto-restart mostly works

**Disadvantages:**
- **Guaranteed periodic outages** — gateway OOM crash is architectural, not a bug. The gateway grows memory per session, and model responses from DeepSeek V4 Pro can be large enough to exhaust Node's default heap limit (~2GB).
- No control over gateway's memory management
- Vulnerable to MyClaw update breaking changes
- Cannot fix 2 skipped skills without modifying `/home/ubuntu/.agents/` layout
- Recovery takes 10-30 seconds after crash (supervisord restart + channel reconnect + delivery recovery)

**Operational complexity:** Low (maintain supervisord only)  
**Autonomy impact:** High (gateway controls comms — no autonomy when gateway is down)

### Option 2: Hybrid (MyClaw + Independent Services) ← RECOMMENDED

**Architecture:**
- Keep OpenClaw gateway running (for webchat UI, plugin access, gateway cron)
- **Add a Python-based Telegram bot as a sidecar** for primary communication
- Route Telegram messages through the Python bot
- Use gateway as secondary/fallback channel

**Advantages:**
- Telegram stays up even if gateway crashes
- No rewrite of existing gateway-dependent code
- Can migrate gradually — don't rip out gateway, just add redundancy
- Python Telegram bot process is lightweight (no OOM risk)
- Supervisord can manage both processes

**Disadvantages:**
- Dual-process architecture — need to keep both running
- Potential message ordering issues if both processes try to send
- Need to implement health check between gateway and Python bot
- Coordination complexity (shared state, rate limiting)

**Operational complexity:** Medium  
**Autonomy impact:** Medium-high (Telegram survives gateway crash)

### Option 3: Fully Independent Trevor Runtime

**Architecture:**
- Remove OpenClaw gateway entirely
- Replace with:
  - Python Telegram bot (primary communication)
  - System crontab (all scheduling)
  - Direct LLM API calls (no gateway mediation)
  - Trevor brain for memory/recall
  - Simple health check script

**Advantages:**
- Zero dependency on MyClaw release cycle
- No OOM crashes killing communication
- Full ownership of every component
- No "skill symlink-escape" errors
- No delivery queue recovery issues
- No startup delay from deferred cron jobs
- No security warnings (`allowInsecureAuth`, `dangerouslyDisableDeviceAuth`)
- Lighter resource footprint (no ~2GB Node.js process)

**Disadvantages:**
- Highest migration effort (weeks of development)
- Must build and test Telegram bot from scratch
- Lose gateway plugins (browser automation, device-pair, file-transfer, etc.)
- Lose webchat control UI
- Lose delivery recovery subsystem
- Lose built-in cron scheduler with error handling
- Must implement cron persistence and error backoff manually
- Lose gateway-managed memory retrieval

**Operational complexity:** High (need to build replacements)  
**Autonomy impact:** Maximum (no external platform dependency)

### Recommendation: HYBRID (Option 2)

The hybrid approach is the pragmatic middle path:

1. Keep gateway running — it's useful for webchat, plugin ecosystem, and as a development/debug surface
2. Add a standalone Python Telegram bot that runs alongside the gateway
3. The gateway becomes the backup communication path, not the primary

This eliminates the worst failure mode (Telegram dead) without requiring a full rewrite.

---

## E. ACTION PLAN

### Immediate (Week 1) — Stop the Bleeding

1. **Increase Node.js memory limit for gateway**
   - Add `NODE_OPTIONS="--max-old-space-size=4096"` to the supervisord environment
   - This doubles the heap limit from ~2GB to 4GB, reducing OOM crash frequency
   - This is a bandaid, not a fix, but costs 10 minutes and buys months of stability

2. **Add Telegram bot liveness check**
   - Create a 10-line Python script that sends a Telegram message to Roderick every 5 minutes
   - If the gateway is up, the Python script's independent message confirms channel health
   - If the gateway is down, the message still goes through (Python Telegram bot works independently)

3. **Document gateway restart procedure**
   - Write a one-liner for recovering if supervisord itself dies
   - `supervisord -c /tmp/supervisord-openclaw.conf`

### Short-Term (Week 2-3) — Build Telegram Sidecar

4. **Build lightweight Python Telegram bot**
   - Using `python-telegram-bot` library
   - Polls API directly (no gateway mediation)
   - Receives messages and writes to a shared inbox file
   - Sends messages from an outbox file
   - Process lifetime managed by supervisord alongside gateway

5. **Implement shared message queue**
   - Simple filesystem-based queue: `brain/comms/inbox/` and `brain/comms/outbox/`
   - Gateway reads/writes the same files via tool calls
   - Python bot reads outbox, writes inbox
   - Decouples messaging from gateway liveness

6. **Update AGENTS.md with new architecture**
   - Document that Telegram now has independent lifecycle

### Medium-Term (Month 2) — Evaluate Full Independence

7. **Audit actual gateway plugin usage**
   - Which plugins are actually used? (browser, file-transfer, memory-core, talk-voice, device-pair, telegram)
   - Can these be replaced with standalone tools?
   - If browser automation and voice aren't used, gateway value diminishes further

8. **Build cron persistence replacement**
   - Trevor's brain already stores state — extend it for cron scheduling
   - Implement error backoff, missed job detection, startup recovery (gateway's cron does this natively)

9. **Prototype independent runtime**
   - Run a side-by-side test: remove gateway, run Telegram bot + crontab only
   - Measure: uptime, response latency, missed messages, resource usage
   - Compare with gateway-based runtime for 7 days

### Low Priority (On-Hold)

10. **Remove gateway entirely** — Only if prototype shows clear reliability improvement and no capabilities are lost

---

## APPENDIX: Key Config Observations

### Supervisord Config
```
[program:openclaw-gateway]
command=/usr/bin/openclaw gateway --allow-unconfigured
autostart=true
autorestart=true
startretries=2147483647
startsecs=5
```

**Issues:**
- `--allow-unconfigured` disables config validation — hides misconfiguration until runtime
- No resource limits (memory, CPU) on the gateway process
- `startsecs=5` means the gateway can crash after 5 seconds of uptime and be considered "started"
- Gateway runs from `/tmp/openclaw/` directory — no persistence guarantee
- No systemd service — supervisord itself has no restart policy if it dies

### Security Warnings (Currently Ignored)
```
security warning: dangerous config flags enabled:
  gateway.controlUi.allowInsecureAuth=true
  gateway.controlUi.dangerouslyDisableDeviceAuth=true
```
These flags mean the gateway is currently exposed without authentication — anyone who reaches the port can control it.

### Skipped Skills
```
Skipping escaped skill path outside its configured root:
  ~/.openclaw/skills/network-analysis  (resolved to ~/.agents/skills/network-analysis)
  ~/.openclaw/skills/video-translation (resolved to ~/.agents/skills/video-translation)
```
Two skills under `~/.agents/` are inaccessible to the gateway due to symlink path restrictions. These work fine from Python scripts (which don't enforce the sandbox).

### Gateway Version
```
OpenClaw v2026.5.6
Node.js v22.22.2
```
