#!/usr/bin/env python3
"""
Consolidated skill security audit script.
Scans all installed skills across all skill directories and generates an aggregated report.
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add skill-scanner to path
sys.path.insert(0, os.path.expanduser("~/.openclaw/skills/skill-scanner"))
from skill_scanner import SkillScanner, format_markdown, format_json, Severity, Verdict

SKILL_DIRS = [
    os.path.expanduser("~/.openclaw/skills"),
    os.path.expanduser("~/.openclaw/workspace/skills"),
    "/usr/lib/node_modules/openclaw/skills",
]

def get_skill_dirs():
    """Get all actual skill subdirectories (skip files, skip skill-scanner itself)."""
    found = []
    for base in SKILL_DIRS:
        if not os.path.isdir(base):
            continue
        for entry in sorted(os.listdir(base)):
            full = os.path.join(base, entry)
            if os.path.isdir(full):
                found.append(full)
    return found

def scan_one(skill_path):
    """Scan a single skill directory, return (path, report_dict) or (path, error_str)."""
    try:
        scanner = SkillScanner(skill_path)
        report = scanner.scan()
        return skill_path, report, None
    except FileNotFoundError as e:
        return skill_path, None, str(e)
    except Exception as e:
        return skill_path, None, str(e)

def main():
    skill_dirs = get_skill_dirs()
    print(f"Found {len(skill_dirs)} skills to scan.")
    
    results = []
    errors = []
    
    for i, sd in enumerate(skill_dirs):
        skill_name = Path(sd).name
        print(f"[{i+1}/{len(skill_dirs)}] Scanning {skill_name}...", end=" ", flush=True)
        path, report, error = scan_one(sd)
        if error:
            print(f"ERROR: {error}")
            errors.append((skill_name, error))
        else:
            verdict = report.verdict
            findings_n = len(report.findings)
            if verdict == 'reject':
                status = "🔴 REJECT"
            elif verdict == 'caution':
                status = "🟡 CAUTION"
            else:
                status = "🟢 APPROVED"
            print(f"{status} ({findings_n} findings)")
            results.append(report)
    
    # Generate summary
    total = len(results) + len(errors)
    approved = sum(1 for r in results if r.verdict == 'approved')
    caution = sum(1 for r in results if r.verdict == 'caution')
    rejected = sum(1 for r in results if r.verdict == 'reject')
    
    all_findings = []
    for r in results:
        for f in r.findings:
            all_findings.append((r.metadata.name, f))
    
    critical = [f for f in all_findings if f[1].severity == 'critical']
    high = [f for f in all_findings if f[1].severity == 'high']
    medium = [f for f in all_findings if f[1].severity == 'medium']
    low = [f for f in all_findings if f[1].severity == 'low']
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    
    # Build summary report
    report_lines = [
        "# 🔒 Daily Skill Security Audit Report",
        "",
        f"**Date:** {timestamp}",
        f"**Tool:** Skill Scanner v1.0",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"- **Total skills scanned:** {total}",
        f"- **✅ Approved:** {approved}",
        f"- **⚠️ Caution (high-severity):** {caution}",
        f"- **🔴 Rejected (critical-severity):** {rejected}",
        f"- **Scan errors:** {len(errors)}",
        "",
        f"- **Total findings:** {len(all_findings)}",
        f"  - Critical: {len(critical)}",
        f"  - High: {len(high)}",
        f"  - Medium: {len(medium)}",
        f"  - Low: {len(low)}",
        "",
        "---",
        "",
    ]
    
    # Verdict summary table
    report_lines.extend([
        "## Verdict Summary",
        "",
        "| Skill | Verdict | Findings | Key Issues |",
        "|-------|---------|----------|------------|",
    ])
    for r in results:
        key_issues = ", ".join(sorted(set(f.pattern_name for f in r.findings)))
        icon = "🔴" if r.verdict == 'reject' else ("🟡" if r.verdict == 'caution' else "🟢")
        report_lines.append(f"| {r.metadata.name} | {icon} {r.verdict.upper()} | {len(r.findings)} | {key_issues or 'None'} |")
    for skill_name, err in errors:
        report_lines.append(f"| {skill_name} | ❌ ERROR | - | {err} |")
    
    report_lines.extend(["", "---", "", "## Critical Findings", ""])
    
    if critical:
        report_lines.extend([
            "| Skill | Pattern | File | Line | Description |",
            "|-------|---------|------|------|-------------|",
        ])
        for skill_name, f in critical:
            report_lines.append(f"| {skill_name} | {f.pattern_name} | `{f.file_path}:{f.line_number}` | `{f.line_content[:80]}` | {f.description} |")
    else:
        report_lines.append("_No critical issues found._ ✅")
    
    report_lines.extend(["", "---", "", "## High Severity Findings", ""])
    
    if high:
        report_lines.extend([
            "| Skill | Pattern | File | Line | Description |",
            "|-------|---------|------|------|-------------|",
        ])
        for skill_name, f in high:
            report_lines.append(f"| {skill_name} | {f.pattern_name} | `{f.file_path}:{f.line_number}` | `{f.line_content[:80]}` | {f.description} |")
    else:
        report_lines.append("_No high-severity issues found._ ✅")
    
    report_lines.extend(["", "---", "", "## Medium Severity Findings", ""])
    
    if medium:
        report_lines.extend([
            "| Skill | Pattern | File | Line | Description |",
            "|-------|---------|------|------|-------------|",
        ])
        for skill_name, f in medium:
            report_lines.append(f"| {skill_name} | {f.pattern_name} | `{f.file_path}:{f.line_number}` | `{f.line_content[:80]}` | {f.description} |")
    else:
        report_lines.append("_No medium-severity issues found._ ✅")
    
    report_lines.extend(["", "---", "", "## Scan Errors", ""])
    
    if errors:
        for skill_name, err in errors:
            report_lines.append(f"- **{skill_name}:** {err}")
    else:
        report_lines.append("_No scan errors._ ✅")
    
    report_lines.extend(["", "---", "", "## Detailed Per-Skill Reports", ""])
    
    for r in results:
        report_lines.append("")
        report_lines.append(format_markdown(r))
        report_lines.append("")
    
    report_content = "\n".join(report_lines)
    
    # Output path
    exports_dir = Path.home() / ".openclaw" / "workspace" / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    report_path = exports_dir / f"skill-security-audit-{datetime.now().strftime('%Y-%m-%d')}.md"
    report_path.write_text(report_content)
    print(f"\n✅ Full report written to {report_path}")
    
    # Also save JSON data for processing
    json_path = exports_dir / f"skill-security-audit-{datetime.now().strftime('%Y-%m-%d')}.json"
    json_data = {
        "timestamp": timestamp,
        "total_skills": total,
        "approved": approved,
        "caution": caution,
        "rejected": rejected,
        "errors": len(errors),
        "total_findings": len(all_findings),
        "critical_count": len(critical),
        "high_count": len(high),
        "medium_count": len(medium),
        "findings": [
            {
                "skill": skill_name,
                "pattern": f.pattern_name,
                "severity": f.severity,
                "file": f.file_path,
                "line": f.line_number,
                "description": f.description
            }
            for skill_name, f in all_findings
        ],
        "error_details": [{"skill": s, "error": e} for s, e in errors]
    }
    json_path.write_text(json.dumps(json_data, indent=2))
    print(f"✅ JSON data written to {json_path}")
    
    # Print executive summary to stdout
    print("\n" + "="*60)
    print("EXECUTIVE SUMMARY")
    print("="*60)
    print(f"Total: {total}  |  Approved: {approved}  |  Caution: {caution}  |  Rejected: {rejected}  |  Errors: {len(errors)}")
    print(f"Findings: {len(all_findings)} (Critical: {len(critical)}, High: {len(high)}, Medium: {len(medium)})")
    
    return report_path

if __name__ == "__main__":
    main()
