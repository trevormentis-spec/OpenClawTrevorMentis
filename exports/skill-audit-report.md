# 🔒 Daily Skill Security Audit Report
**Date:** 2026-05-11 00:01 UTC

## Executive Summary

- **Skills Scanned:** 80
- **Approved:** 62
- **Caution (minor issues):** 1
- **Rejected:** 16
- **Errors:** 1
- **Total Findings:** 37
- **🔴 Critical:** 34
- **🟠 High:** 2

### ⚠️ Critical Alerts

- **api-gateway** — Found 1 critical issue(s): credential_paths
- **gmail** — Found 1 critical issue(s): credential_paths
- **gog** — Found 2 critical issue(s): credential_paths
- **skill-scanner** — Found 8 critical issue(s): crypto_miner, credential_paths, systemd_modify, base64_decode_exec, reverse_shell
- **stripe** — Found 1 critical issue(s): credential_paths
- **video-translation** — Found 1 critical issue(s): credential_paths
- **whatsapp-business** — Found 1 critical issue(s): credential_paths
- **1password** — Found 1 critical issue(s): credential_paths
- **bear-notes** — Found 7 critical issue(s): credential_paths
- **camsnap** — Found 1 critical issue(s): credential_paths
- **eightctl** — Found 1 critical issue(s): credential_paths
- **himalaya** — Found 3 critical issue(s): credential_paths
- **model-usage** — Found 1 critical issue(s): credential_paths
- **notion** — Found 3 critical issue(s): credential_paths
- **oracle** — Found 1 critical issue(s): credential_paths
- **spotify-player** — Found 1 critical issue(s): credential_paths

## Detailed Skill Reports

### 🔴 api-gateway
**Path:** `/home/ubuntu/.openclaw/skills/api-gateway`
**Verdict:** `REJECT` — Found 1 critical issue(s): credential_paths

- **Version:** 1.0 | **Author:** maton | **Files:** 1 | **Scripts:** 0 | **Lines:** 639

**1 finding(s):**

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 539
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `'Authorization': `Bearer ${process.env.MATON_API_KEY}``

---

### 🔴 gmail
**Path:** `/home/ubuntu/.openclaw/skills/gmail`
**Verdict:** `REJECT` — Found 1 critical issue(s): credential_paths

- **Version:** 1.0 | **Author:** maton | **Files:** 1 | **Scripts:** 0 | **Lines:** 340

**1 finding(s):**

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 267
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `'Authorization': `Bearer ${process.env.MATON_API_KEY}``

---

### 🔴 gog
**Path:** `/home/ubuntu/.openclaw/skills/gog-myclaw`
**Verdict:** `REJECT` — Found 2 critical issue(s): credential_paths

- **Version:** unknown | **Author:** unknown | **Files:** 4 | **Scripts:** 1 | **Lines:** 90

**3 finding(s):**

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 23
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `3. Once they provide the `credentials.json` content, save it to `~/.config/gogcli/credentials.json`.`

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 24
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `4. Run: `gog auth credentials set ~/.config/gogcli/credentials.json``

  - 🟡 **http_post_external** (medium) — `config/exchange.py` line 16
    - HTTP POST to external endpoint - could exfiltrate data
    - _Recommendation:_ Verify destination URL is expected and documented
    - Code: `response = requests.post('https://oauth2.googleapis.com/token', data=data)`

---

### 🔴 skill-scanner
**Path:** `/home/ubuntu/.openclaw/skills/skill-scanner`
**Verdict:** `REJECT` — Found 8 critical issue(s): crypto_miner, credential_paths, systemd_modify, base64_decode_exec, reverse_shell

- **Version:** unknown | **Author:** unknown | **Files:** 6 | **Scripts:** 2 | **Lines:** 1091

**9 finding(s):**

  - 🔴 **credential_paths** (critical) — `README.md` line 155
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `- Credential path access (~/.ssh, ~/.aws, /etc/passwd)`

  - 🔴 **crypto_miner** (critical) — `README.md` line 9
    - Cryptocurrency mining indicators
    - _Recommendation:_ REJECT - this is cryptojacking malware
    - Code: `- Catches **crypto-mining** indicators (xmrig, mining pools, wallet addresses)`

  - 🔴 **crypto_miner** (critical) — `README.md` line 158
    - Cryptocurrency mining indicators
    - _Recommendation:_ REJECT - this is cryptojacking malware
    - Code: `- Crypto miners (xmrig, ethminer, stratum+tcp)`

  - 🔴 **credential_paths** (critical) — `skill_scanner.py` line 101
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `"pattern": r"~/\.ssh|~/\.aws|~/\.config|/etc/passwd|\.env\b|\.credentials|keychain",`

  - 🟠 **crontab_modify** (high) — `skill_scanner.py` line 118
    - Modifies system scheduled tasks
    - _Recommendation:_ Skills should use Clawdbot cron, not system crontab
    - Code: `"pattern": r"crontab\s+-|/etc/cron|schtasks\s+/create",`

  - 🔴 **systemd_modify** (critical) — `skill_scanner.py` line 126
    - Creates system services for persistence
    - _Recommendation:_ REJECT - skills should not create system services
    - Code: `"pattern": r"systemctl\s+enable|systemctl\s+start|/etc/systemd|launchctl\s+load",`

  - 🔴 **crypto_miner** (critical) — `skill_scanner.py` line 135
    - Cryptocurrency mining indicators
    - _Recommendation:_ REJECT - this is cryptojacking malware
    - Code: `"pattern": r"xmrig|ethminer|cpuminer|cgminer|stratum\+tcp|mining.*pool|hashrate",`

  - 🔴 **reverse_shell** (critical) — `skill_scanner.py` line 161
    - Reverse shell pattern detected
    - _Recommendation:_ REJECT - this is a backdoor
    - Code: `"pattern": r"/dev/tcp/|nc\s+-e|bash\s+-i\s+>&|python.*pty\.spawn",`

  - 🔴 **base64_decode_exec** (critical) — `skill_scanner.py` line 170
    - Decodes and executes base64 - classic obfuscation
    - _Recommendation:_ REJECT - likely hiding malicious code
    - Code: `"pattern": r"base64\.b64decode.*exec|atob.*eval",`

---

### 🔴 stripe
**Path:** `/home/ubuntu/.openclaw/skills/stripe-api`
**Verdict:** `REJECT` — Found 1 critical issue(s): credential_paths

- **Version:** 1.0 | **Author:** maton | **Files:** 1 | **Scripts:** 0 | **Lines:** 855

**1 finding(s):**

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 778
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `'Authorization': `Bearer ${process.env.MATON_API_KEY}``

---

### 🔴 video-translation
**Path:** `/home/ubuntu/.agents/skills/video-translation`
**Verdict:** `REJECT` — Found 1 critical issue(s): credential_paths

- **Version:** unknown | **Author:** unknown | **Files:** 3 | **Scripts:** 2 | **Lines:** 219

**1 finding(s):**

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 90
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `- `NOIZ_API_KEY` configured for the Noiz backend. If it is not set, first guide the user to get an API key from `https:/`

---

### 🔴 whatsapp-business
**Path:** `/home/ubuntu/.openclaw/skills/whatsapp-business`
**Verdict:** `REJECT` — Found 1 critical issue(s): credential_paths

- **Version:** 1.0 | **Author:** maton | **Files:** 1 | **Scripts:** 0 | **Lines:** 637

**1 finding(s):**

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 494
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `'Authorization': `Bearer ${process.env.MATON_API_KEY}`,`

---

### 🔴 1password
**Path:** `/usr/lib/node_modules/openclaw/skills/1password`
**Verdict:** `REJECT` — Found 1 critical issue(s): credential_paths

- **Version:** unknown | **Author:** unknown | **Files:** 3 | **Scripts:** 0 | **Lines:** 119

**1 finding(s):**

  - 🔴 **credential_paths** (critical) — `references/cli-examples.md` line 19
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `- `op run --env-file="./.env" -- printenv DB_PASSWORD``

---

### 🔴 bear-notes
**Path:** `/usr/lib/node_modules/openclaw/skills/bear-notes`
**Verdict:** `REJECT` — Found 7 critical issue(s): credential_paths

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 108

**7 finding(s):**

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 33
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `- For some operations (add-text, tags, open-note --selected), a Bear app token (stored in `~/.config/grizzly/token`)`

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 40
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `2. Save it: `echo "YOUR_TOKEN" > ~/.config/grizzly/token``

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 60
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `echo "Additional content" | grizzly add-text --id "NOTE_ID" --mode append --token-file ~/.config/grizzly/token`

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 66
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `grizzly tags --enable-callback --json --token-file ~/.config/grizzly/token`

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 92
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `4. `~/.config/grizzly/config.toml``

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 94
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `Example `~/.config/grizzly/config.toml`:`

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 97
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `token_file = "~/.config/grizzly/token"`

---

### 🔴 camsnap
**Path:** `/usr/lib/node_modules/openclaw/skills/camsnap`
**Verdict:** `REJECT` — Found 1 critical issue(s): credential_paths

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 46

**1 finding(s):**

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 31
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `- Config file: `~/.config/camsnap/config.yaml``

---

### 🔴 eightctl
**Path:** `/usr/lib/node_modules/openclaw/skills/eightctl`
**Verdict:** `REJECT` — Found 1 critical issue(s): credential_paths

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 51

**1 finding(s):**

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 31
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `- Config: `~/.config/eightctl/config.yaml``

---

### 🔴 himalaya
**Path:** `/usr/lib/node_modules/openclaw/skills/himalaya`
**Verdict:** `REJECT` — Found 3 critical issue(s): credential_paths

- **Version:** unknown | **Author:** unknown | **Files:** 3 | **Scripts:** 0 | **Lines:** 643

**3 finding(s):**

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 37
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `2. A configuration file at `~/.config/himalaya/config.toml``

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 48
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `Or create `~/.config/himalaya/config.toml` manually:`

  - 🔴 **credential_paths** (critical) — `references/configuration.md` line 3
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `Configuration file location: `~/.config/himalaya/config.toml``

---

### 🔴 model-usage
**Path:** `/usr/lib/node_modules/openclaw/skills/model-usage`
**Verdict:** `REJECT` — Found 1 critical issue(s): credential_paths

- **Version:** unknown | **Author:** unknown | **Files:** 4 | **Scripts:** 2 | **Lines:** 465

**1 finding(s):**

  - 🔴 **credential_paths** (critical) — `references/codexbar-cli.md` line 32
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `- Claude: ~/.config/claude/projects/**/\*.jsonl or ~/.claude/projects/**/\*.jsonl`

---

### 🔴 notion
**Path:** `/usr/lib/node_modules/openclaw/skills/notion`
**Verdict:** `REJECT` — Found 3 critical issue(s): credential_paths

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 175

**3 finding(s):**

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 23
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `mkdir -p ~/.config/notion`

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 24
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `echo "ntn_your_key_here" > ~/.config/notion/api_key`

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 34
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `NOTION_KEY=$(cat ~/.config/notion/api_key)`

---

### 🔴 oracle
**Path:** `/usr/lib/node_modules/openclaw/skills/oracle`
**Verdict:** `REJECT` — Found 1 critical issue(s): credential_paths

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 126

**1 finding(s):**

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 115
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `- Don’t attach secrets by default (`.env`, key files, auth tokens). Redact aggressively; share only what’s required.`

---

### 🔴 spotify-player
**Path:** `/usr/lib/node_modules/openclaw/skills/spotify-player`
**Verdict:** `REJECT` — Found 1 critical issue(s): credential_paths

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 65

**1 finding(s):**

  - 🔴 **credential_paths** (critical) — `SKILL.md` line 62
    - Accesses sensitive credential locations
    - _Recommendation:_ REJECT unless explicitly justified
    - Code: `- Config folder: `~/.config/spotify-player` (e.g., `app.toml`).`

---

### ⚠️ trevor-methodology
**Path:** `/home/ubuntu/.openclaw/skills/trevor-methodology`
**Verdict:** `CAUTION` — Found 1 high-severity issue(s): eval_exec

- **Version:** unknown | **Author:** unknown | **Files:** 26 | **Scripts:** 3 | **Lines:** 5281

**1 finding(s):**

  - 🟠 **eval_exec** (high) — `pipeline/docx-js-template.js` line 37
    - Dynamic code execution - could run arbitrary code
    - _Recommendation:_ Verify input is sanitized, not user-controlled
    - Code: `const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);`

---

### ❌ unknown
**Path:** `/home/ubuntu/.openclaw/skills/OpenClawTrevorMentis`
**Verdict:** `ERROR` — 

_Error: Command '['/usr/bin/python3', '/home/ubuntu/.openclaw/skills/skill-scanner/skill_scanner.py', '/home/ubuntu/.openclaw/skills/OpenClawTrevorMentis', '--json']' timed out after 60 seconds_

### ✅ answeroverflow
**Path:** `/home/ubuntu/.openclaw/skills/answeroverflow`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 89

*No issues detected.*

---

### ✅ claude-code
**Path:** `/home/ubuntu/.openclaw/skills/claude-code`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 4 | **Scripts:** 0 | **Lines:** 85

*No issues detected.*

---

### ✅ unknown
**Path:** `/home/ubuntu/.openclaw/skills/daily_intel`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 1

*No issues detected.*

---

### ✅ find-skills
**Path:** `/home/ubuntu/.openclaw/skills/find-skills`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 134

*No issues detected.*

---

### ✅ huggingface-hub
**Path:** `/home/ubuntu/.openclaw/skills/huggingface-hub`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 36

*No issues detected.*

---

### ✅ humanizer
**Path:** `/home/ubuntu/.openclaw/skills/humanizer`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** 2.1.1 | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 438

*No issues detected.*

---

### ✅ maps
**Path:** `/home/ubuntu/.openclaw/skills/maps-new`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 37

*No issues detected.*

---

### ✅ nano-pdf
**Path:** `/home/ubuntu/.openclaw/skills/nano-pdf`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 21

*No issues detected.*

---

### ✅ Network Analysis
**Path:** `/home/ubuntu/.agents/skills/network-analysis`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 3 | **Scripts:** 2 | **Lines:** 313

*No issues detected.*

---

### ✅ ocr-and-documents
**Path:** `/home/ubuntu/.openclaw/skills/ocr-docu`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 4 | **Scripts:** 0 | **Lines:** 89

*No issues detected.*

---

### ✅ self-improvement
**Path:** `/home/ubuntu/.openclaw/skills/self-improving-agent`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 648

*No issues detected.*

---

### ✅ stock-market-pro
**Path:** `/home/ubuntu/.openclaw/skills/stock-market-pro`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 135

*No issues detected.*

---

### ✅ timeline-chart
**Path:** `/home/ubuntu/.openclaw/skills/timeline-chart`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 5 | **Scripts:** 1 | **Lines:** 340

*No issues detected.*

---

### ✅ video-frames
**Path:** `/home/ubuntu/.openclaw/skills/video-frames`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 30

*No issues detected.*

---

### ✅ wacli
**Path:** `/home/ubuntu/.openclaw/skills/wacli`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 73

*No issues detected.*

---

### ✅ web-search-plus
**Path:** `/home/ubuntu/.openclaw/skills/web-searchplus`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 37

*No issues detected.*

---

### ✅ xurl
**Path:** `/home/ubuntu/.openclaw/skills/xurl`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 462

*No issues detected.*

---

### ✅ youtube-content
**Path:** `/home/ubuntu/.openclaw/skills/youtube-content`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 35

*No issues detected.*

---

### ✅ apple-notes
**Path:** `/usr/lib/node_modules/openclaw/skills/apple-notes`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 78

*No issues detected.*

---

### ✅ apple-reminders
**Path:** `/usr/lib/node_modules/openclaw/skills/apple-reminders`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 119

*No issues detected.*

---

### ✅ blogwatcher
**Path:** `/usr/lib/node_modules/openclaw/skills/blogwatcher`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 70

*No issues detected.*

---

### ✅ blucli
**Path:** `/usr/lib/node_modules/openclaw/skills/blucli`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 48

*No issues detected.*

---

### ✅ bluebubbles
**Path:** `/usr/lib/node_modules/openclaw/skills/bluebubbles`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 132

*No issues detected.*

---

### ✅ unknown
**Path:** `/usr/lib/node_modules/openclaw/skills/canvas`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 200

*No issues detected.*

---

### ✅ clawhub
**Path:** `/usr/lib/node_modules/openclaw/skills/clawhub`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 78

*No issues detected.*

---

### ✅ coding-agent
**Path:** `/usr/lib/node_modules/openclaw/skills/coding-agent`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 366

*No issues detected.*

---

### ✅ discord
**Path:** `/usr/lib/node_modules/openclaw/skills/discord`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 198

*No issues detected.*

---

### ✅ gemini
**Path:** `/usr/lib/node_modules/openclaw/skills/gemini`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 44

*No issues detected.*

---

### ✅ gh-issues
**Path:** `/usr/lib/node_modules/openclaw/skills/gh-issues`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 886

*No issues detected.*

---

### ✅ gifgrep
**Path:** `/usr/lib/node_modules/openclaw/skills/gifgrep`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 86

*No issues detected.*

---

### ✅ github
**Path:** `/usr/lib/node_modules/openclaw/skills/github`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 164

*No issues detected.*

---

### ✅ gog
**Path:** `/usr/lib/node_modules/openclaw/skills/gog`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 117

*No issues detected.*

---

### ✅ goplaces
**Path:** `/usr/lib/node_modules/openclaw/skills/goplaces`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 53

*No issues detected.*

---

### ✅ healthcheck
**Path:** `/usr/lib/node_modules/openclaw/skills/healthcheck`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 246

*No issues detected.*

---

### ✅ imsg
**Path:** `/usr/lib/node_modules/openclaw/skills/imsg`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 123

*No issues detected.*

---

### ✅ mcporter
**Path:** `/usr/lib/node_modules/openclaw/skills/mcporter`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 62

*No issues detected.*

---

### ✅ nano-pdf
**Path:** `/usr/lib/node_modules/openclaw/skills/nano-pdf`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 39

*No issues detected.*

---

### ✅ node-connect
**Path:** `/usr/lib/node_modules/openclaw/skills/node-connect`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 143

*No issues detected.*

---

### ✅ obsidian
**Path:** `/usr/lib/node_modules/openclaw/skills/obsidian`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 82

*No issues detected.*

---

### ✅ openai-whisper
**Path:** `/usr/lib/node_modules/openclaw/skills/openai-whisper`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 39

*No issues detected.*

---

### ✅ openai-whisper-api
**Path:** `/usr/lib/node_modules/openclaw/skills/openai-whisper-api`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 2 | **Scripts:** 1 | **Lines:** 152

*No issues detected.*

---

### ✅ openhue
**Path:** `/usr/lib/node_modules/openclaw/skills/openhue`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 113

*No issues detected.*

---

### ✅ ordercli
**Path:** `/usr/lib/node_modules/openclaw/skills/ordercli`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 79

*No issues detected.*

---

### ✅ peekaboo
**Path:** `/usr/lib/node_modules/openclaw/skills/peekaboo`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 191

*No issues detected.*

---

### ✅ sag
**Path:** `/usr/lib/node_modules/openclaw/skills/sag`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 88

*No issues detected.*

---

### ✅ session-logs
**Path:** `/usr/lib/node_modules/openclaw/skills/session-logs`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 152

*No issues detected.*

---

### ✅ sherpa-onnx-tts
**Path:** `/usr/lib/node_modules/openclaw/skills/sherpa-onnx-tts`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 2 | **Scripts:** 0 | **Lines:** 289

*No issues detected.*

---

### ✅ skill-creator
**Path:** `/usr/lib/node_modules/openclaw/skills/skill-creator`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 7 | **Scripts:** 5 | **Lines:** 1490

*No issues detected.*

---

### ✅ slack
**Path:** `/usr/lib/node_modules/openclaw/skills/slack`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 145

*No issues detected.*

---

### ✅ songsee
**Path:** `/usr/lib/node_modules/openclaw/skills/songsee`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 50

*No issues detected.*

---

### ✅ sonoscli
**Path:** `/usr/lib/node_modules/openclaw/skills/sonoscli`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 66

*No issues detected.*

---

### ✅ summarize
**Path:** `/usr/lib/node_modules/openclaw/skills/summarize`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 88

*No issues detected.*

---

### ✅ taskflow
**Path:** `/usr/lib/node_modules/openclaw/skills/taskflow`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 3 | **Scripts:** 0 | **Lines:** 217

*No issues detected.*

---

### ✅ taskflow-inbox-triage
**Path:** `/usr/lib/node_modules/openclaw/skills/taskflow-inbox-triage`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 120

*No issues detected.*

---

### ✅ things-mac
**Path:** `/usr/lib/node_modules/openclaw/skills/things-mac`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 87

*No issues detected.*

---

### ✅ tmux
**Path:** `/usr/lib/node_modules/openclaw/skills/tmux`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 3 | **Scripts:** 2 | **Lines:** 368

*No issues detected.*

---

### ✅ trello
**Path:** `/usr/lib/node_modules/openclaw/skills/trello`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 109

*No issues detected.*

---

### ✅ video-frames
**Path:** `/usr/lib/node_modules/openclaw/skills/video-frames`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 2 | **Scripts:** 1 | **Lines:** 129

*No issues detected.*

---

### ✅ voice-call
**Path:** `/usr/lib/node_modules/openclaw/skills/voice-call`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 46

*No issues detected.*

---

### ✅ wacli
**Path:** `/usr/lib/node_modules/openclaw/skills/wacli`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 73

*No issues detected.*

---

### ✅ weather
**Path:** `/usr/lib/node_modules/openclaw/skills/weather`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 130

*No issues detected.*

---

### ✅ xurl
**Path:** `/usr/lib/node_modules/openclaw/skills/xurl`
**Verdict:** `APPROVED` — No critical or high-severity issues detected

- **Version:** unknown | **Author:** unknown | **Files:** 1 | **Scripts:** 0 | **Lines:** 462

*No issues detected.*

---

## Scan Summary

Scan completed at 2026-05-11 00:01 UTC.
- 80 skills audited
- 37 total findings (34 critical, 2 high)
