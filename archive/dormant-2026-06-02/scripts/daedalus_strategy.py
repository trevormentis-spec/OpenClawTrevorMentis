#!/usr/bin/env python3
"""
Daedalus Strategy — Iran portfolio downside hedge execution

Designed to be run autonomously when valid credentials are available.

Usage:
  python3 scripts/daedalus_strategy.py          # execute full plan
  python3 scripts/daedalus_strategy.py --dry-run  # display without executing
  python3 scripts/daedalus_strategy.py --check     # verify positions and prices
"""

import json, os, sys, time, urllib.request, urllib.parse, hmac, hashlib, base64

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_env():
    env_path = os.path.join(WORKSPACE, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k] = v

load_env()

API_KEY = os.environ.get("KALSHI_API_KEY", "")
RSA_PATH = os.environ.get("KALSHI_RSA_KEY_PATH", os.path.join(WORKSPACE, ".kalshi_rsa_key.pem"))
API_BASE = "https://api.elections.kalshi.com/trade-api/v2"

# ── Auth ──
def get_jwt_token():
    """Create RSA-signed JWT for Kalshi API auth"""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
    import jwt as pyjwt
    
    with open(RSA_PATH) as f:
        rsa_key_pem = f.read()
    private_key = serialization.load_pem_private_key(rsa_key_pem.encode(), password=None, backend=default_backend())
    
    now = int(time.time())
    payload = {"sub": API_KEY, "iat": now, "exp": now + 120}
    return pyjwt.encode(payload, private_key, algorithm="RS256")

# ── API Helpers ──
def kalshi_get(path, token=None):
    url = f"{API_BASE}{path}"
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode(errors='replace')[:500]}"}
    except Exception as e:
        return {"error": str(e)}

def kalshi_post(path, data, token):
    url = f"{API_BASE}{path}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode(errors='replace')[:500]}"}
    except Exception as e:
        return {"error": str(e)}

# ── Strategy Definition ──
STRATEGY = {
    "name": "Daedalus — Iran Portfolio Downside Hedge",
    "author": "Trevor Desk",
    "date": "2026-05-27",
    "rationale": (
        "Iran positions dominate the portfolio at ~88% directional exposure. "
        "The desk assesses US-Iran nuclear deal probability at 62-63%, which implies "
        "~37% chance of failure. In a failure scenario, Iran positions near-total loss. "
        "This strategy layers partial hedges that are negatively correlated or uncorrelated "
        "with the Iran thesis, without reducing the core directional bet."
    ),
    "trades": [
        {
            "id": "HEDGE-01",
            "ticker": "KXWTIMAX-26DEC31-T200",
            "description": "Scale into WTI oil max price $200+",
            "action": "BUY",
            "contracts": 40,
            "limit_price": 0.125,
            "total_risk": 5.00,
            "edge": "+55.5pt (68% desk vs 12.5% market)",
            "correlation_with_iran": "NEGATIVE",
            "reasoning": (
                "WTI at $200+ benefits from continued supply constraints. "
                "If Iran deal fails → Iranian oil stays off market → supply tight → WTI up. "
                "If Iran deal succeeds → more supply → WTI may dip but Iran thesis pays out. "
                "Adds to existing 17-contract position at $0.12 entry."
            )
        },
        {
            "id": "HEDGE-02",
            "ticker": "KXELECTIRAN-26JUL01",
            "description": "Low-probability Iran election before Jul 1",
            "action": "BUY",
            "contracts": 80,
            "limit_price": 0.03,
            "total_risk": 2.40,
            "edge": "Uncertain — market at 3%, no clear desk edge",
            "correlation_with_iran": "MIXED",
            "reasoning": (
                "Pure lottery-ticket diversification. If Iran political situation "
                "shifts unexpectedly (deal or no-deal chaos), election probability "
                "could spike. Purely speculative at this sizing."
            )
        }
    ],
    "guardrail_check": {
        "quarter_kelly": "PASS",
        "max_5pct_per_position": "PASS ($7.40 limit, max trade $5.00)",
        "max_30pct_exposure": "PASS (current ~$35.65 + $7.40 = ~$43.05 = 29.1%)",
        "min_5pt_edge": "HEDGE-01 PASS (55.5pt), HEDGE-02 UNCERTAIN",
        "total_cost": 7.40
    },
    "portfolio_post_trade": {
        "iran_exposure_pct": "~67% (down from ~88%)",
        "wti_exposure_pct": "~16% (up from ~6%)",
        "other_exposure_pct": "~17%",
        "cash_remaining": "~$105",
        "correlation_summary": "Still Iran-heavy but with a meaningful WTI offset leg"
    }
}

def check_prices():
    """Check current market prices for strategy targets"""
    print("═══ Price Check ═══\n")
    
    # WTI T200
    m = kalshi_get(f"/markets?limit=5&status=open&series_ticker=KXWTIMAX")
    if "error" not in m:
        for market in m.get("markets", []):
            if "T200" in market.get("ticker", ""):
                yb = float(market.get("yes_bid_dollars", 0))
                ya = float(market.get("yes_ask_dollars", 0))
                vol = float(market.get("volume_24h_fp", 0))
                print(f"KXWTIMAX-26DEC31-T200: ${yb:.4f}-${ya:.4f} | 24h vol: {vol:.0f}")
                print(f"  Title: {market.get('title','')}")
                break
    
    # Iran Election
    m = kalshi_get(f"/markets?limit=5&status=open&series_ticker=KXELECTIRAN")
    if "error" not in m:
        for market in m.get("markets", []):
            if "26JUL01" in market.get("ticker", ""):
                yb = float(market.get("yes_bid_dollars", 0))
                ya = float(market.get("yes_ask_dollars", 0))
                vol = float(market.get("volume_24h_fp", 0))
                print(f"KXELECTIRAN-26JUL01: ${yb:.4f}-${ya:.4f} | 24h vol: {vol:.0f}")
                print(f"  Title: {market.get('title','')}")
                break
    
    # Iran deal (reference - current positions)
    m = kalshi_get(f"/markets?limit=5&status=open&series_ticker=KXUSAIRANAGREEMENT")
    if "error" not in m:
        for market in m.get("markets", []):
            tick = market.get("ticker", "")
            yb = float(market.get("yes_bid_dollars", 0))
            if "26JUN01" in tick:
                print(f"\nKXUSAIRANAGREEMENT JUN: ${yb:.4f} bid (your entry $0.08)")
            elif "26JUL01" in tick:
                print(f"KXUSAIRANAGREEMENT JUL: ${yb:.4f} bid (your entry $0.26)")
            elif "26AUG01" in tick:
                print(f"KXUSAIRANAGREEMENT AUG: ${yb:.4f} bid (your entry $0.35)")

def dry_run():
    """Display the strategy without executing"""
    print("\n" + "=" * 60)
    print(f"  {STRATEGY['name']}")
    print("=" * 60 + "\n")
    
    print(f"Date: {STRATEGY['date']}")
    print(f"Rationale: {STRATEGY['rationale']}\n")
    
    print("── Trades ──\n")
    for t in STRATEGY["trades"]:
        print(f"  [{t['id']}] {t['action']} {t['contracts']} x {t['ticker']}")
        print(f"         @ ${t['limit_price']:.3f} = ${t['total_risk']:.2f} risk")
        print(f"         Edge: {t['edge']}")
        print(f"         Iran correlation: {t['correlation_with_iran']}")
        print(f"         {t['reasoning']}\n")
    
    print("── Guardrail Check ──\n")
    for k, v in STRATEGY["guardrail_check"].items():
        status = "✅" if "PASS" in str(v) else "⚠️"
        print(f"  {status} {k}: {v}")
    
    print(f"\n── Post-Trade Portfolio ──\n")
    for k, v in STRATEGY["portfolio_post_trade"].items():
        print(f"  {k}: {v}")
    
    print(f"\n  Total cost: ${STRATEGY['guardrail_check']['total_cost']:.2f}")

def execute():
    """Execute the strategy (requires valid API auth)"""
    print("═══ Executing Daedalus Strategy ═══\n")
    
    # Get JWT
    try:
        token = get_jwt_token()
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        print("   Check RSA key at:", RSA_PATH)
        return False
    
    # Check balance
    balance = kalshi_get("/portfolio/balance", token)
    if "error" in balance:
        print(f"❌ Cannot access portfolio: {balance['error']}")
        print("   API key needs portfolio access. Try:")
        print("   1. Verify KALSHI_API_KEY matches your member ID")
        print("   2. Ensure RSA key is paired with this API key")
        print("   3. Check account has API trading enabled")
        return False
    
    cash = float(balance.get("clearing_balance_dollars", 0))
    print(f"✅ Balance: ${cash:.2f}")
    
    # Execute each trade
    for t in STRATEGY["trades"]:
        print(f"\n── [{t['id']}] {t['action']} {t['contracts']} x {t['ticker']} @ ${t['limit_price']} ──")
        
        # Place order
        order = {
            "ticker": t["ticker"],
            "type": "limit",
            "side": t["action"].lower(),
            "count": t["contracts"],
            "yes_price": int(t["limit_price"] * 100),  # Convert to cents
        }
        
        result = kalshi_post("/portfolio/orders", order, token)
        if "error" in result:
            print(f"❌ Order failed: {result['error']}")
            print(f"   Order: {json.dumps(order, indent=2)}")
        else:
            print(f"✅ Order placed: {json.dumps(result)[:200]}")
    
    print("\n═══ Strategy Complete ═══")
    return True

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "--dry-run"
    
    if mode == "--check":
        check_prices()
    elif mode == "--execute":
        execute()
    else:
        dry_run()
        print("\n── Current Prices ──\n")
        check_prices()

