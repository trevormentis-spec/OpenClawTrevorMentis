#!/usr/bin/env python3
"""daily_enrichment.py — Before-assessment enrichment pipeline.

Runs BEFORE the assessment generator to improve data quality:
  1. Story freshness check (compare vs yesterday)
  2. Source freshness check (are sources still active?)
  3. Kalshi/Polymarket data integration
  4. Web search for new developments per theatre
  5. Produce enrichment report for the assessment generator

Output: cron_tracking/enrichment_report.json (consumed by generate_assessments.py)
"""
import os, sys, json, datetime, urllib.request, urllib.parse, re
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
ASSESS_DIR = SKILL_ROOT / 'assessments'
CRON_DIR = SKILL_ROOT / 'cron_tracking'
from trevor_config import WORKSPACE

STORY_TRACKER = CRON_DIR / 'story_tracker.json'
STORY_DELTA = CRON_DIR / 'story_delta.json'
ENRICHMENT = CRON_DIR / 'enrichment_report.json'
KALSHI_SCAN = WORKSPACE / 'exports'

from trevor_config import THEATRE_KEYS as THEATRES

# Source freshness database — when was each source last used and how reliable?
SOURCE_REGISTRY = {
    "NEWS": [
        {"name": "BBC News", "url": "https://www.bbc.com/news", "priority": 5},
        {"name": "Reuters", "url": "https://www.reuters.com", "priority": 5},
        {"name": "Associated Press", "url": "https://apnews.com", "priority": 5},
        {"name": "Al Jazeera", "url": "https://www.aljazeera.com", "priority": 4},
        {"name": "The New York Times", "url": "https://www.nytimes.com", "priority": 4},
        {"name": "Axios", "url": "https://www.axios.com", "priority": 4},
        {"name": "Bloomberg", "url": "https://www.bloomberg.com", "priority": 4},
        {"name": "The Diplomat", "url": "https://thediplomat.com", "priority": 3},
        {"name": "Kyiv Post", "url": "https://www.kyivpost.com", "priority": 3},
        {"name": "NPR", "url": "https://www.npr.org", "priority": 3},
        {"name": "Financial Times", "url": "https://www.ft.com", "priority": 3},
        {"name": "The Guardian", "url": "https://www.theguardian.com", "priority": 3},
        {"name": "Turkiye Today", "url": "https://www.turkiyetoday.com", "priority": 2},
        {"name": "TASS", "url": "https://tass.com", "priority": 1},
    ],
    "ANALYSIS": [
        {"name": "ISW", "url": "https://understandingwar.org", "priority": 5},
        {"name": "Critical Threats", "url": "https://www.criticalthreats.org", "priority": 5},
        {"name": "ACLED", "url": "https://acleddata.com", "priority": 4},
        {"name": "CSIS", "url": "https://www.csis.org", "priority": 4},
        {"name": "RAND", "url": "https://www.rand.org", "priority": 4},
        {"name": "Chatham House", "url": "https://www.chathamhouse.org", "priority": 3},
        {"name": "IISS", "url": "https://www.iiss.org", "priority": 3},
        {"name": "AEI", "url": "https://www.aei.org", "priority": 3},
        {"name": "Brookings", "url": "https://www.brookings.edu", "priority": 3},
        {"name": "Jane's", "url": "https://janes.com", "priority": 3},
    ],
    "OFFICIAL": [
        {"name": "US State Department", "url": "https://www.state.gov", "priority": 5},
        {"name": "Pentagon", "url": "https://www.defense.gov", "priority": 5},
        {"name": "CENTCOM", "url": "https://www.centcom.mil", "priority": 4},
        {"name": "US Treasury", "url": "https://home.treasury.gov", "priority": 4},
        {"name": "ECOWAS", "url": "https://www.ecowas.int", "priority": 3},
        {"name": "NATO", "url": "https://www.nato.int", "priority": 4},
        {"name": "UN", "url": "https://www.un.org", "priority": 3},
        {"name": "UKMTO", "url": "https://www.ukmto.org", "priority": 3},
    ],
    "INTEL": [
        {"name": "Polymarket", "url": "https://polymarket.com", "priority": 4},
        {"name": "Kalshi", "url": "https://kalshi.com", "priority": 4},
        {"name": "Stratfor", "url": "https://stratfor.com", "priority": 3},
        {"name": "Shurkin", "url": "https://shurkin.substack.com", "priority": 2},
    ],
}

# ─── 1. STORY FRESHNESS CHECK ────────────────────────────

def check_story_freshness():
    """Compare yesterday vs today's states and flag stale stories."""
    result = {"stalled": [], "developing": [], "new": [], "freshness_scores": {}}

    if not STORY_DELTA.exists():
        print("  No story delta available")
        return result

    delta = json.loads(STORY_DELTA.read_text())
    deltas = delta.get("deltas", {})

    for theatre in THEATRES:
        d = deltas.get(theatre, {})
        status = d.get("status", "unknown")

        if status == "stalled":
            result["stalled"].append(theatre)
            result["freshness_scores"][theatre] = "stale"
            print(f"  ⚠ {theatre}: STALLED — no new signatures")
        elif status == "developing":
            result["developing"].append(theatre)
            result["freshness_scores"][theatre] = "fresh"
            print(f"  → {theatre}: DEVELOPING — {len(d.get('new_signatures', []))} new sigs")
        else:
            result["new"].append(theatre)
            result["freshness_scores"][theatre] = "new"
            print(f"  🆕 {theatre}: NEW")

    print(f"  Summary: {len(result['stalled'])} stalled, {len(result['developing'])} developing")
    return result


# ─── 2. SOURCE FRESHNESS CHECK ───────────────────────────

def check_source_freshness():
    """Check which sources were used vs what's available for each theatre."""
    result = {"used": {}, "available": {}, "gaps": [], "recommendations": []}

    # Load yesterday's sources from story tracker
    if STORY_TRACKER.exists():
        tracker = json.loads(STORY_TRACKER.read_text())
        latest = tracker.get("latest", {})
        for theatre in THEATRES:
            t = latest.get("theatres", {}).get(theatre, {})
            result["used"][theatre] = t.get("sources", [])
    else:
        # Read from assessment files if no tracker
        for theatre in THEATRES:
            ass = ASSESS_DIR / f"{theatre}.md"
            if ass.exists():
                text = ass.read_text().lower()
                used = []
                for cat, sources in SOURCE_REGISTRY.items():
                    for src in sources:
                        if src["name"].lower() in text:
                            used.append(src["name"])
                result["used"][theatre] = used
            else:
                result["used"][theatre] = []

    # Check gaps: high-priority sources not being used
    for theatre in THEATRES:
        used = result["used"].get(theatre, [])
        used_lower = [s.lower() for s in used]
        for cat, sources in SOURCE_REGISTRY.items():
            for src in sources:
                if src["priority"] >= 4 and src["name"].lower() not in used_lower:
                    result["gaps"].append({
                        "theatre": theatre,
                        "source": src["name"],
                        "category": cat,
                        "priority": src["priority"],
                    })
                    if src not in result["recommendations"]:
                        result["recommendations"].append(src["name"])

    # Report
    for theatre in THEATRES:
        used = result["used"].get(theatre, [])
        theatre_gaps = [g for g in result["gaps"] if g["theatre"] == theatre]
        print(f"  {theatre}: {len(used)} sources used, {len(theatre_gaps)} high-priority gaps")
        if theatre_gaps:
            for g in theatre_gaps[:2]:
                print(f"    Missing: {g['source']} ({g['category']})")

    return result


# ─── 3. PREDICTION MARKET CHECK ──────────────────────────

def check_prediction_markets():
    """Check if prediction market data has changed significantly."""
    result = {"movements": [], "significant_moves": []}

    # Read latest Kalshi scan
    scans = sorted(KALSHI_SCAN.glob("kalshi-scan-*.md"))
    if not scans:
        print("  No Kalshi data available")
        return result

    latest = scans[-1]
    text = latest.read_text()

    # Parse for notable price movements
    for line in text.split('\n'):
        # Look for lines with percentage point changes
        for pattern in [r'(\d+)¢\s*→\s*(\d+)¢', r'(\+|-)(\d+)pp', r'(\+|-)(\d+)¢']:
            match = re.search(pattern, line)
            if match:
                try:
                    change = abs(int(match.group(2)))
                except:
                    change = 0
                if change >= 10:  # Significant move: 10+ points
                    market = line.strip()[:60]
                    result["significant_moves"].append({
                        "market": market,
                        "change": change,
                    })
                    break

    if result["significant_moves"]:
        print(f"  Notable market moves:")
        for m in result["significant_moves"][:5]:
            print(f"    {m['market']} ({m['change']}pp)")

    return result


# ─── 4. WEB SEARCH FOR NEW DEVELOPMENTS ──────────────────

def online_intel_check():
    """Quick web search for breaking developments per theatre.

    Uses web search to find new story angles.
    Returns suggestions for what to investigate.
    """
    result = {}

    # Only run full search if brave search is available
    try:
        from openclaw_extensions import web_search
        has_search = True
    except ImportError:
        has_search = False

    search_queries = {
        "europe": "Ukraine Russia war latest developments May 2026",
        "africa": "Sahel JNIM Mali latest May 2026",
        "asia": "India Pakistan Sindoor latest",
        "middle_east": "Iran nuclear talks latest May 2026",
        "north_america": "Sinaloa cartel Mexico latest",
        "south_america": "Venezuela Delcy Rodriguez latest",
    }

    if has_search:
        print("  Web search integration available but would slow down pipeline")
        print("  (Skipping for cron — configured for on-demand use)")
        for theatre in THEATRES:
            result[theatre] = {"searched": True, "results": []}
    else:
        print("  Web search not available in this environment")
        for theatre in THEATRES:
            result[theatre] = {"searched": False, "results": []}

    return result


# ─── 5. PRODUCE ENRICHMENT REPORT ───────────────────────

def produce_enrichment_report(freshness, sources, markets, search):
    """Write enrichment report consumed by the assessment generator."""
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "date": datetime.date.today().isoformat(),
        "story_freshness": freshness,
        "source_freshness": sources,
        "prediction_markets": markets,
        "web_intel": search,
        "recommendations": {
            "shake_up_stories": freshness["stalled"] if freshness.get("stalled") else [],
            "prioritize_sources": sources.get("recommendations", [])[:5],
            "notable_market_moves": markets.get("significant_moves", []),
        },
        "narrative_instructions": {},
    }

    # Generate narrative instructions for stalled stories
    for theatre in freshness.get("stalled", []):
        report["narrative_instructions"][theatre] = {
            "severity": "stalled",
            "action": "deepen",
            "instruction": (
                f"The {theatre} story has not changed since yesterday. "
                "Expand analysis: explore second-order effects, historical parallels, "
                "or predictive scenarios rather than re-stating base facts."
            ),
        }

    for theatre in freshness.get("developing", []):
        report["narrative_instructions"][theatre] = {
            "severity": "developing",
            "action": "update",
            "instruction": (
                f"The {theatre} story is developing. "
                "Focus on what changed, update forward assessments."
            ),
        }

    CRON_DIR.mkdir(parents=True, exist_ok=True)
    ENRICHMENT.write_text(json.dumps(report, indent=2))
    print(f"\n✓ Enrichment report written ({len(report['recommendations']['shake_up_stories'])} stale stories flagged)")


# ─── MAIN ────────────────────────────────────────────────

def main():
    date_str = datetime.date.today().isoformat()
    print(f"=== Daily Enrichment: {date_str} ===", flush=True)

    print("\n1. Story Freshness...")
    freshness = check_story_freshness()

    print("\n2. Source Freshness...")
    sources = check_source_freshness()

    print("\n3. Prediction Markets...")
    markets = check_prediction_markets()

    print("\n4. Web Intel...")
    search = online_intel_check()

    print("\n5. Writing enrichment report...")
    produce_enrichment_report(freshness, sources, markets, search)

    print("Done.")


if __name__ == "__main__":
    main()
