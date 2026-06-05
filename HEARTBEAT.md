# HEARTBEAT.md — Dormant Mode

Trevor runs no heartbeat cycles in dormant mode. All autonomous cycles, health checks, source discovery, and collection rotation are disabled.

## What happens

- Brief deliveries fire on their cron schedule (LEO 09:00 PT daily, DC 08:00 PT daily, RDX 08:00 PT Monday)
- AgentMail inbox sweep fires every 2h
- Everything else is disabled

## If you receive a heartbeat wake

Reply with NO_REPLY and continue. The dormant-mode heartbeat is a no-op.

## State

State file: `memory/heartbeat-state.json` — archived at `archive/dormant-2026-06-02/heartbeat-state.json`.
