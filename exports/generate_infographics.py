"""Generate infographic-style diagrams using OpenRouter image models."""
import json, urllib.request, os, base64, time

OUTPUT = "/home/ubuntu/.openclaw/workspace/exports/images"
api_key = os.environ.get("OPENROUTER_API_KEY", "")

def generate_image(prompt, filename, model="openai/gpt-5.4-image-2"):
    """Generate an image via OpenRouter image model."""
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": [
                {"type": "text", "text": prompt}
            ]}
        ]
    }
    
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
    
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        data = json.loads(resp.read())
        content = data['choices'][0]['message']['content']
        print(f"  Generated {filename}")
        return content
    except Exception as e:
        print(f"  ❌ {model_name}: {e}")
        return None


def generate_via_text_model(prompt, filename, model_name="openai/gpt-5.4-nano"):
    """Use a text model to generate SVG code for infographics."""
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are an expert infographic designer. Output ONLY valid SVG code. Use clean, modern design with flat vector style, professional color palette (dark navy #1a1a2e, red #c0392b, gold accents), readable typography, and clear layout."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4096
    }
    
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
    
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        data = json.loads(resp.read())
        text = data['choices'][0]['message']['content']
        
        # Extract SVG if wrapped in markdown
        import re
        svg_match = re.search(r'<svg[\s\S]*?</svg>', text)
        if svg_match:
            svg = svg_match.group(0)
        else:
            svg = text
        
        path = f"{OUTPUT}/{filename}.svg"
        with open(path, 'w') as f:
            f.write(svg)
        print(f"  ✅ Saved {filename}.svg ({len(svg)} bytes)")
        return True
    except Exception as e:
        print(f"  ❌ {model_name}: {e}")
        return False


print("Generating infographics via OpenRouter...")
os.makedirs(OUTPUT, exist_ok=True)

# 1. Strategy flow infographic (like the reference image)
generate_via_text_model(
    'Create an SVG infographic titled "Operation Epic Fury — Strategic Logic Flow". '
    'Show a clean horizontal flow: "Current Posture (Ceasefire + Blockade)" → "Trump Decision Point" → '
    'three branches: "Option A: Renewed Strikes" (red), "Option B: Sustained Blockade" (amber), '
    '"Option C: Diplomatic Off-Ramp" (green). '
    'Below, add "Critical Implications" section listing: Strait of Hormuz Closure ($124.67/bbl), '
    '400+ Militia Strikes (6 countries), Iran Retaliation Risk, Global Energy Disruption. '
    'Use dark navy background with white/gold text, red accents. Flat vector style. '
    'Dimensions: 1000x700.',
    "infographic-strategic-flow",
    model_name="openai/gpt-5.4-nano"
)

# 2. Threat landscape infographic
generate_via_text_model(
    'Create an SVG infographic titled "Threat Landscape — 1 May 2026". '
    'Show a threat matrix with 8 actors as horizontal bars: '
    'Iran (CRITICAL - red, 95%), Hezbollah (HIGH - orange, 75%), '
    'Iraqi Militias (HIGH - orange, 80%), China SCS (HIGH - blue, 70%), '
    'Cyber APTs (MODERATE - amber, 65%), Houthis (MODERATE - amber, 55%), '
    'Russia (MODERATE - blue, 50%), ISIS-K (LOW - grey, 30%). '
    'Each bar should show percentage. Use clean minimal style with dark theme. Dimensions: 800x600.',
    "infographic-threat-landscape",
    model_name="openai/gpt-5.4-nano"
)

# 3. Oil price trend infographic
generate_via_text_model(
    'Create an SVG infographic titled "Brent Crude Oil Price — Crisis Trajectory". '
    'Show a line/bar chart from Jan 2026 ($76) to May 2026 ($124.67). '
    'Mark key events: "Strikes Begin" at Feb ($82), "Hormuz Closure" at Apr ($112), '
    '"Current" at May ($124.67). Use red trending upward line. '
    'Dark theme with gold/red accents. Flat vector style. Dimensions: 800x500.',
    "infographic-oil-price",
    model_name="openai/gpt-5.4-nano"
)

# 4. I&W summary infographic
generate_via_text_model(
    'Create an SVG infographic titled "Indicators & Warnings — Summary Dashboard". '
    'Show 3 columns: "Escalation" (red badge), "De-escalation" (green badge), "Instability" (amber badge). '
    'Under each column, list 4 indicators with status dots (red=triggered, amber=watch, green=not triggered). '
    'Escalation: IRGC Signals ●, Militia Strikes ●, Naval Activity ●●, Diplomacy ●●. '
    'De-escalation: Negotiations ●, Oil Price ●, Blockade ●, Iran Signals ●. '
    'Instability: Iraq Fracture ●, Houthi Risk ●●, Cyber ●, Gulf Alignment ●●. '
    'Dark theme, flat vector, professional. Dimensions: 900x600.',
    "infographic-iw-summary",
    model_name="openai/gpt-5.4-nano"
)

print("\nDone. SVG infographics saved.")
