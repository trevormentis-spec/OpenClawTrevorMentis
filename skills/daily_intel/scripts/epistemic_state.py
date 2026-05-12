#!/usr/bin/env python3
"""
epistemic_state.py — Epistemic state management & deep global collection.

Manages what Trevor knows, how well it knows it, where it is blind,
and where collection quality directly shapes cognition.

Output: cron_tracking/epistemic_state.json
"""
from __future__ import annotations

import datetime
import json
import math
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from trevor_config import THEATRE_KEYS as THEATRES
from trevor_log import get_logger
from trevor_memory import MemoryStore

log = get_logger("epistemic_state")
CRON_DIR = SKILL_ROOT / "cron_tracking"
OUTPUT_FILE = CRON_DIR / "epistemic_state.json"
GLOBAL_FILE = CRON_DIR / "global_collection.json"
INVENTORY_FILE = CRON_DIR / "source_inventory.json"
INTEL_FILE = CRON_DIR / "collection_intelligence.json"

# ── Collection surface taxonomy ──
SURFACES = [
    "government_portal", "local_media", "procurement_system", "legal_gazette",
    "parliamentary_transcript", "customs_database", "shipping_data",
    "aviation_tracking", "energy_infrastructure", "telecom_monitor",
    "sanctions_registry", "defense_procurement", "trade_journal",
    "telegram_channel", "satellite_derived", "academic_source",
    "prediction_market", "think_tank", "official_document",
]

SURFACE_WEIGHTS = {
    "government_portal": 0.15, "procurement_system": 0.12, "sanctions_registry": 0.12,
    "defense_procurement": 0.12, "customs_database": 0.08, "local_media": 0.08,
    "telegram_channel": 0.06, "satellite_derived": 0.10, "parliamentary_transcript": 0.06,
    "shipping_data": 0.04, "aviation_tracking": 0.03, "energy_infrastructure": 0.06,
    "legal_gazette": 0.05, "telecom_monitor": 0.03, "think_tank": 0.03,
    "prediction_market": 0.05, "academic_source": 0.03, "official_document": 0.05,
    "trade_journal": 0.03,
}

# ── Epistemic tiers (how well we know each country) ──
EPISTEMIC_TIERS = {
    1: {"label": "Comprehensive", "color": "green", "min_surfaces": 12, "min_sources": 20, "min_high_value": 6, "min_local": 4},
    2: {"label": "Adequate", "color": "blue", "min_surfaces": 8, "min_sources": 12, "min_high_value": 3, "min_local": 2},
    3: {"label": "Partial", "color": "yellow", "min_surfaces": 4, "min_sources": 6, "min_high_value": 1, "min_local": 1},
    4: {"label": "Weak", "color": "orange", "min_surfaces": 2, "min_sources": 3, "min_high_value": 0, "min_local": 0},
    5: {"label": "Minimal", "color": "red", "min_surfaces": 0, "min_sources": 0, "min_high_value": 0, "min_local": 0},
}


def load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            return {}
    return {}


def compute_epistemic_profile(country_name: str, sources: list[dict]) -> dict:
    """Compute epistemic state for a single country."""
    country_sources = [s for s in sources if s.get("country", "").lower() == country_name]

    source_count = len(country_sources)
    surface_types = set(s.get("source_type", "") for s in country_sources)
    surface_count = len(surface_types)
    
    high_value_types = {"government_portal", "procurement_system", "sanctions_registry",
                       "defense_procurement", "customs_database", "parliamentary_transcript"}
    high_value = sum(1 for s in country_sources if s.get("source_type") in high_value_types)
    
    local_lang = sum(1 for s in country_sources if s.get("source_type") in ("local_media", "telegram_channel"))
    
    gov_portal = sum(1 for s in country_sources if s.get("source_type") == "government_portal")
    procurement = sum(1 for s in country_sources if s.get("source_type") == "procurement_system")
    customs = sum(1 for s in country_sources if s.get("source_type") == "customs_database")
    defense_proc = sum(1 for s in country_sources if s.get("source_type") == "defense_procurement")
    shipping = sum(1 for s in country_sources if s.get("source_type") == "shipping_data")
    satellite = sum(1 for s in country_sources if s.get("source_type") == "satellite_derived")
    
    # Determine epistemic tier
    tier = 5
    for t in sorted(EPISTEMIC_TIERS.keys(), reverse=True):
        targets = EPISTEMIC_TIERS[t]
        if (source_count >= targets["min_sources"] and surface_count >= targets["min_surfaces"]
            and high_value >= targets["min_high_value"]):
            tier = t
            break
    
    # Compute collection surface coverage
    surfaces = {}
    for surface in SURFACES:
        count = sum(1 for s in country_sources if s.get("source_type") == surface)
        has = count > 0
        weight = SURFACE_WEIGHTS.get(surface, 0.03)
        surfaces[surface] = {"has": has, "count": count, "weight": weight}
    
    coverage_weighted = sum(s["weight"] for s in surfaces.values() if s["has"])
    max_weight = sum(SURFACES.values()) if isinstance(SURFACES, set) else sum(SURFACE_WEIGHTS.values())
    coverage_score = round(coverage_weighted / max_weight * 100, 1) if max_weight > 0 else 0
    
    # Collection confidence
    density = min(1.0, source_count / 20)
    surface_diversity = min(1.0, surface_count / 12)
    high_value_density = min(1.0, high_value / 6)
    local_density = min(1.0, local_lang / 4)
    
    confidence = round(
        (density * 0.25 + surface_diversity * 0.25 +
         high_value_density * 0.30 + local_density * 0.20) * 100, 1
    )
    
    # Epistemic risk factors
    risks = []
    if confidence < 20:
        risks.append({"risk": "critically_underinformed", "detail": "Collection confidence below 20%"})
    if gov_portal == 0:
        risks.append({"risk": "no_government_visibility", "detail": "No government portal sources"})
    if procurement == 0:
        risks.append({"risk": "no_procurement_visibility", "detail": "No procurement system sources"})
    if customs == 0:
        risks.append({"risk": "no_trade_visibility", "detail": "No customs database sources"})
    if defense_proc == 0:
        risks.append({"risk": "no_defense_visibility", "detail": "No defense procurement sources"})
    if shipping == 0:
        risks.append({"risk": "no_shipping_visibility", "detail": "No shipping data sources"})
    if satellite == 0:
        risks.append({"risk": "no_satellite_visibility", "detail": "No satellite-derived sources"})
    if local_lang == 0:
        risks.append({"risk": "no_local_language", "detail": "No local-language sources"})
    
    return {
        "epistemic_tier": tier,
        "epistemic_label": EPISTEMIC_TIERS[tier]["label"],
        "collection_confidence": confidence,
        "coverage_score": coverage_score,
        "surfaces_covered": surface_count,
        "surfaces_total": len(SURFACES),
        "surfaces": surfaces,
        "total_sources": source_count,
        "high_value_sources": high_value,
        "local_language_sources": local_lang,
        "government_portals": gov_portal,
        "procurement_systems": procurement,
        "customs_databases": customs,
        "defense_procurement": defense_proc,
        "shipping_sources": shipping,
        "satellite_sources": satellite,
        "epistemic_risks": risks,
        "risk_count": len(risks),
    }


def build_epistemic_state() -> dict:
    """Build the full global epistemic state model."""
    inventory = load_json(INVENTORY_FILE).get("sources", [])
    global_coll = load_json(GLOBAL_FILE)
    country_profiles = global_coll.get("country_profiles", {})
    
    epistemic_states = {}
    for country_name in country_profiles:
        epistemic_states[country_name] = compute_epistemic_profile(country_name, inventory)
    
    return epistemic_states


def compute_global_epistemic_summary(states: dict) -> dict:
    """Compute global epistemic statistics."""
    tiers = {1: [], 2: [], 3: [], 4: [], 5: []}
    for name, state in states.items():
        t = state.get("epistemic_tier", 5)
        tiers[t].append(name)
    
    return {
        "comprehensive_knowledge": tiers[1],
        "adequate_knowledge": tiers[2],
        "partial_knowledge": tiers[3],
        "weak_knowledge": tiers[4],
        "minimal_knowledge": tiers[5],
        "countries_with_comprehensive_coverage": len(tiers[1]),
        "countries_with_critical_risks": sum(1 for s in states.values() if s.get("risk_count", 0) >= 4),
        "countries_with_no_government_visibility": sum(1 for s in states.values() if any(r["risk"] == "no_government_visibility" for r in s.get("epistemic_risks", []))),
        "countries_with_no_local_language": sum(1 for s in states.values() if any(r["risk"] == "no_local_language" for r in s.get("epistemic_risks", []))),
        "countries_with_no_defense_visibility": sum(1 for s in states.values() if any(r["risk"] == "no_defense_visibility" for r in s.get("epistemic_risks", []))),
        "countries_with_no_procurement_visibility": sum(1 for s in states.values() if any(r["risk"] == "no_procurement_visibility" for r in s.get("epistemic_risks", []))),
    }


def generate_epistemic_risk_assessment(states: dict, summary: dict) -> list[dict]:
    """Generate epistemic risk warnings."""
    warnings = []
    
    # Countries with critical risk count
    for name, state in states.items():
        if state.get("risk_count", 0) >= 5:
            warnings.append({
                "country": name,
                "epistemic_tier": state["epistemic_tier"],
                "confidence": state["collection_confidence"],
                "risks": state["risk_count"],
                "top_risks": [r["detail"] for r in state.get("epistemic_risks", [])[:4]],
                "warning": f"Epistemic state critically weak: {name} has {state['risk_count']} epistemic risks",
                "surfaces_covered": f"{state['surfaces_covered']}/{state['surfaces_total']}",
            })
    
    return sorted(warnings, key=lambda x: x.get("risks", 0), reverse=True)


def compute_confidence_adjustment(states: dict) -> dict:
    """Compute per-country confidence adjustment instructions for assessment generation."""
    adjustments = {}
    for name, state in states.items():
        tier = state.get("epistemic_tier", 5)
        confidence = state.get("collection_confidence", 0)
        
        if tier <= 2:
            adjust = {"band_adj": 0, "uncertainty": 10, "style": "standard", "note": ""}
        elif tier == 3:
            adjust = {"band_adj": -5, "uncertainty": 15, "style": "moderate", "note": "Partial epistemic coverage — apply moderate uncertainty."}
        elif tier == 4:
            adjust = {"band_adj": -10, "uncertainty": 25, "style": "conservative", "note": "Weak epistemic coverage — significant uncertainty. Flag collection limits."}
        else:
            adjust = {"band_adj": -20, "uncertainty": 40, "style": "highly_conservative", "note": "Minimal epistemic coverage — highly speculative. Avoid strong predictions."}
        
        adjustments[name] = adjust
    
    return adjustments


def main():
    """Run full epistemic state management cycle."""
    log.info("Building epistemic state model")
    
    epistemic_states = build_epistemic_state()
    summary = compute_global_epistemic_summary(epistemic_states)
    warnings = generate_epistemic_risk_assessment(epistemic_states, summary)
    adjustments = compute_confidence_adjustment(epistemic_states)
    
    report = {
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "countries_analyzed": len(epistemic_states),
        "epistemic_summary": summary,
        "epistemic_states": epistemic_states,
        "epistemic_risk_assessment": warnings[:15],
        "confidence_adjustments": adjustments,
    }
    
    CRON_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(report, indent=2))
    log.info("Epistemic state report saved",
             countries=len(epistemic_states),
             critical_risks=summary.get("countries_with_critical_risks", 0))
    
    # Print summary
    tier_counts = {}
    for s in epistemic_states.values():
        t = s.get("epistemic_tier", 5)
        tier_counts[EPISTEMIC_TIERS[t]["label"]] = tier_counts.get(EPISTEMIC_TIERS[t]["label"], 0) + 1
    
    print(f"\n{'='*60}")
    print(f"GLOBAL EPISTEMIC STATE REPORT")
    print(f"{'='*60}")
    print(f"\nCountries analyzed: {len(epistemic_states)}")
    print(f"Epistemic tier distribution:")
    for label in ["Comprehensive", "Adequate", "Partial", "Weak", "Minimal"]:
        count = tier_counts.get(label, 0)
        bar = "█" * count + "░" * (max(0, 10 - count))
        print(f"  {label:<20s} {bar} {count}")
    
    print(f"\nCritical epistemic risks:")
    print(f"  No government visibility:    {summary.get('countries_with_no_government_visibility', 0)} countries")
    print(f"  No local language sources:   {summary.get('countries_with_no_local_language', 0)} countries")
    print(f"  No defense visibility:       {summary.get('countries_with_no_defense_visibility', 0)} countries")
    print(f"  No procurement visibility:   {summary.get('countries_with_no_procurement_visibility', 0)} countries")
    
    if warnings:
        print(f"\nTop epistemic warnings:")
        for w in warnings[:5]:
            risks_str = ", ".join(w.get("top_risks", [])[:2])
            print(f"  🔴 {w['country']} (confidence={w['confidence']}%, {w['risks']} risks): {risks_str}")
    
    print(f"\nConfidence adjustments would affect {len(adjustments)} countries:")
    adj_tiers = {}
    for adj in adjustments.values():
        key = adj["style"]
        adj_tiers[key] = adj_tiers.get(key, 0) + 1
    for k, v in sorted(adj_tiers.items(), key=lambda x: x[1], reverse=True):
        print(f"  {k}: {v} countries")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
