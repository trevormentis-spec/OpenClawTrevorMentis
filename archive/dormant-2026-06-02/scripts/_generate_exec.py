#!/usr/bin/env python3
"""Generate exec summary from saved regional analyses using DeepSeek Direct API."""
import json, os, sys, urllib.request

SAVE_DIR = "/home/ubuntu/trevor-briefings/2026-06-01-analysis-save"
analysis_dir = os.path.join(SAVE_DIR, "analysis")

# Load all regional analyses
regions = []
for fname in sorted(os.listdir(analysis_dir)):
    if fname.endswith(".json") and fname != "procedural-memory.md":
        with open(os.path.join(analysis_dir, fname)) as f:
            data = json.load(f)
        regions.append(data)

# Build exec summary prompt
system_prompt = """You are an intelligence analyst producing the executive summary for a daily global geopolitical briefing. You are Trevor, briefing a sophisticated principal (Roderick). You write in analyst-to-analyst voice — direct, opinionated, signal-dense.

You MUST respond ONLY with valid JSON. No prose before or after the JSON. No markdown fences.

Structure your response as a JSON object with:
- date: "2026-06-01"
- bluf: 2-3 paragraph bottom-line summary of the most important developments globally. Must cite sources inline with Admiralty ratings.
- models_used: list of models
- key_judgments: 5 key judgments across all regions, each with: id, statement, sherman_kent_band, prediction_pct, horizon_days, evidence_incident_ids, single_source_basis, confidence_in_judgment, what_would_change_it, dissenting_view
- regional_highlights: 1-2 sentence per region
- methodology_statement: brief note on collection quality
- risk_matrix: 3-5 entries with risk, region, description, likelihood, impact"""

user_prompt = f"Generate an executive summary based on these {len(regions)} regional analyses:\n\n"
for r in regions:
    region_name = r.get("region", "unknown")
    narrative = r.get("narrative", "")[:500]
    kjs = r.get("key_judgments", [])
    user_prompt += f"\n--- {region_name} ---\n"
    user_prompt += f"Narrative: {narrative}\n"
    for kj in kjs:
        user_prompt += f"KJ: {kj.get('statement','')} [{kj.get('sherman_kent_band','')} - {kj.get('prediction_pct','')}%]\n"
    user_prompt += f"\n"

user_prompt = user_prompt[:15000]

api_key = os.environ.get("DEEPSEEK_API_KEY", "")
if not api_key:
    print(json.dumps({"error": "DEEPSEEK_API_KEY not set"}))
    sys.exit(1)

payload = json.dumps({
    "model": "deepseek-v4-pro",
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ],
    "temperature": 0.3,
    "max_tokens": 8192,
}).encode()

req = urllib.request.Request(
    "https://api.deepseek.com/chat/completions",
    data=payload,
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
)

try:
    with urllib.request.urlopen(req, timeout=300) as resp:
        result = json.loads(resp.read())
    content = result["choices"][0]["message"]["content"]
    
    # Save exec summary
    output_path = os.path.join(analysis_dir, "exec_summary.json")
    try:
        exec_data = json.loads(content)
        exec_data["models_used"] = ["deepseek/deepseek-v4-pro", "deepseek/deepseek-v4-pro"]
        exec_data["tier2_provider"] = "deepseek"
        exec_data["tier1_provider"] = "deepseek"
        with open(output_path, "w") as f:
            json.dump(exec_data, f, indent=2)
        print(f"SUCCESS: Exec summary saved to {output_path}")
    except json.JSONDecodeError:
        print(f"WARNING: Response not valid JSON, saving raw")
        with open(output_path + ".txt", "w") as f:
            f.write(content)
        print(content[:500])
except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(1)
