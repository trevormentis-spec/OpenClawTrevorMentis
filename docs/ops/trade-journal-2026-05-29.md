# Trade Journal — 2026-05-29

**Cycle:** Cron signal scan + execute (01:00 UTC)
**Scanner:** `philby/trader/trader.py --scan-and-trade`
**Account balance:** $2.26
**Existing positions before run:** 0

---

## Scan Results

- **22 tradeable signals** from intel bridge
- All signals are Iran/Iran-agreement themed (Trump/Iran contracts dominate)

## Trades Attempted

### 1. KXTRUMPIRAN-26JUN01 — BUY Yes
- **Trevor confidence:** 63% | **Market:** 0% | **Edge:** +63pts
- **Kelly fraction:** 0.07 → **$1.00** (100 × 1¢)
- **Order lifecycle:** 1¢ → 3¢ → 5¢ → 7¢ escalation
- **Outcome:** Order placed but fill not confirmed after 3 escalation attempts (logged as placed)

### 2. KXUSAIRANAGREEMENT-27-26JUN — BUY Yes
- **Trevor confidence:** 61.5% | **Market:** 5.5% | **Edge:** +56pts
- **Kelly fraction:** 0.15 → **$1.00** (20 × 5¢)
- **Outcome:** ❌ Failed — insufficient_balance (cash tied up in pending order #1)

### 3. KXTRUMPIRAN-27JAN01 — BUY Yes
- **Trevor confidence:** 63% | **Market:** 8% | **Edge:** +55pts
- **Kelly fraction:** 0.15 → **$1.00** (12 × 8¢)
- **Order lifecycle:** 8¢ → 10¢ → 12¢ escalation
- **Outcome:** Order placed but fill checks failing with insufficient_balance errors

---

## Issues

1. **Low account balance ($2.26)** — insufficient funds to trade multiple signals simultaneously. First order of $1.00 (implied cash hold) blocks subsequent trades.
2. **Pending order cash lockup** — Kalshi holds the $1.00 commitment for order #1, leaving only ~$1.26 available. This blocks trades 2 and 3.
3. **No fills confirmed** — market at 0¢ for KXTRUMPIRAN-26JUN01 suggests no liquidity at any level; the order may never fill until the market develops.

## Notes

- All signals today center on Iran-related contracts (Trump/Iran, US-Iran agreement), indicating the intel bridge sees elevated Iran geopolitical signals.
- The Iran cluster makes sense for a $2 balance — these are cheap contracts with long-tailed upside.
- Consider a `--dry-run` cadence for low-balance periods to avoid burning API rate limits on unfillable orders.
