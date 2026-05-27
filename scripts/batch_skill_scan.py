#!/usr/bin/env python3
"""
Batch skill scanner - scans all skill directories and produces a consolidated report.
"""
import sys
import os
sys.path.insert(0, os.path.expanduser('~/.openclaw/skills/skill-scanner'))

from skill_scanner import SkillScanner, format_markdown
from pathlib import Path
from datetime import datetime
import json

SKILL_ROOTS = [
    os.path.expanduser('~/.openclaw/skills'),
    '/usr/lib/node_modules/openclaw/skills',
    os.path.expanduser('~/.openclaw/workspace/skills'),
]

SKIP_DIRS = {'.git', '__pycache__', 'node_modules', '.venv', 'venv'}

def is_skill_dir(path: Path) -> bool:
    """A skill directory has a SKILL.md or python/js files."""
    if not path.is_dir():
        return False
    if path.name.startswith('.'):
        return False
    if path.name in SKIP_DIRS:
        return False
    # Must contain at least one relevant file
    has_md = (path / 'SKILL.md').exists()
    has_py = any(path.rglob('*.py'))
    has_js = any(path.rglob('*.js'))
    has_sh = any(path.rglob('*.sh'))
    has_ts = any(path.rglob('*.ts'))
    return has_md or has_py or has_js or has_sh or has_ts

def main():
    all_skills = []
    errors = []
    
    for root in SKILL_ROOTS:
        root_path = Path(root)
        if not root_path.exists():
            continue
        
        for item in sorted(root_path.iterdir()):
            if item.name.startswith('.'):
                continue
            if item.name in SKIP_DIRS:
                continue
            if not item.is_dir():
                # registry.json etc — skip
                continue
                
            # Skip skill-scanner itself (we're using it)
            if item.name == 'skill-scanner':
                continue
            
            print(f"Scanning: {item.name} ...", end=' ', flush=True)
            try:
                scanner = SkillScanner(str(item))
                report = scanner.scan()
                all_skills.append(report)
                print(f"✅ verdict={report.verdict} issues={len(report.findings)}")
            except Exception as e:
                errors.append((str(item), str(e)))
                print(f"❌ ERROR: {e}")
    
    # Generate consolidated report
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    summary_lines = [
        "# Consolidated Skill Security Audit Report",
        "",
        f"**Generated:** {timestamp}",
        f"**Skills Scanned:** {len(all_skills)}",
        f"**Errors:** {len(errors)}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
    ]
    
    verdicts = {}
    for r in all_skills:
        v = r.verdict
        verdicts[v] = verdicts.get(v, 0) + 1
    
    summary_lines.extend([
        f"- **APPROVED:** {verdicts.get('approved', 0)} skills",
        f"- **CAUTION:** {verdicts.get('caution', 0)} skills",
        f"- **REJECTED:** {verdicts.get('reject', 0)} skills",
        "",
    ])
    
    # Critical and high findings across all skills
    all_critical = []
    all_high = []
    all_medium = []
    
    for r in all_skills:
        for f in r.findings:
            entry = {
                'skill': r.metadata.name or Path(r.skill_path).name,
                'path': r.skill_path,
                'pattern': f.pattern_name,
                'severity': f.severity,
                'file': f.file_path,
                'line': f.line_number,
                'description': f.description,
            }
            if f.severity == 'critical':
                all_critical.append(entry)
            elif f.severity == 'high':
                all_high.append(entry)
            elif f.severity == 'medium':
                all_medium.append(entry)
    
    # Section: Critical Findings
    summary_lines.extend([
        "## 🔴 Critical Findings",
        "",
    ])
    if all_critical:
        summary_lines.append(f"**{len(all_critical)} critical issue(s) found**")
        summary_lines.append("")
        for f in all_critical:
            summary_lines.extend([
                f"- **[{f['skill']}]** `{f['pattern']}` in `{f['file']}:{f['line']}`",
                f"  - {f['description']}",
                "",
            ])
    else:
        summary_lines.append("None detected. ✅")
        summary_lines.append("")
    
    # Section: High Findings
    summary_lines.extend([
        "## 🟠 High Severity Findings",
        "",
    ])
    if all_high:
        summary_lines.append(f"**{len(all_high)} high-severity issue(s) found**")
        summary_lines.append("")
        for f in all_high:
            summary_lines.extend([
                f"- **[{f['skill']}]** `{f['pattern']}` in `{f['file']}:{f['line']}`",
                f"  - {f['description']}",
                "",
            ])
    else:
        summary_lines.append("None detected. ✅")
        summary_lines.append("")
    
    # Section: Medium Findings
    summary_lines.extend([
        "## 🟡 Medium Severity Findings",
        "",
    ])
    if all_medium:
        summary_lines.append(f"**{len(all_medium)} medium-severity issue(s) found**")
        summary_lines.append("")
        for f in all_medium:
            summary_lines.extend([
                f"- **[{f['skill']}]** `{f['pattern']}` in `{f['file']}:{f['line']}`",
                f"  - {f['description']}",
                "",
            ])
    else:
        summary_lines.append("None detected. ✅")
        summary_lines.append("")
    
    # Section: Error skills
    if errors:
        summary_lines.extend([
            "## ⚠️ Scan Errors",
            "",
        ])
        for name, err in errors:
            summary_lines.append(f"- **{name}**: {err}")
        summary_lines.append("")
    
    # Full per-skill reports
    summary_lines.append("---")
    summary_lines.append("")
    summary_lines.append("## Detailed Per-Skill Reports")
    summary_lines.append("")
    
    for r in all_skills:
        ver = r.verdict
        if ver == 'reject':
            badge = "🔴 REJECT"
        elif ver == 'caution':
            badge = "🟠 CAUTION"
        else:
            badge = "🟢 APPROVED"
        
        skill_name = r.metadata.name or Path(r.skill_path).name
        summary_lines.append(f"### {badge} - {skill_name}")
        summary_lines.append("")
        summary_lines.append(f"**Path:** `{r.skill_path}`")
        summary_lines.append(f"**Verdict:** {r.verdict.upper()} - {r.verdict_reason}")
        summary_lines.append(f"**Files:** {r.metadata.file_count} | **Scripts:** {r.metadata.script_count} | **Lines:** {r.metadata.total_lines}")
        summary_lines.append("")
        
        if r.findings:
            for f in r.findings:
                summary_lines.extend([
                    f"- `{f.pattern_name}` ({f.severity}) | `{f.file_path}` line {f.line_number}",
                    f"  - {f.description}",
                    f"  - *Recommendation:* {f.recommendation}",
                    "",
                ])
        else:
            summary_lines.append("No issues found.")
            summary_lines.append("")
    
    report = '\n'.join(summary_lines)
    
    # Save to file
    report_path = os.path.expanduser('~/.openclaw/workspace/exports/skill-security-audit.md')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    Path(report_path).write_text(report)
    
    print(f"\n✅ Report saved to: {report_path}")
    print(f"Skills scanned: {len(all_skills)}, Errors: {len(errors)}")
    print(f"Verdicts: {json.dumps(verdicts)}")
    print(f"Critical findings: {len(all_critical)}")
    print(f"High findings: {len(all_high)}")
    print(f"Medium findings: {len(all_medium)}")
    
    return report_path

if __name__ == '__main__':
    main()
