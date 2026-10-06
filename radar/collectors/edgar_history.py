#!/usr/bin/env python3
"""
Radar Phase 1b / moves 1+2 (§30, §69, §81, §82): per-company historical series + deltas.

Move 1: for each known CIK, list every DEF 14A in EDGAR submissions, build a per-year series.
Move 2: attribute amounts defensibly. Each security keyword occurrence yields TWO figures:
          direct  - the amount stated with the service ("driver of $203,092"), the defensible one
          near    - the largest amount in a +/-220 char window (context only, may be a total)
        Deltas are computed on `direct`; `near` is retained but marked unreliable.

Usage
  python3 radar/collectors/edgar_history.py --ciks 16058,1326801 --max-years 4
  python3 radar/collectors/edgar_history.py --from-dataset --limit 8
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SERIES = DATA / "exec_security_series.jsonl"
UA = "Trevor-SecurityRadar trevor_mentis@agentmail.to"

CATEGORIES = [
    ("security_driver",      r"s(?:ecurity|ecure)\s+driver"),
    ("secure_transport",     r"secure\s+transportation|secured\s+transportation|"
                             r"company[- ]provided\s+(?:secure\s+)?transportation"),
    ("residential",          r"residential\s+security|home\s+security|residence\s+security"),
    ("executive_protection", r"executive\s+protection|protective\s+services|protective\s+detail"),
    ("personal_security",    r"personal\s+security|personal\s+safety"),
    ("aircraft",             r"corporate\s+aircraft|private\s+aircraft|personal\s+use\s+of\s+aircraft"),
    ("threat_assessment",    r"threat\s+assessment|security\s+assessment"),
    ("security_program",     r"security\s+program(?:me)?|security\s+arrangements|security\s+policy"),
]
AMOUNT = re.compile(r"\$\s?(\d[\d,]{2,})(?:\.\d{2})?")
# "driver of $203,092" / "valued at $x" / "totaling $x" / "costs of $x"
DIRECT_AFTER = re.compile(
    r"^\s*(?:of|for|totaling|totalling|aggregating|valued at|amounting to|approximately|"
    r"costs? of|cost of|in the amount of|was|is|were|are)?\s*:?\s*\$?\s?(\d[\d,]{2,})(?:\.\d{2})?",
    re.I)


def log(m: str) -> None:
    print(f"[edgar-history] {m}", flush=True)


def get(url: str, tries: int = 3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=45) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    import gzip
                    raw = gzip.decompress(raw)
                return raw
        except Exception as e:
            if i == tries - 1:
                log(f"fetch failed {url[:80]}: {str(e)[:70]}")
                return None
            time.sleep(1.5 * (i + 1))


def strip_html(raw: bytes) -> str:
    t = raw.decode("utf-8", "replace")
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", t)
    t = re.sub(r"(?is)<br\s*/?>|</p>|</div>|</tr>|</td>", "\n", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = t.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#8217;", "'")
    t = re.sub(r"[ \t\xa0]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n", t)


def _num(s: str) -> float | None:
    try:
        v = float(s.replace(",", ""))
        return v if 1000 <= v <= 50_000_000 else None
    except Exception:
        return None


def extract_categories(text: str) -> dict:
    out: dict[str, list] = {}
    for cat, pat in CATEGORIES:
        for m in re.finditer(pat, text, re.I):
            after = text[m.end(): m.end() + 120]
            nxt = DIRECT_AFTER.match(after)
            direct = _num(nxt.group(1)) if nxt else None
            window = text[max(0, m.start() - 220): min(len(text), m.end() + 220)]
            if re.search(r"\b(401\(k\)|life insurance|dental|vision|disability)\b", window, re.I) \
               and not AMOUNT.search(window):
                continue
            near = max((_num(x) for x in AMOUNT.findall(window) if _num(x)), default=None)
            snip = re.sub(r"\s+", " ", text[max(0, m.start() - 60): m.end() + 120]).strip()[:260]
            out.setdefault(cat, [])
            if any(s["snippet"][:80] == snip[:80] for s in out[cat]):
                continue
            out[cat].append({"direct": direct, "near": near, "snippet": snip})
    return out


def list_def14a(cik: str, max_years: int) -> list[dict]:
    raw = get(f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json")
    if not raw:
        return []
    rec = json.loads(raw).get("filings", {}).get("recent", {})
    rows = [{"date": d, "acc": a, "doc": doc}
            for f, d, a, doc in zip(rec.get("form", []), rec.get("filingDate", []),
                                    rec.get("accessionNumber", []), rec.get("primaryDocument", []))
            if f == "DEF 14A"]
    rows.sort(key=lambda r: r["date"], reverse=True)
    return rows[:max_years]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ciks", default="")
    ap.add_argument("--from-dataset", action="store_true")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--max-years", type=int, default=4)
    args = ap.parse_args()

    ciks = [c.strip() for c in args.ciks.split(",") if c.strip()]
    if args.from_dataset:
        seen = {}
        for line in open(DATA / "exec_security_disclosures.jsonl"):
            r = json.loads(line)
            if r.get("cik"):
                seen[r["cik"]] = r.get("company", "")
        ciks = list(seen)[: args.limit]

    DATA.mkdir(parents=True, exist_ok=True)
    with SERIES.open("a") as fh:
        for cik in ciks:
            rows = list_def14a(cik, args.max_years)
            log(f"CIK {cik}: {len(rows)} DEF 14A")
            series = []
            for row in rows:
                url = (f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
                       f"{row['acc'].replace('-', '')}/{row['doc']}")
                raw = get(url)
                if raw is None:
                    continue
                cats = extract_categories(strip_html(raw))
                series.append({
                    "filing_date": row["date"], "accession": row["acc"], "source_url": url,
                    "categories": {c: {"direct_max": max((s["direct"] for s in v if s["direct"]),
                                                         default=None),
                                       "near_max": max((s["near"] for s in v if s["near"]),
                                                       default=None),
                                       "instances": len(v),
                                       "sample": v[0]["snippet"]} for c, v in cats.items()},
                    "categories_present": sorted(cats)})
                log(f"   {row['date']} cats={sorted(cats)}")
                time.sleep(0.25)
            series.sort(key=lambda r: r["filing_date"])
            deltas = []
            for prev, cur in zip(series, series[1:]):
                p, c = prev["categories"], cur["categories"]
                for cat in sorted(set(p) | set(c)):
                    pa = (p.get(cat) or {}).get("direct_max")
                    ca = (c.get(cat) or {}).get("direct_max")
                    if cat not in p:
                        deltas.append({"cat": cat, "kind": "FIRST_APPEARANCE", "to": ca})
                    elif cat not in c:
                        deltas.append({"cat": cat, "kind": "DISAPPEARED", "from": pa})
                    elif pa and ca and pa != ca:
                        deltas.append({"cat": cat, "kind": "CHANGE", "from": pa, "to": ca,
                                       "pct": round((ca - pa) / pa * 100, 1)})
            fh.write(json.dumps({"cik": cik, "series": series, "deltas": deltas}) + "\n")
            log(f"   DELTAS({len(deltas)}): {json.dumps(deltas)[:420]}")
    log(f"done -> {SERIES}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
