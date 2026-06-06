# AGENTS — Operational Rules

## Product

Trevor delivers three briefs:

| Brief | Script | Cadence | Recipient |
|---|---|---|---|
| LEO Ground Stations | scripts/leo_daily_brief.py | Daily | roderick.jones@gmail.com |
| Data Center Security | scripts/dc_daily_brief.py | Daily | roderick.jones@gmail.com |
| RDX / C4 Supply | scripts/rdx_weekly_brief.py | Weekly (Monday) | roderick.jones@gmail.com |

A fourth cron sweeps the AgentMail inbox (`scripts/agentmail_reader.py`)
and writes extracted newsletter content to tasks/news_raw.md so the
next brief can incorporate it.

## Red Lines

- Do not add new cron jobs. The four above are the entire schedule.
- Do not add health-monitoring, self-improvement, or feedback loops.
 They were tried and they failed. They are in archive/dormant-2026-06-02/.
- Do not write to public surfaces (landing page, newsletter, social).
 Those skills are archived.
- Do not place trades. The Kalshi adapter is for read-only balance and
 market checks called manually.
- Do not modify SOUL.md, IDENTITY.md, or this file without principal
 approval.
- Do not auto-commit. If a script needs to write state, write it to a
 gitignored path under brain/working-memory/ or tasks/.

## Session Startup

Read IDENTITY.md, this file, and STATUS.md. That's enough.

Do not re-read past briefs to "catch up." If a brief script needs prior
context it will load it itself.

## When Asked to Do Something Beyond the Briefs

Use the skills and adapters that are still present. They are libraries.
If a capability is in archive/dormant-2026-06-02/, surface that to
the principal before pulling it back — there was a reason it was
archived.

## Lessons Carried Forward (Do Not Re-Learn)

- Cron is the delivery mechanism. Script changes are not deployed until
 the cron path is updated.
- "Fix applied" ≠ "fix verified." A fix is closed only after a real run
 produces the expected output.
- Auth mechanisms are the most fragile knowledge. When you figure out
 how to authenticate to a service, write the exact method to
 docs/ops/ immediately.
- Layered automation amplifies failure. Two unreliable components in a
 loop are worse than one. Do not add a watcher to fix a watcher.
