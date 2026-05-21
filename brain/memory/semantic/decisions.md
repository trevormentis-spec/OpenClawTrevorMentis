- [2026-05-11] - Decision: user wants to leave it in agents submolt to gauge engagement (source: 2026-05-11.md, confidence: medium)
- [2026-05-12] - Decision cycle: Phase 4 — Political Screen (D3 received, retreat preserving D1 likely) (source: 2026-05-12.md, confidence: medium)
- [2026-05-12] 3. Starmer LDAP-7 Analysis — scored framework with decision-cycle diagnosis and CPCA overlay (source: 2026-05-12.md, confidence: medium)
- [2026-05-12] {"ts": "2026-05-12T02:01:03.949430Z", "text": "LDAP-7 framework ingested: 7-dimension leader analysis + decision cycle + CPCA overlay integrated as procedural skill. Trump D1-D7 profile created."} (source: 2026-05-12.jsonl, confidence: medium)
- [2026-05-15] - The Morena internal split (AMLO faction vs younger reformers) over the Rocha case is the most important structural constraint on Sheinbaum's decision-making. The Rocha case is the defining stress te... (source: 2026-05-15.md, confidence: medium)
- [2026-05-17] **Probe B** — "Brief me on the ECB rate decision this week." (source: 2026-05-17.md, confidence: medium)
- [2026-05-19] - Decision: no public pushes to openweb repo without Roderick's approval (source: 2026-05-19.md, confidence: medium)

## Session: 2026-05-21 (8-hour iteration)

### Pipeline
- **[2026-05-21]** Daily brief is text-only. No PDF. No social posts. No Buttondown. No landing page.
- **[2026-05-21]** Delivery: send_text_brief_gmail.py → roderick.jones@gmail.com via Maton Gmail API.
- **[2026-05-21]** 10-region taxonomy: europe, north_america, central_america_caribbean, south_america, africa, middle_east, central_asia, south_east_asia, oceania, prediction_markets.
- **[2026-05-21]** North America reframed: includes USA + Canada + Mexico stories (not Mexico-only).
- **[2026-05-21]** Tiered routing: DeepSeek V4 Pro (Direct API) for 10 regional analyses, Opus 4.7 (OpenRouter) for exec summary + red team.
- **[2026-05-21]** analyze.py: added --tier2-provider flag to allow tier-2 to route through different API than tier-1.
- **[2026-05-21]** Humanizer: scripts/humanize_brief.py strips AI patterns (em dashes, AI vocab, -ing constructions) from brief before delivery.

### Source Infrastructure
- **[2026-05-21]** 161 verified RSS feeds in sources_tested.json — 62.6% success rate from 257 tested.
- **[2026-05-21]** RSS collection: scripts/rss_collector.py with daily rotation (25 feeds/day, cycles through all 161).
- **[2026-05-21]** Heartbeat source discovery: hourly 10-query rotation via source_discovery.py --query --auto-add.
- **[2026-05-21]** Brave Search API for source discovery (not DeepSeek). Gzip handling fixed.

### LEO Ground Stations
- **[2026-05-21]** LEO topic onboarded: 54 entities, 83 sources, 8 themes, 15 priority sites, 80-site risk register.
- **[2026-05-21]** Three principal documents incorporated: market opportunity assessment, physical security methodology, 80-site risk register.
- **[2026-05-21]** LEO data collectors: scripts/leo_collectors.py — FCC (daily), launch schedule (daily), ITU (weekly), jobs (weekly), Sentinel-2 imagery (monthly).
- **[2026-05-21]** LEO daily brief: scripts/leo_daily_brief.py — separate product, synthesized by DeepSeek V4 Pro, sent to inbox at 09:00 PT.
- **[2026-05-21]** Sentinel Hub credentials: Copernicus Data Space Ecosystem credentials configured for satellite imagery checks.

### Model Routing
- **[2026-05-21]** Tier-2 regional analysis: DeepSeek V4 Pro via Direct API ($0.001/region).
- **[2026-05-21]** Tier-1 exec + red team: Opus 4.7 via OpenRouter ($0.10/call).
- **[2026-05-21]** Total daily cost: ~$0.22/day (was ~$1.17 all-Opus, ~$35/month vs ~$6/month).
- **[2026-05-21]** ORCHESTRATION.md and llm_gate.py untouched — this is pipeline-level routing only.

### Reasoning & Memory
- **[2026-05-21]** Reasoning loop: scripts/reasoning_loop.py — every 10 min, checks RSS/FCC/Kalshi against last brief's judgments, sends alerts for deltas.
- **[2026-05-21]** Report memory: scripts/report_memory.py — every brief logged to brain/memory/episodic/*.jsonl + memory/YYYY-MM-DD.md with key judgments and summaries.
- **[2026-05-21]** Reports in memory: daily_brief (4674w), leo_daily_brief (1352w), validation_brief (4018w).

### Principal Preferences
- **[2026-05-21]** Deliver to roderick.jones@gmail.com (not AgentMail).
- **[2026-05-21]** Text-only briefs. No PDF, no newsletters, no social posting.
- **[2026-05-21]** Analyst-to-analyst voice. Direct address ("Roderick —"). Signal-dense. No hand-holding.
- **[2026-05-21]** Sources list every day with provenance.
- **[2026-05-21]** Newsletter recommendations at bottom of brief.
