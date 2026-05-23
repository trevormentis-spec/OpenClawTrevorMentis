# TREVOR Daily Intelligence Brief — Pipeline Run Report
## 2026-05-22 22:21–22:50 UTC

### Executive Summary
Full end-to-end pipeline run: collection → 12-region analysis (DeepSeek V4 Pro) → Opus 4.7 QC → AgentMail delivery. Brief delivered to roderick.jones@gmail.com at 22:50 UTC.

---

## 1. PIPELINE ARCHITECTURE

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────┐    ┌──────────┐
│  COLLECTION     │    │  ANALYSIS         │    │  QC (Opus 4.7)│    │ DELIVERY │
│  415 RSS feeds  │───▶│  12 regions       │───▶│  fact check    │───▶│ AgentMail│
│  Email intel    │    │  DeepSeek V4 Pro  │    │  calibration   │    │ HTML body│
│  Web fallback   │    │  16K max_tokens   │    │  grammar       │    │          │
└─────────────────┘    └──────────────────┘    └──────────────┘    └──────────┘
```

### Models Used
| Step | Model | Provider | Input Tokens | Output Tokens* | Cost* |
|------|-------|----------|-------------|----------------|-------|
| 12 regional analyses | DeepSeek V4 Pro | DEEPSEEK_Direct | ~5K each | ~4K each | ~$0.12 |
| Executive summary | DeepSeek V4 Pro | DEEPSEEK_Direct | ~60K (all regions) | ~3K | ~$0.11 |
| Red team | DeepSeek V4 Pro | DEEPSEEK_Direct | ~5K | ~1K | ~$0.01 |
| QC review | Claude Opus 4.7 | OpenRouter | ~35K (full brief) | ~1.2K | ~$0.21 |
| **TOTAL** | | | **~160K** | **~53K** | **~$0.45** |

*Estimated — actual costs will vary. V4 Pro: $1.74/M in, $3.48/M out (75% off until May 31). Opus: $15/M in, $75/M out.

---

## 2. SOURCES USED

### Collection Inputs
- **RSS feeds**: 415 local-language + 9 global wires = 424 total
- **Email intel**: AgentMail inbox (27 incidents merged from newsletters)
- **Web search fallback**: Brave Search API (for regions with <3 incidents)
- **Incidents collected**: 82 (from prior collection at ~18:23 UTC)

### Incidents by Region
| Region | Incidents |
|--------|-----------|
| Europe | 16 |
| North America | 15 |
| Middle East | 15 |
| Africa | 8 |
| Central Asia (5 Stans) | 8 |
| Prediction Markets | 8 |
| Oceania | 6 |
| South East Asia | 4 |
| Central America & Caribbean | 4 |
| South America | 1 |
| East Asia | 0 (taxonomy gap) |
| South Asia | 0 (taxonomy gap) |

### RSS Feed Breakdown
| Category | Feed Count | Working % (est.) |
|----------|-----------|-------------------|
| Global wires (BBC, FT, Guardian, etc.) | 9 | 67% |
| Middle East / Persian / Arabic | 30+ | ~40% |
| Europe / Russia / Ukraine | 40+ | ~45% |
| Africa (English + French + Arabic) | 60+ | ~30% |
| Asia Pacific (CN, JP, KR, IN, PK) | 50+ | ~30% |
| Latin America (ES + PT) | 25+ | ~25% |
| Multilingual broadcasters (BBC, DW, RFE) | 30+ | ~50% |
| Substack / independent analysts | 30+ | ~50% |
| Telegram channels | 18 | 0% (all RSS parse errors) |
| Maritime / Space / Cyber / Energy | 30+ | ~30% |

---

## 3. ANALYSIS TIMINGS

| Time (UTC) | Step | Duration |
|-----------|------|----------|
| 22:21:07 | Pipeline start | — |
| 22:23:58 | Europe complete | 2m 51s |
| 22:26:43 | North America complete | 2m 45s |
| 22:28:23 | Central America & Caribbean | 1m 40s |
| 22:29:38 | South America complete | 1m 15s |
| 22:32:50 | Africa complete | 3m 12s |
| 22:35:01 | Middle East complete | 2m 11s |
| 22:37:17 | Central Asia complete | 2m 16s |
| 22:39:33 | South East Asia complete | 2m 16s |
| 22:40:40 | East Asia complete | 1m 07s |
| 22:42:19 | South Asia complete | 1m 39s |
| 22:44:17 | Oceania complete | 1m 58s |
| 22:46:33 | Prediction Markets complete | 2m 16s |
| 22:47:59 | Executive Summary complete | 1m 26s |
| 22:48:40 | Red Team complete | 0m 41s |
| **22:48:40** | **Analysis complete** | **27m 33s total** |
| 22:50:47 | QC + delivery complete | 2m 07s |

Average per-region: ~2m 06s (range: 41s – 3m 12s). Total pipeline: **29 minutes 40 seconds**.

---

## 4. OPUS 4.7 QC FINDINGS

### CRITICAL (5)
1. **South Asia truncated mid-sentence** — *RESOLVED*: Text was complete in source file; appearance of truncation was from QC text limit (35K chars sent)
2. **Iran posture contradictions** — Middle East/North America/Europe sections frame Iran differently: negotiations, pre-war, slight progress. Unreconciled in BLUF. *NOTED for prompt improvement*
3. **Iran war status inconsistent** — References to "Iran war" (WCK meals, operational costs) alongside negotiation framing. *NOTED*
4. **East Asia calibration failure** — Zero source coverage but issued 95% confidence KJ. *FIXED: downgraded to even chance (50%)*
5. **South America calibration** — Thin collection acknowledged but 65% specific repo call. *NOTED for postdict*

### WARNING (6)
- KJ ownership duplication (Poland/NATO judgment)
- Source attribution gaps (single-email sourcing)
- Geographic miscategorisation (Taiwan as Oceania)
- Tone inconsistency (direct address in some sections)
- BLUF/body mismatch (Taiwan claim not developed)
- Central Asia single-source transit claims

### INFO (5 grammar/style)
- "paper over" → "papers"
- "would repricing" → "would reprice"
- Inconsistent date formats (May 29 vs 29 May)
- Garbled phrasing ("tangible signal risk marker")
- Strait of Hormuz volume figure flagged for sourcing

---

## 5. ACTIONS TAKEN DURING RUN

1. **max_tokens**: Bumped from 8192 → 16384 to prevent output truncation
2. **East Asia calibration**: 95% → 50% (even chance) — QC caught invalid confidence with zero sources
3. **Model name**: Fixed in exec_summary.json from flash/opus → V4 Pro
4. **South Asia narrative**: Verified complete, no truncation in source

---

## 6. KNOWN GAPS (Unresolved)

### Collection Gaps
- **Telegram channels**: All 18 return RSS parse errors — t.me/s/ HTML is malformed. Needs OpenWeb adapter or live browser session
- **South America**: Only 1 incident (up from 0 after feed fixes). Still critically thin
- **East Asia / South Asia**: 0 incidents each — new regions with no retroactively-mapped incidents
- **Substack feeds**: ~50% working, 15 broken ones removed, 14 replacements added

### Analysis Gaps
- **Taiwan filed under Oceania**: regions.json had Taiwan in oceania; need to move to east_asia
- **12-region REGIONS_ORDER**: analyze.py only analyzes 10 regions (printed "10 regions"); the 2 new regions analyzed but the counter text is stale
- **Tone inconsistency**: Some sections open with "Roderick —" direct address; should standardize to analytic voice
- **Date format**: Mix of "May 29" and "29 May" across sections
- **Single-source strength**: Several key claims rest on single email sources with no corroboration

### Pipeline Gaps
- **Heartbeat feed health**: New system running every 30 min but still has dead feeds to cull
- **Collector speed**: 415 sequential feeds take ~10 min; could parallelize or add connection pooling
- **Collection freshness**: Used 4-hour-old incidents for this run; morning run will have fresh collection

---

## 7. DELIVERY

| Metric | Value |
|--------|-------|
| To | roderick.jones@gmail.com |
| From | trevor_mentis@agentmail.to |
| Method | AgentMail SDK |
| Format | HTML email with hyperlinked source citations |
| Message ID | 0100019e51e2515a-f46d67eb... |
| Time | 2026-05-22 22:50 UTC |
| Incident sources linked | 82 URLs from raw/incidents.json |

---

## 8. NEXT STEPS

### Immediate
- [ ] Move Taiwan from oceania to east_asia in regions.json
- [ ] Update REGIONS_ORDER count string from "10" to "12" in analyze.py  
- [ ] Add collection freshness check before analysis

### Short-term
- [ ] Fix Telegram ingestion (switch from t.me/s to OpenWeb adapter)
- [ ] Add calibration directives from Opus QC findings to tomorrow's prompt
- [ ] Standardize tone/voice in prompt template
- [ ] Add Perplexity Sonar fallback for thin-coverage regions where all feeds dead

### Ongoing
- [ ] Feed health audit runs every 30 min via heartbeat
- [ ] Source discovery + pruning cycles daily
- [ ] Newsletter subscriptions flowing to AgentMail → email intel pipeline

---

*Report generated by TREVOR (DeepSeek V4 Flash) — 2026-05-22 22:52 UTC*
