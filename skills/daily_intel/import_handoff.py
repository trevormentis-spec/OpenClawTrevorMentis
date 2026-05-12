from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent

ASSESSMENTS = {
    'africa.md', 'asia.md', 'europe.md', 'global_finance.md',
    'middle_east.md', 'north_america.md', 'south_america.md'
}
SCRIPTS = {
    'build_pdf.py', 'build_maps.py', 'build_infographics.py', 'build_infographics_v2.py'
}
CRON = {'STANDING_RULES.md', 'state.json'}
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp'}


def copy_file(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f'copied {src.name} -> {dst.relative_to(ROOT)}')


def import_handoff(handoff_dir: Path):
    if not handoff_dir.exists():
        raise SystemExit(f'handoff folder not found: {handoff_dir}')

    for src in handoff_dir.rglob('*'):
        if not src.is_file():
            continue
        name = src.name
        suffix = src.suffix.lower()

        if name in ASSESSMENTS:
            copy_file(src, ROOT / 'assessments' / name)
        elif name in SCRIPTS:
            copy_file(src, ROOT / 'scripts' / name)
        elif name in CRON:
            copy_file(src, ROOT / 'cron_tracking' / name)
        elif suffix in IMAGE_EXTS:
            copy_file(src, ROOT / 'images' / name)
        elif name.lower() == 'readme.md':
            copy_file(src, ROOT / 'REPLICATION_BUNDLE.md')

    print('handoff import complete')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python import_handoff.py /path/to/handoff_folder')
    import_handoff(Path(sys.argv[1]).expanduser().resolve())
