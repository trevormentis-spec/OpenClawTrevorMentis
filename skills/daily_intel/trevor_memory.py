#!/usr/bin/env python3
"""
trevor_memory.py — Lightweight memory system for Trevor using FTS5.

Replaces Chroma + sentence-transformers (1.8GB dependency stack) with
sqlite3 FTS5 full-text search. Incremental indexing, portable, fast.

Usage:
    from trevor_memory import MemoryStore
    mem = MemoryStore()
    mem.index("europe", "narrative text here")
    results = mem.search("Ukraine ceasefire")
    mem.prune(keep_last=30)  # keep only 30 most recent entries
    mem.export_snapshot("/tmp/memory-backup.json")
"""
from __future__ import annotations

import datetime
import json
import os
import sqlite3
import uuid
from pathlib import Path


_SKILL_ROOT = Path(__file__).resolve().parent
_MEMORY_DIR = _SKILL_ROOT / "memory"
_DB_PATH = _MEMORY_DIR / "trevor_memory.db"


class MemoryStore:
    """Lightweight memory with FTS5 full-text search.
    
    Collections:
      - narrative: theatre narratives and key judgments
      - procedural: skills and workflows
      - execution: pipeline runs and errors
      - source: source reliability tracking
      - trade_thesis: prediction market theses
    """

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path or _DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        """Create tables and FTS5 virtual tables if they don't exist."""
        c = self._conn.cursor()
        
        # Main content table
        c.execute("""
            CREATE TABLE IF NOT EXISTS memory_entries (
                id TEXT PRIMARY KEY,
                collection TEXT NOT NULL,
                key TEXT,
                content TEXT NOT NULL,
                source TEXT,
                region TEXT,
                confidence REAL,
                created_at TEXT NOT NULL,
                metadata TEXT DEFAULT '{}'
            )
        """)
        
        # FTS5 full-text search index
        c.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                content,
                collection UNINDEXED,
                region UNINDEXED,
                key UNINDEXED,
                content='memory_entries',
                content_rowid='rowid'
            )
        """)
        
        # Triggers to keep FTS in sync
        for trigger_name, trigger_sql in [
            ("memory_ai", "CREATE TRIGGER IF NOT EXISTS memory_ai AFTER INSERT ON memory_entries BEGIN INSERT INTO memory_fts(rowid, content, collection, region, key) VALUES (new.rowid, new.content, new.collection, new.region, new.key); END;"),
            ("memory_ad", "CREATE TRIGGER IF NOT EXISTS memory_ad AFTER DELETE ON memory_entries BEGIN INSERT INTO memory_fts(memory_fts, rowid, content, collection, region, key) VALUES('delete', old.rowid, old.content, old.collection, old.region, old.key); END;"),
            ("memory_au", "CREATE TRIGGER IF NOT EXISTS memory_au AFTER UPDATE ON memory_entries BEGIN INSERT INTO memory_fts(memory_fts, rowid, content, collection, region, key) VALUES('delete', old.rowid, old.content, old.collection, old.region, old.key); INSERT INTO memory_fts(rowid, content, collection, region, key) VALUES (new.rowid, new.content, new.collection, new.region, new.key); END;"),
        ]:
            c.execute(trigger_sql)
        
        # Indexes
        c.execute("CREATE INDEX IF NOT EXISTS idx_collection ON memory_entries(collection)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_region ON memory_entries(region)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_created ON memory_entries(created_at)")
        
        self._conn.commit()

    def index(self, collection: str, content: str, key: str = "",
              source: str = "", region: str = "", confidence: float = 0.0,
              metadata: dict | None = None) -> str:
        """Index a piece of content. Returns entry ID."""
        entry_id = str(uuid.uuid4())[:12]
        now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        self._conn.execute(
            "INSERT INTO memory_entries (id, collection, key, content, source, region, confidence, created_at, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (entry_id, collection, key[:100], content, source, region, confidence, now, json.dumps(metadata or {}))
        )
        self._conn.commit()
        return entry_id

    def search(self, query: str, collection: str | None = None,
               region: str | None = None, top_k: int = 5, min_confidence: float = 0.0) -> list[dict]:
        """Full-text search with optional filters. Returns ranked results."""
        where = "WHERE memory_fts MATCH ?"
        params = [query]
        
        if collection:
            where += " AND me.collection = ?"
            params.append(collection)
        if region:
            where += " AND me.region = ?"
            params.append(region)
        
        where += " AND me.confidence >= ?"
        params.append(min_confidence)
        
        try:
            c = self._conn.execute(f"""
                SELECT me.id, me.collection, me.key, me.content, me.source,
                       me.region, me.confidence, me.created_at,
                       rank as relevance
                FROM memory_fts
                JOIN memory_entries me ON memory_fts.rowid = me.rowid
                {where}
                ORDER BY rank
                LIMIT ?
            """, params + [top_k])
        except sqlite3.OperationalError:
            # FTS5 syntax error in query — fall back to LIKE
            c = self._conn.execute(f"""
                SELECT me.id, me.collection, me.key, me.content, me.source,
                       me.region, me.confidence, me.created_at, 0.0 as relevance
                FROM memory_entries me
                WHERE me.content LIKE ?
                {('AND me.collection = ?' if collection else '')}
                {('AND me.region = ?' if region else '')}
                ORDER BY me.created_at DESC
                LIMIT ?
            """, ['%' + query + '%'] + ([collection] if collection else []) + ([region] if region else []) + [top_k])
        
        return [dict(row) for row in c.fetchall()]

    def get_recent(self, collection: str, limit: int = 10) -> list[dict]:
        """Get most recent entries in a collection."""
        c = self._conn.execute(
            "SELECT * FROM memory_entries WHERE collection = ? ORDER BY created_at DESC LIMIT ?",
            (collection, limit)
        )
        return [dict(row) for row in c.fetchall()]

    def get_previous_narrative(self, region: str, days: int = 7) -> str | None:
        """Get the most recent narrative for a region within the time window."""
        cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        c = self._conn.execute(
            "SELECT content FROM memory_entries WHERE collection = 'narrative' AND region = ? AND created_at >= ? ORDER BY created_at DESC LIMIT 1",
            (region, cutoff)
        )
        row = c.fetchone()
        return row["content"] if row else None

    def get_prior_judgment(self, region: str, topic: str = "") -> list[dict]:
        """Get previous key judgments for a region."""
        c = self._conn.execute(
            "SELECT * FROM memory_entries WHERE collection = 'narrative' AND region = ? AND (key LIKE '%judgment%' OR key LIKE '%KJ%') ORDER BY created_at DESC LIMIT 5",
            (region,)
        )
        return [dict(row) for row in c.fetchall()]

    def count(self, collection: str | None = None) -> int:
        """Count entries, optionally filtered by collection."""
        if collection:
            c = self._conn.execute("SELECT COUNT(*) as cnt FROM memory_entries WHERE collection = ?", (collection,))
        else:
            c = self._conn.execute("SELECT COUNT(*) as cnt FROM memory_entries")
        return c.fetchone()["cnt"]

    def prune(self, collection: str, keep_last: int = 30) -> int:
        """Remove oldest entries beyond keep_last. Returns number deleted."""
        c = self._conn.execute("""
            DELETE FROM memory_entries WHERE rowid IN (
                SELECT rowid FROM memory_entries 
                WHERE collection = ? 
                ORDER BY created_at DESC 
                LIMIT -1 OFFSET ?
            )
        """, (collection, keep_last))
        deleted = self._conn.total_changes
        self._conn.commit()
        return deleted

    def export_snapshot(self, path: str | Path) -> int:
        """Export all memory to a portable JSON snapshot. Returns entry count."""
        c = self._conn.execute("SELECT * FROM memory_entries ORDER BY created_at")
        entries = [dict(row) for row in c.fetchall()]
        snapshot = {
            "exported_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "version": "1.0",
            "entry_count": len(entries),
            "entries": entries,
        }
        Path(path).write_text(json.dumps(snapshot, indent=2))
        return len(entries)

    def import_snapshot(self, path: str | Path) -> int:
        """Import from a portable JSON snapshot. Returns entries imported."""
        data = json.loads(Path(path).read_text())
        count = 0
        for entry in data.get("entries", []):
            self._conn.execute(
                "INSERT OR IGNORE INTO memory_entries (id, collection, key, content, source, region, confidence, created_at, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (entry["id"], entry["collection"], entry.get("key", ""), entry["content"],
                 entry.get("source", ""), entry.get("region", ""), entry.get("confidence", 0.0),
                 entry.get("created_at", datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")),
                 entry.get("metadata", "{}"))
            )
            count += 1
        self._conn.commit()
        return count

    def close(self):
        self._conn.close()
