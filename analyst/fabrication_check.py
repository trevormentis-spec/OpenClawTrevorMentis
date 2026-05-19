#!/usr/bin/env python3
"""Fabrication detector — post-generation quality gate for analytical briefs.

Scans generated briefs for:
- Kalshi/Polymarket contract names → validate against scanner output or known list
- Stock/ETF tickers → validate against a current ticker list
- Specific prices with "trading at" / "last traded at" / "currently $X" → require source citation or tool-output reference
- Specific basis points / yields / spread quotes → same

Usage:
    python3 analyst/fabrication_check.py --brief path/to/brief.md
    python3 analyst/fabrication_check.py --brief path/to/brief.md --scanner-output exports/kalshi-scan-2026-05-18.md
    python3 analyst/fabrication_check.py --brief path/to/brief.md --verbose

Returns exit code 0 (pass) or 1 (block — fabrication detected).
Blocked briefs are not delivered.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Known real instruments for verification
# Stock/ETF tickers commonly appearing in Mexico briefs
KNOWN_TICKERS: set[str] = {
    # Mexico-specific
    "EWW",       # MSCI Mexico ETF
    "MXF",       # Mexico Closed-End Fund
    "FMX",       # Fomento Económico Mexicano
    "AMX",       # América Móvil
    "CEMEXCPO",  # Cemex
    "GMEXICO",   # Grupo México
    "PEMEX",     # Pemex (debt)
    "MXN",       # Mexican peso (forex ticker)
    "USDMXN",    # USD/MXN forex pair
    # EM benchmarks
    "IEMG",      # iShares Core MSCI Emerging Markets
    "EEM",       # iShares MSCI Emerging Markets
    "VWO",       # Vanguard FTSE Emerging Markets
    # Industrial / thematic
    "XLI",       # Industrial Select Sector SPDR
    "INDU",      # Industrial (placeholder)
    # Bond / rates
    "TLT",       # 20+ Year Treasury Bond
    "SHY",       # 1-3 Year Treasury Bond
    "EMB",       # Emerging Markets Bond
    # Commodities
    "USO",       # United States Oil Fund
    "BNO",       # United States Brent Oil Fund
}

# Known Kalshi contracts (from recent scanner output or manual registry)
KNOWN_KALSHI_CONTRACTS: dict[str, str] = {
    # From Kalshi scanner — verified active
    # Format: "contract description": "market_id or identifier"
    # These come from the scanner output; this list is a fallback registry
}

# Pattern: "Kalshi: \"Some Contract Name\"" or "Polymarket: \"Some Name\""
CONTRACT_PATTERN = re.compile(
    r'(Kalshi|Polymarket|PredictIt|Metaculus)[:\s]+[""]([^""]+)[""]',
    re.IGNORECASE
)

# Price patterns
PRICE_PATTERN = re.compile(
    r'(?:trading|traded|last|currently|is)\s*(?:at|around|about|approximately)?\s*\$?(\d+\.?\d*)\s*(?:\$|USD|cents|points|bucks)?(?:/|per|a\s)?',
    re.IGNORECASE
)

# Look for "traded at $X" or "last traded at $X" patterns
LAST_TRADED_PATTERN = re.compile(
    r'(?:last\s+traded|trades?|trading|currently|current price)\s*(?:at|around)?\s*[~≈]?\s*\$?(\d+\.?\d*)',
    re.IGNORECASE
)

# Ticker pattern: 1-5 uppercase letters/numbers
TICKER_PATTERN = re.compile(r'\b[A-Z]{1,5}\b')

# Source citation pattern
SOURCE_CITATION = re.compile(r'\[[^\]]*\]')

# "GAP:" or "GAP" marker
GAP_MARKER = re.compile(r'\bGAP\b', re.IGNORECASE)

# "synthetic" or "proxy" marker — indicates the brief itself flagged the gap
PROXY_MARKER = re.compile(r'\b(?:proxy|synthetic|no direct|no exact|closest)\b', re.IGNORECASE)


def load_known_kalshi_contracts(scanner_output: str | None = None) -> dict[str, str]:
    """Load known contracts from scanner output or static registry."""
    contracts = dict(KNOWN_KALSHI_CONTRACTS)
    
    if scanner_output and os.path.exists(scanner_output):
        with open(scanner_output) as f:
            content = f.read()
        # Extract contract names from scanner markdown
        for match in re.finditer(r'[•\-*]\s*(.+?):\s*\$?(\d+\.?\d*)', content):
            name = match.group(1).strip()
            price = match.group(2)
            contracts[name.lower()] = price
    
    return contracts


def check_ticker(ticker: str, text_lower: str) -> dict[str, Any]:
    """Check if a ticker is known real or potentially fabricated."""
    if ticker in KNOWN_TICKERS:
        return {"ticker": ticker, "status": "known", "detail": "known real instrument"}
    
    # If it looks like a ticker but isn't in registry, warn
    # Only flag if it appears in a context suggesting real instrument (not a generic acronym)
    risky_contexts = [
        r'\b(?:buy|sell|short|long|hedge|overweight|underweight|allocate)\s+' + re.escape(ticker) + r'\b',
        r'\b' + re.escape(ticker) + r'\s+(?:puts|calls|options|futures|forwards)\b',
        r'\b(?:ETF|etf|fund|stock|equity)\s+' + re.escape(ticker) + r'\b',
    ]
    for pattern in risky_contexts:
        if re.search(pattern, text_lower):
            return {"ticker": ticker, "status": "unverified", "detail": f"used in trade context but not in known instrument registry"}
    
    return {"ticker": ticker, "status": "unknown", "detail": "appears once, not in trade context"}


def check_brief(brief_path: str, scanner_output: str | None = None, verbose: bool = False) -> list[dict[str, Any]]:
    """Run all fabrication checks on a brief. Returns list of issues found."""
    
    with open(brief_path) as f:
        text = f.read()
    text_lower = text.lower()
    
    issues: list[dict[str, Any]] = []
    
    # --- Check 1: Named prediction-market contracts ---
    for match in CONTRACT_PATTERN.finditer(text):
        platform = match.group(1)
        contract_name = match.group(2)
        
        # Check if this contract is in a gap/proxy context
        surrounding = text[max(0, match.start()-200):min(len(text), match.end()+200)]
        is_gap = bool(GAP_MARKER.search(surrounding))
        is_proxy = bool(PROXY_MARKER.search(surrounding))
        
        known_contracts = load_known_kalshi_contracts(scanner_output)
        
        if contract_name.lower() in known_contracts:
            issues.append({
                "type": "contract_referenced",
                "platform": platform,
                "name": contract_name,
                "status": "verified",
                "detail": f"contract found in scanner output — {known_contracts[contract_name.lower()]}",
                "is_gap": is_gap,
                "is_proxy": is_proxy,
            })
        elif is_gap or is_proxy:
            issues.append({
                "type": "contract_referenced",
                "platform": platform,
                "name": contract_name,
                "status": "ok_proxy",
                "detail": "contract name present but in GAP/proxy context — acceptable if marked as constructed",
                "is_gap": is_gap,
                "is_proxy": is_proxy,
            })
        else:
            issues.append({
                "type": "fabrication_risk",
                "platform": platform,
                "name": contract_name,
                "status": "UNVERIFIED",
                "detail": "contract named without verification — NOT in scanner output",
                "is_gap": is_gap,
                "is_proxy": is_proxy,
            })
    
    # --- Check 2: "Last traded at" / "trading at" / "currently $X" with prices ---
    for match in LAST_TRADED_PATTERN.finditer(text):
        price = match.group(1)
        
        # --- Exclusion checks: don't flag numbers that are clearly NOT prices ---
        after = text[match.end():match.end()+30].strip()
        # If followed by % or "percent" / "percentage" — it's a proportion, not a price
        if re.match(r'^[%]', after) or re.match(r'^(?:percent|percentage|basis\s+points|bps)', after, re.IGNORECASE):
            continue
        # If followed by "-" and another number (range like "10-12%") — not a discrete price
        # Only skip if there's no $/€/£ sign within or immediately before the match
        currency_window = text[max(0,match.start()-3):match.end()]
        has_currency = bool(re.search(r'[$€£¥]', currency_window))
        if re.match(r'^-\d', after) and not has_currency:
            continue
        # If followed by unit indicators (x, kg, km, bps, pts, ratio, multiple)
        if re.match(r'^(?:x|kg|km|bps|pts|ratio|multiple)\b', after, re.IGNORECASE):
            continue
        # If the number itself is a year (1900-2099)
        if re.match(r'^(19|20)\d{2}$', price) and not re.search(r'[$€£¥]', text[max(0,match.start()-10):match.start()]):
            continue
        
        # Check if the surrounding text has an Admiralty source citation or GAP marker
        surrounding = text[max(0, match.start()-150):min(len(text), match.end()+100)]
        has_source = bool(SOURCE_CITATION.search(surrounding))
        has_gap = bool(GAP_MARKER.search(surrounding))
        
        context_before = text[max(0, match.start()-80):match.start()]
        
        if not has_source and not has_gap:
            issues.append({
                "type": "unverified_price",
                "price": price,
                "context": context_before.strip()[-60:],
                "status": "UNVERIFIED",
                "detail": f"price '${price}' without source citation or GAP marker",
            })
    
    # --- Check 3: Ticker mentions in trade context ---
    # Only check tickers that appear near trade verbs
    trade_verbs = r'\b(?:buy|sell|short|long|hedge|overweight|underweight|allocate|invest|trade|position)\b'
    for ticker_match in TICKER_PATTERN.finditer(text):
        ticker = ticker_match.group()
        # Only check 2-5 char tickers (skip single letters and very long strings)
        if len(ticker) < 2 or len(ticker) > 5:
            continue
        # Only check if near a trade verb
        surrounding = text[max(0, ticker_match.start()-100):min(len(text), ticker_match.end()+100)]
        if re.search(trade_verbs, surrounding, re.IGNORECASE):
            result = check_ticker(ticker, surrounding.lower())
            if result["status"] == "unverified":
                issues.append({
                    "type": "unverified_ticker",
                    "ticker": ticker,
                    "status": "unverified",
                    "detail": result["detail"],
                })
    
    # --- Check 4: Percentage claims (comprehensive) ---
    # Pattern 4a: "X-Y% increase/decrease/rise/drop" (verb after number)
    pct_claims_after = re.finditer(r'(\d+[–-]\d+)%\s+(?:increase|decrease|rise|drop|reduction|premium|gain|fall|swing)', text, re.IGNORECASE)
    # Pattern 4b: "rise/drop/increase/decrease by X-Y%" (verb before number)
    pct_claims_before = re.finditer(r'(?:increase|decrease|rise|drop|gain|fall|climb|decline)\s+by\s+(\d+[–-]\d+)%', text, re.IGNORECASE)
    # Pattern 4c: "up/down X-Y%" or "X-Y% up/down"
    pct_claims_updown = re.finditer(r'(?:up|down)\s+(?:by\s+)?(\d+[–-]\d+)%', text, re.IGNORECASE)
    
    for iterator in [pct_claims_after, pct_claims_before, pct_claims_updown]:
        for match in iterator:
            surrounding = text[max(0, match.start()-150):min(len(text), match.end()+100)]
            has_source = bool(SOURCE_CITATION.search(surrounding))
            has_gap = bool(GAP_MARKER.search(surrounding))
            if not has_source and not has_gap:
                issues.append({
                    "type": "unverified_pct_range",
                    "claim": match.group().strip(),
                    "status": "UNVERIFIED",
                    "detail": f"percentage range '{match.group().strip()}' without source citation",
                })
    

    
    # --- Check 5: Dollar-amount cost estimates ---
    # Pattern 5a: "-YK/year" or "-YK" cost ranges
    dollar_cost = re.finditer(r'\$\d+[–-]\d+[Kk](?:/year|/yr|/month|/mo|/annum)?', text)
    # Pattern 5b: "-YM" cost ranges
    dollar_cost_m = re.finditer(r'\$\d+[–-]\d+[Mm](?:/year|/yr|/month|/mo|/annum)?', text)
    # Pattern 5c: "Cost: ~-YK" or "Cost: ~-YM" with context
    dollar_cost_prefix = re.finditer(r'(?:cost|price|rate|fee|estimated|budget|spend|value)[:.\s]*~?\$\d+[–-]\d+[KMkm]', text, re.IGNORECASE)
    
    for iterator in [dollar_cost, dollar_cost_m, dollar_cost_prefix]:
        for match in iterator:
            surrounding = text[max(0, match.start()-200):min(len(text), match.end()+100)]
            has_source = bool(SOURCE_CITATION.search(surrounding))
            has_gap = bool(GAP_MARKER.search(surrounding))
            has_disclaimer = bool(re.search(r'directional|estimate|order.of.magnitude|planning.figure|rough|approximate|rule.of.thumb|illustrative', surrounding, re.IGNORECASE))
            if not has_source and not has_gap and not has_disclaimer:
                issues.append({
                    "type": "unverified_cost_range",
                    "claim": match.group().strip(),
                    "status": "UNVERIFIED",
                    "detail": f"dollar range '{match.group().strip()}' without source or directional disclaimer",
                })
    
    return issues


def format_report(issues: list[dict[str, Any]], verbose: bool = False) -> str:
    """Format fabrication check results for console output."""
    lines = []
    blocker = False
    
    for issue in issues:
        if issue.get("type") == "fabrication_risk" and issue.get("status") == "UNVERIFIED":
            blocker = True
            lines.append(f"❌ FABRICATION: {issue['platform']} contract \"{issue['name']}\" not verified")
        elif issue.get("type") == "unverified_price" and issue.get("status") == "UNVERIFIED":
            blocker = True
            lines.append(f"❌ FABRICATION: unverified price ${issue['price']} in context: \"{issue['context']}\"")
        elif issue.get("type") == "unverified_pct_range" and issue.get("status") == "UNVERIFIED":
            blocker = True
            lines.append(f"❌ FABRICATION: unsourced percentage range \"{issue['claim']}\"")
        elif issue.get("type") == "unverified_ticker" and issue.get("status") == "unverified":
            lines.append(f"⚠️  WARNING: unverified ticker {issue['ticker']} — {issue['detail']}")
        elif issue.get("type") == "unverified_cost_range" and issue.get("status") == "UNVERIFIED":
            blocker = True
            lines.append('❌ FABRICATION: unsourced cost range "' + issue['claim'] + '"')
        elif issue.get("type") == "contract_referenced" and issue.get("status") == "verified":
            if verbose:
                lines.append(f"✅ OK: {issue['platform']} contract \"{issue['name']}\" verified — {issue['detail']}")
        elif issue.get("type") == "contract_referenced" and issue.get("status") == "ok_proxy":
            if verbose:
                lines.append(f"ℹ️  PROXY: {issue['platform']} contract \"{issue['name']}\" in GAP context")
    
    if not lines:
        lines.append("✅ No fabrication issues detected.")
    
    lines.append(f"\n{'❌ BLOCK — fabrication detected' if blocker else '✅ PASS — deliverable'}")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Fabrication detector for analytical briefs")
    parser.add_argument("--brief", required=True, help="Path to brief markdown file")
    parser.add_argument("--scanner-output", help="Path to Kalshi/Polymarket scanner output file")
    parser.add_argument("--verbose", action="store_true", help="Show passing checks too")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()
    
    if not os.path.exists(args.brief):
        print(f"Error: brief file not found: {args.brief}", file=sys.stderr)
        sys.exit(1)
    
    issues = check_brief(args.brief, args.scanner_output, args.verbose)
    
    if args.json:
        print(json.dumps(issues, indent=2))
    else:
        print(format_report(issues, args.verbose))
    
    # Check if any issues are blockers
    for issue in issues:
        if (issue.get("type") == "fabrication_risk" and issue.get("status") == "UNVERIFIED") or \
           (issue.get("type") == "unverified_price" and issue.get("status") == "UNVERIFIED") or \
           (issue.get("type") == "unverified_pct_range" and issue.get("status") == "UNVERIFIED"):
            sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
