# Polymarket Geopolitics Trading Playbook

> Source: Google Doc — polymarket-trading-geopolitics (updated)
> Retrieved: 2026-05-02

---

## 1. Core Structure & Bankroll Rules

**Bankroll:** $1,000
**Hard limits:**
- Max gross exposure: 60% ($600)
- Min cash reserve: 40% ($400)
- Per single market: 5% ($50)
- Per country/theme complex: 15% ($150)
- Event-driven window (12h): 20% ($200)
- Max loss per day: 8% ($80) — stop opening if hit
- Max drawdown from peak: 20% — halve sizes until >90% recovery

**Market universe:** Geopolitics + World Events pages
**Liquidity filter:** 24h vol >$200k OR lifetime vol >$5M
**Spread:** ≤4¢ for MM, ≤7¢ for directional
**Skip:** <3% or >97% contracts, <$50k liq, novelty, ambiguous rules

**Default sizing:**
- Core spread/term-structure: $20-35/leg
- Event-driven lag: $15-25
- Market-making: $10-20/side
- Long-horizon punt: $10-15

## 2. Module A — Iran Term-Structure Decay

**Screen (every 15 min):** days_to_expiry ≤35, price ≥12%, no confirmed breakthrough in 24h, 24h vol ≥$150k
**Entry:** Buy No at 2.5% of bankroll. If later-dated equivalent exists with higher prob, hedge 40-60% in later leg.
**Exit:** Take profit 50% at -30% rel, exit remaining at -50% rel or 5d to expiry. Stop if +10pts + breakthrough tag.

## 3. Module B — Leader-Out Term Structure

**Screen:** Same leader, far prob − near prob ≥25pp, combined vol ≥$10M, no near catalyst
**Entry:** Short near-date Yes $25-35. Optional: long far-date Yes 40-50% of near size.
**Exit:** Take profit at -40% rel, exit all near at 7d to expiry. Stop if near price doubles + catalyst.

## 4. Module C — Shock-Lag Event Trades

**Screen (every 5 min):** Core market vol ≥$10M, abs 2h change ≥10pp, 24h vol ≥$250k. Scan linked markets for underreaction.
**Entry:** Trade laggard $15-25. Max 3 simultaneous. Hold 2h-3d.
**Exit:** Take profit when lag closes 50%. Exit at 72h. Stop if leader reverses 70%.

**Core market list:** US invades Iran, US-Iran peace, Iran regime fall, China invades Taiwan, Russia-Ukraine ceasefire, Netanyahu out

## 5. Market-Making Module

**Eligible:** Lifetime vol ≥$20M, daily vol ≥$250k, displayed liq ≥$250k, price 8-92%
**Quote:** Both sides if spread ≥3¢. Place 1¢ inside. If inventory long, stop bids/shade asks. Max inventory $20 notional.
**Kill switches:** Cancel all if: news shock fires, spread >8¢, gap 7pts in 10min, rules ambiguity, daily loss >$50.

## 6. News Framework

- **Tier 1 (confirmed):** Gov statements, signed agreements, official announcements, 2+ top-tier outlets → auto-trade OK
- **Tier 2 (credible):** One high-quality outlet, named diplomats, unconfirmed OSINT → alert only, no auto-entry >$15
- **Tier 3 (rumor):** Social posts, unsourced claims → half-size MM only, no directional

## 7. Data Schema (per market)

market_id, title, theme, subtype, current_yes/no_price, best_bid/ask, spread, volume_24h/lifetime, liquidity, days_to_expiry, linked_market_ids, news_score/tier, price_change_10m/2h/24h, open_position_size/avg_price, unrealized_pnl

## 8. Logging

Every action: timestamp UTC, module, market, side, size, reason code, linked trade id, theme/gross exposure, daily PnL

## 9. Daily Review (00:05 UTC)

Starting equity, ending equity, return, open positions by theme, realized/unrealized PnL, best/worst trades, kill switch count, skipped markets + reasons.

## 10. Week 1 Deployment

- Auto-trade: Module A + MM only
- Module B & C: alert + manual approval for first 20 signals
- Reduce all sizes by 20%
- Review after 50 trades

## Current Watchlist

**Priority 1:** US-Iran peace Jun30 (39%), Strait normal May31 (21%)/Jun30 (46%), Regime fall Jun30 (7%), US invades Iran 2027 (31%), Iran leadership change Dec31 (34%)
**Priority 2:** Netanyahu out Jun30 (6%)/Dec31 (44%), Xi out 2027 (8-9%), China invades Taiwan 2026 (7%), Russia-Ukraine ceasefire May31 (7%)/Jun30 (10%)

## Operating Principle

"Exploit three repeatable sources of edge: short-dated overpricing of positive resolution, inconsistent term structure across related markets, and lagged repricing after major shocks."
