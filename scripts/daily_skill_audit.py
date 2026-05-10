#!/usr/bin/env python3
"""
Daily Skill Scanner Audit v2
Scans all installed skills with individual timeouts and skipping oversized/non-skill directories.
"""

import sys
import os
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime, timezone

SCANNER = os.path.expanduser("~/.openclaw/skills/skill-scanner/skill_scanner.py")

SCAN_DIRS = [
    os.path.expanduser("~/.openclaw/skills"),
    "/usr/lib/node_modules/openclaw/skills",
]

# Directories to skip entirely (not real skills)
SKIP_NAMES = {
    "__pycache__", "pyproject.toml",
    "OpenClawTrevorMentis",  # workspace backup, contains recursive skills
}

# Max files to consider a directory a "skill"
MAX_SKILL_FILES = 2000


def get_skill_directories(base_dir):
    """List legitimate skill directories."""
    skills = []
    base = Path(base_dir)
    if not base.exists():
        return skills
    for entry in sorted(base.iterdir()):
        if entry.name in SKIP_NAMES:
            continue
        if not entry.is_dir() and not entry.is_symlink():
            continue
        # Count files - skip massive dirs that aren't real skills
        file_count = 0
        try:
            file_count = len(list(entry.rglob("*")))
        except (PermissionError, OSError):
            pass
        if file_count > MAX_SKILL_FILES:
            print(f"  ⏭️  Skipping {entry.name} ({file_count} files - too large for a skill)")
            continue
        skills.append(entry)
    return skills


def scan_skill(skill_path):
    """Scan a single skill via CLI subprocess with timeout."""
    try:
        result = subprocess.run(
            ["python3", SCANNER, str(skill_path), "--json"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode in (0, 1, 2) and result.stdout.strip():
            return json.loads(result.stdout)
        return None
    except subprocess.TimeoutExpired:
        print(f"  ⏰ Timeout scanning {skill_path.name}")
        return None
    except json.JSONDecodeError:
        return None
    except Exception as e:
        return None


def categorize(verdict):
    if verdict == "reject":
        return "🔴 CRITICAL"
    elif verdict == "caution":
        return "🟡 CAUTION"
    else:
        return "🟢 APPROVED"


def main():
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"🔒 Daily Skill Scanner Audit - {timestamp}")
    print("="*60)

    all_reports = []
    total_critical = 0
    total_high = 0
    total_findings = 0
    reject_skills = []
    caution_skills = []
    approved_skills = []
    scan_errors = []
    scanned_names = set()

    for scan_dir in SCAN_DIRS:
        skills = get_skill_directories(scan_dir)
        source_label = "user" if "openclaw" in scan_dir and "node_modules" not in scan_dir else "system"
        label_map = {"user": "~/.openclaw/skills", "system": "/usr/lib/..."}
        
        print(f"\n📁 Scanning {label_map[source_label]} ({len(skills)} skills)...")
        
        for skill_path in skills:
            if skill_path.name in scanned_names:
                print(f"  ⏩ Skipping {skill_path.name} (already scanned)")
                continue
            scanned_names.add(skill_path.name)
            
            print(f"  🔍 Scanning: {skill_path.name}...", end=" ")
            sys.stdout.flush()
            
            report = scan_skill(skill_path)
            if report is None:
                scan_errors.append(f"{skill_path.name} ({source_label})")
                print("❌ Error")
                continue
            
            all_reports.append(report)
            findings = report.get("findings", [])
            total_findings += len(findings)
            critical_count = sum(1 for f in findings if f.get("severity") == "critical")
            high_count = sum(1 for f in findings if f.get("severity") == "high")
            total_critical += critical_count
            total_high += high_count
            
            verdict = report.get("verdict", "approved")
            skill_name = report.get("metadata", {}).get("name") or skill_path.name
            skill_label = f"{skill_name} ({source_label})"
            
            if verdict == "reject":
                reject_skills.append((skill_label, report.get("verdict_reason", "")))
                print(f"🔴 REJECT ({critical_count} critical)")
            elif verdict == "caution":
                caution_skills.append((skill_label, report.get("verdict_reason", ""), high_count))
                print(f"🟡 CAUTION ({high_count} high)")
            else:
                approved_skills.append(skill_label)
                print("✅ Clean")

    # Build report
    report_lines = [
        f"# 🔒 Daily Skill Scanner Audit Report",
        f"",
        f"**Generated:** {timestamp}",
        f"**Environment:** OpenClaw | **Scanner:** skill-scanner v1.0",
        f"",
        f"## Executive Summary",
        f"",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Total Skills Scanned | {len(all_reports)} |",
        f"| ✅ Approved (clean) | {len(approved_skills)} |",
        f"| 🟡 Caution (high-severity) | {len(caution_skills)} |",
        f"| 🔴 Critical (rejected) | {len(reject_skills)} |",
        f"| Total Findings | {total_findings} |",
        f"| ⬆️ Critical Severity | {total_critical} |",
        f"| ⬆️ High Severity | {total_high} |",
        f"| ❌ Scan Errors | {len(scan_errors)} |",
        f"",
    ]

    if scan_errors:
        report_lines.extend([
            f"---",
            f"## ⚠️ Skills That Failed to Scan ({len(scan_errors)})",
            f"",
        ])
        for err in scan_errors:
            report_lines.append(f"- `{err}`")
        report_lines.append("")

    if reject_skills:
        report_lines.extend([
            f"---",
            f"## 🔴 CRITICAL - Requires Immediate Review",
            f"",
        ])
        for skill, reason in reject_skills:
            report_lines.extend([
                f"### {skill}",
                f"**Reason:** {reason}",
                f"",
            ])

    if caution_skills:
        report_lines.extend([
            f"---",
            f"## 🟡 CAUTION - High-Severity Issues Detected",
            f"",
        ])
        for skill, reason, count in caution_skills:
            report_lines.extend([
                f"### {skill}",
                f"**Reason:** {reason}",
                f"",
            ])

    if approved_skills:
        report_lines.extend([
            f"---",
            f"## ✅ Approved - No Issues ({len(approved_skills)})",
            f"",
        ])
        for s in sorted(approved_skills):
            report_lines.append(f"- {s}")
        report_lines.append("")

    # Detailed findings table
    report_lines.extend([
        f"---",
        f"## 📋 Detailed Findings Per Skill",
        f"",
    ])
    
    for report in all_reports:
        meta = report.get("metadata", {})
        skill_name = meta.get("name") or Path(report.get("skill_path", "")).name
        findings = report.get("findings", [])
        
        report_lines.extend([
            f"### {skill_name}",
            f"**Verdict:** {categorize(report.get('verdict', 'approved'))}",
        ])
        
        if findings:
            report_lines.extend([
                f"| # | Pattern | Severity | File | Line |",
                f"|---|---------|----------|------|------|",
            ])
            for i, f in enumerate(findings, 1):
                report_lines.append(
                    f"| {i} | {f.get('pattern_name','?')} | "
                    f"{f.get('severity','?')} | `{f.get('file_path','?')}` | "
                    f"{f.get('line_number','?')} |"
                )
            report_lines.append("")
        else:
            report_lines.append("No security issues detected.")
            report_lines.append("")

    # Footer
    report_lines.extend([
        f"---",
        f"*Report auto-generated by Daily Skill Scanner Audit cron job.*",
        f"*Scanner location: `~/.openclaw/skills/skill-scanner/skill_scanner.py`*",
        f"*Report saved to `exports/skill-audit-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md`*",
    ])

    full_report = "\n".join(report_lines)

    # Save report
    exports_dir = Path(os.path.expanduser("~/.openclaw/workspace/exports"))
    exports_dir.mkdir(parents=True, exist_ok=True)
    
    report_path = exports_dir / f"skill-audit-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
    report_path.write_text(full_report)
    
    print(f"\n{'='*60}")
    print(f"✅ Audit complete!")
    print(f"   Scanned: {len(all_reports)} skills")
    print(f"   Approved: {len(approved_skills)} | Caution: {len(caution_skills)} | Critical: {len(reject_skills)}")
    print(f"   Total findings: {total_findings} ({total_critical} critical, {total_high} high)")
    print(f"   Report: {report_path}")

    return {
        "report_text": full_report,
        "report_path": str(report_path),
        "summary": {
            "total_scanned": len(all_reports),
            "approved": len(approved_skills),
            "caution": len(caution_skills),
            "rejected": len(reject_skills),
            "critical_findings": total_critical,
            "high_findings": total_high,
            "total_findings": total_findings,
            "errors": len(scan_errors),
        },
        "timestamp": timestamp,
    }


if __name__ == "__main__":
    result = main()
    summary_path = os.path.expanduser("~/.openclaw/workspace/exports/skill-audit-summary.json")
    with open(summary_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Summary: {summary_path}")
