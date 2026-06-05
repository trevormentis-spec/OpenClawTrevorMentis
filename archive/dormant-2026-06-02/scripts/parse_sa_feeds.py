#!/usr/bin/env python3
"""
Parse southamerica-osint-rss.md → structured CSV for validation.
v2 — fixed country tracking, dedup, proper section handling.
"""

import csv
import re
import sys
from pathlib import Path

REPO = Path("/home/ubuntu/.openclaw/workspace")
MD_PATH = REPO / "config/sources/southamerica-osint-rss.md"
OUT_CSV = REPO / "config/sources/southamerica-feeds.csv"

# Country headers in the markdown (emoji + name → ISO code)
COUNTRY_SIGNATURES = [
    ("ARGENTINA", "AR"),
    ("BOLIVIA", "BO"),
    ("BRAZIL", "BR"),
    ("CHILE", "CL"),
    ("COLOMBIA", "CO"),
    ("ECUADOR", "EC"),
    ("GUYANA", "GY"),
    ("PARAGUAY", "PY"),
    ("PERU", "PE"),
    ("SURINAME", "SR"),
    ("URUGUAY", "UY"),
    ("VENEZUELA", "VE"),
    ("FRENCH GUIANA", "GF"),
]

def parse():
    text = MD_PATH.read_text()

    feeds = []
    current_country = "PAN-REGIONAL"
    in_tier1 = False
    seen_urls = set()

    lines = text.split("\n")
    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip non-table lines and empty lines
        if not stripped.startswith("|"):
            # Check for country headers
            for country_name, code in COUNTRY_SIGNATURES:
                if f"### {country_name}" in stripped or country_name in stripped.split("###")[-1] if "###" in stripped else False:
                    pass
            # Better: check if line is a ### header with a country name
            if stripped.startswith("###"):
                matched = False
                for country_name, code in COUNTRY_SIGNATURES:
                    if country_name in stripped.upper():
                        current_country = code
                        matched = True
                        break
                if not matched:
                    # Section header but not a country — could be PAN-REGIONAL or TIER-1
                    if "PAN-REGIONAL" in stripped.upper():
                        current_country = "PAN-REGIONAL"
                    elif "TIER-1" in stripped.upper() or "STARTER PACK" in stripped.upper():
                        in_tier1 = True

            # Check for ## SECTION headers
            if stripped.startswith("## SECTION"):
                if "SECTION A" in stripped:
                    current_country = "PAN-REGIONAL"
                    in_tier1 = False
                elif "SECTION C" in stripped:
                    in_tier1 = True

            continue

        # Parse table row
        # Split by | and strip whitespace
        cells = [c.strip() for c in stripped.split("|")]
        # Remove empty first/last from leading/trailing |
        cells = [c for c in cells if c]

        if len(cells) < 2:
            continue

        # Skip header rows
        if cells[0] in ("Source", "RSS URL", "Status", "---", ":---", ""):
            continue

        # Find the feed URL in cells
        url = ""
        for c in cells:
            if c.startswith("http"):
                url = c
                break

        if not url or url == "n/a":
            continue

        # Skip if not actually a feed URL (e.g., argentina.gob.ar without http)
        if not url.startswith("http"):
            continue

        # Deduplicate
        if url in seen_urls:
            continue
        seen_urls.add(url)

        # Source name is first cell, clean it
        source = cells[0]
        source = re.sub(r'\*\*', '', source)       # strip bold
        source = re.sub(r'^\d+\.\s*', '', source)   # strip tier-1 numbering
        source = source.strip()

        # Verification status from last cell
        status_cell = cells[-1] if cells else ""
        if "✓" in status_cell:
            verif = "verified"
        elif "◐" in status_cell:
            verif = "likely"
        elif "⚠" in status_cell:
            verif = "pattern_guess"
        else:
            verif = "unknown"

        # CMS detection
        full_row = " ".join(cells)
        if "wordpress" in full_row.lower():
            cms = "wordpress"
        elif "arc" in full_row.lower() and "arc publishing" not in full_row.lower():
            # Check if "Arc" appears as CMS mention
            if "(Arc)" in full_row or "Arc)" in full_row:
                cms = "arc"
            else:
                cms = "unknown"
        elif "drupal" in full_row.lower():
            cms = "drupal"
        else:
            cms = "unknown"

        # Country name
        country_name = {v: k for k, v in dict(COUNTRY_SIGNATURES).items()}.get(current_country, current_country)

        feeds.append({
            "source": source,
            "country_code": current_country,
            "country_name": country_name,
            "feed_url": url,
            "verification_status": verif,
            "cms": cms,
            "tier": "1" if in_tier1 else "",
        })

    # Write CSV
    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "source", "country_code", "country_name", "feed_url",
            "verification_status", "cms", "tier"
        ])
        writer.writeheader()
        writer.writerows(feeds)

    # Stats
    by_country = {}
    for feed in feeds:
        by_country[feed["country_code"]] = by_country.get(feed["country_code"], 0) + 1

    print(f"Extracted {len(feeds)} unique feeds → {OUT_CSV}")
    print(f"\nBy country:")
    for cc in sorted(by_country.keys(), key=lambda x: by_country[x], reverse=True):
        print(f"  {cc}: {by_country[cc]}")
    print(f"\nBy verification:")
    for v in ["verified", "likely", "pattern_guess"]:
        cnt = sum(1 for f in feeds if f["verification_status"] == v)
        if cnt:
            print(f"  {v}: {cnt}")
    tier1 = sum(1 for f in feeds if f["tier"] == "1")
    print(f"\nTier-1 feeds: {tier1}")

    return feeds

if __name__ == "__main__":
    parse()
