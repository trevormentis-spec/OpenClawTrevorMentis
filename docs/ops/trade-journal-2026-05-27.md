# Trade Journal — 2026-05-27

## Session Context
Roderick shared his portfolio picture via Telegram. Identified Iran concentration risk (~88% of exposure). Designed and executed Daedalus strategy to add WTI hedge.

## Key Discovery
Kalshi API uses **RSA PSS request signing**, NOT JWT bearer tokens. Auth is documented in `brain/memory/procedural/kalshi-trading.md`. This was the critical gap — spent ~15 minutes trying the wrong auth before finding the client.

## Trades Executed

### HEDGE-01: WTI Scale-In
- **Instrument:** KXWTIMAX-26DEC31-T200 (WTI max $200+ by Dec 31)
- **Entry:** 31 contracts filled at $0.13 (crossing $0.125 spread)
- **New total:** 48 contracts (was 17)
- **Cost:** ~$4.03
- **Edge:** 68% desk vs 12.5% market (+55.5pt)
- **Rationale:** Negative correlation with Iran deal outcome. Portfolio diversification.

### HEDGE-02: Iran Election (Failed)
- **Instrument:** KXELECTIRAN-26JUL01
- **Intent:** 80 contracts at $0.03
- **Result:** Only 1.32 contracts filled. Market too thin (78.68 contracts total on ask at $0.03).
- **Lesson:** Don't trade sub-$100 volume markets without checking order book first.

### HEDGE-03: WTI Resting Order
- **Instrument:** KXWTIMAX-26DEC31-T200
- **Order:** 9 contracts at $0.13 (remaining from intended 40)
- **Status:** Resting on bid (order ID: 82c3ac41-b534-4233-8bfe-d9c2b6d2bd82)
- **Will fill when:** Someone hits the $0.13 bid or market moves up.

## Auth Lessons (Critical)
- **DO NOT** try JWT bearer tokens with the API key
- **DO NOT** use raw API key as Bearer token
- **DO** export KALSHI_API_KEY + KALSHI_RSA_KEY_PATH env vars
- **DO** use `skills/kalshi-trader/scripts/trade.py` or the `KalshiClient` class
- The env variables need to be explicitly exported in the shell — Python's `os.environ` doesn't load `.env` automatically
- The scanner (`kalshi_scanner.py`) works without auth because market data endpoints are public

## Post-Trade Portfolio
- Iran concentration: ~67% (down from ~88%)
- WTI hedge: ~16% (up from ~6%)
- Total equity: ~$178.90
- Cash remaining: ~$137.66

## Items to Track
- [ ] WTI resting order — check if filled next session
- [ ] Iran deal probability — monitor for probability shifts (desk at 62%)
- [ ] Portfolio rebalancing — if Iran deal probability changes, adjust sizing
