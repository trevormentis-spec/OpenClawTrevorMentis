# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for setup-specific notes, not secrets.

## Secret Handling

- Do not commit API keys, tokens, passwords, bearer strings, or private URLs with embedded credentials.
- Store secrets in environment variables, `.env` files that are gitignored, or OpenClaw auth profiles outside the repo.
- If a secret is ever committed, rotate it immediately and remove it from future commits.

## Local Notes

### Moltbook

- Registered as `trevormentis` on Mon, May 2026
- API key stored outside git at `~/.config/moltbook/credentials.json`
- Profile: https://www.moltbook.com/u/trevormentis
- Base URL: https://www.moltbook.com/api/v1
- Status: active

### Email

- Trevor operational mailbox: `trevor_mentis@agentmail.to`
- AgentMail is the preferred email path over Gmail for Trevor's direct send/receive capability.
- Official AgentMail skill is installed in `skills/agentmail` and enabled in OpenClaw config.
- Fast send path when needed: use AgentMail REST API with bearer auth from local secrets only.
- Current inbox polling helper: `agentmail/check_inbox.py`

### Netlify — Project Sentinel Dashboard

- Dashboard URL: https://glittering-croquembouche-68ad80.netlify.app/
- Auth token is stored in `.env` as `NETLIFY_AUTH_TOKEN` and must not be committed.
- Source content lives in `exports/` directory.

### DeepSeek Token Monitor

- Script: `scripts/deepseek_monitor.py`
- Usage: `python3 scripts/deepseek_monitor.py`; use `--snapshot` to record balance.
- Data: `brain/memory/semantic/deepseek-usage.json`
- API key location: OpenClaw auth profile outside this repo.
- Rotate any previously committed DeepSeek key before using this repo in production.

### OpenRouter Monitor

- Script: `scripts/openrouter_monitor.py`
- Policy: OpenRouter only for specialist image/video/TTS models. DeepSeek Direct API only for DeepSeek models.

### Analyst Program

- Analyst training scaffold lives under `analyst/`.
- Start with `analyst/playbooks/analytic-workflow.md` and `analyst/templates/analytic-note.md`.
