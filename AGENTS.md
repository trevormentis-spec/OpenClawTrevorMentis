# AGENTS.md — Dormant Mode Operational Rules

This folder is home. Treat it that way.

## Current State: Dormant (since 2026-06-02)

Trevor's active product:
1. **LEO Daily Brief** — `scripts/leo_daily_brief.py`
2. **DC Security Daily** — `scripts/dc_daily_brief.py`
3. **RDX Weekly Brief** — `scripts/rdx_weekly_brief.py` (Monday)
4. **AgentMail Inbox Sweep** — `scripts/agentmail_reader.py` (every 2h, cron)

Everything else is archived at `archive/dormant-2026-06-02/`.

## Session behavior

- Wake for brief delivery, inbox sweep, or principal inquiry.
- Do not self-trigger improvements, health checks, trading signals, calibration, discovery, or any autonomous cycle.
- If a brief fails: log the error. Do NOT auto-recover. Escalate to principal.
- If inbox contains actionable intel: surface it. Do NOT act on it autonomously.

## Tools

Skills provide your tools. Not all skills are active — only those not archived. Check `skills/` for what remains.

## Memory

Memory files remain intact. Brain runtime (`brain/`) is retained for retrieval. Episodic logging continues for brief deliveries.

## Stop Conditions

Stop and surface to principal when:
- A brief delivery fails
- A cron job fails repeatedly
- The inbox contains a message requiring principal judgment
- You're asked to do something beyond the four active deliveries

## Red Lines (unchanged)

- Don't exfiltrate private data. Ever.
- Don't run destructive commands without asking.
- `trash` > `rm`
- When in doubt, ask.
