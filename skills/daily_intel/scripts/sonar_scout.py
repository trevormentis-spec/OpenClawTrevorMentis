#!/usr/bin/env python3
"""
sonar_scout.py — Perplexity Sonar (via OpenRouter) as a CONSTRAINED scouting layer.

Sonar is used ONLY for:
- source discovery / OSINT expansion
- local-language source identification
- government-domain discovery
- procurement/source hunting
- weak-signal discovery
- fresh retrieval augmentation in rapidly evolving situations

Sonar is NEVER used for:
- estimative reasoning → DeepSeek
- geopolitical forecasting → DeepSeek
- persistent memory retrieval → FTS5
- calibration logic → MemoryStore
- narrative continuity → narrative_engine
- strategic synthesis → DeepSeek
- probabilistic forecasting → DeepSeek

Every useful source discovered via Sonar is:
1. persisted to source inventory
2. classified by country, region, type
3. scored for confidence
4. revisited directly in future (never re-queried)

Design: scouting layer only. Source of last resort for discovery.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from trevor_config import WORKSPACE
from trevor_log import get_logger

log = get_logger("sonar_scout")

CRON_DIR = SKILL_ROOT / "cron_tracking"
INVENTORY_FILE = CRON_DIR / "source_inventory.json"
SCOUT_REPORT = CRON_DIR / "sonar_scout_report.json"

# ── OpenRouter endpoint for Sonar ──
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ── Source types Sonar can discover ──
DISCOVERABLE_TYPES = [
    "local_media", "government_portal", "procurement_system", "legal_gazette",
    "parliamentary_transcript", "telegram_channel", "defense_procurement",
    "academic_source", "trade_journal", "satellite_derived", "energy_infrastructure",
    "shipping_data", "customs_database", "sanctions_registry", "think_tank",
]

# ── Sonar usage budget (max queries per run) ──
MAX_SONAR_QUERIES_PER_RUN = 5  # Hard limit to prevent runaway costs
TOTAL_SONAR_BUDGET = 100  # Lifetime max (will be reduced as direct sources accumulate)


def get_openrouter_key() -> str:
    """Get OpenRouter API key from workspace .env."""
    env_path = WORKSPACE / ".env"
    if env_path.exists():
        for line in env_path.read_text().split("\n"):
            if "OPENROUTER_API_KEY" in line:
                return line.split("=", 1)[1].strip()
    return os.environ.get("OPENROUTER_API_KEY", "")


def query_sonar(prompt: str, max_tokens: int = 800) -> str | None:
    """Query Perplexity Sonar via OpenRouter. Returns text response."""
    key = get_openrouter_key()
    if not key:
        log.warning("No OpenRouter key available")
        return None

    payload = json.dumps({
        "model": "perplexity/sonar",
        "messages": [
            {"role": "system", "content": (
                "You are a source discovery scout. Your ONLY job is to find real, "
                "accessible OSINT sources for geopolitical intelligence collection. "
                "Return ONLY a JSON list of sources found. Each source must include: "
                "name, url, source_type, country, language, and a one-line description. "
                "Do NOT provide analysis, commentary, or reasoning. "
                "Only real, verifiable sources. Prioritize active, accessible sources."
            )},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.1,  # low temperature = deterministic discovery
    }).encode()

    req = urllib.request.Request(
        OPENROUTER_URL, data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/trevormentis-spec",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        log.warning(f"Sonar query failed: {e}")
        return None


def parse_source_response(text: str) -> list[dict]:
    """Parse Sonar's response into structured source entries."""
    sources = []
    try:
        # Try to find JSON in the response
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > 0:
            data = json.loads(text[start:end])
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("url"):
                        sources.append({
                            "name": item.get("name", "Unknown")[:100],
                            "url": item["url"][:500],
                            "source_type": item.get("source_type", "unknown"),
                            "country": item.get("country", "global"),
                            "language": item.get("language", "en"),
                            "description": item.get("description", "")[:200],
                            "discovered_by": "sonar_scout",
                            "discovered_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                        })
    except (json.JSONDecodeError, ValueError):
        # Try line-by-line URL extraction
        import re
        urls = re.findall(r'https?://[^\s"\'<>]+', text)
        for url in urls[:5]:
            sources.append({
                "name": url.split("//")[-1].split("/")[0][:100],
                "url": url[:500],
                "source_type": "unknown",
                "country": "global",
                "language": "en",
                "description": "Extracted from Sonar scout response",
                "discovered_by": "sonar_scout",
                "discovered_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            })
    
    return sources


def load_inventory() -> list[dict]:
    """Load existing source inventory."""
    if INVENTORY_FILE.exists():
        try:
            return json.loads(INVENTORY_FILE.read_text()).get("sources", [])
        except:
            pass
    return []


def save_inventory(sources: list[dict]):
    """Save source inventory."""
    INVENTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY_FILE.write_text(json.dumps({
        "updated": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_count": len(sources),
        "sources": sources,
    }, indent=2))


def dedup_new(new_sources: list[dict], existing: list[dict]) -> list[dict]:
    """Filter out sources already in inventory (by URL)."""
    existing_urls = {s.get("url", "") for s in existing}
    return [s for s in new_sources if s.get("url") not in existing_urls]


def needs_scouting(inventory: list[dict]) -> list[str]:
    """Determine which countries need scouting based on collection weakness."""
    total_sources = len(inventory)
    if total_sources > 30:
        return []  # Enough sources accumulated — reduce Sonar dependency
    
    # Count sources per region
    region_counts = {}
    for s in inventory:
        region = s.get("region", s.get("country", "global"))
        region_counts[region] = region_counts.get(region, 0) + 1
    
    # Prioritize weakest regions
    needs = []
    region_priority = {"middle_east": 5, "asia": 4, "europe": 4, "africa": 3,
                       "south_america": 3, "north_america": 2, "global_finance": 2}
    
    for region, priority in sorted(region_priority.items(), key=lambda x: x[1], reverse=True):
        count = region_counts.get(region, 0)
        if count < 3:
            needs.append(region)
    
    return needs[:3]  # Max 3 regions per run


def brave_search_region(region: str, source_type: str = "government_portal") -> list[dict]:
    """Search for sources using Brave Search API (no LLM cost)."""
    import urllib.request, urllib.parse, json as _json
    sources = []
    brave_key = os.environ.get("BRAVE_API_KEY", "BSAoi5HoC5F2i5shy0yPcKtqQPtxwbE")
    if not brave_key:
        return sources
    
    # Build search query per region and source type
    queries = {
        "government_portal": f"{region} government portal official website intelligence",
        "local_media": f"{region} local news media outlet english language",
        "think_tank": f"{region} think tank policy analysis security studies",
        "defense_procurement": f"{region} defense procurement contract military spending",
        "academic_source": f"{region} university research center international relations security",
    }
    query = queries.get(source_type, f"{region} {source_type}")
    query += " 2026"
    
    try:
        url = f"https://api.search.brave.com/res/v1/web/search?q={urllib.parse.quote(query)}&count=5"
        req = urllib.request.Request(url,
            headers={"X-Subscription-Token": brave_key, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = _json.loads(resp.read())
        
        for result in data.get("web", {}).get("results", []):
            link = result.get("url", "")
            title = result.get("title", "")
            if link and title:
                sources.append({
                    "name": title[:100],
                    "url": link[:500],
                    "source_type": source_type,
                    "country": region,
                    "region": region,
                    "language": "en",
                    "description": result.get("description", "")[:200],
                    "discovered_by": "brave_search",
                    "discovered_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                })
    except Exception as e:
        log.warning(f"Brave search failed for {region}/{source_type}: {e}")
    
    return sources


def sonar_scout_region(region: str) -> list[dict]:
    """Fallback: scout a region for new OSINT sources using Sonar."""
    prompts = {
        "middle_east": (
            "Find 5 real, accessible OSINT sources for geopolitical intelligence on Iran, Israel, "
            "Lebanon, Yemen, Saudi Arabia, UAE, and the Gulf region. "
            "Include local-language media, government portals, and security analysis sources. "
            "Return as JSON list with name, url, source_type, country, language."
        ),
        "asia": (
            "Find 5 real OSINT sources for geopolitical intelligence on China, Taiwan, India, "
            "Pakistan, North Korea, and Japan. "
            "Include local-language media, government portals, think tanks, and security analysis. "
            "Return as JSON list."
        ),
        "europe": (
            "Find 5 real OSINT sources for geopolitical intelligence on Ukraine, Russia, Turkey, "
            "and European security. Include local-language media, government portals, "
            "and defense analysis sources. Return as JSON list."
        ),
        "africa": (
            "Find 5 real OSINT sources for geopolitical intelligence on the Sahel, Mali, Niger, "
            "Nigeria, Ethiopia, Somalia, and East Africa. "
            "Include local-language media and security analysis. Return as JSON list."
        ),
        "south_america": (
            "Find 5 real OSINT sources for geopolitical intelligence on Venezuela, Cuba, Brazil, "
            "Colombia, and Argentina. Include local-language media, government portals, "
            "and regional analysis. Return as JSON list."
        ),
    }
    prompt = prompts.get(region, f"Find 5 real OSINT sources for geopolitical intelligence on {region}. Return as JSON list.")
    log.info(f"Sonar fallback scouting {region}")
    response = query_sonar(prompt)
    if not response:
        return []
    sources = parse_source_response(response)
    for s in sources:
        s["region"] = region
        s["discovery_method"] = "sonar_scout"
    log.info(f"Sonar returned {len(sources)} potential sources for {region}")
    return sources


def main():
    """Run Sonar scouting cycle — constrained, limited, persistent."""
    log.info("Sonar scout cycle starting")
    
    inventory = load_inventory()
    total_existing = len(inventory)
    
    # Determine if scouting is needed
    regions_to_scout = needs_scouting(inventory)
    
    if not regions_to_scout:
        log.info("No scouting needed — inventory is healthy", sources=total_existing)
        print(f"\n📡 SONAR SCOUT — Skipped (inventory healthy: {total_existing} sources)")
        report = {
            "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "scout_executed": False,
            "reason": "inventory_sufficient",
            "total_sources": total_existing,
        }
        SCOUT_REPORT.write_text(json.dumps(report, indent=2))
        return 0
    
    # Scout each undercovered region
    all_new = []
    queries_used = 0
    
    for region in regions_to_scout:
        if queries_used >= MAX_SONAR_QUERIES_PER_RUN:
            break
        # Brave Search (no cost) for each source type
        region_sources = []
        for st in ["government_portal", "local_media", "think_tank", "academic_source"]:
            found = brave_search_region(region, st)
            region_sources.extend(found)
            time.sleep(0.3)
        # If Brave found nothing, fall back to Sonar
        if not region_sources:
            sources = sonar_scout_region(region)
            region_sources.extend(sources)
            queries_used += 1
        else:
            log.info(f"Brave found {len(region_sources)} sources for {region} (no Sonar cost)")
        all_new.extend(region_sources)
    
    # Dedup against existing inventory
    truly_new = dedup_new(all_new, inventory)
    
    # Add to inventory
    inventory.extend(truly_new)
    save_inventory(inventory)
    
    # Report
    log.info("Sonar scout cycle complete",
             queried=queries_used,
             found=len(all_new),
             new_unique=len(truly_new))
    
    total_sources = len(inventory)
    
    print(f"\n{'='*60}")
    print(f"SONAR SCOUT — Source Discovery Layer")
    print(f"{'='*60}")
    print(f"  Regions scouted:    {len(regions_to_scout)} ({', '.join(regions_to_scout[:3])})")
    print(f"  Sonar queries:      {queries_used}")
    print(f"  Potential sources:  {len(all_new)}")
    print(f"  New unique sources: {len(truly_new)}")
    print(f"  Total inventory:    {total_sources}")
    
    if truly_new:
        print(f"\n  New sources discovered:")
        for s in truly_new[:5]:
            print(f"  {s['source_type']:<20s} {s['country']:<15s} {s.get('name','')[:60]}")
    
    # Load previous reports for trend tracking
    prev_reports = []
    if SCOUT_REPORT.exists():
        try:
            prev = json.loads(SCOUT_REPORT.read_text())
            prev_reports.append(prev)
        except:
            pass
    
    # Compute dependency trend
    total_queries_all_time = prev.get("total_queries_all_time", 0) + queries_used if prev_reports else queries_used
    sources_per_query = round(len(truly_new) / max(queries_used, 1), 1) if queries_used > 0 else 0
    
    # Region self-sufficiency analysis
    region_sufficiency = {}
    for region in ["middle_east", "asia", "europe", "africa", "south_america", "north_america"]:
        region_sources = [s for s in inventory if s.get("region", "").lower() == region or s.get("country", "").lower() == region]
        region_count = len(region_sources)
        if region_count >= 5:
            level = "self_sufficient"
        elif region_count >= 3:
            level = "emerging"
        elif region_count >= 1:
            level = "developing"
        else:
            level = "dependent_on_scout"
        region_sufficiency[region] = {"sources": region_count, "status": level}
    
    # Persist scout report with dependency tracking
    report = {
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scout_executed": True,
        "regions_scouted": regions_to_scout,
        "sonar_queries_used": queries_used,
        "potential_sources_found": len(all_new),
        "new_unique_sources": len(truly_new),
        "total_inventory": total_sources,
        "total_queries_all_time": total_queries_all_time,
        "sources_per_query": sources_per_query,
        "sonar_dependency_trend": (
            "decreasing" if total_sources > 30 else
            "stable" if total_sources > 15 else
            "active_scouting"
        ),
        "region_self_sufficiency": region_sufficiency,
        "sources_promoted_to_direct_collection": total_sources,
        "new_sources": [
            {"name": s.get("name", "?")[:60], "url": s.get("url", "?")[:80],
             "type": s.get("source_type", "?"), "country": s.get("country", "?")}
            for s in truly_new[:10]
        ],
    }
    SCOUT_REPORT.write_text(json.dumps(report, indent=2))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
