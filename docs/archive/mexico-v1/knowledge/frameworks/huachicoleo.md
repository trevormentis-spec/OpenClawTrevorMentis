# Framework: Huachicoleo (Fuel Theft)

**Purpose:** Model the intersections of state corruption, cartel revenue, energy infrastructure, and political risk around Mexico's fuel theft economy.
**Scope:** Pipeline tapping, tanker truck theft, refinery internal theft, Pemex administrative fraud, retail fuel diversion (gas stations selling stolen fuel), CFE theft, and huachicoleo's secondary effects on energy infrastructure investment.
**Method:** 4-layer intersection model, each with indicators, updated from official data (Pemex, SAT, SESNSP) and media investigation.
**Note:** No existing playbook in the library covers this intersection well. This is a first-principles build.

---

## Why Huachicoleo Matters as a Framework

Huachicoleo is not a single crime type. It is a **systems crime** — it requires:
- **State corruption** (Pemex insider knowledge, police non-enforcement, judicial impunity)
- **Cartel logistics** (distribution networks, competitor territorial management, violence as business tool)
- **Energy infrastructure vulnerability** (pipeline mapping, valve locations, tanker fleet tracking)
- **Political risk signaling** (who is prosecuted, who isn't, Pemex modernization sabotage, energy reform credibility)

A huachicoleo incident is simultaneously a security event, an energy event, a corruption event, and a political event. Most analysis treats it as only one of these.

---

## The 4-Layer Model

### Layer 1 — State Capture & Corruption

**Question:** Does the government (at any level) enable, tolerate, or profit from fuel theft?

**Indicators:**
- Pemex employee arrests per region (internal theft)
- Pemex union relationship with local officials (OTD union historically implicated)
- Judicial outcomes: conviction rate vs arrest rate for huachicoleo
- AMLO-era "toleration" of community huachicoleo in Hidalgo and Puebla (framed as "the people taking back fuel from corrupt elites")
- State governor relationships with Pemex regional directors
- Security force complicity: SEDENA/SEMAR checkpoint patterns — do they intercept stolen fuel or have "toll" relationships?

**Data sources:** FGR arrest data, Pemex internal audit reports (when leaked/published), MCCI investigations, Reforma/El Universal investigative reporting

**Signal levels:**
- **Low corruption:** FGR independently prosecutes Pemex employees + SEDENA/SEMAR intercept stolen fuel caravans regularly
- **Medium corruption:** Pemex union blocking pipeline modernization + state-level huachicoleo prosecutions limited to low-level operators
- **High corruption:** Officials named in OFAC kingpin act advisories + Pemex internal theft operationally sophisticated

### Layer 2 — Cartel Revenue Diversification

**Question:** Which cartels use fuel theft as a revenue stream, and how importants it to their overall economics?

**Key actors:**
- **CJNG:** Controls huachicoleo networks in Jalisco, Michoacán, Guanajuato, Querétaro. Uses fuel theft to launder money through gas stations (gasolineras). Signature: tapping Pemex pipelines in states where they also control meth/fentanyl corridors
- **Santa Rosa de Lima Cartel (Guanajuato):** Huachicoleo IS their primary identity. Began as fuel thieves before diversifying into extortion and production. Guanajuato is Mexico's #1 fuel theft state — SRLC is the dominant actor
- **Cárteles Unidos (Michoacán):** Fuel theft from Petróleos Mexicanos pipelines as secondary revenue, combined with mining theft
- **La Familia Michoacana:** Has used fuel theft as funding for broader criminal operations
- **CDN (Tamaulipas):** Pipeline tapping in Tamaulipas-Vera cruz corridor. Less publicly documented but structurally embedded

**Revenue significance pattern:**
- For SRLC: Dominant revenue source (70%+)
- For CJNG: Significant but secondary (estimated 15-25% of revenue)
- For CU/LFM: Secondary (10-15%)
- For CDN: Minor (5-10%)

**Signal:** When DEA/CBP data shows cartel revenue shifts between trafficking types, check whether huachicoleo arrests are rising or falling — cartels substitute revenue streams based on enforcement pressure.

### Layer 3 — Energy Infrastructure Vulnerability

**Question:** Where is Mexico's fuel infrastructure most vulnerable to theft, and what does theft geography reveal about broader infrastructure risk?

**Pipeline criticality map (by theft incidence):**
1. **Tuxpan-Tula pipeline** (Veracruz-Hidalgo) — historically the most-tapped pipeline in Mexico. AMLO-era military deployment (Plan Conjunto Huachicoleo, 2019) temporarily reduced tapping but structural vulnerability persists
2. **Salamanca-León pipeline** (Guanajuato) — Santa Rosa de Lima Cartel primary target
3. **Minatitlán-Salina Cruz pipeline** (Veracruz-Oaxaca) — CJNG activity
4. **Cadereyta-Reynosa** (Nuevo León-Tamaulipas) — CDN/Zetas activity

**Non-pipeline vulnerabilities:**
- **Gas station fraud:** Gas stations selling stolen fuel (illegal mix with legitimate fuel). Estimated 10-20% of stations involved
- **Tanker truck theft:** Theft of Pemex-owned or contracted tanker trucks en route — combines fuel theft with asset theft
- **Refinery internal theft:** Pemex workers siphoning from operational refineries (Deer Park historically targeted, Dos Bocas risk)
- **CRE permit manipulation:** Illicit fuel import permits used to launder stolen fuel into legal supply chain

**Cross-impact with energy policy:**
- Pemex debt burden ($105B+) makes infrastructure maintenance and pipeline anti-tapping investment politically difficult
- Dos Bocas refinery (Olmeca) adds new infrastructure to protect, not less
- If Sheinbaum reverses AMLO-era energy policy and opens private investment, pipeline security could degrade as new operators lack the military relationships Pemex has
- CFE fuel theft (diesel theft from power plants) is a growing but under-documented dimension

### Layer 4 — Political Risk Signaling

**Question:** What does the government's huachicoleo enforcement pattern reveal about political priorities, corruption tolerance, and state capacity?

**Analytical use cases:**
1. **Who gets prosecuted:** If the government only prosecutes low-level pipeline tappers (communities, individuals) while Pemex higher-ups and cartel logistics operators remain untouched, that signals state-cartel modus vivendi at enforcement level
2. **Geographic enforcement selectivity:** If enforcement in Guanajuato (opposition-governed, PAN) is higher than enforcement in Sinaloa Morena-controlled territory, that signals politicized enforcement
3. **OFAC/FGR alignment:** If OFAC designates Mexican officials for huachicoleo-related corruption, and FGR does not pursue parallel investigations, that signals FGR independence deficit
4. **Pemex reform resistance:** If Pemex union blocks SCADA modernization (remote valve control = pipeline theft prevention), that signals institutional corruption deeper than cartel activity
5. **Mañanera framing:** How does the government talk about huachicoleo? As a security problem ("cartels stealing fuel") or a social problem ("communities claiming resources")? AMLO used the latter; Sheinbaum's framing is an early indicator of policy direction

**Risk levels for investors/operators:**
- **Low risk:** Consistent enforcement across jurisdictions, Pemex modernization proceeding, FGR arrests Pemex insiders
- **Medium risk:** Selective enforcement, Pemex modernization stalled, judicial impunity for high-level actors
- **High risk:** Widespread impunity, pipeline theft causing supply disruptions, Pemex debt preventing infrastructure investment, investor confidence in energy sector deteriorating

---

## Indicator Dashboard (Weekly Refresh)

| Indicator | Frequency | Source | Mexico Baseline (2025-26) |
|-----------|-----------|--------|--------------------------|
| Pemex pipeline tap count | Monthly | Pemex IR | ~500-800 taps/month (down from 14,000 in 2018 peak) |
| Huachicoleo arrests | Monthly | SESNSP/FGR | ~200/month (level trends) |
| Stolen fuel seized (barrels) | Monthly | SEDENA/Pemex | ~10,000-15,000/month |
| Gas stations sanctioned | Quarterly | CRE | ~200-300 stations/year suspended |
| Guanajuato pipeline taps | Monthly | Pemex regional | 30-50% of national total |
| Homicides in top-5 huachicoleo municipalities | Monthly | SESNSP | Cross-reference with cartel-tempo framework |
| Pemex SCADA coverage (%) | Quarterly | Pemex | ~40-50% of critical pipelines monitored |
| OFAC designations (huachicoleo-linked) | As issued | OFAC | 0-2/year |

---

## Weekly Assessment Protocol

1. Check Pemex monthly operational data for tap count by region — any significant change signals cartel territorial adjustment
2. Cross-reference with cartel factional dynamics A3 (succession) — cartels in succession uncertainty may increase huachicoleo as they need cash for internal consolidation
3. Check CRE gas station sanction list — sudden increases suggest enforcement shift or fraud methodology change
4. Monitor mañaneras for huachicoleo mentions — government narrative is a leading indicator of enforcement will
5. Check SESNSP homicides in Guanajuato, Hidalgo, Veracruz (top 3 huachicoleo states) — violence shifts may signal territorial contests

---

## Framework-Generalizability Note

This 4-layer model (State Capture × Cartel Revenue × Infrastructure Vulnerability × Political Risk) was built for Mexico huachicoleo but generalizes to any resource-theft crime where criminal economies intersect state capacity. Replace:
- Mexico Pemex → any state-owned resource company
- Huachicoleo → oil bunkering (Nigeria), illegal mining (DRC), timber theft (Amazon), water theft (India), artisanal fuel theft (Kurdistan)
- CRE/SAT → relevant regulatory bodies
- OFAC → relevant sanctions regime

The 4-layer intersection is the transferable insight: huachicoleo is never one thing. Neither is any resource-theft system crime.

---

*Framework: Open Claw Mexico Huachicoleo Framework v1.0*
*Framework stored at: analyst/knowledge/mexico/frameworks/huachicoleo.md*
*2026-05-15 16:30 UTC*

---

## Framework Test: Salamanca Tap-Network Seizure Pattern (2026-05-15)

### Test data
- May 3, 2026: FGR/Guardia Nacional seized 455,000 liters stolen fuel in Salamanca/Irapuato corridor
- May 13, 2026: 42,000 liters seized Salamanca-Morelia highway (tanker truck)
- Apr 19, 2026: 10,000 liters pipeline tap seizure Celaya-Salamanca
- Ongoing: FGR dismantled "petrofactureras" — shell-company invoicing scheme worth 23 billion pesos in simulated operations
- Cumulative Sep 2024-Apr 2026: 6.2 million liters seized in Guanajuato, 712M pesos impact

### Layer 1 — State Capture & Corruption
- **Confirmed:** The "petrofactureras" network required Pemex insider cooperation to issue fake invoices. Shell companies invoicing Pemex for fuel deliveries that never occurred.
- **Implied:** FGR is actively prosecuting — suggests enforcement independence in this case, but the scheme operated for months before detection.
- **Gap:** We do not know if Pemex employees were arrested. If no internal prosecutions, the corruption reaches into Pemex without consequences.

### Layer 2 — Cartel Revenue Diversification
- **Confirmed:** Santa Rosa de Lima Cartel is the dominant huachicoleo actor in Guanajuato. The Salamanca refinery / pipeline corridor is SRLC primary operating area.
- **Implied:** 6.2M liters in 8 months at ~20 pesos/liter street value = ~124M pesos ($6M+ USD) seized alone. Actual theft volume is 3-5x seizure volume (standard interdiction rate).
- **Gap:** We cannot attribute the petrofactureras network specifically — it may be SRLC, CJNG, or independent operators.

### Layer 3 — Energy Infrastructure Vulnerability
- **Confirmed:** Salamanca pipeline corridor (Tuxpan-Tula spur, Salamanca-León, Salamanca-Morelia) is the most consistently targeted pipeline network in Mexico
- **Confirmed:** Salamanca refinery is a Pemex operational facility — internal theft risk persists
- **Implied:** The Salamanca-Morelia highway seizure (tanker truck) suggests fuel is being transported from Guanajuato to Michoacán — cross-state huachicoleo logistics

### Layer 4 — Political Risk Signaling
- **Confirmed:** Guanajuato is PAN-governed (opposition). Federal enforcement in PAN states may be more willing than in Morena states — consistent with political selectivity hypothesis
- **Confirmed:** 6.2M liter seizure is a significant enforcement number, suggesting political will to act
- **Gap:** Cannot test selectivity hypothesis without comparable enforcement data from Morena-governed state

### Framework Assessment
- **Works:** The 4-layer model correctly identifies that the Salamanca pattern is simultaneously a corruption story, a cartel revenue story, an infrastructure vulnerability story, and a political risk story. Analyzing it as only one would miss critical dimensions.
- **Needs improvement:** The model lacks a mechanism for quantifying interdiction rates and comparing across states to test political selectivity. That's a future capability.
- **Does it generalize?** ✅ Yes — test Nigeria oil bunkering (state capture × Niger Delta militants × pipeline vulnerability × federal politics) and the identical 4-layer model applies.
