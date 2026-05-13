#!/usr/bin/env python3
"""
Meta-Cognition Engine — Self-Observing Analysis Auditor.

Analyzes Trevor's own analytical outputs across multiple days to detect:
- Repeated reasoning structures (same evidence patterns, same scenario types)
- Confidence band inertia (same bands used for same regions daily)
- Evidence monoculture (same sources cited repeatedly, no diversity)
- Structural pattern repetition (same K.J. structure day after day)

When patterns repeat 3+ days running, generates a meta-cognitive alert
that is injected into the next analysis prompt to force alternative
reasoning.

This is the closest Trevor gets to "thinking about its own thinking."

Usage:
    python3 scripts/meta_cognition.py                           # Check last 7 days
    python3 scripts/meta_cognition.py --days 14                # Deeper lookback
    python3 scripts/meta_cognition.py --report                 # Full pattern report
    python3 scripts/meta_cognition.py --inject                 # Write injection file
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys
from collections import Counter
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BRIEFINGS_DIR = pathlib.Path.home() / "trevor-briefings"
PATTERN_DIR = REPO_ROOT / "analysis" / "meta-cognition"

# Days of repetition before flagging as pattern inertia
PATTERN_INERTIA_DAYS = 3


def log(msg: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%H:%M:%S")
    print(f"[metacog {ts}] {msg}", file=sys.stderr, flush=True)


def load_json(path: pathlib.Path) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, Exception):
            return {}
    return {}


def find_brief_dirs(days: int) -> list[str]:
    """Find trevor-briefings dirs for the last N days that have analysis outputs."""
    found = []
    today = dt.datetime.now(dt.timezone.utc).date()
    for i in range(days):
        date_str = (today - dt.timedelta(days=i)).strftime("%Y-%m-%d")
        for base in [BRIEFINGS_DIR, REPO_ROOT / "trevor-briefings"]:
            analysis_dir = base / date_str / "analysis"
            if analysis_dir.exists() and (analysis_dir / "exec_summary.json").exists():
                found.append(date_str)
                break
    return found


def load_day_analysis(date_str: str) -> dict | None:
    """Load exec summary + all regional analyses for a day."""
    for base in [BRIEFINGS_DIR, REPO_ROOT / "trevor-briefings"]:
        analysis_dir = base / date_str / "analysis"
        if not analysis_dir.exists():
            continue
        result = {"date": date_str, "exec": None, "regions": {}}
        
        exec_path = analysis_dir / "exec_summary.json"
        if exec_path.exists():
            result["exec"] = load_json(exec_path)
        
        for region in ["europe", "asia", "middle_east", "north_america",
                        "south_central_america", "global_finance"]:
            rpath = analysis_dir / f"{region}.json"
            if rpath.exists():
                result["regions"][region] = load_json(rpath)
        
        if result["exec"]:
            return result
    return None


def extract_patterns(analysis: dict) -> dict:
    """Extract structural patterns from a day's analysis."""
    patterns = {
        "date": analysis["date"],
        "bluf": (analysis.get("exec", {}) or {}).get("bluf", ""),
        "judgment_regions": [],
        "judgment_bands": [],
        "judgment_statements": [],
        "judgment_keywords": [],
        "scenario_types": [],
        "source_citations": [],
    }
    
    exec_data = analysis.get("exec") or {}
    for kj in exec_data.get("five_judgments", []):
        patterns["judgment_regions"].append(kj.get("drawn_from_region", "unknown"))
        patterns["judgment_bands"].append(kj.get("sherman_kent_band", "unknown"))
        statement = kj.get("statement", "")
        patterns["judgment_statements"].append(statement)
        # Extract key nouns/verbs from statement
        keywords = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', statement)
        patterns["judgment_keywords"].extend(keywords[:5])
    
    # Extract scenario types from regional analyses
    for region_name, region_data in analysis.get("regions", {}).items():
        scenarios = region_data.get("scenarios", {}) if isinstance(region_data, dict) else {}
        if isinstance(scenarios, dict):
            for scenario_type in ["most_likely", "most_dangerous", "best_case", "wildcard"]:
                if scenarios.get(scenario_type):
                    patterns["scenario_types"].append(scenario_type)
    
    # Extract source citations from exec
    for kj in exec_data.get("five_judgments", []):
        eids = kj.get("evidence_incident_ids", [])
        patterns["source_citations"].extend(eids)
    
    return patterns


def compute_pattern_metrics(patterns: list[dict]) -> dict:
    """Analyze patterns across days for repetition and inertia."""
    metrics = {
        "days_analyzed": len(patterns),
        "region_repetition": {},
        "band_repetition": {},
        "bluf_similarity_scores": [],
        "pattern_alerts": [],
        "inertia_detected": False,
    }
    
    if len(patterns) < 2:
        return metrics
    
    # Track region distributions over time
    region_sequences: dict[str, list[str]] = {}
    for day_pattern in patterns:
        for region in day_pattern["judgment_regions"]:
            region_sequences.setdefault(region, []).append(day_pattern["date"])
    
    # If a region appears in judgments 3+ consecutive days, flag it
    for region, dates in region_sequences.items():
        if len(dates) >= PATTERN_INERTIA_DAYS:
            metrics["region_repetition"][region] = len(dates)
            metrics["pattern_alerts"].append(
                f"{region} has been in the top judgment set for {len(dates)} consecutive days. "
                f"Is this genuine sustained priority, or analytical inertia?"
            )
    
    # Track band usage over time
    band_counter = Counter()
    for day_pattern in patterns:
        for band in day_pattern["judgment_bands"]:
            band_counter[band] += 1
    
    metrics["band_repetition"] = dict(band_counter.most_common(5))
    
    # If same band dominates across days, flag it
    if band_counter:
        most_common_band, most_common_count = band_counter.most_common(1)[0]
        if most_common_count >= len(patterns) * 0.6:
            metrics["pattern_alerts"].append(
                f"'{most_common_band}' used in {most_common_count}/{len(patterns)} days "
                f"({round(most_common_count/len(patterns)*100)}%). "
                f"Confidence band distribution may be habitual rather than evidence-driven."
            )
    
    # BLUF similarity across consecutive days
    for i in range(1, len(patterns)):
        prev = patterns[i]
        curr = patterns[i - 1]
        if prev["bluf"] and curr["bluf"]:
            words_prev = set(re.findall(r'\b\w+\b', prev["bluf"].lower()))
            words_curr = set(re.findall(r'\b\w+\b', curr["bluf"].lower()))
            if words_prev and words_curr:
                sim = len(words_prev & words_curr) / max(len(words_prev | words_curr), 1)
                metrics["bluf_similarity_scores"].append({
                    "day1": prev["date"], "day2": curr["date"],
                    "similarity": round(sim, 3)
                })
                if sim >= 0.5:
                    metrics["pattern_alerts"].append(
                        f"BLUF between {prev['date']} and {curr['date']} shows "
                        f"{round(sim*100)}% word overlap. Consider whether the core "
                        f"narrative has genuinely changed."
                    )
    
    # Check for evidence monoculture (same K.J. evidence IDs across days)
    all_evidence = []
    for day_pattern in patterns:
        all_evidence.extend(day_pattern["source_citations"])
    evidence_counter = Counter(all_evidence)
    for eid, count in evidence_counter.most_common(3):
        if count >= PATTERN_INERTIA_DAYS:
            metrics["pattern_alerts"].append(
                f"Evidence ID '{eid}' cited in {count} consecutive days. "
                f"Is the evidence still current, or is it being carried forward inertially?"
            )
    
    if metrics["pattern_alerts"]:
        metrics["inertia_detected"] = True
    
    return metrics


def generate_meta_challenge(metrics: dict) -> str:
    """Generate a meta-cognitive challenge block for pipeline injection."""
    if not metrics.get("pattern_alerts"):
        return ""
    
    lines = []
    lines.append("\n\n### === META-COGNITIVE CHALLENGE ===")
    lines.append("The following structural patterns were detected across recent analyses.")
    lines.append("They may be analytically sound — or they may be cognitive inertia.")
    lines.append("")
    
    for alert in metrics["pattern_alerts"]:
        lines.append(f"- ⚠ {alert}")
    
    lines.append("")
    lines.append("**Recommended action:**")
    lines.append("1. Explicitly state whether each repeated pattern is analytically justified")
    lines.append("2. If justified, say WHY — don't carry forward without examination")
    lines.append("3. If not justified, break the pattern with alternative framing")
    lines.append("")
    lines.append("**Reminder:** The most comfortable analysis is often the least useful.")
    lines.append("=== END META-COGNITIVE CHALLENGE ===")
    
    return "\n".join(lines)


def run_audit(days: int = 7, inject: bool = False) -> dict:
    """Run the full meta-cognitive audit."""
    PATTERN_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find days with analysis
    date_strings = find_brief_dirs(days)
    if not date_strings:
        log("No brief directories found")
        return {"error": "no briefs found"}
    
    log(f"Analyzing {len(date_strings)} days of briefs")
    
    # Load each day's analysis
    patterns = []
    for date_str in sorted(date_strings):
        analysis = load_day_analysis(date_str)
        if analysis:
            patterns.append(extract_patterns(analysis))
    
    if not patterns:
        log("No analysis data to examine")
        return {"error": "no analysis data"}
    
    # Compute metrics
    metrics = compute_pattern_metrics(patterns)
    metrics["days_analyzed"] = len(patterns)
    metrics["date_range"] = f"{patterns[0]['date']} to {patterns[-1]['date']}"
    
    # Generate challenge
    if inject and metrics.get("pattern_alerts"):
        challenge = generate_meta_challenge(metrics)
        if challenge:
            challenge_path = PATTERN_DIR / f"meta-challenge-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d')}.md"
            challenge_path.write_text(
                f"# Meta-Cognitive Challenge\n"
                f"**Generated:** {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC\n"
                f"**Days analyzed:** {len(patterns)}\n"
                f"**Pattern alerts:** {len(metrics['pattern_alerts'])}\n\n"
                + challenge
            )
            log(f"Meta-cognitive challenge written: {challenge_path}")
    
    # Save audit report
    report_path = PATTERN_DIR / f"audit-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d')}.json"
    save_json(report_path, metrics)
    
    return metrics


def save_json(path: pathlib.Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def render_report(metrics: dict) -> str:
    """Render the meta-cognitive audit as a readable report."""
    lines = []
    lines.append("# Meta-Cognition Audit Report")
    lines.append(f"**Generated:** {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC")
    lines.append(f"**Days analyzed:** {metrics.get('days_analyzed', '?')}")
    lines.append(f"**Date range:** {metrics.get('date_range', 'N/A')}")
    lines.append(f"**Inertia detected:** {'YES ⚠' if metrics.get('inertia_detected') else 'No ✅'}")
    lines.append("")
    
    if metrics.get("region_repetition"):
        lines.append("## Region Repetition (Same regions in top judgments)")
        lines.append("")
        for region, count in sorted(metrics["region_repetition"].items(), key=lambda x: -x[1]):
            lines.append(f"- {region}: {count} consecutive days")
        lines.append("")
    
    if metrics.get("band_repetition"):
        lines.append("## Confidence Band Distribution (All Days)")
        lines.append("")
        for band, count in metrics["band_repetition"].items():
            pct = round(count / max(metrics["days_analyzed"], 1) * 100)
            bar = "█" * (pct // 10)
            lines.append(f"- {band}: {bar} {count}x ({pct}%)")
        lines.append("")
    
    if metrics.get("bluf_similarity_scores"):
        lines.append("## BLUF Similarity (Consecutive Days)")
        lines.append("")
        for entry in metrics["bluf_similarity_scores"]:
            flag = "⚠" if entry["similarity"] >= 0.5 else "✓"
            lines.append(f"- {entry['day1']} → {entry['day2']}: {flag} {round(entry['similarity']*100)}% overlap")
        lines.append("")
    
    if metrics.get("pattern_alerts"):
        lines.append("## Pattern Alerts")
        lines.append("")
        for alert in metrics["pattern_alerts"]:
            lines.append(f"- {alert}")
        lines.append("")
    
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7, help="Number of days to analyze")
    parser.add_argument("--inject", action="store_true", help="Write injection file")
    parser.add_argument("--report", action="store_true", help="Full pattern report")
    args = parser.parse_args()

    metrics = run_audit(days=args.days, inject=args.inject)

    if "error" in metrics:
        print(f"Meta-cognition audit: {metrics['error']}")
        return 1

    if args.report:
        print(render_report(metrics))
        return 0

    if metrics.get("inertia_detected"):
        print(f"Meta-cognition: {metrics['days_analyzed']} days analyzed, "
              f"{len(metrics['pattern_alerts'])} pattern alerts ⚠")
        for alert in metrics["pattern_alerts"]:
            print(f"  ⚠ {alert[:120]}...")
    else:
        print(f"Meta-cognition: {metrics['days_analyzed']} days analyzed, no pattern inertia detected ✅")

    return 0


if __name__ == "__main__":
    sys.exit(main())
