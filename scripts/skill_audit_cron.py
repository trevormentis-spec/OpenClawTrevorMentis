#!/usr/bin/env python3
"""
Daily Skill Scanner Audit - Cron Wrapper
Scans all installed skills across all three skill directories,
aggregates findings, and outputs a consolidated report.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add scanner module path
sys.path.insert(0, os.path.expanduser("~/.openclaw/skills/skill-scanner"))
from skill_scanner import SkillScanner, format_markdown, format_json

SKILL_DIRS = [
    os.path.expanduser("~/.openclaw/skills"),
    "/usr/lib/node_modules/openclaw/skills",
    os.path.expanduser("~/.openclaw/workspace/skills"),
]

def get_all_skill_paths(base_dir):
    """Return list of skill subdirectories that look like skills (have SKILL.md or .py/.js files)."""
    base = Path(base_dir)
    if not base.exists():
        return []
    skills = []
    for item in sorted(base.iterdir()):
        if item.is_dir() and not item.name.startswith('.'):
            # Consider it a skill if it has a SKILL.md or at least one script
            has_skill_md = (item / "SKILL.md").exists()
            has_scripts = any(item.rglob("*.py")) or any(item.rglob("*.js"))
            if has_skill_md or has_scripts:
                skills.append(item)
    return skills

def main():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    output_lines = []
    
    output_lines.append("# Daily Skill Security Audit Report")
    output_lines.append(f"**Generated:** {timestamp}")
    output_lines.append("")
    output_lines.append("---")
    output_lines.append("")
    
    all_skills_scanned = 0
    total_findings = 0
    verdict_summary = {"approved": 0, "caution": 0, "reject": 0}
    all_reports = {}
    
    for skill_dir in SKILL_DIRS:
        label = Path(skill_dir).name
        output_lines.append(f"## Directory: `{skill_dir}`")
        output_lines.append("")
        
        skill_paths = get_all_skill_paths(skill_dir)
        if not skill_paths:
            output_lines.append("No skills found in this directory.\n")
            continue
        
        output_lines.append(f"Found {len(skill_paths)} skill(s):\n")
        
        for skill_path in skill_paths:
            skill_name = skill_path.name
            try:
                scanner = SkillScanner(str(skill_path))
                report = scanner.scan()
                all_skills_scanned += 1
                
                # Track verdict
                verdict_summary[report.verdict] = verdict_summary.get(report.verdict, 0) + 1
                
                findings_count = len(report.findings)
                total_findings += findings_count
                
                # Store for detail section
                all_reports[skill_name] = {
                    "verdict": report.verdict,
                    "verdict_reason": report.verdict_reason,
                    "findings_count": findings_count,
                    "files_scanned": report.metadata.file_count,
                    "scripts": report.metadata.script_count,
                    "lines": report.metadata.total_lines,
                    "version": report.metadata.version,
                    "findings": report.findings,
                }
                
                # Summary line
                status_icon = {"approved": "✅", "caution": "⚠️", "reject": "🚫"}
                icon = status_icon.get(report.verdict, "❓")
                finding_str = f" ({findings_count} finding{'s' if findings_count != 1 else ''})" if findings_count else ""
                output_lines.append(f"- {icon} **{skill_name}** → `{report.verdict.upper()}`{finding_str}")
                
            except Exception as e:
                output_lines.append(f"- ❌ **{skill_name}** → Scan error: {e}")
        
        output_lines.append("")
    
    # --- Executive Summary ---
    exec_summary_lines = [
        "---",
        "",
        "## Executive Summary",
        "",
        f"- **Total Skills Scanned:** {all_skills_scanned}",
        f"- **Total Findings:** {total_findings}",
        f"- **Approved:** {verdict_summary.get('approved', 0)}",
        f"- **Caution:** {verdict_summary.get('caution', 0)}",
        f"- **Reject:** {verdict_summary.get('reject', 0)}",
        "",
    ]
    
    # Reject list
    rejects = {k: v for k, v in all_reports.items() if v["verdict"] == "reject"}
    if rejects:
        exec_summary_lines.append("### 🚫 Skills Flagged for REJECT")
        exec_summary_lines.append("")
        for name, r in sorted(rejects.items()):
            exec_summary_lines.append(f"- **{name}**: {r['verdict_reason']}")
        exec_summary_lines.append("")
    
    # Caution list
    cautions = {k: v for k, v in all_reports.items() if v["verdict"] == "caution"}
    if cautions:
        exec_summary_lines.append("### ⚠️ Skills Flagged for CAUTION")
        exec_summary_lines.append("")
        for name, r in sorted(cautions.items()):
            exec_summary_lines.append(f"- **{name}**: {r['verdict_reason']}")
        exec_summary_lines.append("")
    
    # Insert executive summary after header
    insert_pos = next(i for i, l in enumerate(output_lines) if l == "---") + 1
    output_lines[insert_pos:insert_pos] = exec_summary_lines
    
    # --- Detailed Findings ---
    output_lines.append("---")
    output_lines.append("")
    output_lines.append("## Detailed Findings by Skill")
    output_lines.append("")
    
    for skill_name in sorted(all_reports.keys()):
        r = all_reports[skill_name]
        if r["findings_count"] == 0:
            continue  # Skip clean skills in details
        
        status_icon = {"approved": "✅", "caution": "⚠️", "reject": "🚫"}
        icon = status_icon.get(r["verdict"], "❓")
        
        output_lines.append(f"### {icon} {skill_name}")
        output_lines.append("")
        output_lines.append(f"| Field | Value |")
        output_lines.append(f"|-------|-------|")
        output_lines.append(f"| Verdict | `{r['verdict'].upper()}` |")
        output_lines.append(f"| Reason | {r['verdict_reason']} |")
        output_lines.append(f"| Files | {r['files_scanned']} |")
        output_lines.append(f"| Scripts | {r['scripts']} |")
        output_lines.append(f"| Lines of Code | {r['lines']} |")
        output_lines.append("")
        
        for f in r["findings"]:
            sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "ℹ️"}
            output_lines.append(f"- {sev_icon.get(f.severity, '❓')} **{f.pattern_name}** ({f.severity})")
            output_lines.append(f"  - File: `{f.file_path}` line {f.line_number}")
            output_lines.append(f"  - Code: `{f.line_content}`")
            output_lines.append(f"  - Recommendation: {f.recommendation}")
            output_lines.append("")
    
    # Append files scanned appendix in a separate section
    output_lines.append("---")
    output_lines.append("")
    output_lines.append("## Appendix: All Skills Scanned")
    output_lines.append("")
    
    for skill_name in sorted(all_reports.keys()):
        r = all_reports[skill_name]
        status_icon = {"approved": "✅", "caution": "⚠️", "reject": "🚫"}
        icon = status_icon.get(r["verdict"], "❓")
        fcount = f" ({r['findings_count']} finding{'s' if r['findings_count'] != 1 else ''})" if r['findings_count'] else ""
        output_lines.append(f"- {icon} {skill_name} → {r['verdict'].upper()}{fcount}")
    
    output_lines.append("")
    output_lines.append("---")
    output_lines.append(f"*Report generated automatically by Daily Skill Scanner Audit Cron ({timestamp})*")
    
    report = "\n".join(output_lines)
    
    # Save to file
    report_path = os.path.expanduser(f"~/.openclaw/workspace/exports/skill-audit-{datetime.now().strftime('%Y-%m-%d')}.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        f.write(report)
    
    print(f"REPORT_SAVED:{report_path}")
    print(f"SKILLS_SCANNED:{all_skills_scanned}")
    print(f"FINDINGS:{total_findings}")
    print(f"VERDICTS:{json.dumps(verdict_summary)}")
    
    # For this cron task, also output the report content for email sending
    print("---BEGIN_REPORT---")
    print(report)
    print("---END_REPORT---")

if __name__ == "__main__":
    main()
