#!/usr/bin/env python3
"""LLM Gating — Central routing logic for all model calls.

Every model call in Trevor goes through route(). The gating decision selects
the appropriate model and provider based on task type, complexity signals,
and budget constraints. Decisions are logged to memory/llm-routing-log.jsonl.

Usage:
    from analyst.llm_gate import route
    decision = route("subscriber_brief", {"target_words": 4000, "scenarios": 3})
    # decision.model, decision.provider, decision.estimated_cost_usd, etc.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional

# ── Configuration paths ──────────────────────────────────────────────────────
WORKSPACE = Path(__file__).resolve().parent.parent
CONFIG_PATH = WORKSPACE / "config" / "llm-routing.yaml"
BUDGET_PATH = WORKSPACE / "config" / "budget.yaml"
ROUTING_LOG = WORKSPACE / "memory" / "llm-routing-log.jsonl"

# ── Pricing (USD per million tokens) ─────────────────────────────────────────
PRICING = {
    "anthropic/claude-opus-4.7": {"input": 5.00, "output": 25.00},
    "anthropic/claude-sonnet-4.5": {"input": 3.00, "output": 15.00},
    "anthropic/claude-vision": {"input": 3.00, "output": 15.00},
    "nanobanana/image-gen": {"input": 0.00, "output": 0.00, "per_image": 0.04},
    "openai/whisper-large-v3": {"input": 0.00, "output": 0.00, "per_minute": 0.006},
    "deepseek/deepseek-v4-pro": {"input": 0.40, "output": 1.60},
    "deepseek/deepseek-v4-flash": {"input": 0.14, "output": 0.28},
    "elevenlabs/tts": {"input": 0.00, "output": 0.00, "per_char": 0.00003},
}

# ── Provider mapping ─────────────────────────────────────────────────────────
MODEL_PROVIDER = {
    "anthropic/claude-opus-4.7": "openrouter",
    "anthropic/claude-sonnet-4.5": "openrouter",
    "anthropic/claude-vision": "openrouter",
    "nanobanana/image-gen": "openrouter",
    "openai/whisper-large-v3": "openrouter",
    "deepseek/deepseek-v4-pro": "deepseek_direct",
    "deepseek/deepseek-v4-flash": "deepseek_direct",
    "elevenlabs/tts": "elevenlabs",
}

# ── Task type routing rules ──────────────────────────────────────────────────
# Each rule: default model, escalation triggers, downgrade triggers, budget cap
TASK_RULES: dict[str, dict] = {
    "flagship_document": {
        "default": "anthropic/claude-opus-4.7",
        "escalate_to": None,  # Already at top
        "downgrade_to": "anthropic/claude-sonnet-4.5",
        "downgrade_if": {"target_words_lt": 2000, "routine": True},
        "budget_cap": 15.00,
        "quality_gates": ["scope_check", "fabrication_check", "themes_preflight", "completeness"],
    },
    "subscriber_brief": {
        "default": "deepseek/deepseek-v4-pro",
        "escalate_to": "anthropic/claude-opus-4.7",
        "escalate_if_any": [
            "target_words_gte:3000",
            "scenarios_gte:3",
            "flagship_tag:true",
            "audience_family_office:true",
            "principal_handback:true",
        ],
        "downgrade_to": "deepseek/deepseek-v4-flash",
        "downgrade_if": {"target_words_lt": 1500, "routine": True},
        "budget_cap": 5.00,
        "quality_gates": ["scope_check", "fabrication_check", "themes_preflight"],
    },
    "daily_ingestion": {
        "default": "deepseek/deepseek-v4-flash",
        "escalate_to": "deepseek/deepseek-v4-pro",
        "escalate_if_any": ["complexity_high:true", "critical_source:true"],
        "downgrade_to": None,
        "budget_cap": 2.00,
        "quality_gates": ["scope_check"],
    },
    "entity_deepening": {
        "default": "deepseek/deepseek-v4-pro",
        "escalate_to": "anthropic/claude-opus-4.7",
        "escalate_if_any": ["critical_entity:true", "target_words_gte:3000"],
        "downgrade_to": "deepseek/deepseek-v4-flash",
        "downgrade_if": {"routine": True},
        "budget_cap": 5.00,
        "quality_gates": ["fabrication_check"],
    },
    "source_classification": {
        "default": "deepseek/deepseek-v4-flash",
        "escalate_to": None,
        "downgrade_to": None,
        "budget_cap": 0.50,
        "quality_gates": [],
    },
    "translation": {
        "default": "deepseek/deepseek-v4-flash",
        "escalate_to": "deepseek/deepseek-v4-pro",
        "escalate_if_any": ["formal_document:true", "legal_text:true"],
        "downgrade_to": None,
        "budget_cap": 1.00,
        "quality_gates": [],
    },
    "calibration_review": {
        "default": "deepseek/deepseek-v4-pro",
        "escalate_to": "anthropic/claude-opus-4.7",
        "escalate_if_any": ["high_stakes:true"],
        "downgrade_to": None,
        "budget_cap": 3.00,
        "quality_gates": [],
    },
    "postdiction_analysis": {
        "default": "anthropic/claude-sonnet-4.5",
        "escalate_to": "anthropic/claude-opus-4.7",
        "escalate_if_any": ["flagship_tag:true"],
        "downgrade_to": "deepseek/deepseek-v4-pro",
        "downgrade_if": {"routine": True},
        "budget_cap": 5.00,
        "quality_gates": ["fabrication_check"],
    },
    "red_team_analysis": {
        "default": "anthropic/claude-opus-4.7",
        "escalate_to": None,
        "downgrade_to": None,
        "budget_cap": 10.00,
        "quality_gates": ["scope_check", "fabrication_check"],
    },
    "framework_refinement": {
        "default": "anthropic/claude-opus-4.7",
        "escalate_to": None,
        "downgrade_to": "anthropic/claude-sonnet-4.5",
        "downgrade_if": {"incremental": True},
        "budget_cap": 10.00,
        "quality_gates": [],
    },
    "source_brainstorm": {
        "default": "anthropic/claude-opus-4.7",
        "escalate_to": None,
        "downgrade_to": None,
        "budget_cap": 5.00,
        "quality_gates": [],
    },
    "cross_source_correlation": {
        "default": "deepseek/deepseek-v4-pro",
        "escalate_to": "anthropic/claude-opus-4.7",
        "escalate_if_any": ["sources_gte:5", "critical_finding:true"],
        "downgrade_to": "deepseek/deepseek-v4-flash",
        "downgrade_if": {"sources_lt": 3},
        "budget_cap": 3.00,
        "quality_gates": ["fabrication_check"],
    },
    "scope_classifier": {
        "default": "deepseek/deepseek-v4-flash",
        "escalate_to": "deepseek/deepseek-v4-pro",
        "escalate_if_any": ["slow_path:true"],
        "downgrade_to": None,
        "budget_cap": 0.50,
        "quality_gates": [],
    },
    "topic_onboarding_strategic": {
        "default": "anthropic/claude-opus-4.7",
        "escalate_to": None,
        "downgrade_to": None,
        "budget_cap": 10.00,
        "quality_gates": [],
    },
    "topic_onboarding_tactical": {
        "default": "deepseek/deepseek-v4-pro",
        "escalate_to": None,
        "downgrade_to": None,
        "budget_cap": 5.00,
        "quality_gates": [],
    },
    "topic_onboarding_operational": {
        "default": "deepseek/deepseek-v4-flash",
        "escalate_to": None,
        "downgrade_to": None,
        "budget_cap": 2.00,
        "quality_gates": [],
    },
    "image_analysis": {
        "default": "anthropic/claude-vision",
        "escalate_to": None,
        "downgrade_to": None,
        "budget_cap": 3.00,
        "quality_gates": [],
    },
    "image_generation": {
        "default": "nanobanana/image-gen",
        "escalate_to": None,
        "downgrade_to": None,
        "budget_cap": 2.00,
        "quality_gates": [],
    },
    "audio_transcription": {
        "default": "openai/whisper-large-v3",
        "escalate_to": None,
        "downgrade_to": None,
        "budget_cap": 2.00,
        "quality_gates": [],
    },
    "audio_generation": {
        "default": "elevenlabs/tts",
        "escalate_to": None,
        "downgrade_to": None,
        "budget_cap": 3.00,
        "quality_gates": [],
    },
    "status_report": {
        "default": "deepseek/deepseek-v4-flash",
        "escalate_to": None,
        "downgrade_to": None,
        "budget_cap": 0.50,
        "quality_gates": [],
    },
    "skill_discovery": {
        "default": "anthropic/claude-opus-4.7",
        "escalate_to": None,
        "downgrade_to": None,
        "budget_cap": 5.00,
        "quality_gates": [],
    },
    "forum_synthesis": {
        "default": "anthropic/claude-opus-4.7",
        "escalate_to": None,
        "downgrade_to": None,
        "budget_cap": 5.00,
        "quality_gates": [],
    },
    "capability_gap_review": {
        "default": "deepseek/deepseek-v4-pro",
        "escalate_to": None,
        "downgrade_to": None,
        "budget_cap": 3.00,
        "quality_gates": [],
    },
    "custom_skill_proposal": {
        "default": "anthropic/claude-opus-4.7",
        "escalate_to": None,
        "downgrade_to": None,
        "budget_cap": 5.00,
        "quality_gates": [],
    },
    "section_generation": {
        "default": "anthropic/claude-sonnet-4.5",
        "escalate_to": "anthropic/claude-opus-4.7",
        "escalate_if_any": ["final_coherence_pass:true", "flagship_tag:true"],
        "downgrade_to": "deepseek/deepseek-v4-pro",
        "downgrade_if": {"routine": True, "target_words_lt": 500},
        "budget_cap": 3.00,
        "quality_gates": ["fabrication_check"],
    },
}

# Fallback chains per provider
FALLBACK_CHAINS = {
    "openrouter": [
        "anthropic/claude-sonnet-4.5",
        "deepseek/deepseek-v4-pro",
        "deepseek/deepseek-v4-flash",
    ],
    "deepseek_direct": [
        "deepseek/deepseek-v4-flash",
        "anthropic/claude-sonnet-4.5",
    ],
    "elevenlabs": [],  # No fallback for TTS
}


@dataclass
class GatingDecision:
    """Result of a routing decision."""
    model: str
    provider: str
    estimated_cost_usd: float
    fallback_chain: list[str]
    justification: str
    complexity_signals: dict
    task_type: str = ""
    budget_tolerance: str = "standard"
    quality_gates: list[str] = field(default_factory=list)
    timestamp: str = ""


def _check_escalation_triggers(triggers: list[str], metadata: dict) -> tuple[bool, list[str]]:
    """Check if any escalation triggers are met. Returns (triggered, reasons)."""
    reasons = []
    for trigger in triggers:
        key, value = trigger.split(":", 1)
        if key.endswith("_gte"):
            field_name = key[:-4]
            threshold = int(value) if value.isdigit() else float(value)
            actual = metadata.get(field_name, 0)
            if actual >= threshold:
                reasons.append(f"{field_name}={actual} >= {threshold}")
        elif key.endswith("_lt"):
            field_name = key[:-3]
            threshold = int(value) if value.isdigit() else float(value)
            actual = metadata.get(field_name, 0)
            if actual < threshold:
                reasons.append(f"{field_name}={actual} < {threshold}")
        else:
            # Boolean flag check
            actual = metadata.get(key, False)
            expected = value.lower() == "true"
            if actual == expected:
                reasons.append(f"{key}={actual}")
    return len(reasons) > 0, reasons


def _check_downgrade_triggers(conditions: dict, metadata: dict) -> tuple[bool, list[str]]:
    """Check if ALL downgrade conditions are met. Returns (triggered, reasons).

    Numeric comparisons (_lt, _gte) only trigger when the field is explicitly
    present in metadata — absent fields do not count as meeting the condition.
    """
    if not conditions:
        return False, []
    reasons = []
    for key, value in conditions.items():
        if key.endswith("_lt"):
            field_name = key[:-3]
            if field_name not in metadata:
                return False, []  # Field not provided — can't confirm condition
            actual = metadata[field_name]
            if actual < value:
                reasons.append(f"{field_name}={actual} < {value}")
            else:
                return False, []
        elif key.endswith("_gte"):
            field_name = key[:-4]
            if field_name not in metadata:
                return False, []
            actual = metadata[field_name]
            if actual >= value:
                reasons.append(f"{field_name}={actual} >= {value}")
            else:
                return False, []
        else:
            actual = metadata.get(key, False)
            if actual == value:
                reasons.append(f"{key}={actual}")
            else:
                return False, []
    return True, reasons


def _estimate_cost(model: str, metadata: dict) -> float:
    """Estimate cost for this task based on model pricing and metadata."""
    pricing = PRICING.get(model, {"input": 1.0, "output": 5.0})

    # Image generation
    if "per_image" in pricing:
        num_images = metadata.get("num_images", 1)
        return pricing["per_image"] * num_images

    # Audio transcription
    if "per_minute" in pricing:
        minutes = metadata.get("audio_minutes", 10)
        return pricing["per_minute"] * minutes

    # TTS
    if "per_char" in pricing:
        chars = metadata.get("target_words", 1000) * 5  # ~5 chars per word
        return pricing["per_char"] * chars

    # Text models: estimate based on target output + input context
    target_words = metadata.get("target_words", 1000)
    # Rough: 1 word ≈ 1.3 tokens
    est_output_tokens = target_words * 1.3
    # Input typically 2-5x output for analytical work
    est_input_tokens = est_output_tokens * 3

    cost = (est_input_tokens / 1_000_000 * pricing["input"] +
            est_output_tokens / 1_000_000 * pricing["output"])
    return round(cost, 4)


def _build_fallback_chain(model: str, provider: str) -> list[str]:
    """Build fallback chain excluding the primary model."""
    chain = FALLBACK_CHAINS.get(provider, [])
    return [m for m in chain if m != model]


def _log_decision(decision: GatingDecision) -> None:
    """Append routing decision to log file."""
    ROUTING_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = asdict(decision)
    with open(ROUTING_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def route(
    task_type: str,
    metadata: Optional[dict] = None,
    budget_tolerance: str = "standard",
) -> GatingDecision:
    """
    Select appropriate model for task.

    Args:
        task_type: One of the TASK_RULES keys
        metadata: Task-specific context (target_words, scenarios, etc.)
        budget_tolerance: "tight" | "standard" | "premium"

    Returns:
        GatingDecision with model, provider, cost estimate, and justification.
    """
    if metadata is None:
        metadata = {}

    rule = TASK_RULES.get(task_type)
    if rule is None:
        # Unknown task type: default to V4 Pro as safe middle ground
        model = "deepseek/deepseek-v4-pro"
        return GatingDecision(
            model=model,
            provider=MODEL_PROVIDER[model],
            estimated_cost_usd=_estimate_cost(model, metadata),
            fallback_chain=_build_fallback_chain(model, MODEL_PROVIDER[model]),
            justification=f"Unknown task_type '{task_type}' — defaulting to V4 Pro",
            complexity_signals=metadata,
            task_type=task_type,
            budget_tolerance=budget_tolerance,
            quality_gates=[],
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

    model = rule["default"]
    justification_parts = [f"Default for {task_type}: {model}"]

    # Check escalation triggers
    escalate_triggers = rule.get("escalate_if_any", [])
    escalate_to = rule.get("escalate_to")
    if escalate_to and escalate_triggers:
        triggered, reasons = _check_escalation_triggers(escalate_triggers, metadata)
        if triggered:
            model = escalate_to
            justification_parts.append(f"Escalated to {model}: {', '.join(reasons)}")

    # Check downgrade triggers (only if we haven't escalated)
    if model == rule["default"]:
        downgrade_conditions = rule.get("downgrade_if", {})
        downgrade_to = rule.get("downgrade_to")
        if downgrade_to and downgrade_conditions:
            triggered, reasons = _check_downgrade_triggers(downgrade_conditions, metadata)
            if triggered:
                model = downgrade_to
                justification_parts.append(f"Downgraded to {model}: {', '.join(reasons)}")

    # Budget tolerance adjustments
    if budget_tolerance == "tight" and model in (
        "anthropic/claude-opus-4.7",
        "anthropic/claude-sonnet-4.5",
    ):
        # Downgrade frontier models when budget is tight
        downgrade_to = rule.get("downgrade_to")
        if downgrade_to:
            model = downgrade_to
            justification_parts.append(f"Budget-tight downgrade to {model}")
        elif model == "anthropic/claude-opus-4.7":
            model = "deepseek/deepseek-v4-pro"
            justification_parts.append(f"Budget-tight downgrade to {model}")

    provider = MODEL_PROVIDER.get(model, "openrouter")
    estimated_cost = _estimate_cost(model, metadata)
    fallback_chain = _build_fallback_chain(model, provider)

    decision = GatingDecision(
        model=model,
        provider=provider,
        estimated_cost_usd=estimated_cost,
        fallback_chain=fallback_chain,
        justification=" | ".join(justification_parts),
        complexity_signals=metadata,
        task_type=task_type,
        budget_tolerance=budget_tolerance,
        quality_gates=rule.get("quality_gates", []),
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )

    _log_decision(decision)
    return decision


def get_task_types() -> list[str]:
    """Return all known task types."""
    return sorted(TASK_RULES.keys())


def get_pricing() -> dict:
    """Return current pricing table."""
    return dict(PRICING)


# ── CLI interface ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 analyst/llm_gate.py <task_type> [key=value ...]")
        print(f"\nAvailable task types: {', '.join(get_task_types())}")
        sys.exit(1)

    task = sys.argv[1]
    meta = {}
    for arg in sys.argv[2:]:
        if "=" in arg:
            k, v = arg.split("=", 1)
            # Try to parse as number or bool
            if v.lower() in ("true", "false"):
                meta[k] = v.lower() == "true"
            else:
                try:
                    meta[k] = int(v)
                except ValueError:
                    try:
                        meta[k] = float(v)
                    except ValueError:
                        meta[k] = v

    d = route(task, meta)
    print(f"Model:     {d.model}")
    print(f"Provider:  {d.provider}")
    print(f"Est. cost: ${d.estimated_cost_usd:.4f}")
    print(f"Fallback:  {d.fallback_chain}")
    print(f"Reason:    {d.justification}")
    print(f"Gates:     {d.quality_gates}")
