"""Call OpenRouter GPT-5.5 Pro to generate improved maps code."""
import json, urllib.request, os, re

api_key = os.environ.get("OPENROUTER_API_KEY") or os.popen("env | grep OPENROUTER").read().strip().split("=", 1)[1]

payload = {
    "model": "openai/gpt-5.5-pro",
    "messages": [
        {"role": "system", "content": "You are a data visualization designer for the Financial Times. Output ONLY valid Python code."},
        {"role": "user", "content": """Write a complete Python script using matplotlib + cartopy that generates 4 professional geopolitical maps in Financial Times newspaper style.

FT DESIGN SPECS:
- Background: #F5F3EF (warm cream)
- Ocean: #E8E2D8 (very light warm grey-brown)
- Land: #F0ECE3 (slightly lighter cream)
- Borders: #D5CCC0, linewidth=0.4
- Coastlines: #B8AFA0, linewidth=0.5
- FT Red: #C0392B
- FT Blue: #1B3A5C
- Title: 11pt bold Arial/Helvetica, LEFT aligned at top-left
- Subtitle: 7.5pt #888 below title
- NO background gridlines on maps (remove or alpha=0.1)
- Labels: 7pt #555
- Source: 5.5pt italic #999 bottom-left
- Thin leader lines for annotations
- DPI: 300
- Keep clean, minimal, professional
- Use tight_layout with pad=0

4 maps to generate:

1. hormuz_blockade: Strait of Hormuz (extent [42, 62, 22, 30])
   - Show blockade zone as hatched/transparent red polygon
   - 42 vessel turn-backs as small dots
   - Label: Bandar Abbas, Fujairah, Khalifa Port
   - Metric sidebar box (42 vessels turned back, 200 aircraft, 25 ships, Brent $124.67)
   - '#39;s' marker at Hormuz strait

2. militia_strikes: Regional strikes (extent [32, 62, 20, 38])
   - Proportional circles for strike counts per country
   - Militia base markers (triangles) in Iraq
   - Israel-UAE weapons flow arrow
   - Legend for circle sizes

3. global_impact: Robinson projection global map
   - Show oil shipping routes from Hormuz to Europe, Asia, Africa
   - Mark chokepoints (Hormuz, Bab el-Mandeb, Malacca, Turkish Straits)
   - Annotate regional impacts

4. ukraine_gulf: Ukraine-Gulf partnerships (extent [20, 60, 20, 55])
   - Ukraine marker with anti-drone specialist note
   - Gulf state markers with status badges
   - Connection lines with thin styling

Output ONLY valid Python code with no markdown formatting."""}
    ],
    "max_tokens": 8192
}

req = urllib.request.Request(
    "https://openrouter.ai/api/v1/chat/completions",
    data=json.dumps(payload).encode(),
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    method="POST"
)

try:
    resp = urllib.request.urlopen(req, timeout=120)
    data = json.loads(resp.read())
    text = data['choices'][0]['message']['content']
    text = re.sub(r'^```python\n?', '', text)
    text = re.sub(r'^```\n?', '', text)
    text = re.sub(r'\n?```$', '', text)
    
    path = "/home/ubuntu/.openclaw/workspace/exports/generate_maps_v2.py"
    with open(path, 'w') as f:
        f.write(text)
    print(f"✅ Generated {text.count(chr(10)) + 1} lines to generate_maps_v2.py")
    
    # Check for obvious syntax issues
    import py_compile
    try:
        py_compile.compile(path, doraise=True)
        print("✅ Python syntax check passed")
    except py_compile.PyCompileError as e:
        print(f"⚠️ Syntax error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
