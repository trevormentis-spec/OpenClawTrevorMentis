#!/usr/bin/env python3
"""
Radar — Workday hiring collector (§11, §59, §79).

Most large enterprises post on Workday, not Greenhouse/Lever. This queries a company's
public Workday career site API (the same endpoint the company's own careers page calls)
and extracts security-titled roles into the standard hiring record shape.

Source: https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs
        POST {"appliedFacets":{}, "limit":20, "offset":0, "searchText":"security"}
Public endpoint, no credentials.

A 422 means the (wdN, site) guess is wrong for that tenant — recorded as UNKNOWN, never as
"no hiring" (§52). Tenant/site discovery is a guess-and-verify problem.

Usage
  python3 radar/collectors/workday_hiring.py --search security
  python3 radar/collectors/workday_hiring.py --only nvidia,salesforce
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
MAP = DATA / "ats_tokens.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
           "Content-Type": "application/json", "Accept": "application/json"}

SEC_TITLE = re.compile(
    r"executive protection|protective intelligence|protective services|protection agent|"
    r"corporate security|global security|security operations|gsoc|threat management|"
    r"workplace violence|travel security|security director|head of security|chief security|"
    r"security manager|physical security|security specialist|resilience|security analyst|"
    r"security program|insider threat|investigations analyst|global safety|event security|"
    r"security architect|security engineer", re.I)

PROGRAM_LANGUAGE = re.compile(
    r"build the program|establish|stand ?up|newly created|new role|first[- ]ever|expand|"
    r"vendor management|security assessment|threat assessment|program design|greenfield", re.I)

# company, tenant, workday shard, site — verified entries marked True by a live 200
SEED = [
    ("NVIDIA",     "nvidia",     "wd5",  "NVIDIAExternalCareerSite",  True),
    ("Salesforce", "salesforce", "wd12", "External_Career_Site",      True),
    ("Marriott",   "marriott",   "wd1",  "MarriottCareers",           False),
    ("Marriott",   "marriott",   "wd5",  "External",                  False),
    ("Ford",       "ford",       "wd3",  "FordCareers",               False),
    ("Northrop Grumman", "northropgrumman", "wd1", "NorthropGrumman", False),
    ("CVS Health", "cvshealth",  "wd1",  "CVS_Health_Careers",        False),
    ("Chevron",    "chevron",    "wd1",  "External",                  False),
    ("DuPont",     "dupont",     "wd1",  "External",                  False),
    ("Exelon",     "exelon",     "wd1",  "External",                  False),
    ("Entergy",    "entergy",    "wd1",  "External",                  False),
    ("Lear",       "lear",       "wd5",  "External",                  False),
]


def log(m: str) -> None:
    print(f"[workday] {m}", flush=True)


def query(tenant: str, wd: str, site: str, search: str):
    url = f"https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    body = json.dumps({"appliedFacets": {}, "limit": 20, "offset": 0,
                       "searchText": search}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=HEADERS),
                                    timeout=30) as r:
            d = json.loads(r.read())
            return d.get("total"), d.get("jobPostings", [])
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}", []
    except Exception as e:
        return f"ERR {str(e)[:50]}", []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--search", default="security")
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)

    only = {x.strip().lower() for x in args.only.split(",") if x.strip()}
    mapping = json.loads(MAP.read_text()) if MAP.exists() else {}
    written, verified = 0, 0

    with OUT.open("a") as fh:
        for company, tenant, wd, site, known in SEED:
            if only and company.lower() not in only and tenant not in only:
                continue
            total, posts = query(tenant, wd, site, args.search)
            if isinstance(total, str):
                log(f"  miss {company:18s} {tenant}.{wd}/{site} -> {total}")
                continue
            verified += 1
            mapping[company] = {"ats": "workday", "token": f"{tenant}.{wd}/{site}",
                                "jobs": total,
                                "verified_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
            sec = [p for p in posts if SEC_TITLE.search(p.get("title", ""))]
            log(f"  HIT  {company:18s} {tenant}.{wd}/{site} total={total} security={len(sec)}"
                f" -> {[p.get('title') for p in sec][:3]}")
            for p in sec:
                blob = (p.get("title", "") + " " + str(p.get("jobDescription", "")))
                prog = sorted({m.group(0).lower() for m in PROGRAM_LANGUAGE.finditer(blob)})
                rec = {
                    "company": company, "ats": "workday",
                    "ats_token": f"{tenant}.{wd}/{site}",
                    "job_title": p.get("title"),
                    "location": p.get("locationsText"),
                    "posting_updated": p.get("postedOn"),
                    "source_url": f"https://{tenant}.{wd}.myworkdayjobs.com/en-US/{site}"
                                  f"{p.get('externalPath', '')}",
                    "departments": [],
                    "program_building_language": prog,
                    "new_program_indicator": bool(prog),
                    "replacement_vs_expansion": "UNKNOWN",
                    "retrieved": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                    "evidence_class": "primary (employer's own Workday site)",
                    "excerpt": "",
                }
                fh.write(json.dumps(rec) + "\n")
                written += 1
            time.sleep(0.3)

    MAP.write_text(json.dumps(mapping, indent=1, sort_keys=True))
    log(f"verified {verified} Workday sites; {written} security postings appended")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
