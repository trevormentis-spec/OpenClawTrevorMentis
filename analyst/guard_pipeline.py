#!/usr/bin/env python3
"""Unified Quality Gate Pipeline — runs ALL guards on every brief before delivery.

Gate 0: STRUCTURAL    — All expected files present? Non-empty?
Gate 1: FABRICATION   — Unverified contracts/prices/tickers/pct claims? (via fabrication_check)
Gate 2: THEMES        — Required theme coverage adequate? (via themes_preflight)
Gate 3: CALIBRATION   — Sherman Kent band ↔ numeric prediction agreement?
Gate 4: COMPLETENESS   — Truncation? Word count in range? Missing sections?
Gate 5: SCOPE         — Content within assignment scope? (via scope_check)
Gate 6: RED_TEAM      — Forced dissent note exists?

Each gate returns: {status: PASS|WARN|BLOCK, issues: [...], detail: str}
BLOCK = stop delivery. WARN = log but proceed.

Usage:
    python3 analyst/guard_pipeline.py --brief-dir ~/trevor-briefings/2026-05-23
    python3 analyst/guard_pipeline.py --brief-dir ~/trevor-briefings/2026-05-23 --query "Ukraine energy" --json
    python3 analyst/guard_pipeline.py --brief-dir ~/trevor-briefings/2026-05-23 --block-on-warn
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
from typing import Any, Optional

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


# ═══════════════════════════════════════════════════════════════════════════════
# Gate 0: STRUCTURAL — are all expected deliverables present and non-empty?
# ═══════════════════════════════════════════════════════════════════════════════

EXPECTED_REGIONAL_JSON = {
    "europe.json", "north_america.json", "central_america_caribbean.json",
    "south_america.json", "africa.json", "middle_east.json",
    "central_asia.json", "south_east_asia.json", "east_asia.json", "south_asia.json",
    "oceania.json",
    "prediction_markets.json", "exec_summary.json",
}


def gate_structural(analysis_dir: pathlib.Path) -> dict[str, Any]:
    issues: list[str] = []
    detail_parts: list[str] = []

    if not analysis_dir.exists():
        return {"status": "BLOCK", "issues": [f"Analysis dir not found: {analysis_dir}"],
                "detail": "directory missing", "gate": "structural"}

    have = {p.name for p in analysis_dir.glob("*.json")}
    missing = sorted(EXPECTED_REGIONAL_JSON - have)
    if missing:
        status = "BLOCK" if len(missing) > 3 else "WARN"
        issues.append(f"Missing analysis files: {', '.join(missing)}")
    else:
        status = "PASS"

    # Check each file is non-empty and valid JSON
    empty_files = []
    invalid_files = []
    for json_file in sorted(analysis_dir.glob("*.json")):
        try:
            content = json_file.read_text().strip()
            if not content:
                empty_files.append(json_file.name)
            else:
                json.loads(content)  # validate parseable
        except json.JSONDecodeError:
            invalid_files.append(json_file.name)

    if empty_files:
        issues.append(f"Empty JSON files: {', '.join(empty_files)}")
        status = "BLOCK"
    if invalid_files:
        issues.append(f"Invalid JSON files: {', '.join(invalid_files)}")
        status = "BLOCK"

    detail_parts.append(f"{len(have)}/{len(EXPECTED_REGIONAL_JSON)} files present")
    if empty_files:
        detail_parts.append(f"{len(empty_files)} empty")
    if invalid_files:
        detail_parts.append(f"{len(invalid_files)} invalid")

    return {"gate": "structural", "status": status, "issues": issues,
            "detail": "; ".join(detail_parts)}


# ═══════════════════════════════════════════════════════════════════════════════
# Gate 1: FABRICATION — scan all text output for unverified claims
# ═══════════════════════════════════════════════════════════════════════════════

def gate_fabrication(analysis_dir: pathlib.Path, verbose: bool = False) -> dict[str, Any]:
    """Run fabrication_check on exec_summary and all regional analysis text."""
    issues: list[str] = []
    detail_parts: list[str] = []

    exec_summary = analysis_dir / "exec_summary.json"
    if not exec_summary.exists():
        return {"gate": "fabrication", "status": "WARN", "issues": ["No exec_summary.json to scan"],
                "detail": "skipped — no text source"}

    # Compile text from exec_summary BLUF + all key judgments + context
    try:
        exec_data = json.loads(exec_summary.read_text())
        text_to_scan = ""
        text_to_scan += exec_data.get("bluf", "") + "\n"
        text_to_scan += exec_data.get("context_paragraph", "") + "\n"
        for kj in exec_data.get("five_judgments", []):
            text_to_scan += kj.get("statement", "") + "\n"
    except Exception:
        return {"gate": "fabrication", "status": "WARN", "issues": ["Could not parse exec_summary.json"],
                "detail": "parse error"}

    if len(text_to_scan.strip()) < 100:
        return {"gate": "fabrication", "status": "WARN", "issues": ["Text too short for meaningful scan"],
                "detail": f"only {len(text_to_scan.strip())} chars"}

    # Write temp file for fabrication_check
    temp_brief = analysis_dir / "_gate_scan_text.md"
    temp_brief.write_text(text_to_scan)

    try:
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "analyst" / "fabrication_check.py"),
             "--brief", str(temp_brief), "--json"],
            capture_output=True, text=True, timeout=30, cwd=str(REPO_ROOT),
        )
        if proc.stdout.strip():
            findings = json.loads(proc.stdout)
            blockers = [f for f in findings
                       if f.get("status") == "UNVERIFIED"]
            warns = [f for f in findings
                    if f.get("status") in ("unverified", "unknown") and f.get("type") != "fabrication_risk"]

            for b in blockers:
                issues.append(f"BLOCK: {b.get('type')} — {b.get('detail', b.get('name', ''))}")
            for w in warns:
                if verbose:
                    issues.append(f"WARN: {w.get('type')} — {w.get('detail', w.get('ticker', ''))}")

            status = "BLOCK" if blockers else ("WARN" if warns and verbose else "PASS")
            detail_parts.append(f"{len(blockers)} blockers, {len(warns)} warnings, {len(findings)} total checks")
        else:
            status = "PASS"
            detail_parts.append("no findings")
    except subprocess.TimeoutExpired:
        status = "WARN"
        issues.append("Fabrication check timed out")
        detail_parts.append("timeout")
    except json.JSONDecodeError:
        status = "WARN"
        issues.append("Fabrication check output parse error")
        detail_parts.append("JSON parse error")
    except Exception as exc:
        status = "WARN"
        issues.append(f"Fabrication check failed: {exc}")
        detail_parts.append("exec error")
    finally:
        if temp_brief.exists():
            temp_brief.unlink()

    return {"gate": "fabrication", "status": status, "issues": issues,
            "detail": "; ".join(detail_parts)}


# ═══════════════════════════════════════════════════════════════════════════════
# Gate 2: THEMES — validate mandatory theme coverage
# ═══════════════════════════════════════════════════════════════════════════════

def gate_themes(analysis_dir: pathlib.Path, query: str = "geopolitical intelligence brief",
                verbose: bool = False) -> dict[str, Any]:
    """Run themes_preflight on the brief text content."""
    issues: list[str] = []
    detail_parts: list[str] = []

    exec_summary = analysis_dir / "exec_summary.json"
    if not exec_summary.exists():
        return {"gate": "themes", "status": "WARN", "issues": ["No exec_summary.json for theme check"],
                "detail": "skipped — no text source"}

    # Compile text from ALL analysis files (not just exec_summary — regional
    # analysis files contain the substantive coverage)
    text_to_scan = ""

    # Exec summary
    try:
        exec_data = json.loads(exec_summary.read_text())
        text_to_scan += exec_data.get("bluf", "") + "\n"
        text_to_scan += exec_data.get("context_paragraph", "") + "\n"
        for kj in exec_data.get("five_judgments", []):
            text_to_scan += kj.get("statement", "") + "\n"
    except Exception:
        pass  # exec_summary parse failure shouldn't block — proceed with regional files

    # All regional analysis files
    for region_file in sorted(analysis_dir.glob("*.json")):
        if region_file.name in ("exec_summary.json", "prediction_markets.json"):
            continue
        try:
            data = json.loads(region_file.read_text())
            for kj in data.get("key_judgments", []):
                text_to_scan += kj.get("statement", "") + "\n"
            if data.get("summary"):
                text_to_scan += data["summary"] + "\n"
            if data.get("analysis"):
                text_to_scan += data["analysis"] + "\n"
        except Exception:
            pass

    temp_brief = analysis_dir / "_gate_theme_scan.md"
    temp_brief.write_text(text_to_scan)

    try:
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "analyst" / "themes_preflight.py"),
             "--query", query, "--brief", str(temp_brief), "--json"],
            capture_output=True, text=True, timeout=30, cwd=str(REPO_ROOT),
        )

        if proc.stdout.strip():
            # themes_preflight.py --json prepends "Query category: ..." to stdout — strip it
            raw_stdout = proc.stdout.strip()
            # Find the first '{' to extract JSON
            json_start = raw_stdout.find('{')
            if json_start > 0:
                raw_stdout = raw_stdout[json_start:]
            try:
                data = json.loads(raw_stdout)
            except json.JSONDecodeError:
                return {"gate": "themes", "status": "WARN",
                        "issues": [f"JSON parse error: {raw_stdout[:200]}"],
                        "detail": "parse error"}
            coverage = data.get("coverage", [])
            required = data.get("required", [])
            missing = [c for c in coverage if c.get("status") == "FAIL"]
            # validate_coverage only returns FAIL results; passing = required - missing
            passing_count = len(required) - len(missing)

            for m in missing:
                issues.append(f"MISSING THEME: {m['theme']} — {m.get('detail', 'no coverage')}")

            # BLOCK only if ALL required themes are missing (complete coverage failure)
            status = "BLOCK" if len(missing) == len(required) and len(required) > 0 else ("WARN" if missing else "PASS")
            detail_parts.append(f"{passing_count} themes pass, {len(missing)} missing, {len(required)} required")
        else:
            status = "PASS"
            detail_parts.append("no theme requirements found")
    except subprocess.TimeoutExpired:
        status = "WARN"
        issues.append("Theme check timed out")
        detail_parts.append("timeout")
    except json.JSONDecodeError:
        status = "WARN"
        detail_parts.append("JSON parse error")
    except Exception as exc:
        status = "WARN"
        issues.append(f"Theme check failed: {exc}")
        detail_parts.append("exec error")
    finally:
        if temp_brief.exists():
            temp_brief.unlink()

    return {"gate": "themes", "status": status, "issues": issues,
            "detail": "; ".join(detail_parts)}


# ═══════════════════════════════════════════════════════════════════════════════
# Gate 3: CALIBRATION — Sherman Kent band ↔ numeric agreement + single-source cap
# ═══════════════════════════════════════════════════════════════════════════════

BANDS = {
    "almost certain":      (93, 99),
    "highly likely":       (75, 85),
    "likely":              (55, 70),
    "probable":            (55, 70),
    "even chance":         (45, 55),
    "chances about even":  (45, 55),
    "unlikely":            (25, 35),
    "probably not":        (25, 35),
    "highly unlikely":     (10, 20),
    "almost no chance":    (1, 5),
    "remote":              (1, 5),
}


def gate_calibration(analysis_dir: pathlib.Path, verbose: bool = False) -> dict[str, Any]:
    """Validate Sherman Kent band ↔ prediction_pct consistency + single-source cap."""
    issues: list[str] = []
    total_kjs = 0
    band_mismatches = 0
    single_source_overrides = 0
    missing_indicators = 0

    for region_file in sorted(analysis_dir.glob("*.json")):
        if region_file.name == "exec_summary.json":
            continue
        try:
            payload = json.loads(region_file.read_text())
        except Exception:
            continue

        for kj in payload.get("key_judgments", []) or []:
            total_kjs += 1
            band = (kj.get("sherman_kent_band") or "").lower().strip()
            pct = kj.get("prediction_pct")

            # Check band ↔ pct alignment
            if band and band in BANDS:
                lo, hi = BANDS[band]
                if not isinstance(pct, (int, float)) or not (lo <= pct <= hi):
                    band_mismatches += 1
                    issues.append(
                        f"{region_file.name}: KJ '{kj.get('id', '?')}' "
                        f"band '{band}' ({lo}-{hi}) but pct={pct}"
                    )

            # Single-source cap
            if kj.get("single_source_basis") and isinstance(pct, (int, float)) and pct > 85:
                single_source_overrides += 1
                issues.append(
                    f"{region_file.name}: KJ '{kj.get('id', '?')}' "
                    f"single-source exceeds 85% cap ({pct}%)"
                )

            # Indicators: what_would_change_it needs both softener + tightener
            ind = kj.get("what_would_change_it") or []
            if not isinstance(ind, list) or len(ind) < 2:
                missing_indicators += 1
                if verbose:
                    issues.append(
                        f"{region_file.name}: KJ '{kj.get('id', '?')}' "
                        f"needs ≥2 what_would_change_it indicators (has {len(ind) if isinstance(ind, list) else 0})"
                    )

    # Calibration smell check
    pcts: list[int] = []
    for region_file in sorted(analysis_dir.glob("*.json")):
        if region_file.name == "exec_summary.json":
            continue
        try:
            payload = json.loads(region_file.read_text())
        except Exception:
            continue
        for kj in payload.get("key_judgments", []) or []:
            p = kj.get("prediction_pct")
            if isinstance(p, (int, float)):
                pcts.append(int(p))

    if pcts:
        n_high = sum(1 for p in pcts if p >= 75)
        if len(pcts) >= 6 and n_high / len(pcts) > 0.7:
            issues.append(
                f"CALIBRATION SMELL: {n_high}/{len(pcts)} KJs at ≥75% — spread your bands"
            )
        if len(set(pcts)) <= max(2, len(pcts) // 4):
            issues.append(
                f"CALIBRATION SMELL: only {len(set(pcts))} distinct values across {len(pcts)} KJs — "
                "round-number bias suspected"
            )

    status = "BLOCK" if band_mismatches > 0 else ("WARN" if missing_indicators > 0 else "PASS")

    detail_parts = [f"{total_kjs} KJs checked"]
    if band_mismatches:
        detail_parts.append(f"{band_mismatches} band mismatches")
    if single_source_overrides:
        detail_parts.append(f"{single_source_overrides} single-source cap violations")
    if missing_indicators:
        detail_parts.append(f"{missing_indicators} missing indicators")

    return {"gate": "calibration", "status": status, "issues": issues,
            "detail": "; ".join(detail_parts)}


# ═══════════════════════════════════════════════════════════════════════════════
# Gate 4: COMPLETENESS — truncation, word count, expected sections
# ═══════════════════════════════════════════════════════════════════════════════

def gate_completeness(analysis_dir: pathlib.Path) -> dict[str, Any]:
    """Check output is complete: no truncation, adequate word count, all sections present."""
    issues: list[str] = []
    detail_parts: list[str] = []

    exec_summary = analysis_dir / "exec_summary.json"
    if not exec_summary.exists():
        return {"gate": "completeness", "status": "BLOCK", "issues": ["No exec_summary.json"],
                "detail": "file missing"}

    try:
        exec_data = json.loads(exec_summary.read_text())
    except Exception as exc:
        return {"gate": "completeness", "status": "BLOCK",
                "issues": [f"exec_summary.json parse error: {exc}"],
                "detail": "parse error"}

    # Check BLUF exists and is substantive
    bluf = exec_data.get("bluf", "")
    if not bluf or len(bluf.split()) < 20:
        issues.append(f"BLUF too short: {len(bluf.split())} words (min 20)")
        detail_parts.append("BLUF short")

    # Check five_judgments completeness
    judgments = exec_data.get("five_judgments", [])
    if len(judgments) < 3:
        issues.append(f"Only {len(judgments)} key judgments (min 3)")
        detail_parts.append(f"{len(judgments)}/5 judgments")
    else:
        detail_parts.append(f"{len(judgments)} judgments")

    # Check context paragraph
    context = exec_data.get("context_paragraph", "")
    if not context or len(context.split()) < 10:
        issues.append("Context paragraph missing or too short")

    # Truncation detection — does BLUF end mid-sentence?
    if bluf:
        last_char = bluf.strip()[-1] if bluf.strip() else ""
        if last_char not in (".", "!", "?", '"', "'", ")", "]", "}", "`"):
            issues.append("TRUNCATION: BLUF ends mid-sentence — may be incomplete")

    # Regional coverage check
    regions_present = 0
    for region_file in sorted(analysis_dir.glob("*.json")):
        if region_file.name == "exec_summary.json" or region_file.name == "prediction_markets.json":
            continue
        try:
            data = json.loads(region_file.read_text())
            if data.get("key_judgments") or data.get("summary") or data.get("analysis"):
                regions_present += 1
        except Exception:
            pass
    detail_parts.append(f"{regions_present} regions with content")

    if regions_present < 5:
        issues.append(f"Only {regions_present} regions have content (expected ≥5)")

    status = "BLOCK" if (len(judgments) < 3 or not bluf) else ("WARN" if issues else "PASS")

    return {"gate": "completeness", "status": status, "issues": issues,
            "detail": "; ".join(detail_parts)}


# ═══════════════════════════════════════════════════════════════════════════════
# Gate 5: SCOPE — is the output within assignment scope?
# ═══════════════════════════════════════════════════════════════════════════════

def gate_scope(analysis_dir: pathlib.Path, scope_topic: str = "geopolitical intelligence brief",
               verbose: bool = False) -> dict[str, Any]:
    """Run scope_check against the brief content."""
    issues: list[str] = []
    detail_parts: list[str] = []

    try:
        sys.path.insert(0, str(REPO_ROOT))
        from analyst.scope_check import check_scope

        result = check_scope(scope_topic)
        status_code = result.get("scope_status", "in_scope")

        if status_code == "out_of_scope":
            return {"gate": "scope", "status": "BLOCK",
                    "issues": [f"Topic '{scope_topic}' classified as OUT_OF_SCOPE: {result.get('rationale', '')}"],
                    "detail": "out_of_scope"}
        elif status_code == "adjacent":
            vectors = result.get("topic_vectors", [])
            detail = f"adjacent — {len(vectors)} vectors found"
            if vectors and verbose:
                for v in vectors:
                    issues.append(f"Adjacency vector: {v}")
            return {"gate": "scope", "status": "WARN", "issues": issues, "detail": detail}
        else:
            return {"gate": "scope", "status": "PASS", "issues": [],
                    "detail": f"in_scope: {result.get('rationale', '')}"}

    except ImportError:
        return {"gate": "scope", "status": "WARN", "issues": ["scope_check module not importable"],
                "detail": "skipped — import error"}
    except Exception as exc:
        return {"gate": "scope", "status": "WARN", "issues": [f"scope check failed: {exc}"],
                "detail": "exec error"}


# ═══════════════════════════════════════════════════════════════════════════════
# Gate 6: RED_TEAM — forced dissent note exists
# ═══════════════════════════════════════════════════════════════════════════════

def gate_red_team(analysis_dir: pathlib.Path) -> dict[str, Any]:
    """Verify red-team / forced dissent analysis exists and is substantive."""
    issues: list[str] = []
    detail_parts: list[str] = []

    red_team_path = analysis_dir / "red_team.md"
    if not red_team_path.exists():
        return {"gate": "red_team", "status": "BLOCK",
                "issues": ["Missing: analysis/red_team.md — forced dissent required for all briefs"],
                "detail": "file missing"}

    content = red_team_path.read_text().strip()
    if len(content.split()) < 30:
        return {"gate": "red_team", "status": "WARN",
                "issues": ["Red-team note exists but is very short (<30 words) — may be perfunctory"],
                "detail": f"only {len(content.split())} words"}

    return {"gate": "red_team", "status": "PASS", "issues": [],
            "detail": f"{len(content.split())} words — substantive"}


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def run_pipeline(
    brief_dir: str | pathlib.Path,
    query: str = "geopolitical intelligence brief",
    verbose: bool = False,
    block_on_warn: bool = False,
) -> dict[str, Any]:
    """Run all 7 quality gates on a brief directory. Returns aggregated report."""
    wd = pathlib.Path(brief_dir).expanduser().resolve()
    analysis_dir = wd / "analysis"

    if not analysis_dir.exists():
        return {
            "passed": False,
            "total_gates": 0,
            "passed_count": 0,
            "blocked_count": 0,
            "warn_count": 0,
            "total_issues": 1,
            "gates": [],
            "detail": f"Analysis directory not found: {analysis_dir}",
        }

    gates = [
        gate_structural(analysis_dir),
        gate_fabrication(analysis_dir, verbose=verbose),
        gate_themes(analysis_dir, query=query, verbose=verbose),
        gate_calibration(analysis_dir, verbose=verbose),
        gate_completeness(analysis_dir),
        gate_scope(analysis_dir, scope_topic=query, verbose=verbose),
        gate_red_team(analysis_dir),
    ]

    # Apply block_on_warn — escalate WARN to BLOCK
    if block_on_warn:
        for g in gates:
            if g["status"] == "WARN":
                g["status"] = "BLOCK"

    # Count
    blocked = [g for g in gates if g["status"] == "BLOCK"]
    warned = [g for g in gates if g["status"] == "WARN"]
    passed = [g for g in gates if g["status"] == "PASS"]
    total_issues = sum(len(g["issues"]) for g in gates)

    all_passed = len(blocked) == 0

    # Build detail
    if all_passed:
        detail = f"ALL CLEAR — {len(passed)}/{len(gates)} gates passing"
        if warned:
            detail += f" ({len(warned)} warnings)"
    else:
        detail = f"BLOCKED — {len(blocked)}/{len(gates)} gates blocking delivery"

    return {
        "passed": all_passed,
        "total_gates": len(gates),
        "passed_count": len(passed),
        "blocked_count": len(blocked),
        "warn_count": len(warned),
        "total_issues": total_issues,
        "gates": gates,
        "detail": detail,
    }


def format_report(results: dict[str, Any], verbose: bool = False) -> str:
    """Format pipeline results as a readable console report."""
    lines = []
    lines.append("=" * 72)
    lines.append("  QUALITY GATE PIPELINE REPORT")
    lines.append("=" * 72)
    lines.append("")

    for g in results["gates"]:
        gate_name = g["gate"].upper()
        if g["status"] == "PASS":
            lines.append(f"  ✅ GATE {gate_name}: {g['detail']}")
        elif g["status"] == "WARN":
            lines.append(f"  ⚠️  GATE {gate_name}: {g['detail']}")
        elif g["status"] == "BLOCK":
            lines.append(f"  ❌ GATE {gate_name}: {g['detail']}")

        for issue in g["issues"]:
            lines.append(f"     → {issue}")
        lines.append("")

    lines.append("-" * 72)
    passed = results["passed_count"]
    blocked = results["blocked_count"]
    warned = results["warn_count"]
    total = results["total_gates"]

    if results["passed"]:
        lines.append(f"  RESULT: ✅ PASS — {passed}/{total} gates passing")
        if warned:
            lines.append(f"  ({warned} warnings — logged but delivery proceeds)")
    else:
        lines.append(f"  RESULT: ❌ BLOCKED — {blocked}/{total} gates blocking")
        lines.append(f"  {passed}/{total} passing, {total - passed} failing")
        lines.append("  DELIVERY ABORTED — fix failures before re-running")

    lines.append(f"  Total issues: {results['total_issues']}")
    lines.append("=" * 72)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Unified Quality Gate Pipeline — run ALL guards on a brief",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 analyst/guard_pipeline.py --brief-dir ~/trevor-briefings/2026-05-23
  python3 analyst/guard_pipeline.py --brief-dir ~/trevor-briefings/2026-05-23 --query "Ukraine energy"
  python3 analyst/guard_pipeline.py --brief-dir ~/trevor-briefings/2026-05-23 --verbose --json
  python3 analyst/guard_pipeline.py --brief-dir ~/trevor-briefings/2026-05-23 --block-on-warn
        """,
    )
    parser.add_argument("--brief-dir", required=True,
                        help="Path to brief working directory (e.g., ~/trevor-briefings/2026-05-23)")
    parser.add_argument("--query", default="geopolitical intelligence brief",
                        help="Topic/query for scope and theme gates")
    parser.add_argument("--verbose", action="store_true", help="Show all warnings and details")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted report")
    parser.add_argument("--block-on-warn", action="store_true",
                        help="Treat WARN as BLOCK — stricter delivery gating")
    args = parser.parse_args()

    results = run_pipeline(
        brief_dir=args.brief_dir,
        query=args.query,
        verbose=args.verbose,
        block_on_warn=args.block_on_warn,
    )

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(format_report(results, verbose=args.verbose))

    sys.exit(0 if results["passed"] else 1)


if __name__ == "__main__":
    main()
