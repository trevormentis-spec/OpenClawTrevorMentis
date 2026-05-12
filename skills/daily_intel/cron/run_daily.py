#!/usr/bin/env python3
"""Autonomous daily execution for the Daily Intel pipeline.

Full pipeline:
  1. Generate fresh assessments (DeepSeek V4 Pro)
  2. Refresh imagery (NASA/fallback)
  3. Index memory (Chroma)
  4. Build PDF
  5. Save state
  6. Report completion

Heartbeat every 30s during long tasks. Logs everything.
"""
import os, sys, json, time, datetime, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Load environment from workspace .env (cron may not have it in env)
from trevor_config import WORKSPACE
WORKSPACE_ENV = WORKSPACE / '.env'
if WORKSPACE_ENV.exists():
    for line in WORKSPACE_ENV.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, _, v = line.partition('=')
            os.environ.setdefault(k.strip(), v.strip())

HEARTBEAT = ROOT / 'cron_tracking' / 'heartbeat.json'
STATE = ROOT / 'cron_tracking' / 'state.json'
LOG = ROOT / 'cron_tracking' / 'run.log'
ISSUE_TRACKER = ROOT / 'cron_tracking' / 'issue_number.txt'

os.makedirs(ROOT / 'cron_tracking', exist_ok=True)


def log(msg):
    ts = datetime.datetime.now().isoformat()
    entry = f"[{ts}] {msg}"
    print(entry, flush=True)
    with open(LOG, 'a') as f:
        f.write(entry + '\n')


def heartbeat(step, status, progress=None):
    hb = {
        "timestamp": datetime.datetime.now().isoformat(),
        "step": step,
        "status": status,
        "progress": progress,
        "pid": os.getpid(),
    }
    HEARTBEAT.write_text(json.dumps(hb, indent=2))
    log(f"HB: {step} = {status}" + (f" ({progress})" if progress else ""))


def get_next_issue():
    """Read and increment the issue counter."""
    curr = 1
    if ISSUE_TRACKER.exists():
        curr = int(ISSUE_TRACKER.read_text().strip()) + 1
    ISSUE_TRACKER.write_text(str(curr))
    return f"{curr:02d}"


def run_step(name, cmd, cwd=None, timeout=600):
    log(f"START: {name}")
    heartbeat(name, "running")
    
    cwd = cwd or ROOT
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    
    start = time.time()
    while True:
        try:
            proc.wait(timeout=30)
            break
        except subprocess.TimeoutExpired:
            elapsed = int(time.time() - start)
            heartbeat(name, "running", f"pid={proc.pid} elapsed={elapsed}s")
            if elapsed > timeout:
                proc.kill()
                log(f"TIMEOUT: {name} exceeded {timeout}s")
                heartbeat(name, "timeout")
                return False
    
    output = proc.stdout.read() if proc.stdout else ""
    if proc.returncode != 0:
        log(f"FAIL: {name} (rc={proc.returncode})")
        log(output[:2000])
        heartbeat(name, "failed", f"rc={proc.returncode}")
        return False
    
    log(f"DONE: {name}")
    heartbeat(name, "complete")
    return True


def generate_output_filename():
    date_str = datetime.date.today().isoformat()
    return f"security_brief_{date_str}.pdf"


def run():
    log("=" * 60)
    log("DAILY INTEL AUTONOMOUS RUN")
    log(f"ROOT={ROOT}")
    
    heartbeat("pipeline", "starting")
    issue = get_next_issue()
    log(f"Issue #{issue}")
    
    # Step 1: Generate fresh assessments
    gen_script = ROOT / 'scripts' / 'generate_assessments.py'
    if gen_script.exists():
        run_step("Generate assessments", [sys.executable, str(gen_script)])
    
    # Step 2: Refresh imagery
    img_script = ROOT / 'scripts' / 'refresh_imagery.py'
    if img_script.exists():
        run_step("Refresh imagery", [sys.executable, str(img_script)])
    
    # Step 3: Index memory
    run_step("Index memory", [sys.executable, str(ROOT / 'memory' / 'index_memory.py')])
    
    # Step 4: Build PDF
    build_pdf = ROOT / 'scripts' / 'build_pdf.py'
    if not build_pdf.exists():
        log("ERROR: build_pdf.py missing")
        heartbeat("pipeline", "failed", "missing build_pdf.py")
        sys.exit(1)
    
    pdf_ok = run_step("Build PDF", [sys.executable, str(build_pdf)], cwd=ROOT)
    
    # Step 5: Verify and update state
    pdf_path = ROOT / generate_output_filename()
    if pdf_path.exists():
        size = pdf_path.stat().st_size
        log(f"PDF: {pdf_path.name} ({size:,} bytes)")
    else:
        pdfs = sorted(ROOT.glob("security_brief_*.pdf"))
        if pdfs:
            pdf_path = pdfs[-1]
            log(f"PDF: {pdf_path.name}")
    
    # Update state.json
    state = {
        "issue_number": issue,
        "last_run": datetime.datetime.now().isoformat(),
        "completed": pdf_path.exists(),
        "pdf_path": str(pdf_path),
        "pdf_size_bytes": pdf_path.stat().st_size if pdf_path.exists() else 0,
        "generated": True,
    }
    STATE.write_text(json.dumps(state, indent=2))
    
    # Step 6: Email PDF to Roderick via Gmail
    if pdf_path.exists():
        maton_key = os.environ.get("MATON_API_KEY", "")
        if maton_key:
            run_step("Email PDF", [sys.executable, str(ROOT / 'scripts' / '_email_brief.py'), str(pdf_path), issue])
        else:
            log("WARN: MATON_API_KEY not set — skipping email")
    
    # Step 7: Post to Moltbook
    if pdf_path.exists():
        moltbook_script = Path(os.environ.get("WORKSPACE", str(Path.home() / '.openclaw' / 'workspace'))) / 'scripts' / 'moltbook-post-brief.sh'
        if moltbook_script.exists() and os.environ.get("MOLTBOOK_API_KEY", ""):
            run_step("Moltbook post", ["bash", str(moltbook_script), "--pdf", str(pdf_path)])
    
    # Step 8: Post to GenViral socials
    if pdf_path.exists():
        genviral_script = Path(os.environ.get("WORKSPACE", str(Path.home() / '.openclaw' / 'workspace'))) / 'scripts' / 'genviral-post-brief.sh'
        if genviral_script.exists() and os.environ.get("GENVIRAL_API_KEY", ""):
            run_step("GenViral socials", ["bash", str(genviral_script), "--pdf", str(pdf_path)])
    
    status = "complete" if state["completed"] else "failed"
    progress = f"pdf={pdf_path.name}" if state["completed"] else "no output"
    heartbeat("pipeline", status, progress)
    
    log("DAILY INTEL RUN COMPLETE")
    log("=" * 60)


if __name__ == "__main__":
    run()

    # Step 9: Deploy landing page
    deploy_script = Path.home() / '.openclaw' / 'workspace' / 'scripts' / 'deploy_landing_page.sh'
    if deploy_script.exists():
        run_step("Deploy landing page", ["bash", str(deploy_script)], timeout=120)
