#!/usr/bin/env python3
"""Themes pre-flight checker — validates coverage before and after brief generation.

Pre-generation:
  (a) Determine query category from input (keyword match or LLM)
  (b) Look up required/recommended themes from theme_requirements.yaml
  (c) Pass required-themes list into the analyst prompt as MANDATORY COVERAGE

Post-generation:
  (d) Validate that each required theme has substantive coverage (not just keyword mention)
  (e) If missing, surface for regeneration or flag for principal review

Usage:
    python3 analyst/themes_preflight.py --query "Brief me on Bajío industrial real estate"
    python3 analyst/themes_preflight.py --query "Brief me on Bajío industrial real estate" --brief path/to/brief.md
    python3 analyst/themes_preflight.py --query "Brief me on Bajío industrial real estate" --brief path/to/brief.md --json
    python3 analyst/themes_preflight.py --query "Brief me on Bajío industrial real estate" --brief path/to/brief.md --prompt-instruction  # outputs prompt injection text
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import yaml
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
THEME_REQUIREMENTS = REPO_ROOT / "analyst" / "config" / "theme_requirements.yaml"

# Theme keyword signatures — used for query categorization
THEME_SIGNATURES: dict[str, list[str]] = {
    "conflict_security": [
        "military", "war", "conflict", "strike", "drone", "missile",
        "offensive", "defense", "troop", "militia", "rebel", "terrorist",
        "airstrike", "shelling", "invasion", "occupation", "civil war",
        "weapon", "arms", "naval", "air force", "intelligence agency",
        "violence", "security", "attack", "armed group", "insurgency",
        "ceasefire", "peacekeeping", "peace deal", "demilitarize",
        "nuclear", "proliferation", "sanction", "embargo", "no-fly zone",
        "special forces", "mercenary", "private military", "proxy war",
        "escalation", "de-escalation", "counterterrorism", "counterinsurgency",
        "border dispute", "territorial", "annexation", "secessionist",
        "gulf", "strait", "south china sea", "east china sea", "taiwan strait",
        "black sea", "mediterranean", "red sea", "hormuz",
    ],
    "political_risk": [
        "government", "president", "parliament", "congress", "senate",
        "prime minister", "coalition", "opposition", "election", "vote",
        "coup", "protest", "regime", "authoritarian", "democracy",
        "geopolitical", "alliance", "nato", "un", "diplomatic",
        "sanction", "resolution", "summit", "treaty", "ceasefire",
        "sovereignty", "referendum", "secession", "insurgency",
        "foreign policy", "strategic", "sphere of influence", "hegemony",
        "soft power", "diplomacy", "multilateral", "bilateral",
        "policy", "regulation", "decree", "corruption",
        "human rights", "rule of law", "governance", "institution",
        "political party", "faction", "polarization", "coalition government",
        "transition", "succession", "leadership change",
    ],
    "international_relations": [
        "nato", "un", "european union", "eu", "asean", "apec",
        "g7", "g20", "g77", "oic", "african union", "arabs",
        "brics", "sc", "icc", "who", "imf", "world bank",
        "alliance", "partnership", "treaty", "pact", "agreement",
        "ambassador", "envoy", "diplomatic relations", "consulate",
        "ally", "axis", "axis of resistance", "west", "east",
        "global south", "non-aligned", "regional cooperation",
        "great power", "superpower", "middle power", "rising power",
        "deterrence", "extended deterrence", "security guarantee",
        "free trade", "economic integration", "single market",
        "visa", "travel ban", "diplomatic recognition",
    ],
    "economy_markets": [
        "economy", "market", "investment", "fdi", "gdp", "growth",
        "inflation", "interest rate", "central bank", "fiscal",
        "deficit", "debt", "yield", "treasury", "recession",
        "stimulus", "subsidy", "tariff", "trade war", "trade deficit",
        "current account", "capital flows", "portfolio", "equity",
        "bond", "commodity", "oil", "gas price", "currency",
        "dollar", "forex", "reserve", "sovereign", "credit rating",
        "supply chain", "semiconductor", "manufacturing", "industry",
        "import", "export", "trade balance", "sanctions",
        "infrastructure", "belt and road", "bri", "development bank",
        "foreign exchange", "monetary policy", "tightening", "easing",
        "safe haven", "risk asset", "flight to safety",
    ],
    "cyber_digital": [
        "cyber", "hack", "malware", "ransomware", "phishing",
        "breach", "data leak", "cyber attack", "cyber warfare",
        "cyber espionage", "cyber security", "information security",
        "digital", "ai", "artificial intelligence", "machine learning",
        "surveillance", "encryption", "quantum", "5g", "huawei",
        "tiktok", "social media", "disinformation", "misinformation",
        "deepfake", "influence campaign", "information operation",
        "critical infrastructure protection", "cyber command",
    ],
    "energy_climate": [
        "energy", "oil", "gas", "natural gas", "lng", "petroleum",
        "coal", "nuclear", "renewable", "solar", "wind", "hydro",
        "electricity", "power", "grid", "pipeline", "refinery",
        "opec", "iea", "emissions", "climate", "climate change",
        "global warming", "paris agreement", "cop", "decarbonize",
        "net zero", "green transition", "clean energy", "critical minerals",
        "lithium", "rare earth", "uranium", "cobalt", "copper",
        "energy security", "energy independence", "energy transition",
        "carbon tax", "emissions trading", "carbon border",
        "drought", "flood", "extreme weather", "food security",
        "water scarcity", "natural disaster", "sea level",
    ],
}

# Synonyms used in theme names (so code can look up by human-readable names)
CATEGORY_SYNONYMS: dict[str, list[str]] = {
    "geopolitical_intelligence_brief": ["geopolitical", "intelligence brief", "global brief", "daily brief", "world briefing", "geopolitical risk"],
    "conflict_assessment": ["conflict", "war", "fighting", "battle", "offensive", "military operation"],
    "election_monitoring": ["election", "vote", "campaign", "candidate", "polling"],
    "energy_security": ["energy security", "oil supply", "gas supply", "energy policy"],
    "cyber_threat": ["cyber", "hack", "ransomware", "cyber attack", "data breach"],
    "supply_chain_risk": ["supply chain", "logistics", "cargo", "trade route"],
    "maritime_security": ["maritime", "naval", "shipping", "sea lane", "strait"],
    "default": ["brief", "intel", "report", "summary", "overview", "update"],
}


def load_theme_requirements() -> dict[str, Any]:
    """Load theme requirements from YAML."""
    if not THEME_REQUIREMENTS.exists():
        return {"default": {"required": [], "recommended": []}, "query_categories": {}}
    with open(THEME_REQUIREMENTS) as f:
        return yaml.safe_load(f)


def resolve_query_category(query: str) -> str | None:
    """Determine query category from input text using keyword matching."""
    query_lower = query.lower()
    
    # Score each category by keyword match density
    scores: dict[str, int] = {}
    
    for category, synonyms in CATEGORY_SYNONYMS.items():
        score = 0
        for syn in synonyms:
            if syn in query_lower:
                score += len(syn.split())  # Weight multi-word matches higher
        if score > 0:
            scores[category] = score
    
    if not scores:
        # Fallback: count theme keyword matches
        for theme, keywords in THEME_SIGNATURES.items():
            for kw in keywords:
                if kw in query_lower:
                    if theme not in scores:
                        scores[theme] = 0
                    scores[theme] += 1
        
        if not scores:
            return None
        
        # Pick the highest-scoring theme as category hint
        top_theme = max(scores, key=scores.get)
        # Try to map theme back to a category
        if top_theme == "cartel_security":
            return "cartel_security_assessment"
        elif top_theme == "political_risk":
            return "political_risk_assessment"
        elif top_theme == "economy_markets":
            return "financial_markets"
        elif top_theme == "energy_infra":
            return "energy_infrastructure_investment"
        elif top_theme == "worldcup_travel":
            return "worldcup_travel_risk"
        elif top_theme == "us_mexico":
            return "usmca_review"
        return None
    
    # Return highest-scoring category
    return max(scores, key=scores.get)


def get_required_themes(category: str | None, requirements: dict[str, Any]) -> dict[str, Any]:
    """Get required and recommended themes for a query category."""
    if category and category in requirements.get("query_categories", {}):
        return requirements["query_categories"][category]
    
    # Try fuzzy match
    if category:
        for cat_name, cat_data in requirements.get("query_categories", {}).items():
            if category.lower() in cat_name.lower() or cat_name.lower() in category.lower():
                return cat_data
    
    return requirements.get("default", {"required": [], "recommended": []})


def check_theme_coverage(brief_text: str, theme: str, min_mentions: int = 3) -> tuple[bool, int]:
    """Check if a theme has substantive coverage in a brief (not just keyword mention).
    
    A theme is "covered" only if:
    1. At least min_mentions keyword hits from the theme's signature set, AND
    2. The theme appears in at least 2 paragraph headings (## or bolded section titles).
    
    Returns (has_coverage, evidence_count).
    """
    keywords = THEME_SIGNATURES.get(theme, [])
    count = 0
    for kw in keywords:
        count += len(re.findall(re.escape(kw), brief_text, re.IGNORECASE))
    
    # Check heading depth: theme keywords appearing in ## headings or bolded section headers
    heading_lines = re.findall(r'^##\s+.+$|^.{0,10}KEY JUDGMENTS|^.{0,10}ASSESSMENT', brief_text, re.MULTILINE)
    heading_text = ' '.join(heading_lines)
    heading_hits = sum(1 for kw in keywords if re.search(re.escape(kw), heading_text, re.IGNORECASE))
    
    has_coverage = (count >= min_mentions) and (heading_hits >= 2)
    return (has_coverage, count)


def generate_prompt_instruction(category: str | None, required: list[str], recommended: list[str], 
                                rationales: dict[str, str]) -> str:
    """Generate prompt injection text for mandatory coverage."""
    lines = []
    lines.append("---")
    lines.append("THEME COVERAGE REQUIREMENTS (mandatory):")
    lines.append("")
    
    if required:
        lines.append(f"Required themes: {', '.join(required)}")
        lines.append("These themes MUST have substantive coverage in your response.")
        for theme in required:
            if theme in rationales:
                lines.append(f"  - {theme}: {rationales[theme]}")
    
    lines.append("")
    if recommended:
        lines.append(f"Recommended themes: {', '.join(recommended)}")
        lines.append("These themes SHOULD be covered if the query touches them.")
        for theme in recommended:
            if theme in rationales:
                lines.append(f"  - {theme}: {rationales[theme]}")
    
    lines.append("")
    lines.append("COVERAGE VALIDATION: After writing, verify that every required theme")
    lines.append("has at least 3 substantive mentions (not just keyword drops).")
    lines.append("If a required theme is missing, regenerate with explicit instruction to cover it.")
    lines.append("---")
    
    return "\n".join(lines)


def validate_coverage(brief_text: str, required: list[str], verbose: bool = False) -> list[dict[str, Any]]:
    """Post-generation validation of theme coverage."""
    results = []
    
    for theme in required:
        has_coverage, count = check_theme_coverage(brief_text, theme)
        status = "PASS" if has_coverage else "FAIL"
        
        if verbose or status == "FAIL":
            results.append({
                "theme": theme,
                "status": status,
                "evidence_count": count,
                "min_required": 3,
                "detail": f"{count} keyword mentions ({'adequate' if has_coverage else 'BELOW MINIMUM — needs regeneration'})"
            })
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Themes pre-flight checker")
    parser.add_argument("--query", required=True, help="The user's query/prompt")
    parser.add_argument("--brief", help="Path to generated brief markdown file (post-generation check)")
    parser.add_argument("--prompt-instruction", action="store_true", help="Output prompt injection text only")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    args = parser.parse_args()
    
    requirements = load_theme_requirements()
    
    # Step 1: Resolve query category
    category = resolve_query_category(args.query)
    if args.verbose or args.json:
        print(f"Query category: {category}", file=sys.stderr if not args.json else sys.stdout)
    
    # Step 2: Look up required/recommended themes
    theme_data = get_required_themes(category, requirements)
    required = theme_data.get("required", [])
    recommended = theme_data.get("recommended", [])
    
    # Extract rationales
    rationales = {}
    for theme in required + recommended:
        key = f"rationale_{theme}"
        if key in theme_data:
            rationales[theme] = theme_data[key]
    
    # Step 3: Generate prompt instruction
    instruction = generate_prompt_instruction(category, required, recommended, rationales)
    
    if args.prompt_instruction:
        print(instruction)
        return
    
    # Step 4: Post-generation validation (if brief provided)
    results = {"category": category, "required": required, "recommended": recommended, "coverage": []}
    
    if args.brief and os.path.exists(args.brief):
        with open(args.brief) as f:
            brief_text = f.read()
        
        coverage = validate_coverage(brief_text, required, args.verbose)
        results["coverage"] = coverage
        
        missing = [c for c in coverage if c["status"] == "FAIL"]
        
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"Query category: {category or 'unresolved (using default)'}")
            print(f"Required themes: {', '.join(required) if required else '(none)'}")
            print(f"Recommended themes: {', '.join(recommended) if recommended else '(none)'}")
            print()
            print(f"Prompt instruction ({len(instruction)} chars):")
            print(instruction)
            print()
            print(f"=== Coverage Validation ===")
            for c in coverage:
                status_icon = "✅" if c["status"] == "PASS" else "❌"
                print(f"  {status_icon} {c['theme']}: {c['evidence_count']} mentions — {c['detail']}")
            
            if missing:
                print(f"\n⚠️  {len(missing)} required {'theme has' if len(missing)==1 else 'themes have'} inadequate coverage.")
                for m in missing:
                    print(f"   - {m['theme']}: {m['evidence_count']} mentions (min {m['min_required']})")
                print("   Regenerate with explicit instruction or flag for review.")
            else:
                print(f"\n✅ All required themes have adequate coverage.")
    else:
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"Query category: {category or 'unresolved (using default)'}")
            print(f"Required themes: {', '.join(required) if required else '(none)'}")
            print(f"Recommended themes: {', '.join(recommended) if recommended else '(none)'}")
            print()
            print(f"Prompt injection text ({len(instruction)} chars):")
            print(instruction)
            print()
            print("(No brief file provided — pre-generation check only. Use --brief for post-generation validation.)")
    
    # Exit with error if any required theme has inadequate coverage
    if args.brief and results.get("coverage"):
        missing = [c for c in results["coverage"] if c["status"] == "FAIL"]
        if missing:
            sys.exit(1)


if __name__ == "__main__":
    main()
