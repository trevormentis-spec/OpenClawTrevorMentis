#!/usr/bin/env python3
"""Tests for topic onboarding and domain-general scope framework.

Tests:
- Onboard 3 distinct topics
- Verify config files generated correctly
- Verify scope_check fires correctly per topic
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyst.topic_onboarding import onboard_topic, list_topics, slugify, TopicConfig
from analyst.scope_check import check_scope, load_scope, build_decline, build_adjacency_preamble


def test_slugify():
    """Test slug generation."""
    cases = [
        ("Brazil fiscal policy", "brazil-fiscal-policy"),
        ("Semiconductor Supply Chain 2027", "semiconductor-supply-chain-2027"),
        ("Company XYZ (NYSE: XYZ)", "company-xyz-nyse-xyz"),
        ("  Multiple   Spaces  ", "multiple-spaces"),
    ]
    passed = 0
    for name, expected in cases:
        result = slugify(name)
        ok = result == expected
        if ok:
            passed += 1
        else:
            print(f"  FAIL: slugify('{name}') = '{result}', expected '{expected}'")
    print(f"[slugify] {passed}/{len(cases)} passed")
    return passed == len(cases)


def test_onboard_semiconductor():
    """Test onboarding: semiconductor supply chain."""
    config = onboard_topic(
        name="Semiconductor Supply Chain",
        description="Global semiconductor supply chain dynamics, CHIPS Act impact, China-Taiwan tensions, foundry capacity",
        time_horizon="through end of 2027",
        themes=[
            {"name": "foundry_capacity", "description": "TSMC, Samsung, Intel fab capacity and utilization", "priority": "high"},
            {"name": "us_china_tech_war", "description": "Export controls, entity lists, technology decoupling", "priority": "high"},
            {"name": "demand_cycle", "description": "AI chip demand, automotive, consumer electronics", "priority": "medium"},
            {"name": "supply_chain_resilience", "description": "Geographic concentration risk, reshoring, friend-shoring", "priority": "medium"},
        ],
        sources=[
            {"name": "SIA Reports", "url": "https://www.semiconductors.org", "type": "industry_body", "reliability": "A", "credibility": "2"},
            {"name": "TrendForce", "url": "https://www.trendforce.com", "type": "market_research", "reliability": "B", "credibility": "2"},
        ],
        entities=[
            {"name": "TSMC", "type": "company", "importance": "critical", "aliases": ["Taiwan Semiconductor"]},
            {"name": "NVIDIA", "type": "company", "importance": "high", "aliases": ["NVDA"]},
            {"name": "Morris Chang", "type": "person", "importance": "high", "aliases": []},
        ],
    )

    topic_dir = Path(__file__).resolve().parent.parent / "config" / "topics" / config.slug

    checks = []

    # Check directory created
    checks.append(("dir_exists", topic_dir.exists()))

    # Check all config files
    expected_files = ["topic.yaml", "themes.yaml", "sources.yaml", "entities.yaml",
                      "calibration.json", "routing-overrides.yaml", "branding.yaml"]
    for f in expected_files:
        checks.append((f"file_{f}", (topic_dir / f).exists()))

    # Check topic.yaml content
    topic_text = (topic_dir / "topic.yaml").read_text()
    checks.append(("topic_has_slug", "semiconductor-supply-chain" in topic_text))
    checks.append(("topic_has_scope", "Semiconductor Supply Chain" in topic_text))

    # Check themes.yaml
    themes_text = (topic_dir / "themes.yaml").read_text()
    checks.append(("themes_has_foundry", "foundry_capacity" in themes_text))
    checks.append(("themes_has_techwar", "us_china_tech_war" in themes_text))

    # Check calibration.json
    cal = json.loads((topic_dir / "calibration.json").read_text())
    checks.append(("cal_has_bands", "calibration_bands" in cal))
    checks.append(("cal_has_8_bands", len(cal["calibration_bands"]) == 8))

    # Check config object
    checks.append(("config_name", config.name == "Semiconductor Supply Chain"))
    checks.append(("config_themes", len(config.themes) == 4))
    checks.append(("config_sources", len(config.sources) == 2))
    checks.append(("config_entities", len(config.entities) == 3))

    passed = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        if not ok:
            print(f"  FAIL: {name}")
    print(f"[onboard_semiconductor] {passed}/{len(checks)} passed")
    return passed == len(checks)


def test_onboard_brazil():
    """Test onboarding: Brazil fiscal policy."""
    config = onboard_topic(
        name="Brazil fiscal policy through end of 2027",
        description="Brazilian fiscal consolidation, spending caps, debt trajectory, Lula administration fiscal stance",
        time_horizon="through end of 2027",
        themes=[
            {"name": "fiscal_framework", "description": "Spending cap evolution, primary surplus targets", "priority": "high"},
            {"name": "debt_trajectory", "description": "Gross debt/GDP path, market confidence", "priority": "high"},
            {"name": "political_economy", "description": "Lula coalition dynamics, election cycle spending", "priority": "medium"},
        ],
        sources=[
            {"name": "BCB Reports", "url": "https://www.bcb.gov.br", "type": "central_bank", "reliability": "A", "credibility": "1"},
        ],
        entities=[
            {"name": "Lula", "type": "person", "importance": "critical", "aliases": ["Luiz Inacio Lula da Silva"]},
            {"name": "Fernando Haddad", "type": "person", "importance": "high", "aliases": ["Haddad"]},
        ],
    )

    topic_dir = Path(__file__).resolve().parent.parent / "config" / "topics" / config.slug
    checks = [
        ("dir_exists", topic_dir.exists()),
        ("topic_yaml", (topic_dir / "topic.yaml").exists()),
        ("themes_yaml", (topic_dir / "themes.yaml").exists()),
        ("config_name", "brazil" in config.slug),
        ("config_themes", len(config.themes) == 3),
    ]

    passed = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        if not ok:
            print(f"  FAIL: {name}")
    print(f"[onboard_brazil] {passed}/{len(checks)} passed")
    return passed == len(checks)


def test_onboard_company():
    """Test onboarding: specific company analysis."""
    config = onboard_topic(
        name="Company XYZ Deep Dive",
        description="Comprehensive analysis of Company XYZ competitive position, financial health, regulatory exposure",
        themes=[
            {"name": "competitive_position", "description": "Market share, moat analysis, competitor threats", "priority": "high"},
            {"name": "financial_health", "description": "Balance sheet, cash flow, capital allocation", "priority": "high"},
        ],
    )

    topic_dir = Path(__file__).resolve().parent.parent / "config" / "topics" / config.slug
    checks = [
        ("dir_exists", topic_dir.exists()),
        ("slug_valid", config.slug == "company-xyz-deep-dive"),
        ("calibration_exists", (topic_dir / "calibration.json").exists()),
    ]

    passed = sum(1 for _, ok in checks if ok)
    for name, ok in checks:
        if not ok:
            print(f"  FAIL: {name}")
    print(f"[onboard_company] {passed}/{len(checks)} passed")
    return passed == len(checks)


def test_list_topics():
    """Test listing onboarded topics."""
    topics = list_topics()
    expected = {"brazil-fiscal-policy-through-end-of-2027", "company-xyz-deep-dive", "semiconductor-supply-chain"}
    found = set(topics) & expected
    ok = found == expected
    if not ok:
        print(f"  FAIL: expected {expected}, found {found} in {topics}")
    print(f"[list_topics] {'PASS' if ok else 'FAIL'}")
    return ok


def test_scope_check_general():
    """Test scope_check works with general (no topic) config."""
    # With no active assignment, everything should be in_scope
    result = check_scope("What is happening with TSMC earnings?")
    ok = result["scope_status"] == "in_scope"
    if not ok:
        print(f"  FAIL: expected in_scope, got {result['scope_status']}")
    print(f"[scope_check_general] {'PASS' if ok else 'FAIL'}")
    return ok


def test_scope_check_topic_specific():
    """Test scope_check reads from topic config when specified."""
    # Create a topic with specific keywords
    config = onboard_topic(
        name="Test Scope Topic",
        description="Testing scope boundaries",
        themes=[],
    )

    # Write in-scope keywords to the topic config
    topic_dir = Path(__file__).resolve().parent.parent / "config" / "topics" / config.slug
    topic_yaml = topic_dir / "topic.yaml"
    content = topic_yaml.read_text()
    content += "\nin_scope_keywords:\n  - semiconductor\n  - chips\n"
    content += "\nblocklist:\n  - football\n  - nfl\n"
    topic_yaml.write_text(content)

    # Test in-scope keyword
    result = check_scope("TSMC semiconductor fab update", topic_slug=config.slug)
    ok1 = result["scope_status"] == "in_scope"
    if not ok1:
        print(f"  FAIL: 'semiconductor' should be in_scope, got {result['scope_status']}")

    # Test blocklist keyword
    result2 = check_scope("NFL football draft picks", topic_slug=config.slug)
    ok2 = result2["scope_status"] == "out_of_scope"
    if not ok2:
        print(f"  FAIL: 'football' should be out_of_scope, got {result2['scope_status']}")

    passed = sum([ok1, ok2])
    print(f"[scope_check_topic_specific] {passed}/2 passed")

    # Cleanup test topic
    shutil.rmtree(topic_dir, ignore_errors=True)
    return passed == 2


def test_decline_builder_general():
    """Test decline builder with topic-general config."""
    config = {"primary_scope": "semiconductor analysis", "scope_description": "global chip supply chain"}
    scope_result = {"scope_status": "out_of_scope", "topic_vectors": []}
    decline = build_decline("NFL draft picks", scope_result, config)
    ok1 = "semiconductor analysis" in decline
    ok2 = "NFL draft" in decline

    passed = sum([ok1, ok2])
    print(f"[decline_builder_general] {passed}/2 passed")
    return passed == 2


def test_adjacency_preamble_general():
    """Test adjacency preamble with topic-general config."""
    config = {"primary_scope": "Brazil fiscal policy"}
    scope_result = {"scope_status": "adjacent", "topic_vectors": ["USD/BRL: capital flows"]}
    preamble = build_adjacency_preamble("Fed rate decision", scope_result, config)
    ok1 = "Brazil fiscal policy" in preamble
    ok2 = "Vector 1" in preamble

    passed = sum([ok1, ok2])
    print(f"[adjacency_preamble_general] {passed}/2 passed")
    return passed == 2


def run_all():
    """Run all topic onboarding tests."""
    print("=" * 60)
    print("Trevor v2 — Topic Onboarding & Scope Tests")
    print("=" * 60)

    tests = [
        test_slugify,
        test_onboard_semiconductor,
        test_onboard_brazil,
        test_onboard_company,
        test_list_topics,
        test_scope_check_general,
        test_scope_check_topic_specific,
        test_decline_builder_general,
        test_adjacency_preamble_general,
    ]

    results = []
    for test_fn in tests:
        try:
            results.append(test_fn())
        except Exception as e:
            print(f"[{test_fn.__name__}] ERROR: {e}")
            import traceback
            traceback.print_exc()
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
