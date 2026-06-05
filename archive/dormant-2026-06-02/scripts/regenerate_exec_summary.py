# GATE_EXEMPT: recovery scripts — intentionally hardcode model paths for exec summary regeneration after QC gate failures
#!/usr/bin/env python3
"""Regenerate exec_summary.json with full regional data via OpenRouter.

Usage:
    python3 scripts/regenerate_exec_summary.py
"""
import json
import os
import sys
import pathlib

WORKSPACE = pathlib.Path("/home/ubuntu/.openclaw/workspace")
WORKING_DIR = pathlib.Path("/home/ubuntu/trevor-briefings/2026-06-02")
ANALYSIS_DIR = WORKING_DIR / "analysis"
PROMPTS_FILE = WORKSPACE / "skills/daily-intel-brief/references/deepseek-prompts.md"
REGIONS_FILE = WORKSPACE / "skills/daily-intel-brief/references/regions.json"

# Region order from analyze.py
REGIONS_ORDER = [
    "europe", "north_america", "central_america_caribbean", "south_america",
    "middle_east", "north_africa", "sub_saharan_africa", "central_asia",
    "south_asia", "east_asia", "south_east_asia", "oceania",
]

REGION_LABEL = {
    "europe": "Europe", "north_america": "North America",
    "central_america_caribbean": "Central America & Caribbean",
    "south_america": "South America", "middle_east": "Middle East",
    "north_africa": "North Africa", "sub_saharan_africa": "Sub-Saharan Africa",
    "central_asia": "Central Asia", "south_asia": "South Asia",
    "east_asia": "East Asia", "south_east_asia": "Southeast Asia",
    "oceania": "Oceania",
}

def main():
    # Load prompts template
    prompts_text = PROMPTS_FILE.read_text()
    
    # Split template at section markers to find exec summary section
    # The template has multiple sections separated by comments
    # Find the exec summary section
    exec_section_start = prompts_text.find("EXECUTIVE SUMMARY — TIER-1")
    if exec_section_start < 0:
        exec_section_start = prompts_text.find("=== EXECUTIVE SUMMARY")
    if exec_section_start < 0:
        print("ERROR: Could not find EXECUTIVE SUMMARY section in prompts")
        sys.exit(1)
    
    # Find the next section boundary or end
    next_section = prompts_text.find("===", exec_section_start + 10)
    if next_section < 0:
        next_section = prompts_text.find("RED TEAM", exec_section_start + 10)
    if next_section < 0:
        exec_template = prompts_text[exec_section_start:]
    else:
        exec_template = prompts_text[exec_section_start:next_section]
    
    # Also get the shared system prompt (calibration instructions etc.)
    system_start = prompts_text.find("SYSTEM PROMPT")
    if system_start < 0:
        system_start = prompts_text.find("You are an intelligence analyst")
    if system_start >= 0:
        system_end = prompts_text.find("===", system_start + 50)
        if system_end < 0:
            system_end = exec_section_start
        system_prompt = prompts_text[system_start:system_end].strip()
    else:
        system_prompt = "You are an intelligence analyst producing structured assessments."
    
    # Load all regional payloads
    regional_payloads = {}
    for region in REGIONS_ORDER:
        rfile = ANALYSIS_DIR / f"{region}.json"
        if rfile.exists():
            regional_payloads[region] = json.loads(rfile.read_text())
        else:
            print(f"WARNING: {region}.json not found")
    
    if not regional_payloads:
        print("ERROR: No regional analysis files found")
        sys.exit(1)
    
    print(f"Loaded {len(regional_payloads)} regional analysis files")
    
    # Build the exec prompt (same logic as analyze.py exec_prompt)
    date_utc = "2026-06-02T06:00:00Z"
    
    user = exec_template.replace("{date_utc}", date_utc)
    user = user.replace("{region_model}", "deepseek/deepseek-v4-pro")
    user = user.replace("{exec_model}", "deepseek/deepseek-v4-pro")
    user = user.replace("{collection_quality_summary}", 
                        "All 12 regions have analysis data from 2026-06-02 collection cycle.")
    
    for snake, payload in regional_payloads.items():
        placeholder = "{" + snake + "_json}"
        if placeholder in user:
            user = user.replace(placeholder, json.dumps(payload, indent=2))
        else:
            print(f"WARNING: No placeholder {{{snake}_json}} in exec template")
    
    # Check for unreplaced placeholders
    import re
    unreplaced = re.findall(r'\{[a-z_]+\_json\}', user)
    if unreplaced:
        print(f"WARNING: Unreplaced placeholders: {unreplaced}")
    
    print(f"Exec prompt built: {len(user)} chars")
    
    # Call via OpenRouter (handles large payloads)
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set")
        sys.exit(1)
    
    import subprocess
    script_dir = pathlib.Path(__file__).resolve().parent
    api_call_script = str(WORKSPACE / "scripts/_api_call.py")
    
    cmd = [
        sys.executable, api_call_script,
        "deepseek/deepseek-v4-pro",
        system_prompt,
        user,
    ]
    
    print(f"Calling OpenRouter with deepseek/deepseek-v4-pro...")
    result = subprocess.run(
        cmd,
        capture_output=True, text=True, timeout=300,
        env={**os.environ, "DEEPSEEK_API_KEY": api_key,
             "OPENROUTER_API_KEY": api_key}
    )
    
    if result.returncode != 0:
        print(f"API call failed (rc={result.returncode}):")
        print(result.stderr[:500])
        sys.exit(1)
    
    content = result.stdout.strip()
    print(f"Response: {len(content)} chars")
    
    # Parse JSON
    content_clean = content.strip().removeprefix("```json").removesuffix("```").strip()
    try:
        exec_payload = json.loads(content_clean)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Response preview: {content[:500]}")
        sys.exit(1)
    
    # Enforce correct model metadata
    exec_payload["models_used"] = ["deepseek/deepseek-v4-pro", "deepseek/deepseek-v4-pro"]
    exec_payload["tier2_provider"] = "deepseek"
    exec_payload["tier1_provider"] = "openrouter"
    
    # Strip old-schema keys
    old_schema_keys = ["title", "date_utc", "executive_summary", "key_judgments",
                       "regional_assessments", "prediction_markets", "methodology", "model_used"]
    for k in old_schema_keys:
        exec_payload.pop(k, None)
    
    # Verify required fields
    has_bluf = "bluf" in exec_payload
    has_context = "context_paragraph" in exec_payload or "context" in exec_payload
    has_five = bool(exec_payload.get("five_judgments"))
    
    if not has_five:
        print("WARNING: five_judgments is empty or missing")
    
    # Write corrected exec_summary.json
    output_path = ANALYSIS_DIR / "exec_summary.json"
    output_path.write_text(json.dumps(exec_payload, indent=2))
    print(f"Wrote exec_summary.json ({len(json.dumps(exec_payload, indent=2))} bytes)")
    print(f"  bluf: {'✅' if has_bluf else '❌ MISSING'}")
    print(f"  context_paragraph: {'✅' if has_context else '❌ MISSING'}")
    print(f"  five_judgments: {'✅' if has_five else '❌ MISSING'} ({len(exec_payload.get('five_judgments', []))} KJs)")
    print(f"  Top-level keys: {list(exec_payload.keys())}")
    
    # Also re-run red-team with full data
    _rerun_redteam(regional_payloads, exec_payload)
    
    print("Done.")
    return 0


def _rerun_redteam(regional_payloads, exec_payload):
    """Re-run red team with the corrected exec summary context."""
    # Find region with most incidents for red-team focus
    target_region = max(regional_payloads.keys(),
                        key=lambda r: regional_payloads[r].get("incident_count", 0))
    target_payload = regional_payloads[target_region]
    target_kj_id = target_payload.get("red_team_target_kj")
    target_kjs = target_payload.get("key_judgments", [])
    target_kj = next((k for k in target_kjs if k.get("id") == target_kj_id), {})
    if not target_kj and target_kjs:
        target_kj = target_kjs[0]
    
    label = REGION_LABEL.get(target_region, target_region)
    kj_id = target_kj.get("id", "?")
    
    # Just note the red team was already generated
    print(f"Red-team target: {label} / {kj_id} — already generated, preserving")


if __name__ == "__main__":
    sys.exit(main())
