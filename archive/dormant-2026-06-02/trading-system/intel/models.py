#!/usr/bin/env python3
"""
Trading System — Core Data Models

Defines every data structure used across the system.
These are the contract between components. If the schema changes here,
every consumer must update.

Schemas are validated by tests/test_schemas.py.
"""

from __future__ import annotations

import datetime
import enum
import json
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


# ── Constants ──────────────────────────────────────────────────────

# Sherman Kent ordinal bands with canonical probability + uncertainty
KENT_BANDS = {
    "almost_certain":       {"p": 0.93, "sigma": 0.04},
    "highly_likely":        {"p": 0.85, "sigma": 0.06},
    "likely":               {"p": 0.70, "sigma": 0.08},
    "probable":             {"p": 0.70, "sigma": 0.08},  # alias for likely
    "roughly_even_chance":  {"p": 0.50, "sigma": 0.10},
    "even_chance":          {"p": 0.50, "sigma": 0.10},  # alias
    "unlikely":             {"p": 0.30, "sigma": 0.08},
    "improbable":           {"p": 0.30, "sigma": 0.08},  # alias
    "highly_unlikely":      {"p": 0.15, "sigma": 0.06},
    "remote":               {"p": 0.07, "sigma": 0.04},
    "almost_no_chance":     {"p": 0.07, "sigma": 0.04},  # alias
}

VALID_KENT_BANDS = set(KENT_BANDS.keys())

VALID_REGIONS = [
    "MENA", "EURASIA", "EAST_ASIA", "SOUTH_ASIA",
    "EUROPE", "AMERICAS", "SUB_SAHARAN_AFRICA", "GLOBAL"
]

DECAY_MODELS = ["exponential", "linear", "step", "none"]


# ── Helpers ─────────────────────────────────────────────────────────

def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def parse_iso(ts: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))


# ── Provenance ──────────────────────────────────────────────────────

@dataclass
class SourceRef:
    """A single source cited in a KJ."""
    id: str                         # e.g. "S-1"
    type: str                       # OSINT, marketdata, official, expert, etc.
    ref: str                        # URL, document ID, citation
    weight: float                   # 0.0-1.0 reliability weight
    ts: str                         # ISO timestamp of source publication
    analyst_note: str = ""          # Optional note about this source

    def validate(self) -> list[str]:
        errors = []
        if not self.id:
            errors.append("source.id is required")
        if not 0 <= self.weight <= 1:
            errors.append(f"source.weight must be 0-1, got {self.weight}")
        return errors


@dataclass
class Provenance:
    """Full provenance chain for a KJ."""
    analyst: str                    # "trevor" or sub-agent ID
    model: str                      # "deepseek-flash", "opus-4.8", etc.
    brief_id: str                   # e.g. "BRIEF-2026-05-31"
    sources: list[SourceRef]        # evidence backing this KJ
    watchlist_event_id: str = ""    # optional watchlist reference
    reasoning_digest: str = ""      # hash of reasoning; optional
    signature: str = ""             # integrity signature; optional

    def validate(self) -> list[str]:
        errors = []
        if not self.analyst:
            errors.append("provenance.analyst is required")
        if not self.brief_id:
            errors.append("provenance.brief_id is required")  # Pass brief_id='auto' to skip this check
        for s in self.sources:
            errors.extend(s.validate())
        return errors


# ── Decay ───────────────────────────────────────────────────────────

@dataclass
class DecayConfig:
    """How a probability estimate decays over time."""
    model: str                      # exponential, linear, step, none
    half_life_hours: float = 72    # for exponential
    linear_decay_days: float = 30  # for linear (p reaches 0 after this)
    step_drop_days: list[float] = field(default_factory=lambda: [14, 7, 3, 1])
    step_drop_values: list[float] = field(default_factory=lambda: [0.8, 0.6, 0.4, 0.1])

    def validate(self) -> list[str]:
        errors = []
        if self.model not in DECAY_MODELS:
            errors.append(f"decay.model must be one of {DECAY_MODELS}, got '{self.model}'")
        if self.model == "step":
            if len(self.step_drop_days) != len(self.step_drop_values):
                errors.append("step_drop_days and step_drop_values must have same length")
            if not all(0 <= v <= 1 for v in self.step_drop_values):
                errors.append("step_drop_values must all be 0-1")
        return errors

    def apply(self, age_hours: float) -> float:
        """Return multiplier (0-1) for probability based on age.

        Step decay: thresholds are in descending order (largest first).
        The first threshold the age exceeds determines the multiplier.
        If age is below all thresholds, multiplier = 1.0.
        """
        if self.model == "none":
            return 1.0
        if self.model == "exponential":
            if self.half_life_hours <= 0:
                return 0.0
            return 2 ** (-age_hours / self.half_life_hours)
        if self.model == "linear":
            max_hours = self.linear_decay_days * 24
            if max_hours <= 0:
                return 0.0
            return max(0.0, 1.0 - age_hours / max_hours)
        if self.model == "step":
            age_days = age_hours / 24
            # Thresholds should be in descending order; find first match
            for i, day_threshold in enumerate(self.step_drop_days):
                if age_days >= day_threshold:
                    return self.step_drop_values[i]
            return 1.0
        return 1.0


# ── Key Judgment ────────────────────────────────────────────────────

@dataclass
class KeyJudgment:
    """A calibrated intelligence judgment — the atomic input to the trading system."""
    kj_id: str                      # e.g. "KJ-2026-05-31-MENA-001"
    issued_at: str                  # ISO timestamp
    region: str                     # one of VALID_REGIONS
    claim: str                      # plain English statement
    kent_band: str                  # one of VALID_KENT_BANDS

    # Probability: either from kent_band or explicit
    p_point: Optional[float] = None    # Override from numeric estimate
    p_ci: Optional[list[float]] = None  # [low, high] confidence interval

    horizon: Optional[str] = None   # ISO timestamp of event horizon
    provenance: Optional[Provenance] = None
    decay: Optional[DecayConfig] = None
    risk_factors: list[str] = field(default_factory=list)

    def __post_init__(self):
        if self.p_point is None:
            band = KENT_BANDS.get(self.kent_band)
            if band:
                self.p_point = band["p"]
        if self.decay is None:
            self.decay = DecayConfig(model="exponential", half_life_hours=72)

    def get_p_and_sigma(self) -> tuple[float, float]:
        """Get point estimate p and uncertainty sigma."""
        if self.p_point is not None and self.p_ci is not None:
            # Use explicit CI
            p = self.p_point
            sigma = (self.p_ci[1] - self.p_ci[0]) / 3.29  # 90% CI → σ
        else:
            band = KENT_BANDS.get(self.kent_band)
            if band:
                p = band["p"] if self.p_point is None else self.p_point
                sigma = band["sigma"]
            else:
                p = self.p_point or 0.5
                sigma = 0.10
        return (p, sigma)

    def effective_probability(self, as_of: Optional[str] = None) -> float:
        """Probability at time as_of, accounting for decay."""
        base_p, _ = self.get_p_and_sigma()
        if self.decay is None:
            return base_p
        if as_of is None:
            as_of = now_iso()
        age = (parse_iso(as_of) - parse_iso(self.issued_at)).total_seconds() / 3600
        if age < 0:
            return base_p  # Future-dated KJ, no decay
        return base_p * self.decay.apply(age)

    def validate(self) -> list[str]:
        errors = []
        if not self.kj_id:
            errors.append("kj_id is required")
        if not self.claim:
            errors.append("claim is required")
        if self.region not in VALID_REGIONS:
            errors.append(f"region must be one of {VALID_REGIONS}, got '{self.region}'")
        if self.kent_band not in VALID_KENT_BANDS:
            errors.append(f"kent_band must be one of {VALID_KENT_BANDS}, got '{self.kent_band}'")
        if self.p_ci is not None:
            if len(self.p_ci) != 2:
                errors.append(f"p_ci must have 2 elements [low, high], got {len(self.p_ci)}")
            elif not (0 <= self.p_ci[0] <= self.p_ci[1] <= 1):
                errors.append(f"p_ci values must satisfy 0 <= low <= high <= 1")
        if self.provenance:
            errors.extend(self.provenance.validate())
        if self.decay:
            errors.extend(self.decay.validate())
        return errors

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "KeyJudgment":
        if d.get("provenance"):
            if d["provenance"].get("sources"):
                d["provenance"]["sources"] = [
                    SourceRef(**s) for s in d["provenance"]["sources"]
                ]
            d["provenance"] = Provenance(**d["provenance"])
        if d.get("decay"):
            d["decay"] = DecayConfig(**d["decay"])
        # Handle region validation normalization
        if "region" in d and d["region"]:
            d["region"] = d["region"].upper()
        return KeyJudgment(**d)


# ── ProbabilityEstimate ─────────────────────────────────────────────

@dataclass
class ProbabilityEstimate:
    """Output of the intel layer — a probability with provenance and TTL."""
    p: float                        # Point probability (0-1)
    sigma: float                    # Uncertainty (standard deviation)
    kj_id: str                      # Source Key Judgment ID
    issued_at: str                  # When the source KJ was issued
    effective_at: str               # When this estimate is valid (now = with decay applied)
    ttl_seconds: float              # Time-to-live (time until p decays below threshold)
    risk_factors: list[str] = field(default_factory=list)
    region: str = "GLOBAL"

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_kj(kj: KeyJudgment, as_of: Optional[str] = None) -> "ProbabilityEstimate":
        """Create a ProbabilityEstimate from a KJ at a given time."""
        if as_of is None:
            as_of = now_iso()
        p_eff = kj.effective_probability(as_of)
        _, sigma = kj.get_p_and_sigma()

        # Compute TTL: time until p decays below 0.5% (de minimis)
        if kj.decay and kj.decay.model != "none" and p_eff > 0.005:
            age_hours = (parse_iso(as_of) - parse_iso(kj.issued_at)).total_seconds() / 3600
            if kj.decay.model == "exponential" and kj.decay.half_life_hours > 0:
                # TTL is time until p hits 0.005
                # p(t) = p0 * 2^(-t/hl)
                # 0.005 = p_eff * 2^(-ttl/hl)
                # 2^(-ttl/hl) = 0.005/p_eff
                # -ttl/hl = log2(0.005/p_eff)
                # ttl = -hl * log2(0.005/p_eff)
                import math as _m
                ttl = -kj.decay.half_life_hours * _m.log2(0.005 / p_eff) * 3600
            elif kj.decay.model == "linear" and kj.decay.linear_decay_days > 0:
                # Time until linear decay reaches 0
                ttl = kj.decay.linear_decay_days * 86400 - age_hours * 3600
            else:
                ttl = kj.decay.half_life_hours * 3600 if kj.decay.half_life_hours else 86400
        else:
            ttl = 86400 * 7  # default 1 week for no-decay KJs

        return ProbabilityEstimate(
            p=round(p_eff, 4),
            sigma=round(sigma, 4),
            kj_id=kj.kj_id,
            issued_at=kj.issued_at,
            effective_at=as_of,
            ttl_seconds=max(0, ttl),
            risk_factors=kj.risk_factors,
            region=kj.region,
        )


# ── Edge / Signals ──────────────────────────────────────────────────

@dataclass
class MarketSnapshot:
    """Current state of a Kalshi market from the REST API + WebSocket."""
    ticker: str
    title: str
    yes_bid: float                  # In cents
    yes_ask: float
    no_bid: float
    no_ask: float
    mid_price: float                # Computed
    spread_cents: float
    volume: float
    expiry: str                     # ISO timestamp
    last_updated: str
    depth_yes: int = 0              # Total size on bid
    depth_no: int = 0               # Total size on ask

    def calculate_spread(self) -> float:
        return self.yes_ask - self.yes_bid

    def yes_price_as_probability(self) -> float:
        """Convert yes-ask to probability (cents → fraction)."""
        return self.yes_ask / 100.0

    def no_price_as_probability(self) -> float:
        """Convert no-bid to probability."""
        return self.no_bid / 100.0


@dataclass
class Candidate:
    """A potential trade that survived edge calculation."""
    ticker: str
    side: str                       # "YES" or "NO"
    edge_pct: float                 # Edge in percentage points
    p_effective: float              # Our probability estimate (decayed)
    p_market: float                 # Market price as probability
    sigma: float                    # Our uncertainty
    confidence: str                 # "high", "medium", "low"
    kj_id: str                      # Source judgment
    risk_factors: list[str] = field(default_factory=list)
    region: str = "GLOBAL"
    expiry: str = ""


# ── Orders ──────────────────────────────────────────────────────────

@dataclass
class ExitPlan:
    """Every order must have one of these."""
    stop_loss_pct: Optional[float] = None     # e.g. -50% from entry
    time_decay_exit_days: int = 7             # liquidate N days before expiry
    profit_take_pct: Optional[float] = None   # e.g. +200% from entry
    max_hold_days: int = 30                   # hard max hold time

    def validate(self) -> list[str]:
        errors = []
        if self.stop_loss_pct is not None and self.stop_loss_pct >= 0:
            errors.append("stop_loss_pct must be negative")
        if self.profit_take_pct is not None and self.profit_take_pct <= 0:
            errors.append("profit_take_pct must be positive")
        return errors


@dataclass
class ProposedOrder:
    """An order that passed the portfolio constructor but not guardrails yet."""
    ticker: str
    side: str                       # "YES" or "NO"
    action: str                     # "buy" or "sell"
    shares: int
    price_cents: float              # Limit price
    candidate: Candidate
    exit_plan: ExitPlan
    notional_cents: float = 0       # shares * price_cents
    total_cost: float = 0.0         # shares * price / 100
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = now_iso()


# ── Audit ───────────────────────────────────────────────────────────

@dataclass
class AuditEntry:
    """Every decision, rejection, fill, or gate breach."""
    timestamp: str
    event_type: str                 # kj_ingested, edge_computed, order_proposed,
                                    # gate_breach, order_submitted, order_filled,
                                    # order_rejected, exit_triggered
    data: dict                      # Event-specific payload
    component: str = ""             # Which component generated this

    def to_json(self) -> str:
        return json.dumps({"timestamp": self.timestamp, "event_type": self.event_type,
                          "component": self.component, "data": self.data})


# ── Calibration ─────────────────────────────────────────────────────

@dataclass
class ResolutionRecord:
    """A recorded forecast and its realized outcome."""
    kj_id: str
    claim: str
    predicted_p: float              # Our probability at forecast time
    predicted_sigma: float
    forecast_timestamp: str         # When we made the forecast
    resolution_timestamp: str       # When it resolved
    outcome: bool                   # True if event happened
    region: str = ""
    risk_factors: list[str] = field(default_factory=list)

    def brier_score(self) -> float:
        """Individual Brier score: (p - outcome)^2."""
        return (self.predicted_p - (1.0 if self.outcome else 0.0)) ** 2


# ── Enums for state machine ─────────────────────────────────────────

class AutonomyLevel(enum.IntEnum):
    PAPER = 0
    TINY_CONFIRMED = 1
    LIVE_BATCHED = 2
    AUTONOMOUS = 3


class GateResult(enum.Enum):
    PASS = "pass"
    CLAMP = "clamp"     # Can be reduced to fit limit
    REJECT = "reject"   # Cannot execute at all
