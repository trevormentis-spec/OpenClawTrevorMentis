# Brief Schema v1.0.0 — Open Claw Mexico

**Version:** 1.1.0
**Status:** Stable contract
**Updated:** 2026-05-18 23:00 UTC
**Consumed by:** PDF renderer, audio renderer, Folium mapping, external API consumers

---

## Schema Overview

```json
{
  "schema_version": "1.1.0",
  "brief_id": "uuid-v4",
  "query_type": "enum",
  "produced_at": "ISO-8601",
  "producer": "Open Claw Mexico desk",
  "bluf": "string",
  "calibration": { "band": "enum", "pct_range": [int, int] },
  "headline_judgments": [Judgment],
  "sections": [Section],
  "watch_items": [WatchItem],
  "trade_positions": [TradePosition],
  "gaps": [Gap],
  "action_lines": [ActionLine],
  "sources": [Source],
  "meta": { Metadata },
  "generation_metadata": { GenerationMetadata },
  "custom": {}  // reserved for industry-vertical extensions
}
```

---

## Enums

### kent_band (Sherman Kent confidence ladder)

```
"almost_certain"    85%+
"highly_likely"     70-85%
"likely"            60-70%
"probable"          50-60%
"even_chance"       40-50%
"unlikely"          15-40%
"highly_unlikely"   5-15%
"remote"            <5%
```

### admiralty_grade (NATO Admiralty source ratings)

```
"A-1"  Confirmed by other sources; reliable
"A-2"  Probably true; reliable
"A-3"  Possibly true; reliable
"B-1"  Confirmed by other sources; fairly reliable
"B-2"  Probably true; fairly reliable
"B-3"  Possibly true; fairly reliable
"C-1"  Confirmed by other sources; not usually reliable
"C-2"  Probably true; not usually reliable
"C-3"  Possibly true; not usually reliable
"D"    Not assessed / cannot be judged
"E"    Suspicious / likely false
"F"    Known false
```

### query_type

```
"cartel_security_assessment"
"political_risk_assessment"
"violence_outbreak"
"cartel_succession"
"fentanyl_trafficking"
"election_monitoring"
"legislative_reform"
"industrial_real_estate"
"financial_markets"
"peso_currency_risk"
"nearshoring_analysis"
"usmca_review"
"tariff_risk"
"energy_infrastructure_investment"
"water_security"
"worldcup_travel_risk"
"executive_travel_security"
"supply_chain_risk"
"regional_diversification"
"municipal_security"
"custom"
```

### theme (six Mexico desk themes)

```
"cartel_security"
"political_risk"
"us_mexico"
"energy_infra"
"economy_markets"
"worldcup_travel"
```

---

## Core Types

### Judgment

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string (uuid) | yes | Deterministic: brief_id + index |
| claim | string | yes | The judgment statement |
| kent_band | enum | yes | Sherman Kent confidence band |
| pct_range | [int, int] | no | Optional percentage range [low, high] |
| horizon_end | ISO-8601 | no | When this judgment expires or is testable |
| sources | [SourceRef] | yes | At least one source citation |
| subscriber_action | string | no | What the subscriber does with this |
| updated_at | ISO-8601 | no | If judgment was revised from prior brief |

### Section

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string (uuid) | yes | Deterministic: brief_id + section index |
| title | string | yes | Section heading |
| narrative | string | yes | Prose narrative (markdown allowed) |
| subsections | [Subsection] | no | Optional sub-sections |
| judgments | [Judgment] | no | Section-level judgments |
| subscriber_action | string | no | Section-level action line |
| geographic | GeoJSON Feature | no | Polygon/point with risk properties |
| themes | [enum theme] | no | Which themes this section covers |

### Subsection

Same as Section without the `subsections` recursive field.

### WatchItem

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string (uuid) | yes | Deterministic |
| indicator | string | yes | What to watch |
| trigger | string | yes | Observable trigger event |
| signal | string | yes | What it means for the thesis |
| upgrade_signal | string | no | What upgrades the thesis |
| downgrade_signal | string | no | What downgrades the thesis |

### TradePosition

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string (uuid) | yes | Deterministic |
| instrument | string | yes | Ticker or contract name |
| instrument_type | enum | yes | "kalshi" / "polymarket" / "etf" / "fx_fwd" / "cds" / "option" / "synthetic" |
| strike | string | no | Strike price if applicable |
| price | float | no | Current price (null if not re-fetched) |
| price_as_of | ISO-8601 | no | When the price was last fetched |
| recommendation | enum | yes | "buy" / "sell" / "skip" / "hold" |
| sizing_usd | int | no | Recommended notional in USD |
| sizing_methodology | string | no | "premium-cost-sized" / "var-budget" / "volatility-sized" / "scenario-sized" |
| rationale | string | yes | Why this position |
| is_proxy | bool | no | True if proxy for non-existent direct contract |

### Gap

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string (uuid) | yes | Deterministic |
| description | string | yes | What is not known |
| impact | string | yes | Why this gap matters |
| next_step | string | yes | What would close the gap |
| estimated_cost | string | no | Directional cost estimate |
| timeline | string | no | How long to close the gap |
| source_registry_missing | [string] | no | Source name(s) that would help |

### ActionLine

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string (uuid) | yes | Deterministic |
| priority | int | yes | 1 (immediate) to 5 (long-term) |
| action | string | yes | What to do |
| timeframe | string | yes | "24h" / "7d" / "30d" / "90d" / "ongoing" |
| rationale | string | no | Why this action in this sequence |

### SourceRef

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| source_id | string | yes | Stable ID from sources-mexico.json (future) |
| name | string | yes | Display name |
| admiralty | enum | yes | Admiralty source rating |
| url | string | no | URL to source content |
| accessed_at | ISO-8601 | no | When the source was accessed |

### Source (bibliography entry)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | yes | Stable source_id |
| name | string | yes | Display name |
| admiralty | enum | yes | Admiralty rating |
| themes | [enum theme] | yes | Which themes this source covers |
| language | string | yes | "es" / "en" |
| type | string | no | "newspaper" / "blog" / "api" / "government" |

### Metadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| brief_id | string | yes | Same as root brief_id |
| sources_cited | int | yes | Count of unique sources |
| total_judgments | int | yes | Count of judgments |
| avg_confidence | float | no | Mean confidence across judgments |
| themes_covered | [enum theme] | yes | Which themes have substantive content |
| engine_version | string | yes | Schema version + pipeline version |
| word_count | int | no | Total word count |

### GenerationMetadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| model_used | string | yes | Model name (e.g., "claude-opus-4-7", "deepseek-v4-pro", "deepseek-chat") |
| target_word_count | [int, int] | yes | Target word range [min, max] |
| actual_word_count | int | yes | Actual output word count |
| complexity_triggers | [string] | yes | List of fired routing triggers |
| escalation_events | [string] | no | Escalation events during generation |
| routing_rationale | string | yes | Why this model was selected |
| escalation_ladder | string | no | Escalation path: haiku→v4pro→opus |
| generation_cost | float | no | Approximate API cost |
| truncated | bool | no | Whether output was truncated |

### Public API vs Internal Fields

(Unchanged — same stability contract as v1.0.0)|

---

## Public API Contract vs Internal-Only Fields

### Public (stable, versioned, external consumers can depend on)

- `schema_version`, `brief_id`, `query_type`, `produced_at`
- `bluf`, `calibration`
- `sections[].title`, `sections[].narrative`
- `sections[].subsections[].title`, `sections[].subsections[].narrative`
- `sections[].subsections[].judgments[].claim`, `kent_band`, `pct_range`, `horizon_end`
- `sections[].subsections[].judgments[].sources[].name`, `admiralty`
- `watch_items[].indicator`, `trigger`, `signal`
- `trade_positions[].instrument`, `recommendation`, `rationale`
- `gaps[].description`, `impact`, `next_step`
- `action_lines[].priority`, `action`, `timeframe`
- `meta.sources_cited`, `meta.total_judgments`

### Internal (may change between renderer iterations, not for external API)

- `sections[].id`, `subsections[].id` (stable IDs are internal routing)
- `sections[].geographic` (internal renderer data, not API-stable)
- `sections[].themes` (for renderer layout decisions)
- `judgment[].id`, `watch_item[].id`, `trade_position[].id`, `gap[].id`, `action_line[].id`
- `custom` (industry-vertical extensions)
- Internal fields are NOT documented as part of the public API contract

---

## Example: Bajío v3 as JSON

(A complete JSON rendering of the v3 Bajío brief would be included here.
See `memory/2026-05-18-bajio-v3.json` for the rendered example.)

---

## Validation

JSON output MUST pass schema validation before delivery:

```bash
python3 -c "
import json, jsonschema
schema = json.load(open('docs/brief-schema-v1.md'))
brief = json.load(open('path/to/brief.json'))
jsonschema.validate(brief, schema)
"
```

(Note: jsonschema library is NOT installed. Validation for v1 is manual
field-type checking. Schema enforcement via jsonschema will be added
when `pip install jsonschema` is approved.)
