---
name: kalshi-trader
description: Full Kalshi trading system — research markets, prepare trade plans, execute orders, and autonomously monitor positions with guardrail-enforced stop-loss/take-profit. Direct REST API with RSA key auth. Autonomous monitoring runs continuously with circuit breakers. Never opens new positions autonomously: entries require explicit approval. Exits are automated within guardrail bounds.
metadata:
  trevor:
    requires:
      bins: [python3]
      packages:
        - requests
        - cryptography
      env_required:
        - KALSHI_API_KEY
        - KALSHI_RSA_KEY_PATH
      env_optional:
        - KALSHI_BASE_URL
        - KALSHI_SCANNER_API_KEY
---

# Kalshi Trader

This skill provides a full Kalshi trading client — research, market scanning, portfolio checks, and order execution — authenticated via RSA private key signing.

**It is not an autonomous trading bot.** It may research and propose; execution requires the user to approve the specific order plan.

## Safety Rules

1. **No autonomous trading.** Research, scanning, and portfolio checks are allowed. Order execution requires explicit human approval of exact ticker, side, action, count, and price/cost.
2. **No secret storage in repo.** RSA private key at `KALSHI_RSA_KEY_PATH` is gitignored (`*.pem` in `.gitignore`). API key in `.env`.
3. **No all-in behavior.** Every trade plan must include maximum risk, invalidation condition, and exit criteria.
4. **Max 200k open orders** per Kalshi account — the client warns if approaching this limit.
5. **Demo mode available** — set `KALSHI_BASE_URL=https://demo-api.kalshi.co/trade-api/v2` to test without real funds.
6. **No financial guarantee.** Output is research and execution tooling, not a promise of profit.

## Architecture

```
skills/kalshi-trader/
├── SKILL.md
├── config/
│   └── guardrails.yaml     # Risk parameters, circuit breakers, sizing rules
├── scripts/
│   ├── client.py            # Core API client (RSA signing, all endpoints)
│   ├── markets.py           # Market discovery and research
│   ├── trade.py             # Trade planning and execution
│   ├── guard.py             # Risk engine (Kelly sizing, circuit breakers, exits)
│   ├── monitor.py           # Position monitor (autonomous stop-loss/take-profit)
│   └── cron-monitor.sh      # Cron entry for continuous monitoring
└── templates/
    └── trade-plan.json      # Trade plan schema
```

Two separate API keys are supported:
- **KALSHI_API_KEY + KALSHI_RSA_KEY_PATH** — full read/write trading access
- **KALSHI_SCANNER_API_KEY** — read-only (preserved for existing `kalshi_scanner.py`)

## Environment Variables

| Variable | Purpose |
|---|---|
| `KALSHI_API_KEY` | API key UUID (RSA-authenticated, read/write) |
| `KALSHI_RSA_KEY_PATH` | Path to RSA private key PEM file |
| `KALSHI_BASE_URL` | Base URL; defaults to production `https://api.elections.kalshi.com/trade-api/v2` |
| `KALSHI_SCANNER_API_KEY` | Legacy read-only key for `kalshi_scanner.py` |

## Quick Start

### 1. Check exchange status and portfolio

```bash
python3 skills/kalshi-trader/scripts/trade.py --status
python3 skills/kalshi-trader/scripts/trade.py --balance
python3 skills/kalshi-trader/scripts/trade.py --positions
```

### 2. Discover markets

```bash
# Search for a topic
python3 skills/kalshi-trader/scripts/markets.py --search "tariff"

# Get specific market details
python3 skills/kalshi-trader/scripts/markets.py --ticker KXTARIFFRATEPRC-25JUL01

# List all markets with status filter
python3 skills/kalshi-trader/scripts/markets.py --status open --limit 50
```

### 3. Research a thesis

```bash
python3 skills/kalshi-trader/scripts/markets.py --research "Mexico tariffs will exceed 5% by July 2026"
```

### 4. Dry-run a trade

```bash
python3 skills/kalshi-trader/scripts/trade.py --dry-run --plan /tmp/kalshi-plan.json
```

### 5. Execute (requires explicit approval)

```bash
python3 skills/kalshi-trader/scripts/trade.py --execute --i-understand-risk --plan /tmp/kalshi-plan.json
```

## Trade Plan Format

```json
{
  "thesis": "One falsifiable sentence",
  "max_total_cents": 5000,
  "invalidation": "What would prove the thesis wrong",
  "exit_criteria": "Target, stop, or hold-to-resolution",
  "orders": [
    {
      "ticker": "KXTARIFFRATEPRC-25JUL01",
      "action": "buy",
      "side": "yes",
      "count": 10,
      "yes_price": 35,
      "time_in_force": "good_till_canceled",
      "rationale": "Market at 32c, thesis implies >50% probability"
    }
  ]
}
```

### Order Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `ticker` | string | yes | Market ticker |
| `action` | string | yes | `buy` or `sell` |
| `side` | string | yes | `yes` or `no` |
| `count` | int | yes | Number of contracts (1+) |
| `yes_price` / `no_price` | int | limit* | Limit price in cents (1-99) |
| `buy_max_cost` | int | market* | Max cost in cents for market buy |
| `time_in_force` | string | no | `fill_or_kill`, `good_till_canceled`, `immediate_or_cancel` |
| `client_order_id` | string | no | Your reference ID (max 64 chars) |
| `post_only` | bool | no | Only add liquidity |
| `reduce_only` | bool | no | Only reduce position |

*Use `yes_price` + `no_price` for limit orders, or `buy_max_cost` for market orders.

## Endpoints Available via client.py

| Method | Endpoint | Description |
|---|---|---|
| GET | `/exchange/status` | Exchange operational status |
| GET | `/markets` | List/filter markets |
| GET | `/markets/{ticker}` | Single market detail |
| GET | `/markets/{ticker}/orderbook` | Order book depth |
| GET | `/portfolio/balance` | Account balance |
| GET | `/portfolio/positions` | Open positions |
| GET | `/portfolio/orders` | Open orders |
| GET | `/portfolio/trades` | Trade history |
| GET | `/portfolio/settlements` | Settlement history |
| POST | `/portfolio/orders` | Create order |
| DELETE | `/portfolio/orders/{order_id}` | Cancel order |

## Execution Checklist

Before running `--execute`:

- [ ] Confirm ticker, action, side, count, and price
- [ ] Confirm max_total_cents risk limit
- [ ] Confirm invalidation and exit criteria are set
- [ ] Confirm balance is sufficient (check `--balance`)
- [ ] Run `--dry-run` first and review output
- [ ] User has explicitly approved
