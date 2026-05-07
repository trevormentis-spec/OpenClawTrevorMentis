from pathlib import Path
import json

MEMORY_ROOT = Path.home() / '.openclaw' / 'skills' / 'daily_intel' / 'memory'
ASSESSMENTS = Path.home() / '.openclaw' / 'skills' / 'daily_intel' / 'assessments'


def build_index():
    MEMORY_ROOT.mkdir(parents=True, exist_ok=True)
    index = []

    for file in ASSESSMENTS.glob('*.md'):
        text = file.read_text(encoding='utf-8')
        index.append({
            'file': file.name,
            'chars': len(text),
            'preview': text[:500]
        })

    out = MEMORY_ROOT / 'vector_index.json'
    out.write_text(json.dumps(index, indent=2), encoding='utf-8')
    print(f'indexed {len(index)} assessments')


if __name__ == '__main__':
    build_index()
