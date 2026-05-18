# Synthetic Hedge Construction — Open Claw Mexico

**Use case:** A brief requires a subscriber action line with a
prediction-market or hedge recommendation, but no direct instrument
exists for the specific risk (e.g., "cartel violence in Guanajuato
industrial parks," "USMCA tariff on Bajío auto exports").

**Principle:** Never invent contract names or prices. Construct
synthetic exposure using ONLY named, verifiable real instruments.
If no instrument covers the risk, say so — don't fabricate one.

---

## When to Use Synthetic Hedges

Use this template when:
1. A subscriber asks for a downside hedge recommendation (Section 3
   of subscriber-facing briefs)
2. The direct instrument does not exist (confirmed by running the
   Kalshi scanner and Polymarket check)
3. A real proxy instrument can be justified with explicit logic

---

## Available Real Instruments

### Mexico-Specific Instruments

| Instrument | Type | Exposure | Liquidity |
|------------|------|----------|-----------|
| EWW | MSCI Mexico ETF | Broad MX equity | High |
| MXF | Mexico Closed-End Fund | MX equity + bonds | Medium |
| USDMXN | FX spot/forward | Peso direction | Very high |
| MXN 1M Forward | FX forward | 30-day peso exposure | High |
| Mexico CDS (5Y) | Credit default swap | Sovereign credit risk | Medium |
| PEMEX bonds | Corporate debt | Energy sector | Medium |
| CEMEX CPO | Equity | Construction materials | Medium |

### Proxy EM Instruments (for broad exposure)

| Instrument | Type | Proxy Use Case | Liquidity |
|------------|------|---------------|-----------|
| IEMG | iShares Core MSCI EM ETF | EM beta hedge | High |
| EMB | iShares JPM USD EM Bond ETF | EM credit hedge | High |
| VWO | Vanguard FTSE EM ETF | EM equity hedge | Very high |

### Commodity Instruments (for energy/input hedges)

| Instrument | Type | Exposure | Liquidity |
|------------|------|----------|-----------|
| USO | US Oil Fund | WTI crude | High |
| BNO | Brent Oil Fund | Brent crude | Medium |

---

## Synthetic Hedge Construction Pattern

### Step 1: State the gap explicitly

> GAP: No direct [Kalshi/Polymarket] contract exists
> for "[specific risk]". Per [tool name] scanner run at
> [timestamp], [X] contracts found — none matching this
> exposure.

### Step 2: Identify the closest proxy

Select from the Available Real Instruments table above.
Justify the proxy logic explicitly:

> Closest proxy: [Instrument] [price/level] — because
> [reason]. E.g.: "Because Bajío industrial disruption
> would manifest first in wider Mexico CDS spreads,
> lower EWW prices, and peso depreciation."

### Step 3: State current observable data

If you have scanner output or market data from a tool run:

> Per [scanner name] at [timestamp]:
> - [Instrument 1]: [current price/level]
> - [Instrument 2]: [current price/level]

If you did NOT run a scanner or fetch prices, say so:

> We did not re-fetch current prices for this brief.
> [Instrument] typically trades in the [range] range.
> Verify before executing.

### Step 4: Propose sizing with methodology

> Proposed hedge: [N]% of [exposure] via [instrument(s)].
> Rationale: [methodology — e.g., "volatility-sized to
> cover a 2-standard-deviation move in the exposure" or
> "premium-cost-sized to stay under 1.5% of portfolio cost"]

Acceptable sizing methodologies (choose one, name it):
- **VaR-budget-sized:** Hedge sized to cover the 95% VaR of the
  identified risk over the 12-month horizon
- **Volatility-sized:** Hedge sized to offset a 2-standard-deviation
  move in the proxy instrument
- **Premium-cost-sized:** Hedge sized to a fixed percentage of
  portfolio value (1-2%) — only when better data is unavailable
- **Scenario-sized:** Hedge sized to cover the identified downside
  scenario's estimated P&L impact

### Step 5: Flag the gap

> **Flag:** This is a proxy hedge, not a perfect match.
> The gap is real. [Describe what's not covered.] Monitor
> [specific indicators] for when a closer instrument becomes
> available.

---

## Anti-Patterns (Hard Violations)

| Anti-pattern | Why it's wrong | Better alternative |
|-------------|----------------|-------------------|
| Inventing a contract name on Kalshi/Polymarket | Fabrication — trust violation | Say "no contract exists," propose synthetic construction with real instruments |
| Inventing a price "last traded at $X" | Fabrication — trust violation | Say "we did not re-fetch current prices" |
| Using a feel-right hedge ratio without methodology | Unprofessional — subscriber can't verify | Name the sizing methodology (VaR, volatility, premium-cost) |
| Claiming scanner output exists when it doesn't | Fabrication — trust violation | Only reference tool output that was actually generated this session |
| Naming a ticker that doesn't exist | Fabrication — trust violation | Verify ticker against KNOWN_TICKERS list in fabrication_check.py |

---

## Verification Process

Before any brief containing hedge recommendations is delivered:

1. Run `python3 scripts/kalshi_scanner.py --save` to get current
   Kalshi market data
2. Run `python3 analyst/fabrication_check.py --brief <path> --scanner-output <scanner_path>`
3. If fabrication_check exits with code 1, the brief is BLOCKED.
   Do not deliver. Log the offending claims and surface for review.
4. If fabrication_check exits with code 0, deliver.

---

## Examples

### Good: Gap flagged, synthetic constructed from real instruments

```
GAP: No direct Kalshi contract exists for "Guanajuato industrial
park shutdown due to cartel violence." Our scanner (2026-05-18)
found 0 Mexico-related contracts.

Closest proxy: EWW (MSCI Mexico ETF, ~$38.50) — because a Bajío
industrial disruption would reduce Mexican equity valuations.
Also MXN 1-month forwards (~17.60 spot) — because peso weakness
is a secondary channel.

Proposed hedge: Premium-cost-sized — allocate 1.2% of portfolio
($2.4M on $200M exposure): $800K to EWW puts (strike $35, Jun 2026),
$1.6K to USDMXN 1-month forward at 17.60 (selling MXN). This covers
~70% of the identified downside scenario per scenario analysis.

Flag: This covers equity and FX channels but not real-estate-specific
risk. No instrument covers Bajío industrial property directly.
```

### Bad: Fabricated (do not do this)

```
Kalshi: "Will the U.S. impose tariffs on Mexican goods in 2026?"
– Last traded at ~$0.18 (18% probability).
Buy at target $0.30-0.40. Allocate $1.5M.
```

(No tool run, no price fetch, no methodology — three violations.)

---

## Rubric Integration

The bake-off rubric's trade-integration dimension:

- **3/3:** Contracts named are verified currently trading OR
  synthetic construction uses only verified real instruments with
  explicit proxy logic and named sizing methodology
- **2/3:** Proxy instruments identified but sizing methodology
  unclear or prices not refreshed
- **1/3:** Generic directional recommendation without instrument
  names or proxy logic
- **0/3:** Any named contract is fabricated — no partial credit
