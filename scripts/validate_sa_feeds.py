#!/usr/bin/env python3
"""
Validate South America RSS feeds.
Tests every feed URL, reports OK/FAIL/STALE with entry counts and freshness.
Outputs: config/sources/southamerica-feeds-validated.json
"""

import csv
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import feedparser

REPO = Path("/home/ubuntu/.openclaw/workspace")
CSV_PATH = REPO / "config/sources/southamerica-feeds.csv"
OUT_JSON = REPO / "config/sources/southamerica-feeds-validated.json"

USER_AGENT = "TrevorRSSValidator/1.0 (+https://github.com/trevormentis-spec)"
feedparser.USER_AGENT = USER_AGENT

MAX_WORKERS = 8
TIMEOUT = 20  # seconds per feed
CUTOFF_DAYS = 30  # feeds with no entry newer than this are STALE


def validate_one(row):
    """Test a single feed. Returns result dict."""
    url = row["feed_url"]
    result = {
        "source": row["source"],
        "country_code": row["country_code"],
        "country_name": row["country_name"],
        "feed_url": url,
        "cms": row["cms"],
        "verification_original": row["verification_status"],
        "status": "UNKNOWN",
        "entry_count": 0,
        "latest_entry_date": None,
        "freshness": "UNKNOWN",
        "error": None,
        "elapsed_ms": 0,
    }

    t0 = time.monotonic()
    try:
        p = feedparser.parse(url)
        elapsed = (time.monotonic() - t0) * 1000
        result["elapsed_ms"] = round(elapsed)

        if p.bozo and not p.entries:
            result["status"] = "FAIL"
            result["error"] = f"bozo: {p.bozo_exception}" if hasattr(p, 'bozo_exception') else "no entries, parse error"
            return result

        entries = p.entries
        result["entry_count"] = len(entries)

        if not entries:
            result["status"] = "FAIL"
            result["error"] = "no entries in feed"
            return result

        # Find latest entry date
        latest = None
        for entry in entries:
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            if published and (latest is None or published > latest):
                latest = published

        if latest:
            dt_latest = datetime(*latest[:6])
            result["latest_entry_date"] = dt_latest.isoformat()
            days_ago = (datetime.now() - dt_latest).days
            if days_ago > CUTOFF_DAYS:
                result["freshness"] = "STALE"
                result["status"] = "STALE"
            else:
                result["freshness"] = "FRESH"
                result["status"] = "OK"
        else:
            result["status"] = "OK"
            result["freshness"] = "UNKNOWN_DATE"
            result["entry_count"] = len(entries)

    except Exception as e:
        elapsed = (time.monotonic() - t0) * 1000
        result["elapsed_ms"] = round(elapsed)
        result["status"] = "ERROR"
        result["error"] = str(e)[:200]

    return result


def main():
    # Load CSV
    with open(CSV_PATH) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)
    print(f"Validating {total} feeds (max {MAX_WORKERS} parallel, {TIMEOUT}s timeout)...")
    print()

    results = []
    ok_count = 0
    stale_count = 0
    fail_count = 0
    error_count = 0
    done = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(validate_one, row): row for row in rows}

        for future in as_completed(futures):
            done += 1
            result = future.result()

            if result["status"] == "OK":
                ok_count += 1
            elif result["status"] == "STALE":
                stale_count += 1
            elif result["status"] == "FAIL":
                fail_count += 1
            else:
                error_count += 1

            # Progress indicator
            icon = {"OK": "✓", "STALE": "◐", "FAIL": "✗", "ERROR": "⚠"}.get(result["status"], "?")
            entry_info = f"{result['entry_count']} entries" if result['entry_count'] else ""
            freshness = result.get('freshness', '')
            print(f"  [{done:3d}/{total}] {icon} {result['source'][:40]:40s} {result['status']:6s} {entry_info:15s} {freshness}")

            results.append(result)

    # Sort by status then country
    results.sort(key=lambda r: (
        {"OK": 0, "STALE": 1, "FAIL": 2, "ERROR": 3}.get(r["status"], 9),
        r["country_code"],
        r["source"]
    ))

    # Summary
    print(f"\n{'='*60}")
    print(f"RESULTS: {total} feeds tested")
    print(f"  ✓ OK:     {ok_count} ({100*ok_count/total:.0f}%)")
    print(f"  ◐ STALE:  {stale_count} ({100*stale_count/total:.0f}%)")
    print(f"  ✗ FAIL:   {fail_count} ({100*fail_count/total:.0f}%)")
    print(f"  ⚠ ERROR:  {error_count} ({100*error_count/total:.0f}%)")
    print(f"  ─────────────────")
    usable = ok_count + stale_count
    print(f"  Usable:   {usable} ({100*usable/total:.0f}%)")

    # By country
    by_country = {}
    for r in results:
        cc = r["country_code"]
        if cc not in by_country:
            by_country[cc] = {"OK": 0, "STALE": 0, "FAIL": 0, "ERROR": 0}
        by_country[cc][r["status"]] += 1

    print(f"\nBy country:")
    for cc in sorted(by_country.keys()):
        stats = by_country[cc]
        usable = stats["OK"] + stats["STALE"]
        total_cc = sum(stats.values())
        print(f"  {cc:15s}: {usable:2d}/{total_cc:2d} usable  (OK:{stats['OK']} STALE:{stats['STALE']} FAIL:{stats['FAIL']} ERR:{stats['ERROR']})")

    # Write output
    output = {
        "generated_at": datetime.now().isoformat(),
        "total_tested": total,
        "ok": ok_count,
        "stale": stale_count,
        "fail": fail_count,
        "error": error_count,
        "usable": usable,
        "results": results,
    }

    with open(OUT_JSON, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nFull results → {OUT_JSON}")
    return output


if __name__ == "__main__":
    main()
