# Polymarket Geopolitics Trading Playbook

> Source: Google Doc — polymarket-trading-geopolitics
> Retrieved: 2026-05-02 via Maton API Gateway

---

## 1. Core Structure & Bankroll Rules

**Bankroll:** $1,000 starting
**Risk per thesis:** 10-15% ($100-150 notional)
**Hard cap per market:** 5% ($50)

**Market universe:**
- **Geopolitics page:** Iran peace/war, regime, Strait of Hormuz, uranium, leadership change, Xi out
- **World Events page:** elections, regime-change, "leader out before 2027," Russia-Ukraine ceasefire, Taiwan invasion, Trump foreign policy

**Liquidity filter:** 24h volume > $100k or total volume > $5M

## 2. Strategy A — Iran Term-Structure & Complex

**Core idea:** Near-term optimistic outcomes (peace, regime fall, normalization) tend to be overpriced as deadlines approach without clear progress.

**Rules:**
- Check: days to expiry, current probability, major breakthrough status
- If ≤30d, priced >15%, no imminent resolution → short Yes (buy No)
- Size: 2-3% per trade ($20-30), up to 10-15% thesis cap
- Laddered hedges: short near-term, long longer-dated
- Exit: take 50-75% profit at half the expected move; flatten on genuine breakthrough

## 3. Strategy B — Leader-Out vs Elections

**Term-structure spreads:** If long-dated minus short-dated > 25pp and no near-term event → short near-term "out"
**Cross-country dispersion:** Multi-name "leader out" markets → small speculative bets on mispricings

## 4. Strategy C — Geo-Macro Signal Usage

**Jump detector:** >10 point move in 2h on markets with ≥$10M volume → scan related markets for lag
**Event trades:** 2-3% per trade, held hours to days

## 5. Automation Rules (15-30 min cycle)

1. Data pull: all Geopolitics + World Events geo markets
2. Time-decay screen: ≤30d, >15%, no progress → short candidate
3. Term-structure anomalies: long-short > 25pp
4. Jump detector: >10 point move in 2h on ≥$10M vol markets
5. Alert format: concise message with specific triggers
6. Auto thresholds: pre-defined open/close with manual override
