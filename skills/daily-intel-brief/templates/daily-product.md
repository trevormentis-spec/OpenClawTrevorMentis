# TREVOR DAILY INTELLIGENCE BRIEF

**{{ long_date }}** — DTG {{ dtg }}

> **{{ bluf }}**
>
> {{ context_paragraph }}

## Executive Summary

{% for kj in five_judgments -%}
{{ loop.index }}. **{{ kj.statement }}** ({{ kj.sherman_kent_band }}; {{ kj.prediction_pct }}% / 7d) — *{{ kj.drawn_from_region }}*
{% endfor %}

*Methodology: NATO Admiralty source rating, Sherman Kent probability bands. Predictions are 7-day, falsifiable, scored at the monthly calibration review.*

---

{% for region in regions %}
## {{ region.label }}

*{{ region.incident_count }} incidents in 24h to {{ dtg }} UTC.*

{% if region.map %}![{{ region.label }}]({{ region.map }}){% endif %}

{{ region.narrative }}

### Incidents

| Pin | Country | Category | Headline | Src |
|-----|---------|----------|----------|-----|
{% for inc in region.incidents -%}
| {{ inc.id_short }} | {{ inc.country }} | {{ inc.category }} | {{ inc.headline }} | {{ inc.src_rating }} |
{% endfor %}

### Key Judgments

{% for kj in region.key_judgments -%}
**{{ kj.id }}** ({{ kj.sherman_kent_band }}; {{ kj.prediction_pct }}% / 7d): {{ kj.statement }}
- Evidence: {{ kj.evidence_incident_ids | join(", ") }}
- Indicators: {{ kj.what_would_change_it | join(" // ") }}

{% endfor %}

---
{% endfor %}

## Annex A — Sources & Methodology

{{ sources_block }}

## Annex B — Indicators & Warnings — Status Board

{{ iw_status_block }}

{% if red_team %}
## Annex C — Red-team Note

{{ red_team }}
{% endif %}
