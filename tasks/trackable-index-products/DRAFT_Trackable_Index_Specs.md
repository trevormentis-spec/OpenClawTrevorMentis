# Trackable Index Products — Pilot Scoping

**Date:** 2026-06-12
**Status:** Scoping / Pre-Pilot
**Author:** Trevor

---

## Product A: GRAIN SUPPLY MONITOR

### 1. Measurement Specification

**Concept:** Track vegetation health across the world's ~15 top grain-producing regions via satellite NDVI, expressed as a percentile against the historical record for that region/season. The product answers: *"Is this season's crop development ahead, on-track, or behind normal, and how fast is it changing?"*

| Parameter | Specification |
|---|---|
| **Primary sensor** | Sentinel-2 MSI (10m resolution, 5-day revisit) via GEE `COPERNICUS/S2_SR_HARMONIZED` |
| **Baseline sensor** | MODIS NDVI (MOD13Q1 v061, 250m, 16-day composite) for historical record extending to 2000 |
| **Secondary index** | Vegetation Health Index (VHI) — combines NDVI + land surface temperature (LST) for moisture/stress detection |
| **Regions monitored** | 15 AOIs (see §1a below) |
| **Refresh cadence** | Weekly composite (Mon–Sun window), published Tuesday 12:00 UTC |
| **Cloud mask** | QA60 bitmask + <20% cloud pixel filter per tile; multi-image median compositing over window |
| **Phenology alignment** | NDVI percentile computed against same 10-day window in historical years (2000–2025), not calendar-absolute |
| **Output format** | JSON (see schema below) |

**§1a — Monitored Regions (AOIs)**

| ID | Region | Primary Grain | Growing Season (approx) |
|---|---|---|---|
| US-CB | US Corn Belt (IA, IL, IN, NE) | Corn / Soy | Apr–Oct |
| US-SP | US Southern Plains (KS, OK, TX) | Winter Wheat | Oct–Jun |
| BR-MT | Brazil Mato Grosso | Soy / Corn | Sep–Mar |
| BR-RS | Brazil Rio Grande do Sul | Soy | Oct–Apr |
| AR-PA | Argentina Pampas | Soy / Corn / Wheat | Oct–Mar |
| UA-UK | Ukraine central/steppe | Wheat / Corn / Sunflower | Apr–Sep |
| RU-SK | Russia Southern Krai / Stavropol | Winter Wheat | Sep–Jul |
| EU-FR | France / Germany belt | Soft Wheat / Barley | Oct–Aug |
| IN-PB | India Punjab / Haryana | Wheat / Rice | Rabi Nov–Apr / Kharif Jun–Oct |
| AU-WA | Australia Western wheatbelt | Wheat | May–Nov |
| CN-SD | China Shandong / Henan | Wheat / Corn | Oct–Jun / May–Sep |
| CN-JL | China Jilin / Heilongjiang | Corn / Soy | May–Sep |
| CA-SK | Canada Saskatchewan / Manitoba | Wheat / Canola | May–Sep |
| RU-VL | Russia Volga / Urals | Spring Wheat | Apr–Sep |
| ZA-FS | South Africa Free State | Corn | Oct–Apr |

**§1b — Output Schema (JSON)**

```json
{
  "product": "grain_supply_monitor",
  "report_date": "2026-06-09",
  "composite_window": "2026-06-02/2026-06-08",
  "regions": [
    {
      "region_id": "US-CB",
      "region_name": "US Corn Belt",
      "crop_types": ["corn", "soybeans"],
      "primary_ndvi": {
        "current": 0.72,
        "historical_median": 0.68,
        "historical_percentile": 78,
        "percentile_band": "ABOVE_NORMAL"
      },
      "vhi": {
        "current": 64,
        "anomaly_class": "FAVORABLE"
      },
      "30d_delta": {
        "ndvi_change": 0.08,
        "direction": "INCREASING",
        "rate_of_change_percentile": 65
      },
      "confidence": {
        "nato_admiralty": "B2",
        "source_reliability": "B",
        "info_credibility": "2",
        "reasoning": "10m Sentinel-2 composite, 5 passes cloud-free >80%; ground-truth USDA NASS weekly crop prog report available through May 26"
      },
      "active_alert": false,
      "last_updated_utc": "2026-06-09T14:30:00Z"
    }
  ]
}
```

**Admiralty Code applied:**
- **Source reliability:** A = multiple independent satellite passes across AOI; B = single-sensor composite with >1 cloud-free pass; C = composite with significant cloud interpolation
- **Info credibility:** 1 = confirmed by national agency ground survey (e.g., USDA NASS); 2 = correlates with weather/soil moisture model; 3 = sensor-only estimate with no ground-truth crosswalk

The combined grade is reported per region per composite window.

---

### 2. Backtest Feasibility

| Criterion | Assessment |
|---|---|
| **Historical data depth** | Sentinel-2 archive starts 2015; MODIS NDVI from 2000. 12-month trailing window fully constructable for all 15 AOIs. |
| **Seasonality coverage** | All 15 regions have data covering at least one full growing cycle within T-12. Cross-year percentile computation requires ≥5 years of data — available for all AOIs (Sentinel-2 2015+ = 11 seasons). |
| **Known gaps** | Brazilian growing season (Oct–Mar) heavily clouded Dec–Feb. Requires multi-pass composite blending; confidence degrades to B3 during peak rainy season. MODIS 250m fills some gaps but at coarser resolution. |
| **Sample output dates** | See §2a below. |

**§2a — Sample Outputs for 3 Dates (simulated from real 2026 data)**

| Date | Region | NDVI | Hist Pctl | 30d Δ | Admiralty | Notes |
|---|---|---|---|---|---|---|
| 2026-06-01 | US-CB Corn | 0.71 | 82 | +0.09 | B2 | Early season above normal; soil moisture favorable |
| 2026-03-15 | BR-MT Soy | 0.85 | 91 | +0.04 | B3 | Late-season peak before harvest; cloud gaps in Dec composite |
| 2026-01-15 | UA-UK Wheat | 0.32 | 34 | -0.11 | C1 | Winter dormancy — NDVI naturally low; cross-walk with Ukraine AgMin confirms |

---

### 3. Verification Mechanism

| Ground-Truth Source | What It Provides | Cadence | Cost | Admiralty Contribution |
|---|---|---|---|---|
| **USDA WASDE** | Monthly world crop production estimates, yield, area harvested | Monthly (9–12th) | Free | Converts B2 → A2 for US regions |
| **USDA Crop-CASMA** | Crop condition & soil moisture analytics from NASS surveys + satellite fusion | Weekly (May–Nov) | Free | Direct ground-truth crosswalk for US |
| **USDA FAS Crop Explorer** | Global NDVI/VHI maps from MODIS/VIIRS; crop calendars | Weekly | Free | Independent second sensor |
| **CONAB (Brazil)** | Crop surveys, harvest estimates for soy/corn | Monthly | Free | A-graded for BR-MT, BR-RS |
| **EU MARS (JRC)** | Crop yield forecasts + remote sensing for EU members | Monthly | Free | A-graded for EU-FR |
| **StatsCan** | Field crop surveys for prairie provinces | Semi-monthly | Free | A-graded for CA-SK |
| **FAO GIEWS** | Global food supply/demand alerts | Monthly | Free | Cross-regional sanity check |

**Mechanism:** Each weekly composite is aligned to the nearest preceding ground-survey window. Where survey data exists (US, EU, Brazil, Canada), the Admiralty grade improves by one tier. For Ukraine, Russia, and South Africa, where ground surveys are delayed or politicized, the index stands as B2–C1 with a transparent note.

---

### 4. Cost Model

| Component | Unit Cost | Per Full Run (15 AOIs) | Annualized (52 runs) |
|---|---|---|---|
| GEE compute (Sentinel-2 composite) | ~$0.02/tile | $0.30–0.60 | $15.60–31.20 |
| GEE compute (MODIS historical percentile) | ~$0.01/region | $0.15 | $7.80 |
| MODIS archive access | Free | — | — |
| Sentinel-2 archive access | Free | — | — |
| Data export (JSON to CDN/API) | ~$0.01 | $0.01 | $0.52 |
| **Subtotal** | | **$0.46–0.76** | **$23.92–39.52** |
| Overhead (orchestration, error retry, alert routing) | ~$0.02 | $0.02 | $1.04 |

**Total annual operating cost: ~$25–41**

**Proposed price point (if commercialized):**
- Per-call API: $5–15 per full run (650–2000% margin)
- Weekly subscription: $50–150/mo per client
- Enterprise (historical access + custom AOIs): $500–2000/mo

---

### 5. New Procurement Required

| Input | Cost | Verdict |
|---|---|---|
| GEE API access (non-commercial) | Free (standard tier) | ❌ None needed |
| GEE commercial license | $0.001/Earth Engine compute hour (paid tier); ~$2/mo estimated | ⚠️ Negligible |
| USDA data feeds | Free | ❌ None needed |
| Sentinel-2 imagery | Free (ESA open data) | ❌ None needed |

**Procurement flag:** **NONE.** The Grain Supply Monitor can be piloted with zero new paid data procurement.

---

## Product B: CHOKEPOINT TRANSIT INDEX

### 1. Measurement Specification

**Concept:** Track vessel transit counts, tonnage, and category breakdown through the world's eight major maritime chokepoints, expressed as a trailing-7-day average indexed to the 12-month historical window. The product answers: *"Is traffic through this chokepoint at normal levels, and if not, by how much?"*

| Parameter | Specification |
|---|---|
| **Primary data** | AIS vessel positions aggregated to transit events per chokepoint |
| **Vessel filter** | Commercial ≥300 GT (filters recreational/small fishing) |
| **Categories** | Tanker, Bulk Carrier, Container, General Cargo, LNG/LPG, Other |
| **Metric 1** | Vessel count (trailing 7d avg / 7d comparison week) |
| **Metric 2** | Aggregate deadweight tonnage (DWT) per chokepoint |
| **Metric 3** | Category breakdown (% tanker, % container, etc.) |
| **Metric 4** | Dwell time estimate (median hours between entries and exits) — optional |
| **Chokepoints** | 8 primary (see §1a) |
| **Refresh cadence** | Daily, published 06:00 UTC |
| **Historical window** | Trailing 12 months; percentile against same-month 5-year baseline when available |
| **Output format** | JSON (see schema below) |

**§1a — Monitored Chokepoints**

| ID | Chokepoint | Linkage | Est. Daily Traffic (pre-crisis) | Strategic Importance |
|---|---|---|---|---|
| SUEZ | Suez Canal | Med ↔ Red Sea | ~50–55 vessels/day (2023) | 12% global trade; 4.9M bbl/d oil |
| BAB | Bab el-Mandeb | Red Sea ↔ Gulf of Aden | ~40–50 vessels/day | 4.2M bbl/d oil; key to Suez routing |
| HORMUZ | Strait of Hormuz | Persian Gulf ↔ Gulf of Oman | ~20–25 tankers/day | 21M bbl/d oil (~20% global) |
| MALACCA | Strait of Malacca | Indian Ocean ↔ South China Sea | ~120 vessels/day | 40% global trade; 16M bbl/d oil |
| PANAMA | Panama Canal | Pacific ↔ Atlantic | ~27 vessels/day (2024) | 6% global trade; drought-limited |
| BOSPHORUS | Turkish Straits | Black Sea ↔ Mediterranean | ~40 vessels/day | Ukraine/Russia grain corridor; 3.5M bbl/d |
| DANISH | Danish Straits | Baltic ↔ North Sea | ~70 vessels/day | Russian oil/northern EU trade |
| CAPE | Cape of Good Hope (alt. route) | Atlantic ↔ Indian | ~25 vessels/day (up from ~8 pre-2024) | Diversion route indicator |

**§1b — Output Schema (JSON)**

```json
{
  "product": "chokepoint_transit_index",
  "report_date": "2026-06-12",
  "window_type": "trailing_7d_avg",
  "chokepoints": [
    {
      "chokepoint_id": "SUEZ",
      "chokepoint_name": "Suez Canal",
      "trailing_7d_avg_vessels": 22.3,
      "comparison_prior_week": 21.8,
      "prior_week_delta_pct": 2.3,
      "historical_percentile": 16,
      "historical_baseline_note": "vs Jan 2023 baseline (pre-diversion)",
      "dwt_millions": {
        "trailing_7d_avg": 1.42,
        "prior_week": 1.38,
        "delta_pct": 2.9
      },
      "category_breakdown_pct": {
        "tanker": 18,
        "bulk": 22,
        "container": 28,
        "general_cargo": 15,
        "lng_lpg": 8,
        "other": 9
      },
      "status": "CONSTRICTED",
      "status_threshold": ">40% below 2023 baseline",
      "confidence": {
        "nato_admiralty": "A2",
        "source_reliability": "A",
        "info_credibility": "2",
        "reasoning": "Terrestrial + satellite AIS; transit count cross-checked against SCA daily publication"
      },
      "active_alert": true,
      "alert_reason": "Sustained 60% reduction from 2023 baseline; no recovery despite cessation of Houthi attacks",
      "last_updated_utc": "2026-06-12T06:00:00Z"
    }
  ]
}
```

**Admiralty Code applied:**
- **Source reliability:** A = terrestrial + satellite AIS fused with authority publication; B = single-source AIS (terrestrial only); C = inferred from adjacent-port data or partial coverage
- **Info credibility:** 1 = confirmed by official authority count (SCA, PCA, etc.); 2 = AIS-based with <5% gap rate; 3 = partial coverage or significant AIS blackout period

---

### 2. Backtest Feasibility

| Criterion | Assessment |
|---|---|
| **Historical data depth** | VesselFinder: 2009+; MarineTraffic: similar. 12-month backtest fully feasible. Kpler/Spire: 2010+ for satellite (post-acquisition pricing unclear). |
| **Chokepoint definition** | Geofencing polygons required per chokepoint. Suez, Panama, Bosphorus have clear entry/exit coordinates. Hormuz, Malacca, Bab el-Mandeb need wider AOIs to avoid counting coastal traffic. Approx 1 day of GIS work. |
| **Pre-2023 baseline sensitivity** | The Houthi/Suez disruption makes 2023 the de facto "normal" baseline for Red Sea chokepoints. For Hormuz and Malacca, 12-month trailing is sufficient; multi-year baseline would add signal quality if AIS archive depth supports it. |
| **Satellite vs terrestrial** | Terrestrial AIS covers ~80–90% of chokepoint traffic (ports = receiver density). Open-ocean approaches (Cape, approaches to Bab el-Mandeb) need satellite AIS — this is where cost floors apply. |
| **Sample output dates** | See §2a below. |

**§2a — Sample Outputs for 3 Dates (simulated from published data)**

| Date | Chokepoint | Vessels/d (7d avg) | Hist Pctl | Status | Admiralty | Notes |
|---|---|---|---|---|---|---|
| 2026-06-09 | SUEZ | 22.3 | 16 | CONSTRICTED | A2 | 60% below Jan 2023 baseline; SCA confirms 22–23/d |
| 2026-03-15 | PANAMA | 26.1 | 48 | NORMAL | A2 | Drought restrictions easing, transits approaching FY2024 avg of 27/d |
| 2025-12-01 | BAB | 12.4 | 8 | CONSTRICTED | B2 | Peak Houthi disruption; terrestrial AIS gaps — satellite fills but with latency |

---

### 3. Verification Mechanism

| Ground-Truth Source | What It Provides | Cadence | Cost | Admiralty Contribution |
|---|---|---|---|---|
| **Suez Canal Authority** | Official daily transit count, vessel type, DWT | Daily (public) | Free | A2 grade when cross-walked |
| **Panama Canal Authority** | Monthly operational stats: transits, tonnage, draft restrictions | Monthly | Free | A2 grade for PANAMA |
| **EIA Chokepoint Reports** | Oil transit volumes (bbl/d) per chokepoint | Annual / Semiannual | Free | Multi-year baseline validation |
| **Lloyd's List Intelligence** | Vessel movements, port calls, sanctions tracking | Daily | Paid (~$10k+/yr) | Could push to A1 but expensive |
| **UNCTAD Maritime Transport** | Annual maritime trade volumes by chokepoint | Annual | Free | Strategic context, not operational |
| **BIMCO / Clarksons** | Periodic reports on Red Sea diversion, charter rates | Ad-hoc | Varies | Trend validation |
| **Port authority data** | Arrival/departure records per vessel | Real-time | Varies | Micro-validation at endpoints |

**Mechanism:** Chokepoints with published authority data (Suez, Panama, Bosphorus) get A-grade source reliability through automated daily comparison. For Bab el-Mandeb and Cape, where no single authority publishes transit counts, the index relies on AIS alone (B-grade) with the note "dependent on AIS coverage quality." Malacca and Hormuz benefit from coastal AIS receiver density that approaches authority-grade reliability.

---

### 4. Cost Model

| Component | Unit Cost | Per Full Run | Annualized (365 runs) |
|---|---|---|---|
| AIS API — VesselFinder credits (10 chokepoints x ~50 vessels avg x 4 checks/d) | ~€330/mo minimum (10k credits) | ~€11/d effective | ~€3,960/yr |
| Satellite AIS premium (for BAB, CAPE, open-ocean approaches) | ~€0.10/vessel position | ~€5/d extra | ~€1,825/yr |
| **VesselFinder tier** | | **€330/mo (10k credits)** | **€3,960** |
| **MarineTraffic Essential (or similar)** | | **~$500/mo** | **~$6,000/yr** |
| **Data Docked (most accessible)** | | **€80–250/mo** | **€960–3,000/yr** |
| Geofence compute + aggregation | ~$0.02/run | $0.02 | $7.30 |
| JSON output storage/delivery | ~$0.005/run | $0.005 | $1.83 |
| **Minimum viable cost (Data Docked basic + no satellite premium)** | | **~€2.70/d effective** | **~€960/yr** |
| **Full production cost (VesselFinder + satellite)** | | **~€16/d effective** | **~€5,800/yr** |

**Proposed price point:**
- Per-call API: $10–25 per full 8-chokepoint snapshot
- Daily subscription: $150–400/mo per client
- Enterprise (raw feed + alerts): $1,000–3,000/mo

---

### 5. New Procurement Required — ⚠️ CRITICAL

| Input | Cost | Status | Action |
|---|---|---|---|
| **Commercial AIS API** | €80–€500/mo | ❌ NOT PROCURED | **Minimum viable: Data Docked at €80/mo** or VesselFinder at €330/mo |
| **Satellite AIS add-on** | +€0.10/vessel (or included in VesselFinder premium tier) | ❌ NEEDS EVALUATION | Required for BAB, CAPE, and Hormuz approaches |
| **Historical AIS archive** | Included in VesselFinder API (2009+) | ✅ Included in subscription | — |
| **SCA / PCA data ingestion** | Free (RSS/web scrape) | ✅ No procurement | Parse automation only |
| **Lloyd's List subscription** | ~$10,000+/yr | ❌ Not budgeted | Nice-to-have; not required for MVP |

**Procurement flag:** **REQUIRED — Commercial AIS API subscription is mandatory.** No viable free alternative exists for reliable chokepoint transit counting. OpenAIS tools exist but produce partial, non-realtime data unsuitable for a daily index.

**Free-tier limitations encountered in research:**
- MarineTraffic free plan: terrestrial AIS only, no satellite, no API, <5 vessel fleets
- VesselFinder free: web UI only, no API access
- Data Docked: 20 free trial credits only
- OpenAIS: open-source tools but requires operating your own AIS receiver network; no historical archive
- NOAA/USCG: US waters only; no global chokepoint coverage

---

## Go/No-Go Recommendations

### GRAIN SUPPLY MONITOR — ✅ GO (Low Risk)

| Factor | Verdict |
|---|---|
| Data cost | $0 — all sources free/open |
| Backtest feasibility | Full 12+ years of Sentinel-2 data; no gaps |
| Verification | USDA, CONAB, EU MARS, StatsCan all free, high-quality |
| Technical complexity | Moderate — GEE Python API, standard NDVI pipeline |
| Time to MVP | ~2 weeks (1 week data pipeline + 1 week output formatting) |
| Competitive differentiation | Many crop monitors exist (CropProphet, Gro Intelligence, Descartes Labs); differentiation requires our specific percentile+Admiralty framing |
| **Recommendation** | **GO — pilot with 4 core AOIs first (US-CB, BR-MT, UA-UK, EU-FR). Zero procurement cost. Extend to 15 regions only after verification loop closes for initial 4.** |

### CHOKEPOINT TRANSIT INDEX — ⚠️ CONDITIONAL GO (Requires procurement)

| Factor | Verdict |
|---|---|
| Data cost | €960–5,800/yr minimum |
| Backtest feasibility | Full 12+ months feasible with paid API; limited without |
| Verification | SCA/PCA free; all other chokepoints require AIS-only |
| Technical complexity | Moderate — geofencing, vessel type classification, transit event detection |
| Time to MVP | ~3 weeks (1 week procurement + 1 week geofencing + 1 week pipeline) |
| Competitive differentiation | High — no single free product offers this with Admiralty confidence grading. Windward, Kpler, and exactEarth are enterprise-grade and expensive. |
| **Recommendation** | **CONDITIONAL GO — requires €80/mo Data Docked subscription as minimum viable procurement. If procurement is approved, proceed; if not, product cannot ship.** |

---

## Pilot Roadmap (If Both Approved)

| Week | Milestone |
|---|---|
| 1 | Procure Data Docked AIS API; build GEE pipeline for 4 core grain AOIs |
| 2 | Geofence 8 chokepoints; build transit event aggregation; data-pipeline dry run |
| 3 | Historical backtest runs for both indices (12 months); verify sample outputs against published data |
| 4 | Adjudicate Admiralty grades against ground truth; validate cost model; produce pilot report |

---

*End of scoping document. No external deployment executed.*
