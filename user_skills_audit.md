# Skill Security Review - unknown unknown

**Scan Date:** 2026-04-29T00:01:06.030656
**Skill Path:** `/home/ubuntu/.openclaw/skills`

## Verdict

**REJECT** - Found 14 critical issue(s): base64_decode_exec, credential_paths, reverse_shell, crypto_miner, systemd_modify

## Metadata

- **Name:** unknown
- **Version:** unknown
- **Author:** unknown
- **Has SKILL.md:** False
- **Files:** 60
- **Scripts:** 6
- **Total Lines:** 11124

## Findings

Found **17** potential issue(s):

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

- **File:** `api-gateway/SKILL.md` line 539
- **Description:** Accesses sensitive credential locations
- **Recommendation:** REJECT unless explicitly justified
- **Code:** `'Authorization': `Bearer ${process.env.MATON_API_KEY}``

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

## Files Scanned

- `gmail/SKILL.md`
- `gog-myclaw/SKILL.md`
- `gog-myclaw/_meta.json`
- `self-improving-agent/SKILL.md`
- `api-gateway/SKILL.md`
- `stripe-api/SKILL.md`
- `whatsapp-business/SKILL.md`
- `xurl/SKILL.md`
- `video-frames/SKILL.md`
- `huggingface-hub/SKILL.md`
- `trevor-methodology/SKILL.md`
- `trevor-methodology/sanitize.sh`
- `trevor-methodology/trevor-methodology-sanitized.tar.gz`
- `trevor-methodology/TREVOR-One-Page-Summary.md`
- `find-skills/SKILL.md`
- `humanizer/SKILL.md`
- `stock-market-pro/SKILL.md`
- `nano-pdf/SKILL.md`
- `answeroverflow/SKILL.md`
- `claude-code/README.md`
- `claude-code/SKILL.md`
- `wacli/SKILL.md`
- `web-searchplus/SKILL.md`
- `youtube-content/SKILL.md`
- `maps-new/SKILL.md`
- `ocr-docu/README.md`
- `ocr-docu/SKILL.md`
- `skill-scanner/README.md`
- `skill-scanner/SKILL.md`
- `skill-scanner/_meta.json`
- `skill-scanner/skill_scanner.py`
- `skill-scanner/streamlit_ui.py`
- `gog-myclaw/config/credentials.json`
- `gog-myclaw/config/exchange.py`
- `trevor-methodology/methodology/16-sections.md`
- `trevor-methodology/methodology/6-calibrations.md`
- `trevor-methodology/methodology/sherman-kent-bands.md`
- `trevor-methodology/methodology/nato-admiralty.md`
- `trevor-methodology/methodology/scenario-triage.md`
- `trevor-methodology/methodology/client-threat-matrix-templates.md`
- `trevor-methodology/methodology/actor-mapping.md`
- `trevor-methodology/methodology/hypothesis-archetypes.md`
- `trevor-methodology/methodology/source-acquisition-guide.md`
- `trevor-methodology/methodology/quality-gates.md`
- `trevor-methodology/methodology/11-SATs.md`
- `trevor-methodology/pipeline/docx-js-template.js`
- `trevor-methodology/pipeline/output-format-variants.md`
- `trevor-methodology/pipeline/validate.py`
- `trevor-methodology/verification/phase4-self-test.md`
- `trevor-methodology/verification/phase5-acceptance-demonstrations.md`
- `trevor-methodology/brands/README.md`
- `trevor-methodology/brands/sps-global.json`
- `trevor-methodology/brands/eclipse.json`
- `trevor-methodology/brands/concentric.json`
- `trevor-methodology/brands/neutral.json`
- `trevor-methodology/brands/nova.json`
- `claude-code/references/safety-notes.md`
- `claude-code/references/session-patterns.md`
- `ocr-docu/references/output-schema.md`
- `ocr-docu/references/tooling-matrix.md`