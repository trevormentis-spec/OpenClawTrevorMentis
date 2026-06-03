# QC Watchdog Alert — 2026-06-03

## Status: 🚨 QC CRITICAL — Delivery Aborted

**Timestamp:** Wed Jun 3 19:47 UTC
**Source:** Autonomous cycle heartbeat (21:50 UTC detection)

## Diagnosis

The daily brief pipeline completed analysis successfully (all 12 regions + exec summary, rc=0) at 19:46 UTC, but the Opus QC gate returned **CRITICAL**, aborting delivery.

### Opus QC Findings

| Dimension | Verdict | Issue |
|-----------|---------|-------|
| Calibration | 🚨 CRITICAL | Band-number mismatches (e.g., "Roughly / 47%" doesn't match Kent bands; Middle East KJs have prose/numeric contradictions) |
| Sourcing | ❌ FAIL | BLUF has 4 factual claims with zero citations; 'Operation Epic Fury' unverifiable; copper price '$14,520/ton' unsourced |
| Completeness | 🚨 CRITICAL | CONTEXT field is 'N/A'; Europe KJ-1 body is 'N/A' |
| Clarity | ⚠️ WARN | Truncated band labels; run-on BLUF |
| Red Team | ❌ FAIL | Targets non-existent 'KJ-SSA-1' — orphaned dissent |
| Fabrication Risk | ❌ FAIL | 'Operation Epic Fury' unverifiable name; copper price suspiciously precise |

### Analysis Pipeline History (Today)

1. **14:25 UTC** — First collector run: OpenRouter/400 error on tier-1 exec summary → analyst rc=1
2. **14:45 UTC** — Retry: OpenRouter 400 on tier-2 (europe) → analyst crashed immediately
3. **15:14 UTC** — Retry via OpenRouter: all 12 regions completed, but exec summary call timed out after 240s → analyst rc=1
4. **18:55 UTC** — Pipeline re-triggered by daily brief cron fallback (cron had been disabled, re-enabled at 13:12 UTC)
5. **19:13 UTC** — Second full pipeline trigger
6. **19:47 UTC** — Final run completed analysis (deepseek-v4-pro via DeepSeek Direct), QC blocked delivery

### Auto-Fix Assessment

**Not within autonomy boundaries for full auto-fix.** The QC issues stem from:
- Persistent calibration accuracy problem (3.2% overall — 3rd day below 5%)
- LLM output quality: band-number mismatches, truncated content, unverifiable operation names
- Red team targeting stale KJs

These are analysis-quality issues requiring model re-runs, not structural/infrastructure fixes.

### Recommendations

1. Principal attention needed: calibration accuracy at 3.2% is critically low and degrading brief quality
2. Brief IS complete on disk at `/home/ubuntu/trevor-briefings/2026-06-03/analysis/` — can be manually delivered
3. Consider: increasing analyze.py API timeout (currently 240s, exec summary timed out on one run), or switching to shorter max_input_chars for exec summary to reduce response time
4. Band diversity enforcement may be overly strict given current accuracy state — consider relaxing min_bands to 1 and focusing on factual accuracy instead

### Infrastructure Status

- ✅ DeepSeek balance: $61.48 (healthy)
- ✅ Kalshi balance: $395.60 (healthy)
- ✅ All API keys responding
- ✅ Brain reindex completed
- ✅ GDELT collection: 110 events
- ✅ Source discovery: 2 new sources added
- ⚠️ 74 dead feeds cached from 296 tracked
- ⚠️ Brave Search gap-fill failing ("No module named 'scripts'" in collect.py)
