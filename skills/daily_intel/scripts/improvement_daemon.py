#!/usr/bin/env python3
"""improvement_daemon.py — Master cron process for the daily intel pipeline.

Orchestrates the full daily improvement cycle across all domains:

  DATA SOURCES   → daily_enrichment.py (freshness checks, gap detection)
  PROCESS        → build pipeline (assess, image, map, infographic, PDF)
  QUALITY        → quality_audit.py + briefometer.py + story_tracker.py
  MARKETING      → distribution to social, email, landing page
  SALES          → usage tracking, Stripe monitoring
  IMPROVEMENT    → auto-fix loop, trend tracking, weekly reports

Usage:
  python3 improvement_daemon.py --daily        # Full daily pipeline
  python3 improvement_daemon.py --hourly       # Light hourly checks (KJs, markets)
  python3 improvement_daemon.py --weekly       # Weekly analytics report
  python3 improvement_daemon.py --status       # Show pipeline health
  python3 improvement_daemon.py --auto-fix     # Fix known issues

Cron schedule (as of 2026-05-07):
  Daily: 12:00 UTC (before brief generation)
  Daily: 16:00 UTC (after brief build — distribution)
  Hourly: market check for significant moves
  Weekly: Sunday full analytics
"""
import os, sys, json, datetime, subprocess, logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from trevor_config import WORKSPACE, EXPORTS_DIR, THEATRES, THEATRE_KEYS, HEARTBEAT_INTERVAL_SECONDS
from trevor_log import get_logger

log = get_logger("improvement_daemon")

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_ROOT / 'scripts'
CRON_DIR = SKILL_ROOT / 'cron_tracking'
IMAGES_DIR = SKILL_ROOT / 'images'
MAPS_DIR = SKILL_ROOT / 'maps'
INFO_DIR = SKILL_ROOT / 'infographics'
ASSESS_DIR = SKILL_ROOT / 'assessments'

RUN_LOG = CRON_DIR / 'daemon_run.log'
STATE_FILE = CRON_DIR / 'state.json'

KALSHI_SCANNER = WORKSPACE / 'scripts' / 'kalshi_scanner.py'


def run_script(name, args=None, timeout=300):
    """Run a pipeline script and capture output."""
    script = SCRIPTS_DIR / name
    if not script.exists():
        log(f"✗ {name} not found")
        return False, "NOT_FOUND"

    cmd = ['python3', str(script)]
    if args:
        cmd.extend(args)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            log(f"✓ {name} {' '.join(args) if args else ''}")
            return True, result.stdout[-500:]
        else:
            log(f"✗ {name} failed (rc={result.returncode})")
            log(f"  {result.stderr[-300:]}")
            return False, result.stderr[-300:]
    except subprocess.TimeoutExpired:
        log(f"✗ {name} timed out ({timeout}s)")
        return False, "TIMEOUT"
    except Exception as e:
        log(f"✗ {name} error: {e}")
        return False, str(e)


# ─── PIPELINE STEPS ──────────────────────────────────────

def step_quality_audit():
    """Quality audit + auto-fix loop."""
    log("┌─ Quality Audit")
    ok, msg = run_script('quality_audit.py', timeout=60)
    if not ok:
        log("  Attempting auto-fix...")
        run_script('quality_audit.py', ['--auto-fix'], timeout=180)
    # Briefometer measurement
    run_script('briefometer.py', timeout=30)
    return ok


def step_story_tracker_save():
    """Save today's story state."""
    log("┌─ Story Tracker Save")
    return run_script('story_tracker.py', ['--save'], timeout=15)


def step_story_tracker_diff():
    """Diff yesterday vs today."""
    log("┌─ Story Tracker Diff")
    return run_script('story_tracker.py', ['--diff'], timeout=15)


def step_enrichment():
    """Run pre-assessment enrichment."""
    log("┌─ Daily Enrichment")
    return run_script('daily_enrichment.py', timeout=60)


def step_build_pdf():
    """Build the final PDF."""
    log("┌─ Build PDF")
    ok, msg = run_script('build_pdf.py', timeout=180)
    if ok:
        # Get file info
        pdfs = sorted(SKILL_ROOT.glob("security_brief_*.pdf"))
        if pdfs:
            latest = pdfs[-1]
            size_kb = os.path.getsize(latest) // 1024
            log(f"  PDF: {latest.name} ({size_kb}KB)")
    return ok, msg


def step_refresh_imagery():
    """Regenerate images, maps, infographics."""
    log("┌─ Refresh Imagery")
    return run_script('refresh_imagery.py', timeout=300)


def step_assessments():
    """Generate theatre assessments."""
    log("┌─ Generate Assessments")
    return run_script('generate_assessments.py', timeout=300)


def step_kalshi_scan():
    """Scan prediction markets."""
    log("┌─ Kalshi Scan")
    # Try skill scripts dir first, fall back to workspace scripts
    script = SCRIPTS_DIR / 'kalshi_scanner.py'
    if not script.exists():
        ws_script = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / 'workspace' / 'scripts' / 'kalshi_scanner.py'
        if ws_script.exists():
            cmd = ['python3', str(ws_script), '--save']
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    log(f"✓ kalshi_scanner.py --save (workspace)")
                    return True, result.stdout[-500:]
                else:
                    log(f"✗ kalshi_scanner.py failed (rc={result.returncode})")
                    return False, result.stderr[-300:]
            except subprocess.TimeoutExpired:
                log(f"✗ kalshi_scanner.py timed out (60s)")
                return False, "TIMEOUT"
        log(f"✗ kalshi_scanner.py not found in skill or workspace scripts")
        return False, "NOT_FOUND"
    return run_script('kalshi_scanner.py', ['--save'], timeout=60)


# ─── DISTRIBUTION ────────────────────────────────────────

def step_distribution():
    """Distribute the finished brief to channels.

    Current channels:
    - Exports/pdfs (always)
    - Moltbook (if available)
    - GitHub Pages (if available)
    - Email (if configured)
    """
    log("┌─ Distribution")

    # Find latest PDF
    pdfs = sorted(SKILL_ROOT.glob("security_brief_*.pdf"))
    if not pdfs:
        log("  No PDF to distribute")
        return False, "NO_PDF"

    latest_pdf = pdfs[-1]
    exports_dir = WORKSPACE / 'exports' / 'pdfs'
    exports_dir.mkdir(parents=True, exist_ok=True)

    # Copy to exports
    os.system(f"cp '{latest_pdf}' '{exports_dir}/{latest_pdf.name}'")
    log(f"  ✓ Copied to exports/pdfs/")

    # Try landing page deploy
    deploy_script = WORKSPACE / 'scripts' / 'deploy_landing_page.sh'
    if deploy_script.exists():
        log("  Attempting landing page deploy...")
        try:
            result = subprocess.run(['bash', str(deploy_script)],
                                   capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                log("  ✓ Landing page deployed")
            else:
                log(f"  Landing page deploy: {result.stderr[-200:]}")
        except:
            log("  Landing page deploy skipped (timeout or error)")

    # Try Moltbook posting
    moltbook_script = WORKSPACE / 'scripts' / 'moltbook-post-brief.sh'
    if moltbook_script.exists():
        log("  Attempting Moltbook post...")
        try:
            result = subprocess.run(['bash', str(moltbook_script), '--gmail'],
                                   capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                log("  ✓ Moltbook posted")
            else:
                log(f"  Moltbook: {result.stderr[-200:]}")
        except:
            log("  Moltbook skipped")

    return True, "OK"


# ─── SELF-CHECK: PIPELINE HEALTH ─────────────────────────

def check_pipeline_health():
    """Check if the pipeline is healthy and fixable."""
    issues = []

    # Check assessment files
    for theatre in THEATRES:
        ass = ASSESS_DIR / f"{theatre}.md"
        if not ass.exists():
            issues.append(f"MISSING_ASSESSMENT:{theatre}")
        elif os.path.getsize(ass) < 500:
            issues.append(f"EMPTY_ASSESSMENT:{theatre}")

    # Check image directories
    for d, name in [(IMAGES_DIR, "images"), (MAPS_DIR, "maps"), (INFO_DIR, "infographics")]:
        files = list(d.glob("*"))
        if len(files) < 3:
            issues.append(f"EMPTY_DIR:{name}")

    # Check PDF
    pdfs = sorted(SKILL_ROOT.glob("security_brief_*.pdf"))
    if not pdfs:
        issues.append("NO_PDF")

    # Check disk space
    stat = os.statvfs(str(SKILL_ROOT))
    free_mb = stat.f_bavail * stat.f_frsize / 1024 / 1024
    if free_mb < 100:
        issues.append(f"LOW_DISK:{free_mb:.0f}MB_free")

    return issues


def auto_recover(issues):
    """Attempt automatic recovery for known issues."""
    fixed = 0
    for issue in issues:
        if issue.startswith("MISSING_ASSESSMENT:"):
            theatre = issue.split(":")[1]
            log(f"  Creating placeholder for {theatre}")
            (ASSESS_DIR / f"{theatre}.md").write_text(
                f"# {theatre.title()} Assessment\n\nAssessment pending.\n")
            fixed += 1

        elif issue == "NO_PDF":
            log("  No PDF found — attempting rebuild")
            step_build_pdf()
            fixed += 1

        elif issue.startswith("EMPTY_DIR:"):
            log(f"  Empty directory: {issue.split(':')[1]} — running imagery")
            step_refresh_imagery()
            fixed += 1

    return fixed


# ─── DAILY IMPROVEMENT REPORT ────────────────────────────

def generate_improvement_report():
    """Generate a structured improvement report for trend tracking."""
    date_str = datetime.date.today().isoformat()

    report = {
        "date": date_str,
        "pipeline_success": True,
        "metrics": {},
        "issues": [],
        "improvements": [],
    }

    # Load measurement data
    meas_log = CRON_DIR / 'measurement_log.json'
    if meas_log.exists():
        data = json.loads(meas_log.read_text())
        if data.get("runs"):
            latest = data["runs"][-1]
            report["metrics"] = latest

    # Load story tracker
    tracker_file = CRON_DIR / 'story_tracker.json'
    if tracker_file.exists():
        tracker = json.loads(tracker_file.read_text())
        latest = tracker.get("latest", {})
        report["story_state"] = {
            "total_words": latest.get("summary", {}).get("total_words", 0),
            "total_sources": latest.get("summary", {}).get("total_sources", 0),
            "theatres": list(latest.get("theatres", {}).keys()),
        }

    # Load enrichment
    enrichment_file = CRON_DIR / 'enrichment_report.json'
    if enrichment_file.exists():
        enrichment = json.loads(enrichment_file.read_text())
        report["stale_stories"] = enrichment.get("recommendations", {}).get("shake_up_stories", [])

    # Pipeline health
    health_issues = check_pipeline_health()
    report["issues"] = health_issues

    return report


# ─── STATUS DASHBOARD ────────────────────────────────────

def show_status():
    """Show pipeline health status."""
    print("\n" + "=" * 60)
    print("  ⚙ IMPROVEMENT DAEMON — Pipeline Status")
    print("=" * 60)

    issues = check_pipeline_health()

    print(f"\n  Pipeline Health:")
    print(f"  {'─' * 50}")
    for theatre in THEATRES:
        ass = ASSESS_DIR / f"{theatre}.md"
        ass_ok = "✓" if ass.exists() and os.path.getsize(ass) > 500 else "✗"
        img_count = len(list(IMAGES_DIR.glob(f"*{theatre}*")))
        map_count = len(list(MAPS_DIR.glob(f"*{theatre}*")))
        info_count = len(list(INFO_DIR.glob(f"*{theatre}*")))
        print(f"  {ass_ok} {theatre:<16} img={img_count} map={map_count} info={info_count}")

    pdfs = sorted(SKILL_ROOT.glob("security_brief_*.pdf"))
    pdf_status = f"✓ {pdfs[-1].name} ({os.path.getsize(pdfs[-1])//1024}KB)" if pdfs else "✗ None"
    print(f"\n  PDF: {pdf_status}")

    # Recent run log
    if RUN_LOG.exists():
        lines = RUN_LOG.read_text().strip().split('\n')[-5:]
        print(f"\n  Recent activity:")
        for line in lines:
            print(f"  {line}")

    if issues:
        print(f"\n  ⚠ Issues ({len(issues)}):")
        for i in issues:
            print(f"    • {i}")
        print(f"\n  Run --auto-fix to attempt recovery")
    else:
        print(f"\n  ✓ No issues")

    print("=" * 60 + "\n")


# ─── PIPELINE RUNNERS ──────────────────────────────────

def run_daily():
    """Full daily pipeline — the main daily improvement cycle."""
    date_str = datetime.date.today().isoformat()
    log(f"\n{'='*60}")
    log(f"IMPROVEMENT DAEMON — Daily Run: {date_str}")
    log(f"{'='*60}")

    success = True

    # Phase 1: Enrichment (pre-assessment)
    log("\n── Phase 1: Intelligence Enrichment ──")
    step_story_tracker_diff()
    step_enrichment()
    step_kalshi_scan()

    # Phase 2: Generation
    log("\n── Phase 2: Content Generation ──")
    ok, _ = step_assessments()
    if not ok:
        log("  Assessments failed — continuing with fallback")
        success = False

    ok, _ = step_refresh_imagery()
    if not ok:
        log("  Imagery failed — attempting recovery")
        quality_auto_fix()
        success = False

    ok, _ = step_build_pdf()
    if not ok:
        log("  PDF build failed — will retry")
        success = False

    # Phase 3: Quality & Measurement
    log("\n── Phase 3: Quality & Measurement ──")
    step_quality_audit()
    step_story_tracker_save()

    # Phase 4: Distribution
    log("\n── Phase 4: Distribution ──")
    if ok:
        step_distribution()
    else:
        log("  Skipping distribution — PDF build failed")

    # Phase 5: Improvement report
    log("\n── Phase 5: Improvement Report ──")
    report = generate_improvement_report()
    report["pipeline_success"] = success
    report_path = CRON_DIR / f"daily_report_{date_str}.json"
    report_path.write_text(json.dumps(report, indent=2))
    log(f"  Report: {report_path.name}")

    if success:
        log(f"\n✅ Daily pipeline complete: {date_str}")
    else:
        log(f"\n⚠ Daily pipeline completed with issues: {date_str}")

    return success


def run_hourly():
    """Lightweight hourly checks — market moves, KJ tracking."""
    log("\n── Hourly Check ──")

    # Check Kalshi for significant moves
    script = SCRIPTS_DIR / 'kalshi_scanner.py'
    if script.exists():
        run_script('kalshi_scanner.py', ['--save'], timeout=60)

    # Check enrichment recommendations for alerts
    enr = CRON_DIR / 'enrichment_report.json'
    if enr.exists():
        data = json.loads(enr.read_text())
        markets = data.get("prediction_markets", {})
        sig_moves = markets.get("significant_moves", [])
        if sig_moves:
            # Only alert on big moves (>15pp)
            big_moves = [m for m in sig_moves if m.get("change", 0) >= 15]
            if big_moves:
                for m in big_moves[:3]:
                    log(f"  ⚡ Big market move: {m['market']} ({m['change']}pp)")

    log("  Hourly check complete")


def run_weekly():
    """Weekly analytics — trends, calibration, source diversity."""
    log("\n── Weekly Analytics ──")

    # Trend analysis from measurement_log
    meas_log = CRON_DIR / 'measurement_log.json'
    if meas_log.exists():
        data = json.loads(meas_log.read_text())
        runs = data.get("runs", [])
        if len(runs) >= 2:
            visual_trend = [r.get("visual", 0) for r in runs]
            content_trend = [r.get("content", 0) for r in runs]
            log(f"  Visual trend: {visual_trend[0]} → {visual_trend[-1]} ({visual_trend[-1] - visual_trend[0]:+d})")
            log(f"  Content trend: {content_trend[0]} → {content_trend[-1]} ({content_trend[-1] - content_trend[0]:+d})")

    # Story tracker trend
    tracker_file = CRON_DIR / 'story_tracker.json'
    if tracker_file.exists():
        tracker = json.loads(tracker_file.read_text())
        history = tracker.get("history", [])
        if len(history) >= 2:
            log(f"  Story history: {len(history)} days tracked")
            for h in history:
                words = h.get("summary", {}).get("total_words", 0)
                log(f"    {h['date']}: {words} words")

    # KJ calibration
    kj_file = CRON_DIR / 'key_judgments.json'
    if kj_file.exists():
        kjs = json.loads(kj_file.read_text())
        verdicts = [j for j in kjs.get("judgments", []) if j["outcome"] is not None]
        log(f"  KJs verified: {len(verdicts)}")
        if verdicts and kjs.get("mean_brier"):
            log(f"  Mean Brier: {kjs['mean_brier']}")

    log("  Weekly analytics complete")


def quality_auto_fix():
    """Auto-fix common quality issues."""
    log("  Quality auto-fix running...")
    run_script('quality_audit.py', ['--auto-fix'], timeout=120)


# ─── MAIN ────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Improvement Daemon — pipeline orchestration")
    parser.add_argument('--daily', action='store_true', help='Full daily pipeline')
    parser.add_argument('--hourly', action='store_true', help='Hourly checks')
    parser.add_argument('--weekly', action='store_true', help='Weekly analytics')
    parser.add_argument('--status', action='store_true', help='Show pipeline health')
    parser.add_argument('--auto-fix', action='store_true', help='Fix known issues')
    args = parser.parse_args()

    if args.daily:
        run_daily()
    elif args.hourly:
        run_hourly()
    elif args.weekly:
        run_weekly()
    elif args.status:
        show_status()
    elif args.auto_fix:
        issues = check_pipeline_health()
        fixed = auto_recover(issues)
        log(f"Auto-fix: {fixed} issues resolved")
    else:
        print("Usage: improvement_daemon.py --daily|--hourly|--weekly|--status|--auto-fix")
        print()
        print("  --daily    Full daily pipeline (enrichment → generate → measure → distribute)")
        print("  --hourly   Market checks and alerts")
        print("  --weekly   Trend analysis and calibration report")
        print("  --status   Show pipeline health dashboard")
        print("  --auto-fix Attempt automatic recovery of known issues")


if __name__ == "__main__":
    main()
