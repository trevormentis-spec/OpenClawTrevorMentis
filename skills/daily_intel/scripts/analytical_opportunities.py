#!/usr/bin/env python3
"""
analytical_opportunities.py — Strategic opportunity & product discovery engine.

Runs during every daily intelligence cycle AFTER assessment generation and
narrative tracking but BEFORE final publication.

Purpose:
- Identify emerging analytical opportunities
- Identify strategic blind spots
- Identify forecastable structures
- Identify new intelligence products worth producing
- Function as an intelligence editor, strategic warning cell, and product discovery engine

Output: cron_tracking/analytical_opportunities.json (consumed by improvement_daemon for final report)
"""
from __future__ import annotations

import datetime
import json
import os
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from trevor_config import THEATRE_KEYS as THEATRES, WORKSPACE
from trevor_log import get_logger
from trevor_memory import MemoryStore

log = get_logger("analytical_opportunities")

ASSESS_DIR = SKILL_ROOT / 'assessments'
CRON_DIR = SKILL_ROOT / 'cron_tracking'
ENRICHMENT_FILE = CRON_DIR / 'enrichment_report.json'
NARRATIVE_FILE = CRON_DIR / 'narrative_landscape.json'
PRIORITY_FILE = CRON_DIR / 'state.json'
OUTPUT_FILE = CRON_DIR / 'analytical_opportunities.json'

# ── Product type taxonomy ──
PRODUCT_TYPES = [
    "strategic_warning", "forecasting_product", "monitoring_dashboard",
    "longitudinal_study", "risk_framework", "scenario_tree",
    "escalation_tracker", "leadership_profile", "market_thesis",
    "investigative_line", "intelligence_product", "warning_report",
    "indicator_framework", "strategic_model", "geopolitical_tracker",
]


def load_assessment(region: str) -> str:
    """Load a theatre assessment file."""
    path = ASSESS_DIR / f"{region}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def extract_key_judgments(text: str) -> list[str]:
    """Extract key judgment statements from assessment text."""
    kjs = []
    for line in text.split('\n'):
        if re.match(r'^\d+\.', line.strip()) and any(w in line.lower()
            for w in ['likely', 'unlikely', 'confiden', 'assess', 'expect', 'will', 'may']):
            kjs.append(line.strip()[:200])
    return kjs[:5]


def detect_leadership_escalation_structures(text: str) -> list[str]:
    """Detect leadership dynamics and escalation structures in text."""
    signals = []
    patterns = {
        "leadership_instability": ["resign", "purge", "oust", "coup", "succession", "power struggle"],
        "escalation_language": ["escalate", "retaliate", "ultimatum", "red line", "casus belli", "no choice"],
        "alliance_stress": ["friction", "disagreement", "split", "divergence", "breach", "strain"],
        "military_readiness": ["mobilize", "deploy", "exercise", "readiness", "alert", "posture"],
        "economic_warfare": ["sanction", "tariff", "embargo", "freeze", "block", "restrict"],
    }
    text_lower = text.lower()
    for category, keywords in patterns.items():
        found = [kw for kw in keywords if kw in text_lower]
        if found:
            signals.append(f"{category}: {', '.join(found)}")
    return signals


def detect_cross_theatre_relationships() -> list[dict]:
    """Identify relationships and connections between theatres."""
    relationships = []
    theatre_texts = {}
    for region in THEATRES:
        text = load_assessment(region)
        theatre_texts[region] = text

    # Check for shared keywords indicating cross-theatre dynamics
    cross_themes = {
        "iran_oil": ["iran", "oil", "brent", "hormuz", "sanctions"],
        "russia_china": ["russia", "china", "xi", "putin", "beijing", "moscow"],
        "us_presence": ["united states", "washington", "pentagon", "us forces", "centcom"],
        "energy_crisis": ["energy", "fuel", "gas", "electricity", "shortage", "price spike"],
        "supply_chains": ["supply chain", "semiconductor", "rare earth", "critical mineral"],
    }

    for theme, keywords in cross_themes.items():
        affected = []
        for region, text in theatre_texts.items():
            if any(kw in text.lower() for kw in keywords):
                affected.append(region)
        if len(affected) >= 2:
            relationships.append({
                "theme": theme,
                "theatres": affected,
                "count": len(affected),
                "potential": "cross_theatre_analysis",
            })

    return relationships


def detect_narrative_regime_shifts() -> list[str]:
    """Check narrative_landscape.json for regime shifts."""
    shifts = []
    if NARRATIVE_FILE.exists():
        try:
            data = json.loads(NARRATIVE_FILE.read_text())
            for drift in data.get("drifts", []):
                if drift.get("status") == "regime_shift":
                    shifts.append(f"Regime shift in {drift['region']}")
                elif drift.get("status") == "identical":
                    shifts.append(f"Stagnant narrative in {drift['region']} — may indicate analytical gap")
        except Exception:
            pass
    return shifts


def detect_prediction_market_repricing() -> list[str]:
    """Detect significant prediction market movements from Kalshi scan."""
    signals = []
    today = datetime.date.today().strftime("%Y-%m-%d")
    kalshi_dir = WORKSPACE / 'exports'
    for f in sorted(kalshi_dir.glob("kalshi-scan-*.md"), reverse=True)[:3]:
        if not f.exists():
            continue
        try:
            text = f.read_text()
            # Look for high-volume, high-movement markets
            for line in text.split('\n'):
                parts = line.strip().split()
                if len(parts) >= 8 and parts[0].startswith('KX'):
                    try:
                        yes_bid = float(parts[1].replace('$', ''))
                        volume = int(float(parts[6].replace(',', '')))
                        if volume > 500_000 and yes_bid > 0.3:
                            expiry = parts[7] if len(parts) > 7 else "?"
                            signals.append(
                                f"High-volume market {parts[0]}: ${yes_bid:.2f} YES, "
                                f"${volume:,} volume, expires {expiry}"
                            )
                    except (ValueError, IndexError):
                        pass
        except Exception:
            pass
    return signals[:5]


def detect_intelligence_gaps() -> list[str]:
    """Identify recurring intelligence gaps from assessment content."""
    gaps = []
    for region in THEATRES:
        text = load_assessment(region)
        gap_indicators = [
            "insufficient", "unclear", "unknown", "cannot assess",
            "no data", "limited visibility", "single source",
            "uncorroborated", "not confirmed", "unable to determine",
        ]
        mentions = []
        text_lower = text.lower()
        for indicator in gap_indicators:
            if indicator in text_lower:
                mentions.append(indicator)
        if mentions:
            gaps.append(f"{region}: {', '.join(set(mentions))}")

    return gaps


def generate_analytical_opportunities() -> dict:
    """Main analysis: produce structured analytical opportunities report."""
    log.info("Scanning for analytical opportunities")

    opportunities = []
    product_concepts = []
    cross_theatre = detect_cross_theatre_relationships()
    regime_shifts = detect_narrative_regime_shifts()
    market_repricing = detect_prediction_market_repricing()
    intel_gaps = detect_intelligence_gaps()
    escalation_structures = {}

    for region in THEATRES:
        text = load_assessment(region)
        if not text:
            continue
        kjs = extract_key_judgments(text)
        escalation = detect_leadership_escalation_structures(text)
        escalation_structures[region] = escalation

        # Determine intelligence value and urgency
        intel_volatility = len(kjs) * 15 + min(len(escalation) * 25, 50)
        intel_value = min(intel_volatility + 20, 95)
        urgency = min(intel_volatility + 10, 90)

        # Check for specific analytical opportunities
        opportunities.append({
            "region": region,
            "key_judgment_count": len(kjs),
            "escalation_signals": len(escalation),
            "intel_gaps": any(region in g for g in intel_gaps),
            "estimated_value": intel_value,
            "estimated_urgency": urgency,
            "confidence": min(60 + len(kjs) * 5, 90),
        })

    # Product concepts (cross-theatre, strategic)
    if cross_theatre:
        for rel in cross_theatre:
            product_concepts.append({
                "name": f"Cross-theatre monitor: {rel['theme']}",
                "type": "monitoring_dashboard",
                "rationale": f"Affects {rel['count']} theatres ({', '.join(rel['theatres'])}). "
                            "Cross-theatre dynamics are analytically underserved.",
                "emergence": "Inter-theatre dependencies increasing as crisis complexity grows.",
                "strategic_question": f"How does {rel['theme']} connect across theatres?",
                "methodology": "Comparative narrative tracking + cross-correlation of key indicators.",
                "value": 85,
                "difficulty": "medium",
                "urgency": "medium",
            })

    if market_repricing:
        for signal in market_repricing[:2]:
            product_concepts.append({
                "name": f"Prediction market pulse: {signal[:60]}",
                "type": "market_thesis",
                "rationale": f"Significant repricing detected: {signal}",
                "emergence": "Active prediction-market repricing indicates shifting expectations.",
                "strategic_question": "What information is the market pricing that assessments have not yet captured?",
                "methodology": "Cross-reference market repricing with narrative shifts.",
                "value": 75,
                "difficulty": "low",
                "urgency": "high",
            })

    if intel_gaps:
        for gap in intel_gaps[:3]:
            product_concepts.append({
                "name": f"Intelligence gap monitor: {gap.split(':')[0]}",
                "type": "warning_report",
                "rationale": f"Recurring intelligence gap: {gap}",
                "emergence": "Persistent gaps indicate structural collection deficiency.",
                "strategic_question": "Why do these gaps persist and what alternative sources exist?",
                "methodology": "Source reliability tracking + gap persistence analysis.",
                "value": 70,
                "difficulty": "medium",
                "urgency": "high",
            })

    # New product concepts (longitudinal, strategic, novel)
    new_concepts = [
        {
            "name": "Escalation Ladder Monitor",
            "type": "escalation_tracker",
            "rationale": "Multiple theatres show escalation language. A structured escalation tracking "
                        "framework across all theatres would provide early warning of escalation cascades.",
            "emergence": "Concurrent crisis across Hormuz, Ukraine, Taiwan, Lebanon.",
            "strategic_question": "Are escalation dynamics correlated across theatres?",
            "forecasting_edge": "Cross-theatre view not available to single-theatre analysts.",
            "methodology": "Structured escalation stages (1-10) per theatre, updated daily with trigger events.",
            "value": 90,
            "difficulty": "medium",
            "urgency": "high",
            "confidence": 75,
        },
        {
            "name": "Narrative Regime-Change Detector",
            "type": "strategic_model",
            "rationale": "Narrative regime shifts are early indicators of strategic change. "
                        "A detector that flags when narratives restructure would provide strategic warning.",
            "emergence": "Narrative tracking infrastructure now exists (narrative_engine.py). "
                        "Cross-edition comparison is operational.",
            "strategic_question": "When does a narrative evolution become a regime shift?",
            "forecasting_edge": "Structural narrative analysis across 7 theatres with FTS5 persistence.",
            "methodology": "Fingerprint comparison across editions + header structure analysis.",
            "value": 85,
            "difficulty": "low",
            "urgency": "medium",
            "confidence": 80,
        },
        {
            "name": "Prediction Market vs Assessment Divergence Report",
            "type": "forecasting_product",
            "rationale": "When prediction markets disagree with TREVOR's assessments, "
                        "it signals either market inefficiency or analytical blind spot.",
            "emergence": "Both Kalshi integration and assessment generation are operational. "
                        "Divergence detection is now possible.",
            "strategic_question": "Where is TREVOR's assessment diverging from market pricing?",
            "forecasting_edge": "Direct comparison of estimative probability vs market-implied probability.",
            "methodology": "Systematic comparison of key judgment probability ranges with prediction market prices.",
            "value": 88,
            "difficulty": "medium",
            "urgency": "medium",
            "confidence": 70,
        },
        {
            "name": "Geopolitical Risk Heatmap",
            "type": "monitoring_dashboard",
            "rationale": "A visual risk heatmap across all 7 theatres would provide "
                        "executive-level strategic awareness at a glance.",
            "emergence": "Priority scoring infrastructure exists. Narrative engine provides drift data.",
            "strategic_question": "Where is risk accumulating across the global security environment?",
            "forecasting_edge": "Structured risk assessment across all theatres simultaneously.",
            "methodology": "Aggregate priority scores, narrative volatility, escalation signals, "
                        "and intel gaps into a weighted risk score per theatre.",
            "value": 82,
            "difficulty": "low",
            "urgency": "medium",
            "confidence": 85,
        },
        {
            "name": "Forecast Track Record & Calibration Dashboard",
            "type": "longitudinal_study",
            "rationale": "Trevor produces probabilistic key judgments but has never audited "
                        "its own forecast accuracy. A calibration dashboard would enable "
                        "continuous improvement.",
            "emergence": "Briefometer infrastructure exists. Brier score collection is operational.",
            "strategic_question": "How accurate is TREVOR's estimative analysis over time?",
            "forecasting_edge": "Direct insight into own performance — rare in intelligence analysis.",
            "methodology": "Daily Brier score logging + calibration curve analysis + over/under-confidence detection.",
            "value": 78,
            "difficulty": "low",
            "urgency": "medium",
            "confidence": 90,
        },
    ]
    product_concepts.extend(new_concepts)

    # Build report
    report = {
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pipeline_date": datetime.date.today().isoformat(),
        "summary": {
            "cross_theatre_relationships": len(cross_theatre),
            "narrative_regime_shifts": len(regime_shifts),
            "prediction_market_repricing_signals": len(market_repricing),
            "intelligence_gaps_detected": len(intel_gaps),
            "analytical_opportunities": len(opportunities),
            "new_product_concepts": len(product_concepts),
        },
        "analytical_opportunities": opportunities,
        "new_product_concepts": product_concepts,
        "cross_theatre_relationships": cross_theatre,
        "narrative_regime_shifts": regime_shifts,
        "prediction_market_signals": market_repricing,
        "intelligence_gaps": intel_gaps,
        "escalation_structures": escalation_structures,
    }

    # Save
    CRON_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(report, indent=2))
    log.info("Analytical opportunities report generated",
             opportunities=len(opportunities),
             product_concepts=len(product_concepts),
             regime_shifts=len(regime_shifts))

    return report


def print_report(report: dict):
    """Print a human-readable summary."""
    s = report.get("summary", {})
    print(f"\n{'='*60}")
    print(f"STRATEGIC OPPORTUNITY & PRODUCT DISCOVERY")
    print(f"{'='*60}")
    print(f"\nSummary:")
    print(f"  Cross-theatre relationships: {s.get('cross_theatre_relationships', 0)}")
    print(f"  Narrative regime shifts: {s.get('narrative_regime_shifts', 0)}")
    print(f"  Prediction market repricing signals: {s.get('prediction_market_repricing_signals', 0)}")
    print(f"  Intelligence gaps: {s.get('intelligence_gaps_detected', 0)}")
    print(f"  Analytical opportunities: {s.get('analytical_opportunities', 0)}")
    print(f"  New product concepts: {s.get('new_product_concepts', 0)}")

    concepts = report.get("new_product_concepts", [])
    if concepts:
        print(f"\n{'─'*60}")
        print(f"RECOMMENDED NEW PRODUCTS")
        print(f"{'─'*60}")
        for product in sorted(concepts, key=lambda x: x.get("value", 0), reverse=True):
            print(f"\n  🔷 {product['name']} [{product['type']}]")
            print(f"     Value: {product['value']}/100 | Difficulty: {product['difficulty']} | Urgency: {product['urgency']}")
            print(f"     {product['rationale'][:120]}")

    intel_gaps = report.get("intelligence_gaps", [])
    if intel_gaps:
        print(f"\n{'─'*60}")
        print(f"INTELLIGENCE GAPS")
        print(f"{'─'*60}")
        for gap in intel_gaps[:5]:
            print(f"  ⚠️  {gap}")

    escalation = report.get("escalation_structures", {})
    active_escalation = {k: v for k, v in escalation.items() if v}
    if active_escalation:
        print(f"\n{'─'*60}")
        print(f"ESCALATION SIGNALS")
        print(f"{'─'*60}")
        for region, signals in active_escalation.items():
            for s in signals[:2]:
                print(f"  🔴 {region}: {s}")

    print(f"\n{'='*60}\n")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    report = generate_analytical_opportunities()

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
