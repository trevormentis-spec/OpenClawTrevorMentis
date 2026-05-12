#!/usr/bin/env python3
"""
global_collection.py — Global adaptive collection architecture.

Manages country-level intelligence structures, dynamic tiering, confidence
mapping, and adaptive collection depth for all sovereign states and strategic
territories.

Output: cron_tracking/global_collection.json
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

log = get_logger("global_collection")
CRON_DIR = SKILL_ROOT / "cron_tracking"
OUTPUT_FILE = CRON_DIR / "global_collection.json"
INVENTORY_FILE = CRON_DIR / "source_inventory.json"
COLLECTION_INTEL_FILE = CRON_DIR / "collection_intelligence.json"

# ── Complete country database (UN states + strategic territories) ──
COUNTRIES = {
    # Tier 1 — Critical Strategic Actors
    "china": {"tier": 1, "region": "asia", "population": 1400000000, "gdp_rank": 2,
              "military_spending_rank": 2, "nuclear_power": True},
    "russia": {"tier": 1, "region": "europe", "population": 144000000, "gdp_rank": 11,
               "military_spending_rank": 3, "nuclear_power": True},
    "united_states": {"tier": 1, "region": "north_america", "population": 331000000, "gdp_rank": 1,
                      "military_spending_rank": 1, "nuclear_power": True},
    "iran": {"tier": 1, "region": "middle_east", "population": 88000000, "gdp_rank": 40,
             "military_spending_rank": 14, "nuclear_power": True},
    "taiwan": {"tier": 1, "region": "asia", "population": 23000000, "gdp_rank": 21,
               "military_spending_rank": 21, "nuclear_power": False},
    "ukraine": {"tier": 1, "region": "europe", "population": 41000000, "gdp_rank": 56,
                "military_spending_rank": 8, "nuclear_power": False},
    # Tier 2 — Major Regional Powers
    "turkey": {"tier": 2, "region": "middle_east", "population": 85000000, "gdp_rank": 17,
               "military_spending_rank": 13, "nuclear_power": False},
    "saudi_arabia": {"tier": 2, "region": "middle_east", "population": 35000000, "gdp_rank": 18,
                     "military_spending_rank": 5, "nuclear_power": False},
    "india": {"tier": 2, "region": "asia", "population": 1400000000, "gdp_rank": 5,
              "military_spending_rank": 4, "nuclear_power": True},
    "pakistan": {"tier": 2, "region": "asia", "population": 231000000, "gdp_rank": 42,
                 "military_spending_rank": 9, "nuclear_power": True},
    "north_korea": {"tier": 2, "region": "asia", "population": 26000000, "gdp_rank": 130,
                    "military_spending_rank": 18, "nuclear_power": True},
    "israel": {"tier": 2, "region": "middle_east", "population": 9500000, "gdp_rank": 28,
               "military_spending_rank": 15, "nuclear_power": True},
    # Tier 3 — Regionally Significant
    "germany": {"tier": 3, "region": "europe", "population": 83000000, "gdp_rank": 4, "military_spending_rank": 7, "nuclear_power": False},
    "france": {"tier": 3, "region": "europe", "population": 68000000, "gdp_rank": 7, "military_spending_rank": 6, "nuclear_power": True},
    "united_kingdom": {"tier": 3, "region": "europe", "population": 67000000, "gdp_rank": 6, "military_spending_rank": 10, "nuclear_power": True},
    "japan": {"tier": 3, "region": "asia", "population": 125000000, "gdp_rank": 3, "military_spending_rank": 11, "nuclear_power": False},
    "south_korea": {"tier": 3, "region": "asia", "population": 52000000, "gdp_rank": 12, "military_spending_rank": 12, "nuclear_power": False},
    "poland": {"tier": 3, "region": "europe", "population": 38000000, "gdp_rank": 22, "military_spending_rank": 20, "nuclear_power": False},
    "venezuela": {"tier": 3, "region": "south_america", "population": 28000000, "gdp_rank": 67, "military_spending_rank": 30, "nuclear_power": False},
    "cuba": {"tier": 3, "region": "south_america", "population": 11000000, "gdp_rank": 73, "military_spending_rank": 50, "nuclear_power": False},
    "belarus": {"tier": 3, "region": "europe", "population": 9400000, "gdp_rank": 74, "military_spending_rank": 35, "nuclear_power": False},
    "myanmar": {"tier": 3, "region": "asia", "population": 54000000, "gdp_rank": 64, "military_spending_rank": 28, "nuclear_power": False},
    "ethiopia": {"tier": 3, "region": "africa", "population": 120000000, "gdp_rank": 58, "military_spending_rank": 45, "nuclear_power": False},
    "mali": {"tier": 3, "region": "africa", "population": 22000000, "gdp_rank": 120, "military_spending_rank": 60, "nuclear_power": False},
    "niger": {"tier": 3, "region": "africa", "population": 26000000, "gdp_rank": 125, "military_spending_rank": 62, "nuclear_power": False},
    # Tier 4 — Low-Signal
    "norway": {"tier": 4, "region": "europe", "population": 5400000, "gdp_rank": 23, "military_spending_rank": 32, "nuclear_power": False},
    "canada": {"tier": 4, "region": "north_america", "population": 38000000, "gdp_rank": 9, "military_spending_rank": 16, "nuclear_power": False},
    "mexico": {"tier": 4, "region": "north_america", "population": 128000000, "gdp_rank": 14, "military_spending_rank": 24, "nuclear_power": False},
    "brazil": {"tier": 4, "region": "south_america", "population": 214000000, "gdp_rank": 8, "military_spending_rank": 17, "nuclear_power": False},
    "argentina": {"tier": 4, "region": "south_america", "population": 45000000, "gdp_rank": 31, "military_spending_rank": 35, "nuclear_power": False},
    "colombia": {"tier": 4, "region": "south_america", "population": 51000000, "gdp_rank": 38, "military_spending_rank": 30, "nuclear_power": False},
    "indonesia": {"tier": 4, "region": "asia", "population": 273000000, "gdp_rank": 16, "military_spending_rank": 25, "nuclear_power": False},
    "vietnam": {"tier": 4, "region": "asia", "population": 98000000, "gdp_rank": 35, "military_spending_rank": 29, "nuclear_power": False},
    "nigeria": {"tier": 4, "region": "africa", "population": 218000000, "gdp_rank": 27, "military_spending_rank": 31, "nuclear_power": False},
    "south_africa": {"tier": 4, "region": "africa", "population": 60000000, "gdp_rank": 33, "military_spending_rank": 34, "nuclear_power": False},
    "kenya": {"tier": 4, "region": "africa", "population": 54000000, "gdp_rank": 66, "military_spending_rank": 40, "nuclear_power": False},
}

# ── Collection depth targets by tier ──
TIER_COLLECTION_TARGETS = {
    1: {"min_sources": 15, "source_types": 10, "high_value_sources": 5, "local_language": 3, "update_frequency": "daily"},
    2: {"min_sources": 10, "source_types": 7, "high_value_sources": 3, "local_language": 2, "update_frequency": "daily"},
    3: {"min_sources": 6, "source_types": 5, "high_value_sources": 2, "local_language": 1, "update_frequency": "weekly"},
    4: {"min_sources": 3, "source_types": 3, "high_value_sources": 1, "local_language": 0, "update_frequency": "monthly"},
}


def load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            return {}
    return {}


def build_country_profiles(inventory: list[dict]) -> dict:
    """Build intelligence profiles for all tracked countries."""
    profiles = {}
    
    for country_name, country_data in COUNTRIES.items():
        country_sources = [s for s in inventory if s.get("country", "").lower() == country_name]
        region = country_data["region"]
        tier = country_data.get("tier", 4)
        targets = TIER_COLLECTION_TARGETS.get(tier, TIER_COLLECTION_TARGETS[4])
        
        source_types = set(s.get("source_type", "") for s in country_sources)
        high_value_types = {"government_portal", "procurement_system", "sanctions_registry",
                           "defense_procurement", "customs_database"}
        high_value_count = sum(1 for s in country_sources if s.get("source_type") in high_value_types)
        local_lang = sum(1 for s in country_sources if s.get("source_type") in ("local_media", "telegram_channel"))
        
        # Collection confidence
        density_score = min(1.0, len(country_sources) / max(targets["min_sources"], 1))
        diversity_score = min(1.0, len(source_types) / max(targets["source_types"], 1))
        high_value_score = min(1.0, high_value_count / max(targets["high_value_sources"], 1))
        local_score = min(1.0, local_lang / max(targets["local_language"], 1)) if targets["local_language"] > 0 else 0.5
        
        confidence = round((density_score * 0.30 + diversity_score * 0.25 +
                           high_value_score * 0.25 + local_score * 0.20) * 100, 1)
        
        collection_gap = round(100 - confidence, 1)
        
        profiles[country_name] = {
            "tier": tier,
            "region": region,
            "source_count": len(country_sources),
            "source_diversity": len(source_types),
            "high_value_sources": high_value_count,
            "local_language_sources": local_lang,
            "target_sources": targets["min_sources"],
            "collection_confidence": confidence,
            "collection_gap": collection_gap,
            "update_frequency": targets["update_frequency"],
            "needs_urgent_improvement": confidence < 30 and tier <= 2,
            "is_collection_desert": len(country_sources) == 0,
        }
    
    return profiles


def compute_global_confidence_map(country_profiles: dict) -> dict:
    """Compute global collection confidence statistics."""
    tiers = {1: [], 2: [], 3: [], 4: []}
    for name, profile in country_profiles.items():
        t = profile.get("tier", 4)
        tiers[t].append(profile)
    
    return {
        "tier1_avg_confidence": round(sum(p["collection_confidence"] for p in tiers[1]) / max(len(tiers[1]), 1), 1),
        "tier2_avg_confidence": round(sum(p["collection_confidence"] for p in tiers[2]) / max(len(tiers[2]), 1), 1),
        "tier3_avg_confidence": round(sum(p["collection_confidence"] for p in tiers[3]) / max(len(tiers[3]), 1), 1),
        "tier4_avg_confidence": round(sum(p["collection_confidence"] for p in tiers[4]) / max(len(tiers[4]), 1), 1),
        "countries_with_confidence_below_30": [n for n, p in country_profiles.items() if p["collection_confidence"] < 30],
        "collection_deserts": [n for n, p in country_profiles.items() if p.get("is_collection_desert")],
        "tier1_countries_needing_attention": [n for n, p in country_profiles.items() if p.get("needs_urgent_improvement")],
    }


def detect_strategic_blind_spots(country_profiles: dict) -> list[dict]:
    """Identify countries with dangerous collection weakness that are strategically important."""
    blind_spots = []
    for name, profile in country_profiles.items():
        if profile["tier"] <= 2 and profile["collection_confidence"] < 40:
            blind_spots.append({
                "country": name,
                "tier": profile["tier"],
                "confidence": profile["collection_confidence"],
                "gap": profile["collection_gap"],
                "missing": [],
            })
            # Determine specific gaps
            if profile["high_value_sources"] < (TIER_COLLECTION_TARGETS[profile["tier"]]["high_value_sources"] or 1):
                blind_spots[-1]["missing"].append("high_value_sources")
            if profile["local_language_sources"] < (TIER_COLLECTION_TARGETS[profile["tier"]]["local_language"] or 1):
                blind_spots[-1]["missing"].append("local_language")
            if profile["source_diversity"] < (TIER_COLLECTION_TARGETS[profile["tier"]]["source_types"] or 1):
                blind_spots[-1]["missing"].append("source_diversity")
    return blind_spots


def adapt_collection_depth(country_profiles: dict) -> dict:
    """Dynamically adjust collection depth based on confidence and strategic tier."""
    depth_plan = {}
    for name, profile in country_profiles.items():
        tier = profile["tier"]
        confidence = profile["collection_confidence"]
        gap = profile["collection_gap"]
        
        if tier == 1 and confidence < 50:
            depth = "critical_intensification"
            frequency = "daily"
        elif tier == 1 and confidence < 70:
            depth = "enhanced"
            frequency = "daily"
        elif tier <= 2 and gap > 50:
            depth = "intensified_acquisition"
            frequency = "every_other_day"
        elif tier <= 3 and gap > 40:
            depth = "maintain_improve"
            frequency = "weekly"
        elif tier == 4 and confidence > 60:
            depth = "monitor_only"
            frequency = "monthly"
        else:
            depth = "maintain"
            frequency = "weekly"
        
        depth_plan[name] = {
            "collection_depth": depth,
            "frequency": frequency,
            "confidence_score": confidence,
            "gap_percentage": gap,
        }
    return depth_plan


def generate_strategic_warnings(country_profiles: dict, depth_plan: dict) -> list[dict]:
    """Identify emerging warning signals from collection posture."""
    warnings = []
    
    # Countries with critical collection weakness that are Tier 1-2
    for name, profile in country_profiles.items():
        if profile["tier"] <= 2 and profile["collection_confidence"] < 25:
            warnings.append({
                "type": "critical_blind_spot",
                "country": name,
                "tier": profile["tier"],
                "confidence": profile["collection_confidence"],
                "warning": f"Strategically critical country with dangerous collection weakness ({profile['collection_confidence']}% confidence)",
            })
    
    # Collection deserts in volatile regions
    region_volatility = {"middle_east": "very_high", "europe": "high", "asia": "high",
                        "africa": "medium", "south_america": "medium", "north_america": "low"}
    for name, profile in country_profiles.items():
        if profile.get("is_collection_desert") and region_volatility.get(profile["region"], "low") in ("very_high", "high"):
            warnings.append({
                "type": "collection_desert_in_volatile_region",
                "country": name,
                "region": profile["region"],
                "volatility": region_volatility.get(profile["region"], "low"),
                "warning": f"Collection desert in high-volatility region: {name} ({profile['region']})",
            })
    
    return warnings


def main():
    """Run global collection architecture cycle."""
    log.info("Building global collection architecture")
    
    inventory = load_json(INVENTORY_FILE).get("sources", [])
    global_report = {}
    
    # Phase 1-2: Country profiles + tiering
    country_profiles = build_country_profiles(inventory)
    log.info(f"Country profiles built", count=len(country_profiles))
    
    # Phase 3: Collection confidence map
    confidence_map = compute_global_confidence_map(country_profiles)
    log.info(f"Global confidence map: Tier1={confidence_map['tier1_avg_confidence']}% Tier2={confidence_map['tier2_avg_confidence']}%")
    
    # Phase 4: Strategic blind spots
    blind_spots = detect_strategic_blind_spots(country_profiles)
    log.info(f"Strategic blind spots: {len(blind_spots)}")
    
    # Phase 5: Adaptive collection depth
    depth_plan = adapt_collection_depth(country_profiles)
    log.info(f"Depth plan built: {sum(1 for d in depth_plan.values() if d['collection_depth'] in ('critical_intensification','enhanced'))} countries need intensification")
    
    # Phase 6: Strategic warnings
    warnings = generate_strategic_warnings(country_profiles, depth_plan)
    log.info(f"Strategic warnings: {len(warnings)}")
    
    # Tier distribution
    tier_dist = {}
    for name, profile in country_profiles.items():
        t = profile["tier"]
        tier_dist[t] = tier_dist.get(t, 0) + 1
    
    report = {
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "country_count": len(country_profiles),
        "tier_distribution": {f"tier_{k}": v for k, v in sorted(tier_dist.items())},
        "global_confidence_map": confidence_map,
        "country_profiles": country_profiles,
        "strategic_blind_spots": blind_spots,
        "adaptive_depth_plan": depth_plan,
        "strategic_warnings": warnings,
    }
    
    CRON_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(report, indent=2))
    log.info("Global collection report saved", countries=len(country_profiles), blind_spots=len(blind_spots))
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"GLOBAL ADAPTIVE COLLECTION ARCHITECTURE")
    print(f"{'='*60}")
    
    print(f"\nCountries tracked: {len(country_profiles)} ({len(confidence_map.get('collection_deserts', []))} collection deserts)")
    print(f"Tier distribution: {json.dumps(tier_dist)}")
    
    print(f"\nGlobal confidence by tier:")
    for t in [1, 2, 3, 4]:
        avg = confidence_map.get(f"tier{t}_avg_confidence", 0)
        bar = "█" * (int(avg) // 10) + "░" * (10 - int(avg) // 10)
        print(f"  Tier {t}: {bar} {avg}%")
    
    if blind_spots:
        print(f"\nStrategic blind spots ({len(blind_spots)}):")
        for bs in blind_spots[:5]:
            print(f"  🔴 {bs['country']} (Tier {bs['tier']}) confidence={bs['confidence']}% gap={bs['gap']}% missing={bs['missing']}")
    
    if warnings:
        print(f"\nStrategic warnings ({len(warnings)}):")
        for w in warnings[:5]:
            print(f"  ⚠️  {w['warning'][:100]}")
    
    print(f"\nAdaptive collection depth:")
    depth_counts = {}
    for d in depth_plan.values():
        depth_counts[d['collection_depth']] = depth_counts.get(d['collection_depth'], 0) + 1
    for k, v in sorted(depth_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {k}: {v} countries")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
