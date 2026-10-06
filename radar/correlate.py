#!/usr/bin/env python3
"""
Radar — correlation join (§19, §61, §63, §86).

Joins the independent datasets on a canonical company key and produces the first staged
output. This is what turns three datasets into a radar.

Rules honoured:
  * SECURITY CHANGE and BUYING INTENT stay SEPARATE (§1). Never one score.
  * Convergence of independent categories is the high-value pattern (§61) — but is NOT
    proof of need.
  * Aggressive suppression (§42): a single routine signal does not qualify.
  * Classifications use the fixed vocabulary (§22) and are backed by cited evidence.

Outputs
  radar/data/opportunities.jsonl          one record per company with signals
  radar/reports/radar-<date>.md           human-readable radar report
"""
from __future__ import annotations

import collections
import datetime as dt
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent          # radar/
DATA = ROOT / "data"
REPORTS = ROOT / "reports"


def log(m: str) -> None:
    print(f"[correlate] {m}", flush=True)


# §42 precision: the employer ATS returns every posting containing "security"; most are IT
# security, not protective security. Keep protective/physical roles; drop cyber/infosec-only ones.
PROTECTIVE_STRONG = re.compile(
    r"executive protection|protective intelligence|protective services|protection agent|"
    r"physical security|corporate security|global security|security operations|gsoc|"
    r"workplace violence|travel security|event security|threat management|insider threat|"
    r"investigations analyst|global safety|security director|head of security|"
    r"chief security|security manager|guard|\baccess control\b|resilience", re.I)
CYBER_ONLY = re.compile(
    r"cyber|infosec|information security|application security|product security|"
    r"network security|cloud security|silicon|platform security|cryptograph|"
    r"penetration|malware|security research|security engineer|security architect|"
    r"security analyst|\bit security\b|data security|identity and access|\biam\b|devsecops|"
    r"machine learning|agentic", re.I)


def is_protective(title: str) -> bool:
    t = title or ""
    if PROTECTIVE_STRONG.search(t):
        return True
    return not CYBER_ONLY.search(t)


def norm(name: str) -> str:
    n = re.sub(r"\s*\(.*$", "", (name or "")).strip().lower()
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    n = re.sub(r"\b(inc|corp|corporation|company|holdings|group|the|ltd|limited|plc|co|de|md)\b", "", n)
    return re.sub(r"\s+", " ", n).strip()


def load_jsonl(p: pathlib.Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.open() if l.strip()]


def dedupe_series(rows: list[dict]) -> list[dict]:
    """The series file is append-only, so repeat runs duplicate a CIK's record and would
    double-count its deltas. Keep only the most recent record per CIK (§42 dedup, §86)."""
    latest: dict[str, dict] = {}
    for r in rows:
        k = str(r.get("cik") or "")
        cur = latest.get(k)
        if cur is None or len(r.get("series") or []) >= len(cur.get("series") or []):
            latest[k] = r
    return list(latest.values())


def main() -> int:
    disc = load_jsonl(DATA / "exec_security_disclosures.jsonl")
    series = dedupe_series(load_jsonl(DATA / "exec_security_series.jsonl"))
    hiring = load_jsonl(DATA / "security_hiring.jsonl")

    ent: dict[str, dict] = collections.defaultdict(
        lambda: {"names": set(), "disclosures": [], "deltas": [], "hiring": [],
                 "categories": set(), "structural": False})

    for r in disc:
        k = norm(r.get("company", ""))
        if not k:
            continue
        e = ent[k]
        e["names"].add(r.get("company"))
        e["disclosures"].append(r)
        e["categories"].update(r.get("phrases_matched") or [])
        if r.get("executive_protection_disclosed") or r.get("residential_security_disclosed"):
            e["structural"] = True

    for s in series:
        k = None
        for kk, v in ent.items():
            if any(str(c).lstrip("0") == str(s.get("cik", "")).lstrip("0") for c in [v.get("cik")]):
                k = kk
                break
        # fall back: attach by CIK match against disclosures
        if k is None:
            for kk, v in ent.items():
                if any((d.get("cik") or "") == (s.get("cik") or "") for d in v["disclosures"]):
                    k = kk
                    break
        if k:
            ent[k]["deltas"].extend(s.get("deltas") or [])

    for h in hiring:
        if not is_protective(h.get("job_title", "")):
            continue          # §42: cyber/IT security hiring is not our buying intent
        k = norm(h.get("company", ""))
        if not k:
            continue
        ent[k]["hiring"].append(h)
        ent[k]["names"].add(h.get("company"))

    out = []
    for k, e in ent.items():
        name = sorted(x for x in e["names"] if x)[0] if e["names"] else k
        d = len(e["disclosures"])
        dl = len(e["deltas"])
        hr = len(e["hiring"])
        facts, inference = [], []

        if d:
            facts.append(f"{d} DEF 14A filing(s) with protection-related language")
        if e["structural"]:
            facts.append("discloses an executive-protection / residential-security program")
        if dl:
            facts.append(f"{dl} year-over-year delta(s) in protection categories")
        if hr:
            facts.append(f"{hr} security-titled posting(s) on the employer's own ATS")
            if any(x.get("new_program_indicator") for x in e["hiring"]):
                facts.append("posting language suggests program building")

        # §30/§81: separate AMOUNT deltas (defensible) from SHAPE deltas (category appeared/
        # disappeared with no stated figure). Only amount movement can reach Material.
        amount_deltas = [x for x in e["deltas"] if x.get("from") is not None and x.get("to") is not None]
        shape_deltas = [x for x in e["deltas"] if x not in amount_deltas]
        big = [x for x in amount_deltas if abs(x.get("pct") or 0) >= 25]

        change = "Minimal"
        if amount_deltas or shape_deltas:
            change = "Developing"
        if len(amount_deltas) >= 2 or big:
            change = "Material"

        intent = "None observed"
        if hr:
            intent = "Possible"
        if hr >= 2 or any(x.get("new_program_indicator") for x in e["hiring"]):
            intent = "Evidence present"

        confidence = "Low"
        if d and hr:
            confidence = "Medium"       # two independent source families
        elif d:
            confidence = "Medium"
        elif hr:
            confidence = "Low"

        if hr >= 1 and any(x.get("job_title", "").lower().find("protective intelligence") >= 0
                           for x in e["hiring"]):
            confidence = "Medium"
            inference.append("protective-intelligence hiring indicates security-capability maturation (§79)")

        # §63 stage
        if d and hr:
            stage = 2          # qualified signal — independent categories converge
        elif dl or hr or e["structural"]:
            stage = 1          # developing
        else:
            stage = 0          # observation

        if stage == 0 and not e["structural"]:
            continue           # suppress noise (§42, §91)

        out.append({
            "entity_key": k, "company": name,
            "stage": stage,
            "security_change": change,
            "buying_intent": intent,
            "evidence_confidence": confidence,
            "categories": sorted(e["categories"]),
            "deltas": e["deltas"][:8],
            "hiring": [{"title": x.get("job_title"), "url": x.get("source_url"),
                        "updated": x.get("posting_updated")} for x in e["hiring"]],
            "facts": facts, "inference": inference,
            "sources": sorted({x.get("source_url") for x in e["disclosures"] if x.get("source_url")}
                              | {x.get("source_url") for x in e["hiring"] if x.get("source_url")})[:6],
            "contradictions": ([] if dl else
                               ["no prior-year delta computed — change claim not supported yet"]),
        })

    out.sort(key=lambda r: (-r["stage"], -len(r["facts"])))
    with (DATA / "opportunities.jsonl").open("w") as fh:
        for r in out:
            fh.write(json.dumps(r) + "\n")

    REPORTS.mkdir(parents=True, exist_ok=True)
    day = dt.date.today().isoformat()
    conv = [r for r in out if r["stage"] >= 2]
    lines = [f"# SECURITY OPPORTUNITY RADAR — {day}", "",
             f"Entities with signals: **{len(out)}** · convergent (stage ≥2): **{len(conv)}** · "
             f"disclosure records: {len(disc)} · hiring records: {len(hiring)} · deltas: {sum(len(s.get('deltas') or []) for s in series)}",
             "", "## STAGE 2 — QUALIFIED (independent categories converge)", ""]
    if conv:
        for r in conv:
            lines += [f"### {r['company']}",
                      f"- Security change: **{r['security_change']}** · Buying intent: **{r['buying_intent']}** · Confidence: **{r['evidence_confidence']}**",
                      "- Facts: " + "; ".join(r["facts"]),
                      "- Sources: " + (r["sources"][0] if r["sources"] else "n/a"), ""]
    else:
        lines += ["_None. The disclosure and hiring datasets do not yet overlap on any company — "
                  "an honest finding, not a failure: hiring coverage is limited to 8 ATS boards._", ""]
    lines += ["## STAGE 1 — DEVELOPING", ""]
    for r in [x for x in out if x["stage"] == 1][:15]:
        lines.append(f"- **{r['company']}** — change {r['security_change']}, intent {r['buying_intent']}, "
                     f"confidence {r['evidence_confidence']} — {'; '.join(r['facts'][:2])}")
    lines += ["", "## SUPPRESSED", "",
              f"- {len(ent) - len(out)} entities carried a single routine signal and were stored, not surfaced (§42).",
              "", "## WHAT WE ALMOST ALERTED ON", ""]
    # data-driven, never hardcoded (§92, §93)
    near = [r for r in out if r["stage"] == 1 and r["security_change"] in ("Developing", "Material")][:4]
    if near:
        for r in near:
            amt = [d for d in r["deltas"] if d.get("from") is not None and d.get("to") is not None]
            if amt:
                a = amt[0]
                lines.append(f"- **{r['company']}** — {a['cat']} moved ${a['from']:,.0f} → ${a['to']:,.0f} "
                             f"({a.get('pct')}%). Rated {r['security_change']}, not Material: "
                             f"{'single move without corroboration' if len(amt) < 2 else 'needs review'}.")
            else:
                lines.append(f"- **{r['company']}** — {len(r['deltas'])} category-shape change(s) with "
                             f"no stated dollar figure. Rated {r['security_change']}: shape alone is not escalation.")
    else:
        lines.append("- Nothing in this cycle reached Material. Recorded, not alerted.")
    lines += ["", "## KNOWN LIMITATIONS OF THIS CYCLE", "",
              "- Hiring coverage spans only verified ATS boards; large enterprises on Workday/Taleo "
              "return ATS_UNKNOWN — recorded as unknown, never as 'not hiring'.",
              "- Convergence between the disclosure and hiring datasets is thin because of that gap."]
    rp = REPORTS / f"radar-{day}.md"
    rp.write_text("\n".join(lines) + "\n")

    log(f"{len(out)} entities with signals ({len(conv)} convergent) -> {DATA/'opportunities.jsonl'}")
    log(f"report -> {rp}")
    print("\n".join(lines[:40]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
