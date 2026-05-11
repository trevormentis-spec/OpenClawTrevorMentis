#!/usr/bin/env python3
"""Quality audit + continuous improvement system for the daily intel pipeline.

Checks all outputs, logs issues, attempts auto-fixes, and maintains
an improvement log so the pipeline gets better over time.

Usage:
  python3 quality_audit.py              # full audit + report
  python3 quality_audit.py --auto-fix   # attempt fixes for known issues
  python3 quality_audit.py --fix-list   # show known fixable issues
"""
import os, sys, json, datetime, hashlib
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = SKILL_ROOT / 'images'
MAPS_DIR = SKILL_ROOT / 'maps'
INFO_DIR = SKILL_ROOT / 'infographics'
SCRIPTS_DIR = SKILL_ROOT / 'scripts'
EXPORTS_DIR = Path.home() / '.openclaw' / 'workspace' / 'exports' / 'pdfs'

IMPROVEMENT_LOG = SKILL_ROOT / 'cron_tracking' / 'improvement_log.json'
STATE_FILE = SKILL_ROOT / 'cron_tracking' / 'state.json'

from trevor_config import THEATRE_KEYS as THEATRES

# ═══════════════════════════════════════════════════════════
# QUALITY THRESHOLDS
# ═══════════════════════════════════════════════════════════

THRESHOLDS = {
    "photo": {
        "min_kb": 50,
        "ideal_kb": 100,
        "min_width": 1500,
        "min_height": 1000,
        "ideal_width": 2000,
    },
    "map": {
        "min_kb": 25,
        "ideal_kb": 60,
        "min_width": 800,
        "min_height": 500,
        "ideal_width": 1200,
    },
    "infographic": {
        "min_kb": 15,
        "ideal_kb": 25,
        "min_width": 800,
        "min_height": 500,
        "ideal_width": 1200,
    },
    "pdf": {
        "min_kb": 500,
        "min_pages": 20,
        "max_pages": 50,
        "min_images": 18,
    },
}


# ═══════════════════════════════════════════════════════════
# AUDIT FUNCTIONS
# ═══════════════════════════════════════════════════════════

def audit_image(path, category, date_str):
    """Audit a single image and return (score, issues)."""
    issues = []
    score = 0
    
    if not path.exists():
        issues.append("MISSING")
        return 0, issues
    
    size_kb = os.path.getsize(path) // 1024
    try:
        from PIL import Image
        img = Image.open(path)
        w, h = img.size
    except Exception as e:
        issues.append(f"CORRUPT: {e}")
        return 10, issues

    t = THRESHOLDS.get(category, {})
    
    # Size check
    if size_kb < t.get("min_kb", 10):
        issues.append(f"TOO_SMALL({size_kb}KB < {t['min_kb']}KB)")
    elif size_kb >= t.get("ideal_kb", 100):
        score += 3
        issues.append(f"GOOD_SIZE({size_kb}KB)")
    else:
        score += 1
        issues.append(f"ADEQUATE({size_kb}KB)")
    
    # Resolution check
    if w < t.get("min_width", 800):
        issues.append(f"LOW_RES({w}x{h})")
    elif w >= t.get("ideal_width", 2000):
        score += 2
    else:
        score += 1
    
    # Name check — file name should contain date
    if date_str in path.name:
        score += 1
    else:
        issues.append(f"STALE_DATE(has {path.name.split('_')[0]})")
    
    return score, issues


def audit_pdf(date_str):
    """Audit the final PDF."""
    issues = []
    score = 0
    
    pdf_paths = sorted(EXPORTS_DIR.glob(f"*{date_str}*.pdf"))
    if not pdf_paths:
        pdf_paths = sorted(SKILL_ROOT.glob(f"security_brief_{date_str}.pdf"))
    if not pdf_paths:
        pdf_paths = sorted(SKILL_ROOT.glob(f"security_brief_*.pdf"))
    
    if not pdf_paths:
        return 0, ["PDF_MISSING"]
    
    pdf_path = pdf_paths[-1]
    size_kb = os.path.getsize(pdf_path) // 1024
    
    if size_kb < THRESHOLDS["pdf"]["min_kb"]:
        issues.append(f"PDF_TOO_SMALL({size_kb}KB)")
    else:
        score += 2
        issues.append(f"PDF_SIZE({size_kb}KB)")
    
    # Count embedded images
    try:
        import subprocess
        result = subprocess.run(['pdfimages', '-list', str(pdf_path)],
                               capture_output=True, text=True, timeout=10)
        img_count = len([l for l in result.stdout.split('\n') if l.strip()]) - 2
        if img_count >= THRESHOLDS["pdf"]["min_images"]:
            score += 2
            issues.append(f"IMAGES({img_count})")
        else:
            issues.append(f"FEW_IMAGES({img_count})")
    except:
        issues.append("PDF_CHECK_FAILED")
    
    return score, issues


def run_audit(date_str=None):
    """Run full audit on all outputs."""
    if date_str is None:
        date_str = datetime.date.today().isoformat()
    
    results = {
        "date": date_str,
        "timestamp": datetime.datetime.now().isoformat(),
        "theatres": {},
        "pdf": {},
        "overall_score": 0,
        "total_issues": 0,
    }
    
    for theatre_idx, theatre in enumerate(THEATRES, 1):
        scores = {"photo": 0, "map": 0, "infographic": 0}
        issues = {"photo": [], "map": [], "infographic": []}
        
        for category, directory in [
            ("photo", IMAGES_DIR), ("map", MAPS_DIR), ("infographic", INFO_DIR)
        ]:
            if category == "photo":
                path = directory / f"{date_str}_{theatre}.jpg"
            else:
                path = directory / f"{theatre_idx:02d}_{theatre}.png"
            
            s, iss = audit_image(path, category, date_str)
            scores[category] = s
            issues[category] = iss
        
        theatre_score = sum(scores.values())
        theatre_issues = sum(len(v) for v in issues.values())
        
        results["theatres"][theatre] = {
            "score": theatre_score,
            "issues": theatre_issues,
            "details": issues,
        }
        results["overall_score"] += theatre_score
        results["total_issues"] += theatre_issues
    
    # PDF audit
    pdf_score, pdf_issues = audit_pdf(date_str)
    results["pdf"] = {"score": pdf_score, "issues": pdf_issues}
    results["overall_score"] += pdf_score
    results["total_issues"] += len(pdf_issues) if isinstance(pdf_issues, list) else 1
    
    return results


# ═══════════════════════════════════════════════════════════
# IMPROVEMENT TRACKING
# ═══════════════════════════════════════════════════════════

def load_improvement_log():
    """Load the improvement tracking log."""
    if IMPROVEMENT_LOG.exists():
        return json.loads(IMPROVEMENT_LOG.read_text())
    return {
        "first_run": datetime.datetime.now().isoformat(),
        "runs": [],
        "fix_history": {},
        "known_failures": {},
        "score_trend": [],
    }


def save_improvement_log(log):
    """Save the improvement tracking log."""
    IMPROVEMENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    IMPROVEMENT_LOG.write_text(json.dumps(log, indent=2))


def update_trend(results, log):
    """Record audit results in the improvement trend."""
    entry = {
        "date": results["date"],
        "score": results["overall_score"],
        "issues": results["total_issues"],
        "pdf_score": results["pdf"]["score"],
    }
    log["runs"].append(entry)
    log["score_trend"].append({
        "date": results["date"],
        "score": results["overall_score"],
    })
    save_improvement_log(log)


# ═══════════════════════════════════════════════════════════
# REPORTING
# ═══════════════════════════════════════════════════════════

def print_report(results):
    """Print human-readable quality report."""
    date = results["date"]
    print(f"\n{'='*60}")
    print(f"QUALITY AUDIT  —  {date}")
    print(f"{'='*60}")
    
    print(f"\n{'Theatre':<18} {'Photo':<18} {'Map':<18} {'Info':<18} {'Score':<8}")
    print(f"{'-'*18} {'-'*18} {'-'*18} {'-'*18} {'-'*8}")
    
    for theatre in THEATRES:
        t = results["theatres"][theatre]
        p_issues = t["details"]["photo"]
        m_issues = t["details"]["map"]
        i_issues = t["details"]["infographic"]
        
        p_str = p_issues[0][:16] if p_issues else "OK"
        m_str = m_issues[0][:16] if m_issues else "OK"
        i_str = i_issues[0][:16] if i_issues else "OK"
        
        print(f"{theatre:<18} {p_str:<18} {m_str:<18} {i_str:<18} {t['score']:<8}")
    
    # PDF
    pdf_issues = results["pdf"].get("issues", [])
    pdf_str = pdf_issues[0][:16] if pdf_issues else "OK"
    print(f"\nPDF: {pdf_str}  |  Score: {results['pdf']['score']}")
    
    # Summary — count only REAL problems (not status strings like GOOD_SIZE)
    real_issues = 0
    for theatre in THEATRES:
        for cat in ["photo", "map", "infographic"]:
            for iss in results["theatres"][theatre]["details"][cat]:
                if any(iss.startswith(p) for p in ["MISSING", "TOO_SMALL", "LOW_RES", "CORRUPT", "STALE_DATE", "PDF_"]):
                    real_issues += 1
    real_issues += len(results["pdf"].get("issues", []))
    
    total = results["overall_score"]
    grade = "A" if real_issues == 0 else "B" if real_issues <= 2 else "C" if real_issues <= 5 else "D"
    
    print(f"\n{'='*60}")
    print(f"OVERALL: {total} pts  |  {real_issues} real issues  |  Grade: {grade}")
    print(f"{'='*60}\n")
    
    return grade


# ═══════════════════════════════════════════════════════════
# AUTO-FIX FUNCTIONS
# ═══════════════════════════════════════════════════════════

def known_fixable_issues(log):
    """Return list of issues that have known automatic fixes."""
    fixes = []
    
    # Check if any known failures from previous runs
    for issue_type, count in log.get("known_failures", {}).items():
        if "WIKIMEDIA_DOWNLOAD" in issue_type:
            fixes.append("Retry Wikimedia downloads with alternative search terms")
        if "KALSHI_SCAN" in issue_type:
            fixes.append("Re-run Kalshi scanner")
        if "FONT_MISSING" in issue_type:
            fixes.append("Install missing fonts from system alternatives")
    
    # Check if state.json indicates a failed partial run
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
        if state.get("quality_issues", 0) > 0:
            fixes.append(f"Previous run had {state['quality_issues']} issues — re-run pipeline")
    
    return fixes


def auto_fix(log):
    """Attempt automatic fixes for known issues."""
    from importlib import import_module
    
    fixes_applied = 0
    print("\n=== Auto-Fix ===")
    
    # Re-read state for issues
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
        issues = state.get("quality_issues", 0)
        if issues > 0:
            print(f"  Previous run had {issues} issues — re-running pipeline...")
            
            # Run the pipeline
            refresh_script = SCRIPTS_DIR / 'refresh_imagery.py'
            build_script = SCRIPTS_DIR / 'build_pdf.py'
            
            if refresh_script.exists():
                import subprocess
                print("  Running refresh_imagery...")
                result = subprocess.run(['python3', str(refresh_script)],
                                       capture_output=True, text=True, timeout=180)
                if result.returncode == 0:
                    print("  ✓ Refresh succeeded")
                    fixes_applied += 1
                else:
                    print(f"  ✗ Refresh failed: {result.stderr[-200:]}")
            
            if build_script.exists():
                print("  Running build_pdf...")
                result = subprocess.run(['python3', str(build_script)],
                                       capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    print("  ✓ Build succeeded")
                    fixes_applied += 1
                else:
                    print(f"  ✗ Build failed: {result.stderr[-200:]}")
    
    if fixes_applied:
        print(f"  {fixes_applied} fixes applied\n")
    else:
        print("  No fixes needed\n")
    
    return fixes_applied


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Quality audit for intel pipeline")
    parser.add_argument('--date', help='Date to audit (YYYY-MM-DD, default: today)')
    parser.add_argument('--auto-fix', action='store_true', help='Attempt auto-fixes')
    parser.add_argument('--fix-list', action='store_true', help='Show fixable issues')
    parser.add_argument('--trend', action='store_true', help='Show improvement trend')
    args = parser.parse_args()
    
    date_str = args.date or datetime.date.today().isoformat()
    log = load_improvement_log()
    
    if args.fix_list:
        fixes = known_fixable_issues(log)
        if fixes:
            print("\nKnown fixable issues:")
            for f in fixes:
                print(f"  • {f}")
        else:
            print("\nNo known fixable issues.")
        return
    
    if args.auto_fix:
        fixes = auto_fix(log)
        # Re-audit after fixes
        results = run_audit(date_str)
        print_report(results)
        update_trend(results, log)
        return
    
    if args.trend:
        print(f"\nScore trend ({len(log['score_trend'])} runs):")
        for entry in log['score_trend']:
            marker = "✓" if entry['score'] >= 15 else "⚠"
            print(f"  {entry['date']}: {entry['score']} pts {marker}")
        return
    
    # Default: full audit
    results = run_audit(date_str)
    grade = print_report(results)
    update_trend(results, log)
    
    # If issues found, suggest auto-fix
    if results["total_issues"] > 0:
        print(f"Tip: Run with --auto-fix to attempt automatic fixes\n")


if __name__ == "__main__":
    main()
