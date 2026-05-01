# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

## Local Notes

### Email

- Trevor operational mailbox: `trevor_mentis@agentmail.to`
- AgentMail is the preferred email path over Gmail for Trevor's direct send/receive capability.
- Official AgentMail skill is installed in `skills/agentmail` and enabled in OpenClaw config.
- Fast send path when needed: use AgentMail REST API directly at `https://api.agentmail.to/v0/inboxes/{inbox_id}/messages/send` with bearer auth.
- Known good inbox id: `trevor_mentis@agentmail.to`
- Before building custom email plumbing, check for an existing OpenClaw skill/integration first.
- AgentMail inbox should be checked persistently on an async cadence; email is not instant chat.
- Current inbox polling helper: `agentmail/check_inbox.py`
- Current AgentMail inbox check cron job id: `3aaa53c2-c93d-470f-9dc7-238c9c559c94`

### Analyst Program

- Analyst training scaffold lives under `analyst/`
- Start with `analyst/playbooks/analytic-workflow.md` and `analyst/templates/analytic-note.md` for real work
- Use structured methods rather than intuitive summaries when the stakes are meaningful

---

Add whatever helps you do your job. This is your cheat sheet.
