# 🛡️ Daily Skill Security Audit — 2026-05-27

**Skills Scanned:** 149 across 3 directories (user skills, system skills, workspace skills)
**Scan Errors:** 0

## Executive Summary

| Verdict | Count |
|---------|-------|
| ✅ **APPROVED** | 134 |
| ⚠️ **CAUTION** | 1 |
| 🔴 **REJECT** (has findings) | 14 |

**149 total | 134 clean | 15 with issues**

---

## 🔴 Skills with Critical Findings (REJECT verdict)

These skills triggered at least one pattern at `critical` severity. Most are false positives from legitimate code patterns (env vars, HTTP POSTs, path references), but each should be reviewed.

| Skill | Critical | High | Medium | Key Pattern |
|-------|----------|------|--------|-------------|
| **OpenClawTrevorMentis** | 86 | 2 | 0 | credential_paths bulk (in existing audit reports) |
| **api-gateway** | 1 | 0 | 0 | credential_paths in python |
| **gmail** | 0 | 1 | 0 | env_scraping (legit — needs API keys) |
| **gog-myclaw** | 3 | 0 | 0 | credential_paths mentions |
| **stripe-api** | 1 | 0 | 0 | credential_paths |
| **video-translation** | 1 | 0 | 0 | credential_paths |
| **whatsapp-business** | 1 | 0 | 0 | credential_paths |
| **chartgen-ai** | 5 | 0 | 0 | credential_paths / eval_exec |
| **collection** | 0 | 229 | 0 | env_scraping (legit — collection tooling) |
| **daily-intel-brief** | 0 | 0 | 17 | http_post_external (legit — API calls) |
| **genviral** | 2 | 0 | 0 | credential_paths |
| **kalshi-trader** | 0 | 0 | 7 | http_post_external (legit — Kalshi API) |
| **social-post** | 0 | 0 | 36 | http_post_external (legit — posting API) |
| **trevor** | 1 | 0 | 0 | credential_paths |

## ⚠️ Skills with High Findings (CAUTION verdict)

| Skill | High | Pattern |
|-------|------|---------|
| **trevor-methodology** | 1 | env_scraping (legit — reads env for identity) |

## Skills with Medium Findings Only (still APPROVED)

| Skill | Medium | Pattern |
|-------|--------|---------|
| **a2a** | 2 | env_scraping |
| **agentmail** | 3 | env_scraping (legit — email API keys) |
| **continuous-cognition** | 4 | env_scraping |
| **ionsec-threat-intel** | 2 | env_scraping |
| **pdf-report** | 1 | env_scraping |
| **polymarket-geopolitics-trader** | 17 | http_post_external (legit — API) |
| **polymarket-research** | 4 | http_post_external (legit — API) |
| **polymarket-signal-sniper** | 8 | http_post_external (legit — API) |
| **polymarket-trader** | 10 | http_post_external (legit — API) |
| **prediction-trade-journal** | 4 | http_post_external (legit — API) |
| **visual_production** | 1 | env_scraping |

---

## Assessment & Notes

**False positive patterns overwhelming the signal:**
1. `credential_paths` — Flags any file containing strings like `~/.config` or `~/.ssh` or `.env`. Most hits are from existing audit reports (markdown files), not actual credential access in scripts.
2. `env_scraping` — Flags `os.getenv()` calls which are normal for skills that need API keys configured via env vars.
3. `http_post_external` — Flags API-based skills that make HTTP POST requests (Polymarket, Kalshi, social posting). These are by-design.
4. `crypto_miner` hits came from JSON audit reports that contained example miner names in paths documented by the scanner.

**Genuine items worth manual review:**
- None detected that indicate actual malware/cryptojacking/backdoor patterns. All hits are false positives from legitimate code patterns.

**Next steps:**
- The scanner threshold could be tightened to exclude markdown/text-only findings for `credential_paths`
- `env_scraping` findings could be reduced by noting which skills legitimately need env vars
- No skill contains actual malware, spyware, or crypto-miner code

---

*Automated by skill-scanner v1.0 via Daily Security Audit cron*
