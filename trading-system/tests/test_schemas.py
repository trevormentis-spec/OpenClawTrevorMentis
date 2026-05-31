#!/usr/bin/env python3
"""
Schema Validation Tests — Phase 1 Gate

Tests every data structure defined in intel/models.py.
Run this before any component integration.
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

# Add trading-system to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from intel.models import (
    KeyJudgment, Provenance, SourceRef, DecayConfig, ProbabilityEstimate,
    ExitPlan, ProposedOrder, Candidate, MarketSnapshot, AuditEntry,
    ResolutionRecord, AutonomyLevel, GateResult, KENT_BANDS, VALID_KENT_BANDS,
    now_iso
)

# ── Test helpers ────────────────────────────────────────────────────

passed = 0
failed = 0
errors = []

def test(name: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        msg = f"  ❌ {name} — {detail}" if detail else f"  ❌ {name}"
        print(msg)
        errors.append(msg)


# ── 1. Kent Band Mapping ────────────────────────────────────────────

def test_kent_bands():
    print("\n## Kent Band Mapping")
    test("All 7 primary bands defined",
         len(KENT_BANDS) >= 7)
    test("Almost certain p=0.93",
         KENT_BANDS["almost_certain"]["p"] == 0.93)
    test("Remote p=0.07",
         KENT_BANDS["remote"]["p"] == 0.07)
    test("All bands 0 < p < 1",
         all(0 < v["p"] < 1 for v in KENT_BANDS.values()))
    test("All bands sigma > 0",
         all(v["sigma"] > 0 for v in KENT_BANDS.values()))
    test("Sigma increases at 0.5 (most uncertain)",
         KENT_BANDS["roughly_even_chance"]["sigma"] == max(
             v["sigma"] for v in KENT_BANDS.values()))


# ── 2. Decay Model ──────────────────────────────────────────────────

def test_decay():
    print("\n## Decay Model")
    d = DecayConfig(model="exponential", half_life_hours=24)
    test("Exponential: age=0 → multiplier=1",
         abs(d.apply(0) - 1.0) < 0.001)
    test("Exponential: age=1hl → multiplier≈0.5",
         abs(d.apply(24) - 0.5) < 0.01)
    test("Exponential: age=2hl → multiplier≈0.25",
         abs(d.apply(48) - 0.25) < 0.01)
    test("Exponential: never reaches 0",
         d.apply(10000) > 0)

    d_linear = DecayConfig(model="linear", linear_decay_days=30)
    test("Linear: age=0 → 1.0",
         abs(d_linear.apply(0) - 1.0) < 0.001)
    test("Linear: age=15d → 0.5",
         abs(d_linear.apply(15 * 24) - 0.5) < 0.01)
    test("Linear: age=30d → 0.0",
         d_linear.apply(30 * 24) < 0.001)

    # Step: thresholds [7, 3, 1] days with values [0.8, 0.6, 0.3]
    # Means: age >= 7d → 0.8, age >= 3d → 0.6, age >= 1d → 0.3, < 1d → 1.0
    d_step = DecayConfig(model="step",
                          step_drop_days=[7, 3, 1],
                          step_drop_values=[0.8, 0.6, 0.3])
    test("Step: age=0 → 1.0", abs(d_step.apply(0) - 1.0) < 0.001)
    test("Step: age=12h (<1d) → 1.0",
         abs(d_step.apply(12) - 1.0) < 0.001)
    test("Step: age=1d → 0.3",
         abs(d_step.apply(1 * 24) - 0.3) < 0.001)
    test("Step: age=2d → 0.3 (same band)",
         abs(d_step.apply(2 * 24) - 0.3) < 0.001)
    test("Step: age=4d → 0.6 (second band)",
         abs(d_step.apply(4 * 24) - 0.6) < 0.001)
    test("Step: age=10d → 0.8 (first band)",
         abs(d_step.apply(10 * 24) - 0.8) < 0.001)

    d_none = DecayConfig(model="none")
    test("None: always 1.0",
         abs(d_none.apply(10000) - 1.0) < 0.001)

    errors_bad = DecayConfig(model="invalid").validate()
    test("Invalid model → validation error",
         len(errors_bad) > 0)


# ── 3. KeyJudgment Validation ───────────────────────────────────────

def test_kj_validation():
    print("\n## KeyJudgment Validation")

    valid_kj = KeyJudgment(
        kj_id="KJ-2026-05-31-MENA-001",
        issued_at=now_iso(),
        region="MENA",
        claim="Iran nuclear deal is reached within 90 days",
        kent_band="likely",
        provenance=Provenance(
            analyst="trevor",
            model="deepseek-flash",
            brief_id="BRIEF-2026-05-31",
            sources=[
                SourceRef(id="S-1", type="OSINT",
                          ref="https://example.com/intel1",
                          weight=0.6, ts=now_iso())
            ]
        )
    )
    test("Valid KJ → no validation errors",
         len(valid_kj.validate()) == 0)

    bad_kj = KeyJudgment(
        kj_id="",
        issued_at=now_iso(),
        region="INVALID",
        claim="",
        kent_band="invalid_band"
    )
    errs = bad_kj.validate()
    test("Empty kj_id → error", any("kj_id" in e for e in errs))
    test("Empty claim → error", any("claim" in e for e in errs))
    test("Invalid region → error", any("region" in e for e in errs))
    test("Invalid kent_band → error", any("kent_band" in e for e in errs))

    # Test p_ci validation
    bad_ci = KeyJudgment(
        kj_id="KJ-TEST",
        issued_at=now_iso(),
        region="MENA",
        claim="test",
        kent_band="likely",
        p_ci=[0.9, 0.5]  # low > high
    )
    ci_errs = bad_ci.validate()
    test("p_ci low > high → error", any("ci" in e.lower() or "p_ci" in e for e in ci_errs))


# ── 4. KJ → ProbabilityEstimate Conversion ──────────────────────────

def test_kj_to_estimate():
    print("\n## KJ → ProbabilityEstimate")
    kj = KeyJudgment(
        kj_id="KJ-2026-05-31-TEST-001",
        issued_at=now_iso(),
        region="GLOBAL",
        claim="Test event occurs",
        kent_band="highly_likely",
        decay=DecayConfig(model="none"),
    )

    est = ProbabilityEstimate.from_kj(kj)
    test("Estimate p matches kent band",
         abs(est.p - 0.85) < 0.01)
    test("Estimate sigma populated",
         est.sigma > 0)
    test("Estimate kj_id matches source",
         est.kj_id == "KJ-2026-05-31-TEST-001")
    test("Estimate has risk_factors",
         isinstance(est.risk_factors, list))

    # With decay
    kj_old = KeyJudgment(
        kj_id="KJ-OLD",
        issued_at="2026-01-01T00:00:00Z",
        region="GLOBAL",
        claim="Old event",
        kent_band="likely",
        decay=DecayConfig(model="exponential", half_life_hours=24),
    )
    est_old = ProbabilityEstimate.from_kj(kj_old)
    test("Decayed old KJ → p < original",
         est_old.p < 0.70)


# ── 5. Serialization Round-Trip ─────────────────────────────────────

def test_serialization():
    print("\n## Serialization")

    kj = KeyJudgment(
        kj_id="KJ-2026-05-31-MENA-001",
        issued_at=now_iso(),
        region="MENA",
        claim="Iran deal",
        kent_band="likely",
        provenance=Provenance(
            analyst="trevor",
            model="deepseek-flash",
            brief_id="BRIEF-2026-05-31",
            sources=[
                SourceRef(id="S-1", type="OSINT", ref="url",
                          weight=0.5, ts=now_iso())
            ]
        ),
        decay=DecayConfig(model="exponential", half_life_hours=72),
        risk_factors=["oil", "iran"],
    )

    d = kj.to_dict()
    test("to_dict produces dict", isinstance(d, dict))
    test("to_dict has all fields",
         all(k in d for k in ["kj_id", "issued_at", "region", "claim",
                              "kent_band", "provenance", "decay", "risk_factors"]))

    # Round-trip
    kj2 = KeyJudgment.from_dict(d)
    test("from_dict round-trip: kj_id", kj2.kj_id == kj.kj_id)
    test("from_dict round-trip: kent_band", kj2.kent_band == kj.kent_band)
    test("from_dict round-trip: provenance restored",
         kj2.provenance is not None)
    test("from_dict round-trip: sources restored",
         len(kj2.provenance.sources) == 1)
    test("from_dict round-trip: decay restored",
         kj2.decay is not None)
    test("from_dict round-trip: risk_factors",
         kj2.risk_factors == ["oil", "iran"])


# ── 6. Exit Plan ────────────────────────────────────────────────────

def test_exit_plan():
    print("\n## Exit Plan")
    valid = ExitPlan(stop_loss_pct=-0.5, time_decay_exit_days=7)
    test("Valid exit → no errors", len(valid.validate()) == 0)

    bad_stop = ExitPlan(stop_loss_pct=0.5)
    test("Positive stop_loss → error",
         any("stop_loss" in e for e in bad_stop.validate()))

    bad_take = ExitPlan(profit_take_pct=-1.0)
    test("Negative profit_take → error",
         any("profit_take" in e for e in bad_take.validate()))


# ── 7. AutonomyLevel ────────────────────────────────────────────────

def test_autonomy():
    print("\n## Autonomy Level")
    test("PAPER = 0", AutonomyLevel.PAPER.value == 0)
    test("TINY_CONFIRMED = 1", AutonomyLevel.TINY_CONFIRMED.value == 1)
    test("LIVE_BATCHED = 2", AutonomyLevel.LIVE_BATCHED.value == 2)
    test("AUTONOMOUS = 3", AutonomyLevel.AUTONOMOUS.value == 3)
    test("Ordering: PAPER < TINY",
         AutonomyLevel.PAPER < AutonomyLevel.TINY_CONFIRMED)
    test("Ordering: TINY < LIVE",
         AutonomyLevel.TINY_CONFIRMED < AutonomyLevel.LIVE_BATCHED)
    test("Ordering: LIVE < AUTO",
         AutonomyLevel.LIVE_BATCHED < AutonomyLevel.AUTONOMOUS)


# ── Run ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  Trading System — Schema Validation Tests")
    print("  Phase 1 Gate")
    print("=" * 60)

    test_kent_bands()
    test_decay()
    test_kj_validation()
    test_kj_to_estimate()
    test_serialization()
    test_exit_plan()
    test_autonomy()

    print(f"\n{'=' * 60}")
    print(f"  Results: {passed} passed, {failed} failed")
    if failed > 0:
        print(f"\n  Failures:")
        for e in errors:
            print(f"    {e}")
    print(f"{'=' * 60}")

    sys.exit(0 if failed == 0 else 1)
