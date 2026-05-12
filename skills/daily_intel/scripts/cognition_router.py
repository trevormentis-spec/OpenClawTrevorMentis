#!/usr/bin/env python3
"""
cognition_router.py — Tiered Intelligence Cognition Architecture.

Routes tasks to appropriate model tiers based on strategic importance,
reasoning depth, uncertainty, and expected intelligence value.

Tier 1 — Low-Cost / Continuous (cheap models, local, Sonar)
Tier 2 — Mid-Level Analysis (DeepSeek standard)
Tier 3 — High-Cognition Strategic Analysis (DeepSeek V4 Pro, Claude Opus)

Output: cron_tracking/cognition_routing.json (daily report)
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from trevor_config import WORKSPACE
from trevor_log import get_logger

log = get_logger("cognition_router")

CRON_DIR = SKILL_ROOT / "cron_tracking"
OUTPUT_FILE = CRON_DIR / "cognition_routing.json"

# ── Model tier definitions ──
MODEL_TIERS = {
    1: {
        "label": "Low-Cost / Continuous",
        "models": ["deepseek/deepseek-chat", "sonar"],
        "cost_ratio": 0.1,
        "use_for": [
            "rss_parsing", "source_classification", "metadata_extraction",
            "translation", "formatting", "collection_heartbeat",
            "diagnostics", "monitoring", "source_scoring", "maintenance",
        ],
    },
    2: {
        "label": "Mid-Level Analysis",
        "models": ["deepseek/deepseek-v4-flash"],
        "cost_ratio": 0.3,
        "use_for": [
            "narrative_tracking", "collection_analysis", "regional_summaries",
            "source_synthesis", "narrative_drift", "collection_confidence",
            "medium_analytical_products", "enrichment_synthesis",
        ],
    },
    3: {
        "label": "High-Cognition Strategic Analysis",
        "models": ["deepseek/deepseek-v4-pro", "anthropic/claude-opus-4.7"],
        "cost_ratio": 1.0,
        "use_for": [
            "strategic_forecasting", "estimative_reasoning", "leadership_analysis",
            "escalation_ladders", "scenario_trees", "strategic_warning",
            "longitudinal_synthesis", "alliance_fragmentation_analysis",
            "sanctions_architecture", "military_escalation_analysis",
            "geopolitical_regime_shifts", "high_value_intelligence_products",
        ],
    },
}

# ── Task → tier mapping ──
TASK_TIER_MAP = {
    # Pipeline tasks
    "daily_enrichment": 1,
    "story_tracking": 1,
    "collection_heartbeat": 1,
    "diagnostics": 1,
    # Assessment generation
    "assessment_generation": 3,  # estimative analysis → highest tier
    "narrative_conditioning": 2,
    # Collection intelligence
    "collection_quality": 2,
    "source_scoring": 1,
    "source_discovery": 1,
    # Global collection
    "country_profiling": 2,
    "epistemic_state": 2,
    # Analytical opportunities
    "product_discovery": 2,
    "intelligence_gap_detection": 2,
    # Operational reporting
    "operational_report": 1,
    # Strategic warning
    "strategic_warning": 3,
    "escalation_analysis": 3,
    "forecasting": 3,
}

# ── Task cost tracking ──
COST_MODEL_MAP = {
    "deepseek/deepseek-chat": {"input": 0.14, "output": 0.28},
    "deepseek/deepseek-v4-flash": {"input": 0.14, "output": 0.28},
    "deepseek/deepseek-v4-pro": {"input": 0.435, "output": 0.87},
    "anthropic/claude-opus-4.7": {"input": 15.0, "output": 75.0},
    "sonar": {"input": 0.50, "output": 1.50},
}


def classify_task(task_name: str, context: dict | None = None) -> dict:
    """Classify a task and return recommended model tier and models."""
    tier_num = TASK_TIER_MAP.get(task_name, 2)  # default to mid-level
    tier = MODEL_TIERS[tier_num]
    
    # Check strategic override
    strategic = context.get("strategic", False) if context else False
    if strategic and tier_num < 3:
        tier_num = 3
        tier = MODEL_TIERS[3]
    
    # Check uncertainty override
    uncertainty = context.get("uncertainty", 0) if context else 0
    if uncertainty > 0.7 and tier_num < 3:
        tier_num = 3
        tier = MODEL_TIERS[3]
    
    return {
        "task": task_name,
        "tier": tier_num,
        "tier_label": tier["label"],
        "recommended_models": tier["models"],
        "cost_ratio": tier["cost_ratio"],
        "strategic_override": strategic,
        "uncertainty_override": uncertainty > 0.7,
    }


def estimate_task_cost(task_name: str, estimated_tokens: int = 1000) -> dict:
    """Estimate cost for a task on its recommended tier."""
    tier_num = TASK_TIER_MAP.get(task_name, 2)
    tier = MODEL_TIERS[tier_num]
    model = tier["models"][0]  # primary model for this tier
    
    pricing = COST_MODEL_MAP.get(model, {"input": 1.0, "output": 2.0})
    input_cost = estimated_tokens / 1_000_000 * pricing["input"]
    output_cost = estimated_tokens / 1_000_000 * pricing["output"]
    
    return {
        "task": task_name,
        "model": model,
        "tier": tier_num,
        "estimated_cost_usd": round(input_cost + output_cost, 6),
        "estimated_tokens": estimated_tokens,
    }


def compute_daily_routing() -> dict:
    """Compute the daily cognition routing report."""
    routing = {}
    for task, tier_num in TASK_TIER_MAP.items():
        routing[task] = {
            "assigned_tier": tier_num,
            "tier_label": MODEL_TIERS[tier_num]["label"],
            "recommended_model": MODEL_TIERS[tier_num]["models"][0],
        }
    
    return routing


def compute_cost_allocation() -> dict:
    """Compute cost allocation by tier for the day's tasks."""
    allocation = {1: {"tasks": [], "total_cost": 0.0, "total_tokens": 0},
                  2: {"tasks": [], "total_cost": 0.0, "total_tokens": 0},
                  3: {"tasks": [], "total_cost": 0.0, "total_tokens": 0}}
    
    # Estimate costs for each task
    task_estimates = {
        "daily_enrichment": 2000, "story_tracking": 500, "collection_heartbeat": 300,
        "diagnostics": 200, "assessment_generation": 32000, "narrative_conditioning": 1000,
        "collection_quality": 500, "source_scoring": 300, "source_discovery": 500,
        "country_profiling": 1000, "epistemic_state": 500, "product_discovery": 1000,
        "intelligence_gap_detection": 500, "operational_report": 500,
        "strategic_warning": 4000, "escalation_analysis": 3000, "forecasting": 4000,
    }
    
    for task, tokens in task_estimates.items():
        cost = estimate_task_cost(task, tokens)
        tier = cost["tier"]
        allocation[tier]["tasks"].append(task)
        allocation[tier]["total_cost"] += cost["estimated_cost_usd"]
        allocation[tier]["total_tokens"] += tokens
    
    # Round costs
    for t in allocation:
        allocation[t]["total_cost"] = round(allocation[t]["total_cost"], 6)
    
    return allocation


def main():
    """Generate daily cognition routing report."""
    routing = compute_daily_routing()
    costs = compute_cost_allocation()
    
    report = {
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tier_definitions": {
            f"tier_{t}": {"label": v["label"], "models": v["models"],
                          "use_for": v["use_for"][:5]}
            for t, v in MODEL_TIERS.items()
        },
        "task_routing": routing,
        "cost_allocation_by_tier": costs,
        "total_daily_estimated_cost": round(
            sum(c["total_cost"] for c in costs.values()), 4
        ),
        "total_daily_estimated_tokens": sum(
            c["total_tokens"] for c in costs.values()
        ),
    }
    
    # Save
    CRON_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(report, indent=2))
    log.info("Cognition routing report generated")
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TIERED INTELLIGENCE COGNITION ARCHITECTURE")
    print(f"{'='*60}")
    
    for t_num in [1, 2, 3]:
        t = MODEL_TIERS[t_num]
        c = costs.get(t_num, {"total_cost": 0, "tasks": []})
        bar = "█" * min(20, len(c.get("tasks", [])) * 2)
        print(f"\n  Tier {t_num} — {t['label']}")
        print(f"  Models: {', '.join(t['models'])}")
        print(f"  Tasks ({len(c.get('tasks', []))}): {', '.join(c.get('tasks', [])[:6])}")
        print(f"  Est. daily cost: ${c.get('total_cost', 0):.4f}")
    
    print(f"\n  Total daily est. cost: ${report['total_daily_estimated_cost']:.6f}")
    print(f"  Total daily est. tokens: {report['total_daily_estimated_tokens']:,}")
    
    # Strategic vs operational split
    strategic_tasks = [t for t, tn in TASK_TIER_MAP.items() if tn == 3]
    operational_tasks = [t for t, tn in TASK_TIER_MAP.items() if tn <= 2]
    print(f"\n  Strategic cognition (Tier 3): {len(strategic_tasks)} tasks — "
          f"${costs[3]['total_cost']:.4f} ({costs[3]['total_cost']/max(report['total_daily_estimated_cost'],0.01)*100:.0f}% of cost)")
    print(f"  Operational cognition (Tier 1-2): {len(operational_tasks)} tasks — "
          f"${costs[1]['total_cost'] + costs[2]['total_cost']:.4f} "
          f"({(costs[1]['total_cost'] + costs[2]['total_cost'])/max(report['total_daily_estimated_cost'],0.01)*100:.0f}% of cost)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
