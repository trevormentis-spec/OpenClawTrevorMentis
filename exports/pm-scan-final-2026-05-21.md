# Prediction Market Divergence Scan — FINAL
Timestamp: 2026-05-21T03:42Z

## 1. Executive Summary
# Executive Summary: US-Iran Military Action Prediction Markets

**Market Snapshot (Kalshi):** Probability of US military action against Iran rises across tenors — June 10.5%, August 32.5%, Year-End 2026 50.5%, January 2028 75.5%. Polymarket's "before 2027" contract trades at 64%, a **13.5pp premium** to Kalshi's comparable YE26 tenor.

**Three Judgments:**

1. **Term structure is steeply upward-sloping**, implying markets price escalation as a matter of *when*, not *if* — with ~65pp of probability mass accumulating between now and early 2028.

2. **The 13.5pp Kalshi-Polymarket spread is exploitable** but likely reflects contract-language differences (action thresholds, definitions) and venue liquidity rather than pure mispricing. Verify resolution criteria before arbitraging.

3. **Near-term (June) risk is materially underpriced relative to year-end trajectory**, suggesting markets expect a catalyst-driven step-change rather than imminent kinetic action. Watch August as the inflection tenor.

## 2. Methodology
**Methodology:** At 2026-05-21T03:42Z, we scanned mid-market prices (bid-ask midpoint) across Kalshi (CFTC-regulated, USD-denominated), Polymarket (offshore, USDC-settled), PredictIt (academic exemption, $850 position cap per contract), and Manifold (play-money mana), normalizing contracts to comparable yes/no probabilities and flagging cross-venue spreads >3pp. Volume-weighted reliability tiers were assigned by 24h notional turnover and open interest, with Manifold prices down-weighted given non-monetary stakes.

**Liquidity caveats:** Thin order books (particularly on PredictIt due to position caps and on long-tail Polymarket/Kalshi markets) can produce stale mids, wide spreads, and arbitrage gaps that don't close; quoted probabilities should be treated as indicative rather than executable, especially outside US trading hours.

## 3. Key Divergences
# Three Prediction Market Divergences: Analysis

**1) Kalshi USAIRAN YE26 50.5¢ vs Polymarket before2027 64¢ (13.5pp gap)**

This gap almost certainly reflects resolution criteria differences rather than genuine probabilistic disagreement. Polymarket's "before 2027" markets typically use broader definitions of military action (including airstrikes, cyber, proxy engagements), while Kalshi contracts tend to require more formal/explicit US military involvement with stricter sourcing. A 13.5pp spread is too large to arbitrage if criteria differ — traders on each platform are pricing different events. Check exact contract language: terms like "military force," "armed conflict," or "strike" carry materially different thresholds.

**2) Kalshi USAIRAN Jun 10.5¢ vs Polymarket May31 16.5¢ (6pp gap)**

This is the most interesting divergence because the timeframes are *nearly* comparable but not identical — Polymarket's May 31 deadline is *earlier* yet priced *higher*. That's structurally suspicious unless resolution criteria again diverge (Polymarket likely counts lower-threshold events). Alternatively, it reflects platform liquidity asymmetry: Polymarket has heavier crypto-native speculative flow that overprices near-term tail events, while Kalshi's USD-denominated, KYC'd userbase tends toward more measured pricing. Six points is potentially arbitrageable if criteria align — worth scrutinizing.

**3) Trump-Iran personally 9% vs generic 50.5% (41.5pp gap)**

This is not a divergence — it's a coherent conditional structure. The 9% market asks whether Trump *personally* orders/authorizes specific action (narrow agent-specific criterion), while 50.5% captures *any* US military involvement (delegated strikes, allied coordination, defensive action, escalation under commanders). The 41.5pp spread implies traders assign ~80% of US-Iran conflict probability to scenarios where Trump isn't the explicit named actor on resolution. That's plausible: most kinetic engagement gets attributed institutionally ("US forces," "CENTCOM"), not personally to POTUS. The gap reflects resolution specificity, not market inefficiency.

**Bottom line:** Gaps 1 and 3 are definitional; gap 2 deserves closer arbitrage inspection.

## 4. Term Structure
# Decoding the Kalshi USA-Iran Term Structure

The Kalshi market on U.S. military action against Iran prices a fascinating term structure: 10.5% by June, 32.5% by August, 50.5% by year-end 2026, and 75.5% by January 2028. Raw cumulative probabilities obscure the real signal, so converting to forward hazard rates—the conditional probability of action in each window given no action yet—clarifies the market's view.

The Jun-Aug hazard is (0.325−0.105)/(1−0.105) = **24.6%**. The Aug-YE26 hazard is (0.505−0.325)/(1−0.325) = **26.7%**. These are remarkably stable, suggesting traders see a roughly constant ~25% conditional risk through the summer and fall of 2026—consistent with a sustained but bounded crisis posture, perhaps tied to nuclear breakout timelines or ongoing proxy escalation.

Then the structure breaks. The YE26-Jan28 hazard jumps to (0.755−0.505)/(1−0.505) = **50.5%**, nearly doubling. Conditional on nothing happening through 2026, the market assigns a coin-flip probability to action during 2027.

This kink is the interesting part. It implies traders believe deferred confrontation doesn't dissipate—it compounds. Either the underlying drivers (enrichment progress, regional dynamics, post-midterm U.S. politics) are expected to intensify, or restraint mechanisms holding through 2026 are seen as unlikely to survive another year. The term structure isn't pricing decay; it's pricing a postponed reckoning.

## 5. Trade Ideas
# 4 TRADE IDEAS — 2026-05-21

**TRADE 1: Long Kalshi USAIRAN YE26 / Short Polymarket "before 2027"** ★★★
1. Entry: Buy Kalshi YES ≤0.51, sell Polymarket YES ≥0.63 (lock 13.5pp gap, ~12pp net after fees)
2. Exit: Close when spread compresses to ≤5pp, target +7-8pp realized
3. Stop: Exit pair if spread widens past 20pp (criteria divergence confirmed structural)
4. Size: 2-3% of book, max $25K per leg, delta-neutral
5. Conviction: ★★★
6. Horizon: hold to YE26 resolution or 6 months, whichever first
7. Rationale: 13.5pp gap on similar Iran-deal questions; even if "agree to deal" (Kalshi) vs "credible reporting" (Polymarket) justifies a 4-6pp wedge, residual is mispricing. Polymarket likely overbid by retail flow ($1.37M vol).

**TRADE 2: Short Polymarket "USA-Iran deal May31" 16.5¢** ★★★
1. Entry: Sell YES at ≥0.16
2. Exit: Cover at ≤0.04 or on expiry (10 days to deadline)
3. Stop: Cover if spikes >0.28 on confirmed framework-deal headline
4. Size: 1-2% of book, max $10K notional (binary tail risk)
5. Conviction: ★★★
6. Horizon: 10 days to May 31 resolution
7. Rationale: Kalshi June equivalent at 10.5¢ with tighter 1¢ spread = sharper book. Polymarket 6pp premium on shorter deadline is structurally backwards; theta crushes YES into expiry absent headline.

**TRADE 3: Long Kalshi Pahlavi-visit YES 13.5¢** ★★
1. Entry: Buy YES ≤0.14
2. Exit: Scale out 50% at 0.22, remainder at 0.30+
3. Stop: Exit below 0.08
4. Size: 0.5-1% of book, max $5K (low-liquidity, lottery sizing)
5. Conviction: ★★
6. Horizon: 60-120 days
7. Rationale: $1.22M volume = real interest. Regime-change narrative correlates with the 50.5¢ generic Iran-deal print and 18.3¢ WTI-$180 tail — market pricing escalation optionality. Cheap convex hedge against Trade 1's deal thesis failing.

**TRADE 4: Short PredictIt Vance 2028 GOP 39¢** ★
1. Entry: Sell YES at ≥0.39
2. Exit: Cover at ≤0.28
3. Stop: Cover above 0.50
4. Size: 1% of book, max $850 (PredictIt cap)
5. Conviction: ★
6. Horizon: 6-12 months
7. Rationale: 39¢ implies near-coronation 30+ months pre-primary. Newsom at 24.9¢ on $25M Polymarket vol shows frontrunner ceilings — Vance carries Trump-admin downside correlation (note 9% Trump-Iran personal vs 50.5% generic = 41.5pp admin-execution discount).

~395 words.

## 6. Watchlist
# Iran Prediction Market Watchlist

**1) Kalshi USAIRAN YE26 (50.5)** — Trigger at 60 signals convergence with Polymarket's broader timeline. A 10-point jump indicates traders pricing in materially higher 2026 conflict/deal odds. Watch for cross-venue confirmation before acting.

**2) Polymarket before2027 (55)** — Trigger at 64 reflects repricing event, likely driven by news catalyst (negotiations, strike, sanctions shift). The 9-point move suggests structural reassessment, not noise.

**3) Kalshi USAIRAN Aug26 (45)** — Trigger at 32.5 from base implies imminent deal speculation. Near-term contracts are most sensitive to leaked diplomatic signals; watch volume spikes.

**4) Trump-Iran Jan27 (15)** — Trigger at 9 means market crediting Trump with Iran resolution. Tracks political attribution narrative; correlates with deal contracts but isolates the personality premium.

**5) Pahlavi (20)** — Trigger at 13.5 signals regime change repricing. Thinly traded but high-signal tail risk indicator; sustained moves above 20 warrant attention to internal Iran instability reporting.

## 7. Signal Quality
# Prediction Market Venue Ratings

**Kalshi** — ★★★★☆
CFTC-regulated US exchange with tight spreads (~1¢) and ~$100K volume on liquid contracts. Best for serious retail traders wanting legal, dollar-denominated exposure. Limited contract diversity outside event-of-the-week markets, but execution quality is unmatched domestically.

**Polymarket** — ★★★★★
Deepest liquidity globally: $1.37M on Iran markets, $5M on politics. Crypto-based (USDC on Polygon), blocked for US users. Unrivaled for geopolitical, election, and breaking-news contracts. Spreads widen on long-tail markets, but headline events offer institutional-grade depth.

**PredictIt** — ★★☆☆☆
Academic-exempt platform with a hard $850 position cap and directional-only trading (no shorting). Useful for small political bets and historical data, but caps, fees, and withdrawal frictions make it obsolete next to Kalshi. Legacy venue in slow decline.

**Manifold** — ★★★☆☆
Play-money ("mana") with most markets under $1K equivalent. Zero financial stakes weakens signal quality, but user-created markets cover niches no real-money venue touches. Best as a forecasting sandbox and community tool, not a price-discovery source.

