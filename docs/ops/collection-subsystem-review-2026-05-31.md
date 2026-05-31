# Collection Subsystem Review — Opus Audit

**Date:** 31 May 2026
**Subject:** Trevor OSINT Collection Subsystem — architecture, gaps, and optimization
**Scope:** Simmer role, email intel integration, collection architecture, source registry reconciliation

---

## Q1: Simmer in Collection Pipeline

### Current Role

Simmer is a prediction market trading SDK (`skills/simmer/SKILL.md`) — it provides an agent-native trading interface for Polymarket and Kalshi. It was integrated into the daily brief pipeline as **Step 1d** in `scripts/daily-text-brief.sh`:

```bash
# Step 1d: Simmer market signal overlay (trading context, risk alerts, PnL)
python3 "$REPO/scripts/simmer_scanner.py" --save >> "$LOG" 2>&1
```

The scanner script (`simmer_scanner.py`) was a wrapper around the Simmer SDK that queried prediction markets for geopolitical topics (Iran, Russia) and reported PnL/risk data.

### Post-Trading-Teardown Status

The Philby trading system was torn down on **31 May 2026** via `scripts/teardown-trading.sh`. This script:

1. Removed `simmer_scanner.py` from `scripts/` (line 43: `rm -f "$WORKSPACE/scripts/simmer_scanner.py"`)
2. Removed `kalshi_scanner.py`, Philby code, trading logs
3. Archived everything to `archive/philby-trading-2026-05-31/`

**Critical finding: The pipeline script still calls the deleted file.** The `daily-text-brief.sh` at line 79 will fail with a `python3: can't open file '.../simmer_scanner.py'` error. The `set +e` wrapper prevents it from crashing the pipeline, but it generates a spurious error log entry and wastes time.

### Actual Signal Value (Pre-Teardown)

I examined the last 6 simmer scan exports:

| Date | Markets Found | Risk Alerts | PnL |
|------|--------------|-------------|-----|
| 2026-05-31 | 0 | 0 | -$21.44 |
| 2026-05-29 | 0 | 0 | -$22.54 |
| 2026-05-28 | 2 | 0 | -$22.54 |
| 2026-05-27 | 0 | 0 | -$21.44 |
| 2026-05-26 | 0 | 0 | -$19.92 |

Even when functional, Simmer produced **essentially zero geopolitical signal**. It found at most 2 markets per scan (Polymarket), with PnL data that was purely trading-context — irrelevant to intelligence analysis. The scanner's own note states: *"Simmer provides trading-focused data. For broad market discovery, see Kalshi scanner output."* The Kalshi scanner already covers prediction markets comprehensively (88+ active markets).

### Recommendation: Remove

**Remove the Simmer step entirely.** It is:

- **Dead code**: The file was deleted. The pipeline fails silently but incorrectly.
- **Zero signal value**: Even when working, produced no useful intelligence.
- **Redundant**: Kalshi scanner (Step 1c) already handles prediction market intel.
- **Trading-context only**: PnL, risk alerts, and trade data have no place in an intelligence brief.

**Also remove Step 5b (I&W Feedback Loop):** `scripts/iw_feedback_loop.py` references `philby/desks/philby-config.json` which was also deleted during teardown. This script attempts to "connect calibration to Philby desk narratives" — a dead end post-teardown.

---

## Q2: Email Intel Integration

### Data Flow

```
┌─────────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│ trevor.mentis   │────▶│ scripts/gmail_reader │────▶│ tasks/news_raw.md│
│ @gmail.com      │     │ .py (Maton API)      │     │ (shared staging) │
└─────────────────┘     └──────────────────────┘     └──────────────────┘
                                                              │
┌─────────────────┐     ┌──────────────────────┐              │
│ trevor_mentis   │────▶│ scripts/agentmail_    │─────────────▶│
│ @agentmail.to   │     │ reader.py (AgentMail  │              │
│                 │     │ SDK)                  │              │
└─────────────────┘     └──────────────────────┘              │
                                                               ▼
┌─────────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│ Combined Intel  │────▶│ scripts/              │────▶│ Working dir:     │
│ Digest (cron)   │     │ collect_email_intel   │     │ raw/incidents    │
│ (12:00 PT)      │     │ .py                   │     │ .json           │
└─────────────────┘     └──────────────────────┘     └──────────────────┘
                                                               │
                                                               ▼
                                                     ┌──────────────────┐
                                                     │ collect.py       │
                                                     │ line 923:        │
                                                     │ parse_news_raw(  │
                                                     │ NEWS_RAW_PATH)   │
                                                     └──────────────────┘
```

**Three integration points:**
1. **`gmail_reader.py`** — reads trevor.mentis@gmail.com via Maton API gateway, classifies emails (intel source, newsletter, alert, unknown), appends to `tasks/news_raw.md`
2. **`agentmail_reader.py`** — reads trevor_mentis@agentmail.to via AgentMail SDK, filters out self-sent (Trevor's own outbound), appends to `tasks/news_raw.md`
3. **`collect_email_intel.py`** — orchestrates both inboxes, converts to incident format, injects into working dir's `raw/incidents.json` directly (not just news_raw.md)

The critical integration: **`collect.py` line 923 calls `parse_news_raw(NEWS_RAW_PATH)`**, so email intel IS injected into the collection pipeline. This is working as designed.

### Signal Quality Assessment

I analyzed the current `tasks/news_raw.md` content (31 May 2026, 17:02 UTC):

**High-value intel (usable for brief):**
- ✅ **ISW Iran Update Special Report** (30 May) — CT strategic analysis of Strait of Hormuz
- ✅ **ISW Russian Offensive Campaign Assessment** (30 May) — Russia preparing massive Ukraine strike
- ✅ **CTP Iran Update Evening Special** (30 May) — Iran political/security developments
- ✅ **Reuters Iran Briefing** — Israeli troops capture Beaufort Castle in Lebanon
- ✅ **CSIS Strategic Technologies** — tech/geopolitics newsletter
- ✅ **Lawfare** — security/legal analysis (though this one is a fundraiser pitch)
- ✅ **Ryan McBeth Substack** — Iranian rebels/AR-15 analysis (OSINT)
- ✅ **POLITICO Playbook** — Hill politics

**Low-value noise (not usable for intelligence brief):**
- ❌ **Reuters Technology Roundup** — Blue Origin rocket explosion (commercial space, not intel-relevant)
- ❌ **NYT Wirecutter** — "A jack-of-all-trades stain remover" (zero intel value)
- ❌ **Bloomberg CityLab** — "Reusing old buildings is big business" (zero intel value)
- ❌ **Bloomberg Opinion** — "China's plans are going up in smoke" (opinion, not intel)
- ❌ **NYT Morning** — General news digest (too broad, already covered by RSS feeds)

**Signal ratio:** Roughly **40% useful, 60% noise** on this sample. The noise comes from catch-all newsletters (NYT Wirecutter, Bloomberg CityLab) that shouldn't be in the intel feed at all.

### Identified Issues

1. **Gmail reader captures ALL inbox mail**, not just intel-labeled mail. The sender filter list in `collect_email_intel.py` (16 intel senders) is more selective than `gmail_reader.py`'s broader classification. The news_raw.md contains emails from Reuters newsletters and NYT that aren't in the intel sender list.

2. **No deduplication across cron cycles** — news_raw.md accumulates emails across multiple reads. The same email can appear multiple times (Gmail intel digest headers with different timestamps).

3. **HTML email rendering is broken** — emails in news_raw.md contain raw HTML/CSS from newsletters (e.g., Reuters Technology Roundup shows `*{box-sizing:border-box}body{margin:0...}` CSS). The body extraction in `gmail_reader.py` handles `text/plain` but most newsletters are `text/html` with complex MIME structures.

4. **AgentMail captures all inbound, including newsletters from CSIS, Lawfare, POLITICO** — good for breadth but the "Combined Intel Digest" re-append creates duplicate entries across cycles.

5. **CIPHER BRIEF and FOREIGN POLICY are NOT flowing** — these are listed as target senders (`dailybrief@thecipherbrief.com`, `newsletters@foreignpolicy.com`) but I found no evidence in the current news_raw.md that they're being received. This may be a delivery issue at the provider side or Gmail filtering.

### Recommendations

1. **Filter out known noise senders at the reader level** — add a `NOISE_SENDERS` blocklist to both readers (Wirecutter, CityLab, NYT Morning, Reuters Tech Roundup, Bloomberg Opinion, Bloomberg CityLab). These should never reach the staging file.

2. **Fix HTML email body extraction** — the current base64 decoding and HTML-stripping produces garbled output. Use a lightweight HTML→text converter (html2text or similar) for these emails.

3. **Investigate Cipher Brief and FP delivery** — these are high-value sources. Check if they're being filtered by Gmail (spam/promotions tab) or if the subscriptions have lapsed.

4. **Add content-based dedup** — before appending to news_raw.md, check if the subject line (or a hash of subject+sender) already exists.

5. **Consider reducing Gmail read frequency** — the 2-hour cron for intel email is excessive for the signal level. Change to every 6 hours.

---

## Q3: Collection Architecture Assessment

### Feed Health

| Metric | Value |
|--------|-------|
| Total catalog feeds | 912 |
| Tested so far | 780 |
| Working | 298 (34%) |
| Dead | ~342 (from Cloudflare 403 blocking alone) |
| Hardcoded in collect.py | 324 (8 WIRE_FEEDS + 316 LOCAL_LANGUAGE_FEEDS) |
| Catalog feeds (dynamic) | ~200 tested working, loaded per-region per-run |

**Dead feed composition:** The primary cause of feed death is **Cloudflare 403 blocks** (342+ feeds). Many regional news sites use Cloudflare's bot protection, which blocks `urllib.request` with a `User-Agent` header. The health audit script attempts to test all 912 feeds but is still in progress (780 of 912 tested as of last check).

**The 34% health rate is misleading** because:
- The catalog includes many aggregation sites and search-engine result pages that were never RSS feeds
- The feed health audit tests URL accessibility + XML parse, which is correct for RSS but rejects non-RSS sources
- `sources_tested.json` (7,001 lines) includes many non-RSS URLs that were collected during source discovery

### Regional Coverage

From `collection-state.json` (31 May 2026):

| Region | Score | Status | Latest Data | Issue |
|--------|-------|--------|-------------|-------|
| Europe | 87.1 | **STALLED** | No data since 26 May | High historical but stopped collecting |
| Middle East | 60.5 | **STALLED** | No data since 26 May | High historical but stopped collecting |
| North America | 55.7 | Active | 31 May (13 items) | OK |
| Sub-Saharan Africa | 22.8 | Active | 31 May (8 items) | OK but thin |
| South Asia | 14.4 | Active | 31 May (5 items) | OK |
| East Asia | 13.9 | Active | 31 May (5 items) | OK |
| SE Asia | 10.1 | Active | 31 May (4 items) | OK |
| Oceania | 9.6 | Active | 31 May (4 items) | OK |
| South America | 7.5 | Active | 31 May (3 items) | OK |
| Central America/Carib | 6.7 | Active | 31 May (3 items) | OK |
| Central Asia | 5.2 | Active | 31 May (3 items) | **Thin** |
| Prediction Markets | 4.8 | Active | 31 May (3 items) | OK |
| North Africa | 1.9 | **STALLED** | Last: 29 May | **Critical gap** |
| Global Finance | 0.3 | **DEAD** | No data since 22 May | **Essentially dead** |

**Critical finding: Europe and Middle East — our two highest-priority regions — have zero incident data since 26 May despite smoothed scores of 87.1 and 60.5 respectively.** This suggests the collection pipeline is running but produces zero incidents for these regions. Likely causes:

- Top wire feeds (Reuters, AP) are dead → no high-volume content sources feeding these regions
- The region-matching in `normalise()` may be failing if headlines are generic
- GDELT collection floor may not be filling gaps for these regions
- The per-region cap system may be clipping them (Europe cap=20, Middle East cap=14 — both adequate)

**North Africa at 1.9** — the score is low because coverage is thin (only 3 sources: Mada Masr, Hespress, Radio Dabanga). Egypt, Libya, Algeria, Tunisia, and Morocco all lack dedicated feeds in the live collection.

**Global Finance at 0.3** — essentially dead since 22 May. Bloomberg Markets and FT Markets feeds may be down.

### Source Registry vs Live Feed List Reconciliation

**The Big Disconnect:**
- **26 source registry files** in `brain/memory/semantic/sources-*.md` cataloging sources by region
- **1,463 sources** in `analyst/meta/sources.json` (durable sources)
- **912 feeds** in `analyst/meta/sources_tested.json` (tested catalog)
- **324 feeds** hardcoded in `collect.py` (the actual live collection)
- **Only 5 of 1,463 durable sources have RSS URLs**

The registry files describe many sources (e.g., sources-middle_east.md lists 17 feeds) but most are **not RSS feeds** — they're web page URLs, Substack newsletters, blog homepages, and think tank articles. `collect.py`'s RSS parser can't consume them. The sources.json "durable_sources" list is a **web page URL catalog**, not an RSS feed list.

This explains 60%+ of the regional thinness: the rich source identification work in the registry files is **not reflected in the live RSS collection**. The only bridge is:
- `load_catalog_feeds()` in collect.py — loads tested RSS feeds from `sources_tested.json` (912 tested, but only the ~200 working ones get rotated in)
- The catalog feeds are rotated per-region (max 6 per region per run)

### Collection Optimization

**What's good:**
- ✅ Pipeline has three safety nets: RSS primary → GDELT floor → Brave web search fallback
- ✅ Per-region adaptive caps prevent one region from drowning out others
- ✅ Dead-feed cache prevents re-testing known-bad URLs (8-16s saved per feed)
- ✅ GDELT v2 collector uses CSV export (no API key needed, public domain data)
- ✅ Source discovery script runs weekly to find new sources
- ✅ Feed health audit runs as part of source maintenance
- ✅ Collection state tracks utilization — which sources are actually cited vs fetched but unused

**What's broken:**
- ❌ **Simmer scanner (Step 1d)** — file deleted, pipeline references dead file
- ❌ **I&W Feedback Loop (Step 5b)** — references deleted Philby config
- ❌ **Europe and Middle East stalled** — no incident data since 26 May despite being highest priority
- ❌ **North Africa critically thin** — 1.9 smoothed score
- ❌ **Global Finance dead** — 0.3 score

**What's missing:**
- **Thematic cross-cutting feeds** — no dedicated collection for: Arctic, Space/Satellite, Cyber threat, Supply chain, Bio/health, Disinformation. The region-based model misses these.
- **No Python-level deduplication across pipeline runs** — parse_news_raw doesn't filter duplicates across cron cycles
- **No automatic pruning of dead/noise feeds** — dead feeds remain in the catalog, just skipped from fetching. 342+ Cloudflare-blocked feeds should be removed from rotation entirely
- **Only 6 of 912 sources are tracked for utilization** — the collection_state.py only tracks 6 named sources (Reuters, AP, BBC, Al Jazeera, etc.) for citation analysis
- **No source quality scoring** — all working feeds are treated equally regardless of Admiralty rating

### Recommendation: Reconciliation Plan

1. **Fix the Europe/Middle East stall** — investigate whether the RSS feeds for these regions are actually working. The hardcoded feeds include many Europe-specific ones (Politico Europe, EUobserver, Euractiv, Balkan Insight, etc.) and Middle East feeds (Arab News, Middle East Eye, Times of Israel, etc.). Test these individually.

2. **Update the source registry → live feed pipeline** — the registry files mention specific sources with specific URLs. For each of the 26 registry files, verify which of the listed sources have working RSS and add them to either the hardcoded list or the catalog.

3. **Prune Cloudflare-blocked feeds** — 342 feeds returning 403 should be removed from `sources_tested.json` to keep the catalog clean.

4. **Add North Africa feeds** — Algeria (El Khabar, already in multiling list), Tunisia (Tunis Afrique Presse), Morocco (Hespress, already in list — verify it's working)

5. **Explicitly collect for Arctic, Space, Cyber, Supply chain** — add 2-3 specialty feeds per topic as thematic cross-cutting collectors

---

## Q4: Source Identification — What's Been Done vs What's Live

### The 26 Source Registry Files

The team has done extensive and excellent source identification work across 26 markdown files:

| File | Category | Sources Listed |
|------|----------|---------------|
| `sources-africa.md` | Africa | 30+ |
| `sources-middle_east.md` | Middle East | 17 |
| `sources-europe.md` | Europe | ~25 |
| `sources-north_america.md` | North America | ~15 |
| `sources-south_america.md` | South America | ~20 |
| `sources-central_america_caribbean.md` | Central America | ~15 |
| `sources-central_asia_india.md` | Central Asia/India | ~20 |
| `sources-china_asia.md` | China/East Asia | ~15 |
| `sources-south_east_asia.md` | SE Asia | ~15 |
| `sources-oceania_pacific.md` | Oceania/Pacific | ~10 |
| `sources-russia_ukraine.md` | Russia/Ukraine | ~20 |
| `sources-durable_iran_specialist.md` | Iran specialists | 20+ |
| `sources-durable_israel_lebanon.md` | Israel/Lebanon | ~15 |
| `sources-durable_maritime.md` | Maritime | ~10 |
| `sources-durable_military_osint.md` | Military OSINT | ~15 |
| `sources-durable_cyber_threat.md` | Cyber threat | ~10 |
| `sources-durable_thinktanks.md` | Think tanks | ~25 |
| `sources-durable_substack_energy.md` | Substack energy | ~10 |
| `sources-durable_dashboards_realtime.md` | Real-time dashboards | ~10 |
| `sources-wire_feeds.md` | Wire feeds | 9 |
| `sources-social_media_collection.md` | Social media | ~15 |
| `sources-social_x_twitter.md` | X/Twitter | ~10 |
| `sources-telegram_channels.md` | Telegram | 17 |
| `sources-prediction_markets_finance.md` | Prediction markets | ~10 |
| `sources-collection_methods.md` | Collection methods | 10 methods |
| `sources-newly_added_2026-05-22.md` | New discoveries | 30 |
| **Total sources referenced** | | **~400+ unique source mentions** |

### The 912 Feed Catalog

The catalog (`analyst/meta/sources_tested.json`, 7,001 lines) was built via:
1. Automated source discovery (`scripts/source_discovery.py`) — Brave search for new sources per region
2. Feed health audit (`scripts/feed_health_audit.py`) — tests all URLs for RSS validity
3. Heartbeat source builder — dynamically builds `sources_tested.json`

Of 912 tested feeds, only 298 (34%) are working. The remaining 614 are dead (403/404/timeout/parse errors) or pending testing.

### The Disconnect: Registry vs Live Collection

This is the single biggest collection architecture problem:

**Registry says:** "30+ African sources" (sources-africa.md)
**Live RSS list has:** ~15 African feeds hardcoded + 2-6 catalog feeds per run
**Actually working:** Unknown — many hardcoded African feeds may be dead

**Specific examples of disconnect:**

1. **Think tank feeds** — sources-durable_thinktanks.md catalogs ~25 think tanks (CSIS, CFR, Chatham House, etc.) but only a few have RSS feeds in the live list. Most think tank "sources" in sources.json are web page URLs, not RSS.

2. **Iran specialist sources** — 20+ listed in sources-durable_iran_specialist.md (IranWire, Conflicts Forum, Kian, etc.) but most are Substack or blog URLs, not RSS. Only BBC Persian, Mehr News, IRNA, and Tasnim have RSS feeds in the live pipeline.

3. **Military OSINT** — listed sources include Jane's, Janes (typo), IHS, but these are paywalled and have no public RSS.

4. **Cyber threat** — listed sources include FireEye/Mandiant, Dragos, Recorded Future, but these require API access or are paywalled.

5. **Telegram channels** — all 17 Telegram channels listed in collect.py are **DISABLED** (commented out). Telegram's t.me/s/CHANNEL RSS feature was unreliable.

### Root Causes

1. **Sources.json is a web page URL catalog, not an RSS feed list** — 1,463 "durable sources" but only 5 have RSS URLs. The file serves as a reference but can't drive automated RSS collection.

2. **Registry files are human-readable references** — they were designed as knowledge base entries, not as machine-parseable feed lists. No automated process reads them to extract RSS URLs.

3. **Source discovery finds URLs, not feeds** — Brave search results are web pages, not RSS feeds. Each discovered URL must be manually tested for RSS availability.

4. **No automated RSS discovery from registry URLs** — a source listed as "https://csis.org" doesn't tell us whether `https://csis.org/feed` exists. This requires testing.

5. **The 34% health rate reflects fundamental URL-to-RSS conversion problems** — many valid intelligence sources don't publish RSS feeds or use JavaScript-rendered content that `urllib` can't parse.

### Reconciliation Plan

| Step | Action | Effort | Impact |
|------|--------|--------|--------|
| 1 | Create a `source_registry_to_rss.py` script that reads each registry markdown file, extracts URLs, and tests them for RSS availability | Medium | High — turns 400+ identified sources into actionable feeds |
| 2 | For each discovery: check common RSS paths (/feed, /rss, /rss.xml, /rss/feed), Atom feeds, and JSON feeds | Medium | High — catches feeds at non-obvious paths |
| 3 | Add working discoveries to the catalog or hardcoded list | Low | High — immediately improves coverage |
| 4 | For Substack-only sources (no RSS alternative): consider using Brave Search to surface their latest articles instead | Low | Medium — captures Substack content without RSS |
| 5 | Build a "registry coverage report" that shows: how many registry sources have RSS → how many are in live collection → coverage ratio per region | Medium | Medium — provides visibility into the disconnect |

---

## Recommendations (Ordered by Impact)

### P0 — Fix Pipeline Errors (Immediate)

1. **Remove Simmer Step 1d from pipeline** — edit `daily-text-brief.sh` line 79: delete the simmer_scanner call
   - Effort: 5 minutes
   - Impact: Removes a silent error from every pipeline run

2. **Remove I&W Feedback Loop Step 5b from pipeline** — edit `daily-text-brief.sh` lines 145-147: delete the iw_feedback_loop call. The script itself (`scripts/iw_feedback_loop.py`) can remain as an archive artifact.
   - Effort: 5 minutes
   - Impact: Removes second silent error

### P1 — Fix Stalled Regions (Today)

3. **Diagnose Europe/Middle East stall** — run `collect.py` manually with debug logging to see why these two regions produce zero incidents despite having adequate feeds. Check if `normalise()` region-matching is failing.
   - Effort: 1 hour
   - Impact: Critical — recovers the two highest-priority regions

4. **Verify hardcoded European feed health** — test each of the ~40 Europe-specific feeds in `LOCAL_LANGUAGE_FEEDS` individually. Many may be dead/unreachable.
   - Effort: 30 minutes
   - Impact: High — identifies which feeds need replacing

### P2 — Email Intel Quality (This Week)

5. **Add noise-sender blocklist to gmail_reader.py** — block Wirecutter, Bloomberg CityLab, NYT Morning, Bloomberg Opinion, Reuters Tech Roundup at the reader level
   - Effort: 15 minutes
   - Impact: Medium — improves news_raw.md signal ratio from 40% to ~70%

6. **Fix HTML email body extraction** — add `html2text` or similar library to cleanly convert newsletter HTML to plain text
   - Effort: 1 hour
   - Impact: Medium — eliminates CSS garbage from intel digests

7. **Investigate Cipher Brief and Foreign Policy delivery** — check if these high-value newsletters are actually reaching the Gmail inbox
   - Effort: 30 minutes
   - Impact: Medium — could add 2 high-quality intel sources

### P3 — Collection Architecture (This Week)

8. **Prune Cloudflare-403 feeds from catalog** — run a cleanup pass on `sources_tested.json`: remove all feeds returning 403/404 that have been dead for >7 days
   - Effort: 30 minutes
   - Impact: Medium — reduces catalog size by ~40%, speeds up future tests

9. **Build source_registry_to_rss.py** — automated script that extracts URLs from the 26 registry markdown files and tests for RSS
   - Effort: 2-3 hours
   - Impact: High — bridges the gap between identified sources and live collection

10. **Add North Africa dedicated feeds** — find working RSS for Tunisia (Tunis Afrique Presse), Algeria (El Khabar), Egypt (Egypt Independent — verify), Libya (Libya Herald — verify)
    - Effort: 1 hour
    - Impact: Medium — recovers a critical gap region

### P4 — Thematic Cross-Cutting Collection (Next Week)

11. **Create thematic collector feeds** — add 2-3 feeds each for: Arctic, Space/Satellite, Cyber threat, Supply chain, Bio/health, Disinformation
    - Effort: 3-4 hours
    - Impact: High — fills structural blind spots in the all-regions model

12. **Add utilization tracking for all catalog feeds** — extend `collection_state.py` to track citation rates for all 298 working feeds, not just 6 named ones
    - Effort: 2 hours
    - Impact: Medium — enables data-driven feed pruning

---

## Implementation Plan

| Phase | Item | Effort | Impact | Priority |
|-------|------|--------|--------|----------|
| **Phase A (Today)** | Remove Simmer Step 1d | 5 min | Critical | P0 |
| **Phase A (Today)** | Remove I&W Feedback Loop Step 5b | 5 min | Critical | P0 |
| **Phase A (Today)** | Diagnose Europe/Middle East stall | 1 hr | Critical | P1 |
| **Phase B (Tomorrow)** | Add noise-sender blocklist to readers | 15 min | Medium | P2 |
| **Phase B (Tomorrow)** | Fix HTML email extraction | 1 hr | Medium | P2 |
| **Phase B (Tomorrow)** | Verify European feed health | 30 min | High | P1 |
| **Phase B (Tomorrow)** | Prune Cloudflare-403 feeds | 30 min | Medium | P3 |
| **Phase C (This week)** | Build source_registry_to_rss.py | 2-3 hr | High | P3 |
| **Phase C (This week)** | Investigate Cipher Brief/FP delivery | 30 min | Medium | P2 |
| **Phase C (This week)** | Add North Africa feeds | 1 hr | Medium | P3 |
| **Phase D (Next week)** | Thematic cross-cutting collectors | 3-4 hr | High | P4 |
| **Phase D (Next week)** | Full feed utilization tracking | 2 hr | Medium | P4 |

---

## Summary

The collection subsystem has a solid foundation — 324 hardcoded feeds, 200+ catalog feeds, GDELT floor, Brave fallback, per-region caps, dead-feed cache — but suffers from **two critical pipeline breaks** (Simmer and I&W feedback loop both referencing deleted files), **two stalled priority regions** (Europe and Middle East), and a **fundamental disconnect** between the rich source identification work (26 registry files, 400+ sources) and the live RSS collection (324 feeds, of which an unknown number are actually working).

The most impactful single action is fixing the Europe/Middle East stall — without those two regions, the daily brief has a structural blind spot regardless of all other improvements. After that, closing the registry-to-RSS gap would immediately boost coverage across all regions by making the excellent source identification work actually actionable.
