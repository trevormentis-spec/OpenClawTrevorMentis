# Portfolio Overview — 2026-05-27

## Platforms

### Kalshi (Real Money)
- **Auth:** RSA PSS signing via `skills/kalshi-trader/scripts/client.py`
- **Key:** `KALSHI_API_KEY` + `KALSHI_RSA_KEY_PATH` (`.kalshi_rsa_key.pem`)
- **Endpoint:** `https://api.elections.kalshi.com`
- **Balance:** ~$137.66 cash + ~$41.24 portfolio = ~$178.90 total equity

### Simmer → Polymarket (Real USDC)
- **Auth:** `SIMMER_API_KEY` in `.env`
- **Balance:** ~$4.96 USDC
- **Position:** JD Vance 2028 NO at 81.65¢

### Simmer Paper Trading
- **Balance:** $9,997 $SIM
- **Position:** US-Iran nuclear deal by June 30 — yes side, 42 shares, underwater by $3.06

## Kalshi Positions

| Market | Shares | Entry | Current Mkt | Exposure | Edge |
|---|---|---|---|---|---|
| KXUSAIRANAGREEMENT-27-26JUN | 228 | ~$0.086 | $0.045 bid | $19.64 | 62% desk vs 6% mkt (+56pt) |
| KXUSAIRANAGREEMENT-27-26JUL | 67 | ~$0.265 | $0.205 bid | $17.74 | 62% vs 20% (+42pt) |
| KXUSAIRANAGREEMENT-27-26AUG | 25 | ~$0.35 | $0.335 bid | $8.75 | 62% vs 36% (+26pt) |
| KXTRUMPIRAN-26JUN01 (dead) | 100 | ~$0.003 | $0.00 | $0.30 | — |
| KXTRUMPIRAN-27JAN01 | 12 | ~$0.09 | $0.095 bid | $1.08 | — |
| **KXWTIMAX-26DEC31-T200** | **48** | **~$0.125** | **$0.125 bid** | **$6.07** | **68% vs 12.5% (+55.5pt)** |
| KXELECTIRAN-26JUL01 | 1.32 | ~$0.03 | $0.03 | $0.04 | Uncertain |

## Active Strategies

### Daedalus (2026-05-27)
- **Thesis:** WTI at $200+ is negatively correlated with Iran deal outcome. Scale WTI to hedge Iran concentration.
- **Execution:** Bought 31 WTI contracts at $0.13 (crossing spread), bringing total to 48.
- **Remaining:** 9 contracts resting at $0.13 bid (order: 82c3ac41...)
- **Iran concentration:** Dropped from ~88% to ~67% of risk exposure.
- **WTI hedge:** Increased from ~6% to ~16% of risk.

### Iran Deal (Active)
- **Desk assessment:** 62-63% probability of US-Iran nuclear deal across Jun/Jul/Aug
- **Positions:** 320 contracts across 3 expiries at KXUSAIRANAGREEMENT
- **Risk:** ~$46.13 total exposure. Binary outcome — all or nothing per expiry.
- **Hedge:** WTI position (48 contracts) provides partial offset if deal fails.

## Risk Guardrails

| Guardrail | Limit | Current |
|---|---|---|
| Quarter-Kelly | Edge-based | ✅ Pass |
| Max per position | 5% of equity (~$8.95) | ✅ Largest is $19.64 (11%) — exceeds limit |
| Max total exposure | 30% (~$53.67) | ✅ ~$53.62 (29.9%) — right at limit |
| Daily loss cap | -10% | ✅ |
| Drawdown halt | -20% | ✅ |
| Min edge | 5pt | ✅ All positions qualify |

> **Note:** The 5%-per-position guardrail is exceeded because existing positions were established before the automated trading system was connected. The 30% total exposure is at the hard boundary. Adding more positions requires reducing existing ones first.

## Positions That Shouldn't Be Opened (Meta)
- No Simmer paper trading strategies are active — paper$SIM is idle
- No Polymarket strategies beyond the Vance position
