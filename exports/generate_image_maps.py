"""Generate infographic-style maps using OpenRouter image models."""
import json, urllib.request, os, base64, re

OUTPUT = "/home/ubuntu/.openclaw/workspace/exports/images"
api_key = os.environ.get("OPENROUTER_API_KEY", "")

def call_model(messages, model="openai/gpt-5.4-image-2", max_tokens=4096):
    """Call OpenRouter model and return text response."""
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens}
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/trevormentis-spec"
        },
        method="POST"
    )
    resp = urllib.request.urlopen(req, timeout=120)
    data = json.loads(resp.read())
    return data['choices'][0]['message']['content']


def generate_map_svg(prompt, filename):
    """Generate a map as SVG via text model."""
    text = call_model([
        {"role": "system", "content": "You are an expert infographic and map designer. Output ONLY valid SVG code. Use clean flat vector style, professional colors, readable typography, and clear layout similar to Bloomberg/Financial Times graphics."},
        {"role": "user", "content": prompt}
    ], model="openai/gpt-5.4-nano")
    
    svg_match = re.search(r'<svg[\s\S]*?</svg>', text)
    svg = svg_match.group(0) if svg_match else text
    
    path = f"{OUTPUT}/{filename}.svg"
    with open(path, 'w') as f:
        f.write(svg)
    print(f"  ✅ {filename}.svg ({len(svg)} bytes)")
    
    # Convert to PNG
    from cairosvg import svg2png
    png_path = f"{OUTPUT}/{filename}.png"
    svg2png(bytestring=svg.encode(), write_to=png_path, scale=2)
    print(f"  ✅ {filename}.png")
    return True


print("Generating infographic-style maps via OpenRouter nano...")
os.makedirs(OUTPUT, exist_ok=True)

# Map 1: Hormuz blockade
generate_map_svg(
    'Create an SVG infographic map titled "Strait of Hormuz — Blockade Enforcement Zone". '
    'Show a stylized geographic map of the Persian Gulf with: Iran at top, UAE/Saudi below, '
    'Oman to the east. Mark the Strait of Hormuz with a red hazard symbol. '
    'Show a dashed red blockade enforcement zone polygon. '
    'Add small dot markers for "42 vessels turned back" near the strait. '
    'Label key ports: Bandar Abbas, Fujairah, Khalifa Port. '
    'Add a sidebar with KEY METRICS: "42 vessels turned back, 200+ aircraft, 25 ships, Brent $124.67". '
    'Color scheme: dark background (#1a1a2e), red accents (#c0392b), gold (#c5a572), white text. '
    'Flat vector style, clean and professional like Bloomberg graphics. Dimensions: 1000x750.',
    "map-infographic-hormuz"
)

# Map 2: Militia strikes  
generate_map_svg(
    'Create an SVG infographic map titled "Iran-Aligned Militia Strikes — Regional Impact". '
    'Show a stylized map of the Middle East including Iraq, Iran, Saudi Arabia, UAE, Kuwait, Bahrain, Qatar, Jordan, Israel. '
    'Use proportional red circles on each country to show strike counts: Iraq (120), Saudi Arabia (85), UAE (60), '
    'Kuwait (55), Qatar (40), Bahrain (25), Jordan (15). '
    'Label the circles with country name and count. '
    'Add triangle markers for militia HQs in Iraq labeled "PMF", "Kata\'ib Hezbollah", "Asa\'ib Ahl al-Haq". '
    'Show an arrow from Israel to UAE labeled "Defensive weaponry delivery". '
    'Dark background, flat vector Bloomberg style. Dimensions: 1000x750.',
    "map-infographic-militia"
)

# Map 3: Global impact
generate_map_svg(
    'Create an SVG infographic map titled "Global Energy Disruption — Chokepoint Cascade". '
    'Show a stylized world map highlighting oil shipping routes from the Strait of Hormuz: '
    'Route to Europe (blue), Route to Asia-Pacific (green), Route around Africa (gold). '
    'Mark major chokepoints: Hormuz (red, "BLOCKADED"), Bab el-Mandeb (amber), '
    'Malacca Strait (amber), Turkish Straits (amber). '
    'Add impact annotations for: Europe (Gas +70%), Japan/Korea (LNG +45%), '
    'South Asia (fuel crisis), Americas ($124.67/bbl inflation). '
    'Dark background, flat vector, Bloomberg style. Dimensions: 1100x700.',
    "map-infographic-global"
)

print("\nDone! Maps generated.")
