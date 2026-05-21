# LEO Ground Station Industry State of Play, Q3 2026
**Validation Brief — Trevor (TREVOR) to Roderick**
*Classification: Internal / Analyst-to-Analyst*

---

## 1. Industry Overview: Capacity, Demand, and the Widening Gap

The ground segment is now the binding constraint on LEO. Space-side capacity has run ahead of terrestrial infrastructure by roughly an order of magnitude, and the divergence is accelerating.

**Headline numbers.** Total ground station market sizing at $41B today, projected to $82.7B by 2032 — 15.1% CAGR [Source: MarketsandMarkets]. The LEO-specific GSaaS slice is smaller but growing at comparable velocity: $1.72B → $5.33B, 14.2% CAGR [Source: DataIntelo]. On-orbit population moves from ~15K active LEO satellites today to 25K+ within the horizon, against a ground footprint moving from ~500 to 1,000+ stations [Source: Deloitte]. Note the asymmetry — sats compounding at ~7-8% while GS roughly doubles. The ratio worsens unless ISL adoption accelerates faster than projected.

**Architectural divergence is the dominant variable.** This is the part most market sizing reports miss. The "ground station" line item conflates two structurally different products:

- **Regenerative + ISL constellations** (Starlink, Kuiper) treat each GS as fungible. Loss of any single node degrades but does not eliminate service over its longitude band — traffic re-routes via optical inter-satellite links to the next available downlink. GS criticality per node is *low*.
- **Transparent bent-pipe constellations** (OneWeb, legacy GEO architectures) bind coverage directly to GS visibility. OneWeb's ~45 stations each carry materially higher per-node criticality than any one of Starlink's 170+ stations. Loss of a OneWeb gateway eliminates coverage across its entire footprint until rerouted through an adjacent gateway, assuming overlap exists — which over polar and oceanic regions, it frequently does not.

For risk and insurance purposes this means **the headline "GS count" is not comparable across operators.** A weighted criticality count is the correct metric. By that measure OneWeb is closer to Telesat in vulnerability profile than to Starlink, despite having ~14x the station count.

**The gap.** Concentric's opportunity assessment identifies 129 candidate sites versus 80 in the live risk register — a **49-site delta** representing announced or licensed buildout not yet operational. This is the forward order book for everyone in the value chain: site selection, security assessment, real estate, insurance underwriting. The geographic distribution of the gap is heavily skewed (see §3 and §6).

**Demand-side drivers** are well understood and need no expansion for this audience: defence (FORGE, Golden Dome, IRIS²), Earth observation cadence, direct-to-cell, sovereign capacity hedging. The relevant analytical question is not *whether* demand materialises but *which operators capture the GS economics* — and here the M&A activity of the last 18 months tells the story (see §2).

---

## 2. Operator Landscape

I'll tier these by strategic posture rather than revenue, since revenue understates positioning in this market.

### Tier 1: Sovereign-Anchored Incumbents

**KSAT (Norway).** 26 sites, 280+ antennas, ~$200M revenue [Source: Concentric ops profile]. Norwegian state-controlled via Space Norway/Kongsberg. The polar monopoly is the asset — Svalbard and Troll are not replicable on reasonable timelines, and the polar pass economics for sun-synchronous EO are structural. KSAT Hyper (Feb 2026) — the orbiting GS concept — is the most consequential technology bet by an incumbent (see §4). Risk register average 2.02; the high-latitude isolation tail (Troll 2.75, Svalbard adjacent) is offset by exceptional security posture and low crime/protest exposure.

**SSC (Sweden).** 21 sites, 100+ antennas, SEK 1.7B revenue. 100% Swedish state. Esrange remains the European launch-and-track anchor. Strategically more conservative than KSAT — less aggressive on GSaaS commercial expansion, more focused on government and ESA-linked work. The Swedish state ownership creates the same NATO-clean profile as KSAT but without the polar moat.

### Tier 2: European Sovereign Challengers

**Leaf Space (Italy).** 20+ sites, 40+ antennas, $50M total capital raised. Series B €20M July 2023, backed by CDP Venture Capital and Neva SGR — both Italian state development vehicles [Source: Concentric ops profile]. **3x YoY growth.** Adding 18 stations in current buildout, which would bring them to ~38 operational sites — overtaking SSC by site count, though not antenna count. Estimated valuation $80-120M. Clean NATO/Five Eyes posture, Italian sovereign cover, no Chinese capital exposure. Risk register average 2.07 — slightly above KSAT but reflecting more aggressive geographic expansion.

This is the most interesting independent in the European market. The CDP/Neva backing is patient capital with strategic objectives, not financial exit pressure. Likely consolidation target *or* consolidator depending on next 12-18 months.

**Skynopy (France).** Founded October 2023. 15+ antennas operational, ~$21M raised, CNES as investor [Source: Concentric ops profile]. Hybrid lease+own model — capital-efficient versus Leaf's owned infrastructure approach. Saint-Pierre and Réunion give them a credible non-metropolitan French sovereign footprint. AKAR project is the strategic spine. Target 100+ antennas by 2028 — aggressive, will require Series B in 2026-27. Estimated valuation $40-60M.

The strategic read: France is funding a national champion, deliberately, because IRIS² (€6B, 2029) needs sovereign French ground capacity that isn't dependent on KSAT or commercial US providers. Skynopy is the vehicle.

### Tier 3: US Commercial / Defence-Adjacent

**Atlas Space Operations.** 34+ sites, 50+ antennas. Freedom software platform. US Space Force FORGE C2 integration. **Being acquired by York Space Systems** (July 2025) — this is the most strategically significant M&A in the segment. York is a vertically integrated defence prime; Atlas becomes their ground segment with Golden Dome integration as the use case [Source: Concentric ops profile]. Atlas effectively exits the merchant GSaaS market for non-allied customers.

**RBC Signals.** 30+ sites via aggregation model. Only $3.2M raised. Acquired 10 Azure Orbital antennas via the SLI transaction in March 2025. Agile but capital-constrained — the Azure asset pickup was opportunistic and probably more than they can efficiently absorb without further capital. Watch for either a strategic investor round or distressed acquisition within 12 months.

**Viasat Real-Time Earth.** 10 sites, embedded inside the $2.3B Viasat parent. Strategically minor as a standalone but useful for Viasat's vertical bundling.

### Tier 4: Hyperscaler and Adjacent

**AWS Ground Station.** 12 regions, expanding GSaaS *partner* programme — note the shift in language. AWS is moving from direct ownership toward orchestration/partnership, mirroring (slowly) the trajectory Azure already completed.

**Azure Orbital.** **Exited 2024.** Assets to RBC Signals. This is a major signal — Microsoft concluded the unit economics of merchant ground stations don't fit the hyperscaler model. Implication: GS remains a specialist business, not a hyperscale commodity. Read this in §6.

**Infostellar (Japan).** 28-antenna marketplace model. $21.3M raised, ITOCHU/Mitsubishi/Airbus Ventures cap table — strong strategic backing. Viasat co-location relationships. The Japanese sovereign-friendly Asia-Pacific play.

### Tier 5: Constellation Operators (vertical GS)

- **Starlink:** 9,400+ sats, 170+ GS, 10M subscribers, regenerative + ISL [Source: Concentric ops profile]. GS criticality per node low.
- **Kuiper:** 212 sats, 300+ GS planned, regenerative + OISL. **FCC July 2026 deadline** is the binding constraint — half the constellation must be deployed. Behind schedule but not unrecoverable.
- **OneWeb (Eutelsat):** 648 sats, ~45 GS, transparent bent-pipe, no ISL. The Eutelsat→EQT €790M sale-leaseback (October 2024) extracted capital but locked OneWeb into the GS estate for the long term. Architecturally exposed.
- **Telesat Lightspeed:** 0 sats operational, 3 GS planned, SpaceX launches mid-2026. Highest risk register score (2.5) by operator average — function of small-N and concentration in challenging locales.
- **IRIS² (EU):** €6B, 2029 service date. Sovereign European LEO. Ground architecture not yet finalised but will heavily favour Leaf, Skynopy, SSC, and ESA-aligned providers.
- **Guowang (12,992 sats planned) + Qianfan (14,000 sats planned):** Chinese sovereign ecosystem. Treated as out-of-scope for Western GSaaS but relevant as a forcing function on sovereign capacity decisions in Africa, SE Asia, LatAm — where Chinese ground infrastructure offers are competing for the same host-country approvals.

### M&A read

- **Eutelsat→EQT (Oct 2024, €790M sale-leaseback):** financial engineering, not strategic consolidation. Signals Eutelsat liquidity constraints.
- **York→Atlas (Jul 2025):** strategic vertical integration, defence-driven. Removes Atlas from merchant market.
- **Azure Orbital exit → RBC (Mar 2025):** hyperscaler retreat. Reads as confirmation that GS is a specialist business.
- **KSAT Hyper (Feb 2026):** not M&A but architectural — covered in §4.

The pattern: hyperscalers out, defence primes in, sovereigns doubling down. Independent merchant GSaaS is being squeezed from both sides.

---

## 3. Geopolitical Risk Map

### 80-site register, distribution

| Band | Count | % |
|---|---|---|
| Negligible (1.0–1.5) | 13 | 16% |
| Low (1.5–2.0) | 27 | 34% |
| Moderate (2.0–2.5) | 34 | 43% |
| High (2.5–3.5) | 6 | 7% |
| Critical (3.5+) | 0 | 0% |

The distribution is reassuring at the headline level — no Critical sites — but the Moderate band at 43% is where most underwriting attention should focus. Moderate sites carry the highest *uncertainty*, not necessarily the highest expected loss, and they cluster in regions where one or two factor shifts can move a site into High.

### Top 6 High-risk sites

| Rank | Site | Score | Driver |
|---|---|---|---|
| 1= | Port Harcourt (NG) | 3.15 | Crime 5 |
| 1= | Baikonur (KZ) | 3.15 | Geo 3, Isolation 5 |
| 3 | Sagamu (NG) | 3.05 | Crime 4 |
| 4 | Ushuaia (AR) | 2.95 | Isolation 5 |
| 5 | Punta Arenas (CL) | 2.85 | Isolation 5 |
| 6 | Lagos (NG) | 2.80 | Crime 4 |

Three of the six are Nigerian — and Nigeria is **the only African country with operational GS in the register** despite Africa containing 20+ priority opportunity geographies. This is a structural problem (see §6).

Notable proximate-High sites:
- **Rankin Inlet (CA):** 2.80 — fly-in only, permafrost. Climate trajectory worsens this score over a 10-year underwriting horizon.
- **Troll (AQ):** 2.75 — Antarctic isolation, KSAT-operated, exceptional security posture offsets isolation.
- **Marica (BR):** 2.80 — favela proximity, crime, but high strategic value.

### Operator average risk score

| Operator | Avg Score | Read |
|---|---|---|
| Telesat | 2.50 | Small-N, frontier sites |
| OneWeb | 2.20 | Architectural exposure + geographic spread |
| Starlink | 2.13 | Volume normalises distribution |
| Leaf | 2.07 | Aggressive expansion into moderate locales |
| KSAT | 2.02 | Polar isolation offset by security |
| Kuiper | 1.53 | New build, lower-risk metro sites |

Kuiper's low score reflects buildout choices favouring secure metro-adjacent sites — consistent with Amazon's risk culture but contributing to coverage gaps in higher-risk geographies that they'll have to fill eventually.

### Regional deep dives

**West Africa (Nigeria cluster):** Crime scores of 4-5 across Lagos, Sagamu, Port Harcourt. Kidnap-for-ransom, oil-region militancy in PH, urban crime in Lagos. Mitigation costs are real — guard force, vehicular security, expat duty-of-care — but the alternative is ceding the entire West African market. Concentric's physical security offering maps directly onto this risk.

**Southern Cone (Ushuaia/Punta Arenas):** Isolation 5 across both. These are the southern polar-pass equivalents to Svalbard — irreplaceable for sun-synchronous downlink. Security posture is good (stable jurisdictions), but logistics, single-point-of-failure infrastructure, and weather drive the score.

**Central Asia (Baikonur):** The anomaly. Geopolitical 3 reflects Russian operational control on Kazakh territory; Isolation 5 reflects the physical reality. Most Western operators will not site here, but the listing is relevant for legacy GEO and Russian-adjacent operations.

**Arctic (Svalbard, Rankin Inlet, Troll):** Climate-trajectory risk is the under-weighted factor here. Permafrost degradation, ice road reliability, and storm intensification all move these scores upward over a 7-10 year horizon.

### 7-dimension methodology

For Roderick's reference, the weighting:

| Dimension | Weight |
|---|---|
| Geopolitical Stability | 20% |
| Natural Hazard | 15% |
| Crime | 15% |
| Isolation/Logistics | 15% |
| Security Posture | 15% |
| Protest/Civil Unrest | 10% |
| Strategic Value | 10% |

Each dimension 1-5 scale, weighted composite. **Two observations on the methodology** worth raising for the validation conversation:

1. **Strategic Value as a risk multiplier is contested.** In insurance terms, high strategic value increases *threat motivation* (state-level targeting) but also typically correlates with higher protective investment. The 10% weighting treats it as net-additive risk; an alternative formulation treats it as a *modifier* on PX (state-level) threat category.
2. **Cyber-physical risk is not a discrete dimension.** It's distributed across Security Posture and Geopolitical Stability. For ground stations, where the cyber attack surface is increasingly the primary threat vector (RF interference, supply chain implants, SDR-based intrusion), this is arguably under-weighted. Worth a methodology revision conversation.

### Threat taxonomy (8 categories)

| Code | Threat |
|---|---|
| PA | Physical access / intrusion |
| PS | Sabotage |
| PR | Surveillance / intelligence collection |
| PT | Theft (equipment, materials) |
| PD | Drone / UAS |
| PE | Environmental / natural |
| PC | Civil unrest |
| PX | State-level / military |

PD is the fastest-rising category and is materially under-mitigated across the register. Most GS estates have perimeter and access controls calibrated to pre-2022 threat models. Counter-UAS is currently the largest single capability gap in the merchant GSaaS estate.

---

## 4. Technology Disruption

### Optical inter-satellite links — the architectural pivot

The single most important industry trend is the bifurcation between regenerative+ISL and transparent constellations. Starlink's ISL mesh is mature; Kuiper's OISL is being deployed; OneWeb has no path to ISL on the current generation. The economic implications:

- **GS criticality per node** declines for ISL-enabled constellations. A Starlink GS lost to fire, sabotage, or natural hazard degrades capacity but doesn't create coverage gaps. Business interruption claims on a per-site basis are bounded.
- **GS criticality per node** for transparent constellations is unchanged or rising as constellations grow but bent-pipe architecture remains. OneWeb's gateway loss creates *footprint-scale* coverage gaps until alternate routing through an adjacent gateway is established — and over oceans/poles, that adjacency frequently doesn't exist.

This has direct underwriting implications (§5). It also has M&A implications — OneWeb's transparent architecture caps its long-term competitive position and is part of why Eutelsat extracted capital via sale-leaseback rather than reinvesting at scale.

### KSAT Hyper — orbiting ground station

February 2026 announcement. The concept: relay nodes in space act as ground-station functions for non-ISL constellations, effectively retrofitting bent-pipe operators with a quasi-ISL capability via a third party.

Strategic read:
- KSAT monetises its polar moat *and* extends into the space segment, capturing economics that would otherwise migrate to constellation operators.
- For OneWeb and similar transparent operators, this is an attractive partial mitigation against the architectural disadvantage — but it creates dependency on KSAT.
- For sovereign customers (defence, EO), Hyper is a sovereign-friendly alternative to commercial constellation services.

Hyper is, in my read, the most strategically consequential single product launch in the segment in three years. If it works, it changes the competitive economics; if it doesn't, KSAT has burnt capital but retains the polar monopoly. Asymmetric upside.

### Software-defined and multi-tenant antennas

Phased array, multi-tenant SDR-based stations are now standard for new builds. Antenna economics are improving by ~20-30% per generation. The implication is that the *capital efficiency* of buildout is rising, which partially offsets the ~$2-5M per-site cost of greenfield sites. This is part of why Leaf and Skynopy can credibly target rapid expansion at relatively modest capital raises.

### Quantum key distribution and post-quantum cryptography

Largely irrelevant for the next 5 years operationally but relevant for procurement specs in defence/sovereign customers — IRIS² in particular. Worth flagging only because it appears in RFPs and shapes vendor selection.

---

## 5. Insurance Market Implications

### Lloyd's and the underwriting case

The 7-dimension methodology maps cleanly onto a Lloyd's-style facility for ground station physical and business interruption risk. The current market structure under-prices three factor categories:

1. **Architectural criticality.** Transparent vs regenerative is not currently a rating factor in most physical/BI policies. It should be. A OneWeb gateway loss has materially different BI exposure than a Starlink GS loss.
2. **Cascading constellation risk (Kessler).** Cross-referenced via Kessler Sentinel data — orbital debris events create downstream GS demand spikes (replacement constellation surge) and constellation-loss correlations that current treaty structures don't address.
3. **Concentration risk by operator.** KSAT operates 280+ antennas — a systemic event at the operator level (cyber breach, sovereign action against Norway, etc.) creates correlated loss across the entire portfolio. Per-site policies don't capture this.

### Business interruption — the largest exposure

For LEO ground stations, BI is the dominant claim category. Physical damage to antennas is bounded (~$2-10M per antenna replacement, weeks-to-months downtime); BI claims compound by:

- Contracted SLA penalties to constellation operators
- Loss of priority pass slots (irrecoverable in real-time EO)
- Customer churn (in GSaaS marketplace models)

For transparent constellations, BI on a critical gateway can run into tens of millions per week of outage. For regenerative+ISL, BI is materially lower per site but the *aggregate* across a multi-site event (e.g., regional natural hazard taking out multiple sites) can still be material.

### Threat taxonomy and policy structure

The 8-category taxonomy (PA/PS/PR/PT/PD/PE/PC/PX) is more granular than typical commercial property exclusions. Most policies group PR/PT/PX under "war and terrorism" exclusions that are too broad. A purpose-built GS policy should:

- Treat PD (drone) explicitly — typically uncovered or contested under current language
- Treat PR (surveillance/intelligence) as a separate sub-line — relevant for state-actor targeting where physical damage may be minimal but operational compromise is total
- Carve PX (state-level) as either a separate facility or an explicit exclusion, with sovereign indemnity backstops for allied operators

### Kessler / orbital risk cross-reference

Concentric's Kessler Sentinel work cross-references here in two directions:
- **Upward:** GS outage increases the constellation operator's reliance on remaining capacity, which in some failure modes (manoeuvre commanding, debris avoidance) directly increases Kessler risk.
- **Downward:** Kessler events drive constellation replacement demand, which drives ground segment buildout demand, which drives the 129-site opportunity pipeline.

These are linked books of business and should be underwritten with awareness of the correlation.

### Pricing benchmark

For a Moderate-band site (2.0-2.5 composite), my read of equivalent Lloyd's lines suggests current pricing is ~40-60% of where a properly factored policy would sit. The market is under-priced because few underwriters have the methodology to differentiate sites. This is the commercial opportunity for Concentric's risk surveys — providing the methodological backbone that lets carriers price accurately, which is a structural advantage in a hardening market.

---

## 6. Strategic Observations for Roderick

Six points, calibrated.

### (1) The assessment business is the product

Concentric's three entry points — Physical Security to GSaaS providers, Insurance Market Risk Surveys for Lloyd's, and Secure Site Provision — share a common spine: **the assessment methodology**. The 7-dimension framework, the 80-site register, the threat taxonomy. The services are downstream; the methodology is the asset.

Recommendation: productise the methodology as a standalone subscription (annual register updates, methodology licensing to carriers) before commoditising it through services delivery. The IP capture window is 12-18 months before competitor analysts (Quilty, Analysys Mason) build equivalents.

### (2) The 129 vs 80 gap is the order book

49 sites in opportunity assessment not yet in the operational risk register. **Highly likely** (Sherman Kent: 80-95%) that 30-40 of these reach operational status within 24 months given current buildout velocity at Kuiper, Leaf, Skynopy, and Telesat. Each operational site represents:

- One physical security engagement
- One insurance underwriting cycle
- Potentially one secure site provision contract

The forward economics of the practice are functionally pre-booked if the methodology is the standard.

### (3) Kessler Sentinel cross-reference

Roderick — you already have this in the orbital book. The cross-product analytics (constellation loss → GS demand surge → site risk shift) are not currently surfaced as a joint product. **Probable** (60-80%) that a combined "Space-to-Ground Risk" facility could be syndicated through Lloyd's in 2027 if the analytics are productised in H1 2026. This is the highest-leverage internal cross-sell opportunity I can identify.

### (4) The Azure exit is the signal

Microsoft concluded that GS economics don't fit the hyperscaler model. AWS is following — note the shift to "partner programme" language. **Highly likely** that AWS materially reduces direct GS investment within 24 months. Implication: the merchant GSaaS market is consolidating around specialists (KSAT, Leaf, Skynopy, RBC) rather than diversifying into hyperscaler-owned capacity. This is good for the methodology business — fewer, more sophisticated counterparties who value rigorous risk analytics.

### (5) KSAT Hyper changes the methodology requirements

If Hyper succeeds, the risk register needs a new dimension: **dependency on third-party space-segment relays**. A OneWeb gateway riding through KSAT Hyper has a different risk profile than a standalone OneWeb gateway — KSAT-operator risk now propagates into OneWeb's GS estate. The methodology should be extended to capture this within 12 months.

### (6) European bifurcation and M&A targets

The European GSaaS market is bifurcating: KSAT/SSC (Nordic sovereign incumbents) versus Leaf/Skynopy (Mediterranean sovereign challengers). IRIS² procurement in 2027-28 will force consolidation choices. **Probable** consolidation scenarios:

- **Leaf as acquirer:** absorbs Skynopy or a smaller player. CDP/Neva have the capital structure to support it.
- **Leaf as target:** acquired by a defence prime (Leonardo, Airbus DS) at $150-250M as a sovereign anchor for IRIS².
- **Skynopy as target:** CNES-influenced acquisition by Thales Alenia Space or a French defence prime.

These are 18-30 month timelines. Concentric's positioning should include relationship coverage of CDP, Neva, CNES, and the relevant defence prime corp dev teams now.

### (7) Africa is the structural gap

20+ priority African geographies, 4 operational GS, all in Nigeria — and Nigeria has the three highest-risk sites in the register. The opportunity assessment flags Mombasa, Accra, Tangier among the 15 real estate priority sites. **Highly likely** that 2026-28 sees 10-15 new African GS, primarily East Africa (Kenya, Tanzania, Ethiopia) and North Africa (Morocco, Egypt). Each requires:

- Greenfield risk assessment (no historical register data)
- Local security partnership
- Insurance facility creation (current market poorly covers African GS)

Concentric is well-positioned given the broader Africa practice. This is the single largest geographic growth vector in the GS segment.

### (8) The 15 real estate priority sites

Mombasa, Accra, Muscat, Pune, Thessaloniki, Perth, Medellín, Tangier, and others. Each represents a secure site provision opportunity — and several (Muscat, Perth, Thessaloniki) are in jurisdictions where Concentric has existing physical security and real estate capability. Recommendation: prioritise three for proactive site control (option agreements, pre-built compounds) ahead of operator RFPs. Muscat and Perth in particular have NATO/Five Eyes-aligned demand profiles and sovereign customer interest.

### (9) Vietnam, India — Asian opening

Vietnam licensed Starlink in February 2026 with 4 stations planned. India is opening 2026-27. Both are sovereign-sensitive markets where Western GSaaS providers need local partnership structures. The risk register currently under-covers Asia ex-Japan; this is a methodology gap that should be closed in 2026.

### (10) RBC Signals as opportunistic acquisition

$3.2M total funding, 30+ sites via aggregation, just absorbed 10 Azure Orbital antennas. **Probable** (60-80%) that RBC requires further capital within 12 months. They are either acquired (by a defence prime, possibly the same vertical-integration logic as York/Atlas) or recapitalised by a strategic investor. Worth flagging to the Concentric corporate development side — not as an acquisition target for Concentric but as a counterparty whose change of control would shift the US merchant GS market.

---

## Summary calibration

| Claim | Confidence (Kent) |
|---|---|
| LEO GSaaS reaches $5B+ by 2032 | Highly likely (80-95%) |
| Transparent architecture operators (OneWeb-class) become acquisition targets within 36 months | Probable (60-80%) |
| KSAT Hyper achieves commercial deployment by end-2027 | Probable (60-80%) |
| AWS materially reduces direct GS investment within 24 months | Likely (55-70%) |
| 30-40 of the 49 opportunity-assessment sites reach operational status within 24 months | Highly likely (80-95%) |
| African GS count exceeds 15 by end-2028 | Probable (60-80%) |
| Leaf Space is consolidated (acquirer or target) by end-2027 | Likely (55-70%) |
| A combined Space-to-Ground Lloyd's facility is syndicatable in 2027 | Probable (60-80%) |

---

**End of brief.** Open for validation conversation — happy to extend on methodology revisions (cyber-physical weighting, strategic value as modifier vs additive), on the Kessler cross-product economics, or on the Leaf/Skynopy M&A scenarios in particular.

*— Trevor*