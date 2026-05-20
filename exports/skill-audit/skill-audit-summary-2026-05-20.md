# 🔒 Daily Skill Security Audit — 2026-05-20 00:00 UTC

**Total skills scanned:** 79
**Total files reviewed:** 271
**Total lines of code:** 43510
**Total findings:** 97

---

## 🏆 Verdict Summary

| Category | Count |
|----------|-------|
| ✅ Approved | 71 |
| ⚠️ Caution | 1 |
| ❌ Rejected | 7 |
| ❓ Error | 0 |

### ❌ Rejected Skills (Critical Issues)

- **unknown** (`/home/ubuntu/.openclaw/skills/OpenClawTrevorMentis`)
  - Reason: Found 56 critical issue(s): credential_paths, crypto_miner
  - `credential_paths` in `audit_skills.py` line 6: The raw scanner regex-matches strings like `~/.config` and `Bearer ${...}` as
  - `credential_paths` in `consolidated_audit_report.md` line 21: 2. **Credential Paths:** Multiple skills (`gmail`, `gog-myclaw`, `api-gateway`, `stripe-api`, `whatsapp-business`) were 
  - `credential_paths` in `consolidated_audit_report.md` line 33: 2. **Config Locations:** Skills such as `eightctl`, `camsnap`, and `spotify-player` were flagged for documentation refer
  - `credential_paths` in `consolidated_audit_report.md` line 39: 2. **Audit Config Access:** Ensure that skills accessing `~/.config` are only doing so for their own legitimate configur
  - `credential_paths` in `consolidated_audit_report.md` line 40: 3. **Ignore Documentation Flags:** Findings inside `SKILL.md` files that merely describe setup procedures (e.g., "save y
  - `crypto_miner` in `skill_audit_report.json` line 144: "line_content": "- Catches **crypto-mining** indicators (xmrig, mining pools, wallet addresses)",
  - `crypto_miner` in `skill_audit_report.json` line 153: "line_content": "- Crypto miners (xmrig, ethminer, stratum+tcp)",
  - `crypto_miner` in `skill_audit_report.json` line 189: "line_content": "\"pattern\": r\"xmrig|ethminer|cpuminer|cgminer|stratum\\+tcp|mining.*pool|hashrate\",",
  - `credential_paths` in `system_skills_audit.md` line 29: - **Code:** `- Config: `~/.config/eightctl/config.yaml``
  - `credential_paths` in `system_skills_audit.md` line 36: - **Code:** `- Config file: `~/.config/camsnap/config.yaml``
  - `credential_paths` in `system_skills_audit.md` line 43: - **Code:** `- Config folder: `~/.config/spotify-player` (e.g., `app.toml`).`
  - `credential_paths` in `system_skills_audit.md` line 50: - **Code:** `- For some operations (add-text, tags, open-note --selected), a Bear app token (stored in `~/.config/grizzl
  - `credential_paths` in `system_skills_audit.md` line 57: - **Code:** `2. Save it: `echo "YOUR_TOKEN" > ~/.config/grizzly/token``
  - `credential_paths` in `system_skills_audit.md` line 64: - **Code:** `echo "Additional content" | grizzly add-text --id "NOTE_ID" --mode append --token-file ~/.config/grizzly/to
  - `credential_paths` in `system_skills_audit.md` line 71: - **Code:** `grizzly tags --enable-callback --json --token-file ~/.config/grizzly/token`
  - `credential_paths` in `system_skills_audit.md` line 78: - **Code:** `4. `~/.config/grizzly/config.toml``
  - `credential_paths` in `system_skills_audit.md` line 85: - **Code:** `Example `~/.config/grizzly/config.toml`:`
  - `credential_paths` in `system_skills_audit.md` line 92: - **Code:** `token_file = "~/.config/grizzly/token"`
  - `credential_paths` in `system_skills_audit.md` line 99: - **Code:** `2. A configuration file at `~/.config/himalaya/config.toml``
  - `credential_paths` in `system_skills_audit.md` line 106: - **Code:** `Or create `~/.config/himalaya/config.toml` manually:`
  - `credential_paths` in `system_skills_audit.md` line 113: - **Code:** `- Don’t attach secrets by default (`.env`, key files, auth tokens). Redact aggressively; share only what’s 
  - `credential_paths` in `system_skills_audit.md` line 120: - **Code:** `mkdir -p ~/.config/notion`
  - `credential_paths` in `system_skills_audit.md` line 127: - **Code:** `echo "ntn_your_key_here" > ~/.config/notion/api_key`
  - `credential_paths` in `system_skills_audit.md` line 134: - **Code:** `NOTION_KEY=$(cat ~/.config/notion/api_key)`
  - `credential_paths` in `system_skills_audit.md` line 141: - **Code:** `- `op run --env-file="./.env" -- printenv DB_PASSWORD``
  - `credential_paths` in `system_skills_audit.md` line 148: - **Code:** `- Claude: ~/.config/claude/projects/**/\*.jsonl or ~/.claude/projects/**/\*.jsonl`
  - `credential_paths` in `system_skills_audit.md` line 155: - **Code:** `Configuration file location: `~/.config/himalaya/config.toml``
  - `credential_paths` in `user_skills_audit.md` line 29: - **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}``
  - `credential_paths` in `user_skills_audit.md` line 36: - **Code:** `3. Once they provide the `credentials.json` content, save it to `~/.config/gogcli/credentials.json`.`
  - `credential_paths` in `user_skills_audit.md` line 43: - **Code:** `4. Run: `gog auth credentials set ~/.config/gogcli/credentials.json``
  - `credential_paths` in `user_skills_audit.md` line 50: - **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}``
  - `credential_paths` in `user_skills_audit.md` line 57: - **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}``
  - `credential_paths` in `user_skills_audit.md` line 64: - **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}`,`
  - `credential_paths` in `user_skills_audit.md` line 71: - **Code:** `- Credential path access (~/.ssh, ~/.aws, /etc/passwd)`
  - `credential_paths` in `user_skills_audit.md` line 92: - **Code:** `"pattern": r"~/\.ssh|~/\.aws|~/\.config|/etc/passwd|\.env\b|\.credentials|keychain",`
  - `crypto_miner` in `user_skills_audit.md` line 78: - **Code:** `- Catches **crypto-mining** indicators (xmrig, mining pools, wallet addresses)`
  - `crypto_miner` in `user_skills_audit.md` line 85: - **Code:** `- Crypto miners (xmrig, ethminer, stratum+tcp)`
  - `crypto_miner` in `user_skills_audit.md` line 113: - **Code:** `"pattern": r"xmrig|ethminer|cpuminer|cgminer|stratum\+tcp|mining.*pool|hashrate",`
  - `credential_paths` in `brain/README.md` line 61: - Don't index secrets. The indexer skips `.env`, `*.key`, `*.pem`,
  - `credential_paths` in `brain/scripts/brain.py` line 62: re.compile(r"\.env$"),
  - `credential_paths` in `skills/chartgen-ai/tools/chartgen_api.js` line 25: const BASE_URL = process.env.CHARTGEN_API_URL || "https://chartgen.ai";
  - `credential_paths` in `skills/chartgen-ai/tools/chartgen_api.js` line 40: if (process.env.CHARTGEN_API_KEY) return process.env.CHARTGEN_API_KEY;
  - `credential_paths` in `skills/chartgen-ai/tools/chartgen_api.js` line 44: process.env.OPENCLAW_STATE_DIR
  - `credential_paths` in `skills/chartgen-ai/tools/chartgen_api.js` line 45: ? path.join(process.env.OPENCLAW_STATE_DIR, "skills", "chartgen", "config.json")
  - `credential_paths` in `skills/chartgen-ai/tools/chartgen_api.js` line 74: const stateDir = process.env.OPENCLAW_STATE_DIR;
  - `credential_paths` in `skills/daily_intel/cron/run_daily.py` line 19: # Load environment from workspace .env (cron may not have it in env)
  - `credential_paths` in `skills/daily_intel/cron/run_daily.py` line 21: WORKSPACE_ENV = WORKSPACE / '.env'
  - `credential_paths` in `skills/daily_intel/scripts/_email_brief.py` line 19: # Try reading from workspace .env
  - `credential_paths` in `skills/daily_intel/scripts/_email_brief.py` line 21: env_path = str(WORKSPACE / ".env")
  - `credential_paths` in `skills/daily_intel/scripts/_fetch_intel_emails.py` line 105: """Read MATON_API_KEY from env or workspace .env."""
  - `credential_paths` in `skills/daily_intel/scripts/_fetch_intel_emails.py` line 108: env_path = os.path.expanduser("~/.openclaw/workspace/.env")
  - `credential_paths` in `skills/daily_intel/scripts/improvement_daemon.py` line 29: # Load .env for subprocess environment inheritance
  - `credential_paths` in `skills/daily_intel/scripts/improvement_daemon.py` line 32: env_path = Path.home() / '.openclaw' / 'workspace' / '.env'
  - `credential_paths` in `skills/daily_intel/scripts/improvement_daemon.py` line 41: env_path = Path.home() / '.openclaw' / 'workspace' / '.env'
  - `credential_paths` in `skills/daily_intel/scripts/sonar_scout.py` line 70: """Get OpenRouter API key from workspace .env."""
  - `credential_paths` in `skills/daily_intel/scripts/sonar_scout.py` line 71: env_path = WORKSPACE / ".env"

- **api-gateway** (`/home/ubuntu/.openclaw/skills/api-gateway`)
  - Reason: Found 1 critical issue(s): credential_paths
  - `credential_paths` in `SKILL.md` line 539: 'Authorization': `Bearer ${process.env.MATON_API_KEY}`

- **gmail** (`/home/ubuntu/.openclaw/skills/gmail`)
  - Reason: Found 1 critical issue(s): credential_paths
  - `credential_paths` in `SKILL.md` line 267: 'Authorization': `Bearer ${process.env.MATON_API_KEY}`

- **gog** (`/home/ubuntu/.openclaw/skills/gog-myclaw`)
  - Reason: Found 2 critical issue(s): credential_paths
  - `credential_paths` in `SKILL.md` line 23: 3. Once they provide the `credentials.json` content, save it to `~/.config/gogcli/credentials.json`.
  - `credential_paths` in `SKILL.md` line 24: 4. Run: `gog auth credentials set ~/.config/gogcli/credentials.json`

- **stripe** (`/home/ubuntu/.openclaw/skills/stripe-api`)
  - Reason: Found 1 critical issue(s): credential_paths
  - `credential_paths` in `SKILL.md` line 778: 'Authorization': `Bearer ${process.env.MATON_API_KEY}`

- **video-translation** (`/home/ubuntu/.agents/skills/video-translation`)
  - Reason: Found 1 critical issue(s): credential_paths
  - `credential_paths` in `SKILL.md` line 90: - `NOIZ_API_KEY` configured for the Noiz backend. If it is not set, first guide the user to get an API key from `https:/

- **whatsapp-business** (`/home/ubuntu/.openclaw/skills/whatsapp-business`)
  - Reason: Found 1 critical issue(s): credential_paths
  - `credential_paths` in `SKILL.md` line 494: 'Authorization': `Bearer ${process.env.MATON_API_KEY}`,

### ⚠️ Caution Skills (High-Severity Issues)

- **trevor-methodology** (`/home/ubuntu/.openclaw/skills/trevor-methodology`)
  - Reason: Found 1 high-severity issue(s): eval_exec
  - `eval_exec` in `pipeline/docx-js-template.js` line 37

## 📋 All Findings (By Severity)

| # | Skill | Pattern | Severity | File | Line |
|---|-------|---------|----------|------|------|
| 1 | unknown | credential_paths | 🔴 critical | `audit_skills.py` | 6 |
| 2 | unknown | credential_paths | 🔴 critical | `consolidated_audit_report.md` | 21 |
| 3 | unknown | credential_paths | 🔴 critical | `consolidated_audit_report.md` | 33 |
| 4 | unknown | credential_paths | 🔴 critical | `consolidated_audit_report.md` | 39 |
| 5 | unknown | credential_paths | 🔴 critical | `consolidated_audit_report.md` | 40 |
| 6 | unknown | crypto_miner | 🔴 critical | `skill_audit_report.json` | 144 |
| 7 | unknown | crypto_miner | 🔴 critical | `skill_audit_report.json` | 153 |
| 8 | unknown | crypto_miner | 🔴 critical | `skill_audit_report.json` | 189 |
| 9 | unknown | credential_paths | 🔴 critical | `system_skills_audit.md` | 29 |
| 10 | unknown | credential_paths | 🔴 critical | `system_skills_audit.md` | 36 |
| 11 | unknown | credential_paths | 🔴 critical | `system_skills_audit.md` | 43 |
| 12 | unknown | credential_paths | 🔴 critical | `system_skills_audit.md` | 50 |
| 13 | unknown | credential_paths | 🔴 critical | `system_skills_audit.md` | 57 |
| 14 | unknown | credential_paths | 🔴 critical | `system_skills_audit.md` | 64 |
| 15 | unknown | credential_paths | 🔴 critical | `system_skills_audit.md` | 71 |
| 16 | unknown | credential_paths | 🔴 critical | `system_skills_audit.md` | 78 |
| 17 | unknown | credential_paths | 🔴 critical | `system_skills_audit.md` | 85 |
| 18 | unknown | credential_paths | 🔴 critical | `system_skills_audit.md` | 92 |
| 19 | unknown | credential_paths | 🔴 critical | `system_skills_audit.md` | 99 |
| 20 | unknown | credential_paths | 🔴 critical | `system_skills_audit.md` | 106 |
| 21 | unknown | credential_paths | 🔴 critical | `system_skills_audit.md` | 113 |
| 22 | unknown | credential_paths | 🔴 critical | `system_skills_audit.md` | 120 |
| 23 | unknown | credential_paths | 🔴 critical | `system_skills_audit.md` | 127 |
| 24 | unknown | credential_paths | 🔴 critical | `system_skills_audit.md` | 134 |
| 25 | unknown | credential_paths | 🔴 critical | `system_skills_audit.md` | 141 |
| 26 | unknown | credential_paths | 🔴 critical | `system_skills_audit.md` | 148 |
| 27 | unknown | credential_paths | 🔴 critical | `system_skills_audit.md` | 155 |
| 28 | unknown | credential_paths | 🔴 critical | `user_skills_audit.md` | 29 |
| 29 | unknown | credential_paths | 🔴 critical | `user_skills_audit.md` | 36 |
| 30 | unknown | credential_paths | 🔴 critical | `user_skills_audit.md` | 43 |
| 31 | unknown | credential_paths | 🔴 critical | `user_skills_audit.md` | 50 |
| 32 | unknown | credential_paths | 🔴 critical | `user_skills_audit.md` | 57 |
| 33 | unknown | credential_paths | 🔴 critical | `user_skills_audit.md` | 64 |
| 34 | unknown | credential_paths | 🔴 critical | `user_skills_audit.md` | 71 |
| 35 | unknown | credential_paths | 🔴 critical | `user_skills_audit.md` | 92 |
| 36 | unknown | crypto_miner | 🔴 critical | `user_skills_audit.md` | 78 |
| 37 | unknown | crypto_miner | 🔴 critical | `user_skills_audit.md` | 85 |
| 38 | unknown | crypto_miner | 🔴 critical | `user_skills_audit.md` | 113 |
| 39 | unknown | credential_paths | 🔴 critical | `brain/README.md` | 61 |
| 40 | unknown | credential_paths | 🔴 critical | `brain/scripts/brain.py` | 62 |
| 41 | unknown | credential_paths | 🔴 critical | `skills/chartgen-ai/tools/chartgen_api.js` | 25 |
| 42 | unknown | credential_paths | 🔴 critical | `skills/chartgen-ai/tools/chartgen_api.js` | 40 |
| 43 | unknown | credential_paths | 🔴 critical | `skills/chartgen-ai/tools/chartgen_api.js` | 44 |
| 44 | unknown | credential_paths | 🔴 critical | `skills/chartgen-ai/tools/chartgen_api.js` | 45 |
| 45 | unknown | credential_paths | 🔴 critical | `skills/chartgen-ai/tools/chartgen_api.js` | 74 |
| 46 | unknown | credential_paths | 🔴 critical | `skills/daily_intel/cron/run_daily.py` | 19 |
| 47 | unknown | credential_paths | 🔴 critical | `skills/daily_intel/cron/run_daily.py` | 21 |
| 48 | unknown | credential_paths | 🔴 critical | `skills/daily_intel/scripts/_email_brief.py` | 19 |
| 49 | unknown | credential_paths | 🔴 critical | `skills/daily_intel/scripts/_email_brief.py` | 21 |
| 50 | unknown | credential_paths | 🔴 critical | `skills/daily_intel/scripts/_fetch_intel_emails.py` | 105 |
| 51 | unknown | credential_paths | 🔴 critical | `skills/daily_intel/scripts/_fetch_intel_emails.py` | 108 |
| 52 | unknown | credential_paths | 🔴 critical | `skills/daily_intel/scripts/improvement_daemon.py` | 29 |
| 53 | unknown | credential_paths | 🔴 critical | `skills/daily_intel/scripts/improvement_daemon.py` | 32 |
| 54 | unknown | credential_paths | 🔴 critical | `skills/daily_intel/scripts/improvement_daemon.py` | 41 |
| 55 | unknown | credential_paths | 🔴 critical | `skills/daily_intel/scripts/sonar_scout.py` | 70 |
| 56 | unknown | credential_paths | 🔴 critical | `skills/daily_intel/scripts/sonar_scout.py` | 71 |
| 57 | api-gateway | credential_paths | 🔴 critical | `SKILL.md` | 539 |
| 58 | gmail | credential_paths | 🔴 critical | `SKILL.md` | 267 |
| 59 | gog | credential_paths | 🔴 critical | `SKILL.md` | 23 |
| 60 | gog | credential_paths | 🔴 critical | `SKILL.md` | 24 |
| 61 | stripe | credential_paths | 🔴 critical | `SKILL.md` | 778 |
| 62 | video-translation | credential_paths | 🔴 critical | `SKILL.md` | 90 |
| 63 | whatsapp-business | credential_paths | 🔴 critical | `SKILL.md` | 494 |
| 64 | trevor-methodology | eval_exec | 🟠 high | `pipeline/docx-js-template.js` | 37 |
| 65 | unknown | http_post_external | 🟡 medium | `skills/daily_intel/deepseek_client.py` | 60 |
| 66 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/trevor_config.py` | 54 |
| 67 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/trevor_config.py` | 63 |
| 68 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/trevor_config.py` | 64 |
| 69 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/trevor_config.py` | 65 |
| 70 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/trevor_config.py` | 80 |
| 71 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/trevor_config.py` | 81 |
| 72 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/trevor_config.py` | 82 |
| 73 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/trevor_config.py` | 83 |
| 74 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/trevor_config.py` | 86 |
| 75 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/trevor_config.py` | 87 |
| 76 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/trevor_log.py` | 32 |
| 77 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/trevor_fonts.py` | 38 |
| 78 | unknown | env_scraping | 🟡 medium | `skills/agentmail/scripts/check_inbox.py` | 83 |
| 79 | unknown | env_scraping | 🟡 medium | `skills/agentmail/scripts/send_email.py` | 46 |
| 80 | unknown | env_scraping | 🟡 medium | `skills/agentmail/scripts/setup_webhook.py` | 51 |
| 81 | unknown | env_scraping | 🟡 medium | `skills/pdf-report/scripts/render_pdf.py` | 17 |
| 82 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/cron/run_daily.py` | 165 |
| 83 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/cron/run_daily.py` | 173 |
| 84 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/cron/run_daily.py` | 174 |
| 85 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/cron/run_daily.py` | 179 |
| 86 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/cron/run_daily.py` | 180 |
| 87 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/scripts/generate_assessments.py` | 134 |
| 88 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/scripts/_email_brief.py` | 16 |
| 89 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/scripts/_fetch_intel_emails.py` | 106 |
| 90 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/scripts/improvement_daemon.py` | 49 |
| 91 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/scripts/improvement_daemon.py` | 50 |
| 92 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/scripts/improvement_daemon.py` | 490 |
| 93 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/scripts/osint_collection_expansion.py` | 175 |
| 94 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/scripts/scrape_creators.py` | 29 |
| 95 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/scripts/sonar_scout.py` | 76 |
| 96 | unknown | env_scraping | 🟡 medium | `skills/daily_intel/scripts/sonar_scout.py` | 216 |
| 97 | gog | http_post_external | 🟡 medium | `config/exchange.py` | 16 |

---

## ✅ Approved Skills

- **answeroverflow** (1 files, 0 scripts) — `/home/ubuntu/.openclaw/skills/answeroverflow`
- **claude-code** (4 files, 0 scripts) — `/home/ubuntu/.openclaw/skills/claude-code`
- **unknown** (1 files, 0 scripts) — `/home/ubuntu/.openclaw/skills/daily_intel`
- **find-skills** (1 files, 0 scripts) — `/home/ubuntu/.openclaw/skills/find-skills`
- **huggingface-hub** (1 files, 0 scripts) — `/home/ubuntu/.openclaw/skills/huggingface-hub`
- **humanizer** (1 files, 0 scripts) — `/home/ubuntu/.openclaw/skills/humanizer`
- **maps** (1 files, 0 scripts) — `/home/ubuntu/.openclaw/skills/maps-new`
- **nano-pdf** (1 files, 0 scripts) — `/home/ubuntu/.openclaw/skills/nano-pdf`
- **Network Analysis** (3 files, 2 scripts) — `/home/ubuntu/.agents/skills/network-analysis`
- **ocr-and-documents** (4 files, 0 scripts) — `/home/ubuntu/.openclaw/skills/ocr-docu`
- **self-improvement** (1 files, 0 scripts) — `/home/ubuntu/.openclaw/skills/self-improving-agent`
- **stock-market-pro** (1 files, 0 scripts) — `/home/ubuntu/.openclaw/skills/stock-market-pro`
- **timeline-chart** (5 files, 1 scripts) — `/home/ubuntu/.openclaw/skills/timeline-chart`
- **video-frames** (1 files, 0 scripts) — `/home/ubuntu/.openclaw/skills/video-frames`
- **wacli** (1 files, 0 scripts) — `/home/ubuntu/.openclaw/skills/wacli`
- **web-search-plus** (1 files, 0 scripts) — `/home/ubuntu/.openclaw/skills/web-searchplus`
- **xurl** (1 files, 0 scripts) — `/home/ubuntu/.openclaw/skills/xurl`
- **youtube-content** (1 files, 0 scripts) — `/home/ubuntu/.openclaw/skills/youtube-content`
- **1password** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/1password`
- **apple-notes** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/apple-notes`
- **apple-reminders** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/apple-reminders`
- **bear-notes** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/bear-notes`
- **blogwatcher** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/blogwatcher`
- **blucli** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/blucli`
- **bluebubbles** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/bluebubbles`
- **camsnap** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/camsnap`
- **unknown** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/canvas`
- **clawhub** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/clawhub`
- **coding-agent** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/coding-agent`
- **discord** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/discord`
- **eightctl** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/eightctl`
- **gemini** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/gemini`
- **gh-issues** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/gh-issues`
- **gifgrep** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/gifgrep`
- **github** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/github`
- **gog** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/gog`
- **goplaces** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/goplaces`
- **healthcheck** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/healthcheck`
- **himalaya** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/himalaya`
- **imsg** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/imsg`
- **mcporter** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/mcporter`
- **model-usage** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/model-usage`
- **nano-pdf** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/nano-pdf`
- **node-connect** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/node-connect`
- **notion** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/notion`
- **obsidian** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/obsidian`
- **openai-whisper** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/openai-whisper`
- **openai-whisper-api** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/openai-whisper-api`
- **openhue** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/openhue`
- **oracle** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/oracle`
- **ordercli** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/ordercli`
- **peekaboo** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/peekaboo`
- **sag** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/sag`
- **session-logs** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/session-logs`
- **sherpa-onnx-tts** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/sherpa-onnx-tts`
- **skill-creator** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/skill-creator`
- **slack** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/slack`
- **songsee** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/songsee`
- **sonoscli** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/sonoscli`
- **spotify-player** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/spotify-player`
- **summarize** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/summarize`
- **taskflow** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/taskflow`
- **taskflow-inbox-triage** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/taskflow-inbox-triage`
- **things-mac** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/things-mac`
- **tmux** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/tmux`
- **trello** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/trello`
- **video-frames** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/video-frames`
- **voice-call** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/voice-call`
- **wacli** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/wacli`
- **weather** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/weather`
- **xurl** (0 files, 0 scripts) — `/usr/lib/node_modules/openclaw/skills/xurl`

---
*Report generated by Daily Skill Scanner Audit cron — 2026-05-20 00:00 UTC*