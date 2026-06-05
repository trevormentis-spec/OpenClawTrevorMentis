#!/usr/bin/env python3
"""Standalone API call script — called by analyze.py via subprocess for reliable timeout."""
import json, os, sys, urllib.request

model = sys.argv[1]
system = sys.argv[2]
user = sys.argv[3]
temperature = float(sys.argv[4])
max_tokens = int(sys.argv[5])
provider = sys.argv[6]
max_input_chars = int(sys.argv[7]) if len(sys.argv) > 7 else 18000

# Truncate if needed
if len(user) > max_input_chars:
    user = user[:max_input_chars] + f"\n\n[TRUNCATED — {len(user) - max_input_chars} chars omitted]"

# Get API key
if provider == "deepseek":
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    base_url = "https://api.deepseek.com"
    api_model = model.split("/", 1)[-1] if "/" in model else model
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
elif provider == "openrouter":
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    base_url = "https://openrouter.ai/api/v1"
    api_model = model
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/trevormentis-spec",
        "X-Title": "TREVOR Intel Brief",
    }
else:
    print(json.dumps({"error": f"Unknown provider: {provider}"}))
    sys.exit(1)

payload = json.dumps({
    "model": api_model,
    "messages": [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ],
    "temperature": temperature,
    "max_tokens": max_tokens,
}).encode()

req = urllib.request.Request(
    f"{base_url}/chat/completions",
    data=payload,
    headers=headers,
)

try:
    with urllib.request.urlopen(req, timeout=600) as resp:
        result = json.loads(resp.read())
    content = result["choices"][0]["message"]["content"]
    print(json.dumps({"success": True, "content": content}))
except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(1)
