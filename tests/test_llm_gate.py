# GATE_EXEMPT: Test file — references model strings for testing routing logic. Does not make API calls.
#!/usr/bin/env python3
"""Tests for analyst/llm_gate.py — LLM routing decision system.

50 representative tasks with expected routing, cost projection accuracy,
fallback chain verification, and budget cap enforcement.
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyst.llm_gate import route, GatingDecision, TASK_RULES, PRICING, get_task_types
from analyst.cost_ledger import CostLedger, BudgetExceededError


def test_basic_routing():
    """Test that each task type routes to its default model."""
    results = []
    for task_type, rule in TASK_RULES.items():
        d = route(task_type, {})
        expected = rule["default"]
        ok = d.model == expected
        results.append((task_type, expected, d.model, ok))
        if not ok:
            print(f"  FAIL: {task_type} expected {expected}, got {d.model}")
    passed = sum(1 for _, _, _, ok in results if ok)
    print(f"[basic_routing] {passed}/{len(results)} passed")
    return all(ok for _, _, _, ok in results)


def test_escalation_triggers():
    """Test escalation triggers fire correctly."""
    cases = [
        # (task_type, metadata, expected_model, description)
        ("subscriber_brief", {"target_words": 4000}, "anthropic/claude-opus-4.7",
         "subscriber_brief escalates on target_words >= 3000"),
        ("subscriber_brief", {"scenarios": 5}, "anthropic/claude-opus-4.7",
         "subscriber_brief escalates on scenarios >= 3"),
        ("subscriber_brief", {"flagship_tag": True}, "anthropic/claude-opus-4.7",
         "subscriber_brief escalates on flagship_tag"),
        ("subscriber_brief", {"principal_handback": True}, "anthropic/claude-opus-4.7",
         "subscriber_brief escalates on principal_handback"),
        ("daily_ingestion", {"complexity_high": True}, "deepseek/deepseek-v4-pro",
         "daily_ingestion escalates on complexity_high"),
        ("daily_ingestion", {"critical_source": True}, "deepseek/deepseek-v4-pro",
         "daily_ingestion escalates on critical_source"),
        ("entity_deepening", {"critical_entity": True}, "anthropic/claude-opus-4.7",
         "entity_deepening escalates on critical_entity"),
        ("entity_deepening", {"target_words": 4000}, "anthropic/claude-opus-4.7",
         "entity_deepening escalates on target_words >= 3000"),
        ("translation", {"formal_document": True}, "deepseek/deepseek-v4-pro",
         "translation escalates on formal_document"),
        ("calibration_review", {"high_stakes": True}, "anthropic/claude-opus-4.7",
         "calibration_review escalates on high_stakes"),
        ("scope_classifier", {"slow_path": True}, "deepseek/deepseek-v4-pro",
         "scope_classifier escalates on slow_path"),
        ("section_generation", {"final_coherence_pass": True}, "anthropic/claude-opus-4.7",
         "section_generation escalates on final_coherence_pass"),
        ("cross_source_correlation", {"sources": 6}, "anthropic/claude-opus-4.7",
         "cross_source_correlation escalates on sources >= 5"),
    ]
    passed = 0
    for task_type, metadata, expected, desc in cases:
        d = route(task_type, metadata)
        ok = d.model == expected
        if ok:
            passed += 1
        else:
            print(f"  FAIL: {desc} — expected {expected}, got {d.model}")
    print(f"[escalation_triggers] {passed}/{len(cases)} passed")
    return passed == len(cases)


def test_downgrade_triggers():
    """Test downgrade triggers fire correctly (all conditions must be met)."""
    cases = [
        ("subscriber_brief", {"target_words": 800, "routine": True}, "deepseek/deepseek-v4-flash",
         "subscriber_brief downgrades on short + routine"),
        ("subscriber_brief", {"target_words": 800, "routine": False}, "deepseek/deepseek-v4-pro",
         "subscriber_brief does NOT downgrade if routine=False"),
        ("subscriber_brief", {"target_words": 2000, "routine": True}, "deepseek/deepseek-v4-pro",
         "subscriber_brief does NOT downgrade if words >= 1500"),
        ("entity_deepening", {"routine": True}, "deepseek/deepseek-v4-flash",
         "entity_deepening downgrades on routine"),
        ("flagship_document", {"target_words": 1000, "routine": True}, "anthropic/claude-sonnet-4.5",
         "flagship_document downgrades on short + routine"),
        ("section_generation", {"routine": True, "target_words": 300}, "deepseek/deepseek-v4-pro",
         "section_generation downgrades on routine + short"),
    ]
    passed = 0
    for task_type, metadata, expected, desc in cases:
        d = route(task_type, metadata)
        ok = d.model == expected
        if ok:
            passed += 1
        else:
            print(f"  FAIL: {desc} — expected {expected}, got {d.model}")
    print(f"[downgrade_triggers] {passed}/{len(cases)} passed")
    return passed == len(cases)


def test_budget_tolerance():
    """Test budget tolerance adjustments."""
    # Tight budget should downgrade frontier models
    d = route("flagship_document", {"target_words": 5000}, budget_tolerance="tight")
    ok1 = d.model != "anthropic/claude-opus-4.7"
    if not ok1:
        print(f"  FAIL: tight budget should downgrade flagship_document from Opus")

    # Standard budget should keep default
    d2 = route("flagship_document", {"target_words": 5000}, budget_tolerance="standard")
    ok2 = d2.model == "anthropic/claude-opus-4.7"
    if not ok2:
        print(f"  FAIL: standard budget should keep flagship_document at Opus")

    passed = sum([ok1, ok2])
    print(f"[budget_tolerance] {passed}/2 passed")
    return passed == 2


def test_unknown_task_type():
    """Test that unknown task types default to V4 Pro."""
    d = route("nonexistent_task_xyz", {"target_words": 1000})
    ok = d.model == "deepseek/deepseek-v4-pro"
    print(f"[unknown_task_type] {'PASS' if ok else 'FAIL'}")
    return ok


def test_cost_estimation():
    """Test cost estimation produces reasonable values."""
    cases = [
        ("daily_ingestion", {"target_words": 500}, 0.0001, 1.00),
        ("flagship_document", {"target_words": 5000}, 0.01, 5.00),
        ("subscriber_brief", {"target_words": 2000}, 0.001, 2.00),
        ("source_classification", {"target_words": 200}, 0.0001, 0.50),
    ]
    passed = 0
    for task_type, metadata, min_cost, max_cost in cases:
        d = route(task_type, metadata)
        ok = min_cost <= d.estimated_cost_usd <= max_cost
        if ok:
            passed += 1
        else:
            print(f"  FAIL: {task_type} cost ${d.estimated_cost_usd:.4f} not in [{min_cost}, {max_cost}]")
    print(f"[cost_estimation] {passed}/{len(cases)} passed")
    return passed == len(cases)


def test_fallback_chains():
    """Test fallback chains are built correctly."""
    cases = [
        ("flagship_document", {}, ["anthropic/claude-sonnet-4.5", "deepseek/deepseek-v4-pro", "deepseek/deepseek-v4-flash"]),
        ("daily_ingestion", {}, ["anthropic/claude-sonnet-4.5"]),
        ("audio_generation", {}, []),
    ]
    passed = 0
    for task_type, metadata, expected_chain in cases:
        d = route(task_type, metadata)
        ok = d.fallback_chain == expected_chain
        if ok:
            passed += 1
        else:
            print(f"  FAIL: {task_type} fallback {d.fallback_chain} != {expected_chain}")
    print(f"[fallback_chains] {passed}/{len(cases)} passed")
    return passed == len(cases)


def test_decision_has_justification():
    """Test every routing decision includes a justification."""
    passed = 0
    total = 0
    for task_type in get_task_types():
        d = route(task_type, {})
        total += 1
        if d.justification and len(d.justification) > 5:
            passed += 1
        else:
            print(f"  FAIL: {task_type} has no justification")
    print(f"[justification] {passed}/{total} passed")
    return passed == total


def test_quality_gates_present():
    """Test quality gates are correctly assigned."""
    cases = [
        ("flagship_document", ["scope_check", "fabrication_check", "themes_preflight", "completeness"]),
        ("subscriber_brief", ["scope_check", "fabrication_check", "themes_preflight"]),
        ("red_team_analysis", ["scope_check", "fabrication_check"]),
        ("daily_ingestion", ["scope_check"]),
        ("source_classification", []),
    ]
    passed = 0
    for task_type, expected_gates in cases:
        d = route(task_type, {})
        ok = d.quality_gates == expected_gates
        if ok:
            passed += 1
        else:
            print(f"  FAIL: {task_type} gates {d.quality_gates} != {expected_gates}")
    print(f"[quality_gates] {passed}/{len(cases)} passed")
    return passed == len(cases)


def test_all_task_types_have_rules():
    """Test every task type in the spec has a routing rule."""
    required = [
        "flagship_document", "subscriber_brief", "daily_ingestion",
        "entity_deepening", "source_classification", "translation",
        "calibration_review", "postdiction_analysis", "red_team_analysis",
        "framework_refinement", "source_brainstorm", "cross_source_correlation",
        "scope_classifier", "topic_onboarding_strategic", "topic_onboarding_tactical",
        "topic_onboarding_operational", "image_analysis", "image_generation",
        "audio_transcription", "audio_generation", "status_report",
        "skill_discovery", "forum_synthesis", "capability_gap_review",
        "custom_skill_proposal", "section_generation",
    ]
    passed = 0
    for t in required:
        if t in TASK_RULES:
            passed += 1
        else:
            print(f"  FAIL: missing rule for {t}")
    print(f"[task_type_coverage] {passed}/{len(required)} passed")
    return passed == len(required)


def test_routing_log():
    """Test routing decisions are logged to JSONL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test-routing-log.jsonl"
        # Monkey-patch the log path
        import analyst.llm_gate as gate
        original = gate.ROUTING_LOG
        gate.ROUTING_LOG = log_path

        try:
            route("daily_ingestion", {"target_words": 500})
            route("subscriber_brief", {"target_words": 2000})

            assert log_path.exists(), "Routing log not created"
            lines = log_path.read_text().strip().split("\n")
            assert len(lines) == 2, f"Expected 2 log entries, got {len(lines)}"

            entry = json.loads(lines[0])
            assert "model" in entry
            assert "provider" in entry
            assert "estimated_cost_usd" in entry
            assert "justification" in entry
            print("[routing_log] PASS")
            return True
        except AssertionError as e:
            print(f"[routing_log] FAIL: {e}")
            return False
        finally:
            gate.ROUTING_LOG = original


def test_cost_ledger_basic():
    """Test cost ledger records and queries correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "test-ledger.jsonl"
        budget_path = Path(tmpdir) / "test-budget.yaml"
        budget_path.write_text("daily_cap: 10.00\nmonthly_cap: 50.00\nalert_threshold: 0.80\n")

        ledger = CostLedger(ledger_path=ledger_path, budget_path=budget_path)

        ledger.record("daily_ingestion", "deepseek/deepseek-v4-flash", 0.05)
        ledger.record("subscriber_brief", "deepseek/deepseek-v4-pro", 0.50)

        daily = ledger.daily_spend()
        ok1 = abs(daily - 0.55) < 0.001
        if not ok1:
            print(f"  FAIL: daily spend {daily} != 0.55")

        monthly = ledger.monthly_spend()
        ok2 = abs(monthly - 0.55) < 0.001
        if not ok2:
            print(f"  FAIL: monthly spend {monthly} != 0.55")

        # Test budget check passes
        try:
            status = ledger.check_budget()
            ok3 = status["ok"]
            if not ok3:
                print(f"  FAIL: budget check should be ok")
        except BudgetExceededError:
            ok3 = False
            print("  FAIL: budget check raised error unexpectedly")

        passed = sum([ok1, ok2, ok3])
        print(f"[cost_ledger_basic] {passed}/3 passed")
        return passed == 3


def test_cost_ledger_budget_exceeded():
    """Test budget enforcement halts on cap exceeded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "test-ledger.jsonl"
        budget_path = Path(tmpdir) / "test-budget.yaml"
        budget_path.write_text("daily_cap: 1.00\nmonthly_cap: 5.00\nalert_threshold: 0.80\n")

        ledger = CostLedger(ledger_path=ledger_path, budget_path=budget_path)

        # Exceed daily cap
        ledger.record("flagship_document", "anthropic/claude-opus-4.7", 1.50)

        try:
            ledger.check_budget()
            print("[budget_exceeded] FAIL: should have raised BudgetExceededError")
            return False
        except BudgetExceededError:
            print("[budget_exceeded] PASS")
            return True


def test_cost_projection():
    """Test cost projection accuracy."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "test-ledger.jsonl"
        budget_path = Path(tmpdir) / "test-budget.yaml"
        budget_path.write_text("daily_cap: 20.00\nmonthly_cap: 200.00\n")

        ledger = CostLedger(ledger_path=ledger_path, budget_path=budget_path)
        ledger.record("daily_ingestion", "deepseek/deepseek-v4-flash", 5.00)

        proj = ledger.projection(3.00)
        ok1 = abs(proj["daily_after"] - 8.00) < 0.001
        ok2 = proj["ok"]
        ok3 = abs(proj["daily_remaining_after"] - 12.00) < 0.001

        passed = sum([ok1, ok2, ok3])
        print(f"[cost_projection] {passed}/3 passed")
        return passed == 3


def test_specialist_routing():
    """Test specialist models route correctly."""
    cases = [
        ("image_analysis", {}, "anthropic/claude-vision"),
        ("image_generation", {}, "nanobanana/image-gen"),
        ("audio_transcription", {}, "openai/whisper-large-v3"),
        ("audio_generation", {}, "elevenlabs/tts"),
    ]
    passed = 0
    for task_type, metadata, expected in cases:
        d = route(task_type, metadata)
        ok = d.model == expected
        if ok:
            passed += 1
        else:
            print(f"  FAIL: {task_type} expected {expected}, got {d.model}")
    print(f"[specialist_routing] {passed}/{len(cases)} passed")
    return passed == len(cases)


def test_self_improvement_routing():
    """Test self-improvement task types route to appropriate models."""
    cases = [
        ("skill_discovery", {}, "anthropic/claude-opus-4.7"),
        ("forum_synthesis", {}, "anthropic/claude-opus-4.7"),
        ("capability_gap_review", {}, "deepseek/deepseek-v4-pro"),
        ("custom_skill_proposal", {}, "anthropic/claude-opus-4.7"),
    ]
    passed = 0
    for task_type, metadata, expected in cases:
        d = route(task_type, metadata)
        ok = d.model == expected
        if ok:
            passed += 1
        else:
            print(f"  FAIL: {task_type} expected {expected}, got {d.model}")
    print(f"[self_improvement_routing] {passed}/{len(cases)} passed")
    return passed == len(cases)


def test_topic_onboarding_routing():
    """Test topic onboarding phases route to correct tiers."""
    cases = [
        ("topic_onboarding_strategic", {}, "anthropic/claude-opus-4.7"),
        ("topic_onboarding_tactical", {}, "deepseek/deepseek-v4-pro"),
        ("topic_onboarding_operational", {}, "deepseek/deepseek-v4-flash"),
    ]
    passed = 0
    for task_type, metadata, expected in cases:
        d = route(task_type, metadata)
        ok = d.model == expected
        if ok:
            passed += 1
        else:
            print(f"  FAIL: {task_type} expected {expected}, got {d.model}")
    print(f"[topic_onboarding_routing] {passed}/{len(cases)} passed")
    return passed == len(cases)


def run_all():
    """Run all tests and report results."""
    print("=" * 60)
    print("Trevor v2 — LLM Gate Routing Tests")
    print("=" * 60)

    tests = [
        test_basic_routing,
        test_escalation_triggers,
        test_downgrade_triggers,
        test_budget_tolerance,
        test_unknown_task_type,
        test_cost_estimation,
        test_fallback_chains,
        test_decision_has_justification,
        test_quality_gates_present,
        test_all_task_types_have_rules,
        test_routing_log,
        test_cost_ledger_basic,
        test_cost_ledger_budget_exceeded,
        test_cost_projection,
        test_specialist_routing,
        test_self_improvement_routing,
        test_topic_onboarding_routing,
    ]

    results = []
    for test_fn in tests:
        try:
            results.append(test_fn())
        except Exception as e:
            print(f"[{test_fn.__name__}] ERROR: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"TOTAL: {passed}/{total} test groups passed")
    if passed == total:
        print("ALL TESTS PASSED")
    else:
        print(f"FAILURES: {total - passed} test groups failed")
    print("=" * 60)
    return passed == total


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
