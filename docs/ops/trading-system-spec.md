# TREVOR TRADING SYSTEM — SPECIFICATION v1.0

**Classification:** Internal / Operator-Authorized
**Author:** Quant Architecture
**Operator:** Roderick
**Status:** Clean-slate design. No code inherited from prior system.
**Capital regime:** $50 max exposure at launch. Real USD on Kalshi.

---

## 0. Preamble: What We Are Building (and Why the Last One Died)

The previous system did not lose money because of bad luck. It lost money because it **fabricated edge**. It assigned probabilities by hardcoding, traded 100% YES into correlated tail risk, ran unattended, and treated its guardrails as suggestions. Every one of those is a design defect, not an execution defect.

This spec is built around one inversion: **the burden of proof is on the trade, not on the abstention.** The default action is *do nothing*. A trade must earn its way past intel provenance, calibrated edge, correlation budget, liquidity, and hard gates — in that order — or it does not happen. Most days, Trevor should trade nothing. That is success, not failure.

---

## 1. Philosophy & Design Principles

### 1.1 What "intel-driven" actually means

A trade is **intel-driven** if and only if it can answer the question *"why this trade, at this price, right now?"* with a chain that terminates in a published, timestamped, sourced Key Judgment. If the chain breaks anywhere, the trade is invalid. No KJ → no probability → no edge → no trade.

This is enforced structurally: the edge engine **cannot accept a probability that lacks a `kj_id`**. There is no code path that produces a tradeable probability from a constant.

### 1.2 Governing principles

| # | Principle | Enforcement |
|---|-----------|-------------|
| P1 | **No naked probabilities.** Every `p_true` traces to a KJ with provenance. | Schema-level: probabilities are objects, not floats. |
| P2 | **Conservative until calibrated.** We assume our estimate is wrong; we shrink toward market until evidence says otherwise. | Edge engine applies uncertainty haircut + market-prior shrinkage. |
| P3 | **Exit is designed before entry.** No order is submitted without a written exit plan in the same object. | Order schema requires non-null `exit_plan`. |
| P4 | **Guardrails are physics, not advice.** Limits live in the API client, below the strategy. The strategy *cannot* reach the exchange except through the gated client. | Architectural: single choke point. |
| P5 | **Two-directional by default.** NO is a first-class trade. Overpriced YES = buy NO. | Edge engine evaluates both sides symmetrically. |
| P6 | **Correlation is the enemy.** Diversify across thematic risk factors, not just tickers. | Portfolio constructor uses factor model. |
| P7 | **Small, then earn size.** Exposure caps and autonomy levels expand only on measured calibration. | Calibration loop is the only thing that can raise limits. |
| P8 | **Surgical Opus.** Opus 4.8 ($99 budget) is used only for adjudication of high-stakes/ambiguous calls, never for routine flow. DeepSeek Flash is the daily driver. | Budget gate per model. |
| P9 | **Human in the loop until proven.** Autonomy is earned in stages, never assumed. | Autonomy state machine. |
| P10 | **Fail closed.** Any error, missing data, stale intel, or breached gate → no trade, halt, alert. | Default-deny everywhere. |

### 1.3 Non-goals

- Not a high-frequency system. Decision cadence is daily, intra-day only for exits.
- Not a market-maker. We take liquidity at the touch with spread limits; we do not quote.
- Not multi-venue. Kalshi only. No Philby, Simmer, Polymarket.
- Not a maximizer. It is a survivor that compounds slowly on real edge.

---

## 2. System Architecture

### 2.1 Data flow (text diagram)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INTEL PIPELINE (upstream)                    │
│   Daily 13-region briefs · KJs (Kent bands) · Watchlist + decay      │
└───────────────────────────────┬─────────────────────────────────────┘
                                 │  KJ objects (JSON, signed, timestamped)
                                 ▼
        ┌────────────────────────────────────────────────┐
        │ (1) INTEL LAYER  — intel_layer/                 │
        │  • KJ ingest + schema validation                │
        │  • provenance binding (kj_id → sources)         │
        │  • probability extraction (Kent band → p,σ)     │
        │  • decay engine (time + watchlist functions)    │
        │  OUTPUT: ProbabilityEstimate{p, σ, kj_id, ttl}  │
        └───────────────────────┬────────────────────────┘
                                │
                                ▼
        ┌────────────────────────────────────────────────┐
        │ (2) MARKET MAP — market/                        │
        │  • Kalshi REST: discover markets, fetch books   │
        │  • map KJ event → Kalshi ticker(s)              │
        │  • record bid/ask/mid, depth, time-to-expiry    │
        │  OUTPUT: MarketSnapshot                          │
        └───────────────────────┬────────────────────────┘
                                │  (ProbabilityEstimate, MarketSnapshot) pair
                                ▼
        ┌────────────────────────────────────────────────┐
        │ (3) EDGE ENGINE — edge/                         │
        │  • shrink p toward market by uncertainty        │
        │  • compute edge (YES and NO sides)              │
        │  • apply min-edge gate scaled by σ              │
        │  • reject if stale / illiquid / insufficient    │
        │  OUTPUT: Candidate{side, edge, p_eff, conf}     │
        └───────────────────────┬────────────────────────┘
                                │  list of Candidates
                                ▼
        ┌────────────────────────────────────────────────┐
        │ (4) PORTFOLIO CONSTRUCTOR — portfolio/          │
        │  • factor/correlation model (thematic exposure) │
        │  • fractional-Kelly sizing w/ corr adjustment   │
        │  • concentration + diversification caps         │
        │  • net against existing positions               │
        │  OUTPUT: ProposedOrders[] (with exit_plan)      │
        └───────────────────────┬────────────────────────┘
                                │
                                ▼
        ┌────────────────────────────────────────────────┐
        │ (5) GUARDRAIL GATE — guardrails/  (HARD)        │
        │  • per-position %, total exposure %, daily loss │
        │  • drawdown halt, min edge, min liquidity, ttl  │
        │  • reject or clamp; emit audit record           │
        │  ⇒ THIS IS THE ONLY PATH TO THE EXCHANGE        │
        └───────────────────────┬────────────────────────┘
                                │  approved orders
                                ▼
        ┌────────────────────────────────────────────────┐
        │ (6) AUTONOMY CONTROLLER — autonomy/             │
        │  paper → tiny → confirmed → autonomous          │
        │  routes to human confirm OR auto-submit         │
        └───────────────────────┬────────────────────────┘
                                │
                                ▼
        ┌────────────────────────────────────────────────┐
        │ (7) EXECUTION ENGINE — execution/               │
        │  • gated Kalshi client (only exchange access)   │
        │  • WebSocket: fills, orderbook deltas           │
        │  • partial-fill + cancel/replace logic          │
        │  • spread/liquidity recheck at submit time      │
        └───────────────────────┬────────────────────────┘
                                │  executed positions
                                ▼
        ┌────────────────────────────────────────────────┐
        │ (8) EXIT ENGINE — exits/  (always-on)           │
        │  • stop-loss, time-decay liquidation            │
        │  • profit-taking, correlation-breakdown exit    │
        │  • monitors WS for trigger conditions           │
        └───────────────────────┬────────────────────────┘
                                │  realized outcomes
                                ▼
        ┌────────────────────────────────────────────────┐
        │ (9) CALIBRATION LOOP — calibration/             │
        │  • Brier score, reliability curve per band      │
        │  • feeds autonomy level + min-edge tuning        │
        │  • the ONLY component that can raise limits      │
        └────────────────────────────────────────────────┘

        Cross-cutting: (A) AUDIT LOG — audit/  (append-only, every
        decision, every rejection, every fill, every gate breach)
                       (B) STATE STORE — state/  (positions, limits,
                       autonomy level, daily P&L, kill-switch flag)
```

### 2.2 Component responsibilities (one line each)

- **Intel Layer** — turns KJs into probability estimates with uncertainty and TTL; never invents a number.
- **Market Map** — discovers Kalshi markets and binds them to KJ events; supplies live book.
- **Edge Engine** — decides if there is real, uncertainty-adjusted edge on either side.
- **Portfolio Constructor** — sizes and diversifies; nets against existing book.
- **Guardrail Gate** — the law. Clamps or kills. Sole choke point to the exchange.
- **Autonomy Controller** — decides whether a human must approve.
- **Execution Engine** — places orders intelligently; owns the only Kalshi credentials.
- **Exit Engine** — always-on; ensures every position dies on plan.
- **Calibration Loop** — scores us, governs autonomy and edge thresholds.
- **Audit Log / State Store** — memory and accountability.

---

## 3. The Intel Layer

### 3.1 Kent bands → probability + uncertainty

Sherman Kent's ordinal bands are mapped to a point estimate **and an explicit standard deviation**. The σ is what makes us conservative — wide bands trade smaller and need more edge.

| Kent band | Point `p` | σ (uncertainty) |
|-----------|-----------|------------------|
| Almost certain | 0.93 | 0.04 |
| Highly likely | 0.85 | 0.06 |
| Likely / probable | 0.70 | 0.08 |
| Roughly even chance | 0.50 | 0.10 |
| Unlikely / improbable | 0.30 | 0.08 |
| Highly unlikely | 0.15 | 0.06 |
| Remote / almost no chance | 0.07 | 0.04 |

If a KJ provides a numeric `p_point` and `p_ci` (confidence interval) directly, those override the band table, with `σ = (ci_high − ci_low) / 3.29` (treating CI as ~90%).

### 3.2 KJ schema (input)

```json
{
  "kj_id": "KJ-2025-06-14-MENA-031",
  "issued_at": "2025-06-14T06:00:00Z",
  "region": "MENA",
  "claim": "Strait of Hormuz remains open to commercial traffic through 2025-07-15",
  "kent_band": "highly likely",
  "p_point": 0.85,
  "p_ci": [0.78, 0.92],
  "horizon": "2025-07-15T00:00:00Z",
  "provenance": {
    "analyst": "trevor",
    "model": "deepseek-flash | opus-4.8",
    "brief_id": "BRIEF-2025-06-14",
    "sources": [
      {"id": "S-1", "type": "OSINT", "ref": "...", "weight": 0.4, "ts": "2025-06-13T22:00:00Z"},
      {"id": "S-2", "type": "marketdata", "ref": "...", "weight": 0.3, "ts": "2025-06-14T05:00:00Z"}
    ],
    "watchlist_event_id": "WL-HORMUZ-ESC",
    "reasoning_digest": "sha256:...",
    "signature": "ed25519:..."
  },
  "decay": { "model": "exponential", "half_life_hours": 72 },
  "risk_factors": ["oil_supply", "iran_escalation", "naval_conflict"]
}
```

**Validation rules (fail closed):**
- `kj_id`, `issued_at`, `horizon`, `provenance.sources` (≥1), `signature` all required.
- `signature` must verify or the KJ is rejected.
- `risk_factors` required — used by the correlation model.
- If horizon < now → reject (expired claim).

### 3.3 ProbabilityEstimate (output of intel layer)

```json
{
  "estimate_id": "PE-...",
  "kj_id": "KJ-2025-06-14-MENA-031",
  "p_raw": 0.85,
  "sigma_raw": 0.06,
  "p_decayed": 0.78,
  "sigma_effective": 0.11,
  "age_hours": 30,
  "ttl_hours": 42,
  "stale": false,
  "risk_factors": ["oil_supply", "iran_escalation", "naval_conflict"]
}
```

### 3.4 Decay (this is the fix for "decorative" signals)

Intel rots. We model two effects:

**1. Point decay toward the base rate** (claims drift to prior as evidence ages):
```
p_decayed = p_base + (p_raw − p_base) · exp(−λ·t)
λ = ln(2) / half_life_hours
p_base = 0.5   (neutral prior; or watchlist-supplied base rate)
```

**2. Uncertainty inflation** (we know less as time passes):
```
sigma_effective = sigma_raw · (1 + k·t / half_life_hours),  k = 0.5
```

**Staleness gate:** if `age_hours > 2 · half_life_hours` → `stale = true` → estimate is unusable for *entries* (still usable for exits/risk monitoring). A stale KJ cannot open a position. Period.

Watchlist events with their own decay functions override the default half-life when bound.

---

## 4. The Edge Engine

### 4.1 The shrinkage step (conservative-until-calibrated)

We never trade our raw estimate. We shrink it toward the market price by an amount proportional to our uncertainty and inversely proportional to our demonstrated calibration. The market is a prior we respect.

```
Let m = market mid (in probability terms, 0..1)
Let p = p_decayed, σ = sigma_effective
Calibration trust:  τ ∈ [0,1]   (from calibration loop; starts LOW, e.g. 0.25)

shrink_weight  w = σ² / (σ² + σ_market²)        # more uncertain → pull to market
                 but floored by trust:  w = max(w, 1 − τ)

p_eff = (1 − w)·p + w·m
```

Early in life, `τ` is low, so `w` is high, so `p_eff` sits close to the market — we barely deviate. As calibration is proven, `τ` rises, `w` falls, and we trust our own intel more. **This single mechanism prevents fabricated edge from being traded before we've earned the right.**

`σ_market` is estimated from the bid/ask spread: `σ_market = spread/2` (floored at 0.02).

### 4.2 Edge formula (both directions)

Edge is the gap between our shrunk probability and the executable price, net of cost.

```
YES edge:  e_yes = p_eff − ask_yes − fee
NO  edge:  e_no  = (1 − p_eff) − ask_no − fee
            (ask_no = 1 − bid_yes, on Kalshi the NO side has its own ask)

fee = Kalshi taker fee estimate per contract (modeled, not assumed zero)
```

We evaluate **both** and take the better side, if either clears the gate. This is structurally how NO becomes first-class: there is no preference for YES anywhere in the code.

### 4.3 Uncertainty-scaled minimum edge

The threshold is not a constant. The more uncertain we are, the more edge we demand.

```
min_edge = base_edge + κ · σ_effective
base_edge = 0.04          # 4 cents minimum even when certain
κ = 0.50

# example: σ_eff = 0.11 → min_edge = 0.04 + 0.055 = 0.095 (9.5 cents)
```

A signal passes only if `edge ≥ min_edge`.

### 4.4 Rejection conditions (any one → reject)

| Reject if | Reason |
|-----------|--------|
| `stale == true` | Intel too old to open. |
| `edge < min_edge` | Insufficient uncertainty-adjusted edge. |
| `σ_effective > 0.15` | We simply don't know. |
| `time_to_expiry < min_ttl` (see §6) | No room to be right. |
| market depth at touch < required size | Can't get filled without slippage. |
| spread > `max_spread` (see §7) | Too wide; price unreliable. |
| no `kj_id` | Fabricated probability. Hard reject. |
| KJ signature invalid | Provenance broken. |

### 4.5 Candidate (output)

```json
{
  "candidate_id": "CAND-...",
  "ticker": "HORMUZ-OPEN-JUL15",
  "side": "YES",
  "p_eff": 0.78,
  "market_mid": 0.71,
  "ask": 0.72,
  "edge": 0.06,
  "min_edge_required": 0.055,
  "sigma_effective": 0.09,
  "kj_id": "KJ-2025-06-14-MENA-031",
  "risk_factors": ["oil_supply","iran_escalation","naval_conflict"],
  "expiry": "2025-07-15T00:00:00Z"
}
```

---

## 5. Position Sizing & Portfolio Construction

### 5.1 Fractional Kelly

Full Kelly is for people who enjoy ruin. We use **quarter-Kelly**, further reduced by calibration trust.

For a binary contract priced `c` (cost of one YES contract, pays $1), with our effective win prob `p_eff`:

```
b = (1 − c) / c                      # net odds
f_kelly = (p_eff·b − (1 − p_eff)) / b
        = (p_eff − c) / (1 − c)      # simplified for binary $1 payout

f_used = f_kelly · kelly_fraction · τ
kelly_fraction = 0.25
τ = calibration trust (0.25 → 1.0)
```

So at launch, with τ=0.25, effective Kelly multiplier is **0.0625** — extremely small. This is intentional.

### 5.2 Correlation adjustment (the fix for "100% YES on correlated tail")

We do **not** size positions independently. Each candidate carries `risk_factors`. We maintain factor exposure and penalize candidates that load on already-crowded factors.

```
For candidate i with factor set F_i:
  crowding_i = Σ_{factor ∈ F_i} current_factor_exposure[factor]
  corr_penalty_i = 1 / (1 + γ · crowding_i),   γ = 2.0
  f_final_i = f_used_i · corr_penalty_i
```

`current_factor_exposure[factor]` = sum of dollar exposure of existing + proposed positions that load that factor, as fraction of total capital.

**Directional netting:** if two candidates load the same factor in the *same* market direction (both long oil-supply risk), their combined exposure counts fully toward crowding. If opposite (a natural hedge), crowding is reduced. This makes hedges *cheaper* to add and concentration *expensive* — the opposite of the prior system.

### 5.3 Concentration & diversification limits (hard, see §6 for enforcement)

| Rule | Limit |
|------|-------|
| Max single position | 20% of capital ($10 of $50) |
| Max single risk factor | 35% of capital aggregate |
| Max single region | 40% of capital |
| Min distinct risk factors when >2 positions | ≥3 |
| Max net directional skew on any factor | 60% of factor budget on one side |

### 5.4 Sizing pipeline

```
1. f_kelly per candidate
2. × kelly_fraction × τ            → f_used
3. × corr_penalty                  → f_final
4. dollars_i = f_final_i × capital
5. clamp to per-position cap (20%)
6. rank by edge/σ; fill greedily until factor/region caps bind
7. round to whole contracts; drop sub-minimum sizes
8. attach exit_plan to each (REQUIRED — §3 P3)
```

---

## 6. Guardrails (Hard Gates)

These live in `guardrails/` and are checked inside the gated Kalshi client. **No order reaches Kalshi without passing every gate.** Breach behavior is explicit and defaults to *deny*.

| Gate | Limit (launch) | Calculation | On breach |
|------|----------------|-------------|-----------|
| G1 Per-position max | 20% capital | `order_$ / capital ≤ 0.20` | Clamp to limit; if clamp < min size, reject. |
| G2 Total exposure max | 50% capital ($25 of $50) | `Σ open_$ + new_$ ≤ 0.50·capital` | Reject new orders. |
| G3 Daily loss cap | 10% capital ($5) | `realized + unrealized daily P&L ≤ −0.10·capital` | **Halt all new entries for the day.** Exits still allowed. |
| G4 Drawdown halt | 20% from peak equity | `equity ≤ 0.80·peak_equity` | **KILL SWITCH: liquidate-to-plan, no new trades, alert Roderick.** Manual reset only. |
| G5 Max leverage | 1.0× (no leverage) | cash-secured only | Reject. |
| G6 Min edge | per §4.3 (dynamic) | `edge ≥ base + κσ` | Reject candidate. |
| G7 Min liquidity | depth ≥ 2× order size at touch | from orderbook | Reject or downsize. |
| G8 Max time-to-expiry | ≤ 45 days | `expiry − now ≤ 45d` | Reject (no long-dated tie-ups at this size). |
| G9 Min time-to-expiry | ≥ 3 days for entry | `expiry − now ≥ 3d` | Reject (this directly prevents the "expiring tomorrow" disaster). |
| G10 Max spread | ≤ 8 cents | `ask − bid ≤ 0.08` | Reject. |
| G11 Stale intel | KJ age ≤ 2× half-life | from intel layer | Reject entry. |
| G12 Provenance | `kj_id` present + signature valid | schema + crypto check | Hard reject (cannot be overridden). |
| G13 Max orders/day | 5 entries/day at launch | counter in state | Reject beyond limit. |
| G14 Single-direction concentration | ≤ 70% of open positions on one side (YES/NO) | from book | Reject the order that would breach. Forces hedging consideration. |

**Capital reference:** `capital` is the *current* equity, recomputed daily. Limits scale automatically as equity grows or shrinks. `peak_equity` is a monotonic high-water mark for G4.

**Gate ordering:** G12 → G11 → G6 → G9 → G8 → G10 → G7 → G1 → G14 → G2 → G3 → G4 → G5 → G13### 7. Execution Engine

The execution engine is the only component permitted to send orders. Everything upstream produces *intentions*; the execution engine produces *fills*. This separation is deliberate — it means we can fuzz, replay, and dry-run the entire intelligence stack without a single live order leaving the building.

#### 7.1 Order Types

Kalshi supports limit and market orders. We use **limit orders exclusively**. Market orders on a thin binary book are a tax we refuse to pay — a single market buy on a 4-cent-wide spread donates 2 cents per contract to whoever is camping the offer.

Every order is constructed as a marketable-or-passive limit:

```json
{
  "order_intent": {
    "market_ticker": "KXPRESPARTY-28-DEM",
    "side": "yes",
    "action": "buy",
    "count": 140,
    "limit_price_cents": 47,
    "post_only": false,
    "intent_id": "uuid-v4",
    "edge_engine_ref": "decision-2024-...",
    "max_slippage_cents": 2,
    "expires_at": "2024-01-01T00:00:30Z"
  }
}
```

`max_slippage_cents` is enforced *client-side* before submission and re-checked after each partial fill. If the book has moved such that our remaining fills would exceed it, we cancel the residual rather than chase.

#### 7.2 Liquidity & Spread Gates

Before any order is built, the execution engine runs three checks against the live order book. All three must pass:

| Gate | Rule | Rationale |
|------|------|-----------|
| **Spread** | `(best_ask − best_bid) ≤ max_spread_cents` (default 3) | Wide spreads imply we are the only price discovery; our edge estimate is probably stale |
| **Top-of-book depth** | `depth_at_touch ≥ 0.25 × intended_count` | We don't want to *be* the book |
| **Cumulative depth** | `Σ depth within max_slippage_cents ≥ intended_count` | The full order must be fillable inside our slippage budget |

The depth math, formally. Given the YES book asks as `[(price_i, size_i)]` sorted ascending, for a buy of `N` contracts with limit `L`:

```
fillable(N, L) = min(N, Σ size_i for all i where price_i ≤ L)
vwap(N, L)     = (Σ price_i · min(size_i, remaining_i)) / filled
```

We require `fillable(N, L) == N` and `vwap − best_ask ≤ max_slippage_cents`.

#### 7.3 WebSocket → Execution Wiring

The execution engine subscribes to two channels per active ticker: `orderbook_delta` and `ticker`. The book is maintained as a local replica reconstructed from the snapshot + deltas, sequence-checked.

```
WS orderbook_delta ──> BookReplica.apply(delta)
                              │
                              ├─ if seq gap detected ──> resnapshot + freeze execution
                              │
                              └─ BookReplica.checksum() every 50 deltas
                                        │
                                 mismatch ──> resnapshot + freeze
```

**Critical rule: a stale or gapped book freezes execution.** If we detect a sequence gap, a checksum mismatch, or a heartbeat older than 2 seconds, we immediately:

1. Cancel all resting orders for that ticker.
2. Mark the ticker `EXEC_FROZEN`.
3. Re-snapshot via REST.
4. Only unfreeze after two consecutive clean checksums.

This is the single most important reliability property of the engine. **We would rather miss a fill than fill against a book we don't actually understand.** A book we think is real but isn't is how you wake up to a position you never intended.

#### 7.4 Partial Fill Handling

Binary markets fill in clips. A 140-lot order might fill 40 + 60 + 20 + (cancel residual 20). The engine tracks fill state per intent:

```json
{
  "intent_id": "uuid-v4",
  "target_count": 140,
  "filled_count": 100,
  "avg_fill_cents": 47.3,
  "residual_count": 40,
  "state": "PARTIAL",
  "fills": [
    {"count": 40, "price": 47, "ts": "...", "exchange_order_id": "..."},
    {"count": 60, "price": 47, "ts": "..."}
  ],
  "slippage_used_cents": 0.3
}
```

Decision logic on each fill event:

- **If `avg_fill_cents` still inside slippage budget AND book still passes gates** → leave residual resting, optionally cancel/replace to follow the touch.
- **If book moved against us beyond budget** → cancel residual, mark `PARTIAL_CLOSED`.
- **If filled ≥ 80% of target** → accept the fill, cancel residual, treat the position as established. The last 20% is rarely worth chasing into worse prices.

The position handed to the portfolio layer always reflects *actual* filled size, never intended size. Sizing math downstream must never assume the order filled in full.

#### 7.5 Cancel/Replace Logic

To stay at the touch without crossing, we use cancel/replace with a debounce. Naive replace-on-every-tick burns into rate limits and creates a race where you cancel an order that's filling.

```
on_book_update():
    if our_order.price == best_bid:        # still at touch, do nothing
        return
    if time_since_last_replace < 750ms:    # debounce
        return
    if book_passes_gates():
        cancel_replace(new_price=best_bid)
    else:
        cancel_only()   # don't re-rest into a degraded book
```

Cancel/replace is also rate-limited to a hard ceiling per ticker per minute (default 8). Hitting the ceiling freezes replacement and lets the existing order ride.

#### 7.6 The Gated Kalshi Client

The actual Kalshi client is wrapped in a gate object. **No code path can reach `client.create_order()` except through the gate.** The gate enforces, in order:

```
class GatedKalshiClient:
    def submit(self, order_intent):
        assert self.mode in ("PAPER","LIVE")          # 1. mode set explicitly
        self._check_guardrails(order_intent)           # 2. §6 guardrails
        self._check_liquidity_gates(order_intent)      # 3. §7.2
        self._check_daily_kill_switch()                # 4. loss limit
        self._check_position_caps(order_intent)        # 5. concentration
        if self.mode == "PAPER":
            return self._simulate_fill(order_intent)   # paper path
        if not self._human_confirm_if_required(order_intent):
            return Rejected("not confirmed")
        return self._raw_client.create_order(...)       # only real exit
```

In `PAPER` mode the underlying `_raw_client` is *not even instantiated* with trading credentials — it holds read-only keys. This is belt-and-suspenders: even a bug that bypasses the mode check cannot place a real order in paper mode because the credentials physically cannot.

---

### 8. Exit Engine

Entries are optional; exits are mandatory. Every position must have a defined exit before the entry order is submitted — the entry intent carries its exit plan as metadata, and the exit engine refuses to manage any position that arrives without one.

#### 8.1 Always-On Monitoring Design

The exit engine runs as a separate always-on process, independent of the entry/research loop. It must survive a crash of the research stack. It reconciles its position view from the exchange (source of truth) every 60 seconds, not from internal state.

```
ExitEngine loop (every 15s, faster near triggers):
    positions = kalshi.get_positions()       # ground truth
    for p in positions:
        plan = exit_plans.get(p.ticker)
        if plan is None:
            ALERT("unmanaged position!")      # should never happen
            plan = default_conservative_plan(p)
        evaluate_exits(p, plan, live_book)
```

A position the exit engine doesn't recognize is a P0 alert. Either we have a bug, or someone traded manually, or we got assigned something. Any of those means stop and look.

#### 8.2 Stop-Loss Rules

Stops on binary contracts are awkward — a contract going from 50¢ to 40¢ isn't a 20% loss, it's a probability revision. We use **two stop types**:

1. **Price stop (hard):** exit if mark price moves against entry by more than `stop_cents` (default 12¢). This is a circuit breaker against being wrong about a regime.
2. **Edge-collapse stop (soft):** the edge engine re-prices the market every cycle. If the model's fair value crosses to the *wrong side* of the current market price — i.e., the edge that justified the position is gone or inverted — exit regardless of P&L.

```json
{
  "exit_plan": {
    "stop_price_cents": 35,
    "edge_collapse": {
      "entry_fair_value": 0.55,
      "exit_if_fair_value_below": 0.47
    },
    "profit_take_cents": 78,
    "time_decay": {"days_before_expiry": 5, "action": "liquidate"},
    "correlation_breakdown_ref": "cluster-elections-2024"
  }
}
```

The edge-collapse stop is the important one. **Most of our losses should be small and informational** — we entered because fair value was 55¢ and price was 47¢; if fair value drops to 46¢, the trade thesis is dead and we leave at roughly break-even, not at a 12¢ price stop. The price stop only catches cases where the market moves faster than our model updates.

#### 8.3 Time-Decay Exits

Binary contracts near expiry become pure gamma — small information changes cause violent price swings, spreads widen, and our edge estimate degrades because there's no time for mispricing to correct. Liquidity also evaporates.

Default rule: **liquidate any position with 5 days to expiry**, regardless of P&L, unless it's a high-conviction terminal-resolution play explicitly flagged `hold_to_expiry: true`. For markets resolving on a known scheduled event (an election, a Fed meeting), we permit holding to resolution because the resolution is a clean binary event, not a slow decay. For markets resolving on fuzzy criteria, we always exit early.

The time-decay check runs daily and escalates the urgency of the limit order as expiry approaches (wider acceptable slippage as the window closes).

#### 8.4 Profit-Taking Rules

We don't hold to 99¢. The last few cents carry resolution risk (Kalshi settlement disputes, ambiguous outcomes) disproportionate to their reward. Default profit-take at `profit_take_cents` (78¢ for a YES bought at 47¢ ≈ realizing most of the edge). Beyond that the risk/reward inverts — you're risking 78¢ to make 22¢ on an outcome you're already mostly right about.

Profit-taking is *scaled*: take half the position at the first target, let the remainder run with a trailing edge-collapse stop. This captures the bulk of realized edge while leaving optionality.

#### 8.5 Rebalancing Triggers

Positions are re-sized, not just exited, when:

- **Edge grows:** fair value moved further from price → add (subject to position caps).
- **Edge shrinks but remains valid:** trim toward the Kelly-implied size at the new edge.
- **Correlation changed:** see §8.6.

Rebalancing is rate-limited (no more than one rebalance per position per 6 hours) to avoid churning fees on noise.

#### 8.6 Correlation-Breakdown Exits

Positions are grouped into correlation clusters (e.g., all "2028 Democratic nominee" markets share a cluster). The portfolio sizing assumes a correlation structure. If realized co-movement between cluster members diverges sharply from the assumed correlation matrix — measured as a rolling correlation that breaches a band around the assumed value — our diversification assumption is broken and our aggregate exposure is larger than intended.

```
for cluster in clusters:
    realized_corr = rolling_corr(cluster.members, window=14d)
    if abs(realized_corr - assumed_corr) > 0.35:
        ALERT and de-risk cluster to single-position-equivalent size
```

This catches the failure mode where you think you have five independent 1%-of-bankroll bets and you actually have one 5% bet.

---

### 9. Calibration Feedback Loop

A trading system that can't tell whether its probabilities are any good is just an expensive random number generator with conviction. The calibration loop is what earns the system the right to size up and, eventually, to act autonomously.

#### 9.1 Brier Score Tracking

For every resolved market we predicted, we record the forecast and outcome. The Brier score for a single binary forecast:

```
brier = (p_forecast − outcome)²        outcome ∈ {0, 1}
```

We track a rolling Brier over the last *N* resolutions (N=100) and compare against the **reference Brier of the market price at entry time**:

```
brier_skill = 1 − (brier_model / brier_market)
```

`brier_skill > 0` means our forecasts beat the market's implied probabilities. This is the only metric that actually matters — being well-calibrated against the market is necessary but not sufficient; we must be *better* than the price we traded against, net of edge threshold.

#### 9.2 Reliability Curve Per Kent Band

Raw Brier hides where we're broken. We bin forecasts and check whether predicted frequency matches observed frequency, **stratified by Kent confidence band** (the linguistic-certainty band from the intel layer — "likely", "probable", "almost certain", etc.).

```json
{
  "reliability": {
    "kent_band": "probable (0.60-0.75)",
    "bins": [
      {"pred_range": [0.60,0.65], "predicted_mean": 0.625, "observed_freq": 0.58, "n": 22},
      {"pred_range": [0.65,0.70], "predicted_mean": 0.674, "observed_freq": 0.55, "n": 18},
      {"pred_range": [0.70,0.75], "predicted_mean": 0.721, "observed_freq": 0.71, "n": 25}
    ],
    "calibration_error": 0.061,
    "overconfidence": true
  }
}
```

This stratification is the secret sauce. It lets us discover statements like: *"When the research layer says 'probable' we are systematically overconfident by 6 points, but when it says 'likely' we are well-calibrated."* That maps a linguistic hedge to a numerical correction we can apply.

The per-band calibration error feeds a **band correction map** that shifts the edge engine's probability estimate before it's compared to market price:

```
p_corrected = p_raw − calibration_error_signed(kent_band)
```

#### 9.3 Autonomy Progression

The system climbs a ladder. Each rung requires a calibration gate, evaluated over a minimum sample of resolved markets. No rung is skippable.

| Level | Behavior | Gate to reach |
|-------|----------|---------------|
| **0 — Paper** | Simulated fills only, no real money | Default starting state |
| **1 — Tiny** | Real orders, position cap = $5/contract, $50 aggregate | ≥50 paper resolutions, `brier_skill > 0`, calibration_error < 0.08 in all active Kent bands |
| **2 — Confirmed** | Real orders at normal size, **every entry requires human confirmation** | ≥75 live-tiny resolutions, `brier_skill > 0.03`, no band with calibration_error > 0.06 |
| **3 — Autonomous** | Acts without confirmation within guardrails | ≥150 confirmed resolutions, `brier_skill > 0.05` sustained 60 days, zero guardrail breaches, max drawdown within plan |

**Demotion is automatic and faster than promotion.** Any of: a guardrail breach, calibration_error exceeding 0.10 in an active band, or `brier_skill` going negative over the rolling window → drop one level immediately and freeze new entries pending review. It should be easy to fall and hard to climb.

#### 9.4 How Calibration Feeds Back

Two specific feedback paths:

1. **Into edge threshold τ:** the minimum edge required to trade is a function of recent calibration. When calibration is excellent, τ can tighten (we trust thinner edges). When it degrades, τ widens defensively.

   ```
   τ = τ_base + k · max(0, calibration_error − target_error)
   ```
   with `τ_base = 0.04`, `target_error = 0.04`, `k = 1.5`. Bad calibration mechanically demands fatter edges.

2. **Into sizing (Kelly fraction):** we never bet full Kelly. The Kelly fraction multiplier `λ` scales with `brier_skill`:

   ```
   λ = clamp(0.10 + 2.0 · brier_skill, 0.10, 0.40)
   ```
   A system with no demonstrated skill bets one-tenth Kelly. A system with proven `brier_skill = 0.10` bets up to 0.30 Kelly. We cap at 0.40 — full Kelly is for people who enjoy ruin.

---

### 10. File Structure

```
trading-system/
├── README.md                      # operator runbook, kill-switch instructions first
├── config/
│   ├── guardrails.yaml            # §6 limits — the file you edit to change risk
│   ├── markets.yaml               # watchlist, per-market overrides
│   ├── credentials.enc            # encrypted; paper keys read-only by default
│   └── autonomy_state.json        # current level + gate progress (audited)
├── intel/
│   ├── ingest.py                  # source fetchers (news, polls, scheduled events)
│   ├── kent_mapper.py             # linguistic certainty → probability bands
│   ├── source_weights.py          # per-source reliability priors
│   └── intel_store.py             # append-only timestamped intel log
├── edge/
│   ├── fair_value.py              # ensemble probability estimation
│   ├── calibration_correct.py     # applies §9.2 band correction map
│   ├── edge_calc.py               # edge = p_corrected − price, threshold τ
│   └── sizing.py                  # fractional Kelly, λ from brier_skill
├── execution/
│   ├── gated_client.py            # §7.6 — the only path to real orders
│   ├── book_replica.py            # WS book reconstruction + checksum
│   ├── liquidity_gates.py         # §7.2 spread/depth checks
│   ├── order_manager.py           # partial fills, cancel/replace
│   └── paper_fill.py              # simulated fill engine for PAPER mode
├── exit/
│   ├── exit_engine.py             # always-on monitor loop
│   ├── stops.py                   # price stop + edge-collapse stop
│   ├── time_decay.py              # expiry liquidation
│   └── correlation_monitor.py     # cluster co-movement breakdown
├── guardrails/
│   ├── kill_switch.py             # daily loss limit, manual halt
│   ├── position_caps.py           # concentration limits
│   └── preflight.py               # runs all checks before any submit
├── calibration/
│   ├── brier.py                   # rolling Brier + skill vs market
│   ├── reliability.py             # per-Kent-band reliability curves
│   ├── autonomy_ladder.py         # promotion/demotion logic
│   └── resolution_log.jsonl       # append-only forecast↔outcome record
├── llm/
│   ├── router.py                  # §13 Opus vs DeepSeek routing
│   ├── opus_client.py             # gated, budgeted
│   └── deepseek_client.py         # high-volume cheap path
├── audit/
│   └── decisions.jsonl            # every intent, gate result, fill — immutable
└── tests/
    ├── test_gates.py              # fuzz the guardrails
    ├── test_book_replica.py       # sequence gaps, checksum mismatches
    ├── test_paper_no_real_order.py# proves PAPER cannot place real orders
    └── replay/                    # recorded WS sessions for deterministic tests
```

The two most important files for an operator: `config/guardrails.yaml` (what you edit) and `guardrails/kill_switch.py` (what saves you). Both are documented at the top of `README.md`.

---

### 11. Implementation Order

Build inside-out: the safety and intelligence layers before anything can trade, the execution layer last and gated from birth.

#### Phase 1 — Intel Layer + Spec Validation (no trading)

**Deliverables:**
- `intel/` complete: ingestion, Kent mapping, source weights, append-only store.
- `edge/fair_value.py` producing probability estimates logged but unused.
- `calibration/resolution_log.jsonl` recording forecasts against eventual outcomes.
- Schema validation for every data structure in this spec (`tests/test_schemas.py`).
- **Gate to exit Phase 1:** 50 logged forecasts on real markets, reliability curve drawn, `brier_skill` computed. We must demonstrate the intel layer produces *any* skill before writing a single order path.

This phase costs nothing and risks nothing. If it fails — if we have no edge against market prices on paper — we stop here and the project was cheap.

#### Phase 2 — Edge Engine + Paper Trading

**Deliverables:**
- `edge/` complete with calibration correction and sizing.
- `execution/` in `PAPER` mode only, with read-only credentials.
- `execution/book_replica.py` running live against real WS feeds (real book, fake fills).
- `exit/` engine managing paper positions end-to-end.
- Full `audit/decisions.jsonl` pipeline.
- **Gate to exit Phase 2:** Autonomy ladder Level 1 gate met (§9.3) — 50 paper resolutions, positive skill, calibration error under threshold.

#### Phase 3 — Live with Confirmation (Levels 1→2)

**Deliverables:**
- `gated_client.py` LIVE path enabled, `_human_confirm_if_required` mandatory.
- `guardrails/kill_switch.py` wired and tested (deliberately trip it in a drill).
- Tiny-size live trading ($5/contract cap), every entry confirmed by a human.
- Daily reconciliation report: positions, P&L, calibration drift.
- **Gate to exit Phase 3:** Level 2 then Level 3 gates met over the required windows. This phase is *long* — months — by design.

#### Phase 4 — Autonomous (Level 3)

**Deliverables:**
- Confirmation requirement lifted within guardrails.
- Automated demotion triggers live and tested.
- Weekly operator review replaces per-trade confirmation.
- Continuous calibration monitoring with alerting.

Autonomy is not a feature we build; it is a privilege the system earns by surviving the prior phases with demonstrated skill.

---

### 12. Risk Disclosure

Even built perfectly, this system has failure modes. Honesty about them is part of the design.

**Resolution risk.** Kalshi markets resolve according to specific criteria that can be ambiguous, disputed, or resolved against the "obvious" outcome on a technicality. Our model estimates the *probability of the underlying event*; the contract pays on the *resolution criteria*. The gap between these is invisible to our edge engine and uncatchable by calibration until it bites. **This is the deepest blind spot.** We mitigate by exiting before resolution where possible (§8.4), but event-resolution plays are intrinsically exposed.

**Correlated tail events.** Our sizing assumes a correlation structure that is estimated from history. In a genuine regime break —
### 12. Risk Disclosure (continued)

In a genuine regime break — a structural shift where historical correlations and volatility assumptions cease to hold — the system's statistical models will produce confident but wrong signals. Backtested edge does not survive regime change. The 2008 credit crisis, the March 2020 COVID liquidity collapse, and the 2022 rates repricing each invalidated strategies that had been profitable for years. No amount of in-sample validation protects against an out-of-sample world that has fundamentally changed.

The system mitigates this through three layers, none of which is sufficient alone:

1. **Volatility-scaled position sizing.** When realized volatility exceeds the trailing 90-day 95th percentile, gross exposure is automatically cut by 50%, and by 75% above the 99th percentile. This does not prevent losses but caps the rate of capital destruction during the window before human intervention.

2. **Correlation breakdown detection.** The system monitors the rolling 20-day correlation matrix against the 250-day baseline. A Frobenius-norm deviation beyond 2.5 standard deviations triggers a soft halt: no new positions, existing positions held or reduced only. This is a warning, not a guarantee — correlations can break silently before the metric registers it.

3. **Hard kill switch.** Drawdown exceeding 8% of peak equity within any 5-day window halts all automated trading and requires manual re-enablement. This is the last line of defense and assumes the operator is available and rational at the moment of maximum stress, which is precisely when both are least likely.

**The operator accepts that these mechanisms can fail simultaneously.** A gap event — overnight news, a flash crash, an exchange halt — can move price through stop levels without execution. The kill switch acts on observed equity, which lags actual exposure during illiquid conditions. Position sizing reacts to measured volatility, which is backward-looking by construction. In the worst realistic case, the account can lose substantially more than the 8% drawdown limit suggests, up to and including total capital loss.

**No representation is made that the system is profitable.** Past simulated or live performance is not indicative of future results. The strategies herein are subject to decay as market participants arbitrage away the inefficiencies they exploit. The operator should treat all deployed capital as fully at risk and should never allocate funds whose loss would affect financial stability or wellbeing.

---

### 13. Cost & Opus Budget

#### 13.1 Role of Opus 4.8 in the Architecture

Opus 4.8 is the system's **reasoning escalation layer**, not its workhorse. The architecture is deliberately tiered to keep the expensive model out of the hot path:

| Layer | Model | Frequency | Purpose |
|-------|-------|-----------|---------|
| Signal generation | Local quant models | Per-tick / per-bar | Numeric, deterministic, no LLM |
| Routine classification | DeepSeek Flash | Per-event (~hundreds/day) | News tagging, sentiment, log triage |
| Reasoning escalation | **Opus 4.8** | Rare (~5–20/day) | Ambiguous regime calls, conflicting-signal arbitration, post-mortem analysis |

DeepSeek Flash handles the high-volume, low-stakes inference: parsing headlines, classifying earnings tone, summarizing filings, flagging anomalies in logs. It is roughly two orders of magnitude cheaper than Opus and entirely adequate for tasks where a wrong answer is cheap to correct and the input is structured.

Opus 4.8 is invoked only when:

- **Signals conflict materially** — e.g., the momentum and mean-reversion books disagree by more than a configured threshold, and the position-sizing logic needs a tiebreaker with explained reasoning.
- **A regime-break warning fires** (Section 12, layer 2) and a human-readable assessment is needed before the operator decides whether to override the soft halt.
- **Post-mortem on losing days** exceeding 2% — Opus reconstructs the decision chain and produces a written analysis. This is batch, off-hours, not latency-sensitive.
- **The operator explicitly asks a strategic question** through the console.

#### 13.2 When to Use Opus vs DeepSeek Flash

**Use DeepSeek Flash when:**
- The task is high-frequency or runs in any loop touching live trading.
- A misclassification is recoverable and low-cost.
- The output feeds a downstream numeric model rather than a human decision.
- Latency matters (Flash is faster and cheaper to retry).

**Use Opus 4.8 when:**
- The decision is irreversible or expensive (overriding a halt, sizing a large position).
- Multi-step reasoning over conflicting evidence is required.
- The output will be read by a human and must be defensible.
- It runs at most a few times per day, off the critical path.

**Hard rule:** Opus is never called inside the trading event loop. Any code path that can be triggered more than ~50 times per day must route to Flash or stay local. This is enforced by a rate limiter on the Opus client that hard-fails above 30 calls/day.

#### 13.3 Estimated Monthly Opus Burn

Assumptions (conservative upper bound):

| Use case | Calls/day | Avg input tokens | Avg output tokens |
|----------|-----------|------------------|-------------------|
| Signal conflict arbitration | 8 | 4,000 | 1,200 |
| Regime-break assessment | 1 | 6,000 | 2,000 |
| Daily post-mortem (losing days only) | 0.5 | 8,000 | 2,500 |
| Operator strategic queries | 3 | 3,000 | 1,500 |

**Daily token total (weighted):**
- Input: (8×4,000) + (1×6,000) + (0.5×8,000) + (3×3,000) = 32,000 + 6,000 + 4,000 + 9,000 = **51,000 input tokens/day**
- Output: (8×1,200) + (1×2,000) + (0.5×2,500) + (3×1,500) = 9,600 + 2,000 + 1,250 + 4,500 = **17,350 output tokens/day**

**Monthly (21 trading days):**
- Input: ~1.07M tokens
- Output: ~0.36M tokens

At indicative Opus 4.8 pricing (~$15/M input, ~$75/M output — adjust to current rates):
- Input cost: 1.07 × $15 ≈ **$16.05**
- Output cost: 0.36 × $75 ≈ **$27.00**
- **Estimated monthly Opus burn: ~$43**

#### 13.4 Budget Constraints ($99 remaining)

With **$99 remaining**, the projected ~$43/month Opus burn leaves a buffer but is **not sustainable at the upper-bound estimate for more than ~2 months** without replenishment. Controls:

1. **Monthly Opus cap of $50**, enforced at the API client level. On reaching $40 (80%), the system disables proactive Opus calls (post-mortems, non-urgent arbitration) and reserves remaining budget exclusively for regime-break assessments and operator-initiated queries.

2. **Hard stop at $50/month.** Beyond this, all Opus routing falls back to DeepSeek Flash with a degraded-mode flag logged on every call so the operator knows reasoning quality dropped.

3. **Token trimming.** Input contexts to Opus are summarized by Flash first, cutting average input tokens by an estimated 40% — bringing realistic input burn closer to ~$10/month. Post-summarization, expect actual monthly Opus cost nearer **$30–35**.

4. **Runway:** At ~$33/month realistic burn, the $99 budget covers **~3 months** of Opus availability. The operator should plan replenishment or further downgrade of escalation tasks to Flash before depletion.

**Recommendation:** Operate in summarized-input mode from day one, keep post-mortems batched to losing days only, and treat the $50 cap as a firewall rather than a target. This keeps Opus available for the decisions where its reasoning genuinely earns its cost — which, by design, are few.

---

*End of specification.*