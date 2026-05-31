# Resilience, OSINT Quality & Continuous Improvement Plan

**Date:** 2026-05-31  
**Audit Type:** Deep-dive production system assessment  
**Scope:** Pipeline architecture, provider resilience, OSINT collection, analysis quality, continuous improvement

---

## Part 1: Pipeline Resilience & Autonomy

### Current State Assessment

**Architecture:**
- Bash shell orchestrator (`daily-text-brief.sh`, 284 lines) → Python orchestrator (`orchestrate.py`) → collector (`collect.py`, 1,561 lines) → analyzer (`analyze.py`, 890 lines) → quality gates (7 gates) → AgentMail delivery
- Lockfile prevents duplicate runs (flock-based)
- Quality gate runs AFTER orchestrator, BEFORE delivery (standalone bash step)
- Postdict + I&W feedback loop run after delivery (non-blocking)

**Critical Weaknesses:**

1. **SINGLE POINT OF FAILURE — DeepSeek V4 Pro via OpenRouter only.** The pipeline explicitly forbids fallback to Flash models (hardcoded guard in analyze.py line ~540: `if "flash" in model... return 2`). If OpenRouter has an outage, DeepSeek direct API timeout, or V4 Pro context window exhaustion, the entire pipeline fails. There is NO tier-3 fallback.

2. **No provider health check before pipeline starts.** The orchestrator checks env vars but never probes whether the API endpoint is responsive. A provider could be degraded before the first model call.

3. **No automatic retry.** If the orchestrator fails (rc != 0), the bash wrapper aborts entirely. No retry at 06:00 or 07:00 as previously specified. The pipeline runs once and either succeeds or fails.

4. **No circuit breaker for degraded providers.** A provider that fails on 3 consecutive calls gets retried the same way on every subsequent call. No degradation tracking, no routing table updates.

5. **No pipeline completion reporting to health engine.** The health engine (1229 lines) exists but the pipeline never publishes its status to `tasks/health-dashboard.json`. The health engine runs independently via cron but cannot correlate pipeline failures.

6. **Lockfile is a risk.** If a pipeline crashes mid-run (OOM, segfault, API timeout), the lock persists until manual cleanup. A new cron cycle will fail with "Another daily brief is already running."

### Multi-Provider Fallback Architecture

**Proposed design for `daily-brief-supervisor.py`:**

```
daily-brief-supervisor.py
├── Phase 0: Pre-flight health check
│   ├── Test OpenRouter (probe /api/v1/models with lightweight auth check)
│   ├── Test Anthropic Direct (probe with short completion)
│   ├── Test DeepSeek Direct API (probe with short completion)
│   └── Publish provider status to health engine
│
├── Phase 1: Source discovery + Kalshi + Simmer (unchanged)
│
├── Phase 2: Collection (unchanged - collect.py is network-only, no API dependency)
│
├── Phase 3: Analysis (with provider fallback chain)
│   ├── Regional analysis (10 regions)
│   │   ├── Tier 1: OpenRouter → DeepSeek V4 Pro
│   │   ├── Tier 2 (if Tier 1 fails): Anthropic Direct → Claude Sonnet 4.5
│   │   └── Tier 3 (if Tier 2 fails): DeepSeek Direct API → DeepSeek V4 Flash
│   │
│   ├── Executive summary
│   │   ├── Tier 1: OpenRouter → DeepSeek V4 Pro
│   │   ├── Tier 2 (if Tier 1 fails): Anthropic Direct → Claude Opus 4.7
│   │   └── Tier 3 (if Tier 2 fails): DeepSeek Direct API → DeepSeek V4 Pro (higher timeout)
│   │
│   ├── Red team analysis
│   │   ├── Tier 1: OpenRouter → DeepSeek V4 Pro
│   │   ├── Tier 2 (if Tier 1 fails): Anthropic Direct → Claude Sonnet 4.5
│   │   └── Tier 3 (if Tier 2 fails): DeepSeek Direct API → DeepSeek V4 Flash
│   │
│   └── Provider circuit breaker (per-call tracking in memory)
│       ├── Track: provider, model, success/failure, latency
│       ├── 3 consecutive failures → mark DEGRADED, skip to next tier
│       └── Recovery probe every 30 minutes → re-test degraded providers
│
├── Phase 4: Quality gate (unchanged - no API calls)
│
├── Phase 5: Delivery (unchanged - AgentMail)
│
├── Phase 6: Postdiction + I&W + calibration (unchanged)
│
└── Phase 7: Publish status to health engine dashboard
    ├── Pipeline completion status
    ├── Provider reliability metrics
    ├── Provider fallback chain used (which tiers were invoked)
    └── Alert on hard failures (health engine route)
```

**Provider routing table (configurable YAML):**

```yaml
# config/provider-routing.yaml
provider_routing:
  primary:
    openrouter:
      base_url: "https://openrouter.ai/api/v1"
      models:
        exec_summary: "deepseek/deepseek-v4-pro"
        regional_analysis: "deepseek/deepseek-v4-pro"
        red_team: "deepseek/deepseek-v4-pro"
        calibration_oracle: "anthropic/claude-opus-4.7"
      status: "active"
      circuit_breaker:
        consecutive_failures: 3
        recovery_interval_sec: 1800

  fallback_tier_1:
    anthropic_direct:
      base_url: "https://api.anthropic.com/v1"
      models:
        exec_summary: "claude-opus-4.7"
        regional_analysis: "claude-sonnet-4.5"
        red_team: "claude-sonnet-4.5"
      status: "active"
      circuit_breaker:
        consecutive_failures: 3
        recovery_interval_sec: 1800

  fallback_tier_2:
    deepseek_direct:
      base_url: "https://api.deepseek.com"
      models:
        exec_summary: "deepseek/deepseek-v4-pro"
        regional_analysis: "deepseek/deepseek-v4-flash"
        red_team: "deepseek/deepseek-v4-flash"
      status: "active"
      circuit_breaker:
        consecutive_failures: 3
        recovery_interval_sec: 1800
```

**Key design decisions:**
- Each region call is independently fallbackable — if 3 regions succeed and 1 fails, retry the failed region, not the whole batch
- Circuit breaker state is per-provider, not per-model — if OpenRouter is down, all OpenRouter calls skip to tier 2 immediately
- Recovery probes run in a background thread, not blocking the pipeline
- The pipeline logs WHICH tier was used for each step so the principal knows if fallback occurred

### Auto-Recovery Design

**Retry schedule (configurable in `config/pipeline-retry.yaml`):**

```yaml
pipeline_retry:
  schedule: "05:00 PT"
  retry_windows:
    - time: "06:00 PT"
      note: "First retry — 1h after initial failure"
      action: "full_retry"
    - time: "07:00 PT"
      note: "Second retry — 2h after initial failure"
      action: "full_retry"
    - time: "09:00 PT"
      note: "Final retry — 4h after initial failure"
      action: "skip_source_discovery"  # skip pre-collection steps
  after_final_retry: "escalate_to_health_dashboard"

regional_retry:
  max_attempts: 2
  per_region: true  # retry individual failing regions, not full batch
  backoff_seconds: 30
```

**Partial failure recovery:**
- If specific regions fail to analyze: retry with trimmed payload (reduce max_input_chars for that region)
- If quality gate WARNs (not BLOCK): auto-triage via rules engine:
  - "MISSING THEME" with only 1-2 missing and >>5 passing → override to PASS, log reason
  - "BLUF too short" with <20 words → check if alternative BLUF exists in regional files → use longest
  - "Truncation detected" → re-run exec summary with higher max_input_chars
- If quality gate BLOCKs: surface to principal via health dashboard alert

**State management for recovery:**
- Pipeline state file at `tasks/pipeline-state.json` tracks: last_run_status, failed_steps, retry_count, provider_degradations
- Health engine reads this to determine if escalation is needed
- Lockfile timeout: if pipeline holds lock > 90 minutes, assume stuck and auto-release

### Autonomous Brief Quality System

**Already granted authority (from AGENTS.md):**

The principal has already granted autonomous brief quality fixes. This needs implementation in `daily-brief-supervisor.py`:

1. **Quality gate BLOCK auto-diagnosis:**
   - Read `tasks/qc-alert.md` if it exists
   - If structural BLOCK (missing files): check if files exist with different names → symlink or copy
   - If fabrication BLOCK: scan for false positives (known safe sources, expected tickers) → override if confidence high
   - If completeness BLOCK (short BLUF): aggregate BLUF from regional narratives → create composite BLUF
   - If model violation BLOCK: re-run with correct model, do not abort

2. **Opus QC FAIL/CRITICAL auto-fix:**
   - Read the QC report from `tasks/qc-alert.md`
   - Map each QC finding to an automated fix action
   - Re-run the specific pipeline step that produced the bad output
   - Re-run quality gate
   - Re-deliver if gate passes
   - Log the auto-fix to `tasks/auto-fix-log.jsonl`

3. **Common auto-fix catalog:**
   | Problem | Fix | Confidence |
   |---------|-----|-----------|
   | Model downgrade (Flash vs Pro) | Re-run with `--model deepseek/deepseek-v4-pro` | High |
   | Truncated output | Re-run with higher `max_input_chars` | High |
   | Missing region files | Re-run analyze.py with `--regions-override [missing]` | Medium |
   | Wrong-region KJs | Re-run with stronger region constraint in prompt | Low (surface) |
   | Calibration band mismatch | Re-run with strict band enforcement in prompt | Medium |

4. **Re-delivery on auto-fix:**
   - If fix is applied and quality gate passes → re-send via AgentMail with subject "CORRECTED: ..."
   - Do NOT suppress the original delivery if it already went out — the corrected version supplements it

### Implementation: `daily-brief-supervisor.py` (Spec)

**Location:** `scripts/daily-brief-supervisor.py`  
**Entry point:** Replaces `daily-text-brief.sh` as the orchestrator (or is called FROM the bash orchestrator)  
**Design pattern:** State machine with phase transitions

```python
# Pseudocode architecture

class PipelineSupervisor:
    def __init__(self):
        self.providers = ProviderPool(config_path)
        self.circuit_breaker = CircuitBreaker(config_path)
        self.state = PipelineState(tasks_dir)
        self.health = HealthEngineClient(tasks_dir)
    
    def run(self):
        # Phase 0: Pre-flight
        health = self.check_provider_health()
        self.health.publish_providers(health)
        
        if all_degraded(health):
            self.escalate("ALL_PROVIDERS_DEGRADED")
            return EXIT_FAIL
        
        # Phase 1: Source discovery (unchanged)
        if not self.run_pre_collection():
            log("pre-collection warnings (non-fatal)")
        
        # Phase 2: Collection (unchanged)
        incidents = self.run_collector()
        
        # Phase 3: Analysis with fallback
        analysis = {}
        for region in REGIONS:
            for attempt in range(MAX_RETRIES):
                provider = self.providers.next_for("regional_analysis")
                result = provider.call_analysis(region, incidents)
                if result.success:
                    analysis[region] = result.data
                    break
                self.circuit_breaker.record_failure(provider.name)
        
        # Phase 4: Quality gate
        gate_result = self.run_quality_gate(analysis)
        if gate_result.blocked:
            auto_fix = self.auto_diagnose_and_fix(gate_result)
            if auto_fix.applied:
                gate_result = self.run_quality_gate(analysis)  # re-check
        
        # Phase 5: Delivery
        if gate_result.passed:
            self.deliver(analysis)
        
        # Phase 6: Postdiction + calibration (non-blocking)
        self.run_postdict_if_possible()
        
        # Phase 7: Publish status
        self.health.publish_pipeline({
            "status": "success" if gate_result.passed else "blocked",
            "provider_fallbacks": self.providers.fallback_log,
            "circuit_breaker_state": self.circuit_breaker.dump(),
            "quality_gate": gate_result,
        })
```

**Configuration files needed:**
- `config/provider-routing.yaml` — provider chain, models, circuit breaker thresholds
- `config/pipeline-retry.yaml` — retry schedule, backoff, escalation rules
- `config/auto-fix-rules.yaml` — quality gate auto-fix mapping

**Logging:**
- Structured JSONL at `logs/pipeline-supervisor/YYYY-MM-DD.jsonl`
- Each log entry: phase, step, provider, success/failure, latency, notes
- Summary at `tasks/pipeline-state.json`

---

## Part 2: OSINT Collection & Analysis Assessment

### Feed Health Assessment

**Current metrics (from latest audit, 2026-05-31):**

| Metric | Value |
|--------|-------|
| Total feeds in catalog | 912 |
| Tested so far | 200/780 |
| Working | 68 (34%) |
| Dead | 132 (66%) |
| Projected final health | ~34% |
| Health rate last full audit (2026-05-23) | 51.7% (215/416) — partial |
| Cloudflare/403 blocked | ~342 feeds |

**Critical observations:**

1. **Feed health is DECLINING.** The 2026-05-23 full audit found 51.7% health (215/416). The 2026-05-31 partial audit shows 34% health (68/200). This suggests accelerated feed attrition — likely from sites changing their RSS infrastructure or implementing WAFs.

2. **Only 6 sources tracked in collection-state.json.** The collection state manager only tracks `KNOWN_SOURCES = ["Reuters World", "AP World", "BBC World", "Al Jazeera", "Reuters Business", "FT World"]`. This means the entire adaptive collection system (source utilization tracking, per-region caps, auto-prioritization) only monitors 6 sources out of 912. The other 906 feeds have zero impact on collection decisions.

3. **Feed pruning is incomplete.** The heartbeat Phase C pruned 49 dead feeds from a manual list of 50. The `--prune` flag in `feed_health_audit.py` only removes from `collect.py` hardcoded list, not from `sources_tested.json` catalog. There's no automated pruning of the 342+ Cloudflare-blocked feeds.

4. **Feed testing frequency:** The heartbeat state shows "Phases A-D completed" on 2026-05-23, but the feed health script appears to run on-demand, not on a regular schedule. There's no weekly/monthly feed health rotation.

5. **No noise filtering among working feeds.** Even feeds that return 200 OK may return 0 items or stale content. The audit only tracks "working" vs "dead" — not "useful" vs "noise."

**Recommendations:**

1. **Extend source tracking to all feeds.** The `collection_state.py` script's `KNOWN_SOURCES` list needs to source from the actual feed catalog (12+ regions × ~80 feeds each = ~960 feeds). A feasible approach: track at the REGION level (which regions have high citation rates from their feeds) rather than individual feed level.

2. **Implement graduated feed rotation:**
   - Weekly: test 100 feeds from catalog (random sample)
   - Monthly: full catalog test (or 50%, alternating)
   - Quarterly: prune feeds that have been dead for >2 consecutive monthly tests
   - Auto-demote feeds with 0 citations after 30 consecutive collection runs

3. **Cloudflare WAF mitigation:**
   - Add `User-Agent` rotation to feed fetches
   - Add `Accept: application/rss+xml` header (already present)
   - Log CF challenge pages separately (not just "HTTP 403") to distinguish WAF blocks from actual dead feeds
   - Consider using browser automation (browser-automation skill) for feeds that require JS rendering

4. **Content quality scoring for working feeds** (see Part 3 for scoring system):

### Regional Coverage Assessment (Gap Analysis)

**Current source lists by region (from brain/memory/semantic/sources-*.md):**

| Region | Sources File | Feed Count | Quality | Gap Level |
|--------|-------------|------------|---------|-----------|
| Europe | `sources-europe.md` | ~12 feeds | Moderate — 5 major EU + markets | Low |
| North America | `sources-north_america.md` | — | Major wires standardized | Low |
| Central America/Caribbean | `sources-central_america_caribbean.md` | — | Not well characterized | MEDIUM |
| South America | — | ~10 feeds (in collect.py) | Spanish/Portuguese newspapers | MEDIUM |
| Middle East | `sources-middle_east.md` | — | Jerusalem Post + Arab News + Farsi | Moderate |
| Africa | `sources-africa.md` | ~30+ feeds | Strongest non-major coverage | LOW-MEDIUM |
| Russia/Ukraine | `sources-russia_ukraine.md` | — | Meduza, TASS, Moscow Times | Moderate |
| Central Asia/India | `sources-central_asia_india.md` | ~10 feeds | The Diplomat, Dawn, Times of India, Carnegie | MEDIUM-HIGH |
| China/East Asia | `sources-china_asia.md` | — | SCMP, Xinhua, The Diplomat | Moderate |
| Southeast Asia | — | ~10 feeds | VN Express, PhilStar, Rappler, ASEAN | MEDIUM |
| South Asia | — | — | Covered by central_asia file | Moderate |
| Oceania/Pacific | `sources-oceania_pacific.md` | ~6 feeds | ASPI, SMH, RNZ, Devpolicy | MEDIUM |
| Prediction Markets | `sources-prediction_markets_finance.md` | — | Kalshi + Polymarket scripts | Good |

**Collection state activity scores (from collection-state.json region_activity):**

| Region | Smoothed Score | Latest Count | Trend |
|--------|---------------|-------------|-------|
| Europe | 87.1 | 0 | STALLED (was 30+) |
| Middle East | 60.5 | 0 | STALLED |
| North America | 55.7 | 13 | Active |
| Sub-Saharan Africa | 22.8 | 8 | Active |
| East Asia | 13.9 | 5 | Active |
| South Asia | 14.4 | 5 | Active |
| Southeast Asia | 10.1 | 4 | Active |
| Oceania | 9.6 | 4 | Active |
| South America | 7.5 | 3 | Active |
| Central America/Caribbean | 6.7 | 3 | Active |
| Central Asia | 5.2 | 3 | Active |
| Prediction Markets | 4.8 | 3 | Active |
| North Africa | 1.9 | 0 | STALLED |
| Global Finance | 0.3 | 0 | STATIC |
| Asia (generic) | 0.3 | 0 | STATIC |

**Gap Analysis:**

- **THINNEST REGIONS:**
  1. **Central Asia** — only 3 latest incidents, smoothed 5.2. One of the most geopolitically consequential regions (China Belt & Road, Russia influence, Kazakhstan energy, Afghanistan) with the thinnest coverage.
  2. **North Africa** — smoothed 1.9, latest 0. Completely stalled. Despite proximity to Europe/Middle East crises, barely any collection.
  3. **Central America/Caribbean** — smoothed 6.7, only 3 latest. Critical for US migration, nearshoring, and cartel routes.
  4. **Global Finance** — smoothed 0.3, latest 0. Completely dead despite prediction_markets script existing separately.
  5. **Asia (generic)** — smoothed 0.3, seems like a catch-all for unmatched incidents. Should be eliminated.

- **BEST-SERVED REGIONS:**
  1. **Europe** — historical peak of 30+ incidents/run, 87 smoothed score. Has been stalling in latest runs (0 count), but historically strongest.
  2. **Middle East** — 60.5 smoothed. Strong historical coverage, stalling recently.
  3. **Africa** — 22.8 smoothed, 30+ feeds in the file. Diverse coverage across Sub-Saharan continent.

- **NOTABLE GAPS:**
  - **Arctic/Northern Sea Route:** Zero coverage despite growing strategic importance
  - **Space/Satellite security:** No dedicated feeds despite LEO ground stations being an active assignment
  - **Cyber threat intelligence:** No dedicated cyber threat feeds in regional collection (separate durable lists exist but not integrated)
  - **Supply chain security:** None, despite semiconductor being an active assignment
  - **Bio/health security:** None
  - **Disinformation tracking:** None

**Recommendations:**

1. **Fix stalled regions.** Europe, Middle East, and North Africa all show latest=0 despite high smoothed scores. This indicates either feed failures or collection script issues. Investigate whether these regions' feed groups are returning errors.

2. **Bulk up Central Asia.** Need at least 10-15 feeds: Kazakh/ Uzbek news in English, CACI Analyst, The Diplomat Central Asia, Eurasianet, RFE/RL Central Asia, Nagorno-Karabakh monitoring, Afghanistan-focused OSINT.

3. **Revive North Africa.** Algeria, Morocco, Tunisia, Libya, Egypt all are geopolitically significant with near-zero coverage. Add Maghreb-focused feeds: The Arab Weekly, Libya Herald, Tunisia-focused blogs.

4. **Add thematic cross-cutting feeds for active assignments:**
   - Supply chain: does not exist in any region's collection
   - Cybersecurity: only in separate durable list, not integrated into daily collection
   - Space/Satellite: needed for LEO ground stations assignment

5. **Remove the "asia" generic region** — it conflates East Asia, South Asia, and Central Asia incidents into an untrackable bucket.

### Collection-to-Analysis Pipeline

**How collect.py works:**
- Reads 259+ RSS feeds (hardcoded in collect.py + wire feeds + local-language feeds)
- Plus ~912 catalog feeds from `sources_tested.json` (dynamic source builder)
- Pulls last 24 hours of content via RSS/HTTP
- Normalizes into `incidents.json` with region tags
- Also runs: GDELT collection floor (non-fatal), email intel injection, OpenWeb pipeline
- Total: ~1561 lines of Python

**How analyze.py processes:**
- Reads incidents.json
- Calls DeepSeek V4 Pro once per region (10 regions currently: REGIONS_ORDER shows europe, north_america, central_america_caribbean, south_america, north_africa, sub_saharan_africa, middle_east, central_asia, south_east_asia, east_asia, south_asia, oceania, prediction_markets)
- Each call includes: incidents for the region, I&W board (if exists), collection quality assessment, calibration feedback, brain recall context
- Then calls exec summary (aggregates all 10 regions)
- Then calls red team (focuses on highest-incident region)
- Each regional analysis call sends 18KB-60KB of prompt data
- Models: V4 Pro for ALL tiers, via OpenRouter

**Key issues:**

1. **Memory exhaustion risk for exec summary.** The exec summary prompt includes ALL 10+ regional payloads as JSON (size: 60KB+). V4 Pro has a 64K context window. This leaves almost no room for the response. The `max_input_chars=60000` setting is dangerously close to the context limit.

2. **No collection-to-citation tracking at scale.** Only 6 sources tracked. No way to answer "which feeds produce the most cited KJs?"

3. **RSS-only collection.** No web search integration in the collector (web search exists in `source_discovery.py` but is pre-collection, not in-line). Breaking news that's not in an RSS feed won't be collected.

4. **24-hour window is rigid.** Breaking news at 04:59 PT (just before the 05:00 collection) gets only 1 minute of coverage. The GDELT floor mitigates this slightly but is non-fatal and often unavailable.

**Recommendations:**

1. **Reduce exec summary prompt bloat.** Instead of sending full 10+ regional JSON payloads, send: (a) region labels and incident counts, (b) top 3 KJs per region (summary form), (c) BLUF-level abstractions. This cuts prompt from 60KB to ~15KB.

2. **Implement citation tracking for all feeds.** Extend `KNOWN_SOURCES` to include source names extracted from incidents.json. Use the source `name` field from each incident's `sources` array.

3. **Add web search fallback during collection.** After RSS pull, if a region has <3 incidents, do a Brave search for that region's top news. This closes the gap for thin regions.

4. **Stagger collection windows.** Run a mini-collection at 23:00 PT and 02:00 PT that picks up overnight events, then the 05:00 PT collection merges with the earlier stash.

### Analysis Quality Assessment

**Calibration accuracy is CRITICAL:**

| Metric | Value | Verdict |
|--------|-------|---------|
| Total judgments | 115 | Sample size adequate |
| Correct | 3 (2.6%) | DISASTROUS |
| Incorrect | 42 (36.5%) | Very high |
| Unresolved | 60 (52.2%) | Horizon not elapsed |
| Effective accuracy (correct + resolved) | 3 / 45 = 6.7% | ABYSMAL |
| Bands used | Only "likely" for all 115 | No band diversity |
| Overconfidence | Severe — all at "likely" (55-70%) when actual rate is ~7% | |

**Key findings:**

1. **Every single judgment uses the verbal band "likely".** The calibration gate checks Sherman Kent ↔ numeric alignment but doesn't enforce band DIVERSITY. The `calibration_smell_check` in `orchestrate.py` flags this ("only 1 distinct prediction value across 115 judgments"), but it's non-blocking.

2. **Calibration feedback loop is disconnected.** The `calibration-tracking.json` shows 115 judgments, 3 correct, 42 incorrect — but this data isn't effectively shaping the prompts. The behavioral-state.json (generated 2026-05-13) has `posture: "widen_two_notches"` and `accuracy_pct: 6.7` — but this was generated 18 days ago and may not be injected into current prompts.

3. **Red team analysis is narrow.** The red team targets only the region with the highest incident count. This means the red team never challenges judgments from thin-data regions, which is where red team adds the most value.

4. **Opus QC runs post-delivery.** The `opus_qc_review.py` script runs after the brief is delivered. Findings go to `tasks/qc-alert.md` but by then the bad brief is already in the principal's inbox.

**Recommendations:**

1. **Enforce band diversity in calibration gate.** Add a WARN-level check: if >70% of KJs use the same band, BLOCK delivery. This forces the model to think harder about which band to use.

2. **Fix the behavioral state injection.** The behavioral-state.json was generated on 2026-05-13 and hasn't been refreshed. The pipeline should regenerate it from calibration-tracking.json before each brief run.

3. **Move Opus QC to PRE-delivery.** Run QC between quality gate and AgentMail delivery. If QC finds FAIL/CRITICAL, block delivery and trigger auto-fix.

4. **Expand red team to 2-3 regions.** Pick the most judgment-dense regions plus the thinnest-data region. Red teaming only the highest-incident region is safe but misses where challenge adds value.

5. **Address the calibration accuracy root cause.** 6.7% accuracy suggests the model is not calibrated for this task. Options:
   - Use a different model for KJs (Claude Opus for calibration oracle)
   - Train the model with explicit calibration examples in the prompt
   - Reduce the number of KJs per region from ~5 to ~2-3 (forcing selectivity)
   - Add a "prediction guard" that caps any KJ at 50% unless supported by ≥2 independently-sourced incidents

---

## Part 3: Continuous Improvement Framework

### Source Scoring System

**Proposed design: `analyst/meta/source-scoring.json`**

```json
{
  "version": 1,
  "last_updated": "2026-05-31T00:00:00Z",
  "sources": {
    "BBC World": {
      "score": 7,
      "subscores": {
        "reliability": 8,    // uptime, response time, parse success rate
        "relevance": 6,      // how often cited in briefs
        "freshness": 9,      // how recent are articles (median age in hours)
        "diversity": 5,      // unique perspective vs echo chamber
        "latency": 7         // page load / API response time
      },
      "last_working": "2026-05-31",
      "days_since_citation": 1,
      "citations_total": 5,
      "consecutive_zero_citations": 1,
      "utilization_pct": 11.1,
      "score_30_day_avg": 7.2,
      "region": "global",
      "auto_demote_at_score": 3,
      "status": "active"
    },
    "Reuters World": {
      "score": 1,
      "subscores": {
        "reliability": 1,    // dead feed
        "relevance": 0,
        "freshness": 0,
        "diversity": 0,
        "latency": 0
      },
      "last_working": "2026-04-15",
      "days_since_citation": 44,
      "utilization_pct": 0,
      "consecutive_zero_citations": 44,
      "auto_demote_at_score": 3,
      "status": "dead",
      "next_action": "check_if_replacement_exists"
    }
  }
}
```

**Scoring formula:**

```
reliability (weight 0.30):
  - uptime_pct * 10
  - penalty: -1 per 100ms over 3s response time
relevance (weight 0.30):
  - min(10, citations_per_30_days * 2)
  - bonus: +1 if cited in last 7 days
freshness (weight 0.20):
  - min(10, max(0, 10 - median_age_hours / 6))
  - feeds with median < 6h get 10
diversity (weight 0.10):
  - 10 if unique domain / perspective
  - 5 if duplicates major wire / official
  - 2 if government-controlled outlet
  - manual override available
latency (weight 0.10):
  - 10 if < 1s
  - 7 if 1-3s
  - 4 if 3-5s
  - 1 if > 5s or timeout

total = weighted sum
```

**Auto-demotion rules:**
- Score < 3 for 30 consecutive days → auto-remove from active rotation
- Score < 5 for 60 days → move to "probation" list, only included in region rotation 1/week
- Dead feeds (score = 0 for reliability) → immediate removal, add to graveyard
- Re-discovery: demoted feeds are added to a "re-evaluation queue" checked monthly

### Source Discovery Automation

**Current state:** `source_discovery.py` runs pre-collection with Brave Search queries for 7 coverage areas. It finds Substack, independent analyst blogs, and institutional sources. However, the 2026-05-23 heartbeat showed "BRAVE_API_KEY not set — all web searches skipped."

**Proposed enhancements:**

1. **RSS cross-linking discovery:**
   - When collecting from a feed, parse its `<link>` elements for blogrolls, related feeds, and recommended sources
   - Track cross-references: if feed A links to feed B ≥3 times, add B to discovery queue
   - Implementation: 50-line addition to `collect.py` in the RSS parsing section

2. **Automatic think tank monitoring:**
   - Maintain a list of 30+ major think tanks (CSIS, Chatham House, IISS, Carnegie, RAND, Brookings, etc.)
   - Weekly: check each for new publications via their RSS feeds
   - If a publication covers an underserved region/theme, auto-add to catalog
   - Implementation: `scripts/discover_thinktank_feeds.py` (already partially exists in durable sources)

3. **Academic journal monitoring:**
   - Security studies journals: International Security, Security Studies, Journal of Peace Research, etc.
   - Most don't have RSS — use TOC alerts or web scraping
   - Low priority: quarterly refinement only

4. **Twitter/X account monitoring (via browser automation):**
   - Browser-automation skill is already installed
   - For each region, maintain a list of 5-10 OSINT/X accounts
   - Weekly browser session: check for new accounts followed / retweeted by known good accounts
   - Output: candidate accounts with their recent coverage topics

5. **Feedback integration:**
   - When analysis identifies a "gap" in coverage (e.g., "No data from independent Kurdish sources"), convert that gap into a discovery query
   - Source discovery uses the gap as a search query next run
   - Implementation: add `identified_gaps` from collection-state.json as input to discovery queries

**Discovery schedule:**
- **Daily:** Cross-linking discovery (background, low-cost)
- **Weekly:** Think tank check, academic journal check, Brave search for gap regions
- **Monthly:** Full discovery cycle (all regions, browser X monitoring, graveyard re-evaluation)

### Quality Metrics Dashboard

**Design: `analyst/meta/quality-metrics.json`**

```json
{
  "version": 1,
  "last_updated": "2026-05-31T00:00:00Z",
  "daily_brief": {
    "quality_score": 0.85,
    "trend_7d": [0.82, 0.85, 0.79, 0.88, 0.85, 0.83, 0.85],
    "gate_results_history": [
      {"date": "2026-05-31", "structural": "PASS", "fabrication": "PASS", 
       "themes": "PASS", "calibration": "WARN", "completeness": "PASS",
       "scope": "PASS", "red_team": "PASS"}
    ]
  },
  "feed_health": {
    "pct_working": 34.0,
    "pct_working_7d_avg": [47.2, 44.1, 41.3, 38.9, 36.5, 34.8, 34.0],
    "total_feeds": 912,
    "active_feeds": 298,
    "trend": "declining",
    "last_full_audit": "2026-05-23"
  },
  "source_utilization": {
    "collection_to_citation_ratio": 0.07,
    "citation_rate_by_region": {
      "europe": 0.05,
      "middle_east": 0.12,
      "north_america": 0.08,
      ...
    },
    "zero_citation_sources_pct": 66.7,
    "top_10_sources_by_citation": ["Al Jazeera (12)", "BBC World (5)", "FT World (1)"]
  },
  "calibration": {
    "total_judgments": 115,
    "accuracy_pct": 6.7,
    "correct": 3,
    "incorrect": 42,
    "unresolved": 60,
    "band_diversity": 1,
    "overconfidence_regions": ["all"],
    "calibration_score": "CRITICAL",
    "needs_attention": true
  },
  "provider_reliability": {
    "openrouter": {"successes": 120, "failures": 3, "uptime_pct": 97.5},
    "deepseek_direct": {"successes": 0, "failures": 5, "uptime_pct": 0.0},
    "anthropic_direct": {"successes": 0, "failures": 0, "uptime_pct": 100.0}
  }
}
```

**Weekly quality report (generated by `scripts/generate_weekly_quality_report.py`):**

```
=== TREVOR WEEKLY QUALITY REPORT — 2026-05-25 to 2026-05-31 ===

BRIEF QUALITY:
  Avg quality score: 0.84 (stable ↔)
  Gates passed: 5/7 days (2 WARN days)
  Most common gate issue: Calibration WARN (band diversity)

FEED HEALTH:
  Working feeds: 34% (down from 47% last week) ↓
  Dead feed rate: +13% week-over-week
  Feeds pruned: 49 last week, 0 this week

CALIBRATION:
  Judgments this week: 35 (projected)
  Accuracy this week: N/A (<7d horizon)
  All-time accuracy: 6.7% — CRITICAL
  Band diversity: 1/8 bands used

SOURCE UTILIZATION:
  Collection→citation ratio: 7% (93% of collected content is ignored)
  Zero-citation sources: 66.7%
  Most cited source: Al Jazeera (12 total citations)

PROVIDER RELIABILITY:
  OpenRouter: 97.5% uptime — OK
  DeepSeek Direct: 401 errors (key issue) — NEEDS INVESTIGATION

RECOMMENDATIONS:
  1. Prune zero-citation sources with >30 consecutive failures
  2. Investigate Europe/Middle East stalled collection
  3. Re-run calibration behavioral state generation
  4. Consider reducing KJs per region to improve per-judgment quality
```

### Feedback Loop Integration

**Current state:**

| Loop | Exists? | Quality | Gap |
|------|---------|---------|-----|
| Postdiction → Calibration | ✅ | PARTIAL | Tracks but doesn't meaningfully improve accuracy |
| Calibration → Prompt | ✅ | WEAK | behavioral-state.json injects directives but 18 days stale |
| Source Discovery → Inclusion | ❌ | NONE | Discovery runs but has no scoring → no automated inclusion |
| Brief Quality → Prompt Template | ❌ | NONE | Ad-hoc, not structured |
| Provider Reliability → Routing | ❌ | NONE | Doesn't exist at all |

**Proposed integration:**

1. **Postdiction → Calibration → Prompt (AUTOMATE):**
   - Postdiction updates `calibration-tracking.json` daily
   - After update, `compile_calibration_directives.py` runs automatically (currently runs during pre-collection)
   - Output goes to `behavioral-state.json` (currently doesn't — behavioral-state is 18 days stale)
   - Behavioral-state is injected into analyze.py system prompt via `--behavioral-state` flag
   - **Fix:** The `compile_calibration_directives.py` MUST write to `behavioral-state.json`, not just stdout. Currently it writes calibration directives to a separate file and behavioral-state.json is only updated manually.

2. **Source Discovery → Quality Scoring → Inclusion/Rejection (AUTOMATE):**
   - Source discovery outputs candidate feeds with: name, URL, region, reason
   - Quality scoring system evaluates candidate: test RSS feed, check for content, estimate region fit
   - If score ≥ 6: auto-add to `sources_tested.json` catalog
   - If score 3-5: add to "trial" list, test again in 7 days
   - If score < 3: drop, log reason
   - **Implementation:** 200-line addition to `source_discovery.py` or new `scripts/evaluate_discovered_sources.py`

3. **Brief Quality → Prompt Template Refinement (STRUCTURED):**
   - Track which quality gate failures recur across briefs
   - Example: "band diversity WARN" recurring → update deepseek-prompts.md with stronger band diversity instruction
   - Each gate failure becomes a prompt improvement candidate
   - Monthly: review all quality gate failures from the month, compile prompt template improvements
   - **Implementation:** `scripts/review_quality_failures.py` — reads 30 days of quality gate history, produces prompt recommendations

4. **Provider Reliability → Routing Table Updates (AUTOMATE):**
   - Circuit breaker records: provider, model, success rate, latency
   - If provider has < 70% success rate over 7 days → auto-demote from primary to fallback
   - If provider has < 50% success rate over 7 days → auto-remove, notify principal
   - If a fallback provider has > 98% success rate over 14 days → promote to primary
   - **Implementation:** Part of `daily-brief-supervisor.py` provider pool

**Full feedback integration diagram:**

```
Collection → Quality Scoring → Prune/Add Sources
             ↓
Collection → Analysis (KJs with confidence bands)
             ↓
        Quality Gates (7 checks)
             ↓
        AgentMail Delivery
             ↓
        Opus QC (post-delivery audit)
             ↓
        Postdiction (next day's data)
             ↓
        Calibration Tracking (accuracy %)
             ↓
        CompileDirectives (behavioral-state.json)
             ↓
        Prompt Template Refinement ← ─ Quality gate failure patterns
             ↓
        Next Day's Analysis (injected calibration feedback)
             ↓
        Provider Circuit Breaker ← ─ Failure tracking per provider
```

---

## Implementation Roadmap

| Phase | Item | Effort | Impact | Dependencies |
|-------|------|--------|--------|-------------|
| **P1** | Fix stalled Europe/Middle East collection | 1h | HIGH — restores coverage for 2 most important regions | None |
| **P1** | Regenerate behavioral-state.json from calibration data | 1h | HIGH — fixes calibration feedback loop | Postdiction must have run for at least 1 day |
| **P1** | Move Opus QC to pre-delivery | 2h | HIGH — catches failures before principal sees them | None |
| **P2** | Extend source tracking from 6 to all sources | 3h | HIGH — enables feed utilization metrics | Collection state format change |
| **P2** | Implement band diversity enforcement in calibration gate | 2h | HIGH — prevents 100% "likely" band misuse | None |
| **P2** | Trim exec summary prompt (aggregate instead of full JSON) | 3h | MEDIUM — prevents context window issues | Prompt template changes |
| **P2** | Add provider health check phase | 4h | HIGH — enables fallback chain | Provider routing config |
| **P3** | Build daily-brief-supervisor.py (Phase 0, 7, circuit breaker) | 20h | VERY HIGH — full resilience architecture | All P1-P2 items |
| **P3** | Replace bash orchestrator with Python supervisor | 8h | HIGH — enables retry logic + health reporting | P3 supervisor skeleton |
| **P3** | Add Anthropic Direct as fallback provider | 4h | HIGH — adds provider diversity | API key validation |
| **P3** | Build quality-metrics.json dashboard | 4h | MEDIUM — enables trend tracking | P2 source tracking |
| **P3** | Implement auto-retry for failing regions | 6h | MEDIUM — graceful degradation | P3 supervisor |
| **P4** | Source scoring system (full implementation) | 10h | MEDIUM — enables auto-pruning | P2 source tracking |
| **P4** | Automatic postdiction → calibration → prompt loop | 4h | MEDIUM — closes the feedback loop | P1 behavioral-state regeneration |
| **P4** | Web search fallback during collection | 6h | MEDIUM — fills thin region gaps | Brave API key must be set |
| **P4** | Cross-linking RSS discovery | 4h | MEDIUM — automated source discovery | Collector RSS parsing |
| **P5** | Weekly quality report generator | 4h | LOW — monitoring improvement | All P2-P4 metrics |
| **P5** | Arcitc/Space/Cyber thematic feed addition | 3h | MEDIUM — closes known gaps | None |
| **P5** | Auto-recovery on hard failure (retry schedule) | 6h | LOW — safety net | P3 supervisor + retry config |
| **P6** | Calibration accuracy improvement (reduce KJs, better model) | 8h | VERY HIGH — fixes 6.7% accuracy crisis | Prompt redesign + model selection |

**Phase definitions:**
- **P1 (URGENT):** Fixes acute failures (stalled collection, broken calibration feedback). Do this week.
- **P2 (SHORT-TERM):** Quality improvements and essential metrics. Do next week.
- **P3 (MEDIUM-TERM):** Resilience architecture and provider fallback. 2-4 weeks.
- **P4 (MEDIUM-TERM):** Continuous improvement loops. 3-6 weeks.
- **P5 (LONG-TERM):** Advanced features and trend monitoring. 6-12 weeks.
- **P6 (ONGOING):** Calibration accuracy is the hardest problem. Treat as continuous improvement.

---

## Summary

| Area | Current Grade | Target Grade | Key Gap |
|------|--------------|-------------|---------|
| **Pipeline Resilience** | **2/10** | **8/10** | No provider fallback, no retry, no health reporting. A single OpenRouter outage kills the brief. |
| **OSINT Collection** | **5/10** | **8/10** | Europe/ME stalled, 34% feed health declining, only 6/912 sources tracked, no thematic cross-cutting feeds. |
| **Analysis Quality** | **6/10** | **9/10** | Excellent structural design (7 gates, I&W, calibration tracking) but 6.7% calibration accuracy is a crisis. Band diversity is nonexistent. |
| **Continuous Improvement** | **2/10** | **7/10** | Source discovery exists but is disconnected from inclusion. Calibration feedback is 18 days stale. No quality metrics dashboard. No provider reliability tracking. |

**Most critical actions (this week):**
1. Fix Europe/Middle East stalled collection — check feed health and collector output
2. Regenerate behavioral-state.json from calibration-tracking.json
3. Move Opus QC to pre-delivery
4. Enforce band diversity in calibration gate
5. Extend source tracking to all feeds (not just 6 hardcoded)

**The single biggest ROI:** Fixing calibration accuracy. If the system produces judgments that are 93% wrong, nothing else matters. Reduce KJ count, use Claude Opus for calibration oracle, enforce band diversity, and add single-source caps. Everything else is secondary.

---

*Generated by Trevor subagent during pipeline resilience audit, 2026-05-31*
