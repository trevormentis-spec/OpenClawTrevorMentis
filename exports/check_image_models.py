"""Check available image generation models on OpenRouter."""
import json, urllib.request, os

api_key = os.environ.get("OPENROUTER_API_KEY", "")
req = urllib.request.Request(
    "https://openrouter.ai/api/v1/models",
    headers={"Authorization": f"Bearer {api_key}"}
)
data = json.loads(urllib.request.urlopen(req).read())
models = data.get("data", [])

tags = ["image", "dalle", "flux", "midjourney", "stable", "sdxl", "pixel", "nano"]
img = [m for m in models if any(t in m.get("id", "").lower() for t in tags)]

print(f"Found {len(img)} image/nano-related models:")
for m in img:
    p = m.get("pricing", {})
    pid = m["id"]
    prompt_price = p.get("prompt", "?")
    image_price = p.get("image", "?")
    print(f"  {pid} | prompt=${prompt_price} | image=${image_price}")
