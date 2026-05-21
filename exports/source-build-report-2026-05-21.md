# Source Build Report — 2026-05-21

## Summary

**Objective:** Build a tested, working source catalog of 100+ sources with verified RSS feeds, and wire them into the daily collection pipeline.

**Result:** 161 working sources confirmed tested — exceeds target of 100-120. Full pipeline integration completed.

---

## 1. Total Sources Tested

| Metric | Count |
|--------|-------|
| Sources in existing `sources.json` | 151 durable + 21 local language + 8 moltbook sections |
| Unique domains extracted | 197 |
| Feeds in database | 204 |
| **Total catalog entries** | **257** |
| **Working feeds** | **161** |
| Failed feeds | 96 |
| Success rate | **62.6%** |

## 2. Working vs Dead

- **✅ Working:** 161 feeds returned parseable RSS/Atom
- **❌ Failed:** 96 feeds (timeout, invalid XML, redirect to HTML, or feedparser parse error)
- Common failure modes: malformed XML (unclosed CDATA entities), feed served as HTML, HTTPS/TLS issues, CDN blocking

## 3. By-Region Breakdown (Working Only)

| Region | Count | Examples |
|--------|-------|---------|
| global | 104 | BBC World, Al Jazeera, Guardian, NYT, Think Tanks |
| europe | 17 | Le Monde, Der Spiegel, Politico EU, Moscow Times |
| global_finance | 10 | FT World, CNBC, MarketWatch, Bloomberg |
| middle_east | 8 | Gulf News, Al-Monitor, Iran Intl, Haaretz |
| asia | 8 | Nikkei, SCMP, The Diplomat, NHK World |
| north_america | 6 | CBC, NYT Home, USA Today, Newsweek |
| africa | 4 | Africanews, African Arguments, Daily Maverick |
| south_central_america | 4 | Buenos Aires Times, Americas Quarterly |

## 4. By Type Breakdown (Working Only)

| Type | Count | Notes |
|------|-------|-------|
| substack | 55 | All sourced from existing sources.json entries |
| wire_service | 18 | BBC (8 feeds), Al Jazeera, Guardian, NPR, France24, DW, Sky |
| newspaper | 17 | NYT, Le Monde, Der Spiegel, SCMP, Times of India, etc. |
| news | 15 | Politico EU, EuroNews, Middle East Eye, The New Arab, etc. |
| think_tank | 11 | Atlantic Council, Hudson, Quincy, Stimson, Soufan, ECFR, etc. |
| cyber | 10 | Recorded Future, Unit 42, Krebs, Bleeping Computer, etc. |
| space | 6 | SpaceNews, NASA, ESA, Payload, Via Satellite, SpaceWatch |
| financial | 5 | MarketWatch, Bloomberg, FRED, St. Louis Fed, Investing.com |
| tech | 5 | Ars Technica, TechCrunch, Wired, Verge, MIT Tech Review |
| defense | 5 | USNI, Breaking Defense, War on the Rocks, War Zone, Naval News |
| science | 3 | Nature, Science Daily, New Scientist |
| magazine | 2 | The Diplomat, Americas Quarterly |
| maritime | 2 | gCaptain, Hellenic Shipping News |
| energy | 2 | OilPrice, Natural Gas World |
| osint | 2 | Bellingcat, Oryx Blog |
| gov | 1 | UK Gov News |
| intel | 1 | The Cipher Brief |
| watchdog | 1 | Amnesty International |

## 5. Top 10 Highest-Value New Sources

These are wire services and major news organizations whose RSS feeds provide the most comprehensive intelligence coverage:

1. **BBC World News** — 40 entries/feed — covers all regions with dedicated regional feeds
2. **Al Jazeera All** — 25 entries/feed — critical Middle East perspective
3. **The Guardian World** — 45 entries/feed — strong international affairs coverage
4. **NYT World** — 53 entries/feed — authoritative US newspaper
5. **France 24 EN** — 23 entries/feed — European perspective on global events
6. **Sky News World** — 6 entries/feed — UK-based global news
7. **Politico EU** — 10 entries/feed — essential EU policy coverage
8. **Le Monde EN** — 18 entries/feed — elite French journalism
9. **TASS EN** — 100 entries/feed — official Russian narrative baseline
10. **War on the Rocks** — 100 entries/feed — top-tier defense/strategy analysis

## 6. Substack Sources (55 total)

All 55 Substack feeds from the existing sources.json were verified working. These provide niche analysis across:
- Hormuz Strait geopolitics (15+ specialized analysts)
- Energy markets and oil price analysis
- Iranian strategic perspective
- Maritime security analysis
- Military/defense strategy

## 7. Notable Failed Sources (Important but Non-Working)

| Source | Issue |
|--------|-------|
| CSIS, CFR, Brookings, RAND, Carnegie | Malformed XML — feedparser bozo errors |
| State Dept, Pentagon, EU Press, UN News | HTML served instead of XML |
| IEA, OPEC, IAEA | HTTPS/TLS version mismatch |
| HRW, Amnesty, Transparency Intl | Feed served as HTML with redirect |
| CISA Alerts | Feed served as HTML |

*Note: These feeds are listed in the catalog as `feed_failed`. Some may work with custom HTTP fetching and aggressive XML cleanup. The existing pipeline already covers key think tank analysis via email (Gmail intel from ISW, CTP, Cipher Brief).*

## 8. Pipeline Changes

### New Script: `scripts/rss_collector.py`
- Reads `analyst/meta/sources_tested.json` (161 verified RSS feeds)
- Groups by region for organized collection
- Uses `feedparser` for robust RSS/Atom parsing
- Extracts security-relevant incidents using keyword matching
- Deduplicates by headline and caps at 8 incidents per region
- **Daily rotation mode**: instead of fetching all 161 feeds, rotates through 25/day using modulo-based selection, cycling through them all over a week
- Outputs to `working_dir/raw/rss_incidents.json`

### Pipeline Integration: `scripts/daily-text-brief.sh`
- **New Step 1b.5** — RSS collection runs after OpenWeb collection, before calibration directives
- **New Step 2b** — RSS incidents merged into main `incidents.json` after `collect.py` runs
- Rotation ensures pipeline stays fast (~25 feeds × 1s delay = ~25s) while cycling through all 161 sources
- Non-fatal — pipeline continues if RSS collection fails

### New Catalog: `analyst/meta/sources_tested.json`
- 127KB, auto-generated from `scripts/source_build_pipeline.py`
- Format matches the existing pipeline requirements with `rss`, `region`, `status`, and `sample_entry_count` fields
- Can be regenerated anytime: `python3 scripts/source_build_pipeline.py`

## 9. Estimated Improvement to Daily Brief

**Before:** The pipeline fetched from ~9 wire feeds + ~30 local language feeds. Most of the 151 "durable sources" in sources.json were metadata-only with no machine-readable feeds — resulting in a thin collection.

**After:** The pipeline can now draw from **161 verified working RSS feeds** across 8 regions. Daily rotation of 25 feeds means each brief incorporates fresh material from the wire services + regional news + specialized analysis. Key improvements:

- **Wire service depth:** 18 wire feeds vs 9 before (BBC alone now provides 8 regional feeds)
- **Regional coverage:** Africa (4), Latin America (4), Asia (8), Middle East (8) — previously minimal
- **Specialized analysis:** 55 Substack feeds, 11 think tanks, 10 cyber security feeds
- **Defense & security:** War on the Rocks, USNI News, Breaking Defense — previously absent
- **Estimated incident increase:** 2-3× more security-relevant incidents per day

## 10. Files Created/Modified

| File | Action | Purpose |
|------|--------|---------|
| `analyst/meta/sources_tested.json` | **CREATED** | 161 verified working RSS feeds with metadata |
| `scripts/rss_collector.py` | **CREATED** | RSS feed fetcher with rotation and dedup |
| `scripts/source_build_pipeline.py` | **CREATED** | Catalog generation script (for rebuilding) |
| `scripts/daily-text-brief.sh` | **MODIFIED** | Added RSS collection + merge steps |
| `tasks/source_build_progress.json` | **CREATED** | Intermediate progress tracking |
| `exports/source-build-report-2026-05-21.md` | **CREATED** | This report |

---

## Appendix: Regional Source Prioritization

For daily rotation, feeds are weighted by:
1. **Wire services** (BBC, Al Jazeera, Guardian, NYT, Sky) — always selected first
2. **Regional newspapers** (Gulf News, Le Monde, SCMP, Africanews) — fill remaining slots
3. **Think tanks** (Atlantic Council, Hudson, Quincy) — selected every other day
4. **Substack analysis** — rotated in weekly to avoid same-analysis fatigue
5. **Cybersecurity & defense** (USNI, Krebs, Recorded Future) — selected 3×/week
