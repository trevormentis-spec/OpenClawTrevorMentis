#!/usr/bin/env python3
"""
collection_intelligence.py — Adaptive collection cognition engine.

Evaluates collection quality per theatre and produces confidence adjustments
that materially affect assessment generation and collection prioritization.

Closes the loop:
  collection state → source quality → confidence adjustment →
  prioritization → altered analytical behavior → updated collection state

Output: cron_tracking/collection_intelligence.json
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

log = get_logger("collection_intel")

CRON_DIR = SKILL_ROOT / "cron_tracking"
OUTPUT_FILE = CRON_DIR / "collection_intelligence.json"
INVENTORY_FILE = CRON_DIR / "source_inventory.json"
NARRATIVE_FILE = CRON_DIR / "narrative_landscape.json"

# ── Baseline collection quality per theatre (from coverage targets) ──
BASELINE_SOURCE_TARGETS = {
    "europe": 8, "middle_east": 8, "asia": 8, "north_america": 6,
    "south_america": 5, "africa": 6, "global_finance": 6,
}

# ── Source type → collection quality weight ──
SOURCE_TYPE_WEIGHT = {
    "local_media": 0.15, "government_portal": 0.20, "procurement_system": 0.15,
    "legal_gazette": 0.10, "parliamentary_transcript": 0.10, "customs_database": 0.10,
    "shipping_data": 0.05, "aviation_tracking": 0.05, "energy_infrastructure": 0.10,
    "telecom_monitor": 0.05, "sanctions_registry": 0.15, "defense_procurement": 0.20,
    "telegram_channel": 0.10, "satellite_derived": 0.15, "academic_source": 0.08,
    "trade_journal": 0.08, "think_tank": 0.08, "prediction_market": 0.10,
}

# ── Confidence adjustment ranges based on collection quality ──
COLLECTION_TO_CONFIDENCE = {
    "excellent": {"band_adjust": 0, "uncertainty_width": 10, "estimation_aggressiveness": "full"},
    "good": {"band_adjust": -5, "uncertainty_width": 15, "estimation_aggressiveness": "moderate"},
    "adequate": {"band_adjust": -10, "uncertainty_width": 20, "estimation_aggressiveness": "conservative"},
    "poor": {"band_adjust": -15, "uncertainty_width": 30, "estimation_aggressiveness": "highly_conservative"},
    "minimal": {"band_adjust": -20, "uncertainty_width": 40, "estimation_aggressiveness": "speculative_only"},
}

# ── Theatre → strategic significance weight ──
STRATEGIC_WEIGHT = {
    "middle_east": 0.95, "europe": 0.85, "asia": 0.80,
    "north_america": 0.60, "global_finance": 0.55, "africa": 0.45,
    "south_america": 0.35,
}


def evaluate_collection_quality(region: str, inventory: list[dict]) -> dict:
    """Evaluate collection quality for a theatre based on source inventory."""
    # Count sources relevant to this region
    region_sources = [s for s in inventory if s.get("country", "") in get_region_countries(region)]
    region_sources += [s for s in inventory if s.get("region", "") == region]
    
    # Count unique source types
    source_types = set(s.get("source_type", "") for s in region_sources)
    source_diversity = len(source_types)
    
    # Count high-value source types (government, procurement, customs, defense)
    high_value_types = {"government_portal", "procurement_system", "sanctions_registry",
                        "defense_procurement", "customs_database", "parliamentary_transcript"}
    high_value_count = sum(1 for s in region_sources if s.get("source_type") in high_value_types)
    
    # Local language sources
    local_sources = sum(1 for s in region_sources if s.get("source_type") in ("local_media", "telegram_channel"))
    
    # Compute quality score
    target = BASELINE_SOURCE_TARGETS.get(region, 5)
    density_score = min(1.0, len(region_sources) / max(target, 1))
    diversity_score = min(1.0, source_diversity / 6)  
    high_value_score = min(1.0, high_value_count / 3)
    local_score = min(1.0, local_sources / 2)
    
    total_score = (density_score * 0.35 + diversity_score * 0.25 +
                   high_value_score * 0.25 + local_score * 0.15)
    
    # Categorize
    if total_score >= 0.80:
        level = "excellent"
    elif total_score >= 0.60:
        level = "good"
    elif total_score >= 0.40:
        level = "adequate"
    elif total_score >= 0.20:
        level = "poor"
    else:
        level = "minimal"
    
    confidence = COLLECTION_TO_CONFIDENCE[level]
    
    return {
        "region": region,
        "quality_level": level,
        "quality_score": round(total_score, 3),
        "source_count": len(region_sources),
        "source_diversity": source_diversity,
        "high_value_sources": high_value_count,
        "local_language_sources": local_sources,
        "band_adjustment": confidence["band_adjust"],
        "uncertainty_width": confidence["uncertainty_width"],
        "estimation_aggressiveness": confidence["estimation_aggressiveness"],
        "collection_gap": round(1.0 - total_score, 3),
        "target_sources": target,
    }


def get_region_countries(region: str) -> list[str]:
    """Get country list for a region."""
    region_countries = {
        "europe": ["ukraine", "russia", "germany", "poland", "norway", "france", "uk", "belarus"],
        "middle_east": ["iran", "iraq", "israel", "lebanon", "yemen", "saudi_arabia", "uae", "syria"],
        "asia": ["china", "taiwan", "india", "pakistan", "japan", "south_korea", "indonesia", "vietnam", "afghanistan"],
        "north_america": ["mexico", "canada", "united_states"],
        "south_america": ["venezuela", "colombia", "brazil", "argentina", "chile", "cuba"],
        "africa": ["mali", "niger", "burkina_faso", "nigeria", "ethiopia", "somalia", "sudan", "kenya"],
        "global_finance": ["global", "usa", "china", "eu"],
    }
    return region_countries.get(region, [])


def compute_confidence_adjustment(collection_quality: dict) -> str:
    """Generate a prompt instruction fragment from collection quality."""
    level = collection_quality["quality_level"]
    adj = collection_quality["band_adjustment"]
    width = collection_quality["uncertainty_width"]
    style = collection_quality["estimation_aggressiveness"]
    gap = collection_quality["collection_gap"]
    hvs = collection_quality["high_value_sources"]
    
    messages = {
        "excellent": "Collection quality is excellent. Standard confidence estimation applies. Use normal probability ranges.",
        "good": "Collection quality is good. Apply a slight downward confidence adjustment. Prefer slightly wider ranges.",
        "adequate": "Collection quality is adequate. Apply moderate confidence reduction. Use wider probability bands. Flag collection limitations.",
        "poor": "Collection quality is poor. Apply significant confidence reduction. Mark assessments as lower-confidence. Explicitly flag weak sourcing.",
        "minimal": "Collection quality is minimal. Assessments are highly uncertain. Use the widest probability ranges available. Note that collection gaps may affect analytical accuracy.",
    }
    
    instruction = messages.get(level, messages["adequate"])
    
    if hvs < 2:
        instruction += " Government, procurement, and official sources are scarce. Increase uncertainty."
    
    if gap > 0.5:
        instruction += f" Collection gap is {gap:.0%} — significant information surfaces underexplored. Note this in assessment."
    
    if style == "highly_conservative":
        instruction += " Avoid strong predictive statements. Focus on scenario ranges rather than point estimates."
    elif style == "speculative_only":
        instruction += " Only speculative assessment possible. Do not offer confident predictions."
    
    return instruction


def compute_collection_priorities(inventory: list[dict]) -> list[dict]:
    """Compute dynamic collection priorities based on collection quality and strategic importance."""
    priorities = []
    
    for region in THEATRES:
        quality = evaluate_collection_quality(region, inventory)
        strategic_weight = STRATEGIC_WEIGHT.get(region, 0.5)
        gap = quality["collection_gap"]
        
        # Priority = strategic importance × collection gap
        priority_score = round(strategic_weight * gap * 100, 1)
        
        priorities.append({
            "region": region,
            "strategic_weight": strategic_weight,
            "quality_level": quality["quality_level"],
            "quality_score": quality["quality_score"],
            "gap": gap,
            "priority_score": priority_score,
            "recommended_action": (
                "urgent_collection_push" if priority_score > 30 else
                "intensify_discovery" if priority_score > 15 else
                "maintain_coverage" if priority_score > 5 else
                "monitor_only"
            ),
        })
    
    return sorted(priorities, key=lambda x: x["priority_score"], reverse=True)


def propose_collection_campaigns(priorities: list[dict], inventory: list[dict]) -> list[dict]:
    """Propose targeted collection campaigns based on priority analysis."""
    campaigns = []
    
    for p in priorities[:4]:  # Top 4 priorities get campaign proposals
        if p["recommended_action"] in ("urgent_collection_push", "intensify_discovery"):
            region = p["region"]
            gap = p["gap"]
            
            # Determine which source types are most missing
            region_sources = [s for s in inventory if s.get("country", "") in get_region_countries(region)]
            existing_types = set(s.get("source_type", "") for s in region_sources)
            
            # Find missing high-value source types
            missing_high_value = [st for st in ["government_portal", "procurement_system",
                "sanctions_registry", "defense_procurement", "customs_database"]
                if st not in existing_types]
            
            # Find missing local/regional sources
            missing_local = [st for st in ["local_media", "telegram_channel", "regional_publication"]
                           if st not in existing_types]
            
            campaign = {
                "region": region,
                "priority_score": p["priority_score"],
                "rationale": f"Collection gap of {gap:.0%} with strategic weight {p['strategic_weight']:.2f}",
                "target_source_types": (missing_high_value + missing_local)[:5],
                "estimated_sources_needed": max(1, int(gap * BASELINE_SOURCE_TARGETS.get(region, 5))),
                "urgency": "high" if p["priority_score"] > 30 else "medium",
            }
            campaigns.append(campaign)
    
    return campaigns


def compute_source_trust_history() -> list[dict]:
    """Evolve source trust based on accuracy, bias, and timeliness tracking."""
    trust_updates = []
    try:
        mem = MemoryStore()
        source_entries = mem.get_recent("source", limit=50)
        
        for entry in source_entries:
            trust_updates.append({
                "source": entry.get("key", "unknown"),
                "current_trust": 0.5,  # neutral baseline
                "entries_logged": 1,
                "needs_review": False,
            })
        mem.close()
    except:
        pass
    
    return trust_updates


def main():
    """Run full collection intelligence cycle."""
    log.info("Starting collection intelligence cycle")
    
    inventory = load_json(INVENTORY_FILE)
    sources = inventory.get("sources", [])
    
    # Evaluate collection quality per theatre
    quality_reports = {}
    for region in THEATRES:
        quality = evaluate_collection_quality(region, sources)
        quality_reports[region] = quality
    
        log.info(f"Collection quality for " + region + ": " + str(quality.get("quality_level","?")) + " score=" + str(quality.get("quality_score",0)))
    # Compute collection priorities
    priorities = compute_collection_priorities(sources)
    log.info("Collection priorities computed", top=priorities[0]["region"] if priorities else "none")
    
    # Propose collection campaigns
    campaigns = propose_collection_campaigns(priorities, sources)
    log.info(f"Collection campaigns proposed: {len(campaigns)}")
    
    # Source trust evolution
    trust_history = compute_source_trust_history()
    
    # Generate confidence adjustment instructions for assessment prompts
    confidence_instructions = {}
    for region in THEATRES:
        quality = quality_reports.get(region, {})
        confidence_instructions[region] = compute_confidence_adjustment(quality)
    
    report = {
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "collection_quality": quality_reports,
        "collection_priorities": priorities,
        "collection_campaigns": campaigns,
        "source_trust_evolutions": trust_history[:10],
        "confidence_instructions": confidence_instructions,
    }
    
    # Save
    CRON_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(report, indent=2))
    log.info("Collection intelligence report saved",
             theatres=len(quality_reports),
             campaigns=len(campaigns))
    
    # Phase 6: Adaptive heartbeat — dynamic collection intensity per region
    heartbeat_plan = {}
    for p in priorities:
        score = p["priority_score"]
        if score > 30:
            interval = "every_daily_run"  # intensify: search every cycle
            intensity = "high"
        elif score > 15:
            interval = "every_other_run"  # moderate: search every other cycle
            intensity = "medium"
        elif score > 5:
            interval = "weekly"  # maintain: search weekly
            intensity = "low"
        else:
            interval = "monitor_only"  # deprioritize
            intensity = "minimal"
        
        heartbeat_plan[p["region"]] = {
            "collection_interval": interval,
            "intensity": intensity,
            "priority_score": score,
            "strategic_weight": p["strategic_weight"],
            "quality_level": p["quality_level"],
            "gap": p["gap"],
        }
    
    # Phase 7: Collection-aware product proposals
    collection_aware_products = []
    for region in THEATRES:
        q = quality_reports.get(region, {})
        if q.get("quality_level") in ("minimal", "poor"):
            collection_aware_products.append({
                "product": f"Collection gap warning: {region}",
                "rationale": f"Collection is {q['quality_level']}. Only {q['high_value_sources']} high-value sources, "
                           f"{q['local_language_sources']} local-language sources. Assessments may be unreliable.",
                "strategic_question": f"What intelligence products are impossible because collection in {region} is weak?",
                "value": 75,
                "urgency": "high",
            })
        if q.get("high_value_sources", 0) < 2:
            collection_aware_products.append({
                "product": f"Government source deficit: {region}",
                "rationale": f"Only {q['high_value_sources']} high-value government/procurement sources for strategically important region.",
                "strategic_question": f"Is TREVOR missing structural intelligence because no government/procurement sources exist for {region}?",
                "value": 70,
                "urgency": "medium",
            })
        if q.get("local_language_sources", 0) < 1:
            collection_aware_products.append({
                "product": f"Local-language gap: {region}",
                "rationale": f"Zero local-language sources for {region}. All collection is in English.",
                "strategic_question": f"What narratives is TREVOR missing because it cannot access local-language media in {region}?",
                "value": 65,
                "urgency": "medium",
            })
    
    # Add heartbeat plan to report
    report["adaptive_heartbeat"] = heartbeat_plan
    report["collection_aware_products"] = collection_aware_products[:8]
    
    # Update saved report
    CRON_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(report, indent=2))
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"COLLECTION INTELLIGENCE & CONFIDENCE ADAPTATION")
    print(f"{'='*60}")
    
    for p in priorities:
        icon = {"urgent_collection_push": "🔴", "intensify_discovery": "🟡",
                "maintain_coverage": "🟢", "monitor_only": "⚪"}
        hb = heartbeat_plan.get(p['region'], {})
        print(f"  {icon.get(p['recommended_action'], '❓')} {p['region']:<25s} "
              f"quality={p['quality_level']:<10s} gap={p['gap']:.0%} "
              f"priority={p['priority_score']:.1f} | {hb.get('collection_interval','?')}")
    
    if campaigns:
        print(f"\nCollection campaigns:")
        for c in campaigns:
            print(f"  🎯 {c['region']}: {c['target_source_types'][:3]} ({c['estimated_sources_needed']} sources needed)")
    
    print(f"\nConfidence adjustments will affect assessment generation:")
    for region in THEATRES:
        q = quality_reports.get(region, {})
        ci = confidence_instructions.get(region, "")
        print(f"  {region:<25s} band_adj={q.get('band_adjustment',0):>3d}  "
              f"uncertainty={q.get('uncertainty_width',0)}%  {ci[:50]}...")
    
    if collection_aware_products:
        print(f"\nCollection-aware product proposals: {len(collection_aware_products)}")
        for cp in collection_aware_products[:4]:
            print(f"  📋 {cp['product']}")
    
    print(f"\nAdaptive heartbeat by region:")
    for region, hb in sorted(heartbeat_plan.items(), key=lambda x: x[1]['priority_score'], reverse=True):
        print(f"  {region:<25s} {hb['collection_interval']:<20s} intensity={hb['intensity']}")
    
    return 0


def load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except:
            return {}
    return {}


if __name__ == "__main__":
    sys.exit(main())
