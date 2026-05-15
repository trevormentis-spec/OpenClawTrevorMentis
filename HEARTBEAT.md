# HEARTBEAT.md — Trevor periodic checks

> If this file is empty or contains only comments, heartbeats no-op
> (return `HEARTBEAT_OK`). Add tasks below to make them productive.

## Cadence

Heartbeats fire roughly every 30 minutes. Trevor batches checks instead of
running each one as its own cron. Use cron only when timing has to be exact
or output has to deliver to a channel without main-session involvement.

State is tracked in `memory/heartbeat-state.json` so checks rotate rather
than stack on every fire.

## Standing checks (rotate; do 2–4 per fire, never all)

- [ ] **AgentMail inbox** — `trevor_mentis@agentmail.to`. Surface only
      meaningful new email; ignore newsletters and notifications. If a real
      action is needed, surface to Roderick before acting externally.
- [ ] **Gmail check** — `trevor.mentis@gmail.com` via Maton API.
      `cd REPO && python3 scripts/gmail_reader.py --max 5 --save`
      Check for:
      - OSINT intel (ISW, CTP, Foreign Policy, Cipher Brief, etc.) → save to pipeline
      - Document shares (Concentric briefings, Google Slides)
      - Security alerts, 2FA codes, account notifications
      - ANY email from a known contact (not just newsletters)
      Ignore: LinkedIn, Reddit, Twitter notifications (low value)
      IMPORTANT: The Concentric_Background_Briefing_May2026.pptx share
      request needs attention — may contain useful context.
- [ ] **Calendar** — anything in the next 24–48h that needs prep? Flag
      meetings without an agenda or briefing material.
- [ ] **Durable OSINT scan** — pull from `analyst/meta/sources.json`
      filtered to High signal level. Note any anomalies or material moves
      vs. the running baseline. Don't write a brief unless something
      genuinely changed.
- [ ] **Memory hygiene** — once a day, review the previous day's
      `memory/YYYY-MM-DD.md`. Anything worth promoting to `MEMORY.md`?
      Anything to demote/remove? Use `brain.py promote <key>` for
      structured promotions.
- [ ] **Nudge check** — run `python3 scripts/nudge_check.py`. If it
      returns nudges, address them (create skill, update memory, etc.).
- [ ] **Repo state** — uncommitted Trevor work? If yes, commit and push
      to GitHub backup.
- [ ] **Brain index freshness** — if `brain/index/index.json` is older
      than 24h or memory has changed, run `brain.py reindex`.
- [ ] **DeepSeek balance snapshot** — run `python3 scripts/deepseek_monitor.py --snapshot`
      (once per day to track burn rate). If balance < $50, surface to Roderick.
- [ ] **OpenRouter usage check** — run `python3 scripts/openrouter_monitor.py --alert`.
      If it reports OR-in-use, surface to Roderick.
## Quiet hours

- 23:00–08:00 Pacific Time: only respond on emergency-class triggers
  (UKMTO/JMIC critical alert, urgent personal email, calendar event in
  next 60min).
- Otherwise stay silent (`HEARTBEAT_OK`).

## When to break silence

- Important email arrived from a known correspondent
- Calendar event coming up in <2h with no prep done
- High-signal OSINT source flagged a real movement (not a routine update)
- It's been >8h of work hours and Trevor hasn't said anything

## When to stay silent

- Routine OSINT noise
- Newsletter / promotional email
- Calendar item that's already prepared for
- You just checked <30 min ago

## Anti-patterns to watch in self

- Heartbeat-as-anxiety: pinging Roderick every fire to demonstrate activity
- Heartbeat-as-spam: surfacing routine newsletters as "important email"
- Skipping the 30-min cooldown because the heartbeat fired again
- Forgetting to update `memory/heartbeat-state.json` (then everything
  fires every time)
