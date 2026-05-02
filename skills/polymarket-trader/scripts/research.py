#!/usr/bin/env python3
"""Research Polymarket markets for a thesis.

Public/read-only: no wallet, no API key, no trading.
Produces a JSON research packet with candidate markets and a trade-plan scaffold.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request
from typing import Any

GAMMA = os.environ.get("POLYMARKET_GAMMA_HOST", "https://gamma-api.polymarket.com").rstrip("/")
CLOB = os.environ.get("POLYMARKET_CLOB_HOST", "https://clob.polymarket.com").rstrip("/")


def utc_stamp() -> str:
    return dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z")


def get_json(url: str, timeout: int = 20) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "Trevor-polymarket-trader/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def try_urls(urls: list[str]) -> list[Any]:
    out: list[Any] = []
    errors: list[str] = []
    for url in urls:
        try:
            out.append(get_json(url))
        except Exception as exc:
            errors.append(f"{url}: {exc}")
    if not out:
        raise RuntimeError("all market-data requests failed:\n" + "\n".join(errors))
    return out


def flatten(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("data", "markets", "events", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
        return [payload]
    return []


def text_blob(item: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("title", "question", "description", "slug", "ticker", "eventTitle", "category"):
        value = item.get(key)
        if value:
            parts.append(str(value))
    for key in ("markets", "outcomes", "tags"):
        value = item.get(key)
        if isinstance(value, list):
            parts.extend(json.dumps(x, sort_keys=True)[:600] for x in value[:10])
    return " ".join(parts).lower()


def score_item(item: dict[str, Any], terms: list[str]) -> int:
    blob = text_blob(item)
    return sum(1 for t in terms if t in blob)


def extract_candidate(item: dict[str, Any]) -> dict[str, Any]:
    markets = item.get("markets") if isinstance(item.get("markets"), list) else []
    tokens: list[dict[str, Any]] = []
    for m in markets:
        if not isinstance(m, dict):
            continue
        for key in ("clobTokenIds", "tokenIds", "tokens", "outcomes"):
            value = m.get(key)
            if isinstance(value, list):
                for v in value:
                    if isinstance(v, dict):
                        tokens.append(v)
                    else:
                        tokens.append({"value": v})
    return {
        "id": item.get("id") or item.get("conditionId") or item.get("marketId"),
        "slug": item.get("slug"),
        "title": item.get("title") or item.get("question") or item.get("eventTitle"),
        "description": item.get("description"),
        "active": item.get("active"),
        "closed": item.get("closed"),
        "end_date": item.get("endDate") or item.get("end_date") or item.get("endDateIso"),
        "liquidity": item.get("liquidity") or item.get("liquidityNum"),
        "volume": item.get("volume") or item.get("volumeNum"),
        "best_bid": item.get("bestBid"),
        "best_ask": item.get("bestAsk"),
        "last_price": item.get("lastTradePrice") or item.get("last_price"),
        "tokens": tokens[:20],
        "raw_keys": sorted(item.keys()),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Research Polymarket markets for a thesis")
    parser.add_argument("--thesis", required=True, help="Falsifiable trading thesis")
    parser.add_argument("--query", help="Explicit market search query; defaults to thesis")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--out", default="polymarket-research.json")
    args = parser.parse_args(argv)

    query = args.query or args.thesis
    encoded = urllib.parse.urlencode({"limit": args.limit, "active": "true", "closed": "false", "q": query})
    encoded_search = urllib.parse.urlencode({"limit": args.limit, "query": query})
    urls = [
        f"{GAMMA}/markets?{encoded}",
        f"{GAMMA}/events?{encoded}",
        f"{GAMMA}/search?{encoded_search}",
    ]
    payloads = try_urls(urls)
    terms = [t.lower() for t in query.replace("/", " ").replace("-", " ").split() if len(t) > 2]
    seen: set[str] = set()
    candidates: list[dict[str, Any]] = []
    for payload in payloads:
        for item in flatten(payload):
            candidate = extract_candidate(item)
            key = str(candidate.get("id") or candidate.get("slug") or candidate.get("title"))
            if key in seen:
                continue
            seen.add(key)
            candidate["match_score"] = score_item(item, terms)
            candidates.append(candidate)
    candidates.sort(key=lambda x: (x.get("match_score") or 0, x.get("liquidity") or 0, x.get("volume") or 0), reverse=True)
    packet = {
        "generated_at": utc_stamp(),
        "thesis": args.thesis,
        "query": query,
        "mode": "research_only",
        "notes": [
            "Review exact resolution criteria before trading.",
            "Fill token_id, side, price/size or amount manually after confirming the market outcome token.",
            "Execution is dry-run by default; trade.py requires --execute and --i-understand-risk.",
        ],
        "candidate_markets": candidates[: args.limit],
        "trade_plan": {
            "thesis": args.thesis,
            "max_total_usdc": 0,
            "risk_notes": [],
            "orders": [],
        },
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(packet, f, indent=2)
        f.write("\n")
    print(json.dumps({"out": args.out, "candidates": len(packet["candidate_markets"]), "generated_at": packet["generated_at"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
