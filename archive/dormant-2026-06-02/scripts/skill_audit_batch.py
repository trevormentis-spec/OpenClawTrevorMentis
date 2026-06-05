#!/usr/bin/env python3
"""
Batch skill scanner audit — runs skill_scanner.py on all installed skills
and produces a consolidated summary report.
"""

import subprocess
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Paths
SKILL_SCANNER = os.path.expanduser("~/.openclaw/skills/skill-scanner/skill_scanner.py")
HOME_SKILLS = os.path.expanduser("~/.openclaw/skills")
SYS_SKILLS = "/usr/lib/node_modules/openclaw/skills"
OUTPUT_DIR = os.path.expanduser("~/.openclaw/workspace/exports/skill-audit")
SUMMARY_FILE = os.path.join(OUTPUT_DIR, f"skill-audit-summary-{datetime.now().strftime('%Y-%m-%d')}.md")

# Skills to skip (the scanner itself)
SKIP_DIRS = {"skill-scanner", ".git", "__pycache__", "node_modules"}

os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_skill_dirs(base_path):
    if not os.path.isdir(base_path):
        return []
    return sorted([
        os.path.join(base_path, d) for d in os.listdir(base_path)
        if os.path.isdir(os.path.join(base_path, d)) and d not in SKIP_DIRS
    ])

def scan_skill(skill_path):
    """Run the skill scanner on a single skill directory, return JSON output."""
    skill_name = os.path.basename(skill_path)
    try:
        result = subprocess.run(
            [sys.executable, SKILL_SCANNER, skill_path, "--json"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode in (0, 1, 2) and result.stdout:
            return json.loads(result.stdout)
        else:
            return {
                "skill_path": skill_path,
                "verdict": "error",
                "verdict_reason": f"Scanner stderr: {result.stderr[:500]}" if result.stderr else "No output",
                "metadata": {"name": skill_name, "file_count": 0, "script_count": 0, "total_lines": 0},
                "findings": []
            }
    except subprocess.TimeoutExpired:
        return {
            "skill_path": skill_path,
            "verdict": "error",
            "verdict_reason": "Scanner timed out (>60s)",
            "metadata": {"name": skill_name, "file_count": 0, "script_count": 0, "total_lines": 0},
            "findings": []
        }
    except json.JSONDecodeError:
        return {
            "skill_path": skill_path,
            "verdict": "error",
            "verdict_reason": "Failed to parse scanner JSON output",
            "metadata": {"name": skill_name, "file_count": 0, "script_count": 0, "total_lines": 0},
            "findings": []
        }

def severity_score(sev):
    return {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}.get(sev, 0)

def generate_summary(all_reports):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    # Categorize
    rejected = [r for r in all_reports if r["verdict"] == "reject"]
    caution = [r for r in all_reports if r["verdict"] == "caution"]
    approved = [r for r in all_reports if r["verdict"] == "approved"]
    errors = [r for r in all_reports if r["verdict"] == "error"]
    
    # Aggregate findings
    all_findings = []
    for r in all_reports:
        for f in r.get("findings", []):
            f["skill_name"] = r["metadata"].get("name", os.path.basename(r["skill_path"]))
            all_findings.append(f)
    
    # Sort findings by severity
    all_findings.sort(key=lambda x: severity_score(x.get("severity", "info")), reverse=True)
    
    # Stats
    total_skills = len(all_reports)
    total_files = sum(r["metadata"].get("file_count", 0) for r in all_reports)
    total_lines = sum(r["metadata"].get("total_lines", 0) for r in all_reports)
    
    # Build markdown
    lines = [
        f"# 🔒 Daily Skill Security Audit — {now}",
        "",
        f"**Total skills scanned:** {total_skills}",
        f"**Total files reviewed:** {total_files}",
        f"**Total lines of code:** {total_lines}",
        f"**Total findings:** {len(all_findings)}",
        "",
        "---",
        "",
        "## 🏆 Verdict Summary",
        "",
        f"| Category | Count |",
        f"|----------|-------|",
        f"| ✅ Approved | {len(approved)} |",
        f"| ⚠️ Caution | {len(caution)} |",
        f"| ❌ Rejected | {len(rejected)} |",
        f"| ❓ Error | {len(errors)} |",
        "",
    ]
    
    if errors:
        lines.extend([
            "### ❓ Errors (Scan Failed)",
            "",
        ])
        for r in errors:
            name = r["metadata"].get("name", os.path.basename(r["skill_path"]))
            lines.append(f"- **{name}:** {r.get('verdict_reason', 'Unknown error')}")
        lines.append("")
    
    if rejected:
        lines.extend([
            "### ❌ Rejected Skills (Critical Issues)",
            "",
        ])
        for r in rejected:
            name = r["metadata"].get("name", os.path.basename(r["skill_path"]))
            path = r["skill_path"]
            crit = [f for f in r["findings"] if f["severity"] == "critical"]
            lines.append(f"- **{name}** (`{path}`)")
            lines.append(f"  - Reason: {r['verdict_reason']}")
            for c in crit:
                lines.append(f"  - `{c['pattern_name']}` in `{c['file_path']}` line {c['line_number']}: {c['line_content'][:120]}")
            lines.append("")
    
    if caution:
        lines.extend([
            "### ⚠️ Caution Skills (High-Severity Issues)",
            "",
        ])
        for r in caution:
            name = r["metadata"].get("name", os.path.basename(r["skill_path"]))
            path = r["skill_path"]
            high = [f for f in r["findings"] if f["severity"] == "high"]
            lines.append(f"- **{name}** (`{path}`)")
            lines.append(f"  - Reason: {r['verdict_reason']}")
            for h in high:
                lines.append(f"  - `{h['pattern_name']}` in `{h['file_path']}` line {h['line_number']}")
            lines.append("")
    
    if all_findings:
        lines.extend([
            "## 📋 All Findings (By Severity)",
            "",
            "| # | Skill | Pattern | Severity | File | Line |",
            "|---|-------|---------|----------|------|------|",
        ])
        for i, f in enumerate(all_findings, 1):
            sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "🔵"}.get(f["severity"], "⚪")
            skill = f.get("skill_name", "?")
            lines.append(f"| {i} | {skill} | {f['pattern_name']} | {sev_icon} {f['severity']} | `{f['file_path']}` | {f['line_number']} |")
    
    lines.extend([
        "",
        "---",
        "",
        "## ✅ Approved Skills",
        "",
    ])
    for r in approved:
        name = r["metadata"].get("name", os.path.basename(r["skill_path"]))
        path = r["skill_path"]
        fc = r["metadata"].get("file_count", 0)
        sc = r["metadata"].get("script_count", 0)
        lines.append(f"- **{name}** ({fc} files, {sc} scripts) — `{path}`")
    
    lines.append("")
    lines.append("---")
    lines.append(f"*Report generated by Daily Skill Scanner Audit cron — {now}*")
    
    return "\n".join(lines)

def main():
    print("=" * 60)
    print("🔒 DAILY SKILL SECURITY AUDIT")
    print("=" * 60)
    
    all_skill_dirs = get_skill_dirs(HOME_SKILLS) + get_skill_dirs(SYS_SKILLS)
    print(f"\nFound {len(all_skill_dirs)} skill directories to scan.")
    
    # Deduplicate (sys skills may shadow home skills, but both dirs are legit)
    seen = set()
    unique_dirs = []
    for d in all_skill_dirs:
        resolved = os.path.realpath(d)
        if resolved not in seen:
            seen.add(resolved)
            unique_dirs.append(d)
    
    print(f"Scanning {len(unique_dirs)} unique skill directories...\n")
    
    all_reports = []
    for i, skill_dir in enumerate(unique_dirs, 1):
        skill_name = os.path.basename(skill_dir)
        print(f"  [{i}/{len(unique_dirs)}] Scanning: {skill_name} ...", end=" ", flush=True)
        report = scan_skill(skill_dir)
        all_reports.append(report)
        
        # Print outcome
        verdict = report["verdict"]
        findings_count = len(report.get("findings", []))
        if verdict == "error":
            print(f"❌ ERROR ({report.get('verdict_reason', '?')})")
        elif verdict == "reject":
            print(f"❌ REJECT ({findings_count} findings)")
        elif verdict == "caution":
            print(f"⚠️  CAUTION ({findings_count} findings)")
        else:
            print(f"✅ approved")
    
    print(f"\n{'=' * 60}")
    print("Generating summary report...")
    
    summary = generate_summary(all_reports)
    
    with open(SUMMARY_FILE, "w") as f:
        f.write(summary)
    
    print(f"Summary written to: {SUMMARY_FILE}")
    print(f"Total: {len(all_reports)} skills | Findings: {sum(len(r.get('findings', [])) for r in all_reports)}")
    print(f"Rejected: {sum(1 for r in all_reports if r['verdict'] == 'reject')} | Caution: {sum(1 for r in all_reports if r['verdict'] == 'caution')} | Approved: {sum(1 for r in all_reports if r['verdict'] == 'approved')} | Errors: {sum(1 for r in all_reports if r['verdict'] == 'error')}")
    print("=" * 60)
    
    return SUMMARY_FILE

if __name__ == "__main__":
    summary_path = main()
    print(f"\nSummary file path: {summary_path}")
