#!/usr/bin/env python3
"""Set up Stripe subscription product for Daily OSINT Brief.

Usage:
    export STRIPE_SECRET_KEY=sk_live_...
    python3 scripts/setup-stripe-product.py

Creates:
    - Product: "Daily OSINT Briefing"
    - Price: $19/month (recurring)
"""
import json
import os
import sys
from urllib.request import Request, urlopen

API_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
if not API_KEY:
    print("❌ STRIPE_SECRET_KEY not set")
    sys.exit(1)

BASE = "https://api.stripe.com/v1"
AUTH = f"Bearer {API_KEY}"

def stripe_post(path, data):
    req = Request(f"{BASE}{path}", data.encode(), {"Authorization": AUTH})
    with urlopen(req) as r:
        return json.loads(r.read())

# Create product
print("📦 Creating Stripe product...")
product = stripe_post("/products", "name=Daily OSINT Briefing&description=Automated daily open-source intelligence analysis with calibrated judgments, 6-region coverage, and professional PDF exports.")
print(f"   Product ID: {product['id']} | Name: {product['name']}")

# Create price ($19/month)
print("💰 Creating $19/month price...")
price = stripe_post("/prices", f"product={product['id']}&unit_amount=1900&currency=usd&recurring[interval]=month")
print(f"   Price ID: {price['id']} | {price['unit_amount']/100} {price['currency']}/month")

# Create payment link
print("🔗 Creating payment link...")
link = stripe_post("/payment_links", f"line_items[0][price]={price['id']}&line_items[0][quantity]=1")
print(f"   Payment link: {link['url']}")

print()
print("✅ Stripe setup complete!")
print(f"   Subscribe at: {link['url']}")
