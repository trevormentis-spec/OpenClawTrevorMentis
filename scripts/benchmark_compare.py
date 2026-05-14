#!/usr/bin/env python3
"""
Benchmark Comparison — Perplexity GSIB vs Trevor GSIB.

Fetches the latest Perplexity-produced GSIB from Gmail (labeled
"Important MyClaw Use this") and compares it against Trevor's
own GSIB output. Produces a structured comparison report.

Usage:
    python3 scripts/benchmark_compare.py                       # latest comparison
    python3 scripts/benchmark_compare.py --date YYYY-MM-DD    # specific date
    python3 scripts/benchmark_compare.py --save               # save report
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
GMAIL_BASE = "https://gateway.maton.ai/google-mail/gmail/v1/users/me"
BENCHMARK_DIR = REPO_ROOT / "analysis" / "perplexity-benchmark"
COMPARISON_DIR = REPO_ROOT / "analysis" / "benchmark-comparisons"

# The Gmail label ID for "Important MyClaw Use this"
TARGET_LABEL_ID = "Label_1645217335260921418"

USER_AGENT = "TrevorBenchmark/1.0"


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[benchmark {ts}] {msg}", file=sys.stderr, flush=True)


def get_api_key() -> str:
    key = os.environ.get("MATON_API_KEY", "")
    if not key:
        raise RuntimeError("MATON_API_KEY not set")
    return key


def gmail_get(path: str, params: dict | None = None) -> dict:
    api_key = get_api_key()
    url = f"{GMAIL_BASE}/{path}"
    if params:
        qs = urllib.parse.urlencode(params)
        url = f"{url}?{qs}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("User-Agent", USER_AGENT)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as exc:
        log(f"GET {path} failed: {exc}")
        return {}


def fetch_latest_perplexity_brief() -> dict | None:
    """Fetch the latest email with the Important MyClaw Use this label."""
    data = gmail_get("messages", {"q": "label:important-myclaw-use-this", "maxResults": 5})
    msg_refs = data.get("messages", [])
    if not msg_refs:
        log("No Perplexity briefs found")
        return None

    for ref in msg_refs:
        mid = ref["id"]
        msg = gmail_get(f"messages/{mid}", {"format": "full"})
        if not msg:
            continue

        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        date_str = headers.get("Date", "")

        def extract_text(payload: dict) -> str:
            parts = payload.get("parts", [])
            mime = payload.get("mimeType", "")
            text = ""
            if mime == "text/plain":
                data = payload.get("body", {}).get("data", "")
                if data:
                    try:
                        text = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                    except Exception:
                        text = data
            for p in parts:
                text += extract_text(p)
            return text

        body = extract_text(msg.get("payload", {}))

        return {
            "id": mid,
            "date": date_str,
            "subject": headers.get("Subject", ""),
            "from": headers.get("From", ""),
            "body": body,
            "raw_msg": msg,
        }

    return None


def fetch_trevor_gsib() -> dict | None:
    """Read Trevor's own GSIB from tasks/news_analysis.md."""
    path = REPO_ROOT / "tasks" / "news_analysis.md"
    if not path.exists():
        log("Trevor GSIB not found at tasks/news_analysis.md")
        return None
    content = path.read_text(encoding="utf-8", errors="replace")
    return {"path": str(path), "content": content, "date": dt.date.today().isoformat()}


def count_words(text: str) -> int:
    return len(text.split())


def extract_region_coverage(text: str) -> dict[str, bool]:
    """Check which regions are covered."""
    regions = {
        "north_america": ["north america", "mexico", "canada", "united states", "cia", "cartel", "trump"],
        "europe": ["europe", "russia", "ukraine", "nato", "putin", "zelensky", "eu"],
        "middle_east": ["middle east", "iran", "israel", "gaza", "hormuz", "lebanon", "hezbollah"],
        "asia": ["asia", "china", "xi", "taiwan", "india", "modi", "south china", "sindoor"],
        "south_america": ["south america", "venezuela", "maduro", "machado", "brazil", "argentina"],
        "africa": ["africa", "sahel", "mali", "sudan", "niger", "bamako"],
        "global_finance": ["market", "trade", "oil", "price", "polymarket", "kalshi", "ceasefire"],
    }
    t = text.lower()
    coverage = {}
    for region, keywords in regions.items():
        coverage[region] = any(kw in t for kw in keywords)
    return coverage


def extract_trade_mentions(text: str) -> list[str]:
    """Find trade/prediction market references."""
    patterns = [
        r"(?:Polymarket|Kalshi)[^.]*\.?",
        r"(?:¢|cents?)[^.]*(?:YES|NO)[^.)]*",
        r"(?:YES|NO)\s*(?:at|repriced|→|→)\s*\d+",
        r"(?:repriced|trading at|entered at|retraced)\s*\d+",
        r"(?:Trade #?\d+|contract)[^.]*\.?",
    ]
    mentions = []
    for p in patterns:
        matches = re.findall(p, text, re.IGNORECASE)
        mentions.extend(m.strip() for m in matches)
    return mentions


def extract_framework_reframes(text: str) -> list[str]:
    """Find analytic framework language."""
    patterns = [
        r"converts? our (?:read|assessment|framing)[^.]*\.?",
        r"reframes?[^.]*\.?",
        r"(?:materially|structurally|functionally)\s+\w+er\s+",
        r"our standing (?:read|assessment)[^.]*\.?",
    ]
    reframes = []
    for p in patterns:
        matches = re.findall(p, text, re.IGNORECASE)
        reframes.extend(m.strip() for m in matches)
    return reframes


def score_persona_consistency(text: str) -> dict:
    """Score persona/voice features."""
    score = 0
    findings = []
    if re.search(r"^[A-Za-z]+,", text.strip(), re.MULTILINE):
        score += 1
        findings.append("Direct address opening")
    if re.search(r"(?:—|–)\s*(?:Trevor|Computer|Trevor Mentis)\s*$", text.strip(), re.MULTILINE):
        score += 1
        findings.append("Consistent sign-off")
    if text.strip().startswith(("Roderick", "Trevor", "Computer")):
        score += 2
        findings.append("Analyst-to-analyst tone")
    return {"score": score, "max": 4, "findings": findings}


def score_signal_density(text: str) -> dict:
    """Score signal-to-noise ratio."""
    word_count = count_words(text)
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    sentence_count = len(sentences)
    if sentence_count == 0:
        return {"score": 0, "max": 5, "findings": ["No substantive sentences"]}
    # Signal density = substantive sentences per 100 words
    density = (sentence_count / word_count) * 100 if word_count > 0 else 0
    score = min(5, round(density / 2))
    return {"score": score, "max": 5, "findings": [f"{density:.1f} signal sentences per 100 words"]}


def score_trade_integration(text: str) -> dict:
    """Score how well trade info is embedded."""
    mentions = extract_trade_mentions(text)
    score = 0
    findings = []
    if mentions:
        score += 1
        findings.append(f"{len(mentions)} trade/pricing mentions found")
        natural_inline = [m for m in mentions if "→" in m or "repriced" in m.lower()]
        if natural_inline:
            score += 2
            findings.append("Trade prices integrated inline with narrative")
        # Check if price movements have direction
        has_direction = any(
            "+" in m or "-" in m or "pp" in m.lower() or "adverse" in m.lower() or "supportive" in m.lower()
            for m in mentions
        )
        if has_direction:
            score += 2
            findings.append("Price movements include direction/delta")
    else:
        findings.append("No trade/pricing mentions found")
    return {"score": score, "max": 5, "findings": findings}


def score_framework_reframes(text: str) -> dict:
    """Score use of analytic framework language."""
    reframes = extract_framework_reframes(text)
    score = min(3, len(reframes))
    return {"score": score, "max": 3, "findings": [f"{len(reframes)} analytic reframe(s)"]}


def score_prioritization(text: str) -> dict:
    """Score whether the brief leads with the most consequential development."""
    score = 0
    findings = []
    first_para = text.strip().split("\n\n")[0] if text.strip() else ""
    if re.search(r"(?:most|biggest|top|primary|key|single most)", first_para, re.IGNORECASE):
        score += 2
        findings.append("Opens with weighted priority statement")
    if re.search(r"(?:NORTH AMERICA|EUROPE|MIDDLE EAST|ASIA|AFRICA)", first_para):
        score += 1
        findings.append("Regional header anchors first paragraph")
    return {"score": score, "max": 3, "findings": findings}


def compare_briefs(perplexity: dict, trevor: dict) -> dict:
    """Compare the two briefs and produce a scorecard."""
    perplexity_body = perplexity.get("body", "")
    trevor_content = trevor.get("content", "")

    perplexity_words = count_words(perplexity_body)
    trevor_words = count_words(trevor_content)

    perplexity_regions = extract_region_coverage(perplexity_body)
    trevor_regions = extract_region_coverage(trevor_content)

    # Perplexity scores
    pp_persona = score_persona_consistency(perplexity_body)
    pp_density = score_signal_density(perplexity_body)
    pp_trade = score_trade_integration(perplexity_body)
    pp_framework = score_framework_reframes(perplexity_body)
    pp_prioritization = score_prioritization(perplexity_body)
    pp_total = pp_persona["score"] + pp_density["score"] + pp_trade["score"] + pp_framework["score"] + pp_prioritization["score"]
    pp_max = pp_persona["max"] + pp_density["max"] + pp_trade["max"] + pp_framework["max"] + pp_prioritization["max"]

    # Trevor scores
    tv_persona = score_persona_consistency(trevor_content)
    tv_density = score_signal_density(trevor_content)
    tv_trade = score_trade_integration(trevor_content)
    tv_framework = score_framework_reframes(trevor_content)
    tv_prioritization = score_prioritization(trevor_content)
    tv_total = tv_persona["score"] + tv_density["score"] + tv_trade["score"] + tv_framework["score"] + tv_prioritization["score"]
    tv_max = tv_persona["max"] + tv_density["max"] + tv_trade["max"] + tv_framework["max"] + tv_prioritization["max"]

    return {
        "date": perplexity.get("date", dt.date.today().isoformat()),
        "metrics": {
            "word_count": {"perplexity": perplexity_words, "trevor": trevor_words},
        },
        "region_coverage": {
            "perplexity_only": [r for r, v in perplexity_regions.items() if v and not trevor_regions.get(r)],
            "trevor_only": [r for r, v in trevor_regions.items() if v and not perplexity_regions.get(r)],
            "both": [r for r in perplexity_regions if perplexity_regions[r] and trevor_regions.get(r)],
            "neither": [r for r in perplexity_regions if not perplexity_regions[r] and not trevor_regions.get(r)],
        },
        "scores": {
            "perplexity": {
                "persona": pp_persona,
                "signal_density": pp_density,
                "trade_integration": pp_trade,
                "framework_reframes": pp_framework,
                "prioritization": pp_prioritization,
                "total": pp_total,
                "max": pp_max,
                "pct": round((pp_total / pp_max) * 100) if pp_max > 0 else 0,
            },
            "trevor": {
                "persona": tv_persona,
                "signal_density": tv_density,
                "trade_integration": tv_trade,
                "framework_reframes": tv_framework,
                "prioritization": tv_prioritization,
                "total": tv_total,
                "max": tv_max,
                "pct": round((tv_total / tv_max) * 100) if tv_max > 0 else 0,
            },
        },
        "perplexity_trade_mentions": extract_trade_mentions(perplexity_body),
        "trevor_trade_mentions": extract_trade_mentions(trevor_content),
    }


def format_report(comparison: dict) -> str:
    """Format the comparison as a readable report."""
    pp = comparison["scores"]["perplexity"]
    tv = comparison["scores"]["trevor"]
    regions = comparison["region_coverage"]

    report = []
    report.append(f"# Benchmark Comparison — {comparison['date']}")
    report.append("")
    report.append("## Scorecard")
    report.append("")
    report.append(f"| Dimension            | Perplexity | Trevor | Gap |")
    report.append(f"|----------------------|-----------|--------|-----|")
    for dim in ["persona", "signal_density", "trade_integration", "framework_reframes", "prioritization"]:
        pp_s = f"{pp[dim]['score']}/{pp[dim]['max']}"
        tv_s = f"{tv[dim]['score']}/{tv[dim]['max']}"
        gap = tv[dim]["score"] - pp[dim]["score"]
        gap_s = f"{'+' if gap > 0 else ''}{gap}" if gap != 0 else "0"
        report.append(f"| {dim.replace('_', ' ').title():20s} | {pp_s:9s} | {tv_s:6s} | {gap_s:3s} |")
    report.append(f"| **Total**            | **{pp['total']}/{pp['max']} ({pp['pct']}%)** | **{tv['total']}/{tv['max']} ({tv['pct']}%)** | **{tv['total'] - pp['total']:+d}** |")
    report.append("")
    report.append(f"**Word count:** Perplexity {comparison['metrics']['word_count']['perplexity']} · Trevor {comparison['metrics']['word_count']['trevor']}")
    report.append("")

    # Region coverage
    report.append(f"## Region Coverage")
    report.append(f"- **Both:** {', '.join(regions['both']) if regions['both'] else 'none'}")
    report.append(f"- **Perplexity only:** {', '.join(regions['perplexity_only']) if regions['perplexity_only'] else 'none'}")
    report.append(f"- **Trevor only:** {', '.join(regions['trevor_only']) if regions['trevor_only'] else 'none'}")

    # Perplexity findings
    report.append("")
    report.append("## Perplexity Benchmarks")
    for dim in ["persona", "signal_density", "trade_integration", "framework_reframes", "prioritization"]:
        findings = pp[dim]["findings"]
        if findings:
            for f in findings:
                report.append(f"- **{dim.replace('_',' ').title()}:** {f}")

    # Trevor gaps
    report.append("")
    report.append("## Trevor Improvement Areas")
    for dim in ["persona", "signal_density", "trade_integration", "framework_reframes", "prioritization"]:
        tv_score = tv[dim]["score"]
        pp_score = pp[dim]["score"]
        if tv_score < pp_score:
            report.append(f"- **{dim.replace('_',' ').title()}:** {tv_score}/{tv[dim]['max']} vs {pp_score}/{pp[dim]['max']} (gap: {pp_score - tv_score})")
            for f in tv[dim]["findings"]:
                report.append(f"  - Current: {f}")
            for f in pp[dim]["findings"]:
                report.append(f"  - Target: {f}")

    # Trade mentions comparison
    report.append("")
    report.append("## Trade/Pricing Language")
    report.append(f"**Perplexity:** {len(comparison['perplexity_trade_mentions'])} mentions")
    if comparison["perplexity_trade_mentions"]:
        for m in comparison["perplexity_trade_mentions"][:5]:
            report.append(f"  - {m[:120]}")
    report.append(f"**Trevor:** {len(comparison['trevor_trade_mentions'])} mentions")
    if comparison["trevor_trade_mentions"]:
        for m in comparison["trevor_trade_mentions"][:5]:
            report.append(f"  - {m[:120]}")

    return "\n".join(report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="", help="Comparison date (YYYY-MM-DD)")
    parser.add_argument("--save", action="store_true", help="Save comparison report")
    args = parser.parse_args()

    COMPARISON_DIR.mkdir(parents=True, exist_ok=True)

    log("Fetching Perplexity benchmark brief...")
    perplexity = fetch_latest_perplexity_brief()
    if not perplexity:
        log("No Perplexity brief available for comparison")
        return 1

    log("Fetching Trevor GSIB...")
    trevor = fetch_trevor_gsib()
    if not trevor:
        log("No Trevor GSIB available for comparison")
        return 1

    log("Comparing...")
    comparison = compare_briefs(perplexity, trevor)
    report = format_report(comparison)

    print(report)

    if args.save:
        date = args.date or dt.date.today().isoformat()
        out_path = COMPARISON_DIR / f"{date}.md"
        out_path.write_text(report, encoding="utf-8")
        log(f"Saved comparison to {out_path}")

    # Save the perplexity brief body for reference
    date = args.date or dt.date.today().isoformat()
    bench_path = BENCHMARK_DIR / f"{date}.txt"
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
    bench_path.write_text(perplexity.get("body", ""), encoding="utf-8")
    log(f"Saved Perplexity body to {bench_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
