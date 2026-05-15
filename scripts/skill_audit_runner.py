#!/usr/bin/env python3
"""
Daily Skill Scanner Audit - scans all installed skills and generates a summary report.
Runs the skill-scanner against ~/.openclaw/skills and /usr/lib/node_modules/openclaw/skills.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone

# Add skill-scanner to path
sys.path.insert(0, os.path.expanduser("~/.openclaw/skills/skill-scanner"))
from skill_scanner import SkillScanner, format_markdown, Verdict, Severity

SCAN_DIRS = [
    os.path.expanduser("~/.openclaw/skills"),
    "/usr/lib/node_modules/openclaw/skills",
]

REPORT_PATH = os.path.expanduser("~/.openclaw/workspace/exports/skill-audit-report.md")
SUMMARY_PATH = os.path.expanduser("~/.openclaw/workspace/exports/skill-audit-summary.json")

SKIP_SKILLS = {
    'OpenClawTrevorMentis',  # Full workspace repo, not a skill
}

def scan_all():
    all_reports = []
    
    for base_dir in SCAN_DIRS:
        base = Path(base_dir)
        if not base.exists():
            print(f"SKIP: {base_dir} not found")
            continue
        
        for item in sorted(base.iterdir()):
            if not item.is_dir():
                continue
            skill_name = item.name
            if skill_name in SKIP_SKILLS:
                print(f"SKIP: {skill_name} (not a standalone skill)")
                continue
            print(f"Scanning: {skill_name} ...", end=" ", flush=True)
            try:
                scanner = SkillScanner(str(item))
                report = scanner.scan()
                all_reports.append(report)
                print(f"done ({report.verdict})")
            except Exception as e:
                print(f"ERROR: {e}")
    
    return all_reports

def build_aggregate_report(reports):
    # Count by verdict
    verdicts = {"approved": 0, "caution": 0, "reject": 0}
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    
    caution_skills = []
    reject_skills = []
    all_findings_by_severity = {"critical": [], "high": [], "medium": [], "low": [], "info": []}
    
    for r in reports:
        verdicts[r.verdict] = verdicts.get(r.verdict, 0) + 1
        if r.verdict == "caution":
            caution_skills.append(r.metadata.name)
        if r.verdict == "reject":
            reject_skills.append(r.metadata.name)
        
        for f in r.findings:
            severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1
            all_findings_by_severity[f.severity].append({
                "skill": r.metadata.name,
                "pattern": f.pattern_name,
                "file": f.file_path,
                "line": f.line_number,
                "severity": f.severity,
                "description": f.description,
            })
    
    total_skills = len(reports)
    total_files = sum(r.metadata.file_count for r in reports)
    total_lines = sum(r.metadata.total_lines for r in reports)
    total_findings = sum(len(r.findings) for r in reports)
    
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    lines = []
    lines.append("# 🔒 Daily Skill Scanner Audit Report")
    lines.append(f"**Generated:** {now_utc}")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- **Skills scanned:** {total_skills}")
    lines.append(f"- **Total files:** {total_files}")
    lines.append(f"- **Total lines of code:** {total_lines:,}")
    lines.append(f"- **Total findings:** {total_findings}")
    lines.append(f"- **Approved:** {verdicts.get('approved', 0)}")
    lines.append(f"- **Caution:** {verdicts.get('caution', 0)}")
    lines.append(f"- **Rejected:** {verdicts.get('reject', 0)}")
    lines.append("")
    
    lines.append("### Severity Breakdown")
    lines.append("")
    lines.append(f"| Severity | Count |")
    lines.append(f"|----------|-------|")
    lines.append(f"| 🔴 Critical | {severity_counts.get('critical', 0)} |")
    lines.append(f"| 🟠 High | {severity_counts.get('high', 0)} |")
    lines.append(f"| 🟡 Medium | {severity_counts.get('medium', 0)} |")
    lines.append(f"| 🔵 Low | {severity_counts.get('low', 0)} |")
    lines.append(f"| ⚪ Info | {severity_counts.get('info', 0)} |")
    lines.append("")
    
    if reject_skills:
        lines.append("### 🚫 Rejected Skills")
        lines.append("")
        for name in sorted(set(reject_skills)):
            lines.append(f"- **{name}**")
        lines.append("")
    
    if caution_skills:
        lines.append("### ⚠️ Skills Requiring Caution")
        lines.append("")
        for name in sorted(set(caution_skills)):
            lines.append(f"- **{name}**")
        lines.append("")
    
    # Group findings by skill for detailed section
    lines.append("## Detailed Findings by Skill")
    lines.append("")
    
    for r in sorted(reports, key=lambda x: x.metadata.name):
        if not r.findings:
            continue
        lines.append(f"### {r.metadata.name} (v{r.metadata.version})")
        lines.append(f"- **Verdict:** {r.verdict.upper()}")
        lines.append(f"- **Reason:** {r.verdict_reason}")
        lines.append(f"- **Files:** {r.metadata.file_count} | **Lines:** {r.metadata.total_lines}")
        lines.append("")
        
        for f in r.findings:
            severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "info": "⚪"}.get(f.severity, "⚪")
            lines.append(f"- {severity_icon} **[{f.severity.upper()}]** `{f.pattern_name}` in `{f.file_path}`:{f.line_number}")
            lines.append(f"  - *{f.description}*")
            lines.append(f"  - Recommendation: {f.recommendation}")
            lines.append("")
    
    # Skills with zero findings
    clean_skills = [r for r in reports if not r.findings]
    if clean_skills:
        lines.append("### ✅ Skills With No Issues")
        lines.append("")
        for r in sorted(clean_skills, key=lambda x: x.metadata.name):
            lines.append(f"- {r.metadata.name} v{r.metadata.version} — {r.metadata.file_count} files, {r.metadata.total_lines} lines")
        lines.append("")
    
    lines.append("---")
    lines.append(f"*Report generated by Daily Skill Scanner Audit cron ({now_utc})*")
    
    return "\n".join(lines), {
        "scan_timestamp": now_utc,
        "total_skills": total_skills,
        "total_files": total_files,
        "total_lines": total_lines,
        "total_findings": total_findings,
        "verdict_counts": verdicts,
        "severity_counts": severity_counts,
        "rejected_skills": sorted(set(reject_skills)),
        "caution_skills": sorted(set(caution_skills)),
        "critical_findings": all_findings_by_severity.get("critical", []),
    }

def main():
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    
    print("=" * 60)
    print("  DAILY SKILL SCANNER AUDIT")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 60)
    print()
    
    reports = scan_all()
    print(f"\nScanned {len(reports)} skills total.")
    
    markdown, summary = build_aggregate_report(reports)
    
    with open(REPORT_PATH, "w") as f:
        f.write(markdown)
    with open(SUMMARY_PATH, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nReport written to {REPORT_PATH}")
    print(f"Summary written to {SUMMARY_PATH}")
    
    # Print key stats for downstream use
    print(f"\nKEY STATS:")
    print(f"Total skills: {summary['total_skills']}")
    print(f"Total findings: {summary['total_findings']}")
    print(f"Rejected: {len(summary['rejected_skills'])}")
    print(f"Caution: {len(summary['caution_skills'])}")
    print(f"Critical issues: {len(summary['critical_findings'])}")
    
    # Return the markdown report path for emailing
    return REPORT_PATH

if __name__ == "__main__":
    main()
