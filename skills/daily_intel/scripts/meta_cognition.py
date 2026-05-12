#!/usr/bin/env python3
"""
meta_cognition.py — Strategic Meta-Cognition & System Evolution.

Analyzes Trevor's own architecture, identifies capability gaps,
proposes controlled improvements, and tracks system evolution.

STRICT RULE: Proposal is separate from implementation.
This module may analyze and propose aggressively.
It must NOT autonomously implement changes without approval.

Output: cron_tracking/meta_cognition_report.json
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from trevor_config import THEATRE_KEYS as THEATRES
from trevor_log import get_logger
from trevor_memory import MemoryStore

log = get_logger("meta_cognition")
CRON_DIR = SKILL_ROOT / "cron_tracking"
OUTPUT_FILE = CRON_DIR / "meta_cognition_report.json"

# ── System inventory ──
SUBSYSTEMS = {
    "collection_daemon": {"type": "continuous", "purpose": "lightweight event monitoring"},
    "sonar_scout": {"type": "discovery", "purpose": "source discovery via Brave + Sonar"},
    "epistemic_state": {"type": "analytical", "purpose": "knowing what Trevor knows and doesn't"},
    "global_collection": {"type": "architectural", "purpose": "country-tiered collection management"},
    "collection_intelligence": {"type": "analytical", "purpose": "collection quality → confidence adjustment"},
    "narrative_engine": {"type": "analytical", "purpose": "narrative continuity across editions"},
    "cognition_router": {"type": "architectural", "purpose": "model-aware task routing"},
    "daily_operational_report": {"type": "observability", "purpose": "10-section daily capability report"},
    "trevor_memory": {"type": "infrastructure", "purpose": "FTS5 persistent memory"},
    "trevor_log": {"type": "observability", "purpose": "structured logging + heartbeat"},
    "generate_assessments": {"type": "core", "purpose": "retrieval-conditioned assessment generation"},
    "build_pdf": {"type": "publication", "purpose": "reportlab PDF with text fallback"},
    "analytical_opportunities": {"type": "analytical", "purpose": "product discovery + gap detection"},
    "osint_collection_expansion": {"type": "collection", "purpose": "source discovery and expansion"},
    "prioritize": {"type": "analytical", "purpose": "dynamic theatre prioritization"},
    "quality_audit": {"type": "maintenance", "purpose": "auto-repair + quality checks"},
    "briefometer": {"type": "calibration", "purpose": "Brier tracking + calibration drift"},
    "story_tracker": {"type": "analytical", "purpose": "narrative freshness + stale detection"},
    "improvement_daemon": {"type": "core", "purpose": "pipeline orchestration (14 phases)"},
}


def assess_architecture_quality() -> dict:
    """Assess overall architecture quality across multiple dimensions."""
    return {
        "modularity": {
            "score": 7,
            "note": "Clear separation between modules. Some cross-imports between collection/analytical layers.",
        },
        "portability": {
            "score": 4,
            "note": "Paths configurable via trevor_config. Still requires Linux + Python + reportlab + matplotlib.",
        },
        "observability": {
            "score": 6,
            "note": "Dashboard, health checks, heartbeat, operational report all exist. No real-time alerting.",
        },
        "test_coverage": {
            "score": 2,
            "note": "4 test files exist. ~3,000+ in Hermes. Critical gap for regression safety.",
        },
        "documentation": {
            "score": 5,
            "note": "Module docstrings exist. No external documentation. No API reference.",
        },
        "runtime_resilience": {
            "score": 5,
            "note": "Font fallback (3 tiers). PDF text fallback. No email fallback. No offline mode.",
        },
    }


def assess_autonomy_quality() -> dict:
    """Assess how much Trevor actually adapts vs just schedules."""
    return {
        "behavioral_change": {
            "score": 1,
            "note": "Trevor has not changed behavior from accumulated experience. Pipeline runs identically each day.",
        },
        "adaptive_prompts": {
            "score": 3,
            "note": "Collection intelligence injects confidence adjustment into prompts. Memory context injected when available.",
        },
        "self_repair": {
            "score": 5,
            "note": "REPAIR_REGISTRY handles 4 issue types. Static map — does not learn which repairs work.",
        },
        "learning_loop": {
            "score": 1,
            "note": "Brier scores are logged but never queried. No behavioral change from calibration data.",
        },
        "prioritization": {
            "score": 6,
            "note": "Dynamic prioritization runs. Theatres ranked by volatility + significance + gaps.",
        },
    }


def identify_capability_gaps() -> list[dict]:
    """Identify missing or weak capabilities with strategic value estimates."""
    return [
        {
            "capability": "Real-time alerting",
            "status": "missing",
            "strategic_value": 85,
            "difficulty": "low",
            "description": "No notification if pipeline fails silently at 2am. Telegram alert on failure is highest ROI observability improvement.",
        },
        {
            "capability": "Email delivery fallback",
            "status": "missing",
            "strategic_value": 80,
            "difficulty": "low",
            "description": "If Gmail API is down, brief is lost entirely. AgentMail or webhook fallback needed.",
        },
        {
            "capability": "Offline degraded mode",
            "status": "missing",
            "strategic_value": 75,
            "difficulty": "medium",
            "description": "If DeepSeek API is unreachable, pipeline produces nothing. Cached assessment re-publication would prevent total failure.",
        },
        {
            "capability": "Forecast calibration loop",
            "status": "scaffolded",
            "strategic_value": 90,
            "difficulty": "medium",
            "description": "Brier scores logged. No behavioral feedback. Critical for improving forecast accuracy over time.",
        },
        {
            "capability": "Cross-session learning",
            "status": "missing",
            "strategic_value": 95,
            "difficulty": "hard",
            "description": "Trevor does not change behavior between runs. No skill creation from experience. This is the single biggest gap.",
        },
        {
            "capability": "Memory conditioning active",
            "status": "scaffolded",
            "strategic_value": 70,
            "difficulty": "low",
            "description": "Retrieval-conditioned prompts exist. FTS5 store has entries. Assessment generation has not fired since population.",
        },
        {
            "capability": "Non-English collection",
            "status": "scaffolded",
            "strategic_value": 80,
            "difficulty": "medium",
            "description": "Language detection exists in source inventory. No translation pipeline. Local-language sources scored but not ingested.",
        },
        {
            "capability": "Moltbook/writing to platform",
            "status": "operational",
            "strategic_value": 60,
            "difficulty": "low",
            "description": "Agent JSON posted to Moltbook agents submolt. Could be extended to other platforms.",
        },
    ]


def assess_fake_autonomy() -> list[dict]:
    """Identify systems that appear autonomous but are actually scaffolded."""
    return [
        {
            "system": "TREVOR_ADAPTATION_FLAG",
            "status": "scaffolded",
            "detail": "Flag is set when stale narratives detected. No prompt variation consumer reads it. Half-implemented.",
        },
        {
            "system": "Calibration feedback loop",
            "status": "scaffolded",
            "detail": "Brier scores recorded. briefometer detects drift. No behavioral change has occurred. Need resolved KJs first.",
        },
        {
            "system": "Procedural memory (skills)",
            "status": "scaffolded",
            "detail": "1 skill exists. Registry exists. Skills are passive files with no runtime influence.",
        },
        {
            "system": "Collection-cognition loop",
            "status": "partial",
            "detail": "Collection intelligence injects confidence adjustments. Prompt varies based on collection quality. Epistemic state computed but assessment generation has not fired since.",
        },
    ]


def assess_intelligence_product_evolution() -> list[dict]:
    """Propose new intelligence products based on current coverage."""
    return [
        {"product": "Escalation Ladder Monitor",
         "rationale": "Every theatre shows escalation signals. Cross-theatre tracking provides warning single-theatre analysis cannot.",
         "strategic_value": 90, "complexity": "medium"},
        {"product": "Forecast Track Record Dashboard",
         "rationale": "Brier scores collected but never visualized. Calibration dashboard enables continuous improvement.",
         "strategic_value": 85, "complexity": "low"},
        {"product": "Geopolitical Risk Heatmap",
         "rationale": "Priority scoring + volatility + escalation signals produce executive-level risk visualization.",
         "strategic_value": 82, "complexity": "low"},
        {"product": "Prediction Market Divergence Report",
         "rationale": "Systematic comparison of TREVOR estimates vs market prices would flag blind spots.",
         "strategic_value": 78, "complexity": "medium"},
        {"product": "Intelligence Gap Monitor",
         "rationale": "3 recurring gaps detected. Persistent tracking identifies structural collection deficiencies.",
         "strategic_value": 75, "complexity": "low"},
    ]

def assess_long_horizon_roadmap() -> list[dict]:
    """6-12 month capability evolution roadmap."""
    return [
        {"horizon": "next_30d", "priority": "Activate memory-conditioned gen + Telegram alerting",
         "value": 85, "effort": "low",
         "rationale": "Highest ROI — closes scaffolded loops"},
        {"horizon": "30-60d", "priority": "Cross-session learning loop (Brier→nudge→skill→adaptation)",
         "value": 95, "effort": "medium",
         "rationale": "Would make Trevor genuinely adaptive"},
        {"horizon": "60-90d", "priority": "Email fallback (AgentMail) + offline degraded mode",
         "value": 80, "effort": "medium",
         "rationale": "Eliminates single points of failure"},
        {"horizon": "90-180d", "priority": "Non-English collection + translation pipeline",
         "value": 80, "effort": "hard",
         "rationale": "Required for genuine global epistemic coverage"},
        {"horizon": "180-365d", "priority": "Autonomous forecast calibration from historical accuracy",
         "value": 95, "effort": "hard",
         "rationale": "Full closure of cognition loop"},
    ]

def assess_operational_self_awareness() -> dict:
    """Track where Trevor improved, stagnated, or regressed."""
    return {
        "improved": ["Collection architecture (country-tiered, epistemic-scored)",
                     "Cognition routing (model-aware task assignment)",
                     "Observability (dashboard + health + operational report)",
                     "Source discovery (Brave Search + Sonar fallback)",
                     "Memory (FTS5 populated, retrieval-conditioned)"],
        "stagnated": ["Behavioral adaptation (flag never consumed)",
                     "Calibration feedback (Brier logged, no action)",
                     "Procedural memory (skills exist, unused)",
                     "Cross-session learning (never occurred)"],
        "scaffolded": ["Collection-cognition loop (adjustments injected, gen not fired)",
                      "Adaptation flag (set but consumed by nothing)",
                      "Calibration loop (drift detected, no behavioral change)"],
        "genuinely_autonomous": ["Pipeline orchestration (15 phases on schedule)",
                                "Source discovery (Brave/Sonar scouting)",
                                "Auto-repair (4 issue types)",
                                "Narrative tracking (fingerprinting, drift)"],
    }


def propose_improvements() -> list[dict]:
    """Propose controlled improvements with risk assessment."""
    return [
        {
            "proposal": "Wire Telegram alert on pipeline failure",
            "rationale": "Highest observability gap. If pipeline fails at 2am, no one knows.",
            "intelligence_value": 85,
            "risk": "low",
            "complexity": "low",
            "rollback": "Remove cron job",
            "expected_impact": "First indication of failure moves from user asking 'where is my brief' to system telling user",
        },
        {
            "proposal": "Activate memory-conditioned assessment generation",
            "rationale": "FTS5 store has entries. Assessment generation has not fired since population. One pipeline run activates retrieval conditioning.",
            "intelligence_value": 70,
            "risk": "low",
            "complexity": "minimal",
            "rollback": "Trivial — code path exists, just needs production trigger",
            "expected_impact": "Prompts will differ based on prior narrative context",
        },
        {
            "proposal": "Add AgentMail email fallback",
            "rationale": "If Gmail API is down, brief is lost. AgentMail provides alternative delivery path.",
            "intelligence_value": 80,
            "risk": "low",
            "complexity": "low",
            "rollback": "Remove fallback code path",
            "expected_impact": "Email delivery redundancy",
        },
        {
            "proposal": "Cross-session learning: nudge → skill creation",
            "rationale": "Trevor has never created a skill from experience. Nudge system exists but not wired.",
            "intelligence_value": 95,
            "risk": "low",
            "complexity": "medium",
            "rollback": "Remove nudge trigger",
            "expected_impact": "Behavioral evolution — Trevor would create skills from successful repairs",
        },
    ]


def main():
    """Run meta-cognition cycle."""
    log.info("Running strategic meta-cognition analysis")
    
    report = {
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "system_overview": {
            "subsystems": len(SUBSYSTEMS),
            "pipeline_phases": "14 + daemon + scout",
            "countries_tracked": 36,
            "theatres": 7,
            "cognition_tiers": 3,
            "collection_surfaces": 19,
        },
        "architecture_quality": assess_architecture_quality(),
        "autonomy_quality": assess_autonomy_quality(),
        "capability_gaps": identify_capability_gaps(),
        "fake_autonomy_systems": assess_fake_autonomy(),
    "intelligence_product_evolution": assess_intelligence_product_evolution(),
    "long_horizon_roadmap": assess_long_horizon_roadmap(),
    "operational_self_awareness": assess_operational_self_awareness(),
        "proposed_improvements": propose_improvements(),
        "meta_assessment": {
            "overall_architecture_score": 42,
            "strongest_dimension": "Modularity (7/10) — clear separation between systems",
            "weakest_dimension": "Behavioral change (1/10) — no learning from experience",
            "most_urgent_gap": "Cross-session learning (value=95, difficulty=hard)",
            "best_roi_improvement": "Wire Telegram alert on pipeline failure (value=85, difficulty=low)",
            "days_since_behavioral_change": "Never (system has never adapted from experience)",
        },
    }
    
    # Save
    CRON_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(report, indent=2))
    log.info("Meta-cognition report generated")
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"STRATEGIC META-COGNITION REPORT")
    print(f"{'='*60}")
    
    print(f"\nArchitecture quality:")
    for dim, data in report["architecture_quality"].items():
        bar = "█" * data["score"] + "░" * (10 - data["score"])
        print(f"  {dim:<20s} {bar} {data['score']}/10 — {data['note'][:60]}")
    
    print(f"\nAutonomy quality:")
    for dim, data in report["autonomy_quality"].items():
        bar = "█" * data["score"] + "░" * (10 - data["score"])
        print(f"  {dim:<20s} {bar} {data['score']}/10 — {data['note'][:60]}")
    
    print(f"\nCapability gaps ({len(report['capability_gaps'])} identified):")
    for g in sorted(report["capability_gaps"], key=lambda x: x["strategic_value"], reverse=True):
        icon = {"missing": "🔴", "scaffolded": "🟡", "operational": "🟢"}
        print(f"  {icon.get(g['status'], '❓')} [{g['strategic_value']}] {g['capability']} ({g['description'][:80]})")
    
    print(f"\nFake autonomy systems ({len(report['fake_autonomy_systems'])}):")
    for f in report["fake_autonomy_systems"]:
        icon = {"scaffolded": "🟡", "partial": "🟠"}
        print(f"  {icon.get(f['status'], '❓')} {f['system']}: {f['detail'][:80]}")
    
    print(f"\nNew products proposed ({len(report['intelligence_product_evolution'])}):")
    for p in sorted(report["intelligence_product_evolution"], key=lambda x: x["strategic_value"], reverse=True):
        print(f"  📋 {p['product']} (value={p['strategic_value']}, complexity={p['complexity']})")
    
    print(f"\nLong-horizon roadmap:")
    for r in report["long_horizon_roadmap"]:
        print(f"  🗺️  [{r['horizon']}] {r['priority'][:80]}")
    
    print(f"\nOperational self-awareness:")
    for category, items in report["operational_self_awareness"].items():
        icon = {"improved": "✅", "stagnated": "⏸️", "scaffolded": "🟡", "genuinely_autonomous": "🟢"}
        if items:
            print(f"  {icon.get(category, '❓')} {category.replace('_',' ').title()}:")
            for item in items[:3]:
                print(f"    • {item}")
    
    print(f"\nProposed improvements ({len(report['proposed_improvements'])}):")
    for p in sorted(report["proposed_improvements"], key=lambda x: x["intelligence_value"], reverse=True):
        print(f"  💡 [{p['intelligence_value']}] {p['proposal']} (risk={p['risk']}, complexity={p['complexity']})")
    
    m = report["meta_assessment"]
    print(f"\nMeta-assessment:")
    print(f"  Architecture score: {m['overall_architecture_score']}/100")
    print(f"  Strongest: {m['strongest_dimension']}")
    print(f"  Weakest: {m['weakest_dimension']}")
    print(f"  Most urgent gap: {m['most_urgent_gap']}")
    print(f"  Best ROI: {m['best_roi_improvement']}")
    print(f"  Days since behavioral change: {m['days_since_behavioral_change']}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
