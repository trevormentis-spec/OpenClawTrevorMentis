"""TPS Approval Gate — present plan + cost, await approval before execution.

Rules:
- Plans under $0.50 aggregate: auto-approved.
- Plans over $0.50: require explicit approval via CLI/REST/UI.
- Any single asset over $5.00: requires second explicit confirmation.
- Approved plans are logged to provenance before execution begins.
"""
from __future__ import annotations

import sys

from .schemas import (
    PresentationPlan,
    PlanCostEstimate,
    ApprovalStatus,
    AssetKind,
)
from .config import get_config


def format_plan_summary(
    plan: PresentationPlan,
    estimate: PlanCostEstimate,
) -> str:
    """Format a plan for human review — asset table with costs."""
    lines = [
        "=" * 60,
        "  TREVOR PRESENTATIONAL SUITE — PLAN REVIEW",
        "=" * 60,
        f"  Plan ID:    {plan.plan_id}",
        f"  Brief ID:   {plan.brief_id}",
        f"  Deliverables: {', '.join(d.value for d in plan.deliverables)}",
        "",
        f"  {'#':<4} {'Kind':<14} {'Generator':<16} {'Cost':>8} {'Time':>8}",
        f"  {'-'*4} {'-'*14} {'-'*16} {'-'*8} {'-'*8}",
    ]

    for i, (spec, est) in enumerate(zip(plan.assets, estimate.assets), 1):
        lines.append(
            f"  {i:<4} {spec.kind.value:<14} {spec.generator:<16} "
            f"${est.estimated_cost_usd:>6.2f} {est.estimated_time_sec:>6.1f}s"
        )

    lines.extend([
        f"  {'-'*4} {'-'*14} {'-'*16} {'-'*8} {'-'*8}",
        f"  {'TOTAL':<35} ${estimate.total_cost_usd:>6.2f} "
        f"{estimate.total_time_sec:>6.1f}s",
    ])

    if estimate.expensive_assets:
        lines.extend([
            "",
            "  HIGH-COST ASSETS (>$5.00 each):",
        ])
        for item in estimate.expensive_assets:
            lines.append(f"    ! {item}")

    if estimate.stale_pricing_warnings:
        lines.extend([
            "",
            "  STALE PRICING WARNINGS:",
        ])
        for w in estimate.stale_pricing_warnings:
            lines.append(f"    ? {w}")

    lines.append("=" * 60)
    return "\n".join(lines)


def auto_approve_if_cheap(
    plan: PresentationPlan,
    estimate: PlanCostEstimate,
) -> ApprovalStatus:
    """Auto-approve plans under the cost threshold."""
    config = get_config()
    if estimate.total_cost_usd <= config.auto_approve_threshold_usd:
        plan.approval_status = ApprovalStatus.AUTO_APPROVED
        return ApprovalStatus.AUTO_APPROVED
    return ApprovalStatus.PENDING


def present_plan_cli(
    plan: PresentationPlan,
    estimate: PlanCostEstimate,
) -> ApprovalStatus:
    """Present plan summary to CLI, prompt for approval.

    Returns APPROVED, REJECTED, or MODIFIED.
    For non-interactive contexts, returns PENDING.
    """
    # Check auto-approve first
    status = auto_approve_if_cheap(plan, estimate)
    if status == ApprovalStatus.AUTO_APPROVED:
        return status

    summary = format_plan_summary(plan, estimate)
    print(summary)
    print()

    if not sys.stdin.isatty():
        # Non-interactive — return PENDING for API/programmatic handling
        plan.approval_status = ApprovalStatus.PENDING
        return ApprovalStatus.PENDING

    try:
        response = input("  Approve this plan? [y/n/m(odify)]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        plan.approval_status = ApprovalStatus.REJECTED
        return ApprovalStatus.REJECTED

    if response in ("y", "yes"):
        # Check for high-cost assets that need second confirmation
        config = get_config()
        if estimate.expensive_assets:
            print(f"\n  WARNING: {len(estimate.expensive_assets)} asset(s) exceed "
                  f"${config.high_cost_asset_threshold_usd:.2f} individually.")
            try:
                confirm = input("  Confirm high-cost assets? [y/n]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                plan.approval_status = ApprovalStatus.REJECTED
                return ApprovalStatus.REJECTED

            if confirm not in ("y", "yes"):
                plan.approval_status = ApprovalStatus.REJECTED
                return ApprovalStatus.REJECTED

        plan.approval_status = ApprovalStatus.APPROVED
        return ApprovalStatus.APPROVED
    elif response in ("m", "modify"):
        plan.approval_status = ApprovalStatus.MODIFIED
        return ApprovalStatus.MODIFIED
    else:
        plan.approval_status = ApprovalStatus.REJECTED
        return ApprovalStatus.REJECTED


def approve_programmatic(
    plan: PresentationPlan,
    estimate: PlanCostEstimate,
    approval: str,
) -> ApprovalStatus:
    """Programmatic approval for REST/API use.

    approval: "APPROVED", "REJECTED", or "MODIFY"
    """
    mapping = {
        "APPROVED": ApprovalStatus.APPROVED,
        "REJECTED": ApprovalStatus.REJECTED,
        "MODIFY": ApprovalStatus.MODIFIED,
    }
    status = mapping.get(approval.upper(), ApprovalStatus.REJECTED)
    plan.approval_status = status
    return status
