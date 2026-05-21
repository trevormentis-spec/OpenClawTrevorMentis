# LEO Ground Station Site Risk Profile

## Introduction
This file tracks risk assessments for ground station sites across the Concentric 129-site register (Market Opportunity Assessment) and the 80+ site physical security risk register (Physical Security Methodology). Sites are assessed on:

1. **Deployment difficulty** (1-5 scale per Concentric Opportunity Assessment)
2. **Traffic volume tier** (1-5 per Concentric Traffic Value Model)
3. **Concentric 7-Dimension Site Context Profile** (Geopolitical Stability, Local Crime, Protest/Activism, Natural Hazard, Site Isolation, Existing Security Posture, Strategic Value — each 1-5)
4. **Likelihood × Consequence Risk Rating** (Negligible → Critical per Concentric risk matrix)
5. Regulatory, political, infrastructure, and operational risk dimensions

Where Concentric scoring dimensions have been formally assessed (from the physical security risk register), they are noted in the Risk Assessment tables. Where a full assessment has not been conducted, the site is rated using the deployment difficulty and traffic tiers only.

## 80-Site Global Risk Register (Ingested)

The 80-site Global Risk Register has been fully ingested into `config/topics/leo_ground_stations/entities.yaml` as 80 `ground_station_site` entities. Each site has:
- Ref ID, operator, country, region, lat/lon, status, architecture type
- Full 7-dimension context profile scores (each 1-5)
- Composite contextual score
- Concentric risk rating (Negligible → Critical)

### Register Summary

| Operator | Sites | Avg Composite Score |
|----------|-------|-------------------|
| Starlink | 38 | 2.13 |
| KSAT | 15 | 2.02 |
| OneWeb | 10 | 2.20 |
| Leaf Space | 9 | 2.07 |
| Kuiper | 5 | 1.53 |
| Telesat | 3 | 2.50 |

| Risk Rating | Count | % of Total |
|-------------|-------|-----------|
| Negligible | 13 | 16.3% |
| Low | 27 | 33.8% |
| Moderate | 34 | 42.5% |
| High | 6 | 7.5% |
| Critical | 0 | 0% |

| Region | Sites |
|--------|-------|
| N. America | 26 |
| Europe | 18 |
| Asia | 8 |
| Oceania | 7 |
| S. America | 6 |
| Africa | 5 |
| Pacific | 2 |
| Arctic | 2 |
| Caribbean | 1 |
| Central Asia | 1 |
| Polar | 1 |
| Middle East | 1 |
| Indian Ocean | 1 |
| Atlantic | 1 |

### High-Risk Sites (Composite >= 2.8 or Rated High)
| Ref | Site | Operator | Composite | Risk |
|-----|------|----------|-----------|------|
| SL-031 | Punta Arenas, Chile | Starlink | 2.85 | High |
| SL-050 | Lagos (Ajah), Nigeria | Starlink | 2.80 | High |
| SL-052 | Port Harcourt, Nigeria | Starlink | 3.15 | High |
| SL-053 | Sagamu, Nigeria | Starlink | 3.05 | High |
| SL-073 | Ushuaia Region, Argentina | Starlink | 2.95 | High |
| OW-004 | Baikonur Region, Kazakhstan | OneWeb | 3.15 | High |

### Out-of-Register Sites (Market Opportunity Assessment 129-Site Register)
The 15 additional sites from the principle-driven real_estate_sites.json analysis are now superseded by the 80-site risk register. Key out-of-register sites (in the 129-site Mkt Opp register but not in the 80-site physical security register) should be noted for future ingestion: Muscat/Duqm (Oman), Tashkent (Uzbekistan), Surabaya/Bali (Indonesia), Antananarivo (Madagascar), Nouméa (New Caledonia), Perth (Australia), and other market-opportunity-driven sites.

**Next step:** Cross-reference the 80-site physical security register with the 129-site market opportunity register to identify coverage gaps and reconciliation needs.

## Concentric Deployment Difficulty Scale (Source: Concentric Opportunity Assessment Mar 2026)

| Difficulty | Label | Characteristics |
|------------|-------|-----------------|
| 5 | Extreme | No law enforcement, seasonal access only, permafrost structural risk, polar darkness for months, emergency response in hours. Examples: Svalbard, Troll Antarctica, Rankin Inlet, Port Harcourt (Niger Delta), Baikonur region. |
| 4 | Very High | Combines high strategic value with genuine security threats or regulatory barriers. Examples: Lagos/Sagamu, Inuvik, Punta Arenas/Ushuaia, Sanya, Addis Ababa, Karachi. |
| 3 | Elevated | Solvable with professional security design but not trivial. Examples: Merrillan WI (severe winter, forest concealment), Manila (typhoon corridor), Maricá Brazil (dense informal urban), Hanoi/HCMC, Mumbai/Jakarta. |
| 2 | Moderate | Standard deployment challenges. Examples: Most Western sites, moderate-climate developing-market sites with good infrastructure. |
| 1 | Low | Straightforward deployment. Excellent infrastructure, stable governance. Examples: Perth, Thessaloniki, most European/US sites. |

## Concentric Traffic Tiers (Source: Concentric Traffic Value Model)

| Tier | Score | Driver | Example Sites |
|------|-------|--------|--------------|
| Peak | 5 | Constellation HQ/control, 100M+ population footprints, polar TT&C concentration | Redmond WA, N. Virginia, Hawthorne CA, Lagos, Tokyo, Manila, Jakarta, Mumbai, São Paulo, Ho Chi Minh City, KSAT Svalbard/Tromsø |
| High | 4 | Major European gateways, polar coverage, military strategic, southern hemisphere backbone | Goonhilly, Gravelines, Stuttgart, Fairbanks/Inuvik, Guam, Punta Arenas, Hartebeesthoek, Maricá, Puerto Rico, Abuja |
| Moderate | 3 | Standard GSaaS multi-mission, smaller gateways, US regional E-band, planned sites | Most GSaaS sites, US domestic backbone, new market entry pre-scaling |
| Low | 2 | Remote backup, low-population-density, early-phase expansion | Redundancy coverage, niche EO downlink |

## Regional Analysis (from Concentric Opportunity Assessment)

### Africa — Highest Priority, Highest Difficulty
Starlink operates in 20+ African countries with only 4 ground stations, all in Nigeria. Most under-served ground segment globally relative to subscriber growth. Kenya, South Africa, Ghana, Egypt, and Morocco are most likely next deployments. Most African deployments score 3-5 on difficulty.

### Southeast Asia — Highest Priority, Moderate Difficulty
Vietnam licensed Feb 2026 (4 Starlink stations planned, 600K terminal target). Indonesia, Philippines, Thailand represent largest near-term opportunity. India's 1.4B market anticipated 2026-27.

### Latin America — High Priority, Low-Moderate Difficulty
Brazil (200M+, Anatel regulatory friction), Mexico (130M, security concerns), Colombia, Argentina. Amazon Vrio partnership covers Latin America Kuiper distribution.

### Middle East — Moderate Priority, Low Difficulty
UAE, Saudi Arabia (NEOM OneWeb JV), Bahrain, Qatar. Well-resourced, security-capable, but data sovereignty creates regulatory complexity.

### Arctic and Polar — Critical Strategic Value, Maximum Difficulty
Svalbard and Troll are irreplaceable for polar TT&C. Telesat Rankin Inlet (fly-in only, permafrost, no law enforcement) is the single most challenging deployment in the entire register.

---

## Site Profiles

## 1. KSAT Svalbard, Norway (78°N)
- **Region:** Arctic / Polar
- **Fiber Access:** Satellite backhaul (limited)
- **Difficulty:** 5
- **Traffic Tier:** 5 (Peak)
- **Terrain:** Arctic permafrost
- **Coverage Gap For:** All polar-orbit constellations

### Risk Assessment
| Risk Category | Rating | Notes |
|--------------|--------|-------|
| Regulatory | Low | Norwegian sovereignty. Svalbard Treaty constraints. |
| Political | Low-Medium | Svalbard Treaty limits Norwegian sovereignty. Russian presence in archipelago. |
| Infrastructure | High | Satellite backhaul only. Seasonal access. Permafrost structural risk. |
| Environmental | Extreme | Polar darkness months. Extreme cold. Polar bears. |
| Security | High | No local law enforcement. Emergency response measured in hours. |

### Strategic Notes
Irreplaceable for polar TT&C. KSAT's polar monopoly asset. KSAT Hyper in-orbit relay concept may reduce ground dependency but will not eliminate polar ground need.

---

## 2. Troll Station, Antarctica (72°S)
- **Region:** Antarctic / Polar
- **Fiber Access:** Satellite backhaul only
- **Difficulty:** 5
- **Traffic Tier:** 5 (Peak)
- **Terrain:** Antarctic ice shelf

### Risk Assessment
| Risk Category | Rating | Notes |
|--------------|--------|-------|
| Regulatory | Low-Medium | Antarctic Treaty constraints. Norwegian claim. |
| Political | Low-Medium | Antarctic Treaty governance. |
| Infrastructure | Extreme | Seasonal access only (summer). Pre-positioned supplies. Satellite backhaul. |
| Environmental | Extreme | Extreme cold. Polar darkness. Katabatic winds. |
| Security | Extreme | No law enforcement. Emergency evacuation extremely difficult. |

### Strategic Notes
Southern hemisphere polar TT&C complement to Svalbard. KSAT operates. Essential for south-polar coverage symmetry.

---

## 3. Mombasa / Malindi, Kenya
- **Lat/Lon:** -4.04, 39.67
- **Region:** East Africa
- **Fiber Access:** Excellent (TEAMS/EASSy/LION2)
- **Difficulty:** 3
- **Traffic Tier:** 4 (High — projected)
- **Terrain:** Coastal tropical
- **Coverage Gap For:** Starlink, Kuiper, OneWeb

### Risk Assessment
| Risk Category | Rating | Notes |
|--------------|--------|-------|
| Regulatory | Low | Starlink licensed. Kenya Space Agency active. ESA Malindi nearby. |
| Political | Low | Stable governance. Western-aligned. |
| Infrastructure | Low | Excellent fiber connectivity. Multiple cable landings. |
| Environmental | Medium | Coastal tropical — corrosion, humidity, cyclone risk. |
| Security | Low-Medium | Terrorism risk in coastal Kenya (Al-Shabaab). |

### Strategic Notes
Highest-priority African site per Concentric. Only existing GS infrastructure is ESA Malindi tracking station. 55M population. Starlink expanding.

---

## 4. Accra / Tema, Ghana
- **Lat/Lon:** 5.56, -0.19
- **Region:** West Africa
- **Fiber Access:** Good (ACE/WACS/MainOne)
- **Difficulty:** 2
- **Traffic Tier:** 3 (Moderate — projected)
- **Terrain:** Coastal tropical
- **Coverage Gap For:** Starlink, Kuiper

### Risk Assessment
| Risk Category | Rating | Notes |
|--------------|--------|-------|
| Regulatory | Low | Starlink licensed. Ghana Space Science & Technology Institute. |
| Political | Low | Stable democracy. |
| Infrastructure | Low-Medium | Good fiber. ACE/WACS/MainOne cables. Power reliability moderate. |
| Environmental | Low-Medium | Coastal tropical humidity. |
| Security | Low | Low terrorism risk for West Africa. |

### Strategic Notes
Best West African coverage gap filler. Second-priority Africa site.

---

## 5. Lagos / Sagamu, Nigeria
- **Lat/Lon:** 6.52, 3.38
- **Region:** West Africa
- **Fiber Access:** Good (SAT-3, MainOne, WACS)
- **Difficulty:** 4
- **Traffic Tier:** 5 (Peak)
- **Terrain:** Coastal tropical / urban
- **Coverage Gap For:** All constellations (only 4 Starlink GS in Nigeria currently)

### Risk Assessment
| Risk Category | Rating | Notes |
|--------------|--------|-------|
| Regulatory | Medium | Nigerian Communications Commission active. Spectrum allocation complex. |
| Political | Medium | Stable but corruption concerns. |
| Infrastructure | Medium | Good fiber. Power grid unreliable. |
| Environmental | Medium | Coastal tropical. Urban congestion. |
| Security | High | Organized crime. Kidnapping risk in Sagamu area. Niger Delta militant groups. |

### Strategic Notes
Nigeria has all 4 existing Starlink African ground stations but more needed. Concentric rates Port Harcourt (Niger Delta) as Difficulty 5 due to militant group activity. Lagos less severe but still challenging.

---

## 6. Muscat / Duqm, Oman
- **Lat/Lon:** 23.59, 58.17
- **Region:** Middle East
- **Fiber Access:** Good
- **Difficulty:** 2
- **Traffic Tier:** 3 (Moderate — projected)
- **Terrain:** Desert coastal
- **Coverage Gap For:** Kuiper, OneWeb

### Risk Assessment
| Risk Category | Rating | Notes |
|--------------|--------|-------|
| Regulatory | Low | Open regulatory environment. |
| Political | Low | Stable Oman. Neutral foreign policy. Good US relations. |
| Infrastructure | Low-Medium | Growing. Etlaq Spaceport under construction (2027). |
| Environmental | Low-Medium | Desert heat, sand. |
| Security | Low | Low terrorism risk. |

### Strategic Notes
Top Middle East site. Etlaq Spaceport development will transform Oman into regional space hub.

---

## 7. Tashkent Area, Uzbekistan
- **Lat/Lon:** 41.3, 69.28
- **Region:** Central Asia
- **Fiber Access:** Developing
- **Difficulty:** 3
- **Traffic Tier:** 2-3 (Low-Moderate)
- **Terrain:** Continental steppe
- **Coverage Gap For:** Multiple constellations

### Risk Assessment
| Risk Category | Rating | Notes |
|--------------|--------|-------|
| Regulatory | Medium | Developing framework. BRI influence. |
| Political | Medium | Authoritarian. Reforming economy. |
| Infrastructure | Medium | Developing fiber. Power reliability moderate. |
| Environmental | Low | Continental steppe. |
| Security | Low | Low crime. Regional concern (Afghanistan border). |

### Strategic Notes
Central Asian coverage gap is significant but market size limited. BRI connectivity corridor.

---

## 8. Surabaya / Bali, Indonesia
- **Lat/Lon:** -7.28, 112.75
- **Region:** Southeast Asia — High Priority
- **Fiber Access:** Good (Java backbone)
- **Difficulty:** 3
- **Traffic Tier:** 4 (High — projected)
- **Terrain:** Tropical volcanic
- **Coverage Gap For:** Starlink, Kuiper

### Risk Assessment
| Risk Category | Rating | Notes |
|--------------|--------|-------|
| Regulatory | Low | Starlink licensed. |
| Political | Low | Stable democracy. |
| Infrastructure | Medium | Java backbone good. Bali tourist infrastructure excellent. |
| Environmental | High | Volcanic activity, seismic, tropical storms. |
| Security | Low | Generally low. |

### Strategic Notes
270M population. Archipelago geography demands multiple ground stations. Second Indonesian gateway needed alongside Jakarta.

---

## 9. Pune / Hyderabad, India
- **Lat/Lon:** 18.52, 73.86
- **Region:** South Asia — Highest Priority
- **Fiber Access:** Excellent
- **Difficulty:** 2
- **Traffic Tier:** 5 (Peak — projected)
- **Terrain:** Deccan plateau
- **Coverage Gap For:** Starlink, Kuiper

### Risk Assessment
| Risk Category | Rating | Notes |
|--------------|--------|-------|
| Regulatory | Medium | Expected 2026-27. Foreign ownership restrictions on telecom. |
| Political | Low | Stable Modi government. Pro-space policy. |
| Infrastructure | Excellent | Tech hub. AWS AP-South-1. Strong fiber. Power stable. |
| Environmental | Low | Deccan plateau — dry, stable. |
| Security | Low-Medium | Major tech hubs secure. |

### Strategic Notes
1.4B population market — largest coverage gap by population. Massive subscriber potential. Starlink granted regulatory approval as part of broader US diplomatic engagement. Kuiper also targeting.

---

## 10. Dakar, Senegal
- **Lat/Lon:** 14.69, -17.44
- **Region:** West Africa
- **Fiber Access:** Good (ACE cable)
- **Difficulty:** 3
- **Traffic Tier:** 3 (Moderate — projected)
- **Terrain:** Coastal semi-arid
- **Coverage Gap For:** Skynopy, OneWeb

### Risk Assessment
| Risk Category | Rating | Notes |
|--------------|--------|-------|
| Regulatory | Low | Open. |
| Political | Low | Stable governance. Francophone — strong French ties. |
| Infrastructure | Medium | ACE cable landing. Power reliability moderate. |
| Environmental | Low | Semi-arid. |
| Security | Medium | Sahel terrorism spillover risk. |

### Strategic Notes
Skynopy/CNES have strategic interest. French overseas positioning. Gateway to Sahel region.

---

## 11. Antananarivo Area, Madagascar
- **Lat/Lon:** -18.88, 47.51
- **Region:** Indian Ocean
- **Fiber Access:** Limited
- **Difficulty:** 4
- **Traffic Tier:** 2 (Low)
- **Terrain:** Tropical highland
- **Coverage Gap For:** KSAT, Leaf Space

### Risk Assessment
| Risk Category | Rating | Notes |
|--------------|--------|-------|
| Regulatory | Medium | Developing. |
| Political | Medium | Periodic instability. Corruption. |
| Infrastructure | High | Limited fiber. Power unreliable. |
| Environmental | Medium | Tropical highland. Cyclone risk. |
| Security | Low | Low crime. |

### Strategic Notes
Highest difficulty (4). Only justified if Indian Ocean coverage is strategic priority. Réunion (French) nearby provides alternative.

---

## 12. Medellín Area, Colombia
- **Lat/Lon:** 6.25, -75.56
- **Region:** South America
- **Fiber Access:** Good
- **Difficulty:** 2
- **Traffic Tier:** 3 (Moderate — projected)
- **Terrain:** Mountain valley
- **Coverage Gap For:** Starlink, Kuiper

### Risk Assessment
| Risk Category | Rating | Notes |
|--------------|--------|-------|
| Regulatory | Low | Starlink active. |
| Political | Medium | Left-wing government. US relations complex. |
| Infrastructure | Good | Growing tech hub. AWS Bogotá nearby. |
| Environmental | Low | Mountain valley — mild. |
| Security | Medium | Lower than other Colombian regions but elevated. |

### Strategic Notes
Andean coverage gap. Growing AWS presence. Key Latin American site.

---

## 13. Thessaloniki, Greece
- **Lat/Lon:** 40.64, 22.94
- **Region:** Southeast Europe
- **Fiber Access:** Good
- **Difficulty:** 1
- **Traffic Tier:** 3 (Moderate)
- **Terrain:** Coastal
- **Coverage Gap For:** KSAT (extends Athens)

### Risk Assessment
| Risk Category | Rating | Notes |
|--------------|--------|-------|
| Regulatory | Very Low | EU regulated. |
| Political | Very Low | Stable EU/NATO. |
| Infrastructure | Excellent | Good fiber. EU power grid. |
| Environmental | Low | Mediterranean. |
| Security | Very Low | Very low crime. |

### Strategic Notes
Lowest difficulty (1) of any assessed site. EU member provides regulatory certainty for data sovereignty.

---

## 14. Perth Suburbs, Australia
- **Lat/Lon:** -31.95, 115.86
- **Region:** Oceania
- **Fiber Access:** Excellent
- **Difficulty:** 1
- **Traffic Tier:** 3 (Moderate)
- **Terrain:** Coastal temperate
- **Coverage Gap For:** Starlink, Kuiper

### Risk Assessment
| Risk Category | Rating | Notes |
|--------------|--------|-------|
| Regulatory | Very Low | Open. Five Eyes alignment. |
| Political | Very Low | Stable. Close US/UK alliance. |
| Infrastructure | Excellent | Excellent fiber. AWS AP-Southeast-2. |
| Environmental | Low | Temperate. Wildfire risk occasional. |
| Security | Very Low | Very low. |

### Strategic Notes
Difficulty 1. Five Eyes member provides security advantages for defence customers. Western Australia complement to Geraldton.

---

## 15. Nouméa, New Caledonia
- **Lat/Lon:** -22.28, 166.46
- **Region:** South Pacific
- **Fiber Access:** Good (Gondwana-2)
- **Difficulty:** 3
- **Traffic Tier:** 2-3 (Low-Moderate)
- **Terrain:** Tropical island
- **Coverage Gap For:** Skynopy, OneWeb

### Risk Assessment
| Risk Category | Rating | Notes |
|--------------|--------|-------|
| Regulatory | Low | French sovereignty. |
| Political | Medium | Independence referendum tensions (2018-2021). Stayed French. |
| Infrastructure | Medium | Good fiber. Remote logistics. |
| Environmental | Medium | Tropical. Cyclone risk. |
| Security | Low | Low crime. |

### Strategic Notes
Strategic for French Pacific coverage. Skynopy/CNES strategic asset. French overseas territory advantage.

---

## 16. Djibouti City, Djibouti
- **Lat/Lon:** 11.59, 43.15
- **Region:** Horn of Africa
- **Fiber Access:** Excellent
- **Difficulty:** 3
- **Traffic Tier:** 3-4 (Moderate-High — military demand)
- **Terrain:** Desert coastal
- **Coverage Gap For:** Multiple military + commercial

### Risk Assessment
| Risk Category | Rating | Notes |
|--------------|--------|-------|
| Regulatory | Low | Open. Attracts foreign military. |
| Political | Medium | Authoritarian but stable. Multi-power basing. |
| Infrastructure | Good | Excellent fiber. Extreme heat. |
| Environmental | High | Extreme heat (40°C+). Sand and dust. |
| Security | Medium | Regionally stable. Terrorism risk general. |

### Strategic Notes
Unique location: US, French, Chinese, Japanese military bases simultaneously. Multiple cables. Military demand driver significant.

---

## 17. Tangier Area, Morocco
- **Lat/Lon:** 35.77, -5.8
- **Region:** North Africa
- **Fiber Access:** Good
- **Difficulty:** 2
- **Traffic Tier:** 3 (Moderate — projected)
- **Terrain:** Mediterranean
- **Coverage Gap For:** OneWeb, Starlink

### Risk Assessment
| Risk Category | Rating | Notes |
|--------------|--------|-------|
| Regulatory | Low | OneWeb approval expected 2025. |
| Political | Low | Stable monarchy. Close EU/US ties. |
| Infrastructure | Good | Good fiber. Tangier Med port. |
| Environmental | Low | Mediterranean. |
| Security | Low | Low terrorism risk. |

### Strategic Notes
Gibraltar Strait strategic position. North African gateway. EU-adjacent for data sovereignty.

---

## 18. Ulaanbaatar Area, Mongolia
- **Lat/Lon:** 47.92, 106.92
- **Region:** East Asia
- **Fiber Access:** Developing
- **Difficulty:** 4
- **Traffic Tier:** 2 (Low)
- **Terrain:** Continental steppe
- **Coverage Gap For:** Multiple

### Risk Assessment
| Risk Category | Rating | Notes |
|--------------|--------|-------|
| Regulatory | Medium | Developing. |
| Political | Low | Stable democracy. Between Russia and China. |
| Infrastructure | High | Developing fiber. -40°C winter. |
| Environmental | High | Extreme cold. Dust storms. |
| Security | Low | Very low crime. |

### Strategic Notes
Between Russian and Chinese infrastructure — unique geopolitical position. High difficulty (4), low traffic.

---

## Summary: Site Priority Ranking by Risk-Adjusted Opportunity

| Priority | Site | Diff. | Traffic | Risk Score | Opportunity |
|----------|------|-------|---------|-----------|-------------|
| 1 | Pune/Hyderabad, India | 2 | 5 (Peak) | Low-Med | Very High |
| 2 | Perth, Australia | 1 | 3 (Mod) | Very Low | High |
| 3 | Accra/Tema, Ghana | 2 | 3 (Mod) | Low | High |
| 4 | Muscat/Duqm, Oman | 2 | 3 (Mod) | Low | High |
| 5 | Mombasa/Malindi, Kenya | 3 | 4 (High) | Low-Med | High |
| 6 | Thessaloniki, Greece | 1 | 3 (Mod) | Very Low | Medium |
| 7 | Medellín, Colombia | 2 | 3 (Mod) | Low-Med | Medium |
| 8 | Surabaya/Bali, Indonesia | 3 | 4 (High) | Medium | High |
| 9 | Tangier, Morocco | 2 | 3 (Mod) | Low | Medium |
| 10 | Nouméa, New Caledonia | 3 | 2-3 | Low-Med | Medium |
| — | Lagos/Sagamu, Nigeria | 4 | 5 (Peak) | High | Very High (risk-adjusted) |
| — | KSAT Svalbard, Norway | 5 | 5 (Peak) | Very High | Critical (irreplaceable) |
| — | Dakar, Senegal | 3 | 3 (Mod) | Low-Med | Medium |
| — | Djibouti City, Djibouti | 3 | 3-4 | Medium | Medium |
| — | Tashkent, Uzbekistan | 3 | 2-3 | Medium | Low-Med |
| — | Antananarivo, Madagascar | 4 | 2 | Medium-High | Low |
| — | Ulaanbaatar, Mongolia | 4 | 2 | High | Low |

## Sources
- Principal data (real_estate_sites.json)
- Concentric Security Group LEO Ground Station Market Opportunity Assessment (Mar 2026)
- CIA World Factbook (country risk profiles)
- Open-source infrastructure reports

## Appendix: Concentric 129-Site Register Note
The Concentric assessment references a 129-site ground station register (16 operators, 45+ countries) with full traffic, difficulty, and risk data. The full register is in the accompanying spreadsheet (not extracted in the opportunity assessment text). Sites profiled above are the 15 highest-priority new-build sites plus additional critical existing sites. The full 129-site register should be obtained and ingested for complete coverage.
