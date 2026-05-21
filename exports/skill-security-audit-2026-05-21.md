# 🔒 Daily Skill Security Audit Report

**Date:** 2026-05-21 00:00 UTC
**Tool:** Skill Scanner v1.0

---

## Executive Summary

- **Total skills scanned:** 133
- **✅ Approved:** 118
- **⚠️ Caution (high-severity):** 1
- **🔴 Rejected (critical-severity):** 14
- **Scan errors:** 0

- **Total findings:** 405
  - Critical: 179
  - High: 122
  - Medium: 104
  - Low: 0

---

## Verdict Summary

| Skill | Verdict | Findings | Key Issues |
|-------|---------|----------|------------|
| unknown | 🔴 REJECT | 88 | credential_paths, crypto_miner, env_scraping, http_post_external |
| answeroverflow | 🟢 APPROVED | 0 | None |
| api-gateway | 🔴 REJECT | 1 | credential_paths |
| claude-code | 🟢 APPROVED | 0 | None |
| unknown | 🟢 APPROVED | 0 | None |
| find-skills | 🟢 APPROVED | 0 | None |
| gmail | 🔴 REJECT | 1 | credential_paths |
| gog | 🔴 REJECT | 3 | credential_paths, http_post_external |
| huggingface-hub | 🟢 APPROVED | 0 | None |
| humanizer | 🟢 APPROVED | 0 | None |
| maps | 🟢 APPROVED | 0 | None |
| mobula | 🟢 APPROVED | 0 | None |
| nano-pdf | 🟢 APPROVED | 0 | None |
| Network Analysis | 🟢 APPROVED | 0 | None |
| ocr-and-documents | 🟢 APPROVED | 0 | None |
| flight-tracker | 🟢 APPROVED | 0 | None |
| self-improvement | 🟢 APPROVED | 0 | None |
| skill-scanner | 🔴 REJECT | 9 | base64_decode_exec, credential_paths, crontab_modify, crypto_miner, reverse_shell, systemd_modify |
| stock-market-pro | 🟢 APPROVED | 0 | None |
| stripe | 🔴 REJECT | 1 | credential_paths |
| timeline-chart | 🟢 APPROVED | 0 | None |
| trevor-methodology | 🟡 CAUTION | 1 | eval_exec |
| video-frames | 🟢 APPROVED | 0 | None |
| video-translation | 🔴 REJECT | 1 | credential_paths |
| wacli | 🟢 APPROVED | 0 | None |
| web-search-plus | 🟢 APPROVED | 0 | None |
| whatsapp-business | 🔴 REJECT | 1 | credential_paths |
| xurl | 🟢 APPROVED | 0 | None |
| youtube-content | 🟢 APPROVED | 0 | None |
| agent-intelligence | 🟢 APPROVED | 0 | None |
| agentmail | 🟢 APPROVED | 3 | env_scraping |
| akashic-doc-analyzer | 🟢 APPROVED | 0 | None |
| baoyu-translate | 🟢 APPROVED | 0 | None |
| bluf-report | 🟢 APPROVED | 0 | None |
| chartgen | 🔴 REJECT | 5 | credential_paths |
| trevor-web-collection | 🔴 REJECT | 229 | bulk_env_access, credential_paths, download_execute, env_scraping, eval_exec, http_post_external |
| content-generation | 🟢 APPROVED | 0 | None |
| Content Marketing | 🟢 APPROVED | 0 | None |
| corpusgraph | 🟢 APPROVED | 0 | None |
| social-poster | 🟢 APPROVED | 0 | None |
| daily-intel-brief | 🔴 REJECT | 11 | bulk_env_access, credential_paths, env_scraping |
| Data Analysis | 🟢 APPROVED | 0 | None |
| data-charts-visualization | 🟢 APPROVED | 0 | None |
| data-visualization-studio | 🟢 APPROVED | 0 | None |
| genviral | 🔴 REJECT | 2 | credential_paths |
| geopolitics-expert | 🟢 APPROVED | 0 | None |
| geospatial-osint | 🟢 APPROVED | 0 | None |
| graph-analysis | 🟢 APPROVED | 0 | None |
| indicators-and-warnings | 🟢 APPROVED | 0 | None |
| landing-page-generator | 🟢 APPROVED | 0 | None |
| landing-page-roast | 🟢 APPROVED | 0 | None |
| unknown | 🟢 APPROVED | 0 | None |
| mapbox-data-visualization-patterns | 🟢 APPROVED | 0 | None |
| mapbox-geospatial-operations | 🟢 APPROVED | 0 | None |
| unknown | 🟢 APPROVED | 0 | None |
| News | 🟢 APPROVED | 0 | None |
| Newsletter | 🟢 APPROVED | 0 | None |
| newsletter-creation-curation | 🟢 APPROVED | 0 | None |
| oraclaw-graph | 🟢 APPROVED | 0 | None |
| pdf-report | 🟢 APPROVED | 1 | env_scraping |
| polymarket-trader | 🟢 APPROVED | 10 | env_scraping |
| unknown | 🟢 APPROVED | 0 | None |
| My skill | 🟢 APPROVED | 0 | None |
| unknown | 🟢 APPROVED | 0 | None |
| sat-toolkit | 🟢 APPROVED | 0 | None |
| scraper | 🟢 APPROVED | 0 | None |
| unknown | 🟢 APPROVED | 0 | None |
| skill-stripe-monitor | 🟢 APPROVED | 0 | None |
| social-intelligence | 🟢 APPROVED | 0 | None |
| social-media-agent | 🟢 APPROVED | 0 | None |
| Social Media Scheduler | 🟢 APPROVED | 0 | None |
| SocialPack Multi-Platform Social Media Generator | 🟢 APPROVED | 0 | None |
| social-post | 🔴 REJECT | 36 | credential_paths |
| unknown | 🟢 APPROVED | 0 | None |
| source-evaluation | 🟢 APPROVED | 0 | None |
| unknown | 🟢 APPROVED | 0 | None |
| Threat Intelligence Aggregator | 🟢 APPROVED | 0 | None |
| unknown | 🔴 REJECT | 1 | credential_paths |
| translate | 🟢 APPROVED | 0 | None |
| visual_production | 🟢 APPROVED | 1 | env_scraping |
| 1password | 🟢 APPROVED | 0 | None |
| apple-notes | 🟢 APPROVED | 0 | None |
| apple-reminders | 🟢 APPROVED | 0 | None |
| bear-notes | 🟢 APPROVED | 0 | None |
| blogwatcher | 🟢 APPROVED | 0 | None |
| blucli | 🟢 APPROVED | 0 | None |
| bluebubbles | 🟢 APPROVED | 0 | None |
| camsnap | 🟢 APPROVED | 0 | None |
| unknown | 🟢 APPROVED | 0 | None |
| clawhub | 🟢 APPROVED | 0 | None |
| coding-agent | 🟢 APPROVED | 0 | None |
| discord | 🟢 APPROVED | 0 | None |
| eightctl | 🟢 APPROVED | 0 | None |
| gemini | 🟢 APPROVED | 0 | None |
| gh-issues | 🟢 APPROVED | 0 | None |
| gifgrep | 🟢 APPROVED | 0 | None |
| github | 🟢 APPROVED | 0 | None |
| gog | 🟢 APPROVED | 0 | None |
| goplaces | 🟢 APPROVED | 0 | None |
| healthcheck | 🟢 APPROVED | 0 | None |
| himalaya | 🟢 APPROVED | 0 | None |
| imsg | 🟢 APPROVED | 0 | None |
| mcporter | 🟢 APPROVED | 0 | None |
| model-usage | 🟢 APPROVED | 0 | None |
| nano-pdf | 🟢 APPROVED | 0 | None |
| node-connect | 🟢 APPROVED | 0 | None |
| notion | 🟢 APPROVED | 0 | None |
| obsidian | 🟢 APPROVED | 0 | None |
| openai-whisper | 🟢 APPROVED | 0 | None |
| openai-whisper-api | 🟢 APPROVED | 0 | None |
| openhue | 🟢 APPROVED | 0 | None |
| oracle | 🟢 APPROVED | 0 | None |
| ordercli | 🟢 APPROVED | 0 | None |
| peekaboo | 🟢 APPROVED | 0 | None |
| sag | 🟢 APPROVED | 0 | None |
| session-logs | 🟢 APPROVED | 0 | None |
| sherpa-onnx-tts | 🟢 APPROVED | 0 | None |
| skill-creator | 🟢 APPROVED | 0 | None |
| slack | 🟢 APPROVED | 0 | None |
| songsee | 🟢 APPROVED | 0 | None |
| sonoscli | 🟢 APPROVED | 0 | None |
| spotify-player | 🟢 APPROVED | 0 | None |
| summarize | 🟢 APPROVED | 0 | None |
| taskflow | 🟢 APPROVED | 0 | None |
| taskflow-inbox-triage | 🟢 APPROVED | 0 | None |
| things-mac | 🟢 APPROVED | 0 | None |
| tmux | 🟢 APPROVED | 0 | None |
| trello | 🟢 APPROVED | 0 | None |
| video-frames | 🟢 APPROVED | 0 | None |
| voice-call | 🟢 APPROVED | 0 | None |
| wacli | 🟢 APPROVED | 0 | None |
| weather | 🟢 APPROVED | 0 | None |
| xurl | 🟢 APPROVED | 0 | None |

---

## Critical Findings

| Skill | Pattern | File | Line | Description |
|-------|---------|------|------|-------------|
| unknown | credential_paths | `audit_skills.py:6` | `The raw scanner regex-matches strings like `~/.config` and `Bearer ${...}` as` | Accesses sensitive credential locations |
| unknown | credential_paths | `consolidated_audit_report.md:21` | `2. **Credential Paths:** Multiple skills (`gmail`, `gog-myclaw`, `api-gateway`, ` | Accesses sensitive credential locations |
| unknown | credential_paths | `consolidated_audit_report.md:33` | `2. **Config Locations:** Skills such as `eightctl`, `camsnap`, and `spotify-play` | Accesses sensitive credential locations |
| unknown | credential_paths | `consolidated_audit_report.md:39` | `2. **Audit Config Access:** Ensure that skills accessing `~/.config` are only do` | Accesses sensitive credential locations |
| unknown | credential_paths | `consolidated_audit_report.md:40` | `3. **Ignore Documentation Flags:** Findings inside `SKILL.md` files that merely ` | Accesses sensitive credential locations |
| unknown | crypto_miner | `skill_audit_report.json:144` | `"line_content": "- Catches **crypto-mining** indicators (xmrig, mining pools, wa` | Cryptocurrency mining indicators |
| unknown | crypto_miner | `skill_audit_report.json:153` | `"line_content": "- Crypto miners (xmrig, ethminer, stratum+tcp)",` | Cryptocurrency mining indicators |
| unknown | crypto_miner | `skill_audit_report.json:189` | `"line_content": "\"pattern\": r\"xmrig|ethminer|cpuminer|cgminer|stratum\\+tcp|m` | Cryptocurrency mining indicators |
| unknown | credential_paths | `system_skills_audit.md:29` | `- **Code:** `- Config: `~/.config/eightctl/config.yaml``` | Accesses sensitive credential locations |
| unknown | credential_paths | `system_skills_audit.md:36` | `- **Code:** `- Config file: `~/.config/camsnap/config.yaml``` | Accesses sensitive credential locations |
| unknown | credential_paths | `system_skills_audit.md:43` | `- **Code:** `- Config folder: `~/.config/spotify-player` (e.g., `app.toml`).`` | Accesses sensitive credential locations |
| unknown | credential_paths | `system_skills_audit.md:50` | `- **Code:** `- For some operations (add-text, tags, open-note --selected), a Bea` | Accesses sensitive credential locations |
| unknown | credential_paths | `system_skills_audit.md:57` | `- **Code:** `2. Save it: `echo "YOUR_TOKEN" > ~/.config/grizzly/token``` | Accesses sensitive credential locations |
| unknown | credential_paths | `system_skills_audit.md:64` | `- **Code:** `echo "Additional content" | grizzly add-text --id "NOTE_ID" --mode ` | Accesses sensitive credential locations |
| unknown | credential_paths | `system_skills_audit.md:71` | `- **Code:** `grizzly tags --enable-callback --json --token-file ~/.config/grizzl` | Accesses sensitive credential locations |
| unknown | credential_paths | `system_skills_audit.md:78` | `- **Code:** `4. `~/.config/grizzly/config.toml``` | Accesses sensitive credential locations |
| unknown | credential_paths | `system_skills_audit.md:85` | `- **Code:** `Example `~/.config/grizzly/config.toml`:`` | Accesses sensitive credential locations |
| unknown | credential_paths | `system_skills_audit.md:92` | `- **Code:** `token_file = "~/.config/grizzly/token"`` | Accesses sensitive credential locations |
| unknown | credential_paths | `system_skills_audit.md:99` | `- **Code:** `2. A configuration file at `~/.config/himalaya/config.toml``` | Accesses sensitive credential locations |
| unknown | credential_paths | `system_skills_audit.md:106` | `- **Code:** `Or create `~/.config/himalaya/config.toml` manually:`` | Accesses sensitive credential locations |
| unknown | credential_paths | `system_skills_audit.md:113` | `- **Code:** `- Don’t attach secrets by default (`.env`, key files, auth tokens).` | Accesses sensitive credential locations |
| unknown | credential_paths | `system_skills_audit.md:120` | `- **Code:** `mkdir -p ~/.config/notion`` | Accesses sensitive credential locations |
| unknown | credential_paths | `system_skills_audit.md:127` | `- **Code:** `echo "ntn_your_key_here" > ~/.config/notion/api_key`` | Accesses sensitive credential locations |
| unknown | credential_paths | `system_skills_audit.md:134` | `- **Code:** `NOTION_KEY=$(cat ~/.config/notion/api_key)`` | Accesses sensitive credential locations |
| unknown | credential_paths | `system_skills_audit.md:141` | `- **Code:** `- `op run --env-file="./.env" -- printenv DB_PASSWORD``` | Accesses sensitive credential locations |
| unknown | credential_paths | `system_skills_audit.md:148` | `- **Code:** `- Claude: ~/.config/claude/projects/**/\*.jsonl or ~/.claude/projec` | Accesses sensitive credential locations |
| unknown | credential_paths | `system_skills_audit.md:155` | `- **Code:** `Configuration file location: `~/.config/himalaya/config.toml``` | Accesses sensitive credential locations |
| unknown | credential_paths | `user_skills_audit.md:29` | `- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}``` | Accesses sensitive credential locations |
| unknown | credential_paths | `user_skills_audit.md:36` | `- **Code:** `3. Once they provide the `credentials.json` content, save it to `~/` | Accesses sensitive credential locations |
| unknown | credential_paths | `user_skills_audit.md:43` | `- **Code:** `4. Run: `gog auth credentials set ~/.config/gogcli/credentials.json` | Accesses sensitive credential locations |
| unknown | credential_paths | `user_skills_audit.md:50` | `- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}``` | Accesses sensitive credential locations |
| unknown | credential_paths | `user_skills_audit.md:57` | `- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}``` | Accesses sensitive credential locations |
| unknown | credential_paths | `user_skills_audit.md:64` | `- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}`,`` | Accesses sensitive credential locations |
| unknown | credential_paths | `user_skills_audit.md:71` | `- **Code:** `- Credential path access (~/.ssh, ~/.aws, /etc/passwd)`` | Accesses sensitive credential locations |
| unknown | credential_paths | `user_skills_audit.md:92` | `- **Code:** `"pattern": r"~/\.ssh|~/\.aws|~/\.config|/etc/passwd|\.env\b|\.crede` | Accesses sensitive credential locations |
| unknown | crypto_miner | `user_skills_audit.md:78` | `- **Code:** `- Catches **crypto-mining** indicators (xmrig, mining pools, wallet` | Cryptocurrency mining indicators |
| unknown | crypto_miner | `user_skills_audit.md:85` | `- **Code:** `- Crypto miners (xmrig, ethminer, stratum+tcp)`` | Cryptocurrency mining indicators |
| unknown | crypto_miner | `user_skills_audit.md:113` | `- **Code:** `"pattern": r"xmrig|ethminer|cpuminer|cgminer|stratum\+tcp|mining.*p` | Cryptocurrency mining indicators |
| unknown | credential_paths | `brain/README.md:61` | `- Don't index secrets. The indexer skips `.env`, `*.key`, `*.pem`,` | Accesses sensitive credential locations |
| unknown | credential_paths | `brain/scripts/brain.py:62` | `re.compile(r"\.env$"),` | Accesses sensitive credential locations |
| unknown | credential_paths | `skills/chartgen-ai/tools/chartgen_api.js:25` | `const BASE_URL = process.env.CHARTGEN_API_URL || "https://chartgen.ai";` | Accesses sensitive credential locations |
| unknown | credential_paths | `skills/chartgen-ai/tools/chartgen_api.js:40` | `if (process.env.CHARTGEN_API_KEY) return process.env.CHARTGEN_API_KEY;` | Accesses sensitive credential locations |
| unknown | credential_paths | `skills/chartgen-ai/tools/chartgen_api.js:44` | `process.env.OPENCLAW_STATE_DIR` | Accesses sensitive credential locations |
| unknown | credential_paths | `skills/chartgen-ai/tools/chartgen_api.js:45` | `? path.join(process.env.OPENCLAW_STATE_DIR, "skills", "chartgen", "config.json")` | Accesses sensitive credential locations |
| unknown | credential_paths | `skills/chartgen-ai/tools/chartgen_api.js:74` | `const stateDir = process.env.OPENCLAW_STATE_DIR;` | Accesses sensitive credential locations |
| unknown | credential_paths | `skills/daily_intel/cron/run_daily.py:19` | `# Load environment from workspace .env (cron may not have it in env)` | Accesses sensitive credential locations |
| unknown | credential_paths | `skills/daily_intel/cron/run_daily.py:21` | `WORKSPACE_ENV = WORKSPACE / '.env'` | Accesses sensitive credential locations |
| unknown | credential_paths | `skills/daily_intel/scripts/_email_brief.py:19` | `# Try reading from workspace .env` | Accesses sensitive credential locations |
| unknown | credential_paths | `skills/daily_intel/scripts/_email_brief.py:21` | `env_path = str(WORKSPACE / ".env")` | Accesses sensitive credential locations |
| unknown | credential_paths | `skills/daily_intel/scripts/_fetch_intel_emails.py:105` | `"""Read MATON_API_KEY from env or workspace .env."""` | Accesses sensitive credential locations |
| unknown | credential_paths | `skills/daily_intel/scripts/_fetch_intel_emails.py:108` | `env_path = os.path.expanduser("~/.openclaw/workspace/.env")` | Accesses sensitive credential locations |
| unknown | credential_paths | `skills/daily_intel/scripts/improvement_daemon.py:29` | `# Load .env for subprocess environment inheritance` | Accesses sensitive credential locations |
| unknown | credential_paths | `skills/daily_intel/scripts/improvement_daemon.py:32` | `env_path = Path.home() / '.openclaw' / 'workspace' / '.env'` | Accesses sensitive credential locations |
| unknown | credential_paths | `skills/daily_intel/scripts/improvement_daemon.py:41` | `env_path = Path.home() / '.openclaw' / 'workspace' / '.env'` | Accesses sensitive credential locations |
| unknown | credential_paths | `skills/daily_intel/scripts/sonar_scout.py:70` | `"""Get OpenRouter API key from workspace .env."""` | Accesses sensitive credential locations |
| unknown | credential_paths | `skills/daily_intel/scripts/sonar_scout.py:71` | `env_path = WORKSPACE / ".env"` | Accesses sensitive credential locations |
| api-gateway | credential_paths | `SKILL.md:539` | `'Authorization': `Bearer ${process.env.MATON_API_KEY}`` | Accesses sensitive credential locations |
| gmail | credential_paths | `SKILL.md:267` | `'Authorization': `Bearer ${process.env.MATON_API_KEY}`` | Accesses sensitive credential locations |
| gog | credential_paths | `SKILL.md:23` | `3. Once they provide the `credentials.json` content, save it to `~/.config/gogcl` | Accesses sensitive credential locations |
| gog | credential_paths | `SKILL.md:24` | `4. Run: `gog auth credentials set ~/.config/gogcli/credentials.json`` | Accesses sensitive credential locations |
| skill-scanner | credential_paths | `README.md:155` | `- Credential path access (~/.ssh, ~/.aws, /etc/passwd)` | Accesses sensitive credential locations |
| skill-scanner | crypto_miner | `README.md:9` | `- Catches **crypto-mining** indicators (xmrig, mining pools, wallet addresses)` | Cryptocurrency mining indicators |
| skill-scanner | crypto_miner | `README.md:158` | `- Crypto miners (xmrig, ethminer, stratum+tcp)` | Cryptocurrency mining indicators |
| skill-scanner | credential_paths | `skill_scanner.py:101` | `"pattern": r"~/\.ssh|~/\.aws|~/\.config|/etc/passwd|\.env\b|\.credentials|keycha` | Accesses sensitive credential locations |
| skill-scanner | systemd_modify | `skill_scanner.py:126` | `"pattern": r"systemctl\s+enable|systemctl\s+start|/etc/systemd|launchctl\s+load"` | Creates system services for persistence |
| skill-scanner | crypto_miner | `skill_scanner.py:135` | `"pattern": r"xmrig|ethminer|cpuminer|cgminer|stratum\+tcp|mining.*pool|hashrate"` | Cryptocurrency mining indicators |
| skill-scanner | reverse_shell | `skill_scanner.py:161` | `"pattern": r"/dev/tcp/|nc\s+-e|bash\s+-i\s+>&|python.*pty\.spawn",` | Reverse shell pattern detected |
| skill-scanner | base64_decode_exec | `skill_scanner.py:170` | `"pattern": r"base64\.b64decode.*exec|atob.*eval",` | Decodes and executes base64 - classic obfuscation |
| stripe | credential_paths | `SKILL.md:778` | `'Authorization': `Bearer ${process.env.MATON_API_KEY}`` | Accesses sensitive credential locations |
| video-translation | credential_paths | `SKILL.md:90` | `- `NOIZ_API_KEY` configured for the Noiz backend. If it is not set, first guide ` | Accesses sensitive credential locations |
| whatsapp-business | credential_paths | `SKILL.md:494` | `'Authorization': `Bearer ${process.env.MATON_API_KEY}`,` | Accesses sensitive credential locations |
| chartgen | credential_paths | `tools/chartgen_api.js:25` | `const BASE_URL = process.env.CHARTGEN_API_URL || "https://chartgen.ai";` | Accesses sensitive credential locations |
| chartgen | credential_paths | `tools/chartgen_api.js:40` | `if (process.env.CHARTGEN_API_KEY) return process.env.CHARTGEN_API_KEY;` | Accesses sensitive credential locations |
| chartgen | credential_paths | `tools/chartgen_api.js:44` | `process.env.OPENCLAW_STATE_DIR` | Accesses sensitive credential locations |
| chartgen | credential_paths | `tools/chartgen_api.js:45` | `? path.join(process.env.OPENCLAW_STATE_DIR, "skills", "chartgen", "config.json")` | Accesses sensitive credential locations |
| chartgen | credential_paths | `tools/chartgen_api.js:74` | `const stateDir = process.env.OPENCLAW_STATE_DIR;` | Accesses sensitive credential locations |
| trevor-web-collection | download_execute | `openweb/install-skill.sh:5` | `#   curl -fsSL https://raw.githubusercontent.com/openweb-org/openweb/main/instal` | Downloads and executes remote code |
| trevor-web-collection | credential_paths | `reverse-api-engineer/RELEASING.md:40` | `source .env  # or export UV_PUBLISH_TOKEN manually` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/scripts/pack-check.js:14` | `const forbidden = ['.ts', 'src/', 'tests/', 'capture/', 'node_modules/', '.env']` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/doc/main/security.md:121` | `Under `process.env.VITEST`, any operation with permission category `write`, `del` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/commands/browser.ts:23` | `return join(process.env.LOCALAPPDATA ?? join(homedir(), 'AppData', 'Local'), 'Go` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/lib/adapter-helpers.ts:71` | `credentials: args.credentials as RequestCredentials,` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/lib/adapter-helpers.ts:90` | `credentials: options.credentials ?? 'include',` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/lib/config.test.ts:20` | `originalHome = process.env.OPENWEB_HOME` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/lib/config.test.ts:21` | `process.env.OPENWEB_HOME = tmpDir` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/lib/config.test.ts:26` | `Reflect.deleteProperty(process.env, 'OPENWEB_HOME')` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/lib/config.test.ts:28` | `process.env.OPENWEB_HOME = originalHome` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/lib/config.ts:18` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), '.openweb')` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/runtime/http-executor.ts:121` | `if (process.env.VITEST && (category === 'write' || category === 'delete' || cate` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/runtime/primitives/primitives.test.ts:870` | `chunk_global: 'process.env',` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/costco/PROGRESS.md:9` | `- Identified required custom headers: `client-identifier`, `costco.env`, `costco` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/costco/PROGRESS.md:11` | `- Fixed product 404 by adding `costco.env: ecom` and `costco.service: restProduc` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/bluesky/adapters/bluesky-public.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/booking/adapters/booking.ts:267` | `// Try to get from booking.env on the current page` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/booking/adapters/booking.ts:270` | `const hotelEnv = env?.env as Record<string, unknown> | undefined` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/booking/adapters/booking.js:163` | `const hotelEnv = env?.env;` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/boss/adapters/boss.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/coingecko/adapters/coingecko.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/coinmarketcap/adapters/coinmarketcap.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/costco/adapters/costco-api.ts:190` | `'costco.env': 'ecom',` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/costco/adapters/costco-api.ts:271` | `'costco.env': 'ecom',` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/costco/adapters/costco-api.ts:445` | `'costco.env': 'ecom',` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/costco/adapters/costco-api.ts:584` | `'costco.env': 'ecom',` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/costco/adapters/costco-api.ts:769` | `'costco.env': 'ecom',` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/costco/adapters/costco-api.ts:814` | `'costco.env': 'ecom',` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/costco/adapters/costco-api.js:134` | `"costco.env": "ecom",` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/costco/adapters/costco-api.js:199` | `"costco.env": "ecom",` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/costco/adapters/costco-api.js:340` | `"costco.env": "ecom",` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/costco/adapters/costco-api.js:456` | `"costco.env": "ecom",` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/costco/adapters/costco-api.js:605` | `"costco.env": "ecom",` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/costco/adapters/costco-api.js:642` | `"costco.env": "ecom",` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/docker-hub/adapters/docker-hub.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/douban/adapters/douban-read.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/ebay/adapters/ebay.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/espn/adapters/espn.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/github/adapters/github-read.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/gitlab/adapters/gitlab.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/goodreads/adapters/goodreads.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/google-flights/adapters/google-flights.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/guardian/adapters/guardian.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/huggingface/adapters/huggingface.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/imdb/adapters/imdb.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/npm/adapters/npm.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/npr/adapters/npr.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/pypi/adapters/pypi.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/reddit/adapters/reddit-read.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/redfin/adapters/redfin.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/rotten-tomatoes/adapters/rotten-tomatoes-web.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/soundcloud/adapters/soundcloud.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/stackoverflow/adapters/stackoverflow.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/steam/adapters/steam.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/substack/adapters/substack.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/techcrunch/adapters/techcrunch.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/yahoo-finance/adapters/yahoo-finance.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/yelp/adapters/yelp.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/src/sites/zhihu/adapters/zhihu-read.js:7` | `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `openweb/tests/integration/runner.ts:14` | `const CDP_ENDPOINT = process.env.CDP_ENDPOINT ?? 'http://localhost:9222'` | Accesses sensitive credential locations |
| trevor-web-collection | credential_paths | `reverse-api-engineer/src/reverse_api/browser.py:326` | `"--use-mock-keychain",` | Accesses sensitive credential locations |
| daily-intel-brief | credential_paths | `scripts/collect.py:510` | `# Load .env for BRAVE_API_KEY and other secrets` | Accesses sensitive credential locations |
| daily-intel-brief | credential_paths | `scripts/collect.py:511` | `_env = pathlib.Path("/home/ubuntu/.openclaw/workspace/.env")` | Accesses sensitive credential locations |
| genviral | credential_paths | `scripts/genviral.sh:192` | `[[ -f "${HOME}/.config/env/global.env" ]] && source "${HOME}/.config/env/global.` | Accesses sensitive credential locations |
| genviral | credential_paths | `scripts/genviral.sh:219` | `die "GENVIRAL_API_KEY is not set.\n  Set it via: export GENVIRAL_API_KEY=\"your_` | Accesses sensitive credential locations |
| social-post | credential_paths | `CHANGELOG.md:42` | `- Support for custom credential prefixes in `.env` file` | Accesses sensitive credential locations |
| social-post | credential_paths | `CHANGELOG.md:143` | `- ❌ Fixed `.env` file parsing error (quoted mnemonic)` | Accesses sensitive credential locations |
| social-post | credential_paths | `CHANGELOG.md:175` | `- Automatic credential loading from `.env` and Farcaster credentials file` | Accesses sensitive credential locations |
| social-post | credential_paths | `README.md:44` | `| **X/Twitter** | Pay-per-use (consumption-based) | `~/.openclaw/.env` | 5-10 mi` | Accesses sensitive credential locations |
| social-post | credential_paths | `README.md:91` | `**Step 3: Add to .env file**` | Accesses sensitive credential locations |
| social-post | credential_paths | `README.md:92` | `Location: `/home/phan_harry/.openclaw/.env`` | Accesses sensitive credential locations |
| social-post | credential_paths | `README.md:180` | `grep "^X_CONSUMER_KEY" ~/.openclaw/.env` | Accesses sensitive credential locations |
| social-post | credential_paths | `README.md:308` | `1. Check `.env` file exists: `ls -la ~/.openclaw/.env`` | Accesses sensitive credential locations |
| social-post | credential_paths | `README.md:311` | `grep "^X_" ~/.openclaw/.env` | Accesses sensitive credential locations |
| social-post | credential_paths | `README.md:314` | `4. Check file permissions: `chmod 600 ~/.openclaw/.env`` | Accesses sensitive credential locations |
| social-post | credential_paths | `SKILL.md:43` | `**Required credentials** (stored in `/home/phan_harry/.openclaw/.env`):` | Accesses sensitive credential locations |
| social-post | credential_paths | `SKILL.md:76` | `4. **Add to .env file**` | Accesses sensitive credential locations |
| social-post | credential_paths | `SKILL.md:78` | `echo "X_CONSUMER_KEY=xxx" >> ~/.openclaw/.env` | Accesses sensitive credential locations |
| social-post | credential_paths | `SKILL.md:79` | `echo "X_CONSUMER_SECRET=xxx" >> ~/.openclaw/.env` | Accesses sensitive credential locations |
| social-post | credential_paths | `SKILL.md:80` | `echo "X_ACCESS_TOKEN=xxx" >> ~/.openclaw/.env` | Accesses sensitive credential locations |
| social-post | credential_paths | `SKILL.md:81` | `echo "X_ACCESS_TOKEN_SECRET=xxx" >> ~/.openclaw/.env` | Accesses sensitive credential locations |
| social-post | credential_paths | `SKILL.md:98` | `echo "MYACCOUNT_API_KEY=xxx" >> ~/.openclaw/.env` | Accesses sensitive credential locations |
| social-post | credential_paths | `SKILL.md:99` | `echo "MYACCOUNT_API_KEY_SECRET=xxx" >> ~/.openclaw/.env` | Accesses sensitive credential locations |
| social-post | credential_paths | `SKILL.md:100` | `echo "MYACCOUNT_ACCESS_TOKEN=xxx" >> ~/.openclaw/.env` | Accesses sensitive credential locations |
| social-post | credential_paths | `SKILL.md:101` | `echo "MYACCOUNT_ACCESS_TOKEN_SECRET=xxx" >> ~/.openclaw/.env` | Accesses sensitive credential locations |
| social-post | credential_paths | `SKILL.md:179` | `- ⚠️ `.env` file should have `600` permissions (read/write owner only)` | Accesses sensitive credential locations |
| social-post | credential_paths | `SKILL.md:253` | `- `--account <name>` - Twitter account to use (lowercase prefix from .env)` | Accesses sensitive credential locations |
| social-post | credential_paths | `SKILL.md:266` | `- `--account <name>` - Twitter account to use (lowercase prefix from .env)` | Accesses sensitive credential locations |
| social-post | credential_paths | `SKILL.md:362` | `- Twitter credentials in `.env` (X_CONSUMER_KEY, X_CONSUMER_SECRET, X_ACCESS_TOK` | Accesses sensitive credential locations |
| social-post | credential_paths | `lib/farcaster.sh:30` | `const wallet = new Wallet(process.env.PRIVATE_KEY, baseProvider);` | Accesses sensitive credential locations |
| social-post | credential_paths | `lib/farcaster.sh:31` | `const signerBytes = Buffer.from(process.env.SIGNER_PRIVATE_KEY, 'hex');` | Accesses sensitive credential locations |
| social-post | credential_paths | `lib/farcaster.sh:33` | `const fid = parseInt(process.env.FID);` | Accesses sensitive credential locations |
| social-post | credential_paths | `lib/farcaster.sh:34` | `const parentHashBytes = Buffer.from(process.env.PARENT_HASH.replace('0x', ''), '` | Accesses sensitive credential locations |
| social-post | credential_paths | `lib/farcaster.sh:117` | `const wallet = new Wallet(process.env.PRIVATE_KEY, baseProvider);` | Accesses sensitive credential locations |
| social-post | credential_paths | `lib/farcaster.sh:118` | `const signerBytes = Buffer.from(process.env.SIGNER_PRIVATE_KEY, 'hex');` | Accesses sensitive credential locations |
| social-post | credential_paths | `lib/farcaster.sh:120` | `const fid = parseInt(process.env.FID);` | Accesses sensitive credential locations |
| social-post | credential_paths | `lib/farcaster.sh:121` | `const imageUrl = process.env.IMAGE_URL;` | Accesses sensitive credential locations |
| social-post | credential_paths | `lib/farcaster.sh:131` | `if (process.env.PARENT_HASH) {` | Accesses sensitive credential locations |
| social-post | credential_paths | `lib/farcaster.sh:132` | `const parentHashBytes = Buffer.from(process.env.PARENT_HASH.replace('0x', ''), '` | Accesses sensitive credential locations |
| social-post | credential_paths | `lib/twitter.sh:8` | `source /home/phan_harry/.openclaw/.env` | Accesses sensitive credential locations |
| social-post | credential_paths | `scripts/reply.sh:272` | `source /home/phan_harry/.openclaw/.env` | Accesses sensitive credential locations |
| unknown | credential_paths | `publishing/build-agent-brief.md:40` | `- Moltbook API key must be in .env or environment` | Accesses sensitive credential locations |

---

## High Severity Findings

| Skill | Pattern | File | Line | Description |
|-------|---------|------|------|-------------|
| skill-scanner | crontab_modify | `skill_scanner.py:118` | `"pattern": r"crontab\s+-|/etc/cron|schtasks\s+/create",` | Modifies system scheduled tasks |
| trevor-methodology | eval_exec | `pipeline/docx-js-template.js:37` | `const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/scripts/adapter-inventory.ts:121` | `const mCase = caseRe.exec(source)` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/scripts/adapter-inventory.ts:124` | `const nextCase = /\n\s*case\s+['\"][^'\"]+['\"]\s*:|\n\s*default\s*:/.exec(tail)` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/scripts/adapter-inventory.ts:131` | `const mRec = recRe.exec(source)` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/scripts/adapter-inventory.ts:139` | `const mFn = fnRe.exec(source)` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/capture/session.ts:111` | `/** Attach framenavigated listener; returns cleanup function (Leak #2 fix) */` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/lib/adapter-helpers.ts:350` | `const m = new RegExp(pattern).exec(value)` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/lib/template-resolver.ts:62` | `const wholeMatch = /^\$\{([^}]+)\}$/.exec(escaped)` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/compiler/analyzer/auth-candidates.ts:303` | `for (let match = metaRegex.exec(data.domHtml); match !== null; match = metaRegex` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/compiler/analyzer/classify.ts:40` | `const match = /<script\s+id="__NEXT_DATA__"\s+type="application\/json"[^>]*>/i.e` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/compiler/analyzer/classify.ts:63` | `for (let match = regex.exec(html); match !== null; match = regex.exec(html)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/compiler/analyzer/classify.ts:69` | `const idMatch = /id="([^"]+)"/i.exec(attrs)` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/compiler/analyzer/classify.ts:70` | `const dataTargetMatch = /data-target="([^"]+)"/i.exec(attrs)` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/compiler/analyzer/classify.ts:102` | `for (let m = regex.exec(html); m; m = regex.exec(html)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/compiler/analyzer/csrf-detect.ts:85` | `for (let match = metaRegex.exec(data.domHtml); match !== null; match = metaRegex` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/compiler/analyzer/graphql-cluster.ts:152` | `const match = OPERATION_NAME_RE.exec(query)` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/compiler/analyzer/graphql-cluster.ts:168` | `const match = OPERATION_TYPE_RE.exec(queryText)` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/compiler/curation/apply-curation.test.ts:177` | `it('is a pure function (same inputs → same output)', () => {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/runtime/primitives/page-expression.ts:12` | `'eval(',` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/runtime/primitives/page-expression.ts:13` | `'Function(',` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/runtime/primitives/page-expression.ts:46` | `return new Function(`return ${expr}`)() as unknown` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/runtime/primitives/primitives.test.ts:281` | `for (const malicious of ['fetch("http://evil.com")', 'document.cookie', 'eval("a` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/runtime/primitives/script-json-parse.ts:10` | `const m = HTML_COMMENT.exec(raw)` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/runtime/primitives/script-json-parse.ts:55` | `const match = /^([a-zA-Z_-][\w-]*)\s*=\s*"([^"]*)"$/.exec(clause) ?? /^([a-zA-Z_` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/runtime/primitives/script-json-parse.ts:88` | `const m = re.exec(attrsStr)` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/runtime/primitives/script-json-parse.ts:105` | `for (let m = SCRIPT_TAG_RE.exec(html); m; m = SCRIPT_TAG_RE.exec(html)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/runtime/primitives/script-json-parse.ts:116` | `for (let m = SCRIPT_TAG_RE.exec(html); m; m = SCRIPT_TAG_RE.exec(html)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/angellist/adapters/angellist.ts:125` | `await page.waitForFunction(() => !!(window as any).__APOLLO_CLIENT__, { timeout:` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/angellist/adapters/angellist.js:105` | `await page.waitForFunction(() => !!window.__APOLLO_CLIENT__, { timeout: 15e3 });` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/craigslist/adapters/craigslist.ts:62` | `for (m = resultRe.exec(html); m !== null; m = resultRe.exec(html)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/craigslist/adapters/craigslist.ts:129` | `for (tm = timeRe.exec(html); tm !== null; tm = timeRe.exec(html)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/craigslist/adapters/craigslist.ts:140` | `for (am = attrRe.exec(html); am !== null; am = attrRe.exec(html)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/craigslist/adapters/craigslist.ts:152` | `for (im = hrefRe.exec(thumbsMatch[1]); im !== null; im = hrefRe.exec(thumbsMatch` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/craigslist/adapters/craigslist.ts:173` | `for (lm = catRe.exec(html); lm !== null; lm = catRe.exec(html)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/craigslist/adapters/craigslist.js:42` | `for (m = resultRe.exec(html); m !== null; m = resultRe.exec(html)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/craigslist/adapters/craigslist.js:87` | `for (tm = timeRe.exec(html); tm !== null; tm = timeRe.exec(html)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/craigslist/adapters/craigslist.js:96` | `for (am = attrRe.exec(html); am !== null; am = attrRe.exec(html)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/craigslist/adapters/craigslist.js:106` | `for (im = hrefRe.exec(thumbsMatch[1]); im !== null; im = hrefRe.exec(thumbsMatch` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/craigslist/adapters/craigslist.js:120` | `for (lm = catRe.exec(html); lm !== null; lm = catRe.exec(html)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/github/adapters/github-web.ts:83` | `await page.waitForFunction(` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/github/adapters/github-web.js:27` | `await page.waitForFunction(` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/goodreads/adapters/goodreads.ts:60` | `for (rm = rowRe.exec(html); rm !== null; rm = rowRe.exec(html)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/goodreads/adapters/goodreads.ts:214` | `for (gm = genreRe.exec(html); gm !== null; gm = genreRe.exec(html)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/goodreads/adapters/goodreads.ts:227` | `for (bm = bookRowRe.exec(html); bm !== null; bm = bookRowRe.exec(html)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/goodreads/adapters/goodreads.js:494` | `for (rm = rowRe.exec(html); rm !== null; rm = rowRe.exec(html)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/goodreads/adapters/goodreads.js:608` | `for (gm = genreRe.exec(html); gm !== null; gm = genreRe.exec(html)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/goodreads/adapters/goodreads.js:617` | `for (bm = bookRowRe.exec(html); bm !== null; bm = bookRowRe.exec(html)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/google-flights/adapters/google-flights.ts:21` | `for (match = regex.exec(html); match !== null; match = regex.exec(html)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/google-flights/adapters/google-flights.js:458` | `for (match = regex.exec(html); match !== null; match = regex.exec(html)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/google-search/adapters/google-search.ts:152` | `await page.waitForFunction(() => /\$\d/.test(document.body.innerText), { timeout` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/google-search/adapters/google-search.js:123` | `await page.waitForFunction(() => /\$\d/.test(document.body.innerText), { timeout` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/linkedin/adapters/linkedin-graphql.ts:67` | `let m: RegExpExecArray | null = re.exec(text)` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/linkedin/adapters/linkedin-graphql.ts:70` | `m = re.exec(text)` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/linkedin/adapters/linkedin-graphql.js:30` | `let m = re.exec(text);` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/linkedin/adapters/linkedin-graphql.js:33` | `m = re.exec(text);` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/redfin/adapters/redfin.ts:95` | `for (match = jsonLdRegex.exec(result.text); match !== null; match = jsonLdRegex.` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/redfin/adapters/redfin.js:538` | `for (match = jsonLdRegex.exec(result.text); match !== null; match = jsonLdRegex.` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/rotten-tomatoes/adapters/rotten-tomatoes-web.ts:78` | `for (m = rowRegex.exec(section); m !== null; m = rowRegex.exec(section)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/rotten-tomatoes/adapters/rotten-tomatoes-web.js:493` | `for (m = rowRegex.exec(section); m !== null; m = rowRegex.exec(section)) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.ts:124` | `const getGlobal = new Function(`return (${globalSrc})()`)() as (() => Record<str` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.ts:126` | `const callApi = new Function(`return (${apiSrc})()`)() as ((...a: unknown[]) => ` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.ts:169` | `const getGlobal = new Function(`return (${args.fnSrc})()`)() as (() => Record<st` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.ts:215` | `const getGlobal = new Function(`return (${args.fnSrc})()`)() as (() => Record<st` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.ts:251` | `const getGlobal = new Function(`return (${args.fnSrc})()`)() as (() => Record<st` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.ts:290` | `const getGlobal = new Function(`return (${args.fnSrc})()`)() as (() => Record<st` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.ts:315` | `const getGlobal = new Function(`return (${fnSrc})()`)() as (() => Record<string,` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.ts:339` | `const getGlobal = new Function(`return (${fnSrc})()`)() as (() => Record<string,` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.ts:372` | `const resolveCtx = new Function(`return (${args.ctxSrc})`)() as typeof import('.` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.ts:385` | `const resolveCtx = new Function(`return (${args.ctxSrc})`)() as typeof import('.` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.ts:410` | `const resolveCtx = new Function(`return (${args.ctxSrc})`)() as typeof import('.` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.ts:435` | `const resolveCtx = new Function(`return (${args.ctxSrc})`)() as typeof import('.` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.ts:473` | `const resolveCtx = new Function(`return (${args.ctxSrc})`)() as typeof import('.` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.ts:496` | `const resolveCtx = new Function(`return (${args.ctxSrc})`)() as typeof import('.` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.ts:523` | `const resolveCtx = new Function(`return (${args.ctxSrc})`)() as typeof import('.` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.ts:566` | `const findFn = new Function(`return (${fnSrc})()`) as () => (() => Record<string` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.ts:600` | `const findFn = new Function(`return (${fnSrc})()`) as () => (() => Record<string` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.ts:667` | `const getGlobal = new Function(`return (${args.globalSrc})()`)() as (() => Recor` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.ts:669` | `const getActions = new Function(`return (${args.actionsSrc})()`)() as (() => Rec` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.js:104` | `const getGlobal = new Function(`return (${globalSrc})()`)();` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.js:106` | `const callApi = new Function(`return (${apiSrc})()`)();` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.js:131` | `const getGlobal = new Function(`return (${args.fnSrc})()`)();` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.js:167` | `const getGlobal = new Function(`return (${args.fnSrc})()`)();` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.js:198` | `const getGlobal = new Function(`return (${args.fnSrc})()`)();` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.js:232` | `const getGlobal = new Function(`return (${args.fnSrc})()`)();` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.js:251` | `const getGlobal = new Function(`return (${fnSrc})()`)();` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.js:268` | `const getGlobal = new Function(`return (${fnSrc})()`)();` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.js:292` | `const resolveCtx2 = new Function(`return (${args.ctxSrc})`)();` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.js:304` | `const resolveCtx2 = new Function(`return (${args.ctxSrc})`)();` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.js:328` | `const resolveCtx2 = new Function(`return (${args.ctxSrc})`)();` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.js:352` | `const resolveCtx2 = new Function(`return (${args.ctxSrc})`)();` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.js:388` | `const resolveCtx2 = new Function(`return (${args.ctxSrc})`)();` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.js:410` | `const resolveCtx2 = new Function(`return (${args.ctxSrc})`)();` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.js:435` | `const resolveCtx2 = new Function(`return (${args.ctxSrc})`)();` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.js:461` | `const findFn = new Function(`return (${fnSrc})()`);` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.js:492` | `const findFn = new Function(`return (${fnSrc})()`);` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.js:531` | `const getGlobal = new Function(`return (${args.globalSrc})()`)();` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/telegram/adapters/telegram-protocol.js:533` | `const getActions = new Function(`return (${args.actionsSrc})()`)();` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/x/adapters/x-graphql.ts:66` | `let m: RegExpExecArray | null = re.exec(before)` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/x/adapters/x-graphql.ts:67` | `while (m !== null) { lastId = m[1]; m = re.exec(before) }` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/x/adapters/x-graphql.ts:92` | `let m: RegExpExecArray | null = re.exec(text)` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/x/adapters/x-graphql.ts:95` | `m = re.exec(text)` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/x/adapters/x-graphql.js:38` | `let m = re.exec(before);` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/x/adapters/x-graphql.js:41` | `m = re.exec(before);` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/x/adapters/x-graphql.js:60` | `let m = re.exec(text);` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/x/adapters/x-graphql.js:63` | `m = re.exec(text);` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/xiaohongshu/adapters/xiaohongshu-web.ts:101` | `await page.waitForFunction(` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/xiaohongshu/adapters/xiaohongshu-web.ts:243` | `await page.waitForFunction(` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/xiaohongshu/adapters/xiaohongshu-web.ts:352` | `await page.waitForFunction(() => !!(window as XhsWindow).__INITIAL_STATE__?.note` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/xiaohongshu/adapters/xiaohongshu-web.ts:498` | `await page.waitForFunction(` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/xiaohongshu/adapters/xiaohongshu-web.js:77` | `await page.waitForFunction(` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/xiaohongshu/adapters/xiaohongshu-web.js:236` | `await page.waitForFunction(` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/xiaohongshu/adapters/xiaohongshu-web.js:342` | `await page.waitForFunction(() => !!window.__INITIAL_STATE__?.note, { timeout: 1e` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/xiaohongshu/adapters/xiaohongshu-web.js:501` | `await page.waitForFunction(` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/youtube/adapters/youtube-innertube.ts:424` | `await page.waitForFunction(() => {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `openweb/src/sites/youtube/adapters/youtube-innertube.js:316` | `await page.waitForFunction(() => {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `reverse-api-engineer/src/reverse_api/browser.py:94` | `Element.prototype.attachShadow = function(init) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `reverse-api-engineer/src/reverse_api/browser.py:103` | `WebGLRenderingContext.prototype.getParameter = function(parameter) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `reverse-api-engineer/src/reverse_api/browser.py:115` | `WebGL2RenderingContext.prototype.getParameter = function(parameter) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | eval_exec | `reverse-api-engineer/src/reverse_api/browser.py:127` | `navigator.permissions.query = function(permissionDesc) {` | Dynamic code execution - could run arbitrary code |
| trevor-web-collection | bulk_env_access | `reverse-api-engineer/src/reverse_api/cursor_engineer.py:218` | `env=os.environ.copy(),` | Bulk access to all environment variables - likely exfiltration |
| daily-intel-brief | bulk_env_access | `scripts/build_pdf.py:330` | `env = dict(os.environ)` | Bulk access to all environment variables - likely exfiltration |

---

## Medium Severity Findings

| Skill | Pattern | File | Line | Description |
|-------|---------|------|------|-------------|
| unknown | http_post_external | `skills/daily_intel/deepseek_client.py:60` | `r = requests.post(` | HTTP POST to external endpoint - could exfiltrate data |
| unknown | env_scraping | `skills/daily_intel/trevor_config.py:54` | `_WORKSPACE_ENV = os.environ.get("TREVOR_WORKSPACE", "")` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/trevor_config.py:63` | `EXPORTS_DIR = Path(os.environ.get("TREVOR_EXPORTS", str(WORKSPACE / "exports")))` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/trevor_config.py:64` | `DATA_DIR = Path(os.environ.get("TREVOR_DATA_DIR", str(WORKSPACE / "tmp" / "data"` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/trevor_config.py:65` | `FONTS_DIR = Path(os.environ.get("TREVOR_FONTS_DIR", str(_SKILL_ROOT / "fonts")))` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/trevor_config.py:80` | `DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/trevor_config.py:81` | `DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.co` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/trevor_config.py:82` | `DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/trevor_config.py:83` | `MATON_API_KEY = os.environ.get("MATON_API_KEY", "")` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/trevor_config.py:86` | `DEEPSEEK_TIMEOUT_SECONDS = int(os.environ.get("DEEPSEEK_TIMEOUT", "120"))` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/trevor_config.py:87` | `DEEPSEEK_MAX_RETRIES = int(os.environ.get("DEEPSEEK_MAX_RETRIES", "2"))` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/trevor_log.py:32` | `_LOG_DIR = Path(os.environ.get("TREVOR_EXPORTS", Path.home() / ".openclaw" / "wo` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/trevor_fonts.py:38` | `FONTS_DIR = Path(os.environ.get("TREVOR_FONTS_DIR", str(_SKILL_ROOT / "fonts")))` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/agentmail/scripts/check_inbox.py:83` | `api_key = os.getenv('AGENTMAIL_API_KEY')` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/agentmail/scripts/send_email.py:46` | `api_key = os.getenv('AGENTMAIL_API_KEY')` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/agentmail/scripts/setup_webhook.py:51` | `api_key = os.getenv('AGENTMAIL_API_KEY')` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/pdf-report/scripts/render_pdf.py:17` | `env_root = os.environ.get("OPENCLAW_WORKSPACE")` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/cron/run_daily.py:165` | `maton_key = os.environ.get("MATON_API_KEY", "")` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/cron/run_daily.py:173` | `moltbook_script = Path(os.environ.get("WORKSPACE", str(Path.home() / '.openclaw'` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/cron/run_daily.py:174` | `if moltbook_script.exists() and os.environ.get("MOLTBOOK_API_KEY", ""):` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/cron/run_daily.py:179` | `genviral_script = Path(os.environ.get("WORKSPACE", str(Path.home() / '.openclaw'` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/cron/run_daily.py:180` | `if genviral_script.exists() and os.environ.get("GENVIRAL_API_KEY", ""):` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/scripts/generate_assessments.py:134` | `adaptation_flag = os.environ.get("TREVOR_ADAPTATION_FLAG", "")` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/scripts/_email_brief.py:16` | `maton_key = os.environ.get("MATON_API_KEY", "")` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/scripts/_fetch_intel_emails.py:106` | `key = os.environ.get("MATON_API_KEY", "")` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/scripts/improvement_daemon.py:49` | `if not os.environ.get(k):` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/scripts/improvement_daemon.py:50` | `os.environ[k] = v` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/scripts/improvement_daemon.py:490` | `os.environ["TREVOR_ADAPTATION_FLAG"] = adaptation_flag` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/scripts/osint_collection_expansion.py:175` | `brave_key = os.environ.get("BRAVE_API_KEY", "")` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/scripts/scrape_creators.py:29` | `API_KEY = os.environ.get("SCRAPECREATORS_API_KEY", "mYa56PnRKges2xHchvb4Jx7YND43` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/scripts/sonar_scout.py:76` | `return os.environ.get("OPENROUTER_API_KEY", "")` | Reads environment variables - could access secrets |
| unknown | env_scraping | `skills/daily_intel/scripts/sonar_scout.py:216` | `brave_key = os.environ.get("BRAVE_API_KEY", "BSAoi5HoC5F2i5shy0yPcKtqQPtxwbE")` | Reads environment variables - could access secrets |
| gog | http_post_external | `config/exchange.py:16` | `response = requests.post('https://oauth2.googleapis.com/token', data=data)` | HTTP POST to external endpoint - could exfiltrate data |
| agentmail | env_scraping | `scripts/check_inbox.py:83` | `api_key = os.getenv('AGENTMAIL_API_KEY')` | Reads environment variables - could access secrets |
| agentmail | env_scraping | `scripts/send_email.py:46` | `api_key = os.getenv('AGENTMAIL_API_KEY')` | Reads environment variables - could access secrets |
| agentmail | env_scraping | `scripts/setup_webhook.py:51` | `api_key = os.getenv('AGENTMAIL_API_KEY')` | Reads environment variables - could access secrets |
| trevor-web-collection | http_post_external | `_specs/animalpolitico/client.py:13` | `response = requests.post(f"{base_url}{endpoint}", json=payload, headers=headers)` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/costco/adapters/costco-api.ts:946` | `const r = await fetch(u, { method: 'POST', headers: { Accept: '*/*', 'Content-Ty` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/costco/adapters/costco-api.js:758` | `const r = await fetch(u, { method: "POST", headers: { Accept: "*/*", "Content-Ty` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/instagram/adapters/instagram-api.ts:80` | `const result = await pageFetch(page, { url, method: 'POST', headers, body, crede` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/instagram/adapters/instagram-api.js:63` | `const result = await pageFetch(page, { url, method: "POST", headers, body, crede` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/medium/adapters/medium-graphql.ts:232` | `const data = (await graphqlFetch(page, 'PostDetailQuery', POST_DETAIL_QUERY, {` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/medium/adapters/medium-graphql.ts:345` | `const data = (await graphqlFetch(page, 'ClapCountQuery', POST_CLAPS_QUERY, {` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/medium/adapters/medium-graphql.js:482` | `const data = await graphqlFetch(page, "PostDetailQuery", POST_DETAIL_QUERY, {` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/medium/adapters/medium-graphql.js:576` | `const data = await graphqlFetch(page, "ClapCountQuery", POST_CLAPS_QUERY, {` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/spotify/adapters/spotify-pathfinder.ts:382` | `const result = await spclientFetch(page, 'POST', url, accessToken, clientToken, ` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/spotify/adapters/spotify-pathfinder.ts:403` | `const result = await spclientFetch(page, 'POST', url, accessToken, clientToken, ` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/spotify/adapters/spotify-pathfinder.ts:419` | `const result = await spclientFetch(page, 'POST', url, accessToken, clientToken, ` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/spotify/adapters/spotify-pathfinder.ts:433` | `await spclientFetch(page, 'POST', `https://spclient.wg.spotify.com/playlist/v2/p` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/spotify/adapters/spotify-pathfinder.js:280` | `const result = await spclientFetch(page, "POST", url, accessToken, clientToken, ` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/spotify/adapters/spotify-pathfinder.js:301` | `const result = await spclientFetch(page, "POST", url, accessToken, clientToken, ` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/spotify/adapters/spotify-pathfinder.js:315` | `const result = await spclientFetch(page, "POST", url, accessToken, clientToken, ` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/spotify/adapters/spotify-pathfinder.js:326` | `await spclientFetch(page, "POST", `https://spclient.wg.spotify.com/playlist/v2/p` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/todoist/adapters/todoist-api.ts:210` | `const raw = await apiFetch(page, 'POST', '/tasks', body, errors) as Record<strin` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/todoist/adapters/todoist-api.ts:219` | `const seed = await apiFetch(page, 'POST', '/tasks', { content: '_openweb_verify_` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/todoist/adapters/todoist-api.ts:223` | `const result = await apiFetch(page, 'POST', `/tasks/${encodeURIComponent(taskId)` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/todoist/adapters/todoist-api.ts:233` | `const seed = await apiFetch(page, 'POST', '/tasks', { content: '_openweb_verify_` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/todoist/adapters/todoist-api.ts:236` | `await apiFetch(page, 'POST', `/tasks/${encodeURIComponent(taskId)}/close`, null,` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/todoist/adapters/todoist-api.ts:238` | `const result = await apiFetch(page, 'POST', `/tasks/${encodeURIComponent(taskId)` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/todoist/adapters/todoist-api.ts:247` | `const seed = await apiFetch(page, 'POST', '/tasks', { content: '_openweb_verify_` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/todoist/adapters/todoist-api.js:160` | `const raw = await apiFetch(page, "POST", "/tasks", body, errors);` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/todoist/adapters/todoist-api.js:168` | `const seed = await apiFetch(page, "POST", "/tasks", { content: "_openweb_verify_` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/todoist/adapters/todoist-api.js:172` | `const result = await apiFetch(page, "POST", `/tasks/${encodeURIComponent(taskId)` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/todoist/adapters/todoist-api.js:182` | `const seed = await apiFetch(page, "POST", "/tasks", { content: "_openweb_verify_` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/todoist/adapters/todoist-api.js:185` | `await apiFetch(page, "POST", `/tasks/${encodeURIComponent(taskId)}/close`, null,` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/todoist/adapters/todoist-api.js:187` | `const result = await apiFetch(page, "POST", `/tasks/${encodeURIComponent(taskId)` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/todoist/adapters/todoist-api.js:196` | `const seed = await apiFetch(page, "POST", "/tasks", { content: "_openweb_verify_` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/trello/adapters/trello-api.ts:228` | `const card = (await apiFetch(page, helpers, 'POST', '/cards', undefined, body)) ` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/trello/adapters/trello-api.js:167` | `const card = await apiFetch(page, helpers, "POST", "/cards", void 0, body);` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/x/adapters/x-graphql.ts:187` | `const resp = await fetch(url, { method: 'POST', headers, body: args.body, creden` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/x/adapters/x-graphql.js:139` | `const resp = await fetch(url, { method: "POST", headers, body: args.body, creden` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/youtube/adapters/youtube-innertube.ts:123` | `const result = await pageFetch(page, { url, method: 'POST', headers, body: JSON.` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/youtube/adapters/youtube-innertube.ts:158` | `const result = await pageFetch(page, { url, method: 'POST', headers, body: JSON.` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/youtube/adapters/youtube-innertube.js:71` | `const result = await pageFetch(page, { url, method: "POST", headers, body: JSON.` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | http_post_external | `openweb/src/sites/youtube/adapters/youtube-innertube.js:98` | `const result = await pageFetch(page, { url, method: "POST", headers, body: JSON.` | HTTP POST to external endpoint - could exfiltrate data |
| trevor-web-collection | env_scraping | `reverse-api-engineer/src/reverse_api/base_engineer.py:17` | `DEBUG = os.environ.get("DEBUG", "0") == "1"` | Reads environment variables - could access secrets |
| trevor-web-collection | env_scraping | `reverse-api-engineer/src/reverse_api/cli.py:258` | `elif not os.environ.get(sdk_env_var):` | Reads environment variables - could access secrets |
| trevor-web-collection | env_scraping | `reverse-api-engineer/src/reverse_api/cursor_engineer.py:184` | `api_key = os.environ.get("CURSOR_API_KEY", "")` | Reads environment variables - could access secrets |
| trevor-web-collection | env_scraping | `reverse-api-engineer/src/reverse_api/cursor_engineer.py:347` | `if not os.environ.get("CURSOR_API_KEY"):` | Reads environment variables - could access secrets |
| trevor-web-collection | env_scraping | `reverse-api-engineer/src/reverse_api/cursor_engineer.py:479` | `if not os.environ.get("CURSOR_API_KEY"):` | Reads environment variables - could access secrets |
| trevor-web-collection | env_scraping | `reverse-api-engineer/src/reverse_api/opencode_engineer.py:20` | `DEBUG = os.environ.get("OPENCODE_DEBUG", "0") == "1"` | Reads environment variables - could access secrets |
| trevor-web-collection | env_scraping | `reverse-api-engineer/src/reverse_api/opencode_engineer.py:128` | `self.opencode_password = os.environ.get("OPENCODE_SERVER_PASSWORD")` | Reads environment variables - could access secrets |
| trevor-web-collection | env_scraping | `reverse-api-engineer/src/reverse_api/opencode_engineer.py:129` | `self.opencode_username = os.environ.get("OPENCODE_SERVER_USERNAME", "opencode")` | Reads environment variables - could access secrets |
| trevor-web-collection | env_scraping | `reverse-api-engineer/src/reverse_api/utils.py:458` | `user_profile = os.environ.get("USERPROFILE", str(home))` | Reads environment variables - could access secrets |
| daily-intel-brief | env_scraping | `scripts/build_visuals.py:152` | `token = os.environ.get("MAPBOX_TOKEN")` | Reads environment variables - could access secrets |
| daily-intel-brief | env_scraping | `scripts/collect.py:696` | `brave_key = os.environ.get("BRAVE_API_KEY", "")` | Reads environment variables - could access secrets |
| daily-intel-brief | env_scraping | `scripts/orchestrate.py:57` | `missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]` | Reads environment variables - could access secrets |
| daily-intel-brief | env_scraping | `scripts/orchestrate.py:65` | `if not os.environ.get(k):` | Reads environment variables - could access secrets |
| daily-intel-brief | env_scraping | `scripts/orchestrate.py:548` | `if os.environ.get("AGENTMAIL_API_KEY"):` | Reads environment variables - could access secrets |
| daily-intel-brief | env_scraping | `scripts/analyze.py:35` | `DEEPSEEK_BASE = os.environ.get("DEEPSEEK_BASE", "https://api.deepseek.com")` | Reads environment variables - could access secrets |
| daily-intel-brief | env_scraping | `scripts/analyze.py:124` | `api_key = _os.environ.get("OPENROUTER_API_KEY")` | Reads environment variables - could access secrets |
| daily-intel-brief | env_scraping | `scripts/analyze.py:134` | `api_key = _os.environ.get("DEEPSEEK_API_KEY")` | Reads environment variables - could access secrets |
| pdf-report | env_scraping | `scripts/render_pdf.py:17` | `env_root = os.environ.get("OPENCLAW_WORKSPACE")` | Reads environment variables - could access secrets |
| polymarket-trader | env_scraping | `scripts/research.py:18` | `GAMMA = os.environ.get("POLYMARKET_GAMMA_HOST", "https://gamma-api.polymarket.co` | Reads environment variables - could access secrets |
| polymarket-trader | env_scraping | `scripts/research.py:19` | `CLOB = os.environ.get("POLYMARKET_CLOB_HOST", "https://clob.polymarket.com").rst` | Reads environment variables - could access secrets |
| polymarket-trader | env_scraping | `scripts/trade.py:19` | `HOST = os.environ.get("POLYMARKET_CLOB_HOST", "https://clob.polymarket.com").rst` | Reads environment variables - could access secrets |
| polymarket-trader | env_scraping | `scripts/trade.py:20` | `CHAIN_ID = int(os.environ.get("POLYMARKET_CHAIN_ID", "137"))` | Reads environment variables - could access secrets |
| polymarket-trader | env_scraping | `scripts/trade.py:114` | `value = os.environ.get(name)` | Reads environment variables - could access secrets |
| polymarket-trader | env_scraping | `scripts/trade.py:128` | `signature_type = int(os.environ.get("POLYMARKET_SIGNATURE_TYPE", "2"))` | Reads environment variables - could access secrets |
| polymarket-trader | env_scraping | `scripts/trade.py:129` | `funder = os.environ.get("POLYMARKET_FUNDER")` | Reads environment variables - could access secrets |
| polymarket-trader | env_scraping | `scripts/trade.py:135` | `api_key = os.environ.get("POLYMARKET_CLOB_API_KEY")` | Reads environment variables - could access secrets |
| polymarket-trader | env_scraping | `scripts/trade.py:136` | `secret = os.environ.get("POLYMARKET_CLOB_SECRET")` | Reads environment variables - could access secrets |
| polymarket-trader | env_scraping | `scripts/trade.py:137` | `passphrase = os.environ.get("POLYMARKET_CLOB_PASS_PHRASE")` | Reads environment variables - could access secrets |
| visual_production | env_scraping | `visual_production/pipeline.py:233` | `api_key = os.environ.get("OPENROUTER_API_KEY")` | Reads environment variables - could access secrets |

---

## Scan Errors

_No scan errors._ ✅

---

## Detailed Per-Skill Reports


# Skill Security Review - unknown unknown

**Scan Date:** 2026-05-21T00:00:31.731198
**Skill Path:** `/home/ubuntu/.openclaw/skills/OpenClawTrevorMentis`

## Verdict

**REJECT** - Found 56 critical issue(s): crypto_miner, credential_paths

## Metadata

- **Name:** unknown
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** False
- **Files:** 205
- **Scripts:** 51
- **Total Lines:** 32760

## Findings

Found **88** potential issue(s):

### credential_paths (critical)

- **File:** `audit_skills.py` line 6
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `The raw scanner regex-matches strings like `~/.config` and `Bearer ${...}` as`

### credential_paths (critical)

- **File:** `consolidated_audit_report.md` line 21
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `2. **Credential Paths:** Multiple skills (`gmail`, `gog-myclaw`, `api-gateway`, `stripe-api`, `whatsapp-business`) were flagged for referencing `~/.config` or `Bearer` tokens in their documentation (``

### credential_paths (critical)

- **File:** `consolidated_audit_report.md` line 33
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `2. **Config Locations:** Skills such as `eightctl`, `camsnap`, and `spotify-player` were flagged for documentation referencing `~/.config` directories.`

### credential_paths (critical)

- **File:** `consolidated_audit_report.md` line 39
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `2. **Audit Config Access:** Ensure that skills accessing `~/.config` are only doing so for their own legitimate configuration and not attempting to exfiltrate other service tokens.`

### credential_paths (critical)

- **File:** `consolidated_audit_report.md` line 40
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `3. **Ignore Documentation Flags:** Findings inside `SKILL.md` files that merely describe setup procedures (e.g., "save your token to ~/.config/...") can generally be considered low-risk documentation `

### crypto_miner (critical)

- **File:** `skill_audit_report.json` line 144
- **Description:** Cryptocurrency mining indicators
- **Recommendation:** REJECT - this is cryptojacking malware
- **Code:** `"line_content": "- Catches **crypto-mining** indicators (xmrig, mining pools, wallet addresses)",`

### crypto_miner (critical)

- **File:** `skill_audit_report.json` line 153
- **Description:** Cryptocurrency mining indicators
- **Recommendation:** REJECT - this is cryptojacking malware
- **Code:** `"line_content": "- Crypto miners (xmrig, ethminer, stratum+tcp)",`

### crypto_miner (critical)

- **File:** `skill_audit_report.json` line 189
- **Description:** Cryptocurrency mining indicators
- **Recommendation:** REJECT - this is cryptojacking malware
- **Code:** `"line_content": "\"pattern\": r\"xmrig|ethminer|cpuminer|cgminer|stratum\\+tcp|mining.*pool|hashrate\",",`

### credential_paths (critical)

- **File:** `system_skills_audit.md` line 29
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `- Config: `~/.config/eightctl/config.yaml```

### credential_paths (critical)

- **File:** `system_skills_audit.md` line 36
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `- Config file: `~/.config/camsnap/config.yaml```

### credential_paths (critical)

- **File:** `system_skills_audit.md` line 43
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `- Config folder: `~/.config/spotify-player` (e.g., `app.toml`).``

### credential_paths (critical)

- **File:** `system_skills_audit.md` line 50
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `- For some operations (add-text, tags, open-note --selected), a Bear app token (stored in `~/.config/grizzly/token`)``

### credential_paths (critical)

- **File:** `system_skills_audit.md` line 57
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `2. Save it: `echo "YOUR_TOKEN" > ~/.config/grizzly/token```

### credential_paths (critical)

- **File:** `system_skills_audit.md` line 64
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `echo "Additional content" | grizzly add-text --id "NOTE_ID" --mode append --token-file ~/.config/grizzly/token``

### credential_paths (critical)

- **File:** `system_skills_audit.md` line 71
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `grizzly tags --enable-callback --json --token-file ~/.config/grizzly/token``

### credential_paths (critical)

- **File:** `system_skills_audit.md` line 78
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `4. `~/.config/grizzly/config.toml```

### credential_paths (critical)

- **File:** `system_skills_audit.md` line 85
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `Example `~/.config/grizzly/config.toml`:``

### credential_paths (critical)

- **File:** `system_skills_audit.md` line 92
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `token_file = "~/.config/grizzly/token"``

### credential_paths (critical)

- **File:** `system_skills_audit.md` line 99
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `2. A configuration file at `~/.config/himalaya/config.toml```

### credential_paths (critical)

- **File:** `system_skills_audit.md` line 106
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `Or create `~/.config/himalaya/config.toml` manually:``

### credential_paths (critical)

- **File:** `system_skills_audit.md` line 113
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `- Don’t attach secrets by default (`.env`, key files, auth tokens). Redact aggressively; share only what’s required.``

### credential_paths (critical)

- **File:** `system_skills_audit.md` line 120
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `mkdir -p ~/.config/notion``

### credential_paths (critical)

- **File:** `system_skills_audit.md` line 127
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `echo "ntn_your_key_here" > ~/.config/notion/api_key``

### credential_paths (critical)

- **File:** `system_skills_audit.md` line 134
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `NOTION_KEY=$(cat ~/.config/notion/api_key)``

### credential_paths (critical)

- **File:** `system_skills_audit.md` line 141
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `- `op run --env-file="./.env" -- printenv DB_PASSWORD```

### credential_paths (critical)

- **File:** `system_skills_audit.md` line 148
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `- Claude: ~/.config/claude/projects/**/\*.jsonl or ~/.claude/projects/**/\*.jsonl``

### credential_paths (critical)

- **File:** `system_skills_audit.md` line 155
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `Configuration file location: `~/.config/himalaya/config.toml```

### credential_paths (critical)

- **File:** `user_skills_audit.md` line 29
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}```

### credential_paths (critical)

- **File:** `user_skills_audit.md` line 36
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `3. Once they provide the `credentials.json` content, save it to `~/.config/gogcli/credentials.json`.``

### credential_paths (critical)

- **File:** `user_skills_audit.md` line 43
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `4. Run: `gog auth credentials set ~/.config/gogcli/credentials.json```

### credential_paths (critical)

- **File:** `user_skills_audit.md` line 50
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}```

### credential_paths (critical)

- **File:** `user_skills_audit.md` line 57
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}```

### credential_paths (critical)

- **File:** `user_skills_audit.md` line 64
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}`,``

### credential_paths (critical)

- **File:** `user_skills_audit.md` line 71
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `- Credential path access (~/.ssh, ~/.aws, /etc/passwd)``

### credential_paths (critical)

- **File:** `user_skills_audit.md` line 92
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- **Code:** `"pattern": r"~/\.ssh|~/\.aws|~/\.config|/etc/passwd|\.env\b|\.credentials|keychain",``

### crypto_miner (critical)

- **File:** `user_skills_audit.md` line 78
- **Description:** Cryptocurrency mining indicators
- **Recommendation:** REJECT - this is cryptojacking malware
- **Code:** `- **Code:** `- Catches **crypto-mining** indicators (xmrig, mining pools, wallet addresses)``

### crypto_miner (critical)

- **File:** `user_skills_audit.md` line 85
- **Description:** Cryptocurrency mining indicators
- **Recommendation:** REJECT - this is cryptojacking malware
- **Code:** `- **Code:** `- Crypto miners (xmrig, ethminer, stratum+tcp)``

### crypto_miner (critical)

- **File:** `user_skills_audit.md` line 113
- **Description:** Cryptocurrency mining indicators
- **Recommendation:** REJECT - this is cryptojacking malware
- **Code:** `- **Code:** `"pattern": r"xmrig|ethminer|cpuminer|cgminer|stratum\+tcp|mining.*pool|hashrate",``

### credential_paths (critical)

- **File:** `brain/README.md` line 61
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- Don't index secrets. The indexer skips `.env`, `*.key`, `*.pem`,`

### credential_paths (critical)

- **File:** `brain/scripts/brain.py` line 62
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `re.compile(r"\.env$"),`

### http_post_external (medium)

- **File:** `skills/daily_intel/deepseek_client.py` line 60
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `r = requests.post(`

### env_scraping (medium)

- **File:** `skills/daily_intel/trevor_config.py` line 54
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `_WORKSPACE_ENV = os.environ.get("TREVOR_WORKSPACE", "")`

### env_scraping (medium)

- **File:** `skills/daily_intel/trevor_config.py` line 63
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `EXPORTS_DIR = Path(os.environ.get("TREVOR_EXPORTS", str(WORKSPACE / "exports")))`

### env_scraping (medium)

- **File:** `skills/daily_intel/trevor_config.py` line 64
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `DATA_DIR = Path(os.environ.get("TREVOR_DATA_DIR", str(WORKSPACE / "tmp" / "data")))`

### env_scraping (medium)

- **File:** `skills/daily_intel/trevor_config.py` line 65
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `FONTS_DIR = Path(os.environ.get("TREVOR_FONTS_DIR", str(_SKILL_ROOT / "fonts")))`

### env_scraping (medium)

- **File:** `skills/daily_intel/trevor_config.py` line 80
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")`

### env_scraping (medium)

- **File:** `skills/daily_intel/trevor_config.py` line 81
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")`

### env_scraping (medium)

- **File:** `skills/daily_intel/trevor_config.py` line 82
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")`

### env_scraping (medium)

- **File:** `skills/daily_intel/trevor_config.py` line 83
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `MATON_API_KEY = os.environ.get("MATON_API_KEY", "")`

### env_scraping (medium)

- **File:** `skills/daily_intel/trevor_config.py` line 86
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `DEEPSEEK_TIMEOUT_SECONDS = int(os.environ.get("DEEPSEEK_TIMEOUT", "120"))`

### env_scraping (medium)

- **File:** `skills/daily_intel/trevor_config.py` line 87
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `DEEPSEEK_MAX_RETRIES = int(os.environ.get("DEEPSEEK_MAX_RETRIES", "2"))`

### env_scraping (medium)

- **File:** `skills/daily_intel/trevor_log.py` line 32
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `_LOG_DIR = Path(os.environ.get("TREVOR_EXPORTS", Path.home() / ".openclaw" / "workspace" / "exports")) / "logs"`

### env_scraping (medium)

- **File:** `skills/daily_intel/trevor_fonts.py` line 38
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `FONTS_DIR = Path(os.environ.get("TREVOR_FONTS_DIR", str(_SKILL_ROOT / "fonts")))`

### env_scraping (medium)

- **File:** `skills/agentmail/scripts/check_inbox.py` line 83
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `api_key = os.getenv('AGENTMAIL_API_KEY')`

### env_scraping (medium)

- **File:** `skills/agentmail/scripts/send_email.py` line 46
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `api_key = os.getenv('AGENTMAIL_API_KEY')`

### env_scraping (medium)

- **File:** `skills/agentmail/scripts/setup_webhook.py` line 51
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `api_key = os.getenv('AGENTMAIL_API_KEY')`

### credential_paths (critical)

- **File:** `skills/chartgen-ai/tools/chartgen_api.js` line 25
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `const BASE_URL = process.env.CHARTGEN_API_URL || "https://chartgen.ai";`

### credential_paths (critical)

- **File:** `skills/chartgen-ai/tools/chartgen_api.js` line 40
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `if (process.env.CHARTGEN_API_KEY) return process.env.CHARTGEN_API_KEY;`

### credential_paths (critical)

- **File:** `skills/chartgen-ai/tools/chartgen_api.js` line 44
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `process.env.OPENCLAW_STATE_DIR`

### credential_paths (critical)

- **File:** `skills/chartgen-ai/tools/chartgen_api.js` line 45
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `? path.join(process.env.OPENCLAW_STATE_DIR, "skills", "chartgen", "config.json")`

### credential_paths (critical)

- **File:** `skills/chartgen-ai/tools/chartgen_api.js` line 74
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `const stateDir = process.env.OPENCLAW_STATE_DIR;`

### env_scraping (medium)

- **File:** `skills/pdf-report/scripts/render_pdf.py` line 17
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `env_root = os.environ.get("OPENCLAW_WORKSPACE")`

### env_scraping (medium)

- **File:** `skills/daily_intel/cron/run_daily.py` line 165
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `maton_key = os.environ.get("MATON_API_KEY", "")`

### env_scraping (medium)

- **File:** `skills/daily_intel/cron/run_daily.py` line 173
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `moltbook_script = Path(os.environ.get("WORKSPACE", str(Path.home() / '.openclaw' / 'workspace'))) / 'scripts' / 'moltbook-post-brief.sh'`

### env_scraping (medium)

- **File:** `skills/daily_intel/cron/run_daily.py` line 174
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `if moltbook_script.exists() and os.environ.get("MOLTBOOK_API_KEY", ""):`

### env_scraping (medium)

- **File:** `skills/daily_intel/cron/run_daily.py` line 179
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `genviral_script = Path(os.environ.get("WORKSPACE", str(Path.home() / '.openclaw' / 'workspace'))) / 'scripts' / 'genviral-post-brief.sh'`

### env_scraping (medium)

- **File:** `skills/daily_intel/cron/run_daily.py` line 180
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `if genviral_script.exists() and os.environ.get("GENVIRAL_API_KEY", ""):`

### credential_paths (critical)

- **File:** `skills/daily_intel/cron/run_daily.py` line 19
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `# Load environment from workspace .env (cron may not have it in env)`

### credential_paths (critical)

- **File:** `skills/daily_intel/cron/run_daily.py` line 21
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `WORKSPACE_ENV = WORKSPACE / '.env'`

### env_scraping (medium)

- **File:** `skills/daily_intel/scripts/generate_assessments.py` line 134
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `adaptation_flag = os.environ.get("TREVOR_ADAPTATION_FLAG", "")`

### env_scraping (medium)

- **File:** `skills/daily_intel/scripts/_email_brief.py` line 16
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `maton_key = os.environ.get("MATON_API_KEY", "")`

### credential_paths (critical)

- **File:** `skills/daily_intel/scripts/_email_brief.py` line 19
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `# Try reading from workspace .env`

### credential_paths (critical)

- **File:** `skills/daily_intel/scripts/_email_brief.py` line 21
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `env_path = str(WORKSPACE / ".env")`

### env_scraping (medium)

- **File:** `skills/daily_intel/scripts/_fetch_intel_emails.py` line 106
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `key = os.environ.get("MATON_API_KEY", "")`

### credential_paths (critical)

- **File:** `skills/daily_intel/scripts/_fetch_intel_emails.py` line 105
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `"""Read MATON_API_KEY from env or workspace .env."""`

### credential_paths (critical)

- **File:** `skills/daily_intel/scripts/_fetch_intel_emails.py` line 108
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `env_path = os.path.expanduser("~/.openclaw/workspace/.env")`

### env_scraping (medium)

- **File:** `skills/daily_intel/scripts/improvement_daemon.py` line 49
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `if not os.environ.get(k):`

### env_scraping (medium)

- **File:** `skills/daily_intel/scripts/improvement_daemon.py` line 50
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `os.environ[k] = v`

### env_scraping (medium)

- **File:** `skills/daily_intel/scripts/improvement_daemon.py` line 490
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `os.environ["TREVOR_ADAPTATION_FLAG"] = adaptation_flag`

### credential_paths (critical)

- **File:** `skills/daily_intel/scripts/improvement_daemon.py` line 29
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `# Load .env for subprocess environment inheritance`

### credential_paths (critical)

- **File:** `skills/daily_intel/scripts/improvement_daemon.py` line 32
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `env_path = Path.home() / '.openclaw' / 'workspace' / '.env'`

### credential_paths (critical)

- **File:** `skills/daily_intel/scripts/improvement_daemon.py` line 41
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `env_path = Path.home() / '.openclaw' / 'workspace' / '.env'`

### env_scraping (medium)

- **File:** `skills/daily_intel/scripts/osint_collection_expansion.py` line 175
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `brave_key = os.environ.get("BRAVE_API_KEY", "")`

### env_scraping (medium)

- **File:** `skills/daily_intel/scripts/scrape_creators.py` line 29
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `API_KEY = os.environ.get("SCRAPECREATORS_API_KEY", "mYa56PnRKges2xHchvb4Jx7YND43")`

### env_scraping (medium)

- **File:** `skills/daily_intel/scripts/sonar_scout.py` line 76
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `return os.environ.get("OPENROUTER_API_KEY", "")`

### env_scraping (medium)

- **File:** `skills/daily_intel/scripts/sonar_scout.py` line 216
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `brave_key = os.environ.get("BRAVE_API_KEY", "BSAoi5HoC5F2i5shy0yPcKtqQPtxwbE")`

### credential_paths (critical)

- **File:** `skills/daily_intel/scripts/sonar_scout.py` line 70
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `"""Get OpenRouter API key from workspace .env."""`

### credential_paths (critical)

- **File:** `skills/daily_intel/scripts/sonar_scout.py` line 71
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `env_path = WORKSPACE / ".env"`

## Files Scanned

- `IDENTITY.md`
- `MEMORY.md`
- `README.md`
- `SOUL.md`
- `USER.md`
- `audit_skills.py`
- `consolidated_audit_report.md`
- `skill_audit_report.json`
- `skill_audit_report.md`
- `system_skills_audit.md`
- `user_skills_audit.md`
- `.gitignore`
- `AGENTS.md`
- `HEARTBEAT.md`
- `ORCHESTRATION.md`
- `TOOLS.md`
- `.clawhub/lock.json`
- `.openclaw/model-config-note.md`
- `.openclaw/workspace-state.json`
- `analyst/README.md`
- `brain/README.md`
- `brain/working-memory.example.json`
- `memory/2026-03-05.md`
- `memory/2026-04-25.md`
- `memory/2026-04-27.md`
- `memory/heartbeat-state.json`
- `tasks/quick-test-render.md`
- `tasks/news_raw.md`
- `tests/test_config.py`
- `tests/test_fonts.py`
- `tests/test_diagnostics.py`
- `tests/test_memory.py`
- `analyst/meta/sources.json`
- `analyst/methodology/README.md`
- `analyst/playbooks/analytic-workflow.md`
- `analyst/playbooks/quality-gates.md`
- `analyst/playbooks/scenario-triage.md`
- `analyst/playbooks/source-acquisition.md`
- `analyst/templates/ach-matrix.md`
- `analyst/templates/analytic-note.md`
- `analyst/templates/bluf-report.md`
- `analyst/templates/indicators-and-warnings.md`
- `analyst/templates/pmesii-pt-scan.md`
- `analyst/templates/red-team-review.md`
- `analyst/templates/source-evaluation-matrix.md`
- `brain/index/.gitkeep`
- `brain/meta/.gitkeep`
- `brain/scripts/brain.py`
- `brain/memory/episodic/.gitkeep`
- `brain/memory/procedural/.gitkeep`
- `brain/memory/semantic/.gitkeep`
- `docs/archive/README.md`
- `docs/archive/REBUILD_ORCHESTRATION-2026-04-28.md`
- `memory/.dreams/events.jsonl`
- `memory/.dreams/short-term-recall.json`
- `skills/agentmail/SKILL.md`
- `skills/agentmail/_meta.json`
- `skills/baoyu-translate/SKILL.md`
- `skills/baoyu-translate/_meta.json`
- `skills/bluf-report/SKILL.md`
- `skills/bluf-report/_meta.json`
- `skills/chartgen-ai/SKILL.md`
- `skills/chartgen-ai/_meta.json`
- `skills/data-analysis/SKILL.md`
- `skills/data-analysis/_meta.json`
- `skills/data-analysis/chart-selection.md`
- `skills/data-analysis/decision-briefs.md`
- `skills/data-analysis/metric-contracts.md`
- `skills/data-analysis/pitfalls.md`
- `skills/data-analysis/techniques.md`
- `skills/geospatial-osint/SKILL.md`
- `skills/geospatial-osint/_meta.json`
- `skills/indicators-and-warnings/SKILL.md`
- `skills/indicators-and-warnings/_meta.json`
- `skills/mermaid/README.md`
- `skills/mermaid/SKILL.md`
- `skills/mermaid/_meta.json`
- `skills/mermaid/generate-test.sh`
- `skills/mermaid/package.json`
- `skills/pdf-report/SKILL.md`
- `skills/pdf-report/_meta.json`
- `skills/quick-translation/SKILL.md`
- `skills/quick-translation/_meta.json`
- `skills/sat-toolkit/SKILL.md`
- `skills/sat-toolkit/_meta.json`
- `skills/source-evaluation/SKILL.md`
- `skills/source-evaluation/_meta.json`
- `skills/daily_intel/AUTONOMOUS_WORKFLOW.md`
- `skills/daily_intel/README.md`
- `skills/daily_intel/deepseek_client.py`
- `skills/daily_intel/requirements.txt`
- `skills/daily_intel/skill_config.json`
- `skills/daily_intel/import_handoff.py`
- `skills/daily_intel/trevor_config.py`
- `skills/daily_intel/trevor_log.py`
- `skills/daily_intel/trevor_fonts.py`
- `skills/daily_intel/trevor_diag.py`
- `skills/daily_intel/trevor_memory.py`
- `skills/daily_intel/trevor_skills.py`
- `skills/daily_intel/trevor_cost.py`
- `skills/daily_intel/trevor_freeze.py`
- `skills/daily_intel/trevor_dashboard.py`
- `skills/agentmail/.clawhub/origin.json`
- `skills/agentmail/references/API.md`
- `skills/agentmail/references/EXAMPLES.md`
- `skills/agentmail/references/WEBHOOKS.md`
- `skills/agentmail/scripts/check_inbox.py`
- `skills/agentmail/scripts/send_email.py`
- `skills/agentmail/scripts/setup_webhook.py`
- `skills/baoyu-translate/.clawhub/origin.json`
- `skills/baoyu-translate/references/glossary-en-zh.md`
- `skills/baoyu-translate/references/refined-workflow.md`
- `skills/baoyu-translate/references/subagent-prompt-template.md`
- `skills/baoyu-translate/references/workflow-mechanics.md`
- `skills/baoyu-translate/scripts/bun.lock`
- `skills/baoyu-translate/scripts/chunk.ts`
- `skills/baoyu-translate/scripts/main.ts`
- `skills/baoyu-translate/scripts/package.json`
- `skills/baoyu-translate/references/config/extend-schema.md`
- `skills/baoyu-translate/references/config/first-time-setup.md`
- `skills/chartgen-ai/.clawhub/origin.json`
- `skills/chartgen-ai/references/upgrade-skill.md`
- `skills/chartgen-ai/tools/chartgen_api.js`
- `skills/data-analysis/.clawhub/origin.json`
- `skills/geospatial-osint/.clawhub/origin.json`
- `skills/geospatial-osint/references/adsb-api.md`
- `skills/geospatial-osint/references/cesium-basics.md`
- `skills/geospatial-osint/references/effects.md`
- `skills/geospatial-osint/references/rendering-stack.md`
- `skills/geospatial-osint/references/satellite-passes.md`
- `skills/mermaid/.clawhub/origin.json`
- `skills/pdf-report/.clawhub/origin.json`
- `skills/pdf-report/scripts/render_pdf.py`
- `skills/pdf-report/templates/report.html`
- `skills/quick-translation/.clawhub/origin.json`
- `skills/daily_intel/cron/run_daily.py`
- `skills/daily_intel/memory/retrieve.py`
- `skills/daily_intel/memory/index_memory.py`
- `skills/daily_intel/memory/vector_index.json`
- `skills/daily_intel/memory/trevor_memory.db`
- `skills/daily_intel/memory/memory_freeze.json`
- `skills/daily_intel/assessments/europe.md`
- `skills/daily_intel/assessments/africa.md`
- `skills/daily_intel/assessments/asia.md`
- `skills/daily_intel/assessments/middle_east.md`
- `skills/daily_intel/assessments/north_america.md`
- `skills/daily_intel/assessments/south_america.md`
- `skills/daily_intel/assessments/global_finance.md`
- `skills/daily_intel/scripts/build_pdf.py`
- `skills/daily_intel/scripts/generate_assessments.py`
- `skills/daily_intel/scripts/refresh_imagery.py`
- `skills/daily_intel/scripts/_email_brief.py`
- `skills/daily_intel/scripts/_fetch_intel_emails.py`
- `skills/daily_intel/scripts/quality_audit.py`
- `skills/daily_intel/scripts/briefometer.py`
- `skills/daily_intel/scripts/story_tracker.py`
- `skills/daily_intel/scripts/daily_enrichment.py`
- `skills/daily_intel/scripts/improvement_daemon.py`
- `skills/daily_intel/scripts/narrative_engine.py`
- `skills/daily_intel/scripts/prioritize.py`
- `skills/daily_intel/scripts/analytical_opportunities.py`
- `skills/daily_intel/scripts/osint_collection_expansion.py`
- `skills/daily_intel/scripts/scrape_creators.py`
- `skills/daily_intel/scripts/daily_operational_report.py`
- `skills/daily_intel/scripts/collection_intelligence.py`
- `skills/daily_intel/scripts/global_collection.py`
- `skills/daily_intel/scripts/collection_daemon.py`
- `skills/daily_intel/scripts/epistemic_state.py`
- `skills/daily_intel/scripts/sonar_scout.py`
- `skills/daily_intel/scripts/cognition_router.py`
- `skills/daily_intel/scripts/meta_cognition.py`
- `skills/daily_intel/cron_tracking/state.json`
- `skills/daily_intel/cron_tracking/STANDING_RULES.md`
- `skills/daily_intel/cron_tracking/run.log`
- `skills/daily_intel/cron_tracking/heartbeat.json`
- `skills/daily_intel/cron_tracking/issue_number.txt`
- `skills/daily_intel/cron_tracking/.gitignore`
- `skills/daily_intel/cron_tracking/improvement_log.json`
- `skills/daily_intel/cron_tracking/measurement_log.json`
- `skills/daily_intel/cron_tracking/key_judgments.json`
- `skills/daily_intel/cron_tracking/story_tracker.json`
- `skills/daily_intel/cron_tracking/daemon_run.log`
- `skills/daily_intel/cron_tracking/enrichment_report.json`
- `skills/daily_intel/cron_tracking/daily_report_2026-05-08.json`
- `skills/daily_intel/cron_tracking/story_delta.json`
- `skills/daily_intel/cron_tracking/daily_report_2026-05-09.json`
- `skills/daily_intel/cron_tracking/daily_report_2026-05-10.json`
- `skills/daily_intel/cron_tracking/session-costs.json`
- `skills/daily_intel/cron_tracking/daily_report_2026-05-11.json`
- `skills/daily_intel/cron_tracking/narrative_landscape.json`
- `skills/daily_intel/cron_tracking/analytical_opportunities.json`
- `skills/daily_intel/cron_tracking/source_inventory.json`
- `skills/daily_intel/cron_tracking/collection_expansion.json`
- `skills/daily_intel/cron_tracking/latest_operational_report.json`
- `skills/daily_intel/cron_tracking/collection_intelligence.json`
- `skills/daily_intel/cron_tracking/global_collection.json`
- `skills/daily_intel/cron_tracking/collection_daemon_state.json`
- `skills/daily_intel/cron_tracking/collection_events.json`
- `skills/daily_intel/cron_tracking/epistemic_state.json`
- `skills/daily_intel/cron_tracking/sonar_scout_report.json`
- `skills/daily_intel/cron_tracking/cognition_routing.json`
- `skills/daily_intel/cron_tracking/meta_cognition_report.json`
- `skills/daily_intel/memory/chroma_db/chroma.sqlite3`
- `skills/daily_intel/cron_tracking/daily_reports/operational_report_2026-05-12.json`
- `skills/daily_intel/skills/publishing/daily-intel-pipeline.md`


# Skill Security Review - answeroverflow unknown

**Scan Date:** 2026-05-21T00:00:32.372387
**Skill Path:** `/home/ubuntu/.openclaw/skills/answeroverflow`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** answeroverflow
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 1
- **Scripts:** 0
- **Total Lines:** 89

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`


# Skill Security Review - api-gateway 1.0

**Scan Date:** 2026-05-21T00:00:32.373056
**Skill Path:** `/home/ubuntu/.openclaw/skills/api-gateway`

## Verdict

**REJECT** - Found 1 critical issue(s): credential_paths

## Metadata

- **Name:** api-gateway
- **Version:** 1.0
- **Author:** maton
- **Has SKILL.md:** True
- **Files:** 1
- **Scripts:** 0
- **Total Lines:** 639

## Findings

Found **1** potential issue(s):

### credential_paths (critical)

- **File:** `SKILL.md` line 539
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}``

## Files Scanned

- `SKILL.md`


# Skill Security Review - claude-code unknown

**Scan Date:** 2026-05-21T00:00:32.375821
**Skill Path:** `/home/ubuntu/.openclaw/skills/claude-code`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** claude-code
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 4
- **Scripts:** 0
- **Total Lines:** 85

## Findings

No security issues detected.

## Files Scanned

- `README.md`
- `SKILL.md`
- `references/safety-notes.md`
- `references/session-patterns.md`


# Skill Security Review - unknown unknown

**Scan Date:** 2026-05-21T00:00:32.376941
**Skill Path:** `/home/ubuntu/.openclaw/skills/daily_intel`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** unknown
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** False
- **Files:** 1
- **Scripts:** 0
- **Total Lines:** 1

## Findings

No security issues detected.

## Files Scanned

- `memory/vector_index.json`


# Skill Security Review - find-skills unknown

**Scan Date:** 2026-05-21T00:00:32.377442
**Skill Path:** `/home/ubuntu/.openclaw/skills/find-skills`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** find-skills
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 1
- **Scripts:** 0
- **Total Lines:** 134

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`


# Skill Security Review - gmail 1.0

**Scan Date:** 2026-05-21T00:00:32.378148
**Skill Path:** `/home/ubuntu/.openclaw/skills/gmail`

## Verdict

**REJECT** - Found 1 critical issue(s): credential_paths

## Metadata

- **Name:** gmail
- **Version:** 1.0
- **Author:** maton
- **Has SKILL.md:** True
- **Files:** 1
- **Scripts:** 0
- **Total Lines:** 340

## Findings

Found **1** potential issue(s):

### credential_paths (critical)

- **File:** `SKILL.md` line 267
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}``

## Files Scanned

- `SKILL.md`


# Skill Security Review - gog unknown

**Scan Date:** 2026-05-21T00:00:32.379177
**Skill Path:** `/home/ubuntu/.openclaw/skills/gog-myclaw`

## Verdict

**REJECT** - Found 2 critical issue(s): credential_paths

## Metadata

- **Name:** gog
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 4
- **Scripts:** 1
- **Total Lines:** 90

## Findings

Found **3** potential issue(s):

### credential_paths (critical)

- **File:** `SKILL.md` line 23
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `3. Once they provide the `credentials.json` content, save it to `~/.config/gogcli/credentials.json`.`

### credential_paths (critical)

- **File:** `SKILL.md` line 24
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `4. Run: `gog auth credentials set ~/.config/gogcli/credentials.json``

### http_post_external (medium)

- **File:** `config/exchange.py` line 16
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `response = requests.post('https://oauth2.googleapis.com/token', data=data)`

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `config/credentials.json`
- `config/exchange.py`


# Skill Security Review - huggingface-hub unknown

**Scan Date:** 2026-05-21T00:00:32.380782
**Skill Path:** `/home/ubuntu/.openclaw/skills/huggingface-hub`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** huggingface-hub
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 1
- **Scripts:** 0
- **Total Lines:** 36

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`


# Skill Security Review - humanizer 2.1.1

**Scan Date:** 2026-05-21T00:00:32.381318
**Skill Path:** `/home/ubuntu/.openclaw/skills/humanizer`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** humanizer
- **Version:** 2.1.1
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 1
- **Scripts:** 0
- **Total Lines:** 438

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`


# Skill Security Review - maps unknown

**Scan Date:** 2026-05-21T00:00:32.383216
**Skill Path:** `/home/ubuntu/.openclaw/skills/maps-new`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** maps
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 1
- **Scripts:** 0
- **Total Lines:** 37

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`


# Skill Security Review - mobula 1.0.1

**Scan Date:** 2026-05-21T00:00:32.383726
**Skill Path:** `/home/ubuntu/.openclaw/skills/mobula`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** mobula
- **Version:** 1.0.1
- **Author:** Mobula
- **Has SKILL.md:** True
- **Files:** 3
- **Scripts:** 0
- **Total Lines:** 585

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - nano-pdf unknown

**Scan Date:** 2026-05-21T00:00:32.386058
**Skill Path:** `/home/ubuntu/.openclaw/skills/nano-pdf`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** nano-pdf
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 1
- **Scripts:** 0
- **Total Lines:** 21

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`


# Skill Security Review - Network Analysis unknown

**Scan Date:** 2026-05-21T00:00:32.386491
**Skill Path:** `/home/ubuntu/.agents/skills/network-analysis`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** Network Analysis
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 3
- **Scripts:** 2
- **Total Lines:** 313

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `scripts/scaffold-analysis.sh`
- `templates/notebook-template.py`


# Skill Security Review - ocr-and-documents unknown

**Scan Date:** 2026-05-21T00:00:32.388311
**Skill Path:** `/home/ubuntu/.openclaw/skills/ocr-docu`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** ocr-and-documents
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 4
- **Scripts:** 0
- **Total Lines:** 89

## Findings

No security issues detected.

## Files Scanned

- `README.md`
- `SKILL.md`
- `references/output-schema.md`
- `references/tooling-matrix.md`


# Skill Security Review - flight-tracker unknown

**Scan Date:** 2026-05-21T00:00:32.389389
**Skill Path:** `/home/ubuntu/.openclaw/skills/opensky-flight-tracker`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** flight-tracker
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 4
- **Scripts:** 0
- **Total Lines:** 86

## Findings

No security issues detected.

## Files Scanned

- `clawhub.json`
- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - self-improvement unknown

**Scan Date:** 2026-05-21T00:00:32.390707
**Skill Path:** `/home/ubuntu/.openclaw/skills/self-improving-agent`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** self-improvement
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 1
- **Scripts:** 0
- **Total Lines:** 648

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`


# Skill Security Review - skill-scanner unknown

**Scan Date:** 2026-05-21T00:00:32.392520
**Skill Path:** `/home/ubuntu/.openclaw/skills/skill-scanner`

## Verdict

**REJECT** - Found 8 critical issue(s): base64_decode_exec, reverse_shell, credential_paths, systemd_modify, crypto_miner

## Metadata

- **Name:** skill-scanner
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 5
- **Scripts:** 2
- **Total Lines:** 955

## Findings

Found **9** potential issue(s):

### credential_paths (critical)

- **File:** `README.md` line 155
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- Credential path access (~/.ssh, ~/.aws, /etc/passwd)`

### crypto_miner (critical)

- **File:** `README.md` line 9
- **Description:** Cryptocurrency mining indicators
- **Recommendation:** REJECT - this is cryptojacking malware
- **Code:** `- Catches **crypto-mining** indicators (xmrig, mining pools, wallet addresses)`

### crypto_miner (critical)

- **File:** `README.md` line 158
- **Description:** Cryptocurrency mining indicators
- **Recommendation:** REJECT - this is cryptojacking malware
- **Code:** `- Crypto miners (xmrig, ethminer, stratum+tcp)`

### credential_paths (critical)

- **File:** `skill_scanner.py` line 101
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `"pattern": r"~/\.ssh|~/\.aws|~/\.config|/etc/passwd|\.env\b|\.credentials|keychain",`

### crontab_modify (high)

- **File:** `skill_scanner.py` line 118
- **Description:** Modifies system scheduled tasks
- **Recommendation:** Skills should use Clawdbot cron, not system crontab
- **Code:** `"pattern": r"crontab\s+-|/etc/cron|schtasks\s+/create",`

### systemd_modify (critical)

- **File:** `skill_scanner.py` line 126
- **Description:** Creates system services for persistence
- **Recommendation:** REJECT - skills should not create system services
- **Code:** `"pattern": r"systemctl\s+enable|systemctl\s+start|/etc/systemd|launchctl\s+load",`

### crypto_miner (critical)

- **File:** `skill_scanner.py` line 135
- **Description:** Cryptocurrency mining indicators
- **Recommendation:** REJECT - this is cryptojacking malware
- **Code:** `"pattern": r"xmrig|ethminer|cpuminer|cgminer|stratum\+tcp|mining.*pool|hashrate",`

### reverse_shell (critical)

- **File:** `skill_scanner.py` line 161
- **Description:** Reverse shell pattern detected
- **Recommendation:** REJECT - this is a backdoor
- **Code:** `"pattern": r"/dev/tcp/|nc\s+-e|bash\s+-i\s+>&|python.*pty\.spawn",`

### base64_decode_exec (critical)

- **File:** `skill_scanner.py` line 170
- **Description:** Decodes and executes base64 - classic obfuscation
- **Recommendation:** REJECT - likely hiding malicious code
- **Code:** `"pattern": r"base64\.b64decode.*exec|atob.*eval",`

## Files Scanned

- `README.md`
- `SKILL.md`
- `_meta.json`
- `skill_scanner.py`
- `streamlit_ui.py`


# Skill Security Review - stock-market-pro unknown

**Scan Date:** 2026-05-21T00:00:32.403852
**Skill Path:** `/home/ubuntu/.openclaw/skills/stock-market-pro`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** stock-market-pro
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 1
- **Scripts:** 0
- **Total Lines:** 135

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`


# Skill Security Review - stripe 1.0

**Scan Date:** 2026-05-21T00:00:32.404776
**Skill Path:** `/home/ubuntu/.openclaw/skills/stripe-api`

## Verdict

**REJECT** - Found 1 critical issue(s): credential_paths

## Metadata

- **Name:** stripe
- **Version:** 1.0
- **Author:** maton
- **Has SKILL.md:** True
- **Files:** 1
- **Scripts:** 0
- **Total Lines:** 855

## Findings

Found **1** potential issue(s):

### credential_paths (critical)

- **File:** `SKILL.md` line 778
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}``

## Files Scanned

- `SKILL.md`


# Skill Security Review - timeline-chart unknown

**Scan Date:** 2026-05-21T00:00:32.406422
**Skill Path:** `/home/ubuntu/.openclaw/skills/timeline-chart`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** timeline-chart
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 5
- **Scripts:** 1
- **Total Lines:** 340

## Findings

No security issues detected.

## Files Scanned

- `skill.json`
- `SKILL.md`
- `template.py`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - trevor-methodology unknown

**Scan Date:** 2026-05-21T00:00:32.410188
**Skill Path:** `/home/ubuntu/.openclaw/skills/trevor-methodology`

## Verdict

**CAUTION** - Found 1 high-severity issue(s): eval_exec

## Metadata

- **Name:** trevor-methodology
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 25
- **Scripts:** 3
- **Total Lines:** 4967

## Findings

Found **1** potential issue(s):

### eval_exec (high)

- **File:** `pipeline/docx-js-template.js` line 37
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);`

## Files Scanned

- `SKILL.md`
- `TREVOR-One-Page-Summary.md`
- `sanitize.sh`
- `brands/README.md`
- `brands/concentric.json`
- `brands/eclipse.json`
- `brands/neutral.json`
- `brands/nova.json`
- `brands/sps-global.json`
- `methodology/11-SATs.md`
- `methodology/16-sections.md`
- `methodology/6-calibrations.md`
- `methodology/actor-mapping.md`
- `methodology/client-threat-matrix-templates.md`
- `methodology/hypothesis-archetypes.md`
- `methodology/nato-admiralty.md`
- `methodology/quality-gates.md`
- `methodology/scenario-triage.md`
- `methodology/sherman-kent-bands.md`
- `methodology/source-acquisition-guide.md`
- `pipeline/docx-js-template.js`
- `pipeline/output-format-variants.md`
- `pipeline/validate.py`
- `verification/phase4-self-test.md`
- `verification/phase5-acceptance-demonstrations.md`


# Skill Security Review - video-frames unknown

**Scan Date:** 2026-05-21T00:00:32.435344
**Skill Path:** `/home/ubuntu/.openclaw/skills/video-frames`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** video-frames
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 1
- **Scripts:** 0
- **Total Lines:** 30

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`


# Skill Security Review - video-translation unknown

**Scan Date:** 2026-05-21T00:00:32.435785
**Skill Path:** `/home/ubuntu/.agents/skills/video-translation`

## Verdict

**REJECT** - Found 1 critical issue(s): credential_paths

## Metadata

- **Name:** video-translation
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 3
- **Scripts:** 2
- **Total Lines:** 219

## Findings

Found **1** potential issue(s):

### credential_paths (critical)

- **File:** `SKILL.md` line 90
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- `NOIZ_API_KEY` configured for the Noiz backend. If it is not set, first guide the user to get an API key from `https://developers.noiz.ai/api-keys`. After the user provides the key, ask whether they`

## Files Scanned

- `SKILL.md`
- `scripts/replace_audio.sh`
- `scripts/srt_to_duck.py`


# Skill Security Review - wacli unknown

**Scan Date:** 2026-05-21T00:00:32.437921
**Skill Path:** `/home/ubuntu/.openclaw/skills/wacli`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** wacli
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 1
- **Scripts:** 0
- **Total Lines:** 73

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`


# Skill Security Review - web-search-plus unknown

**Scan Date:** 2026-05-21T00:00:32.438464
**Skill Path:** `/home/ubuntu/.openclaw/skills/web-searchplus`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** web-search-plus
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 1
- **Scripts:** 0
- **Total Lines:** 37

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`


# Skill Security Review - whatsapp-business 1.0

**Scan Date:** 2026-05-21T00:00:32.438927
**Skill Path:** `/home/ubuntu/.openclaw/skills/whatsapp-business`

## Verdict

**REJECT** - Found 1 critical issue(s): credential_paths

## Metadata

- **Name:** whatsapp-business
- **Version:** 1.0
- **Author:** maton
- **Has SKILL.md:** True
- **Files:** 1
- **Scripts:** 0
- **Total Lines:** 637

## Findings

Found **1** potential issue(s):

### credential_paths (critical)

- **File:** `SKILL.md` line 494
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}`,`

## Files Scanned

- `SKILL.md`


# Skill Security Review - xurl unknown

**Scan Date:** 2026-05-21T00:00:32.440504
**Skill Path:** `/home/ubuntu/.openclaw/skills/xurl`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** xurl
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 1
- **Scripts:** 0
- **Total Lines:** 462

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`


# Skill Security Review - youtube-content unknown

**Scan Date:** 2026-05-21T00:00:32.441975
**Skill Path:** `/home/ubuntu/.openclaw/skills/youtube-content`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** youtube-content
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 1
- **Scripts:** 0
- **Total Lines:** 35

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`


# Skill Security Review - agent-intelligence unknown

**Scan Date:** 2026-05-21T00:00:32.442437
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/agent-intelligence-network-scan`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** agent-intelligence
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 5
- **Scripts:** 0
- **Total Lines:** 901

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`
- `references/API_REFERENCE.md`
- `references/REPUTATION_ALGORITHM.md`


# Skill Security Review - agentmail unknown

**Scan Date:** 2026-05-21T00:00:32.445665
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/agentmail`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** agentmail
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 9
- **Scripts:** 3
- **Total Lines:** 1745

## Findings

Found **3** potential issue(s):

### env_scraping (medium)

- **File:** `scripts/check_inbox.py` line 83
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `api_key = os.getenv('AGENTMAIL_API_KEY')`

### env_scraping (medium)

- **File:** `scripts/send_email.py` line 46
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `api_key = os.getenv('AGENTMAIL_API_KEY')`

### env_scraping (medium)

- **File:** `scripts/setup_webhook.py` line 51
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `api_key = os.getenv('AGENTMAIL_API_KEY')`

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`
- `references/API.md`
- `references/EXAMPLES.md`
- `references/WEBHOOKS.md`
- `scripts/check_inbox.py`
- `scripts/send_email.py`
- `scripts/setup_webhook.py`


# Skill Security Review - akashic-doc-analyzer 1.0.0

**Scan Date:** 2026-05-21T00:00:32.456631
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/akashic-doc-analyzer`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** akashic-doc-analyzer
- **Version:** 1.0.0
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 3
- **Scripts:** 0
- **Total Lines:** 82

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - baoyu-translate 1.59.0

**Scan Date:** 2026-05-21T00:00:32.457737
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/baoyu-translate`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** baoyu-translate
- **Version:** 1.59.0
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 13
- **Scripts:** 2
- **Total Lines:** 1236

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`
- `references/glossary-en-zh.md`
- `references/refined-workflow.md`
- `references/subagent-prompt-template.md`
- `references/workflow-mechanics.md`
- `scripts/bun.lock`
- `scripts/chunk.ts`
- `scripts/main.ts`
- `scripts/package.json`
- `references/config/extend-schema.md`
- `references/config/first-time-setup.md`


# Skill Security Review - bluf-report unknown

**Scan Date:** 2026-05-21T00:00:32.465417
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/bluf-report`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** bluf-report
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 2
- **Scripts:** 0
- **Total Lines:** 86

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`


# Skill Security Review - chartgen unknown

**Scan Date:** 2026-05-21T00:00:32.466154
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/chartgen-ai`

## Verdict

**REJECT** - Found 5 critical issue(s): credential_paths

## Metadata

- **Name:** chartgen
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 5
- **Scripts:** 1
- **Total Lines:** 826

## Findings

Found **5** potential issue(s):

### credential_paths (critical)

- **File:** `tools/chartgen_api.js` line 25
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `const BASE_URL = process.env.CHARTGEN_API_URL || "https://chartgen.ai";`

### credential_paths (critical)

- **File:** `tools/chartgen_api.js` line 40
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `if (process.env.CHARTGEN_API_KEY) return process.env.CHARTGEN_API_KEY;`

### credential_paths (critical)

- **File:** `tools/chartgen_api.js` line 44
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `process.env.OPENCLAW_STATE_DIR`

### credential_paths (critical)

- **File:** `tools/chartgen_api.js` line 45
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `? path.join(process.env.OPENCLAW_STATE_DIR, "skills", "chartgen", "config.json")`

### credential_paths (critical)

- **File:** `tools/chartgen_api.js` line 74
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `const stateDir = process.env.OPENCLAW_STATE_DIR;`

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`
- `references/upgrade-skill.md`
- `tools/chartgen_api.js`


# Skill Security Review - trevor-web-collection 1.0.0

**Scan Date:** 2026-05-21T00:00:32.473440
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/collection`

## Verdict

**REJECT** - Found 62 critical issue(s): download_execute, credential_paths

## Metadata

- **Name:** trevor-web-collection
- **Version:** 1.0.0
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 1805
- **Scripts:** 467
- **Total Lines:** 192160

## Findings

Found **229** potential issue(s):

### download_execute (critical)

- **File:** `openweb/install-skill.sh` line 5
- **Description:** Downloads and executes remote code
- **Recommendation:** REJECT - classic malware pattern
- **Code:** `#   curl -fsSL https://raw.githubusercontent.com/openweb-org/openweb/main/install-skill.sh | bash`

### credential_paths (critical)

- **File:** `reverse-api-engineer/RELEASING.md` line 40
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `source .env  # or export UV_PUBLISH_TOKEN manually`

### http_post_external (medium)

- **File:** `_specs/animalpolitico/client.py` line 13
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `response = requests.post(f"{base_url}{endpoint}", json=payload, headers=headers)`

### eval_exec (high)

- **File:** `openweb/scripts/adapter-inventory.ts` line 121
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const mCase = caseRe.exec(source)`

### eval_exec (high)

- **File:** `openweb/scripts/adapter-inventory.ts` line 124
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const nextCase = /\n\s*case\s+['\"][^'\"]+['\"]\s*:|\n\s*default\s*:/.exec(tail)`

### eval_exec (high)

- **File:** `openweb/scripts/adapter-inventory.ts` line 131
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const mRec = recRe.exec(source)`

### eval_exec (high)

- **File:** `openweb/scripts/adapter-inventory.ts` line 139
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const mFn = fnRe.exec(source)`

### credential_paths (critical)

- **File:** `openweb/scripts/pack-check.js` line 14
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `const forbidden = ['.ts', 'src/', 'tests/', 'capture/', 'node_modules/', '.env']`

### credential_paths (critical)

- **File:** `openweb/doc/main/security.md` line 121
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `Under `process.env.VITEST`, any operation with permission category `write`, `delete`, or `transact` is refused pre-dispatch with a `TEST_BARRIER` error. This prevents tests from accidentally executing`

### eval_exec (high)

- **File:** `openweb/src/capture/session.ts` line 111
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `/** Attach framenavigated listener; returns cleanup function (Leak #2 fix) */`

### credential_paths (critical)

- **File:** `openweb/src/commands/browser.ts` line 23
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return join(process.env.LOCALAPPDATA ?? join(homedir(), 'AppData', 'Local'), 'Google', 'Chrome', 'User Data', 'Default')`

### credential_paths (critical)

- **File:** `openweb/src/lib/adapter-helpers.ts` line 71
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `credentials: args.credentials as RequestCredentials,`

### credential_paths (critical)

- **File:** `openweb/src/lib/adapter-helpers.ts` line 90
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `credentials: options.credentials ?? 'include',`

### eval_exec (high)

- **File:** `openweb/src/lib/adapter-helpers.ts` line 350
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const m = new RegExp(pattern).exec(value)`

### credential_paths (critical)

- **File:** `openweb/src/lib/config.test.ts` line 20
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `originalHome = process.env.OPENWEB_HOME`

### credential_paths (critical)

- **File:** `openweb/src/lib/config.test.ts` line 21
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `process.env.OPENWEB_HOME = tmpDir`

### credential_paths (critical)

- **File:** `openweb/src/lib/config.test.ts` line 26
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `Reflect.deleteProperty(process.env, 'OPENWEB_HOME')`

### credential_paths (critical)

- **File:** `openweb/src/lib/config.test.ts` line 28
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `process.env.OPENWEB_HOME = originalHome`

### credential_paths (critical)

- **File:** `openweb/src/lib/config.ts` line 18
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), '.openweb')`

### eval_exec (high)

- **File:** `openweb/src/lib/template-resolver.ts` line 62
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const wholeMatch = /^\$\{([^}]+)\}$/.exec(escaped)`

### credential_paths (critical)

- **File:** `openweb/src/runtime/http-executor.ts` line 121
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `if (process.env.VITEST && (category === 'write' || category === 'delete' || category === 'transact')) {`

### eval_exec (high)

- **File:** `openweb/src/compiler/analyzer/auth-candidates.ts` line 303
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (let match = metaRegex.exec(data.domHtml); match !== null; match = metaRegex.exec(data.domHtml)) {`

### eval_exec (high)

- **File:** `openweb/src/compiler/analyzer/classify.ts` line 40
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const match = /<script\s+id="__NEXT_DATA__"\s+type="application\/json"[^>]*>/i.exec(html)`

### eval_exec (high)

- **File:** `openweb/src/compiler/analyzer/classify.ts` line 63
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (let match = regex.exec(html); match !== null; match = regex.exec(html)) {`

### eval_exec (high)

- **File:** `openweb/src/compiler/analyzer/classify.ts` line 69
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const idMatch = /id="([^"]+)"/i.exec(attrs)`

### eval_exec (high)

- **File:** `openweb/src/compiler/analyzer/classify.ts` line 70
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const dataTargetMatch = /data-target="([^"]+)"/i.exec(attrs)`

### eval_exec (high)

- **File:** `openweb/src/compiler/analyzer/classify.ts` line 102
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (let m = regex.exec(html); m; m = regex.exec(html)) {`

### eval_exec (high)

- **File:** `openweb/src/compiler/analyzer/csrf-detect.ts` line 85
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (let match = metaRegex.exec(data.domHtml); match !== null; match = metaRegex.exec(data.domHtml)) {`

### eval_exec (high)

- **File:** `openweb/src/compiler/analyzer/graphql-cluster.ts` line 152
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const match = OPERATION_NAME_RE.exec(query)`

### eval_exec (high)

- **File:** `openweb/src/compiler/analyzer/graphql-cluster.ts` line 168
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const match = OPERATION_TYPE_RE.exec(queryText)`

### eval_exec (high)

- **File:** `openweb/src/compiler/curation/apply-curation.test.ts` line 177
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `it('is a pure function (same inputs → same output)', () => {`

### eval_exec (high)

- **File:** `openweb/src/runtime/primitives/page-expression.ts` line 12
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `'eval(',`

### eval_exec (high)

- **File:** `openweb/src/runtime/primitives/page-expression.ts` line 13
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `'Function(',`

### eval_exec (high)

- **File:** `openweb/src/runtime/primitives/page-expression.ts` line 46
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `return new Function(`return ${expr}`)() as unknown`

### credential_paths (critical)

- **File:** `openweb/src/runtime/primitives/primitives.test.ts` line 870
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `chunk_global: 'process.env',`

### eval_exec (high)

- **File:** `openweb/src/runtime/primitives/primitives.test.ts` line 281
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (const malicious of ['fetch("http://evil.com")', 'document.cookie', 'eval("alert(1)")']) {`

### eval_exec (high)

- **File:** `openweb/src/runtime/primitives/script-json-parse.ts` line 10
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const m = HTML_COMMENT.exec(raw)`

### eval_exec (high)

- **File:** `openweb/src/runtime/primitives/script-json-parse.ts` line 55
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const match = /^([a-zA-Z_-][\w-]*)\s*=\s*"([^"]*)"$/.exec(clause) ?? /^([a-zA-Z_-][\w-]*)\s*=\s*'([^']*)'$/.exec(clause)`

### eval_exec (high)

- **File:** `openweb/src/runtime/primitives/script-json-parse.ts` line 88
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const m = re.exec(attrsStr)`

### eval_exec (high)

- **File:** `openweb/src/runtime/primitives/script-json-parse.ts` line 105
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (let m = SCRIPT_TAG_RE.exec(html); m; m = SCRIPT_TAG_RE.exec(html)) {`

### eval_exec (high)

- **File:** `openweb/src/runtime/primitives/script-json-parse.ts` line 116
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (let m = SCRIPT_TAG_RE.exec(html); m; m = SCRIPT_TAG_RE.exec(html)) {`

### credential_paths (critical)

- **File:** `openweb/src/sites/costco/PROGRESS.md` line 9
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- Identified required custom headers: `client-identifier`, `costco.env`, `costco.service``

### credential_paths (critical)

- **File:** `openweb/src/sites/costco/PROGRESS.md` line 11
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- Fixed product 404 by adding `costco.env: ecom` and `costco.service: restProduct` headers`

### eval_exec (high)

- **File:** `openweb/src/sites/angellist/adapters/angellist.ts` line 125
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `await page.waitForFunction(() => !!(window as any).__APOLLO_CLIENT__, { timeout: 15_000 })`

### eval_exec (high)

- **File:** `openweb/src/sites/angellist/adapters/angellist.js` line 105
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `await page.waitForFunction(() => !!window.__APOLLO_CLIENT__, { timeout: 15e3 });`

### credential_paths (critical)

- **File:** `openweb/src/sites/bluesky/adapters/bluesky-public.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### credential_paths (critical)

- **File:** `openweb/src/sites/booking/adapters/booking.ts` line 267
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `// Try to get from booking.env on the current page`

### credential_paths (critical)

- **File:** `openweb/src/sites/booking/adapters/booking.ts` line 270
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `const hotelEnv = env?.env as Record<string, unknown> | undefined`

### credential_paths (critical)

- **File:** `openweb/src/sites/booking/adapters/booking.js` line 163
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `const hotelEnv = env?.env;`

### credential_paths (critical)

- **File:** `openweb/src/sites/boss/adapters/boss.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### credential_paths (critical)

- **File:** `openweb/src/sites/coingecko/adapters/coingecko.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### credential_paths (critical)

- **File:** `openweb/src/sites/coinmarketcap/adapters/coinmarketcap.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### credential_paths (critical)

- **File:** `openweb/src/sites/costco/adapters/costco-api.ts` line 190
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `'costco.env': 'ecom',`

### credential_paths (critical)

- **File:** `openweb/src/sites/costco/adapters/costco-api.ts` line 271
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `'costco.env': 'ecom',`

### credential_paths (critical)

- **File:** `openweb/src/sites/costco/adapters/costco-api.ts` line 445
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `'costco.env': 'ecom',`

### credential_paths (critical)

- **File:** `openweb/src/sites/costco/adapters/costco-api.ts` line 584
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `'costco.env': 'ecom',`

### credential_paths (critical)

- **File:** `openweb/src/sites/costco/adapters/costco-api.ts` line 769
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `'costco.env': 'ecom',`

### credential_paths (critical)

- **File:** `openweb/src/sites/costco/adapters/costco-api.ts` line 814
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `'costco.env': 'ecom',`

### http_post_external (medium)

- **File:** `openweb/src/sites/costco/adapters/costco-api.ts` line 946
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const r = await fetch(u, { method: 'POST', headers: { Accept: '*/*', 'Content-Type': 'text/plain;charset=UTF-8' }, credentials: 'include' })`

### credential_paths (critical)

- **File:** `openweb/src/sites/costco/adapters/costco-api.js` line 134
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `"costco.env": "ecom",`

### credential_paths (critical)

- **File:** `openweb/src/sites/costco/adapters/costco-api.js` line 199
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `"costco.env": "ecom",`

### credential_paths (critical)

- **File:** `openweb/src/sites/costco/adapters/costco-api.js` line 340
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `"costco.env": "ecom",`

### credential_paths (critical)

- **File:** `openweb/src/sites/costco/adapters/costco-api.js` line 456
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `"costco.env": "ecom",`

### credential_paths (critical)

- **File:** `openweb/src/sites/costco/adapters/costco-api.js` line 605
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `"costco.env": "ecom",`

### credential_paths (critical)

- **File:** `openweb/src/sites/costco/adapters/costco-api.js` line 642
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `"costco.env": "ecom",`

### http_post_external (medium)

- **File:** `openweb/src/sites/costco/adapters/costco-api.js` line 758
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const r = await fetch(u, { method: "POST", headers: { Accept: "*/*", "Content-Type": "text/plain;charset=UTF-8" }, credentials: "include" });`

### eval_exec (high)

- **File:** `openweb/src/sites/craigslist/adapters/craigslist.ts` line 62
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (m = resultRe.exec(html); m !== null; m = resultRe.exec(html)) {`

### eval_exec (high)

- **File:** `openweb/src/sites/craigslist/adapters/craigslist.ts` line 129
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (tm = timeRe.exec(html); tm !== null; tm = timeRe.exec(html)) {`

### eval_exec (high)

- **File:** `openweb/src/sites/craigslist/adapters/craigslist.ts` line 140
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (am = attrRe.exec(html); am !== null; am = attrRe.exec(html)) {`

### eval_exec (high)

- **File:** `openweb/src/sites/craigslist/adapters/craigslist.ts` line 152
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (im = hrefRe.exec(thumbsMatch[1]); im !== null; im = hrefRe.exec(thumbsMatch[1])) {`

### eval_exec (high)

- **File:** `openweb/src/sites/craigslist/adapters/craigslist.ts` line 173
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (lm = catRe.exec(html); lm !== null; lm = catRe.exec(html)) {`

### eval_exec (high)

- **File:** `openweb/src/sites/craigslist/adapters/craigslist.js` line 42
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (m = resultRe.exec(html); m !== null; m = resultRe.exec(html)) {`

### eval_exec (high)

- **File:** `openweb/src/sites/craigslist/adapters/craigslist.js` line 87
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (tm = timeRe.exec(html); tm !== null; tm = timeRe.exec(html)) {`

### eval_exec (high)

- **File:** `openweb/src/sites/craigslist/adapters/craigslist.js` line 96
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (am = attrRe.exec(html); am !== null; am = attrRe.exec(html)) {`

### eval_exec (high)

- **File:** `openweb/src/sites/craigslist/adapters/craigslist.js` line 106
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (im = hrefRe.exec(thumbsMatch[1]); im !== null; im = hrefRe.exec(thumbsMatch[1])) {`

### eval_exec (high)

- **File:** `openweb/src/sites/craigslist/adapters/craigslist.js` line 120
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (lm = catRe.exec(html); lm !== null; lm = catRe.exec(html)) {`

### credential_paths (critical)

- **File:** `openweb/src/sites/docker-hub/adapters/docker-hub.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### credential_paths (critical)

- **File:** `openweb/src/sites/douban/adapters/douban-read.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### credential_paths (critical)

- **File:** `openweb/src/sites/ebay/adapters/ebay.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### credential_paths (critical)

- **File:** `openweb/src/sites/espn/adapters/espn.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### eval_exec (high)

- **File:** `openweb/src/sites/github/adapters/github-web.ts` line 83
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `await page.waitForFunction(`

### credential_paths (critical)

- **File:** `openweb/src/sites/github/adapters/github-read.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### eval_exec (high)

- **File:** `openweb/src/sites/github/adapters/github-web.js` line 27
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `await page.waitForFunction(`

### credential_paths (critical)

- **File:** `openweb/src/sites/gitlab/adapters/gitlab.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### eval_exec (high)

- **File:** `openweb/src/sites/goodreads/adapters/goodreads.ts` line 60
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (rm = rowRe.exec(html); rm !== null; rm = rowRe.exec(html)) {`

### eval_exec (high)

- **File:** `openweb/src/sites/goodreads/adapters/goodreads.ts` line 214
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (gm = genreRe.exec(html); gm !== null; gm = genreRe.exec(html)) {`

### eval_exec (high)

- **File:** `openweb/src/sites/goodreads/adapters/goodreads.ts` line 227
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (bm = bookRowRe.exec(html); bm !== null; bm = bookRowRe.exec(html)) {`

### credential_paths (critical)

- **File:** `openweb/src/sites/goodreads/adapters/goodreads.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### eval_exec (high)

- **File:** `openweb/src/sites/goodreads/adapters/goodreads.js` line 494
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (rm = rowRe.exec(html); rm !== null; rm = rowRe.exec(html)) {`

### eval_exec (high)

- **File:** `openweb/src/sites/goodreads/adapters/goodreads.js` line 608
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (gm = genreRe.exec(html); gm !== null; gm = genreRe.exec(html)) {`

### eval_exec (high)

- **File:** `openweb/src/sites/goodreads/adapters/goodreads.js` line 617
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (bm = bookRowRe.exec(html); bm !== null; bm = bookRowRe.exec(html)) {`

### eval_exec (high)

- **File:** `openweb/src/sites/google-flights/adapters/google-flights.ts` line 21
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (match = regex.exec(html); match !== null; match = regex.exec(html)) {`

### credential_paths (critical)

- **File:** `openweb/src/sites/google-flights/adapters/google-flights.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### eval_exec (high)

- **File:** `openweb/src/sites/google-flights/adapters/google-flights.js` line 458
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (match = regex.exec(html); match !== null; match = regex.exec(html)) {`

### eval_exec (high)

- **File:** `openweb/src/sites/google-search/adapters/google-search.ts` line 152
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `await page.waitForFunction(() => /\$\d/.test(document.body.innerText), { timeout: 10_000 }).catch(() => {})`

### eval_exec (high)

- **File:** `openweb/src/sites/google-search/adapters/google-search.js` line 123
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `await page.waitForFunction(() => /\$\d/.test(document.body.innerText), { timeout: 1e4 }).catch(() => {`

### credential_paths (critical)

- **File:** `openweb/src/sites/guardian/adapters/guardian.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### credential_paths (critical)

- **File:** `openweb/src/sites/huggingface/adapters/huggingface.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### credential_paths (critical)

- **File:** `openweb/src/sites/imdb/adapters/imdb.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### http_post_external (medium)

- **File:** `openweb/src/sites/instagram/adapters/instagram-api.ts` line 80
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const result = await pageFetch(page, { url, method: 'POST', headers, body, credentials: 'include' })`

### http_post_external (medium)

- **File:** `openweb/src/sites/instagram/adapters/instagram-api.js` line 63
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const result = await pageFetch(page, { url, method: "POST", headers, body, credentials: "include" });`

### eval_exec (high)

- **File:** `openweb/src/sites/linkedin/adapters/linkedin-graphql.ts` line 67
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `let m: RegExpExecArray | null = re.exec(text)`

### eval_exec (high)

- **File:** `openweb/src/sites/linkedin/adapters/linkedin-graphql.ts` line 70
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `m = re.exec(text)`

### eval_exec (high)

- **File:** `openweb/src/sites/linkedin/adapters/linkedin-graphql.js` line 30
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `let m = re.exec(text);`

### eval_exec (high)

- **File:** `openweb/src/sites/linkedin/adapters/linkedin-graphql.js` line 33
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `m = re.exec(text);`

### http_post_external (medium)

- **File:** `openweb/src/sites/medium/adapters/medium-graphql.ts` line 232
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const data = (await graphqlFetch(page, 'PostDetailQuery', POST_DETAIL_QUERY, {`

### http_post_external (medium)

- **File:** `openweb/src/sites/medium/adapters/medium-graphql.ts` line 345
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const data = (await graphqlFetch(page, 'ClapCountQuery', POST_CLAPS_QUERY, {`

### http_post_external (medium)

- **File:** `openweb/src/sites/medium/adapters/medium-graphql.js` line 482
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const data = await graphqlFetch(page, "PostDetailQuery", POST_DETAIL_QUERY, {`

### http_post_external (medium)

- **File:** `openweb/src/sites/medium/adapters/medium-graphql.js` line 576
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const data = await graphqlFetch(page, "ClapCountQuery", POST_CLAPS_QUERY, {`

### credential_paths (critical)

- **File:** `openweb/src/sites/npm/adapters/npm.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### credential_paths (critical)

- **File:** `openweb/src/sites/npr/adapters/npr.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### credential_paths (critical)

- **File:** `openweb/src/sites/pypi/adapters/pypi.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### credential_paths (critical)

- **File:** `openweb/src/sites/reddit/adapters/reddit-read.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### eval_exec (high)

- **File:** `openweb/src/sites/redfin/adapters/redfin.ts` line 95
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (match = jsonLdRegex.exec(result.text); match !== null; match = jsonLdRegex.exec(result.text)) {`

### credential_paths (critical)

- **File:** `openweb/src/sites/redfin/adapters/redfin.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### eval_exec (high)

- **File:** `openweb/src/sites/redfin/adapters/redfin.js` line 538
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (match = jsonLdRegex.exec(result.text); match !== null; match = jsonLdRegex.exec(result.text)) {`

### eval_exec (high)

- **File:** `openweb/src/sites/rotten-tomatoes/adapters/rotten-tomatoes-web.ts` line 78
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (m = rowRegex.exec(section); m !== null; m = rowRegex.exec(section)) {`

### credential_paths (critical)

- **File:** `openweb/src/sites/rotten-tomatoes/adapters/rotten-tomatoes-web.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### eval_exec (high)

- **File:** `openweb/src/sites/rotten-tomatoes/adapters/rotten-tomatoes-web.js` line 493
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `for (m = rowRegex.exec(section); m !== null; m = rowRegex.exec(section)) {`

### credential_paths (critical)

- **File:** `openweb/src/sites/soundcloud/adapters/soundcloud.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### http_post_external (medium)

- **File:** `openweb/src/sites/spotify/adapters/spotify-pathfinder.ts` line 382
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const result = await spclientFetch(page, 'POST', url, accessToken, clientToken, body)`

### http_post_external (medium)

- **File:** `openweb/src/sites/spotify/adapters/spotify-pathfinder.ts` line 403
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const result = await spclientFetch(page, 'POST', url, accessToken, clientToken, body)`

### http_post_external (medium)

- **File:** `openweb/src/sites/spotify/adapters/spotify-pathfinder.ts` line 419
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const result = await spclientFetch(page, 'POST', url, accessToken, clientToken, body)`

### http_post_external (medium)

- **File:** `openweb/src/sites/spotify/adapters/spotify-pathfinder.ts` line 433
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `await spclientFetch(page, 'POST', `https://spclient.wg.spotify.com/playlist/v2/playlist/${playlistId}/changes`, accessToken, clientToken, updateBody)`

### http_post_external (medium)

- **File:** `openweb/src/sites/spotify/adapters/spotify-pathfinder.js` line 280
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const result = await spclientFetch(page, "POST", url, accessToken, clientToken, body);`

### http_post_external (medium)

- **File:** `openweb/src/sites/spotify/adapters/spotify-pathfinder.js` line 301
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const result = await spclientFetch(page, "POST", url, accessToken, clientToken, body);`

### http_post_external (medium)

- **File:** `openweb/src/sites/spotify/adapters/spotify-pathfinder.js` line 315
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const result = await spclientFetch(page, "POST", url, accessToken, clientToken, body);`

### http_post_external (medium)

- **File:** `openweb/src/sites/spotify/adapters/spotify-pathfinder.js` line 326
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `await spclientFetch(page, "POST", `https://spclient.wg.spotify.com/playlist/v2/playlist/${playlistId}/changes`, accessToken, clientToken, updateBody);`

### credential_paths (critical)

- **File:** `openweb/src/sites/stackoverflow/adapters/stackoverflow.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### credential_paths (critical)

- **File:** `openweb/src/sites/steam/adapters/steam.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### credential_paths (critical)

- **File:** `openweb/src/sites/substack/adapters/substack.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### credential_paths (critical)

- **File:** `openweb/src/sites/techcrunch/adapters/techcrunch.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.ts` line 124
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const getGlobal = new Function(`return (${globalSrc})()`)() as (() => Record<string, unknown>) | null`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.ts` line 126
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const callApi = new Function(`return (${apiSrc})()`)() as ((...a: unknown[]) => Promise<unknown>) | null`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.ts` line 169
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const getGlobal = new Function(`return (${args.fnSrc})()`)() as (() => Record<string, unknown>) | null`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.ts` line 215
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const getGlobal = new Function(`return (${args.fnSrc})()`)() as (() => Record<string, unknown>) | null`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.ts` line 251
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const getGlobal = new Function(`return (${args.fnSrc})()`)() as (() => Record<string, unknown>) | null`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.ts` line 290
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const getGlobal = new Function(`return (${args.fnSrc})()`)() as (() => Record<string, unknown>) | null`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.ts` line 315
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const getGlobal = new Function(`return (${fnSrc})()`)() as (() => Record<string, unknown>) | null`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.ts` line 339
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const getGlobal = new Function(`return (${fnSrc})()`)() as (() => Record<string, unknown>) | null`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.ts` line 372
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const resolveCtx = new Function(`return (${args.ctxSrc})`)() as typeof import('./telegram-protocol').resolveCtx`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.ts` line 385
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const resolveCtx = new Function(`return (${args.ctxSrc})`)() as typeof import('./telegram-protocol').resolveCtx`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.ts` line 410
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const resolveCtx = new Function(`return (${args.ctxSrc})`)() as typeof import('./telegram-protocol').resolveCtx`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.ts` line 435
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const resolveCtx = new Function(`return (${args.ctxSrc})`)() as typeof import('./telegram-protocol').resolveCtx`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.ts` line 473
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const resolveCtx = new Function(`return (${args.ctxSrc})`)() as typeof import('./telegram-protocol').resolveCtx`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.ts` line 496
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const resolveCtx = new Function(`return (${args.ctxSrc})`)() as typeof import('./telegram-protocol').resolveCtx`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.ts` line 523
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const resolveCtx = new Function(`return (${args.ctxSrc})`)() as typeof import('./telegram-protocol').resolveCtx`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.ts` line 566
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const findFn = new Function(`return (${fnSrc})()`) as () => (() => Record<string, unknown>) | null`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.ts` line 600
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const findFn = new Function(`return (${fnSrc})()`) as () => (() => Record<string, unknown>) | null`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.ts` line 667
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const getGlobal = new Function(`return (${args.globalSrc})()`)() as (() => Record<string, unknown>) | null`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.ts` line 669
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const getActions = new Function(`return (${args.actionsSrc})()`)() as (() => Record<string, (a?: unknown) => unknown>) | null`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.js` line 104
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const getGlobal = new Function(`return (${globalSrc})()`)();`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.js` line 106
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const callApi = new Function(`return (${apiSrc})()`)();`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.js` line 131
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const getGlobal = new Function(`return (${args.fnSrc})()`)();`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.js` line 167
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const getGlobal = new Function(`return (${args.fnSrc})()`)();`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.js` line 198
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const getGlobal = new Function(`return (${args.fnSrc})()`)();`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.js` line 232
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const getGlobal = new Function(`return (${args.fnSrc})()`)();`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.js` line 251
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const getGlobal = new Function(`return (${fnSrc})()`)();`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.js` line 268
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const getGlobal = new Function(`return (${fnSrc})()`)();`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.js` line 292
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const resolveCtx2 = new Function(`return (${args.ctxSrc})`)();`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.js` line 304
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const resolveCtx2 = new Function(`return (${args.ctxSrc})`)();`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.js` line 328
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const resolveCtx2 = new Function(`return (${args.ctxSrc})`)();`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.js` line 352
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const resolveCtx2 = new Function(`return (${args.ctxSrc})`)();`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.js` line 388
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const resolveCtx2 = new Function(`return (${args.ctxSrc})`)();`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.js` line 410
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const resolveCtx2 = new Function(`return (${args.ctxSrc})`)();`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.js` line 435
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const resolveCtx2 = new Function(`return (${args.ctxSrc})`)();`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.js` line 461
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const findFn = new Function(`return (${fnSrc})()`);`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.js` line 492
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const findFn = new Function(`return (${fnSrc})()`);`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.js` line 531
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const getGlobal = new Function(`return (${args.globalSrc})()`)();`

### eval_exec (high)

- **File:** `openweb/src/sites/telegram/adapters/telegram-protocol.js` line 533
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `const getActions = new Function(`return (${args.actionsSrc})()`)();`

### http_post_external (medium)

- **File:** `openweb/src/sites/todoist/adapters/todoist-api.ts` line 210
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const raw = await apiFetch(page, 'POST', '/tasks', body, errors) as Record<string, unknown>`

### http_post_external (medium)

- **File:** `openweb/src/sites/todoist/adapters/todoist-api.ts` line 219
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const seed = await apiFetch(page, 'POST', '/tasks', { content: '_openweb_verify_complete' }, errors) as Record<string, unknown>`

### http_post_external (medium)

- **File:** `openweb/src/sites/todoist/adapters/todoist-api.ts` line 223
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const result = await apiFetch(page, 'POST', `/tasks/${encodeURIComponent(taskId)}/close`, null, errors)`

### http_post_external (medium)

- **File:** `openweb/src/sites/todoist/adapters/todoist-api.ts` line 233
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const seed = await apiFetch(page, 'POST', '/tasks', { content: '_openweb_verify_uncomplete' }, errors) as Record<string, unknown>`

### http_post_external (medium)

- **File:** `openweb/src/sites/todoist/adapters/todoist-api.ts` line 236
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `await apiFetch(page, 'POST', `/tasks/${encodeURIComponent(taskId)}/close`, null, errors)`

### http_post_external (medium)

- **File:** `openweb/src/sites/todoist/adapters/todoist-api.ts` line 238
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const result = await apiFetch(page, 'POST', `/tasks/${encodeURIComponent(taskId)}/reopen`, null, errors)`

### http_post_external (medium)

- **File:** `openweb/src/sites/todoist/adapters/todoist-api.ts` line 247
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const seed = await apiFetch(page, 'POST', '/tasks', { content: '_openweb_verify_delete' }, errors) as Record<string, unknown>`

### http_post_external (medium)

- **File:** `openweb/src/sites/todoist/adapters/todoist-api.js` line 160
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const raw = await apiFetch(page, "POST", "/tasks", body, errors);`

### http_post_external (medium)

- **File:** `openweb/src/sites/todoist/adapters/todoist-api.js` line 168
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const seed = await apiFetch(page, "POST", "/tasks", { content: "_openweb_verify_complete" }, errors);`

### http_post_external (medium)

- **File:** `openweb/src/sites/todoist/adapters/todoist-api.js` line 172
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const result = await apiFetch(page, "POST", `/tasks/${encodeURIComponent(taskId)}/close`, null, errors);`

### http_post_external (medium)

- **File:** `openweb/src/sites/todoist/adapters/todoist-api.js` line 182
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const seed = await apiFetch(page, "POST", "/tasks", { content: "_openweb_verify_uncomplete" }, errors);`

### http_post_external (medium)

- **File:** `openweb/src/sites/todoist/adapters/todoist-api.js` line 185
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `await apiFetch(page, "POST", `/tasks/${encodeURIComponent(taskId)}/close`, null, errors);`

### http_post_external (medium)

- **File:** `openweb/src/sites/todoist/adapters/todoist-api.js` line 187
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const result = await apiFetch(page, "POST", `/tasks/${encodeURIComponent(taskId)}/reopen`, null, errors);`

### http_post_external (medium)

- **File:** `openweb/src/sites/todoist/adapters/todoist-api.js` line 196
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const seed = await apiFetch(page, "POST", "/tasks", { content: "_openweb_verify_delete" }, errors);`

### http_post_external (medium)

- **File:** `openweb/src/sites/trello/adapters/trello-api.ts` line 228
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const card = (await apiFetch(page, helpers, 'POST', '/cards', undefined, body)) as Record<string, unknown>`

### http_post_external (medium)

- **File:** `openweb/src/sites/trello/adapters/trello-api.js` line 167
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const card = await apiFetch(page, helpers, "POST", "/cards", void 0, body);`

### eval_exec (high)

- **File:** `openweb/src/sites/x/adapters/x-graphql.ts` line 66
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `let m: RegExpExecArray | null = re.exec(before)`

### eval_exec (high)

- **File:** `openweb/src/sites/x/adapters/x-graphql.ts` line 67
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `while (m !== null) { lastId = m[1]; m = re.exec(before) }`

### eval_exec (high)

- **File:** `openweb/src/sites/x/adapters/x-graphql.ts` line 92
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `let m: RegExpExecArray | null = re.exec(text)`

### eval_exec (high)

- **File:** `openweb/src/sites/x/adapters/x-graphql.ts` line 95
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `m = re.exec(text)`

### http_post_external (medium)

- **File:** `openweb/src/sites/x/adapters/x-graphql.ts` line 187
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const resp = await fetch(url, { method: 'POST', headers, body: args.body, credentials: 'include' })`

### eval_exec (high)

- **File:** `openweb/src/sites/x/adapters/x-graphql.js` line 38
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `let m = re.exec(before);`

### eval_exec (high)

- **File:** `openweb/src/sites/x/adapters/x-graphql.js` line 41
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `m = re.exec(before);`

### eval_exec (high)

- **File:** `openweb/src/sites/x/adapters/x-graphql.js` line 60
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `let m = re.exec(text);`

### eval_exec (high)

- **File:** `openweb/src/sites/x/adapters/x-graphql.js` line 63
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `m = re.exec(text);`

### http_post_external (medium)

- **File:** `openweb/src/sites/x/adapters/x-graphql.js` line 139
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const resp = await fetch(url, { method: "POST", headers, body: args.body, credentials: "include" });`

### eval_exec (high)

- **File:** `openweb/src/sites/xiaohongshu/adapters/xiaohongshu-web.ts` line 101
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `await page.waitForFunction(`

### eval_exec (high)

- **File:** `openweb/src/sites/xiaohongshu/adapters/xiaohongshu-web.ts` line 243
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `await page.waitForFunction(`

### eval_exec (high)

- **File:** `openweb/src/sites/xiaohongshu/adapters/xiaohongshu-web.ts` line 352
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `await page.waitForFunction(() => !!(window as XhsWindow).__INITIAL_STATE__?.note, { timeout: 10000 }).catch(() => null)`

### eval_exec (high)

- **File:** `openweb/src/sites/xiaohongshu/adapters/xiaohongshu-web.ts` line 498
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `await page.waitForFunction(`

### eval_exec (high)

- **File:** `openweb/src/sites/xiaohongshu/adapters/xiaohongshu-web.js` line 77
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `await page.waitForFunction(`

### eval_exec (high)

- **File:** `openweb/src/sites/xiaohongshu/adapters/xiaohongshu-web.js` line 236
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `await page.waitForFunction(`

### eval_exec (high)

- **File:** `openweb/src/sites/xiaohongshu/adapters/xiaohongshu-web.js` line 342
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `await page.waitForFunction(() => !!window.__INITIAL_STATE__?.note, { timeout: 1e4 }).catch(() => null);`

### eval_exec (high)

- **File:** `openweb/src/sites/xiaohongshu/adapters/xiaohongshu-web.js` line 501
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `await page.waitForFunction(`

### credential_paths (critical)

- **File:** `openweb/src/sites/yahoo-finance/adapters/yahoo-finance.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### credential_paths (critical)

- **File:** `openweb/src/sites/yelp/adapters/yelp.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### eval_exec (high)

- **File:** `openweb/src/sites/youtube/adapters/youtube-innertube.ts` line 424
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `await page.waitForFunction(() => {`

### http_post_external (medium)

- **File:** `openweb/src/sites/youtube/adapters/youtube-innertube.ts` line 123
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const result = await pageFetch(page, { url, method: 'POST', headers, body: JSON.stringify(body) })`

### http_post_external (medium)

- **File:** `openweb/src/sites/youtube/adapters/youtube-innertube.ts` line 158
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const result = await pageFetch(page, { url, method: 'POST', headers, body: JSON.stringify(body) })`

### eval_exec (high)

- **File:** `openweb/src/sites/youtube/adapters/youtube-innertube.js` line 316
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `await page.waitForFunction(() => {`

### http_post_external (medium)

- **File:** `openweb/src/sites/youtube/adapters/youtube-innertube.js` line 71
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const result = await pageFetch(page, { url, method: "POST", headers, body: JSON.stringify(body) });`

### http_post_external (medium)

- **File:** `openweb/src/sites/youtube/adapters/youtube-innertube.js` line 98
- **Description:** HTTP POST to external endpoint - could exfiltrate data
- **Recommendation:** Verify destination URL is expected and documented
- **Code:** `const result = await pageFetch(page, { url, method: "POST", headers, body: JSON.stringify(body) });`

### credential_paths (critical)

- **File:** `openweb/src/sites/zhihu/adapters/zhihu-read.js` line 7
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `return process.env.OPENWEB_HOME ?? path.join(os.homedir(), ".openweb");`

### credential_paths (critical)

- **File:** `openweb/tests/integration/runner.ts` line 14
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `const CDP_ENDPOINT = process.env.CDP_ENDPOINT ?? 'http://localhost:9222'`

### env_scraping (medium)

- **File:** `reverse-api-engineer/src/reverse_api/base_engineer.py` line 17
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `DEBUG = os.environ.get("DEBUG", "0") == "1"`

### credential_paths (critical)

- **File:** `reverse-api-engineer/src/reverse_api/browser.py` line 326
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `"--use-mock-keychain",`

### eval_exec (high)

- **File:** `reverse-api-engineer/src/reverse_api/browser.py` line 94
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `Element.prototype.attachShadow = function(init) {`

### eval_exec (high)

- **File:** `reverse-api-engineer/src/reverse_api/browser.py` line 103
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `WebGLRenderingContext.prototype.getParameter = function(parameter) {`

### eval_exec (high)

- **File:** `reverse-api-engineer/src/reverse_api/browser.py` line 115
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `WebGL2RenderingContext.prototype.getParameter = function(parameter) {`

### eval_exec (high)

- **File:** `reverse-api-engineer/src/reverse_api/browser.py` line 127
- **Description:** Dynamic code execution - could run arbitrary code
- **Recommendation:** Verify input is sanitized, not user-controlled
- **Code:** `navigator.permissions.query = function(permissionDesc) {`

### env_scraping (medium)

- **File:** `reverse-api-engineer/src/reverse_api/cli.py` line 258
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `elif not os.environ.get(sdk_env_var):`

### env_scraping (medium)

- **File:** `reverse-api-engineer/src/reverse_api/cursor_engineer.py` line 184
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `api_key = os.environ.get("CURSOR_API_KEY", "")`

### env_scraping (medium)

- **File:** `reverse-api-engineer/src/reverse_api/cursor_engineer.py` line 347
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `if not os.environ.get("CURSOR_API_KEY"):`

### env_scraping (medium)

- **File:** `reverse-api-engineer/src/reverse_api/cursor_engineer.py` line 479
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `if not os.environ.get("CURSOR_API_KEY"):`

### bulk_env_access (high)

- **File:** `reverse-api-engineer/src/reverse_api/cursor_engineer.py` line 218
- **Description:** Bulk access to all environment variables - likely exfiltration
- **Recommendation:** REJECT - review carefully for data theft
- **Code:** `env=os.environ.copy(),`

### env_scraping (medium)

- **File:** `reverse-api-engineer/src/reverse_api/opencode_engineer.py` line 20
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `DEBUG = os.environ.get("OPENCODE_DEBUG", "0") == "1"`

### env_scraping (medium)

- **File:** `reverse-api-engineer/src/reverse_api/opencode_engineer.py` line 128
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `self.opencode_password = os.environ.get("OPENCODE_SERVER_PASSWORD")`

### env_scraping (medium)

- **File:** `reverse-api-engineer/src/reverse_api/opencode_engineer.py` line 129
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `self.opencode_username = os.environ.get("OPENCODE_SERVER_USERNAME", "opencode")`

### env_scraping (medium)

- **File:** `reverse-api-engineer/src/reverse_api/utils.py` line 458
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `user_profile = os.environ.get("USERPROFILE", str(home))`

## Files Scanned

- `LICENSES.md`
- `VERSIONS.md`
- `SKILL.md`
- `RUNBOOK.md`
- `.gitignore`
- `openweb/.gitignore`
- `openweb/.npmrc`
- `openweb/AGENTS.md`
- `openweb/CLAUDE.md`
- `openweb/GEMINI.md`
- `openweb/LICENSE`
- `openweb/README.md`
- `openweb/biome.json`
- `openweb/install-skill.sh`
- `openweb/package.json`
- `openweb/pnpm-lock.yaml`
- `openweb/tsconfig.json`
- `openweb/vitest.config.ts`
- `openweb/package-lock.json`
- `reverse-api-engineer/.gitignore`
- `reverse-api-engineer/.python-version`
- `reverse-api-engineer/CHANGELOG.md`
- `reverse-api-engineer/CONTRIBUTING.md`
- `reverse-api-engineer/LICENSE`
- `reverse-api-engineer/README.md`
- `reverse-api-engineer/RELEASING.md`
- `reverse-api-engineer/pyproject.toml`
- `reverse-api-engineer/uv.lock`
- `_specs/elfinanciero/spec.json`
- `_specs/elfinanciero/client.py`
- `_specs/animalpolitico/spec.json`
- `_specs/animalpolitico/client.py`
- `_specs/jornada/spec.json`
- `_specs/jornada/client.py`
- `openweb/.claude-plugin/plugin.json`
- `openweb/doc/PROGRESS.md`
- `openweb/doc/blocked.md`
- `openweb/scripts/adapter-inventory.ts`
- `openweb/scripts/adapter-pattern-baseline.json`
- `openweb/scripts/adapter-pattern-report.ts`
- `openweb/scripts/build-adapters.js`
- `openweb/scripts/build-sites.js`
- `openweb/scripts/clawhub-publish.sh`
- `openweb/scripts/pack-check.js`
- `openweb/src/cli.ts`
- `openweb/doc/dev/adding-sites.md`
- `openweb/doc/dev/development.md`
- `openweb/doc/main/README.md`
- `openweb/doc/main/adapters.md`
- `openweb/doc/main/architecture.md`
- `openweb/doc/main/browser-capture.md`
- `openweb/doc/main/compiler.md`
- `openweb/doc/main/meta-spec.md`
- `openweb/doc/main/runtime.md`
- `openweb/doc/main/security.md`
- `openweb/doc/main/primitives/README.md`
- `openweb/doc/main/primitives/auth.md`
- `openweb/doc/main/primitives/page-plan.md`
- `openweb/doc/main/primitives/signing.md`
- `openweb/skills/openweb/SKILL.md`
- `openweb/skills/openweb/add-site/capture.md`
- `openweb/skills/openweb/add-site/curate-operations.md`
- `openweb/skills/openweb/add-site/curate-runtime.md`
- `openweb/skills/openweb/add-site/curate-schemas.md`
- `openweb/skills/openweb/add-site/document.md`
- `openweb/skills/openweb/add-site/guide.md`
- `openweb/skills/openweb/add-site/probe.md`
- `openweb/skills/openweb/add-site/review.md`
- `openweb/skills/openweb/add-site/verify.md`
- `openweb/skills/openweb/knowledge/adapter-recipes.md`
- `openweb/skills/openweb/knowledge/archetypes.md`
- `openweb/skills/openweb/knowledge/auth-primitives.md`
- `openweb/skills/openweb/knowledge/auth-routing.md`
- `openweb/skills/openweb/knowledge/bot-detection.md`
- `openweb/skills/openweb/knowledge/extraction.md`
- `openweb/skills/openweb/knowledge/graphql.md`
- `openweb/skills/openweb/knowledge/transport-upgrade.md`
- `openweb/skills/openweb/knowledge/ws.md`
- `openweb/skills/openweb/references/cli.md`
- `openweb/skills/openweb/references/troubleshooting.md`
- `openweb/skills/openweb/references/x-openweb.md`
- `openweb/src/capture/bundle.test.ts`
- `openweb/src/capture/bundle.ts`
- `openweb/src/capture/connection.ts`
- `openweb/src/capture/dom-capture.test.ts`
- `openweb/src/capture/dom-capture.ts`
- `openweb/src/capture/har-capture.test.ts`
- `openweb/src/capture/har-capture.ts`
- `openweb/src/capture/session.test.ts`
- `openweb/src/capture/session.ts`
- `openweb/src/capture/state-capture.ts`
- `openweb/src/capture/types.ts`
- `openweb/src/capture/ws-capture.ts`
- `openweb/src/commands/browser.test.ts`
- `openweb/src/commands/browser.ts`
- `openweb/src/commands/capture.ts`
- `openweb/src/commands/compile.test.ts`
- `openweb/src/commands/compile.ts`
- `openweb/src/commands/exec.test.ts`
- `openweb/src/commands/exec.ts`
- `openweb/src/commands/registry.ts`
- `openweb/src/commands/show.ts`
- `openweb/src/commands/sites.ts`
- `openweb/src/commands/test.ts`
- `openweb/src/commands/verify.ts`
- `openweb/src/compiler/generator.test.ts`
- `openweb/src/compiler/recorder.test.ts`
- `openweb/src/compiler/recorder.ts`
- `openweb/src/compiler/types-v2.ts`
- `openweb/src/compiler/types.ts`
- `openweb/src/lib/adapter-helpers.test.ts`
- `openweb/src/lib/adapter-helpers.ts`
- `openweb/src/lib/adapter-params.ts`
- `openweb/src/lib/adapter-patterns.test.ts`
- `openweb/src/lib/asyncapi.ts`
- `openweb/src/lib/config.test.ts`
- `openweb/src/lib/config.ts`
- `openweb/src/lib/cookies.ts`
- `openweb/src/lib/csrf-scope.test.ts`
- `openweb/src/lib/csrf-scope.ts`
- `openweb/src/lib/errors.ts`
- `openweb/src/lib/logger.ts`
- `openweb/src/lib/manifest.ts`
- `openweb/src/lib/openapi.test.ts`
- `openweb/src/lib/param-validator.test.ts`
- `openweb/src/lib/param-validator.ts`
- `openweb/src/lib/permission-derive.test.ts`
- `openweb/src/lib/permission-derive.ts`
- `openweb/src/lib/permissions.test.ts`
- `openweb/src/lib/permissions.ts`
- `openweb/src/lib/response-parser.test.ts`
- `openweb/src/lib/response-parser.ts`
- `openweb/src/lib/site-package.test.ts`
- `openweb/src/lib/site-package.ts`
- `openweb/src/lib/site-resolver.ts`
- `openweb/src/lib/spec-loader.test.ts`
- `openweb/src/lib/spec-loader.ts`
- `openweb/src/lib/ssrf.test.ts`
- `openweb/src/lib/ssrf.ts`
- `openweb/src/lib/template-resolver.test.ts`
- `openweb/src/lib/template-resolver.ts`
- `openweb/src/lib/url-builder.ts`
- `openweb/src/lifecycle/registry.test.ts`
- `openweb/src/lifecycle/registry.ts`
- `openweb/src/lifecycle/shape-diff.test.ts`
- `openweb/src/lifecycle/shape-diff.ts`
- `openweb/src/lifecycle/verify.test.ts`
- `openweb/src/lifecycle/verify.ts`
- `openweb/src/runtime/adapter-executor.test.ts`
- `openweb/src/runtime/adapter-executor.ts`
- `openweb/src/runtime/apollo-refs.test.ts`
- `openweb/src/runtime/apollo-refs.ts`
- `openweb/src/runtime/auth-check.test.ts`
- `openweb/src/runtime/auth-check.ts`
- `openweb/src/runtime/bot-detect.ts`
- `openweb/src/runtime/browser-fetch-executor.test.ts`
- `openweb/src/runtime/browser-fetch-executor.ts`
- `openweb/src/runtime/browser-lifecycle.test.ts`
- `openweb/src/runtime/browser-lifecycle.ts`
- `openweb/src/runtime/cache-manager.test.ts`
- `openweb/src/runtime/cache-manager.ts`
- `openweb/src/runtime/executor-result.ts`
- `openweb/src/runtime/executor.test.ts`
- `openweb/src/runtime/executor.ts`
- `openweb/src/runtime/extraction-executor.test.ts`
- `openweb/src/runtime/extraction-executor.ts`
- `openweb/src/runtime/http-executor.test.ts`
- `openweb/src/runtime/http-executor.ts`
- `openweb/src/runtime/http-retry.test.ts`
- `openweb/src/runtime/http-retry.ts`
- `openweb/src/runtime/navigator.test.ts`
- `openweb/src/runtime/navigator.ts`
- `openweb/src/runtime/node-ssr-executor.test.ts`
- `openweb/src/runtime/node-ssr-executor.ts`
- `openweb/src/runtime/operation-context.test.ts`
- `openweb/src/runtime/operation-context.ts`
- `openweb/src/runtime/page-candidates.ts`
- `openweb/src/runtime/page-plan.test.ts`
- `openweb/src/runtime/page-plan.ts`
- `openweb/src/runtime/page-polyfill.ts`
- `openweb/src/runtime/paginator.test.ts`
- `openweb/src/runtime/paginator.ts`
- `openweb/src/runtime/redirect.test.ts`
- `openweb/src/runtime/redirect.ts`
- `openweb/src/runtime/request-builder.test.ts`
- `openweb/src/runtime/request-builder.ts`
- `openweb/src/runtime/response-unwrap.ts`
- `openweb/src/runtime/session-executor.test.ts`
- `openweb/src/runtime/session-executor.ts`
- `openweb/src/runtime/token-cache.test.ts`
- `openweb/src/runtime/token-cache.ts`
- `openweb/src/runtime/value-path.test.ts`
- `openweb/src/runtime/value-path.ts`
- `openweb/src/runtime/warm-session.test.ts`
- `openweb/src/runtime/warm-session.ts`
- `openweb/src/runtime/ws-cli-executor.ts`
- `openweb/src/runtime/ws-connection.test.ts`
- `openweb/src/runtime/ws-connection.ts`
- `openweb/src/runtime/ws-executor.test.ts`
- `openweb/src/runtime/ws-executor.ts`
- `openweb/src/runtime/ws-pool.ts`
- `openweb/src/runtime/ws-router.test.ts`
- `openweb/src/runtime/ws-router.ts`
- `openweb/src/runtime/ws-runtime.ts`
- `openweb/src/runtime/ws-socket.ts`
- `openweb/src/types/adapter.ts`
- `openweb/src/types/extensions.ts`
- `openweb/src/types/manifest.ts`
- `openweb/src/types/primitive-schemas.ts`
- `openweb/src/types/primitives.ts`
- `openweb/src/types/schema.ts`
- `openweb/src/types/validator.test.ts`
- `openweb/src/types/validator.ts`
- `openweb/src/types/ws-extensions.ts`
- `openweb/src/types/ws-primitives.test.ts`
- `openweb/src/types/ws-primitives.ts`
- `openweb/src/compiler/analyzer/analyze.test.ts`
- `openweb/src/compiler/analyzer/analyze.ts`
- `openweb/src/compiler/analyzer/annotate.test.ts`
- `openweb/src/compiler/analyzer/annotate.ts`
- `openweb/src/compiler/analyzer/auth-candidates.test.ts`
- `openweb/src/compiler/analyzer/auth-candidates.ts`
- `openweb/src/compiler/analyzer/auth-detect.ts`
- `openweb/src/compiler/analyzer/classify.test.ts`
- `openweb/src/compiler/analyzer/classify.ts`
- `openweb/src/compiler/analyzer/cluster.test.ts`
- `openweb/src/compiler/analyzer/cluster.ts`
- `openweb/src/compiler/analyzer/constant-headers.test.ts`
- `openweb/src/compiler/analyzer/constant-headers.ts`
- `openweb/src/compiler/analyzer/csrf-detect.test.ts`
- `openweb/src/compiler/analyzer/csrf-detect.ts`
- `openweb/src/compiler/analyzer/differentiate.test.ts`
- `openweb/src/compiler/analyzer/differentiate.ts`
- `openweb/src/compiler/analyzer/example-select.ts`
- `openweb/src/compiler/analyzer/graphql-cluster.test.ts`
- `openweb/src/compiler/analyzer/graphql-cluster.ts`
- `openweb/src/compiler/analyzer/labeler.test.ts`
- `openweb/src/compiler/analyzer/labeler.ts`
- `openweb/src/compiler/analyzer/path-normalize.test.ts`
- `openweb/src/compiler/analyzer/path-normalize.ts`
- `openweb/src/compiler/analyzer/schema-v2.test.ts`
- `openweb/src/compiler/analyzer/schema-v2.ts`
- `openweb/src/compiler/analyzer/schema.test.ts`
- `openweb/src/compiler/analyzer/schema.ts`
- `openweb/src/compiler/analyzer/shared-constants.ts`
- `openweb/src/compiler/analyzer/signing-detect.ts`
- `openweb/src/compiler/curation/apply-curation.test.ts`
- `openweb/src/compiler/curation/apply-curation.ts`
- `openweb/src/compiler/curation/scrub.test.ts`
- `openweb/src/compiler/curation/scrub.ts`
- `openweb/src/compiler/generator/asyncapi.test.ts`
- `openweb/src/compiler/generator/asyncapi.ts`
- `openweb/src/compiler/generator/generate-v2.test.ts`
- `openweb/src/compiler/generator/generate-v2.ts`
- `openweb/src/compiler/generator/index.ts`
- `openweb/src/compiler/generator/openapi.ts`
- `openweb/src/compiler/generator/package.ts`
- `openweb/src/compiler/ws-analyzer/ws-classify.test.ts`
- `openweb/src/compiler/ws-analyzer/ws-classify.ts`
- `openweb/src/compiler/ws-analyzer/ws-cluster.test.ts`
- `openweb/src/compiler/ws-analyzer/ws-cluster.ts`
- `openweb/src/compiler/ws-analyzer/ws-load.test.ts`
- `openweb/src/compiler/ws-analyzer/ws-load.ts`
- `openweb/src/compiler/ws-analyzer/ws-schema.test.ts`
- `openweb/src/compiler/ws-analyzer/ws-schema.ts`
- `openweb/src/lib/config/blocked-domains.json`
- `openweb/src/lib/config/blocked-paths.json`
- `openweb/src/lib/config/static-extensions.json`
- `openweb/src/lib/config/tracking-cookies.json`
- `openweb/src/runtime/primitives/api-response.ts`
- `openweb/src/runtime/primitives/cookie-session.ts`
- `openweb/src/runtime/primitives/cookie-to-header.ts`
- `openweb/src/runtime/primitives/exchange-chain.ts`
- `openweb/src/runtime/primitives/extraction-resolvers.test.ts`
- `openweb/src/runtime/primitives/html-selector.ts`
- `openweb/src/runtime/primitives/index.ts`
- `openweb/src/runtime/primitives/localstorage-jwt.ts`
- `openweb/src/runtime/primitives/meta-tag.ts`
- `openweb/src/runtime/primitives/page-expression.ts`
- `openweb/src/runtime/primitives/page-global-data.ts`
- `openweb/src/runtime/primitives/page-global.ts`
- `openweb/src/runtime/primitives/primitives.test.ts`
- `openweb/src/runtime/primitives/registry.ts`
- `openweb/src/runtime/primitives/response-capture.test.ts`
- `openweb/src/runtime/primitives/response-capture.ts`
- `openweb/src/runtime/primitives/sapisidhash.ts`
- `openweb/src/runtime/primitives/script-json-parse.test.ts`
- `openweb/src/runtime/primitives/script-json-parse.ts`
- `openweb/src/runtime/primitives/script-json.ts`
- `openweb/src/runtime/primitives/sessionstorage-msal.test.ts`
- `openweb/src/runtime/primitives/sessionstorage-msal.ts`
- `openweb/src/runtime/primitives/ssr-next-data.ts`
- `openweb/src/runtime/primitives/types.ts`
- `openweb/src/runtime/primitives/webpack-module-walk.ts`
- `openweb/src/runtime/primitives/ws-first-message.ts`
- `openweb/src/runtime/primitives/ws-http-handshake.ts`
- `openweb/src/runtime/primitives/ws-primitives.test.ts`
- `openweb/src/runtime/primitives/ws-registry.ts`
- `openweb/src/runtime/primitives/ws-upgrade-header.ts`
- `openweb/src/runtime/primitives/ws-url-token.ts`
- `openweb/src/sites/airbnb/DOC.md`
- `openweb/src/sites/airbnb/PROGRESS.md`
- `openweb/src/sites/airbnb/SKILL.md`
- `openweb/src/sites/airbnb/manifest.json`
- `openweb/src/sites/airbnb/openapi.yaml`
- `openweb/src/sites/amazon/DOC.md`
- `openweb/src/sites/amazon/PROGRESS.md`
- `openweb/src/sites/amazon/SKILL.md`
- `openweb/src/sites/amazon/manifest.json`
- `openweb/src/sites/amazon/openapi.yaml`
- `openweb/src/sites/amazon/pipeline-gaps.md`
- `openweb/src/sites/angellist/DOC.md`
- `openweb/src/sites/angellist/PROGRESS.md`
- `openweb/src/sites/angellist/SKILL.md`
- `openweb/src/sites/angellist/manifest.json`
- `openweb/src/sites/angellist/openapi.yaml`
- `openweb/src/sites/apple-podcasts/DOC.md`
- `openweb/src/sites/apple-podcasts/PROGRESS.md`
- `openweb/src/sites/apple-podcasts/SKILL.md`
- `openweb/src/sites/apple-podcasts/manifest.json`
- `openweb/src/sites/apple-podcasts/openapi.yaml`
- `openweb/src/sites/apple-podcasts/pipeline-gaps.md`
- `openweb/src/sites/arxiv/DOC.md`
- `openweb/src/sites/arxiv/PROGRESS.md`
- `openweb/src/sites/arxiv/SKILL.md`
- `openweb/src/sites/arxiv/manifest.json`
- `openweb/src/sites/arxiv/openapi.yaml`
- `openweb/src/sites/bbc-news/DOC.md`
- `openweb/src/sites/bbc-news/PROGRESS.md`
- `openweb/src/sites/bbc-news/SKILL.md`
- `openweb/src/sites/bbc-news/manifest.json`
- `openweb/src/sites/bbc-news/openapi.yaml`
- `openweb/src/sites/bestbuy/DOC.md`
- `openweb/src/sites/bestbuy/PROGRESS.md`
- `openweb/src/sites/bestbuy/SKILL.md`
- `openweb/src/sites/bestbuy/manifest.json`
- `openweb/src/sites/bestbuy/openapi.yaml`
- `openweb/src/sites/bilibili/DOC.md`
- `openweb/src/sites/bilibili/PROGRESS.md`
- `openweb/src/sites/bilibili/SKILL.md`
- `openweb/src/sites/bilibili/manifest.json`
- `openweb/src/sites/bilibili/openapi.yaml`
- `openweb/src/sites/bloomberg/DOC.md`
- `openweb/src/sites/bloomberg/PROGRESS.md`
- `openweb/src/sites/bloomberg/SKILL.md`
- `openweb/src/sites/bloomberg/manifest.json`
- `openweb/src/sites/bloomberg/openapi.yaml`
- `openweb/src/sites/bloomberg/pipeline-gaps.md`
- `openweb/src/sites/bluesky/DOC.md`
- `openweb/src/sites/bluesky/PROGRESS.md`
- `openweb/src/sites/bluesky/SKILL.md`
- `openweb/src/sites/bluesky/manifest.json`
- `openweb/src/sites/bluesky/openapi.yaml`
- `openweb/src/sites/bluesky/pipeline-gaps.md`
- `openweb/src/sites/booking/DOC.md`
- `openweb/src/sites/booking/PROGRESS.md`
- `openweb/src/sites/booking/SKILL.md`
- `openweb/src/sites/booking/manifest.json`
- `openweb/src/sites/booking/openapi.yaml`
- `openweb/src/sites/booking/pipeline-gaps.md`
- `openweb/src/sites/boss/DOC.md`
- `openweb/src/sites/boss/PROGRESS.md`
- `openweb/src/sites/boss/SKILL.md`
- `openweb/src/sites/boss/manifest.json`
- `openweb/src/sites/boss/openapi.yaml`
- `openweb/src/sites/boss/pipeline-gaps.md`
- `openweb/src/sites/chatgpt/DOC.md`
- `openweb/src/sites/chatgpt/PROGRESS.md`
- `openweb/src/sites/chatgpt/SKILL.md`
- `openweb/src/sites/chatgpt/manifest.json`
- `openweb/src/sites/chatgpt/openapi.yaml`
- `openweb/src/sites/chatgpt/pipeline-gaps.md`
- `openweb/src/sites/cnn/DOC.md`
- `openweb/src/sites/cnn/PROGRESS.md`
- `openweb/src/sites/cnn/SKILL.md`
- `openweb/src/sites/cnn/manifest.json`
- `openweb/src/sites/cnn/openapi.yaml`
- `openweb/src/sites/coingecko/DOC.md`
- `openweb/src/sites/coingecko/PROGRESS.md`
- `openweb/src/sites/coingecko/SKILL.md`
- `openweb/src/sites/coingecko/manifest.json`
- `openweb/src/sites/coingecko/openapi.yaml`
- `openweb/src/sites/coinmarketcap/DOC.md`
- `openweb/src/sites/coinmarketcap/PROGRESS.md`
- `openweb/src/sites/coinmarketcap/SKILL.md`
- `openweb/src/sites/coinmarketcap/manifest.json`
- `openweb/src/sites/coinmarketcap/openapi.yaml`
- `openweb/src/sites/costco/DOC.md`
- `openweb/src/sites/costco/PROGRESS.md`
- `openweb/src/sites/costco/SKILL.md`
- `openweb/src/sites/costco/manifest.json`
- `openweb/src/sites/costco/openapi.yaml`
- `openweb/src/sites/craigslist/DOC.md`
- `openweb/src/sites/craigslist/PROGRESS.md`
- `openweb/src/sites/craigslist/SKILL.md`
- `openweb/src/sites/craigslist/manifest.json`
- `openweb/src/sites/craigslist/openapi.yaml`
- `openweb/src/sites/ctrip/DOC.md`
- `openweb/src/sites/ctrip/PROGRESS.md`
- `openweb/src/sites/ctrip/SKILL.md`
- `openweb/src/sites/ctrip/manifest.json`
- `openweb/src/sites/ctrip/openapi.yaml`
- `openweb/src/sites/discord/DOC.md`
- `openweb/src/sites/discord/PROGRESS.md`
- `openweb/src/sites/discord/SKILL.md`
- `openweb/src/sites/discord/manifest.json`
- `openweb/src/sites/discord/openapi.yaml`
- `openweb/src/sites/docker-hub/DOC.md`
- `openweb/src/sites/docker-hub/PROGRESS.md`
- `openweb/src/sites/docker-hub/SKILL.md`
- `openweb/src/sites/docker-hub/manifest.json`
- `openweb/src/sites/docker-hub/openapi.yaml`
- `openweb/src/sites/doordash/DOC.md`
- `openweb/src/sites/doordash/PROGRESS.md`
- `openweb/src/sites/doordash/SKILL.md`
- `openweb/src/sites/doordash/manifest.json`
- `openweb/src/sites/doordash/openapi.yaml`
- `openweb/src/sites/douban/DOC.md`
- `openweb/src/sites/douban/PROGRESS.md`
- `openweb/src/sites/douban/SKILL.md`
- `openweb/src/sites/douban/manifest.json`
- `openweb/src/sites/douban/openapi.yaml`
- `openweb/src/sites/ebay/DOC.md`
- `openweb/src/sites/ebay/PROGRESS.md`
- `openweb/src/sites/ebay/SKILL.md`
- `openweb/src/sites/ebay/manifest.json`
- `openweb/src/sites/ebay/openapi.yaml`
- `openweb/src/sites/espn/DOC.md`
- `openweb/src/sites/espn/PROGRESS.md`
- `openweb/src/sites/espn/SKILL.md`
- `openweb/src/sites/espn/manifest.json`
- `openweb/src/sites/espn/openapi.yaml`
- `openweb/src/sites/espn/pipeline-gaps.md`
- `openweb/src/sites/etsy/DOC.md`
- `openweb/src/sites/etsy/PROGRESS.md`
- `openweb/src/sites/etsy/SKILL.md`
- `openweb/src/sites/etsy/manifest.json`
- `openweb/src/sites/etsy/openapi.yaml`
- `openweb/src/sites/expedia/DOC.md`
- `openweb/src/sites/expedia/PROGRESS.md`
- `openweb/src/sites/expedia/SKILL.md`
- `openweb/src/sites/expedia/manifest.json`
- `openweb/src/sites/expedia/openapi.yaml`
- `openweb/src/sites/expedia/pipeline-gaps.md`
- `openweb/src/sites/fidelity/DOC.md`
- `openweb/src/sites/fidelity/PROGRESS.md`
- `openweb/src/sites/fidelity/SKILL.md`
- `openweb/src/sites/fidelity/manifest.json`
- `openweb/src/sites/fidelity/openapi.yaml`
- `openweb/src/sites/fidelity/pipeline-gaps.md`
- `openweb/src/sites/github/DOC.md`
- `openweb/src/sites/github/PROGRESS.md`
- `openweb/src/sites/github/SKILL.md`
- `openweb/src/sites/github/manifest.json`
- `openweb/src/sites/github/openapi.yaml`
- `openweb/src/sites/gitlab/DOC.md`
- `openweb/src/sites/gitlab/PROGRESS.md`
- `openweb/src/sites/gitlab/SKILL.md`
- `openweb/src/sites/gitlab/manifest.json`
- `openweb/src/sites/gitlab/openapi.yaml`
- `openweb/src/sites/glassdoor/DOC.md`
- `openweb/src/sites/glassdoor/PROGRESS.md`
- `openweb/src/sites/glassdoor/SKILL.md`
- `openweb/src/sites/glassdoor/manifest.json`
- `openweb/src/sites/glassdoor/openapi.yaml`
- `openweb/src/sites/goodreads/DOC.md`
- `openweb/src/sites/goodreads/PROGRESS.md`
- `openweb/src/sites/goodreads/SKILL.md`
- `openweb/src/sites/goodreads/manifest.json`
- `openweb/src/sites/goodreads/openapi.yaml`
- `openweb/src/sites/goodrx/DOC.md`
- `openweb/src/sites/goodrx/PROGRESS.md`
- `openweb/src/sites/goodrx/SKILL.md`
- `openweb/src/sites/goodrx/manifest.json`
- `openweb/src/sites/goodrx/openapi.yaml`
- `openweb/src/sites/goodrx/pipeline-gaps.md`
- `openweb/src/sites/google-flights/DOC.md`
- `openweb/src/sites/google-flights/PROGRESS.md`
- `openweb/src/sites/google-flights/SKILL.md`
- `openweb/src/sites/google-flights/manifest.json`
- `openweb/src/sites/google-flights/openapi.yaml`
- `openweb/src/sites/google-flights/pipeline-gaps.md`
- `openweb/src/sites/google-maps/DOC.md`
- `openweb/src/sites/google-maps/PROGRESS.md`
- `openweb/src/sites/google-maps/SKILL.md`
- `openweb/src/sites/google-maps/manifest.json`
- `openweb/src/sites/google-maps/openapi.yaml`
- `openweb/src/sites/google-maps/pipeline-gaps.md`
- `openweb/src/sites/google-scholar/DOC.md`
- `openweb/src/sites/google-scholar/PROGRESS.md`
- `openweb/src/sites/google-scholar/SKILL.md`
- `openweb/src/sites/google-scholar/manifest.json`
- `openweb/src/sites/google-scholar/openapi.yaml`
- `openweb/src/sites/google-search/DOC.md`
- `openweb/src/sites/google-search/PROGRESS.md`
- `openweb/src/sites/google-search/SKILL.md`
- `openweb/src/sites/google-search/manifest.json`
- `openweb/src/sites/google-search/openapi.yaml`
- `openweb/src/sites/grubhub/DOC.md`
- `openweb/src/sites/grubhub/PROGRESS.md`
- `openweb/src/sites/grubhub/SKILL.md`
- `openweb/src/sites/grubhub/manifest.json`
- `openweb/src/sites/grubhub/openapi.yaml`
- `openweb/src/sites/guardian/DOC.md`
- `openweb/src/sites/guardian/PROGRESS.md`
- `openweb/src/sites/guardian/SKILL.md`
- `openweb/src/sites/guardian/manifest.json`
- `openweb/src/sites/guardian/openapi.yaml`
- `openweb/src/sites/hackernews/DOC.md`
- `openweb/src/sites/hackernews/PROGRESS.md`
- `openweb/src/sites/hackernews/SKILL.md`
- `openweb/src/sites/hackernews/manifest.json`
- `openweb/src/sites/hackernews/openapi.yaml`
- `openweb/src/sites/homedepot/DOC.md`
- `openweb/src/sites/homedepot/PROGRESS.md`
- `openweb/src/sites/homedepot/SKILL.md`
- `openweb/src/sites/homedepot/manifest.json`
- `openweb/src/sites/homedepot/openapi.yaml`
- `openweb/src/sites/huggingface/DOC.md`
- `openweb/src/sites/huggingface/PROGRESS.md`
- `openweb/src/sites/huggingface/SKILL.md`
- `openweb/src/sites/huggingface/manifest.json`
- `openweb/src/sites/huggingface/openapi.yaml`
- `openweb/src/sites/imdb/DOC.md`
- `openweb/src/sites/imdb/PROGRESS.md`
- `openweb/src/sites/imdb/SKILL.md`
- `openweb/src/sites/imdb/manifest.json`
- `openweb/src/sites/imdb/openapi.yaml`
- `openweb/src/sites/indeed/DOC.md`
- `openweb/src/sites/indeed/PROGRESS.md`
- `openweb/src/sites/indeed/SKILL.md`
- `openweb/src/sites/indeed/manifest.json`
- `openweb/src/sites/indeed/openapi.yaml`
- `openweb/src/sites/indeed/pipeline-gaps.md`
- `openweb/src/sites/instacart/DOC.md`
- `openweb/src/sites/instacart/PROGRESS.md`
- `openweb/src/sites/instacart/SKILL.md`
- `openweb/src/sites/instacart/manifest.json`
- `openweb/src/sites/instacart/openapi.yaml`
- `openweb/src/sites/instagram/DOC.md`
- `openweb/src/sites/instagram/PROGRESS.md`
- `openweb/src/sites/instagram/SKILL.md`
- `openweb/src/sites/instagram/manifest.json`
- `openweb/src/sites/instagram/openapi.yaml`
- `openweb/src/sites/instagram/pipeline-gaps.md`
- `openweb/src/sites/jd/DOC.md`
- `openweb/src/sites/jd/PROGRESS.md`
- `openweb/src/sites/jd/SKILL.md`
- `openweb/src/sites/jd/manifest.json`
- `openweb/src/sites/jd/openapi.yaml`
- `openweb/src/sites/jd/pipeline-gaps.md`
- `openweb/src/sites/kayak/DOC.md`
- `openweb/src/sites/kayak/PROGRESS.md`
- `openweb/src/sites/kayak/SKILL.md`
- `openweb/src/sites/kayak/manifest.json`
- `openweb/src/sites/kayak/openapi.yaml`
- `openweb/src/sites/leetcode/DOC.md`
- `openweb/src/sites/leetcode/PROGRESS.md`
- `openweb/src/sites/leetcode/SKILL.md`
- `openweb/src/sites/leetcode/manifest.json`
- `openweb/src/sites/leetcode/openapi.yaml`
- `openweb/src/sites/linkedin/DOC.md`
- `openweb/src/sites/linkedin/PROGRESS.md`
- `openweb/src/sites/linkedin/SKILL.md`
- `openweb/src/sites/linkedin/manifest.json`
- `openweb/src/sites/linkedin/openapi.yaml`
- `openweb/src/sites/linkedin/pipeline-gaps.md`
- `openweb/src/sites/medium/DOC.md`
- `openweb/src/sites/medium/PROGRESS.md`
- `openweb/src/sites/medium/SKILL.md`
- `openweb/src/sites/medium/manifest.json`
- `openweb/src/sites/medium/openapi.yaml`
- `openweb/src/sites/medium/pipeline-gaps.md`
- `openweb/src/sites/notion/DOC.md`
- `openweb/src/sites/notion/PROGRESS.md`
- `openweb/src/sites/notion/SKILL.md`
- `openweb/src/sites/notion/manifest.json`
- `openweb/src/sites/notion/openapi.yaml`
- `openweb/src/sites/npm/DOC.md`
- `openweb/src/sites/npm/PROGRESS.md`
- `openweb/src/sites/npm/SKILL.md`
- `openweb/src/sites/npm/manifest.json`
- `openweb/src/sites/npm/openapi.yaml`
- `openweb/src/sites/npr/DOC.md`
- `openweb/src/sites/npr/PROGRESS.md`
- `openweb/src/sites/npr/SKILL.md`
- `openweb/src/sites/npr/manifest.json`
- `openweb/src/sites/npr/openapi.yaml`
- `openweb/src/sites/opentable/DOC.md`
- `openweb/src/sites/opentable/PROGRESS.md`
- `openweb/src/sites/opentable/SKILL.md`
- `openweb/src/sites/opentable/manifest.json`
- `openweb/src/sites/opentable/openapi.yaml`
- `openweb/src/sites/pinterest/DOC.md`
- `openweb/src/sites/pinterest/PROGRESS.md`
- `openweb/src/sites/pinterest/SKILL.md`
- `openweb/src/sites/pinterest/manifest.json`
- `openweb/src/sites/pinterest/openapi.yaml`
- `openweb/src/sites/pinterest/pipeline-gaps.md`
- `openweb/src/sites/producthunt/DOC.md`
- `openweb/src/sites/producthunt/PROGRESS.md`
- `openweb/src/sites/producthunt/SKILL.md`
- `openweb/src/sites/producthunt/manifest.json`
- `openweb/src/sites/producthunt/openapi.yaml`
- `openweb/src/sites/pypi/DOC.md`
- `openweb/src/sites/pypi/PROGRESS.md`
- `openweb/src/sites/pypi/SKILL.md`
- `openweb/src/sites/pypi/manifest.json`
- `openweb/src/sites/pypi/openapi.yaml`
- `openweb/src/sites/quora/DOC.md`
- `openweb/src/sites/quora/PROGRESS.md`
- `openweb/src/sites/quora/SKILL.md`
- `openweb/src/sites/quora/manifest.json`
- `openweb/src/sites/quora/openapi.yaml`
- `openweb/src/sites/reddit/DOC.md`
- `openweb/src/sites/reddit/PROGRESS.md`
- `openweb/src/sites/reddit/SKILL.md`
- `openweb/src/sites/reddit/manifest.json`
- `openweb/src/sites/reddit/openapi.yaml`
- `openweb/src/sites/redfin/DOC.md`
- `openweb/src/sites/redfin/PROGRESS.md`
- `openweb/src/sites/redfin/SKILL.md`
- `openweb/src/sites/redfin/manifest.json`
- `openweb/src/sites/redfin/openapi.yaml`
- `openweb/src/sites/redfin/pipeline-gaps.md`
- `openweb/src/sites/reuters/DOC.md`
- `openweb/src/sites/reuters/PROGRESS.md`
- `openweb/src/sites/reuters/SKILL.md`
- `openweb/src/sites/reuters/manifest.json`
- `openweb/src/sites/reuters/openapi.yaml`
- `openweb/src/sites/reuters/pipeline-gaps.md`
- `openweb/src/sites/robinhood/DOC.md`
- `openweb/src/sites/robinhood/PROGRESS.md`
- `openweb/src/sites/robinhood/SKILL.md`
- `openweb/src/sites/robinhood/manifest.json`
- `openweb/src/sites/robinhood/openapi.yaml`
- `openweb/src/sites/rotten-tomatoes/DOC.md`
- `openweb/src/sites/rotten-tomatoes/PROGRESS.md`
- `openweb/src/sites/rotten-tomatoes/SKILL.md`
- `openweb/src/sites/rotten-tomatoes/manifest.json`
- `openweb/src/sites/rotten-tomatoes/openapi.yaml`
- `openweb/src/sites/seeking-alpha/DOC.md`
- `openweb/src/sites/seeking-alpha/PROGRESS.md`
- `openweb/src/sites/seeking-alpha/SKILL.md`
- `openweb/src/sites/seeking-alpha/manifest.json`
- `openweb/src/sites/seeking-alpha/openapi.yaml`
- `openweb/src/sites/soundcloud/DOC.md`
- `openweb/src/sites/soundcloud/PROGRESS.md`
- `openweb/src/sites/soundcloud/SKILL.md`
- `openweb/src/sites/soundcloud/manifest.json`
- `openweb/src/sites/soundcloud/openapi.yaml`
- `openweb/src/sites/spotify/DOC.md`
- `openweb/src/sites/spotify/PROGRESS.md`
- `openweb/src/sites/spotify/SKILL.md`
- `openweb/src/sites/spotify/manifest.json`
- `openweb/src/sites/spotify/openapi.yaml`
- `openweb/src/sites/stackoverflow/DOC.md`
- `openweb/src/sites/stackoverflow/PROGRESS.md`
- `openweb/src/sites/stackoverflow/SKILL.md`
- `openweb/src/sites/stackoverflow/manifest.json`
- `openweb/src/sites/stackoverflow/openapi.yaml`
- `openweb/src/sites/starbucks/DOC.md`
- `openweb/src/sites/starbucks/PROGRESS.md`
- `openweb/src/sites/starbucks/SKILL.md`
- `openweb/src/sites/starbucks/manifest.json`
- `openweb/src/sites/starbucks/openapi.yaml`
- `openweb/src/sites/steam/DOC.md`
- `openweb/src/sites/steam/PROGRESS.md`
- `openweb/src/sites/steam/SKILL.md`
- `openweb/src/sites/steam/manifest.json`
- `openweb/src/sites/steam/openapi.yaml`
- `openweb/src/sites/substack/DOC.md`
- `openweb/src/sites/substack/PROGRESS.md`
- `openweb/src/sites/substack/SKILL.md`
- `openweb/src/sites/substack/manifest.json`
- `openweb/src/sites/substack/openapi.yaml`
- `openweb/src/sites/substack/pipeline-gaps.md`
- `openweb/src/sites/target/DOC.md`
- `openweb/src/sites/target/PROGRESS.md`
- `openweb/src/sites/target/SKILL.md`
- `openweb/src/sites/target/manifest.json`
- `openweb/src/sites/target/openapi.yaml`
- `openweb/src/sites/techcrunch/DOC.md`
- `openweb/src/sites/techcrunch/PROGRESS.md`
- `openweb/src/sites/techcrunch/SKILL.md`
- `openweb/src/sites/techcrunch/manifest.json`
- `openweb/src/sites/techcrunch/openapi.yaml`
- `openweb/src/sites/telegram/DOC.md`
- `openweb/src/sites/telegram/PROGRESS.md`
- `openweb/src/sites/telegram/SKILL.md`
- `openweb/src/sites/telegram/manifest.json`
- `openweb/src/sites/telegram/openapi.yaml`
- `openweb/src/sites/telegram/pipeline-gaps.md`
- `openweb/src/sites/tiktok/DOC.md`
- `openweb/src/sites/tiktok/PROGRESS.md`
- `openweb/src/sites/tiktok/SKILL.md`
- `openweb/src/sites/tiktok/manifest.json`
- `openweb/src/sites/tiktok/openapi.yaml`
- `openweb/src/sites/todoist/DOC.md`
- `openweb/src/sites/todoist/PROGRESS.md`
- `openweb/src/sites/todoist/SKILL.md`
- `openweb/src/sites/todoist/manifest.json`
- `openweb/src/sites/todoist/openapi.yaml`
- `openweb/src/sites/trello/DOC.md`
- `openweb/src/sites/trello/PROGRESS.md`
- `openweb/src/sites/trello/SKILL.md`
- `openweb/src/sites/trello/manifest.json`
- `openweb/src/sites/trello/openapi.yaml`
- `openweb/src/sites/tripadvisor/DOC.md`
- `openweb/src/sites/tripadvisor/PROGRESS.md`
- `openweb/src/sites/tripadvisor/SKILL.md`
- `openweb/src/sites/tripadvisor/manifest.json`
- `openweb/src/sites/tripadvisor/openapi.yaml`
- `openweb/src/sites/twitch/DOC.md`
- `openweb/src/sites/twitch/PROGRESS.md`
- `openweb/src/sites/twitch/SKILL.md`
- `openweb/src/sites/twitch/manifest.json`
- `openweb/src/sites/twitch/openapi.yaml`
- `openweb/src/sites/twitch/pipeline-gaps.md`
- `openweb/src/sites/uber/DOC.md`
- `openweb/src/sites/uber/PROGRESS.md`
- `openweb/src/sites/uber/SKILL.md`
- `openweb/src/sites/uber/manifest.json`
- `openweb/src/sites/uber/openapi.yaml`
- `openweb/src/sites/ubereats/DOC.md`
- `openweb/src/sites/ubereats/PROGRESS.md`
- `openweb/src/sites/ubereats/SKILL.md`
- `openweb/src/sites/ubereats/manifest.json`
- `openweb/src/sites/ubereats/openapi.yaml`
- `openweb/src/sites/walmart/DOC.md`
- `openweb/src/sites/walmart/PROGRESS.md`
- `openweb/src/sites/walmart/SKILL.md`
- `openweb/src/sites/walmart/manifest.json`
- `openweb/src/sites/walmart/openapi.yaml`
- `openweb/src/sites/weibo/DOC.md`
- `openweb/src/sites/weibo/PROGRESS.md`
- `openweb/src/sites/weibo/SKILL.md`
- `openweb/src/sites/weibo/manifest.json`
- `openweb/src/sites/weibo/openapi.yaml`
- `openweb/src/sites/weibo/pipeline-gaps.md`
- `openweb/src/sites/whatsapp/DOC.md`
- `openweb/src/sites/whatsapp/PROGRESS.md`
- `openweb/src/sites/whatsapp/SKILL.md`
- `openweb/src/sites/whatsapp/manifest.json`
- `openweb/src/sites/whatsapp/openapi.yaml`
- `openweb/src/sites/whatsapp/pipeline-gaps.md`
- `openweb/src/sites/wikipedia/DOC.md`
- `openweb/src/sites/wikipedia/PROGRESS.md`
- `openweb/src/sites/wikipedia/SKILL.md`
- `openweb/src/sites/wikipedia/manifest.json`
- `openweb/src/sites/wikipedia/openapi.yaml`
- `openweb/src/sites/x/DOC.md`
- `openweb/src/sites/x/PROGRESS.md`
- `openweb/src/sites/x/SKILL.md`
- `openweb/src/sites/x/manifest.json`
- `openweb/src/sites/x/openapi.yaml`
- `openweb/src/sites/xiaohongshu/DOC.md`
- `openweb/src/sites/xiaohongshu/PROGRESS.md`
- `openweb/src/sites/xiaohongshu/SKILL.md`
- `openweb/src/sites/xiaohongshu/manifest.json`
- `openweb/src/sites/xiaohongshu/openapi.yaml`
- `openweb/src/sites/xueqiu/DOC.md`
- `openweb/src/sites/xueqiu/PROGRESS.md`
- `openweb/src/sites/xueqiu/SKILL.md`
- `openweb/src/sites/xueqiu/manifest.json`
- `openweb/src/sites/xueqiu/openapi.yaml`
- `openweb/src/sites/xueqiu/pipeline-gaps.md`
- `openweb/src/sites/yahoo-finance/DOC.md`
- `openweb/src/sites/yahoo-finance/PROGRESS.md`
- `openweb/src/sites/yahoo-finance/SKILL.md`
- `openweb/src/sites/yahoo-finance/manifest.json`
- `openweb/src/sites/yahoo-finance/openapi.yaml`
- `openweb/src/sites/yelp/DOC.md`
- `openweb/src/sites/yelp/PROGRESS.md`
- `openweb/src/sites/yelp/SKILL.md`
- `openweb/src/sites/yelp/manifest.json`
- `openweb/src/sites/yelp/openapi.yaml`
- `openweb/src/sites/youtube-music/DOC.md`
- `openweb/src/sites/youtube-music/PROGRESS.md`
- `openweb/src/sites/youtube-music/SKILL.md`
- `openweb/src/sites/youtube-music/manifest.json`
- `openweb/src/sites/youtube-music/openapi.yaml`
- `openweb/src/sites/youtube-music/pipeline-gaps.md`
- `openweb/src/sites/youtube/DOC.md`
- `openweb/src/sites/youtube/PROGRESS.md`
- `openweb/src/sites/youtube/SKILL.md`
- `openweb/src/sites/youtube/manifest.json`
- `openweb/src/sites/youtube/openapi.yaml`
- `openweb/src/sites/zhihu/DOC.md`
- `openweb/src/sites/zhihu/PROGRESS.md`
- `openweb/src/sites/zhihu/SKILL.md`
- `openweb/src/sites/zhihu/manifest.json`
- `openweb/src/sites/zhihu/openapi.yaml`
- `openweb/src/sites/zillow/DOC.md`
- `openweb/src/sites/zillow/PROGRESS.md`
- `openweb/src/sites/zillow/SKILL.md`
- `openweb/src/sites/zillow/manifest.json`
- `openweb/src/sites/zillow/openapi.yaml`
- `openweb/src/sites/airbnb/adapters/airbnb.ts`
- `openweb/src/sites/airbnb/adapters/airbnb.js`
- `openweb/src/sites/airbnb/examples/getHostProfile.example.json`
- `openweb/src/sites/airbnb/examples/getListingAvailability.example.json`
- `openweb/src/sites/airbnb/examples/getListingDetail.example.json`
- `openweb/src/sites/airbnb/examples/getListingReviews.example.json`
- `openweb/src/sites/airbnb/examples/searchListings.example.json`
- `openweb/src/sites/amazon/adapters/amazon.ts`
- `openweb/src/sites/amazon/adapters/amazon.js`
- `openweb/src/sites/amazon/examples/addToCart.example.json`
- `openweb/src/sites/amazon/examples/getBestSellers.example.json`
- `openweb/src/sites/amazon/examples/getCart.example.json`
- `openweb/src/sites/amazon/examples/getProductDetail.example.json`
- `openweb/src/sites/amazon/examples/getProductReviews.example.json`
- `openweb/src/sites/amazon/examples/removeFromCart.example.json`
- `openweb/src/sites/amazon/examples/searchDeals.example.json`
- `openweb/src/sites/amazon/examples/searchProducts.example.json`
- `openweb/src/sites/angellist/adapters/angellist.ts`
- `openweb/src/sites/angellist/adapters/angellist.js`
- `openweb/src/sites/angellist/examples/getInvite.example.json`
- `openweb/src/sites/angellist/examples/getMessage.example.json`
- `openweb/src/sites/angellist/examples/getPost.example.json`
- `openweb/src/sites/angellist/examples/listInvites.example.json`
- `openweb/src/sites/angellist/examples/listMessages.example.json`
- `openweb/src/sites/angellist/examples/listPosts.example.json`
- `openweb/src/sites/apple-podcasts/examples/getPodcast.example.json`
- `openweb/src/sites/apple-podcasts/examples/getSearchSuggestions.example.json`
- `openweb/src/sites/apple-podcasts/examples/getTopCharts.example.json`
- `openweb/src/sites/apple-podcasts/examples/searchPodcasts.example.json`
- `openweb/src/sites/arxiv/adapters/arxiv.ts`
- `openweb/src/sites/arxiv/adapters/arxiv.js`
- `openweb/src/sites/arxiv/examples/getAbstract.example.json`
- `openweb/src/sites/arxiv/examples/getPaper.example.json`
- `openweb/src/sites/arxiv/examples/searchPapers.example.json`
- `openweb/src/sites/bbc-news/examples/getArticle.example.json`
- `openweb/src/sites/bbc-news/examples/getHeadlines.example.json`
- `openweb/src/sites/bbc-news/examples/getTopicFeed.example.json`
- `openweb/src/sites/bbc-news/examples/searchArticles.example.json`
- `openweb/src/sites/bestbuy/adapters/bestbuy-read.ts`
- `openweb/src/sites/bestbuy/adapters/bestbuy-read.js`
- `openweb/src/sites/bestbuy/examples/addToCart.example.json`
- `openweb/src/sites/bestbuy/examples/getProductDetails.example.json`
- `openweb/src/sites/bestbuy/examples/getProductPricing.example.json`
- `openweb/src/sites/bestbuy/examples/removeFromCart.example.json`
- `openweb/src/sites/bestbuy/examples/searchProducts.example.json`
- `openweb/src/sites/bilibili/adapters/bilibili-web.ts`
- `openweb/src/sites/bilibili/adapters/bilibili-web.js`
- `openweb/src/sites/bilibili/examples/addToFavorites.example.json`
- `openweb/src/sites/bilibili/examples/followUploader.example.json`
- `openweb/src/sites/bilibili/examples/getDanmaku.example.json`
- `openweb/src/sites/bilibili/examples/getPopularVideos.example.json`
- `openweb/src/sites/bilibili/examples/getRecommendedFeed.example.json`
- `openweb/src/sites/bilibili/examples/getUserProfile.example.json`
- `openweb/src/sites/bilibili/examples/getVideoComments.example.json`
- `openweb/src/sites/bilibili/examples/getVideoDetail.example.json`
- `openweb/src/sites/bilibili/examples/likeVideo.example.json`
- `openweb/src/sites/bilibili/examples/listFavoriteFolders.example.json`
- `openweb/src/sites/bilibili/examples/removeFromFavorites.example.json`
- `openweb/src/sites/bilibili/examples/searchUserVideos.example.json`
- `openweb/src/sites/bilibili/examples/searchVideos.example.json`
- `openweb/src/sites/bilibili/examples/unfollowUploader.example.json`
- `openweb/src/sites/bilibili/examples/unlikeVideo.example.json`
- `openweb/src/sites/bloomberg/adapters/bloomberg.ts`
- `openweb/src/sites/bloomberg/adapters/bloomberg.js`
- `openweb/src/sites/bloomberg/examples/getCompanyProfile.example.json`
- `openweb/src/sites/bloomberg/examples/getLatestNews.example.json`
- `openweb/src/sites/bloomberg/examples/getMarketOverview.example.json`
- `openweb/src/sites/bloomberg/examples/getNewsHeadlines.example.json`
- `openweb/src/sites/bloomberg/examples/getStockChart.example.json`
- `openweb/src/sites/bloomberg/examples/getTickerBar.example.json`
- `openweb/src/sites/bloomberg/examples/searchBloomberg.example.json`
- `openweb/src/sites/bluesky/adapters/bluesky-pds.ts`
- `openweb/src/sites/bluesky/adapters/bluesky-public.ts`
- `openweb/src/sites/bluesky/adapters/bluesky-pds.js`
- `openweb/src/sites/bluesky/adapters/bluesky-public.js`
- `openweb/src/sites/bluesky/examples/blockUser.example.json`
- `openweb/src/sites/bluesky/examples/createPost.example.json`
- `openweb/src/sites/bluesky/examples/deletePost.example.json`
- `openweb/src/sites/bluesky/examples/follow.example.json`
- `openweb/src/sites/bluesky/examples/getAuthorFeed.example.json`
- `openweb/src/sites/bluesky/examples/getFeed.example.json`
- `openweb/src/sites/bluesky/examples/getFollowers.example.json`
- `openweb/src/sites/bluesky/examples/getFollows.example.json`
- `openweb/src/sites/bluesky/examples/getNotifications.example.json`
- `openweb/src/sites/bluesky/examples/getPostThread.example.json`
- `openweb/src/sites/bluesky/examples/getPosts.example.json`
- `openweb/src/sites/bluesky/examples/getProfile.example.json`
- `openweb/src/sites/bluesky/examples/likePost.example.json`
- `openweb/src/sites/bluesky/examples/muteUser.example.json`
- `openweb/src/sites/bluesky/examples/repost.example.json`
- `openweb/src/sites/bluesky/examples/searchActors.example.json`
- `openweb/src/sites/bluesky/examples/searchPosts.example.json`
- `openweb/src/sites/bluesky/examples/unblockUser.example.json`
- `openweb/src/sites/bluesky/examples/unfollow.example.json`
- `openweb/src/sites/bluesky/examples/unlikePost.example.json`
- `openweb/src/sites/bluesky/examples/unmuteUser.example.json`
- `openweb/src/sites/bluesky/examples/unrepost.example.json`
- `openweb/src/sites/booking/adapters/booking-web.ts`
- `openweb/src/sites/booking/adapters/booking.ts`
- `openweb/src/sites/booking/adapters/booking-web.js`
- `openweb/src/sites/booking/adapters/booking.js`
- `openweb/src/sites/booking/examples/getHotelDetail.example.json`
- `openweb/src/sites/booking/examples/getHotelPrices.example.json`
- `openweb/src/sites/booking/examples/getHotelReviews.example.json`
- `openweb/src/sites/booking/examples/searchFlights.example.json`
- `openweb/src/sites/booking/examples/searchHotels.example.json`
- `openweb/src/sites/boss/adapters/boss.ts`
- `openweb/src/sites/boss/adapters/boss.js`
- `openweb/src/sites/boss/examples/getCities.example.json`
- `openweb/src/sites/boss/examples/getCompanyProfile.example.json`
- `openweb/src/sites/boss/examples/getFilterConditions.example.json`
- `openweb/src/sites/boss/examples/getIndustries.example.json`
- `openweb/src/sites/boss/examples/getJobDetail.example.json`
- `openweb/src/sites/boss/examples/getSalary.example.json`
- `openweb/src/sites/boss/examples/searchJobs.example.json`
- `openweb/src/sites/chatgpt/adapters/chatgpt-api.ts`
- `openweb/src/sites/chatgpt/adapters/chatgpt-web.ts`
- `openweb/src/sites/chatgpt/adapters/chatgpt-api.js`
- `openweb/src/sites/chatgpt/adapters/chatgpt-web.js`
- `openweb/src/sites/chatgpt/examples/getConversation.example.json`
- `openweb/src/sites/chatgpt/examples/getModels.example.json`
- `openweb/src/sites/chatgpt/examples/getProfile.example.json`
- `openweb/src/sites/chatgpt/examples/listConversations.example.json`
- `openweb/src/sites/chatgpt/examples/searchConversations.example.json`
- `openweb/src/sites/chatgpt/examples/sendMessage.example.json`
- `openweb/src/sites/cnn/adapters/cnn.ts`
- `openweb/src/sites/cnn/adapters/cnn.js`
- `openweb/src/sites/cnn/examples/getArticle.example.json`
- `openweb/src/sites/cnn/examples/getHeadlines.example.json`
- `openweb/src/sites/cnn/examples/searchArticles.example.json`
- `openweb/src/sites/coingecko/adapters/coingecko.ts`
- `openweb/src/sites/coingecko/adapters/coingecko.js`
- `openweb/src/sites/coingecko/examples/getCoinDetail.example.json`
- `openweb/src/sites/coingecko/examples/getMarketData.example.json`
- `openweb/src/sites/coingecko/examples/getPrice.example.json`
- `openweb/src/sites/coingecko/examples/getTrending.example.json`
- `openweb/src/sites/coingecko/examples/searchCoins.example.json`
- `openweb/src/sites/coinmarketcap/adapters/coinmarketcap.ts`
- `openweb/src/sites/coinmarketcap/adapters/coinmarketcap.js`
- `openweb/src/sites/coinmarketcap/examples/getListings.example.json`
- `openweb/src/sites/coinmarketcap/examples/getQuote.example.json`
- `openweb/src/sites/coinmarketcap/examples/getTrending.example.json`
- `openweb/src/sites/costco/adapters/costco-api.ts`
- `openweb/src/sites/costco/adapters/costco-api.js`
- `openweb/src/sites/costco/examples/addToCart.example.json`
- `openweb/src/sites/costco/examples/browseCategory.example.json`
- `openweb/src/sites/costco/examples/checkWarehouseStock.example.json`
- `openweb/src/sites/costco/examples/compareProducts.example.json`
- `openweb/src/sites/costco/examples/findWarehouses.example.json`
- `openweb/src/sites/costco/examples/getDeliveryOptions.example.json`
- `openweb/src/sites/costco/examples/getMultipleProducts.example.json`
- `openweb/src/sites/costco/examples/getProductDetail.example.json`
- `openweb/src/sites/costco/examples/getProductReviews.example.json`
- `openweb/src/sites/costco/examples/getWarehouseDetails.example.json`
- `openweb/src/sites/costco/examples/removeFromCart.example.json`
- `openweb/src/sites/costco/examples/searchProducts.example.json`
- `openweb/src/sites/costco/examples/searchSuggestions.example.json`
- `openweb/src/sites/costco/examples/updateCartQuantity.example.json`
- `openweb/src/sites/craigslist/adapters/craigslist-dom.ts`
- `openweb/src/sites/craigslist/adapters/craigslist.ts`
- `openweb/src/sites/craigslist/adapters/craigslist-dom.js`
- `openweb/src/sites/craigslist/adapters/craigslist.js`
- `openweb/src/sites/craigslist/examples/getCategories.example.json`
- `openweb/src/sites/craigslist/examples/getListing.example.json`
- `openweb/src/sites/craigslist/examples/searchListings.example.json`
- `openweb/src/sites/ctrip/adapters/ctrip.ts`
- `openweb/src/sites/ctrip/adapters/ctrip.js`
- `openweb/src/sites/ctrip/examples/getDestinationInfo.example.json`
- `openweb/src/sites/ctrip/examples/getFlightComfort.example.json`
- `openweb/src/sites/ctrip/examples/getGeneralInfo.example.json`
- `openweb/src/sites/ctrip/examples/getHotDestinations.example.json`
- `openweb/src/sites/ctrip/examples/getTrainStations.example.json`
- `openweb/src/sites/ctrip/examples/searchAttractions.example.json`
- `openweb/src/sites/ctrip/examples/searchFlights.example.json`
- `openweb/src/sites/ctrip/examples/searchPOI.example.json`
- `openweb/src/sites/ctrip/examples/searchTrains.example.json`
- `openweb/src/sites/discord/examples/addReaction.example.json`
- `openweb/src/sites/discord/examples/deleteMessage.example.json`
- `openweb/src/sites/discord/examples/getChannelInfo.example.json`
- `openweb/src/sites/discord/examples/getChannelMessages.example.json`
- `openweb/src/sites/discord/examples/getCurrentUser.example.json`
- `openweb/src/sites/discord/examples/getDirectMessages.example.json`
- `openweb/src/sites/discord/examples/getGuildInfo.example.json`
- `openweb/src/sites/discord/examples/getGuildRoles.example.json`
- `openweb/src/sites/discord/examples/getPinnedMessages.example.json`
- `openweb/src/sites/discord/examples/listGuildChannels.example.json`
- `openweb/src/sites/discord/examples/listGuilds.example.json`
- `openweb/src/sites/discord/examples/removeReaction.example.json`
- `openweb/src/sites/discord/examples/searchMessages.example.json`
- `openweb/src/sites/discord/examples/sendMessage.example.json`
- `openweb/src/sites/docker-hub/adapters/docker-hub.ts`
- `openweb/src/sites/docker-hub/adapters/docker-hub.js`
- `openweb/src/sites/docker-hub/examples/getImage.example.json`
- `openweb/src/sites/docker-hub/examples/getTags.example.json`
- `openweb/src/sites/docker-hub/examples/searchImages.example.json`
- `openweb/src/sites/doordash/adapters/doordash-read.ts`
- `openweb/src/sites/doordash/adapters/doordash-read.js`
- `openweb/src/sites/doordash/examples/addToCart.example.json`
- `openweb/src/sites/doordash/examples/getOrderHistory.example.json`
- `openweb/src/sites/doordash/examples/getRestaurantMenu.example.json`
- `openweb/src/sites/doordash/examples/removeFromCart.example.json`
- `openweb/src/sites/doordash/examples/searchRestaurants.example.json`
- `openweb/src/sites/douban/adapters/douban-read.ts`
- `openweb/src/sites/douban/adapters/douban-read.js`
- `openweb/src/sites/douban/examples/getBook.example.json`
- `openweb/src/sites/douban/examples/getBookReviews.example.json`
- `openweb/src/sites/douban/examples/getMovie.example.json`
- `openweb/src/sites/douban/examples/getMovieCelebrities.example.json`
- `openweb/src/sites/douban/examples/getMoviePhotos.example.json`
- `openweb/src/sites/douban/examples/getMovieReviews.example.json`
- `openweb/src/sites/douban/examples/getMusicDetail.example.json`
- `openweb/src/sites/douban/examples/getNowShowingMovies.example.json`
- `openweb/src/sites/douban/examples/getRecentHotMovies.example.json`
- `openweb/src/sites/douban/examples/getRecentHotTv.example.json`
- `openweb/src/sites/douban/examples/getTop250.example.json`
- `openweb/src/sites/douban/examples/searchBooks.example.json`
- `openweb/src/sites/douban/examples/searchMovies.example.json`
- `openweb/src/sites/douban/examples/searchMusic.example.json`
- `openweb/src/sites/ebay/adapters/ebay.ts`
- `openweb/src/sites/ebay/adapters/ebay.js`
- `openweb/src/sites/ebay/examples/getItemDetail.example.json`
- `openweb/src/sites/ebay/examples/getSellerProfile.example.json`
- `openweb/src/sites/ebay/examples/searchItems.example.json`
- `openweb/src/sites/espn/adapters/espn.ts`
- `openweb/src/sites/espn/adapters/espn.js`
- `openweb/src/sites/espn/examples/getNews.example.json`
- `openweb/src/sites/espn/examples/getScoreboard.example.json`
- `openweb/src/sites/espn/examples/getStandings.example.json`
- `openweb/src/sites/espn/examples/getTeam.example.json`
- `openweb/src/sites/espn/examples/getTeams.example.json`
- `openweb/src/sites/espn/examples/searchPlayers.example.json`
- `openweb/src/sites/etsy/examples/getListingDetail.example.json`
- `openweb/src/sites/etsy/examples/getReviews.example.json`
- `openweb/src/sites/etsy/examples/getShop.example.json`
- `openweb/src/sites/etsy/examples/searchListings.example.json`
- `openweb/src/sites/expedia/adapters/expedia-graphql.ts`
- `openweb/src/sites/expedia/adapters/expedia-graphql.js`
- `openweb/src/sites/expedia/examples/getFlightDetail.example.json`
- `openweb/src/sites/expedia/examples/getHotelDetail.example.json`
- `openweb/src/sites/expedia/examples/getHotelPrices.example.json`
- `openweb/src/sites/expedia/examples/getHotelReviews.example.json`
- `openweb/src/sites/expedia/examples/searchFlights.example.json`
- `openweb/src/sites/expedia/examples/searchHotels.example.json`
- `openweb/src/sites/fidelity/examples/getCompanyLogo.example.json`
- `openweb/src/sites/fidelity/examples/getCompanyProfile.example.json`
- `openweb/src/sites/fidelity/examples/getFundPerformance.example.json`
- `openweb/src/sites/fidelity/examples/getFundPicks.example.json`
- `openweb/src/sites/fidelity/examples/getFundSummary.example.json`
- `openweb/src/sites/fidelity/examples/getIndexQuotes.example.json`
- `openweb/src/sites/fidelity/examples/getMarketSummary.example.json`
- `openweb/src/sites/fidelity/examples/getNewsHeadlines.example.json`
- `openweb/src/sites/fidelity/examples/getQuote.example.json`
- `openweb/src/sites/fidelity/examples/getResearchData.example.json`
- `openweb/src/sites/fidelity/examples/listAssetClasses.example.json`
- `openweb/src/sites/fidelity/examples/listFundFamilies.example.json`
- `openweb/src/sites/fidelity/examples/searchFunds.example.json`
- `openweb/src/sites/github/adapters/github-read.ts`
- `openweb/src/sites/github/adapters/github-web.ts`
- `openweb/src/sites/github/adapters/github-read.js`
- `openweb/src/sites/github/adapters/github-web.js`
- `openweb/src/sites/github/examples/closeIssue.example.json`
- `openweb/src/sites/github/examples/createComment.example.json`
- `openweb/src/sites/github/examples/createIssue.example.json`
- `openweb/src/sites/github/examples/deleteComment.example.json`
- `openweb/src/sites/github/examples/forkRepo.example.json`
- `openweb/src/sites/github/examples/get_repo.example.json`
- `openweb/src/sites/github/examples/graphqlQuery.example.json`
- `openweb/src/sites/github/examples/list_issues.example.json`
- `openweb/src/sites/github/examples/reopenIssue.example.json`
- `openweb/src/sites/github/examples/starRepo.example.json`
- `openweb/src/sites/github/examples/unstarRepo.example.json`
- `openweb/src/sites/github/examples/unwatchRepo.example.json`
- `openweb/src/sites/github/examples/watchRepo.example.json`
- `openweb/src/sites/gitlab/adapters/gitlab.ts`
- `openweb/src/sites/gitlab/adapters/gitlab.js`
- `openweb/src/sites/gitlab/examples/closeIssue.example.json`
- `openweb/src/sites/gitlab/examples/createComment.example.json`
- `openweb/src/sites/gitlab/examples/createIssue.example.json`
- `openweb/src/sites/gitlab/examples/deleteComment.example.json`
- `openweb/src/sites/gitlab/examples/getGroup.example.json`
- `openweb/src/sites/gitlab/examples/getProject.example.json`
- `openweb/src/sites/gitlab/examples/listGroupProjects.example.json`
- `openweb/src/sites/gitlab/examples/listProjectBranches.example.json`
- `openweb/src/sites/gitlab/examples/listProjectIssues.example.json`
- `openweb/src/sites/gitlab/examples/listProjectMergeRequests.example.json`
- `openweb/src/sites/gitlab/examples/listProjectPipelines.example.json`
- `openweb/src/sites/gitlab/examples/searchGroups.example.json`
- `openweb/src/sites/gitlab/examples/searchProjects.example.json`
- `openweb/src/sites/gitlab/examples/searchUsers.example.json`
- `openweb/src/sites/gitlab/examples/starProject.example.json`
- `openweb/src/sites/gitlab/examples/unstarProject.example.json`
- `openweb/src/sites/glassdoor/adapters/glassdoor.ts`
- `openweb/src/sites/glassdoor/adapters/glassdoor.js`
- `openweb/src/sites/glassdoor/examples/getInterviews.example.json`
- `openweb/src/sites/glassdoor/examples/getReviews.example.json`
- `openweb/src/sites/glassdoor/examples/getSalaries.example.json`
- `openweb/src/sites/glassdoor/examples/searchCompanies.example.json`
- `openweb/src/sites/goodreads/adapters/goodreads.ts`
- `openweb/src/sites/goodreads/adapters/goodreads.js`
- `openweb/src/sites/goodreads/examples/getAuthor.example.json`
- `openweb/src/sites/goodreads/examples/getBook.example.json`
- `openweb/src/sites/goodreads/examples/getReviews.example.json`
- `openweb/src/sites/goodreads/examples/searchBooks.example.json`
- `openweb/src/sites/goodrx/examples/getDrugPrices.example.json`
- `openweb/src/sites/goodrx/examples/getPharmacies.example.json`
- `openweb/src/sites/goodrx/examples/searchDrugs.example.json`
- `openweb/src/sites/google-flights/adapters/google-flights.ts`
- `openweb/src/sites/google-flights/adapters/google-flights.js`
- `openweb/src/sites/google-flights/examples/exploreDestinations.example.json`
- `openweb/src/sites/google-flights/examples/getFlightBookingDetails.example.json`
- `openweb/src/sites/google-flights/examples/getFlightOverview.example.json`
- `openweb/src/sites/google-flights/examples/getPriceInsights.example.json`
- `openweb/src/sites/google-flights/examples/searchFlights.example.json`
- `openweb/src/sites/google-maps/adapters/google-maps-api.ts`
- `openweb/src/sites/google-maps/adapters/google-maps-api.js`
- `openweb/src/sites/google-maps/examples/getAutocompleteSuggestions.example.json`
- `openweb/src/sites/google-maps/examples/getDirections.example.json`
- `openweb/src/sites/google-maps/examples/getPlaceDetails.example.json`
- `openweb/src/sites/google-maps/examples/getPlacePhotos.example.json`
- `openweb/src/sites/google-maps/examples/getPlaceReviews.example.json`
- `openweb/src/sites/google-maps/examples/getTransitDirections.example.json`
- `openweb/src/sites/google-maps/examples/getWalkingDirections.example.json`
- `openweb/src/sites/google-maps/examples/nearbySearch.example.json`
- `openweb/src/sites/google-maps/examples/reverseGeocode.example.json`
- `openweb/src/sites/google-maps/examples/searchPlaces.example.json`
- `openweb/src/sites/google-scholar/examples/getAuthorProfile.example.json`
- `openweb/src/sites/google-scholar/examples/getCitations.example.json`
- `openweb/src/sites/google-scholar/examples/searchPapers.example.json`
- `openweb/src/sites/google-search/adapters/google-search.ts`
- `openweb/src/sites/google-search/adapters/google-search.js`
- `openweb/src/sites/google-search/examples/getKnowledgePanel.example.json`
- `openweb/src/sites/google-search/examples/getPeopleAlsoAsk.example.json`
- `openweb/src/sites/google-search/examples/getRelatedSearches.example.json`
- `openweb/src/sites/google-search/examples/searchImages.example.json`
- `openweb/src/sites/google-search/examples/searchLocal.example.json`
- `openweb/src/sites/google-search/examples/searchNews.example.json`
- `openweb/src/sites/google-search/examples/searchShopping.example.json`
- `openweb/src/sites/google-search/examples/searchSuggestions.example.json`
- `openweb/src/sites/google-search/examples/searchVideos.example.json`
- `openweb/src/sites/google-search/examples/searchWeb.example.json`
- `openweb/src/sites/grubhub/adapters/grubhub-read.ts`
- `openweb/src/sites/grubhub/adapters/grubhub-read.js`
- `openweb/src/sites/grubhub/examples/getDeliveryEstimate.example.json`
- `openweb/src/sites/grubhub/examples/getMenu.example.json`
- `openweb/src/sites/grubhub/examples/searchRestaurants.example.json`
- `openweb/src/sites/guardian/adapters/guardian.ts`
- `openweb/src/sites/guardian/adapters/guardian.js`
- `openweb/src/sites/guardian/examples/getArticle.example.json`
- `openweb/src/sites/guardian/examples/getSectionFeed.example.json`
- `openweb/src/sites/guardian/examples/searchArticles.example.json`
- `openweb/src/sites/hackernews/adapters/hackernews.ts`
- `openweb/src/sites/hackernews/adapters/hackernews.js`
- `openweb/src/sites/hackernews/examples/add_comment.example.json`
- `openweb/src/sites/hackernews/examples/delete_comment.example.json`
- `openweb/src/sites/hackernews/examples/get_ask_stories.example.json`
- `openweb/src/sites/hackernews/examples/get_best_stories.example.json`
- `openweb/src/sites/hackernews/examples/get_front_page_stories.example.json`
- `openweb/src/sites/hackernews/examples/get_job_postings.example.json`
- `openweb/src/sites/hackernews/examples/get_new_comments.example.json`
- `openweb/src/sites/hackernews/examples/get_newest_stories.example.json`
- `openweb/src/sites/hackernews/examples/get_show_stories.example.json`
- `openweb/src/sites/hackernews/examples/get_stories_by_domain.example.json`
- `openweb/src/sites/hackernews/examples/get_story_comments.example.json`
- `openweb/src/sites/hackernews/examples/get_story_detail.example.json`
- `openweb/src/sites/hackernews/examples/get_top_stories.example.json`
- `openweb/src/sites/hackernews/examples/get_user_comments.example.json`
- `openweb/src/sites/hackernews/examples/get_user_profile.example.json`
- `openweb/src/sites/hackernews/examples/get_user_submissions.example.json`
- `openweb/src/sites/hackernews/examples/unvote_story.example.json`
- `openweb/src/sites/hackernews/examples/upvote_story.example.json`
- `openweb/src/sites/homedepot/adapters/homedepot-web.ts`
- `openweb/src/sites/homedepot/adapters/homedepot-web.js`
- `openweb/src/sites/homedepot/examples/getProductDetail.example.json`
- `openweb/src/sites/homedepot/examples/getProductPricing.example.json`
- `openweb/src/sites/homedepot/examples/getProductReviews.example.json`
- `openweb/src/sites/homedepot/examples/getStoreAvailability.example.json`
- `openweb/src/sites/homedepot/examples/searchProducts.example.json`
- `openweb/src/sites/huggingface/adapters/huggingface.ts`
- `openweb/src/sites/huggingface/adapters/huggingface.js`
- `openweb/src/sites/huggingface/examples/getDataset.example.json`
- `openweb/src/sites/huggingface/examples/getModel.example.json`
- `openweb/src/sites/huggingface/examples/getSpaces.example.json`
- `openweb/src/sites/huggingface/examples/searchDatasets.example.json`
- `openweb/src/sites/huggingface/examples/searchModels.example.json`
- `openweb/src/sites/imdb/adapters/imdb.ts`
- `openweb/src/sites/imdb/adapters/imdb.js`
- `openweb/src/sites/imdb/examples/get_cast.example.json`
- `openweb/src/sites/imdb/examples/get_ratings.example.json`
- `openweb/src/sites/imdb/examples/get_title_detail.example.json`
- `openweb/src/sites/imdb/examples/search_titles.example.json`
- `openweb/src/sites/indeed/adapters/indeed-web.ts`
- `openweb/src/sites/indeed/adapters/indeed-web.js`
- `openweb/src/sites/indeed/examples/autocompleteJobTitle.example.json`
- `openweb/src/sites/indeed/examples/autocompleteLocation.example.json`
- `openweb/src/sites/indeed/examples/getCompanyOverview.example.json`
- `openweb/src/sites/indeed/examples/getCompanyReviews.example.json`
- `openweb/src/sites/indeed/examples/getCompanySalaries.example.json`
- `openweb/src/sites/indeed/examples/getJobDetail.example.json`
- `openweb/src/sites/indeed/examples/getSalary.example.json`
- `openweb/src/sites/indeed/examples/searchJobs.example.json`
- `openweb/src/sites/instacart/adapters/instacart-graphql.ts`
- `openweb/src/sites/instacart/adapters/queries.ts`
- `openweb/src/sites/instacart/adapters/instacart-graphql.js`
- `openweb/src/sites/instacart/adapters/queries.js`
- `openweb/src/sites/instacart/examples/getNearbyStores.example.json`
- `openweb/src/sites/instacart/examples/getStoreProducts.example.json`
- `openweb/src/sites/instacart/examples/searchProducts.example.json`
- `openweb/src/sites/instagram/adapters/instagram-api.ts`
- `openweb/src/sites/instagram/adapters/instagram-api.js`
- `openweb/src/sites/instagram/examples/blockUser.example.json`
- `openweb/src/sites/instagram/examples/createComment.example.json`
- `openweb/src/sites/instagram/examples/deleteComment.example.json`
- `openweb/src/sites/instagram/examples/followUser.example.json`
- `openweb/src/sites/instagram/examples/getExplore.example.json`
- `openweb/src/sites/instagram/examples/getFeed.example.json`
- `openweb/src/sites/instagram/examples/getFollowers.example.json`
- `openweb/src/sites/instagram/examples/getFollowing.example.json`
- `openweb/src/sites/instagram/examples/getNotifications.example.json`
- `openweb/src/sites/instagram/examples/getPost.example.json`
- `openweb/src/sites/instagram/examples/getPostComments.example.json`
- `openweb/src/sites/instagram/examples/getReels.example.json`
- `openweb/src/sites/instagram/examples/getStories.example.json`
- `openweb/src/sites/instagram/examples/getUserPosts.example.json`
- `openweb/src/sites/instagram/examples/getUserProfile.example.json`
- `openweb/src/sites/instagram/examples/likePost.example.json`
- `openweb/src/sites/instagram/examples/muteUser.example.json`
- `openweb/src/sites/instagram/examples/savePost.example.json`
- `openweb/src/sites/instagram/examples/searchUsers.example.json`
- `openweb/src/sites/instagram/examples/unblockUser.example.json`
- `openweb/src/sites/instagram/examples/unfollowUser.example.json`
- `openweb/src/sites/instagram/examples/unlikePost.example.json`
- `openweb/src/sites/instagram/examples/unmuteUser.example.json`
- `openweb/src/sites/instagram/examples/unsavePost.example.json`
- `openweb/src/sites/jd/adapters/jd-global-api.ts`
- `openweb/src/sites/jd/adapters/jd-global-api.js`
- `openweb/src/sites/jd/examples/getProductDetail.example.json`
- `openweb/src/sites/jd/examples/getProductPrice.example.json`
- `openweb/src/sites/jd/examples/getProductReviews.example.json`
- `openweb/src/sites/jd/examples/searchProducts.example.json`
- `openweb/src/sites/kayak/adapters/kayak-search.ts`
- `openweb/src/sites/kayak/adapters/kayak-search.js`
- `openweb/src/sites/kayak/examples/searchFlights.example.json`
- `openweb/src/sites/kayak/examples/searchHotels.example.json`
- `openweb/src/sites/leetcode/adapters/leetcode-graphql.ts`
- `openweb/src/sites/leetcode/adapters/leetcode-graphql.js`
- `openweb/src/sites/leetcode/examples/getContestHistory.example.json`
- `openweb/src/sites/leetcode/examples/getContestQuestions.example.json`
- `openweb/src/sites/leetcode/examples/getContestRanking.example.json`
- `openweb/src/sites/leetcode/examples/getDailyChallenge.example.json`
- `openweb/src/sites/leetcode/examples/getProblemList.example.json`
- `openweb/src/sites/leetcode/examples/getRecentSubmissions.example.json`
- `openweb/src/sites/leetcode/examples/getSolutionArticles.example.json`
- `openweb/src/sites/leetcode/examples/getSubmissions.example.json`
- `openweb/src/sites/leetcode/examples/getUpcomingContests.example.json`
- `openweb/src/sites/leetcode/examples/getUserContestRanking.example.json`
- `openweb/src/sites/leetcode/examples/getUserProfile.example.json`
- `openweb/src/sites/leetcode/examples/searchProblems.example.json`
- `openweb/src/sites/linkedin/adapters/linkedin-graphql.ts`
- `openweb/src/sites/linkedin/adapters/linkedin-graphql.js`
- `openweb/src/sites/linkedin/examples/getCompany.example.json`
- `openweb/src/sites/linkedin/examples/getConnectionsSummary.example.json`
- `openweb/src/sites/linkedin/examples/getFeed.example.json`
- `openweb/src/sites/linkedin/examples/getInvitations.example.json`
- `openweb/src/sites/linkedin/examples/getJobDetail.example.json`
- `openweb/src/sites/linkedin/examples/getMe.example.json`
- `openweb/src/sites/linkedin/examples/getMyNetworkNotifications.example.json`
- `openweb/src/sites/linkedin/examples/getNewsStorylines.example.json`
- `openweb/src/sites/linkedin/examples/getNotificationCards.example.json`
- `openweb/src/sites/linkedin/examples/getProfile.example.json`
- `openweb/src/sites/linkedin/examples/getProfileByUrn.example.json`
- `openweb/src/sites/linkedin/examples/searchGeo.example.json`
- `openweb/src/sites/linkedin/examples/searchJobs.example.json`
- `openweb/src/sites/medium/adapters/medium-graphql.ts`
- `openweb/src/sites/medium/adapters/queries.ts`
- `openweb/src/sites/medium/adapters/medium-graphql.js`
- `openweb/src/sites/medium/adapters/queries.js`
- `openweb/src/sites/medium/examples/clapArticle.example.json`
- `openweb/src/sites/medium/examples/followWriter.example.json`
- `openweb/src/sites/medium/examples/getArticle.example.json`
- `openweb/src/sites/medium/examples/getPostClaps.example.json`
- `openweb/src/sites/medium/examples/getRecommendedFeed.example.json`
- `openweb/src/sites/medium/examples/getRecommendedTags.example.json`
- `openweb/src/sites/medium/examples/getRecommendedWriters.example.json`
- `openweb/src/sites/medium/examples/getTagCuratedLists.example.json`
- `openweb/src/sites/medium/examples/getTagFeed.example.json`
- `openweb/src/sites/medium/examples/getTagWriters.example.json`
- `openweb/src/sites/medium/examples/saveArticle.example.json`
- `openweb/src/sites/medium/examples/searchArticles.example.json`
- `openweb/src/sites/medium/examples/unfollowWriter.example.json`
- `openweb/src/sites/medium/examples/unsaveArticle.example.json`
- `openweb/src/sites/notion/adapters/notion-api.ts`
- `openweb/src/sites/notion/adapters/notion-api.js`
- `openweb/src/sites/notion/examples/createPage.example.json`
- `openweb/src/sites/notion/examples/deletePage.example.json`
- `openweb/src/sites/notion/examples/getPage.example.json`
- `openweb/src/sites/notion/examples/getSpaces.example.json`
- `openweb/src/sites/notion/examples/queryDatabase.example.json`
- `openweb/src/sites/notion/examples/searchPages.example.json`
- `openweb/src/sites/notion/examples/updatePage.example.json`
- `openweb/src/sites/npm/adapters/npm.ts`
- `openweb/src/sites/npm/adapters/npm.js`
- `openweb/src/sites/npm/examples/getDownloads.example.json`
- `openweb/src/sites/npm/examples/getPackage.example.json`
- `openweb/src/sites/npm/examples/getVersions.example.json`
- `openweb/src/sites/npm/examples/searchPackages.example.json`
- `openweb/src/sites/npr/adapters/npr.ts`
- `openweb/src/sites/npr/adapters/npr.js`
- `openweb/src/sites/npr/examples/getArticle.example.json`
- `openweb/src/sites/npr/examples/getTopStories.example.json`
- `openweb/src/sites/npr/examples/searchArticles.example.json`
- `openweb/src/sites/opentable/adapters/opentable.ts`
- `openweb/src/sites/opentable/adapters/opentable.js`
- `openweb/src/sites/opentable/examples/getAvailability.example.json`
- `openweb/src/sites/opentable/examples/getRestaurant.example.json`
- `openweb/src/sites/opentable/examples/getReviews.example.json`
- `openweb/src/sites/opentable/examples/searchRestaurants.example.json`
- `openweb/src/sites/pinterest/adapters/pinterest-api.ts`
- `openweb/src/sites/pinterest/adapters/pinterest-api.js`
- `openweb/src/sites/pinterest/examples/followBoard.example.json`
- `openweb/src/sites/pinterest/examples/getBoard.example.json`
- `openweb/src/sites/pinterest/examples/getHomeFeed.example.json`
- `openweb/src/sites/pinterest/examples/getNotifications.example.json`
- `openweb/src/sites/pinterest/examples/getPin.example.json`
- `openweb/src/sites/pinterest/examples/getUserProfile.example.json`
- `openweb/src/sites/pinterest/examples/savePin.example.json`
- `openweb/src/sites/pinterest/examples/searchPins.example.json`
- `openweb/src/sites/pinterest/examples/searchTypeahead.example.json`
- `openweb/src/sites/pinterest/examples/unfollowBoard.example.json`
- `openweb/src/sites/pinterest/examples/unsavePin.example.json`
- `openweb/src/sites/producthunt/adapters/producthunt.ts`
- `openweb/src/sites/producthunt/adapters/producthunt.js`
- `openweb/src/sites/producthunt/examples/get_post.example.json`
- `openweb/src/sites/producthunt/examples/get_posts.example.json`
- `openweb/src/sites/producthunt/examples/get_today.example.json`
- `openweb/src/sites/producthunt/examples/search_products.example.json`
- `openweb/src/sites/pypi/adapters/pypi.ts`
- `openweb/src/sites/pypi/adapters/pypi.js`
- `openweb/src/sites/pypi/examples/getPackage.example.json`
- `openweb/src/sites/pypi/examples/getPackageVersion.example.json`
- `openweb/src/sites/pypi/examples/getReleases.example.json`
- `openweb/src/sites/quora/adapters/quora.ts`
- `openweb/src/sites/quora/adapters/quora.js`
- `openweb/src/sites/quora/examples/getAnswers.example.json`
- `openweb/src/sites/quora/examples/getProfile.example.json`
- `openweb/src/sites/quora/examples/getQuestion.example.json`
- `openweb/src/sites/quora/examples/searchQuestions.example.json`
- `openweb/src/sites/reddit/adapters/reddit-read.ts`
- `openweb/src/sites/reddit/adapters/reddit-read.js`
- `openweb/src/sites/reddit/examples/blockUser.example.json`
- `openweb/src/sites/reddit/examples/createComment.example.json`
- `openweb/src/sites/reddit/examples/createPost.example.json`
- `openweb/src/sites/reddit/examples/deleteThing.example.json`
- `openweb/src/sites/reddit/examples/getMe.example.json`
- `openweb/src/sites/reddit/examples/getNotifications.example.json`
- `openweb/src/sites/reddit/examples/getPopularPosts.example.json`
- `openweb/src/sites/reddit/examples/getPostComments.example.json`
- `openweb/src/sites/reddit/examples/getSubredditAbout.example.json`
- `openweb/src/sites/reddit/examples/getSubredditPosts.example.json`
- `openweb/src/sites/reddit/examples/getUserPosts.example.json`
- `openweb/src/sites/reddit/examples/getUserProfile.example.json`
- `openweb/src/sites/reddit/examples/savePost.example.json`
- `openweb/src/sites/reddit/examples/searchPosts.example.json`
- `openweb/src/sites/reddit/examples/subscribe.example.json`
- `openweb/src/sites/reddit/examples/unsavePost.example.json`
- `openweb/src/sites/reddit/examples/vote.example.json`
- `openweb/src/sites/redfin/adapters/redfin.ts`
- `openweb/src/sites/redfin/adapters/redfin.js`
- `openweb/src/sites/redfin/examples/getMarketData.example.json`
- `openweb/src/sites/redfin/examples/getPropertyDetails.example.json`
- `openweb/src/sites/redfin/examples/searchHomes.example.json`
- `openweb/src/sites/reuters/adapters/reuters-api.ts`
- `openweb/src/sites/reuters/adapters/reuters-api.js`
- `openweb/src/sites/reuters/examples/getArticleDetail.example.json`
- `openweb/src/sites/reuters/examples/getTopNews.example.json`
- `openweb/src/sites/reuters/examples/getTopicArticles.example.json`
- `openweb/src/sites/reuters/examples/searchArticles.example.json`
- `openweb/src/sites/robinhood/examples/getAnalystRatings.example.json`
- `openweb/src/sites/robinhood/examples/getCryptoHistoricals.example.json`
- `openweb/src/sites/robinhood/examples/getCryptoQuote.example.json`
- `openweb/src/sites/robinhood/examples/getInstruments.example.json`
- `openweb/src/sites/robinhood/examples/getMarketMovers.example.json`
- `openweb/src/sites/robinhood/examples/getStockEarnings.example.json`
- `openweb/src/sites/robinhood/examples/getStockFundamentals.example.json`
- `openweb/src/sites/robinhood/examples/getStockHistoricals.example.json`
- `openweb/src/sites/robinhood/examples/getStockNews.example.json`
- `openweb/src/sites/robinhood/examples/getStockQuotes.example.json`
- `openweb/src/sites/rotten-tomatoes/adapters/rotten-tomatoes-web.ts`
- `openweb/src/sites/rotten-tomatoes/adapters/rotten-tomatoes-web.js`
- `openweb/src/sites/rotten-tomatoes/examples/getMovieDetail.example.json`
- `openweb/src/sites/rotten-tomatoes/examples/getTomatoMeter.example.json`
- `openweb/src/sites/rotten-tomatoes/examples/searchMovies.example.json`
- `openweb/src/sites/seeking-alpha/adapters/seeking-alpha-api.ts`
- `openweb/src/sites/seeking-alpha/adapters/seeking-alpha-api.js`
- `openweb/src/sites/seeking-alpha/examples/getArticle.example.json`
- `openweb/src/sites/seeking-alpha/examples/getEarnings.example.json`
- `openweb/src/sites/seeking-alpha/examples/getStockAnalysis.example.json`
- `openweb/src/sites/seeking-alpha/examples/searchArticles.example.json`
- `openweb/src/sites/soundcloud/adapters/soundcloud.ts`
- `openweb/src/sites/soundcloud/adapters/soundcloud.js`
- `openweb/src/sites/soundcloud/examples/getPlaylist.example.json`
- `openweb/src/sites/soundcloud/examples/getTrack.example.json`
- `openweb/src/sites/soundcloud/examples/getUser.example.json`
- `openweb/src/sites/soundcloud/examples/searchTracks.example.json`
- `openweb/src/sites/spotify/adapters/spotify-pathfinder.ts`
- `openweb/src/sites/spotify/adapters/spotify-pathfinder.js`
- `openweb/src/sites/spotify/examples/addToPlaylist.example.json`
- `openweb/src/sites/spotify/examples/createPlaylist.example.json`
- `openweb/src/sites/spotify/examples/getAlbumTracks.example.json`
- `openweb/src/sites/spotify/examples/getArtist.example.json`
- `openweb/src/sites/spotify/examples/getArtistDiscography.example.json`
- `openweb/src/sites/spotify/examples/getPlaylist.example.json`
- `openweb/src/sites/spotify/examples/getRecommendations.example.json`
- `openweb/src/sites/spotify/examples/getTrack.example.json`
- `openweb/src/sites/spotify/examples/getUserPlaylists.example.json`
- `openweb/src/sites/spotify/examples/likeTrack.example.json`
- `openweb/src/sites/spotify/examples/removeFromPlaylist.example.json`
- `openweb/src/sites/spotify/examples/searchMusic.example.json`
- `openweb/src/sites/spotify/examples/unlikeTrack.example.json`
- `openweb/src/sites/stackoverflow/adapters/stackoverflow.ts`
- `openweb/src/sites/stackoverflow/adapters/stackoverflow.js`
- `openweb/src/sites/stackoverflow/examples/getAnswers.example.json`
- `openweb/src/sites/stackoverflow/examples/getQuestion.example.json`
- `openweb/src/sites/stackoverflow/examples/getUser.example.json`
- `openweb/src/sites/stackoverflow/examples/searchQuestions.example.json`
- `openweb/src/sites/stackoverflow/examples/searchTags.example.json`
- `openweb/src/sites/starbucks/adapters/starbucks.ts`
- `openweb/src/sites/starbucks/adapters/starbucks.js`
- `openweb/src/sites/starbucks/examples/getMenu.example.json`
- `openweb/src/sites/starbucks/examples/getStoreDetail.example.json`
- `openweb/src/sites/starbucks/examples/searchStores.example.json`
- `openweb/src/sites/steam/adapters/steam.ts`
- `openweb/src/sites/steam/adapters/steam.js`
- `openweb/src/sites/steam/examples/getAppDetails.example.json`
- `openweb/src/sites/steam/examples/getAppNews.example.json`
- `openweb/src/sites/steam/examples/getAppReviews.example.json`
- `openweb/src/sites/steam/examples/getCurrentPlayers.example.json`
- `openweb/src/sites/steam/examples/getFeatured.example.json`
- `openweb/src/sites/steam/examples/getFeaturedCategories.example.json`
- `openweb/src/sites/steam/examples/getGlobalAchievements.example.json`
- `openweb/src/sites/steam/examples/getPackageDetails.example.json`
- `openweb/src/sites/steam/examples/searchGames.example.json`
- `openweb/src/sites/substack/adapters/substack.ts`
- `openweb/src/sites/substack/adapters/substack.js`
- `openweb/src/sites/substack/examples/getArchive.example.json`
- `openweb/src/sites/substack/examples/getPost.example.json`
- `openweb/src/sites/substack/examples/getPostComments.example.json`
- `openweb/src/sites/substack/examples/searchPosts.example.json`
- `openweb/src/sites/target/examples/addToCart.example.json`
- `openweb/src/sites/target/examples/get_product_detail.example.json`
- `openweb/src/sites/target/examples/get_store_availability.example.json`
- `openweb/src/sites/target/examples/removeFromCart.example.json`
- `openweb/src/sites/target/examples/search_products.example.json`
- `openweb/src/sites/techcrunch/adapters/techcrunch.ts`
- `openweb/src/sites/techcrunch/adapters/techcrunch.js`
- `openweb/src/sites/techcrunch/examples/getArticle.example.json`
- `openweb/src/sites/techcrunch/examples/getCategory.example.json`
- `openweb/src/sites/techcrunch/examples/getLatest.example.json`
- `openweb/src/sites/techcrunch/examples/searchArticles.example.json`
- `openweb/src/sites/telegram/adapters/telegram-protocol.ts`
- `openweb/src/sites/telegram/adapters/telegram-protocol.js`
- `openweb/src/sites/telegram/examples/deleteMessage.example.json`
- `openweb/src/sites/telegram/examples/editMessage.example.json`
- `openweb/src/sites/telegram/examples/forwardMessages.example.json`
- `openweb/src/sites/telegram/examples/getChats.example.json`
- `openweb/src/sites/telegram/examples/getMe.example.json`
- `openweb/src/sites/telegram/examples/getMessages.example.json`
- `openweb/src/sites/telegram/examples/getUserInfo.example.json`
- `openweb/src/sites/telegram/examples/markAsRead.example.json`
- `openweb/src/sites/telegram/examples/pinMessage.example.json`
- `openweb/src/sites/telegram/examples/searchMessages.example.json`
- `openweb/src/sites/telegram/examples/sendMessage.example.json`
- `openweb/src/sites/telegram/examples/unpinMessage.example.json`
- `openweb/src/sites/tiktok/adapters/tiktok-web.ts`
- `openweb/src/sites/tiktok/adapters/tiktok-web.js`
- `openweb/src/sites/tiktok/examples/blockUser.example.json`
- `openweb/src/sites/tiktok/examples/bookmarkVideo.example.json`
- `openweb/src/sites/tiktok/examples/createComment.example.json`
- `openweb/src/sites/tiktok/examples/deleteComment.example.json`
- `openweb/src/sites/tiktok/examples/followUser.example.json`
- `openweb/src/sites/tiktok/examples/getCommentReplies.example.json`
- `openweb/src/sites/tiktok/examples/getExplore.example.json`
- `openweb/src/sites/tiktok/examples/getHashtagDetail.example.json`
- `openweb/src/sites/tiktok/examples/getHashtagVideos.example.json`
- `openweb/src/sites/tiktok/examples/getHomeFeed.example.json`
- `openweb/src/sites/tiktok/examples/getRelatedVideos.example.json`
- `openweb/src/sites/tiktok/examples/getUserProfile.example.json`
- `openweb/src/sites/tiktok/examples/getUserVideos.example.json`
- `openweb/src/sites/tiktok/examples/getVideoComments.example.json`
- `openweb/src/sites/tiktok/examples/getVideoDetail.example.json`
- `openweb/src/sites/tiktok/examples/likeComment.example.json`
- `openweb/src/sites/tiktok/examples/likeVideo.example.json`
- `openweb/src/sites/tiktok/examples/replyComment.example.json`
- `openweb/src/sites/tiktok/examples/searchUsers.example.json`
- `openweb/src/sites/tiktok/examples/searchVideos.example.json`
- `openweb/src/sites/tiktok/examples/unblockUser.example.json`
- `openweb/src/sites/tiktok/examples/unbookmarkVideo.example.json`
- `openweb/src/sites/tiktok/examples/unfollowUser.example.json`
- `openweb/src/sites/tiktok/examples/unlikeComment.example.json`
- `openweb/src/sites/tiktok/examples/unlikeVideo.example.json`
- `openweb/src/sites/todoist/adapters/todoist-api.ts`
- `openweb/src/sites/todoist/adapters/todoist-api.js`
- `openweb/src/sites/todoist/examples/completeTask.example.json`
- `openweb/src/sites/todoist/examples/createTask.example.json`
- `openweb/src/sites/todoist/examples/deleteTask.example.json`
- `openweb/src/sites/todoist/examples/getProjects.example.json`
- `openweb/src/sites/todoist/examples/getTasks.example.json`
- `openweb/src/sites/todoist/examples/uncompleteTask.example.json`
- `openweb/src/sites/trello/adapters/trello-api.ts`
- `openweb/src/sites/trello/adapters/trello-api.js`
- `openweb/src/sites/trello/examples/archiveCard.example.json`
- `openweb/src/sites/trello/examples/createCard.example.json`
- `openweb/src/sites/trello/examples/deleteCard.example.json`
- `openweb/src/sites/trello/examples/getBoards.example.json`
- `openweb/src/sites/tripadvisor/adapters/tripadvisor.ts`
- `openweb/src/sites/tripadvisor/adapters/tripadvisor.js`
- `openweb/src/sites/tripadvisor/examples/getAttractionDetail.example.json`
- `openweb/src/sites/tripadvisor/examples/getAttractionReviews.example.json`
- `openweb/src/sites/tripadvisor/examples/getHotelDetail.example.json`
- `openweb/src/sites/tripadvisor/examples/getRestaurant.example.json`
- `openweb/src/sites/tripadvisor/examples/searchHotels.example.json`
- `openweb/src/sites/tripadvisor/examples/searchLocation.example.json`
- `openweb/src/sites/tripadvisor/examples/searchRestaurants.example.json`
- `openweb/src/sites/twitch/examples/getChannel.example.json`
- `openweb/src/sites/twitch/examples/getClips.example.json`
- `openweb/src/sites/twitch/examples/getStream.example.json`
- `openweb/src/sites/twitch/examples/getTopGames.example.json`
- `openweb/src/sites/twitch/examples/getTopStreams.example.json`
- `openweb/src/sites/twitch/examples/getVideos.example.json`
- `openweb/src/sites/twitch/examples/searchChannels.example.json`
- `openweb/src/sites/uber/adapters/uber-rides.ts`
- `openweb/src/sites/uber/adapters/uber-rides.js`
- `openweb/src/sites/uber/examples/getRideEstimate.example.json`
- `openweb/src/sites/uber/examples/getRideHistory.example.json`
- `openweb/src/sites/uber/examples/searchLocations.example.json`
- `openweb/src/sites/ubereats/adapters/uber-eats.ts`
- `openweb/src/sites/ubereats/adapters/uber-eats.js`
- `openweb/src/sites/ubereats/examples/addToCart.example.json`
- `openweb/src/sites/ubereats/examples/emptyCart.example.json`
- `openweb/src/sites/ubereats/examples/getCart.example.json`
- `openweb/src/sites/ubereats/examples/getEatsOrderHistory.example.json`
- `openweb/src/sites/ubereats/examples/getItemDetails.example.json`
- `openweb/src/sites/ubereats/examples/getRestaurantMenu.example.json`
- `openweb/src/sites/ubereats/examples/removeFromCart.example.json`
- `openweb/src/sites/ubereats/examples/searchRestaurants.example.json`
- `openweb/src/sites/walmart/adapters/walmart-cart.ts`
- `openweb/src/sites/walmart/adapters/walmart-read.ts`
- `openweb/src/sites/walmart/adapters/walmart-cart.js`
- `openweb/src/sites/walmart/adapters/walmart-read.js`
- `openweb/src/sites/walmart/examples/addToCart.example.json`
- `openweb/src/sites/walmart/examples/get_product_detail.example.json`
- `openweb/src/sites/walmart/examples/get_product_pricing.example.json`
- `openweb/src/sites/walmart/examples/removeFromCart.example.json`
- `openweb/src/sites/walmart/examples/search_products.example.json`
- `openweb/src/sites/weibo/adapters/weibo-read.ts`
- `openweb/src/sites/weibo/adapters/weibo-read.js`
- `openweb/src/sites/weibo/examples/bookmarkPost.example.json`
- `openweb/src/sites/weibo/examples/followUser.example.json`
- `openweb/src/sites/weibo/examples/getFriendsFeed.example.json`
- `openweb/src/sites/weibo/examples/getHotFeed.example.json`
- `openweb/src/sites/weibo/examples/getHotSearch.example.json`
- `openweb/src/sites/weibo/examples/getPost.example.json`
- `openweb/src/sites/weibo/examples/getUserDetail.example.json`
- `openweb/src/sites/weibo/examples/getUserProfile.example.json`
- `openweb/src/sites/weibo/examples/getUserStatuses.example.json`
- `openweb/src/sites/weibo/examples/likePost.example.json`
- `openweb/src/sites/weibo/examples/listReposts.example.json`
- `openweb/src/sites/weibo/examples/repost.example.json`
- `openweb/src/sites/weibo/examples/unbookmarkPost.example.json`
- `openweb/src/sites/weibo/examples/unfollowUser.example.json`
- `openweb/src/sites/weibo/examples/unlikePost.example.json`
- `openweb/src/sites/whatsapp/adapters/whatsapp-modules.ts`
- `openweb/src/sites/whatsapp/adapters/whatsapp-modules.js`
- `openweb/src/sites/whatsapp/examples/deleteMessage.example.json`
- `openweb/src/sites/whatsapp/examples/getChats.example.json`
- `openweb/src/sites/whatsapp/examples/getContacts.example.json`
- `openweb/src/sites/whatsapp/examples/markAsRead.example.json`
- `openweb/src/sites/whatsapp/examples/searchChats.example.json`
- `openweb/src/sites/whatsapp/examples/sendMessage.example.json`
- `openweb/src/sites/wikipedia/examples/getFeaturedContent.example.json`
- `openweb/src/sites/wikipedia/examples/getOnThisDay.example.json`
- `openweb/src/sites/wikipedia/examples/getPageBacklinks.example.json`
- `openweb/src/sites/wikipedia/examples/getPageCategories.example.json`
- `openweb/src/sites/wikipedia/examples/getPageMediaList.example.json`
- `openweb/src/sites/wikipedia/examples/getPageRevisions.example.json`
- `openweb/src/sites/wikipedia/examples/getPageSource.example.json`
- `openweb/src/sites/wikipedia/examples/getPageSummary.example.json`
- `openweb/src/sites/wikipedia/examples/getRandomArticle.example.json`
- `openweb/src/sites/wikipedia/examples/searchArticles.example.json`
- `openweb/src/sites/x/adapters/x-graphql.ts`
- `openweb/src/sites/x/adapters/x-graphql.js`
- `openweb/src/sites/x/examples/blockUser.example.json`
- `openweb/src/sites/x/examples/createBookmark.example.json`
- `openweb/src/sites/x/examples/createRetweet.example.json`
- `openweb/src/sites/x/examples/createTweet.example.json`
- `openweb/src/sites/x/examples/deleteBookmark.example.json`
- `openweb/src/sites/x/examples/deleteRetweet.example.json`
- `openweb/src/sites/x/examples/deleteTweet.example.json`
- `openweb/src/sites/x/examples/followUser.example.json`
- `openweb/src/sites/x/examples/getBookmarks.example.json`
- `openweb/src/sites/x/examples/getExplorePage.example.json`
- `openweb/src/sites/x/examples/getHomeTimeline.example.json`
- `openweb/src/sites/x/examples/getNotifications.example.json`
- `openweb/src/sites/x/examples/getTweetDetail.example.json`
- `openweb/src/sites/x/examples/getUserByScreenName.example.json`
- `openweb/src/sites/x/examples/getUserFollowers.example.json`
- `openweb/src/sites/x/examples/getUserFollowing.example.json`
- `openweb/src/sites/x/examples/getUserLikes.example.json`
- `openweb/src/sites/x/examples/getUserTweets.example.json`
- `openweb/src/sites/x/examples/hideReply.example.json`
- `openweb/src/sites/x/examples/likeTweet.example.json`
- `openweb/src/sites/x/examples/muteUser.example.json`
- `openweb/src/sites/x/examples/reply.example.json`
- `openweb/src/sites/x/examples/searchTweets.example.json`
- `openweb/src/sites/x/examples/sendDM.example.json`
- `openweb/src/sites/x/examples/unblockUser.example.json`
- `openweb/src/sites/x/examples/unfollowUser.example.json`
- `openweb/src/sites/x/examples/unhideReply.example.json`
- `openweb/src/sites/x/examples/unlikeTweet.example.json`
- `openweb/src/sites/x/examples/unmuteUser.example.json`
- `openweb/src/sites/xiaohongshu/adapters/xiaohongshu-web.ts`
- `openweb/src/sites/xiaohongshu/adapters/xiaohongshu-web.js`
- `openweb/src/sites/xiaohongshu/examples/getExploreFeed.example.json`
- `openweb/src/sites/xiaohongshu/examples/getHotSearch.example.json`
- `openweb/src/sites/xiaohongshu/examples/getNoteComments.example.json`
- `openweb/src/sites/xiaohongshu/examples/getNoteDetail.example.json`
- `openweb/src/sites/xiaohongshu/examples/getRelatedNotes.example.json`
- `openweb/src/sites/xiaohongshu/examples/getUserCollections.example.json`
- `openweb/src/sites/xiaohongshu/examples/getUserLiked.example.json`
- `openweb/src/sites/xiaohongshu/examples/getUserNotes.example.json`
- `openweb/src/sites/xiaohongshu/examples/getUserProfile.example.json`
- `openweb/src/sites/xiaohongshu/examples/searchNotes.example.json`
- `openweb/src/sites/xueqiu/adapters/xueqiu.ts`
- `openweb/src/sites/xueqiu/adapters/xueqiu.js`
- `openweb/src/sites/xueqiu/examples/getOrderBook.example.json`
- `openweb/src/sites/xueqiu/examples/getStockFinancials.example.json`
- `openweb/src/sites/xueqiu/examples/getStockKline.example.json`
- `openweb/src/sites/xueqiu/examples/getStockQuote.example.json`
- `openweb/src/sites/xueqiu/examples/getTimeline.example.json`
- `openweb/src/sites/xueqiu/examples/getWatchlist.example.json`
- `openweb/src/sites/xueqiu/examples/searchStocks.example.json`
- `openweb/src/sites/yahoo-finance/adapters/yahoo-finance.ts`
- `openweb/src/sites/yahoo-finance/adapters/yahoo-finance.js`
- `openweb/src/sites/yahoo-finance/examples/getCalendarEvents.example.json`
- `openweb/src/sites/yahoo-finance/examples/getChart.example.json`
- `openweb/src/sites/yahoo-finance/examples/getInsights.example.json`
- `openweb/src/sites/yahoo-finance/examples/getQuoteType.example.json`
- `openweb/src/sites/yahoo-finance/examples/getRatings.example.json`
- `openweb/src/sites/yahoo-finance/examples/getScreener.example.json`
- `openweb/src/sites/yahoo-finance/examples/getSparkline.example.json`
- `openweb/src/sites/yahoo-finance/examples/getTimeSeries.example.json`
- `openweb/src/sites/yahoo-finance/examples/searchTickers.example.json`
- `openweb/src/sites/yelp/adapters/yelp.ts`
- `openweb/src/sites/yelp/adapters/yelp.js`
- `openweb/src/sites/yelp/examples/autocompleteBusinesses.example.json`
- `openweb/src/sites/yelp/examples/searchBusinesses.example.json`
- `openweb/src/sites/youtube-music/examples/browseCharts.example.json`
- `openweb/src/sites/youtube-music/examples/browseHome.example.json`
- `openweb/src/sites/youtube-music/examples/getAlbum.example.json`
- `openweb/src/sites/youtube-music/examples/getArtist.example.json`
- `openweb/src/sites/youtube-music/examples/getPlaylist.example.json`
- `openweb/src/sites/youtube-music/examples/getSearchSuggestions.example.json`
- `openweb/src/sites/youtube-music/examples/getSong.example.json`
- `openweb/src/sites/youtube-music/examples/getUpNext.example.json`
- `openweb/src/sites/youtube-music/examples/searchMusic.example.json`
- `openweb/src/sites/youtube/adapters/youtube-innertube.ts`
- `openweb/src/sites/youtube/adapters/youtube-innertube.js`
- `openweb/src/sites/youtube/examples/addComment.example.json`
- `openweb/src/sites/youtube/examples/browseContent.example.json`
- `openweb/src/sites/youtube/examples/deleteComment.example.json`
- `openweb/src/sites/youtube/examples/getComments.example.json`
- `openweb/src/sites/youtube/examples/getGuide.example.json`
- `openweb/src/sites/youtube/examples/getNotificationCount.example.json`
- `openweb/src/sites/youtube/examples/getPlaylist.example.json`
- `openweb/src/sites/youtube/examples/getTranscript.example.json`
- `openweb/src/sites/youtube/examples/getVideoDetail.example.json`
- `openweb/src/sites/youtube/examples/getVideoPlayer.example.json`
- `openweb/src/sites/youtube/examples/likeVideo.example.json`
- `openweb/src/sites/youtube/examples/searchVideos.example.json`
- `openweb/src/sites/youtube/examples/subscribeChannel.example.json`
- `openweb/src/sites/youtube/examples/unlikeVideo.example.json`
- `openweb/src/sites/youtube/examples/unsubscribeChannel.example.json`
- `openweb/src/sites/zhihu/adapters/zhihu-read.ts`
- `openweb/src/sites/zhihu/adapters/zhihu-read.js`
- `openweb/src/sites/zhihu/examples/cancelUpvote.example.json`
- `openweb/src/sites/zhihu/examples/followQuestion.example.json`
- `openweb/src/sites/zhihu/examples/followUser.example.json`
- `openweb/src/sites/zhihu/examples/getEntityWord.example.json`
- `openweb/src/sites/zhihu/examples/getFeedRecommend.example.json`
- `openweb/src/sites/zhihu/examples/getHotSearch.example.json`
- `openweb/src/sites/zhihu/examples/getMe.example.json`
- `openweb/src/sites/zhihu/examples/getMember.example.json`
- `openweb/src/sites/zhihu/examples/listMemberActivities.example.json`
- `openweb/src/sites/zhihu/examples/listMemberMutuals.example.json`
- `openweb/src/sites/zhihu/examples/listQuestionFollowers.example.json`
- `openweb/src/sites/zhihu/examples/listSimilarQuestions.example.json`
- `openweb/src/sites/zhihu/examples/searchContent.example.json`
- `openweb/src/sites/zhihu/examples/unfollowQuestion.example.json`
- `openweb/src/sites/zhihu/examples/unfollowUser.example.json`
- `openweb/src/sites/zhihu/examples/upvoteAnswer.example.json`
- `openweb/src/sites/zillow/adapters/zillow-detail.ts`
- `openweb/src/sites/zillow/adapters/zillow-detail.js`
- `openweb/src/sites/zillow/examples/getNeighborhood.example.json`
- `openweb/src/sites/zillow/examples/getPropertyDetail.example.json`
- `openweb/src/sites/zillow/examples/getZestimate.example.json`
- `openweb/src/sites/zillow/examples/searchProperties.example.json`
- `openweb/tests/benchmark/01-direct-http.md`
- `openweb/tests/benchmark/02-session-http-instagram.md`
- `openweb/tests/benchmark/03-session-http-github.md`
- `openweb/tests/benchmark/04-session-http-youtube.md`
- `openweb/tests/benchmark/05-browser-fetch-discord.md`
- `openweb/tests/benchmark/06-l3-adapter-telegram.md`
- `openweb/tests/benchmark/07-auth-failure.md`
- `openweb/tests/benchmark/08-extraction-dom-hackernews.md`
- `openweb/tests/benchmark/09-extraction-nextjs-walmart.md`
- `openweb/tests/benchmark/10-msal-microsoft-word.md`
- `openweb/tests/integration/instagram-integration.test.ts`
- `openweb/tests/integration/phase2-fixtures.test.ts`
- `openweb/tests/integration/runner.ts`
- `openweb/tests/integration/sites.config.ts`
- `reverse-api-engineer/scripts/clean_build.sh`
- `reverse-api-engineer/tests/__init__.py`
- `reverse-api-engineer/tests/conftest.py`
- `reverse-api-engineer/tests/test_auto_engineer.py`
- `reverse-api-engineer/tests/test_base_engineer.py`
- `reverse-api-engineer/tests/test_cli_agent_json.py`
- `reverse-api-engineer/tests/test_cli_engineer_command.py`
- `reverse-api-engineer/tests/test_cli_followups.py`
- `reverse-api-engineer/tests/test_collector.py`
- `reverse-api-engineer/tests/test_collector_ui.py`
- `reverse-api-engineer/tests/test_config.py`
- `reverse-api-engineer/tests/test_cursor_engineer.py`
- `reverse-api-engineer/tests/test_engineer.py`
- `reverse-api-engineer/tests/test_init.py`
- `reverse-api-engineer/tests/test_messages.py`
- `reverse-api-engineer/tests/test_opencode_engineer.py`
- `reverse-api-engineer/tests/test_opencode_ui.py`
- `reverse-api-engineer/tests/test_pricing.py`
- `reverse-api-engineer/tests/test_prompts.py`
- `reverse-api-engineer/tests/test_run_command.py`
- `reverse-api-engineer/tests/test_session.py`
- `reverse-api-engineer/tests/test_sync.py`
- `reverse-api-engineer/tests/test_tui.py`
- `reverse-api-engineer/tests/test_utils.py`
- `reverse-api-engineer/examples/apple/INDEX.md`
- `reverse-api-engineer/examples/apple/QUICKSTART.md`
- `reverse-api-engineer/examples/apple/README.md`
- `reverse-api-engineer/examples/apple/SUMMARY.md`
- `reverse-api-engineer/examples/apple/api_client.py`
- `reverse-api-engineer/examples/apple/extract_job_fields.py`
- `reverse-api-engineer/examples/apple/main.py`
- `reverse-api-engineer/examples/apple/quick_example.py`
- `reverse-api-engineer/examples/apple/requirements.txt`
- `reverse-api-engineer/examples/ashby/API_SUMMARY.txt`
- `reverse-api-engineer/examples/ashby/QUICKSTART.md`
- `reverse-api-engineer/examples/ashby/README.md`
- `reverse-api-engineer/examples/ashby/api_client.py`
- `reverse-api-engineer/examples/ashby/example_usage.py`
- `reverse-api-engineer/examples/ashby/requirements.txt`
- `reverse-api-engineer/examples/autoscout24/README.md`
- `reverse-api-engineer/examples/autoscout24/SUMMARY.md`
- `reverse-api-engineer/examples/autoscout24/api_client.py`
- `reverse-api-engineer/examples/ikea/README.md`
- `reverse-api-engineer/examples/ikea/api_client.py`
- `reverse-api-engineer/examples/mintlify/README.md`
- `reverse-api-engineer/examples/mintlify/api_client.py`
- `reverse-api-engineer/examples/uber/API_ANALYSIS_SUMMARY.md`
- `reverse-api-engineer/examples/uber/README.md`
- `reverse-api-engineer/examples/uber/api_client.py`
- `reverse-api-engineer/examples/uber/example_fetch_all_jobs.py`
- `reverse-api-engineer/examples/uber/quick_start.py`
- `reverse-api-engineer/examples/uber/requirements.txt`
- `reverse-api-engineer/src/reverse_api/__init__.py`
- `reverse-api-engineer/src/reverse_api/auto_engineer.py`
- `reverse-api-engineer/src/reverse_api/base_engineer.py`
- `reverse-api-engineer/src/reverse_api/browser.py`
- `reverse-api-engineer/src/reverse_api/cli.py`
- `reverse-api-engineer/src/reverse_api/collector.py`
- `reverse-api-engineer/src/reverse_api/collector_ui.py`
- `reverse-api-engineer/src/reverse_api/config.py`
- `reverse-api-engineer/src/reverse_api/copilot_engineer.py`
- `reverse-api-engineer/src/reverse_api/cursor_engineer.py`
- `reverse-api-engineer/src/reverse_api/engineer.py`
- `reverse-api-engineer/src/reverse_api/messages.py`
- `reverse-api-engineer/src/reverse_api/opencode_engineer.py`
- `reverse-api-engineer/src/reverse_api/opencode_ui.py`
- `reverse-api-engineer/src/reverse_api/pricing.py`
- `reverse-api-engineer/src/reverse_api/session.py`
- `reverse-api-engineer/src/reverse_api/sync.py`
- `reverse-api-engineer/src/reverse_api/tui.py`
- `reverse-api-engineer/src/reverse_api/utils.py`
- `reverse-api-engineer/src/reverse_api/cursor_bridge/.gitignore`
- `reverse-api-engineer/src/reverse_api/cursor_bridge/package-lock.json`
- `reverse-api-engineer/src/reverse_api/cursor_bridge/package.json`
- `reverse-api-engineer/src/reverse_api/cursor_bridge/run.mjs`
- `reverse-api-engineer/src/reverse_api/prompts/__init__.py`
- `reverse-api-engineer/src/reverse_api/prompts/auto/system.md`
- `reverse-api-engineer/src/reverse_api/prompts/auto/user_chrome_mcp.md`
- `reverse-api-engineer/src/reverse_api/prompts/auto/user_playwright.md`
- `reverse-api-engineer/src/reverse_api/prompts/chat/system.md`
- `reverse-api-engineer/src/reverse_api/prompts/collector/system.md`
- `reverse-api-engineer/src/reverse_api/prompts/collector/user.md`
- `reverse-api-engineer/src/reverse_api/prompts/engineer/system.md`
- `reverse-api-engineer/src/reverse_api/prompts/engineer/user.md`
- `reverse-api-engineer/src/reverse_api/prompts/partials/_docs_instructions.md`
- `reverse-api-engineer/src/reverse_api/prompts/partials/_language_javascript.md`
- `reverse-api-engineer/src/reverse_api/prompts/partials/_language_python.md`
- `reverse-api-engineer/src/reverse_api/prompts/partials/_language_typescript.md`


# Skill Security Review - content-generation 1.0.0

**Scan Date:** 2026-05-21T00:00:34.403164
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/content-generation`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** content-generation
- **Version:** 1.0.0
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 3
- **Scripts:** 0
- **Total Lines:** 385

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - Content Marketing 1.0.0

**Scan Date:** 2026-05-21T00:00:34.404762
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/content-marketing`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** Content Marketing
- **Version:** 1.0.0
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 7
- **Scripts:** 0
- **Total Lines:** 454

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `funnels.md`
- `memory-template.md`
- `repurposing.md`
- `setup.md`
- `.clawhub/origin.json`


# Skill Security Review - corpusgraph unknown

**Scan Date:** 2026-05-21T00:00:34.407144
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/corpusgraph`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** corpusgraph
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 5
- **Scripts:** 0
- **Total Lines:** 240

## Findings

No security issues detected.

## Files Scanned

- `README.md`
- `skill.json`
- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - social-poster unknown

**Scan Date:** 2026-05-21T00:00:34.409909
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/cross-poster`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** social-poster
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 3
- **Scripts:** 0
- **Total Lines:** 145

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - daily-intel-brief unknown

**Scan Date:** 2026-05-21T00:00:34.410980
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/daily-intel-brief`

## Verdict

**REJECT** - Found 2 critical issue(s): credential_paths

## Metadata

- **Name:** daily-intel-brief
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 21
- **Scripts:** 6
- **Total Lines:** 4829

## Findings

Found **11** potential issue(s):

### bulk_env_access (high)

- **File:** `scripts/build_pdf.py` line 330
- **Description:** Bulk access to all environment variables - likely exfiltration
- **Recommendation:** REJECT - review carefully for data theft
- **Code:** `env = dict(os.environ)`

### env_scraping (medium)

- **File:** `scripts/build_visuals.py` line 152
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `token = os.environ.get("MAPBOX_TOKEN")`

### env_scraping (medium)

- **File:** `scripts/collect.py` line 696
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `brave_key = os.environ.get("BRAVE_API_KEY", "")`

### credential_paths (critical)

- **File:** `scripts/collect.py` line 510
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `# Load .env for BRAVE_API_KEY and other secrets`

### credential_paths (critical)

- **File:** `scripts/collect.py` line 511
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `_env = pathlib.Path("/home/ubuntu/.openclaw/workspace/.env")`

### env_scraping (medium)

- **File:** `scripts/orchestrate.py` line 57
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]`

### env_scraping (medium)

- **File:** `scripts/orchestrate.py` line 65
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `if not os.environ.get(k):`

### env_scraping (medium)

- **File:** `scripts/orchestrate.py` line 548
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `if os.environ.get("AGENTMAIL_API_KEY"):`

### env_scraping (medium)

- **File:** `scripts/analyze.py` line 35
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `DEEPSEEK_BASE = os.environ.get("DEEPSEEK_BASE", "https://api.deepseek.com")`

### env_scraping (medium)

- **File:** `scripts/analyze.py` line 124
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `api_key = _os.environ.get("OPENROUTER_API_KEY")`

### env_scraping (medium)

- **File:** `scripts/analyze.py` line 134
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `api_key = _os.environ.get("DEEPSEEK_API_KEY")`

## Files Scanned

- `INSTALL.sh`
- `README.md`
- `SKILL.md`
- `_meta.json`
- `agents/analyst.md`
- `agents/collector.md`
- `agents/visuals.md`
- `playbooks/daily-cadence.md`
- `playbooks/escalation-criteria.md`
- `references/deepseek-prompts.md`
- `references/product-template.md`
- `references/regions.json`
- `references/visual-spec.md`
- `scripts/build_pdf.py`
- `scripts/build_visuals.py`
- `scripts/collect.py`
- `scripts/orchestrate.py`
- `scripts/analyze.py.bak`
- `scripts/analyze.py`
- `templates/daily-product.html`
- `templates/daily-product.md`


# Skill Security Review - Data Analysis 1.0.2

**Scan Date:** 2026-05-21T00:00:34.465760
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/data-analysis`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** Data Analysis
- **Version:** 1.0.2
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 8
- **Scripts:** 0
- **Total Lines:** 607

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `chart-selection.md`
- `decision-briefs.md`
- `metric-contracts.md`
- `pitfalls.md`
- `techniques.md`
- `.clawhub/origin.json`


# Skill Security Review - data-charts-visualization unknown

**Scan Date:** 2026-05-21T00:00:34.468964
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/data-charts-visualization`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** data-charts-visualization
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 19
- **Scripts:** 0
- **Total Lines:** 2512

## Findings

No security issues detected.

## Files Scanned

- `package.json`
- `README.md`
- `SKILL.md`
- `_meta.json`
- `agents/openai.yaml`
- `config/area_style.json`
- `config/bar_style.json`
- `config/dual_axis_style.json`
- `config/funnel_style.json`
- `config/gauge_style.json`
- `config/line_style.json`
- `config/pie_style.json`
- `config/radar_style.json`
- `config/README.md`
- `config/scatter_style.json`
- `references/chart-selection-and-variants.md`
- `references/cli-and-config.md`
- `references/config-page-handoff.md`
- `.clawhub/origin.json`


# Skill Security Review - data-visualization-studio unknown

**Scan Date:** 2026-05-21T00:00:34.478576
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/data-visualization-studio`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** data-visualization-studio
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 5
- **Scripts:** 1
- **Total Lines:** 352

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`
- `references/visualization_types.md`
- `scripts/visualize_data.py`


# Skill Security Review - genviral unknown

**Scan Date:** 2026-05-21T00:00:34.482323
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/genviral`

## Verdict

**REJECT** - Found 2 critical issue(s): credential_paths

## Metadata

- **Name:** genviral
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 34
- **Scripts:** 2
- **Total Lines:** 8313

## Findings

Found **2** potential issue(s):

### credential_paths (critical)

- **File:** `scripts/genviral.sh` line 192
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `[[ -f "${HOME}/.config/env/global.env" ]] && source "${HOME}/.config/env/global.env" 2>/dev/null || true`

### credential_paths (critical)

- **File:** `scripts/genviral.sh` line 219
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `die "GENVIRAL_API_KEY is not set.\n  Set it via: export GENVIRAL_API_KEY=\"your_public_id.your_secret\"\n  Or add to ~/.config/env/global.env"`

## Files Scanned

- `defaults.yaml`
- `README.md`
- `SKILL.md`
- `_meta.json`
- `docs/setup.md`
- `scripts/genviral.sh`
- `scripts/update-skill.sh`
- `.clawhub/origin.json`
- `docs/api/accounts-files.md`
- `docs/api/analytics.md`
- `docs/api/errors.md`
- `docs/api/packs.md`
- `docs/api/pipeline.md`
- `docs/api/posts.md`
- `docs/api/slideshows.md`
- `docs/api/studio.md`
- `docs/api/subscription.md`
- `docs/api/templates.md`
- `docs/prompts/hooks.md`
- `docs/prompts/slideshow.md`
- `docs/references/analytics-loop.md`
- `docs/references/competitor-research.md`
- `workspace/content/calendar.json`
- `workspace/content/scratchpad.md`
- `workspace/context/brand-voice.md`
- `workspace/context/niche-research.md`
- `workspace/context/product.md`
- `workspace/hooks/formulas.md`
- `workspace/hooks/library.json`
- `workspace/performance/competitor-insights.md`
- `workspace/performance/hook-tracker.json`
- `workspace/performance/insights.md`
- `workspace/performance/log.json`
- `workspace/performance/weekly-review.md`


# Skill Security Review - geopolitics-expert unknown

**Scan Date:** 2026-05-21T00:00:34.533998
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/geopolitics-expert`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** geopolitics-expert
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 4
- **Scripts:** 0
- **Total Lines:** 279

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `references/frameworks.md`
- `.clawhub/origin.json`


# Skill Security Review - geospatial-osint unknown

**Scan Date:** 2026-05-21T00:00:34.535834
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/geospatial-osint`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** geospatial-osint
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 8
- **Scripts:** 0
- **Total Lines:** 899

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `references/adsb-api.md`
- `references/cesium-basics.md`
- `references/effects.md`
- `references/rendering-stack.md`
- `references/satellite-passes.md`
- `.clawhub/origin.json`


# Skill Security Review - graph-analysis unknown

**Scan Date:** 2026-05-21T00:00:34.539434
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/graph-analysis`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** graph-analysis
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 3
- **Scripts:** 0
- **Total Lines:** 239

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - indicators-and-warnings unknown

**Scan Date:** 2026-05-21T00:00:34.540628
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/indicators-and-warnings`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** indicators-and-warnings
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 2
- **Scripts:** 0
- **Total Lines:** 80

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`


# Skill Security Review - landing-page-generator unknown

**Scan Date:** 2026-05-21T00:00:34.541363
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/landing-page-generator`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** landing-page-generator
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 5
- **Scripts:** 2
- **Total Lines:** 534

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`
- `scripts/__init__.py`
- `scripts/generate_landing.py`


# Skill Security Review - landing-page-roast unknown

**Scan Date:** 2026-05-21T00:00:34.545776
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/landing-page-roast`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** landing-page-roast
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 3
- **Scripts:** 0
- **Total Lines:** 59

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - unknown unknown

**Scan Date:** 2026-05-21T00:00:34.546629
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/ldap7`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** unknown
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** False
- **Files:** 1
- **Scripts:** 0
- **Total Lines:** 96

## Findings

No security issues detected.

## Files Scanned

- `skill.md`


# Skill Security Review - mapbox-data-visualization-patterns unknown

**Scan Date:** 2026-05-21T00:00:34.547644
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/mapbox-data-visualization-patterns`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** mapbox-data-visualization-patterns
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 11
- **Scripts:** 0
- **Total Lines:** 1744

## Findings

No security issues detected.

## Files Scanned

- `AGENTS.md`
- `SKILL.md`
- `_meta.json`
- `evals/evals.json`
- `references/3d-extrusions.md`
- `references/animation.md`
- `references/circles-lines.md`
- `references/clustering.md`
- `references/legends-use-cases.md`
- `references/performance.md`
- `.clawhub/origin.json`


# Skill Security Review - mapbox-geospatial-operations unknown

**Scan Date:** 2026-05-21T00:00:34.553289
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/mapbox-geospatial-operations`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** mapbox-geospatial-operations
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 4
- **Scripts:** 0
- **Total Lines:** 516

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `evals/evals.json`
- `.clawhub/origin.json`


# Skill Security Review - unknown unknown

**Scan Date:** 2026-05-21T00:00:34.556105
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/mermaid`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** unknown
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 6
- **Scripts:** 1
- **Total Lines:** 357

## Findings

No security issues detected.

## Files Scanned

- `generate-test.sh`
- `package.json`
- `README.md`
- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - News 1.0.1

**Scan Date:** 2026-05-21T00:00:34.558700
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/news`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** News
- **Version:** 1.0.1
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 3
- **Scripts:** 0
- **Total Lines:** 98

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - Newsletter unknown

**Scan Date:** 2026-05-21T00:00:34.559851
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/newsletter`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** Newsletter
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 3
- **Scripts:** 0
- **Total Lines:** 136

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - newsletter-creation-curation unknown

**Scan Date:** 2026-05-21T00:00:34.560935
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/newsletter-creation-curation`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** newsletter-creation-curation
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 4
- **Scripts:** 0
- **Total Lines:** 2039

## Findings

No security issues detected.

## Files Scanned

- `README.md`
- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - oraclaw-graph 1.0.0

**Scan Date:** 2026-05-21T00:00:34.567039
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/oraclaw-graph`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** oraclaw-graph
- **Version:** 1.0.0
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 3
- **Scripts:** 0
- **Total Lines:** 69

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - pdf-report 1.0.1

**Scan Date:** 2026-05-21T00:00:34.567921
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/pdf-report`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** pdf-report
- **Version:** 1.0.1
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 5
- **Scripts:** 1
- **Total Lines:** 379

## Findings

Found **1** potential issue(s):

### env_scraping (medium)

- **File:** `scripts/render_pdf.py` line 17
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `env_root = os.environ.get("OPENCLAW_WORKSPACE")`

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`
- `scripts/render_pdf.py`
- `templates/report.html`


# Skill Security Review - polymarket-trader unknown

**Scan Date:** 2026-05-21T00:00:34.572716
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/polymarket-trader`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** polymarket-trader
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 5
- **Scripts:** 2
- **Total Lines:** 594

## Findings

Found **10** potential issue(s):

### env_scraping (medium)

- **File:** `scripts/research.py` line 18
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `GAMMA = os.environ.get("POLYMARKET_GAMMA_HOST", "https://gamma-api.polymarket.com").rstrip("/")`

### env_scraping (medium)

- **File:** `scripts/research.py` line 19
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `CLOB = os.environ.get("POLYMARKET_CLOB_HOST", "https://clob.polymarket.com").rstrip("/")`

### env_scraping (medium)

- **File:** `scripts/trade.py` line 19
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `HOST = os.environ.get("POLYMARKET_CLOB_HOST", "https://clob.polymarket.com").rstrip("/")`

### env_scraping (medium)

- **File:** `scripts/trade.py` line 20
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `CHAIN_ID = int(os.environ.get("POLYMARKET_CHAIN_ID", "137"))`

### env_scraping (medium)

- **File:** `scripts/trade.py` line 114
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `value = os.environ.get(name)`

### env_scraping (medium)

- **File:** `scripts/trade.py` line 128
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `signature_type = int(os.environ.get("POLYMARKET_SIGNATURE_TYPE", "2"))`

### env_scraping (medium)

- **File:** `scripts/trade.py` line 129
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `funder = os.environ.get("POLYMARKET_FUNDER")`

### env_scraping (medium)

- **File:** `scripts/trade.py` line 135
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `api_key = os.environ.get("POLYMARKET_CLOB_API_KEY")`

### env_scraping (medium)

- **File:** `scripts/trade.py` line 136
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `secret = os.environ.get("POLYMARKET_CLOB_SECRET")`

### env_scraping (medium)

- **File:** `scripts/trade.py` line 137
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `passphrase = os.environ.get("POLYMARKET_CLOB_PASS_PHRASE")`

## Files Scanned

- `README.md`
- `SKILL.md`
- `scripts/research.py`
- `scripts/trade.py`
- `templates/trade-plan.example.json`


# Skill Security Review - unknown unknown

**Scan Date:** 2026-05-21T00:00:34.581283
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/quick-translation`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** unknown
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 3
- **Scripts:** 0
- **Total Lines:** 125

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - My skill unknown

**Scan Date:** 2026-05-21T00:00:34.582139
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/recursive-knowledge-miner`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** My skill
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 3
- **Scripts:** 0
- **Total Lines:** 82

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - unknown unknown

**Scan Date:** 2026-05-21T00:00:34.583164
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/renderers`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** unknown
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** False
- **Files:** 2
- **Scripts:** 2
- **Total Lines:** 45

## Findings

No security issues detected.

## Files Scanned

- `__init__.py`
- `intel_svg_renderer.py`


# Skill Security Review - sat-toolkit unknown

**Scan Date:** 2026-05-21T00:00:34.584467
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/sat-toolkit`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** sat-toolkit
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 2
- **Scripts:** 0
- **Total Lines:** 120

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`


# Skill Security Review - scraper unknown

**Scan Date:** 2026-05-21T00:00:34.585318
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/scraper`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** scraper
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 11
- **Scripts:** 6
- **Total Lines:** 325

## Findings

No security issues detected.

## Files Scanned

- `skill.json`
- `SKILL.md`
- `_meta.json`
- `references/safety.md`
- `scripts/extract_text.py`
- `scripts/fetch_page.py`
- `scripts/init_storage.py`
- `scripts/list_jobs.py`
- `scripts/save_output.py`
- `.clawhub/origin.json`
- `scripts/lib/storage.py`


# Skill Security Review - unknown unknown

**Scan Date:** 2026-05-21T00:00:34.590560
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/skill-generator`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** unknown
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 2
- **Scripts:** 1
- **Total Lines:** 253

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `scripts/generate_skill.py`


# Skill Security Review - skill-stripe-monitor 1.0.2

**Scan Date:** 2026-05-21T00:00:34.593292
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/skill-stripe-monitor`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** skill-stripe-monitor
- **Version:** 1.0.2
- **Author:** ordo-tech
- **Has SKILL.md:** True
- **Files:** 5
- **Scripts:** 0
- **Total Lines:** 782

## Findings

No security issues detected.

## Files Scanned

- `README.md`
- `SKILL-FULL.md`
- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - social-intelligence unknown

**Scan Date:** 2026-05-21T00:00:34.596226
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/social-intelligence`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** social-intelligence
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 3
- **Scripts:** 0
- **Total Lines:** 139

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - social-media-agent unknown

**Scan Date:** 2026-05-21T00:00:34.597370
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/social-media-agent`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** social-media-agent
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 4
- **Scripts:** 0
- **Total Lines:** 229

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`
- `references/content-templates.md`


# Skill Security Review - Social Media Scheduler unknown

**Scan Date:** 2026-05-21T00:00:34.598798
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/social-media-scheduler`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** Social Media Scheduler
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 4
- **Scripts:** 0
- **Total Lines:** 94

## Findings

No security issues detected.

## Files Scanned

- `README.md`
- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - SocialPack Multi-Platform Social Media Generator 1.0.0

**Scan Date:** 2026-05-21T00:00:34.599894
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/social-pack`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** SocialPack Multi-Platform Social Media Generator
- **Version:** 1.0.0
- **Author:** @TheShadowRose
- **Has SKILL.md:** True
- **Files:** 6
- **Scripts:** 1
- **Total Lines:** 278

## Findings

No security issues detected.

## Files Scanned

- `LICENSE.md`
- `README.md`
- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`
- `src/social-pack.js`


# Skill Security Review - social-post 1.4.0

**Scan Date:** 2026-05-21T00:00:34.602261
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/social-post`

## Verdict

**REJECT** - Found 36 critical issue(s): credential_paths

## Metadata

- **Name:** social-post
- **Version:** 1.4.0
- **Author:** 0xdas
- **Has SKILL.md:** True
- **Files:** 14
- **Scripts:** 9
- **Total Lines:** 2598

## Findings

Found **36** potential issue(s):

### credential_paths (critical)

- **File:** `CHANGELOG.md` line 42
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- Support for custom credential prefixes in `.env` file`

### credential_paths (critical)

- **File:** `CHANGELOG.md` line 143
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- ❌ Fixed `.env` file parsing error (quoted mnemonic)`

### credential_paths (critical)

- **File:** `CHANGELOG.md` line 175
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- Automatic credential loading from `.env` and Farcaster credentials file`

### credential_paths (critical)

- **File:** `README.md` line 44
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `| **X/Twitter** | Pay-per-use (consumption-based) | `~/.openclaw/.env` | 5-10 min |`

### credential_paths (critical)

- **File:** `README.md` line 91
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `**Step 3: Add to .env file**`

### credential_paths (critical)

- **File:** `README.md` line 92
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `Location: `/home/phan_harry/.openclaw/.env``

### credential_paths (critical)

- **File:** `README.md` line 180
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `grep "^X_CONSUMER_KEY" ~/.openclaw/.env`

### credential_paths (critical)

- **File:** `README.md` line 308
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `1. Check `.env` file exists: `ls -la ~/.openclaw/.env``

### credential_paths (critical)

- **File:** `README.md` line 311
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `grep "^X_" ~/.openclaw/.env`

### credential_paths (critical)

- **File:** `README.md` line 314
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `4. Check file permissions: `chmod 600 ~/.openclaw/.env``

### credential_paths (critical)

- **File:** `SKILL.md` line 43
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `**Required credentials** (stored in `/home/phan_harry/.openclaw/.env`):`

### credential_paths (critical)

- **File:** `SKILL.md` line 76
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `4. **Add to .env file**`

### credential_paths (critical)

- **File:** `SKILL.md` line 78
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `echo "X_CONSUMER_KEY=xxx" >> ~/.openclaw/.env`

### credential_paths (critical)

- **File:** `SKILL.md` line 79
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `echo "X_CONSUMER_SECRET=xxx" >> ~/.openclaw/.env`

### credential_paths (critical)

- **File:** `SKILL.md` line 80
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `echo "X_ACCESS_TOKEN=xxx" >> ~/.openclaw/.env`

### credential_paths (critical)

- **File:** `SKILL.md` line 81
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `echo "X_ACCESS_TOKEN_SECRET=xxx" >> ~/.openclaw/.env`

### credential_paths (critical)

- **File:** `SKILL.md` line 98
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `echo "MYACCOUNT_API_KEY=xxx" >> ~/.openclaw/.env`

### credential_paths (critical)

- **File:** `SKILL.md` line 99
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `echo "MYACCOUNT_API_KEY_SECRET=xxx" >> ~/.openclaw/.env`

### credential_paths (critical)

- **File:** `SKILL.md` line 100
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `echo "MYACCOUNT_ACCESS_TOKEN=xxx" >> ~/.openclaw/.env`

### credential_paths (critical)

- **File:** `SKILL.md` line 101
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `echo "MYACCOUNT_ACCESS_TOKEN_SECRET=xxx" >> ~/.openclaw/.env`

### credential_paths (critical)

- **File:** `SKILL.md` line 179
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- ⚠️ `.env` file should have `600` permissions (read/write owner only)`

### credential_paths (critical)

- **File:** `SKILL.md` line 253
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- `--account <name>` - Twitter account to use (lowercase prefix from .env)`

### credential_paths (critical)

- **File:** `SKILL.md` line 266
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- `--account <name>` - Twitter account to use (lowercase prefix from .env)`

### credential_paths (critical)

- **File:** `SKILL.md` line 362
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- Twitter credentials in `.env` (X_CONSUMER_KEY, X_CONSUMER_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)`

### credential_paths (critical)

- **File:** `lib/farcaster.sh` line 30
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `const wallet = new Wallet(process.env.PRIVATE_KEY, baseProvider);`

### credential_paths (critical)

- **File:** `lib/farcaster.sh` line 31
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `const signerBytes = Buffer.from(process.env.SIGNER_PRIVATE_KEY, 'hex');`

### credential_paths (critical)

- **File:** `lib/farcaster.sh` line 33
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `const fid = parseInt(process.env.FID);`

### credential_paths (critical)

- **File:** `lib/farcaster.sh` line 34
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `const parentHashBytes = Buffer.from(process.env.PARENT_HASH.replace('0x', ''), 'hex');`

### credential_paths (critical)

- **File:** `lib/farcaster.sh` line 117
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `const wallet = new Wallet(process.env.PRIVATE_KEY, baseProvider);`

### credential_paths (critical)

- **File:** `lib/farcaster.sh` line 118
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `const signerBytes = Buffer.from(process.env.SIGNER_PRIVATE_KEY, 'hex');`

### credential_paths (critical)

- **File:** `lib/farcaster.sh` line 120
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `const fid = parseInt(process.env.FID);`

### credential_paths (critical)

- **File:** `lib/farcaster.sh` line 121
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `const imageUrl = process.env.IMAGE_URL;`

### credential_paths (critical)

- **File:** `lib/farcaster.sh` line 131
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `if (process.env.PARENT_HASH) {`

### credential_paths (critical)

- **File:** `lib/farcaster.sh` line 132
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `const parentHashBytes = Buffer.from(process.env.PARENT_HASH.replace('0x', ''), 'hex');`

### credential_paths (critical)

- **File:** `lib/twitter.sh` line 8
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `source /home/phan_harry/.openclaw/.env`

### credential_paths (critical)

- **File:** `scripts/reply.sh` line 272
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `source /home/phan_harry/.openclaw/.env`

## Files Scanned

- `CHANGELOG.md`
- `README.md`
- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`
- `lib/farcaster.sh`
- `lib/links.sh`
- `lib/threads.sh`
- `lib/twitter.sh`
- `lib/validate.sh`
- `lib/variation.sh`
- `scripts/check-balance.sh`
- `scripts/post.sh`
- `scripts/reply.sh`


# Skill Security Review - unknown unknown

**Scan Date:** 2026-05-21T00:00:34.618025
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/social-poster`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** unknown
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 4
- **Scripts:** 0
- **Total Lines:** 52

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`
- `scripts/post.mjs`


# Skill Security Review - source-evaluation unknown

**Scan Date:** 2026-05-21T00:00:34.618967
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/source-evaluation`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** source-evaluation
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 2
- **Scripts:** 0
- **Total Lines:** 106

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`


# Skill Security Review - unknown unknown

**Scan Date:** 2026-05-21T00:00:34.619820
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/spanish-pdf-ocr`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** unknown
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 2
- **Scripts:** 1
- **Total Lines:** 69

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `scripts/run.py`


# Skill Security Review - Threat Intelligence Aggregator unknown

**Scan Date:** 2026-05-21T00:00:34.620757
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/threat-intel-aggregator`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** Threat Intelligence Aggregator
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 4
- **Scripts:** 0
- **Total Lines:** 238

## Findings

No security issues detected.

## Files Scanned

- `openapi.json`
- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - unknown unknown

**Scan Date:** 2026-05-21T00:00:34.622136
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/trevor`

## Verdict

**REJECT** - Found 1 critical issue(s): credential_paths

## Metadata

- **Name:** unknown
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** False
- **Files:** 3
- **Scripts:** 0
- **Total Lines:** 127

## Findings

Found **1** potential issue(s):

### credential_paths (critical)

- **File:** `publishing/build-agent-brief.md` line 40
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `- Moltbook API key must be in .env or environment`

## Files Scanned

- `publishing/build-agent-brief.md`
- `publishing/build-gsib-agent-brief-json.md`
- `publishing/daily-4-briefings.md`


# Skill Security Review - translate unknown

**Scan Date:** 2026-05-21T00:00:34.623331
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/universal-translate`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** translate
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 3
- **Scripts:** 0
- **Total Lines:** 126

## Findings

No security issues detected.

## Files Scanned

- `SKILL.md`
- `_meta.json`
- `.clawhub/origin.json`


# Skill Security Review - visual_production unknown

**Scan Date:** 2026-05-21T00:00:34.624352
**Skill Path:** `/home/ubuntu/.openclaw/workspace/skills/visual_production`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** visual_production
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 17
- **Scripts:** 16
- **Total Lines:** 2317

## Findings

Found **1** potential issue(s):

### env_scraping (medium)

- **File:** `visual_production/pipeline.py` line 233
- **Description:** Reads environment variables - could access secrets
- **Recommendation:** Verify only expected env vars are read, not bulk scraping
- **Code:** `api_key = os.environ.get("OPENROUTER_API_KEY")`

## Files Scanned

- `__init__.py`
- `nano_prompts.py`
- `pipeline.py`
- `prompt_builder.py`
- `quality_gate.py`
- `router.py`
- `schemas.py`
- `SKILL.md`
- `test_pipeline.py`
- `scripts/format_magazine.py`
- `visual_production/nano_prompts.py`
- `visual_production/prompt_builder.py`
- `visual_production/quality_gate.py`
- `visual_production/router.py`
- `visual_production/schemas.py`
- `visual_production/__init__.py`
- `visual_production/pipeline.py`


# Skill Security Review - 1password unknown

**Scan Date:** 2026-05-21T00:00:34.655858
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/1password`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** 1password
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - apple-notes unknown

**Scan Date:** 2026-05-21T00:00:34.656214
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/apple-notes`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** apple-notes
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - apple-reminders unknown

**Scan Date:** 2026-05-21T00:00:34.656428
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/apple-reminders`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** apple-reminders
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - bear-notes unknown

**Scan Date:** 2026-05-21T00:00:34.656631
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/bear-notes`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** bear-notes
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - blogwatcher unknown

**Scan Date:** 2026-05-21T00:00:34.656832
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/blogwatcher`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** blogwatcher
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - blucli unknown

**Scan Date:** 2026-05-21T00:00:34.657038
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/blucli`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** blucli
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - bluebubbles unknown

**Scan Date:** 2026-05-21T00:00:34.657239
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/bluebubbles`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** bluebubbles
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - camsnap unknown

**Scan Date:** 2026-05-21T00:00:34.657430
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/camsnap`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** camsnap
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - unknown unknown

**Scan Date:** 2026-05-21T00:00:34.657627
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/canvas`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** unknown
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - clawhub unknown

**Scan Date:** 2026-05-21T00:00:34.657811
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/clawhub`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** clawhub
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - coding-agent unknown

**Scan Date:** 2026-05-21T00:00:34.658010
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/coding-agent`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** coding-agent
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - discord unknown

**Scan Date:** 2026-05-21T00:00:34.658221
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/discord`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** discord
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - eightctl unknown

**Scan Date:** 2026-05-21T00:00:34.658425
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/eightctl`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** eightctl
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - gemini unknown

**Scan Date:** 2026-05-21T00:00:34.658708
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/gemini`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** gemini
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - gh-issues unknown

**Scan Date:** 2026-05-21T00:00:34.659012
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/gh-issues`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** gh-issues
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - gifgrep unknown

**Scan Date:** 2026-05-21T00:00:34.659373
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/gifgrep`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** gifgrep
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - github unknown

**Scan Date:** 2026-05-21T00:00:34.659698
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/github`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** github
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - gog unknown

**Scan Date:** 2026-05-21T00:00:34.660006
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/gog`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** gog
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - goplaces unknown

**Scan Date:** 2026-05-21T00:00:34.660308
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/goplaces`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** goplaces
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - healthcheck unknown

**Scan Date:** 2026-05-21T00:00:34.660618
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/healthcheck`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** healthcheck
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - himalaya unknown

**Scan Date:** 2026-05-21T00:00:34.660907
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/himalaya`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** himalaya
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - imsg unknown

**Scan Date:** 2026-05-21T00:00:34.661280
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/imsg`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** imsg
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - mcporter unknown

**Scan Date:** 2026-05-21T00:00:34.661607
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/mcporter`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** mcporter
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - model-usage unknown

**Scan Date:** 2026-05-21T00:00:34.661924
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/model-usage`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** model-usage
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - nano-pdf unknown

**Scan Date:** 2026-05-21T00:00:34.662248
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/nano-pdf`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** nano-pdf
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - node-connect unknown

**Scan Date:** 2026-05-21T00:00:34.662527
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/node-connect`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** node-connect
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - notion unknown

**Scan Date:** 2026-05-21T00:00:34.662799
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/notion`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** notion
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - obsidian unknown

**Scan Date:** 2026-05-21T00:00:34.663009
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/obsidian`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** obsidian
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - openai-whisper unknown

**Scan Date:** 2026-05-21T00:00:34.663209
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/openai-whisper`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** openai-whisper
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - openai-whisper-api unknown

**Scan Date:** 2026-05-21T00:00:34.663409
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/openai-whisper-api`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** openai-whisper-api
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - openhue unknown

**Scan Date:** 2026-05-21T00:00:34.663655
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/openhue`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** openhue
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - oracle unknown

**Scan Date:** 2026-05-21T00:00:34.663852
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/oracle`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** oracle
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - ordercli unknown

**Scan Date:** 2026-05-21T00:00:34.664057
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/ordercli`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** ordercli
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - peekaboo unknown

**Scan Date:** 2026-05-21T00:00:34.664254
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/peekaboo`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** peekaboo
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - sag unknown

**Scan Date:** 2026-05-21T00:00:34.664447
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/sag`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** sag
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - session-logs unknown

**Scan Date:** 2026-05-21T00:00:34.664639
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/session-logs`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** session-logs
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - sherpa-onnx-tts unknown

**Scan Date:** 2026-05-21T00:00:34.664839
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/sherpa-onnx-tts`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** sherpa-onnx-tts
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - skill-creator unknown

**Scan Date:** 2026-05-21T00:00:34.665100
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/skill-creator`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** skill-creator
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - slack unknown

**Scan Date:** 2026-05-21T00:00:34.665362
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/slack`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** slack
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - songsee unknown

**Scan Date:** 2026-05-21T00:00:34.665549
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/songsee`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** songsee
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - sonoscli unknown

**Scan Date:** 2026-05-21T00:00:34.665745
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/sonoscli`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** sonoscli
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - spotify-player unknown

**Scan Date:** 2026-05-21T00:00:34.665941
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/spotify-player`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** spotify-player
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - summarize unknown

**Scan Date:** 2026-05-21T00:00:34.666146
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/summarize`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** summarize
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - taskflow unknown

**Scan Date:** 2026-05-21T00:00:34.666351
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/taskflow`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** taskflow
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - taskflow-inbox-triage unknown

**Scan Date:** 2026-05-21T00:00:34.666600
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/taskflow-inbox-triage`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** taskflow-inbox-triage
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - things-mac unknown

**Scan Date:** 2026-05-21T00:00:34.666791
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/things-mac`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** things-mac
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - tmux unknown

**Scan Date:** 2026-05-21T00:00:34.666996
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/tmux`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** tmux
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - trello unknown

**Scan Date:** 2026-05-21T00:00:34.667240
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/trello`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** trello
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - video-frames unknown

**Scan Date:** 2026-05-21T00:00:34.667480
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/video-frames`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** video-frames
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - voice-call unknown

**Scan Date:** 2026-05-21T00:00:34.667875
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/voice-call`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** voice-call
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - wacli unknown

**Scan Date:** 2026-05-21T00:00:34.668153
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/wacli`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** wacli
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - weather unknown

**Scan Date:** 2026-05-21T00:00:34.668455
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/weather`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** weather
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned



# Skill Security Review - xurl unknown

**Scan Date:** 2026-05-21T00:00:34.668788
**Skill Path:** `/usr/lib/node_modules/openclaw/skills/xurl`

## Verdict

**APPROVED** - No critical or high-severity issues detected

## Metadata

- **Name:** xurl
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** True
- **Files:** 0
- **Scripts:** 0
- **Total Lines:** 0

## Findings

No security issues detected.

## Files Scanned

