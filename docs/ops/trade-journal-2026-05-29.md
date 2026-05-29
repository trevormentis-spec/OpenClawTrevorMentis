# Trade Journal — 2026-05-29

## Cron: Kalshi Trader Signal Scan + Execute

**Time:** 06:03 UTC
**Balance:** $0.24
**Result:** 0/10 trades executed — insufficient balance

## Signals Identified (top 10 by edge)

1. **KXTRUMPIRAN-26JUN01** — BUY Yes @ 1¢ (63% vs 0%, +63pt edge)
2. **KXUSAIRANAGREEMENT-27-26JUN** — BUY Yes @ 5¢ (61.5% vs 5.5%, +56pt edge)
3. **KXTRUMPIRAN-27JAN01** — BUY Yes @ 8¢ (63% vs 8%, +55pt edge)
4. **KXTARIFFRATEPRC-26JUL01-55** — BUY Yes @ 3¢ (50% vs 3.5%, +46pt edge)
5. **KXTARIFFRATEPRC-26JUL01-55** — BUY Yes @ 5¢ (50% vs 5.5%, +44pt edge)
6. **KXUSAIRANAGREEMENT-27-26JUL** — BUY Yes @ 17¢ (61.5% vs 17.5%, +44pt edge)
7. **KXUKRAINEEU-27JAN01** — BUY Yes @ 31¢ (72% vs 31%, +41pt edge)
8. **KXWTIMAX-26DEC31-T200** — BUY Yes @ 12¢ (50% vs 12%, +38pt edge)
9. **KXWTIMAX-26DEC31-T200** — BUY Yes @ 15¢ (50% vs 15%, +35pt edge)
10. **KXWTIMAX-26DEC31-T200** — BUY Yes @ 17¢ (50% vs 17.5%, +32pt edge)

## Notes

- All trades blocked by `insufficient_balance` — account needs at minimum $10+ to deploy across multiple signals
- Highest edge: Trump/Iran contracts (market near 0%, Trevor at 63%)
- Duplicate KXTARIFFRATEPRC signals: same market resolved to slightly different prices (3.5¢ and 5.5¢), likely spread from different order book levels
- Duplicate KXWTIMAX signals: same market across 12¢, 15¢, 17¢ prices — likely multiple edge thresholds in scanner logic
