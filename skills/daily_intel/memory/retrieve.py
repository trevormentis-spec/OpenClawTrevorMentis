from pathlib import Path
import json
from difflib import SequenceMatcher

INDEX = Path.home() / '.openclaw' / 'skills' / 'daily_intel' / 'memory' / 'vector_index.json'


def retrieve(query:str, top_k:int=3):
    if not INDEX.exists():
        return []

    data = json.loads(INDEX.read_text())

    scored = []
    for item in data:
        score = SequenceMatcher(None, query.lower(), item['preview'].lower()).ratio()
        scored.append((score, item))

    scored.sort(reverse=True, key=lambda x:x[0])
    return [x[1] for x in scored[:top_k]]


if __name__ == '__main__':
    import sys
    q = ' '.join(sys.argv[1:])
    print(json.dumps(retrieve(q), indent=2))
