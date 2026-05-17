#!/usr/bin/env python3
"""
Spanish → English translation helper for the Mexico desk pipeline.

Used by the brief writer to translate headlines and short quotes from
Mexican-Spanish primary sources without spending Tier-1 budget. Routes
to DeepSeek V4 Flash (Tier-3) for cost. Falls back to a length-limited
pass-through if no API key is set, so the pipeline never hard-fails on
missing translation.

Usage:
    # Single string from CLI
    python3 scripts/translate_es_to_en.py --text "El presidente anunció..."

    # JSON list of strings (one translation per input)
    echo '["Hola","Buenos días"]' | python3 scripts/translate_es_to_en.py --stdin-json

    # Apply to mexico-scan output: translate article titles in place
    python3 scripts/translate_es_to_en.py \\
        --scan exports/mexico-news-scan-2026-05-17.json \\
        --out  exports/mexico-news-scan-2026-05-17.en.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.request


MODEL = "deepseek-chat"   # Tier-3, cheapest
ENDPOINT = "https://api.deepseek.com/v1/chat/completions"


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[xlate {ts}] {msg}", file=sys.stderr, flush=True)


def translate_batch(strings: list[str]) -> list[str]:
    """Translate a list of Spanish strings to English. Order preserved."""
    if not strings:
        return []
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        log("DEEPSEEK_API_KEY not set — returning inputs unchanged")
        return strings

    system = (
        "You translate Mexican-Spanish news headlines and short passages "
        "into clear, terse English. Preserve proper nouns. Preserve "
        "Mexican institutional names (Pemex, CFE, SEDENA, FGR, INEGI, "
        "Banxico, Morena, USMCA) as-is. No commentary. Output JSON only: "
        '{"translations": ["...", "...", ...]} in the same order.'
    )
    user = json.dumps({"to_translate": strings}, ensure_ascii=False)
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.0,
        "max_tokens": min(4096, 80 * len(strings) + 256),
        "response_format": {"type": "json_object"},
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
    except Exception as exc:
        log(f"translation API failed: {type(exc).__name__}: {exc} — returning inputs")
        return strings

    try:
        raw = result["choices"][0]["message"]["content"]
        out = json.loads(raw).get("translations", [])
        if len(out) != len(strings):
            log(f"length mismatch ({len(out)} vs {len(strings)}) — returning inputs")
            return strings
        return [str(s) for s in out]
    except (KeyError, json.JSONDecodeError, IndexError) as exc:
        log(f"could not parse translation response ({exc}) — returning inputs")
        return strings


def translate_scan_file(scan_path: pathlib.Path, out_path: pathlib.Path) -> int:
    doc = json.loads(scan_path.read_text())
    titles: list[str] = []
    pointers: list[tuple[int, int]] = []
    for ri, result in enumerate(doc.get("results", [])):
        for ai, art in enumerate(result.get("articles", [])):
            title = art.get("title", "").strip()
            if title:
                titles.append(title)
                pointers.append((ri, ai))

    log(f"translating {len(titles)} titles from {scan_path.name}")
    translations = translate_batch(titles)

    for (ri, ai), en in zip(pointers, translations):
        doc["results"][ri]["articles"][ai]["title_en"] = en

    doc["translation_added_at"] = dt.datetime.now(dt.timezone.utc).isoformat() + "Z"
    out_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    log(f"wrote {out_path}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--text", help="single string to translate")
    p.add_argument("--stdin-json", action="store_true",
                   help="read a JSON list of strings from stdin")
    p.add_argument("--scan", help="path to a mexico-news-scan-*.json")
    p.add_argument("--out", help="output path (with --scan)")
    args = p.parse_args()

    if args.text:
        print(translate_batch([args.text])[0])
        return 0
    if args.stdin_json:
        data = json.loads(sys.stdin.read() or "[]")
        if not isinstance(data, list):
            log("stdin must be a JSON array of strings")
            return 1
        print(json.dumps(translate_batch(data), ensure_ascii=False))
        return 0
    if args.scan:
        scan_path = pathlib.Path(args.scan)
        if not scan_path.exists():
            log(f"no such file: {scan_path}")
            return 1
        out_path = pathlib.Path(args.out) if args.out else scan_path.with_suffix(".en.json")
        return translate_scan_file(scan_path, out_path)

    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
