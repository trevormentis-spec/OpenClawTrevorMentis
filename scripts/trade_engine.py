#!/usr/bin/env python3
"""
Trade suggestion engine — called by deliver_brief_email.py

Reads a JSON payload file with judgments and markets, calls Opus 4.7
to cross-reference them, and writes suggested trades to stdout.

Usage:
    python3 scripts/trade_engine.py <payload_file>

Payload format:
    {
        "judgments": [{"statement": "...", "region": "...", "band": "...", "probability_pct": 55}, ...],
        "markets": [{"ticker": "KX...", "label": "...", "market_price_cents": 19, "volume": 572407}, ...]
    }

Output:
    TRADE: TICKER | BUY Yes/No | rationale
    ... (one per trade)
    or: NO TRADES IDENTIFIED
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = "anthropic/claude-opus-4.7"


def build_prompt(judgments: list[dict], markets: list[dict]) -> tuple[str, str]:
    system = (
        "You are a prediction market analyst. Given today's intelligence judgments "
        "and available Kalshi markets, identify where the intelligence assessment "
        "diverges from market pricing. For each divergence, suggest a trade.\n\n"
        "Rules:\n"
        "1. If intelligence probability > market mid-price + 15pts -> BUY Yes (undervalued)\n"
        "2. If intelligence probability < market mid-price - 15pts -> BUY No (overvalued)\n"
        "3. High confidence in brief + market mispricing = stronger signal\n"
        "4. Only suggest trades where you have a clear directional view\n"
        "5. Format each suggestion as: TRADE: TICKER | BUY Yes/No | rationale\n\n"
        "If no clear trades: NO TRADES IDENTIFIED\n"
        "Do not include any other text or commentary."
    )

    user = (
        f"Today's intelligence judgments:\n{json.dumps(judgments, indent=2)}\n\n"
        f"Available Kalshi markets:\n{json.dumps(markets, indent=2)}\n\n"
        "What trades do you recommend?"
    )
    return system, user


def call_model(system: str, user: str) -> str:
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": 1024,
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/trevormentis-spec",
            "X-Title": "TREVOR Trade Engine",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"NO TRADES IDENTIFIED — model call failed: {e}"


def main() -> int:
    if len(sys.argv) < 2:
        print("NO TRADES IDENTIFIED — no payload file provided", file=sys.stderr)
        return 1

    payload_file = sys.argv[1]
    with open(payload_file, encoding="utf-8") as f:
        data = json.load(f)

    judgments = data.get("judgments", [])
    markets = data.get("markets", [])

    if not judgments or not markets:
        print("NO TRADES IDENTIFIED")
        return 0

    if not API_KEY:
        print("NO TRADES IDENTIFIED — no API key")
        return 0

    system, user = build_prompt(judgments, markets)
    result = call_model(system, user)
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
