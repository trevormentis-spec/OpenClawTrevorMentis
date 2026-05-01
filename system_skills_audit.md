# Skill Security Review - unknown unknown

**Scan Date:** 2026-04-29T00:01:09.060266
**Skill Path:** `/usr/lib/node_modules/openclaw/skills`

## Verdict

**REJECT** - Found 19 critical issue(s): credential_paths

## Metadata

- **Name:** unknown
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** False
- **Files:** 73
- **Scripts:** 11
- **Total Lines:** 9810

## Findings

Found **19** potential issue(s):

### credential_paths (critical)

- **File:** `eightctl/SKILL.md` line 31
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- Config: `~/.config/eightctl/config.yaml``

### credential_paths (critical)

- **File:** `camsnap/SKILL.md` line 31
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- Config file: `~/.config/camsnap/config.yaml``

### credential_paths (critical)

- **File:** `spotify-player/SKILL.md` line 62
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- Config folder: `~/.config/spotify-player` (e.g., `app.toml`).`

### credential_paths (critical)

- **File:** `bear-notes/SKILL.md` line 33
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- For some operations (add-text, tags, open-note --selected), a Bear app token (stored in `~/.config/grizzly/token`)`

### credential_paths (critical)

- **File:** `bear-notes/SKILL.md` line 40
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `2. Save it: `echo "YOUR_TOKEN" > ~/.config/grizzly/token``

### credential_paths (critical)

- **File:** `bear-notes/SKILL.md` line 60
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `echo "Additional content" | grizzly add-text --id "NOTE_ID" --mode append --token-file ~/.config/grizzly/token`

### credential_paths (critical)

- **File:** `bear-notes/SKILL.md` line 66
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `grizzly tags --enable-callback --json --token-file ~/.config/grizzly/token`

### credential_paths (critical)

- **File:** `bear-notes/SKILL.md` line 92
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `4. `~/.config/grizzly/config.toml``

### credential_paths (critical)

- **File:** `bear-notes/SKILL.md` line 94
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `Example `~/.config/grizzly/config.toml`:`

### credential_paths (critical)

- **File:** `bear-notes/SKILL.md` line 97
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `token_file = "~/.config/grizzly/token"`

### credential_paths (critical)

- **File:** `himalaya/SKILL.md` line 37
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `2. A configuration file at `~/.config/himalaya/config.toml``

### credential_paths (critical)

- **File:** `himalaya/SKILL.md` line 48
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `Or create `~/.config/himalaya/config.toml` manually:`

### credential_paths (critical)

- **File:** `oracle/SKILL.md` line 115
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- Don’t attach secrets by default (`.env`, key files, auth tokens). Redact aggressively; share only what’s required.`

### credential_paths (critical)

- **File:** `notion/SKILL.md` line 23
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `mkdir -p ~/.config/notion`

### credential_paths (critical)

- **File:** `notion/SKILL.md` line 24
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `echo "ntn_your_key_here" > ~/.config/notion/api_key`

### credential_paths (critical)

- **File:** `notion/SKILL.md` line 34
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `NOTION_KEY=$(cat ~/.config/notion/api_key)`

### credential_paths (critical)

- **File:** `1password/references/cli-examples.md` line 19
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- `op run --env-file="./.env" -- printenv DB_PASSWORD``

### credential_paths (critical)

- **File:** `model-usage/references/codexbar-cli.md` line 32
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- Claude: ~/.config/claude/projects/**/\*.jsonl or ~/.claude/projects/**/\*.jsonl`

### credential_paths (critical)

- **File:** `himalaya/references/configuration.md` line 3
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `Configuration file location: `~/.config/himalaya/config.toml``

## Files Scanned

- `gh-issues/SKILL.md`
- `canvas/SKILL.md`
- `session-logs/SKILL.md`
- `skill-creator/SKILL.md`
- `skill-creator/license.txt`
- `trello/SKILL.md`
- `bluebubbles/SKILL.md`
- `goplaces/SKILL.md`
- `voice-call/SKILL.md`
- `openai-whisper/SKILL.md`
- `blucli/SKILL.md`
- `songsee/SKILL.md`
- `summarize/SKILL.md`
- `clawhub/SKILL.md`
- `coding-agent/SKILL.md`
- `nano-pdf/SKILL.md`
- `eightctl/SKILL.md`
- `wacli/SKILL.md`
- `discord/SKILL.md`
- `sonoscli/SKILL.md`
- `blogwatcher/SKILL.md`
- `1password/SKILL.md`
- `model-usage/SKILL.md`
- `camsnap/SKILL.md`
- `openai-whisper-api/SKILL.md`
- `sherpa-onnx-tts/SKILL.md`
- `taskflow/SKILL.md`
- `imsg/SKILL.md`
- `peekaboo/SKILL.md`
- `video-frames/SKILL.md`
- `gemini/SKILL.md`
- `spotify-player/SKILL.md`
- `slack/SKILL.md`
- `github/SKILL.md`
- `bear-notes/SKILL.md`
- `himalaya/SKILL.md`
- `tmux/SKILL.md`
- `oracle/SKILL.md`
- `apple-notes/SKILL.md`
- `obsidian/SKILL.md`
- `sag/SKILL.md`
- `healthcheck/SKILL.md`
- `gog/SKILL.md`
- `apple-reminders/SKILL.md`
- `taskflow-inbox-triage/SKILL.md`
- `mcporter/SKILL.md`
- `ordercli/SKILL.md`
- `notion/SKILL.md`
- `things-mac/SKILL.md`
- `node-connect/SKILL.md`
- `xurl/SKILL.md`
- `openhue/SKILL.md`
- `gifgrep/SKILL.md`
- `weather/SKILL.md`
- `skill-creator/scripts/package_skill.py`
- `skill-creator/scripts/test_quick_validate.py`
- `skill-creator/scripts/init_skill.py`
- `skill-creator/scripts/quick_validate.py`
- `skill-creator/scripts/test_package_skill.py`
- `1password/references/get-started.md`
- `1password/references/cli-examples.md`
- `model-usage/scripts/test_model_usage.py`
- `model-usage/scripts/model_usage.py`
- `model-usage/references/codexbar-cli.md`
- `openai-whisper-api/scripts/transcribe.sh`
- `sherpa-onnx-tts/bin/sherpa-onnx-tts`
- `taskflow/examples/inbox-triage.lobster`
- `taskflow/examples/pr-intake.lobster`
- `video-frames/scripts/frame.sh`
- `himalaya/references/message-composition.md`
- `himalaya/references/configuration.md`
- `tmux/scripts/find-sessions.sh`
- `tmux/scripts/wait-for-text.sh`