# 🔒 Daily Skill Scanner Audit Report

**Generated:** 2026-05-08 09:01 UTC
**Environment:** OpenClaw | **Scanner:** skill-scanner v1.0

## Executive Summary

| Metric | Count |
|--------|-------|
| Total Skills Scanned | 74 |
| ✅ Approved (clean) | 57 |
| 🟡 Caution (high-severity) | 1 |
| 🔴 Critical (rejected) | 16 |
| Total Findings | 37 |
| ⬆️ Critical Severity | 34 |
| ⬆️ High Severity | 2 |
| ❌ Scan Errors | 0 |

---
## 🔴 CRITICAL - Requires Immediate Review

### api-gateway (user)
**Reason:** Found 1 critical issue(s): credential_paths

### gmail (user)
**Reason:** Found 1 critical issue(s): credential_paths

### gog (user)
**Reason:** Found 2 critical issue(s): credential_paths

### skill-scanner (user)
**Reason:** Found 8 critical issue(s): systemd_modify, base64_decode_exec, crypto_miner, credential_paths, reverse_shell

### stripe (user)
**Reason:** Found 1 critical issue(s): credential_paths

### video-translation (user)
**Reason:** Found 1 critical issue(s): credential_paths

### whatsapp-business (user)
**Reason:** Found 1 critical issue(s): credential_paths

### 1password (system)
**Reason:** Found 1 critical issue(s): credential_paths

### bear-notes (system)
**Reason:** Found 7 critical issue(s): credential_paths

### camsnap (system)
**Reason:** Found 1 critical issue(s): credential_paths

### eightctl (system)
**Reason:** Found 1 critical issue(s): credential_paths

### himalaya (system)
**Reason:** Found 3 critical issue(s): credential_paths

### model-usage (system)
**Reason:** Found 1 critical issue(s): credential_paths

### notion (system)
**Reason:** Found 3 critical issue(s): credential_paths

### oracle (system)
**Reason:** Found 1 critical issue(s): credential_paths

### spotify-player (system)
**Reason:** Found 1 critical issue(s): credential_paths

---
## 🟡 CAUTION - High-Severity Issues Detected

### trevor-methodology (user)
**Reason:** Found 1 high-severity issue(s): eval_exec

---
## ✅ Approved - No Issues (57)

- Network Analysis (user)
- answeroverflow (user)
- apple-notes (system)
- apple-reminders (system)
- blogwatcher (system)
- blucli (system)
- bluebubbles (system)
- claude-code (user)
- clawhub (system)
- coding-agent (system)
- discord (system)
- find-skills (user)
- gemini (system)
- gh-issues (system)
- gifgrep (system)
- github (system)
- gog (system)
- goplaces (system)
- healthcheck (system)
- huggingface-hub (user)
- humanizer (user)
- imsg (system)
- maps (user)
- mcporter (system)
- nano-pdf (user)
- node-connect (system)
- obsidian (system)
- ocr-and-documents (user)
- openai-whisper (system)
- openai-whisper-api (system)
- openhue (system)
- ordercli (system)
- peekaboo (system)
- sag (system)
- self-improvement (user)
- session-logs (system)
- sherpa-onnx-tts (system)
- skill-creator (system)
- slack (system)
- songsee (system)
- sonoscli (system)
- stock-market-pro (user)
- summarize (system)
- taskflow (system)
- taskflow-inbox-triage (system)
- things-mac (system)
- tmux (system)
- trello (system)
- unknown (system)
- unknown (user)
- video-frames (user)
- voice-call (system)
- wacli (user)
- weather (system)
- web-search-plus (user)
- xurl (user)
- youtube-content (user)

---
## 📋 Detailed Findings Per Skill

### answeroverflow
**Verdict:** 🟢 APPROVED
No security issues detected.

### api-gateway
**Verdict:** 🔴 CRITICAL
| # | Pattern | Severity | File | Line |
|---|---------|----------|------|------|
| 1 | credential_paths | critical | `SKILL.md` | 539 |

### claude-code
**Verdict:** 🟢 APPROVED
No security issues detected.

### unknown
**Verdict:** 🟢 APPROVED
No security issues detected.

### find-skills
**Verdict:** 🟢 APPROVED
No security issues detected.

### gmail
**Verdict:** 🔴 CRITICAL
| # | Pattern | Severity | File | Line |
|---|---------|----------|------|------|
| 1 | credential_paths | critical | `SKILL.md` | 267 |

### gog
**Verdict:** 🔴 CRITICAL
| # | Pattern | Severity | File | Line |
|---|---------|----------|------|------|
| 1 | credential_paths | critical | `SKILL.md` | 23 |
| 2 | credential_paths | critical | `SKILL.md` | 24 |
| 3 | http_post_external | medium | `config/exchange.py` | 16 |

### huggingface-hub
**Verdict:** 🟢 APPROVED
No security issues detected.

### humanizer
**Verdict:** 🟢 APPROVED
No security issues detected.

### maps
**Verdict:** 🟢 APPROVED
No security issues detected.

### nano-pdf
**Verdict:** 🟢 APPROVED
No security issues detected.

### Network Analysis
**Verdict:** 🟢 APPROVED
No security issues detected.

### ocr-and-documents
**Verdict:** 🟢 APPROVED
No security issues detected.

### self-improvement
**Verdict:** 🟢 APPROVED
No security issues detected.

### skill-scanner
**Verdict:** 🔴 CRITICAL
| # | Pattern | Severity | File | Line |
|---|---------|----------|------|------|
| 1 | credential_paths | critical | `README.md` | 155 |
| 2 | crypto_miner | critical | `README.md` | 9 |
| 3 | crypto_miner | critical | `README.md` | 158 |
| 4 | credential_paths | critical | `skill_scanner.py` | 101 |
| 5 | crontab_modify | high | `skill_scanner.py` | 118 |
| 6 | systemd_modify | critical | `skill_scanner.py` | 126 |
| 7 | crypto_miner | critical | `skill_scanner.py` | 135 |
| 8 | reverse_shell | critical | `skill_scanner.py` | 161 |
| 9 | base64_decode_exec | critical | `skill_scanner.py` | 170 |

### stock-market-pro
**Verdict:** 🟢 APPROVED
No security issues detected.

### stripe
**Verdict:** 🔴 CRITICAL
| # | Pattern | Severity | File | Line |
|---|---------|----------|------|------|
| 1 | credential_paths | critical | `SKILL.md` | 778 |

### trevor-methodology
**Verdict:** 🟡 CAUTION
| # | Pattern | Severity | File | Line |
|---|---------|----------|------|------|
| 1 | eval_exec | high | `pipeline/docx-js-template.js` | 37 |

### video-frames
**Verdict:** 🟢 APPROVED
No security issues detected.

### video-translation
**Verdict:** 🔴 CRITICAL
| # | Pattern | Severity | File | Line |
|---|---------|----------|------|------|
| 1 | credential_paths | critical | `SKILL.md` | 90 |

### wacli
**Verdict:** 🟢 APPROVED
No security issues detected.

### web-search-plus
**Verdict:** 🟢 APPROVED
No security issues detected.

### whatsapp-business
**Verdict:** 🔴 CRITICAL
| # | Pattern | Severity | File | Line |
|---|---------|----------|------|------|
| 1 | credential_paths | critical | `SKILL.md` | 494 |

### xurl
**Verdict:** 🟢 APPROVED
No security issues detected.

### youtube-content
**Verdict:** 🟢 APPROVED
No security issues detected.

### 1password
**Verdict:** 🔴 CRITICAL
| # | Pattern | Severity | File | Line |
|---|---------|----------|------|------|
| 1 | credential_paths | critical | `references/cli-examples.md` | 19 |

### apple-notes
**Verdict:** 🟢 APPROVED
No security issues detected.

### apple-reminders
**Verdict:** 🟢 APPROVED
No security issues detected.

### bear-notes
**Verdict:** 🔴 CRITICAL
| # | Pattern | Severity | File | Line |
|---|---------|----------|------|------|
| 1 | credential_paths | critical | `SKILL.md` | 33 |
| 2 | credential_paths | critical | `SKILL.md` | 40 |
| 3 | credential_paths | critical | `SKILL.md` | 60 |
| 4 | credential_paths | critical | `SKILL.md` | 66 |
| 5 | credential_paths | critical | `SKILL.md` | 92 |
| 6 | credential_paths | critical | `SKILL.md` | 94 |
| 7 | credential_paths | critical | `SKILL.md` | 97 |

### blogwatcher
**Verdict:** 🟢 APPROVED
No security issues detected.

### blucli
**Verdict:** 🟢 APPROVED
No security issues detected.

### bluebubbles
**Verdict:** 🟢 APPROVED
No security issues detected.

### camsnap
**Verdict:** 🔴 CRITICAL
| # | Pattern | Severity | File | Line |
|---|---------|----------|------|------|
| 1 | credential_paths | critical | `SKILL.md` | 31 |

### unknown
**Verdict:** 🟢 APPROVED
No security issues detected.

### clawhub
**Verdict:** 🟢 APPROVED
No security issues detected.

### coding-agent
**Verdict:** 🟢 APPROVED
No security issues detected.

### discord
**Verdict:** 🟢 APPROVED
No security issues detected.

### eightctl
**Verdict:** 🔴 CRITICAL
| # | Pattern | Severity | File | Line |
|---|---------|----------|------|------|
| 1 | credential_paths | critical | `SKILL.md` | 31 |

### gemini
**Verdict:** 🟢 APPROVED
No security issues detected.

### gh-issues
**Verdict:** 🟢 APPROVED
No security issues detected.

### gifgrep
**Verdict:** 🟢 APPROVED
No security issues detected.

### github
**Verdict:** 🟢 APPROVED
No security issues detected.

### gog
**Verdict:** 🟢 APPROVED
No security issues detected.

### goplaces
**Verdict:** 🟢 APPROVED
No security issues detected.

### healthcheck
**Verdict:** 🟢 APPROVED
No security issues detected.

### himalaya
**Verdict:** 🔴 CRITICAL
| # | Pattern | Severity | File | Line |
|---|---------|----------|------|------|
| 1 | credential_paths | critical | `SKILL.md` | 37 |
| 2 | credential_paths | critical | `SKILL.md` | 48 |
| 3 | credential_paths | critical | `references/configuration.md` | 3 |

### imsg
**Verdict:** 🟢 APPROVED
No security issues detected.

### mcporter
**Verdict:** 🟢 APPROVED
No security issues detected.

### model-usage
**Verdict:** 🔴 CRITICAL
| # | Pattern | Severity | File | Line |
|---|---------|----------|------|------|
| 1 | credential_paths | critical | `references/codexbar-cli.md` | 32 |

### node-connect
**Verdict:** 🟢 APPROVED
No security issues detected.

### notion
**Verdict:** 🔴 CRITICAL
| # | Pattern | Severity | File | Line |
|---|---------|----------|------|------|
| 1 | credential_paths | critical | `SKILL.md` | 23 |
| 2 | credential_paths | critical | `SKILL.md` | 24 |
| 3 | credential_paths | critical | `SKILL.md` | 34 |

### obsidian
**Verdict:** 🟢 APPROVED
No security issues detected.

### openai-whisper
**Verdict:** 🟢 APPROVED
No security issues detected.

### openai-whisper-api
**Verdict:** 🟢 APPROVED
No security issues detected.

### openhue
**Verdict:** 🟢 APPROVED
No security issues detected.

### oracle
**Verdict:** 🔴 CRITICAL
| # | Pattern | Severity | File | Line |
|---|---------|----------|------|------|
| 1 | credential_paths | critical | `SKILL.md` | 115 |

### ordercli
**Verdict:** 🟢 APPROVED
No security issues detected.

### peekaboo
**Verdict:** 🟢 APPROVED
No security issues detected.

### sag
**Verdict:** 🟢 APPROVED
No security issues detected.

### session-logs
**Verdict:** 🟢 APPROVED
No security issues detected.

### sherpa-onnx-tts
**Verdict:** 🟢 APPROVED
No security issues detected.

### skill-creator
**Verdict:** 🟢 APPROVED
No security issues detected.

### slack
**Verdict:** 🟢 APPROVED
No security issues detected.

### songsee
**Verdict:** 🟢 APPROVED
No security issues detected.

### sonoscli
**Verdict:** 🟢 APPROVED
No security issues detected.

### spotify-player
**Verdict:** 🔴 CRITICAL
| # | Pattern | Severity | File | Line |
|---|---------|----------|------|------|
| 1 | credential_paths | critical | `SKILL.md` | 62 |

### summarize
**Verdict:** 🟢 APPROVED
No security issues detected.

### taskflow
**Verdict:** 🟢 APPROVED
No security issues detected.

### taskflow-inbox-triage
**Verdict:** 🟢 APPROVED
No security issues detected.

### things-mac
**Verdict:** 🟢 APPROVED
No security issues detected.

### tmux
**Verdict:** 🟢 APPROVED
No security issues detected.

### trello
**Verdict:** 🟢 APPROVED
No security issues detected.

### voice-call
**Verdict:** 🟢 APPROVED
No security issues detected.

### weather
**Verdict:** 🟢 APPROVED
No security issues detected.

---
*Report auto-generated by Daily Skill Scanner Audit cron job.*
*Scanner location: `~/.openclaw/skills/skill-scanner/skill_scanner.py`*
*Report saved to `exports/skill-audit-2026-05-08.md`*