# brain/

Trevor's file-backed memory runtime. Plain text and a small Python script —
no external dependencies, no databases, no vector services.

## Layout

```
brain/
├── working-memory.json        # current task scratch; ephemeral
├── memory/
│   ├── episodic/              # what happened — JSONL by day
│   ├── semantic/              # stable facts — markdown
│   └── procedural/            # how to do recurring things — markdown
├── meta/
│   ├── corrections.jsonl      # user-flagged corrections, append-only
│   ├── retrieval-signals.jsonl # was a retrieved chunk useful?
│   └── promotions.jsonl       # episodic → semantic promotions
├── index/
│   └── index.json             # built from memory/ + repo docs
└── scripts/
    └── brain.py               # the runtime
```

## Why a file-backed brain?

Three reasons:

1. **Inspectable.** Roderick can `cat` any file and see what Trevor knows.
2. **Versioned.** Every memory move is a git commit; corrections and
   promotions are auditable.
3. **Resilient.** No service to fail. A corrupted index is rebuilt with
   `brain.py reindex` in seconds.

## Usage

| Command                                  | What it does                              |
|------------------------------------------|-------------------------------------------|
| `python3 brain/scripts/brain.py recall "<q>"`     | Fast path: top-3 relevant chunks   |
| `python3 brain/scripts/brain.py synthesize "<q>"` | Slow path: recommend files to read |
| `python3 brain/scripts/brain.py reindex`          | Rebuild index from memory + repo docs |
| `python3 brain/scripts/brain.py status`           | Show what's indexed                |
| `python3 brain/scripts/brain.py store-episodic "<text>"` | Log a daily event              |
| `python3 brain/scripts/brain.py store-semantic <topic> "<text>"` | Save a stable fact     |
| `python3 brain/scripts/brain.py store-procedural <slug> "<text>"` | Save a how-to        |
| `python3 brain/scripts/brain.py mark-retrieval <key> <useful\|not-useful>` | Log retrieval signal |
| `python3 brain/scripts/brain.py record-correction "<text>"` | Log a correction        |
| `python3 brain/scripts/brain.py promote <key>`    | Episodic → semantic promotion      |

## Promotion: episodic → semantic

When the same fact shows up usefully across three or more days, promote it
from `memory/episodic/` to `brain/memory/semantic/<topic>.md`. That's how
working knowledge becomes durable knowledge. Promotions are logged in
`meta/promotions.jsonl` so we can roll them back if they were premature.

## Discipline

- Don't read source files in the fast path (`recall`). Trust the index.
- Don't auto-promote without a retrieval-signal log. Promotion is opt-in.
- Don't index secrets. The indexer skips `.env`, `*.key`, `*.pem`,
  anything under `**/credentials/`, and any file matching .gitignore.
