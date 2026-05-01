import os
import subprocess
import json
from datetime import datetime

SCANNER_PATH = os.path.expanduser("~/.openclaw/skills/skill-scanner/skill_scanner.py")
SKILL_DIRS = [
    os.path.expanduser("~/.openclaw/skills"),
    "/usr/lib/node_modules/openclaw/skills"
]

def run_scan(skill_path):
    try:
        result = subprocess.run(
            ["python3", SCANNER_PATH, "--json", skill_path],
            capture_output=True,
            text=True,
            check=False
        )
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"error": result.stderr or result.stdout, "path": skill_path}
    except Exception as e:
        return {"error": str(e), "path": skill_path}

def main():
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_skills": 0,
        "scanned": [],
        "errors": [],
        "high_risk": [],
        "medium_risk": []
    }

    for base_dir in SKILL_DIRS:
        if not os.path.exists(base_dir):
            continue
        for skill_name in os.listdir(base_dir):
            skill_path = os.path.join(base_dir, skill_name)
            if not os.path.isdir(skill_path):
                continue
            
            report["total_skills"] += 1
            print(f"Scanning {skill_name}...")
            scan_result = run_scan(skill_path)
            
            if "error" in scan_result:
                report["errors"].append(scan_result)
            score = scan_result.get("risk_score", 0)
            if scan_result.get("verdict") == "reject":
                score = max(score, 7)
            
            if score >= 7:
                report["high_risk"].append(skill_name)
            elif score >= 4:
                report["medium_risk"].append(skill_name)
                
            s_data = {
                "name": skill_name,
                "path": skill_path,
                "risk_score": score,
                "findings": scan_result.get("findings", [])
            }
            report["scanned"].append(s_data)

    with open("skill_audit_report.json", "w") as f:
        json.dump(report, f, indent=2)

    # Generate Markdown Summary
    md = f"# Skill Security Audit Report\n\n"
    md += f"- **Date:** {report['timestamp']}\n"
    md += f"- **Total Skills Scanned:** {report['total_skills']}\n"
    md += f"- **High Risk Found:** {len(report['high_risk'])}\n"
    md += f"- **Medium Risk Found:** {len(report['medium_risk'])}\n\n"

    if report["high_risk"]:
        md += "### 🚨 High Risk Skills\n"
        for s in report["high_risk"]:
            md += f"- {s}\n"
        md += "\n"

    if report["medium_risk"]:
        md += "### ⚠️ Medium Risk Skills\n"
        for s in report["medium_risk"]:
            md += f"- {s}\n"
        md += "\n"

    md += "### Detailed Findings (High/Medium Risk)\n"
    for s in report["scanned"]:
        if s["risk_score"] >= 4:
            md += f"#### {s['name']} (Score: {s['risk_score']})\n"
            for f in s["findings"]:
                md += f"- [{f['severity']}] {f['description']}\n"
            md += "\n"

    if report["errors"]:
        md += "### ❌ Scan Errors\n"
        for e in report["errors"]:
            md += f"- {e['path']}: {e['error']}\n"

    with open("skill_audit_report.md", "w") as f:
        f.write(md)

if __name__ == "__main__":
    main()
