# Blocklist Audit — 2026-05-18

**Source:** analyst/config/scope.yaml — `out_of_scope_keywords`
**Audited against:** adjacency_vectors in same file
**Status:** Proposed changes only — no auto-modification

---

## Audit Method

Each blocked keyword was checked against:
1. Whether any existing adjacency vector provides a credible Mexico transmission mechanism for topics containing that keyword
2. Whether the keyword is broad enough to catch topics with genuine Mexico relevance (overreach risk)
3. Whether the block saves meaningful cost vs. the cost of misclassifying adjacent topics

---

## Keyword-by-Keyword Audit

### "russia ukraine", "russia ukraine front", "ukraine war", "ukraine russia", "ukraine front"

- **Rationale:** Broad geographic exclusion — Ukraine war is the paradigmatic out-of-scope topic
- **Adjacency contradiction:** EXISTS — "wheat-imports" and "fertilizer-corridor" vectors both connect Ukraine/Russia topics to Mexico (wheat prices → tortilla inflation; fertilizer → Bajío input costs)
- **Overreach risk:** HIGH — the blocklist entry is broader than the adjacency vectors. "Ukraine war" blocks ALL Ukraine-Russia topics, but specific angles (wheat supply, fertilizer corridor) are adjacent
- **Proposed action:** RECLASSIFY to adjacency-only — remove blocklist entries, ensure LLM can find adjacency vectors for wheat/fertilizer angles

### "china taiwan"

- **Rationale:** Classic geopolitical out-of-scope topic
- **Adjacency contradiction:** EXISTS — "china-precursors" vector (fentanyl precursors). Also, Taiwan semiconductor disruption would affect Mexican electronics assembly (not in any vector but real)
- **Overreach risk:** MODERATE — "China" is too broad a block; it catches topics with real adjacency through precursor chemicals and supply chains
- **Proposed action:** REMOVE — replace with more specific "taiwan invasion", "cross-strait" if block needed at all

### "south china sea"

- **Rationale:** Maritime security, out-of-scope
- **Adjacency contradiction:** EXISTS — "china-precursors" vector (fentanyl via Chinese chemicals). Also, semiconductor supply chain, Pacific shipping lanes, Mexican port security
- **Overreach risk:** MODERATE — has Mexico vectors through three distinct channels
- **Proposed action:** REMOVE — covered by LLM slow-path with china-precursors vector

### "north korea missile"

- **Rationale:** Northeast Asia security, no Mexico relevance
- **Adjacency contradiction:** NONE — no adjacency vector connects NK missile tests to Mexico
- **Overreach risk:** LOW — narrow keyword, unlikely to catch Mexico-relevant topics
- **Proposed action:** KEEP

### "israel gaza"

- **Rationale:** Middle East conflict, out-of-scope
- **Adjacency contradiction:** POSSIBLE — oil prices (Brent/Pemex) are an explicit vector. Israel-Hamas war affects oil prices. But the keyword is specific enough that "Israel Gaza" topics would typically not have additional Mexico vectors beyond oil
- **Overreach risk:** LOW-MODERATE — some Israel-Gaza topics affect oil prices (adjacent via brent-pemex) but most don't
- **Proposed action:** KEEP — oil-price adjacency is handled by LLM examining topic content, not by keyword

### "iran nuclear"

- **Rationale:** Middle East security, out-of-scope
- **Adjacency contradiction:** POSSIBLE — Iran nuclear deal affects oil markets (brent-pemex vector)
- **Overreach risk:** LOW — keyword specificity is high; oil angle is narrow
- **Proposed action:** KEEP

### "european union", "europe region"

- **Rationale:** Geographic exclusion — broad Europe
- **Adjacency contradiction:** EXISTS — ECB rate decisions (adjacent via peso/financial channels) and EU trade policy (affects USMCA indirectly)
- **Overreach risk:** HIGH — "european union" blocks ECB, EU trade policy, and any Europe-Mexico economic topic. The ECB probe (Probe B) was blocked by this until the LLM slow-path fix
- **Proposed action:** REMOVE "european union" — too broad. "europe region" can stay as it's a geographic descriptor not likely to appear in Mexico-adjacent queries

### "africa", "sahel"

- **Rationale:** Geographic exclusion
- **Adjacency contradiction:** NONE — no adjacency vector connects Africa/Sahel to Mexico
- **Overreach risk:** LOW — no Mexico transmission mechanism
- **Proposed action:** KEEP

### "middle east"

- **Rationale:** Geographic exclusion
- **Adjacency contradiction:** EXISTS — oil prices (brent-pemex) connect Middle East to Mexico via energy markets
- **Overreach risk:** MODERATE — "middle east" blocks ALL Middle East topics, but oil-specific topics are adjacent
- **Proposed action:** KEEP — "middle east" is too broad to be specific; oil adjacency is better handled by LLM examining topic content (e.g. "Saudi oil production" vs "Yemen civil war")

### "afghanistan", "pakistan"

- **Rationale:** Geographic exclusion
- **Adjacency contradiction:** NONE — no adjacency vector
- **Overreach risk:** LOW
- **Proposed action:** KEEP

### "india china"

- **Rationale:** Bilateral geopolitical tension, out-of-scope
- **Adjacency contradiction:** EXISTS — "china-precursors" vector. India-China border tensions affect Chinese export policy and global supply chains
- **Overreach risk:** LOW-MODERATE — narrow keyword, but China angle catches precursor chemical relevance
- **Proposed action:** KEEP — narrow keyword; LLM adjacency borderline

### "global finance"

- **Rationale:** Global financial topics, out-of-scope
- **Adjacency contradiction:** EXISTS — ECB rates, Fed policy, global capital flows all affect Mexican peso and bonds (economy_markets theme)
- **Overreach risk:** HIGH — this keyword blocks ALL "global finance" topics, many of which have direct Mexico relevance (capital flows, EM debt, FX markets)
- **Proposed action:** REMOVE — this is the most overreaching blocklist entry. Global finance IS Mexico-adjacent through economy_markets

### "asia pacific", "southeast asia"

- **Rationale:** Geographic exclusion
- **Adjacency contradiction:** EXISTS — "china-precursors" vector. Southeast Asia includes Indonesia (nickel, EV supply chains — see Item 4(a))
- **Overreach risk:** MODERATE-HIGH — "asia pacific" and "southeast asia" catch topics with genuine Mexico adjacency (EV supply chains, China's regional economic policy)
- **Proposed action:** REMOVE "asia pacific" — too broad and catches nickel/EV/SCS topics. RECLASSIFY "southeast asia" to adjacency-only or remove

### "nato europe"

- **Rationale:** Security alliance, out-of-scope
- **Adjacency contradiction:** NONE — no Mexico vector for NATO Europe
- **Overreach risk:** LOW — narrow keyword
- **Proposed action:** KEEP

---

## Summary

| Keyword | Overreach Risk | Has Adjacency Contradiction? | Proposed Action |
|---------|---------------|------------------------------|----------------|
| russia ukraine | HIGH | Yes (wheat, fertilizer) | RECLASSIFY — block specific sub-keywords only |
| ukraine war | HIGH | Yes (wheat, fertilizer) | RECLASSIFY |
| russia ukraine front | HIGH | Yes (wheat, fertilizer) | RECLASSIFY |
| ukraine russia | HIGH | Yes (wheat, fertilizer) | RECLASSIFY |
| ukraine front | HIGH | Yes (wheat, fertilizer) | RECLASSIFY |
| china taiwan | MODERATE | Yes (precursors) | REMOVE |
| south china sea | MODERATE | Yes (precursors, supply chain) | REMOVE |
| north korea missile | LOW | No | KEEP |
| israel gaza | LOW-MODERATE | Possible (oil) | KEEP |
| iran nuclear | LOW | Possible (oil) | KEEP |
| european union | HIGH | Yes (ECB, trade) | REMOVE |
| europe region | LOW | No | KEEP |
| africa | LOW | No | KEEP |
| sahel | LOW | No | KEEP |
| middle east | MODERATE | Yes (oil) | KEEP (oil handled by LLM) |
| afghanistan | LOW | No | KEEP |
| pakistan | LOW | No | KEEP |
| india china | LOW-MODERATE | Possible (China) | KEEP |
| global finance | HIGH | Yes (capital flows, FX) | REMOVE |
| asia pacific | MODERATE-HIGH | Yes (nickel, supply chains) | REMOVE |
| southeast asia | MODERATE-HIGH | Yes (nickel, EV) | RECLASSIFY |
| nato europe | LOW | No | KEEP |

### Count of problematic entries

- **Remove (definite overreach):** russia ukraine (5 variants), china taiwan, south china sea, european union, global finance, asia pacific = **10 entries**
- **Reclassify (adjacency-only, keep in scope.yaml as search terms):** ukraine variants (5), southeast asia = **6 entries**
- **Keep (low/no overreach):** 8 entries (NK missile, israel gaza, iran nuclear, europe region, africa, sahel, middle east, afghanistan, pakistan, india china, nato europe)

**Total problematic entries needing principal review: 16 of 23 keywords (70%)**

### Adjacency Vector Gap

The audit reveals a missing adjacency vector: **critical-minerals/supply-chain** — topics like Indonesian nickel, Taiwan semiconductors, and South China Sea shipping don't have a dedicated vector. The china-precursors vector covers fentanyl but not critical mineral supply chains or EV batteries. A new vector with appropriate search terms would capture these cleanly without over-broad blocklisting.

---

## Recommendation (deferred for principal review)

1. **Immediate:** Remove `european union`, `global finance`, `asia pacific` from blocklist — these are the most overreaching and cost the most in misclassified adjacency. No corresponding adjacency vector needs creation; existing vectors (brent-pemex, china-precursors) plus the LLM slow path handle them.
2. **Phase 2:** Reclassify Ukraine-Russia keywords from blocklist to adjacency-only — move to an `out_of_scope_blocklist_exceptions` section or handle via the LLM with specific search terms for wheat/fertilizer vectors.
3. **Phase 2:** Add a `critical-minerals` adjacency vector with search terms covering nickel, lithium, semiconductors, supply chain resilience, EV batteries — this fills the gap currently causing false negatives on otherwise-adjacent topics.
4. **No action:** Keep narrow/Euro keywords (NK missile, Iran nuclear, Afghanistan) — these have no Mexico transmission mechanism and the cost of checking each via LLM would exceed the benefit.
