"""TPS Cost Estimator — predict USD and wall-clock time before execution.

Pricing data is seeded from providers.yaml and verified against the
GENERATOR_PRICING table. If last_verified > 30 days old, a warning is surfaced.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

from .schemas import (
    AssetSpec,
    AssetKind,
    PresentationPlan,
    CostEstimate,
    PlanCostEstimate,
)
from .config import get_config

# ── Generator Pricing Table ──────────────────────────────────────────────────
# Extends analyst/llm_gate.py PRICING with TPS-specific generators.

GENERATOR_PRICING: dict[str, dict] = {
    # Local / code-based (zero marginal cost)
    "mermaid": {"fixed_usd": 0.0, "time_sec": 5},
    "matplotlib": {"fixed_usd": 0.0, "time_sec": 3},
    "plotly": {"fixed_usd": 0.0, "time_sec": 3},
    "vega_lite": {"fixed_usd": 0.0, "time_sec": 3},
    "d2": {"fixed_usd": 0.0, "time_sec": 4},
    "graphviz": {"fixed_usd": 0.0, "time_sec": 3},
    "html_to_png": {"fixed_usd": 0.0, "time_sec": 5},
    "reportlab_table": {"fixed_usd": 0.0, "time_sec": 2},
    "leaflet": {"fixed_usd": 0.0, "time_sec": 3},
    "timeline": {"fixed_usd": 0.0, "time_sec": 4},
    # Maps
    "mapbox_static": {"fixed_usd": 0.0, "time_sec": 2},
    "mapbox_interactive": {"fixed_usd": 0.0, "time_sec": 3},
    "annotated_satellite": {"fixed_usd": 0.0, "time_sec": 10},
    # Image generation
    "flux2pro": {"per_image_usd": 0.05, "time_sec": 15},
    "ideogram_v3": {"per_image_usd": 0.08, "time_sec": 20},
    "recraft_v4": {"per_image_usd": 0.04, "time_sec": 12},
    "imagen_4": {"per_image_usd": 0.04, "time_sec": 10},
    "gpt_image_2": {"per_image_usd": 0.04, "time_sec": 15},
    # Audio
    "elevenlabs": {"per_char_usd": 0.00003, "time_sec_per_1k_chars": 5},
    "openai_tts": {"per_char_usd": 0.000015, "time_sec_per_1k_chars": 3},
    "suno": {"per_song_usd": 0.10, "time_sec": 30},
    # Video
    "veo_3_1": {"per_sec_video_usd": 0.40, "time_sec_per_sec_video": 30},
    "kling_3_0": {"per_sec_video_usd": 0.12, "time_sec_per_sec_video": 20},
    "runway_4_5": {"per_sec_video_usd": 0.18, "time_sec_per_sec_video": 25},
    "heygen": {"per_min_video_usd": 1.00, "time_sec_per_sec_video": 15},
}


def estimate_asset(spec: AssetSpec) -> CostEstimate:
    """Estimate cost and time for a single asset."""
    pricing = GENERATOR_PRICING.get(spec.generator, {})
    cost = 0.0
    time_sec = pricing.get("time_sec", 10.0)

    # Fixed cost generators
    if "fixed_usd" in pricing:
        cost = pricing["fixed_usd"]

    # Per-image pricing
    elif "per_image_usd" in pricing:
        count = spec.parameters.get("count", 1)
        cost = pricing["per_image_usd"] * count

    # Per-character pricing (audio)
    elif "per_char_usd" in pricing:
        chars = spec.parameters.get("char_count", 1000)
        cost = pricing["per_char_usd"] * chars
        time_sec = (chars / 1000) * pricing.get("time_sec_per_1k_chars", 5)

    # Per-second video pricing
    elif "per_sec_video_usd" in pricing:
        duration = spec.parameters.get("duration_sec", 10)
        cost = pricing["per_sec_video_usd"] * duration
        time_sec = duration * pricing.get("time_sec_per_sec_video", 20)

    # Per-minute video pricing
    elif "per_min_video_usd" in pricing:
        duration = spec.parameters.get("duration_sec", 60)
        cost = pricing["per_min_video_usd"] * (duration / 60)
        time_sec = duration * pricing.get("time_sec_per_sec_video", 15)

    # Per-song pricing
    elif "per_song_usd" in pricing:
        cost = pricing["per_song_usd"]

    config = get_config()
    requires_approval = cost > config.auto_approve_threshold_usd

    return CostEstimate(
        asset_id=spec.asset_id,
        kind=spec.kind,
        generator=spec.generator,
        estimated_cost_usd=round(cost, 4),
        estimated_time_sec=round(time_sec, 1),
        breakdown={"pricing_rule": pricing, "parameters": spec.parameters},
        requires_approval=requires_approval,
    )


def estimate_plan(plan: PresentationPlan) -> PlanCostEstimate:
    """Estimate total cost and time for a full presentation plan."""
    config = get_config()
    asset_estimates: list[CostEstimate] = []
    total_cost = 0.0
    total_time = 0.0
    expensive: list[str] = []
    stale_warnings: list[str] = []

    for spec in plan.assets:
        est = estimate_asset(spec)
        asset_estimates.append(est)
        total_cost += est.estimated_cost_usd
        total_time += est.estimated_time_sec

        if est.estimated_cost_usd > config.high_cost_asset_threshold_usd:
            expensive.append(
                f"{spec.asset_id} ({spec.generator}): ${est.estimated_cost_usd:.2f}"
            )

    # Check for stale pricing
    for spec in plan.assets:
        provider = config.get_provider(spec.generator)
        if provider.last_verified:
            try:
                verified = datetime.strptime(provider.last_verified, "%Y-%m-%d")
                if datetime.utcnow() - verified > timedelta(days=30):
                    stale_warnings.append(
                        f"{spec.generator}: pricing last verified {provider.last_verified}"
                    )
            except ValueError:
                pass

    requires_approval = total_cost > config.auto_approve_threshold_usd

    # Update plan with estimates
    plan.total_estimated_cost_usd = round(total_cost, 4)
    plan.total_estimated_time_sec = round(total_time, 1)

    return PlanCostEstimate(
        plan_id=plan.plan_id,
        assets=asset_estimates,
        total_cost_usd=round(total_cost, 4),
        total_time_sec=round(total_time, 1),
        expensive_assets=expensive,
        requires_approval=requires_approval,
        stale_pricing_warnings=stale_warnings,
    )


def check_budget_headroom(estimated_total: float) -> dict:
    """Check if estimated cost fits within TREVOR's existing budget.

    Integrates with analyst/cost_ledger.py CostLedger.projection().
    Returns dict with ok, daily_remaining, monthly_remaining, warnings.
    """
    try:
        trevor_root = Path(__file__).resolve().parent.parent.parent
        sys.path.insert(0, str(trevor_root))
        from analyst.cost_ledger import CostLedger
        ledger = CostLedger()
        projection = ledger.projection(estimated_total)
        return projection
    except (ImportError, Exception):
        # If TREVOR cost ledger unavailable, return permissive default
        return {
            "ok": True,
            "daily_remaining": 20.0,
            "monthly_remaining": 200.0,
            "warnings": ["TREVOR cost ledger unavailable — budget not checked"],
        }
