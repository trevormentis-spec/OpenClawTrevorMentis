import subprocess
from pathlib import Path

ROOT = Path.home() / '.openclaw' / 'skills' / 'daily_intel'


def run():
    print('== Daily Intel Autonomous Run ==')

    subprocess.run([
        'python3',
        str(ROOT / 'memory' / 'index_memory.py')
    ])

    subprocess.run([
        'python3',
        str(ROOT / 'scripts' / 'build_pdf.py')
    ])

    print('daily run complete')


if __name__ == '__main__':
    run()
