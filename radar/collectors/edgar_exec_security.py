#!/usr/bin/env python3
"""
Radar Phase 1 / Project 1 (§58): Executive Security Disclosure Dataset.

Mines SEC EDGAR DEF 14A proxy filings for disclosed executive-security spending and
program language, and emits one structured record per filing.

Method
  1. EDGAR full-text search (efts.sec.gov) for each security concept phrase, DEF 14A only.
  2. De-duplicate filings by accession number.
  3. Fetch each filing's primary document, strip markup, locate passages containing the
     concepts, and pull any dollar amounts near them.
  4. Append JSONL records; keep a seen-set so re-runs are incremental.

Rules honoured: primary source only; nothing invented (unknown -> null); passage text is
stored verbatim with its source URL so every claim is traceable (§41, §52).

Usage
  python3 radar/collectors/edgar_exec_security.py --months 3 --limit 20
  python3 radar/collectors/edgar_exec_security.py --start 2026-06-01 --end 2026-09-22
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "exec_security_disclosures.jsonl"
STATE = DATA / "state.json"

UA = "Trevor-SecurityRadar trevor_mentis@agentmail.to"
FTS = "https://efts.sec.gov/LATEST/search-index"

PHRASES = [
    "executive protection",
    "personal security",
    "security driver",
    "secure transportation",
    "residential security",
    "protective intelligence",
    "threat assessment",
    "security assessment",
    "protective services",
    "security arrangements",
    "personal safety",
    "corporate security",
]

# statement-level context we do NOT want to mistake for a security programme
BENEFIT_NOISE = re.compile(
    r"\b(401\(k\)|health insurance|life insurance|disability|dental|vision|"
    r"employee assistance|vacation|paid time off)\b", re.I)


def log(m: str) -> None:
    print(f"[edgar-exec-sec] {m}", flush=True)


def get(url: str, tries: int = 3) -> bytes | None:
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
                log(f"fetch failed {url[:90]}: {str(e)[:80]}")
                return None
            time.sleep(1.5 * (i + 1))
    return None


def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except Exception:
            pass
    return {"seen_accessions": []}


def save_state(s: dict) -> None:
    s["seen_accessions"] = s.get("seen_accessions", [])[-5000:]
    DATA.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=1))


def search(phrase: str, start: str, end: str) -> list[dict]:
    q = urllib.parse.quote(f'"{phrase}"')
    forms = urllib.parse.quote("DEF 14A")
    url = (f"{FTS}?q={q}&forms={forms}"
           f"&dateRange=custom&startdt={start}&enddt={end}&hits=10")
    raw = get(url)
    if not raw:
        return []
    try:
        d = json.loads(raw)
    except Exception:
        return []
    out = []
    for h in d.get("hits", {}).get("hits", []):
        src = h.get("_source", {})
        _id = h.get("_id", "")
        adsh, _, doc = _id.partition(":")
        ciks = src.get("ciks") or []
        out.append({
            "adsh": adsh,
            "doc": doc or src.get("file_type") or "",
            "cik": (ciks[0].lstrip("0") if ciks else None),
            "company": (src.get("display_names") or [""])[0],
            "filed": src.get("file_date"),
            "form": (src.get("root_forms") or src.get("form_type") or [""])[0]
                    if isinstance(src.get("root_forms") or src.get("form_type"), list)
                    else src.get("form_type"),
            "matched_phrase": phrase,
        })
    return out


def strip_html(raw: bytes) -> str:
    t = raw.decode("utf-8", "replace")
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", t)
    t = re.sub(r"(?is)<br\s*/?>|</p>|</div>|</tr>", "\n", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    t = t.replace("&nbsp;", " ").replace("&amp;", "&").replace("&#8217;", "'")
    t = re.sub(r"[ \t\xa0]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    return t


def passages(text: str) -> list[dict]:
    """Sentences containing a concept phrase, with nearby dollar amounts."""
    found = []
    sents = re.split(r"(?<=[.;])\s+", text)
    for i, s in enumerate(sents):
        low = s.lower()
        hit = next((p for p in PHRASES if p in low), None)
        if not hit:
            continue
        window = " ".join(sents[max(0, i - 1): i + 2])
        if BENEFIT_NOISE.search(window) and not re.search(r"\$\s?[\d,]{3,}", window):
            continue
        amounts = re.findall(r"\$\s?[\d][\d,]{2,}(?:\.\d{2})?", window)
        found.append({
            "phrase": hit,
            "passage": re.sub(r"\s+", " ", s).strip()[:600],
            "amounts": amounts[:6],
        })
    # de-dup identical passages, cap
    seen, out = set(), []
    for f in found:
        k = f["passage"][:120]
        if k in seen:
            continue
        seen.add(k)
        out.append(f)
    return out[:8]


def build_record(hit: dict, text: str) -> dict:
    ps = passages(text)
    cik = hit["cik"] or ""
    adsh_nd = (hit["adsh"] or "").replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{adsh_nd}/{hit['doc']}"
    amounts = [a for p in ps for a in p["amounts"]]
    return {
        "company": hit["company"],
        "cik": cik,
        "filing_type": "DEF 14A",
        "filing_date": hit["filed"],
        "accession": hit["adsh"],
        "source_url": url,
        "retrieved": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "phrases_matched": sorted({p["phrase"] for p in ps}),
        "dollar_amounts_near": sorted(set(amounts)),
        "passages": ps,
        "executive_protection_disclosed": any(
            p["phrase"] in ("executive protection", "protective services", "personal security")
            for p in ps),
        "residential_security_disclosed": any(p["phrase"] == "residential security" for p in ps),
        "security_driver_disclosed": any(p["phrase"] == "security driver" for p in ps),
        "threat_assessment_disclosed": any(p["phrase"] == "threat assessment" for p in ps),
        "protective_intelligence_disclosed": any(p["phrase"] == "protective intelligence" for p in ps),
        # YoY / prior-year amount and baseline work happens in Phase 1b (§4, §30)
        "prior_year_amount": None,
        "yoy_change": None,
        "notes": "UNKNOWN" if not ps else "",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=None)
    ap.add_argument("--end", default=None)
    ap.add_argument("--months", type=int, default=3)
    ap.add_argument("--limit", type=int, default=25, help="max filings to fetch per run")
    args = ap.parse_args()

    today = dt.date.today()
    end = args.end or today.isoformat()
    start = args.start or (today - dt.timedelta(days=30 * args.months)).isoformat()
    DATA.mkdir(parents=True, exist_ok=True)
    state = load_state()
    seen = set(state.get("seen_accessions", []))
    log(f"window {start} -> {end}; seen {len(seen)} accessions")

    hits: dict[str, dict] = {}
    for ph in PHRASES:
        for h in search(ph, start, end):
            key = h["adsh"]
            if not key:
                continue
            if key not in hits:
                hits[key] = h
            hits[key].setdefault("phrases", set()).add(ph)
        time.sleep(0.25)

    log(f"unique DEF 14A filings matched: {len(hits)}")
    todo = [(k, v) for k, v in hits.items() if k not in seen][: args.limit]
    log(f"fetching {len(todo)} new filings")

    written = 0
    with OUT.open("a") as fh:
        for adsh, h in todo:
            cik = h["cik"] or ""
            adsh_nd = adsh.replace("-", "")
            doc = h["doc"] or ""
            if not doc:
                continue
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{adsh_nd}/{doc}"
            raw = get(url)
            if raw is None:
                continue
            rec = build_record(h, strip_html(raw))
            fh.write(json.dumps(rec) + "\n")
            written += 1
            seen.add(adsh)
            log(f"  + {rec['company'][:52]:52s} {rec['filing_date']} "
                f"phrases={len(rec['phrases_matched'])} amounts={rec['dollar_amounts_near'][:3]}")
            time.sleep(0.2)

    state["seen_accessions"] = sorted(seen)
    state["last_run"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    state["last_window"] = [start, end]
    save_state(state)
    log(f"done: {written} records appended -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
