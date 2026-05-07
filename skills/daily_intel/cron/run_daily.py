import os
import subprocess
import sys
from pathlib import Path

# Repo layout: <repo>/skills/daily_intel/cron/run_daily.py
ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]


def run_step(name, cmd, cwd=None):
    print(f'== {name} ==')
    result = subprocess.run(cmd, cwd=cwd or ROOT)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def run():
    print('== Daily Intel Autonomous Run ==')
    print(f'ROOT={ROOT}')

    run_step('Index memory', [sys.executable, str(ROOT / 'memory' / 'index_memory.py')])

    build_pdf = ROOT / 'scripts' / 'build_pdf.py'
    if build_pdf.exists():
        run_step('Build PDF', [sys.executable, str(build_pdf)], cwd=ROOT)
    else:
        print('PDF builder not present yet; skipping build step.')

    print('daily run complete')


if __name__ == '__main__':
    run()
