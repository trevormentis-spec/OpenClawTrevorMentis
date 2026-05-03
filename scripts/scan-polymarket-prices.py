#!/usr/bin/env python3
"""Query Polymarket Gamma API for tracked markets and compare prices to last scan."""

import json
import sys
import urllib.request
import urllib.error
import time

SCAN_FILE = "/home/ubuntu/.openclaw/workspace/analyst/polymarket-scan.json"
GAMMA_BASE = "https://gamma-api.polymarket.com/markets"
BATCH_DELAY = 0.15  # 150ms between requests to be polite
MOVEMENT_THRESHOLD = 0.10  # 10%

def fetch_json(url, retries=2):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "TrevorBot/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                return None

def main():
    # Load stored scan data
    with open(SCAN_FILE) as f:
        scan_data = json.load(f)

    stored = {}
    for r in scan_data.get("recommendations", []):
        slug = r["market_slug"]
        stored[slug] = {
            "question": r.get("question", slug),
            "no_price": r.get("no_price_current"),
            "yes_price": r.get("yes_price_current"),
        }

    slugs = list(stored.keys())
    total = len(slugs)
    print(f"📊 Scanning {total} tracked Polymarket markets for price movement...\n", flush=True)

    movements = []
    errors = []
    checked = 0

    for i, slug in enumerate(slugs):
        url = f"{GAMMA_BASE}?slug={slug}&closed=false"
        data = fetch_json(url)

        if data is None:
            errors.append(slug)
            continue

        # Gamma returns an array; pick first match
        market = data[0] if isinstance(data, list) and len(data) > 0 else data
        if not market or not isinstance(market, dict):
            errors.append(slug)
            continue

        outcome_prices = market.get("outcomePrices")
        if not outcome_prices or not isinstance(outcome_prices, (list, str)):
            errors.append(slug)
            continue

        # Parse outcomePrices - it could be JSON string or already a list
        if isinstance(outcome_prices, str):
            try:
                outcome_prices = json.loads(outcome_prices)
            except json.JSONDecodeError:
                errors.append(slug)
                continue

        if len(outcome_prices) < 2:
            errors.append(slug)
            continue

        try:
            new_yes = float(outcome_prices[0])
            new_no = float(outcome_prices[1])
        except (ValueError, TypeError):
            errors.append(slug)
            continue

        old_no = stored[slug]["no_price"]
        old_yes = stored[slug]["yes_price"]

        if old_no is not None and old_yes is not None:
            no_change = abs(new_no - old_no)
            yes_change = abs(new_yes - old_yes)
            max_change = max(no_change, yes_change)

            if max_change >= MOVEMENT_THRESHOLD:
                pct_no = ((new_no - old_no) / old_no * 100) if old_no != 0 else 0
                pct_yes = ((new_yes - old_yes) / old_yes * 100) if old_yes != 0 else 0
                direction_no = "🟢" if pct_no > 0 else "🔴" if pct_no < 0 else "⚪"
                direction_yes = "🟢" if pct_yes > 0 else "🔴" if pct_yes < 0 else "⚪"

                movements.append({
                    "slug": slug,
                    "question": stored[slug]["question"],
                    "old_no": round(old_no, 3),
                    "new_no": round(new_no, 3),
                    "old_yes": round(old_yes, 3),
                    "new_yes": round(new_yes, 3),
                    "no_change_pct": round(pct_no, 1),
                    "yes_change_pct": round(pct_yes, 1),
                    "max_change": round(max_change, 3),
                })

                print(f"⚠️  MOVEMENT: {stored[slug]['question']}")
                print(f"   NO:  {old_no:.3f} → {new_no:.3f} ({direction_no} {pct_no:+.1f}%)")
                print(f"   YES: {old_yes:.3f} → {new_yes:.3f} ({direction_yes} {pct_yes:+.1f}%)\n")

        checked += 1
        time.sleep(BATCH_DELAY)

        # Progress indicator every 25 markets
        if (i + 1) % 25 == 0:
            print(f"  ... {i+1}/{total} checked, {len(movements)} movements found so far", flush=True)

    # Summary
    print(f"\n{'='*60}")
    print(f"SCAN COMPLETE: {checked}/{total} markets checked, {len(errors)} errors")
    print(f"Significant movements (>10%): {len(movements)}")

    if movements:
        print(f"\n--- MARKETS WITH >10% PRICE MOVEMENT ---")
        movements.sort(key=lambda m: abs(m["max_change"]), reverse=True)
        for m in movements:
            print(f"\n{m['question']}")
            print(f"  Slug: {m['slug']}")
            print(f"  NO:  {m['old_no']:.3f} → {m['new_no']:.3f} ({m['no_change_pct']:+.1f}%)")
            print(f"  YES: {m['old_yes']:.3f} → {m['new_yes']:.3f} ({m['yes_change_pct']:+.1f}%)")

    if errors:
        print(f"\n--- ERRORS ({len(errors)}) ---")
        for e in errors[:10]:
            print(f"  ⚠️  {e}")
        if len(errors) > 10:
            print(f"  ... and {len(errors)-10} more")

    # Save results
    result = {
        "checked": checked,
        "errors": len(errors),
        "movements_found": len(movements),
        "movements": movements,
        "error_slugs": errors[:20],
    }
    with open("/home/ubuntu/.openclaw/workspace/analyst/price-scan-result.json", "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nResults saved to analyst/price-scan-result.json")

    # Return exit code based on whether we found movements
    return 1 if movements else 0

if __name__ == "__main__":
    sys.exit(main())
