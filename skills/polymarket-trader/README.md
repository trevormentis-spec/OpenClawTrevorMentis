# Polymarket Trader Skill

Research a thesis, prepare a trade plan, and optionally execute approved Polymarket CLOB orders.

This skill is intentionally split into two stages:

1. `research.py` — public, read-only market research.
2. `trade.py` — dry-run validation by default; real execution requires explicit flags and wallet env vars.

## Install optional trading dependency

```bash
python3 -m pip install py-clob-client-v2
```

Research mode uses only the Python standard library.

## Research a thesis

```bash
python3 skills/polymarket-trader/scripts/research.py \
  --thesis "Your thesis here" \
  --out /tmp/polymarket-research.json
```

Open the JSON and inspect `candidate_markets`. Confirm the market resolution criteria and exact outcome token before editing `trade_plan.orders`.

## Dry-run a plan

```bash
python3 skills/polymarket-trader/scripts/trade.py \
  --plan /tmp/polymarket-research.json
```

Dry-run validates risk and order shape. It does not submit anything.

## Execute a plan

Only run this after manually approving the exact plan JSON.

```bash
export POLYMARKET_PRIVATE_KEY="..."
export POLYMARKET_FUNDER="0x..."              # if using a proxy/funder wallet
export POLYMARKET_SIGNATURE_TYPE="2"          # default browser/proxy wallet type

python3 skills/polymarket-trader/scripts/trade.py \
  --plan /tmp/approved-trade-plan.json \
  --execute \
  --i-understand-risk
```

Optional pre-derived CLOB credentials:

```bash
export POLYMARKET_CLOB_API_KEY="..."
export POLYMARKET_CLOB_SECRET="..."
export POLYMARKET_CLOB_PASS_PHRASE="..."
```

If they are absent, the script attempts to derive them using the official client.

## Guardrails

- No autonomous trading.
- No geoblock bypass.
- No private keys in git.
- No execution without `--execute --i-understand-risk`.
- No trade plan without `max_total_usdc`, rationale, and invalidation conditions.
