# 🔒 Daily Skill Security Audit — 2026-05-05 00:00 UTC

## Executive Summary

| Metric | Count |
|--------|-------|
| Skills scanned | 76 |
| ✅ Approved | 60 |
| ⚠️ Caution | 1 |
| ❌ Rejected | 15 |
| Scan errors | 0 |
| Total findings | 28 |
| 🔴 Critical | 26 |
| 🟠 High | 1 |
| 🟡 Medium | 1 |
| 🔵 Info | 0 |

### ✅ Approved Skills (no critical/high issues)

- **answeroverflow** — 1 files, 0 issue(s)
- **apple-notes** — 1 files, 0 issue(s)
- **apple-reminders** — 1 files, 0 issue(s)
- **blogwatcher** — 1 files, 0 issue(s)
- **blucli** — 1 files, 0 issue(s)
- **bluebubbles** — 1 files, 0 issue(s)
- **canvas** — 1 files, 0 issue(s)
- **claude-code** — 4 files, 0 issue(s)
- **clawhub** — 1 files, 0 issue(s)
- **coding-agent** — 1 files, 0 issue(s)
- **discord** — 1 files, 0 issue(s)
- **find-skills** — 1 files, 0 issue(s)
- **gemini** — 1 files, 0 issue(s)
- **gh-issues** — 1 files, 0 issue(s)
- **gifgrep** — 1 files, 0 issue(s)
- **github** — 1 files, 0 issue(s)
- **gog** — 1 files, 0 issue(s)
- **goplaces** — 1 files, 0 issue(s)
- **healthcheck** — 1 files, 0 issue(s)
- **huggingface-hub** — 1 files, 0 issue(s)
- **humanizer** — 1 files, 0 issue(s)
- **imsg** — 1 files, 0 issue(s)
- **maps-new** — 1 files, 0 issue(s)
- **mcporter** — 1 files, 0 issue(s)
- **nano-pdf** — 1 files, 0 issue(s)
- **network-analysis** — 3 files, 0 issue(s)
- **node-connect** — 1 files, 0 issue(s)
- **obsidian** — 1 files, 0 issue(s)
- **ocr-docu** — 4 files, 0 issue(s)
- **openai-whisper** — 1 files, 0 issue(s)
- **openai-whisper-api** — 2 files, 0 issue(s)
- **openhue** — 1 files, 0 issue(s)
- **ordercli** — 1 files, 0 issue(s)
- **peekaboo** — 1 files, 0 issue(s)
- **sag** — 1 files, 0 issue(s)
- **self-improving-agent** — 1 files, 0 issue(s)
- **session-logs** — 1 files, 0 issue(s)
- **sherpa-onnx-tts** — 2 files, 0 issue(s)
- **skill-creator** — 7 files, 0 issue(s)
- **slack** — 1 files, 0 issue(s)
- **songsee** — 1 files, 0 issue(s)
- **sonoscli** — 1 files, 0 issue(s)
- **stock-market-pro** — 1 files, 0 issue(s)
- **summarize** — 1 files, 0 issue(s)
- **taskflow** — 3 files, 0 issue(s)
- **taskflow-inbox-triage** — 1 files, 0 issue(s)
- **things-mac** — 1 files, 0 issue(s)
- **tmux** — 3 files, 0 issue(s)
- **trello** — 1 files, 0 issue(s)
- **video-frames** — 2 files, 0 issue(s)
- **voice-call** — 1 files, 0 issue(s)
- **wacli** — 1 files, 0 issue(s)
- **weather** — 1 files, 0 issue(s)
- **web-searchplus** — 1 files, 0 issue(s)
- **xurl** — 1 files, 0 issue(s)
- **youtube-content** — 1 files, 0 issue(s)

### ⚠️ Skills Requiring Caution (high-severity issues)

- **trevor-methodology** — 1 high issue(s)
  - `eval_exec` in `pipeline/docx-js-template.js` line 37: Dynamic code execution - could run arbitrary code

### ❌ Rejected Skills (critical issues)

- **1password** — 1 critical issue(s)
  - `credential_paths` in `references/cli-examples.md` line 19: Accesses sensitive credential locations
- **api-gateway** — 1 critical issue(s)
  - `credential_paths` in `SKILL.md` line 539: Accesses sensitive credential locations
- **bear-notes** — 7 critical issue(s)
  - `credential_paths` in `SKILL.md` line 33: Accesses sensitive credential locations
  - `credential_paths` in `SKILL.md` line 40: Accesses sensitive credential locations
  - `credential_paths` in `SKILL.md` line 60: Accesses sensitive credential locations
  - `credential_paths` in `SKILL.md` line 66: Accesses sensitive credential locations
  - `credential_paths` in `SKILL.md` line 92: Accesses sensitive credential locations
  - `credential_paths` in `SKILL.md` line 94: Accesses sensitive credential locations
  - `credential_paths` in `SKILL.md` line 97: Accesses sensitive credential locations
- **camsnap** — 1 critical issue(s)
  - `credential_paths` in `SKILL.md` line 31: Accesses sensitive credential locations
- **eightctl** — 1 critical issue(s)
  - `credential_paths` in `SKILL.md` line 31: Accesses sensitive credential locations
- **gmail** — 1 critical issue(s)
  - `credential_paths` in `SKILL.md` line 267: Accesses sensitive credential locations
- **gog-myclaw** — 2 critical issue(s)
  - `credential_paths` in `SKILL.md` line 23: Accesses sensitive credential locations
  - `credential_paths` in `SKILL.md` line 24: Accesses sensitive credential locations
- **himalaya** — 3 critical issue(s)
  - `credential_paths` in `SKILL.md` line 37: Accesses sensitive credential locations
  - `credential_paths` in `SKILL.md` line 48: Accesses sensitive credential locations
  - `credential_paths` in `references/configuration.md` line 3: Accesses sensitive credential locations
- **model-usage** — 1 critical issue(s)
  - `credential_paths` in `references/codexbar-cli.md` line 32: Accesses sensitive credential locations
- **notion** — 3 critical issue(s)
  - `credential_paths` in `SKILL.md` line 23: Accesses sensitive credential locations
  - `credential_paths` in `SKILL.md` line 24: Accesses sensitive credential locations
  - `credential_paths` in `SKILL.md` line 34: Accesses sensitive credential locations
- **oracle** — 1 critical issue(s)
  - `credential_paths` in `SKILL.md` line 115: Accesses sensitive credential locations
- **spotify-player** — 1 critical issue(s)
  - `credential_paths` in `SKILL.md` line 62: Accesses sensitive credential locations
- **stripe-api** — 1 critical issue(s)
  - `credential_paths` in `SKILL.md` line 778: Accesses sensitive credential locations
- **video-translation** — 1 critical issue(s)
  - `credential_paths` in `SKILL.md` line 90: Accesses sensitive credential locations
- **whatsapp-business** — 1 critical issue(s)
  - `credential_paths` in `SKILL.md` line 494: Accesses sensitive credential locations

---
## Detailed Findings (Non-Approved Skills)

### 1password — REJECT

- Path: `/usr/lib/node_modules/openclaw/skills/1password`
- Files: 3 | Scripts: 0 | Lines: 119
- Verdict reason: Found 1 critical issue(s): credential_paths

| Pattern | Severity | File | Line | Code |
|---------|----------|------|------|------|
| credential_paths | 🔴 critical | `references/cli-examples.md` | 19 | `- `op run --env-file="./.env" -- printenv DB_PASSWORD`` |

### api-gateway — REJECT

- Path: `/home/ubuntu/.openclaw/skills/api-gateway`
- Files: 1 | Scripts: 0 | Lines: 639
- Verdict reason: Found 1 critical issue(s): credential_paths

| Pattern | Severity | File | Line | Code |
|---------|----------|------|------|------|
| credential_paths | 🔴 critical | `SKILL.md` | 539 | `'Authorization': `Bearer ${process.env.MATON_API_KEY}`` |

### bear-notes — REJECT

- Path: `/usr/lib/node_modules/openclaw/skills/bear-notes`
- Files: 1 | Scripts: 0 | Lines: 108
- Verdict reason: Found 7 critical issue(s): credential_paths

| Pattern | Severity | File | Line | Code |
|---------|----------|------|------|------|
| credential_paths | 🔴 critical | `SKILL.md` | 33 | `- For some operations (add-text, tags, open-note --selected), a Bear app token (` |
| credential_paths | 🔴 critical | `SKILL.md` | 40 | `2. Save it: `echo "YOUR_TOKEN" > ~/.config/grizzly/token`` |
| credential_paths | 🔴 critical | `SKILL.md` | 60 | `echo "Additional content" | grizzly add-text --id "NOTE_ID" --mode append --toke` |
| credential_paths | 🔴 critical | `SKILL.md` | 66 | `grizzly tags --enable-callback --json --token-file ~/.config/grizzly/token` |
| credential_paths | 🔴 critical | `SKILL.md` | 92 | `4. `~/.config/grizzly/config.toml`` |
| credential_paths | 🔴 critical | `SKILL.md` | 94 | `Example `~/.config/grizzly/config.toml`:` |
| credential_paths | 🔴 critical | `SKILL.md` | 97 | `token_file = "~/.config/grizzly/token"` |

### camsnap — REJECT

- Path: `/usr/lib/node_modules/openclaw/skills/camsnap`
- Files: 1 | Scripts: 0 | Lines: 46
- Verdict reason: Found 1 critical issue(s): credential_paths

| Pattern | Severity | File | Line | Code |
|---------|----------|------|------|------|
| credential_paths | 🔴 critical | `SKILL.md` | 31 | `- Config file: `~/.config/camsnap/config.yaml`` |

### eightctl — REJECT

- Path: `/usr/lib/node_modules/openclaw/skills/eightctl`
- Files: 1 | Scripts: 0 | Lines: 51
- Verdict reason: Found 1 critical issue(s): credential_paths

| Pattern | Severity | File | Line | Code |
|---------|----------|------|------|------|
| credential_paths | 🔴 critical | `SKILL.md` | 31 | `- Config: `~/.config/eightctl/config.yaml`` |

### gmail — REJECT

- Path: `/home/ubuntu/.openclaw/skills/gmail`
- Files: 1 | Scripts: 0 | Lines: 340
- Verdict reason: Found 1 critical issue(s): credential_paths

| Pattern | Severity | File | Line | Code |
|---------|----------|------|------|------|
| credential_paths | 🔴 critical | `SKILL.md` | 267 | `'Authorization': `Bearer ${process.env.MATON_API_KEY}`` |

### gog-myclaw — REJECT

- Path: `/home/ubuntu/.openclaw/skills/gog-myclaw`
- Files: 4 | Scripts: 1 | Lines: 90
- Verdict reason: Found 2 critical issue(s): credential_paths

| Pattern | Severity | File | Line | Code |
|---------|----------|------|------|------|
| credential_paths | 🔴 critical | `SKILL.md` | 23 | `3. Once they provide the `credentials.json` content, save it to `~/.config/gogcl` |
| credential_paths | 🔴 critical | `SKILL.md` | 24 | `4. Run: `gog auth credentials set ~/.config/gogcli/credentials.json`` |
| http_post_external | 🟡 medium | `config/exchange.py` | 16 | `response = requests.post('https://oauth2.googleapis.com/token', data=data)` |

### himalaya — REJECT

- Path: `/usr/lib/node_modules/openclaw/skills/himalaya`
- Files: 3 | Scripts: 0 | Lines: 643
- Verdict reason: Found 3 critical issue(s): credential_paths

| Pattern | Severity | File | Line | Code |
|---------|----------|------|------|------|
| credential_paths | 🔴 critical | `SKILL.md` | 37 | `2. A configuration file at `~/.config/himalaya/config.toml`` |
| credential_paths | 🔴 critical | `SKILL.md` | 48 | `Or create `~/.config/himalaya/config.toml` manually:` |
| credential_paths | 🔴 critical | `references/configuration.md` | 3 | `Configuration file location: `~/.config/himalaya/config.toml`` |

### model-usage — REJECT

- Path: `/usr/lib/node_modules/openclaw/skills/model-usage`
- Files: 4 | Scripts: 2 | Lines: 465
- Verdict reason: Found 1 critical issue(s): credential_paths

| Pattern | Severity | File | Line | Code |
|---------|----------|------|------|------|
| credential_paths | 🔴 critical | `references/codexbar-cli.md` | 32 | `- Claude: ~/.config/claude/projects/**/\*.jsonl or ~/.claude/projects/**/\*.json` |

### notion — REJECT

- Path: `/usr/lib/node_modules/openclaw/skills/notion`
- Files: 1 | Scripts: 0 | Lines: 175
- Verdict reason: Found 3 critical issue(s): credential_paths

| Pattern | Severity | File | Line | Code |
|---------|----------|------|------|------|
| credential_paths | 🔴 critical | `SKILL.md` | 23 | `mkdir -p ~/.config/notion` |
| credential_paths | 🔴 critical | `SKILL.md` | 24 | `echo "ntn_your_key_here" > ~/.config/notion/api_key` |
| credential_paths | 🔴 critical | `SKILL.md` | 34 | `NOTION_KEY=$(cat ~/.config/notion/api_key)` |

### oracle — REJECT

- Path: `/usr/lib/node_modules/openclaw/skills/oracle`
- Files: 1 | Scripts: 0 | Lines: 126
- Verdict reason: Found 1 critical issue(s): credential_paths

| Pattern | Severity | File | Line | Code |
|---------|----------|------|------|------|
| credential_paths | 🔴 critical | `SKILL.md` | 115 | `- Don’t attach secrets by default (`.env`, key files, auth tokens). Redact aggre` |

### spotify-player — REJECT

- Path: `/usr/lib/node_modules/openclaw/skills/spotify-player`
- Files: 1 | Scripts: 0 | Lines: 65
- Verdict reason: Found 1 critical issue(s): credential_paths

| Pattern | Severity | File | Line | Code |
|---------|----------|------|------|------|
| credential_paths | 🔴 critical | `SKILL.md` | 62 | `- Config folder: `~/.config/spotify-player` (e.g., `app.toml`).` |

### stripe-api — REJECT

- Path: `/home/ubuntu/.openclaw/skills/stripe-api`
- Files: 1 | Scripts: 0 | Lines: 855
- Verdict reason: Found 1 critical issue(s): credential_paths

| Pattern | Severity | File | Line | Code |
|---------|----------|------|------|------|
| credential_paths | 🔴 critical | `SKILL.md` | 778 | `'Authorization': `Bearer ${process.env.MATON_API_KEY}`` |

### trevor-methodology — CAUTION

- Path: `/home/ubuntu/.openclaw/skills/trevor-methodology`
- Files: 26 | Scripts: 3 | Lines: 5281
- Verdict reason: Found 1 high-severity issue(s): eval_exec

| Pattern | Severity | File | Line | Code |
|---------|----------|------|------|------|
| eval_exec | 🟠 high | `pipeline/docx-js-template.js` | 37 | `const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);` |

### video-translation — REJECT

- Path: `/home/ubuntu/.agents/skills/video-translation`
- Files: 3 | Scripts: 2 | Lines: 219
- Verdict reason: Found 1 critical issue(s): credential_paths

| Pattern | Severity | File | Line | Code |
|---------|----------|------|------|------|
| credential_paths | 🔴 critical | `SKILL.md` | 90 | `- `NOIZ_API_KEY` configured for the Noiz backend. If it is not set, first guide ` |

### whatsapp-business — REJECT

- Path: `/home/ubuntu/.openclaw/skills/whatsapp-business`
- Files: 1 | Scripts: 0 | Lines: 637
- Verdict reason: Found 1 critical issue(s): credential_paths

| Pattern | Severity | File | Line | Code |
|---------|----------|------|------|------|
| credential_paths | 🔴 critical | `SKILL.md` | 494 | `'Authorization': `Bearer ${process.env.MATON_API_KEY}`,` |

---
*Report generated by skill-scanner (daily cron audit) at 2026-05-05 00:00 UTC*
