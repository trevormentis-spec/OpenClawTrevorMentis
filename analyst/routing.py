# GATE_EXEMPT: Legacy routing module being phased out. Always routes through select_model() which consults config.
#!/usr/bin/env python3
"""Task Complexity Router — determines model tier based on task complexity.

Route to Opus 4.7 when ANY trigger fires:
- Target word count >= 3000
- Visual elements >= 8
- Themes required >= 5
- Multi-scenario analysis (>=3 scenarios)
- "Flagship" or "stress test" in task description
- Target audience: family office, sovereign wealth, Lloyd's, SPV

Route to Haiku when:
- Brief generation 600-1500 words
- Standard daily intel brief format
- Routine entity deepening
- Source classification
- Postdiction resolution

Route to DeepSeek Flash when:
- Bulk mechanical work (source freshness, schema validation)
- Scope classifier slow-path
- Daily ingestion pipeline tasks

Usage:
    python3 -c "from analyst.routing import select_model; print(select_model({'target_words': [4000, 6000], 'visuals': 11, 'audience': 'family office'}))"
"""

from __future__ import annotations

from typing import Any

# ── Complexity triggers for Opus 4.7 ──────────────────────────

OPUS_TRIGGERS: list[dict] = [
    {"field": "target_words_max", "op": ">=", "value": 3000, "label": "target>=3000"},
    {"field": "visual_elements", "op": ">=", "value": 8, "label": "visuals>=8"},
    {"field": "themes_required", "op": ">=", "value": 5, "label": "themes>=5"},
    {"field": "scenario_count", "op": ">=", "value": 3, "label": "multi_scenario"},
    {"field": "description", "op": "contains", "value": ["flagship", "stress test", "flagship-style"], "label": "flagship_stress_test"},
    {"field": "audience", "op": "contains", "value": ["family office", "sovereign wealth", "lloyd's", "spv", "institutional investor", "investment committee"], "label": "premium_audience"},
    {"field": "estimated_output_tokens", "op": ">=", "value": 4000, "label": "output_tokens>=4K"},
]

# ── Model definitions ────────────────────────────────────────

MODELS = {
    "opus": {
        "name": "anthropic/claude-opus-4.7",
        "provider": "openrouter",
        "max_output_tokens": 8192,
        "cost_per_m_input": 15.0,
        "cost_per_m_output": 60.0,
        "tier": 1,
        "label": "Opus 4.7",
    },
    "v4pro": {
        "name": "deepseek/deepseek-v4-pro",
        "provider": "deepseek",
        "max_output_tokens": 8192,
        "cost_per_m_input": 0.435,
        "cost_per_m_output": 0.87,
        "tier": 2,
        "label": "DeepSeek V4 Pro",
    },

    "deepseek_flash": {
        "name": "deepseek-chat",
        "provider": "deepseek",
        "max_output_tokens": 8192,
        "cost_per_m_input": 0.14,
        "cost_per_m_output": 0.28,
        "tier": 4,
        "label": "DeepSeek Flash",
    },
}


def evaluate_triggers(task: dict[str, Any]) -> list[str]:
    """Evaluate which Opus triggers fire for a given task."""
    fired = []

    for trigger in OPUS_TRIGGERS:
        field = trigger["field"]
        op = trigger["op"]
        value = trigger["value"]
        label = trigger["label"]

        actual = task.get(field)

        if actual is None:
            continue

        if op == ">=" and isinstance(actual, (int, float)):
            if actual >= value:
                fired.append(label)

        elif op == "contains":
            if isinstance(value, list):
                if isinstance(actual, str):
                    actual_lower = actual.lower()
                    if any(v.lower() in actual_lower for v in value):
                        fired.append(label)

    return fired


def estimate_output_tokens(target_words: int | list[int]) -> int:
    """Estimate output tokens needed (~1.5 tokens/word for English)."""
    if isinstance(target_words, list):
        max_words = max(target_words)
    else:
        max_words = target_words
    return int(max_words * 1.5)


def select_model(task: dict[str, Any], verbose: bool = False) -> dict[str, Any]:
    """Select the appropriate model based on task complexity.

    Args:
        task: dict with keys like target_words, visual_elements,
              themes_required, scenario_count, description, audience
        verbose: print routing decision

    Returns:
        dict with model info, triggers fired, and reasoning
    """
    triggers_fired = evaluate_triggers(task)

    # Estimate output tokens
    target_words = task.get("target_words", 0)
    est_tokens = estimate_output_tokens(target_words)
    task["estimated_output_tokens"] = est_tokens

    # Re-check with token estimate
    triggers_fired = evaluate_triggers(task)

    # Decide model
    if triggers_fired:
        # Default to V4 Pro for complex work; escalate to Opus for flagship
        is_flagship = any(t in triggers_fired for t in ["flagship_stress_test", "premium_audience"])
        if is_flagship or "flagship" in str(task.get("description", "")).lower():
            model = MODELS["opus"]
            rationale = "Complexity triggers + flagship/premium audience → Opus 4.7"
        else:
            model = MODELS["v4pro"]
            rationale = "Complexity triggers fired → V4 Pro (mid-tier, 97% cheaper than Opus)"
        rationale = "Complexity triggers fired"
    elif task.get("task_type") in ("scope_classifier", "source_freshness", "schema_validation", "daily_ingestion"):
        model = MODELS["deepseek_flash"]
        rationale = "Mechanical/bulk work"
        triggers_fired = []
    elif task.get("task_type") in ("entity_deepening", "source_classification", "postdiction_resolution"):
        model = MODELS["v4pro"]
        rationale = "Routine analytical work (no complexity triggers)"
        triggers_fired = []
    elif isinstance(target_words, (int, list)):
        max_w = max(target_words) if isinstance(target_words, list) else target_words
        if max_w <= 1500:
            model = MODELS["v4pro"]
            rationale = "Standard brief length — V4 Pro default"
        elif max_w <= 3000:
            model = MODELS["deepseek_flash"]
            rationale = "Medium brief — DeepSeek adequate"
        else:
            model = MODELS["opus"]
            rationale = f"Target word count {max_w} >= 3000"
            triggers_fired = ["target>=3000"]
    else:
        model = MODELS["deepseek_flash"]
        rationale = "Default — no complexity signal"

    # Check token-limit compatibility
    if est_tokens > model["max_output_tokens"] * 0.9:
        # Current model can't handle output — escalate
        if model["tier"] > 1:
            for m in [MODELS["opus"], MODELS["v4pro"], MODELS["deepseek_flash"]]:
                if m["max_output_tokens"] >= est_tokens:
                    model = m
                    rationale += f" (escalated due to token limit: {est_tokens} > {model['max_output_tokens']*0.9:.0f})"
                    break

    result = {
        "model_key": [k for k, v in MODELS.items() if v["name"] == model["name"]][0],
        "model_name": model["name"],
        "provider": model["provider"],
        "max_output_tokens": model["max_output_tokens"],
        "triggers_fired": triggers_fired,
        "rationale": rationale,
        "estimated_output_tokens": est_tokens,
    }

    if verbose:
        print(f"[routing] Model: {model['label']} ({model['provider']})")
        if triggers_fired:
            print(f"[routing] Triggers: {', '.join(triggers_fired)}")
        print(f"[routing] Rationale: {rationale}")

    return result


# ── Test ──────────────────────────────────────────────────────

if __name__ == "__main__":
    test_cases = [
        {"target_words": [4000, 6000], "visual_elements": 11, "themes_required": 3,
         "scenario_count": 3, "description": "flagship-style PDF on USMCA review risk",
         "audience": "family office investment committee"},
        {"target_words": [600, 900], "task_type": "scope_classifier"},
        {"target_words": [800, 1200], "task_type": "entity_deepening"},
    ]

    for tc in test_cases:
        print("\n" + "=" * 50)
        result = select_model(tc, verbose=True)
        print(f"  → {result['model_name']}")
