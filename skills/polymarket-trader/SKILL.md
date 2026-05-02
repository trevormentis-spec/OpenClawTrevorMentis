---
name: polymarket-trader
description: Research Polymarket markets for a user-supplied thesis, prepare a disciplined trade plan, and optionally execute human-confirmed orders through a wallet-backed Polymarket CLOB client. Trigger on "polymarket", "prediction market trade", "trade this thesis", "market odds", "price this thesis", "make a Polymarket plan", or "execute Polymarket order". Never trade autonomously: execution requires explicit user approval plus script flags. Do not bypass geoblocking, KYC, sanctions, platform rules, or local law.
metadata:
  trevor:
    requires:
      bins: [python3]
      env_optional:
        - POLYMARKET_PRIVATE_KEY
        - POLYMARKET_FUNDER
        - POLYMARKET_SIGNATURE_TYPE
        - POLYMARKET_CLOB_API_KEY
        - POLYMARKET_CLOB_SECRET
        - POLYMARKET_CLOB_PASS_PHRASE
    packages_optional:
      - py-clob-client-v2
---

# Polymarket Trader

This skill turns a thesis into a research packet, a trade plan, and — only after explicit confirmation — Polymarket CLOB orders.

It is **not** an autonomous trading bot. It must not trade just because a thesis exists. It may research and propose; execution requires the user to approve the specific order plan and then run `trade.py` with both `--execute` and `--i-understand-risk`.

## Safety and compliance rules

1. **No autonomous trading.** Research and planning are allowed. Order execution requires explicit human approval of exact market, side, token, price/amount/size, and maximum risk.
2. **No geoblock bypass.** Before execution, run Polymarket's geoblock check. If blocked, stop. Do not suggest VPNs or location workarounds.
3. **No secret storage in repo.** Private keys and API credentials stay in environment variables or local secret managers only.
4. **No all-in behavior.** Plans must include a maximum total USDC risk, per-order limits, liquidity notes, and a thesis invalidation condition.
5. **No unsupported jurisdictions or accounts.** User is responsible for platform eligibility, KYC, tax, and local-law compliance.
6. **No financial guarantee.** Output is research and execution tooling, not a promise of profit.

## Operating modes

### 1. Research a thesis

```bash
python3 skills/polymarket-trader/scripts/research.py \
  --thesis "Example: candidate X is undervalued in market Y" \
  --out /tmp/polymarket-research.json
```

The research script searches public Polymarket market data endpoints and writes a JSON packet with candidate markets, liquidity/pricing fields when available, and a blank trade-plan scaffold.

### 2. Create a trade plan

Edit the research output or copy `templates/trade-plan.example.json`. A valid plan must include:

- `thesis`
- `max_total_usdc`
- `orders[]`
  - `token_id`
  - `side`: `BUY` or `SELL`
  - `order_type`: `GTC`, `FOK`, or `FAK`
  - either `price` + `size` for limit orders, or `amount` for market orders
  - `rationale`
  - `invalidation`

### 3. Dry-run the trade

```bash
python3 skills/polymarket-trader/scripts/trade.py \
  --plan /tmp/polymarket-research.json
```

Dry-run is the default. It validates risk limits and prints what would be sent.

### 4. Execute only after explicit approval

```bash
export POLYMARKET_PRIVATE_KEY="..."
export POLYMARKET_FUNDER="0x..."              # proxy/funder wallet if applicable
export POLYMARKET_SIGNATURE_TYPE="2"          # 0 EOA, 1 Magic/proxy, 2 browser/proxy

python3 skills/polymarket-trader/scripts/trade.py \
  --plan /tmp/approved-trade-plan.json \
  --execute \
  --i-understand-risk
```

If `POLYMARKET_CLOB_API_KEY`, `POLYMARKET_CLOB_SECRET`, and `POLYMARKET_CLOB_PASS_PHRASE` are present, they are used. Otherwise the script derives CLOB API credentials from the private key via the official client.

## Environment variables

| Variable | Purpose |
|---|---|
| `POLYMARKET_PRIVATE_KEY` | Wallet private key used by the SDK for L1 signing and order signing. Required for execution. |
| `POLYMARKET_FUNDER` | Funder/proxy wallet address. Required for proxy-wallet accounts. |
| `POLYMARKET_SIGNATURE_TYPE` | `0` EOA, `1` Magic/proxy, `2` browser/proxy/Gnosis-style account. Default: `2`. |
| `POLYMARKET_CLOB_API_KEY` | Optional pre-derived L2 API key. |
| `POLYMARKET_CLOB_SECRET` | Optional pre-derived L2 API secret. |
| `POLYMARKET_CLOB_PASS_PHRASE` | Optional pre-derived L2 passphrase. |
| `POLYMARKET_CLOB_HOST` | Defaults to `https://clob.polymarket.com`. |
| `POLYMARKET_GAMMA_HOST` | Defaults to `https://gamma-api.polymarket.com`. |

## Files

```text
skills/polymarket-trader/
├── SKILL.md
├── README.md
├── scripts/
│   ├── research.py
│   └── trade.py
└── templates/
    └── trade-plan.example.json
```

## Research checklist

Before proposing any trade, write down:

- The thesis in one falsifiable sentence.
- Candidate markets and exact resolution criteria.
- Current midpoint / best bid / best ask when available.
- Liquidity, spread, and slippage risks.
- Why the market price might be wrong.
- What would invalidate the trade.
- Maximum risk in USDC and maximum acceptable price.
- Exit plan: target, stop, expiration, or resolution hold.

## Execution checklist

Before running `--execute`:

- Confirm the selected outcome token ID.
- Confirm order type, side, size/amount, and limit price.
- Confirm geoblock returns unblocked.
- Confirm wallet has funds/allowances.
- Confirm the user approved the exact JSON plan.
