#!/usr/bin/env python3
"""
Query Claude Opus 4.7 via OpenRouter for map design recommendations
for each of the 6 theatre analyses.
"""
import json
import os
import sys
import urllib.request
import urllib.error

# Load .env
env_path = os.path.expanduser("~/.openclaw/workspace/.env")
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ[k] = v

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-opus-4.7"

REGIONS = ["europe", "asia", "middle_east", "north_america", "south_central_america", "global_finance"]
ANALYSIS_DIR = os.path.expanduser("~/trevor-briefings/2026-05-10/analysis")

def load_analysis(region):
    path = os.path.join(ANALYSIS_DIR, f"{region}.json")
    with open(path) as f:
        return json.load(f)

def build_prompt(data):
    narrative = data.get("narrative", "")
    story = data.get("story", "")
    kjs = data.get("key_judgments", [])
    kj_text = "\n".join(f"- KJ: {k['statement']} [{k['sherman_kent_band']}, {k['prediction_pct']}%]" for k in kjs)
    btn = data.get("by_the_numbers", [])
    btn_text = "\n".join(f"- {item}" for item in btn)
    
    return f"""You are a map designer for an intelligence briefing. You have been given the analysis text for a specific theatre.

Read the text below and answer these questions:

1. WOULD A MAP ILLUMINATE THIS STORY? Answer YES or NO. If NO, explain why not and skip the rest.
2. If YES, what specific data points should the map show? List exact numbers, locations, routes, infrastructure.
3. What geographic area and zoom level would best frame this story?
4. What additional data would you need to collect to make this map useful? (e.g., "Brent crude prices for last 7 days", "troop positions", "shipping traffic data")
5. What would the map look like? Describe the visual layout — what goes where.

Here is the analysis:

NARRATIVE:
{narrative}

STORY CONTEXT:
{story}

KEY JUDGMENTS:
{kj_text}

BY THE NUMBERS:
{btn_text}

Respond in a structured format.
"""

def query_claude(region, data):
    prompt = build_prompt(data)
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1500,
        "temperature": 0.3,
    }
    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=req_data,
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/trevormentis-spec",
            "X-Title": "Trevor Intel Brief Map Designer",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})
            print(f"[{region}] Tokens: {usage.get('total_tokens', '?')}", file=sys.stderr)
            return content
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[{region}] HTTP Error {e.code}: {body}", file=sys.stderr)
        return f"ERROR: {e.code} - {body}"
    except Exception as e:
        print(f"[{region}] Error: {e}", file=sys.stderr)
        return f"ERROR: {e}"

def main():
    print("=== Querying Claude Opus 4.7 for map designs ===", file=sys.stderr)
    
    if not OPENROUTER_KEY:
        print("ERROR: No OPENROUTER_API_KEY found", file=sys.stderr)
        return 1
    
    results = {}
    for region in REGIONS:
        print(f"\n[{region}] Querying...", file=sys.stderr)
        data = load_analysis(region)
        response = query_claude(region, data)
        results[region] = response
        print(f"[{region}] Done.", file=sys.stderr)
    
    # Save results
    out_dir = os.path.expanduser("~/trevor-briefings/2026-05-10")
    exports_dir = os.path.expanduser("~/.openclaw/workspace/exports/comparisons")
    os.makedirs(exports_dir, exist_ok=True)
    
    out_path = os.path.join(exports_dir, "map-design-plan.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved to {out_path}", file=sys.stderr)
    
    # Print summary
    for region in REGIONS:
        resp = results.get(region, "")
        first_line = resp.strip().split("\n")[0] if resp else "NO RESPONSE"
        print(f"  {region}: {first_line[:80]}...")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
