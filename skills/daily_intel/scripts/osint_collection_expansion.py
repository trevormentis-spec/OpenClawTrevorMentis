#!/usr/bin/env python3
"""
osint_collection_expansion.py — Continuous global OSINT source discovery & collection expansion.

Runs during every daily intelligence cycle to:
- Discover new OSINT sources by region, country, and type
- Evaluate and score source quality
- Identify collection gaps and undercovered regions
- Propose new collection campaigns
- Expand information surface diversity

Not a feed consumer — a persistent collection platform.

Output: cron_tracking/collection_expansion.json
"""
from __future__ import annotations

import datetime
import hashlib
import json
import re
import sys
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from trevor_config import THEATRE_KEYS as THEATRES, WORKSPACE
from trevor_log import get_logger
from trevor_memory import MemoryStore

log = get_logger("osint_collection")

CRON_DIR = SKILL_ROOT / "cron_tracking"
OUTPUT_FILE = CRON_DIR / "collection_expansion.json"
SOURCE_INVENTORY = CRON_DIR / "source_inventory.json"

# ── Source type taxonomy ──
SOURCE_TYPES = [
    "local_media", "regional_publication", "government_portal",
    "procurement_system", "legal_gazette", "parliamentary_transcript",
    "customs_database", "shipping_data", "aviation_tracking",
    "energy_infrastructure", "telecom_monitor", "sanctions_registry",
    "defense_procurement", "trade_journal", "military_forum",
    "telegram_channel", "local_influencer", "satellite_derived",
    "academic_source", "technical_source", "prediction_market",
    "think_tank", "official_document", "social_media_monitor",
]

# ── Region/country coverage targets ──
COVERAGE_TARGETS = {
    "europe": {
        "countries": ["ukraine", "russia", "germany", "poland", "norway",
                     "france", "uk", "belarus", "baltic_states", "balkans"],
        "current_sources": 3,
        "target_sources": 8,
        "priority": "high",
    },
    "middle_east": {
        "countries": ["iran", "iraq", "israel", "lebanon", "yemen",
                      "saudi_arabia", "uae", "syria", "qatar", "oman"],
        "current_sources": 2,
        "target_sources": 8,
        "priority": "critical",
    },
    "asia": {
        "countries": ["china", "taiwan", "india", "pakistan", "japan",
                      "south_korea", "indonesia", "vietnam", "myanmar", "afghanistan"],
        "current_sources": 2,
        "target_sources": 8,
        "priority": "high",
    },
    "north_america": {
        "countries": ["mexico", "canada", "united_states", "cuba", "haiti"],
        "current_sources": 4,
        "target_sources": 6,
        "priority": "medium",
    },
    "south_central_america": {
        "countries": ["venezuela", "colombia", "brazil", "argentina",
                      "chile", "peru", "bolivia", "ecuador"],
        "current_sources": 1,
        "target_sources": 5,
        "priority": "medium",
    },
    "africa": {
        "countries": ["mali", "niger", "burkina_faso", "nigeria", "ethiopia",
                      "somalia", "sudan", "kenya", "south_africa", "drc"],
        "current_sources": 1,
        "target_sources": 6,
        "priority": "high",
    },
    "global_finance": {
        "countries": ["global", "usa", "china", "eu", "russia", "gulf_states"],
        "current_sources": 3,
        "target_sources": 6,
        "priority": "high",
    },
}

# ── Source type → strategic value weights ──
SOURCE_TYPE_VALUE = {
    "local_media": 6, "regional_publication": 5, "government_portal": 8,
    "procurement_system": 7, "legal_gazette": 6, "parliamentary_transcript": 7,
    "customs_database": 8, "shipping_data": 7, "aviation_tracking": 6,
    "energy_infrastructure": 7, "telecom_monitor": 5, "sanctions_registry": 8,
    "defense_procurement": 9, "trade_journal": 5, "military_forum": 4,
    "telegram_channel": 6, "local_influencer": 3, "satellite_derived": 8,
    "academic_source": 5, "technical_source": 4, "prediction_market": 7,
    "think_tank": 5, "official_document": 7, "social_media_monitor": 4,
}


def search_source_candidates(country: str, source_type: str, max_results: int = 5) -> list[dict]:
    """Search for potential new OSINT sources for a country and type."""
    candidates = []
    # Build search query targeting the specific source type in the country
    queries = {
        "local_media": f"{country} local news website english OR native language",
        "government_portal": f"{country} .gov OR .mil official website intelligence analysis",
        "legal_gazette": f"{country} official gazette OR legal register published",
        "parliamentary_transcript": f"{country} parliament OR congress debate transcript",
        "defense_procurement": f"{country} defense OR military procurement contract tender",
        "telegram_channel": f"{country} telegram channel geopolitical analysis English",
        "shipping_data": f"{country} port shipping maritime traffic live tracking",
        "aviation_tracking": f"{country} flight radar aviation movement realtime",
        "energy_infrastructure": f"{country} oil gas energy pipeline infrastructure map",
        "sanctions_registry": f"{country} sanctions export control restricted entities list",
        "customs_database": f"{country} customs trade import export statistics portal",
        "satellite_derived": f"{country} satellite imagery analysis infrastructure monitoring",
        "academic_source": f"{country} university research center geopolitical security studies",
        "trade_journal": f"{country} business trade industry journal economic intelligence",
        "think_tank": f"{country} think tank policy analysis strategy report",
    }
    query = queries.get(source_type, f"{country} {source_type} intelligence analysis english")
    query += " 2026"

    try:
        search_url = (
            f"https://html.duckduckgo.com/html/?q="
            f"{urllib.parse.quote(query)}"
        )
        req = urllib.request.Request(
            search_url,
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode(errors="replace")

        # Extract result links and titles
        for match in re.finditer(
            r'<a rel="nofollow" class="result__a" href="([^"]+)">(.*?)</a>',
            html, re.DOTALL
        ):
            url = match.group(1)
            title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            if url and title and len(title) > 10:
                candidates.append({
                    "url": url,
                    "title": title[:200],
                    "source_type": source_type,
                    "country": country,
                    "discovered_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                })
                if len(candidates) >= max_results:
                    break
    except Exception as e:
        log.warning(f"Search failed for {country}/{source_type}: {e}")

    return candidates


def score_candidate(candidate: dict) -> dict:
    """Score a candidate source on multiple axes."""
    url = candidate.get("url", "")
    title = candidate.get("title", "")
    source_type = candidate.get("source_type", "")
    strategic_base = SOURCE_TYPE_VALUE.get(source_type, 3)

    score = {
        "reliability": 0,
        "novelty": 0,
        "strategic_value": strategic_base,
        "regional_depth": 0,
        "accessibility": 0,
    }

    # Reliability signals
    if any(domain in url for domain in [".gov", ".mil", ".int", ".edu", "ac."]):
        score["reliability"] = 7
    elif url.startswith("https://"):
        score["reliability"] = 5
    else:
        score["reliability"] = 3

    # Regional depth (sources with country-specific domains)
    country = candidate.get("country", "")
    country_tlds = {
        "ukraine": ".ua", "russia": ".ru", "germany": ".de", "poland": ".pl",
        "norway": ".no", "france": ".fr", "iran": ".ir", "iraq": ".iq",
        "china": ".cn", "india": ".in", "japan": ".jp", "brazil": ".br",
        "mexico": ".mx", "nigeria": ".ng", "kenya": ".ke",
    }
    tld = country_tlds.get(country, "")
    if tld and tld in url:
        score["regional_depth"] = 8
    elif country.lower() in url.lower():
        score["regional_depth"] = 6
    else:
        score["regional_depth"] = 3

    # Accessibility
    score["accessibility"] = 6 if "rss" in url.lower() or "feed" in url.lower() else 4

    # Novelty (is this a surface we haven't explored?)
    # Local-language, Telegram, procurement, satellite — higher novelty
    high_novelty_types = ["telegram_channel", "defense_procurement", "satellite_derived",
                         "local_media", "legal_gazette", "customs_database", "parliamentary_transcript"]
    score["novelty"] = 7 if source_type in high_novelty_types else 4

    # Overall
    score["overall"] = round(
        (score["reliability"] * 0.25) +
        (score["novelty"] * 0.20) +
        (score["strategic_value"] * 0.25) +
        (score["regional_depth"] * 0.15) +
        (score["accessibility"] * 0.15),
        1
    )

    return score


def load_existing_inventory() -> list[dict]:
    """Load the existing source inventory."""
    if SOURCE_INVENTORY.exists():
        try:
            return json.loads(SOURCE_INVENTORY.read_text()).get("sources", [])
        except:
            return []
    return []


def save_inventory(sources: list[dict]):
    """Save the source inventory."""
    SOURCE_INVENTORY.parent.mkdir(parents=True, exist_ok=True)
    SOURCE_INVENTORY.write_text(json.dumps({
        "updated": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_count": len(sources),
        "sources": sources,
    }, indent=2))


def dedup_candidates(candidates: list[dict], existing_urls: set) -> list[dict]:
    """Remove candidates already in the inventory."""
    return [c for c in candidates if c.get("url") not in existing_urls]


def analyze_coverage_gaps(existing: list[dict]) -> list[dict]:
    """Identify collection gaps per country and region."""
    gaps = []

    # Count existing sources by country and type
    country_sources = {}
    for s in existing:
        country = s.get("country", "unknown")
        if country not in country_sources:
            country_sources[country] = {"count": 0, "types": set()}
        country_sources[country]["count"] += 1
        country_sources[country]["types"].add(s.get("source_type", "unknown"))

    for region_key, region_data in COVERAGE_TARGETS.items():
        for country in region_data["countries"]:
            current = country_sources.get(country, {"count": 0, "types": set()})
            target = region_data.get("target_sources", 5)
            if current["count"] < target:
                missing_types = [
                    st for st in SOURCE_TYPES
                    if st not in current["types"]
                ]
                gaps.append({
                    "region": region_key,
                    "country": country,
                    "current_sources": current["count"],
                    "target_sources": target,
                    "gap": target - current["count"],
                    "missing_source_types": missing_types[:5],
                    "priority": region_data.get("priority", "medium"),
                })

    return sorted(gaps, key=lambda x: x["gap"], reverse=True)


def main():
    """Run the OSINT collection expansion cycle."""
    log.info("Starting OSINT collection expansion")

    existing = load_existing_inventory()
    existing_urls = {s.get("url", "") for s in existing}

    # Discover new sources — focus on highest-priority gaps
    gaps = analyze_coverage_gaps(existing)
    all_candidates = []
    high_gaps = [g for g in gaps if g["gap"] >= 2][:5]  # top 5 gaps

    for gap in high_gaps:
        country = gap["country"]
        for source_type in gap["missing_source_types"][:3]:
            log.info(f"Searching {country} for {source_type}")
            candidates = search_source_candidates(country, source_type, max_results=3)
            all_candidates.extend(candidates)

    new_sources = dedup_candidates(all_candidates, existing_urls)

    # Score new candidates
    scored_sources = []
    for candidate in new_sources:
        scores = score_candidate(candidate)
        scored_sources.append({**candidate, **scores})

    # Keep only sources above minimum quality threshold
    viable = [s for s in scored_sources if s.get("overall", 0) >= 4.0]

    # Update inventory with viable new sources
    existing.extend(viable)
    save_inventory(existing)

    # Build report
    report = {
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pipeline_date": datetime.date.today().isoformat(),
        "summary": {
            "existing_sources": len(existing) - len(viable),
            "candidates_found": len(all_candidates),
            "new_sources_added": len(viable),
            "total_inventory": len(existing),
            "regions_checked": len(high_gaps),
        },
        "new_source_discoveries": [
            {
                "url": s.get("url", ""),
                "title": s.get("title", "")[:100],
                "source_type": s.get("source_type", ""),
                "country": s.get("country", ""),
                "score": s.get("overall", 0),
                "strategic_value": s.get("strategic_value", 0),
                "novelty": s.get("novelty", 0),
            }
            for s in viable[:10]
        ],
        "collection_gaps": [
            {
                "region": g["region"],
                "country": g["country"],
                "current_sources": g["current_sources"],
                "target": g["target_sources"],
                "missing_types": g["missing_source_types"][:3],
                "priority": g["priority"],
            }
            for g in gaps[:10]
        ],
        "collection_expansion_opportunities": [
            {
                "country": g["country"],
                "region": g["region"],
                "opportunity": f"Add {g['gap']} sources to reach target of {g['target_sources']}",
                "strategic_value": "high" if g["priority"] == "critical" else "medium" if g["priority"] == "high" else "low",
                "priority": g["priority"],
                "collect_effort": "low" if g["target_sources"] - g["current_sources"] <= 3 else "medium",
            }
            for g in gaps[:8]
        ],
    }

    # Save report
    CRON_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(report, indent=2))
    log.info("Collection expansion report generated",
             new_sources=len(viable),
             gaps=len(gaps),
             total_inventory=len(existing))

    # Print summary
    print(f"\n{'='*60}")
    print(f"OSINT COLLECTION EXPANSION")
    print(f"{'='*60}")
    print(f"\nExisting sources:               {len(existing) - len(viable)}")
    print(f"Candidates found:              {len(all_candidates)}")
    print(f"New sources added:             {len(viable)}")
    print(f"Total inventory:               {len(existing)}")
    print(f"Regions checked:               {len(high_gaps)}")
    print(f"Collection gaps identified:    {len(gaps)}")

    if viable:
        print(f"\nNew source discoveries:")
        for s in viable[:5]:
            print(f"  {s.get('overall', 0):.1f} | {s.get('title', '')[:80]}")

    if gaps:
        print(f"\nTop collection gaps:")
        for g in gaps[:5]:
            print(f"  {g['region']:25s} {g['country']:20s} {g['current_sources']}/{g['target_sources']} sources ({g['gap']} missing)")

    print(f"\n{'='*60}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
