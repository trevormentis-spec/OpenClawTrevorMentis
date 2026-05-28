#!/usr/bin/env python3
"""
Post-Delivery Quality Validator — checks that delivered brief has substance.

Runs after delivery in the daily brief pipeline. If the brief fails quality
checks, it alerts and attempts auto-fix + re-delivery.

Usage:
    python3 scripts/validate_delivery.py --brief-dir ~/trevor-briefings/2026-05-27
    python3 scripts/validate_delivery.py --brief-dir ~/trevor-briefings/2026-05-27 --fix
"""

import json, pathlib, sys, argparse

MIN_BLUF_WORDS = 50
MIN_KJS = 3
MIN_REGIONS_WITH_CONTENT = 5


def check_brief(brief_dir: pathlib.Path) -> dict:
    """Check the delivered brief for content quality issues."""
    issues = []
    
    exec_path = brief_dir / "analysis" / "exec_summary.json"
    if not exec_path.exists():
        return {"pass": False, "issues": ["exec_summary.json missing"], "fixable": False}
    
    exec_data = json.loads(exec_path.read_text())
    
    # 1. Check BLUF
    es = exec_data.get("executive_summary", {})
    bluf = es.get("bluf", exec_data.get("bluf", ""))
    bluf_words = len(bluf.split())
    if bluf_words < MIN_BLUF_WORDS:
        issues.append(f"BLUF too short: {bluf_words} words (min {MIN_BLUF_WORDS})")
    
    # 2. Check KJs — aggregate from all region files
    all_kjs = []
    for ra in exec_data.get("regional_assessments", []):
        all_kjs.extend(ra.get("key_judgments", []))
    
    if not all_kjs:
        # Fallback: read from region files
        for rf in sorted((brief_dir / "analysis").glob("*.json")):
            if rf.name in ("exec_summary.json", "prediction_markets.json"):
                continue
            try:
                rd = json.loads(rf.read_text())
                all_kjs.extend(rd.get("key_judgments", []))
            except:
                pass
    
    if len(all_kjs) < MIN_KJS:
        issues.append(f"Only {len(all_kjs)} KJs (min {MIN_KJS})")
    
    # 3. Check regions with content
    regions_with = 0
    regions_blackout = []
    for rf in sorted((brief_dir / "analysis").glob("*.json")):
        if rf.name == "exec_summary.json":
            continue
        try:
            rd = json.loads(rf.read_text())
            kjs = rd.get("key_judgments", [])
            narrative = rd.get("narrative", rd.get("summary", ""))
            if kjs and len(narrative) > 50:
                regions_with += 1
            else:
                name = rf.name.replace(".json", "")
                if "prediction" not in name:
                    regions_blackout.append(name)
        except:
            pass
    
    if regions_with < MIN_REGIONS_WITH_CONTENT:
        issues.append(f"Only {regions_with} regions with substantive content (min {MIN_REGIONS_WITH_CONTENT})")
    
    if regions_blackout:
        issues.append(f"Collection blackouts: {', '.join(regions_blackout[:5])}")
    
    # Determine if fixable
    fixable = bluf_words == 0 and len(all_kjs) == 0  # Format issue = fixable
    # Check if it's a format issue (wrong field names)
    has_content_somewhere = bluf_words > 20 or len(all_kjs) > 3 or regions_with >= 3
    if not has_content_somewhere and exec_path.exists():
        fixable = True  # Content exists somewhere but wrong format
    
    return {
        "pass": len(issues) == 0,
        "issues": issues,
        "fixable": fixable,
        "metrics": {
            "bluf_words": bluf_words,
            "total_kjs": len(all_kjs),
            "regions_with_content": regions_with,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Post-Delivery Quality Validator")
    parser.add_argument("--brief-dir", required=True, help="Brief working directory")
    parser.add_argument("--fix", action="store_true", help="Attempt auto-fix if format issue detected")
    args = parser.parse_args()
    
    brief_dir = pathlib.Path(args.brief_dir).expanduser()
    result = check_brief(brief_dir)
    
    if result["pass"]:
        print(f"✅ DELIVERY QUALITY PASS — {result['metrics']['bluf_words']}w BLUF, {result['metrics']['total_kjs']} KJs, {result['metrics']['regions_with_content']} regions")
        return 0
    
    print(f"❌ DELIVERY QUALITY FAIL — {len(result['issues'])} issues")
    for issue in result["issues"]:
        print(f"  → {issue}")
    print(f"  Metrics: {json.dumps(result['metrics'])}")
    
    if result["fixable"] and args.fix:
        print("  🔧 Format issue detected — attempting auto-fix...")
        # Re-deliver using the fixed script
        import subprocess
        env = {"WORKING_DIR": str(brief_dir)}
        r = subprocess.run([
            "python3", str(pathlib.Path(__file__).parent / "skills" / "daily-intel-brief" / "scripts" / "deliver_text_brief.py"),
            "--working-dir", str(brief_dir),
            "--to", "roderick.jones@gmail.com",
            "--from", "trevor_mentis@agentmail.to",
        ], capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            print("  ✅ Re-delivered successfully")
        else:
            print(f"  ❌ Re-delivery failed: {r.stderr[:200]}")
    
    return 1 if not result["pass"] else 0


if __name__ == "__main__":
    sys.exit(main())
