# Frameworks — LEO Ground Stations

This directory stores analytical frameworks, mental models, and structured methods relevant to LEO ground station analysis.

---

## 1. Traffic Volume Model (Concentric Security Group Methodology)

**Source:** Concentric Security Group LEO Ground Station Market Opportunity Assessment (Mar 2026)

### Model Overview
Relative traffic volume per site is estimated on a 1-5 scale based on four weighted factors:

1. **Subscriber density** within the coverage footprint
2. **Backbone fibre capacity** at the site
3. **Number of simultaneous satellite contacts** (antenna count × multi-mission capability)
4. **Operator-reported capacity allocation**

### Traffic Tier Definitions

| Tier | Score | Description | Representative Sites |
|------|-------|-------------|---------------------|
| Peak | 5 | Constellation HQ/control centres, mega-population footprints (100M+), polar TT&C concentration | Redmond WA, N. Virginia, Hawthorne CA, Lagos, Tokyo, Manila, Jakarta, Mumbai, São Paulo, Ho Chi Minh City, KSAT Svalbard/Tromsø |
| High | 4 | Major European gateways, polar coverage, military strategic, southern hemisphere backbone, Africa coverage | Goonhilly, Gravelines, Stuttgart, Fairbanks/Inuvik, Guam, Punta Arenas, Hartebeesthoek, Maricá, Puerto Rico, Abuja |
| Moderate | 3 | Most GSaaS multi-mission sites, smaller gateways, US regional E-band sites, planned/projected sites | Standard GSaaS operations, US domestic backbone fill, new market entry pre-scaling |
| Low | 2 | Remote backup sites, low-population-density coverage, early-phase GSaaS expansion | Redundancy coverage, niche EO downlink, early commercial viability uncertain |

### Critical Finding (from Concentric)
The highest-traffic sites are increasingly in developing markets (Nigeria, Philippines, Vietnam, Indonesia, India) where ground station physical security capability is weakest. This is where physical security differentiation is most valuable.

### Methodology Limitations
- Traffic tier ratings are qualitative (1-5 scale), not quantitative (Mbps per site)
- Does not account for traffic variation by time of day or season
- Assumes all operational antennas are running at similar utilization rates
- Does not differentiate between TT&C traffic vs payload downlink traffic

---

## 2. Site Selection Matrix

**Framework for evaluating new ground station locations.**

Weighted criteria:
- Regulatory environment (25%)
- Fibre backbone availability (20%)
- Physical security environment (20%)
- Political stability (15%)
- Coverable gap in current networks (10%)
- Terrain and climate (5%)
- Power infrastructure (5%)

*(To be populated with specific weights and scoring sheets)*

---

## 3. GSaaS Operator Valuation

**Revenue-per-antenna, EBITDA margin, and capacity utilization models.**

Key metrics from principal data:
- KSAT: ~$200M rev / 280 antennas = ~$714K per antenna
- SSC: ~$160M rev / 100 antennas = ~$1.6M per antenna
- Leaf Space: revenue-generating (undisclosed) / 40 antennas
- Skynopy: early commercial / 15 antennas
- Atlas: revenue-generating / 50 antennas

*(To be populated with full comp sheet)*

---

## 4. Regulatory Risk Scoring

**Country-by-country regulatory environment scoring.**

Factors:
- Foreign ownership restrictions on telecom infrastructure
- Data sovereignty/residency requirements
- Starlink/Kuiper/OneWeb licensing status
- ITU filing coordination status
- Environmental review requirements

*(To be populated)*

---

## 5. Physical Security Risk Assessment Methodology (Ingested)

**Dedicated file:** `concentric-physical-security-methodology.md` (12.5 KB — full methodology document)

Comprehensive methodology from Concentric Security Group (March 2026) covering:

- **Asset Taxonomy** — 4 asset types: Gateway Earth Stations (GES), Satellite Network Portals (SNP), TT&C Facilities, Supporting Infrastructure
- **10-Threat Taxonomy** — 8 categories with standardised IDs (PA-01/02, PS-01/02, PR-01, PT-01, PD-01, PE-01, PC-01, PX-01)
- **5-Phase Assessment Process** — Orient → Context → Threat Assessment → Vulnerability Assessment → Risk Rating
- **7-Dimension Site Context Profile** — Geopolitical Stability (20%), Local Crime (15%), Protest/Activism (10%), Natural Hazard (15%), Site Isolation (15%), Existing Security Posture (15%), Strategic Value (10%) — each scored 1-5 with weighted composite
- **Risk Matrix** — likelihood × consequence producing Negligible → Low → Moderate → High → Critical ratings
- **Control Checklist** — 9 control areas with minimum standards (perimeter, detection, CCTV, access control, guard force, lighting, resilience, counter-UAS)
- **Architecture Implications** — transparent (bent-pipe) vs regenerative (ISL) architecture effect on criticality scoring
- **Deliverables** — 6 standard outputs per site assessment

### Usage
For any ground station site assessment, apply the 5-Phase Process:
1. **Orient** — catalogue all physical assets at the site
2. **Context** — score the 7-dimension Site Context Profile
3. **Threat Assessment** — assess likelihood and consequence for each of the 10 threats
4. **Vulnerability Assessment** — evaluate existing controls against the 9-area checklist
5. **Risk Rating** — plot on the risk matrix and generate prioritised recommendations

### 80-Site Register (Ingested)
The 80-site Global Risk Register has been fully ingested into `entities.yaml` as 80 `ground_station_site` entities with full 7-dimension context profile scores, composite scores, and risk ratings. Cross-reference with:
- `config/topics/leo_ground_stations/entities.yaml` (124 total entities including all 80 sites)
- `geography/site_risk_profile.md` (summary tables, high-risk site list, out-of-register sites)
- `config/topics/leo_ground_stations/_principal_data/global_risk_register_risk_register.json` (raw data)
- `config/topics/leo_ground_stations/_principal_data/global_risk_register_scoring_guide.json` (dimension definitions)
- `config/topics/leo_ground_stations/_principal_data/global_risk_register_risk_summary.json` (aggregate statistics)
