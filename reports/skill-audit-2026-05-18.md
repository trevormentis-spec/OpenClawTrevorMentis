# Skill Security Review - unknown unknown

**Scan Date:** 2026-05-18T00:02:08.773926
**Skill Path:** `/home/ubuntu/.openclaw/skills`

## Verdict

**REJECT** - Found 70 critical issue(s): base64_decode_exec, credential_paths, crypto_miner, systemd_modify, reverse_shell

## Metadata

- **Name:** unknown
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** False
- **Files:** 270
- **Scripts:** 58
- **Total Lines:** 43933

## Findings

Found **105** potential issue(s):

### credential_paths (critical)

- **File:** `api-gateway/SKILL.md` line 539
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}``

### credential_paths (critical)

- **File:** `gmail/SKILL.md` line 267
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}``

### credential_paths (critical)

- **File:** `gog-myclaw/SKILL.md` line 23
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `3. Once they provide the `credentials.json` content, save it to `~/.config/gogcli/credentials.json`.`

### credential_paths (critical)

- **File:** `gog-myclaw/SKILL.md` line 24
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `4. Run: `gog auth credentials set ~/.config/gogcli/credentials.json``

### credential_paths (critical)

- **File:** `skill-scanner/README.md` line 155
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- Credential path access (~/.ssh, ~/.aws, /etc/passwd)`

### crypto_miner (critical)

- **File:** `skill-scanner/README.md` line 9
- **Description:** Cryptocurrency mining indicators
- **Recommendation:** REJECT - this is cryptojacking malware
- **Code:** `- Catches **crypto-mining** indicators (xmrig, mining pools, wallet addresses)`

### crypto_miner (critical)

- **File:** `skill-scanner/README.md` line 158
- **Description:** Cryptocurrency mining indicators
- **Recommendation:** REJECT - this is cryptojacking malware
- **Code:** `- Crypto miners (xmrig, ethminer, stratum+tcp)`

### credential_paths (critical)

- **File:** `skill-scanner/skill_scanner.py` line 101
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `"pattern": r"~/\.ssh|~/\.aws|~/\.config|/etc/passwd|\.env\b|\.credentials|keychain",`

### crontab_modify (high)

- **File:** `skill-scanner/skill_scanner.py` line 118
- **Description:** Modifies system scheduled tasks
- **Recommendation:** Skills should use Clawdbot cron, not system crontab
- **Code:** `"pattern": r"crontab\s+-|/etc/cron|schtasks\s+/create",`

### systemd_modify (critical)

- **File:** `skill-scanner/skill_scanner.py` line 126
- **Description:** Creates system services for persistence
- **Recommendation:** REJECT - skills should not create system services
- **Code:** `"pattern": r"systemctl\s+enable|systemctl\s+start|/etc/systemd|launchctl\s+load",`

### crypto_miner (critical)

- **File:** `skill-scanner/skill_scanner.py` line 135
- **Description:** Cryptocurrency mining indicators
- **Recommendation:** REJECT - this is cryptojacking malware
- **Code:** `"pattern": r"xmrig|ethminer|cpuminer|cgminer|stratum\+tcp|mining.*pool|hashrate",`

### reverse_shell (critical)

- **File:** `skill-scanner/skill_scanner.py` line 161
- **Description:** Reverse shell pattern detected
- **Recommendation:** REJECT - this is a backdoor
- **Code:** `"pattern": r"/dev/tcp/|nc\s+-e|bash\s+-i\s+>&|python.*pty\.spawn",`

### base64_decode_exec (critical)

- **File:** `skill-scanner/skill_scanner.py` line 170
- **Description:** Decodes and executes base64 - classic obfuscation
- **Recommendation:** REJECT - likely hiding malicious code
- **Code:** `"pattern": r"base64\.b64decode.*exec|atob.*eval",`

### credential_paths (critical)

- **File:** `stripe-api/SKILL.md` line 778
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}``

### credential_paths (critical)

- **File:** `whatsapp-business/SKILL.md` line 494
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}`,`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/audit_skills.py` line 6
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `The raw scanner regex-matches strings like `~/.config` and `Bearer ${...}` as`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/consolidated_audit_report.md` line 21
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `2. **Credential Paths:** Multiple skills (`gmail`, `gog-myclaw`, `api-gateway`, `stripe-api`, `whatsapp-business`) were flagged for referencing `~/.config` or `Bearer` tokens in their documentation (``

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/consolidated_audit_report.md` line 33
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `2. **Config Locations:** Skills such as `eightctl`, `camsnap`, and `spotify-player` were flagged for documentation referencing `~/.config` directories.`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/consolidated_audit_report.md` line 39
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `2. **Audit Config Access:** Ensure that skills accessing `~/.config` are only doing so for their own legitimate configuration and not attempting to exfiltrate other service tokens.`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/consolidated_audit_report.md` line 40
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `3. **Ignore Documentation Flags:** Findings inside `SKILL.md` files that merely describe setup procedures (e.g., "save your token to ~/.config/...") can generally be considered low-risk documentation `

### crypto_miner (critical)

- **File:** `OpenClawTrevorMentis/skill_audit_report.json` line 144
- **Description:** Cryptocurrency mining indicators
- **Recommendation:** REJECT - this is cryptojacking malware
- **Code:** `"line_content": "- Catches **crypto-mining** indicators (xmrig, mining pools, wallet addresses)",`

### crypto_miner (critical)

- **File:** `OpenClawTrevorMentis/skill_audit_report.json` line 153
- **Description:** Cryptocurrency mining indicators
- **Recommendation:** REJECT - this is cryptojacking malware
- **Code:** `"line_content": "- Crypto miners (xmrig, ethminer, stratum+tcp)",`

### crypto_miner (critical)

- **File:** `OpenClawTrevorMentis/skill_audit_report.json` line 189
- **Description:** Cryptocurrency mining indicators
- **Recommendation:** REJECT - this is cryptojacking malware
- **Code:** `"line_content": "\"pattern\": r\"xmrig|ethminer|cpuminer|cgminer|stratum\\+tcp|mining.*pool|hashrate\",",`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/system_skills_audit.md` line 29
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `- Config: `~/.config/eightctl/config.yaml```

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/system_skills_audit.md` line 36
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `- Config file: `~/.config/camsnap/config.yaml```

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/system_skills_audit.md` line 43
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `- Config folder: `~/.config/spotify-player` (e.g., `app.toml`).``

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/system_skills_audit.md` line 50
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `- For some operations (add-text, tags, open-note --selected), a Bear app token (stored in `~/.config/grizzly/token`)``

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/system_skills_audit.md` line 57
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `2. Save it: `echo "YOUR_TOKEN" > ~/.config/grizzly/token```

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/system_skills_audit.md` line 64
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `echo "Additional content" | grizzly add-text --id "NOTE_ID" --mode append --token-file ~/.config/grizzly/token``

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/system_skills_audit.md` line 71
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `grizzly tags --enable-callback --json --token-file ~/.config/grizzly/token``

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/system_skills_audit.md` line 78
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `4. `~/.config/grizzly/config.toml```

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/system_skills_audit.md` line 85
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `Example `~/.config/grizzly/config.toml`:``

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/system_skills_audit.md` line 92
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `token_file = "~/.config/grizzly/token"``

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/system_skills_audit.md` line 99
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `2. A configuration file at `~/.config/himalaya/config.toml```

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/system_skills_audit.md` line 106
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `Or create `~/.config/himalaya/config.toml` manually:``

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/system_skills_audit.md` line 113
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `- Don’t attach secrets by default (`.env`, key files, auth tokens). Redact aggressively; share only what’s required.``

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/system_skills_audit.md` line 120
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `mkdir -p ~/.config/notion``

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/system_skills_audit.md` line 127
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `echo "ntn_your_key_here" > ~/.config/notion/api_key``

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/system_skills_audit.md` line 134
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `NOTION_KEY=$(cat ~/.config/notion/api_key)``

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/system_skills_audit.md` line 141
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `- `op run --env-file="./.env" -- printenv DB_PASSWORD```

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/system_skills_audit.md` line 148
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `- Claude: ~/.config/claude/projects/**/\*.jsonl or ~/.claude/projects/**/\*.jsonl``

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/system_skills_audit.md` line 155
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `Configuration file location: `~/.config/himalaya/config.toml```

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/user_skills_audit.md` line 29
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}```

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/user_skills_audit.md` line 36
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `3. Once they provide the `credentials.json` content, save it to `~/.config/gogcli/credentials.json`.``

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/user_skills_audit.md` line 43
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `4. Run: `gog auth credentials set ~/.config/gogcli/credentials.json```

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/user_skills_audit.md` line 50
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}```

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/user_skills_audit.md` line 57
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}```

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/user_skills_audit.md` line 64
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}`,``

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/user_skills_audit.md` line 71
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `- Credential path access (~/.ssh, ~/.aws, /etc/passwd)``

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/user_skills_audit.md` line 92
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `"pattern": r"~/\.ssh|~/\.aws|~/\.config|/etc/passwd|\.env\b|\.credentials|keychain",``

### crypto_miner (critical)

- **File:** `OpenClawTrevorMentis/user_skills_audit.md` line 78
- **Description:** Cryptocurrency mining indicators
- **Recommendation:** REJECT - this is cryptojacking malware
- **Code:** `- **Code:** `- Catches **crypto-mining** indicators (xmrig, mining pools, wallet addresses)``

### crypto_miner (critical)

- **File:** `OpenClawTrevorMentis/user_skills_audit.md` line 85
- **Description:** Cryptocurrency mining indicators
- **Recommendation:** REJECT - this is cryptojacking malware
- **Code:** `- **Code:** `- Crypto miners (xmrig, ethminer, stratum+tcp)``

### crypto_miner (critical)

- **File:** `OpenClawTrevorMentis/user_skills_audit.md` line 113
- **Description:** Cryptocurrency mining indicators
- **Recommendation:** REJECT - this is cryptojacking malware
- **Code:** `- **Code:** `"pattern": r"xmrig|ethminer|cpuminer|cgminer|stratum\+tcp|mining.*pool|hashrate",``

### http_post_external (medium)

- **File:** `gog-myclaw/config/exchange.py` line 16
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `response = requests.post('https://oauth2.googleapis.com/token', data=data)`

### eval_exec (high)

- **File:** `trevor-methodology/pipeline/docx-js-template.js` line 37
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/brain/README.md` line 61
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- Don't index secrets. The indexer skips `.env`, `*.key`, `*.pem`,`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/brain/scripts/brain.py` line 62
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `re.compile(r"\.env$"),`

### http_post_external (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/deepseek_client.py` line 60
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `r = requests.post(`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/trevor_config.py` line 54
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `_WORKSPACE_ENV = os.environ.get("TREVOR_WORKSPACE", "")`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/trevor_config.py` line 63
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `EXPORTS_DIR = Path(os.environ.get("TREVOR_EXPORTS", str(WORKSPACE / "exports")))`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/trevor_config.py` line 64
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `DATA_DIR = Path(os.environ.get("TREVOR_DATA_DIR", str(WORKSPACE / "tmp" / "data")))`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/trevor_config.py` line 65
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `FONTS_DIR = Path(os.environ.get("TREVOR_FONTS_DIR", str(_SKILL_ROOT / "fonts")))`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/trevor_config.py` line 80
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/trevor_config.py` line 81
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/trevor_config.py` line 82
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/trevor_config.py` line 83
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `MATON_API_KEY = os.environ.get("MATON_API_KEY", "")`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/trevor_config.py` line 86
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `DEEPSEEK_TIMEOUT_SECONDS = int(os.environ.get("DEEPSEEK_TIMEOUT", "120"))`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/trevor_config.py` line 87
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `DEEPSEEK_MAX_RETRIES = int(os.environ.get("DEEPSEEK_MAX_RETRIES", "2"))`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/trevor_log.py` line 32
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `_LOG_DIR = Path(os.environ.get("TREVOR_EXPORTS", Path.home() / ".openclaw" / "workspace" / "exports")) / "logs"`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/trevor_fonts.py` line 38
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `FONTS_DIR = Path(os.environ.get("TREVOR_FONTS_DIR", str(_SKILL_ROOT / "fonts")))`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/agentmail/scripts/check_inbox.py` line 83
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `api_key = os.getenv('AGENTMAIL_API_KEY')`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/agentmail/scripts/send_email.py` line 46
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `api_key = os.getenv('AGENTMAIL_API_KEY')`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/agentmail/scripts/setup_webhook.py` line 51
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `api_key = os.getenv('AGENTMAIL_API_KEY')`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/skills/chartgen-ai/tools/chartgen_api.js` line 25
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `const BASE_URL = process.env.CHARTGEN_API_URL || "https://chartgen.ai";`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/skills/chartgen-ai/tools/chartgen_api.js` line 40
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `if (process.env.CHARTGEN_API_KEY) return process.env.CHARTGEN_API_KEY;`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/skills/chartgen-ai/tools/chartgen_api.js` line 44
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `process.env.OPENCLAW_STATE_DIR`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/skills/chartgen-ai/tools/chartgen_api.js` line 45
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `? path.join(process.env.OPENCLAW_STATE_DIR, "skills", "chartgen", "config.json")`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/skills/chartgen-ai/tools/chartgen_api.js` line 74
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `const stateDir = process.env.OPENCLAW_STATE_DIR;`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/pdf-report/scripts/render_pdf.py` line 17
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `env_root = os.environ.get("OPENCLAW_WORKSPACE")`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/cron/run_daily.py` line 165
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `maton_key = os.environ.get("MATON_API_KEY", "")`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/cron/run_daily.py` line 173
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `moltbook_script = Path(os.environ.get("WORKSPACE", str(Path.home() / '.openclaw' / 'workspace'))) / 'scripts' / 'moltbook-post-brief.sh'`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/cron/run_daily.py` line 174
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `if moltbook_script.exists() and os.environ.get("MOLTBOOK_API_KEY", ""):`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/cron/run_daily.py` line 179
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `genviral_script = Path(os.environ.get("WORKSPACE", str(Path.home() / '.openclaw' / 'workspace'))) / 'scripts' / 'genviral-post-brief.sh'`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/cron/run_daily.py` line 180
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `if genviral_script.exists() and os.environ.get("GENVIRAL_API_KEY", ""):`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/cron/run_daily.py` line 19
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `# Load environment from workspace .env (cron may not have it in env)`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/cron/run_daily.py` line 21
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `WORKSPACE_ENV = WORKSPACE / '.env'`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/scripts/generate_assessments.py` line 134
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `adaptation_flag = os.environ.get("TREVOR_ADAPTATION_FLAG", "")`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/scripts/_email_brief.py` line 16
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `maton_key = os.environ.get("MATON_API_KEY", "")`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/scripts/_email_brief.py` line 19
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `# Try reading from workspace .env`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/scripts/_email_brief.py` line 21
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `env_path = str(WORKSPACE / ".env")`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/scripts/_fetch_intel_emails.py` line 106
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `key = os.environ.get("MATON_API_KEY", "")`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/scripts/_fetch_intel_emails.py` line 105
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `"""Read MATON_API_KEY from env or workspace .env."""`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/scripts/_fetch_intel_emails.py` line 108
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `env_path = os.path.expanduser("~/.openclaw/workspace/.env")`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/scripts/improvement_daemon.py` line 49
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `if not os.environ.get(k):`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/scripts/improvement_daemon.py` line 50
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `os.environ[k] = v`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/scripts/improvement_daemon.py` line 490
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `os.environ["TREVOR_ADAPTATION_FLAG"] = adaptation_flag`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/scripts/improvement_daemon.py` line 29
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `# Load .env for subprocess environment inheritance`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/scripts/improvement_daemon.py` line 32
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `env_path = Path.home() / '.openclaw' / 'workspace' / '.env'`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/scripts/improvement_daemon.py` line 41
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `env_path = Path.home() / '.openclaw' / 'workspace' / '.env'`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/scripts/osint_collection_expansion.py` line 175
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `brave_key = os.environ.get("BRAVE_API_KEY", "")`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/scripts/scrape_creators.py` line 29
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `API_KEY = os.environ.get("SCRAPECREATORS_API_KEY", "mYa56PnRKges2xHchvb4Jx7YND43")`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/scripts/sonar_scout.py` line 76
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `return os.environ.get("OPENROUTER_API_KEY", "")`

### env_scraping (medium)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/scripts/sonar_scout.py` line 216
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `brave_key = os.environ.get("BRAVE_API_KEY", "BSAoi5HoC5F2i5shy0yPcKtqQPtxwbE")`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/scripts/sonar_scout.py` line 70
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `"""Get OpenRouter API key from workspace .env."""`

### credential_paths (critical)

- **File:** `OpenClawTrevorMentis/skills/daily_intel/scripts/sonar_scout.py` line 71
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `env_path = WORKSPACE / ".env"`

## Files Scanned

- `answeroverflow/SKILL.md`
- `api-gateway/SKILL.md`
- `claude-code/README.md`
- `claude-code/SKILL.md`
- `find-skills/SKILL.md`
- `gmail/SKILL.md`
- `gog-myclaw/SKILL.md`
- `gog-myclaw/_meta.json`
- `huggingface-hub/SKILL.md`
- `humanizer/SKILL.md`
- `maps-new/SKILL.md`
- `nano-pdf/SKILL.md`
- `ocr-docu/README.md`
- `ocr-docu/SKILL.md`
- `self-improving-agent/SKILL.md`
- `skill-scanner/README.md`
- `skill-scanner/SKILL.md`
- `skill-scanner/_meta.json`
- `skill-scanner/skill_scanner.py`
- `skill-scanner/streamlit_ui.py`
- `stock-market-pro/SKILL.md`
- `stripe-api/SKILL.md`
- `trevor-methodology/SKILL.md`
- `trevor-methodology/TREVOR-One-Page-Summary.md`
- `trevor-methodology/sanitize.sh`
- `video-frames/SKILL.md`
- `wacli/SKILL.md`
- `web-searchplus/SKILL.md`
- `whatsapp-business/SKILL.md`
- `xurl/SKILL.md`
- `youtube-content/SKILL.md`
- `OpenClawTrevorMentis/IDENTITY.md`
- `OpenClawTrevorMentis/MEMORY.md`
- `OpenClawTrevorMentis/README.md`
- `OpenClawTrevorMentis/SOUL.md`
- `OpenClawTrevorMentis/USER.md`
- `OpenClawTrevorMentis/audit_skills.py`
- `OpenClawTrevorMentis/consolidated_audit_report.md`
- `OpenClawTrevorMentis/skill_audit_report.json`
- `OpenClawTrevorMentis/skill_audit_report.md`
- `OpenClawTrevorMentis/system_skills_audit.md`
- `OpenClawTrevorMentis/user_skills_audit.md`
- `OpenClawTrevorMentis/.gitignore`
- `OpenClawTrevorMentis/AGENTS.md`
- `OpenClawTrevorMentis/HEARTBEAT.md`
- `OpenClawTrevorMentis/ORCHESTRATION.md`
- `OpenClawTrevorMentis/TOOLS.md`
- `timeline-chart/skill.json`
- `timeline-chart/SKILL.md`
- `timeline-chart/template.py`
- `timeline-chart/_meta.json`
- `claude-code/references/safety-notes.md`
- `claude-code/references/session-patterns.md`
- `gog-myclaw/config/credentials.json`
- `gog-myclaw/config/exchange.py`
- `ocr-docu/references/output-schema.md`
- `ocr-docu/references/tooling-matrix.md`
- `trevor-methodology/brands/README.md`
- `trevor-methodology/brands/concentric.json`
- `trevor-methodology/brands/eclipse.json`
- `trevor-methodology/brands/neutral.json`
- `trevor-methodology/brands/nova.json`
- `trevor-methodology/brands/sps-global.json`
- `trevor-methodology/methodology/11-SATs.md`
- `trevor-methodology/methodology/16-sections.md`
- `trevor-methodology/methodology/6-calibrations.md`
- `trevor-methodology/methodology/actor-mapping.md`
- `trevor-methodology/methodology/client-threat-matrix-templates.md`
- `trevor-methodology/methodology/hypothesis-archetypes.md`
- `trevor-methodology/methodology/nato-admiralty.md`
- `trevor-methodology/methodology/quality-gates.md`
- `trevor-methodology/methodology/scenario-triage.md`
- `trevor-methodology/methodology/sherman-kent-bands.md`
- `trevor-methodology/methodology/source-acquisition-guide.md`
- `trevor-methodology/pipeline/docx-js-template.js`
- `trevor-methodology/pipeline/output-format-variants.md`
- `trevor-methodology/pipeline/validate.py`
- `trevor-methodology/verification/phase4-self-test.md`
- `trevor-methodology/verification/phase5-acceptance-demonstrations.md`
- `OpenClawTrevorMentis/.clawhub/lock.json`
- `OpenClawTrevorMentis/.openclaw/model-config-note.md`
- `OpenClawTrevorMentis/.openclaw/workspace-state.json`
- `OpenClawTrevorMentis/analyst/README.md`
- `OpenClawTrevorMentis/brain/README.md`
- `OpenClawTrevorMentis/brain/working-memory.example.json`
- `OpenClawTrevorMentis/memory/2026-03-05.md`
- `OpenClawTrevorMentis/memory/2026-04-25.md`
- `OpenClawTrevorMentis/memory/2026-04-27.md`
- `OpenClawTrevorMentis/memory/heartbeat-state.json`
- `OpenClawTrevorMentis/tasks/quick-test-render.md`
- `OpenClawTrevorMentis/tasks/news_raw.md`
- `OpenClawTrevorMentis/tests/test_config.py`
- `OpenClawTrevorMentis/tests/test_fonts.py`
- `OpenClawTrevorMentis/tests/test_diagnostics.py`
- `OpenClawTrevorMentis/tests/test_memory.py`
- `OpenClawTrevorMentis/analyst/meta/sources.json`
- `OpenClawTrevorMentis/analyst/methodology/README.md`
- `OpenClawTrevorMentis/analyst/playbooks/analytic-workflow.md`
- `OpenClawTrevorMentis/analyst/playbooks/quality-gates.md`
- `OpenClawTrevorMentis/analyst/playbooks/scenario-triage.md`
- `OpenClawTrevorMentis/analyst/playbooks/source-acquisition.md`
- `OpenClawTrevorMentis/analyst/templates/ach-matrix.md`
- `OpenClawTrevorMentis/analyst/templates/analytic-note.md`
- `OpenClawTrevorMentis/analyst/templates/bluf-report.md`
- `OpenClawTrevorMentis/analyst/templates/indicators-and-warnings.md`
- `OpenClawTrevorMentis/analyst/templates/pmesii-pt-scan.md`
- `OpenClawTrevorMentis/analyst/templates/red-team-review.md`
- `OpenClawTrevorMentis/analyst/templates/source-evaluation-matrix.md`
- `OpenClawTrevorMentis/brain/index/.gitkeep`
- `OpenClawTrevorMentis/brain/meta/.gitkeep`
- `OpenClawTrevorMentis/brain/scripts/brain.py`
- `OpenClawTrevorMentis/brain/memory/episodic/.gitkeep`
- `OpenClawTrevorMentis/brain/memory/procedural/.gitkeep`
- `OpenClawTrevorMentis/brain/memory/semantic/.gitkeep`
- `OpenClawTrevorMentis/docs/archive/README.md`
- `OpenClawTrevorMentis/docs/archive/REBUILD_ORCHESTRATION-2026-04-28.md`
- `OpenClawTrevorMentis/memory/.dreams/events.jsonl`
- `OpenClawTrevorMentis/memory/.dreams/short-term-recall.json`
- `OpenClawTrevorMentis/skills/agentmail/SKILL.md`
- `OpenClawTrevorMentis/skills/agentmail/_meta.json`
- `OpenClawTrevorMentis/skills/baoyu-translate/SKILL.md`
- `OpenClawTrevorMentis/skills/baoyu-translate/_meta.json`
- `OpenClawTrevorMentis/skills/bluf-report/SKILL.md`
- `OpenClawTrevorMentis/skills/bluf-report/_meta.json`
- `OpenClawTrevorMentis/skills/chartgen-ai/SKILL.md`
- `OpenClawTrevorMentis/skills/chartgen-ai/_meta.json`
- `OpenClawTrevorMentis/skills/data-analysis/SKILL.md`
- `OpenClawTrevorMentis/skills/data-analysis/_meta.json`
- `OpenClawTrevorMentis/skills/data-analysis/chart-selection.md`
- `OpenClawTrevorMentis/skills/data-analysis/decision-briefs.md`
- `OpenClawTrevorMentis/skills/data-analysis/metric-contracts.md`
- `OpenClawTrevorMentis/skills/data-analysis/pitfalls.md`
- `OpenClawTrevorMentis/skills/data-analysis/techniques.md`
- `OpenClawTrevorMentis/skills/geospatial-osint/SKILL.md`
- `OpenClawTrevorMentis/skills/geospatial-osint/_meta.json`
- `OpenClawTrevorMentis/skills/indicators-and-warnings/SKILL.md`
- `OpenClawTrevorMentis/skills/indicators-and-warnings/_meta.json`
- `OpenClawTrevorMentis/skills/mermaid/README.md`
- `OpenClawTrevorMentis/skills/mermaid/SKILL.md`
- `OpenClawTrevorMentis/skills/mermaid/_meta.json`
- `OpenClawTrevorMentis/skills/mermaid/generate-test.sh`
- `OpenClawTrevorMentis/skills/mermaid/package.json`
- `OpenClawTrevorMentis/skills/pdf-report/SKILL.md`
- `OpenClawTrevorMentis/skills/pdf-report/_meta.json`
- `OpenClawTrevorMentis/skills/quick-translation/SKILL.md`
- `OpenClawTrevorMentis/skills/quick-translation/_meta.json`
- `OpenClawTrevorMentis/skills/sat-toolkit/SKILL.md`
- `OpenClawTrevorMentis/skills/sat-toolkit/_meta.json`
- `OpenClawTrevorMentis/skills/source-evaluation/SKILL.md`
- `OpenClawTrevorMentis/skills/source-evaluation/_meta.json`
- `OpenClawTrevorMentis/skills/daily_intel/AUTONOMOUS_WORKFLOW.md`
- `OpenClawTrevorMentis/skills/daily_intel/README.md`
- `OpenClawTrevorMentis/skills/daily_intel/deepseek_client.py`
- `OpenClawTrevorMentis/skills/daily_intel/requirements.txt`
- `OpenClawTrevorMentis/skills/daily_intel/skill_config.json`
- `OpenClawTrevorMentis/skills/daily_intel/import_handoff.py`
- `OpenClawTrevorMentis/skills/daily_intel/trevor_config.py`
- `OpenClawTrevorMentis/skills/daily_intel/trevor_log.py`
- `OpenClawTrevorMentis/skills/daily_intel/trevor_fonts.py`
- `OpenClawTrevorMentis/skills/daily_intel/trevor_diag.py`
- `OpenClawTrevorMentis/skills/daily_intel/trevor_memory.py`
- `OpenClawTrevorMentis/skills/daily_intel/trevor_skills.py`
- `OpenClawTrevorMentis/skills/daily_intel/trevor_cost.py`
- `OpenClawTrevorMentis/skills/daily_intel/trevor_freeze.py`
- `OpenClawTrevorMentis/skills/daily_intel/trevor_dashboard.py`
- `OpenClawTrevorMentis/skills/agentmail/.clawhub/origin.json`
- `OpenClawTrevorMentis/skills/agentmail/references/API.md`
- `OpenClawTrevorMentis/skills/agentmail/references/EXAMPLES.md`
- `OpenClawTrevorMentis/skills/agentmail/references/WEBHOOKS.md`
- `OpenClawTrevorMentis/skills/agentmail/scripts/check_inbox.py`
- `OpenClawTrevorMentis/skills/agentmail/scripts/send_email.py`
- `OpenClawTrevorMentis/skills/agentmail/scripts/setup_webhook.py`
- `OpenClawTrevorMentis/skills/baoyu-translate/.clawhub/origin.json`
- `OpenClawTrevorMentis/skills/baoyu-translate/references/glossary-en-zh.md`
- `OpenClawTrevorMentis/skills/baoyu-translate/references/refined-workflow.md`
- `OpenClawTrevorMentis/skills/baoyu-translate/references/subagent-prompt-template.md`
- `OpenClawTrevorMentis/skills/baoyu-translate/references/workflow-mechanics.md`
- `OpenClawTrevorMentis/skills/baoyu-translate/scripts/bun.lock`
- `OpenClawTrevorMentis/skills/baoyu-translate/scripts/chunk.ts`
- `OpenClawTrevorMentis/skills/baoyu-translate/scripts/main.ts`
- `OpenClawTrevorMentis/skills/baoyu-translate/scripts/package.json`
- `OpenClawTrevorMentis/skills/baoyu-translate/references/config/extend-schema.md`
- `OpenClawTrevorMentis/skills/baoyu-translate/references/config/first-time-setup.md`
- `OpenClawTrevorMentis/skills/chartgen-ai/.clawhub/origin.json`
- `OpenClawTrevorMentis/skills/chartgen-ai/references/upgrade-skill.md`
- `OpenClawTrevorMentis/skills/chartgen-ai/tools/chartgen_api.js`
- `OpenClawTrevorMentis/skills/data-analysis/.clawhub/origin.json`
- `OpenClawTrevorMentis/skills/geospatial-osint/.clawhub/origin.json`
- `OpenClawTrevorMentis/skills/geospatial-osint/references/adsb-api.md`
- `OpenClawTrevorMentis/skills/geospatial-osint/references/cesium-basics.md`
- `OpenClawTrevorMentis/skills/geospatial-osint/references/effects.md`
- `OpenClawTrevorMentis/skills/geospatial-osint/references/rendering-stack.md`
- `OpenClawTrevorMentis/skills/geospatial-osint/references/satellite-passes.md`
- `OpenClawTrevorMentis/skills/mermaid/.clawhub/origin.json`
- `OpenClawTrevorMentis/skills/pdf-report/.clawhub/origin.json`
- `OpenClawTrevorMentis/skills/pdf-report/scripts/render_pdf.py`
- `OpenClawTrevorMentis/skills/pdf-report/templates/report.html`
- `OpenClawTrevorMentis/skills/quick-translation/.clawhub/origin.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron/run_daily.py`
- `OpenClawTrevorMentis/skills/daily_intel/memory/retrieve.py`
- `OpenClawTrevorMentis/skills/daily_intel/memory/index_memory.py`
- `OpenClawTrevorMentis/skills/daily_intel/memory/vector_index.json`
- `OpenClawTrevorMentis/skills/daily_intel/memory/trevor_memory.db`
- `OpenClawTrevorMentis/skills/daily_intel/memory/memory_freeze.json`
- `OpenClawTrevorMentis/skills/daily_intel/assessments/europe.md`
- `OpenClawTrevorMentis/skills/daily_intel/assessments/africa.md`
- `OpenClawTrevorMentis/skills/daily_intel/assessments/asia.md`
- `OpenClawTrevorMentis/skills/daily_intel/assessments/middle_east.md`
- `OpenClawTrevorMentis/skills/daily_intel/assessments/north_america.md`
- `OpenClawTrevorMentis/skills/daily_intel/assessments/south_america.md`
- `OpenClawTrevorMentis/skills/daily_intel/assessments/global_finance.md`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/build_pdf.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/generate_assessments.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/refresh_imagery.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/_email_brief.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/_fetch_intel_emails.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/quality_audit.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/briefometer.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/story_tracker.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/daily_enrichment.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/improvement_daemon.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/narrative_engine.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/prioritize.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/analytical_opportunities.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/osint_collection_expansion.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/scrape_creators.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/daily_operational_report.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/collection_intelligence.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/global_collection.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/collection_daemon.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/epistemic_state.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/sonar_scout.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/cognition_router.py`
- `OpenClawTrevorMentis/skills/daily_intel/scripts/meta_cognition.py`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/state.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/STANDING_RULES.md`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/run.log`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/heartbeat.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/issue_number.txt`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/.gitignore`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/improvement_log.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/measurement_log.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/key_judgments.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/story_tracker.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/daemon_run.log`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/enrichment_report.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/daily_report_2026-05-08.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/story_delta.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/daily_report_2026-05-09.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/daily_report_2026-05-10.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/session-costs.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/daily_report_2026-05-11.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/narrative_landscape.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/analytical_opportunities.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/source_inventory.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/collection_expansion.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/latest_operational_report.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/collection_intelligence.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/global_collection.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/collection_daemon_state.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/collection_events.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/epistemic_state.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/sonar_scout_report.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/cognition_routing.json`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/meta_cognition_report.json`
- `OpenClawTrevorMentis/skills/daily_intel/memory/chroma_db/chroma.sqlite3`
- `OpenClawTrevorMentis/skills/daily_intel/cron_tracking/daily_reports/operational_report_2026-05-12.json`
- `OpenClawTrevorMentis/skills/daily_intel/skills/publishing/daily-intel-pipeline.md`
- `daily_intel/memory/vector_index.json`
- `timeline-chart/.clawhub/origin.json`