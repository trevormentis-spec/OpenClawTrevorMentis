# 🔒 Daily Skill Scanner Audit Report
**Generated:** 2026-05-15 00:04:05 UTC

## Executive Summary

- **Skills scanned:** 79
- **Total files:** 71
- **Total lines of code:** 11,705
- **Total findings:** 18
- **Approved:** 71
- **Caution:** 1
- **Rejected:** 7

### Severity Breakdown

| Severity | Count |
|----------|-------|
| 🔴 Critical | 15 |
| 🟠 High | 2 |
| 🟡 Medium | 1 |
| 🔵 Low | 0 |
| ⚪ Info | 0 |

### 🚫 Rejected Skills

- **api-gateway**
- **gmail**
- **gog**
- **skill-scanner**
- **stripe**
- **video-translation**
- **whatsapp-business**

### ⚠️ Skills Requiring Caution

- **trevor-methodology**

## Detailed Findings by Skill

### api-gateway (v1.0)
- **Verdict:** REJECT
- **Reason:** Found 1 critical issue(s): credential_paths
- **Files:** 1 | **Lines:** 639

- 🔴 **[CRITICAL]** `credential_paths` in `SKILL.md`:539
  - *Accesses sensitive credential locations*
  - Recommendation: REJECT unless explicitly justified

### gmail (v1.0)
- **Verdict:** REJECT
- **Reason:** Found 1 critical issue(s): credential_paths
- **Files:** 1 | **Lines:** 340

- 🔴 **[CRITICAL]** `credential_paths` in `SKILL.md`:267
  - *Accesses sensitive credential locations*
  - Recommendation: REJECT unless explicitly justified

### gog (vunknown)
- **Verdict:** REJECT
- **Reason:** Found 2 critical issue(s): credential_paths
- **Files:** 4 | **Lines:** 90

- 🔴 **[CRITICAL]** `credential_paths` in `SKILL.md`:23
  - *Accesses sensitive credential locations*
  - Recommendation: REJECT unless explicitly justified

- 🔴 **[CRITICAL]** `credential_paths` in `SKILL.md`:24
  - *Accesses sensitive credential locations*
  - Recommendation: REJECT unless explicitly justified

- 🟡 **[MEDIUM]** `http_post_external` in `config/exchange.py`:16
  - *HTTP POST to external endpoint - could exfiltrate data*
  - Recommendation: Verify destination URL is expected and documented

### skill-scanner (vunknown)
- **Verdict:** REJECT
- **Reason:** Found 8 critical issue(s): base64_decode_exec, systemd_modify, credential_paths, crypto_miner, reverse_shell
- **Files:** 5 | **Lines:** 955

- 🔴 **[CRITICAL]** `credential_paths` in `README.md`:155
  - *Accesses sensitive credential locations*
  - Recommendation: REJECT unless explicitly justified

- 🔴 **[CRITICAL]** `crypto_miner` in `README.md`:9
  - *Cryptocurrency mining indicators*
  - Recommendation: REJECT - this is cryptojacking malware

- 🔴 **[CRITICAL]** `crypto_miner` in `README.md`:158
  - *Cryptocurrency mining indicators*
  - Recommendation: REJECT - this is cryptojacking malware

- 🔴 **[CRITICAL]** `credential_paths` in `skill_scanner.py`:101
  - *Accesses sensitive credential locations*
  - Recommendation: REJECT unless explicitly justified

- 🟠 **[HIGH]** `crontab_modify` in `skill_scanner.py`:118
  - *Modifies system scheduled tasks*
  - Recommendation: Skills should use Clawdbot cron, not system crontab

- 🔴 **[CRITICAL]** `systemd_modify` in `skill_scanner.py`:126
  - *Creates system services for persistence*
  - Recommendation: REJECT - skills should not create system services

- 🔴 **[CRITICAL]** `crypto_miner` in `skill_scanner.py`:135
  - *Cryptocurrency mining indicators*
  - Recommendation: REJECT - this is cryptojacking malware

- 🔴 **[CRITICAL]** `reverse_shell` in `skill_scanner.py`:161
  - *Reverse shell pattern detected*
  - Recommendation: REJECT - this is a backdoor

- 🔴 **[CRITICAL]** `base64_decode_exec` in `skill_scanner.py`:170
  - *Decodes and executes base64 - classic obfuscation*
  - Recommendation: REJECT - likely hiding malicious code

### stripe (v1.0)
- **Verdict:** REJECT
- **Reason:** Found 1 critical issue(s): credential_paths
- **Files:** 1 | **Lines:** 855

- 🔴 **[CRITICAL]** `credential_paths` in `SKILL.md`:778
  - *Accesses sensitive credential locations*
  - Recommendation: REJECT unless explicitly justified

### trevor-methodology (vunknown)
- **Verdict:** CAUTION
- **Reason:** Found 1 high-severity issue(s): eval_exec
- **Files:** 25 | **Lines:** 4967

- 🟠 **[HIGH]** `eval_exec` in `pipeline/docx-js-template.js`:37
  - *Dynamic code execution - could run arbitrary code*
  - Recommendation: Verify input is sanitized, not user-controlled

### video-translation (vunknown)
- **Verdict:** REJECT
- **Reason:** Found 1 critical issue(s): credential_paths
- **Files:** 3 | **Lines:** 219

- 🔴 **[CRITICAL]** `credential_paths` in `SKILL.md`:90
  - *Accesses sensitive credential locations*
  - Recommendation: REJECT unless explicitly justified

### whatsapp-business (v1.0)
- **Verdict:** REJECT
- **Reason:** Found 1 critical issue(s): credential_paths
- **Files:** 1 | **Lines:** 637

- 🔴 **[CRITICAL]** `credential_paths` in `SKILL.md`:494
  - *Accesses sensitive credential locations*
  - Recommendation: REJECT unless explicitly justified

### ✅ Skills With No Issues

- 1password vunknown — 0 files, 0 lines
- Network Analysis vunknown — 3 files, 313 lines
- answeroverflow vunknown — 1 files, 89 lines
- apple-notes vunknown — 0 files, 0 lines
- apple-reminders vunknown — 0 files, 0 lines
- bear-notes vunknown — 0 files, 0 lines
- blogwatcher vunknown — 0 files, 0 lines
- blucli vunknown — 0 files, 0 lines
- bluebubbles vunknown — 0 files, 0 lines
- camsnap vunknown — 0 files, 0 lines
- claude-code vunknown — 4 files, 85 lines
- clawhub vunknown — 0 files, 0 lines
- coding-agent vunknown — 0 files, 0 lines
- discord vunknown — 0 files, 0 lines
- eightctl vunknown — 0 files, 0 lines
- find-skills vunknown — 1 files, 134 lines
- gemini vunknown — 0 files, 0 lines
- gh-issues vunknown — 0 files, 0 lines
- gifgrep vunknown — 0 files, 0 lines
- github vunknown — 0 files, 0 lines
- gog vunknown — 0 files, 0 lines
- goplaces vunknown — 0 files, 0 lines
- healthcheck vunknown — 0 files, 0 lines
- himalaya vunknown — 0 files, 0 lines
- huggingface-hub vunknown — 1 files, 36 lines
- humanizer v2.1.1 — 1 files, 438 lines
- imsg vunknown — 0 files, 0 lines
- maps vunknown — 1 files, 37 lines
- mcporter vunknown — 0 files, 0 lines
- model-usage vunknown — 0 files, 0 lines
- nano-pdf vunknown — 1 files, 21 lines
- nano-pdf vunknown — 0 files, 0 lines
- node-connect vunknown — 0 files, 0 lines
- notion vunknown — 0 files, 0 lines
- obsidian vunknown — 0 files, 0 lines
- ocr-and-documents vunknown — 4 files, 89 lines
- openai-whisper vunknown — 0 files, 0 lines
- openai-whisper-api vunknown — 0 files, 0 lines
- openhue vunknown — 0 files, 0 lines
- oracle vunknown — 0 files, 0 lines
- ordercli vunknown — 0 files, 0 lines
- peekaboo vunknown — 0 files, 0 lines
- sag vunknown — 0 files, 0 lines
- self-improvement vunknown — 1 files, 648 lines
- session-logs vunknown — 0 files, 0 lines
- sherpa-onnx-tts vunknown — 0 files, 0 lines
- skill-creator vunknown — 0 files, 0 lines
- slack vunknown — 0 files, 0 lines
- songsee vunknown — 0 files, 0 lines
- sonoscli vunknown — 0 files, 0 lines
- spotify-player vunknown — 0 files, 0 lines
- stock-market-pro vunknown — 1 files, 135 lines
- summarize vunknown — 0 files, 0 lines
- taskflow vunknown — 0 files, 0 lines
- taskflow-inbox-triage vunknown — 0 files, 0 lines
- things-mac vunknown — 0 files, 0 lines
- timeline-chart vunknown — 5 files, 340 lines
- tmux vunknown — 0 files, 0 lines
- trello vunknown — 0 files, 0 lines
- unknown vunknown — 1 files, 1 lines
- unknown vunknown — 0 files, 0 lines
- video-frames vunknown — 1 files, 30 lines
- video-frames vunknown — 0 files, 0 lines
- voice-call vunknown — 0 files, 0 lines
- wacli vunknown — 1 files, 73 lines
- wacli vunknown — 0 files, 0 lines
- weather vunknown — 0 files, 0 lines
- web-search-plus vunknown — 1 files, 37 lines
- xurl vunknown — 1 files, 462 lines
- xurl vunknown — 0 files, 0 lines
- youtube-content vunknown — 1 files, 35 lines

---
*Report generated by Daily Skill Scanner Audit cron (2026-05-15 00:04:05 UTC)*