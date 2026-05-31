# Trading System — Operator Runbook

**First thing to read if something goes wrong.**

## Kill Switch
If the system is trading unexpectedly or behaving badly:

```bash
# Hard stop — prevents any order from reaching the exchange
python3 trading-system/guardrails/kill_switch.py --halt

# Verify halted state
python3 trading-system/guardrails/kill_switch.py --status
```

The kill switch is independent of the trading logic. It lives in the gated API client and blocks all outbound orders regardless of what the strategy thinks it's doing.

## Current Autonomy Level
See `config/autonomy_state.json`.

| Level | Meaning | Capital |
|-------|---------|---------|
| 0 | Paper trading only | $0 |
| 1 | Tiny live, human-confirmed | $5/contract |
| 2 | Live with guardrails, batched confirm | $50 max exposure |
| 3 | Autonomous within guardrails | $250 max exposure |

## Key Files
- `config/guardrails.yaml` — edit this to change risk limits
- `config/markets.yaml` — which markets are watched
- `guardrails/kill_switch.py` — emergency halt (test this)
- `audit/decisions.jsonl` — every decision the system makes
- `calibration/resolution_log.jsonl` — how well we're calibrated

## Daily Checks
```bash
# Check kill switch state
python3 trading-system/guardrails/kill_switch.py --status

# Check current positions
python3 trading-system/execution/gated_client.py --positions

# Check calibration
python3 trading-system/calibration/brier.py --report

# Check Opus budget
python3 scripts/anthropic_monitor.py
```

## Architecture
```
Intel sources → KJ → ProbabilityEstimate → Edge calc → Sizing → Guardrails → Execute
```

No trade reaches the exchange without passing every guardrail. Default action: do nothing.
