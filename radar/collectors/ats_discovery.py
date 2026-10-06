#!/usr/bin/env python3
"""
Radar — ATS token discovery (§59 bottleneck).

Companies post security roles on their own ATS boards, but we need the board token.
This probes candidate tokens (derived from company name + ticker) against the public
Greenhouse and Lever board APIs and stores the map that verifies.

Verified tokens unlock the Security Hiring Radar at scale. A failed probe is recorded as
UNKNOWN — never as "this company is not hiring" (§52).

Output: radar/data/ats_tokens.json   {"Company": {"ats": "...", "token": "...", "jobs": n, "verified_at": ...}}

Usage
  python3 radar/collectors/ats_discovery.py --limit 60
  python3 radar/collectors/ats_discovery.py --companies "Anthropic,Reddit"
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MAP = DATA / "ats_tokens.json"
UA = {"User-Agent": "Trevor-SecurityRadar trevor_mentis@agentmail.to"}

# tokens that are common words / already known — avoid pointless probes
STOP = {"inc", "corp", "corporation", "company", "holdings", "group", "the", "and",
        "international", "industries", "technologies", "limited", "ltd", "plc", "co"}


def log(m: str) -> None:
    print(f"[ats-discovery] {m}", flush=True)


def company_list(limit: int) -> list[tuple[str, str]]:
    """(company, ticker) pairs from the disclosure dataset, de-duplicated."""
    seen: dict[str, str] = {}
    for line in open(DATA / "exec_security_disclosures.jsonl"):
        r = json.loads(line)
        name = (r.get("company") or "").strip()
        if not name:
            continue
        disp = re.sub(r"\s*\(.*$", "", name).strip()
        tick = ""
        m = re.search(r"\(([A-Z][A-Z0-9.,\- ]{0,12})\)", name)
        if m:
            tick = m.group(1).split(",")[0].strip()
        seen.setdefault(disp, tick)
    return list(seen.items())[:limit]


def candidates(company: str, ticker: str) -> list[str]:
    words = [w for w in re.split(r"[^A-Za-z0-9]+", company.lower()) if w and w not in STOP]
    cands = []
    if words:
        cands.append("".join(words))
        cands.append(words[0])
    if ticker:
        cands.append(ticker.lower())
    if words:
        cands.append("-".join(words))
    out, seen = [], set()
    for c in cands:
        if len(c) >= 3 and c not in seen:
            seen.add(c)
            out.append(c)
    return out[:4]


def probe_greenhouse(token: str):
    try:
        with urllib.request.urlopen(urllib.request.Request(
                f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs", headers=UA),
                timeout=20) as r:
            d = json.loads(r.read())
            return len(d.get("jobs", []))
    except Exception:
        return None


def probe_lever(token: str):
    try:
        with urllib.request.urlopen(urllib.request.Request(
                f"https://api.lever.co/v0/postings/{token}?mode=json", headers=UA),
                timeout=20) as r:
            d = json.loads(r.read())
            return len(d) if isinstance(d, list) else None
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--companies", default="")
    args = ap.parse_args()

    DATA.mkdir(parents=True, exist_ok=True)
    mapping = {}
    if MAP.exists():
        mapping = json.loads(MAP.read_text())

    if args.companies:
        targets = [(c.strip(), "") for c in args.companies.split(",") if c.strip()]
    else:
        targets = company_list(args.limit)

    hits = 0
    for company, ticker in targets:
        cands = candidates(company, ticker)
        for token in cands:
            n = probe_greenhouse(token)
            if n is not None:
                mapping[company] = {"ats": "greenhouse", "token": token, "jobs": n,
                                    "verified_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
                log(f"  HIT  {company:34s} greenhouse/{token} ({n} jobs)")
                hits += 1
                break
            n = probe_lever(token)
            if n is not None:
                mapping[company] = {"ats": "lever", "token": token, "jobs": n,
                                    "verified_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
                log(f"  HIT  {company:34s} lever/{token} ({n} jobs)")
                hits += 1
                break
            time.sleep(0.15)
        else:
            mapping.setdefault(company, {"ats": "ATS_UNKNOWN", "token": None, "jobs": None})
            log(f"  miss {company:34s} (ATS_UNKNOWN)")

    MAP.write_text(json.dumps(mapping, indent=1, sort_keys=True))
    verified = sum(1 for v in mapping.values() if v.get("token"))
    log(f"done: {verified} verified boards of {len(mapping)} companies -> {MAP}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
