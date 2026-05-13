#!/usr/bin/env python3
"""
Daily Starmer Political Survival Assessment — LDAP-7 Framework.

Every day, assesses Keir Starmer's political survival chances using
the LDAP-7 framework. Updates dimension scores based on overnight
developments and produces a structured survival assessment.

Output: analysis/starmer/{date}.md
Injected into: daily email delivery

Usage:
    python3 scripts/starmer_daily.py --date 2026-05-13
    python3 scripts/starmer_daily.py --report          # Show tracker summary
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys
import urllib.request
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
STARMER_PROFILE = REPO_ROOT / "brain" / "memory" / "semantic" / "ldap7-profiles" / "starmer-keir.md"
STARMER_DIR = REPO_ROOT / "analysis" / "starmer"
TRACKER_FILE = REPO_ROOT / "brain" / "memory" / "semantic" / "starmer-tracker.json"

# LDAP-7 dimension weights for survival assessment
DIMENSION_WEIGHTS_SURVIVAL = {
    "D1_optionality": 0.10,
    "D2_coercion": 0.10,
    "D3_popularity": 0.30,  # Most important for electoral survival
    "D4_constraint_rejection": 0.15,
    "D5_zero_sum": 0.10,
    "D6_escalate_retreat": 0.10,
    "D7_loyalty": 0.15,
}

USER_AGENT = "TrevorStarmerDaily/1.0"


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[starmer {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, Exception):
            return {}
    return {}


def save_json(path: pathlib.Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def fetch_uk_headlines() -> list[dict]:
    """Fetch recent UK political headlines."""
    headlines = []
    api_key = ""
    api_key = None  # Will try NewsAPI
    try:
        newskey = None
        # Try NewsAPI
        import os
        newskey = os.environ.get("NEWSAPI_KEY", "")
        if newskey:
            url = (f"https://newsapi.org/v2/everything?"
                   f"q=Keir+Starmer+UK+government&"
                   f"from={(dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=2)).strftime('%Y-%m-%d')}&"
                   f"sortBy=publishedAt&pageSize=10&"
                   f"apiKey={newskey}")
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
            for article in data.get("articles", []):
                headlines.append({
                    "title": article.get("title", ""),
                    "source": article.get("source", {}).get("name", "NewsAPI"),
                    "url": article.get("url", ""),
                    "published": article.get("publishedAt", "")[:10],
                })
    except Exception as exc:
        log(f"NewsAPI fetch failed: {exc}")

    if not headlines:
        # Fallback: use known UK headlines from brief analysis
        headlines = [
            {"title": "Standard UK political update — no breaking news detected", "source": "baseline",
             "published": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")}
        ]

    return headlines


def assess_survival(profile: dict, headlines: list[dict], date_str: str) -> dict:
    """Assess Starmer's political survival chances based on LDAP-7 + recent events."""

    # Extract LDAP-7 dimension scores from profile text
    profile_text = STARMER_PROFILE.read_text() if STARMER_PROFILE.exists() else ""

    dimensions = {
        "D1_optionality": _extract_dimension(profile_text, "D1", 4),
        "D2_coercion": _extract_dimension(profile_text, "D2", 3),
        "D3_popularity": _extract_dimension(profile_text, "D3", 6),
        "D4_constraint_rejection": _extract_dimension(profile_text, "D4", 2),
        "D5_zero_sum": _extract_dimension(profile_text, "D5", 2),
        "D6_escalate_retreat": _extract_dimension(profile_text, "D6", 2),
        "D7_loyalty": _extract_dimension(profile_text, "D7", 4),
    }

    # Adjust dimensions based on today's headlines
    headline_text = " ".join(h["title"] for h in headlines).lower()

    # D3 (Popularity) adjustments
    if any(k in headline_text for k in ["poll", "approval", "rating", "yougov"]):
        # Poll movement detected — adjust D3
        if any(k in headline_text for k in ["drop", "fall", "decline", "low"]):
            dimensions["D3_popularity"] = min(7, dimensions["D3_popularity"] + 1)
        elif any(k in headline_text for k in ["rise", "improve", "increase", "surge"]):
            dimensions["D3_popularity"] = max(3, dimensions["D3_popularity"] - 1)

    # D1 (Optionality) adjustments
    if any(k in headline_text for k in ["speech", "announce", "plan", "pledge", "policy"]):
        dimensions["D1_optionality"] = min(5, dimensions["D1_optionality"] + 1)

    # D4 (Constraint Rejection)
    if any(k in headline_text for k in ["rebel", "revolt", "suspension", "expel"]):
        dimensions["D4_constraint_rejection"] = min(4, dimensions["D4_constraint_rejection"] + 1)

    # Compute survival score
    # Scale each dimension to 0-1, weight and sum, then convert to probability
    # Formula: survival = weighted_score * 100
    weighted = 0.0
    dim_details = {}
    for dim, weight in DIMENSION_WEIGHTS_SURVIVAL.items():
        score = dimensions.get(dim, 4)
        # For each dimension, higher isn't always better for survival
        # D3 (popularity sensitivity): 4-5 is optimal; lower = ignores voters, higher = too reactive
        if dim == "D3_popularity":
            # Inverted U-shape: optimal at 5
            norm = max(0, 1.0 - abs(score - 5) * 0.25)
        elif dim == "D4_constraint_rejection":
            # Lower is better for UK system (respects institutions)
            norm = max(0, 1.0 - (score - 1) * 0.2)
        elif dim == "D5_zero_sum":
            # Lower is better (cooperative)
            norm = max(0, 1.0 - (score - 1) * 0.15)
        else:
            # Middle range (3-5) generally good for survival
            norm = max(0, 1.0 - abs(score - 4) * 0.2)
        weighted += weight * norm
        dim_details[dim] = {"score": score, "normalized": round(norm, 2), "weight": weight}

    survival_pct = round(weighted * 100, 1)

    # Confidence in assessment
    if headlines and any(h["source"] != "baseline" for h in headlines):
        confidence = "moderate"
    else:
        confidence = "low"

    # Key risk factors
    risks = []
    strengths = []
    if dimensions["D3_popularity"] >= 6:
        risks.append("High popularity sensitivity — policy reactive to negative polling")
    if dimensions["D5_zero_sum"] >= 3:
        risks.append("Zero-sum framing emerging — risks adversarial relationships")
    if dimensions["D7_loyalty"] <= 3:
        risks.append("Low loyalty score — narrow trust circle leaves coalition vulnerable")
    if dimensions["D4_constraint_rejection"] <= 2:
        strengths.append("Strong institutional respect — avoids constitutional crises")
    if dimensions["D2_coercion"] <= 3:
        strengths.append("Non-coercive leadership — coalition-building, not confrontation")

    return {
        "date": date_str,
        "survival_probability": survival_pct,
        "sherman_kent_band": _pct_to_band(survival_pct),
        "confidence": confidence,
        "dimensions": dim_details,
        "risks": risks,
        "strengths": strengths,
        "headline_count": len(headlines),
    }


def _extract_dimension(text: str, dim_label: str, default: int) -> int:
    """Extract a dimension score from profile text."""
    pattern = rf"{dim_label}\s*[—\-–]+\s*.*?Score:\s*(\d+)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return int(match.group(1))
    return default


def _pct_to_band(pct: float) -> str:
    if pct >= 80:
        return "highly likely"
    elif pct >= 65:
        return "likely"
    elif pct >= 45:
        return "even chance"
    elif pct >= 25:
        return "unlikely"
    return "highly unlikely"


def generate_report(assessment: dict, headlines: list[dict]) -> str:
    """Generate a formatted daily Starmer assessment."""
    lines = []
    lines.append(f"# Keir Starmer — Political Survival Assessment")
    lines.append(f"**Date:** {assessment['date']}")
    lines.append(f"**Survival Probability:** {assessment['survival_probability']}% ({assessment['sherman_kent_band']})")
    lines.append(f"**Confidence:** {assessment['confidence']}")
    lines.append("")

    lines.append("## LDAP-7 Dimension Scores")
    lines.append("")
    lines.append("| Dimension | Score (1-7) | Normalized | Weight |")
    lines.append("|-----------|-------------|------------|--------|")
    for dim_key, dim_label in [("D1_optionality", "D1 Optionality"),
                                ("D2_coercion", "D2 Coercion"),
                                ("D3_popularity", "D3 Popularity Sensitivity"),
                                ("D4_constraint_rejection", "D4 Constraint Rejection"),
                                ("D5_zero_sum", "D5 Zero-Sum Framing"),
                                ("D6_escalate_retreat", "D6 Escalate-Retreat"),
                                ("D7_loyalty", "D7 Loyalty")]:
        info = assessment["dimensions"].get(dim_key, {})
        score = info.get("score", "?")
        norm = info.get("normalized", "?")
        weight = info.get("weight", "?")
        lines.append(f"| {dim_label} | {score}/7 | {norm} | {weight} |")
    lines.append("")

    if assessment.get("strengths"):
        lines.append("## Strengths")
        for s in assessment["strengths"]:
            lines.append(f"- ✅ {s}")
        lines.append("")

    if assessment.get("risks"):
        lines.append("## Risks to Survival")
        for r in assessment["risks"]:
            lines.append(f"- ⚠ {r}")
        lines.append("")

    lines.append("## Headlines Considered")
    lines.append("")
    for h in headlines[:5]:
        title = h.get("title", "")[:120]
        source = h.get("source", "?")
        lines.append(f"- [{source}] {title}")
    lines.append("")

    # Survival outlook
    lines.append("## Outlook")
    lines.append("")
    if assessment['survival_probability'] >= 70:
        lines.append(f"Starmer's position is relatively secure ({assessment['survival_probability']}%). "
                     "No immediate threat to his leadership, though medium-term risks from "
                     "economic headwinds and internal party dynamics persist.")
    elif assessment['survival_probability'] >= 50:
        lines.append(f"Starmer faces moderate headwinds ({assessment['survival_probability']}%). "
                     "His position is not immediately threatened but sustained negative "
                     "pressure could erode his standing over 3-6 months.")
    else:
        lines.append(f"Starmer's position is under significant threat ({assessment['survival_probability']}%). "
                     "Multiple risk factors converging. Leadership challenge becomes "
                     "a realistic possibility within 6-12 months.")

    return "\n".join(lines)


def update_tracker(assessment: dict) -> None:
    """Update the daily tracker with today's assessment."""
    tracker = load_json(TRACKER_FILE)
    if not tracker:
        tracker = {
            "version": 1,
            "created": dt.datetime.now(dt.timezone.utc).isoformat() + "Z",
            "assessments": [],
            "trajectory": "stable",
        }
    tracker.setdefault("assessments", []).append({
        "date": assessment["date"],
        "survival_probability": assessment["survival_probability"],
        "band": assessment["sherman_kent_band"],
        "confidence": assessment["confidence"],
        "dimensions": {k: v["score"] for k, v in assessment.get("dimensions", {}).items()},
        "risk_count": len(assessment.get("risks", [])),
    })
    # Keep last 90 days
    tracker["assessments"] = tracker["assessments"][-90:]

    # Compute trajectory
    scores = [a["survival_probability"] for a in tracker["assessments"]]
    if len(scores) >= 3:
        recent = scores[-3:]
        if all(recent[i] < recent[i-1] for i in range(1, 3)):
            tracker["trajectory"] = "declining"
        elif all(recent[i] > recent[i-1] for i in range(1, 3)):
            tracker["trajectory"] = "improving"
        else:
            tracker["trajectory"] = "stable"

    save_json(TRACKER_FILE, tracker)


def show_report() -> None:
    """Show the Starmer tracker summary."""
    tracker = load_json(TRACKER_FILE)
    assessments = tracker.get("assessments", [])
    if not assessments:
        print("No Starmer assessments recorded yet.")
        return
    print(f"# Starmer Political Survival Tracker")
    print(f"**Trajectory:** {tracker.get('trajectory', 'stable')}")
    print(f"**Total assessments:** {len(assessments)}")
    print()
    for a in assessments[-14:]:  # Last 14 days
        bar = "█" * max(0, int(a["survival_probability"] / 10))
        print(f"  {a['date']}: {bar} {a['survival_probability']}% ({a['band']}) [{a['confidence']}]")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default="", help="Date in YYYY-MM-DD format")
    parser.add_argument("--report", action="store_true", help="Show tracker summary")
    args = parser.parse_args()

    if args.report:
        show_report()
        return 0

    date_str = args.date or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")

    # Fetch headlines
    headlines = fetch_uk_headlines()
    log(f"Fetched {len(headlines)} UK headlines")

    # Assess survival
    assessment = assess_survival({}, headlines, date_str)
    log(f"Survival probability: {assessment['survival_probability']}%")

    # Generate and save report
    report = generate_report(assessment, headlines)
    STARMER_DIR.mkdir(parents=True, exist_ok=True)
    report_path = STARMER_DIR / f"{date_str}.md"
    report_path.write_text(report)
    log(f"Report saved: {report_path}")

    # Update tracker
    update_tracker(assessment)
    log(f"Tracker updated")

    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
