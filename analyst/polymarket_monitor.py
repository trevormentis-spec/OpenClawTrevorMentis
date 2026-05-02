#!/usr/bin/env python3
"""Monitor Polymarket tracked markets for price movement >10%.

Correct API path: GET /markets?slug={slug} returns outcomePrices = [Yes, No].
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

SCAN_FILE = os.path.expanduser("~/.openclaw/workspace/analyst/polymarket-scan.json")
STATE_FILE = os.path.expanduser("~/.openclaw/workspace/analyst/polymarket-price-state.json")
GAMMA_BASE = "https://gamma-api.polymarket.com"

def fetch_json(url, retries=2):
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TrevorBot/1.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if attempt < retries:
                time.sleep(1)
                continue
            return {"error": str(e)}

def main():
    if not os.path.exists(SCAN_FILE):
        print(json.dumps({"error": "Scan file not found"}))
        sys.exit(1)

    with open(SCAN_FILE) as f:
        scan = json.load(f)

    recommendations = scan.get("recommendations", [])
    slugs = [r["market_slug"] for r in recommendations]

    # Build a lookup from the scan data: slug -> {no_price, yes_price, question}
    scan_prices = {}
    for r in recommendations:
        scan_prices[r["market_slug"]] = {
            "no": r.get("no_price_current"),
            "yes": r.get("yes_price_current"),
            "question": r.get("question", r["market_slug"]),
        }

    # Load previous price state (from last monitor run, NOT the scan)
    prev_state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            prev_state = json.load(f)

    print(f"Querying {len(slugs)} tracked markets via Gamma API...", file=sys.stderr)

    current_prices = {}
    errors = []

    for i, slug in enumerate(slugs):
        if i > 0 and i % 15 == 0:
            print(f"  ... {i}/{len(slugs)}", file=sys.stderr)

        data = fetch_json(f"{GAMMA_BASE}/markets?slug={slug}")
        if isinstance(data, dict) and "error" in data:
            print(f"  ERROR {slug}: {data['error']}", file=sys.stderr)
            errors.append(slug)
            continue

        if not data or not isinstance(data, list) or len(data) == 0:
            print(f"  No data for {slug}", file=sys.stderr)
            continue

        # Get the specific market matching the slug
        market = None
        for m in data:
            if m.get("slug") == slug:
                market = m
                break
        if not market:
            market = data[0]

        outcomes = market.get("outcomes", "[]")
        if isinstance(outcomes, str):
            outcomes = json.loads(outcomes)
        outcome_prices_raw = market.get("outcomePrices", "[]")
        if isinstance(outcome_prices_raw, str):
            outcome_prices = json.loads(outcome_prices_raw)
        else:
            outcome_prices = outcome_prices_raw

        if len(outcome_prices) < 2:
            continue

        # outcomes tells us the order: e.g. ["Yes", "No"] => idx0=Yes, idx1=No
        yes_idx = 0
        no_idx = 1
        if outcomes and len(outcomes) >= 2:
            if outcomes[0].lower() == "no":
                yes_idx, no_idx = 1, 0

        yes_price = float(outcome_prices[yes_idx])
        no_price = float(outcome_prices[no_idx])
        question = market.get("question", slug)

        current_prices[slug] = {
            "no": no_price,
            "yes": yes_price,
            "question": question,
            "liquidity": market.get("liquidity"),
            "volume": market.get("volume"),
            "query_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        time.sleep(0.15)

    # Compare current API prices with both:
    # 1) previous monitor-run state (for >10% movement detection)
    # 2) scan file baseline (first run reference)
    movements = []

    # Use either prev_state (from previous monitor runs) or scan_prices as baseline
    for slug, cur in current_prices.items():
        baseline = prev_state.get(slug) or scan_prices.get(slug, {})
        prev_no = baseline.get("no")

        if prev_no is not None and prev_no > 0:
            change = abs(cur["no"] - prev_no)
            pct_change = change / prev_no * 100

            if pct_change > 10:
                direction = "📈 UP" if cur["no"] > prev_no else "📉 DOWN"
                movements.append({
                    "slug": slug,
                    "question": cur["question"],
                    "old_no": round(prev_no, 3),
                    "new_no": round(cur["no"], 3),
                    "change_pct": round(pct_change, 1),
                    "direction": direction
                })

    # For first run: note which slugs are new vs existed
    is_first_run = len(prev_state) == 0
    new_slugs = [s for s in current_prices if s not in prev_state]

    # Save current state
    with open(STATE_FILE, "w") as f:
        json.dump(current_prices, f, indent=2)

    result = {
        "scanned": len(current_prices),
        "errors": len(errors),
        "prev_tracked": len(prev_state),
        "is_first_run": is_first_run,
        "movements_count": len(movements),
        "movements": movements,
        "new_markets": len(new_slugs) if is_first_run else 0,
        "query_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
