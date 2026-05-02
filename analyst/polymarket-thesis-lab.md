# Polymarket Specificity-Short Thesis Lab

> Ongoing research log for the specificity-short trading thesis.
> Updated by scanner outputs, price monitor alerts, and manual analysis.

---

## Thesis Statement

**Prediction markets overprice vivid affirmative events.**
The edge is to buy No when Yes is narratively exciting but operationally fragile.

---

## Current Hypothesis Set

### H1: Exact Phrase > Official Announcement > Tech Release > Multi-Condition > Narrow Count Band
*Predicted rank of category performance based on operational fragility.*

### H2: Sweet spot is No @ 35¢-60¢
*Narrower than original 25¢-75¢. Extreme ends misprice differently.*

### H3: 7-21 day resolution outperforms 1-7 day and 22-60 day
*Very short markets have unpredictable news shocks; very long markets decay theta too slowly.*

### H4: Multi-condition markets are the strongest category
*Yes requiring everything to align makes No statistically dominant.*

---

## Category Performance Tracker

| Category | Trades | Wins | Losses | Win Rate | Avg Edge | Notes |
|---|---|---|---|---|---|---|
| Exact Phrase | — | — | — | — | — | Hardest to find in wild |
| Official Announcement | — | — | — | — | — | Bureaucracy delays common |
| Tech Release | — | — | — | — | — | Hype cycles predictable |
| Narrow Count Band | — | — | — | — | — | |
| Multi-Condition | — | — | — | — | — | |

---

## Candidate Watchlist

*Automatically populated by short_thesis_scanner.py runs.*

| Date | Slug | No @ | Days | Edge Est | Cat | Status |
|---|---|---|---|---|---|---|
| 2026-05-02 | no-one-announced-as-next-james-bond | .75 | 58 | | OA | Pending |
| 2026-05-02 | will-openai-not-ipo-by-december-31-2026 | .74 | 58 | | TR | Pending |
| 2026-05-02 | will-ken-paxton-win-the-2026-republican-primary | .57 | 23 | | OA | Pending |
| 2026-05-02 | will-freddie-macs-market-cap-be-between-150b-and-200b | .55 | 58 | | NCB | Pending |
| 2026-05-02 | will-arsenal-win-the-202526-english-premier-league | .51 | 24 | | MC | Pending |

---

## Thesis Research Plan

### Phase 1: Historical Analysis (first 30 days)
- Track every scanner recommendation and its outcome
- Record what moved prices (news shocks, resolution events, whale activity)
- Identify false positives (markets that should have been No but went Yes)
- Refine category keywords and scoring weights

### Phase 2: Category Deep Dive
For each of the 5 categories:
- Collect 20 past resolved markets matching the category
- Analyze pricing trajectory (did No drift up or down as resolution approached?)
- Identify the specific conditions that led to Yes/No outcomes
- Publish a per-category mini-thesis with updated edge estimates

### Phase 3: Entry & Exit Optimization
- Track limit order fill rates by spread tier
- Analyze optimal exit timing (hold to resolution vs take profit at XX¢)
- Backtest: "what if we entered every market with score >X and exited at Y?"

### Phase 4: Moltbook Intelligence Loop
- Monitor Unity, celerybot-local, claw_1771997882 for new Polymarket insights
- Track m/trading and m/agentfinance for strategy discussions
- Incorporate external signal into thesis refinement

---

## Research Log

### 2026-05-02 — Roderick's Picks & 95c+ Warning

**Initial basket (3 live positions):**
1. **Hormuz blockade lifted by May 31, No @ 59.5c** — Best balance: price/liquidity/thesis-fit
2. **GPT-5.6 released by May 31, No @ 68c** — Pure tech release date (smaller size due to liquidity)
3. **Hormuz blockade lifted by May 22, No @ 75.5c** — Nearer-term variant (correlated with #1)

**The 95-99c No market trap (Key Thesis Refinement #1):**
Roderick: "They may win often, but the upside is too small relative to the occasional surprise loss."

Structural math: At No = 97c, max gain is 3c/unit but loss can be 97c. One surprise Yes wipes out ~32 winning trades.

**Updated entry rule:** Cap No entry price at 85c. Prefer 25c-75c. Accept 75c-85c only with tight spreads and <14d duration. Never above 85c.

**Updated tracked file** with 3 priority markets + 39 auto-scanned candidates.

---

### 2026-05-02 — Initial Setup
- Scanner built and running (1,500 markets / 6h)
- 39 tracked markets with baseline prices
- 2 crons active (3h price monitor, 6h scanner)
- Moltbook Polymarket agents followed: Unity, celerybot-local, claw_1771997882, vector_flo_sabaudia
- Submolts subscribed: m/agentfinance, m/trading

**Initial category distribution from scan:**
- Official Announcement: 38 markets
- Multi-Condition: 32 markets
- Narrow Count Band: 31 markets
- Tech Release: 28 markets
- Exact Phrase: 4 markets (rarest category)

**Observation:** Exact phrase markets are very rare. May need to expand indicator set or accept that most available trades are Official Announcement / Multi-Condition.

### External Intel: Unity's Polymarket Bot (Coastal Crypto)

**Source:** Moltbook — Unity (Coastal Crypto)
**7-signal engine:** momentum, RSI, volume, Fear & Greed, range position, exchange divergence, trend alignment
**Architecture:** Worker pattern > orchestrator (latency kills profitability on fast markets)
**Signal conflict resolution:** Prioritize faster data; accept partial signal set over waiting for complete picture
**Estimated cron latency cost:** ~0.3%/day in missed Polymarket opportunities

**Implication for our thesis:** The specificity-short thesis is inherently *slow* — it doesn't need 40ms signal processing. Our edge comes from structural analysis, not speed. This is an advantage: we compete on thesis quality, not execution latency. Event-driven monitoring (our 3h price monitor) is sufficient for our timeframes.

---

### Historical Validation Attempt
- Scanned 150 resolved markets via Gamma API — mostly 2020-2021 vintage
- Thesis pattern holds in historical data:
  - "Will Kim/Kanye divorce?" → resolved No ✅
  - "Will Coinbase begin trading before date?" → resolved No ✅ (tech release thesis)
  - "Will Biden get COVID?" → resolved No ✅ (exact event thesis)
- Recent (2025-2026) resolved markets not yet available for analysis
- **Action:** Monitor for resolution events on tracked markets; log outcomes systematically

---

### Open Questions
1. Do official announcement markets predictably drift No-ward until the deadline?
2. Is there a theta decay pattern we can model for specificity-short?
3. Are weekend vs weekday resolution patterns different?
4. Do whale wallets (large holders) systematically trade against this thesis?
5. Does the 5-minute resolution problem (from celerybot-local) apply to non-sports specificity markets?
6. How long after resolution do markets actually settle? (slippage risk)
