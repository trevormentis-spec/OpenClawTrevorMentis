# Kalshi Trading Operations

## Authentication

Kalshi uses **RSA PSS request signing**, NOT JWT bearer tokens.

**Required credentials (in `.env`):**
- `KALSHI_API_KEY` — API key UUID (e.g., `4748f0c0-...0a05`)
- `KALSHI_RSA_KEY_PATH` — path to RSA private key PEM (`.kalshi_rsa_key.pem`)
- `KALSHI_BASE_URL` — `https://api.elections.kalshi.com`

**Auth mechanism (per request):**
1. Timestamp (ms) + HTTP method + path (without query params) → message string
2. Sign message with RSA-PSS-SHA256 using the private key
3. Base64-encode signature
4. Send in headers: `KALSHI-ACCESS-KEY`, `KALSHI-ACCESS-TIMESTAMP`, `KALSHI-ACCESS-SIGNATURE`

## Client Library

The client lives at: `skills/kalshi-trader/scripts/client.py`
Class: `KalshiClient` — auto-loads env vars, handles auth, provides methods.

Key methods:
- `get_balance()` — cash balance + portfolio value
- `get_positions()` — event-level and market-level positions
- `get_orders(ticker=, status=)` — open orders
- `create_order(ticker, side, action, count, yes_price=, ...)` — place order
- `get_market(ticker)` — single market detail
- `get_markets(series_ticker=)` — list markets
- `get_orderbook(ticker)` — order book depth
- `cancel_order(order_id)` / `cancel_all_orders(ticker=)`

## Trade Execution Script

Script: `skills/kalshi-trader/scripts/trade.py`

Quick queries (export env vars first):
```bash
export KALSHI_API_KEY=$(grep KALSHI_API_KEY .env | cut -d= -f2)
export KALSHI_RSA_KEY_PATH=$(grep KALSHI_RSA_KEY_PATH .env | cut -d= -f2)

python3 skills/kalshi-trader/scripts/trade.py --balance
python3 skills/kalshi-trader/scripts/trade.py --positions
python3 skills/kalshi-trader/scripts/trade.py --orders
```

Trade plan execution (requires JSON plan file):
```bash
python3 skills/kalshi-trader/scripts/trade.py --dry-run --plan plan.json
python3 skills/kalshi-trader/scripts/trade.py --execute --i-understand-risk --plan plan.json
```

## Market Scanner

Script: `scripts/kalshi_scanner.py`
```bash
python3 scripts/kalshi_scanner.py              # full scan
python3 scripts/kalshi_scanner.py --save       # save to exports/
```

Scans 60+ geopolitics series across Iran, Russia-Ukraine, oil/energy, China/Taiwan, etc.
Output: `exports/kalshi-scan-YYYY-MM-DD.md`

## Risk Guardrails

From TOOLS.md / AGENTS.md / guardrails:
- Quarter-Kelly sizing
- 5% max per position (of total equity)
- 30% max total exposure
- -10% daily loss cap
- -20% max drawdown halt
- Minimum 5pt edge requirement

## Daedalus Strategy (Active — 2026-05-27)

**Thesis:** WTI oil at $200+ provides negative correlation hedge against Iran deal concentration (68% desk vs 12.5% market, +55.5pt edge).

**Positions executed:**
- KXWTIMAX-26DEC31-T200: 48 contracts (was 17, added 31 at $0.13 crossing spread)
- KXELECTIRAN-26JUL01: 1.32 contracts (market too thin, most didn't fill)
- KXUSAIRANAGREEMENT-27-26JUN: 228 contracts @ ~$0.086
- KXUSAIRANAGREEMENT-27-26JUL: 67 contracts @ ~$0.26
- KXUSAIRANAGREEMENT-27-26AUG: 25 contracts @ ~$0.35
- KXTRUMPIRAN-26JUN01: 100 contracts @ ~$0.003 (dead/resolved)
- KXTRUMPIRAN-27JAN01: 12 contracts @ ~$0.09

**Open orders:**
- 9 contracts KXWTIMAX-26DEC31-T200 @ $0.13 (resting bid, order ID: 82c3ac41-b534-4233-8bfe-d9c2b6d2bd82)

**Post-trade (2026-05-27 ~04:15 UTC):**
- Cash: ~$137.66, Portfolio: ~$41.24, Total equity: ~$178.90
