#!/usr/bin/env python3
"""
Radar Phase 1 / Project 2 (§59, §11): Security Hiring Radar.

Source: companies' own public ATS boards (Greenhouse, Lever) — Level-1/2 public endpoints,
no credentials, no aggregator scraping. This is the honest replacement for the job-board
scraper: we ask the employer directly.

Emits one record per matching posting with the §11 fields, plus program-building language
flags (§11 "build the program", "newly created", "vendor management", ... ) that indicate an
active purchasing or program-development window.

Company -> ATS token must be discovered/verified; an unverified token returns 404 and is
recorded as ATS_UNKNOWN (that is NOT evidence of no hiring — §52 NOT FOUND != DOES NOT EXIST).

Usage
  python3 radar/collectors/security_hiring.py                 # use built-in map
  python3 radar/collectors/security_hiring.py --tokens anthropic,robinhood
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
OUT = DATA / "security_hiring.jsonl"
UA = {"User-Agent": "Trevor-SecurityRadar trevor_mentis@agentmail.to"}

SEC_TITLE = re.compile(
    r"executive protection|protective intelligence|protective services|protection agent|"
    r"corporate security|global security|security operations|gsoc|threat management|"
    r"workplace violence|travel security|security director|head of security|chief security|"
    r"security manager|physical security|security specialist|resilience|security analyst|"
    r"security program|insider threat|investigations manager", re.I)

PROGRAM_LANGUAGE = re.compile(
    r"build the program|establish|stand ?up|newly created|new role|first[- ]ever|expand|"
    r"vendor management|manage (?:third[- ]party|external) (?:security )?(?:vendors|providers)|"
    r"security assessment|threat assessment|program design|greenfield|from the ground up", re.I)

# (company, ats, token, verified)  verified = we have seen this token return data
SEED = [
    ("Anthropic",    "greenhouse", "anthropic",  True),
    ("Robinhood",    "greenhouse", "robinhood",  True),
    ("Reddit",       "greenhouse", "reddit",     True),
    ("Coinbase",     "greenhouse", "coinbase",   True),
    ("Databricks",   "greenhouse", "databricks", True),
    ("Stripe",       "greenhouse", "stripe",     True),
    ("Block",        "greenhouse", "block",      True),
]


def log(m: str) -> None:
    print(f"[security-hiring] {m}", flush=True)


def fetch_json(url: str, tries: int = 2):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            return {"__http__": e.code}
        except Exception as e:
            if i == tries - 1:
                return {"__err__": str(e)[:80]}
            time.sleep(1.2)


def greenhouse(token: str) -> list[dict]:
    d = fetch_json(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true")
    if "__http__" in d or "__err__" in d:
        return []
    out = []
    for j in d.get("jobs", []):
        body = re.sub(r"<[^>]+>", " ", str(j.get("content", "")))
        out.append({
            "title": j.get("title", ""),
            "location": (j.get("location") or {}).get("name"),
            "updated": j.get("updated_at"),
            "url": j.get("absolute_url"),
            "departments": [x.get("name") for x in (j.get("departments") or [])],
            "body_excerpt": re.sub(r"\s+", " ", body).strip()[:600],
        })
    return out


def lever(token: str) -> list[dict]:
    d = fetch_json(f"https://api.lever.co/v0/postings/{token}?mode=json")
    if isinstance(d, dict):
        return []
    out = []
    for p in d:
        cats = p.get("categories") or {}
        out.append({
            "title": p.get("text", ""),
            "location": cats.get("location"),
            "updated": p.get("createdAt"),
            "url": p.get("hostedUrl"),
            "departments": [cats.get("team")] if cats.get("team") else [],
            "body_excerpt": re.sub(r"\s+", " ", str(p.get("descriptionPlain", ""))).strip()[:600],
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokens", default="", help="comma list of greenhouse tokens to probe")
    ap.add_argument("--from-map", action="store_true", help="use verified tokens from ats_tokens.json")
    args = ap.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)

    targets = [(f"token:{t}", "greenhouse", t, False) for t in args.tokens.split(",") if t.strip()] or SEED
    if args.from_map:
        mp = json.loads((DATA / "ats_tokens.json").read_text())
        targets = [(name, v["ats"], v["token"], True)
                   for name, v in mp.items() if v.get("token")]
    hits, checked = [], 0
    with OUT.open("a") as fh:
        for company, ats, token, verified in targets:
            jobs = greenhouse(token) if ats == "greenhouse" else lever(token)
            checked += 1
            sec = [j for j in jobs if SEC_TITLE.search(j["title"] or "")]
            log(f"{company:22s} {ats}/{token:14s} jobs={len(jobs):4d} security={len(sec)}")
            for j in sec:
                prog = sorted(set(m.group(0).lower() for m in PROGRAM_LANGUAGE.finditer(
                    (j["title"] or "") + " " + (j["body_excerpt"] or ""))))
                rec = {
                    "company": company, "ats": ats, "ats_token": token,
                    "job_title": j["title"], "location": j["location"],
                    "posting_updated": j["updated"], "source_url": j["url"],
                    "departments": j["departments"],
                    "program_building_language": prog,
                    "new_program_indicator": bool(prog),
                    "replacement_vs_expansion": "UNKNOWN",
                    "retrieved": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                    "evidence_class": "primary (employer's own ATS)",
                    "excerpt": (j["body_excerpt"] or "")[:400],
                }
                fh.write(json.dumps(rec) + "\n")
                hits.append(rec)
            time.sleep(0.3)
    log(f"checked {checked} boards; {len(hits)} security postings -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
