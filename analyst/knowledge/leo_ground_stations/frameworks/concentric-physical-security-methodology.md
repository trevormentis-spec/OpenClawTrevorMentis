# Concentric Physical Security Risk Assessment Methodology

**Source:** Concentric Security Group, "Physical Security Risk Assessment Methodology for LEO Basestation Ground Infrastructure," V1.0, March 2026. CLIENT CONFIDENTIAL.

**Status:** Ingested. This is the definitive methodology for assessing physical security risk to LEO ground segment assets. All site assessments conducted under this topic should follow this framework.

---

## 1. Asset Taxonomy (Section 2.1)

Four asset types are within scope for physical security assessment:

| Asset Type | Abbreviation | Description |
|------------|-------------|-------------|
| **Gateway Earth Stations** | GES | Primary ground stations hosting Ka/Ku-band phased array antenna arrays, radome enclosures, and fibre interconnects to Internet Exchange Points |
| **Satellite Network Portals** | SNP | Data processing and routing facilities co-located with or adjacent to gateway stations |
| **Telemetry, Tracking and Command Facilities** | TT&C | Sites responsible for satellite orbit management and health monitoring |
| **Supporting Infrastructure** | — | Power substations, backup generators, cooling systems, fibre landing points, and access roads serving basestation complexes |

### Out of Scope (Section 2.2)
- User terminal equipment and residential/commercial customer premises
- Space segment assets (satellites, inter-satellite links)
- Mission Operations Centres (MOCs) unless co-located with ground stations

---

## 2. Physical Threat Taxonomy (Section 3)

Eight threat categories with standardised IDs, developed specifically for LEO ground infrastructure:

| ID | Category | Description |
|----|----------|-------------|
| **PA-01** | Unauthorised Access (External) | Perimeter breach by hostile actors seeking to damage, destroy, or tamper with antenna arrays, radomes, or data centre equipment |
| **PA-02** | Unauthorised Access (Insider) | Insider threat from maintenance contractors, construction workers, or co-located facility staff with legitimate physical access |
| **PS-01** | Sabotage / Vandalism (Infrastructure) | Deliberate damage to antenna infrastructure, fibre optic cables, or power supply systems by ideologically motivated, criminal, or state-sponsored actors |
| **PS-02** | Sabotage / Vandalism (Access Denial) | Destruction of access roads or supporting utilities to deny operational capability |
| **PR-01** | Surveillance / Reconnaissance | Hostile reconnaissance of site layout, security posture, shift patterns, and vulnerability mapping by adversary actors |
| **PT-01** | Theft | Theft of high-value electronic components, copper cabling, or backup power equipment |
| **PD-01** | Drone / UAS Threat | Unmanned aerial systems used for surveillance, signal interference, or direct kinetic attack on exposed antenna arrays |
| **PE-01** | Environmental / Natural Hazard | Severe weather, seismic events, flooding, wildfire, or volcanic activity affecting site operability and structural integrity |
| **PC-01** | Civil Unrest / Protest | Protest activity, blockade, or civil disorder targeting the facility or its operator due to political, environmental, or social grievance |
| **PX-01** | State-Level Threat | Covert or overt state action against ground infrastructure in the context of geopolitical competition, hybrid warfare, or conflict escalation |

---

## 3. The Concentric 5-Phase Assessment Process (Section 4)

### Phase 1: Orient
Establish assessment scope by identifying and cataloguing all physical assets at the target site. Produces a **Site Asset Register** including GPS coordinates, building footprints, antenna counts, perimeter dimensions, access points, and utility interconnections. Map against asset categories (Section 2.1).

### Phase 2: Context
Evaluate the environmental and geopolitical context of the site. Produces a **Site Context Profile** covering seven scoring dimensions (Section 4 below), each rated 1 to 5 with weighted composite score.

### Phase 3: Threat Assessment
Apply the Threat Taxonomy (Section 2) to the specific site, assessing the likelihood and consequence of each applicable threat. Likelihood informed by Context Profile scores and local intelligence. Consequence assessed against a standardised impact scale covering operational disruption, financial loss, reputational damage, and national security implications.

### Phase 4: Vulnerability Assessment
Conduct detailed assessment of existing physical security controls against each identified threat. Covers:
- **Perimeter security** — fencing, barriers, detection systems
- **Access control** — authentication, visitor management, lock hardware
- **Surveillance systems** — CCTV, monitoring coverage, retention
- **Guard force** — manning levels, response times, training standards
- **Resilience measures** — backup power, redundant connectivity, hardening against natural hazards

### Phase 5: Risk Rating and Recommendations
Integrate findings from Phases 2-4 to produce a composite **Physical Security Risk Rating**. Apply the risk matrix (Section 5) and generate prioritised recommendations with implementation timelines and cost estimates.

---

## 4. Site Context Profile — 7 Scoring Dimensions (Section 5)

Each dimension scored 1 (lowest risk) to 5 (highest risk). Composite score = weighted average.

| # | Dimension | Weight | Assessment Criteria | 1 (Low) | 5 (High) |
|---|-----------|--------|-------------------|---------|---------|
| 1 | **Geopolitical Stability** | 20% | Country-level stability, conflict proximity, sanctions exposure, governance quality (Fragile States Index, EIU Democracy Index) | Stable NATO/EU state | Active conflict zone |
| 2 | **Local Crime Environment** | 15% | Violent crime rates, organised crime presence, theft/burglary rates within 50km radius | Very low crime | High violent crime |
| 3 | **Protest / Activism Risk** | 10% | History of anti-technology, environmental, or anti-corporate protest targeting comms infrastructure | No history | Active/recent targeting |
| 4 | **Natural Hazard Exposure** | 15% | Seismic zone, flood plain, hurricane/cyclone, wildfire, extreme temperature events | Minimal hazards | Multiple severe hazards |
| 5 | **Site Isolation / Remoteness** | 15% | Distance to nearest LE, emergency response time, road access, proximity to population centres | Urban, rapid response | Extremely remote |
| 6 | **Existing Security Posture** | 15% | Quality of perimeter, access control, CCTV, guard force, hardening measures | Robust controls | Minimal/no controls |
| 7 | **Strategic Value / Criticality** | 10% | Constellation dependency (redundancy), military/govt use, TT&C function, population served | High redundancy | Single point of failure |

**Composite Context Score** = (Geopolitical × 0.20) + (Crime × 0.15) + (Protest × 0.10) + (Natural Hazard × 0.15) + (Isolation × 0.15) + (Security Posture × 0.15) + (Strategic Value × 0.10)

---

## 5. Risk Matrix (Section 6)

The final Physical Security Risk Rating is determined by plotting **Likelihood** (from threat assessment + context scoring) against **Consequence** (from impact analysis):

| Likelihood \ Consequence | Negligible | Low | Moderate | High |
|--------------------------|-----------|-----|----------|------|
| **Very Likely** | Moderate | High | Critical | Critical |
| **Likely** | Low | Moderate | High | Critical |
| **Possible** | Low | Low | Moderate | High |
| **Unlikely** | Negligible | Low | Low | Moderate |
| **Rare** | Negligible | Negligible | Low | Low |

### Risk Response Requirements

| Risk Level | Response |
|------------|----------|
| **Negligible** | Monitor. No additional measures beyond baseline standards. |
| **Low** | Awareness. Standard perimeter & access control. Annual reassessment. |
| **Moderate** | Enhanced controls. Active CCTV, intrusion detection, regular patrol. Semi-annual reassessment. |
| **High** | Significant investment. 24/7 guard force, hardened perimeter, integrated alarm systems, LE liaison. Quarterly reassessment. |
| **Critical** | Maximum protection. Armed security, counter-UAS, blast protection, redundant site planning, government coordination. Continuous monitoring. |

---

## 6. Architecture Implications (Section 7)

### Transparent (Bent-Pipe) vs Regenerative (ISL) Architecture
- **Transparent architecture** — ground station hosts the entire gNB processing stack, making it an exceptionally high-value target. Loss of a T-architecture station directly eliminates connectivity for all users in the coverage footprint.
- **Regenerative architecture with ISLs** — satellite can route traffic via alternative ground stations, reducing single-point-of-failure risk. But does not eliminate the physical threat to the node itself.
- **Assessment impact:** T-architecture stations warrant a minimum Strategic Value score of 3.

### Handover Topology
LEO constellations depend on continuous handover between satellites and ground stations. Loss of a single ground station affects Topologies B and C (inter-satellite handover to different ground stations) and may cascade to Topology D/E swarm architectures if the station serves as a Master-Satellite control point.

### The 'Anonymous Attacking' Problem
Analogous to the digital 'anonymous attacking' vulnerability, many LEO ground stations are in rural/semi-rural areas with minimal surveillance and limited law enforcement presence. Physical attacks can be executed with low attribution risk. The Site Isolation / Remoteness dimension directly addresses this factor.

---

## 7. Physical Security Control Checklist (Appendix A)

Minimum control standards for Vulnerability Assessment:

| Control Area | Minimum Standard |
|--------------|-----------------|
| **Perimeter** | 2.4m anti-climb fencing with topping; 3m clear zone inside and outside fence line; anti-vehicle barriers at all approach points |
| **Detection** | Perimeter intrusion detection system (PIDS) with alarm annunciation to manned control room; <5 min response |
| **CCTV** | Full perimeter coverage with IR/low-light; 30-day min retention; remote monitoring |
| **Access Control** | Multi-factor authentication at all entry points; visitor management system; vehicle search |
| **Guard Force** | Risk-appropriate manning; documented response procedures; training records; comms equipment |
| **Lighting** | Full perimeter and approach lighting to CCTV-performance LUX standards; emergency backup |
| **Resilience** | UPS + backup generator with 72-hour min fuel autonomy; redundant fibre paths; fire suppression in data halls |
| **Counter-UAS** | For High/Critical rated sites: drone detection with alerting; documented response SOP |

---

## 8. Deliverables (Section 8)

Each assessment produces:
1. **Site Asset Register** — catalogued inventory with GPS coordinates and photographs
2. **Context Profile Scorecard** — all 7 dimensions scored with supporting evidence and source citations
3. **Threat Assessment Matrix** — each threat assessed for likelihood and consequence at the specific site
4. **Vulnerability Gap Analysis** — controls mapped against threats, gaps highlighted
5. **Physical Security Risk Rating** — composite with narrative and portfolio benchmark comparison
6. **Prioritised Recommendations Register** — costed and time-bound remediation ranked by risk reduction impact

Classification: **TLP:AMBER** default for site-specific assessments. Portfolio summaries may be **TLP:GREEN**.

---

## 9. Quality Assurance (Section 9)

- Methodology reviewed **annually** or following significant threat landscape change
- All assessors must be **Concentric-certified** in physical security assessment + satellite communications fundamentals + country-specific regulatory environment
- **Annual inter-rater reliability exercises** — maximum permissible variance between assessors on any single dimension is **1.0 points**

---

## 10. Register Note

The methodology states: *"The accompanying spreadsheet provides an initial risk register of identified global LEO basestation locations with preliminary risk ratings derived from this methodology."*

This is the **80-site (or larger) risk register** referenced in principal communications. It has not been uploaded as of the methodology ingestion date. When obtained, full site risk register should be cross-referenced with the 15 sites profiled in `geography/site_risk_profile.md` and the 129-site register from the Concentric Market Opportunity Assessment.
