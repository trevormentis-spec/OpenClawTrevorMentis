# Daily Skill Scanner Audit - 2026-05-16 00:00 UTC

## Overview


### Source: skills


### Source: skills


### Source: skills


### Source: skills


---

## Summary Statistics

- **Total skills scanned:** 125
- **Approved (clean):** 110
- **Caution (high issues):** 1
- **Rejected (critical issues):** 14
- **Total findings:** 0
  - Critical: 0
  - High: 0
  - Medium: 0

## Skills Requiring Attention

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: audit_skills.py:6
- Code: The raw scanner regex-matches strings like `~/.config` and `Bearer ${...}` as
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: consolidated_audit_report.md:21
- Code: 2. **Credential Paths:** Multiple skills (`gmail`, `gog-myclaw`, `api-gateway`, `stripe-api`, `whatsapp-business`) were flagged for referencing `~/.co
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: consolidated_audit_report.md:33
- Code: 2. **Config Locations:** Skills such as `eightctl`, `camsnap`, and `spotify-player` were flagged for documentation referencing `~/.config` directories
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: consolidated_audit_report.md:39
- Code: 2. **Audit Config Access:** Ensure that skills accessing `~/.config` are only doing so for their own legitimate configuration and not attempting to ex
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: consolidated_audit_report.md:40
- Code: 3. **Ignore Documentation Flags:** Findings inside `SKILL.md` files that merely describe setup procedures (e.g., "save your token to ~/.config/...") c
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: crypto_miner (critical)
- File: skill_audit_report.json:144
- Code: "line_content": "- Catches **crypto-mining** indicators (xmrig, mining pools, wallet addresses)",
- Recommendation: REJECT - this is cryptojacking malware

### unknown [verdict: reject]
- Pattern: crypto_miner (critical)
- File: skill_audit_report.json:153
- Code: "line_content": "- Crypto miners (xmrig, ethminer, stratum+tcp)",
- Recommendation: REJECT - this is cryptojacking malware

### unknown [verdict: reject]
- Pattern: crypto_miner (critical)
- File: skill_audit_report.json:189
- Code: "line_content": "\"pattern\": r\"xmrig|ethminer|cpuminer|cgminer|stratum\\+tcp|mining.*pool|hashrate\",",
- Recommendation: REJECT - this is cryptojacking malware

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: system_skills_audit.md:29
- Code: - **Code:** `- Config: `~/.config/eightctl/config.yaml``
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: system_skills_audit.md:36
- Code: - **Code:** `- Config file: `~/.config/camsnap/config.yaml``
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: system_skills_audit.md:43
- Code: - **Code:** `- Config folder: `~/.config/spotify-player` (e.g., `app.toml`).`
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: system_skills_audit.md:50
- Code: - **Code:** `- For some operations (add-text, tags, open-note --selected), a Bear app token (stored in `~/.config/grizzly/token`)`
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: system_skills_audit.md:57
- Code: - **Code:** `2. Save it: `echo "YOUR_TOKEN" > ~/.config/grizzly/token``
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: system_skills_audit.md:64
- Code: - **Code:** `echo "Additional content" | grizzly add-text --id "NOTE_ID" --mode append --token-file ~/.config/grizzly/token`
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: system_skills_audit.md:71
- Code: - **Code:** `grizzly tags --enable-callback --json --token-file ~/.config/grizzly/token`
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: system_skills_audit.md:78
- Code: - **Code:** `4. `~/.config/grizzly/config.toml``
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: system_skills_audit.md:85
- Code: - **Code:** `Example `~/.config/grizzly/config.toml`:`
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: system_skills_audit.md:92
- Code: - **Code:** `token_file = "~/.config/grizzly/token"`
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: system_skills_audit.md:99
- Code: - **Code:** `2. A configuration file at `~/.config/himalaya/config.toml``
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: system_skills_audit.md:106
- Code: - **Code:** `Or create `~/.config/himalaya/config.toml` manually:`
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: system_skills_audit.md:113
- Code: - **Code:** `- Don’t attach secrets by default (`.env`, key files, auth tokens). Redact aggressively; share only what’s required.`
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: system_skills_audit.md:120
- Code: - **Code:** `mkdir -p ~/.config/notion`
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: system_skills_audit.md:127
- Code: - **Code:** `echo "ntn_your_key_here" > ~/.config/notion/api_key`
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: system_skills_audit.md:134
- Code: - **Code:** `NOTION_KEY=$(cat ~/.config/notion/api_key)`
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: system_skills_audit.md:141
- Code: - **Code:** `- `op run --env-file="./.env" -- printenv DB_PASSWORD``
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: system_skills_audit.md:148
- Code: - **Code:** `- Claude: ~/.config/claude/projects/**/\*.jsonl or ~/.claude/projects/**/\*.jsonl`
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: system_skills_audit.md:155
- Code: - **Code:** `Configuration file location: `~/.config/himalaya/config.toml``
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: user_skills_audit.md:29
- Code: - **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}``
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: user_skills_audit.md:36
- Code: - **Code:** `3. Once they provide the `credentials.json` content, save it to `~/.config/gogcli/credentials.json`.`
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: user_skills_audit.md:43
- Code: - **Code:** `4. Run: `gog auth credentials set ~/.config/gogcli/credentials.json``
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: user_skills_audit.md:50
- Code: - **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}``
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: user_skills_audit.md:57
- Code: - **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}``
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: user_skills_audit.md:64
- Code: - **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}`,`
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: user_skills_audit.md:71
- Code: - **Code:** `- Credential path access (~/.ssh, ~/.aws, /etc/passwd)`
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: user_skills_audit.md:92
- Code: - **Code:** `"pattern": r"~/\.ssh|~/\.aws|~/\.config|/etc/passwd|\.env\b|\.credentials|keychain",`
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: crypto_miner (critical)
- File: user_skills_audit.md:78
- Code: - **Code:** `- Catches **crypto-mining** indicators (xmrig, mining pools, wallet addresses)`
- Recommendation: REJECT - this is cryptojacking malware

### unknown [verdict: reject]
- Pattern: crypto_miner (critical)
- File: user_skills_audit.md:85
- Code: - **Code:** `- Crypto miners (xmrig, ethminer, stratum+tcp)`
- Recommendation: REJECT - this is cryptojacking malware

### unknown [verdict: reject]
- Pattern: crypto_miner (critical)
- File: user_skills_audit.md:113
- Code: - **Code:** `"pattern": r"xmrig|ethminer|cpuminer|cgminer|stratum\+tcp|mining.*pool|hashrate",`
- Recommendation: REJECT - this is cryptojacking malware

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: brain/README.md:61
- Code: - Don't index secrets. The indexer skips `.env`, `*.key`, `*.pem`,
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: brain/scripts/brain.py:62
- Code: re.compile(r"\.env$"),
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: skills/chartgen-ai/tools/chartgen_api.js:25
- Code: const BASE_URL = process.env.CHARTGEN_API_URL || "https://chartgen.ai";
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: skills/chartgen-ai/tools/chartgen_api.js:40
- Code: if (process.env.CHARTGEN_API_KEY) return process.env.CHARTGEN_API_KEY;
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: skills/chartgen-ai/tools/chartgen_api.js:44
- Code: process.env.OPENCLAW_STATE_DIR
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: skills/chartgen-ai/tools/chartgen_api.js:45
- Code: ? path.join(process.env.OPENCLAW_STATE_DIR, "skills", "chartgen", "config.json")
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: skills/chartgen-ai/tools/chartgen_api.js:74
- Code: const stateDir = process.env.OPENCLAW_STATE_DIR;
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: skills/daily_intel/cron/run_daily.py:19
- Code: # Load environment from workspace .env (cron may not have it in env)
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: skills/daily_intel/cron/run_daily.py:21
- Code: WORKSPACE_ENV = WORKSPACE / '.env'
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: skills/daily_intel/scripts/_email_brief.py:19
- Code: # Try reading from workspace .env
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: skills/daily_intel/scripts/_email_brief.py:21
- Code: env_path = str(WORKSPACE / ".env")
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: skills/daily_intel/scripts/_fetch_intel_emails.py:105
- Code: """Read MATON_API_KEY from env or workspace .env."""
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: skills/daily_intel/scripts/_fetch_intel_emails.py:108
- Code: env_path = os.path.expanduser("~/.openclaw/workspace/.env")
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: skills/daily_intel/scripts/improvement_daemon.py:29
- Code: # Load .env for subprocess environment inheritance
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: skills/daily_intel/scripts/improvement_daemon.py:32
- Code: env_path = Path.home() / '.openclaw' / 'workspace' / '.env'
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: skills/daily_intel/scripts/improvement_daemon.py:41
- Code: env_path = Path.home() / '.openclaw' / 'workspace' / '.env'
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: skills/daily_intel/scripts/sonar_scout.py:70
- Code: """Get OpenRouter API key from workspace .env."""
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: skills/daily_intel/scripts/sonar_scout.py:71
- Code: env_path = WORKSPACE / ".env"
- Recommendation: REJECT unless explicitly justified

### api-gateway [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:539
- Code: 'Authorization': `Bearer ${process.env.MATON_API_KEY}`
- Recommendation: REJECT unless explicitly justified

### gmail [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:267
- Code: 'Authorization': `Bearer ${process.env.MATON_API_KEY}`
- Recommendation: REJECT unless explicitly justified

### gog [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:23
- Code: 3. Once they provide the `credentials.json` content, save it to `~/.config/gogcli/credentials.json`.
- Recommendation: REJECT unless explicitly justified

### gog [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:24
- Code: 4. Run: `gog auth credentials set ~/.config/gogcli/credentials.json`
- Recommendation: REJECT unless explicitly justified

### skill-scanner [verdict: reject]
- Pattern: credential_paths (critical)
- File: README.md:155
- Code: - Credential path access (~/.ssh, ~/.aws, /etc/passwd)
- Recommendation: REJECT unless explicitly justified

### skill-scanner [verdict: reject]
- Pattern: crypto_miner (critical)
- File: README.md:9
- Code: - Catches **crypto-mining** indicators (xmrig, mining pools, wallet addresses)
- Recommendation: REJECT - this is cryptojacking malware

### skill-scanner [verdict: reject]
- Pattern: crypto_miner (critical)
- File: README.md:158
- Code: - Crypto miners (xmrig, ethminer, stratum+tcp)
- Recommendation: REJECT - this is cryptojacking malware

### skill-scanner [verdict: reject]
- Pattern: credential_paths (critical)
- File: skill_scanner.py:101
- Code: "pattern": r"~/\.ssh|~/\.aws|~/\.config|/etc/passwd|\.env\b|\.credentials|keychain",
- Recommendation: REJECT unless explicitly justified

### skill-scanner [verdict: reject]
- Pattern: crontab_modify (high)
- File: skill_scanner.py:118
- Code: "pattern": r"crontab\s+-|/etc/cron|schtasks\s+/create",
- Recommendation: Skills should use Clawdbot cron, not system crontab

### skill-scanner [verdict: reject]
- Pattern: systemd_modify (critical)
- File: skill_scanner.py:126
- Code: "pattern": r"systemctl\s+enable|systemctl\s+start|/etc/systemd|launchctl\s+load",
- Recommendation: REJECT - skills should not create system services

### skill-scanner [verdict: reject]
- Pattern: crypto_miner (critical)
- File: skill_scanner.py:135
- Code: "pattern": r"xmrig|ethminer|cpuminer|cgminer|stratum\+tcp|mining.*pool|hashrate",
- Recommendation: REJECT - this is cryptojacking malware

### skill-scanner [verdict: reject]
- Pattern: reverse_shell (critical)
- File: skill_scanner.py:161
- Code: "pattern": r"/dev/tcp/|nc\s+-e|bash\s+-i\s+>&|python.*pty\.spawn",
- Recommendation: REJECT - this is a backdoor

### skill-scanner [verdict: reject]
- Pattern: base64_decode_exec (critical)
- File: skill_scanner.py:170
- Code: "pattern": r"base64\.b64decode.*exec|atob.*eval",
- Recommendation: REJECT - likely hiding malicious code

### stripe [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:778
- Code: 'Authorization': `Bearer ${process.env.MATON_API_KEY}`
- Recommendation: REJECT unless explicitly justified

### trevor-methodology [verdict: caution]
- Pattern: eval_exec (high)
- File: pipeline/docx-js-template.js:37
- Code: const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
- Recommendation: Verify input is sanitized, not user-controlled

### video-translation [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:90
- Code: - `NOIZ_API_KEY` configured for the Noiz backend. If it is not set, first guide the user to get an API key from `https://developers.noiz.ai/api-keys`.
- Recommendation: REJECT unless explicitly justified

### whatsapp-business [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:494
- Code: 'Authorization': `Bearer ${process.env.MATON_API_KEY}`,
- Recommendation: REJECT unless explicitly justified

### chartgen [verdict: reject]
- Pattern: credential_paths (critical)
- File: tools/chartgen_api.js:25
- Code: const BASE_URL = process.env.CHARTGEN_API_URL || "https://chartgen.ai";
- Recommendation: REJECT unless explicitly justified

### chartgen [verdict: reject]
- Pattern: credential_paths (critical)
- File: tools/chartgen_api.js:40
- Code: if (process.env.CHARTGEN_API_KEY) return process.env.CHARTGEN_API_KEY;
- Recommendation: REJECT unless explicitly justified

### chartgen [verdict: reject]
- Pattern: credential_paths (critical)
- File: tools/chartgen_api.js:44
- Code: process.env.OPENCLAW_STATE_DIR
- Recommendation: REJECT unless explicitly justified

### chartgen [verdict: reject]
- Pattern: credential_paths (critical)
- File: tools/chartgen_api.js:45
- Code: ? path.join(process.env.OPENCLAW_STATE_DIR, "skills", "chartgen", "config.json")
- Recommendation: REJECT unless explicitly justified

### chartgen [verdict: reject]
- Pattern: credential_paths (critical)
- File: tools/chartgen_api.js:74
- Code: const stateDir = process.env.OPENCLAW_STATE_DIR;
- Recommendation: REJECT unless explicitly justified

### daily-intel-brief [verdict: reject]
- Pattern: bulk_env_access (high)
- File: scripts/build_pdf.py:330
- Code: env = dict(os.environ)
- Recommendation: REJECT - review carefully for data theft

### daily-intel-brief [verdict: reject]
- Pattern: credential_paths (critical)
- File: scripts/collect.py:510
- Code: # Load .env for BRAVE_API_KEY and other secrets
- Recommendation: REJECT unless explicitly justified

### daily-intel-brief [verdict: reject]
- Pattern: credential_paths (critical)
- File: scripts/collect.py:511
- Code: _env = pathlib.Path("/home/ubuntu/.openclaw/workspace/.env")
- Recommendation: REJECT unless explicitly justified

### genviral [verdict: reject]
- Pattern: credential_paths (critical)
- File: scripts/genviral.sh:192
- Code: [[ -f "${HOME}/.config/env/global.env" ]] && source "${HOME}/.config/env/global.env" 2>/dev/null || true
- Recommendation: REJECT unless explicitly justified

### genviral [verdict: reject]
- Pattern: credential_paths (critical)
- File: scripts/genviral.sh:219
- Code: die "GENVIRAL_API_KEY is not set.\n  Set it via: export GENVIRAL_API_KEY=\"your_public_id.your_secret\"\n  Or add to ~/.config/env/global.env"
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: CHANGELOG.md:42
- Code: - Support for custom credential prefixes in `.env` file
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: CHANGELOG.md:143
- Code: - ❌ Fixed `.env` file parsing error (quoted mnemonic)
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: CHANGELOG.md:175
- Code: - Automatic credential loading from `.env` and Farcaster credentials file
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: README.md:44
- Code: | **X/Twitter** | Pay-per-use (consumption-based) | `~/.openclaw/.env` | 5-10 min |
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: README.md:91
- Code: **Step 3: Add to .env file**
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: README.md:92
- Code: Location: `/home/phan_harry/.openclaw/.env`
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: README.md:180
- Code: grep "^X_CONSUMER_KEY" ~/.openclaw/.env
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: README.md:308
- Code: 1. Check `.env` file exists: `ls -la ~/.openclaw/.env`
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: README.md:311
- Code: grep "^X_" ~/.openclaw/.env
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: README.md:314
- Code: 4. Check file permissions: `chmod 600 ~/.openclaw/.env`
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:43
- Code: **Required credentials** (stored in `/home/phan_harry/.openclaw/.env`):
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:76
- Code: 4. **Add to .env file**
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:78
- Code: echo "X_CONSUMER_KEY=xxx" >> ~/.openclaw/.env
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:79
- Code: echo "X_CONSUMER_SECRET=xxx" >> ~/.openclaw/.env
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:80
- Code: echo "X_ACCESS_TOKEN=xxx" >> ~/.openclaw/.env
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:81
- Code: echo "X_ACCESS_TOKEN_SECRET=xxx" >> ~/.openclaw/.env
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:98
- Code: echo "MYACCOUNT_API_KEY=xxx" >> ~/.openclaw/.env
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:99
- Code: echo "MYACCOUNT_API_KEY_SECRET=xxx" >> ~/.openclaw/.env
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:100
- Code: echo "MYACCOUNT_ACCESS_TOKEN=xxx" >> ~/.openclaw/.env
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:101
- Code: echo "MYACCOUNT_ACCESS_TOKEN_SECRET=xxx" >> ~/.openclaw/.env
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:179
- Code: - ⚠️ `.env` file should have `600` permissions (read/write owner only)
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:253
- Code: - `--account <name>` - Twitter account to use (lowercase prefix from .env)
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:266
- Code: - `--account <name>` - Twitter account to use (lowercase prefix from .env)
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:362
- Code: - Twitter credentials in `.env` (X_CONSUMER_KEY, X_CONSUMER_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: lib/farcaster.sh:30
- Code: const wallet = new Wallet(process.env.PRIVATE_KEY, baseProvider);
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: lib/farcaster.sh:31
- Code: const signerBytes = Buffer.from(process.env.SIGNER_PRIVATE_KEY, 'hex');
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: lib/farcaster.sh:33
- Code: const fid = parseInt(process.env.FID);
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: lib/farcaster.sh:34
- Code: const parentHashBytes = Buffer.from(process.env.PARENT_HASH.replace('0x', ''), 'hex');
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: lib/farcaster.sh:117
- Code: const wallet = new Wallet(process.env.PRIVATE_KEY, baseProvider);
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: lib/farcaster.sh:118
- Code: const signerBytes = Buffer.from(process.env.SIGNER_PRIVATE_KEY, 'hex');
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: lib/farcaster.sh:120
- Code: const fid = parseInt(process.env.FID);
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: lib/farcaster.sh:121
- Code: const imageUrl = process.env.IMAGE_URL;
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: lib/farcaster.sh:131
- Code: if (process.env.PARENT_HASH) {
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: lib/farcaster.sh:132
- Code: const parentHashBytes = Buffer.from(process.env.PARENT_HASH.replace('0x', ''), 'hex');
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: lib/twitter.sh:8
- Code: source /home/phan_harry/.openclaw/.env
- Recommendation: REJECT unless explicitly justified

### social-post [verdict: reject]
- Pattern: credential_paths (critical)
- File: scripts/reply.sh:272
- Code: source /home/phan_harry/.openclaw/.env
- Recommendation: REJECT unless explicitly justified

### unknown [verdict: reject]
- Pattern: credential_paths (critical)
- File: publishing/build-agent-brief.md:40
- Code: - Moltbook API key must be in .env or environment
- Recommendation: REJECT unless explicitly justified

### video-translation [verdict: reject]
- Pattern: credential_paths (critical)
- File: SKILL.md:90
- Code: - `NOIZ_API_KEY` configured for the Noiz backend. If it is not set, first guide the user to get an API key from `https://developers.noiz.ai/api-keys`.
- Recommendation: REJECT unless explicitly justified


## Detailed Reports

Individual scan reports saved to: `/tmp/skill-audit-20260516/`

---
Generated by Daily Skill Scanner Audit cron | 2026-05-16 00:00 UTC
