#!/usr/bin/env python3
"""
Batch skill scanner - runs skill_scanner.py on all skill directories
and produces a combined summary report.
"""
import sys
import os
import subprocess
import json
from datetime import datetime

SKILL_DIRS = [
    os.path.expanduser("~/.openclaw/skills"),
    "/usr/lib/node_modules/openclaw/skills",
]
SCANNER = os.path.expanduser("~/.openclaw/skills/skill-scanner/skill_scanner.py")

def get_skill_folders(base_dir):
    if not os.path.isdir(base_dir):
        return []
    return sorted([
        os.path.join(base_dir, d)
        for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d))
    ])

def scan_skill(skill_path):
    """Run scanner in JSON mode and return parsed result."""
    name = os.path.basename(skill_path)
    try:
        result = subprocess.run(
            [sys.executable, SCANNER, skill_path, "--json"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 or result.returncode in (1, 2):
            return json.loads(result.stdout)
        else:
            return {
                "error": f"Scanner exit code {result.returncode}: {result.stderr.strip()}",
                "skill_path": skill_path,
                "verdict": "error",
            }
    except Exception as e:
        return {
            "error": str(e),
            "skill_path": skill_path,
            "verdict": "error",
        }

def severity_score(s):
    return {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0, "error": 5}.get(s, 0)

def generate_report(all_results):
    lines = []
    lines.append("# 🔒 Daily Skill Security Audit Report")
    lines.append(f"**Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")

    total = len(all_results)
    approved = sum(1 for r in all_results if r.get("verdict") == "approved")
    caution = sum(1 for r in all_results if r.get("verdict") == "caution")
    rejected = sum(1 for r in all_results if r.get("verdict") == "reject")
    errors = sum(1 for r in all_results if r.get("verdict") == "error")
    total_findings = sum(len(r.get("findings", [])) for r in all_results)
    critical_findings = sum(
        1 for r in all_results for f in r.get("findings", []) if f.get("severity") == "critical"
    )
    high_findings = sum(
        1 for r in all_results for f in r.get("findings", []) if f.get("severity") == "high"
    )

    lines.append(f"- **Skills Scanned:** {total}")
    lines.append(f"- **Approved:** {approved}")
    lines.append(f"- **Caution (minor issues):** {caution}")
    lines.append(f"- **Rejected:** {rejected}")
    lines.append(f"- **Errors:** {errors}")
    lines.append(f"- **Total Findings:** {total_findings}")
    lines.append(f"- **🔴 Critical:** {critical_findings}")
    lines.append(f"- **🟠 High:** {high_findings}")
    lines.append("")

    if critical_findings > 0 or rejected > 0:
        lines.append("### ⚠️ Critical Alerts")
        lines.append("")
        for r in all_results:
            if r.get("verdict") == "reject":
                lines.append(f"- **{r.get('metadata',{}).get('name', os.path.basename(r.get('skill_path','')))}** — {r.get('verdict_reason','')}")
        lines.append("")

    lines.append("## Detailed Skill Reports")
    lines.append("")

    # Sort by severity (most problematic first)
    sorted_results = sorted(all_results, key=lambda r: max([severity_score(f.get("severity")) for f in r.get("findings", [])] + [0]), reverse=True)

    for r in sorted_results:
        skill_name = r.get("metadata", {}).get("name", "unknown") or os.path.basename(r.get("skill_path", "unknown"))
        skill_path = r.get("skill_path", "")
        verdict = r.get("verdict", "unknown")
        verdict_icon = {"approved": "✅", "caution": "⚠️", "reject": "🔴", "error": "❌"}.get(verdict, "❓")
        findings = r.get("findings", [])
        lines.append(f"### {verdict_icon} {skill_name}")
        lines.append(f"**Path:** `{skill_path}`")
        lines.append(f"**Verdict:** `{verdict.upper()}` — {r.get('verdict_reason', '')}")
        lines.append("")

        if r.get("error"):
            lines.append(f"_Error: {r['error']}_")
            lines.append("")
            continue

        meta = r.get("metadata", {})
        lines.append(f"- **Version:** {meta.get('version','unknown')} | **Author:** {meta.get('author','unknown')} | **Files:** {meta.get('file_count',0)} | **Scripts:** {meta.get('script_count',0)} | **Lines:** {meta.get('total_lines',0)}")
        lines.append("")

        if findings:
            lines.append(f"**{len(findings)} finding(s):**")
            lines.append("")
            for f in findings:
                sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "info": "ℹ️"}.get(f.get("severity",""), "❓")
                lines.append(f"  - {sev_icon} **{f.get('pattern_name','')}** ({f.get('severity','')}) — `{f.get('file_path','')}` line {f.get('line_number','')}")
                lines.append(f"    - {f.get('description','')}")
                lines.append(f"    - _Recommendation:_ {f.get('recommendation','')}")
                lines.append(f"    - Code: `{f.get('line_content','')[:120]}`")
                lines.append("")
        else:
            lines.append("*No issues detected.*")
            lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Scan Summary")
    lines.append("")
    lines.append(f"Scan completed at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}.")
    lines.append(f"- {total} skills audited")
    lines.append(f"- {total_findings} total findings ({critical_findings} critical, {high_findings} high)")
    lines.append("")

    return "\n".join(lines)

def main():
    all_results = []

    for base in SKILL_DIRS:
        folders = get_skill_folders(base)
        print(f"Scanning {len(folders)} skills in {base}...")
        for sf in folders:
            name = os.path.basename(sf)
            print(f"  → {name}...", end=" ", flush=True)
            result = scan_skill(sf)
            all_results.append(result)
            status = result.get("verdict", "error")
            print(f"[{status}]")

    report = generate_report(all_results)
    report_path = os.path.expanduser("~/.openclaw/workspace/exports/skill-audit-report.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\nReport written to {report_path}")

    # Also save JSON for programmatic use
    json_path = os.path.expanduser("~/.openclaw/workspace/exports/skill-audit-report.json")
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"JSON data written to {json_path}")

    # Summary stats for email body
    total = len(all_results)
    approved = sum(1 for r in all_results if r.get("verdict") == "approved")
    caution = sum(1 for r in all_results if r.get("verdict") == "caution")
    rejected = sum(1 for r in all_results if r.get("verdict") == "reject")
    total_findings = sum(len(r.get("findings", [])) for r in all_results)
    critical = sum(1 for r in all_results for f in r.get("findings", []) if f.get("severity") == "critical")

    print("\n===== SUMMARY =====")
    print(f"Scanned: {total} | ✅ Approved: {approved} | ⚠️ Caution: {caution} | 🔴 Rejected: {rejected}")
    print(f"Findings: {total_findings} total, {critical} critical")
    print(f"Report: {report_path}")

if __name__ == "__main__":
    main()
